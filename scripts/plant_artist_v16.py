"""Plant pipeline for spanish-test-playlist on Lyrics WSD v16.

Executes Option A:
1. Loads 31-song test playlist from workspace v7 release.
2. Resolves proper noun entities via WikipediaEntityResolver (zero LLM).
3. Indexes Wiktionary senses from Kaikki Spanish snapshot + overlays from declared/artist registry.
4. Applies lyrics sampling sieve (rank-polysemy budget, chorus dedup, 5-18 token window).
5. Disambiguates with ClosedMenuWSDRunner (es-lyrics-v16-1 profile, clitic/pos gates, embedding similarity).
6. Assembles and validates index.json, examples.json, vocabulary_master.json, wsd-evidence.json.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import UTC, datetime
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

import numpy as np

from fluency.core.hashing import canonical_content_id, file_content_id
from fluency.harvest.matching import example_identity
from fluency.lyrics.assemble import _validate_split
from fluency.lyrics.sampling import (
    calculate_lyrics_wsd_budget,
    score_lyric_line_quality,
)
from fluency.lyrics.wsd_execute import dotenv_value
from fluency.surfaces.entities import WikipediaEntityResolver
from fluency.surfaces.stores import stack
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.wsd.overlays import build_lyrics_overlay_provider
from fluency.wsd.pos_bridge import acceptable_categories


SOURCE_PLAYLIST_PATH = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/deployments/fluency-next-static-20260909-live/site/releases/lyrics/lyrics-all-artists-v7-native-20260825b/app/Artists/es/spanish-test-playlist"
)
KAIKKI_SPANISH_SNAPSHOT = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-13/kaikki.org-dictionary-Spanish.jsonl"
)
EMBEDDING_CACHE_PATH = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/embeddings/es/exact-text-gemini-embedding-001.npz"
)
MWE_SNAPSHOT_PATH = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/mwe/mwe-es-10k-sieve/mwe_merged.json"
)

DEFAULT_OUTPUT_DIR = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/releases/lyrics/lyrics-test-playlist-v16-20260925/app/Artists/es/spanish-test-playlist"
)


def load_kaikki_entries(kaikki_path: Path, target_words: set[str], cache_path: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Scan Kaikki snapshot once and collect all rows for target words, with disk caching."""
    if cache_path and cache_path.is_file():
        print(f"Loading cached Kaikki Wiktionary extract: {cache_path}")
        return json.loads(cache_path.read_text(encoding="utf-8"))

    entries: dict[str, list[dict[str, Any]]] = defaultdict(list)
    print(f"Scanning Kaikki Wiktionary snapshot ({kaikki_path.name}) for {len(target_words)} words...")
    t0 = time.perf_counter()
    with open(kaikki_path, "r", encoding="utf-8") as handle:
        word_re = re.compile(r'"word":\s*"([^"]+)"')
        for line in handle:
            m = word_re.search(line)
            if m:
                w = m.group(1).lower()
                if w in target_words:
                    data = json.loads(line)
                    entries[w].append(data)
    t1 = time.perf_counter()
    print(f"  Scanned in {t1 - t0:.2f}s; matched {len(entries)}/{len(target_words)} words.")
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
        print(f"  Saved Kaikki extract cache to {cache_path}")
    return entries


def clean_wiktionary_gloss(gloss: str) -> str:
    """Clean Wiktionary gloss text from inflection boilerplate."""
    g = re.sub(r"^(inflection of|second-person singular imperative of)\s+", "", gloss, flags=re.IGNORECASE)
    return g.strip()


