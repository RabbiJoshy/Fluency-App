"""Audit the actual release examples, including surfaces excluded by fw-overlay."""
import hashlib
import importlib
import json
import re
import sys
from pathlib import Path

from record_gold import AUDIT

ROOT = Path(__file__).resolve().parents[2]
WS = ROOT.parent / "Fluency-Workspace"
sys.path.insert(0, str(ROOT / "research/cascade/trouble-words"))
CLOSED = {"article", "det", "pron", "prep", "conj", "particle", "postp", "contraction", "adp", "cconj", "sconj", "pronoun", "determiner", "preposition", "conjunction"}


def main():
    config = json.loads((AUDIT / "inputs/Fluency-Next/app/config/config.json").read_text())
    original = [json.loads(line) for line in (AUDIT / "blind-all.jsonl").read_text().splitlines()]
    by_identity = {(r["language"], r["card_id"], r["sentence_id"]): r for r in original}
    expanded = []
    extra_pins = []
    scope = []
    next_id = len(original)
    for lang, name in (("es", "spanish"), ("pt", "portuguese")):
        labeller = importlib.import_module("labeller_" + lang)
        declared = {"que", "se"}
        for attribute in ("ARTICLE", "PREP_GLOSS", "PRON_GLOSS", "CONJ_GLOSS", "CONTRACTION"):
            declared.update(getattr(labeller, attribute))
        manifest_path = WS / config["languages"][name]["releaseManifestPath"]
        manifest = json.loads(manifest_path.read_text())
        run = WS / "runs" / lang / "speech" / manifest["wsd"]["source_id"]
        menu_path = run / "stages/02_sense_menu/output/sense-menu.json"
        menu = json.loads(menu_path.read_text())
        eligible = {c["card_id"] for c in menu["cards"] if any(a["part_of_speech"].lower() in CLOSED for a in c["analyses"])}
        deck_path = manifest_path.parent / "deck.json"
        for path in (menu_path, run / "stages/01_inventory/output/inventory.json", run / "stages/04_wsd_assignments/output/assignments.jsonl", deck_path, Path(labeller.KAIKKI)):
            digest = hashlib.sha256()
            with path.open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            extra_pins.append({"path": str(path.resolve()), "sha256": digest.hexdigest()})
        deck = json.loads(deck_path.read_text())
        for card in deck["cards"]:
            form, cid = card["display_form"], card["card_id"]
            if cid not in eligible and form.lower() not in declared:
                continue
            scope.append({"language": lang, "card_id": cid, "word": form, "shown": len(card["examples"]), "declared": form.lower() in declared, "closed_menu": cid in eligible, "overlay_candidate": any(k[0] == lang and k[1] == cid for k in by_identity)})
            for example in card["examples"]:
                sid = example["metadata"]["sentence_id"]
                identity = (lang, cid, sid)
                if identity in by_identity:
                    row = by_identity[identity]
                else:
                    text = example["text"] if "text" in example else example["metadata"]["target"]["text"]
                    matches = list(re.finditer(r"(?<![\w'’])" + re.escape(form) + r"(?![\w'’])", text, re.I))
                    row = {"language": lang, "card_id": cid, "word": form, "rank": card.get("rank"), "sentence_id": sid, "text": text, "translation": example.get("english", ""), "spans": [[m.start(), m.end()] for m in matches], "review_id": next_id}
                    next_id += 1
                expanded.append(row)
        print(lang, sum(c["language"] == lang for c in scope), "cards;", sum(r["language"] == lang for r in expanded), "shown examples", flush=True)
    (AUDIT / "blind-census.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in expanded))
    (AUDIT / "scope.json").write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n")
    (AUDIT / "release-input-pins.json").write_text(json.dumps(extra_pins, indent=2) + "\n")
    included = {(r["language"], r["card_id"], r["sentence_id"]) for r in expanded}
    absent = sorted(set(by_identity) - included)
    print("Additional rows:", next_id - len(original), "original selection rows absent from release:", len(absent))
    (AUDIT / "selection-release-difference.json").write_text(json.dumps(absent) + "\n")


if __name__ == "__main__":
    main()
