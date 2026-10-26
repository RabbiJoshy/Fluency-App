#!/usr/bin/env python3
"""Release-bound companion files for pt-speech-v25-decide-1-expr-10000-slim.

Follows scripts/prepare_pt_decide1_assets.py (the DECIDE-1 version) for the
release that adds inflected-expression answers (decision 0034). Cognates are
rebound first with scripts/rebind_cognates.py. This writes the bridge, speech
frequency, merge exceptions (then the form-privilege rule, -fp2), dictionary
examples, assignment filter and estimation pool, and points the Portuguese
config at them. Spanish/French bridges are repinned to the new pt source.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT.parent / "Fluency-Workspace"
OLD_REL = "pt-speech-v25-decide-1-10000-slim"
NEW_REL = "pt-speech-v25-decide-1-expr-10000-slim"
REL_DIR = WS / "releases/pt/speech" / NEW_REL
INDEX_PATH = REL_DIR / "app/vocabulary.index.json"
SUFFIX = "decide-expr-v1"
REVIEWS = WS / "reviews"
EXPR = REVIEWS / "pt-expressions-inflected-20261026"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def merged_answers(provider: str) -> Path:
    """DECIDE-1 answers for this provider, with its own re-asked expression answers applied."""
    folder = {"decide": "pt-top10000-decide-20261025", "jev": "pt-top10000-jev-remaining-20261025"}[provider]
    rows = [json.loads(line) for line in (REVIEWS / folder / f"answers-{provider}.jsonl").open(encoding="utf-8")]
    owned = {r["card_id"] for r in rows}
    override = {}
    for item in read_json(EXPR / f"requests-{provider}.json"):
        if item["card_id"] not in owned:
            continue
        path = EXPR / f"responses-{provider}" / f"{item['card_id']}.json"
        answers = read_json(path).get("answers") or {} if path.exists() else {}
        for sid in item["ids"]:
            if sid in answers:
                override[(item["card_id"], sid)] = answers[sid]
    out = EXPR / f"answers-{provider}-merged.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for r in rows:
            a = override.get((r["card_id"], r["sentence_id"]))
            if a:
                r = {**r, "choice": str(a.get("choice")), "confidence": a.get("confidence"),
                     "probabilities": a.get("probabilities")}
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out


def main() -> None:
    index_sha = hashlib.sha256(INDEX_PATH.read_bytes()).hexdigest()
    index_rows = read_json(INDEX_PATH)
    cfg_file = ROOT / "app/config/config.json"
    cfg_text = cfg_file.read_text(encoding="utf-8")
    cfg = json.loads(cfg_text)
    pt = cfg["languages"]["portuguese"]

    cognates = f"cognates/pt/cognates-literal-ground-r4-fw1-ds25-{SUFFIX}.json"
    assert read_json(ROOT / "app" / cognates)["built_from_release_id"] == NEW_REL

    bridge = f"data/bridge/pt-fw1-ds25-{SUFFIX}.json"
    data = read_json(ROOT / "app" / pt["bridgePath"])
    data["built_from_release_id"] = NEW_REL
    data["rebound_from"] = {"from_release": OLD_REL, "why": "DECIDE-1 + inflected expressions: same cards"}
    write_json(ROOT / "app" / bridge, data)
    for name in ("spanish", "french"):
        path = ROOT / "app" / cfg["languages"][name]["bridgePath"]
        other = read_json(path)
        if other.get("source_releases", {}).get("pt") == OLD_REL:
            other["source_releases"]["pt"] = NEW_REL
            write_json(path, other)

    frequency = f"data/speech-frequency/pt-literal-ground-r4-fw1-ds25-{SUFFIX}.json"
    data = read_json(ROOT / "app" / pt["frequencyPath"])
    data["indexPath"] = f"releases/pt/speech/{NEW_REL}/app/vocabulary.index.json"
    data["indexSha256"] = index_sha
    data["rebound_from"] = {"from_release": OLD_REL, "why": "DECIDE-1 + inflected expressions: same cards"}
    write_json(ROOT / "app" / frequency, data)

    merge = f"data/merge-exceptions/pt-literal-ground-r4-seam-v1-fw1-ds25-visible-v1-{SUFFIX}.json"
    data = read_json(REL_DIR / "app/merge-exceptions.json")
    assert data["release_id"] == NEW_REL and data["release_index_content_id"] == f"sha256:{index_sha}"
    previous = read_json(ROOT / "app" / pt["mergeExceptionsPath"])
    if "evidence" in previous and "evidence" not in data:
        data["evidence"] = previous["evidence"]
    write_json(ROOT / "app" / merge, data)

    replacements = {
        "indexPath": f"releases/pt/speech/{NEW_REL}/app/vocabulary.index.json",
        "examplesPath": f"releases/pt/speech/{NEW_REL}/app/vocabulary.examples.json",
        "studyStructurePath": f"releases/pt/speech/{NEW_REL}/app/study-structure.json",
        "releaseManifestPath": f"releases/pt/speech/{NEW_REL}/manifest.json",
        "releaseCompositionPath": f"releases/pt/speech/{NEW_REL}/composition.json",
        "conjugationsPath": f"releases/pt/speech/{NEW_REL}/app/conjugations.json",
        "cognatesPath": cognates, "bridgePath": bridge, "frequencyPath": frequency, "mergeExceptionsPath": merge,
        "dictionaryExamplesPath": f"data/dictionary-examples/pt-pt-speech-v25-literal-ground-r4-10000x30-slim-v1-fw1-ds25-{SUFFIX}.json",
        "assignmentFilterPath": "data/assignment-filters/pt-v25-decide-1-expr.json",
        "estimationPoolPath": f"data/estimation-pools/portuguese-literal-ground-r4-seam-v1-fw1-ds25-visible-v1-{SUFFIX}.json",
    }
    # Edit only the Portuguese block's lines, so other sessions' uncommitted lines survive.
    start = cfg_text.index('"portuguese": {')
    end = cfg_text.index('"portuguese_brazilian"', start)
    block = cfg_text[start:end]
    for key, value in replacements.items():
        old = pt[key]
        block = block.replace(f'"{key}": {json.dumps(old)}', f'"{key}": {json.dumps(value)}', 1)
    cfg_text = cfg_text[:start] + block + cfg_text[end:]
    cfg_file.write_text(cfg_text, encoding="utf-8")
    assert json.loads(cfg_text)["languages"]["portuguese"]["indexPath"] == replacements["indexPath"]

    subprocess.run(["node", str(ROOT / "scripts/build_form_privilege_merges.cjs"), "portuguese"], check=True)
    cfg = read_json(cfg_file)
    pt = cfg["languages"]["portuguese"]
    keys = read_json(ROOT / "app" / pt["mergeExceptionsPath"])["keys"]

    dictionary = read_json(ROOT / "app/data/dictionary-examples/pt-pt-speech-v25-literal-ground-r4-10000x30-slim-v1-fw1-ds25-decide-v1.json")
    dictionary["release_id"] = NEW_REL
    dictionary["index_sha256"] = index_sha
    dictionary["groups"] = {}
    for row in index_rows:
        key = keys.get(row["word"].lower())
        if key:
            dictionary["groups"].setdefault(key, []).append(row["word"])
    write_json(ROOT / "app" / replacements["dictionaryExamplesPath"], dictionary)

    subprocess.run([sys.executable, str(ROOT / "scripts/build_assignment_filter_index.py"), str(REL_DIR),
                    str(ROOT / "app" / replacements["assignmentFilterPath"]),
                    "--answers", f"decide={merged_answers('decide')}", "--answers", f"jev={merged_answers('jev')}"],
                   check=True)
    subprocess.run(["node", str(ROOT / "scripts/build_estimation_pools.cjs"), str(WS), "portuguese"], check=True)
    print("portuguese config ->", pt["indexPath"])


if __name__ == "__main__":
    main()
