"""Pin HINGE inputs and export sentence-only review rows, never model labels.

Run from the repository root. Large evidence stays in Fluency-Workspace.
"""
from pathlib import Path
import hashlib
import json
import random
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
WS = ROOT.parent / "Fluency-Workspace"
OUT = WS / "audits/hinge-20261014"


def read(path):
    return json.loads(path.read_text())


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    pins = []

    def pin(path):
        content = path.read_bytes()
        pins.append({"path": str(path.resolve()), "sha256": hashlib.sha256(content).hexdigest()})
        target = OUT / "inputs" / path.resolve().relative_to(ROOT.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != content:
            raise RuntimeError(f"Pinned input changed: {path}")
        target.write_bytes(content)

    pin(ROOT / "app/config/config.json")
    for directory in ("trouble-words", "fw-overlay"):
        for path in sorted((ROOT / "research/cascade" / directory).glob("*.py")):
            pin(path)
    config = read(ROOT / "app/config/config.json")
    all_rows = []
    for lang, name in (("es", "spanish"), ("pt", "portuguese")):
        release = WS / config["languages"][name]["releaseManifestPath"]
        pin(release)
        manifest = read(release)
        run = WS / "runs" / lang / "speech" / manifest["wsd"]["source_id"]
        for relative in ("manifest.json", "profile.json", "stages/04_wsd_assignments/output/method.json", "stages/05_example_selection/output/selection.json"):
            path = run / relative
            if path.exists():
                pin(path)
        for tag in ("fw1", "fw2"):
            pin(WS / "raw/wsd" / lang / f"{tag}-function-word-labels.json")
        # A review's scope includes candidate cards which did not pass the cutoff.
        cards = read(WS / "raw/wsd" / lang / "fw1-function-word-labels.json")["cards"]
        selection = read(run / "stages/05_example_selection/output/selection.json")
        shown = {c["card_id"]: c["selected"] for c in selection["cards"]}
        bank = {}
        needed = {e["sentence_id"] for cid in cards for e in shown.get(cid, [])}
        bank_path = run / "stages/03_sentence_harvest/output/sentence-bank.jsonl"
        digest = hashlib.sha256()
        with bank_path.open("rb") as source:
            for line in source:
                digest.update(line)
                item = json.loads(line)
                if item["sentence_id"] in needed:
                    bank[item["sentence_id"]] = item
        pins.append({"path": str(bank_path.resolve()), "sha256": digest.hexdigest()})
        for cid, card in sorted(cards.items(), key=lambda x: x[1]["rank"]):
            for selected in shown.get(cid, []):
                sid = selected["sentence_id"]
                sentence = bank[sid]
                text = sentence["target"]["text"]
                matches = list(re.finditer(r"(?<![\w'’])" + re.escape(card["form"]) + r"(?![\w'’])", text, re.I))
                all_rows.append({"language": lang, "card_id": cid, "word": card["form"], "rank": card["rank"], "sentence_id": sid, "text": text, "translation": (sentence.get("translation") or {}).get("text", ""), "spans": [[m.start(), m.end()] for m in matches]})
    for i, row in enumerate(all_rows):
        row["review_id"] = i
    def write(name, rows):
        path = OUT / name
        content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        if path.exists() and path.read_text() != content:
            raise RuntimeError(f"Review input changed: {path}")
        path.write_text(content)
    write("blind-all.jsonl", all_rows)
    # Complete high-frequency card sets, plus independent stratified holdout.
    frequent = {"es": {"que", "de", "se", "a", "la", "lo", "me", "al", "del", "qué", "por"}, "pt": {"que", "de", "se", "a", "o", "me", "no", "por", "cada", "nos", "do", "uma"}}
    development = [r for r in all_rows if r["word"] in frequent[r["language"]]]
    remaining = [r for r in all_rows if r not in development]
    rng = random.Random(14102026)
    holdout = []
    for lang in ("es", "pt"):
        holdout.extend(rng.sample([r for r in remaining if r["language"] == lang], 100))
    write("blind-development.jsonl", development)
    write("blind-holdout.jsonl", holdout)
    (OUT / "pins.json").write_text(json.dumps(pins, indent=2) + "\n")
    (OUT / "parked.diff").write_bytes(subprocess.check_output(["git", "diff", "--", "research/cascade"], cwd=ROOT))
    print(f"{OUT}: {len(all_rows)} census rows, {len(development)} development, {len(holdout)} holdout")


if __name__ == "__main__":
    prepare()
