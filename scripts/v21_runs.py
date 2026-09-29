#!/usr/bin/env python3
"""v21 runs: re-score the live Speech decks with the *-v21-1 profiles.

v21 (decision 0029) changes the commit only (dictionary order stops vetoing the gloss between
analyses) and lets a headword spelled like the surface survive the tagger's
POS and lemma gates. Menus, sentences and the pre-WSD freeze are unchanged, so
each new run carries stages 01-03 byte-for-byte from the run behind the live
release and re-executes stage 04 on the same freeze.

    python scripts/v21_runs.py --step plan               # new runs, stages 01-03 carried
    python scripts/v21_runs.py --step wsd                # offline: prints uncached texts, no spend
    python scripts/v21_runs.py --step wsd --probe ty sé  # offline, a few surfaces, no import
    python scripts/v21_runs.py --step wsd --go           # full stage 04, splice declared rows, import
    python scripts/v21_runs.py --step release            # inactive candidates, validated, measured

Nothing is activated or published.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# The run behind each live release, and the pre-WSD freeze it was scored on.
SOURCES = {
    "es": ("20260923T220622Z-e1ef2457", "es/prewsd/20260914T223348Z-c35194bc-v2",
           "es/speech/es-speech-v15-mend-10000x10"),
    "pt": ("20260923T220643Z-1da6511e", "pt/prewsd/20260914T222723Z-e43a0469-v2",
           "pt/speech/pt-speech-v15-mend-10000x10"),
    "cs": ("20260923T220659Z-80b0f6a4", "cs/prewsd/20260914T223828Z-ad405a28",
           "cs/speech/cs-speech-v15-mend-10000x10"),
    "fi": ("20260927T144559Z-046fa948", "fi/prewsd/20260927T144559Z-046fa948",
           "fi/speech/fi-speech-v12-wsd-2000x10-20260927-r2"),
}
RELEASE_ID = {"es": "es-speech-v21-10000x10", "pt": "pt-speech-v21-10000x10",
              "cs": "cs-speech-v21-10000x10", "fi": "fi-speech-v21-2000x10"}
PROFILE = {"es": "es-v21-1", "pt": "pt-v21-1", "cs": "cs-v21-1", "fi": "fi-v21-1"}
DECLARED_STRATEGIES = ("declared_gloss", "entity")
RUNS_FILE = "v21-runs.json"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _say(message: str) -> None:
    print(message, flush=True)


def _carry_stage(source: Path, run: Path, stage_dir: str) -> None:
    from fluency.core.hashing import file_content_id
    src, dst = source / "stages" / stage_dir / "output", run / "stages" / stage_dir / "output"
    shutil.copytree(src, dst)
    manifest = _json(dst / "manifest.json")
    manifest["reused_from"] = str(src)
    _write(dst / "manifest.json", manifest)
    contract_path = run / "stages" / stage_dir / "contract.json"
    contract = _json(contract_path)
    contract.update(status="complete", completed_at=manifest.get("completed_at"),
                    output_directory="output",
                    manifest_content_id=file_content_id(dst / "manifest.json"),
                    carried_note=f"carried byte-for-byte from {source.name}; v21 changes stage 04 only")
    _write(contract_path, contract)


def _languages(args) -> list[str]:
    return args.language or list(SOURCES)


def _runs(out: Path) -> dict[str, str]:
    path = out / RUNS_FILE
    return _json(path) if path.exists() else {}


def step_plan(args, ws: Path, out: Path) -> int:
    from fluency.core.workspace import Workspace
    from fluency.pipeline.planning import create_pipeline_plan
    workspace = Workspace.load(ws)
    runs = _runs(out)
    for lang in _languages(args):
        if lang in runs:
            _say(f"{lang}: run {runs[lang]} already planned")
            continue
        source = ws / "runs" / lang / "speech" / SOURCES[lang][0]
        profile = _json(source / "profile.json")
        profile["profile_id"] = f"{profile['profile_id']}-v21"
        run = create_pipeline_plan(workspace, profile)
        for stage in ("01_inventory", "02_sense_menu", "03_sentence_harvest"):
            _carry_stage(source, run, stage)
        runs[lang] = run.name
        _write(out / RUNS_FILE, runs)
        _say(f"{lang}: planned run {run.name} (stages 01-03 carried from {source.name})")
    return 0


def _multiword_path(ws: Path, content_id: str | None) -> Path | None:
    from fluency.core.hashing import file_content_id
    if not content_id:
        return None
    for path in sorted((ws / "raw/mwe").rglob("mwe_merged.json")):
        if file_content_id(path) == content_id:
            return path
    raise SystemExit(f"no raw/mwe/**/mwe_merged.json matches {content_id}")


def step_wsd(args, ws: Path, out: Path) -> int:
    from fluency.core.hashing import file_content_id
    from fluency.core.workspace import Workspace
    from fluency.wsd.importer import import_wsd_assignments
    from fluency.wsd.splice import carried_row, write_spliced_bundle
    workspace = Workspace.load(ws)
    runs = _runs(out)
    for lang in _languages(args):
        run = ws / "runs" / lang / "speech" / runs[lang]
        source = ws / "runs" / lang / "speech" / SOURCES[lang][0]
        src4 = source / "stages/04_wsd_assignments/output"
        if (run / "stages/04_wsd_assignments/output/assignments.jsonl").exists():
            _say(f"{lang}: stage 04 already imported in {run.name}")
            continue
        menu_path = run / "stages/02_sense_menu/output/sense-menu.json"
        menu = {c["card_id"]: c for c in _json(menu_path)["cards"]}
        declared = {cid for cid, c in menu.items()
                    if (c.get("resolution") or {}).get("strategy") in DECLARED_STRATEGIES}
        candidates = _json(run / "stages/03_sentence_harvest/output/candidates.json")
        display = {card["card_id"]: card["display_form"] for card in candidates["cards"]}
        targets = sorted({display[cid] for cid in display if cid not in declared})
        if args.probe:
            targets = sorted(set(args.probe) & set(targets))
        src_report = _json(src4 / "report.json")
        mwe = _multiword_path(ws, (src_report.get("input_content_ids") or {}).get("multiword_inventory"))
        bundle_dir = ws / "raw/wsd" / lang
        bundle_dir.mkdir(parents=True, exist_ok=True)
        tag = "probe" if args.probe else "targets"
        bundle = bundle_dir / f"v21-{run.name}-{tag}.json"
        command = [sys.executable, "-X", "faulthandler", "-m", "fluency.speech.wsd_execute",
                   "--run-dir", str(run), "--out", str(bundle), "--profile-id", PROFILE[lang],
                   "--prewsd", str(ws / "raw/surfaces" / SOURCES[lang][1]),
                   "--target-surfaces", *targets]
        if mwe:
            command[command.index("--target-surfaces"):command.index("--target-surfaces")] = [
                "--multiword-inventory", str(mwe)]
        if args.env_file:
            command += ["--env-file", str(args.env_file)]
        if not args.go:
            command.append("--offline-only")
        if args.go and not args.probe and bundle.exists():
            _say(f"{lang}: reusing finished bundle {bundle.name}")
        else:
            log = bundle_dir / f"v21-{run.name}-{tag}.log"
            _say(f"{lang}: wsd_execute on {len(targets):,} surfaces "
                 f"({'paid if uncached' if args.go else 'offline only'}); log {log}")
            with log.open("w", encoding="utf-8") as handle, subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                    env={**os.environ, "PYTHONPATH": str(REPO / "src")}) as process:
                for line in process.stdout:
                    handle.write(line)
                    if any(k in line for k in ("exact texts", "cache", "embedded", "absent",
                                                "Error", "error", "assigned", "abstained")):
                        print("  | " + line.rstrip(), flush=True)
                code = process.wait()
            if code != 0:
                _say(f"{lang}: wsd_execute exited {code}. Without --go an exit here is the "
                     f"uncached count above, i.e. the projected spend. See {log}.")
                continue
        if not args.go or args.probe:
            _say(f"{lang}: offline run finished; nothing imported")
            continue
        fresh_bundle = _json(bundle)
        new_menu_id = file_content_id(menu_path)
        src_method = _json(src4 / "method.json")["method"]

        def carried_rows():
            with (src4 / "assignments.jsonl").open(encoding="utf-8", newline="\n") as handle:
                for line in handle:
                    if line.strip():
                        row = json.loads(line)
                        if row["card_id"] in declared:
                            yield carried_row(row, source_run_id=source.name, source_method=src_method,
                                              sense_menu_content_id=new_menu_id)

        spliced = bundle_dir / f"v21-{run.name}-spliced.json"
        report = write_spliced_bundle(
            spliced, run_id=run.name, language=lang, mode="speech", inputs=fresh_bundle["inputs"],
            method=fresh_bundle["method"],
            sampling_policy=(src_report.get("occurrence_sampling") or {}).get("policy") or {},
            carried=carried_rows(), fresh=fresh_bundle["assignments"], declared=(), progress=_say)
        _write(bundle_dir / f"v21-{run.name}-splice-report.json", report)
        import_wsd_assignments(workspace, run_id=run.name, language=lang, mode="speech",
                               bundle_path=spliced)
        _say(f"{lang}: stage 04 imported: {report['rows_by_origin']}; statuses {report['statuses']}")
    return 0


def step_release(args, ws: Path, out: Path) -> int:
    from fluency.core.workspace import Workspace
    from fluency.release.example_shards import shard_app_examples
    from fluency.release.index_shards import shard_app_index
    from fluency.release.run_candidate import build_inactive_run_candidate
    from fluency.release.validation import validate_release_bundle
    workspace = Workspace.load(ws)
    runs = _runs(out)
    for lang in _languages(args):
        live = ws / "releases" / SOURCES[lang][2]
        composition = _json(live / "composition.json")
        layers = composition.get("layers") or {}
        params = (layers.get("wsd_assignments") or {}).get("parameters") or {}
        titles = REPO / "app/data/source_titles.json"
        titled = any("source_title" in (ex.get("metadata") or {})
                     for card in list(_json(live / "app/vocabulary.examples.json").values())[:200]
                     for group in card.get("m") or [] for ex in group)
        output = build_inactive_run_candidate(
            workspace, run_id=runs[lang], release_id=RELEASE_ID[lang], language=lang, mode="speech",
            conjugations_artifact_id=(layers.get("conjugations") or {}).get("artifact_id"),
            source_titles_path=titles if titled else None,
            wsd_selection_projection=params.get("selection_projection", "provider_only"),
            wsd_publication_projection=params.get("publication_projection", "forced_leaf"))
        validate_release_bundle(output)
        shard_app_index(output / "app")
        shard_app_examples(output / "app")
        deck = _json(output / "deck.json")
        empty = [c["surface_key"] for c in deck["cards"] if not c.get("meanings")]
        _say(f"{lang}: candidate {output.name} validated; cards {len(deck['cards'])}, empty meanings {len(empty)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", required=True, choices=["plan", "wsd", "release"])
    ap.add_argument("--language", nargs="+", choices=sorted(SOURCES))
    ap.add_argument("--go", action="store_true", help="wsd: full run, splice and import (paid only if uncached)")
    ap.add_argument("--probe", nargs="+", help="wsd: offline, these surfaces only, nothing imported")
    ap.add_argument("--env-file", type=Path)
    ap.add_argument("--workspace", type=Path, default=REPO.parent / "Fluency-Workspace")
    args = ap.parse_args()
    ws = args.workspace.resolve()
    out = ws / "raw/wsd"
    out.mkdir(parents=True, exist_ok=True)
    return {"plan": step_plan, "wsd": step_wsd, "release": step_release}[args.step](args, ws, out)


if __name__ == "__main__":
    raise SystemExit(main())
