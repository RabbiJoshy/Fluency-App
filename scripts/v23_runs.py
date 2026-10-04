#!/usr/bin/env python3
"""v23 runs: the v22 Speech decks with the pronominal family narrowed by fluency.reflexive.

v23 changes stage 04 on pronominal-pair cards only: cards whose menu offers
both a pronominal and a non-pronominal family (SpanishDict X / Xse, Wiktionary
senses tagged pronominal or reflexive=true). Every other card's rows are carried
byte-for-byte from v22. Menus, sentences and the pre-WSD freeze are unchanged.

The pair cards are re-scored offline (exact-text embedding cache only, so no
spend) with the v21 profile's commit plus the reflexive filter (*-v23-1), on
the 10k-sieve MWE inventory v22 spliced from. v21's own inventory no longer
exists: the 10k sieve was rebuilt in place on 2026-10-03. So the baseline
(the same cards under *-v21-1, no tags) separates the two effects: v22 ->
baseline is the newer MWE inventory, baseline -> v23 is the reflexive filter.
v22's invariant-MWE splice is applied to every fresh row as it was to the rest.

    python scripts/build_reflexive_tags.py ...         # tags per freeze, first
    python scripts/v23_runs.py --step plan             # new runs, stages 01-03 carried from v22
    python scripts/v23_runs.py --step wsd --baseline   # pair cards under *-v21-1, no tags
    python scripts/v23_runs.py --step wsd              # pair cards under *-v23-1
    python scripts/v23_runs.py --step compare          # what changed, with samples
    python scripts/v23_runs.py --step import           # splice, MWE splice, import stage 04
    python scripts/v23_runs.py --step release          # inactive candidates, validated, sharded

Nothing is activated or published.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import v21_runs  # noqa: E402

SOURCES = {  # v22 run, pre-WSD freeze, the 10k sieve v22 spliced invariant MWEs from
    "es": ("20261003T160000Z-v22-es", "es/prewsd/20260914T223348Z-c35194bc-v2",
           "raw/mwe/mwe-es-10k-sieve/mwe_merged.json"),
    "pt": ("20261003T160000Z-v22-pt", "pt/prewsd/20260914T222723Z-e43a0469-v2",
           "raw/mwe/mwe-pt-10k-sieve/mwe_merged.json"),
}
RELEASE_ID = {"es": "es-speech-v23-10000x30-slim", "pt": "pt-speech-v23-10000x30-slim"}
RUNS_FILE = "v23-runs.json"
_json, _write, _say = v21_runs._json, v21_runs._write, v21_runs._say


def _languages(args) -> list[str]:
    return args.language or list(SOURCES)


def _runs(out: Path) -> dict[str, str]:
    return _json(out / RUNS_FILE) if (out / RUNS_FILE).exists() else {}


def _source(ws: Path, lang: str) -> Path:
    return ws / "runs" / lang / "speech" / SOURCES[lang][0]


def _tags(ws: Path, lang: str) -> Path:
    return ws / "raw/reflexive" / lang / f"tags-{SOURCES[lang][0]}.json"


def _bundle(ws: Path, lang: str, run: str, baseline: bool) -> Path:
    return ws / "raw/wsd" / lang / f"v23-{run}-{'baseline' if baseline else 'pairs'}.json"


def _pair_cards(run: Path) -> dict[str, str]:
    """card_id -> display form, for cards with both families."""
    from build_reflexive_tags import pair_cards
    menu = _json(run / "stages/02_sense_menu/output/sense-menu.json")
    pairs = pair_cards(menu)
    candidates = _json(run / "stages/03_sentence_harvest/output/candidates.json")
    return {c["card_id"]: c["display_form"] for c in candidates["cards"] if c["card_id"] in pairs}


def step_plan(args, ws: Path, out: Path) -> int:
    from fluency.core.workspace import Workspace
    from fluency.pipeline.planning import create_pipeline_plan
    workspace = Workspace.load(ws)
    runs = _runs(out)
    for lang in _languages(args):
        if lang in runs:
            _say(f"{lang}: run {runs[lang]} already planned")
            continue
        source = _source(ws, lang)
        profile = _json(source / "profile.json")
        profile["profile_id"] = profile["profile_id"].replace("-v22-", "-v23-")
        profile["wsd"]["model_profile"] = f"{lang}-v23-1"
        run = create_pipeline_plan(workspace, profile)
        for stage in ("01_inventory", "02_sense_menu", "03_sentence_harvest"):
            v21_runs._carry_stage(source, run, stage)
        runs[lang] = run.name
        _write(out / RUNS_FILE, runs)
        _say(f"{lang}: planned run {run.name} (stages 01-03 carried from {source.name})")
    return 0


def step_wsd(args, ws: Path, out: Path) -> int:
    runs = _runs(out)
    for lang in _languages(args):
        run = ws / "runs" / lang / "speech" / runs[lang]
        targets = sorted(set(_pair_cards(run).values()))
        if args.probe:
            targets = sorted(set(args.probe) & set(targets))
        mwe = ws / SOURCES[lang][2]
        bundle = _bundle(ws, lang, run.name, args.baseline)
        bundle.parent.mkdir(parents=True, exist_ok=True)
        profile = f"{lang}-v21-1" if args.baseline else f"{lang}-v23-1"
        command = [sys.executable, "-m", "fluency.speech.wsd_execute",
                   "--run-dir", str(run), "--out", str(bundle), "--profile-id", profile,
                   "--prewsd", str(ws / "raw/surfaces" / SOURCES[lang][1]),
                   "--multiword-inventory", str(mwe),
                   "--target-surfaces", *targets]
        if not args.baseline:
            command[command.index("--target-surfaces"):command.index("--target-surfaces")] = [
                "--reflexive-tags", str(_tags(ws, lang))]
        if args.spend:
            command += ["--env-file", str(REPO / ".env")]
        else:
            command.append("--offline-only")
        log = bundle.with_suffix(".log")
        _say(f"{lang}: {profile} on {len(targets):,} pair surfaces, "
             f"{'embedding uncached texts' if args.spend else 'offline only'}; log {log.name}")
        with log.open("w", encoding="utf-8") as handle:
            code = subprocess.call(command, stdout=handle, stderr=subprocess.STDOUT,
                                   env={**os.environ, "PYTHONPATH": str(REPO / "src")})
        tail = log.read_text(encoding="utf-8").strip().split("\n")[-6:]
        for line in tail:
            _say("  | " + line)
        if code:
            return code
    return 0


def _rows_by_key(rows) -> dict[tuple[str, str], dict]:
    return {(r["card_id"], r["sentence_id"]): r for r in rows}


def _verdict(row: dict) -> tuple:
    return (row.get("status"), row.get("menu_analysis_id"), row.get("selected_sense_id"))


def _v22_rows(source: Path, cards: set[str]):
    with (source / "stages/04_wsd_assignments/output/assignments.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["card_id"] in cards:
                yield row


def _mwe_splicer(ws: Path, lang: str):
    from build_v22_releases import splice_invariant_mwe
    from fluency.wsd.multiword import index_multiword_senses
    index = index_multiword_senses(_json(ws / SOURCES[lang][2]))
    columns = _json(ws / "raw/surfaces" / SOURCES[lang][1] / "examples.json")["columns"]
    text_of = dict(zip(columns["sentence_id"], columns["target"]))

    def splice(row: dict) -> dict:
        splice_invariant_mwe(row, text_of.get(row["sentence_id"].replace("sentence_", "")), index)
        return row
    return splice, text_of


def step_compare(args, ws: Path, out: Path) -> int:
    runs = _runs(out)
    for lang in _languages(args):
        run = ws / "runs" / lang / "speech" / runs[lang]
        source = _source(ws, lang)
        pairs = _pair_cards(run)
        splice, text_of = _mwe_splicer(ws, lang)
        old = _rows_by_key(_v22_rows(source, set(pairs)))
        menu = {c["card_id"]: c for c in _json(run / "stages/02_sense_menu/output/sense-menu.json")["cards"]}

        def label(card: str, row: dict) -> str:
            analysis = next((a for a in menu[card]["analyses"]
                             if a["menu_analysis_id"] == row.get("menu_analysis_id")), None)
            if analysis is None:
                return str((row.get("selected_tuple") or {}).get("headword") or row.get("status"))
            leaf = next((s for s in analysis["senses"] if s["sense_id"] == row.get("selected_sense_id")), None)
            return f"{analysis['headword']}: {(leaf or {}).get('translation') or '?'}"

        evaluated = sum(1 for r in old.values() if r["status"] in ("assigned", "abstained"))
        base = _rows_by_key(splice(dict(r)) for r in _json(_bundle(ws, lang, run.name, True))["assignments"])
        v23 = _rows_by_key(splice(dict(r)) for r in _json(_bundle(ws, lang, run.name, False))["assignments"])
        for kind, before, after in (("v22 -> baseline (MWE inventory)", old, base),
                                    ("baseline -> v23 (reflexive filter)", base, v23)):
            missing = set(before) ^ set(after)
            changed = [k for k in before if k in after and _verdict(before[k]) != _verdict(after[k])]
            _say(f"{lang} {kind}: key mismatches {len(missing)}, changed {len(changed):,} of {evaluated:,} evaluated")
            if before is old or not changed:
                continue
            old, new = before, after
            tags = Counter(str((new[k].get("evidence") or {}).get("candidate_preparation", {}).get("reflexive_tag"))
                           for k in changed)
            statuses = Counter((old[k]["status"], new[k]["status"]) for k in changed)
            _say(f"  by tag {dict(tags)}; status moves {dict(statuses)}")
            random.seed(7)
            sample = random.sample(changed, min(args.sample, len(changed)))
            lines = []
            for k in sample:
                text = text_of.get(k[1].replace("sentence_", ""), "")
                lines.append(f"[{pairs[k[0]]}] {text}\n    v22: {label(k[0], old[k])}\n    v23: {label(k[0], new[k])}")
            path = ws / "raw/wsd" / lang / f"v23-{run.name}-changes-sample.txt"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            _say(f"  {len(sample)} sampled changes in {path}")
    return 0


def _repair_spliced_row(row: dict, menu_card: dict | None, source_adapter: str, inventory_id: str) -> bool:
    """Give a v22-spliced invariant-MWE row the shape wsd_execute writes for one.

    v22's splice set an ``mwe_augmented`` projection only, so a row that had
    been abstained (or carried no projections) lacks ``provider_only`` and
    breaks the stage 04 contract; the release builder never checked. The
    word-level projection is rebuilt exactly as wsd_execute builds it for a
    deterministic invariant MWE: the menu's sole leaf, else its first.
    """
    from fluency.speech.wsd_execute import build_analyses
    from fluency.wsd.sampling import sole_leaf
    evidence = row.get("evidence") or {}
    if row.get("decision_path") != ["multiword"] or evidence.get("reason") != "deterministic_invariant_mwe":
        return False
    # v22 spliced from the 10k sieve but never recorded which file; it is
    # unchanged since (written 2026-10-03 15:30, v22 built at 15:57).
    unpinned = [c for c in evidence.get("multiword_candidates") or [] if not c.get("inventory_content_id")]
    for candidate in unpinned:
        candidate["inventory_content_id"] = inventory_id
    projections = row.get("selection_projections") or {}
    if "provider_only" in projections and row.get("active_selection_projection") == "mwe_augmented":
        return bool(unpinned)
    analyses = build_analyses(menu_card, menu_source_adapter=source_adapter) if menu_card else ()
    only = sole_leaf(analyses) if analyses else None
    word_a = only[0] if only else (analyses[0] if analyses else None)
    word_l = only[1] if only else (analyses[0].senses[0] if analyses and analyses[0].senses else None)
    if "provider_only" not in projections:
        if word_a is None or word_l is None:
            return False
        projections["provider_only"] = {
            "menu_analysis_id": word_a.menu_analysis_id, "selected_sense_id": word_l.sense_id,
            "selected_tuple": {"headword": word_a.headword, "part_of_speech": word_a.part_of_speech},
            "source_kind": "provider", "selected_score": 1.0, "runner_up_score": None, "raw_margin": None,
            "rank": 1, "emitted_level": "leaf", "raw_axis_margins": {"leaf": 1.0, "glosskey": 1.0, "tuple": 1.0},
        }
    row["selection_projections"] = projections
    row["active_selection_projection"] = "mwe_augmented"
    for key in ("confidence",):
        row.setdefault(key, None)
    evidence["repaired"] = ("v22 splice lacked the provider_only projection; rebuilt as wsd_execute "
                            "writes a deterministic invariant MWE row (menu sole or first leaf)")
    row["evidence"] = evidence
    return True


def step_import(args, ws: Path, out: Path) -> int:
    from fluency.core.hashing import file_content_id
    from fluency.core.workspace import Workspace
    from fluency.wsd.importer import import_wsd_assignments
    from fluency.wsd.splice import carried_row, write_spliced_bundle
    workspace = Workspace.load(ws)
    runs = _runs(out)
    for lang in _languages(args):
        run = ws / "runs" / lang / "speech" / runs[lang]
        if (run / "stages/04_wsd_assignments/output/assignments.jsonl").exists():
            _say(f"{lang}: stage 04 already imported in {run.name}")
            continue
        source = _source(ws, lang)
        src4 = source / "stages/04_wsd_assignments/output"
        pairs = set(_pair_cards(run))
        menu_doc = _json(run / "stages/02_sense_menu/output/sense-menu.json")
        menu_cards = {c["card_id"]: c for c in menu_doc["cards"]}
        repaired = Counter()
        inventory_id = file_content_id(ws / SOURCES[lang][2])
        fresh_bundle = _json(_bundle(ws, lang, run.name, False))
        new_menu_id = file_content_id(run / "stages/02_sense_menu/output/sense-menu.json")
        src_method = _json(src4 / "method.json")["method"]
        src_report = _json(src4 / "report.json")

        def carried_rows():
            with (src4 / "assignments.jsonl").open(encoding="utf-8", newline="\n") as handle:
                for line in handle:
                    if line.strip():
                        row = json.loads(line)
                        if row["card_id"] not in pairs:
                            repaired[_repair_spliced_row(row, menu_cards.get(row["card_id"]),
                                                         menu_doc["source_adapter"], inventory_id)] += 1
                            yield carried_row(row, source_run_id=source.name, source_method=src_method,
                                              sense_menu_content_id=new_menu_id)

        spliced = ws / "raw/wsd" / lang / f"v23-{run.name}-spliced.json"
        report = write_spliced_bundle(
            spliced, run_id=run.name, language=lang, mode="speech", inputs=fresh_bundle["inputs"],
            method=fresh_bundle["method"],
            sampling_policy=(src_report.get("occurrence_sampling") or {}).get("policy") or {},
            # Fresh rows need no splice: wsd_execute routed the same invariant
            # MWEs itself, from the same inventory and the same sentences.
            carried=carried_rows(), fresh=fresh_bundle["assignments"],
            declared=(), progress=_say)
        report["repaired_v22_splice_rows"] = repaired[True]
        _write(ws / "raw/wsd" / lang / f"v23-{run.name}-splice-report.json", report)
        _say(f"{lang}: repaired {repaired[True]:,} carried v22 splice rows")
        import_wsd_assignments(workspace, run_id=run.name, language=lang, mode="speech", bundle_path=spliced)
        _say(f"{lang}: stage 04 imported: {report['rows_by_origin']}; statuses {report['statuses']}")
    return 0


def step_release(args, ws: Path, out: Path) -> int:
    import functools
    from fluency.core.workspace import Workspace
    from fluency.release.example_shards import shard_app_examples
    from fluency.release.index_shards import shard_app_index
    from fluency.release.run_candidate import build_inactive_run_candidate
    from fluency.release.validation import validate_release_bundle
    workspace = Workspace.load(ws)
    runs = _runs(out)
    # Wiktionary conjugation layers built from each v23 run's own sense menu
    # (fluency.enrichments.conjugations, Kaikki provider), so the card back
    # ships with the deck instead of pointing at an older -conj release.
    layers = _json(out / "v23-conjugation-layers.json")
    for lang in _languages(args):
        output = build_inactive_run_candidate(
            workspace, run_id=runs[lang], release_id=RELEASE_ID[lang], language=lang, mode="speech",
            conjugations_artifact_id=layers[lang],
            wsd_selection_projection="mwe_augmented", wsd_publication_projection="forced_leaf")
        validate_release_bundle(output)
        functools.partial(shard_app_index, slim=True)(output / "app")
        functools.partial(shard_app_examples, slim=True)(output / "app")
        deck = _json(output / "deck.json")
        empty = [c["surface_key"] for c in deck["cards"] if not c.get("meanings")]
        _say(f"{lang}: candidate {output.name} validated; cards {len(deck['cards'])}, empty meanings {len(empty)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", required=True, choices=["plan", "wsd", "compare", "import", "release"])
    ap.add_argument("--language", nargs="+", choices=sorted(SOURCES))
    ap.add_argument("--baseline", action="store_true", help="wsd: score pair cards with *-v21-1, no tags")
    ap.add_argument("--probe", nargs="+", help="wsd: these surfaces only")
    ap.add_argument("--spend", action="store_true",
                    help="wsd: embed texts missing from the cache (paid); without it a miss stops the run "
                         "and the log lists the uncached texts, i.e. the projected spend")
    ap.add_argument("--sample", type=int, default=40, help="compare: changed rows to print")
    ap.add_argument("--workspace", type=Path, default=REPO.parent / "Fluency-Workspace")
    args = ap.parse_args()
    ws = args.workspace.resolve()
    out = ws / "raw/wsd"
    out.mkdir(parents=True, exist_ok=True)
    steps = {"plan": step_plan, "wsd": step_wsd, "compare": step_compare,
             "import": step_import, "release": step_release}
    return steps[args.step](args, ws, out)


if __name__ == "__main__":
    raise SystemExit(main())
