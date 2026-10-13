#!/usr/bin/env python3
"""Function-word overlay: grammar-word labels on a live Speech deck, nothing else changed.

The Dutch prototype labels function words by rule instead of WSD. On a live deck
(es, pt, cs) the senses already exist, so this overlay keeps every Stage 04 row
exactly as decided -- carried, with its sense -- and adds `evidence.function_word`
to the selected sentences of function-word cards. The release builder turns those
labels into the card's 'Grammar word' block and each example's chip.

    overlay.py --language pt --step plan      # new run, stages 01-03 carried from the live run
    overlay.py --language pt --step label     # Stanza + labeller_<lang> over the shown sentences
    overlay.py --language pt --step sample    # print a random labelled sample for a hand check
    overlay.py --language pt --step import    # live Stage 04 carried + labels -> new Stage 04
    overlay.py --language cs --step carry     # same, for live rows older than the import contract
    overlay.py --language pt --step release   # inactive candidate, validated, slim-sharded

Function-word candidates: cards whose menu has a closed-class part of speech
(article, determiner, pronoun, preposition, conjunction, particle, contraction)
and more than one sense. A candidate gets the presentation when the rules label
at least KEEP_SHARE of its shown sentences. Nothing is activated or published.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "research/cascade/trouble-words"))

# Closed classes under both providers' names: Wiktionary (prep, conj) and SpanishDict (ADP, CCONJ).
CLOSED = {"article", "det", "pron", "prep", "conj", "particle", "postp", "contraction",
          "adp", "cconj", "sconj", "pronoun", "determiner", "preposition", "conjunction"}
KEEP_SHARE = 0.6
LIVE_RELEASE = {
    "pt": "pt/speech/pt-speech-v25-literal-ground-r4-10000x30-slim",
    "es": "es/speech/es-speech-v25-literal-ground-r6-10000x30-slim",
    "cs": "cs/speech/cs-speech-v22-10000x30-slim",
}
STANZA_LANG = {"pt": "pt", "es": "es", "cs": "cs"}
TAG = "fw1"
RUNS_FILE = "fw-overlay-runs.json"


def _json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, data) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _say(msg: str) -> None:
    print(msg, flush=True)


def release_id(lang: str) -> str:
    live = LIVE_RELEASE[lang].rsplit("/", 1)[1]
    return live.replace("-slim", "") + f"-{TAG}-slim"


def source_run(ws: Path, lang: str) -> Path:
    manifest = _json(ws / "releases" / LIVE_RELEASE[lang] / "manifest.json")
    return ws / "runs" / lang / "speech" / manifest["wsd"]["source_id"]


def labels_path(ws: Path, lang: str) -> Path:
    return ws / "raw/wsd" / lang / f"{TAG}-function-word-labels.json"


def step_plan(args, ws: Path) -> int:
    import v21_runs
    from fluency.core.workspace import Workspace
    from fluency.pipeline.planning import create_pipeline_plan
    runs_path = ws / "raw/wsd" / RUNS_FILE
    runs = _json(runs_path) if runs_path.exists() else {}
    lang = args.language
    if lang in runs:
        _say(f"{lang}: run {runs[lang]} already planned"); return 0
    source = source_run(ws, lang)
    profile = _json(source / "profile.json")
    profile["profile_id"] = f"{profile['profile_id']}-{TAG}"
    profile.setdefault("scope", {})["note"] = (
        f"Function-word overlay ({TAG}): stages 01-03 and every Stage 04 decision carried from "
        f"{source.name}; function-word cards gain rule labels (research/cascade/fw-overlay).")
    run = create_pipeline_plan(Workspace.load(ws), profile)
    for stage in ("01_inventory", "02_sense_menu", "03_sentence_harvest"):
        v21_runs._carry_stage(source, run, stage)
        contract_path = run / "stages" / stage / "contract.json"
        contract = _json(contract_path)
        contract["carried_note"] = f"carried byte-for-byte from {source.name}; {TAG} adds function-word labels only"
        _write(contract_path, contract)
    runs[lang] = run.name
    _write(runs_path, runs)
    _say(f"{lang}: planned run {run.name} (stages 01-03 carried from {source.name})")
    return 0


def candidates(ws: Path, lang: str):
    """(card_id, form, rank, shown sentence ids) for every function-word candidate."""
    src = source_run(ws, lang) / "stages"
    menu = _json(src / "02_sense_menu/output/sense-menu.json")["cards"]
    inv = {c["card_id"]: c for c in _json(src / "01_inventory/output/inventory.json")["cards"]}
    shown = {c["card_id"]: [e["sentence_id"] for e in c["selected"]]
             for c in _json(src / "05_example_selection/output/selection.json")["cards"]}
    out = []
    for card in menu:
        pos = {a["part_of_speech"].lower() for a in card["analyses"]}
        senses = sum(len(a["senses"]) for a in card["analyses"])
        if pos & CLOSED and senses > 1 and shown.get(card["card_id"]):
            info = inv[card["card_id"]]
            out.append((card["card_id"], info.get("display_form") or info.get("surface_key"), info["rank"],
                        shown[card["card_id"]]))
    return sorted(out, key=lambda c: c[2])


def _bank(ws: Path, lang: str, need: set[str]) -> dict[str, tuple[str, str]]:
    bank = {}
    with open(source_run(ws, lang) / "stages/03_sentence_harvest/output/sentence-bank.jsonl", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["sentence_id"] in need:
                bank[r["sentence_id"]] = (r["target"]["text"], (r.get("translation") or {}).get("text", ""))
    return bank


def locate(doc, text: str, form: str):
    """(words, first word index, token text) of the first occurrence of `form` as a whole token."""
    pat = re.escape(form).replace("'", "['’]")
    m = re.search(r"(?<![\w'’])" + pat + r"(?![\w'’])", text, re.I)
    if not m:
        return None
    for s in doc.sentences:
        for k, w in enumerate(s.words):
            if w.parent.start_char <= m.start() < w.parent.end_char:
                return s.words, k, w.parent.text
    return None


def step_label(args, ws: Path) -> int:
    import importlib
    import stanza
    lang = args.language
    L = importlib.import_module(f"labeller_{lang}")
    cards = candidates(ws, lang)
    need = {s for c in cards for s in c[3]}
    bank = _bank(ws, lang, need)
    if lang == "es":  # the repo's pinned Spanish parser (fluency.nlp.pos), seen through a Stanza-shaped adapter
        import spacy_adapter
        sp = spacy_adapter.Pipeline("es_dep_news_trf")
        parse, parser = sp.bulk, sp.version
    else:
        nlp = stanza.Pipeline(STANZA_LANG[lang], processors="tokenize,mwt,pos,lemma,depparse",
                              download_method=None, use_gpu=False, verbose=False)
        parse = lambda texts: nlp.bulk_process([stanza.Document([], text=t) for t in texts])
        parser = f"stanza-{lang}-default@{stanza.__version__}"
    out = {"labeller": f"research/cascade/trouble-words/labeller_{lang}.py", "keep_share": KEEP_SHARE,
           "parser": parser, "cards": {}}
    for n, (cid, form, rank, sids) in enumerate(cards):
        texts = [bank[s][0] for s in sids if s in bank]
        docs = parse(texts)
        labels = {}
        for sid, text, doc in zip([s for s in sids if s in bank], texts, docs):
            hit = locate(doc, text, form)
            if not hit:
                continue
            lab = L.label(hit[0], hit[1], surface=hit[2])
            if lab and lab["kind"] != "none":
                labels[sid] = {k: lab[k] for k in ("kind", "value", "gloss", "rule")}
        keep = len(labels) >= KEEP_SHARE * len(sids)
        out["cards"][cid] = {"form": form, "rank": rank, "shown": len(sids), "keep": keep, "labels": labels}
        if n % 25 == 0:
            _say(f"  {n}/{len(cards)} {form}: {len(labels)}/{len(sids)} labelled")
    path = labels_path(ws, lang)
    path.parent.mkdir(parents=True, exist_ok=True)
    _write(path, out)
    kept = [v for v in out["cards"].values() if v["keep"]]
    _say(f"{lang}: {len(cards)} candidates, {len(kept)} get the function-word presentation -> {path}")
    _say("  not kept: " + ", ".join(f"{v['form']} {len(v['labels'])}/{v['shown']}"
                                    for v in out["cards"].values() if not v["keep"]))
    return 0


def step_sample(args, ws: Path) -> int:
    lang = args.language
    data = _json(labels_path(ws, lang))["cards"]
    kept = sorted((v for v in data.values() if v["keep"]), key=lambda v: v["rank"])
    rng = random.Random(args.seed)
    top = kept[:40]
    picks = []
    for _ in range(args.n):
        card = rng.choice(top if rng.random() < 0.6 else kept)
        if card["labels"]:
            picks.append((card["form"], rng.choice(sorted(card["labels"]))))
    bank = _bank(ws, lang, {s for _, s in picks})
    for n, (form, sid) in enumerate(picks):
        lab = data[next(k for k, v in data.items() if v["form"] == form)]["labels"][sid]
        text, en = bank[sid]
        _say(f"{n} {form} => {lab['value']} | {lab['gloss']} || {text[:100]} // {en[:90]}")
    return 0


def step_import(args, ws: Path) -> int:
    from fluency.core.hashing import file_content_id
    from fluency.core.workspace import Workspace
    from fluency.wsd.importer import import_wsd_assignments
    from fluency.wsd.splice import carried_row, write_spliced_bundle
    lang = args.language
    run = ws / "runs" / lang / "speech" / _json(ws / "raw/wsd" / RUNS_FILE)[lang]
    source = source_run(ws, lang)
    src4 = source / "stages/04_wsd_assignments/output"
    labels_file = labels_path(ws, lang)
    data = _json(labels_file)
    kept = {cid: v["labels"] for cid, v in data["cards"].items() if v["keep"]}
    src_method = _json(src4 / "method.json")["method"]
    menu_id = file_content_id(run / "stages/02_sense_menu/output/sense-menu.json")
    labeller = REPO / data["labeller"]
    method = dict(src_method)
    method["profile_id"] = f"{src_method['profile_id']}-{TAG}"
    method["function_word_overlay"] = {
        "version": f"research.cascade.fw-overlay/{TAG}",
        "labeller": data["labeller"], "labeller_content_id": file_content_id(labeller),
        "overlay_content_id": file_content_id(Path(__file__)), "labels_content_id": file_content_id(labels_file),
        "parser": data["parser"], "keep_share": data["keep_share"], "cards": len(kept),
        "why": "senses carried unchanged; function-word cards gain rule labels for the grammar-word presentation",
    }
    counts = {"labelled": 0}

    def rows():
        with open(src4 / "assignments.jsonl", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                out = carried_row(row, source_run_id=source.name, source_method=src_method,
                                  sense_menu_content_id=menu_id)
                lab = kept.get(row["card_id"], {}).get(row["sentence_id"])
                if lab:
                    out["evidence"]["function_word"] = dict(lab)
                    counts["labelled"] += 1
                yield out

    # the source's own declared inputs, including the multiword inventory its MWE senses came from
    inputs = dict(_json(src4 / "report.json")["input_content_ids"])
    inputs.pop("assignment_bundle", None)
    bundle = ws / "raw/wsd" / lang / f"{TAG}-{run.name}-spliced.json"
    report = write_spliced_bundle(
        bundle, run_id=run.name, language=lang, mode="speech", inputs=inputs, method=method,
        sampling_policy=(_json(src4 / "report.json").get("occurrence_sampling") or {}).get("policy") or {},
        carried=rows(), fresh=(), declared=(), progress=_say)
    report["function_word_labelled_rows"] = counts["labelled"]
    _write(ws / "raw/wsd" / lang / f"{TAG}-{run.name}-splice-report.json", report)
    import_wsd_assignments(Workspace.load(ws), run_id=run.name, language=lang, mode="speech", bundle_path=bundle,
                           streaming=True)
    _say(f"{lang}: stage 04 imported into {run.name}: {report['statuses']}; labelled rows {counts['labelled']}")
    return 0


def step_carry(args, ws: Path) -> int:
    """Stage 04 for a run whose live rows predate the import contract (cs v22: no provider_only
    projection). The importer would refuse rows it did not write, so they are carried as x30_runs
    carried them -- unchanged -- with the function-word labels added to the evidence of labelled
    rows, and the manifest says so. Nothing here re-validates the carried decisions."""
    import shutil
    from fluency.core.hashing import file_content_id
    lang = args.language
    run = ws / "runs" / lang / "speech" / _json(ws / "raw/wsd" / RUNS_FILE)[lang]
    source = source_run(ws, lang)
    src4, dst4 = source / "stages/04_wsd_assignments/output", run / "stages/04_wsd_assignments/output"
    if dst4.exists():
        _say(f"{lang}: stage 04 already present in {run.name}"); return 0
    labels_file = labels_path(ws, lang)
    data = _json(labels_file)
    kept = {cid: v["labels"] for cid, v in data["cards"].items() if v["keep"]}
    dst4.mkdir(parents=True)
    for name in ("method.json", "report.json"):
        shutil.copy2(src4 / name, dst4 / name)
    overlay_note = {
        "version": f"research.cascade.fw-overlay/{TAG}", "labeller": data["labeller"],
        "labeller_content_id": file_content_id(REPO / data["labeller"]), "labels_content_id": file_content_id(labels_file),
        "overlay_content_id": file_content_id(Path(__file__)), "parser": data["parser"], "cards": len(kept),
        "why": "rows carried from the live run unchanged (they predate the current import contract and are not "
               "re-validated); function-word cards gain rule labels in evidence.function_word"}
    labelled = 0
    with open(src4 / "assignments.jsonl", encoding="utf-8") as fh, open(dst4 / "assignments.jsonl", "w", encoding="utf-8") as out:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            lab = kept.get(row["card_id"], {}).get(row["sentence_id"])
            if lab:
                row.setdefault("evidence", {})["function_word"] = dict(lab)
                labelled += 1
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            else:
                out.write(line if line.endswith("\n") else line + "\n")
    method = _json(dst4 / "method.json")
    method.setdefault("method", {})["function_word_overlay"] = overlay_note
    _write(dst4 / "method.json", method)
    manifest = _json(src4 / "manifest.json")
    manifest["reused_from"] = str(src4)
    manifest["function_word_overlay"] = {**overlay_note, "labelled_rows": labelled}
    manifest["outputs"] = {"assignments": file_content_id(dst4 / "assignments.jsonl"),
                           "method": file_content_id(dst4 / "method.json"), "report": file_content_id(dst4 / "report.json")}
    _write(dst4 / "manifest.json", manifest)
    contract_path = run / "stages/04_wsd_assignments/contract.json"
    contract = _json(contract_path)
    contract.update(status="complete", completed_at=manifest.get("completed_at"), output_directory="output",
                    manifest_content_id=file_content_id(dst4 / "manifest.json"),
                    carried_note=f"rows carried from {source.name}; {TAG} adds function-word labels to {labelled} rows")
    _write(contract_path, contract)
    _say(f"{lang}: stage 04 carried into {run.name} with {labelled} labelled rows")
    return 0


def step_release(args, ws: Path) -> int:
    from fluency.core.workspace import Workspace
    from fluency.release.example_shards import shard_app_examples
    from fluency.release.index_shards import shard_app_index
    from fluency.release.run_candidate import build_inactive_run_candidate
    from fluency.release.validation import validate_release_bundle
    lang = args.language
    run_id = _json(ws / "raw/wsd" / RUNS_FILE)[lang]
    live = ws / "releases" / LIVE_RELEASE[lang]
    layers = _json(live / "composition.json").get("layers") or {}
    params = (layers.get("wsd_assignments") or {}).get("parameters") or {}
    titled = any("source_title" in (ex.get("metadata") or {})
                 for card in list(_json(live / "app/vocabulary.examples.json").values())[:200]
                 for group in card.get("m") or [] for ex in group)
    output = build_inactive_run_candidate(
        Workspace.load(ws), run_id=run_id, release_id=release_id(lang), language=lang, mode="speech",
        conjugations_artifact_id=(layers.get("conjugations") or {}).get("artifact_id"),
        source_titles_path=REPO / "app/data/source_titles.json" if titled else None,
        wsd_selection_projection=params.get("selection_projection", "provider_only"),
        wsd_publication_projection=params.get("publication_projection", "forced_leaf"), memory_bounded=True)
    validate_release_bundle(output)
    shard_app_index(output / "app", slim=True)
    shard_app_examples(output / "app", slim=True)
    idx = _json(output / "app/vocabulary.index.json")
    cards = idx if isinstance(idx, list) else idx.get("cards") or idx.get("entries") or []
    fw = sum(1 for c in cards if c.get("function_word"))
    _say(f"{lang}: candidate {output.name} validated; cards {len(cards)}, with function-word block {fw}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--language", required=True, choices=sorted(LIVE_RELEASE))
    ap.add_argument("--step", required=True, choices=["plan", "label", "sample", "import", "carry", "release"])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--workspace", type=Path, default=REPO.parent / "Fluency-Workspace")
    args = ap.parse_args()
    ws = args.workspace.resolve()
    return {"plan": step_plan, "label": step_label, "sample": step_sample,
            "import": step_import, "carry": step_carry, "release": step_release}[args.step](args, ws)


if __name__ == "__main__":
    raise SystemExit(main())
