#!/usr/bin/env python3
"""Build DECIDE-1 plus inflected-expression answers (decision 0034) as a new Portuguese release.

Derived from scripts/build_decide1_full_release.py (the DECIDE-1 build, kept
as the worker left it): the same inputs and rules, plus
- each re-asked card's expression senses (reviews/pt-expressions-inflected-20261026),
  added to its stage-02 menu as phrase senses and to its request menu;
- the re-asked sentences' answers, overriding DECIDE-1's for those sentences.
Every other card must come out identical to DECIDE-1 (checked after the build).
The original DECIDE-1 build:

Inputs:
- ../Fluency-Workspace/reviews/pt-top10000-decide-20261025/answers-decide.jsonl (1,077 cards, mercury-decide)
- ../Fluency-Workspace/reviews/pt-top10000-jev-remaining-20261025/answers-jev.jsonl (6,713 cards, jev-1.14)
- ../Fluency-Workspace/reviews/pt-top10000-decide-20261025/menus.json (all requested polysemous card menus)
- ../Fluency-Workspace/runs/pt/speech/20261025T215847Z-2903e0bf/stages/04_wsd_assignments/output/assignments.jsonl (staged unchanged top-1,000 cards)
- Single-sense cards assigned directly to sole sense up to example budget.
- Overriding rules: NONE accepted only at P(NONE) >= 0.8; ties recorded for all senses >= 0.5 * top sense probability.
- Provenance: model recorded per row (mercury-decide or jev-1.14).
- Published to Fluency-Releases-pt; staged via ?ptRelease= flow; live config untouched.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fluency.core.hashing import canonical_content_id, file_content_id
from fluency.core.identity import create_card_record
from fluency.core.workspace import Workspace
from fluency.enrichments.conjugations import build_conjugation_layer
from fluency.mwe.builder import count_mwe_occurrences
from fluency.pipeline.planning import create_pipeline_plan
from fluency.release.example_shards import shard_app_examples
from fluency.release.index_shards import shard_app_index
from fluency.release.run_candidate import build_inactive_run_candidate
from fluency.release.validation import validate_release_bundle
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.equivalences import find_card_equivalences
from fluency.sense_menu.kaikki import KaikkiSenseMenuAdapter
from fluency.wsd.sampling import is_hyphenated_compound_occurrence

UTC = timezone.utc
WS_ROOT = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace")
BASE_RUN = WS_ROOT / "runs/pt/speech/20261013T133630Z-12746d8c"
STAGED_RUN = WS_ROOT / "runs/pt/speech/20261025T215847Z-2903e0bf"
SNAPSHOT_PATH = WS_ROOT / "raw/wiktionary/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl"
SNAPSHOT_ID = "enwiktionary-2026-08-20"
MWE_PATH = WS_ROOT / "raw/mwe/mwe-pt-10k-sieve/mwe_merged.json"
DECK_PATH = REPO / "dist/pt-finite-staging/pt/speech/pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-finite-v1-meta-candidate-slim/deck.json"
STAGED_DECK_PATH = WS_ROOT / "releases/pt/speech/pt-speech-v25-top1000-decide-v2-slim/deck.json"
REVIEWS_DECIDE_DIR = WS_ROOT / "reviews/pt-top10000-decide-20261025"
REVIEWS_JEV_DIR = WS_ROOT / "reviews/pt-top10000-jev-remaining-20261025"
FW1_PATH = WS_ROOT / "raw/wsd/pt/fw1-function-word-labels.json"
RELEASE_ID = "pt-speech-v25-decide-1-expr-10000-slim"
EXPR_DIR = WS_ROOT / "reviews/pt-expressions-inflected-20261026"
EXPR_INVENTORY = WS_ROOT / "raw/mwe/mwe-pt-20261026-v15-inflected/mwe_merged.json"


def load_expression_rerun():
    """Card -> appended menu choices, and the re-asked answer rows."""
    extra_menu, rows = {}, []
    for provider in ("decide", "jev"):
        for item in read_json(EXPR_DIR / f"requests-{provider}.json"):
            menu = item["body"]["state"]["menu"]
            extra_menu[item["card_id"]] = {k: v for k, v in menu.items() if str(v.get("sense_id", "")).startswith("mwe:")}
            path = EXPR_DIR / f"responses-{provider}" / f"{item['card_id']}.json"
            if not path.exists():
                continue
            answers = read_json(path).get("answers") or {}
            model = "mercury-decide" if provider == "decide" else "jev-1.14"
            for sid in item["ids"]:
                a = answers.get(sid)
                if a:
                    rows.append(({"card_id": item["card_id"], "surface": item["surface"], "rank": item["rank"],
                                  "sentence_id": sid, "choice": str(a.get("choice")), "confidence": a.get("confidence"),
                                  "probabilities": a.get("probabilities") or {}}, model))
    return extra_menu, rows


def read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compute_budget(rank: int, sense_count: int) -> int:
    m = 1.0 if rank <= 1000 else max(0.6, 1.0 - 0.4 * math.log10(rank / 1000.0))
    if sense_count <= 1:
        return max(5, round(10.0 * m))
    return max(5, round(min(36.0, 8.0 + 6.0 * math.log2(sense_count)) * m))


def main():
    global EXTRA_MENU
    EXTRA_MENU, EXPR_ROWS = load_expression_rerun()
    print(f"=== DECIDE-1 + inflected expressions: {RELEASE_ID} ({len(EXTRA_MENU)} cards, {len(EXPR_ROWS)} re-asked sentences) ===")
    ws = Workspace.load(WS_ROOT)

    # 1. Pipeline Plan
    print("1. Creating pipeline plan...")
    base_profile = read_json(BASE_RUN / "profile.json")
    profile = deepcopy(base_profile)
    profile["profile_id"] = "pt-speech-v25-decide-1-10000"
    profile["scope"]["surface_limit"] = 10000
    profile["scope"]["note"] = "10,000 cards DECIDE-1 release (mercury-decide + Jev 1.14 + staged unchanged)."
    profile["wsd"]["model_profile"] = "pt-decide-1-10000"
    profile["wsd"]["model_revisions"] = {"decision": "mercury-decide;jev-1.14"}

    new_run = create_pipeline_plan(ws, profile)
    print(f"   Initialized run: {new_run.name} at {new_run}")

    # 2. Stage 01: Inventory (10,000 cards)
    print("2. Stage 01: Inventory...")
    s1_in = read_json(BASE_RUN / "stages/01_inventory/output/inventory.json")
    all_cards = s1_in["cards"]
    cards_by_id = {c["card_id"]: c for c in all_cards}
    assert len(all_cards) == 10000

    s1_out = new_run / "stages/01_inventory/output"
    write_json(s1_out / "inventory.json", s1_in)
    shutil.copy2(BASE_RUN / "stages/01_inventory/output/frequency-ranks.json", s1_out / "frequency-ranks.json")
    shutil.copy2(BASE_RUN / "stages/01_inventory/output/report.json", s1_out / "report.json")

    s1_manifest = read_json(BASE_RUN / "stages/01_inventory/output/manifest.json")
    s1_manifest["outputs"]["inventory"] = file_content_id(s1_out / "inventory.json")
    s1_manifest["outputs"]["report"] = file_content_id(s1_out / "report.json")
    write_json(s1_out / "manifest.json", s1_manifest)

    c1 = read_json(new_run / "stages/01_inventory/contract.json")
    c1.update(status="complete", output_directory="output", manifest_content_id=file_content_id(s1_out / "manifest.json"))
    write_json(new_run / "stages/01_inventory/contract.json", c1)
    print("   Stage 01 complete.")

    # 3. Stage 02: Sense Menu (10,000 cards)
    print("3. Stage 02: Building full sense menu with fixed adapter & MWEs...")
    
    # Load rescued verbal phrases (Fix 1)
    mwe_data = read_json(MWE_PATH)
    mwes = mwe_data["mwes"]
    verbal_candidates = {
        expr: row for expr, row in mwes.items()
        if ("verb" in row.get("pos", "") or row.get("verbal_idiom")) and row.get("corpus_freq", 0) == 0
    }
    
    # Sample sentences from sentence-bank for MWE count
    targets_for_mwe = []
    translations_for_mwe = []
    with open(BASE_RUN / "stages/03_sentence_harvest/output/sentence-bank.jsonl", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 60000: break
            row = json.loads(line)
            targets_for_mwe.append(row.get("target", {}).get("text", ""))
            translations_for_mwe.append(row.get("translation", {}).get("text", ""))

    counts, _ = count_mwe_occurrences(verbal_candidates, targets_for_mwe, translations_for_mwe)
    rescued_mwes = {k: mwes[k] for k, v in counts.items() if v > 0}
    rescued_by_word = defaultdict(list)
    for expr, r_row in rescued_mwes.items():
        for aw in r_row.get("attach_words", []):
            rescued_by_word[aw].append((expr, r_row))
    print(f"   Rescued {len(rescued_mwes)} verbal phrases (e.g. haver de, doer em).")

    # Build Kaikki menus
    pt_policy = load_sense_menu_language_policy(REPO, policy_id="pt-v1", language="pt")
    adapter = KaikkiSenseMenuAdapter(SNAPSHOT_PATH, language_code="pt", language_policy=pt_policy)
    card_surfaces = sorted({c["display_form"] for c in all_cards})
    card_records = [create_card_record("pt", s).to_dict() for s in card_surfaces]
    menu_bundle, _ = adapter.build(card_records, snapshot_id=SNAPSHOT_ID)
    built_cards_by_id = {c["card_id"]: c for c in menu_bundle["cards"]}

    live_deck = read_json(DECK_PATH)
    live_deck_cards = {c["card_id"]: c for c in live_deck["cards"]}
    live_deck_by_surf = {c["display_form"]: c for c in live_deck["cards"]}

    decide_menus = read_json(REVIEWS_DECIDE_DIR / "menus.json")
    requested_cids = set(decide_menus.keys())
    staged_deck = read_json(STAGED_DECK_PATH)
    staged_cards_by_id = {c["card_id"]: c for c in staged_deck["cards"]}
    unchanged_top1000_cids = set(staged_cards_by_id.keys()) - requested_cids
    staged_sm = read_json(STAGED_RUN / "stages/02_sense_menu/output/sense-menu.json")
    staged_sm_cards = {c["card_id"]: c for c in staged_sm["cards"]}
    print(f"   Requested cards: {len(requested_cids)}, Unchanged top-1000 cards: {len(unchanged_top1000_cids)}")

    # Build full stage 02 menu cards
    final_menu_cards = []
    # Index menus for fast assignment synthesis: card_id -> {sense_id: (analysis_id, headword, pos)}
    menu_index = {}
    phrase_by_card_and_scoped_id = {}
    all_card_flat_senses = {}

    for c_info in all_cards:
        cid = c_info["card_id"]
        surf = c_info["display_form"]

        if cid in unchanged_top1000_cids and cid in staged_sm_cards:
            menu_card = deepcopy(staged_sm_cards[cid])
            final_menu_cards.append(menu_card)
            c_index = {}
            flat_senses = []
            for a in menu_card.get("analyses", []):
                aid = a["menu_analysis_id"]
                hw = a["headword"]
                pos = a["part_of_speech"]
                for s in a.get("senses", []):
                    sid = s["sense_id"]
                    c_index[sid] = (aid, hw, pos)
                    flat_senses.append((hw, pos, s, False))
            menu_index[cid] = c_index
            all_card_flat_senses[cid] = flat_senses
            continue

        built_c = built_cards_by_id.get(cid)
        deck_c = live_deck_cards.get(cid) or live_deck_by_surf.get(surf) or {}

        analyses = deepcopy(built_c.get("analyses", [])) if built_c else []
        flat_senses = []
        c_index = {}
        for a in analyses:
            aid = a["menu_analysis_id"]
            hw = a["headword"]
            pos = a["part_of_speech"]
            for s in a.get("senses", []):
                sid = s["sense_id"]
                c_index[sid] = (aid, hw, pos)
                flat_senses.append((hw, pos, s, False))

        # Re-attach MWE phrase senses from live deck
        seen_phrase_sids = set()
        for m in deck_c.get("meanings", []):
            if m.get("part_of_speech") == "PHRASE":
                sid = m.get("sense_id")
                seen_phrase_sids.add(sid)
                phrase_by_card_and_scoped_id[(cid, sid)] = m
                flat_senses.append((
                    m.get("headword") or surf,
                    "PHRASE",
                    {
                        "sense_id": sid,
                        "translation": m.get("translation") or "",
                        "definition": "",
                        "provider_metadata": {
                            "definition_path": list(m.get("wsd_target", {}).get("definition_path") or [m.get("translation") or ""]),
                            "tags": ["phrase"],
                            "wsd_routing": "competitive_wsd",
                            "examples": [],
                            "synonyms": [],
                            "equivalent_sense_ids": [],
                        },
                        "wsd_routing": "competitive_wsd",
                    },
                    True,
                ))

        # Attach rescued verbal phrases (Fix 1)
        if surf in rescued_by_word:
            for expr, r_row in rescued_by_word[surf]:
                expr_sid = f"mwe:{expr}"
                if expr_sid not in seen_phrase_sids:
                    seen_phrase_sids.add(expr_sid)
                    trans = r_row.get("translations", [""])[0]
                    # Synthesize phrase meaning
                    m_syn = {
                        "sense_id": expr_sid,
                        "headword": expr,
                        "part_of_speech": "PHRASE",
                        "translation": trans,
                        "menu_analysis_id": f"analysis_phrase_{hashlib.sha256(expr_sid.encode()).hexdigest()[:16]}",
                        "metadata": {
                            "multiword_evidence": [{
                                "expression": expr,
                                "expression_id": expr_sid,
                                "wsd_routing": "competitive_wsd",
                                "route": "competitive",
                                "translations": [trans],
                            }]
                        },
                        "wsd_target": {"definition_path": [trans]},
                    }
                    phrase_by_card_and_scoped_id[(cid, expr_sid)] = m_syn
                    flat_senses.append((
                        expr,
                        "PHRASE",
                        {
                            "sense_id": expr_sid,
                            "translation": trans,
                            "definition": "",
                            "provider_metadata": {
                                "definition_path": [trans],
                                "tags": ["phrase", "verbal_phrase"],
                                "wsd_routing": "competitive_wsd",
                                "examples": [],
                                "synonyms": [],
                                "equivalent_sense_ids": [],
                            },
                            "wsd_routing": "competitive_wsd",
                        },
                        True,
                    ))

        # Inflected expressions offered in the 2026-10-26 re-run (decision 0034).
        for choice in EXTRA_MENU.get(cid, {}).values():
            expr_sid = choice["sense_id"]
            if expr_sid in seen_phrase_sids:
                continue
            seen_phrase_sids.add(expr_sid)
            expr, trans = choice["headword"], choice["translation"]
            phrase_by_card_and_scoped_id[(cid, expr_sid)] = {
                "sense_id": expr_sid, "headword": expr, "part_of_speech": "PHRASE", "translation": trans,
                "menu_analysis_id": f"analysis_phrase_{hashlib.sha256(expr_sid.encode()).hexdigest()[:16]}",
                "metadata": {"multiword_evidence": [{"expression": expr, "expression_id": expr_sid,
                                                     "wsd_routing": "competitive_wsd", "route": "competitive",
                                                     "flexibility": "head_inflecting", "translations": [trans]}]},
                "wsd_target": {"definition_path": [trans]},
            }
            flat_senses.append((expr, "PHRASE", {
                "sense_id": expr_sid, "translation": trans, "definition": "",
                "provider_metadata": {"definition_path": [trans], "tags": ["phrase", "inflected_expression"],
                                      "wsd_routing": "competitive_wsd", "examples": [], "synonyms": [],
                                      "equivalent_sense_ids": []},
                "wsd_routing": "competitive_wsd",
            }, True))

        menu_index[cid] = c_index
        all_card_flat_senses[cid] = flat_senses

        menu_card = deepcopy(built_c) if built_c else {
            "card_id": cid,
            "surface_form": surf,
            "analyses": [],
        }
        menu_card["analyses"] = analyses
        if not analyses and "resolution" not in menu_card:
            menu_card["resolution"] = {
                "resolver_version": "surface-resolver/v1",
                "strategy": "no_menu",
                "provider": "wiktionary",
                "coverage": "absent",
                "entry_id": None,
                "expanded_to": None,
                "word_class": "unresolved",
                "surface": surf,
                "reason": "absent",
                "headwords": [],
                "entry": None,
                "notes": {},
            }
        final_menu_cards.append(menu_card)

    s2_out = new_run / "stages/02_sense_menu/output"
    s2_bundle = {
        "menu_version": "sense-menu/v1",
        "metadata_contract": "sense-metadata/v1",
        "language": "pt",
        "gloss_language": "en",
        "source_edition": "enwiktionary",
        "cards": final_menu_cards,
    }
    write_json(s2_out / "sense-menu.json", s2_bundle)
    menu_content_id = file_content_id(s2_out / "sense-menu.json")

    s2_report = {
        "inventory_cards": 10000,
        "cards_ready": 10000,
        "language": "pt",
        "report_version": "sense-menu-report/v1",
    }
    write_json(s2_out / "report.json", s2_report)

    s2_manifest = {
        "manifest_version": "stage/v1",
        "stage_name": "sense_menu",
        "stage_version": "sense-menu-stage/v1",
        "status": "complete",
        "started_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "inputs": {
            "inventory": file_content_id(s1_out / "inventory.json"),
            "dictionary_snapshot": file_content_id(SNAPSHOT_PATH),
        },
        "outputs": {
            "sense_menu": menu_content_id,
            "report": file_content_id(s2_out / "report.json"),
        },
        "config_hash": canonical_content_id({"profile_sense_menu": profile["sense_menu"]}),
        "implementation_hash": canonical_content_id({"adapter": "KaikkiSenseMenuAdapter"}),
        "cache_key": canonical_content_id({"s2": menu_content_id}),
        "model_revisions": {},
        "random_seed": 0,
    }
    write_json(s2_out / "manifest.json", s2_manifest)

    c2 = read_json(new_run / "stages/02_sense_menu/contract.json")
    c2.update(status="complete", output_directory="output", manifest_content_id=file_content_id(s2_out / "manifest.json"))
    write_json(new_run / "stages/02_sense_menu/contract.json", c2)
    print("   Stage 02 complete.")

    # 4. Stage 03: Sentence Harvest (reusing base run candidates & sentence bank)
    print("4. Stage 03: Carrying sentence harvest from base run...")
    s3_out = new_run / "stages/03_sentence_harvest/output"
    s3_out.mkdir(parents=True, exist_ok=True)
    
    # Symlink or copy candidates and sentence bank to avoid 400MB duplication
    cand_src = BASE_RUN / "stages/03_sentence_harvest/output/candidates.json"
    sbank_src = BASE_RUN / "stages/03_sentence_harvest/output/sentence-bank.jsonl"
    report_src = BASE_RUN / "stages/03_sentence_harvest/output/report.json"
    
    target_cand = s3_out / "candidates.json"
    target_sbank = s3_out / "sentence-bank.jsonl"
    target_report = s3_out / "report.json"
    
    if not target_cand.exists():
        os.link(cand_src, target_cand)
    if not target_sbank.exists():
        os.link(sbank_src, target_sbank)
    if not target_report.exists():
        shutil.copy2(report_src, target_report)

    s3_manifest = read_json(BASE_RUN / "stages/03_sentence_harvest/output/manifest.json")
    write_json(s3_out / "manifest.json", s3_manifest)

    c3 = read_json(new_run / "stages/03_sentence_harvest/contract.json")
    c3.update(status="complete", output_directory="output", manifest_content_id=file_content_id(s3_out / "manifest.json"))
    write_json(new_run / "stages/03_sentence_harvest/contract.json", c3)
    print("   Stage 03 complete.")

    # 5. Stage 04: WSD Assignments
    print("5. Stage 04: Assembling assignments from decide, jev, staged, and single-sense...")
    
    # Load candidate sentences by card
    print("   Loading candidates and sentence bank...")
    cand_data = read_json(target_cand)
    candidates_by_card = {c["card_id"]: c["candidates"] for c in cand_data["cards"]}

    sentence_texts = {}
    with open(target_sbank, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            sentence_texts[row["sentence_id"]] = row.get("target", {}).get("text", "")

    # Load requested cards and menus
    requested_cards_manifest = read_json(REVIEWS_DECIDE_DIR / "manifest.json")
    req_sha = requested_cards_manifest.get("requests_sha256", "")
    decide_menus = read_json(REVIEWS_DECIDE_DIR / "menus.json")
    for cid, extra in EXTRA_MENU.items():
        decide_menus.setdefault(cid, {}).update(extra)

    # Equivalence map from decide menus + all card flat senses
    equiv_by_card_and_sense = defaultdict(dict)
    for cid, m_choices in decide_menus.items():
        for ch_num, ch_data in m_choices.items():
            sid = ch_data.get("sense_id")
            if sid:
                equiv_by_card_and_sense[cid][sid] = (
                    ch_data.get("equivalent_choices", []),
                    ch_data.get("equivalent_sense_ids", []),
                )

    # Load staged assignments for unchanged cards
    unchanged_assignments = {}
    with open(STAGED_RUN / "stages/04_wsd_assignments/output/assignments.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            cid = row["card_id"]
            if cid in unchanged_top1000_cids:
                unchanged_assignments[(cid, row["sentence_id"])] = row

    print(f"   Loaded {len(unchanged_assignments)} assignments for {len(unchanged_top1000_cids)} unchanged top-1000 cards.")

    # Process model answers (mercury-decide and jev-1.14)
    model_assigned_count = 0
    model_none_count = 0
    model_ties_count = 0
    ties_by_card_and_sense = defaultdict(lambda: defaultdict(list))
    example_ties_by_id = {}
    model_assignments = {}

    def process_model_row(row: dict, model_name: str, assigner_label: str) -> dict:
        nonlocal model_assigned_count, model_none_count, model_ties_count
        cid = row["card_id"]
        sid = row["sentence_id"]
        surf = row["surface"]
        choice = row["choice"]
        probs = row.get("probabilities", {})
        confidence = row.get("confidence")
        card_menu = decide_menus.get(cid, {})

        is_none = (choice == "NONE")
        p_none = probs.get("NONE", 0.0)
        
        if is_none or p_none >= 0.8:
            if p_none >= 0.8:
                model_none_count += 1
                return {
                    "assignment_version": "wsd-assignment/v1",
                    "card_id": cid,
                    "surface_form": surf,
                    "sentence_id": sid,
                    "status": "abstained",
                    "sense_menu_content_id": menu_content_id,
                    "menu_analysis_id": None,
                    "selected_sense_id": None,
                    "selected_tuple": None,
                    "decision_path": ["commit"],
                    "evidence": {
                        "assigner": assigner_label,
                        "model": model_name,
                        "request_set": req_sha,
                        "none_threshold": 0.8,
                        "tie_rule": ">= 0.5 * top_sense",
                        "probabilities": probs,
                        "none_probability": p_none,
                        "reason": "explicit_none_threshold",
                    },
                    "confidence": None,
                    "model_revisions": {"decision": model_name},
                    "emitted_level": None,
                    "decision_kind": None,
                    "selection_projections": None,
                    "active_selection_projection": None,
                }
            else:
                # Override NONE < 0.8: take highest non-NONE sense
                non_none = {k: v for k, v in probs.items() if k != "NONE"}
                choice = max(non_none, key=non_none.get) if non_none else "1"

        item = card_menu.get(choice, {})
        chosen_sense_id = item.get("sense_id")
        top_prob = probs.get(choice, 1.0)

        # Record ties (every sense >= 0.5 * top)
        ties = []
        for k, p in probs.items():
            if k != "NONE" and k != choice and p >= 0.5 * top_prob:
                ch_item = card_menu.get(k, {})
                ties.append({
                    "choice": k,
                    "sense_id": ch_item.get("sense_id"),
                    "headword": ch_item.get("headword"),
                    "translation": ch_item.get("translation"),
                    "probability": p,
                })

        if ties:
            model_ties_count += 1
            example_ties_by_id[sid] = ties
            for tie in ties:
                existing_choices = [t["choice"] for t in ties_by_card_and_sense[cid][chosen_sense_id]]
                if tie["choice"] not in existing_choices:
                    ties_by_card_and_sense[cid][chosen_sense_id].append(tie)

        evidence = {
            "assigner": assigner_label,
            "model": model_name,
            "request_set": req_sha,
            "none_threshold": 0.8,
            "tie_rule": ">= 0.5 * top_sense",
            "choice": choice,
            "confidence": confidence,
            "probabilities": probs,
            "ties": ties,
        }

        # Check if chosen sense is provider sense or MWE
        c_index = menu_index.get(cid, {})
        if chosen_sense_id in c_index:
            aid, hw, pos = c_index[chosen_sense_id]
            model_assigned_count += 1
            proj = {
                "menu_analysis_id": aid,
                "selected_sense_id": chosen_sense_id,
                "selected_tuple": {"headword": hw, "part_of_speech": pos},
                "source_kind": "provider",
                "selected_score": float(top_prob),
                "runner_up_score": float(sorted(probs.values(), reverse=True)[1]) if len(probs) > 1 else None,
                "raw_margin": None,
                "rank": 1,
                "emitted_level": "leaf",
                "raw_axis_margins": {"leaf": 1.0, "glosskey": 1.0, "tuple": 1.0},
            }
            return {
                "assignment_version": "wsd-assignment/v1",
                "card_id": cid,
                "surface_form": surf,
                "sentence_id": sid,
                "status": "assigned",
                "sense_menu_content_id": menu_content_id,
                "menu_analysis_id": aid,
                "selected_sense_id": chosen_sense_id,
                "selected_tuple": {"headword": hw, "part_of_speech": pos},
                "decision_path": ["commit"],
                "evidence": evidence,
                "confidence": confidence,
                "model_revisions": {"decision": model_name},
                "emitted_level": "leaf",
                "decision_kind": "disambiguated",
                "selection_projections": {
                    "provider_only": proj,
                    "mwe_augmented": deepcopy(proj),
                },
                "active_selection_projection": "provider_only",
            }
        elif (cid, chosen_sense_id) in phrase_by_card_and_scoped_id:
            model_assigned_count += 1
            m = phrase_by_card_and_scoped_id[(cid, chosen_sense_id)]
            ev = (m.get("metadata", {}).get("multiword_evidence") or [{}])[0]
            expr = m.get("headword") or surf
            aid = m.get("menu_analysis_id") or f"analysis_phrase_{hashlib.sha256(chosen_sense_id.encode()).hexdigest()[:16]}"
            expr_id = chosen_sense_id
            routing = ev.get("wsd_routing") or "competitive_wsd"
            trans = m.get("translation") or expr

            declared_cand = {
                "additional_translations": ev.get("additional_translations", []),
                "corpus_frequency": ev.get("corpus_frequency", 100),
                "expression": expr,
                "expression_id": expr_id,
                "flexibility": ev.get("flexibility", "frozen"),
                "inventory_content_id": file_content_id(MWE_PATH),
                "menu_analysis_id": aid,
                "route": ev.get("route", "competitive"),
                "sources": ["wiktionary"],
                "span": ev.get("span", [0, len(surf)]),
                "template_gap_limit": 0,
                "translation": trans,
                "transparency": ev.get("transparency", "formulaic"),
                "ui_role": ev.get("ui_role", "formula"),
                "verbal_idiom": False,
                "wsd_routing": routing,
            }
            evidence["selected_multiword"] = expr
            evidence["multiword_candidates"] = [declared_cand]
            evidence["wsd_routing"] = routing

            proj_mwe = {
                "menu_analysis_id": aid,
                "selected_sense_id": expr_id,
                "selected_tuple": {"headword": expr, "part_of_speech": "PHRASE"},
                "source_kind": "multiword",
                "selected_score": float(top_prob),
                "runner_up_score": None,
                "raw_margin": None,
                "rank": 1,
                "emitted_level": "leaf",
                "raw_axis_margins": {"leaf": 1.0, "glosskey": 1.0, "tuple": 1.0},
            }
            # Fallback provider proj if any provider sense exists
            first_aid = next(iter(c_index.values())) if c_index else (aid, surf, "phrase")
            proj_prov = {
                "menu_analysis_id": first_aid[0],
                "selected_sense_id": next(iter(c_index.keys())) if c_index else chosen_sense_id,
                "selected_tuple": {"headword": first_aid[1], "part_of_speech": first_aid[2]},
                "source_kind": "provider",
                "selected_score": 0.5,
                "runner_up_score": None,
                "raw_margin": None,
                "rank": 1,
                "emitted_level": "leaf",
                "raw_axis_margins": {"leaf": 1.0, "glosskey": 1.0, "tuple": 1.0},
            }
            return {
                "assignment_version": "wsd-assignment/v1",
                "card_id": cid,
                "surface_form": surf,
                "sentence_id": sid,
                "status": "assigned",
                "sense_menu_content_id": menu_content_id,
                "menu_analysis_id": aid,
                "selected_sense_id": chosen_sense_id,
                "selected_tuple": {"headword": expr, "part_of_speech": "PHRASE"},
                "decision_path": ["commit"],
                "evidence": evidence,
                "confidence": confidence,
                "model_revisions": {"decision": model_name},
                "emitted_level": "leaf",
                "decision_kind": "disambiguated",
                "selection_projections": {
                    "provider_only": proj_prov,
                    "mwe_augmented": proj_mwe,
                },
                "active_selection_projection": "mwe_augmented",
            }
        else:
            # Fallback if sense_id not found
            model_assigned_count += 1
            aid = f"analysis_fallback_{hashlib.sha256(str(chosen_sense_id).encode()).hexdigest()[:16]}"
            proj = {
                "menu_analysis_id": aid,
                "selected_sense_id": chosen_sense_id,
                "selected_tuple": {"headword": surf, "part_of_speech": "noun"},
                "source_kind": "provider",
                "selected_score": float(top_prob),
                "runner_up_score": None,
                "raw_margin": None,
                "rank": 1,
                "emitted_level": "leaf",
                "raw_axis_margins": {"leaf": 1.0, "glosskey": 1.0, "tuple": 1.0},
            }
            return {
                "assignment_version": "wsd-assignment/v1",
                "card_id": cid,
                "surface_form": surf,
                "sentence_id": sid,
                "status": "assigned",
                "sense_menu_content_id": menu_content_id,
                "menu_analysis_id": aid,
                "selected_sense_id": chosen_sense_id,
                "selected_tuple": {"headword": surf, "part_of_speech": "noun"},
                "decision_path": ["commit"],
                "evidence": evidence,
                "confidence": confidence,
                "model_revisions": {"decision": model_name},
                "emitted_level": "leaf",
                "decision_kind": "disambiguated",
                "selection_projections": {"provider_only": proj, "mwe_augmented": deepcopy(proj)},
                "active_selection_projection": "provider_only",
            }

    # Ingest answers-decide.jsonl
    print("   Ingesting mercury-decide answers...")
    with open(REVIEWS_DECIDE_DIR / "answers-decide.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cid = r["card_id"]
            sid = r["sentence_id"]
            model_assignments[(cid, sid)] = process_model_row(r, "mercury-decide", "MERCURY_DECIDE v1")

    # Ingest answers-jev.jsonl
    print("   Ingesting jev-1.14 answers...")
    with open(REVIEWS_JEV_DIR / "answers-jev.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cid = r["card_id"]
            sid = r["sentence_id"]
            model_assignments[(cid, sid)] = process_model_row(r, "jev-1.14", "JEV v1.14")

    # Re-asked sentences (inflected expressions on the menu) replace DECIDE-1's answer.
    for r, model in EXPR_ROWS:
        label = "MERCURY_DECIDE v1 + EXPR_INFLECTED" if model == "mercury-decide" else "JEV v1.14 + EXPR_INFLECTED"
        model_assignments[(r["card_id"], r["sentence_id"])] = process_model_row(r, model, label)
    print(f"   Re-asked expression sentences applied: {len(EXPR_ROWS)}")

    print(f"   Model assignments ready: {len(model_assignments)} (assigned: {model_assigned_count}, NONE: {model_none_count}, ties: {model_ties_count})")

    # Assemble all assignments across all 10,000 cards
    print("   Writing complete assignments.jsonl...")
    s4_out = new_run / "stages/04_wsd_assignments/output"
    s4_out.mkdir(parents=True, exist_ok=True)
    assignments_file = s4_out / "assignments.jsonl"

    total_assignments_written = 0
    assigned_total = 0
    none_total = 0
    overflow_total = 0
    single_sense_assigned_total = 0

    with open(assignments_file, "w", encoding="utf-8") as out_f:
        for c_info in all_cards:
            cid = c_info["card_id"]
            surf = c_info["display_form"]
            rank = c_info["rank"]
            cands = candidates_by_card.get(cid, [])
            flat_senses = all_card_flat_senses.get(cid, [])
            sense_count = len(flat_senses)
            budget = compute_budget(rank, sense_count)

            if cid in unchanged_top1000_cids:
                # 1. Unchanged top-1,000 card: carry rows directly from staged run
                for cand in cands:
                    sid = cand["sentence_id"]
                    row = unchanged_assignments.get((cid, sid))
                    if row:
                        total_assignments_written += 1
                        st = row.get("status")
                        if st == "assigned": assigned_total += 1
                        elif st == "abstained": none_total += 1
                        elif st == "not_evaluated_example_cap": overflow_total += 1
                        row_copy = deepcopy(row)
                        row_copy["sense_menu_content_id"] = menu_content_id
                        out_f.write(json.dumps(row_copy, ensure_ascii=False) + "\n")
            elif cid in requested_cids:
                # 2. Requested card: write model rows + overflow for remainder
                for cand in cands:
                    sid = cand["sentence_id"]
                    if (cid, sid) in model_assignments:
                        row = model_assignments[(cid, sid)]
                        total_assignments_written += 1
                        st = row.get("status")
                        if st == "assigned": assigned_total += 1
                        elif st == "abstained": none_total += 1
                        out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    else:
                        # Overflow candidate
                        overflow_total += 1
                        total_assignments_written += 1
                        overflow_row = {
                            "assignment_version": "wsd-assignment/v1",
                            "card_id": cid,
                            "surface_form": surf,
                            "sentence_id": sid,
                            "status": "not_evaluated_example_cap",
                            "sense_menu_content_id": menu_content_id,
                            "menu_analysis_id": None,
                            "selected_sense_id": None,
                            "selected_tuple": None,
                            "decision_path": [],
                            "evidence": {"cap_per_surface": budget, "reason": "per_surface_wsd_execution_cap"},
                            "confidence": None,
                            "model_revisions": {"decision": "mercury-decide"},
                            "emitted_level": None,
                            "decision_kind": None,
                            "selection_projections": None,
                            "active_selection_projection": None,
                        }
                        out_f.write(json.dumps(overflow_row, ensure_ascii=False) + "\n")
            else:
                # 3. Single-sense cards in ranks 1001-10000: assign directly up to budget
                selected_count = 0
                c_index = menu_index.get(cid, {})
                sole_info = next(iter(c_index.items())) if c_index else None

                for cand in cands:
                    sid = cand["sentence_id"]
                    stext = sentence_texts.get(sid, "")
                    is_compound = is_hyphenated_compound_occurrence(stext, surf)

                    if not is_compound and selected_count < budget and sole_info:
                        selected_count += 1
                        assigned_total += 1
                        single_sense_assigned_total += 1
                        total_assignments_written += 1

                        chosen_sense_id, (aid, hw, pos) = sole_info
                        proj = {
                            "menu_analysis_id": aid,
                            "selected_sense_id": chosen_sense_id,
                            "selected_tuple": {"headword": hw, "part_of_speech": pos},
                            "source_kind": "provider",
                            "selected_score": 1.0,
                            "runner_up_score": None,
                            "raw_margin": None,
                            "rank": 1,
                            "emitted_level": "leaf",
                            "raw_axis_margins": {"leaf": 1.0, "glosskey": 1.0, "tuple": 1.0},
                        }
                        direct_row = {
                            "assignment_version": "wsd-assignment/v1",
                            "card_id": cid,
                            "surface_form": surf,
                            "sentence_id": sid,
                            "status": "assigned",
                            "sense_menu_content_id": menu_content_id,
                            "menu_analysis_id": aid,
                            "selected_sense_id": chosen_sense_id,
                            "selected_tuple": {"headword": hw, "part_of_speech": pos},
                            "decision_path": ["sole_leaf"],
                            "evidence": {
                                "assigner": "SOLE_LEAF",
                                "model": "single_sense_direct",
                                "reason": "single_sense_direct",
                            },
                            "confidence": 1.0,
                            "model_revisions": {"decision": "single_sense_direct"},
                            "emitted_level": "leaf",
                            "decision_kind": "deterministic_default",
                            "selection_projections": {"provider_only": proj, "mwe_augmented": deepcopy(proj)},
                            "active_selection_projection": "provider_only",
                        }
                        out_f.write(json.dumps(direct_row, ensure_ascii=False) + "\n")
                    else:
                        overflow_total += 1
                        total_assignments_written += 1
                        overflow_row = {
                            "assignment_version": "wsd-assignment/v1",
                            "card_id": cid,
                            "surface_form": surf,
                            "sentence_id": sid,
                            "status": "not_evaluated_example_cap",
                            "sense_menu_content_id": menu_content_id,
                            "menu_analysis_id": None,
                            "selected_sense_id": None,
                            "selected_tuple": None,
                            "decision_path": [],
                            "evidence": {"cap_per_surface": budget, "reason": "per_surface_wsd_execution_cap"},
                            "confidence": None,
                            "model_revisions": {"decision": "single_sense_direct"},
                            "emitted_level": None,
                            "decision_kind": None,
                            "selection_projections": None,
                            "active_selection_projection": None,
                        }
                        out_f.write(json.dumps(overflow_row, ensure_ascii=False) + "\n")

    print(f"   Stage 04 assignments written: {total_assignments_written} total rows.")
    print(f"   Breakdown: assigned={assigned_total} (model={model_assigned_count}, single_sense={single_sense_assigned_total}), NONE={none_total}, overflow={overflow_total}")

    # Stage 04 metadata files
    s4_report = {
        "assignment_counts": {
            "assigned": assigned_total,
            "abstained": none_total,
            "not_evaluated_example_cap": overflow_total,
            "no_menu": 0,
            "rejected": 0,
        },
        "report_version": "wsd-report/v1",
        "run_id": new_run.name,
        "language": "pt",
    }
    write_json(s4_out / "report.json", s4_report)

    s4_method = {
        "method_version": "wsd-method/v1",
        "profile_id": "pt-decide-1-10000",
        "implementation_version": "decide-1/v1",
        "model_revisions": {"decision": "mercury-decide;jev-1.14"},
    }
    write_json(s4_out / "method.json", s4_method)

    s4_manifest = {
        "manifest_version": "stage/v1",
        "stage_name": "wsd_assignments",
        "stage_version": "wsd-assignment-import/v1",
        "status": "complete",
        "started_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "inputs": {
            "inventory": file_content_id(s1_out / "inventory.json"),
            "sense_menu": menu_content_id,
            "candidates": file_content_id(target_cand),
            "sentence_bank": file_content_id(target_sbank),
        },
        "outputs": {
            "assignments": file_content_id(assignments_file),
            "report": file_content_id(s4_out / "report.json"),
            "method": file_content_id(s4_out / "method.json"),
        },
        "config_hash": canonical_content_id({"profile_wsd": profile["wsd"]}),
        "implementation_hash": canonical_content_id({"script": "build_decide1_full_release.py"}),
        "cache_key": canonical_content_id({"s4": file_content_id(assignments_file)}),
        "model_revisions": {"decision": "mercury-decide;jev-1.14"},
        "random_seed": 0,
    }
    write_json(s4_out / "manifest.json", s4_manifest)

    c4 = read_json(new_run / "stages/04_wsd_assignments/contract.json")
    c4.update(status="complete", output_directory="output", manifest_content_id=file_content_id(s4_out / "manifest.json"))
    write_json(new_run / "stages/04_wsd_assignments/contract.json", c4)
    print("   Stage 04 complete.")

    # 6. Build Candidate Release
    print(f"6. Composing release candidate: {RELEASE_ID}...")
    rel_out = WS_ROOT / "releases/pt/speech" / RELEASE_ID
    if rel_out.exists():
        print(f"   Removing existing candidate at {rel_out}...")
        shutil.rmtree(rel_out)

    print("   Building conjugation layer...")
    metadata, layer_report = build_conjugation_layer(
        ws,
        sense_menu=s2_out / "sense-menu.json",
        source_snapshot=WS_ROOT / "raw/conjugations/pt/kaikki" / SNAPSHOT_ID,
    )

    print("   Building inactive run candidate (memory_bounded=True)...")
    output = build_inactive_run_candidate(
        ws,
        run_id=new_run.name,
        release_id=RELEASE_ID,
        language="pt",
        mode="speech",
        conjugations_artifact_id=metadata.artifact_id,
        wsd_selection_projection="mwe_augmented",
        wsd_publication_projection="forced_leaf",
        memory_bounded=True,
    )

    # 6b. Enrich release metadata with equivalences, ties, and separate unused_menu_senses
    print("   Enriching release metadata with equivalences, ties, and unused_menu_senses...")
    deck_rel = read_json(output / "deck.json")
    total_cards = len(deck_rel["cards"])
    print(f"   Release deck contains {total_cards} cards.")

    # Ingest ties from unchanged cards as well
    for c in staged_deck["cards"]:
        if c["card_id"] in unchanged_top1000_cids:
            for ex in c.get("examples", []):
                sid = ex.get("metadata", {}).get("sentence_id")
                ties = ex.get("metadata", {}).get("wsd", {}).get("ties")
                if sid and ties:
                    example_ties_by_id[sid] = ties

    for card in deck_rel["cards"]:
        cid = card["card_id"]
        equiv_map = equiv_by_card_and_sense.get(cid, {})
        ties_map = ties_by_card_and_sense.get(cid, {})

        all_meanings = card.get("meanings", [])
        for m in all_meanings:
            meta = m.setdefault("metadata", {})
            src_sid = m.get("source_sense_id")
            equiv_choices, equiv_sids = equiv_map.get(src_sid, ([], []))
            if equiv_choices:
                meta["equivalent_choices"] = equiv_choices
            if equiv_sids:
                meta["equivalent_sense_ids"] = equiv_sids
            m_ties = ties_map.get(src_sid, [])
            if m_ties:
                meta["ties"] = m_ties

        # Enrich examples with ties
        for ex in card.get("examples", []):
            ex_sid = ex.get("metadata", {}).get("sentence_id")
            if ex_sid in example_ties_by_id:
                ex.setdefault("metadata", {}).setdefault("wsd", {})["ties"] = example_ties_by_id[ex_sid]

        # Separate meanings: assigned vs unused
        assigned = [m for m in all_meanings if m.get("assignment_status") == "assigned"]
        unassigned = [m for m in all_meanings if m.get("assignment_status") != "assigned"]
        if assigned:
            card["meanings"] = assigned
            card["unused_menu_senses"] = unassigned
        else:
            card["unused_menu_senses"] = []

    write_json(output / "deck.json", deck_rel)

    # Re-render app compatibility index
    print("   Re-rendering app compatibility index...")
    app_index = read_json(output / "app/vocabulary.index.json")
    for card in app_index:
        cid = card.get("surface_card_id")
        equiv_map = equiv_by_card_and_sense.get(cid, {})
        ties_map = ties_by_card_and_sense.get(cid, {})
        for m in [*card.get("meanings", []), *card.get("unused_menu_senses", [])]:
            meta = m.setdefault("metadata", {})
            src_sid = m.get("source_sense_id")
            equiv_choices, equiv_sids = equiv_map.get(src_sid, ([], []))
            if equiv_choices:
                meta["equivalent_choices"] = equiv_choices
            if equiv_sids:
                meta["equivalent_sense_ids"] = equiv_sids
            m_ties = ties_map.get(src_sid, [])
            if m_ties:
                meta["ties"] = m_ties

    write_json(output / "app/vocabulary.index.json", app_index)

    # Update manifest file hashes
    manifest = read_json(output / "manifest.json")
    manifest["deck_content_id"] = file_content_id(output / "deck.json")
    manifest["app_contract"]["index_content_id"] = file_content_id(output / "app/vocabulary.index.json")
    write_json(output / "manifest.json", manifest)

    print("   Validating release bundle...")
    validate_release_bundle(output)

    print("   Building merge exceptions...")
    command = [
        sys.executable, str(REPO / "scripts/build_merge_exceptions.py"),
        "--language", "pt",
        "--release-index", str(output / "app/vocabulary.index.json"),
        "--sense-menu", str(s2_out / "sense-menu.json"),
        "--out", str(output / "app/merge-exceptions.json"),
        "--extract", str(SNAPSHOT_PATH),
    ]
    subprocess.run(command, check=True, env={**os.environ, "PYTHONPATH": str(REPO / "src")})

    print("   Sharding app index and examples...")
    shard_app_index(output / "app", slim=True)
    shard_app_examples(output / "app", slim=True)
    print(f"   Candidate release built and sharded at {output}!")

    # 7. Collect deck metrics
    deck_rel = read_json(output / "deck.json")
    total_assigned_examples = sum(len(c.get("examples", [])) for c in deck_rel["cards"])
    total_ties_recorded = sum(
        1 for c in deck_rel["cards"]
        for ex in c.get("examples", [])
        if ex.get("metadata", {}).get("wsd", {}).get("ties")
    )
    print("\n=== Release Deck Summary ===")
    print(f"Release ID: {RELEASE_ID}")
    print(f"Total cards: {len(deck_rel['cards'])}")
    print(f"Assigned examples: {total_assigned_examples}")
    print(f"NONE count (Stage 04): {none_total}")
    print(f"Examples with recorded ties: {total_ties_recorded}")

    # Published separately, after the unchanged-card check.


if __name__ == "__main__":
    main()
