"""Compare DECIDE-1 answers with the expression re-run, under the release's NONE rule."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4] / "Fluency-Workspace"
OUT = WORKSPACE / "reviews/pt-expressions-inflected-20261026"
SETS = {"decide": WORKSPACE / "reviews/pt-top10000-decide-20261025",
        "jev": WORKSPACE / "reviews/pt-top10000-jev-remaining-20261025"}
LIGHT = {"to", "a", "an", "the", "of", "in", "on", "at", "for", "with", "be", "have", "take", "make", "get",
         "do", "go", "give", "put", "keep", "one", "someone", "something", "oneself", "s"}


def final(probabilities: dict, choice: str) -> str:
    """The release rule: NONE only at P(NONE) >= 0.8, else the best real sense."""
    if (probabilities or {}).get("NONE", 0) >= 0.8:
        return "NONE"
    real = {k: v for k, v in (probabilities or {}).items() if k != "NONE"}
    return max(real, key=real.get) if real else choice


def content(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower())) - LIGHT


rows, stats = [], Counter()
for provider, folder in SETS.items():
    before = {}
    with open(folder / f"answers-{provider}.jsonl", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            before[r["sentence_id"]] = final(r.get("probabilities"), r["choice"])
    items = json.loads((OUT / f"requests-{provider}.json").read_text(encoding="utf-8"))
    for item in items:
        path = OUT / f"responses-{provider}" / f"{item['card_id']}.json"
        if not path.exists():
            stats["missing_card"] += 1
            continue
        answers = json.loads(path.read_text(encoding="utf-8")).get("answers") or {}
        menu = item["body"]["state"]["menu"]
        label = lambda c: "NONE" if c == "NONE" or c not in menu else f"{menu[c]['headword']}: {menu[c]['translation'][:48]}"
        for sid in item["ids"]:
            a = answers.get(sid)
            if not a:
                stats["missing_sentence"] += 1
                continue
            b, w = before.get(sid, "NONE"), final(a.get("probabilities"), a.get("choice"))
            if b != "NONE" and b not in menu:
                stats["before answer off this menu"] += 1
                continue
            took = w in menu and menu[w]["pos"] == "PHRASE" and menu[w]["headword"] in item["offers"][sid]
            if not took:
                kind = "not chosen" if b == w else "changed, no expression"
            elif b == "NONE":
                kind = "was NONE"
            elif content(menu[b]["translation"]) & content(menu[w]["translation"]):
                kind = "relabel"
            else:
                kind = "meaning corrected"
            stats[kind] += 1
            rows.append({"provider": provider, "card": item["surface"], "kind": kind, "offers": item["offers"][sid],
                         "sentence": item["body"]["state"]["sentences"][sid],
                         "english": (item["body"]["state"].get("sentence_translations") or {}).get(sid),
                         "before": label(b), "after": label(w)})
by_expr = defaultdict(Counter)
for r in rows:
    if r["kind"] in ("was NONE", "meaning corrected", "relabel"):
        by_expr[r["after"].split(":")[0]][r["kind"]] += 1
(OUT / "comparison.json").write_text(json.dumps({"stats": stats, "rows": rows}, ensure_ascii=False, indent=1))
print(dict(stats))
print("top expressions taken:", sorted(((e, dict(c)) for e, c in by_expr.items()), key=lambda x: -sum(x[1].values()))[:25])
