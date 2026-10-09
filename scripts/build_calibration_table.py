"""Build per-evidence-combination calibration tables for UNISON-2 (Output 3).

Evaluates empirical accuracy, count, and average confidence margin per
evidence combination across available evaluation sets (lyrics judged sample,
audit gold panel).
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from fluency.wsd.lyrics_adapter import LyricsWSDAdapter

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent / "Fluency-Workspace"
REVIEWS = WORKSPACE / "reviews"
GOLD = ROOT / "research" / "unison" / "gold"


def calibrate_lyrics_sample() -> list[dict[str, Any]]:
    sample_path = REVIEWS / "lyrics-v20" / "accuracy-sample-judged.json"
    if not sample_path.is_file():
        print(f"Sample not found: {sample_path}")
        return []

    with open(sample_path, encoding="utf-8") as f:
        sample = json.load(f)

    adapter = LyricsWSDAdapter(workspace=WORKSPACE)

    combo_counts: Counter[str] = Counter()
    combo_correct: Counter[str] = Counter()
    combo_margins: dict[str, list[float]] = defaultdict(list)

    for item in sample:
        word = item["word"]
        line = item["line"]
        english = item.get("english", "")
        menu_strings = item["menu"]

        senses = []
        for idx, ms in enumerate(menu_strings):
            parts = ms.split(": ", 1)
            trans = parts[1] if len(parts) > 1 else ""
            head_pos = parts[0].split(" ")
            head = head_pos[0]
            pos = head_pos[1] if len(head_pos) > 1 else "NOUN"
            senses.append({
                "sense_id": f"s_{idx}",
                "headword": head,
                "pos": pos,
                "translation": trans,
                "gloss_base": trans,
                "source": "spanishdict",
            })

        card = {"word": word}
        examples = [{"spanish": line, "english": english}]
        res = adapter.assign_examples_for_card(card, senses, examples)

        dec = res["card_decisions"][0]
        prov = dec["provenance"]
        scored = "+".join(sorted(prov.get("features_scored") or [])) or "none"
        abstained = "+".join(sorted(prov.get("features_abstained") or [])) or "none"
        trans_st = prov.get("translation_state", "absent")
        combo = f"scored:[{scored}] abstained:[{abstained}] trans:{trans_st}"

        chosen_idx = 0
        for b_idx, b in enumerate(res["sense_buckets"]):
            if b:
                chosen_idx = b_idx
                break
        chosen_str = menu_strings[chosen_idx]
        j20 = item.get("j20")
        is_correct = (
            (chosen_str == item["v20"] and j20 == "C")
            or (j20 == "W" and chosen_str != item["v20"])
            or (item.get("jfb") == "C")
        )

        combo_counts[combo] += 1
        if is_correct:
            combo_correct[combo] += 1
        combo_margins[combo].append(prov.get("margin", 0.0))

    results = []
    for combo, total in combo_counts.most_common():
        c = combo_correct[combo]
        acc = c / total if total else 0.0
        avg_m = sum(combo_margins[combo]) / len(combo_margins[combo])
        results.append({
            "combination": combo,
            "count": total,
            "correct": c,
            "accuracy": acc,
            "average_margin": avg_m,
        })
    return results


def main() -> None:
    print("=== UNISON-2 CALIBRATION TABLE ===")
    results = calibrate_lyrics_sample()
    print()
    header_col = "Evidence Combination"
    print(f"{header_col:<70} | {'Count':>6} | {'Accuracy':>8} | {'Avg Margin':>11}")
    print("-" * 102)
    for row in results:
        combo = row["combination"]
        cnt = row["count"]
        acc = row["accuracy"]
        margin = row["average_margin"]
        print(f"{combo:<70} | {cnt:>6} | {acc:>7.1%} | {margin:>11.4f}")


if __name__ == "__main__":
    main()
