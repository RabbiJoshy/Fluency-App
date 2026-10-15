"""Store explicit, sentence-reviewed annotations independently of predictions.

Annotation batches are authored by the reviewer after reading blind rows.
This utility only joins IDs; it does not infer any label from text or a parser.
"""
import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[3] / "Fluency-Workspace/audits/hinge-20261014"


def record(groups, *, split="development"):
    source = {r["review_id"]: r for r in map(json.loads, (AUDIT / f"blind-{split}.jsonl").read_text().splitlines())}
    path = AUDIT / f"gold-{split}.jsonl"
    existing = {r["review_id"]: r for r in map(json.loads, path.read_text().splitlines())} if path.exists() else {}
    for ids, accepted, meaning, reason in groups:
        for identifier in ids:
            row = dict(source[identifier])
            row.update({"target_span": row["spans"][0] if row["spans"] else None,
                        "accepted": accepted, "meaning": meaning, "reason": reason,
                        "reviewer": "Codex", "review_method": "sentence read before predictions", "split": split})
            if identifier in existing:
                raise ValueError(f"Duplicate annotation: {identifier}")
            existing[identifier] = row
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for _, r in sorted(existing.items())))
    print(f"{split}: {len(existing)} independently annotated rows")
