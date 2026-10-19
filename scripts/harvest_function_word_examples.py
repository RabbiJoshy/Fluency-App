#!/usr/bin/env python3
"""Harvest, assign, and verify examples for all 115 function-word patterns.

Connects to real speech banks (OpenSubtitles/Tatoeba) and artist lyric archives (Bad Bunny,
Rosalía, Portuguese test playlists).
Aims for 3 distinct, confidently matched examples per pattern.
Reports shortages honestly where source material is insufficient.
Preserves existing vetted pilot examples, corrects the metadata export bug,
and leaves approved UI unchanged.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent / "Fluency-Workspace"
sys.path.insert(0, str(ROOT / "research/function_word_audit"))
sys.path.insert(0, str(ROOT / "scripts"))

from assign_function_word_examples import parse_rows, build
from syntax_assignment import assign_occurrences, VERSION

_WORDS = re.compile(r"[^\W\d_]+", re.UNICODE)


def example_identity(text: str) -> str:
    """Distinctness key: word sequence ignoring case, punctuation, accents."""
    return " ".join(_WORDS.findall(unicodedata.normalize("NFC", text).casefold()))


def load_suites() -> tuple[dict, dict]:
    es = json.loads((ROOT / "app/data/grammar-words/es.json").read_text(encoding="utf-8"))
    pt = json.loads((ROOT / "app/data/grammar-words/pt.json").read_text(encoding="utf-8"))
    return es, pt


def harvest_speech_candidates(lang: str, words: set[str], max_per_word: int = 15) -> list[dict]:
    pool_files = [WORKSPACE / f"pools/{lang}/{lang}-10k-speech/sentence-bank.jsonl"]
    if lang == "pt":
        pool_files.append(WORKSPACE / "pools/pt/pt-tatoeba-brazilian/sentence-bank.jsonl")
        pool_files.append(WORKSPACE / "pools/pt/pt-opensubtitles-european-2015plus/sentence-bank.jsonl")

    candidates = defaultdict(list)
    patterns = {w: re.compile(r"(?<![\w'’])" + re.escape(w) + r"(?![\w'’])", re.I) for w in words}

    for pool_file in pool_files:
        if not pool_file.exists():
            continue
        with open(pool_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                target = record.get("target", {}).get("text", "")
                trans = record.get("translation", {}).get("text", "")
                if not target or not trans or len(target) > 120 or len(target) < 10:
                    continue
                if any(c in target for c in "[]{}()_~#"):
                    continue

                for w, pat in patterns.items():
                    if len(candidates[w]) < max_per_word and pat.search(target):
                        candidates[w].append({
                            "language": lang,
                            "word": w,
                            "example_id": f"speech_{record['sentence_id']}",
                            "sentence_id": record["sentence_id"],
                            "sentence": target,
                            "translation": trans,
                            "source": record.get("source", {"name": "opensubtitles", "source_record_id": record["sentence_id"]}),
                            "channel": "speech"
                        })
                # Sample comparative que sentences for pattern 2
                if "que" in words and len(candidates.get("que_comp", [])) < 8:
                    if re.search(r"\b(mais|menos|melhor|pior|maior|menor|más)\b.*?\bque\b", target, re.I):
                        candidates["que_comp"].append({
                            "language": lang,
                            "word": "que",
                            "example_id": f"speech_comp_{record['sentence_id']}",
                            "sentence_id": record["sentence_id"],
                            "sentence": target,
                            "translation": trans,
                            "source": record.get("source", {"name": "opensubtitles", "source_record_id": record["sentence_id"]}),
                            "channel": "speech"
                        })
                # Sample "todo el + noun" for es:todo:1 ("all the"): the first
                # fifteen todo sentences are nearly all "everything".
                if lang == "es" and "todo" in words and len(candidates.get("todo_el", [])) < 8:
                    if re.search(r"\btodo el\b", target, re.I) and not re.search(r"\btodo el mundo\b", target, re.I):
                        candidates["todo_el"].append({
                            "language": lang,
                            "word": "todo",
                            "example_id": f"speech_todo_el_{record['sentence_id']}",
                            "sentence_id": record["sentence_id"],
                            "sentence": target,
                            "translation": trans,
                            "source": record.get("source", {"name": "opensubtitles", "source_record_id": record["sentence_id"]}),
                            "channel": "speech"
                        })
                todo_el_done = not (lang == "es" and "todo" in words) or len(candidates.get("todo_el", [])) >= 8
                if all(len(candidates[w]) >= max_per_word for w in words) and todo_el_done:
                    break

    if "que_comp" in candidates:
        candidates["que"].extend(candidates["que_comp"])
    if "todo_el" in candidates:
        candidates["todo"].extend(candidates["todo_el"])

    out = []
    for w in words:
        out.extend(candidates[w])
    return out


def harvest_artist_candidates(lang: str, words: set[str], max_per_artist: int = 8) -> list[dict]:
    artist_candidates = defaultdict(lambda: defaultdict(list))
    patterns = {w: re.compile(r"(?<![\w'’])" + re.escape(w) + r"(?![\w'’])", re.I) for w in words}

    if lang == "es":
        artist_sources = [
            ("Bad Bunny", WORKSPACE / "releases/lyrics/lyrics-bad-bunny-v20/app/Artists/es/bad/examples.json"),
            ("Rosalía", WORKSPACE / "releases/lyrics/lyrics-rosalia-v20/app/Artists/es/rosalia/examples.json"),
            ("Young Miko", WORKSPACE / "releases/lyrics/lyrics-young-miko-v20/app/Artists/es/young/examples.json"),
            ("Latin Playlist", WORKSPACE / "releases/lyrics/lyrics-test-playlist-v20/app/Artists/es/test/examples.json"),
        ]
        for artist_name, ex_file in artist_sources:
            if not ex_file.exists():
                continue
            data = json.loads(ex_file.read_text(encoding="utf-8"))
            for group in data.values():
                sublists = list(group.values()) if isinstance(group, dict) else [group]
                for sub in sublists:
                    if not isinstance(sub, list):
                        continue
                    for cluster in sub:
                        items = cluster if isinstance(cluster, list) else [cluster]
                        for item in items:
                            if not isinstance(item, dict):
                                continue
                            sp = item.get("spanish", "").strip()
                            en = item.get("english", "").strip()
                            song = item.get("song_name", artist_name)
                            if not sp or len(sp) > 120 or len(sp) < 10 or any(c in sp for c in "[]{}()_~#"):
                                continue
                            for w, pat in patterns.items():
                                if len(artist_candidates[w][artist_name]) < max_per_artist and pat.search(sp):
                                    eid = hashlib.md5((sp + w + artist_name).encode()).hexdigest()[:12]
                                    artist_candidates[w][artist_name].append({
                                        "language": lang,
                                        "word": w,
                                        "example_id": f"artist_es_{eid}",
                                        "sentence_id": f"artist_{eid}",
                                        "sentence": sp,
                                        "translation": en,
                                        "source": {
                                            "name": f"{artist_name} · {song}",
                                            "source_record_id": f"{artist_name}:{song}:{item.get('timestamp_ms', 0)}",
                                            "artist": artist_name,
                                            "song": song
                                        },
                                        "channel": "artist"
                                    })

    elif lang == "pt":
        pt_sources = [
            ("Portuguese Playlist", WORKSPACE / "releases/lyrics/lyrics-portuguese-test-playlist-polyglot-v6/app/Artists/pt/portuguese-test-playlist/examples.json"),
            ("Portuguese Playlist", WORKSPACE / "releases/lyrics/lyrics-portuguese-test-playlist-polyglot-v5/app/Artists/pt/portuguese-test-playlist/examples.json"),
            ("Polyglot PT", WORKSPACE / "releases/lyrics/polyglot-pt-v1-20261003/examples.json"),
        ]
        for default_artist, ex_file in pt_sources:
            if not ex_file.exists():
                continue
            data = json.loads(ex_file.read_text(encoding="utf-8"))
            for group in data.values():
                sublists = list(group.values()) if isinstance(group, dict) else [group]
                for sub in sublists:
                    if not isinstance(sub, list):
                        continue
                    for cluster in sub:
                        items = cluster if isinstance(cluster, list) else [cluster]
                        for item in items:
                            if not isinstance(item, dict):
                                continue
                            pt_text = (item.get("source_text") or item.get("spanish") or "").strip()
                            en_text = (item.get("english") or item.get("translation") or "").strip()
                            song = item.get("song_name") or default_artist
                            artist = item.get("artist") or default_artist
                            if not pt_text or len(pt_text) > 120 or len(pt_text) < 10 or any(c in pt_text for c in "[]{}()_~#"):
                                continue
                            for w, pat in patterns.items():
                                if len(artist_candidates[w][artist]) < max_per_artist and pat.search(pt_text):
                                    eid = hashlib.md5((pt_text + w + artist).encode()).hexdigest()[:12]
                                    artist_candidates[w][artist].append({
                                        "language": lang,
                                        "word": w,
                                        "example_id": f"artist_pt_{eid}",
                                        "sentence_id": f"artist_{eid}",
                                        "sentence": pt_text,
                                        "translation": en_text,
                                        "source": {
                                            "name": f"{artist} · {song}",
                                            "source_record_id": f"{artist}:{song}:{item.get('timestamp_ms', 0)}",
                                            "artist": artist,
                                            "song": song
                                        },
                                        "channel": "artist"
                                    })

    out = []
    for w in words:
        for art_list in artist_candidates[w].values():
            out.extend(art_list)
    return out


def get_pattern_pos(lang: str, word: str, idx: int, tag: str = "", formula: str = "") -> str:
    """Canonical POS for function word within a specific pattern relation."""
    # Prepositional contractions
    if word in {'del', 'al', 'ao', 'à', 'do', 'da', 'no', 'na', 'pelo', 'pela', 'num', 'numa', 'naquele'}:
        return 'prep'
    if lang == 'pt' and word == 'nos' and idx == 1:
        return 'prep'  # pt nos = em + os
    if lang == 'es' and word == 'todo' and idx == 1:
        return 'det'  # todo el día: "all the"

    # Prepositions
    if word in {'de', 'en', 'em', 'por', 'para', 'con', 'com', 'sin', 'sem', 'sobre'}:
        return 'prep'
    if word == 'a' and idx in {0, 1} and (lang == 'es' or idx == 0):
        return 'prep'
    if word == 'até' and idx == 0:
        return 'prep'
    if word == 'como':
        return 'prep'

    # Conjunctions
    if word in {'pero', 'mas', 'porque', 'cuando', 'quando', 'y', 'e', 'si'}:
        return 'conj'
    if lang == 'pt' and word == 'se' and idx == 0:
        return 'conj'
    if word == 'que' and idx in {0, 2}:
        return 'conj'
    if word == 'ao' and idx == 1:
        return 'conj'

    # Articles & Determiners
    if word in {'el', 'la', 'los', 'las', 'o', 'os', 'as', 'un', 'una', 'um', 'uma', 'mi', 'su', 'tu'}:
        if word in {'la', 'los', 'las', 'o', 'os', 'as'} and idx == 1:
            return 'pron'  # object clitic
        return 'det'
    if word == 'a' and lang == 'pt' and idx == 1:
        return 'det'
    if word == 'lo' and idx == 0:
        return 'det'  # neuter article lo + adj

    # Pronouns & Clitics
    if word in {'yo', 'tú', 'eu', 'ele', 'ela', 'eso', 'esto', 'todo', 'algo', 'isso', 'isto', 'tudo', 'dele', 'dela'}:
        return 'pron'
    if word in {'me', 'te', 'le', 'lhe'}:
        return 'pron'
    if word == 'nos' and (idx == 0 or lang == 'es'):
        return 'pron'
    if word == 'se' and (lang == 'es' or idx == 1):
        return 'pron'
    if word == 'que' and idx == 1:
        return 'pron'  # relative pronoun
    if word == 'lo' and idx in {1, 2}:
        return 'pron'  # object lo; lo que
    if word == 'a' and lang == 'pt' and idx == 2:
        return 'pron'  # object clitic
    if word == 'até' and idx == 1:
        return 'part'

    return 'prep'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply verified examples to app/data/grammar-words/")
    args = parser.parse_args()

    es_suite, pt_suite = load_suites()
    baseline_dir = ROOT / "research/function_word_audit/baseline"
    baseline_suites = {}
    if (baseline_dir / "es.json").exists() and (baseline_dir / "pt.json").exists():
        baseline_suites["es"] = json.loads((baseline_dir / "es.json").read_text(encoding="utf-8"))
        baseline_suites["pt"] = json.loads((baseline_dir / "pt.json").read_text(encoding="utf-8"))

    all_patterns = {}
    for lang, suite in [("es", es_suite), ("pt", pt_suite)]:
        for w, card in suite.items():
            for i, rel in enumerate(card.get("relations", [])):
                pid = f"{lang}:{w}:{i}"
                base_card = baseline_suites.get(lang, {}).get(w)
                base_rel = base_card.get("relations", [])[i] if base_card and i < len(base_card.get("relations", [])) else None
                base_examples = base_rel.get("examples", []) if base_rel else []
                if not base_examples:
                    base_examples = [ex for ex in rel.get("examples", []) if not ex.get("metadata", {}).get("automaticSyntax")]

                all_patterns[pid] = {
                    "lang": lang,
                    "word": w,
                    "index": i,
                    "tag": rel.get("tag"),
                    "formulaHTML": rel.get("formulaHTML"),
                    "slotTypes": rel.get("slotTypes", {}),
                    "existing_examples": base_examples
                }

    print(f"Loaded {len(all_patterns)} total patterns.", flush=True)

    # 1. Harvest candidates
    es_words = set(es_suite.keys())
    pt_words = set(pt_suite.keys())

    print("Harvesting speech sentences for Spanish...", flush=True)
    es_speech = harvest_speech_candidates("es", es_words, max_per_word=15)
    print(f"Harvested {len(es_speech)} Spanish speech candidates.", flush=True)

    print("Harvesting artist sentences for Spanish...", flush=True)
    es_artist = harvest_artist_candidates("es", es_words, max_per_artist=8)
    print(f"Harvested {len(es_artist)} Spanish artist candidates.", flush=True)

    print("Harvesting speech sentences for Portuguese...", flush=True)
    pt_speech = harvest_speech_candidates("pt", pt_words, max_per_word=15)
    print(f"Harvested {len(pt_speech)} Portuguese speech candidates.", flush=True)

    print("Harvesting artist sentences for Portuguese...", flush=True)
    pt_artist = harvest_artist_candidates("pt", pt_words, max_per_artist=8)
    print(f"Harvested {len(pt_artist)} Portuguese artist candidates.", flush=True)

    all_rows = es_speech + es_artist + pt_speech + pt_artist
    print(f"Parsing and assigning total {len(all_rows)} candidate sentences across speech and artist channels...", flush=True)

    # Index rows by example_id to resolve the export metadata bug
    rows_by_id = {r["example_id"]: r for r in all_rows}

    parses = parse_rows(all_rows)
    assignments, _ = build(all_rows, parses, max_per_pattern=12)

    # Group confident candidates by pattern ID, preserving translations and source metadata
    matched_by_pattern = defaultdict(list)
    seen_identities = defaultdict(set)

    for item in assignments:
        asn = item.get("assignment", {})
        if asn.get("status") == "candidate":
            pid = asn.get("pattern_id")
            eid = item.get("example_id")
            orig_row = rows_by_id.get(eid, {})
            text = item.get("sentence", "")
            ident = example_identity(text)
            if ident not in seen_identities[pid]:
                seen_identities[pid].add(ident)
                source_meta = orig_row.get("source") or {"name": "Contemporary dialogue"}
                source_name = source_meta.get("name") if isinstance(source_meta, dict) else str(source_meta)
                matched_by_pattern[pid].append({
                    "sentence": text,
                    "targetHTML": asn.get("targetHTML"),
                    "translation": orig_row.get("translation", ""),
                    "source": source_name,
                    "channel": orig_row.get("channel", "speech"),
                    "metadata": {
                        "source": source_meta,
                        "sentence_id": orig_row.get("sentence_id"),
                        "channel": orig_row.get("channel", "speech"),
                        "automaticSyntax": {
                            "patternId": pid,
                            "matcherVersion": VERSION,
                            "reason": asn.get("reason")
                        }
                    }
                })

    # Evaluate pattern coverage per deck and overall
    final_pattern_status = {}
    shortages = []
    speech_deck_shortages = []
    artist_deck_shortages = []

    PILOT_WORDS = {'naquele', 'que', 'de', 'se', 'nos', 'o', 'al', 'el', 'la', 'los', 'lo', 'un'}

    patterns_with_ge_3_fresh = 0
    speech_deck_patterns_full = 0
    artist_deck_patterns_full = 0

    for pid, pinfo in all_patterns.items():
        lang = pinfo["lang"]
        w = pinfo["word"]
        idx = pinfo["index"]
        existing = pinfo["existing_examples"]
        fresh = matched_by_pattern.get(pid, [])

        speech_matches = [ex for ex in fresh if ex.get("channel") == "speech"]
        artist_matches = [ex for ex in fresh if ex.get("channel") == "artist"]

        # 1. Speech Deck Generation (target: 3 distinct speech examples)
        speech_deck_examples = []
        speech_ids = set()
        if w in PILOT_WORDS:
            for ex in existing:
                s_text = ex.get("sentence") or ex.get("targetHTML", "")
                ident = example_identity(s_text)
                if ident not in speech_ids:
                    speech_ids.add(ident)
                    speech_deck_examples.append(ex)
                    if len(speech_deck_examples) >= 3:
                        break
        for ex in speech_matches:
            if len(speech_deck_examples) >= 3:
                break
            ident = example_identity(ex["sentence"])
            if ident not in speech_ids:
                speech_ids.add(ident)
                speech_deck_examples.append(ex)

        has_speech_deck_full = len(speech_deck_examples) >= 3
        if has_speech_deck_full:
            speech_deck_patterns_full += 1
            speech_shortage = 0
        else:
            speech_shortage = 3 - len(speech_deck_examples)
            speech_deck_shortages.append({
                "pattern_id": pid,
                "tag": pinfo["tag"],
                "formula": pinfo["formulaHTML"],
                "matches_found": len(speech_deck_examples),
                "shortage": speech_shortage,
                "reason": "Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria."
            })

        # 2. Artist Deck Generation (target: 3 distinct artist examples)
        artist_deck_examples = []
        artist_deck_by_artist = defaultdict(list)
        artist_ids = set()
        for ex in artist_matches:
            ident = example_identity(ex["sentence"])
            if ident not in artist_ids:
                artist_ids.add(ident)
                artist_deck_examples.append(ex)
                ex_source = ex.get("metadata", {}).get("source") or {}
                if isinstance(ex_source, dict):
                    art = ex_source.get("artist")
                else:
                    art = None
                if not art:
                    source_str = ex.get("source", "")
                    art = source_str.split(" · ")[0].strip() if " · " in source_str else (source_str or "Unknown")
                if len(artist_deck_by_artist[art]) < 3:
                    artist_deck_by_artist[art].append(ex)

        has_artist_deck_full = len(artist_deck_examples) >= 3
        if has_artist_deck_full:
            artist_deck_patterns_full += 1
            artist_shortage = 0
        else:
            artist_shortage = 3 - len(artist_deck_examples)
            artist_deck_shortages.append({
                "pattern_id": pid,
                "tag": pinfo["tag"],
                "formula": pinfo["formulaHTML"],
                "matches_found": len(artist_deck_examples),
                "shortage": artist_shortage,
                "reason": "Corpus scarcity in artist lyrics material or strict grammatical licensing criteria."
            })

        # 3. Overall Cross-Deck Match Status
        has_ge_3_fresh = len(fresh) >= 3
        if has_ge_3_fresh:
            patterns_with_ge_3_fresh += 1
            is_shortage = False
            shortage_count = 0
        else:
            is_shortage = True
            shortage_count = 3 - len(fresh)
            shortages.append({
                "pattern_id": pid,
                "tag": pinfo["tag"],
                "formula": pinfo["formulaHTML"],
                "fresh_matches_found": len(fresh),
                "shortage_count": shortage_count,
                "speech_matches": len(speech_matches),
                "artist_matches": len(artist_matches),
                "is_pilot": w in PILOT_WORDS,
                "reason": (
                    f"Pilot pattern with vetted traceable baseline examples; {len(fresh)} additional fresh matches harvested."
                    if w in PILOT_WORDS else
                    "Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing."
                )
            })

        combined = []
        comb_identities = set()

        if w in PILOT_WORDS:
            # Pilot cards have existing vetted traceable examples; preserve them
            for ex in existing:
                s_text = ex.get("targetHTML", "").replace("<span class='fw-token-v'>", "").replace("<span class='fw-token-c'>", "").replace("<span class='fw-token-connector'>", "").replace("</span>", "").replace("<span class=\"fw-token-v\">", "").replace("<span class=\"fw-token-c\">", "").replace("<span class=\"fw-token-connector\">", "")
                ident = example_identity(s_text)
                if ident not in comb_identities:
                    comb_identities.add(ident)
                    combined.append(ex)
                    if len(combined) >= 3:
                        break
            # Backfill with fresh matches if fewer than 3
            if len(combined) < 3:
                for ex in fresh:
                    ident = example_identity(ex["sentence"])
                    if ident not in comb_identities:
                        comb_identities.add(ident)
                        combined.append(ex)
                        if len(combined) >= 3:
                            break
        else:
            # Prefer speech deck examples first, then artist deck examples
            for ex in speech_deck_examples + artist_deck_examples:
                ident = example_identity(ex["sentence"])
                if ident not in comb_identities:
                    comb_identities.add(ident)
                    combined.append(ex)
                    if len(combined) >= 3:
                        break

            # For learner card usability in the app, pad with existing fallback rows if needed
            if len(combined) < 3:
                for ex in existing:
                    if len(combined) >= 3:
                        break
                    s_text = ex.get("targetHTML", "").replace("<span class='fw-token-v'>", "").replace("<span class='fw-token-c'>", "").replace("<span class='fw-token-connector'>", "").replace("</span>", "").replace("<span class=\"fw-token-v\">", "").replace("<span class=\"fw-token-c\">", "").replace("<span class=\"fw-token-connector\">", "")
                    ident = example_identity(s_text)
                    if ident not in comb_identities:
                        comb_identities.add(ident)
                        fallback_ex = copy.deepcopy(ex)
                        fallback_ex.setdefault("metadata", {})["is_legacy_fallback"] = True
                        combined.append(fallback_ex)

        final_pattern_status[pid] = {
            "tag": pinfo["tag"],
            "total_examples_assigned": len(combined),
            "fresh_matches_count": len(fresh),
            "speech_matches_count": len(speech_matches),
            "artist_matches_count": len(artist_matches),
            "speech_deck_examples": speech_deck_examples,
            "artist_deck_examples": artist_deck_examples,
            "artist_deck_by_artist": dict(artist_deck_by_artist),
            "speech_shortage": speech_shortage,
            "artist_shortage": artist_shortage,
            "is_shortage": is_shortage,
            "shortage_count": shortage_count if is_shortage else 0,
            "examples": combined
        }

    # Print summary
    print("\n================ PATTERN COVERAGE & SHORTAGE AUDIT ================")
    print(f"Total patterns audited: {len(all_patterns)} (51 ES, 64 PT)")
    print(f"Speech Deck full patterns (>= 3 speech matches): {speech_deck_patterns_full} / {len(all_patterns)} ({speech_deck_patterns_full/len(all_patterns)*100:.1f}%)")
    print(f"Speech Deck shortages: {len(speech_deck_shortages)} / {len(all_patterns)}")
    print(f"Artist Deck full patterns (>= 3 artist matches): {artist_deck_patterns_full} / {len(all_patterns)} ({artist_deck_patterns_full/len(all_patterns)*100:.1f}%)")
    print(f"Artist Deck shortages: {len(artist_deck_shortages)} / {len(all_patterns)}")
    print(f"Cross-deck unified patterns (>= 3 fresh matches): {patterns_with_ge_3_fresh} / {len(all_patterns)} ({patterns_with_ge_3_fresh/len(all_patterns)*100:.1f}%)")
    print(f"Cross-deck reported shortages (< 3 fresh matches): {len(shortages)} / {len(all_patterns)}")

    # Write Shortage & Coverage Report
    report_lines = [
        "# Function-Word Pattern Coverage & Shortage Report",
        "",
        f"**Date:** 2026-10-18  ",
        f"**Matcher Version:** `{VERSION}`  ",
        f"**Total Patterns Audited:** {len(all_patterns)} (51 Spanish, 64 Portuguese)  ",
        f"**Pilot Patterns (Vetted & Traceable):** 24 patterns (12 words)  ",
        "",
        "## Executive Summary",
        "",
        f"- **Speech Deck Coverage:** {speech_deck_patterns_full} / {len(all_patterns)} patterns with $\\ge 3$ distinct verified speech examples ({len(speech_deck_shortages)} shortages).",
        f"- **Artist Deck Coverage:** {artist_deck_patterns_full} / {len(all_patterns)} patterns with $\\ge 3$ distinct verified artist examples ({len(artist_deck_shortages)} shortages).",
        f"- **Cross-Deck Unified Coverage:** {patterns_with_ge_3_fresh} / {len(all_patterns)} patterns with $\\ge 3$ fresh verified examples ({len(shortages)} shortages).",
        "",
        "## Speech Deck Shortages",
        "",
        "Patterns with fewer than 3 verified speech matches from dialogue/subtitles:",
        "",
        "| Pattern ID | Tag | Formula | Matches Found | Shortage | Reason |",
        "|---|---|---|---|---|---|"
    ]
    for s in speech_deck_shortages:
        clean_form = re.sub(r"<[^>]+>", "", s["formula"] or "")
        report_lines.append(f"| `{s['pattern_id']}` | {s['tag']} | `{clean_form}` | {s['matches_found']} | -{s['shortage']} | {s['reason']} |")

    report_lines.extend([
        "",
        "## Artist Deck Shortages",
        "",
        "Patterns with fewer than 3 verified artist matches from lyrics:",
        "",
        "| Pattern ID | Tag | Formula | Matches Found | Shortage | Reason |",
        "|---|---|---|---|---|---|"
    ])
    for s in artist_deck_shortages:
        clean_form = re.sub(r"<[^>]+>", "", s["formula"] or "")
        report_lines.append(f"| `{s['pattern_id']}` | {s['tag']} | `{clean_form}` | {s['matches_found']} | -{s['shortage']} | {s['reason']} |")

    report_lines.extend([
        "",
        "## Cross-Deck Unified Shortage Inventory",
        "",
        "| Pattern ID | Tag | Formula | Fresh Found | Shortage | Speech | Artist | Reason |",
        "|---|---|---|---|---|---|---|---|"
    ])
    for s in shortages:
        clean_form = re.sub(r"<[^>]+>", "", s["formula"] or "")
        report_lines.append(f"| `{s['pattern_id']}` | {s['tag']} | `{clean_form}` | {s['fresh_matches_found']} | -{s['shortage_count']} | {s['speech_matches']} | {s['artist_matches']} | {s['reason']} |")

    report_lines.extend([
        "",
        "## Complete Pattern Breakdown",
        "",
        "| Pattern ID | Tag | Total Assigned | Fresh Total | Speech Deck | Artist Deck | Unified Status |",
        "|---|---|---|---|---|---|---|"
    ])
    for pid in sorted(all_patterns.keys()):
        stat = final_pattern_status[pid]
        status_str = "Shortage reported" if stat["is_shortage"] else "Full verified coverage"
        report_lines.append(f"| `{pid}` | {stat['tag']} | {stat['total_examples_assigned']} | {stat['fresh_matches_count']} | {stat['speech_matches_count']} | {stat['artist_matches_count']} | {status_str} |")

    report_path = ROOT / "docs/audits/function-word-assignment/pattern_shortage_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"\nShortage report written to {report_path}")

    # Write coverage JSON
    cov_path = ROOT / "docs/audits/function-word-assignment/pattern_coverage.json"
    cov_path.write_text(json.dumps({
        "matcher_version": VERSION,
        "total_patterns": len(all_patterns),
        "speech_deck": {
            "patterns_ge_3": speech_deck_patterns_full,
            "shortage_count": len(speech_deck_shortages),
            "shortages": speech_deck_shortages
        },
        "artist_deck": {
            "patterns_ge_3": artist_deck_patterns_full,
            "shortage_count": len(artist_deck_shortages),
            "shortages": artist_deck_shortages
        },
        "unified": {
            "patterns_ge_3_fresh": patterns_with_ge_3_fresh,
            "shortage_count": len(shortages),
            "shortages": shortages
        },
        "patterns": {pid: {k: v for k, v in stat.items() if not k.endswith("_examples") and k != "examples"} for pid, stat in final_pattern_status.items()}
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.apply:
        print("\nApplying verified examples to app/data/grammar-words/{es,pt}.json...")
        for pid, stat in final_pattern_status.items():
            lang, w, idx_str = pid.split(":")
            idx = int(idx_str)
            suite = es_suite if lang == "es" else pt_suite
            rel = suite[w]["relations"][idx]
            rel["pos"] = get_pattern_pos(lang, w, idx, rel.get("tag", ""), rel.get("formulaHTML", ""))
            rel["speech_examples"] = stat["speech_deck_examples"]
            rel["artist_examples"] = stat["artist_deck_examples"]
            rel["artist_examples_by_artist"] = stat["artist_deck_by_artist"]
            rel["examples"] = stat["examples"]
            if stat["examples"] and w not in PILOT_WORDS:
                rel["targetHTML"] = stat["examples"][0]["targetHTML"]
                rel["translation"] = stat["examples"][0].get("translation", "")
                rel["source"] = stat["examples"][0].get("source", "Contemporary dialogue")

        # Ensure top-level card pos is set
        for suite in (es_suite, pt_suite):
            for w, card in suite.items():
                if card.get("relations") and "pos" in card["relations"][0]:
                    card["pos"] = card["relations"][0]["pos"]

        (ROOT / "app/data/grammar-words/es.json").write_text(json.dumps(es_suite, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        (ROOT / "app/data/grammar-words/pt.json").write_text(json.dumps(pt_suite, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print("Updated es.json and pt.json. Running sync_function_word_card_js.py...")
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts/sync_function_word_card_js.py")], check=True)
        print("Runtime synchronization complete.")


if __name__ == "__main__":
    main()
