"""Plant pipeline for artist discographies on Lyrics WSD v17.

Upgrades from v16:
1. Rescues real lyric occurrences from raw occurrences ('r') when 'm' is empty or under-budgeted,
   eliminating the 1,454 dummy '5305010/Unknown' cards across Bad Bunny, Rosalía, and Young Miko.
2. Sanitizes Wikipedia entity resolution with strict stopword, letter, and cultural relevance guards,
   eliminating false positives (Big Audio Dynamite, Aeropuerto El Arish, King Onela, Ukrainian metal band, Gyál).
3. Prunes dictionary noise senses (alphabet letter names, secondary school acronyms like ESO, telephone hello for sí).
4. Translates Wiktionary clitic meta-descriptions ('decir combined with indirect object me...') to natural human glosses.
5. Ingests expanded GRAFT-style overlays (Caribbean slang, Peninsular/flamenco idioms, discourse fillers).
6. Detects foreign language intrusions / code-switching (English, Catalan, French) and sets proper metadata.
7. Executes ClosedMenu WSD using es-lyrics-v17-1 profile with zero paid API calls.
8. Validates split app invariants (_validate_split) and publishes v17 candidate releases.
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
from fluency.lyrics.assemble import _validate_split
from fluency.lyrics.sampling import (
    calculate_lyrics_wsd_budget,
    score_lyric_line_quality,
)
from fluency.surfaces.entities import WikipediaEntityResolver
from fluency.surfaces.stores import stack
from fluency.wsd.overlays import build_lyrics_overlay_provider
from fluency.wsd.pos_bridge import acceptable_categories


KAIKKI_SPANISH_SNAPSHOT = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-13/kaikki.org-dictionary-Spanish.jsonl"
)
EMBEDDING_CACHE_PATH = Path(
    "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/embeddings/es/exact-text-gemini-embedding-001.npz"
)


# Entity guard: stopword / letter / noise blacklist for Wikipedia resolution
ENTITY_BLOCKLIST = {
    "bad", "music", "hear", "this", "the", "g", "damn", "gyal", "all", "one", "c", "i",
    "you", "and", "to", "for", "she", "my", "it", "is", "a", "or", "in", "up", "so",
    "do", "let", "can", "type", "picky", "yeh", "yeah", "movie", "babies", "yah", "nah",
    "booty", "wuh", "brr", "ready", "nigga", "carbon", "mmm", "good", "racineta", "scared",
    "ist", "rom", "it's", "i'm", "don't", "phillie", "huh", "dios", "gaby", "vvs", "tkn"
}

# Curated overrides for entities or cultural terms that Wikipedia botches
CULTURAL_ENTITY_OVERRIDES: dict[str, dict[str, Any]] = {
    "bad": {
        "translation": "bad (English loanword / part of Bad Bunny)",
        "context": "English loanword pervasive in reggaeton / trap",
        "pos": "ADJ",
        "source": "curated:lyrics_loanword",
        "is_english": True,
    },
    "music": {
        "translation": "music (English loanword / Hear This Music label)",
        "context": "English loanword and signature record label shoutout",
        "pos": "NOUN",
        "source": "curated:lyrics_loanword",
        "is_english": True,
    },
    "hear": {
        "translation": "Hear (Hear This Music record label)",
        "context": "Record label founded by DJ Luian and Mambo Kingz",
        "pos": "PROPN",
        "source": "curated:artist_label",
        "is_english": True,
    },
    "kush": {
        "translation": "kush (high-grade marijuana strain)",
        "context": "Cannabis strain celebrated in reggaeton and Latin trap (Krippy Kush)",
        "pos": "NOUN",
        "source": "curated:slang",
    },
    "krippy": {
        "translation": "kush, high-grade marijuana",
        "context": "High-potency cannabis in Latin trap (Bad Bunny Krippy Kush)",
        "pos": "NOUN",
        "source": "overlay:slang",
    },
    "lebron": {
        "translation": "LeBron James (legendary NBA basketball icon)",
        "context": "NBA superstar frequently referenced in reggaeton as a symbol of athletic greatness",
        "pos": "PROPN",
        "source": "curated:entity",
    },
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
        "context": "Boxing icon celebrated in Rosalía song 'Como Alí' ('yo brillo sola como Alí')",
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
        "context": "Hit song celebrating family omertà and loyalty ('Ni un amigo nuevo, ni una hería')",
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
    "booty": {
        "translation": "booty, butt, ass",
        "context": "Urban loanword ubiquitous in reggaeton dance tracks",
        "pos": "NOUN",
        "source": "overlay:slang",
    },
    "can": {
        "translation": "can (English modal verb / or Spanish dog/hound)",
        "context": "English modal verb in bilingual duet (Lo Vas A Olvidar) or Spanish poetic dog",
        "pos": "VERB",
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
}

# Common English stopwords to flag
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
    """Clean Wiktionary gloss text from inflection boilerplate and meta-grammar descriptions."""
    g = gloss.strip()
    
    # Noise pruning: skip alphabet letter descriptions
    if re.search(r"^(The\s+([a-z]+|\d+)\w*\s+letter of the (Spanish|Latin) alphabet|The name of the Latin script letter)", g, flags=re.IGNORECASE):
        return ""
        
    # Noise pruning: skip secondary education acronym for 'eso'
    if "Educación Secundaria Obligatoria" in g:
        return ""
        
    # Noise pruning: skip telephone greeting 'hello?' for affirmative 'sí'
    if re.search(r"^hello\?\s*\(used when answering a phone call\)", g, flags=re.IGNORECASE):
        return ""

    # Human clitic gloss translation
    clitic_maps = [
        (r"^decir combined with indirect object me and direct object lo", "tell me (it) / what's up (urban greeting)"),
        (r"^decir combined with indirect object le/les and direct object lo", "tell them (it) / tell him (it)"),
        (r"^first-person plural imperative of ir combined with nos", "let's go, let's leave"),
        (r"^ir combined with te", "go away, leave, get out"),
        (r"^second-person singular imperative combined with te", "take it, do it (imperative with te)"),
        (r"^infinitive of poner combined with se", "to put on / to become"),
        (r"^infinitive of quitar combined with se", "to take off / to remove"),
        (r"^infinitive of olvidar combined with se", "to forget"),
        (r"^infinitive of morir combined with se", "to die"),
        (r"^enseñar combined with me", "show me"),
        (r"^pasar combined with me", "pass me / hand me"),
        (r"^infinitive of quedar combined with se", "to stay, to remain"),
        (r"^infinitive of sentir combined with se", "to feel"),
        (r"^infinitive of dejar combined with se", "to let oneself, to quit"),
        (r"^infinitive of comer combined with se", "to eat up"),
        (r"^infinitive of traer combined with se", "to bring along"),
        (r"^infinitive of mirar combined with se", "to look at oneself / each other"),
        (r"^infinitive of relajar combined with se", "to relax"),
        (r"^infinitive of hacer combined with se", "to become / to play (e.g. dumb)"),
        (r"^infinitive of trepar combined with se", "to climb up"),
        (r"^infinitive of chequear combined with se", "to check oneself"),
        (r"^infinitive of escapar combined with se", "to escape, to run away"),
    ]
    for pattern, replacement in clitic_maps:
        if re.search(pattern, g, flags=re.IGNORECASE):
            return replacement

    # Strip standard inflection boilerplate
    g = re.sub(r"^(inflection of|second-person singular imperative of)\s+", "", g, flags=re.IGNORECASE)
    return g.strip()


class OfflineEmbeddingManager:
    """Manages exact-text Gemini embeddings completely offline from cached .npz files."""

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
            # Word overlap heuristic when uncached
            q_words = set(query.lower().split())
            c_words = set(candidate.lower().split())
            if q_words & c_words:
                return 0.40
            return 0.10
        return float(np.dot(qv, cv))


def main() -> None:
    parser = argparse.ArgumentParser(description="Plant artist on Lyrics WSD v17")
    parser.add_argument("--artist", type=str, required=True, help="Artist slug (e.g. bad-bunny, rosalia, young-miko)")
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    artist_slug = args.artist
    repo_root = Path(__file__).parents[1]
    workspace = repo_root.parent / "Fluency-Workspace"

    if args.source is None:
        args.source = workspace / "deployments" / "fluency-next-static-20260909-live" / "site" / "releases" / "lyrics" / "lyrics-all-artists-v7-native-20260825b" / "app" / "Artists" / "es" / artist_slug
    if args.output is None:
        args.output = workspace / "releases" / "lyrics" / f"lyrics-{artist_slug}-v17-candidate" / "app" / "Artists" / "es" / artist_slug

    print("================================================================================")
    print(f"Lyrics WSD v17 Plant Pipeline: {artist_slug}")
    print(f"Source: {args.source}")
    print(f"Output: {args.output}")
    print("================================================================================")

    # 1. Load source assets
    print("1. Loading source playlist files...")
    songs_doc = json.loads((args.source / "songs.json").read_text(encoding="utf-8"))
    raw_master = json.loads((args.source / "vocabulary_master.json").read_text(encoding="utf-8"))
    raw_examples = json.loads((args.source / "examples.json").read_text(encoding="utf-8"))
    raw_index = json.loads((args.source / "index.json").read_text(encoding="utf-8"))

    song_id_to_name = {
        str(s.get("id")): (s.get("track_name") or s.get("title") or "Unknown")
        for s in songs_doc.get("songs", [])
    }

    print(f"  Loaded {len(songs_doc.get('songs', []))} songs, {len(raw_master)} cards, {len(raw_index)} index rows.")

    # 2. Setup Wikipedia Entity Resolver and Declared Registry
    print("\n2. Initializing Entity Resolver & Declared Overlays...")
    entity_cache = workspace / "raw" / "cache" / "wikipedia"
    resolver = WikipediaEntityResolver(cache_dir=entity_cache)
    declared_registry = stack(repo_root, "es", workspace=workspace, artist=artist_slug)
    declared_words = {e.surface.casefold(): e for e in declared_registry.entries}
    print(f"  Loaded {len(declared_words)} declared entries from language & artist layers.")

    # 3. Kaikki Wiktionary Scan
    all_target_words = {card.get("word", "").strip().lower() for card in raw_master.values() if card.get("word")}
    kaikki_cache_path = workspace / "raw" / "cache" / "kaikki" / f"{artist_slug}-kaikki.json"
    kaikki_entries = load_kaikki_entries(KAIKKI_SPANISH_SNAPSHOT, all_target_words, cache_path=kaikki_cache_path)

    # 4. Resolve lexical menus for all cards
    print(f"\n3. Resolving lexical menus for all {len(raw_master):,} cards...")
    resolved_cards: dict[str, dict[str, Any]] = {}
    resolved_senses_by_card: dict[str, list[dict[str, Any]]] = {}

    entity_hits = 0
    declared_hits = 0
    wiktionary_hits = 0
    cultural_override_hits = 0
    fallback_hits = 0

    for card_id, orig_card in raw_master.items():
        word = orig_card.get("word", "").strip()
        word_lower = word.casefold()
        is_propn = orig_card.get("is_propernoun", False)
        orig_senses = orig_card.get("senses", [])

        # Priority 0: Cultural overrides (sanitizing known false-positive entity queries and slang)
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
            cultural_override_hits += 1
            continue

        # Priority A: Check declared registry (GRAFT overlays / artist layers)
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

        # Priority B: Wiktionary common definitions
        k_rows = kaikki_entries.get(word_lower, [])
        has_common_wiktionary = False
        if k_rows:
            for row in k_rows:
                r_pos = (row.get("pos") or "").lower()
                if r_pos in {"noun", "verb", "adj", "adv", "pron", "prep", "conj", "intj"}:
                    has_common_wiktionary = True
                    break

        # Priority C: Wikipedia entity resolution with strict sanitization guard
        if (is_propn or orig_card.get("extra_category") == "proper_noun") and not has_common_wiktionary:
            if word_lower not in ENTITY_BLOCKLIST and len(word_lower) > 1:
                wiki_entity = resolver.resolve(word, language="es")
                if wiki_entity:
                    clean_desc = (wiki_entity.description or wiki_entity.extract[:80]).strip()
                    # Sanity check: title must not be an obscure unhelpful disambiguation
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

        # Priority D: Wiktionary senses from Kaikki with noise sense pruning
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

        # Priority E: Retained / loanword fallback
        clean_fallbacks = []
        for idx, s in enumerate(orig_senses, start=1):
            trans = (s.get("translation") or "").strip()
            if trans and trans.lower() != word_lower:
                clean_fallbacks.append({
                    "headword": word,
                    "pos": s.get("pos") or "NOUN",
                    "translation": trans,
                    "context": s.get("context") or "lexical fallback",
                    "source": s.get("source") or "retained_fallback",
                    "sense_id": s.get("sense_id") or f"fallback:{word_lower}#{idx}",
                })
        if not clean_fallbacks:
            # If word is in English stopwords, label as English loanword
            is_eng = word_lower in ENGLISH_STOPWORDS or orig_card.get("is_english", False)
            clean_fallbacks.append({
                "headword": word,
                "pos": "NOUN",
                "translation": f"{word} (English loanword)" if is_eng else word,
                "context": "English loanword / code-switching" if is_eng else "colloquial lyrics surface",
                "source": "retained_fallback",
                "sense_id": f"fallback:{word_lower}#1",
            })
            if is_eng:
                orig_card["is_english"] = True
                orig_card["is_code_switching"] = True

        resolved_cards[card_id] = orig_card
        resolved_senses_by_card[card_id] = clean_fallbacks
        fallback_hits += 1

    print(f"  Menu resolution results:")
    print(f"    - Cultural & artist overrides: {cultural_override_hits}")
    print(f"    - Declared overlays: {declared_hits}")
    print(f"    - Sanitized Wikipedia entities: {entity_hits}")
    print(f"    - Wiktionary senses: {wiktionary_hits}")
    print(f"    - Retained/loanword fallbacks: {fallback_hits}")

    # 5. Occurrence Sampling Sieve with 'r' Raw Occurrence Rescue
    print("\n4. Applying Occurrence Sampling Sieve & Rescuing Raw 'r' Occurrences...")
    card_selected_examples: dict[str, list[dict[str, Any]]] = {}
    total_raw_occurrences = 0
    total_selected_occurrences = 0
    chorus_dropped = 0
    rescued_from_r_count = 0

    for rank, item in enumerate(raw_index, start=1):
        cid = item["id"]
        ex_data = raw_examples.get(cid, {})
        raw_buckets = ex_data.get("m", [])
        
        occurrences = []
        for b in raw_buckets:
            occurrences.extend(b)

        # RESCUE FIX: If 'm' was empty or had 0 occurrences, check 'r'!
        if not occurrences and ex_data.get("r"):
            occurrences = list(ex_data["r"])
            rescued_from_r_count += 1

        total_raw_occurrences += len(occurrences)

        # Budget calculation
        senses = resolved_senses_by_card[cid]
        budget = calculate_lyrics_wsd_budget(rank, len(senses), len(occurrences))

        # Filter and score candidates
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

            q_score = score_lyric_line_quality(stext, ex.get("english"))
            
            # Enrich missing song name from songs_doc if unknown
            sid = str(ex.get("song", ""))
            if ex.get("song_name") in {"Unknown", None, ""}:
                if sid in song_id_to_name:
                    ex["song_name"] = song_id_to_name[sid]

            scored_candidates.append((q_score, ex))

        scored_candidates.sort(key=lambda item: -item[0])
        selected = [item[1] for item in scored_candidates[:budget]]
        card_selected_examples[cid] = selected
        total_selected_occurrences += len(selected)

    print(f"  Raw occurrences scanned: {total_raw_occurrences}")
    print(f"  Cards rescued from 'r' occurrences: {rescued_from_r_count}")
    print(f"  Chorus lines deduped: {chorus_dropped}")
    print(f"  Selected for WSD budget: {total_selected_occurrences}")

    # 6. WSD Execution (Offline embedding manager)
    print("\n5. Loading embedding cache for polysemous disambiguation...")
    delta_cache_path = workspace / "raw" / "cache" / "embeddings" / f"{artist_slug}-delta.npz"
    embed_mgr = OfflineEmbeddingManager(
        cache_path=EMBEDDING_CACHE_PATH if EMBEDDING_CACHE_PATH.is_file() else None,
        delta_path=delta_cache_path if delta_cache_path.is_file() else None,
    )

    print("\n6. Executing ClosedMenu WSD (es-lyrics-v17-1)...")
    import spacy
    print("  Loading spaCy occurrence tagger (es_dep_news_trf)...")
    nlp = spacy.load("es_dep_news_trf")

    final_master: dict[str, dict[str, Any]] = {}
    final_index: list[dict[str, Any]] = []
    final_examples: dict[str, dict[str, Any]] = {}
    wsd_decisions_by_card: dict[str, list[dict[str, Any]]] = {}

    assigned_occurrences_count = 0
    dummy_fallback_used_count = 0
    t_wsd_start = time.perf_counter()

    for item in raw_index:
        cid = item["id"]
        card = resolved_cards[cid]
        word = card.get("word", "")
        senses = resolved_senses_by_card[cid]
        examples_to_assign = card_selected_examples.get(cid, [])

        if not examples_to_assign:
            # Fall back to first raw occurrence if budget had 0
            raw_b = raw_examples.get(cid, {}).get("m", [[]])
            if raw_b and raw_b[0]:
                examples_to_assign = [raw_b[0][0]]
            elif raw_examples.get(cid, {}).get("r"):
                examples_to_assign = [raw_examples[cid]["r"][0]]
            else:
                dummy_fallback_used_count += 1
                examples_to_assign = [{
                    "song": "unknown",
                    "song_name": "Lyrical Context",
                    "spanish": f"{word} en la letra",
                    "english": f"{word} in lyrics",
                }]

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
            sense = senses[0]
            for ex_idx, ex in enumerate(examples_to_assign):
                enriched_ex = {
                    **ex,
                    "assignment_method": "es-lyrics-v17-1",
                    "prompt_id": "lyrics-v17-declared-deterministic" if "overlay" in sense["source"] else "lyrics-v17-monosemous-deterministic",
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
                        "assignment_method": "es-lyrics-v17-1",
                        "prompt_id": "lyrics-v17-deterministic",
                        "run_ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                    },
                    "subject": {"bucket_index": 0, "example_index": ex_idx, "kind": "materialized_example"},
                })
        else:
            # Polysemous WSD
            for ex_idx, ex in enumerate(examples_to_assign):
                stext = ex.get("spanish", "").strip()
                doc = nlp(stext)
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
                    # prune non-clitic readings
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
                    prior = 0.02 * (0.5 ** s_i)
                    sim = embed_mgr.similarity(stext, s["translation"])
                    overlay_bonus = 0.15 if s["source"].startswith("overlay") else 0.0
                    score = sim + prior + overlay_bonus
                    if score > best_score:
                        best_score = score
                        best_idx = s_i

                chosen_sense = senses[best_idx]
                conf = round(max(0.40, min(0.99, best_score if best_score > 0 else 0.60)), 4)
                band = "high" if conf >= 0.70 else ("medium" if conf >= 0.50 else "low")

                enriched_ex = {
                    **ex,
                    "assignment_method": "es-lyrics-v17-1",
                    "prompt_id": "lyrics-v17-polysemous-embedding",
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
                        "assignment_method": "es-lyrics-v17-1",
                        "prompt_id": "lyrics-v17-polysemous-embedding",
                        "run_ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                    },
                    "subject": {"bucket_index": best_idx, "example_index": len(sense_buckets[best_idx]) - 1, "kind": "materialized_example"},
                })

        # Ensure split app invariant: Every published sense MUST have >= 1 example!
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
            round(sum(c_list) / len(c_list), 4) if c_list else 0.60 for c_list in active_confidences
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
            **item,
            "sense_frequencies": sense_frequencies,
            "sense_confidence": avg_confidences,
            "sense_band": sense_bands,
            "sense_prompt_ids": ["es-lyrics-v17-1"] * len(active_senses),
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
    print(f"  Completed WSD for {len(final_master):,} cards ({assigned_occurrences_count} occurrences) in {t_wsd_end - t_wsd_start:.2f}s.")
    print(f"  Dummy fallback lines used: {dummy_fallback_used_count} (down from v16's ~1,454).")

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
        "source_kind": "lyrics_wsd_v17_pipeline",
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

    # 10. Probe Audit (v16 vs v17 comparison)
    print("\n================================================================================")
    print(f"Probe Word Audit: Key Linguistic Markers for {artist_slug}")
    print("================================================================================")
    probe_words = ["dale", "dímelo", "vete", "saoco", "algarete", "motomami", "bizcochito", "conejo", "bad", "miko", "ducas"]
    for cid, card in final_master.items():
        w = card.get("word")
        if w in probe_words:
            print(f"\nCard '{w}' (id={cid}, propn={card.get('is_propernoun')}):")
            for idx, s in enumerate(card["senses"], start=1):
                bucket_len = len(final_examples[cid]["m"][idx - 1])
                ex_sample = final_examples[cid]["m"][idx - 1][0]
                print(f"  Sense {idx} [{s['source']}|{s['pos']}]: {s['translation']} — {s.get('context', '')} ({bucket_len} examples)")
                print(f"     Example: [{ex_sample.get('song_name')}] \"{ex_sample.get('spanish')}\" -> \"{ex_sample.get('english')}\"")


if __name__ == "__main__":
    main()
