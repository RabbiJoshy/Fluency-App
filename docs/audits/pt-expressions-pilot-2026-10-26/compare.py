"""Compare baseline vs with-expressions Jev answers for the pilot cards."""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent / "responses"
rows, stats = [], Counter()
for plan_path in sorted(HERE.glob("*-plan.json")):
    surface = plan_path.name[:-len("-plan.json")]
    plan = json.loads(plan_path.read_text())
    menu = plan["menu"]
    base = json.loads((HERE / f"{surface}-baseline.json").read_text())["answers"]
    new = json.loads((HERE / f"{surface}-with.json").read_text())["answers"]
    matched = {sid: e for e, sids in plan["matched"].items() for sid in sids}
    label = lambda c: "NONE" if c == "NONE" else f"{menu[c]['headword']}: {menu[c]['translation'][:38]}"
    for sid, text in plan["sentences"].items():
        b, w = base.get(sid, {}).get("choice"), new.get(sid, {}).get("choice")
        if b is None or w is None:
            stats["missing"] += 1
            continue
        took = w != "NONE" and menu[w]["pos"] == "PHRASE"
        kind = "matched" if sid in matched else "unmatched"
        stats[f"{kind}:{'changed' if b != w else 'same'}"] += 1
        if sid in matched:
            stats["matched:expression_chosen"] += took
        rows.append({"card": surface, "kind": kind, "expr": matched.get(sid), "sentence": text,
                     "english": (plan.get("translations") or {}).get(sid), "before": label(b), "after": label(w),
                     "conf": new[sid].get("confidence")})
(HERE.parent / "comparison.json").write_text(json.dumps({"stats": stats, "rows": rows}, ensure_ascii=False, indent=1))
print(dict(stats))
