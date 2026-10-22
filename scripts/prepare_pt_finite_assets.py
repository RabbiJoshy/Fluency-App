#!/usr/bin/env python3
"""Prepare release-bound app supplements without changing saved learning identities."""
import hashlib
import json
from pathlib import Path
import subprocess

from fluency.enrichments.card_rules import card_cognate, lemma_group_key, normal_token

ROOT = Path(__file__).resolve().parents[1]
OLD = "pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-slim"
NEW = OLD.replace("-slim", "-finite-v1-slim")
RELEASE = ROOT / "dist/pt-finite-staging/pt/speech" / NEW


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")


def main():
    before = read(ROOT.parent / "Fluency-Workspace/releases/pt/speech" / OLD / "app/vocabulary.index.json")
    after = read(RELEASE / "app/vocabulary.index.json")
    assert len(before) == len(after) == 10000
    changed = set()
    for a, b in zip(before, after):
        assert (a["id"], a["surface_card_id"]) == (b["id"], b["surface_card_id"])
        assert len(a["meanings"]) == len(b["meanings"])
        for x, y in zip(a["meanings"], b["meanings"]):
            assert x.get("sense_id") == y.get("sense_id")
            assert {k:v for k,v in x.items() if k not in ("headword", "translation", "metadata")} == {k:v for k,v in y.items() if k not in ("headword", "translation", "metadata")}
        if a != b:
            changed.add(normal_token(b["word"]))
    assert len(changed) == 99
    digest = hashlib.sha256((RELEASE / "app/vocabulary.index.json").read_bytes()).hexdigest()
    config_path = ROOT / "app/config/config.json"
    text = config_path.read_text().replace(NEW, OLD).replace("-finite-v1.json", ".json")
    cfg = json.loads(text)["languages"]["portuguese"]
    # Use separate files so the previous release remains available for rollback.
    supplements = {}
    for key in ("frequencyPath", "cognatesPath", "bridgePath", "mergeExceptionsPath", "dictionaryExamplesPath", "estimationPoolPath"):
        old_path = cfg[key]
        new_path = old_path.removesuffix(".json") + "-finite-v1.json"
        supplements[key] = read(ROOT / "app" / old_path)
        text = text.replace(json.dumps(old_path), json.dumps(new_path))
        cfg[key] = new_path
    frequency = supplements["frequencyPath"]
    frequency["indexPath"] = frequency["indexPath"].replace(OLD, NEW)
    frequency["indexSha256"] = digest
    cognates = supplements["cognatesPath"]
    cognates["built_from_release_id"] = NEW
    # Existing pair scores remain evidence; a new headword has no assumed score.
    for row in after:
        word = normal_token(row["word"])
        if word not in changed:
            continue
        cognates["cards"].pop(word, None)
        for code in cognates["known_languages"]:
            verdict = card_cognate(row, cognates["scores"].get(word), code, cognates.get("matches", {}).get(word))
            if verdict is not None and verdict[0] > 0:
                cognates["cards"].setdefault(word, {})[code] = [round(verdict[0], 3), verdict[1]]
    bridge = supplements["bridgePath"]
    bridge["built_from_release_id"] = NEW
    # Withdraw old grammatical-description matches instead of inventing evidence.
    for word in changed:
        bridge["targets"].pop(word, None)
        bridge.get("verb_compatible", {}).pop(word, None)
    merge = supplements["mergeExceptionsPath"]
    merge["release_id"] = NEW
    merge["release_index_content_id"] = "sha256:" + digest
    for row in after:
        word = normal_token(row["word"])
        if word in changed:
            merge["keys"][word] = lemma_group_key(row, merge["contractions"])
    built = subprocess.run(["node", "scripts/build_visible_sense_merges.cjs"], cwd=ROOT,
        input=json.dumps(after), text=True, capture_output=True, check=True)
    signatures = json.loads(built.stdout)
    merge["visible_sense_keys"] = {w:s for w,s in signatures.items() if merge["keys"].get(w)}
    merge["visible_sense_source_sha256"] = hashlib.sha256((ROOT / "app/js/vocab.js").read_bytes()).hexdigest()
    dictionary = supplements["dictionaryExamplesPath"]
    dictionary["release_id"] = NEW
    dictionary["index_sha256"] = digest
    dictionary["groups"] = {}
    for row in after:
        key = merge["keys"].get(normal_token(row["word"]))
        if key:
            dictionary["groups"].setdefault(key, []).append(row["word"])
    for key, payload in supplements.items():
        if key != "estimationPoolPath":
            write(ROOT / "app" / cfg[key], payload)
    # Source-language transfer bundles must name the active Portuguese release too.
    full_config = json.loads(text)
    for name, language in full_config["languages"].items():
        path = language.get("bridgePath")
        if name == "portuguese" or not path:
            continue
        payload = read(ROOT / "app" / path)
        if payload.get("source_releases", {}).get("pt") != OLD:
            continue
        payload["source_releases"]["pt"] = NEW
        for word in changed:
            payload.get("sources", {}).get("pt", {}).pop(word, None)
        new_path = path.removesuffix(".json") + "-finite-v1.json"
        write(ROOT / "app" / new_path, payload)
        text = text.replace(json.dumps(path), json.dumps(new_path))
    config_path.write_text(text.replace(OLD, NEW))
    print("Prepared supplements; verified 10000 card IDs, all meaning IDs and example assignments. Rebuild estimation pool next.")


if __name__ == "__main__":
    main()
