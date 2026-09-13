import json
from pathlib import Path
import unittest


APP_ROOT = Path(__file__).resolve().parents[2] / "app"


class MetadataContractUITests(unittest.TestCase):
    def test_card_ui_prefers_canonical_features_and_source_metadata(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        self.assertIn("const canonical = metadata.sense_metadata || {};", metadata_pills)
        self.assertIn("canonical.source_metadata || metadata.sense_provider_metadata", metadata_pills)
        self.assertIn("Array.isArray(canonical.features)", metadata_pills)

    def test_legacy_string_parsing_is_only_a_pre_contract_compatibility_path(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        self.assertIn("canonical.contract_version ? [] : projectWiktionaryGloss", metadata_pills)
        self.assertIn("if (!canonical.contract_version", metadata_pills)

    def test_canonical_adapter_decisions_are_not_overridden_by_raw_provider_fields(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        fallback = metadata_pills[
            metadata_pills.index("// Provider-shaped fallbacks exist only"):
            metadata_pills.index("// Compatibility for releases made before")
        ]
        self.assertIn("if (!canonical.contract_version)", fallback)
        self.assertIn("for (const region of provider.regions", fallback)

    def test_inactive_wiktionary_subsenses_use_clean_navigation_labels(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        styles = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("function displaySenseGloss(meaning, value, active = true)", flashcards)
        self.assertIn("return senseSummaryText(projected) || projected;", flashcards)
        self.assertIn('class="sense-metadata-tier sense-metadata-tier--primary"', metadata_pills)
        self.assertIn(".sense-metadata-detail + .sense-metadata-detail::before", styles)
        self.assertIn("group-card-varying-cell${isMemberSelected ? ' is-active-subsense' : ''}", flashcards)
        self.assertIn(".group-card-varying-cell:not(.is-active-subsense)", styles)
        self.assertIn(".meaning-row-regular:not(.is-current-sense)", styles)

    def test_active_metadata_is_ordered_compact_and_disclosable(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        styles = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("const familyOrder = {", metadata_pills)
        self.assertIn("const primary = items.filter", metadata_pills)
        self.assertIn("const grammar = items.filter", metadata_pills)
        self.assertIn("display.short", metadata_pills)
        self.assertIn("toggleSenseMetadataOverflow(event, this)", metadata_pills)
        self.assertIn("'gender=variable-by-person': 'varies by gender'", metadata_pills)
        self.assertIn("'form=personal-infinitive': 'personal infinitive'", metadata_pills)
        self.assertIn("'pronoun-class=personal': 'personal pronoun'", metadata_pills)
        self.assertNotIn("if (provider.etymology_text) add('source', 'etymology'", metadata_pills)
        self.assertIn("if (family === 'source' && kind !== 'qualifier') return;", metadata_pills)
        self.assertIn("function isSenseDefiningGrammar(item)", metadata_pills)
        self.assertIn("item.family === 'grammar' && !isSenseDefiningGrammar(item)", metadata_pills)
        self.assertIn("function isSupportingSenseMetadata(item)", metadata_pills)
        self.assertIn("feature.embedding_text", metadata_pills)
        self.assertIn("String(b.sourceText || '').length", metadata_pills)
        self.assertIn("item.kind === 'optional_companion'", metadata_pills)
        self.assertIn("function|mood|noun-class|number|person", metadata_pills)
        self.assertIn("supporting.length === 1 ? ' is-single'", metadata_pills)
        self.assertIn("supporting.length > 1", metadata_pills)
        self.assertIn("sense-metadata-more-label", metadata_pills)
        self.assertIn("${primaryHTML}${grammarHTML}${more}${supportingHTML}", metadata_pills)
        self.assertIn("combine('Early', 'Modern', 'Early Modern')", metadata_pills)
        self.assertNotIn("short.slice(0, 31)", metadata_pills)
        self.assertIn(".sense-metadata-more", styles)
        self.assertIn(".sense-metadata-tier--details.is-single", styles)
        self.assertIn("text-align: center", styles)

    def test_atomic_grammar_features_recombine_for_the_learner(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        self.assertIn("kind: 'combined_sense_mark'", metadata_pills)
        self.assertIn("sourceLabels.join(' · ')", metadata_pills)
        self.assertIn("item.kind === 'combined_sense_mark'", metadata_pills)
        self.assertIn("item.kind === 'complement_form'", metadata_pills)
        self.assertIn("full: `used with ${item.value}`", metadata_pills)
        self.assertIn("item.kind === 'argument_type'", metadata_pills)
        self.assertIn("item.kind === 'clause_context'", metadata_pills)
        self.assertIn("const label = item.sourceText || item.value", metadata_pills)
        self.assertIn("family === 'functional' && kind === 'semantic_scope'", metadata_pills)

    def test_inactive_spanishdict_rows_keep_semantics_but_drop_typed_metadata(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        context_renderer = metadata_pills[
            metadata_pills.index("function contextWithoutSenseMetadata"):
            metadata_pills.index("function toggleSenseMetadataChip")
        ]
        self.assertNotIn("if (!active || !context) return context;", context_renderer)
        self.assertIn("Do this for inactive rows as well", context_renderer)

    def test_canonical_wiktionary_context_is_not_repeated_beside_features(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        self.assertIn("String(provider.context || '').trim() === context", metadata_pills)
        self.assertIn("pure duplication", metadata_pills)

    def test_one_shared_metadata_renderer_serves_every_active_dictionary_language(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        gloss_renderer = flashcards[
            flashcards.index("function displaySenseGloss"):
            flashcards.index("function senseCrossReferences")
        ]
        metadata_renderer = metadata_pills[
            metadata_pills.index("function senseMetadataItems"):
            metadata_pills.index("function contextWithoutSenseMetadata")
        ]
        self.assertNotIn("selectedLanguage", gloss_renderer)
        self.assertNotIn("selectedLanguage", metadata_renderer)
        for language in ("portuguese", "french", "spanish", "czech"):
            with self.subTest(language=language):
                language_config = config["languages"][language]
                self.assertTrue(language_config["hasData"])
                self.assertTrue(language_config["indexPath"].endswith("vocabulary.index.json"))

    def test_cross_references_use_the_same_card_navigation_in_every_language(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        navigation = flashcards[
            flashcards.index("function senseCrossReferences"):
            flashcards.index("function condenseSenseContext")
        ]
        self.assertIn("openSenseCrossReference", navigation)
        self.assertIn("window.popupFoundWord", navigation)
        self.assertNotIn("selectedLanguage", navigation)

    def test_related_cards_are_supporting_navigation_not_gloss_text(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        styles = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("function senseCrossReferenceHTML(meaning, fallbackText, active = true)", flashcards)
        self.assertIn("if (!active) return fallbackText", flashcards)
        self.assertIn('class="sense-cross-reference-gloss"', flashcards)
        self.assertIn('aria-label="Related cards"', flashcards)
        self.assertIn("Indirect form", flashcards)
        self.assertIn("After prepositions", flashcards)
        self.assertIn(".sense-cross-reference-related {", styles)
        self.assertNotIn('sense-metadata-tier-label">grammar', flashcards)

    def test_privileged_companion_and_adaptive_density_ui(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        styles = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        about_example = (APP_ROOT / "js" / "about-example.js").read_text(encoding="utf-8")

        # Privileged companion ordering and icon
        self.assertIn("companion: 0,", metadata_pills)
        self.assertIn("construction: 1,", metadata_pills)
        self.assertIn("export const COMPANION_ICON_SVG =", metadata_pills)
        self.assertIn("sense-pill--companion sense-pill--privileged", metadata_pills)
        self.assertIn("Used with &quot;${escapeCardText(item.value)}&quot;", metadata_pills)

        # Syntax frames and pills
        self.assertIn("sense-pill--syntax", metadata_pills)
        self.assertIn("sense-pill--${family}", metadata_pills)

        # Adaptive density based on sense count
        self.assertIn("senseCount >= 3", metadata_pills)
        self.assertIn("overflowContext", metadata_pills)
        self.assertIn("is-dense", metadata_pills)
        self.assertIn("senseCount: card.meanings?.length", flashcards)

        # Walkthrough demo alignment
        self.assertIn("sense-pill--companion", about_example)
        self.assertIn("sense-pill--syntax", about_example)

        # CSS styling for pills and adaptive density
        self.assertIn(".sense-pill--companion {", styles)
        self.assertIn(".sense-pill--construction,", styles)
        self.assertIn(".sense-pill--register {", styles)
        self.assertIn(".sense-pill--domain {", styles)
        self.assertIn(".sense-metadata-list.is-dense {", styles)
        self.assertIn(".sense-pill + .sense-pill::before {", styles)


if __name__ == "__main__":
    unittest.main()