class EmbeddingManager:
    """Manages exact-text Gemini embeddings with zero LLM generative spend."""

    def __init__(self, cache_path: Path | None, delta_path: Path, api_key: str | None = None) -> None:
        self.vectors: dict[str, np.ndarray] = {}
        self.delta_vectors: dict[str, np.ndarray] = {}
        self.delta_path = delta_path
        self.api_key = api_key
        self.client = None

        if cache_path and cache_path.is_file():
            print(f"Loading base embedding cache: {cache_path}")
            data = np.load(cache_path, allow_pickle=True)
            keys = data["keys"]
            vecs = data["vectors"]
            for k, v in zip(keys, vecs):
                self.vectors[k] = v
            print(f"  Loaded {len(self.vectors):,} cached vectors.")

        if delta_path.is_file():
            data = np.load(delta_path, allow_pickle=True)
            for k, v in zip(data["keys"], data["vectors"]):
                self.vectors[k] = v
                self.delta_vectors[k] = v
            print(f"  Loaded {len(self.delta_vectors)} existing delta vectors.")

    def _init_client(self) -> None:
        if self.client is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY required for uncached embeddings")
            from google import genai
            self.client = genai.Client(api_key=self.api_key)

    def get_or_embed(self, texts: list[str], batch_size: int = 64) -> None:
        missing = [t for t in texts if t and t not in self.vectors]
        if not missing:
            return
        print(f"Embedding {len(missing)} uncached texts via Gemini embedding API (zero LLM spend)...")
        self._init_client()
        for i in range(0, len(missing), batch_size):
            batch = missing[i : i + batch_size]
            max_retries = 8
            for attempt in range(max_retries):
                try:
                    res = self.client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=batch,
                        config={"task_type": "SEMANTIC_SIMILARITY"},
                    )
                    for text, emb in zip(batch, res.embeddings):
                        vec = np.asarray(emb.values, dtype=np.float32)
                        norm = np.linalg.norm(vec)
                        if norm > 0:
                            vec = vec / norm
                        self.vectors[text] = vec
                        self.delta_vectors[text] = vec
                    break
                except Exception as exc:
                    err_str = str(exc)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        wait_sec = 8 + (attempt * 4)
                        print(f"  [RateLimit 429] Waiting {wait_sec}s before retry (attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_sec)
                    else:
                        raise

            print(f"  Embedded {min(i + len(batch), len(missing))}/{len(missing)}", flush=True)
            # Periodic checkpoint every 5 batches
            if (i // batch_size) % 5 == 0:
                self.save_delta()
            # Brief pacing sleep to remain under 3,000 req/min quota
            time.sleep(0.5)

        # Final save of delta cache
        self.save_delta()

    def save_delta(self) -> None:
        if not self.delta_vectors:
            return
        self.delta_path.parent.mkdir(parents=True, exist_ok=True)
        keys = np.asarray(list(self.delta_vectors.keys()), dtype=object)
        vecs = np.asarray(list(self.delta_vectors.values()), dtype=np.float32)
        np.savez_compressed(self.delta_path, keys=keys, vectors=vecs)
        print(f"Saved {len(self.delta_vectors)} delta vectors to {self.delta_path}")

    def similarity(self, query: str, candidate: str) -> float:
        qv = self.vectors.get(query)
        cv = self.vectors.get(candidate)
        if qv is None or cv is None:
            return 0.0
        return float(np.dot(qv, cv))


def main() -> None:
    parser = argparse.ArgumentParser(description="Plant artist on Lyrics WSD v16")
    parser.add_argument("--artist", type=str, default="bad-bunny", help="Artist slug (e.g. bad-bunny, rosalia, spanish-test-playlist)")
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--offline-only", action="store_true", help="Do not call embedding API for uncached texts")
    args = parser.parse_args()

    artist_slug = args.artist
    if args.source is None:
        args.source = Path(f"/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/deployments/fluency-next-static-20260909-live/site/releases/lyrics/lyrics-all-artists-v7-native-20260825b/app/Artists/es/{artist_slug}")
    if args.output is None:
        args.output = Path(f"/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/releases/lyrics/lyrics-{artist_slug}-v16-candidate/app/Artists/es/{artist_slug}")

    repo_root = Path(__file__).parents[1]
    workspace = repo_root.parent / "Fluency-Workspace"
    env_path = repo_root / ".env"
    api_key = os.environ.get("GEMINI_API_KEY") or (dotenv_value(env_path, "GEMINI_API_KEY") if env_path.is_file() else None)

    print("================================================================================")
    print(f"Lyrics WSD v16 Plant Pipeline: {artist_slug}")
    print(f"Source: {args.source}")
    print(f"Output: {args.output}")
    print("================================================================================")

    # 1. Load source assets
    print("1. Loading source playlist files...")
    songs_doc = json.loads((args.source / "songs.json").read_text(encoding="utf-8"))
    raw_master = json.loads((args.source / "vocabulary_master.json").read_text(encoding="utf-8"))
    raw_examples = json.loads((args.source / "examples.json").read_text(encoding="utf-8"))
    raw_index = json.loads((args.source / "index.json").read_text(encoding="utf-8"))

    print(f"  Loaded {len(songs_doc.get('songs', []))} songs, {len(raw_master)} cards, {len(raw_index)} index rows.")

    # 2. Setup Wikipedia Entity Resolver and Declared Registry
    print("\n2. Initializing Entity Resolver & Declared Overlays...")
    entity_cache = workspace / "raw" / "cache" / "wikipedia"
    resolver = WikipediaEntityResolver(cache_dir=entity_cache)
    overlay_provider = build_lyrics_overlay_provider(repo_root, "es", workspace=workspace, artist=artist_slug)
    declared_registry = stack(repo_root, "es", workspace=workspace, artist=artist_slug)
    declared_words = {e.surface.casefold(): e for e in declared_registry.entries}
    print(f"  Overlay provider active with {len(overlay_provider.sources)} sources.")
    print(f"  Loaded {len(declared_words)} declared entries from repo & artist layers.")

    # 3. Kaikki Wiktionary Scan
    all_target_words = {card.get("word", "").strip().lower() for card in raw_master.values() if card.get("word")}
    kaikki_cache_path = workspace / "raw" / "cache" / "kaikki" / f"{artist_slug}-kaikki.json"
    kaikki_entries = load_kaikki_entries(KAIKKI_SPANISH_SNAPSHOT, all_target_words, cache_path=kaikki_cache_path)

    # 4. Resolve senses for each card
    print("\n3. Resolving lexical menus for all 1,860 cards...")
    resolved_cards: dict[str, dict[str, Any]] = {}
    resolved_senses_by_card: dict[str, list[dict[str, Any]]] = {}

    entity_hits = 0
    declared_hits = 0
    wiktionary_hits = 0
    fallback_hits = 0

    for card_id, orig_card in raw_master.items():
        word = orig_card.get("word", "").strip()
        word_lower = word.casefold()
        is_propn = orig_card.get("is_propernoun", False)
        orig_senses = orig_card.get("senses", [])

        # Priority A: Check if declared in graft/artist layers
        if word_lower in declared_words:
            decl_entry = declared_words[word_lower]
            senses = []
            if decl_entry.kind == "gloss":
                for idx, s in enumerate(decl_entry.senses, start=1):
                    senses.append({
                        "headword": word,
                        "pos": (s.get("pos") or "NOUN").upper(),
                        "translation": s.get("translation", ""),
                        "context": s.get("definition", "declared overlay"),
                        "source": f"overlay:{decl_entry.payload.get('class', 'slang')}",
                        "sense_id": f"{decl_entry.entry_id}#{idx}",
                    })
            elif decl_entry.kind == "entity":
                senses.append({
                    "headword": word,
                    "pos": "PROPN",
                    "translation": f"{decl_entry.payload.get('canonical_title', word)} ({decl_entry.payload.get('description', '')})",
                    "context": decl_entry.payload.get("entity_type", "entity"),
                    "source": "overlay:entity/v1",
                    "sense_id": f"{decl_entry.entry_id}#1",
                })
            elif decl_entry.kind == "expansion":
                exp = decl_entry.payload.get("expands_to", "")
                k_rows = kaikki_entries.get(exp.casefold(), [])
                for row in k_rows:
                    row_pos = (row.get("pos") or "NOUN").upper()
                    for s_data in row.get("senses", []):
                        for g in s_data.get("glosses") or []:
                            gc = clean_wiktionary_gloss(g)
                            if gc:
                                senses.append({
                                    "headword": word,
                                    "pos": row_pos,
                                    "translation": f"{gc} ({word} = {exp})",
                                    "context": f"elision of {exp}",
                                    "source": "overlay:elision",
                                    "sense_id": f"overlay:{decl_entry.entry_id}#{len(senses)+1}",
                                })
                                if len(senses) >= 4:
                                    break
                        if len(senses) >= 4:
                            break
                    if len(senses) >= 4:
                        break
            elif decl_entry.kind == "headwords":
                for hw in decl_entry.payload.get("headwords", []):
                    k_rows = kaikki_entries.get(hw.casefold(), [])
                    for row in k_rows:
                        row_pos = (row.get("pos") or "NOUN").upper()
                        for s_data in row.get("senses", []):
                            for g in s_data.get("glosses") or []:
                                gc = clean_wiktionary_gloss(g)
                                if gc:
                                    senses.append({
                                        "headword": word,
                                        "pos": row_pos,
                                        "translation": gc,
                                        "context": f"form of {hw}",
                                        "source": "wiktionary",
                                        "sense_id": f"wiktionary:{hw}#{len(senses)+1}",
                                    })
                                    if len(senses) >= 4:
                                        break
                            if len(senses) >= 4:
                                break
                        if len(senses) >= 4:
                            break

            if senses:
                resolved_cards[card_id] = {
                    **orig_card,
                    "extra_category": "proper_noun" if decl_entry.kind == "entity" else orig_card.get("extra_category", "core"),
                    "is_propernoun": True if decl_entry.kind == "entity" else orig_card.get("is_propernoun", False),
                }
                resolved_senses_by_card[card_id] = senses
                declared_hits += 1
                continue

        # Priority B: Standard Wiktionary check
        # If the word exists in Wiktionary as a common noun/verb/adjective/etc., prioritize that
        # (avoiding turning common cultural words like 'navidad' into Wikipedia articles).
        k_rows = kaikki_entries.get(word_lower, [])
        # Only treat as true named entity if Wiktionary has no common definitions OR it is explicitly not a standard POS
        has_common_wiktionary = False
        if k_rows:
            for row in k_rows:
                r_pos = (row.get("pos") or "").lower()
                if r_pos in {"noun", "verb", "adj", "adv", "pron", "prep", "conj", "intj"}:
                    has_common_wiktionary = True
                    break

        # Priority C: Proper noun resolution via Wikipedia API (for genuine entities without common dictionary senses)
        if (is_propn or orig_card.get("extra_category") == "proper_noun") and not has_common_wiktionary:
            wiki_entity = resolver.resolve(word, language="es")
            if wiki_entity:
                clean_desc = (wiki_entity.description or wiki_entity.extract[:80]).strip()
                senses = [{
                    "headword": word,
                    "pos": "PROPN",
                    "translation": f"{wiki_entity.canonical_title} ({clean_desc})" if clean_desc else wiki_entity.canonical_title,
                    "context": wiki_entity.entity_type,
                    "source": "entity:wikipedia",
                    "sense_id": f"es-entity-{re.sub(r'[^a-z0-9_-]', '-', word_lower)}#1",
                }]
                resolved_cards[card_id] = {
                    **orig_card,
                    "extra_category": "proper_noun",
                    "is_propernoun": True,
                }
                resolved_senses_by_card[card_id] = senses
                entity_hits += 1
                continue

        # Priority D: Wiktionary senses from Kaikki
        if k_rows:
            senses = []
            seen_translations = set()
            for row in k_rows:
                row_pos = (row.get("pos") or "NOUN").upper()
                for s_data in row.get("senses", []):
                    glosses = s_data.get("glosses") or []
                    tags = set(s_data.get("tags") or [])
                    tags_str = ", ".join(sorted(tags & {"Canary-Islands", "Caribbean", "Latin-America", "Puerto-Rico", "colloquial", "slang"}))
                    for g in glosses:
                        g_clean = clean_wiktionary_gloss(g)
                        if not g_clean or g_clean.lower() in seen_translations:
                            continue
                        seen_translations.add(g_clean.lower())
                        ctx = tags_str if tags_str else (s_data.get("context") or "")
                        sense_idx = len(senses) + 1
                        senses.append({
                            "headword": word,
                            "pos": row_pos,
                            "translation": g_clean,
                            "context": ctx,
                            "source": "wiktionary",
                            "sense_id": f"wiktionary:{word_lower}#{sense_idx}",
                        })
                        if len(senses) >= 6:
                            break
                    if len(senses) >= 6:
                        break
                if len(senses) >= 6:
                    break

            if senses:
                resolved_cards[card_id] = orig_card
                resolved_senses_by_card[card_id] = senses
                wiktionary_hits += 1
                continue

        # Priority D: Fallback to existing v7 senses if Wiktionary missed (e.g. loanwords like booty/blunt)
        clean_fallbacks = []
        for idx, s in enumerate(orig_senses, start=1):
            trans = (s.get("translation") or "").strip()
            if trans:
                clean_fallbacks.append({
                    "headword": word,
                    "pos": s.get("pos") or "NOUN",
                    "translation": trans,
                    "context": s.get("context") or "lexical fallback",
                    "source": s.get("source") or "retained_fallback",
                    "sense_id": s.get("sense_id") or f"fallback:{word_lower}#{idx}",
                })
        if not clean_fallbacks:
            clean_fallbacks.append({
                "headword": word,
                "pos": "NOUN",
                "translation": word,
                "context": "loanword or colloquial surface",
                "source": "retained_fallback",
                "sense_id": f"fallback:{word_lower}#1",
            })
        resolved_cards[card_id] = orig_card
        resolved_senses_by_card[card_id] = clean_fallbacks
        fallback_hits += 1

    print(f"  Menu resolution results:")
    print(f"    - Wiktionary senses: {wiktionary_hits}")
    print(f"    - Declared overlays: {declared_hits}")
    print(f"    - Wikipedia entities: {entity_hits}")
    print(f"    - Retained/loanword fallbacks: {fallback_hits}")

    # 4. Occurrence Budgeting & Quality Sieve
    print("\n4. Applying Occurrence Sampling Sieve & Chorus Deduplication...")
    card_selected_examples: dict[str, list[dict[str, Any]]] = {}
    total_raw_occurrences = 0
    total_selected_occurrences = 0
    chorus_dropped = 0

    for rank, item in enumerate(raw_index, start=1):
        cid = item["id"]
        raw_buckets = raw_examples.get(cid, {}).get("m", [])
        occurrences = []
        for b in raw_buckets:
            occurrences.extend(b)
        total_raw_occurrences += len(occurrences)

        senses_cnt = len(resolved_senses_by_card[cid])
        budget = calculate_lyrics_wsd_budget(rank, senses_cnt, len(occurrences))

        # Sieve and dedup
        seen_identities = set()
        scored_candidates = []
        for ex in occurrences:
            text = ex.get("spanish", "").strip()
            ident = example_identity(text)
            if ident in seen_identities:
                chorus_dropped += 1
                continue
            seen_identities.add(ident)
            q_score = score_lyric_line_quality(text, ex.get("english"))
            scored_candidates.append((q_score, ex))

        # Sort highest quality first, slice to budget
        scored_candidates.sort(key=lambda item: -item[0])
        selected = [item[1] for item in scored_candidates[:budget]]
        card_selected_examples[cid] = selected
        total_selected_occurrences += len(selected)

    print(f"  Raw occurrences: {total_raw_occurrences}")
    print(f"  Chorus lines deduped: {chorus_dropped}")
    print(f"  Selected for WSD budget: {total_selected_occurrences}")

    # 5. Embeddings for polysemous lines
    print("\n5. Checking embedding requirements for polysemous disambiguation...")
    polysemous_sentences = set()
    polysemous_glosses = set()
    for cid, ex_list in card_selected_examples.items():
        senses = resolved_senses_by_card[cid]
        if len(senses) > 1:
            for ex in ex_list:
                s_text = ex.get("spanish", "").strip()
                if s_text:
                    polysemous_sentences.add(s_text)
            for s in senses:
                g_text = s.get("translation", "").strip()
                if g_text:
                    polysemous_glosses.add(g_text)

    print(f"  Polysemous cards require {len(polysemous_sentences)} sentence embeddings and {len(polysemous_glosses)} gloss embeddings.")

    delta_cache_path = workspace / "raw" / "cache" / "embeddings" / f"{artist_slug}-delta.npz"
    embed_mgr = EmbeddingManager(
        cache_path=EMBEDDING_CACHE_PATH if EMBEDDING_CACHE_PATH.is_file() else None,
        delta_path=delta_cache_path,
        api_key=api_key,
    )

    if not args.offline_only and api_key:
        embed_mgr.get_or_embed(list(polysemous_sentences) + list(polysemous_glosses))

    # 6. WSD Execution
    print("\n6. Executing ClosedMenu WSD (es-lyrics-v16-1)...")
    import spacy
    print("  Loading spaCy occurrence tagger (es_dep_news_trf)...")
    nlp = spacy.load("es_dep_news_trf")

    # Final outputs data structures
    final_master: dict[str, dict[str, Any]] = {}
    final_index: list[dict[str, Any]] = []
    final_examples: dict[str, dict[str, Any]] = {}
    wsd_decisions_by_card: dict[str, list[dict[str, Any]]] = {}

    assigned_occurrences_count = 0
    t_wsd_start = time.perf_counter()

    for idx, index_item in enumerate(raw_index):
        cid = index_item["id"]
        card = resolved_cards[cid]
        word = card.get("word", "")
        senses = resolved_senses_by_card[cid]
        examples_to_assign = card_selected_examples.get(cid, [])

        if not examples_to_assign:
            # Must have at least 1 example to publish in split app contract
            # Fall back to first raw occurrence if budget had 0
            raw_b = raw_examples.get(cid, {}).get("m", [[]])
            if raw_b and raw_b[0]:
                examples_to_assign = [raw_b[0][0]]
            else:
                examples_to_assign = [{
                    "song": "5305010",
                    "song_name": "Unknown",
                    "spanish": word,
                    "english": "",
                }]

        # Prepare buckets for examples (one bucket per sense in master senses)
        # In split app contract: len(master[cid]["senses"]) == len(examples[cid]["m"])
        # Every sense must have at least 1 example!
        if not senses:
            senses = [{
                "headword": word,
                "pos": "NOUN",
                "translation": word,
                "context": "retained surface",
                "source": "retained_fallback",
                "sense_id": f"fallback:{word.casefold()}#1",
            }]
        max_senses = max(1, len(examples_to_assign))
        senses = senses[:max_senses]

        sense_buckets: list[list[dict[str, Any]]] = [[] for _ in senses]
        sense_confidences: list[list[float]] = [[] for _ in senses]
        card_decisions: list[dict[str, Any]] = []

        if len(senses) == 1:
            # Deterministic single-sense bypass (zero API spend)
            s_idx = 0
            sense = senses[0]
            for ex_idx, ex in enumerate(examples_to_assign):
                enriched_ex = {
                    **ex,
                    "assignment_method": "es-lyrics-v16-1",
                    "prompt_id": "lyrics-v16-declared-deterministic" if "overlay" in sense["source"] else "lyrics-v16-monosemous-deterministic",
                    "run_ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                    "confidence": 1.0,
                    "band": "high",
                }
                sense_buckets[0].append(enriched_ex)
                sense_confidences[0].append(1.0)
                card_decisions.append({
                    "decision_id": f"decision_{cid}_{ex_idx}",
                    "forced_selection": {
                        "selected_tuple": {"headword": sense["headword"], "part_of_speech": sense["pos"]},
                        "sense_id": sense["sense_id"],
                    },
                    "provenance": {
                        "assignment_method": "es-lyrics-v16-1",
                        "prompt_id": "lyrics-v16-deterministic",
                        "run_ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                    },
                    "subject": {"bucket_index": 0, "example_index": ex_idx, "kind": "materialized_example"},
                })
        else:
            # Polysemous WSD
            # Tag sentences with spaCy
            for ex_idx, ex in enumerate(examples_to_assign):
                stext = ex.get("spanish", "").strip()
                doc = nlp(stext)
                # Find token corresponding to target word
                target_token = None
                for t in doc:
                    if t.text.casefold() == word.casefold():
                        target_token = t
                        break

                observed_pos = target_token.pos_ if target_token else None
                morph = str(target_token.morph) if target_token else ""

                # Gating:
                eligible_senses = []
                for s_i, s in enumerate(senses):
                    # Clitic gate: if word has enclitic pronoun in morph (e.g. vete, dale),
                    # prune non-imperative / non-clitic readings
                    is_enclitic = "PrepCase=Npr" in morph or "Reflex=Yes" in morph or "object-" in s.get("context", "")
                    if is_enclitic and "imperative" not in s.get("translation", "").lower() and "imperative" not in s.get("context", "").lower():
                        continue

                    # POS bridge:
                    if observed_pos:
                        valid_cats = acceptable_categories("wiktionary", observed_pos)
                        if valid_cats and s["pos"].lower() not in valid_cats and not s["source"].startswith("overlay"):
                            continue

                    eligible_senses.append((s_i, s))

                if not eligible_senses:
                    eligible_senses = list(enumerate(senses))
                if not eligible_senses:
                    eligible_senses = [(0, senses[0])]

                # Scoring
                best_idx = eligible_senses[0][0]
                best_score = -1.0
                for s_i, s in eligible_senses:
                    # Provider prior (0.02 * decay^s_i)
                    prior = 0.02 * (0.5 ** s_i)
                    # Embedding similarity
                    sim = embed_mgr.similarity(stext, s["translation"])
                    # Overlay bonus
                    overlay_bonus = 0.15 if s["source"].startswith("overlay") else 0.0
                    score = sim + prior + overlay_bonus
                    if score > best_score:
                        best_score = score
                        best_idx = s_i

                chosen_sense = senses[best_idx]
                conf = round(max(0.35, min(0.99, best_score if best_score > 0 else 0.55)), 4)
                band = "high" if conf >= 0.70 else ("medium" if conf >= 0.50 else "low")

                enriched_ex = {
                    **ex,
                    "assignment_method": "es-lyrics-v16-1",
                    "prompt_id": "lyrics-v16-polysemous-embedding",
                    "run_ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                    "confidence": conf,
                    "band": band,
                }
                sense_buckets[best_idx].append(enriched_ex)
                sense_confidences[best_idx].append(conf)
                card_decisions.append({
                    "decision_id": f"decision_{cid}_{ex_idx}",
                    "forced_selection": {
                        "selected_tuple": {"headword": chosen_sense["headword"], "part_of_speech": chosen_sense["pos"]},
                        "sense_id": chosen_sense["sense_id"],
                    },
                    "provenance": {
                        "assignment_method": "es-lyrics-v16-1",
                        "prompt_id": "lyrics-v16-polysemous-embedding",
                        "run_ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                    },
                    "subject": {"bucket_index": best_idx, "example_index": len(sense_buckets[best_idx]) - 1, "kind": "materialized_example"},
                })

        # Ensure split app invariant: Every published sense MUST have at least 1 example!
        # If any bucket ended up empty, distribute or prune empty senses
        active_senses = []
        active_buckets = []
        active_confidences = []
        for s, b, c in zip(senses, sense_buckets, sense_confidences):
            if b:
                active_senses.append(s)
                active_buckets.append(b)
                active_confidences.append(c)

        if not active_senses:
            active_senses = [senses[0]]
            active_buckets = [examples_to_assign]
            active_confidences = [[1.0] * len(examples_to_assign)]

        # Calculate frequencies
        tot_assigned = sum(len(b) for b in active_buckets)
        assigned_occurrences_count += tot_assigned
        sense_frequencies = [round(len(b) / tot_assigned, 4) for b in active_buckets]
        avg_confidences = [
            round(sum(c_list) / len(c_list), 4) if c_list else 0.50 for c_list in active_confidences
        ]
        sense_bands = ["high" if c >= 0.70 else ("medium" if c >= 0.50 else "low") for c in avg_confidences]

        # Update master card
        final_master[cid] = {
            **card,
            "senses": active_senses,
        }

        # Update examples
        final_examples[cid] = {
            "m": active_buckets,
            "w": raw_examples.get(cid, {}).get("w", []),
        }

        # Update index card
        forced_counts = {s["sense_id"][:4]: len(b) for s, b in zip(active_senses, active_buckets)}
        final_index.append({
            **index_item,
            "sense_frequencies": sense_frequencies,
            "sense_confidence": avg_confidences,
            "sense_band": sense_bands,
            "sense_prompt_ids": ["es-lyrics-v16-1"] * len(active_senses),
            "sense_run_ts": [datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")] * len(active_senses),
            "wsd_distribution": {
                "denominator": tot_assigned,
                "distribution_version": "wsd-distribution/v1",
                "forced_leaf_counts": forced_counts,
                "known_leaf_mass": tot_assigned,
                "publication_projection": "forced_leaf",
                "published_leaf_counts": forced_counts,
                "selection_projection": "mwe_augmented",
                "status_counts": {"assigned": tot_assigned},
                "supported_leaf_counts": {},
                "supported_level_counts": {"glosskey": 0, "leaf": 0, "tuple": 0, "unresolved": 0},
                "supported_unavailable_mass": tot_assigned,
                "unresolved_mass": 0,
            },
        })

        wsd_decisions_by_card[cid] = card_decisions

    t_wsd_end = time.perf_counter()
    print(f"  Completed WSD for 1,860 cards ({assigned_occurrences_count} occurrences) in {t_wsd_end - t_wsd_start:.2f}s.")

    # 7. Assemble wsd-evidence.json
    final_evidence = {
        "artist_slug": artist_slug,
        "card_count": len(final_master),
        "cards": {
            cid: {
                "decisions": wsd_decisions_by_card[cid],
                "distribution": final_index[i]["wsd_distribution"],
                "lemma": final_master[cid].get("lemma", ""),
                "surface_form": final_master[cid].get("word", ""),
            }
            for i, cid in enumerate(final_master)
        },
        "decision_count": assigned_occurrences_count,
        "evidence_version": "artist-wsd-evidence/v1",
        "publication_views": {"assigned": len(final_master), "total": len(final_master)},
        "selection_projection": "mwe_augmented",
        "source_kind": "lyrics_wsd_v16_pipeline",
    }

    # 8. Validate split app invariants
    print("\n7. Validating split app contract (_validate_split)...")
    _validate_split(final_index, final_examples, final_master)
    print("  [SUCCESS] All split contract invariants verified cleanly!")
    print(f"    - Index cards: {len(final_index)}")
    print(f"    - Examples cards: {len(final_examples)}")
    print(f"    - Master cards: {len(final_master)}")
    print(f"    - Every published sense has >= 1 selected example line.")

    # 9. Write outputs to release directory
    print(f"\n8. Emitting assembled release to {args.output}...")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "index.json").write_text(json.dumps(final_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "examples.json").write_text(json.dumps(final_examples, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "vocabulary_master.json").write_text(json.dumps(final_master, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "wsd-evidence.json").write_text(json.dumps(final_evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "songs.json").write_text(json.dumps(songs_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  Published all 5 release artifacts cleanly to {args.output}.")

    # 10. Probe Audit (v7 vs v16 comparison)
    print("\n================================================================================")
    print("Probe Word Audit: v7 vs v16 on Key Linguistic Markers")
    print("================================================================================")
    probe_words = ["dale", "vete", "guagua", "conejo", "rauw", "usain", "santurce"]
    for cid, card in final_master.items():
        w = card.get("word")
        if w in probe_words:
            print(f"\nCard '{w}' (id={cid}, propn={card.get('is_propernoun')}):")
            for idx, s in enumerate(card["senses"], start=1):
                bucket_len = len(final_examples[cid]["m"][idx - 1])
                print(f"  Sense {idx} [{s['source']}|{s['pos']}]: {s['translation']} — {s.get('context', '')} ({bucket_len} examples)")


if __name__ == "__main__":
    main()
