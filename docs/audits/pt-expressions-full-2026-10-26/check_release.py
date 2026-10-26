"""Check the expressions release against DECIDE-1: untouched cards identical, re-run cards before/after."""
import json
import sys
from collections import Counter
from pathlib import Path

WS = Path(__file__).resolve().parents[4] / "Fluency-Workspace"
OLD = WS / "releases/pt/speech/pt-speech-v25-decide-1-10000-slim/deck.json"
NEW = WS / "releases/pt/speech/pt-speech-v25-decide-1-expr-10000-slim/deck.json"
RERUN = WS / "reviews/pt-expressions-inflected-20261026"
SHOW = sys.argv[1:] or ["tomou", "vale", "faz", "dou", "tintas", "fazia", "dava"]


def signature(card):
    meanings = sorted((m.get("headword"), m.get("translation"), m.get("assignment_status")) for m in card.get("meanings", []))
    examples = sorted((e.get("metadata", {}).get("sentence_id"), e.get("sense_id")) for e in card.get("examples", []))
    return meanings, examples


def rows(card):
    counts = Counter(e.get("sense_id") for e in card.get("examples", []))
    return [(counts.get(m.get("sense_id"), 0), m.get("headword"), (m.get("translation") or "")[:50])
            for m in card.get("meanings", []) if counts.get(m.get("sense_id"), 0)]


old = {c["card_id"]: c for c in json.loads(OLD.read_text())["cards"]}
new = {c["card_id"]: c for c in json.loads(NEW.read_text())["cards"]}
rerun = {i["card_id"] for p in ("decide", "jev") for i in json.loads((RERUN / f"requests-{p}.json").read_text())}
drift = [cid for cid in old if cid not in rerun and signature(old[cid]) != signature(new.get(cid, {}))]
changed = [cid for cid in rerun if cid in old and signature(old[cid]) != signature(new.get(cid, {}))]
print(f"cards {len(new)}; re-run cards changed {len(changed)} of {len(rerun)}; untouched cards that drifted: {len(drift)}")
for cid in drift[:10]:
    print("  DRIFT", old[cid].get("display_form"))
examples_old = sum(len(c.get("examples", [])) for c in old.values())
examples_new = sum(len(c.get("examples", [])) for c in new.values())
print(f"published examples {examples_old:,} -> {examples_new:,}")
by_surface = {c.get("display_form"): c["card_id"] for c in new.values()}
for surface in SHOW:
    cid = by_surface.get(surface)
    if not cid:
        continue
    print(f"\n## {surface}")
    print("  before:", rows(old[cid]))
    print("  after: ", rows(new[cid]))
