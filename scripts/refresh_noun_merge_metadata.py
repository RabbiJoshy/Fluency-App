#!/usr/bin/env python3
"""Recover noun evidence into a separate copy of a release's original menu.

No senses, references, examples or display translations are rewritten. Fresh
evidence is accepted only for an exactly matching complete dictionary menu.
Unmatched evidence or release references block the entire candidate group.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

from fluency.core.hashing import canonical_content_id, file_content_id
from fluency.features.spanishdict import extract
from fluency.sense_menu.noun_merge import is_noun, stamp_noun_merge


def lexical(card):
    return [a for a in card.get("analyses", [])
            if str(a.get("part_of_speech", "")).lower() not in {"mwe", "clitic"}]


def leaves(card):
    return {(a["headword"], a["part_of_speech"].lower(), s["source_reference"]): (a, s)
            for a in lexical(card) for s in a["senses"]}


def meaning_signature(sense):
    features = sense.get("specialist_features") or sense.get("metadata", {}).get("features") or []
    return (sense["translation"], sense.get("definition", ""),
            tuple(sorted({canonical_content_id(f) for f in features if f.get("kind") != "surface_mark"})))


def refresh_wiktionary(card, fresh):
    if fresh is None:
        return "missing_fresh_menu"
    old, new = leaves(card), leaves(fresh)
    if old.keys() != new.keys() or any(meaning_signature(s) != meaning_signature(new[k][1]) for k, (_, s) in old.items()):
        return "fresh_menu_mismatch"
    # Populate only after the whole menu has passed the comparison.
    for key, (_, sense) in old.items():
        provider = new[key][1].get("provider_metadata", {})
        if "entry_tags" not in provider:
            return "missing_entry_tags"
    for key, (_, sense) in old.items():
        sense.setdefault("provider_metadata", {})["entry_tags"] = new[key][1]["provider_metadata"]["entry_tags"]
    for analysis in lexical(card):
        matches = [a for a in lexical(fresh) if (a["headword"], a["part_of_speech"]) ==
                   (analysis["headword"], analysis["part_of_speech"])]
        if len(matches) == 1:
            for field in ("resolution", "surface_grammar"):
                if field in matches[0].get("provider_metadata", {}):
                    analysis.setdefault("provider_metadata", {})[field] = matches[0]["provider_metadata"][field]
    return None


def sd_key(headword, translation, context, regions):
    return (headword, translation, context, tuple(sorted(set(regions))))


def refresh_spanishdict(card, response):
    if not response or response.get("flags") or response.get("entry_lang") != "es":
        return "missing_or_rejected_response"
    originals = {}
    for analysis in lexical(card):
        if not is_noun(analysis["part_of_speech"]):
            return "multiple_dictionary_entries"
        for sense in analysis["senses"]:
            provider = sense.get("provider_metadata", {})
            regions = provider.get("spanishdict", {}).get("regions", provider.get("regions", []))
            key = sd_key(analysis["headword"], sense["translation"], provider.get("context", sense.get("definition", "")), regions)
            originals.setdefault(key, []).append(sense)
    fresh = {}
    for row in response.get("analyses", []):
        label = row.get("part_of_speech_label")
        if not label or not is_noun(label) or not row.get("headword"):
            return "fresh_other_entry_or_missing_label"
        key = sd_key(row["headword"], row["translation"], row.get("context", ""), row.get("regions", []))
        fresh.setdefault(key, []).append(row)
    if not fresh or originals.keys() != fresh.keys():
        return "fresh_menu_mismatch"
    for key, senses in originals.items():
        labels = {row["part_of_speech_label"] for row in fresh[key]}
        if len(labels) != 1:
            return "ambiguous_sense_label"
    for key, senses in originals.items():
        row = fresh[key][0]
        for sense in senses:
            sense.setdefault("provider_metadata", {}).setdefault("spanishdict", {})["part_of_speech_label"] = row["part_of_speech_label"]
            # Preserve all original features and append newly recovered number restrictions.
            number_features = [f.to_dict() for f in extract(row) if f.value.startswith("number=")]
            features = sense.setdefault("specialist_features", [])
            features.extend(f for f in number_features if f not in features)
    for analysis in lexical(card):
        relations = [r for r in response.get("possible_results", []) if isinstance(r, dict)
                     and r.get("headword") == analysis["headword"] and r.get("heuristic") == "inflection"]
        types = [r["inflection_type"] for r in relations if r.get("inflection_type")]
        provider = analysis.setdefault("provider_metadata", {}).setdefault("spanishdict", {})
        provider["inflection_types"] = types
        provider["declared_plural"] = any("plural" in t.lower().split() for t in types)
    return None


def refresh(source, rows, *, fresh=None, responses=None):
    result = copy.deepcopy(source)
    failures = {}
    fresh_by_surface = {c["surface_form"]: c for c in fresh["cards"]} if fresh else {}
    if fresh and fresh["language"] != source["language"]:
        raise ValueError("fresh and original menus have different languages")
    by_id = {r["surface_card_id"]: r for r in rows}
    for card in result["cards"]:
        card.pop("noun_merge", None)
        row = by_id.get(card["card_id"])
        if row is None or row["word"] != card["surface_form"]:
            raise ValueError("original menu does not match the release's surfaces")
        if not any(is_noun(a["part_of_speech"]) for a in lexical(card)):
            continue
        reason = (refresh_wiktionary(card, fresh_by_surface.get(card["surface_form"])) if fresh
                  else refresh_spanishdict(card, (responses or {}).get(card["surface_form"])))
        if reason:
            failures[card["surface_form"]] = reason
        senses = [*row.get("meanings", []), *row.get("unused_menu_senses", [])]
        senses.extend(s for m in row.get("meanings", []) for s in m.get("allSenses", []))
        references = {s["source_reference"] for s in senses if s.get("source_reference") and s["source_reference"] != "mwe-merged/v1"}
        menu_references = {s["source_reference"] for a in card["analyses"] for s in a["senses"]}
        if references != menu_references:
            failures[card["surface_form"]] = "release_menu_mismatch"
    # A mismatch at either end invalidates every participant in its group.
    blocked = {}
    for card in result["cards"]:
        if card["surface_form"] in failures:
            for analysis in lexical(card):
                if is_noun(analysis["part_of_speech"]):
                    blocked[analysis["headword"].casefold()] = failures[card["surface_form"]]
    for card in result["cards"]:
        heads = {a["headword"].casefold() for a in lexical(card) if is_noun(a["part_of_speech"])}
        reasons = [blocked[head] for head in sorted(heads) if head in blocked]
        if reasons:
            card["noun_merge_refresh_failure"] = reasons[0]
    stamp_noun_merge(result["cards"])
    report = {"surface_failures": failures, "verdict_counts": dict(Counter(
        c["noun_merge"]["reason"] for c in result["cards"] if "noun_merge" in c))}
    return result, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-menu", type=Path, required=True)
    parser.add_argument("--release-index", type=Path, required=True)
    evidence = parser.add_mutually_exclusive_group(required=True)
    evidence.add_argument("--fresh-menu", type=Path)
    evidence.add_argument("--spanishdict-evidence", type=Path)
    parser.add_argument("--out-menu", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.out_menu.resolve() in {args.source_menu.resolve(), args.release_index.resolve()}:
        parser.error("output must not replace the original menu or release")
    source = json.loads(args.source_menu.read_text())
    rows = json.loads(args.release_index.read_text())
    fresh = json.loads(args.fresh_menu.read_text()) if args.fresh_menu else None
    responses = {r["word"]: r for line in args.spanishdict_evidence.read_text().splitlines()
                 if (r := json.loads(line))} if args.spanishdict_evidence else None
    result, report = refresh(source, rows, fresh=fresh, responses=responses)
    provenance = {"source_menu": file_content_id(args.source_menu),
                  "release_index": file_content_id(args.release_index),
                  "evidence": file_content_id(args.fresh_menu or args.spanishdict_evidence)}
    result["noun_merge_refresh"] = provenance
    report["provenance"] = provenance
    args.out_menu.parent.mkdir(parents=True, exist_ok=True)
    args.out_menu.write_text(json.dumps(result, ensure_ascii=False))
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["verdict_counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
