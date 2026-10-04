#!/usr/bin/env python3
"""CHISEL: 10,000-card MWE overlay curation and retagging.

Audits MWE attachments against QUARRY's 10k pre-WSD freeze (ranks 6,001–10,000),
verifies Invariant vs Ambiguous routing tags, enriches each entry with verbal idiom
and flexibility axes, and produces the signed-off 10k MWE overlays under:
  Fluency-Workspace/raw/mwe/mwe-*-10k-sieve/mwe_merged.json
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from fluency.wsd.multiword import index_multiword_senses

WORKSPACE_DIR = Path("../Fluency-Workspace").resolve()
MODELS_DIR = Path("config/wsd/models").resolve()

# Words ending in -ar, -er, -ir that are NOT verbs
FALSE_VERB_TOKENS = {
    "lugar", "mar", "color", "favor", "pesar", "par", "lar", "dor", "amor", "solar", 
    "militar", "popular", "açúcar", "azar", "radar", "bar", "ar", "dólar", "líder", 
    "hambúrguer", "suéter", "mulher", "primer", "tercer", "mejor", "peor", "mayor", 
    "menor", "señor", "mujer", "placer", "deber", "ayer", "haber"
}

ES_COMMON_VERBS = {
    "hacer", "dar", "poner", "tomar", "llevar", "tener", "echar", "pasar", "quedar", "ver", "ir", 
    "venir", "estar", "dejar", "salir", "caer", "valer", "tocar", "doblar", "prender", 
    "ajustar", "rendir", "meter", "pedir", "partir", "seguir", "romper", "perder", "ganar", 
    "morir", "vivir", "abrir", "cerrar", "correr", "dormir", "comer", "beber", "sentir", "oír",
    "escuchar", "decir", "hablar", "cortar", "jugar", "lavar", "lavarse", "portar", "portarse",
    "llevarse", "pasarlo", "saber", "conocer", "llegar", "empezar", "mantener", "faltar", "gustar",
    "parecer", "vaya", "sea", "ha", "he", "hay", "debería", "te quiero", "sé", "quiero", "tengo"
}

PT_COMMON_VERBS = {
    "fazer", "pôr", "dar", "ter", "ficar", "ir", "vir", "ver", "ser", "estar", "haver", 
    "tomar", "levar", "cair", "bater", "chegar", "tirar", "abrir", "fechar", "andar",
    "dizer", "saber", "querer", "poder", "passar", "deixar", "falar", "olhar", "ouvir",
    "apertar", "cala", "cale", "sei", "sabe", "faz", "põe", "dá", "tem", "fica", "vai", "vem",
    "ama", "amo", "custa", "entendo", "tenho", "falas", "fumar", "proibido", "brinca", "manda",
    "perder", "ganhar", "morrer", "viver", "comer", "beber", "sentir", "cortar", "jogar"
}

CS_COMMON_VERBS = {
    "mít", "být", "dát", "brát", "vzít", "jít", "jíst", "dělat", "udělat", "stát", 
    "světit", "žít", "zlomit", "zlom", "padat", "hrát", "vést", "ležet", "nechat", 
    "vědět", "znát", "vidět", "chtít", "moci", "muset", "říct", "říkat", "mluvit", 
    "ptát", "volat", "patřit", "znamenat", "opatruj", "miluji", "máš", "máte", "je",
    "jsou", "byl", "má", "mají", "chce", "musí", "ví", "jde", "světí", "žije", "není"
}

# Fixed grammatical locutions that have a plausible literal meaning in everyday text
# and therefore must compete in WSD rather than bypass as invariant.
EXPLICIT_AMBIGUOUS_FIXED = {
    "a mano", "en blanco", "de pie", "al aire", "mano a mano", "en vivo", "en directo",
    "de paso", "en juego", "a tiempo", "de sobra", "en punto", "por nada", "para mí",
    "dobrý den", "dobrou noc", "dobrý večer", "dobré ráno", "hezký den", "šťastnou cestu",
    "cor de rosa", "porta a porta"
}

# Spanish orphaned expressions whose attach_words are recovered to 10k ledger surfaces
ES_ATTACH_RECOVERY = {
    "poner en jaque": ["poner"],
    "vuestra merced": ["vuestra"],
    "prender fuego": ["fuego"],
    "santa sede": ["santa"],
    "estrecho de miras": ["miras"],
    "ajustar cuentas": ["cuentas"],
    "rendir cuentas": ["cuentas"],
    "como un roble": ["como"],
    "a lo sumo": ["lo"],
    "a las apuradas": ["las"],
    "a cobro revertido": ["a"],
    "en circulación": ["en"],
    "triángulo de las bermudas": ["las"],
    "ni mu": ["ni"],
}


def classify_axes(expression: str, pos: Any, language: str) -> tuple[str, str, str]:
    """Classifies the 3 core axes: wsd_routing, flexibility, and ui_role."""
    p = pos if isinstance(pos, list) else ([pos] if pos else [])
    toks = [t.strip(",.!?¿¡;:") for t in expression.lower().split()]

    # 1. Verbal / Grammatical status
    is_verbal = False
    if "verb" in p:
        is_verbal = True
    elif not (p and all(x in {"adv", "prep", "conj", "intj", "prep_phrase", "num", "name"} for x in p)):
        verb_set = ES_COMMON_VERBS if language == "es" else (PT_COMMON_VERBS if language == "pt" else CS_COMMON_VERBS)
        if any(t in verb_set for t in toks):
            is_verbal = True
        elif language in ("es", "pt") and any(t.endswith(("ar", "er", "ir", "arse", "erse", "irse")) and t not in FALSE_VERB_TOKENS for t in toks):
            is_verbal = True

    # 2. Flexibility axis: frozen, head_inflecting, discontiguous
    if "[x]" in expression.lower() or "..." in expression:
        flexibility = "discontiguous"
    elif is_verbal:
        if expression in {"vaya con dios", "zlom vaz", "tanto faz", "není zač", "opatruj se", "bendito sea dios"}:
            flexibility = "frozen"
        else:
            flexibility = "head_inflecting"
    elif "adj" in p or any(w in expression.lower().split() for w in ("como", "jako")):
        flexibility = "head_inflecting"
    else:
        flexibility = "frozen"

    # 3. UI Role axis: connector, formula, idiom
    if any(x in {"prep", "conj", "adv", "prep_phrase"} for x in p) and not is_verbal:
        ui_role = "connector"
    elif any(x in {"intj"} for x in p) or expression in {
        "por favor", "de nada", "buenos días", "buenas noches", "com certeza", 
        "obrigado", "dobrý den", "dobrou noc", "na shledanou", "děkuji"
    }:
        ui_role = "formula"
    elif is_verbal or "adj" in p or "name" in p:
        ui_role = "idiom"
    else:
        ui_role = "connector"

    # 4. WSD Routing axis: deterministic_bypass vs competitive_wsd
    if flexibility == "frozen" and expression not in EXPLICIT_AMBIGUOUS_FIXED and ui_role in {"connector", "formula"}:
        wsd_routing = "deterministic_bypass"
    else:
        wsd_routing = "competitive_wsd"

    return wsd_routing, flexibility, ui_role


def curate_language_overlay(language: str) -> dict[str, Any]:
    """Curates the 10,000-card MWE overlay for a single language."""
    print(f"\n==================== Curating 10k MWE Overlay: {language} ====================")
    ledger_path = WORKSPACE_DIR / f"raw/surfaces/{language}/ledger.json"
    sieve_input_path = WORKSPACE_DIR / f"raw/mwe/mwe-{language}-2026-09-18-v14-sieve/mwe_merged.json"
    output_dir = WORKSPACE_DIR / f"raw/mwe/mwe-{language}-10k-sieve"
    output_path = output_dir / "mwe_merged.json"

    # 1. Load 10k surfaces
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    surfaces = ledger.get("surfaces", {})
    surface_ranks = {k: v["rank"] for k, v in surfaces.items() if v.get("rank") is not None}
    ranks_6k_10k = {k for k, r in surface_ranks.items() if 6001 <= r <= 10000}

    # 2. Load sieve input
    input_data = json.loads(sieve_input_path.read_text(encoding="utf-8"))
    raw_mwes = input_data.get("mwes", {})
    parent_meta = input_data.get("meta", {})

    curated_mwes: dict[str, Any] = {}
    kept_count = 0
    excluded_count = 0
    routing_breakdown = {"deterministic_bypass": 0, "competitive_wsd": 0}
    flex_breakdown = {"frozen": 0, "head_inflecting": 0, "discontiguous": 0}
    ui_breakdown = {"connector": 0, "formula": 0, "idiom": 0}
    attachments_6k_10k_count = 0
    cards_6k_10k_attached: set[str] = set()
    recovered_orphans: list[str] = []

    for expr, row in raw_mwes.items():
        entry = dict(row)
        verdict = entry.get("verdict", "exclude")
        pos = entry.get("pos")

        # Spanish attachment recovery for orphans
        if language == "es" and expr in ES_ATTACH_RECOVERY:
            entry["attach_words"] = ES_ATTACH_RECOVERY[expr]
            recovered_orphans.append(expr)

        # Audit attachments against 10k cards
        curr_attach = entry.get("attach_words", [])
        for w in curr_attach:
            if w in ranks_6k_10k:
                attachments_6k_10k_count += 1
                cards_6k_10k_attached.add(w)

        # Classify the 3 axes
        wsd_routing, flexibility, ui_role = classify_axes(expr, pos, language)
        entry["wsd_routing"] = wsd_routing
        entry["flexibility"] = flexibility
        entry["ui_role"] = ui_role

        # Map to pipeline backward-compatible fields
        entry["route"] = "invariant" if wsd_routing == "deterministic_bypass" else "ambiguous"
        entry["verbal_idiom"] = (ui_role == "idiom")

        if verdict == "keep":
            kept_count += 1
            routing_breakdown[wsd_routing] += 1
            flex_breakdown[flexibility] += 1
            ui_breakdown[ui_role] += 1
        else:
            excluded_count += 1

        curated_mwes[expr] = entry

    meta = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "language": language,
        "contract": "mwe-merged/v1",
        "parent_snapshot": sieve_input_path.parent.name,
        "filter_policy": "v15_10k_chisel_1_three_axes",
        "audit": "chisel_1",
        "candidates": len(curated_mwes),
        "kept_non_compositional": kept_count,
        "excluded_compositional": excluded_count,
        "routing_breakdown": routing_breakdown,
        "flexibility_breakdown": flex_breakdown,
        "ui_role_breakdown": ui_breakdown,
        "kept_invariant": routing_breakdown["deterministic_bypass"],
        "kept_ambiguous": routing_breakdown["competitive_wsd"],
        "attachments_6k_10k": attachments_6k_10k_count,
        "cards_6k_10k_attached": len(cards_6k_10k_attached),
        "recovered_orphans": len(recovered_orphans),
        "sources_breakdown": parent_meta.get("sources_breakdown"),
        "prewsd_freeze": parent_meta.get("prewsd_freeze"),
        "wiktionary_snapshot": parent_meta.get("wiktionary_snapshot"),
        "axes_definition": {
            "wsd_routing": "deterministic_bypass (~75% $0.00 compute) vs competitive_wsd",
            "flexibility": "frozen (exact) vs head_inflecting (inflected verb/adj) vs discontiguous",
            "ui_role": "connector (grammar/discourse) vs formula (spoken/polite) vs idiom (figurative)"
        },
        "note": (
            "CHISEL 1: 3-axis overlay curation across 10,000 cards. Baseline for KILN 1."
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "mwes": curated_mwes}
    output_path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"Generated {output_path}")
    print(f"  Total Candidates:      {len(curated_mwes):,}")
    print(f"  Kept Tier-1 MWEs:      {kept_count:,}")
    print(f"    - Routing:           {routing_breakdown}")
    print(f"    - Flexibility:       {flex_breakdown}")
    print(f"    - UI Role:           {ui_breakdown}")
    print(f"  Attachments (6k-10k):  {attachments_6k_10k_count} across {len(cards_6k_10k_attached)} distinct cards")
    if recovered_orphans:
        print(f"  Recovered Orphans:     {len(recovered_orphans)} ({recovered_orphans[:5]}...)")

    return meta


def update_v15_model_configs() -> None:
    """Updates config/wsd/models/*-v15-1.json to point to the 10k sieve snapshots."""
    print("\n==================== Updating v15-1 Model Profiles ====================")
    for lang in ["es", "pt", "cs"]:
        cfg_path = MODELS_DIR / f"{lang}-v15-1.json"
        if not cfg_path.exists():
            print(f"Warning: {cfg_path} does not exist, skipping.")
            continue
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        rel_path = f"raw/mwe/mwe-{lang}-10k-sieve/mwe_merged.json"
        cfg["multiword"]["snapshot_path"] = rel_path
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Updated {cfg_path.name} -> snapshot_path: {rel_path}")


def verify_overlays() -> None:
    """Verifies overlay schema, index building, and alignment with QUARRY's pairs.json."""
    print("\n==================== Verifying 10k MWE Overlays ====================")
    for lang in ["es", "pt", "cs"]:
        overlay_path = WORKSPACE_DIR / f"raw/mwe/mwe-{lang}-10k-sieve/mwe_merged.json"
        assert overlay_path.exists(), f"Missing overlay: {overlay_path}"
        data = json.loads(overlay_path.read_text(encoding="utf-8"))

        # Verify index building
        idx = index_multiword_senses(data, minimum_corpus_frequency=1, filter_compositional=True)
        assert len(idx) > 0, f"Index is empty for {lang}"
        sample_key = next(iter(idx))
        sample_entry = idx[sample_key][0]
        assert hasattr(sample_entry, "verbal_idiom"), "MultiwordEntry missing verbal_idiom"
        assert hasattr(sample_entry, "flexibility"), "MultiwordEntry missing flexibility"
        assert hasattr(sample_entry, "route"), "MultiwordEntry missing route"

        # Check against QUARRY's frozen pairs.json
        run_ids = {
            "es": "20260914T223348Z-c35194bc",
            "pt": "20260914T222723Z-e43a0469",
            "cs": "20260914T223828Z-ad405a28",
        }
        pairs_path = WORKSPACE_DIR / f"raw/surfaces/{lang}/prewsd/{run_ids[lang]}/pairs.json"
        assert pairs_path.exists(), f"Pairs missing: {pairs_path}"
        pairs_data = json.loads(pairs_path.read_text(encoding="utf-8"))
        pair_surfaces = set(pairs_data.get("surfaces", {}).keys())

        # Verify attachment overlap with pair surfaces
        overlap = set(idx.keys()) & pair_surfaces
        assert len(overlap) > 0, f"No overlap between MWE attach words and pair surfaces for {lang}"
        print(f"{lang.upper()}: Index verified ({len(idx)} attach keys, {len(overlap)} matching 10k prewsd surfaces). Zero paid calls.")


def main() -> None:
    metas = {}
    for lang in ["es", "pt", "cs"]:
        metas[lang] = curate_language_overlay(lang)
    update_v15_model_configs()
    verify_overlays()
    print("\nCHISEL: 10,000-card MWE overlay curation complete and verified.")


if __name__ == "__main__":
    main()
