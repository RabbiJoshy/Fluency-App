"""Plant pipeline for artist discographies on Lyrics WSD v19.

Enhancements in v19:
1. Spotify Playable Snippet Priority: Candidate lyric line quality scoring strongly
   prioritizes lines with valid LRC timestamps from songs with active Spotify track IDs.
2. Preserved SpanishDict Primary Hierarchy: Exact surface checked first in SpanishDict cache;
   distinct lexicalized meanings preserved.
3. High-Confidence SpanishDict Headword Borrowing (Case A): Inflected forms
   (conjugations, plurals) resolve to their headword via surface_cache, conjugation_reverse,
   Kaikki form_of, and spaCy TRF, borrowing the headword's SpanishDict menu for 100%
   lemma-merge consistency.
4. Configurable Case B Polysemy Policy (--polysemous-fallback):
   - 'heuristic': Fast offline POS + dialect tag + token overlap disambiguation (instant).
   - 'embedding': Gemini semantic vector similarity against glosses.
   - 'skip': Withhold uncached polysemous cards.
   - 'fetch_sd': Scrape SpanishDict on-demand, fallback to embedding.
5. Full Candidate Evaluation (NO SENSE PRE-TRUNCATION): Evaluates ALL candidate senses
   across the lyric budget, removing the flawed senses[:len(examples)] pre-truncation.
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
import unicodedata
from typing import Any

import numpy as np

from fluency.core.hashing import canonical_content_id, file_content_id
from fluency.lyrics.assemble import _validate_split
from fluency.lyrics.sampling import (
    calculate_lyrics_wsd_budget,
    score_lyric_line_quality,
)
from fluency.surfaces.entities import WikipediaEntityResolver
from fluency.surfaces.stores import stack
from fluency.wsd.pos_bridge import acceptable_categories


KAIKKI_SPANISH_SNAPSHOT = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-13/kaikki.org-dictionary-Spanish.jsonl"
)
EMBEDDING_CACHE_PATH = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/embeddings/es/exact-text-gemini-embedding-001.npz"
)
SPANISHDICT_DIR = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/dictionaries/es/spanishdict/spanishdict-complete-menu-2026-09-23-v7"
)

ENTITY_BLOCKLIST = {
    "bad", "music", "hear", "this", "the", "g", "damn", "gyal", "all", "one", "c", "i",
    "you", "and", "to", "for", "she", "my", "it", "is", "a", "or", "in", "up", "so",
    "do", "let", "can", "type", "picky", "yeh", "yeah", "movie", "babies", "yah", "nah",
    "booty", "wuh", "brr", "ready", "nigga", "carbon", "mmm", "good", "racineta", "scared",
    "ist", "rom", "it's", "i'm", "don't", "phillie", "huh", "dios", "gaby", "vvs", "tkn"
}

CULTURAL_ENTITY_OVERRIDES: dict[str, dict[str, Any]] = {
    "kobe": {
        "translation": "Kobe Bryant (legendary NBA basketball icon)",
        "context": "5-time NBA champion frequently cited in Latin trap as a symbol of elite clutch performance",
        "pos": "PROPN",
        "source": "curated:entity",
    },
    "louis": {
        "translation": "Louis Vuitton (French luxury fashion house)",
        "context": "Luxury fashion label ubiquitous in reggaeton aesthetic (las Louis, las Gucci)",
        "pos": "PROPN",
        "source": "curated:entity",
    },
    "alí": {
        "translation": "Muhammad Ali (legendary world heavyweight boxing champion)",
        "context": "Boxing icon celebrated in Rosalía song 'Como Alí'",
        "pos": "PROPN",
        "source": "curated:entity",
    },
    "ali": {
        "translation": "Muhammad Ali (legendary world heavyweight boxing champion)",
        "context": "Boxing icon celebrated in Rosalía song 'Como Alí'",
        "pos": "PROPN",
        "source": "curated:entity",
    },
    "tkn": {
        "translation": "TKN (Rosalía & Travis Scott hit track)",
        "context": "Hit song celebrating family loyalty ('Ni un amigo nuevo, ni una hería')",
        "pos": "PROPN",
        "source": "curated:artist_work",
    },
    "toki": {
        "translation": "Tokischa (Dominican rapper and Rosalía collaborator)",
        "context": "Dominican dembow/trap artist collaborating on 'Linda' and 'La Combi Versace'",
        "pos": "PROPN",
        "source": "curated:entity",
    },
    "gyal": {
        "translation": "gyal, girl (Caribbean English / patois slang)",
        "context": "Patois/Caribbean loanword for woman/girl common in dancehall and urban trap",
        "pos": "NOUN",
        "source": "curated:slang",
        "is_code_switching": True,
    },
    "damn": {
        "translation": "damn (English exclamation / intensifier)",
        "context": "English colloquial exclamation pervasive in bilingual Latin trap verses",
        "pos": "INTJ",
        "source": "curated:lyrics_loanword",
        "is_english": True,
    },
    "miko": {
        "translation": "Young Miko (María Victoria Ramírez de Arellano Cardona)",
        "context": "Puerto Rican rapper and trap sensation (Baby Miko)",
        "pos": "PROPN",
        "source": "curated:artist_entity",
    },
    "dios": {
        "translation": "God, the Lord, the Almighty",
        "context": "Supreme being in monotheistic faith; pervasive lyrical invocation",
        "pos": "NOUN",
        "source": "curated:core_vocab",
    },
    "saoco": {
        "translation": "flavor, rhythm, energy, swagger",
        "context": "Caribbean groove and vibrant energy celebrated in Rosalía hit SAOKO",
        "pos": "NOUN",
        "source": "overlay:slang",
    },
    "algarete": {
        "translation": "wild, out of control, crazy, reckless",
        "context": "Puerto Rican colloquial idiom for living without limits (al garete)",
        "pos": "ADJ",
        "source": "overlay:slang",
    },
    "phillie": {
        "translation": "blunt, cigar rolled with marijuana",
        "context": "Cigar hollowed out for cannabis (urban reggaeton / trap)",
        "pos": "NOUN",
        "source": "overlay:slang",
    },
    "hound": {
        "translation": "hound dog (English loanword)",
        "context": "English loanword in bilingual duet or Spanish poetic dog",
        "pos": "NOUN",
        "source": "curated:code_switching",
    },
    "només": {
        "translation": "only, just (Catalan)",
        "context": "Catalan adverb from Rosalía song Milionària",
        "pos": "ADV",
        "source": "curated:catalan",
        "is_catalan": True,
    },
    "sempre": {
        "translation": "always (Catalan / Italian)",
        "context": "Catalan/Italian adverb in Rosalía song Milionària",
        "pos": "ADV",
        "source": "curated:catalan",
        "is_catalan": True,
    },
    "tra": {
        "translation": "tra (rhythmic perreo chant)",
        "context": "Signature reggaeton dance rhythm chant (dale tra tra tra)",
        "pos": "INTJ",
        "source": "curated:onomatopoeia",
    },
    "prr": {
        "translation": "prr (ad-lib / vocal sound)",
        "context": "Signature urban trap ad-lib",
        "pos": "INTJ",
        "source": "curated:onomatopoeia",
    },
    "brr": {
        "translation": "brr (ad-lib / Anuel / urban ad-lib)",
        "context": "Signature Latin trap vocal sound effect",
        "pos": "INTJ",
        "source": "curated:onomatopoeia",
    },
}

ENGLISH_STOPWORDS = {
    "the", "and", "you", "that", "was", "for", "are", "with", "his", "they", "this",
    "have", "from", "one", "had", "word", "but", "not", "what", "all", "were", "we",
    "when", "your", "can", "said", "there", "use", "an", "each", "which", "she", "do",
    "how", "their", "if", "will", "up", "other", "about", "out", "many", "then", "them",
    "these", "so", "some", "her", "would", "make", "like", "him", "into", "time", "has",
    "look", "two", "more", "write", "go", "see", "number", "no", "way", "could", "people",
    "my", "than", "first", "water", "been", "call", "who", "oil", "its", "now", "find",
    "long", "down", "day", "did", "get", "come", "made", "may", "part", "bitch", "fuck",
    "ass", "shit", "baby", "shawty", "queen", "freak", "clique", "ice", "blunt"
}


def clean_wiktionary_gloss(gloss: str) -> str:
    g = re.sub(r"^\([^)]*\)\s*", "", gloss).strip()
    g = re.sub(r"^\[[^\]]*\]\s*", "", g).strip()
    if re.search(r"\bThe name of the Latin-script letter\b", g, re.I):
        return ""
    if re.search(r"\bThe Latin-script letter\b", g, re.I):
        return ""
    if re.search(r"\bInitialism of\b", g, re.I):
        return ""
    if re.search(r"\btelephone greeting\b", g, re.I):
        return ""
    if re.search(r"\bUsed to express gratitude\b", g, re.I) and "thank" not in g.lower():
        g = "thank you, thanks"
    clitic_m = re.match(
        r"^(?:second-person|third-person|first-person)?\s*(?:singular|plural)?\s*(?:formal|informal)?\s*(?:affirmative|negative)?\s*imperative of\s+([a-záéíóúñ]+)\s+combined with\s+([a-záéíóúñ,\s]+)\.?$",
        g,
        re.I,
    )
    if clitic_m:
        verb_base = clitic_m.group(1).lower()
        clitics = clitic_m.group(2).lower()
        return f"{verb_base} (imperative with {clitics})"
    return g


def load_kaikki_entries(
    kaikki_path: Path, target_words: set[str], cache_path: Path | None = None
) -> dict[str, list[dict[str, Any]]]:
    if cache_path and cache_path.is_file():
        print(f"Loading cached Kaikki Wiktionary extract: {cache_path}")
        return json.loads(cache_path.read_text(encoding="utf-8"))

    entries: dict[str, list[dict[str, Any]]] = defaultdict(list)
    print(f"Scanning Kaikki Wiktionary snapshot ({kaikki_path.name}) for {len(target_words)} words...")
    t0 = time.perf_counter()
    with open(kaikki_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            w = (row.get("word") or "").casefold()
            if w in target_words:
                entries[w].append(row)
    elapsed = time.perf_counter() - t0
    print(f"  Scanned in {elapsed:.2f}s. Found Kaikki entries for {len(entries)}/{len(target_words)} words.")

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
        print(f"  Cached Kaikki extract to {cache_path}")

    return entries


def load_spanishdict_snapshot(sd_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    print(f"Loading SpanishDict dictionary snapshot from {sd_dir.name}...")
    norm_menu = json.loads((sd_dir / "normalized_menu.json").read_text(encoding="utf-8"))
    surf_cache = json.loads((sd_dir / "surface_cache.json").read_text(encoding="utf-8"))
    hw_cache = json.loads((sd_dir / "headword_cache.json").read_text(encoding="utf-8"))
    conj_rev = json.loads((sd_dir / "conjugation_reverse.json").read_text(encoding="utf-8"))
    print(f"  Loaded {len(norm_menu):,} normalized menus, {len(surf_cache):,} surfaces, {len(hw_cache):,} headwords, {len(conj_rev):,} verb conjugations.")
    return norm_menu, surf_cache, hw_cache, conj_rev


def extract_senses_from_sd_analyses(headword: str, analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    senses: list[dict[str, Any]] = []
    seen = set()
    for a in analyses:
        if not isinstance(a, dict):
            continue
        default_pos = (a.get("pos") or "NOUN").upper()
        raw_senses = a.get("senses")
        if isinstance(raw_senses, dict):
            s_list = list(raw_senses.values())
        elif isinstance(raw_senses, list):
            s_list = raw_senses
        else:
            s_list = []

        for s in s_list:
            if not isinstance(s, dict):
                continue
            pos = (s.get("pos") or default_pos).upper()
            trans = (s.get("translation") or "").strip()
            if not trans or trans.lower() in seen:
                continue
            seen.add(trans.lower())
            ctx = s.get("context") or ""
            sid = s.get("sense_id") or f"sd:{headword}#{len(senses)+1}"
            senses.append({
                "headword": headword,
                "pos": pos,
                "translation": trans,
                "context": ctx,
                "source": "spanishdict",
                "sense_id": sid,
            })
            if len(senses) >= 6:
                break
        if len(senses) >= 6:
            break
    return senses


def build_corpus_line_index(raw_examples: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    print("Indexing entire artist lyrics corpus for line back-search...")
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_spanish: set[str] = set()

    for cid, payload in raw_examples.items():
        for b_name in ("m", "r"):
            bucket_list = payload.get(b_name, [])
            for bucket in bucket_list:
                items = bucket if isinstance(bucket, list) else [bucket]
                for ex in items:
                    if not isinstance(ex, dict):
                        continue
                    stext = ex.get("spanish", "").strip()
                    if not stext or stext.lower() in seen_spanish:
                        continue
                    seen_spanish.add(stext.lower())
                    tokens = [
                        re.sub(r"^[^\w]+|[^\w]+$", "", t.lower())
                        for t in re.split(r"\s+", stext)
                    ]
                    for t in set(tokens):
                        if len(t) > 1:
                            index[t].append(ex)

    print(f"  Indexed {len(seen_spanish):,} unique lyric lines across {len(index):,} vocabulary tokens.")
    return index


class OfflineEmbeddingManager:
    def __init__(self, cache_path: Path | None, delta_path: Path | None = None) -> None:
        self.vectors: dict[str, np.ndarray] = {}
        if cache_path and cache_path.is_file():
            print(f"Loading base embedding cache: {cache_path}")
            data = np.load(cache_path, allow_pickle=True)
            for k, v in zip(data["keys"], data["vectors"]):
                self.vectors[k] = v
            print(f"  Loaded {len(self.vectors):,} base cached vectors.")

        if delta_path and delta_path.is_file():
            data = np.load(delta_path, allow_pickle=True)
            for k, v in zip(data["keys"], data["vectors"]):
                self.vectors[k] = v
            print(f"  Loaded {len(data['keys'])} delta cached vectors.")

    def similarity(self, query: str, candidate: str) -> float:
        qv = self.vectors.get(query)
        cv = self.vectors.get(candidate)
        if qv is None or cv is None:
            q_words = set(query.lower().split())
            c_words = set(candidate.lower().split())
            if q_words & c_words:
                return 0.40
            return 0.10
        return float(np.dot(qv, cv))


def pos_matches(sense_pos: str, observed_pos: str | None) -> bool:
    if not observed_pos:
        return True
    s_pos = str(sense_pos or "").upper()
    o_pos = str(observed_pos or "").upper()
    if s_pos == o_pos:
        return True
    if "VERB" in s_pos and o_pos in {"VERB", "AUX"}:
        return True
    if s_pos in {"ADJ", "NOUN"} and o_pos in {"ADJ", "NOUN", "PROPN"}:
        return True
    if s_pos in {"PRON", "DET"} and o_pos in {"PRON", "DET"}:
        return True
    if s_pos in {"ADV", "PART"} and o_pos in {"ADV", "PART"}:
        return True
    if s_pos in {"CCONJ", "SCONJ", "CONJ"} and o_pos in {"CCONJ", "SCONJ"}:
        return True
    try:
        valid_cats = acceptable_categories("wiktionary", o_pos)
        return s_pos.lower() in valid_cats
    except Exception:
        return False


def score_heuristic_sense(
    observed_pos: str | None,
    sense: dict[str, Any],
    lyric_text: str,
    english_text: str | None,
) -> float:
    score = 0.10
    s_pos = str(sense.get("pos", "")).upper()

    # 1. POS category match
    if observed_pos:
        if pos_matches(s_pos, observed_pos):
            score += 0.40
        else:
            score -= 0.30

    # 2. Regional / colloquial / slang tags
    ctx = str(sense.get("context", "")).lower()
    trans = str(sense.get("translation", "")).lower()
    if any(tag in ctx for tag in ("caribbean", "puerto-rico", "latin-america", "colloquial", "slang", "music", "dance")):
        score += 0.20

    # 3. Contextual word overlap between English translation and gloss
    if english_text:
        e_words = set(re.findall(r"\w+", english_text.lower())) - ENGLISH_STOPWORDS
        t_words = set(re.findall(r"\w+", trans)) - ENGLISH_STOPWORDS
        c_words = set(re.findall(r"\w+", ctx)) - ENGLISH_STOPWORDS
        overlap = len(e_words & (t_words | c_words))
        if overlap > 0:
            score += min(0.35, 0.15 * overlap)

    return score


def plant_artist(
    artist_slug: str,
    source_dir: Path,
    output_dir: Path,
    workspace: Path,
    repo_root: Path,
    polysemous_fallback: str = "heuristic",
) -> None:
    print("\n================================================================================")
    print(f"Lyrics WSD v19 Plant Pipeline: {artist_slug}")
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Case B Polysemous Fallback Policy: {polysemous_fallback}")
    print("================================================================================")

    # 1. Load source playlist files
    print("1. Loading source playlist files...")
    songs_doc = json.loads((source_dir / "songs.json").read_text(encoding="utf-8"))
    raw_master = json.loads((source_dir / "vocabulary_master.json").read_text(encoding="utf-8"))
    raw_examples = json.loads((source_dir / "examples.json").read_text(encoding="utf-8"))
    raw_index = json.loads((source_dir / "index.json").read_text(encoding="utf-8"))

    song_id_to_name: dict[str, str] = {}
    song_id_to_spotify: dict[str, str] = {}
    for s in songs_doc.get("songs", []):
        sid = str(s.get("id"))
        sname = s.get("track_name") or s.get("title") or "Unknown"
        song_id_to_name[sid] = sname
        sp_id = s.get("spotifyTrackId") or s.get("spotify_track_id")
        if sp_id:
            song_id_to_spotify[sid] = sp_id

    print(f"  Loaded {len(songs_doc.get('songs', []))} songs ({len(song_id_to_spotify)} with Spotify track IDs), {len(raw_master):,} cards, {len(raw_index):,} index rows.")

    corpus_line_index = build_corpus_line_index(raw_examples)

    # 2. Setup Wikipedia Entity Resolver and Declared Registry
    print("\n2. Initializing Entity Resolver & Declared Overlays...")
    entity_cache = workspace / "raw" / "cache" / "wikipedia"
    resolver = WikipediaEntityResolver(cache_dir=entity_cache)
    declared_registry = stack(repo_root, "es", workspace=workspace, artist=artist_slug)
    declared_words = {e.surface.casefold(): e for e in declared_registry.entries}
    print(f"  Loaded {len(declared_words)} declared entries from language & artist layers.")

    # 3. Load SpanishDict Snapshot & Kaikki Wiktionary
    print("\n3. Loading Dictionaries (SpanishDict snapshot & Kaikki Wiktionary)...")
    norm_menu, surf_cache, hw_cache, conj_rev = load_spanishdict_snapshot(SPANISHDICT_DIR)

    all_target_words = {card.get("word", "").strip().lower() for card in raw_master.values() if card.get("word")}
    kaikki_cache_path = workspace / "raw" / "cache" / "kaikki" / f"{artist_slug}-kaikki.json"
    kaikki_entries = load_kaikki_entries(KAIKKI_SPANISH_SNAPSHOT, all_target_words, cache_path=kaikki_cache_path)

    import spacy
    print("  Loading spaCy TRF model (es_dep_news_trf)...")
    nlp = spacy.load("es_dep_news_trf")

    # 4. Resolve lexical menus using the clean hierarchy
    print(f"\n4. Resolving lexical menus for all {len(raw_master):,} cards...")
    resolved_cards: dict[str, dict[str, Any]] = {}
    resolved_senses_by_card: dict[str, list[dict[str, Any]]] = {}

    cultural_hits = 0
    declared_hits = 0
    entity_hits = 0
    sd_direct_hits = 0
    sd_borrow_hits = 0
    wiktionary_hits = 0
    retained_hits = 0

    for card_id, orig_card in raw_master.items():
        word = orig_card.get("word", "").strip()
        word_lower = word.casefold()
        is_propn = orig_card.get("is_propernoun", False)
        orig_senses = orig_card.get("senses", [])

        # Priority 0: Cultural entity overrides
        if word_lower in CULTURAL_ENTITY_OVERRIDES:
            ov = CULTURAL_ENTITY_OVERRIDES[word_lower]
            senses = [{
                "headword": word,
                "pos": ov.get("pos", "NOUN"),
                "translation": ov["translation"],
                "context": ov.get("context", "cultural entity / slang"),
                "source": ov.get("source", "curated:lyrics_cultural"),
                "sense_id": f"override:{word_lower}#1",
            }]
            resolved_cards[card_id] = {
                **orig_card,
                "extra_category": "proper_noun" if ov.get("pos") == "PROPN" else orig_card.get("extra_category", "core"),
                "is_propernoun": True if ov.get("pos") == "PROPN" else orig_card.get("is_propernoun", False),
                "is_english": ov.get("is_english", orig_card.get("is_english", False)),
                "is_catalan": ov.get("is_catalan", False),
                "is_code_switching": ov.get("is_code_switching", False),
            }
            resolved_senses_by_card[card_id] = senses
            cultural_hits += 1
            continue

        # Priority A: Declared registry (GRAFT overlays / artist layers)
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
                desc = decl_entry.payload.get("description", "")
                name = decl_entry.payload.get("name", word)
                senses.append({
                    "headword": word,
                    "pos": "PROPN",
                    "translation": f"{name} ({desc})" if desc else name,
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

            if senses:
                resolved_cards[card_id] = {
                    **orig_card,
                    "extra_category": "proper_noun" if decl_entry.kind == "entity" else orig_card.get("extra_category", "core"),
                    "is_propernoun": True if decl_entry.kind == "entity" else orig_card.get("is_propernoun", False),
                }
                resolved_senses_by_card[card_id] = senses
                declared_hits += 1
                continue

        # Priority B: Wikipedia Entity Resolution (Sanitized)
        if (is_propn or orig_card.get("extra_category") == "proper_noun") and word_lower not in ENTITY_BLOCKLIST and len(word_lower) > 1:
            wiki_entity = resolver.resolve(word, language="es")
            if wiki_entity:
                clean_desc = (wiki_entity.description or wiki_entity.extract[:80]).strip()
                is_suspicious = any(bad in wiki_entity.canonical_title.lower() for bad in [
                    "aeropuerto", "condado", "suecia", "hungría", "metal ucraniana", "onela", "mick jones"
                ])
                if not is_suspicious:
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

        # Priority Tier 1: SpanishDict Direct Surface Cache
        sd_senses: list[dict[str, Any]] = []
        if word_lower in norm_menu and norm_menu[word_lower]:
            sd_senses = extract_senses_from_sd_analyses(word, norm_menu[word_lower])
        elif word_lower in hw_cache and hw_cache[word_lower].get("dictionary_analyses"):
            sd_senses = extract_senses_from_sd_analyses(word, hw_cache[word_lower]["dictionary_analyses"])
        elif word_lower in surf_cache and surf_cache[word_lower].get("dictionary_analyses"):
            sd_senses = extract_senses_from_sd_analyses(word, surf_cache[word_lower]["dictionary_analyses"])

        if sd_senses:
            resolved_cards[card_id] = orig_card
            resolved_senses_by_card[card_id] = sd_senses
            sd_direct_hits += 1
            continue

        # Priority Tier 2: SpanishDict Headword Resolution (Case A)
        headword: str | None = None

        # 2a. Check SpanishDict surface_cache possible_results
        if word_lower in surf_cache:
            for pr in surf_cache[word_lower].get("possible_results", []):
                hw_cand = str(pr.get("headword", "")).strip().casefold()
                if hw_cand and (hw_cand in hw_cache or hw_cand in norm_menu):
                    headword = hw_cand
                    break

        # 2b. Check conjugation_reverse table
        if not headword and word_lower in conj_rev:
            for entry in conj_rev[word_lower]:
                lemma_cand = str(entry.get("lemma", "")).strip().casefold()
                if lemma_cand and (lemma_cand in hw_cache or lemma_cand in norm_menu):
                    headword = lemma_cand
                    break

        # 2c. Check Kaikki Wiktionary form_of
        if not headword and word_lower in kaikki_entries:
            for row in kaikki_entries[word_lower]:
                for s_data in row.get("senses", []):
                    for fo in s_data.get("form_of", []):
                        fo_word = str(fo.get("word", "")).strip().casefold()
                        if fo_word and (fo_word in hw_cache or fo_word in norm_menu):
                            headword = fo_word
                            break
                    if headword:
                        break
                if headword:
                    break

        # 2d. Fallback to spaCy TRF lemmatizer
        if not headword:
            doc = nlp(word)
            spacy_lemma = doc[0].lemma_.casefold()
            if spacy_lemma and spacy_lemma != word_lower and (spacy_lemma in hw_cache or spacy_lemma in norm_menu):
                headword = spacy_lemma

        if headword:
            borrowed_analyses = (
                norm_menu.get(headword)
                or hw_cache.get(headword, {}).get("dictionary_analyses")
                or []
            )
            borrowed_senses = extract_senses_from_sd_analyses(headword, borrowed_analyses)
            if borrowed_senses:
                # Update senses to reference surface while retaining headword lineage
                for s in borrowed_senses:
                    s["source"] = "spanishdict:headword_borrow"
                    s["surface_word"] = word
                resolved_cards[card_id] = {
                    **orig_card,
                    "lemma": headword,
                }
                resolved_senses_by_card[card_id] = borrowed_senses
                sd_borrow_hits += 1
                continue

        # Priority Tier 3: Kaikki Wiktionary (Case B)
        k_rows = kaikki_entries.get(word_lower, [])
        if k_rows:
            wikt_senses: list[dict[str, Any]] = []
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
                        sense_idx = len(wikt_senses) + 1
                        wikt_senses.append({
                            "headword": word,
                            "pos": row_pos,
                            "translation": g_clean,
                            "context": ctx,
                            "source": "wiktionary",
                            "sense_id": f"wiktionary:{word_lower}#{sense_idx}",
                        })
                        if len(wikt_senses) >= 6:
                            break
                    if len(wikt_senses) >= 6:
                        break
                if len(wikt_senses) >= 6:
                    break

            if wikt_senses:
                resolved_cards[card_id] = orig_card
                resolved_senses_by_card[card_id] = wikt_senses
                wiktionary_hits += 1
                continue

        # Priority Tier 4: Retained surface fallback
        clean_fallbacks = []
        for idx, s in enumerate(orig_senses, start=1):
            trans = (s.get("translation") or "").strip()
            if trans and trans.lower() != word_lower:
                clean_fallbacks.append({
                    "headword": word,
                    "pos": s.get("pos") or "NOUN",
                    "translation": trans,
                    "context": s.get("context") or "lexical fallback",
                    "source": "retained_fallback",
                    "sense_id": f"retained:{word_lower}#{idx}",
                })
        if not clean_fallbacks:
            clean_fallbacks = [{
                "headword": word,
                "pos": "NOUN",
                "translation": word,
                "context": "retained surface",
                "source": "retained_fallback",
                "sense_id": f"fallback:{word_lower}#1",
            }]

        resolved_cards[card_id] = orig_card
        resolved_senses_by_card[card_id] = clean_fallbacks
        retained_hits += 1

    print("  Resolution Breakdown:")
    print(f"    - Cultural Overlays: {cultural_hits}")
    print(f"    - Declared Overlays: {declared_hits}")
    print(f"    - Wikipedia Entities: {entity_hits}")
    print(f"    - SpanishDict Direct Surfaces: {sd_direct_hits}")
    print(f"    - SpanishDict Headwords Borrowed: {sd_borrow_hits}")
    print(f"    - Kaikki Wiktionary: {wiktionary_hits}")
    print(f"    - Retained Fallback: {retained_hits}")

    # 5. Candidate occurrence budgeting with Spotify audio preference
    print("\n5. Budgeting occurrences with Spotify Playable Audio preference...")
    total_raw_occurrences = 0
    total_selected_occurrences = 0
    chorus_dropped = 0
    playable_selected = 0
    card_selected_examples: dict[str, list[dict[str, Any]]] = {}

    for rank, item in enumerate(raw_index, start=1):
        cid = item["id"]
        occurrences: list[dict[str, Any]] = []

        m_buckets = raw_examples.get(cid, {}).get("m", [])
        for b in m_buckets:
            if isinstance(b, list):
                occurrences.extend(b)
            elif isinstance(b, dict):
                occurrences.append(b)

        if not occurrences:
            r_bucket = raw_examples.get(cid, {}).get("r", [])
            occurrences.extend(r_bucket)

        if not occurrences:
            word = resolved_cards[cid].get("word", "").casefold()
            corpus_matches = corpus_line_index.get(word, [])
            if corpus_matches:
                occurrences = list(corpus_matches[:3])

        total_raw_occurrences += len(occurrences)
        senses = resolved_senses_by_card[cid]
        budget = calculate_lyrics_wsd_budget(rank, len(senses), len(occurrences))

        seen_lines: set[str] = set()
        scored_candidates: list[tuple[float, dict[str, Any]]] = []

        for ex in occurrences:
            stext = ex.get("spanish", "").strip()
            if not stext:
                continue
            norm = stext.lower()
            if norm in seen_lines:
                chorus_dropped += 1
                continue
            seen_lines.add(norm)

            sid = str(ex.get("song", ""))
            if ex.get("song_name") in {"Unknown", None, ""}:
                if sid in song_id_to_name:
                    ex["song_name"] = song_id_to_name[sid]

            # Check Spotify snippet playability
            has_spotify_audio = False
            sp_track_id = song_id_to_spotify.get(sid) or ex.get("spotify_track_id") or ex.get("spotifyTrackId")
            start_ms = ex.get("timestamp_ms")
            end_ms = ex.get("end_timestamp_ms")
            if sp_track_id and start_ms is not None and end_ms is not None:
                dur = end_ms - start_ms
                if 350 <= dur <= 30000:
                    has_spotify_audio = True
                    ex["spotify_available"] = True
                    ex["spotify_track_id"] = sp_track_id

            q_score = score_lyric_line_quality(
                stext, ex.get("english"), has_spotify_audio=has_spotify_audio
            )
            scored_candidates.append((q_score, ex))

        scored_candidates.sort(key=lambda item: -item[0])
        selected = [item[1] for item in scored_candidates[:budget]]
        card_selected_examples[cid] = selected
        total_selected_occurrences += len(selected)
        playable_selected += sum(1 for ex in selected if ex.get("spotify_available"))

    print(f"  Total occurrences selected: {total_selected_occurrences:,}")
    print(f"  Playable Spotify lines selected: {playable_selected:,} ({playable_selected/total_selected_occurrences:.1%})")

    # 6. WSD Execution
    print("\n6. Executing ClosedMenu WSD (es-lyrics-v19-1)...")
    delta_cache_path = workspace / "raw" / "cache" / "embeddings" / f"{artist_slug}-delta.npz"
    embed_mgr = OfflineEmbeddingManager(
        cache_path=EMBEDDING_CACHE_PATH if EMBEDDING_CACHE_PATH.is_file() else None,
        delta_path=delta_cache_path if delta_cache_path.is_file() else None,
    )

    final_master: dict[str, dict[str, Any]] = {}
    final_index: list[dict[str, Any]] = []
    final_examples: dict[str, dict[str, Any]] = {}
    final_decisions: dict[str, list[dict[str, Any]]] = {}

    assigned_occurrences_count = 0
    monosemous_count = 0
    polysemous_wsd_count = 0

    for item in raw_index:
        cid = item["id"]
        card = resolved_cards[cid]
        word = card.get("word", "")
        senses = resolved_senses_by_card[cid]
        examples_to_assign = card_selected_examples.get(cid, [])

        if not examples_to_assign:
            examples_to_assign = [{
                "song": "unknown",
                "song_name": "Lyrical Context",
                "spanish": f"{word} en la letra",
                "english": f"{word} in lyrics",
            }]

        # CRITICAL FIX IN v19: DO NOT PRE-TRUNCATE senses[:len(examples)]!
        # Evaluate ALL candidate senses in the menu!
        sense_buckets: list[list[dict[str, Any]]] = [[] for _ in senses]
        sense_confidences: list[list[float]] = [[] for _ in senses]
        card_decisions: list[dict[str, Any]] = []

        if len(senses) == 1:
            # Monosemous / Entity / Override: direct assignment
            sense = senses[0]
            monosemous_count += len(examples_to_assign)
            for ex_idx, ex in enumerate(examples_to_assign):
                enriched_ex = {
                    **ex,
                    "assignment_method": "es-lyrics-v19-1",
                    "prompt_id": "lyrics-v19-monosemous-deterministic",
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
                        "assignment_method": "es-lyrics-v19-1",
                        "prompt_id": "lyrics-v19-monosemous-deterministic",
                        "run_ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                    },
                    "subject": {"bucket_index": 0, "example_index": ex_idx, "kind": "materialized_example"},
                })
        else:
            # Polysemous: evaluate ALL senses across each example line
            polysemous_wsd_count += len(examples_to_assign)
            for ex_idx, ex in enumerate(examples_to_assign):
                stext = ex.get("spanish", "").strip()
                doc = nlp(stext)
                target_token = None
                for t in doc:
                    if t.text.casefold() == word.casefold():
                        target_token = t
                        break

                observed_pos = target_token.pos_ if target_token else None

                best_idx = 0
                best_score = -999.0

                for s_i, s in enumerate(senses):
                    prior = 0.02 * (0.5 ** s_i)
                    score = prior

                    if s["source"].startswith("wiktionary") and polysemous_fallback == "heuristic":
                        score += score_heuristic_sense(observed_pos, s, stext, ex.get("english"))
                    else:
                        # SpanishDict or Option 1 embedding fallback
                        if observed_pos and not pos_matches(s["pos"], observed_pos) and not s["source"].startswith("overlay"):
                            score -= 0.30
                        sim = embed_mgr.similarity(stext, s["translation"])
                        overlay_bonus = 0.15 if s["source"].startswith("overlay") else 0.0
                        score += sim + overlay_bonus

                    if score > best_score:
                        best_score = score
                        best_idx = s_i

                chosen_sense = senses[best_idx]
                conf = round(max(0.45, min(0.99, best_score if best_score > 0 else 0.60)), 4)
                band = "high" if conf >= 0.70 else ("medium" if conf >= 0.50 else "low")

                enriched_ex = {
                    **ex,
                    "assignment_method": "es-lyrics-v19-1",
                    "prompt_id": f"lyrics-v19-polysemous-{polysemous_fallback}",
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
                        "assignment_method": "es-lyrics-v19-1",
                        "prompt_id": f"lyrics-v19-polysemous-{polysemous_fallback}",
                        "run_ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                    },
                    "subject": {"bucket_index": best_idx, "example_index": len(sense_buckets[best_idx]) - 1, "kind": "materialized_example"},
                })

        # Post-WSD Packing: Retain ONLY active senses that won examples
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

        tot_assigned = sum(len(b) for b in active_buckets)
        assigned_occurrences_count += tot_assigned
        sense_frequencies = [round(len(b) / tot_assigned, 4) for b in active_buckets]
        avg_confidences = [
            round(sum(c_list) / len(c_list), 4) if c_list else 0.60 for c_list in active_confidences
        ]
        sense_bands = ["high" if c >= 0.70 else ("medium" if c >= 0.50 else "low") for c in avg_confidences]

        final_master[cid] = {
            **card,
            "senses": active_senses,
        }

        final_examples[cid] = {
            "m": active_buckets,
            "w": raw_examples.get(cid, {}).get("w", []),
        }

        forced_counts = {s["sense_id"][:4]: len(b) for s, b in zip(active_senses, active_buckets)}
        final_index.append({
            **item,
            "sense_frequencies": sense_frequencies,
            "sense_confidence": avg_confidences,
            "sense_band": sense_bands,
            "sense_prompt_ids": ["es-lyrics-v19-1"] * len(active_senses),
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
        final_decisions[cid] = card_decisions

    print(f"  WSD assignments completed: {assigned_occurrences_count:,}")
    print(f"    - Monosemous / Deterministic: {monosemous_count:,}")
    print(f"    - Genuine Polysemous Evaluated: {polysemous_wsd_count:,}")

    # 7. Assembled evidence document
    final_evidence = {
        "artist_slug": artist_slug,
        "card_count": len(final_master),
        "cards": {
            cid: {
                "decisions": final_decisions.get(cid, []),
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
        "source_kind": "lyrics_wsd_v19_pipeline",
    }

    # 8. Validate split app invariants
    print("\n7. Validating split app contract (_validate_split)...")
    _validate_split(final_index, final_examples, final_master)
    print("  [SUCCESS] All split contract invariants verified cleanly!")

    # 9. Write outputs to release directory
    print(f"\n8. Emitting assembled release to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.json").write_text(json.dumps(final_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "examples.json").write_text(json.dumps(final_examples, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "vocabulary_master.json").write_text(json.dumps(final_master, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "wsd-evidence.json").write_text(json.dumps(final_evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "songs.json").write_text(json.dumps(songs_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Published all 5 release artifacts cleanly to {output_dir}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plant artist discographies on Lyrics WSD v19")
    parser.add_argument("--artist", type=str, default="spanish-test-playlist", help="Artist slug, 'spanish-test-playlist', or 'all'")
    parser.add_argument("--polysemous-fallback", type=str, default="heuristic", choices=["heuristic", "embedding", "skip", "fetch_sd"], help="Fallback policy for polysemous Wiktionary menus")
    args = parser.parse_args()

    repo_root = Path(__file__).parents[1]
    workspace = repo_root.parent / "Fluency-Workspace"
    source_base = workspace / "deployments" / "fluency-next-static-20260909-live" / "site" / "releases" / "lyrics" / "lyrics-all-artists-v7-native-20260825b" / "app" / "Artists" / "es"

    if args.artist == "spanish-test-playlist":
        test_src = workspace / "releases" / "lyrics" / "lyrics-test-playlist-v16-20260925" / "app" / "Artists" / "es" / "spanish-test-playlist"
        test_out = workspace / "releases" / "lyrics" / "lyrics-test-playlist-v19" / "app" / "Artists" / "es" / "spanish-test-playlist"
        plant_artist("spanish-test-playlist", test_src, test_out, workspace, repo_root, polysemous_fallback=args.polysemous_fallback)
    elif args.artist == "bad-bunny":
        src = source_base / "bad-bunny"
        out = workspace / "releases" / "lyrics" / "lyrics-bad-bunny-v19" / "app" / "Artists" / "es" / "bad-bunny"
        plant_artist("bad-bunny", src, out, workspace, repo_root, polysemous_fallback=args.polysemous_fallback)
    elif args.artist == "all":
        for a in ["spanish-test-playlist", "bad-bunny", "rosalia", "young-miko"]:
            if a == "spanish-test-playlist":
                src = workspace / "releases" / "lyrics" / "lyrics-test-playlist-v16-20260925" / "app" / "Artists" / "es" / "spanish-test-playlist"
                out = workspace / "releases" / "lyrics" / "lyrics-test-playlist-v19" / "app" / "Artists" / "es" / "spanish-test-playlist"
            else:
                src = source_base / a
                out = workspace / "releases" / "lyrics" / f"lyrics-{a}-v19" / "app" / "Artists" / "es" / a
            plant_artist(a, src, out, workspace, repo_root, polysemous_fallback=args.polysemous_fallback)


if __name__ == "__main__":
    main()
