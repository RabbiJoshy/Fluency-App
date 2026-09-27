"""Plant artist discographies on Lyrics WSD v20 (profile ``es-lyrics-v20-1``).

What changed from v19 (proposal 0004, update of 2026-09-27):

1. **Menus come from the shared resolver.** Each card's headword set is
   decided by ``fluency.surfaces.resolver`` over SpanishDict then Wiktionary
   (``fluency.surfaces.provider_chain``), with declared entries at lyrics scope
   plus the artist layer. The menu is built from those headwords' entries by
   the stage-02 adapters (``fluency.sense_menu.chain_menus``). v19's tier
   chain -- hard-coded overrides, Wikipedia search, SpanishDict page /
   headword borrow, Kaikki glosses, spaCy lemma, retained fallback -- is gone.
   Its hand-written overrides moved to ``config/declared/es/lyrics-v19-curated.json``.
2. **Wiktionary parity.** Form-of glosses are never senses; the Kaikki adapter
   follows the chain to the lemma (``muerdo`` -> *morder*).
3. **Elisions** resolve through the resolver (``ta`` -> ``está`` -> *estar*),
   and are inflected for the expanded form (``he/she is``).
4. **A surface nobody answers is reported, not guessed**: it ships with an
   explicit empty meaning and its reason (``no_menu``).
5. **WSD scores the uninflected gloss**; the inflected one is for display.
   Vectors come from the shared resumable store
   (``fluency.nlp.embeddings``); the per-artist delta file is not read.

Example selection, WSD and packaging are v19's, unchanged.

    python scripts/plant_artist_v20.py --artist all --stage menus   # shadow menus only
    python scripts/plant_artist_v20.py --artist all --stage build   # releases (after sign-off)
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np

from fluency.lyrics.assemble import _validate_split
from fluency.lyrics.inflector import inflect_card_senses, inflect_clitic_memberships
from fluency.lyrics.sampling import calculate_target_occurrence_budget, score_lyric_line_quality
from fluency.nlp.embeddings import load_cache
from fluency.nlp.models import pin
from fluency.sense_menu.chain_menus import ChainMenu, build_chain_menus
from fluency.surfaces.declared import Context
from fluency.surfaces.resolver import DECLARED_GLOSS, ENTITY, NO_MENU, ModePolicy
from fluency.surfaces.stores import stack
from fluency.wsd.pos_bridge import acceptable_categories

PROFILE_ID = "es-lyrics-v20-1"
REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = REPO_ROOT.parent / "Fluency-Workspace"
ARTISTS = ("spanish-test-playlist", "bad-bunny", "rosalia", "young-miko")

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


def load_profile() -> dict[str, Any]:
    profile = json.loads((REPO_ROOT / "config/wsd/models" / f"{PROFILE_ID}.json").read_text(encoding="utf-8"))
    if profile.get("profile_id") != PROFILE_ID:
        raise SystemExit(f"profile id mismatch in {PROFILE_ID}.json")
    return profile


def source_dir(workspace: Path, artist: str) -> Path:
    """The decks v19 planted from (its ``main``), so v19 and v20 read the same cards."""
    if artist == "spanish-test-playlist":
        return workspace / "releases/lyrics/lyrics-test-playlist-v16-20260925/app/Artists/es/spanish-test-playlist"
    return (workspace / "deployments/fluency-next-static-20260909-live/site/releases/lyrics"
            / "lyrics-all-artists-v7-native-20260825b/app/Artists/es" / artist)


def output_dir(workspace: Path, artist: str) -> Path:
    name = "lyrics-test-playlist-v20" if artist == "spanish-test-playlist" else f"lyrics-{artist}-v20"
    return workspace / "releases/lyrics" / name / "app/Artists/es" / artist


# --------------------------------------------------------------------- menus

def card_surfaces(orig_card: dict[str, Any]) -> tuple[str, str]:
    """(surface resolved, surface inflected for). v19's rule for merged clitics."""
    word = orig_card.get("word", "").strip()
    merged = orig_card.get("merged_clitic_ids") or {}
    clitics = [cl.strip() for cl in merged.values() if cl.strip()]
    if clitics and (word.endswith("se") or word.casefold() in {"guillar", "guillarse"}):
        orig_card["display_form"] = clitics[0]
        return word.casefold(), clitics[0]
    return word.casefold(), orig_card.get("display_form") or word


