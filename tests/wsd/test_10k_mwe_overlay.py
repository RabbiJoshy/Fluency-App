"""Unit tests for CHISEL 10,000-card MWE overlay curation, retagging, and attachments."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from fluency.wsd.multiword import (
    MultiwordEntry,
    index_multiword_senses,
    multiword_matches,
)

WORKSPACE_DIR = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace")
MODELS_DIR = Path("config/wsd/models")


class Test10kMWEOverlay(unittest.TestCase):
    def test_overlay_files_exist_and_match_schema(self):
        for lang in ("es", "pt", "cs"):
            overlay_path = WORKSPACE_DIR / f"raw/mwe/mwe-{lang}-10k-sieve/mwe_merged.json"
            self.assertTrue(overlay_path.exists(), f"Missing overlay: {overlay_path}")
            data = json.loads(overlay_path.read_text(encoding="utf-8"))

            meta = data.get("meta", {})
            self.assertEqual(meta.get("audit"), "chisel_2")
            self.assertEqual(meta.get("contract"), "mwe-merged/v1")
            self.assertEqual(meta.get("filter_policy"), "v15_10k_chisel_2_five_axes")
            self.assertGreater(meta.get("routing_breakdown", {}).get("deterministic_bypass", 0), 0)
            self.assertGreater(meta.get("routing_breakdown", {}).get("competitive_wsd", 0), 0)
            self.assertGreater(meta.get("attachments_6k_10k", 0), 0)

            # Check kept entries
            mwes = data.get("mwes", {})
            kept = [v for v in mwes.values() if v.get("verdict") == "keep"]
            self.assertGreater(len(kept), 0)
            for entry in kept:
                self.assertIn("wsd_routing", entry)
                self.assertIn(entry["wsd_routing"], {"deterministic_bypass", "competitive_wsd"})
                self.assertIn("flexibility", entry)
                self.assertIn(entry["flexibility"], {"frozen", "head_inflecting", "discontiguous"})
                self.assertIn("ui_role", entry)
                self.assertIn(entry["ui_role"], {"connector", "formula", "idiom"})
                self.assertIn("transparency", entry)
                self.assertIn(entry["transparency"], {"opaque", "semi_compositional", "formulaic"})
                self.assertIn("template_gap_limit", entry)
                self.assertIn(entry["template_gap_limit"], {0, 1, 2, 3})

    def test_multiword_index_contains_new_axes(self):
        for lang in ("es", "pt", "cs"):
            overlay_path = WORKSPACE_DIR / f"raw/mwe/mwe-{lang}-10k-sieve/mwe_merged.json"
            data = json.loads(overlay_path.read_text(encoding="utf-8"))
            idx = index_multiword_senses(data, minimum_corpus_frequency=1, filter_compositional=True)
            self.assertGreater(len(idx), 0)

            sample_entry = next(iter(idx.values()))[0]
            self.assertIsInstance(sample_entry, MultiwordEntry)
            self.assertIsInstance(sample_entry.verbal_idiom, bool)
            self.assertIn(sample_entry.flexibility, {"frozen", "head_inflecting", "discontiguous"})
            self.assertIn(sample_entry.route, {"invariant", "ambiguous"})
            self.assertIn(sample_entry.transparency, {"opaque", "semi_compositional", "formulaic"})
            self.assertIn(sample_entry.template_gap_limit, {0, 1, 2, 3})

    def test_recovered_orphans_in_spanish(self):
        overlay_path = WORKSPACE_DIR / "raw/mwe/mwe-es-10k-sieve/mwe_merged.json"
        data = json.loads(overlay_path.read_text(encoding="utf-8"))
        mwes = data.get("mwes", {})

        # Verify formerly orphaned expressions now attach to 10k ledger surfaces
        self.assertIn("poner", mwes["poner en jaque"]["attach_words"])
        self.assertIn("fuego", mwes["prender fuego"]["attach_words"])
        self.assertIn("santa", mwes["santa sede"]["attach_words"])
        self.assertIn("cuentas", mwes["ajustar cuentas"]["attach_words"])
        self.assertIn("cuentas", mwes["rendir cuentas"]["attach_words"])

    def test_v15_model_profiles_point_to_10k_sieve(self):
        for lang in ("es", "pt", "cs"):
            model_path = MODELS_DIR / f"{lang}-v15-1.json"
            self.assertTrue(model_path.exists())
            cfg = json.loads(model_path.read_text(encoding="utf-8"))
            expected_snapshot = f"raw/mwe/mwe-{lang}-10k-sieve/mwe_merged.json"
            self.assertEqual(cfg["multiword"]["snapshot_path"], expected_snapshot)

    def test_discontiguous_and_inflected_mwe_matching(self):
        tomar_entry = MultiwordEntry(
            expression="tomar el pelo",
            translations=("to tease", "to pull someone's leg"),
            corpus_frequency=150,
            sources=("wiktionary",),
            entry_id="mwe:tomar el pelo",
            flexibility="head_inflecting",
            verbal_idiom=True,
        )
        poner_entry = MultiwordEntry(
            expression="poner en jaque",
            translations=("to jeopardize",),
            corpus_frequency=50,
            sources=("wiktionary",),
            entry_id="mwe:poner en jaque",
            flexibility="head_inflecting",
            verbal_idiom=True,
        )
        idx = {
            "pelo": (tomar_entry,),
            "jaque": (poner_entry,),
        }

        # 1. Test discontiguous with intervening words
        matches = multiword_matches(
            surface_form="pelo",
            sentence="Le estás tomando a Juan el pelo.",
            index=idx,
        )
        self.assertEqual(len(matches), 1)
        entry, span = matches[0]
        self.assertEqual(entry.expression, "tomar el pelo")
        self.assertEqual(span, (9, 31))  # "tomando a Juan el pelo"

        # 2. Test discontiguous with chess object intervening
        matches_jaque = multiword_matches(
            surface_form="jaque",
            sentence="Poner a su rey en jaque es ilegal.",
            index=idx,
        )
        self.assertEqual(len(matches_jaque), 1)
        entry_j, span_j = matches_jaque[0]
        self.assertEqual(entry_j.expression, "poner en jaque")
        self.assertEqual(span_j, (0, 23))  # "Poner a su rey en jaque"

    def test_v15_profiles_registered_in_wsd_execute(self):
        from fluency.speech.wsd_execute import (
            SUPPORTED_PROFILE_CONSTRAINT_MODES,
            PROFILE_LANGUAGES,
            RANK_AGREEMENT_PROFILES,
            EVIDENCE_GUARD_PROFILES,
            ABSTAIN_UNRESOLVED_PROFILES,
            PHRASE_SKIP_PROVIDER_ORDER_PROFILES,
        )
        for pid, lang in (("es-v15-1", "es"), ("pt-v15-1", "pt"), ("cs-v15-1", "cs")):
            self.assertEqual(SUPPORTED_PROFILE_CONSTRAINT_MODES.get(pid), "filter")
            self.assertEqual(PROFILE_LANGUAGES.get(pid), lang)
            self.assertIn(pid, RANK_AGREEMENT_PROFILES)
            self.assertIn(pid, EVIDENCE_GUARD_PROFILES)
            self.assertIn(pid, ABSTAIN_UNRESOLVED_PROFILES)
            self.assertIn(pid, PHRASE_SKIP_PROVIDER_ORDER_PROFILES)

    def test_multiword_evidence_includes_all_axes(self):
        from fluency.wsd.multiword import multiword_evidence, multiword_analyses

        entry = MultiwordEntry(
            expression="a menudo",
            translations=("often",),
            corpus_frequency=100,
            sources=("wiktionary",),
            entry_id="mwe:a menudo",
            route="invariant",
            verbal_idiom=False,
            flexibility="frozen",
            wsd_routing="deterministic_bypass",
            ui_role="connector",
        )
        idx = {"menudo": (entry,)}
        analyses = multiword_analyses(
            card_id="card_1",
            surface_form="menudo",
            sentence="Voy a menudo al cine.",
            index=idx,
        )
        self.assertEqual(len(analyses), 1)
        analysis, matched_entry, span = analyses[0]
        ev = multiword_evidence(analysis, matched_entry, span, inventory_content_id="test_inv")
        self.assertEqual(ev["wsd_routing"], "deterministic_bypass")
        self.assertEqual(ev["flexibility"], "frozen")
        self.assertEqual(ev["ui_role"], "connector")
        self.assertFalse(ev["verbal_idiom"])
        self.assertEqual(ev["route"], "invariant")

    def test_deterministic_bypass_routing_logic(self):
        from fluency.wsd.multiword import multiword_analyses

        bypass_entry = MultiwordEntry(
            expression="por favor",
            translations=("please",),
            corpus_frequency=500,
            sources=("wiktionary",),
            entry_id="mwe:por favor",
            route="invariant",
            flexibility="frozen",
            wsd_routing="deterministic_bypass",
            ui_role="formula",
        )
        comp_entry = MultiwordEntry(
            expression="dar una mano",
            translations=("to help out",),
            corpus_frequency=80,
            sources=("wiktionary",),
            entry_id="mwe:dar una mano",
            route="ambiguous",
            flexibility="discontiguous",
            wsd_routing="competitive_wsd",
            ui_role="idiom",
        )
        idx = {
            "favor": (bypass_entry,),
            "mano": (comp_entry,),
        }

        # 1. Matching bypass entry:
        matches_favor = list(multiword_analyses(
            card_id="c1", surface_form="favor", sentence="Un café, por favor.", index=idx
        ))
        inv_matches = [
            m for m in matches_favor
            if getattr(m[1], "wsd_routing", "") == "deterministic_bypass"
            or getattr(m[1], "route", "") == "invariant"
        ]
        amb_matches = [
            m for m in matches_favor
            if getattr(m[1], "wsd_routing", "") != "deterministic_bypass"
            and getattr(m[1], "route", "") != "invariant"
        ]
        self.assertEqual(len(inv_matches), 1)
        self.assertEqual(len(amb_matches), 0)
        self.assertEqual(inv_matches[0][1].expression, "por favor")

        # 2. Matching competitive entry:
        matches_mano = list(multiword_analyses(
            card_id="c2", surface_form="mano", sentence="Dame una mano aquí.", index=idx
        ))
        inv_matches_mano = [
            m for m in matches_mano
            if getattr(m[1], "wsd_routing", "") == "deterministic_bypass"
            or getattr(m[1], "route", "") == "invariant"
        ]
        amb_matches_mano = [
            m for m in matches_mano
            if getattr(m[1], "wsd_routing", "") != "deterministic_bypass"
            and getattr(m[1], "route", "") != "invariant"
        ]
        self.assertEqual(len(inv_matches_mano), 0)
        self.assertEqual(len(amb_matches_mano), 1)
        self.assertEqual(amb_matches_mano[0][1].expression, "dar una mano")

    def test_dar_stem_regex_precision(self):
        import re
        from fluency.wsd.multiword import _VERB_STEM_MAP

        dar_pattern = re.compile(rf"\b{_VERB_STEM_MAP['dar']}\b", re.I)
        # Valid forms of dar
        for valid_form in ("da", "dame", "dámelo", "dale", "danos", "dando", "darle", "darte", "dio", "dan", "doy", "daba", "dieron"):
            self.assertTrue(bool(dar_pattern.fullmatch(valid_form)), f"Expected match for: {valid_form}")

        # Invalid non-dar words (prepositions, numerals, other verbs)
        for invalid_word in ("de", "del", "dos", "dicho", "debemos", "diablos", "durante", "desde", "donde", "daño", "dato"):
            self.assertFalse(bool(dar_pattern.fullmatch(invalid_word)), f"Expected rejection for: {invalid_word}")

    def test_por_and_mit_stem_precision(self):
        import re
        from fluency.wsd.multiword import _VERB_STEM_MAP

        # Portuguese pôr vs preposition por
        por_pattern = re.compile(rf"\b{_VERB_STEM_MAP['pôr']}\b", re.I)
        self.assertTrue(bool(por_pattern.fullmatch("pôs")))
        self.assertTrue(bool(por_pattern.fullmatch("ponha")))
        self.assertTrue(bool(por_pattern.fullmatch("puseram")))
        self.assertFalse(bool(por_pattern.fullmatch("por")), "Preposition 'por' must not match 'pôr'")

        # Czech mít vs nouns místo/místě
        mit_pattern = re.compile(rf"\b{_VERB_STEM_MAP['mít']}\b", re.I)
        self.assertTrue(bool(mit_pattern.fullmatch("mám")))
        self.assertTrue(bool(mit_pattern.fullmatch("měl")))
        self.assertTrue(bool(mit_pattern.fullmatch("mají")))
        self.assertFalse(bool(mit_pattern.fullmatch("místo")), "Noun 'místo' must not match 'mít'")
        self.assertFalse(bool(mit_pattern.fullmatch("místě")), "Noun 'místě' must not match 'mít'")

    def test_template_gap_limit_enforcement(self):
        tight_entry = MultiwordEntry(
            expression="tener cuidado",
            translations=("to be careful",),
            corpus_frequency=100,
            sources=("wiktionary",),
            entry_id="mwe:tener cuidado",
            flexibility="head_inflecting",
            verbal_idiom=True,
            template_gap_limit=1,
        )
        idx = {"cuidado": (tight_entry,)}

        # Gap 1 (e.g. "más") matches with template_gap_limit=1
        m_gap1 = multiword_matches(
            surface_form="cuidado",
            sentence="Deberías tener más cuidado.",
            index=idx,
        )
        self.assertEqual(len(m_gap1), 1)

        # Gap 3 fails with template_gap_limit=1
        m_gap3 = multiword_matches(
            surface_form="cuidado",
            sentence="Deberías tener mucho pero mucho cuidado.",
            index=idx,
        )
        self.assertEqual(len(m_gap3), 0)

    def test_chisel_2_bypass_promotions(self):
        es_path = WORKSPACE_DIR / "raw/mwe/mwe-es-10k-sieve/mwe_merged.json"
        data = json.loads(es_path.read_text(encoding="utf-8"))
        mwes = data.get("mwes", {})

        # Verify prominent audited idioms are now deterministic_bypass
        for expr in ("meter la pata", "reino unido", "no sé", "formar parte", "echar un vistazo", "vía láctea"):
            entry = mwes.get(expr)
            self.assertIsNotNone(entry, f"Missing expression: {expr}")
            self.assertEqual(entry.get("wsd_routing"), "deterministic_bypass")
            self.assertEqual(entry.get("calibration_reason"), "promoted_chisel_2_100pct_win")



