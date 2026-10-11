"""Tally research/literal-ground/labels.jsonl: every row v25 changed, hand-judged.

verdict: after = only v25 right; before = only v24 right; same = both
acceptable (often the same English on the card); neither = both wrong.
"""
from collections import Counter
import json
from pathlib import Path

rows = [json.loads(line) for line in (Path(__file__).parent / "labels.jsonl").open()]
groups: dict[tuple[str, str], Counter] = {}
for row in rows:
    groups.setdefault((row["track"], row["language"]), Counter())[row["verdict"]] += 1
print(f"{'track':8} {'lang':4} {'rows':>4} {'after':>5} {'before':>6} {'same':>4} {'neither':>7}")
for (track, lang), c in sorted(groups.items()):
    print(f"{track:8} {lang:4} {sum(c.values()):>4} {c['after']:>5} {c['before']:>6} {c['same']:>4} {c['neither']:>7}")
visible = [row for row in rows if row["card_text_changed"]]
c = Counter(row["verdict"] for row in visible)
print(f"\nrows whose card English changed: {len(visible)}  after {c['after']}  before {c['before']}  same {c['same']}  neither {c['neither']}")
for row in rows:
    if row["verdict"] == "before":
        print(f"  worse: [{row['language']} {row['surface']}] {row['sentence']}  {row['before']} -> {row['after']}")