def _source_of(adapter: str) -> str:
    if adapter.startswith("spanishdict"):
        return "spanishdict"
    if adapter.startswith("wiktionary"):
        return "wiktionary"
    return "declared:entity" if "entity" in adapter else "declared:gloss"


def menu_senses(menu: ChainMenu, cap: int) -> list[dict[str, Any]]:
    """Lyric-card senses from a chain menu, uninflected, in provider order."""
    records = {h.headword: h for h in menu.resolution.headwords}
    senses: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    per_headword: Counter[str] = Counter()
    for analysis in menu.analyses:
        headword = analysis["headword"]
        source = _source_of(analysis["source_adapter"])
        for leaf in analysis["senses"]:
            text = str(leaf.get("translation") or "").strip()
            definition = str(leaf.get("definition") or "").strip()
            if source == "declared:entity" and definition:
                text = f"{text} ({definition})"
            if not text or (headword.casefold(), text.casefold()) in seen:
                continue
            if source in ("spanishdict", "wiktionary") and per_headword[headword] >= cap:
                continue
            seen.add((headword.casefold(), text.casefold()))
            per_headword[headword] += 1
            record = records.get(headword)
            senses.append({
                "headword": headword,
                "pos": str(analysis["part_of_speech"]).upper(),
                "translation": text,
                "gloss_base": text,
                "context": definition,
                "source": source,
                "sense_id": leaf["sense_id"],
                **({"headword_provenance": record.provenance, "headword_trust": record.trust}
                   if record else {}),
            })
    return senses


def overlay_senses(entry: Any) -> list[dict[str, Any]]:
    """A declared gloss competing beside a provider menu (GRAFT's overlays)."""
    cls = entry.payload.get("class", "slang")
    return [{
        "headword": entry.surface,
        "pos": str(s.get("pos") or "NOUN").upper(),
        "translation": s["translation"],
        "gloss_base": s["translation"],
        "context": s.get("definition", "declared overlay"),
        "source": f"overlay:{cls}",
        "sense_id": f"{entry.entry_id}#{i}",
    } for i, s in enumerate(entry.senses, start=1)]


def card_lemma(orig_card: dict[str, Any], menu: ChainMenu) -> str:
    """The lookup lemma the app merges by: v19's lemma if the resolver agrees, else the resolver's."""
    heads = menu.resolution.headwords
    names = [h.headword for h in heads]
    if orig_card.get("lemma") in names:
        return orig_card["lemma"]
    for relation in ("form", "enclitic", "override", "self"):
        for h in heads:
            if h.relation == relation:
                return h.headword
    return orig_card.get("lemma") or orig_card.get("word", "")


