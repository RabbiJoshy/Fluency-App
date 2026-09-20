import sys
import os
from pathlib import Path
import json

sys.path.insert(0, "src")

# load .env
env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("\"'")

from fluency.nlp.embeddings import load_cache, ensure_embeddings
from fluency.surfaces.prewsd import ID_PREFIX
from fluency.speech.wsd_execute import select_occurrences, build_analyses, EVIDENCE_GUARD_PROFILES
from fluency.wsd.sampling import sole_leaf, OccurrenceSamplingPolicy
from fluency.wsd.multiword import index_multiword_senses, multiword_analyses

W = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace")
TARGETS = [
    ("pt", "pt-v14-1", "20260915T130807Z-4120e951", "20260914T222723Z-e43a0469-v2", "mwe-pt-2026-09-18-v14-sieve"),
    ("cs", "cs-v14-1", "20260915T162357Z-ca5c81cd", "20260914T223828Z-ad405a28", "mwe-cs-2026-09-18-v14-sieve"),
]

api_key = os.getenv("GEMINI_API_KEY")
assert api_key, "GEMINI_API_KEY must be set"

for lang, profile_id, run_id, pre_id, sieve_id in TARGETS:
    run_dir = W / f"runs/{lang}/speech/{run_id}"
    prewsd_dir = W / f"raw/surfaces/{lang}/prewsd/{pre_id}"
    mwe_path = W / f"raw/mwe/{sieve_id}/mwe_merged.json"
    cache_path = W / f"embeddings/{lang}/exact-text-gemini-embedding-001.npz"

    print(f"\n=======================================================")
    print(f"Collecting uncached texts for {lang.upper()} ({profile_id})...")
    cached = set(load_cache(cache_path))
    candidates = json.loads((run_dir / "stages/03_sentence_harvest/output/candidates.json").read_text())
    menu = json.loads((run_dir / "stages/02_sense_menu/output/sense-menu.json").read_text())
    menu_by_card = {c["card_id"]: c for c in menu["cards"]}
    menu_source_adapter = str(menu.get("source_adapter") or "")

    ex = json.loads((prewsd_dir / "examples.json").read_text())
    pr = json.loads((prewsd_dir / "pairs.json").read_text())
    cols = ex["columns"]
    ids = [i if str(i).startswith(ID_PREFIX) else ID_PREFIX + str(i) for i in cols["sentence_id"]]
    sentences = {
        sid: {"sentence_id": sid,
              "target": {"text": cols["target"][n]},
              "translation": {"text": cols["translation"][n]}}
        for n, sid in enumerate(ids)
    }
    prewsd_set = {form: [ids[i] for i in entry["eligible"]]
                  for form, entry in pr["surfaces"].items()}

    mwe_index = index_multiword_senses(json.loads(mwe_path.read_text()))

    policy = OccurrenceSamplingPolicy(cap_per_surface=30)
    cards_to_process = candidates["cards"]

    needed = set()
    work = []
    deterministic = []
    deterministic_invariant = []
    embedding_scored_cards = set()

    for card in cards_to_process:
        card_id = card["card_id"]
        menu_card = menu_by_card.get(card_id)
        display_form = card.get("display_form")
        preferred_order = prewsd_set.get(display_form)
        
        selection = select_occurrences(
            card["candidates"],
            policy,
            card_id=card_id,
            ineligible=set(),
            preferred_order=preferred_order,
        )
        analyses = (
            build_analyses(menu_card, menu_source_adapter=menu_source_adapter)
            if menu_card and menu_card["analyses"]
            else ()
        )
        only = sole_leaf(analyses) if analyses else None
        for sentence_id in selection.selected:
            row = sentences.get(sentence_id)
            if row is None:
                continue
            text = row["target"]["text"]
            all_mwe_matches = (
                list(
                    multiword_analyses(
                        card_id=card_id,
                        surface_form=card["display_form"],
                        sentence=text,
                        index=mwe_index,
                    )
                )
                if mwe_index is not None
                else []
            )
            inv_matches = [
                m for m in all_mwe_matches
                if getattr(m[1], "wsd_routing", "") == "deterministic_bypass"
                or getattr(m[1], "route", "") == "invariant"
            ]
            amb_matches = [
                m for m in all_mwe_matches
                if getattr(m[1], "wsd_routing", "") != "deterministic_bypass"
                and getattr(m[1], "route", "") != "invariant"
            ]

            if inv_matches:
                deterministic_invariant.append((card, menu_card, sentence_id))
                continue

            has_multiword_alternative = bool(amb_matches)
            if (
                only is not None
                and not has_multiword_alternative
                and profile_id not in EVIDENCE_GUARD_PROFILES
            ):
                deterministic.append((card, menu_card, sentence_id))
                continue
            translation = (row.get("translation") or {}).get("text") or ""
            work.append((card, menu_card, sentence_id, text, translation))
            leaf_count = sum(len(analysis.senses) for analysis in analyses)
            if leaf_count > 1 or has_multiword_alternative:
                needed.add(text)
                embedding_scored_cards.add(card_id)

    if mwe_index is not None:
        for card, menu_card, _sentence_id, text, _translation in work:
            for analysis, _entry, _span in multiword_analyses(
                card_id=card["card_id"], surface_form=card["display_form"],
                sentence=text, index=mwe_index,
            ):
                needed.add(analysis.senses[0].gloss_text)

    for card in menu["cards"]:
        if card["card_id"] not in embedding_scored_cards:
            continue
        for analysis in card["analyses"]:
            for leaf in analysis["senses"]:
                translation = leaf.get("translation") or ""
                definition = leaf.get("definition") or ""
                needed.add(" — ".join(value for value in (translation, definition) if value))

    needed = {text for text in needed if text.strip()}
    missing = sorted(needed - cached)
    print(f"[{lang.upper()}] Needed: {len(needed):,}, In cache: {len(needed & cached):,}, Missing: {len(missing):,}")
    
    if missing:
        print(f"[{lang.upper()}] Embedding {len(missing):,} misses...")
        ensure_embeddings(cache_path, missing, api_key=api_key, log=print)
        print(f"[{lang.upper()}] Embedding complete! New cache size: {len(load_cache(cache_path)):,}")
    else:
        print(f"[{lang.upper()}] 100% cached! Nothing to embed.")

print("\nALL EMBEDDINGS COMPLETE!")