def resolve_menus(artist: str, raw_master: dict[str, Any], *, workspace: Path = WORKSPACE,
                  profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Every card's v20 menu, before inflection. Shared by the plant and the shadow diff."""
    profile = profile or load_profile()
    menu_cfg = profile["menu"]
    registry = stack(REPO_ROOT, "es", workspace=workspace, artist=artist)
    context = Context(language="es", mode="lyrics", artist=artist)
    policy = ModePolicy.load(REPO_ROOT / menu_cfg["strategy_policy"], "lyrics")
    surfaces = {cid: card_surfaces(card) for cid, card in raw_master.items()}
    menus, pinned = build_chain_menus(
        REPO_ROOT, [s for s, _ in surfaces.values()],
        spanishdict_snapshot=workspace / menu_cfg["spanishdict_snapshot"],
        kaikki_snapshot=workspace / menu_cfg["wiktionary_snapshot"],
        registry=registry, context=context, policy=policy,
        spanishdict_policy_id=menu_cfg["spanishdict_policy_id"],
        wiktionary_policy_id=menu_cfg["wiktionary_policy_id"])
    cards: dict[str, Any] = {}
    for cid, (surface, inflect_as) in surfaces.items():
        menu = menus[surface]
        senses = menu_senses(menu, int(menu_cfg["max_senses_per_headword"]))
        overlay = None
        if menu.resolution.strategy != DECLARED_GLOSS and menu_cfg.get("declared_gloss_competes_as_overlay"):
            overlay = registry.select(surface, "gloss", context, policy.minimum_trust)
            if overlay is not None:
                senses += overlay_senses(overlay)
        cards[cid] = {"surface": surface, "inflect_as": inflect_as, "menu": menu,
                      "senses": senses, "overlay": overlay.entry_id if overlay else None}
    return {"cards": cards, "pinned": pinned, "registry": registry, "context": context}


def resolution_record(menu: ChainMenu) -> dict[str, Any]:
    r = menu.resolution
    return {**r.stamp(), "reason": r.reason or None, "answered_by": menu.provider,
            "headwords": [h.to_dict() for h in r.headwords]}


def finish_card(orig_card: dict[str, Any], resolved: dict[str, Any], conj_rev: dict[str, Any],
                surf_cache: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Inflect for display, stamp the resolution, and handle an unanswered surface."""
    menu: ChainMenu = resolved["menu"]
    r = menu.resolution
    word = orig_card.get("word", "").strip()
    inflect_as = r.expanded_to or resolved["inflect_as"]
    card = {**orig_card, "word_class": r.word_class, "resolution": resolution_record(menu),
            "headwords": r.headword_names}
    if r.strategy == ENTITY:
        card.update(extra_category="proper_noun", is_propernoun=True)
    if not resolved["senses"]:
        # Invariant 2: the card says it has no meaning and why, rather than
        # echoing the word back as its own translation. menu_empty: resolved,
        # but the entries hold no translated sense.
        reason = r.reason if r.strategy == NO_MENU else "menu_empty"
        card["menu_status"] = "no_menu"
        card["resolution"]["reason"] = reason
        return card, [{
            "headword": word, "pos": orig_card.get("pos") or "X", "translation": "",
            "gloss_base": "", "context": f"no dictionary entry ({reason})",
            "source": "no_menu", "sense_id": f"no_menu:{resolved['surface']}",
        }]
    card["lemma"] = card_lemma(orig_card, menu)
    is_plural = any(pr.get("inflection_type") == "plural"
                    for pr in (surf_cache.get(inflect_as.casefold()) or {}).get("possible_results", []))
    by_headword: dict[str, list[dict[str, Any]]] = defaultdict(list)
    order: list[str] = []
    for s in resolved["senses"]:
        if s["headword"] not in by_headword:
            order.append(s["headword"])
        by_headword[s["headword"]].append(s)
    senses: list[dict[str, Any]] = []
    for headword in order:
        senses += inflect_card_senses(inflect_as, headword, by_headword[headword], conj_rev, is_plural=is_plural)
    return card, senses


# ------------------------------------------------------------ v19 selection

def normalize_lyrics_token(token: str) -> str:
    t = token.replace("’", "'").replace("‘", "'").replace("`", "'")
    return re.sub(r"^[^\w']+|[^\w']+$", "", t.lower())


def build_corpus_line_index(raw_examples: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_spanish: set[str] = set()
    for cid, payload in raw_examples.items():
        for b_name in ("m", "r", "w"):
            for bucket in payload.get(b_name, []):
                items = bucket if isinstance(bucket, list) else [bucket]
                for ex in items:
                    if not isinstance(ex, dict):
                        continue
                    stext = ex.get("spanish", "").strip()
                    if not stext or stext.lower() in seen_spanish:
                        continue
                    if ex.get("song_name") in {"Unknown", "Lyrical Context", None, ""} or "en la letra" in stext:
                        continue
                    seen_spanish.add(stext.lower())
                    for token in {normalize_lyrics_token(t) for t in re.split(r"\s+", stext)} - {""}:
                        index[token].append(ex)
    print(f"  Indexed {len(seen_spanish):,} unique lyric lines across {len(index):,} vocabulary tokens.")
    return index


def load_source(src: Path) -> dict[str, Any]:
    songs_doc = json.loads((src / "songs.json").read_text(encoding="utf-8"))
    raw_master = json.loads((src / "vocabulary_master.json").read_text(encoding="utf-8"))
    raw_examples = json.loads((src / "examples.json").read_text(encoding="utf-8"))
    raw_index = json.loads((src / "index.json").read_text(encoding="utf-8"))
    return {"songs": songs_doc, "master": raw_master, "examples": raw_examples, "index": raw_index}


def select_examples(source: dict[str, Any], resolved_cards: dict[str, Any],
                    senses_by_card: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """v19 step 5, unchanged: budget occurrences with the Spotify preference."""
    songs_doc, raw_examples, raw_index = source["songs"], source["examples"], source["index"]
    song_id_to_name: dict[str, str] = {}
    song_id_to_spotify: dict[str, str] = {}
    card_to_song_ids: dict[str, list[str]] = defaultdict(list)
    for s in songs_doc.get("songs", []):
        sid = str(s.get("id"))
        song_id_to_name[sid] = s.get("track_name") or s.get("title") or "Unknown"
        sp_id = s.get("spotifyTrackId") or s.get("spotify_track_id")
        if sp_id:
            song_id_to_spotify[sid] = sp_id
        for cid in s.get("cardIds", []):
            card_to_song_ids[cid].append(sid)
    corpus_line_index = build_corpus_line_index(raw_examples)
    song_id_to_valid_lines: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cid, payload in raw_examples.items():
        for b_name in ("m", "r", "w"):
            for bucket in payload.get(b_name, []):
                items = bucket if isinstance(bucket, list) else [bucket]
                for ex in items:
                    if not isinstance(ex, dict):
                        continue
                    sid = str(ex.get("song", ""))
                    stext = ex.get("spanish", "").strip()
                    if sid and stext and ex.get("song_name") not in {"Unknown", "Lyrical Context", None, ""} and "en la letra" not in stext:
                        song_id_to_valid_lines[sid].append(ex)

    card_selected_examples: dict[str, list[dict[str, Any]]] = {}
    total_selected = playable = 0
    for rank, item in enumerate(raw_index, start=1):
        cid = item["id"]
        card = resolved_cards[cid]
        target_budget = calculate_target_occurrence_budget(rank, len(senses_by_card[cid]))
        occurrences: list[dict[str, Any]] = []
        for b in raw_examples.get(cid, {}).get("m", []):
            if isinstance(b, list):
                occurrences.extend(b)
            elif isinstance(b, dict):
                occurrences.append(b)
        if not occurrences:
            occurrences.extend(raw_examples.get(cid, {}).get("r", []))
        occurrences = [ex for ex in occurrences
                       if ex.get("song_name") not in {"Unknown", "Lyrical Context", None, ""}
                       and "en la letra" not in ex.get("spanish", "")]
        if len(occurrences) < target_budget:
            word_str = normalize_lyrics_token(card.get("word", ""))
            lemma_str = normalize_lyrics_token(card.get("lemma", ""))
            disp_str = normalize_lyrics_token(card.get("display_form") or "")
            clitic_terms = [normalize_lyrics_token(cl) for cl in card.get("merged_clitic_ids", {}).values()]
            variant_terms = [normalize_lyrics_token(v) for v in item.get("variants", [])]
            search_terms: list[str] = []
            for t in [disp_str, word_str] + clitic_terms + variant_terms:
                if t and t not in search_terms:
                    search_terms.append(t)
            if word_str == lemma_str or not search_terms:
                if lemma_str and lemma_str not in search_terms:
                    search_terms.append(lemma_str)
            seen_sp = {ex.get("spanish", "").strip().lower() for ex in occurrences}
            for term in search_terms:
                for match_ex in corpus_line_index.get(term, []):
                    sp_text = match_ex.get("spanish", "").strip().lower()
                    if sp_text not in seen_sp:
                        seen_sp.add(sp_text)
                        cloned = dict(match_ex)
                        cloned["surface"] = term
                        occurrences.append(cloned)
                        if len(occurrences) >= target_budget:
                            break
                if len(occurrences) >= target_budget:
                    break
        if not occurrences:
            for l_sid in card_to_song_ids.get(cid, []):
                song_lines = song_id_to_valid_lines.get(l_sid, [])
                if song_lines:
                    cloned = dict(song_lines[0])
                    cloned["surface"] = card.get("display_form") or card.get("word") or ""
                    occurrences.append(cloned)
                    break
        budget = min(len(occurrences), target_budget) if occurrences else 0
        seen_lines: set[str] = set()
        scored: list[tuple[float, dict[str, Any]]] = []
        for ex in occurrences:
            stext = ex.get("spanish", "").strip()
            if not stext or stext.lower() in seen_lines:
                continue
            seen_lines.add(stext.lower())
            sid = str(ex.get("song", ""))
            if ex.get("song_name") in {"Unknown", None, ""} and sid in song_id_to_name:
                ex["song_name"] = song_id_to_name[sid]
            has_audio = False
            sp_track_id = song_id_to_spotify.get(sid) or ex.get("spotify_track_id") or ex.get("spotifyTrackId")
            start_ms, end_ms = ex.get("timestamp_ms"), ex.get("end_timestamp_ms")
            if sp_track_id and start_ms is not None and end_ms is not None and 350 <= end_ms - start_ms <= 30000:
                has_audio = True
                ex["spotify_available"] = True
                ex["spotify_track_id"] = sp_track_id
            scored.append((score_lyric_line_quality(stext, ex.get("english"), has_spotify_audio=has_audio), ex))
        scored.sort(key=lambda item: -item[0])
        selected = [item[1] for item in scored[:budget]]
        card_selected_examples[cid] = selected
        total_selected += len(selected)
        playable += sum(1 for ex in selected if ex.get("spotify_available"))
    print(f"  Total occurrences selected: {total_selected:,} (playable Spotify lines {playable:,})")
    return {"selected": card_selected_examples, "card_to_song_ids": card_to_song_ids,
            "song_id_to_valid_lines": song_id_to_valid_lines}


# ------------------------------------------------------------------ v19 WSD

class StoreEmbeddings:
    """Vectors from the shared resumable store; word overlap when a side is missing (v19)."""

    def __init__(self, cache_path: Path, overlap_scores: tuple[float, float]) -> None:
        print(f"Loading shared embedding store: {cache_path}")
        self.vectors = load_cache(cache_path)
        print(f"  {len(self.vectors):,} vectors.")
        self.hit, self.miss = overlap_scores
        self.pairs_scored = 0
        self.pairs_uncached = 0

    def similarity(self, query: str, candidate: str) -> float:
        qv, cv = self.vectors.get(query), self.vectors.get(candidate)
        self.pairs_scored += 1
        if qv is None or cv is None:
            self.pairs_uncached += 1
            return self.hit if set(query.lower().split()) & set(candidate.lower().split()) else self.miss
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
        return s_pos.lower() in acceptable_categories("wiktionary", o_pos)
    except Exception:
        return False


def score_heuristic_sense(observed_pos: str | None, sense: dict[str, Any], english_text: str | None) -> float:
    score = 0.10
    s_pos = str(sense.get("pos", "")).upper()
    if observed_pos:
        score += 0.40 if pos_matches(s_pos, observed_pos) else -0.30
    ctx = str(sense.get("context", "")).lower()
    trans = str(sense.get("gloss_base") or sense.get("translation", "")).lower()
    if any(tag in ctx for tag in ("caribbean", "puerto-rico", "latin-america", "colloquial", "slang", "music", "dance")):
        score += 0.20
    if english_text:
        e_words = set(re.findall(r"\w+", english_text.lower())) - ENGLISH_STOPWORDS
        t_words = set(re.findall(r"\w+", trans)) - ENGLISH_STOPWORDS
        c_words = set(re.findall(r"\w+", ctx)) - ENGLISH_STOPWORDS
        overlap = len(e_words & (t_words | c_words))
        if overlap > 0:
            score += min(0.35, 0.15 * overlap)
    return score


def embedding_scored(sense: dict[str, Any], polysemous_fallback: str) -> bool:
    """Whether v19's WSD scores this sense by embedding rather than the heuristic."""
    return not (sense["source"].startswith("wiktionary") and polysemous_fallback == "heuristic")


def scored_strings(senses_by_card: dict[str, list[dict[str, Any]]],
                   selected: dict[str, list[dict[str, Any]]], polysemous_fallback: str) -> tuple[set[str], set[str]]:
    """Lyric lines and uninflected glosses WSD will look up, for the embedding plan."""
    lines: set[str] = set()
    glosses: set[str] = set()
    for cid, senses in senses_by_card.items():
        if len(senses) < 2:
            continue
        embedded = [s for s in senses if embedding_scored(s, polysemous_fallback)]
        if not embedded:
            continue
        glosses.update(s["gloss_base"] for s in embedded if s.get("gloss_base"))
        lines.update(ex.get("spanish", "").strip() for ex in selected.get(cid, []) if ex.get("spanish", "").strip())
    return lines, glosses


def plan_artist(artist: str, *, workspace: Path = WORKSPACE, polysemous_fallback: str = "heuristic",
                profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Menus and example selection for one artist: everything before WSD."""
    profile = profile or load_profile()
    source = load_source(source_dir(workspace, artist))
    menu_cfg = profile["menu"]
    sd_dir = workspace / menu_cfg["spanishdict_snapshot"]
    conj_rev = json.loads((sd_dir / "conjugation_reverse.json").read_text(encoding="utf-8"))
    surf_cache = json.loads((sd_dir / "surface_cache.json").read_text(encoding="utf-8"))
    print(f"\n[{artist}] resolving {len(source['master']):,} cards through the shared resolver...")
    resolved = resolve_menus(artist, source["master"], workspace=workspace, profile=profile)
    resolved_cards: dict[str, Any] = {}
    senses_by_card: dict[str, list[dict[str, Any]]] = {}
    for cid, orig in source["master"].items():
        resolved_cards[cid], senses_by_card[cid] = finish_card(orig, resolved["cards"][cid], conj_rev, surf_cache)
    strategies = Counter((c["menu"].resolution.strategy, c["menu"].provider) for c in resolved["cards"].values())
    print("  Resolution: " + ", ".join(f"{s}/{p}: {n}" for (s, p), n in strategies.most_common()))
    selection = select_examples(source, resolved_cards, senses_by_card)
    return {"artist": artist, "source": source, "resolved": resolved, "cards": resolved_cards,
            "senses": senses_by_card, "selection": selection, "conj_rev": conj_rev,
            "polysemous_fallback": polysemous_fallback}


def plant_artist(artist: str, *, workspace: Path = WORKSPACE, polysemous_fallback: str = "heuristic") -> None:
    profile = load_profile()
    wsd_cfg = profile["wsd"]
    plan = plan_artist(artist, workspace=workspace, polysemous_fallback=polysemous_fallback, profile=profile)
    source, resolved_cards, senses_by_card = plan["source"], plan["cards"], plan["senses"]
    raw_examples, raw_index, songs_doc = source["examples"], source["index"], source["songs"]
    card_selected_examples = plan["selection"]["selected"]
    card_to_song_ids = plan["selection"]["card_to_song_ids"]
    song_id_to_valid_lines = plan["selection"]["song_id_to_valid_lines"]
    conj_rev = plan["conj_rev"]

    from fluency.nlp.pos import load_pinned
    nlp = load_pinned(pin(wsd_cfg["occurrence_pos"]))
    embed = StoreEmbeddings(workspace / wsd_cfg["embedding_cache"], tuple(wsd_cfg["uncached_overlap_scores"]))
    prior_w, prior_decay = wsd_cfg["provider_prior"]["weight"], wsd_cfg["provider_prior"]["decay"]
    pos_penalty, overlay_bonus_w = wsd_cfg["pos_mismatch_penalty"], wsd_cfg["overlay_bonus"]

    final_master: dict[str, dict[str, Any]] = {}
    final_index: list[dict[str, Any]] = []
    final_examples: dict[str, dict[str, Any]] = {}
    final_decisions: dict[str, list[dict[str, Any]]] = {}
    assigned = monosemous = polysemous = 0
    trf_doc_cache: dict[str, Any] = {}
    run_ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")
    prompt_poly = f"lyrics-v20-polysemous-{polysemous_fallback}"

    print(f"\n[{artist}] ClosedMenu WSD ({PROFILE_ID})...")
    for item in raw_index:
        cid = item["id"]
        card = resolved_cards[cid]
        word = card.get("word", "")
        senses = senses_by_card[cid]
        examples_to_assign = card_selected_examples.get(cid, [])
        if not examples_to_assign:
            fallback_line = None
            for l_sid in card_to_song_ids.get(cid, []):
                if song_id_to_valid_lines.get(l_sid):
                    fallback_line = song_id_to_valid_lines[l_sid][0]
                    break
            if not fallback_line and song_id_to_valid_lines:
                fallback_line = song_id_to_valid_lines[next(iter(song_id_to_valid_lines))][0]
            examples_to_assign = [fallback_line] if fallback_line else [{
                "song": "unknown", "song_name": "Lyrical Context",
                "spanish": f"{word} en la letra", "english": f"{word} in lyrics"}]

        sense_buckets: list[list[dict[str, Any]]] = [[] for _ in senses]
        sense_confidences: list[list[float]] = [[] for _ in senses]
        card_decisions: list[dict[str, Any]] = []
        if len(senses) == 1:
            sense = senses[0]
            monosemous += len(examples_to_assign)
            for ex_idx, ex in enumerate(examples_to_assign):
                sense_buckets[0].append({**ex, "assignment_method": PROFILE_ID,
                                         "prompt_id": "lyrics-v20-monosemous-deterministic",
                                         "run_ts": run_ts, "confidence": 1.0, "band": "high"})
                sense_confidences[0].append(1.0)
                card_decisions.append({
                    "decision_id": f"decision_{cid}_{ex_idx}",
                    "forced_selection": {"selected_tuple": {"headword": sense["headword"], "part_of_speech": sense["pos"]},
                                         "sense_id": sense["sense_id"]},
                    "provenance": {"assignment_method": PROFILE_ID,
                                   "prompt_id": "lyrics-v20-monosemous-deterministic", "run_ts": run_ts},
                    "subject": {"bucket_index": 0, "example_index": ex_idx, "kind": "materialized_example"},
                })
        else:
            polysemous += len(examples_to_assign)
            for ex_idx, ex in enumerate(examples_to_assign):
                stext = ex.get("spanish", "").strip()
                if stext not in trf_doc_cache:
                    trf_doc_cache[stext] = nlp(stext)
                target_token = next((t for t in trf_doc_cache[stext] if t.text.casefold() == word.casefold()), None)
                observed_pos = target_token.pos_ if target_token else None
                best_idx, best_score = 0, -999.0
                for s_i, s in enumerate(senses):
                    score = prior_w * (prior_decay ** s_i)
                    if not embedding_scored(s, polysemous_fallback):
                        score += score_heuristic_sense(observed_pos, s, ex.get("english"))
                    else:
                        if observed_pos and not pos_matches(s["pos"], observed_pos) and not s["source"].startswith("overlay"):
                            score -= pos_penalty
                        # The uninflected gloss: the string the store holds.
                        score += embed.similarity(stext, s.get("gloss_base") or s["translation"])
                        score += overlay_bonus_w if s["source"].startswith("overlay") else 0.0
                    if score > best_score:
                        best_score, best_idx = score, s_i
                chosen = senses[best_idx]
                conf = round(max(0.45, min(0.99, best_score if best_score > 0 else 0.60)), 4)
                band = "high" if conf >= 0.70 else ("medium" if conf >= 0.50 else "low")
                sense_buckets[best_idx].append({**ex, "assignment_method": PROFILE_ID, "prompt_id": prompt_poly,
                                                "run_ts": run_ts, "confidence": conf, "band": band})
                sense_confidences[best_idx].append(conf)
                card_decisions.append({
                    "decision_id": f"decision_{cid}_{ex_idx}",
                    "forced_selection": {"selected_tuple": {"headword": chosen["headword"], "part_of_speech": chosen["pos"]},
                                         "sense_id": chosen["sense_id"]},
                    "provenance": {"assignment_method": PROFILE_ID, "prompt_id": prompt_poly, "run_ts": run_ts},
                    "subject": {"bucket_index": best_idx, "example_index": len(sense_buckets[best_idx]) - 1,
                                "kind": "materialized_example"},
                })

        active = [(s, b, c) for s, b, c in zip(senses, sense_buckets, sense_confidences) if b]
        if not active:
            active = [(senses[0], examples_to_assign, [1.0] * len(examples_to_assign))]
        active_senses = [a[0] for a in active]
        active_buckets = [a[1] for a in active]
        tot = sum(len(b) for b in active_buckets)
        assigned += tot
        avg_conf = [round(sum(a[2]) / len(a[2]), 4) if a[2] else 0.60 for a in active]
        final_master[cid] = {**card, "senses": active_senses}
        final_examples[cid] = {"m": active_buckets, "w": raw_examples.get(cid, {}).get("w", [])}
        forced_counts = {s["sense_id"][:4]: len(b) for s, b in zip(active_senses, active_buckets)}
        index_entry = {
            **item,
            "sense_frequencies": [round(len(b) / tot, 4) for b in active_buckets],
            "sense_confidence": avg_conf,
            "sense_band": ["high" if c >= 0.70 else ("medium" if c >= 0.50 else "low") for c in avg_conf],
            "sense_prompt_ids": [PROFILE_ID] * len(active_senses),
            "sense_run_ts": [run_ts] * len(active_senses),
            "wsd_distribution": {
                "denominator": tot, "distribution_version": "wsd-distribution/v1",
                "forced_leaf_counts": forced_counts, "known_leaf_mass": tot,
                "publication_projection": "forced_leaf", "published_leaf_counts": forced_counts,
                "selection_projection": "mwe_augmented", "status_counts": {"assigned": tot},
                "supported_leaf_counts": {},
                "supported_level_counts": {"glosskey": 0, "leaf": 0, "tuple": 0, "unresolved": 0},
                "supported_unavailable_mass": tot, "unresolved_mass": 0,
            },
        }
        if card.get("display_form"):
            index_entry["display_form"] = card["display_form"]
        if item.get("clitic_memberships"):
            index_entry["clitic_memberships"] = inflect_clitic_memberships(
                item["clitic_memberships"], card.get("lemma") or word,
                active_senses[0].get("translation", ""), conj_rev)
        final_index.append(index_entry)
        final_decisions[cid] = card_decisions

    print(f"  WSD assignments: {assigned:,} (monosemous {monosemous:,}, polysemous {polysemous:,})")
    if embed.pairs_scored:
        print(f"  Embedding pairs without a stored vector (word-overlap fallback): "
              f"{embed.pairs_uncached:,} of {embed.pairs_scored:,} ({embed.pairs_uncached / embed.pairs_scored:.1%})")

    final_evidence = {
        "artist_slug": artist, "card_count": len(final_master),
        "cards": {cid: {"decisions": final_decisions.get(cid, []), "distribution": final_index[i]["wsd_distribution"],
                        "lemma": final_master[cid].get("lemma", ""), "surface_form": final_master[cid].get("word", ""),
                        "resolution": final_master[cid].get("resolution")}
                  for i, cid in enumerate(final_master)},
        "decision_count": assigned, "evidence_version": "artist-wsd-evidence/v1",
        "publication_views": {"assigned": len(final_master), "total": len(final_master)},
        "selection_projection": "mwe_augmented", "source_kind": "lyrics_wsd_v20_pipeline",
        "profile_id": PROFILE_ID, "menu_provenance": plan["resolved"]["pinned"],
        "embedding_pairs": {"scored": embed.pairs_scored, "without_vector": embed.pairs_uncached},
        "polysemous_fallback": polysemous_fallback,
    }
    _validate_split(final_index, final_examples, final_master)
    out = output_dir(workspace, artist)
    out.mkdir(parents=True, exist_ok=True)
    for name, doc in (("index.json", final_index), ("examples.json", final_examples),
                      ("vocabulary_master.json", final_master), ("wsd-evidence.json", final_evidence),
                      ("songs.json", songs_doc)):
        (out / name).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--artist", default="spanish-test-playlist", choices=(*ARTISTS, "all"))
    parser.add_argument("--stage", default="menus", choices=("menus", "build"),
                        help="menus: resolve and report only (no release). build: plant releases.")
    parser.add_argument("--polysemous-fallback", default=None, choices=("heuristic", "embedding"),
                        help="How Wiktionary senses are scored; default from the profile.")
    args = parser.parse_args()
    fallback = args.polysemous_fallback or load_profile()["wsd"]["polysemous_fallback_default"]
    for artist in ARTISTS if args.artist == "all" else (args.artist,):
        if args.stage == "menus":
            plan_artist(artist, polysemous_fallback=fallback)
        else:
            plant_artist(artist, polysemous_fallback=fallback)


if __name__ == "__main__":
    sys.exit(main())
