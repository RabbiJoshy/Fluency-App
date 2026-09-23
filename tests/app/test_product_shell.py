import json
from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"


# The service worker's cache name, pinned so that bumping an asset version
# without bumping the cache fails here rather than silently serving a stale
# shell. Update alongside app/service-worker.js.
EXPECTED_CACHE_NAME = "flashcards-v548"


class ProductShellTests(unittest.TestCase):
    def test_speech_frequency_files_match_their_releases_and_declare_units(self) -> None:
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        for language, unit in (("spanish", "per_million"), ("french", "per_million"),
                               ("portuguese", "occurrences"), ("czech", "occurrences")):
            language_config = config["languages"][language]
            path = language_config["frequencyPath"]
            data = json.loads((APP_ROOT / path).read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "speech-source-frequency/v1")
            self.assertEqual(data["indexPath"], language_config["indexPath"])
            self.assertEqual(data["unit"], unit)
            self.assertGreaterEqual(data["covered"], data["total"] * 0.95)
            self.assertIn(f"'/{path}'", worker)
        self.assertIn("lemmaSourceFrequencies.get(lemmaGroupKey(item))", vocab)
        self.assertIn("!activeArtist && Number(card.sourceFrequency) > 0", flashcards)

    def test_existing_fluency_entrypoint_and_core_surfaces_are_present(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        for required_id in (
            "authModal",
            "languageTabs",
            "setupPanel",
            "appContent",
            "flashcard",
            "deckProgressSegments",
            "cardBackScrubber",
            "settingsModal",
        ):
            self.assertIn(f'id="{required_id}"', html)
        self.assertIn('src="js/main.js?v=', html)
        self.assertNotIn('src="src/boot.js"', html)

    def test_complete_existing_runtime_module_set_is_transplanted(self) -> None:
        for filename in (
            "main.js",
            "state.js",
            "ui.js",
            "vocab.js",
            "grammar-cards.js",
            "flashcards.js",
            "progress.js",
            "knowledge.js",
            "speech.js",
            "auth.js",
            "theme.js",
            "data-contracts.js",
        ):
            self.assertTrue((APP_ROOT / "js" / filename).is_file(), filename)
        self.assertFalse((APP_ROOT / "src").exists())

    def test_abandoned_preview_and_csv_paths_are_removed(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (APP_ROOT / "js").glob("*.js")
        )
        self.assertFalse((APP_ROOT / "js" / "speech-vnext.js").exists())
        self.assertNotIn("speechVnext", combined)
        self.assertNotIn("loadCSVFiles", combined)

    def test_card_data_is_available_without_owner_login(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.assertIn("label: 'Card data'", flashcards)
        self.assertNotIn("if (!isJstOwner()) return null", flashcards)
        self.assertIn('class="prov-ex-record"', flashcards)
        self.assertIn("['Occurrence', x.occurrence_id]", flashcards)
        self.assertIn("Raw example record", flashcards)
        self.assertIn("Historical retained assignment", flashcards)
        self.assertIn("Release ${esc(releaseId)}", flashcards)

    def test_spanishdict_inspector_is_audit_only(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.assertIn("function canInspectSpanishDictData()", flashcards)
        self.assertIn("canInspectSpanishDictData()", flashcards)
        self.assertIn("window.isAuditAccount?.()", flashcards)
        self.assertIn('class="ref-tile ref-dictionary-btn"', flashcards)
        self.assertIn("if (!canInspectSpanishDictData()) return;", flashcards)

    def test_synonym_jump_uses_the_language_lookup_not_spanishdict(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.assertIn("function synonymExternalLookup(word)", flashcards)
        self.assertIn("function confirmLeaveForSynonymLookup(word, lookup)", flashcards)
        self.assertIn("['wordReference', 'WordReference']", flashcards)
        self.assertNotIn(
            "https://www.spanishdict.com/translate/${encodeURIComponent((word || '').toLowerCase())}",
            flashcards,
        )

    def test_only_languages_with_clean_releases_are_enabled(self) -> None:
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        enabled = {
            key for key, value in config["languages"].items()
            if value.get("hasData", True)
        }
        self.assertEqual(enabled, {"czech", "french", "portuguese", "spanish"})
        self.assertEqual(config["languages"]["portuguese"]["name"], "Portuguese")
        self.assertEqual(config["languages"]["portuguese"]["flag"], "🇵🇹")
        self.assertEqual(config["languages"]["portuguese"]["speechLang"], "pt-PT")
        self.assertFalse(config["languages"]["portuguese_brazilian"]["hasData"])
        self.assertEqual(config["languages"]["portuguese_brazilian"]["flag"], "🇧🇷")
        self.assertEqual(config["languages"]["portuguese_brazilian"]["speechLang"], "pt-BR")
        self.assertEqual(
            config["languages"]["spanish"]["studyStructurePath"],
            "releases/es/speech/es-speech-v15-10000x10/app/study-structure.json",
        )
        self.assertEqual(
            config["languages"]["spanish"]["releaseManifestPath"],
            "releases/es/speech/es-speech-v15-10000x10/manifest.json",
        )
        self.assertEqual(
            config["languages"]["spanish"]["releaseCompositionPath"],
            "releases/es/speech/es-speech-v15-10000x10/composition.json",
        )
        for legacy_path in (
            "conjugatedEnglishPath",
            "ppmDataPath",
        ):
            self.assertNotIn(legacy_path, config["languages"]["spanish"])
        self.assertEqual(
            config["languages"]["spanish"]["conjugationsPath"],
            "releases/es/speech/es-speech-v12-6000x10-conj/app/conjugations.json",
        )
        self.assertEqual(
            config["languages"]["portuguese"]["indexPath"],
            "releases/pt/speech/pt-speech-v15-10000x10/app/vocabulary.index.json",
        )
        self.assertEqual(
            config["languages"]["portuguese"]["conjugationsPath"],
            "releases/pt/speech/pt-speech-v12-6000x10-conj/app/conjugations.json",
        )
        self.assertEqual(
            config["languages"]["czech"]["indexPath"],
            "releases/cs/speech/cs-speech-v15-10000x10/app/vocabulary.index.json",
        )
        self.assertEqual(
            config["languages"]["czech"]["conjugationsPath"],
            "releases/cs/speech/cs-speech-v12-4000x10-conj/app/conjugations.json",
        )
        self.assertEqual(
            config["languages"]["french"]["indexPath"],
            "releases/fr/speech/fr-speech-v7-dual-metadata-v5-20260918/app/vocabulary.index.json",
        )
        self.assertEqual(
            config["languages"]["french"]["conjugationsPath"],
            "releases/fr/speech/fr-speech-v7-dual-metadata-v3-20260910-conj/app/conjugations.json",
        )
        self.assertIsNone(config["languages"]["dutch"]["conjugationsPath"])
        self.assertNotIn("ppmDataPath", config["languages"]["french"])
        self.assertEqual(
            config["languages"]["french"]["studyStructurePath"],
            "releases/fr/speech/fr-speech-v7-dual-metadata-v5-20260918/app/study-structure.json",
        )
        root_entries = {p.name for p in APP_ROOT.iterdir()}
        self.assertNotIn("Data", root_entries)
        self.assertNotIn("Artists", root_entries)

    def test_speech_release_can_be_previewed_without_activation(self) -> None:
        config_js = (APP_ROOT / "js" / "config.js").read_text(encoding="utf-8")
        self.assertIn("params.get('speechRelease')", config_js)
        self.assertIn("releases/${code}/speech/${encodeURIComponent(releaseId)}", config_js)
        self.assertIn("languageConfig.releaseManifestPath = `${base}/manifest.json`", config_js)

    def test_merge_lemma_control_explains_missing_capability(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        fast_mode = (APP_ROOT / "js" / "fast-mode.js").read_text(encoding="utf-8")
        self.assertIn("lemmaContainer.dataset.available = String(lemmaFieldAvailable)", ui)
        self.assertIn("showFastModeUnavailable?.('lemmas')", ui)
        self.assertIn("Word-form mapping not found for", fast_mode)

    def test_language_choice_defers_loading_until_source_choice(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))

        self.assertIn('id="standardSourceSpeechBtn"', html)
        self.assertIn('id="standardSourcePickerBtn"', html)
        self.assertIn("speechSourceButton.onclick", ui)
        self.assertIn("sourceCardButton.onclick = openLyrics", ui)
        self.assertNotIn("sessionStorage.removeItem('fluencyPendingSpeechLanguage');\n            await continueToSpeech();", ui)
        self.assertIn("if ((isResumeNavigation || wordRoute) && !activeArtist) {", main)
        self.assertIn("if (window.loadConjugationData) await window.loadConjugationData();", main)
        self.assertIn("if (window.loadConjugationData) window.loadConjugationData();", ui)
        self.assertNotIn("if (window.loadConjugationData) await window.loadConjugationData();", ui)
        self.assertTrue(config["languages"]["spanish"]["capabilities"]["speech"])
        self.assertTrue(config["languages"]["spanish"]["capabilities"]["lyrics"])
        self.assertTrue(config["languages"]["french"]["capabilities"]["speech"])
        self.assertFalse(config["languages"]["french"]["capabilities"]["lyrics"])
        self.assertIn("if (speechSourceButton.disabled) return", ui)

    def test_learning_context_replaces_repeated_language_setup(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        progress = (APP_ROOT / "js" / "progress.js").read_text(encoding="utf-8")
        modals = (APP_ROOT / "js" / "flashcards-modals.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")

        for required_id in (
            "learningContextBtn",
            "learningContextModal",
            "learningContextSourceBtn",
            "levelCompleteCelebration",
        ):
            self.assertIn(f'id="{required_id}"', html)
        self.assertIn("fluencyPreferredLanguageV1", main)
        self.assertIn("fluencyPreferredLanguageV1", ui)
        self.assertIn("context-ready", ui)
        self.assertIn("id: 'learningSourceChoiceSheet'", main)
        self.assertNotIn("Current learning context", html)
        self.assertNotIn('id="learningContextTitle"', html)
        self.assertIn('aria-label="Your learning settings"', html)
        self.assertIn('class="learning-context-switches"', html)
        self.assertIn('class="learning-context-progress" type="button"', html)
        self.assertNotIn("learningContextAction--secondary", html)
        self.assertIn("showSettingsModalWithTab('account')", main)
        self.assertIn("getCurrentCoverageSnapshot", progress)
        self.assertIn("window.lastSetupCoverageSnapshot", progress)
        self.assertIn("isLevelCompletion", modals)
        self.assertIn("Review this level", modals)
        self.assertIn("this.dataset.action === 'review-level'", flashcards)
        self.assertNotIn("Natural speech", html)
        self.assertIn("The words people say in films and TV", html)
        self.assertIn("The words in songs you choose", html)
        self.assertIn("original line as the example", html)
        self.assertNotIn('id="learningContextMode"', html)
        self.assertNotIn('id="learningContextCoverage"', html)
        self.assertIn("Recommended", html)
        self.assertIn("Music &amp; lyrics", html)
        self.assertIn("Look up a playlist and study speech meanings", main)
        self.assertNotIn('<span class="step-number">1</span>', html)

    def test_merge_lemmas_remains_a_declared_learner_feature(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        self.assertTrue(config["languages"]["spanish"]["capabilities"]["mergeLemmas"])
        self.assertIn("window._activeReleaseCapabilities?.mergeLemmas", ui)
        self.assertIn("Keep the explanation and its control visible", ui)

    def test_card_back_omits_only_redundant_single_pos_legend(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.assertIn("const hideRedundantSingleBackPos", flashcards)
        self.assertIn("posItems.length === 1", flashcards)
        self.assertIn("!onlyPosHasAction", flashcards)
        self.assertIn("!suppressBackPosLegend && !hideRedundantSingleBackPos", flashcards)

    def test_replica_card_uses_the_current_compact_back(self) -> None:
        replica = (APP_ROOT / "js" / "card-replica.js").read_text(encoding="utf-8")
        tutorial = (APP_ROOT / "js" / "tutorial.js").read_text(encoding="utf-8")
        self.assertNotIn('<div class="back-pos-legend"', replica)
        self.assertIn('class="pos-section-head"', replica)
        self.assertIn('class="meaning-row-check"', replica)
        self.assertIn('class="example-ticks"', replica)
        self.assertNotIn('class="compact-example-counter-label"', replica)
        self.assertIn("speechCard: 'tem'", tutorial)
        self.assertIn('class="sense-metadata-tier sense-metadata-tier--primary"', replica)
        self.assertIn('class="sense-metadata-more"', replica)
        self.assertIn('class="sense-cross-reference"', replica)
        self.assertIn('replicaSenseSummary(meaning.translation)', replica)
        self.assertNotIn("font-family: var(--font-data); font-size: 14px", replica)

    def test_mobile_tutorial_is_a_guided_animated_sequence(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        tutorial = (APP_ROOT / "js" / "tutorial.js").read_text(encoding="utf-8")
        styles = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn('id="cardTutorialMobileCoach"', html)
        self.assertIn("function moveMobileTour(direction)", tutorial)
        self.assertIn("MOBILE_TUTORIAL_QUERY", tutorial)
        # Front and back of a flashcard, not "question side" / "answer side":
        # anyone reaching for a tutorial already knows what a flashcard is.
        self.assertIn("'Flip over'", tutorial)
        self.assertNotIn("answer side", tutorial)
        self.assertNotIn("question side", tutorial)
        self.assertIn("'Finish'", tutorial)
        # The story is a flat list of steps: Speech front, Speech back, a slide
        # about Lyrics mode, then a Lyrics card. Front before back throughout.
        self.assertIn("function tutorialSteps()", tutorial)
        self.assertIn("{ kind: 'card', deck: 'speech', face: 'front' }", tutorial)
        self.assertIn("{ kind: 'break', id: 'lyrics' }", tutorial)
        self.assertIn("function renderBreakStep()", tutorial)
        self.assertIn('id="cardTutorialBreak"', html)
        self.assertIn(".card-tutorial-body.is-break-step", styles)
        # No mode chrome in what the header renders: a first-time reader has
        # not met either mode yet. (The comment above the change still names
        # the old chip, so assert on the template, not on the file's prose.)
        self.assertNotIn("<span>${modes}</span>", tutorial)
        # The tutorial owns the flip. Tapping the card and pressing space
        # both used to turn it mid-tour, which broke the guided order.
        self.assertNotIn("function wireCardShell", tutorial)
        self.assertNotIn("e.key === ' '", tutorial)
        # A short mime of the setup flow runs before the first card.
        self.assertIn('id="cardTutorialSetupAnim"', html)
        self.assertIn("function playSetupIntro(onDone)", tutorial)
        self.assertIn("function skipSetupIntro()", tutorial)
        # The intro holds on its last step and waits to be dismissed by hand
        # rather than pressing its own button and moving on.
        self.assertIn("function startSetupIntroCard()", tutorial)
        self.assertIn(".setup-anim-learn-btn.is-ready", styles)
        # The intro is a replica of the real setup screen, so it reuses that
        # screen's own class names rather than a lookalike.
        self.assertIn("standard-source-choice-btn", html)
        self.assertIn("learning-context-chip", html)
        self.assertIn("function moveSetupPointer(target)", tutorial)
        # The numbered badges indexed a numbered note list; both are gone, and
        # the amber ring on the annotated element is the only link left.
        self.assertNotIn("card-tutorial-marker", tutorial)
        self.assertNotIn("card-tutorial-note-num", tutorial)
        self.assertIn(".card-tutorial-anchored.is-annotation-active", styles)
        self.assertIn(".card-tutorial-body.is-setup-intro", styles)
        self.assertIn("@keyframes card-tutorial-mobile-spotlight", styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)

    def test_speech_cards_keep_dictionary_examples_separate_from_usage_share(self) -> None:
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.assertNotIn("examples: mergeReferenceExamples(m.examples || [], m)", vocab)
        self.assertIn("if (m.canonical_example) meaning.canonicalExample = m.canonical_example;", vocab)
        self.assertIn("item._indexRowsPending === true", vocab)
        self.assertGreaterEqual(vocab.count("source_mode: 'reference'"), 2)
        self.assertIn("be merged into corpus ticks", vocab)
        self.assertIn("function canonicalExampleHTML(meaning)", flashcards)
        self.assertIn("function displayExamplesForSense(meaning, examples", flashcards)
        self.assertIn("function rankConfidentWsdExamples(examples)", flashcards)
        self.assertIn("function chooseSingleDisplayExample(meaning, examples", flashcards)
        self.assertIn("function isReliableWsdExample(example)", flashcards)
        self.assertIn("const WSD_EXAMPLE_LEVEL_RANK", flashcards)
        self.assertNotIn("method && method !== 'unassigned'", flashcards)
        self.assertNotIn("backHTML += canonicalExampleHTML(currentMeaning);", flashcards)
        self.assertIn("if (examplesAllowCycling(examples)) return examples;", flashcards)
        self.assertIn("function highlightWithDeclaredOffsets(text, offsets)", flashcards)
        self.assertIn("spanishdict.com", flashcards)
        self.assertIn("wiktionary.org", flashcards)
        self.assertIn("function exampleSourceChipHTML", flashcards)
        self.assertIn("function exampleTicksHTML(current, total, label = 'example')", flashcards)
        self.assertIn(
            '<span class="example-credit-start">${creditStart}</span>\n'
            '                    <span class="example-credit-end">${exampleTicks}${creditEnd}</span>',
            flashcards,
        )
        self.assertNotIn('compact-example-counter-label', flashcards)

    def test_only_the_active_meaning_group_exposes_subsenses(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.assertIn(
            "card._expandedPos = new Set([lemmaPosGroupKeyForMeaning(currentMeaning)])",
            flashcards,
        )

    def test_wiktionary_grammar_tails_become_compact_metadata(self) -> None:
        metadata_pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        self.assertIn("function isWiktionaryGrammarNote(note)", metadata_pills)
        self.assertIn("family === 'grammar' ? 'gloss_note'", metadata_pills)
        self.assertIn("addressing several people", metadata_pills)
        self.assertIn("'mood=imperative': 'command'", metadata_pills)

    def test_first_run_tutorial_is_once_only_and_replayable(self) -> None:
        auth = (APP_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
        tutorial = (APP_ROOT / "js" / "tutorial.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("window.openFirstRunCardTutorial?.()", auth)
        # Guest and sign-in both offer it; a linked word defers it to a later visit.
        self.assertEqual(auth.count("setTimeout(_openFirstRunTutorialUnlessLinked, 250)"), 2)
        self.assertIn("function openFirstRunCardTutorial()", tutorial)
        self.assertIn("const TUTORIAL_LANGUAGE_ADAPTERS", tutorial)
        self.assertIn("function tutorialSteps()", tutorial)
        self.assertIn("Step ${progress.current} of ${progress.total}", tutorial)
        self.assertIn("function explicitTutorialLanguageKey()", tutorial)
        self.assertIn("if (!explicitTutorialLanguageKey()) return false", tutorial)
        self.assertNotIn("TUTORIAL_DECK_SEQUENCE", tutorial)
        self.assertIn("spanish: { language: 'Spanish'", tutorial)
        self.assertIn("portuguese: { language: 'Portuguese'", tutorial)
        self.assertIn("czech: { language: 'Czech'", tutorial)
        self.assertIn("french: { language: 'French'", tutorial)
        self.assertNotIn("function renderTabs()", tutorial)
        self.assertIn("fluencyCardWalkthroughSeenV1", tutorial)
        self.assertIn("fluencyCardWalkthroughSeenV1", flashcards)
        self.assertIn("helpBtn').addEventListener('click', openTutorialIntroduction", main)

    def test_about_links_the_walkthrough_and_never_the_tutorial(self) -> None:
        # Three things for three audiences (docs/NOMENCLATURE.md): the tutorial
        # is for learners, the walkthrough and About are for visitors. About
        # links the walkthrough; it must not open or contain the tutorial.
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        about = (APP_ROOT / "content" / "about.md").read_text(encoding="utf-8")
        auth = (APP_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
        self.assertIn('id="helpBtn" class="top-bar-icon-btn"', html)
        self.assertIn('aria-label="Open tutorial"', html)
        # The demo cards are the way in: tapping one opens the walkthrough on
        # that card, with a caption under the pair saying so.
        self.assertIn("window.openWalkthrough?.({ start })", auth)
        self.assertIn("Tap a card to see every part of it explained", auth)
        self.assertIn("demo://normal", about)
        self.assertIn("demo://artist", about)
        self.assertNotIn("tutorial", about.lower())
        self.assertIn("window.openWalkthrough && window.openWalkthrough()", auth)
        self.assertNotIn("startAboutTutorial", auth)
        self.assertNotIn("openTutorialIntroduction", auth)
        self.assertNotIn("openCardTutorial?.()", auth.replace("openFirstRunCardTutorial?.()", ""))
        # Visitors arrive logged out, onto the landing card. About and the
        # walkthrough on top of it must stack above it or nobody sees them.
        styles = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("#aboutProjectModal {\n    z-index: 30002;", styles)
        self.assertIn("#walkthroughModal {\n    z-index: 30003;", styles)
        self.assertIn("#authModal {\n            z-index: 30001;", styles)
        # The walkthrough is layered after About in the DOM, over it.
        self.assertLess(html.index('id="aboutProjectModal"'), html.index('id="walkthroughModal"'))

    def test_walkthrough_is_a_short_whole_face_demo_for_visitors(self) -> None:
        walkthrough = (APP_ROOT / "js" / "walkthrough.js").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        # Shares the replica card with the tutorial rather than a copy of it.
        self.assertIn("from './card-replica.js?v=", walkthrough)
        self.assertIn("import './walkthrough.js?v=", main)
        # Two screens where two cards fit side by side, three on a phone.
        self.assertIn("function buildScreens(pair)", walkthrough)
        self.assertIn("id: 'card'", walkthrough)
        self.assertIn("id: 'lyrics'", walkthrough)
        # Every label on a face at once, not one ringed element per step.
        self.assertIn("function placeLabels()", walkthrough)
        self.assertIn("walkthrough-callout", walkthrough)
        self.assertIn("walkthrough-pin", walkthrough)
        # No learner machinery: no setup intro, no language choice.
        self.assertNotIn("playSetupIntro", walkthrough)
        self.assertNotIn("setCardTutorialLanguage", walkthrough)
        self.assertIn("'Back to About'", walkthrough)

    def test_tutorial_and_replica_are_separate_modules(self) -> None:
        self.assertFalse((APP_ROOT / "js" / "about-example.js").exists())
        tutorial = (APP_ROOT / "js" / "tutorial.js").read_text(encoding="utf-8")
        replica = (APP_ROOT / "js" / "card-replica.js").read_text(encoding="utf-8")
        self.assertIn("from './card-replica.js?v=", tutorial)
        self.assertIn("export const REPLICA_CARDS", replica)
        # The replica knows nothing about steps, notes or audiences.
        for word in ("tutorialSteps", "stepNotes", "openWalkthrough", "openCardTutorial"):
            self.assertNotIn(word, replica)

    def test_setup_shell_uses_a_quiet_single_surface_hierarchy(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn('class="step-title step-title-trigger" data-tooltip="step5Tooltip"', html)
        self.assertIn('class="step-title step-title-trigger" data-tooltip="step2Tooltip"', html)
        self.assertIn('id="fastTrackHubBtn"', html)
        self.assertIn(".sync-status.is-synced { display: none; }", css)
        self.assertIn(".fast-mode-master-switch", css)
        self.assertIn(".fast-track-hub-btn {", css)
        self.assertIn(".fast-track-hub-row {", css)
        self.assertIn("#step2,\n#step4 {", css)
        self.assertIn("--accent-primary: #8795ff;", css)

    def test_in_app_tutorial_has_a_short_separate_intro_and_top_action(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        intro = html.index('id="tutorialIntroModal"')
        start = html.index('id="startCardTutorialBtn"', intro)
        choices = html.index('id="tutorialLanguageChoices"', intro)
        self.assertLess(start, choices)
        self.assertNotIn('id="tutorialLanguageSelect"', html)

        self.assertIn("window.openCardTutorial?.()", main)
        self.assertIn("function startCardTutorial()", main)
        self.assertIn("function renderTutorialLanguageChoices()", main)
        self.assertIn("tutorialLanguageStep')?.classList.remove('hidden')", main)
        self.assertIn("window.getCardTutorialLanguageKey?.()", main)
        self.assertIn("window.setCardTutorialLanguage?.(key)", main)
        self.assertIn("How common this meaning is", (APP_ROOT / "js" / "tutorial.js").read_text(encoding="utf-8"))
        self.assertIn("Tap them to read Common, Uncommon, or Rare", (APP_ROOT / "js" / "tutorial.js").read_text(encoding="utf-8"))

    def test_sense_frequency_uses_readable_labels_not_mystery_dots(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        tutorial = (APP_ROOT / "js" / "tutorial.js").read_text(encoding="utf-8")
        self.assertIn("function prominenceBadgeHTML(promInfo, extraStyle = '')", flashcards)
        self.assertIn("function toggleProminenceBadge(event, button)", flashcards)
        self.assertIn("sense-prominence-meter", flashcards)
        self.assertIn("function prominenceInfoFromShare(meanings)", flashcards)
        self.assertIn("function withinGlossLeafSeparationIsReliable(meanings)", flashcards)
        self.assertIn("function glossClusterProminenceState(card)", flashcards)
        self.assertIn("class=\"cbs-scrub\"", (APP_ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertIn("sense-prominence-detail", flashcards)
        self.assertNotIn("sense-prominence-dots", flashcards)
        self.assertIn("conjugationsPath)", flashcards)
        self.assertIn("conjugationData: _conjugationData", flashcards)
        self.assertIn("window.loadConjugationData()", (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8"))
        self.assertIn("function replicaProminence(pct)", (APP_ROOT / "js" / "card-replica.js").read_text(encoding="utf-8"))
        self.assertIn("How common this meaning is", tutorial)
        self.assertIn("Tap them to read Common, Uncommon, or Rare", tutorial)

    def test_in_app_tutorial_skips_language_choice_when_one_is_already_selected(self) -> None:
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("function startCardTutorial()", main)
        start = main.index("function startCardTutorial()")
        language_step = main.index("tutorialLanguageStep')?.classList.remove('hidden')", start)
        self.assertLess(main.index("getCardTutorialLanguageKey?.()", start), language_step)
        self.assertLess(main.index("setCardTutorialLanguage?.(knownLanguage)", start), language_step)

    def test_fast_track_has_one_language_switch_and_fine_tuning(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="level-choosing"', html)
        choosing = html[html.index('class="level-choosing"'):html.index('id="step4"')]
        self.assertIn('id="levelSelector"', choosing)
        self.assertIn('id="setupOptions"', choosing)
        # One row carrying both: the switch turns Fast Track on where the
        # learner already is, and the rest of the row opens the page that says
        # what that means. A first-time user needs the second half.
        self.assertIn('id="fastTrackHubBtn"', choosing)
        self.assertIn('id="fastTrackHubSwitch"', choosing)
        self.assertIn('id="fastTrackHubSummary"', choosing)
        self.assertNotIn('id="fastModeToggleBtn"', html)
        self.assertNotIn('id="fastModeDetailBtn"', html)
        self.assertNotIn('id="settingsFastTrackBtn"', html)
        # The sheet leads with the explanation, and its controls are the page
        # rather than a drawer inside it, so neither a second master switch nor
        # a reveal button survives.
        self.assertNotIn('id="fastModeHomeSwitch"', html)
        self.assertNotIn('id="fastModeFineTuneBtn"', html)
        self.assertNotIn('id="fastModeLanguageStatus"', html)
        self.assertIn('id="fastModeFineTune"', html)
        # The skipped and merged word lists belong to the steps that create
        # them, not to a duplicate set of rows above them.
        self.assertIn('id="viewSkippedWordsBtn"', html)
        self.assertIn('id="viewMergedFormsBtn"', html)
        self.assertNotIn('id="fastModeSkippedWordsRow"', html)
        self.assertNotIn('id="fastModeMergedFormsRow"', html)
        self.assertNotIn('id="fastModeSkippedLink"', html)
        # The skipped-word decks sit below the controls that produce them.
        self.assertIn('id="fastTrackDeckCard"', html)
        self.assertLess(html.index('id="fastModeFineTune"'), html.index('id="fastTrackDeckCard"'))

    def test_settings_are_organised_around_learner_tasks(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        overview = html[html.index('id="studyTabContent"'):html.index('id="lookupTabContent"')]
        self.assertIn('id="settingsImportKnownBtn"', overview)
        self.assertIn('id="settingsExportMistakesBtn"', overview)
        self.assertIn('id="settingsFindWordBtn"', overview)
        self.assertIn('data-open-find-word', overview)
        self.assertIn('id="settingsWordsDataBtn"', overview)
        self.assertIn('id="settingsAccountBtn"', overview)
        self.assertIn('id="appearanceSettingsTitle">Theme', overview)
        self.assertIn('id="progressImportKnownBtn"', html)
        self.assertIn('id="progressExportMistakesBtn"', html)
        self.assertIn('id="settingsBackBtn"', html)
        self.assertIn('function setupSettingsOverview()', ui)
        self.assertIn('> .settings-tabs { display: none !important; }', css)
        self.assertIn("Show first", html)
        self.assertIn("Speak the word", html)
        self.assertIn('Bring back learned words', overview)
        # Rare senses open from the card's "Rarer uses" tile as a sheet, so
        # there is no longer a setting that chains them as a child card.
        self.assertNotIn('More study options', overview)
        self.assertNotIn('Rare senses after a correct answer', overview)
        self.assertNotIn('Expressions after a correct answer', overview)
        self.assertNotIn('data-setting="rareSensesMode"', overview)
        self.assertNotIn('data-setting="expressionsMode"', overview)
        self.assertNotIn('data-setting="phrasesMode"', overview)
        self.assertIn('expressionsModeEnabled = true;', ui)

    def test_fast_track_skipped_words_are_study_sets_of_twenty(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        extras = (APP_ROOT / "js" / "extras.js").read_text(encoding="utf-8")
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn('id="viewSkippedWordsBtn"', html)
        self.assertIn('id="skippedWordsSearch"', html)
        self.assertIn('id="mergedFormsTotal"', html)
        self.assertIn('id="skippedWordsTotal"', html)
        self.assertIn("class=\"extras-open-card\"", extras)
        self.assertIn("${escapeHtml(item.word)}</button>", extras)
        self.assertIn("globalThis.popupFoundWord", extras)
        self.assertIn('class="extras-set-pill${complete', extras)
        self.assertIn('class="extras-level-group"${current', extras)
        self.assertIn('function skippedByLevel', extras)
        self.assertIn("function startFastTrackSkippedSet", extras)
        self.assertIn("fastTrackCards: slice", extras)
        self.assertIn("startFastTrackSkippedSet", ui)
        self.assertIn(".extras-set-pill", css)
        self.assertNotIn("openSpeechExtrasBtn", ui)
        self.assertIn("#settingsModal.product-modal { align-items: flex-start; }", css)

    def test_wsd_publication_view_is_user_selectable(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        self.assertIn('data-wsd-publication="forced_leaf"', html)
        self.assertIn('data-wsd-publication="supported_specificity"', html)
        self.assertIn("window.setWsdPublicationProjection", ui)
        self.assertIn("target.searchParams.set('wsdPublication', projection)", vocab)

    def test_active_set_keeps_existing_interaction_model(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        for behavior in (
            "flipCard",
            "handleSwipeAction",
            "cycleExample",
            "showEndOfDeckOptions",
            "deckProgressSegments",
        ):
            self.assertIn(behavior, flashcards)
        self.assertIn('id="cardBackScrubber"', (APP_ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertIn("saveStudySessionSnapshot", flashcards)
        self.assertIn("buildFocusedReviewCard", vocab)

    def test_unassigned_dictionary_menu_does_not_claim_wsd_confidence(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("if (!m.unassigned)", flashcards)
        self.assertIn("hasAssignedEvidence", flashcards)
        self.assertIn("pos-pill-unassigned", flashcards)
        self.assertIn(".pos-collapsible .pos-pill-unassigned", css)

    def test_collapsed_sense_group_uses_measured_overflow_and_clear_hierarchy(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("function fitPosSectionSummaries(root)", flashcards)
        self.assertIn("summary.scrollWidth > summary.clientWidth + 1", flashcards)
        self.assertIn("function senseSummaryText(value)", flashcards)
        self.assertIn("senses[index].hidden = true", flashcards)
        self.assertIn('class="pos-summary-sense"', flashcards)
        self.assertIn('class="pos-pill-more" hidden', flashcards)
        self.assertIn("fitPosSectionSummaries(backEl)", flashcards)
        self.assertIn("fitPosSectionSummaries(document.getElementById('backContent'))", flashcards)
        self.assertIn(".pos-collapsible .pos-section-summary", css)
        self.assertIn("font-size: 16px", css)
        self.assertIn("showBackLemmaPair", flashcards)
        self.assertIn('class="pos-pill-pct sense-percentage"', flashcards)
        self.assertIn('class="sense-percentage sense-percentage-tail"', flashcards)
        self.assertIn(".sense-percentage", css)
        self.assertIn("border-left: 1px solid rgba(var(--sense-match-rgb), 0.38)", css)
        self.assertIn('class="pos-pill-lemma"', flashcards)
        self.assertNotIn("headword-group-label", flashcards)

    def test_long_radials_scrub_one_readable_ring(self) -> None:
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("const maxSeats = 6", main)
        self.assertIn("wrappedDistance", main)
        self.assertIn("Drag ring", main)
        self.assertIn("stage.addEventListener('pointermove'", main)
        self.assertIn("Math.abs(delta) > 4 && !scrubMoved", main)
        self.assertLess(
            main.index("Math.abs(delta) > 4 && !scrubMoved"),
            main.index("stage.setPointerCapture?.(event.pointerId)"),
        )
        self.assertIn(".artist-radial-thumb.is-off-ring", css)
        self.assertIn("touch-action: none", css)
        self.assertNotIn("headword-group-label", css)

    def test_growing_language_and_study_lists_use_stable_choice_sheets(self) -> None:
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("function showChoiceSheet", main)
        self.assertIn("id: 'languageChoiceSheet'", main)
        self.assertIn("variant: 'grid'", main)
        self.assertIn("id: 'studyChoiceSheet'", flashcards)
        self.assertIn("variant: 'list'", flashcards)
        self.assertIn("dock: true", flashcards)
        self.assertIn("id: 'lyricsSourceSheet'", main)
        self.assertIn("id: 'artistChoiceSheet'", main)
        self.assertIn("Import a playlist and use songs already in the Fluency lyrics library.", main)
        self.assertIn("onBack: openLearningSourcePicker", main)
        self.assertIn("label: 'Live playlist'", main)
        self.assertIn("label: 'Match a Spotify playlist'", main)
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertIn("lyricsCatalog || speechAvailable", ui)
        self.assertIn("lyricsStatus.textContent = lyricsCatalog ? '›' : 'Live'", ui)
        self.assertNotIn("id: 'artistRadialPicker'", main)
        self.assertIn(".choice-sheet-grid .choice-sheet-body", css)
        self.assertIn(".choice-sheet-list .choice-sheet-item", css)

    def test_study_and_knowledge_dock_with_priority_and_keyboard_stays_off_the_card(self) -> None:
        dock = (APP_ROOT / "js" / "side-dock.js").read_text(encoding="utf-8")
        conj = (APP_ROOT / "js" / "flashcards-conj.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("PRIORITY_STUDY", dock)
        self.assertIn("PRIORITY_KNOWLEDGE", dock)
        self.assertIn("id: 'studyChoiceSheet'", dock)
        self.assertIn("keyboardHoldsLeft", dock)
        self.assertIn("can-dock-card", dock)
        self.assertIn("dock = false", main)
        self.assertIn("placeById?.(id)", main)
        self.assertIn("matchingTenses", conj)
        self.assertIn("All tenses in conjugation mode", conj)
        self.assertNotIn("switchConjMood", conj)
        # Hints sit beside the card: the full guide where there is room, a
        # keyboard button that opens it where there is less, never on the card.
        self.assertIn("body:has([data-dock=\"left\"]) .desktop-keyboard-guide", css)
        self.assertIn("body:has(#appContent:not(.hidden)) .kb-guide-toggle { display: grid; }", css)
        self.assertIn(".card-desktop-shortcuts {\n            display: none !important;", css)
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="kbGuideToggle"', html)
        self.assertIn(".choice-sheet-overlay[data-dock]", css)
        self.assertIn(".conj-match-tense", css)

    def test_mobile_modals_share_a_top_edge(self) -> None:
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("Mobile overlays all follow one spatial rule", css)
        self.assertIn("align-items: flex-start !important", css)
        self.assertIn("border-radius: 0 0 24px 24px", css)
        self.assertIn(".choice-sheet-overlay {\n    align-items: flex-start", css)
        self.assertIn("transform: translateY(-28px)", css)

    def test_multi_pos_controls_use_bounded_grid_without_reordering_senses(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("pos-count-${Math.min(pairs.length, 4)}", flashcards)
        self.assertIn("pos-count-${Math.min(posItems.length, 4)}", flashcards)
        self.assertIn("pos === activeBackPos ? 'is-active' : 'is-inactive'", flashcards)
        self.assertIn("function orderMeaningEntriesForDisplay(meanings)", flashcards)
        self.assertNotIn("[entries[activeIndex]", flashcards)
        self.assertIn("const orderedMembers = members;", flashcards)
        self.assertIn("activeSense.scrollIntoView", flashcards)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", css)
        self.assertIn(".card-pos-list.pos-count-3 > :last-child", css)
        self.assertNotIn("pos-peek-stack", css)

    def test_optional_conjugations_join_by_dictionary_headword_not_identity_lemma(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.assertIn("currentMeaning?.headword", flashcards)
        self.assertIn("conjugationLookupSurface(card)", flashcards)
        self.assertIn("currentMeaning.cycle_pos", flashcards)

    def test_approved_numbered_scrubber_animation_is_retained(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("Numbered active-set scrubber", flashcards)
        self.assertIn("deck-scrubber-lens", css)
        self.assertIn(".deck-progress-segment.is-current", css)

    def test_light_theme_does_not_turn_primary_study_action_white(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        light_css = (APP_ROOT / "css" / "light-theme.css").read_text(encoding="utf-8")
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")

        pale_unstarted_selector = (
            ':root[data-theme="light"] '
            '.range-btn-new:not(.study-set-start):not(.has-progress):not(:hover)'
        )
        self.assertIn(pale_unstarted_selector, light_css)
        self.assertNotIn(
            '.range-btn-new:not(.has-progress):not(:hover)',
            light_css,
        )
        self.assertIn('css/light-theme.css?v=20260921freq', html)
        self.assertIn('/css/light-theme.css?v=20260921freq', worker)

    def test_active_release_aliases_are_never_cached(self) -> None:
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("vocabulary\\.(?:index|examples)", worker)
        self.assertIn("study-structure", worker)
        self.assertIn("release-(?:manifest|composition)", worker)
        self.assertIn("conjugations", worker)
        self.assertIn("appPathname === '/config/artists.json'", worker)
        self.assertIn("appPathname.startsWith('/Artists/')", worker)
        self.assertIn("cache: 'no-store'", worker)
        self.assertIn("matchInstalledLyricsCatalog", worker)
        self.assertIn("exact immutable catalog", worker)

    def test_artist_catalog_is_validated_and_loads_release_provenance(self) -> None:
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        contracts = (APP_ROOT / "js" / "data-contracts.js").read_text(encoding="utf-8")
        config = (APP_ROOT / "js" / "config.js").read_text(encoding="utf-8")
        self.assertIn("validateArtistCatalog", main)
        self.assertIn("config/artists.json?contract=lyrics-v1", main)
        self.assertIn("export function validateArtistCatalog", contracts)
        self.assertIn("await loadReleaseProvenance(selectedLanguage)", main)
        self.assertIn("const releaseConfig = activeArtist || languageConfig", config)
        self.assertIn("layers[`artist:${activeArtist.slug}`]", config)
        catalog_path = APP_ROOT / "config" / "artists.json"
        self.assertTrue(catalog_path.is_file())
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertIn("bad-bunny", catalog)
        self.assertEqual(catalog["bad-bunny"]["language"], "spanish")
        self.assertIn("lyrics-all-artists-v7-native-20260825b", main)

    def test_lyrics_preview_and_resume_are_bound_to_an_exact_release(self) -> None:
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        self.assertIn("lyricsRelease", main)
        self.assertIn("bindArtistCatalogToRelease", main)
        self.assertIn("requestedReleaseId || artist.releaseId", main)
        self.assertIn("'spotifyPath'", main)
        self.assertIn("activeArtist?.spotifyPath", vocab)
        self.assertIn("releaseId: activeArtist ? currentLyricsReleaseId()", vocab)
        self.assertIn("studySessionMatchesCurrentRelease", vocab)
        self.assertIn("url.searchParams.set('lyricsRelease', snapshot.releaseId)", vocab)
        self.assertIn("if (cachedExamples)", vocab)

    def test_spotify_login_uses_deployable_public_configuration(self) -> None:
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        auth = (APP_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
        spotify = (APP_ROOT / "js" / "spotify.js").read_text(encoding="utf-8")
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")

        client_id = config["publicServices"]["spotifyClientId"]
        self.assertRegex(client_id, r"^[A-Za-z0-9]{16,128}$")
        self.assertIn("config?.publicServices?.spotifyClientId", auth)
        self.assertIn("secrets.spotifyClientId || window._spotifyClientId", auth)
        # One registered callback per origin, whatever path the app was opened at.
        pinned = config["publicServices"]["spotifyRedirectUris"]
        self.assertEqual(
            pinned["https://rabbijoshy.github.io"],
            "https://rabbijoshy.github.io/Fluency-App/callback.html",
        )
        self.assertIn("config?.publicServices?.spotifyRedirectUris", auth)
        self.assertIn("window._spotifyRedirectUris?.[window.location.origin]", spotify)
        self.assertEqual(spotify.count("const redirectUri = spotifyRedirectUri();"), 2)
        self.assertIn("Spotify sign-in is temporarily unavailable", spotify)
        self.assertIn("window.open('about:blank', 'spotify-auth'", spotify)
        self.assertIn("spotifyLogin(trackId, positionMs, options.authPopup)", spotify)
        self.assertIn("Popup blocked; redirecting to Spotify auth", spotify)
        self.assertIn("function _loadSpotifyPlaybackSdk()", spotify)
        self.assertNotIn("function _loadSpotifyPlaybackSdk() {\n    if (_isMobile) return", spotify)
        self.assertNotIn("if (_isMobile || !isSpotifyConnected()", spotify)
        self.assertIn("_player.activateElement()", spotify)
        self.assertIn("_activateMobileSdkElementFromGesture();", spotify)
        self.assertLess(
            spotify.index("_activateMobileSdkElementFromGesture();"),
            spotify.index("const authPopup = !_isMobile"),
        )
        self.assertIn("await _mobileSdkIsReadyForPlayback()", spotify)
        self.assertIn("return await _playViaConnect(trackId, positionMs, token)", spotify)
        self.assertIn("_playbackBackend === 'sdk'", spotify)
        self.assertIn("_playbackBackend === 'connect'", spotify)
        self.assertLess(
            spotify.index("window.onSpotifyWebPlaybackSDKReady ="),
            spotify.index("_loadSpotifyPlaybackSdk();"),
        )
        self.assertNotIn("sdk.scdn.co/spotify-player.js", html)
        self.assertIn("/js/spotify.js?v=20260923sp", worker)
        self.assertIn("/js/main.js?v=20260921freqb", worker)
        self.assertIn("/js/ui.js?v=20260921mwe", worker)
        self.assertIn(f"const CACHE_NAME = '{EXPECTED_CACHE_NAME}'", worker)

    def test_progress_sync_uses_deployable_public_configuration(self) -> None:
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        auth = (APP_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")

        sync_url = config["publicServices"]["progressSyncUrl"]
        # The guarantee is that the shipped config points at a real, public,
        # deployable endpoint over TLS — not a localhost rig, a placeholder, or
        # anything requiring a secret the static build cannot carry. It pinned
        # the Apps Script URL shape until progress moved to the Cloudflare
        # Worker; both remain acceptable so a rollback does not fail the suite.
        self.assertRegex(
            sync_url,
            r"^https://(?:script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec"
            r"|[A-Za-z0-9-]+\.[A-Za-z0-9-]+\.workers\.dev)$",
        )
        self.assertIn("config?.publicServices?.progressSyncUrl", auth)
        self.assertIn("secrets.googleScriptUrl || GOOGLE_SCRIPT_URL", auth)
        self.assertIn('js/auth.js?v=20260921rt', html)
        self.assertIn("auth.js?v=20260921rt", main)
        self.assertIn("/js/auth.js?v=20260921rt", worker)

    def test_progress_identity_bridges_historical_mode_ids_by_surface(self) -> None:
        progress = (APP_ROOT / "js" / "progress.js").read_text(encoding="utf-8")
        identity = (APP_ROOT / "js" / "progress-identity.js").read_text(encoding="utf-8")
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")

        self.assertIn("matchingProgressRecords", progress)
        self.assertIn("getMergedWordProgress", progress)
        self.assertIn("row.language !== language", identity)
        self.assertIn("normalizeProgressSurface(row.word)", identity)
        self.assertIn("registerProgressCardSurface", vocab)
        self.assertIn("/js/progress-identity.js?v=20260831a", worker)

    def test_static_assets_follow_the_deployment_scope(self) -> None:
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")

        release_host = (APP_ROOT / "js" / "release-host.js").read_text(encoding="utf-8")
        # Releases are served by their own Pages site, not the app's path.
        self.assertIn("releaseUrl(`releases/lyrics/", main)
        self.assertIn("export const RELEASE_BASE_URL = 'https://rabbijoshy.github.io/Fluency-Releases/'", release_host)
        self.assertIn("const SCOPE_PATH = new URL(self.registration.scope)", worker)
        self.assertIn("new Request(scopedPath(url)", worker)
        self.assertIn("new URL(file.path, self.registration.scope)", worker)
        self.assertIn("pathname.slice(SCOPE_PATH.length)", worker)

    def test_spotify_music_visualizer_requires_confirmed_playback(self) -> None:
        spotify = (APP_ROOT / "js" / "spotify.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")

        self.assertIn("_player.addListener('player_state_changed'", spotify)
        self.assertIn("_setPlaying(playing)", spotify)
        self.assertIn("await _confirmConnectPlayback", spotify)
        self.assertIn("state?.is_playing && activeTrackId === trackId", spotify)
        self.assertIn("spotify-music-visualizer", spotify)
        self.assertIn("spotify-playing-amplitude", css)
        self.assertNotIn("spotify-playing-ripple", css)
        self.assertIn("/js/spotify.js?v=20260923sp", worker)
        self.assertIn(f"const CACHE_NAME = '{EXPECTED_CACHE_NAME}'", worker)

    def test_audit_accounts_and_flags_use_release_provenance(self) -> None:
        auth = (APP_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
        modals = (APP_ROOT / "js" / "flashcards-modals.js").read_text(encoding="utf-8")
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        self.assertIn("new Set(['JST', 'JSTA'])", auth)
        self.assertIn("provenanceJson: JSON.stringify(provenance)", auth)
        self.assertIn("flagId = createFlagId()", auth)
        self.assertIn("`flag|${flagId}`", auth)
        self.assertIn("schemaVersion: 4", auth)
        self.assertIn("function _flagRunProvenance", modals)
        self.assertIn("Attached automatically", modals)
        self.assertIn("Release ID:", modals)
        self.assertEqual(
            config["languages"]["french"]["releaseManifestPath"],
            "releases/fr/speech/fr-speech-v7-dual-metadata-v5-20260918/manifest.json",
        )

    def test_spotify_playlist_import_looks_up_lyrics_with_visible_percent(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        importer = (APP_ROOT / "js" / "spotify-playlist-import.js").read_text(encoding="utf-8")
        spotify = (APP_ROOT / "js" / "spotify.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")

        self.assertIn('id="spotifyPlaylistProgress"', html)
        self.assertIn('id="spotifyPlaylistPercent"', html)
        self.assertIn('id="spotifyPlaylistSpinner"', html)
        self.assertIn('id="spotifyPlaylistLog"', html)
        self.assertIn("playlist-lyrics-spinner", css)
        self.assertIn("fluency-playlist-lyrics", importer)
        self.assertIn("savePlaylistLiveTracks", importer)
        self.assertIn("/api/playlist-live", importer)
        self.assertIn("window.postPlaylistLive", importer)
        self.assertIn("const LOOKUP_CONCURRENCY = 6", importer)
        self.assertIn("https://lrclib.net/api/search", importer)
        self.assertIn("indexedDB.open(LYRICS_DB_NAME", importer)
        self.assertIn("Looking up:", importer)
        self.assertIn("${percent}%", importer)
        self.assertIn("function fetchSpotifyPlaylistTracks", spotify)
        self.assertIn(".playlist-lyrics-percent", css)
        self.assertIn(".playlist-lyrics-bar-fill", css)
        self.assertIn("event.stopPropagation()", importer)
        self.assertIn("replaceRoute(", importer)
        self.assertIn("_importBusy", importer)
        self.assertIn("setDismissLock", importer)
        self.assertIn("allowReauth: false", spotify)
        self.assertIn("/playlists/${id}/items?limit=100", spotify)
        self.assertIn("row?.item || row?.track", spotify)
        self.assertIn("canReadItems", spotify)
        self.assertIn("tracksHref", spotify)
        self.assertIn('id="reconnectSpotifyPlaylistBtn"', html)
        self.assertIn("showDialog", spotify)
        self.assertIn("/js/spotify-playlist-import.js?v=20260923cj", worker)
        self.assertIn('css/style.css?v=20260921freq', html)
        self.assertIn('id="useSpotifyLiveBtn"', html)
        self.assertIn("buildPlaylistLiveDeck", importer)
        self.assertIn("replaceRoute({\n        kind: 'live'", importer)

    def test_live_playlist_joins_naive_tokens_to_speech_vocab(self) -> None:
        live = (APP_ROOT / "js" / "playlist-live.js").read_text(encoding="utf-8")
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("function naiveLyricTokens", live)
        self.assertIn("function applyPlaylistLiveVocabulary", live)
        self.assertIn("unassigned: true", live)
        self.assertIn("share >= 0.05", live)
        self.assertIn("window.savePlaylistLiveDeckToServer", live)
        self.assertIn("action: 'loadPlaylistLiveDeck'", live)
        self.assertIn("window.applyPlaylistLiveVocabulary?.(_baseVocab)", vocab)
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertIn("fluencyPendingSpeechLanguage", main)
        self.assertIn("window.resetActiveArtist", main)
        self.assertIn("ensureArtistCatalog", main)
        self.assertIn("window.clearPlaylistLiveSession?.()", main)
        self.assertIn("window.continueToSpeechAfterLive", ui)
        self.assertIn("if (window.playlistLiveActive?.()) {", vocab)
        self.assertIn("playlist-live", vocab)

    def test_song_sets_retain_contributing_artist_slugs(self) -> None:
        song_sets = (APP_ROOT / "js" / "song-sets.js").read_text(encoding="utf-8")
        auth = (APP_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
        self.assertIn("function artistSlugsForSongs", song_sets)
        self.assertIn("artistSlugs,", song_sets)
        self.assertIn("remote.artistSlugs", song_sets)
        self.assertIn("window.reconcileRemoteSongSet = reconcileRemoteSongSet", song_sets)
        self.assertIn("setTimeout(() => controller.abort(), 12000)", song_sets)
        self.assertIn("window.reconcileRemoteSongSet?.()", auth)

    def test_language_switch_clears_source_scoped_runtime_data(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        song_sets = (APP_ROOT / "js" / "song-sets.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        self.assertIn("window.clearActiveExamplesData?.()", ui)
        self.assertIn("window.resetLanguageOptionalData?.()", ui)
        self.assertIn("export function clearActiveExamplesData", song_sets)
        self.assertIn("window._cachedExamplesDataPath = resolvedSource", song_sets)
        self.assertIn("function resetLanguageOptionalData", flashcards)
        self.assertIn("ensureExampleShardsForRange", vocab)
        self.assertIn("prefetchStudySetPayload", vocab)
        self.assertIn("vocabulary.examples.manifest.json", vocab)
        self.assertIn("loadColumnarIndex", vocab)
        self.assertIn("vocabulary.index.manifest.json", vocab)

    def test_pilot_interface_remains_a_readable_reference(self) -> None:
        reference = REPOSITORY_ROOT / "docs" / "reference" / "pilot-ui-v1.html"
        self.assertTrue(reference.is_file())
        self.assertIn('id="welcome-screen"', reference.read_text(encoding="utf-8"))

    def test_all_relative_module_imports_resolve(self) -> None:
        import_pattern = re.compile(r'^import\s+.*?(?:from\s+)?["\'](.+?)["\'];?$', re.MULTILINE)
        for module in (APP_ROOT / "js").glob("*.js"):
            for target in import_pattern.findall(module.read_text(encoding="utf-8")):
                if not target.startswith("."):
                    continue
                clean_target = target.split("?", 1)[0]
                resolved = (module.parent / clean_target).resolve()
                with self.subTest(module=module.name, target=target):
                    self.assertTrue(resolved.is_file())

    def test_every_example_names_its_corpus(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        titles = APP_ROOT / "data" / "source_titles.json"

        self.assertEqual(config["sourceTitlesPath"], "data/source_titles.json")
        self.assertTrue(titles.is_file())
        self.assertIn("corpus === 'tatoeba'", flashcards)
        self.assertIn("domain: 'tatoeba.org'", flashcards)
        self.assertIn("domain: 'imdb.com'", flashcards)
        self.assertIn("function exampleSourceChipHTML", flashcards)
        self.assertIn("Episode titles and years live on the IMDb page", flashcards)
        self.assertIn("loadSourceTitles", flashcards)
        self.assertNotIn("source_mode === 'speech'", flashcards)


if __name__ == "__main__":
    unittest.main()


class KnownLanguageCognateSurfaceTests(unittest.TestCase):
    """The learner declares which languages they already read, and cognate
    exclusion scores against all of them rather than only English."""

    def test_the_setup_panel_carries_the_known_language_picker(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        for required_id in (
            "setupOptions",          # the Fast Track row under the level picker
            "fastTrackHubBtn",
            "fastModeModal",         # the full page behind it
            "knownLanguagesContainer",
            "knownLanguagesSelector",
            "extrasModal",           # what the exclusions did, kept browsable
            "extrasBtn",
        ):
            self.assertIn(f'id="{required_id}"', html)
        self.assertIn("Boolean(window.isAuditAccount?.())", (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8"))

    def test_the_runtime_modules_ship_and_are_precached(self) -> None:
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        for filename in ("cognates.js", "extras.js", "fast-mode.js"):
            self.assertTrue((APP_ROOT / "js" / filename).is_file(), filename)
            # A module missing from the precache list is invisible offline,
            # which is the failure this pins.
            self.assertIn(f"/js/{filename}?v=", worker, filename)
            self.assertIn(f"./{filename}?v=", main, filename)

    def test_each_known_language_excludes_on_its_own_cutoff(self) -> None:
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        # The filter must not read the legacy scalar directly: that could only
        # ever mean "close to English".
        self.assertIn("isCognateAlreadyKnown(item)", vocab)
        cognates = (APP_ROOT / "js" / "cognates.js").read_text(encoding="utf-8")
        self.assertIn("cognate_scores", cognates)
        # Falling back to the scalar keeps releases that predate per-language
        # scores behaving exactly as before.
        self.assertIn("item.cognate_score", cognates)

    def test_the_prepared_vocabulary_cache_notices_a_selection_change(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertIn("activeKnownLanguages?.() || []", ui)


class FastModeSurfaceTests(unittest.TestCase):
    """Fast mode is one row under the level picker, with everything it bundles
    on a page of its own."""

    def setUp(self) -> None:
        self.html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        self.script = (APP_ROOT / "js" / "fast-mode.js").read_text(encoding="utf-8")

    def test_the_individual_controls_live_on_the_page_not_the_setup_screen(self) -> None:
        # The toggles a learner cannot judge before seeing a card belong behind
        # the explanation, not beside the level picker.
        page_start = self.html.index('id="fastModeModal"')
        for control in ("lemmaToggleContainer", "cognateToggleContainer"):
            self.assertGreater(
                self.html.index(f'id="{control}"'), page_start,
                f"{control} must sit inside the Fast mode page",
            )
        self.assertNotIn('id="coverageModeContainer"', self.html)

    def test_turning_fast_mode_on_drives_the_real_controls(self) -> None:
        # Setting the state directly would be a second implementation of what
        # each toggle means, free to drift from ui.js's.
        self.assertIn(".lemma-toggle-btn[data-lemma=", self.script)
        self.assertIn(".cognate-toggle-btn[data-cognate=", self.script)
        self.assertIn("?.click();", self.script)

    def test_fast_track_reports_binary_on_or_off_without_custom_state(self) -> None:
        self.assertIn("return readFastTrack(selectedLanguage).enabled ? 'on' : 'off';", self.script)
        self.assertNotIn("return 'custom'", self.script)

    def test_fast_track_state_only_uses_parts_the_release_supports(self) -> None:
        # Keep the language choice while only changing controls supported here.
        self.assertIn("if (lemmaAvailable() && lemmaOn()", self.script)
        self.assertIn("if (cognateAvailable() && cognatesExcluded()", self.script)

    def test_master_switch_is_independent_and_details_explain_missing_mappings(self) -> None:
        self.assertIn("saveFastTrack(selectedLanguage, { enabled: on, merge, skip })", self.script)
        self.assertNotIn("if (!lemmaAvailable() && !cognateAvailable())", self.script)
        self.assertIn("updateMappingStatus()", self.script)
        self.assertIn('class="fast-mode-number" aria-hidden="true">1</span>', self.html)
        self.assertIn('class="fast-mode-number" aria-hidden="true">2</span>', self.html)
        self.assertIn('id="lemmaMappingStatus"', self.html)
        self.assertIn('id="cognateMappingStatus"', self.html)
        self.assertIn("chocolate</b><small>Spanish", self.html)


class ReleaseLevelSetsTests(unittest.TestCase):
    """Routing release levels through the scrubber dropped the marker the range
    selector branches on, and every Speech language rendered no sets at all."""

    def test_release_levels_keep_their_marker_on_the_hidden_buttons(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertIn(
            """${usingReleaseLevels ? ' data-release-level="true"' : ''}""", ui
        )

    def test_both_readers_of_that_marker_still_exist(self) -> None:
        # Without the attribute these fall through to a CEFR lookup that cannot
        # match a release level id, and the set list comes back empty.
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertEqual(ui.count("dataset.releaseLevel === 'true'"), 2)


class LevelCoverageTests(unittest.TestCase):
    """Speech levels are a pure ordering; the corpus shares give them a figure
    a learner can act on."""

    def setUp(self) -> None:
        self.script = (APP_ROOT / "js" / "coverage.js").read_text(encoding="utf-8")

    def test_both_readings_come_from_the_same_shares(self) -> None:
        # share: fraction of the corpus. gain: fraction of what is left.
        self.assertIn("if (readMode() === 'share') return band;", self.script)
        self.assertIn("return remaining > 0 ? band / remaining : null;", self.script)

    def test_a_level_with_nothing_to_say_reports_nothing(self) -> None:
        # A zero would read as "this level is worthless" rather than "unknown".
        self.assertIn("if (band <= 0) return null;", self.script)

    def test_the_switch_hides_when_a_language_ships_no_shares(self) -> None:
        self.assertIn("container.style.display = coverageAvailable() ? 'block' : 'none';", self.script)

    def test_the_display_switch_is_not_mixed_into_fast_mode(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('id="coverageModeContainer"', html)


class CognateAvailabilityTests(unittest.TestCase):
    """cognateFilter is declared per language, but the data is per language and
    mode — Spanish's flags are in the artist master, French's in one playlist
    of a language with lyrics disabled. Both showed a dead toggle."""

    def test_the_declaration_cannot_turn_a_filter_on_by_itself(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertIn("cognateFieldAvailable = false;", ui)
        self.assertIn("if (declaredCapability !== false && langConfig) {", ui)

    def test_the_deck_is_what_decides(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertIn("item.cognate_scores", ui)
        self.assertIn("item.is_transparent_cognate", ui)


class CognateMapScopeTests(unittest.TestCase):
    """Cognate scores are keyed by bare surface, so a map must not outlive the
    language it was built for — a stale Czech map scored six Spanish words,
    because a, to and je exist in both."""

    def test_switching_to_a_language_without_a_map_clears_the_old_one(self) -> None:
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        # The loader must run when the path changes to null, not be skipped.
        self.assertIn("if (_cognateScoresLoadedFor !== path && globalThis.loadCognateScores) {", vocab)
        self.assertIn("if (_coverageLoadedFor !== coveragePath) {", vocab)

    def test_a_map_refuses_a_language_it_was_not_built_for(self) -> None:
        cognates = (APP_ROOT / "js" / "cognates.js").read_text(encoding="utf-8")
        self.assertIn("if (languageCode && cognateLanguage && languageCode !== cognateLanguage) return;", cognates)


class CognateSourceUnionTests(unittest.TestCase):
    """A language can hold a hand-built score and a generated map at once —
    Spanish does. Preferring the map would narrow Lyrics to whichever of its
    words happened to appear in the Speech deck's map."""

    def test_a_legacy_flag_still_excludes_when_a_map_exists(self) -> None:
        source = (APP_ROOT / "js" / "cognates.js").read_text(encoding="utf-8")
        legacy_line = source.index("const legacy = Number(item.cognate_score || 0);")
        per_language_line = source.index("const perLanguage = item.cognate_scores;", legacy_line)
        self.assertLess(legacy_line, per_language_line,
                        "the legacy score must be consulted before returning on the map")


class StudySetProgressConsistencyTests(unittest.TestCase):
    """Displayed set counts and the committed deck must use the same current
    progress snapshot, including after a background refresh or the final
    answer in the preceding set."""

    def test_set_state_memo_is_invalidated_by_progress_epoch_and_each_render(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertIn("let _setupStateMemoEpoch = -1;", ui)
        self.assertIn("_setupStateMemoEpoch !== epoch", ui)
        range_start = ui.index("async function renderRangeSelector(")
        reset = ui.index("resetSetupStateMemo();", range_start)
        first_fetch = ui.index("fetchActiveVocabularyData(langConfig)", range_start)
        self.assertLess(reset, first_fetch)

    def test_learn_new_never_bounces_to_another_set(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        auth = (APP_ROOT / "js" / "auth.js").read_text(encoding="utf-8")
        # Only the progress-derived answer is memoised; lemma inheritance and
        # the estimate depend on per-call options and Fast Track.
        recorded = ui[ui.index("function getRecordedSetupState(item)"):]
        recorded = recorded[:recorded.index("\n}\n")]
        self.assertNotIn("seenLemmas", recorded)
        self.assertNotIn("<= estimate", recorded)
        # The landing set's rows load before it is offered, so cards the
        # builder would drop (no translated meaning) are not advertised.
        self.assertIn("landingWords.some(item => item._indexRowsPending)", ui)
        self.assertIn("return renderRangeSelector({ landingRowsChecked: landingRowsChecked + 1 });", ui)
        # Start waits for an in-flight progress refresh, and an empty set goes
        # straight on to the recount's next set instead of back to setup.
        self.assertIn("window.progressRefreshSettled = progressRefreshSettled;", auth)
        self.assertIn("await window.progressRefreshSettled?.(5000);", ui)
        self.assertIn("is already done. Starting Set", ui)
        self.assertIn("silentIfEmpty: true", ui)

    def test_empty_replacement_preserves_the_active_deck_without_an_unseen_popup(self) -> None:
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        self.assertIn("const previousDeckState = {", vocab)
        self.assertIn("restorePreviousDeckState();", vocab)
        self.assertIn("if (!opts.silentIfEmpty) await window.refreshSetupAfterProgress?.();", vocab)
        self.assertNotIn("No unseen flashcards remain in this set", vocab)

    def test_completion_recounts_same_level_and_only_autostarts_unseen_cards(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        continuation = ui[ui.index("async function startNextStudyLevelFirstSet()"):
                          ui.index("function showStatsModal()")]
        self.assertIn("await renderRangeSelector();", continuation)
        self.assertIn("const sameLevelCandidates", continuation)
        self.assertIn("Number(dot.dataset.unseen || 0) > 0", continuation)
        self.assertNotIn("Number(dot.dataset.review || 0) > 0", continuation)

    def test_portuguese_variety_selection_is_supported_without_cluttering_ui(self) -> None:
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        config = json.loads((APP_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")

        self.assertEqual(config["languages"]["portuguese"]["name"], "Portuguese")
        self.assertEqual(config["languages"]["portuguese"]["flag"], "🇵🇹")
        self.assertIn("function showPortugueseVarietyPicker()", main)
        self.assertIn("showPortugueseVarietyPicker()", main)
        self.assertIn("European Portuguese", main)
        self.assertIn("Brazilian Portuguese", main)
        self.assertIn(".choice-sheet-back", css)

    def test_artist_mode_source_card_is_slim_and_has_parity_with_speech_mode(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")

        # Header and redundant language picker button are hidden for parity
        self.assertIn("#artistSourceStep > .artist-source-header,", css)
        self.assertIn("#artistSourceCard > .artist-source-language-btn", css)
        self.assertIn("display: none !important;", css)

        # Main choice layout is a horizontal flex row with pill action buttons
        self.assertIn(".artist-source-main-choice {", css)
        self.assertIn(".artist-source-secondary-actions {", css)
        self.assertIn("display: flex;", css)
        self.assertIn("border-radius: 999px;", css)

        # Button label is concise and non-clunky
        self.assertIn("speechBtn.textContent = 'Speech ›';", main)
        self.assertIn('id="artistSourceSpeechBtn" class="artist-source-action-btn">Speech ›</button>', html)
        self.assertNotIn(">Switch to Speech<", html)

    def test_lyrics_mode_level_and_sets_generation_is_not_blocked_by_release_levels(self) -> None:
        ui = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        cfg = (APP_ROOT / "js" / "config.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")

        # In main.js, activeArtist must NOT be declared as a module-local let, so it updates globalThis.activeArtist from state.js
        self.assertNotIn("let activeArtist", main)

        # In flashcards.js, sense-prominence-badge must be a span, not a button, to avoid breaking parent button elements
        self.assertIn("<span class=\"sense-prominence-badge", flashcards)

        # In ui.js, if (usingReleaseLevels) must be closed so smart level ranges execute for lyrics mode
        slider_block = ui[ui.index("const usingReleaseLevels = releaseLevels.length > 0;"):
                          ui.index("const percentageRanges = getActiveLevelRanges();")]
        self.assertIn("if (usingReleaseLevels) {\n        _smartLevelRangesCache = releaseLevels.map", slider_block)
        self.assertIn("        }));\n    }", slider_block)
        self.assertIn("if (_raw && !usingReleaseLevels) {", slider_block)

        # In ui.js, renderRangeSelector must guard releaseStudyStructure?.levels with !activeArtist
        self.assertIn("} else if (!activeArtist && !window.playlistLiveActive?.() && releaseStudyStructure?.levels) {", ui)

        # In vocab.js, fetchAndJoinIndex must join with master vocab when activeArtist has masterPath
        self.assertIn("effectiveConfig = (activeArtist && (activeArtist.language || 'spanish') === (langConfig?.language || selectedLanguage))", vocab)
        self.assertIn("data = joinWithMaster(data, window._cachedMasterVocab);", vocab)

        # In config.js, loadPpmData must use activeArtist config when activeArtist is set
        self.assertIn("activeArtist && (activeArtist.language || 'spanish') === language", cfg)

        # In main.js, switching from Lyrics to Speech must store pending language and reload to avoid hybrid state
        speech_btn_block = main[main.index("speechBtn.onclick ="):
                                main.index("window.renderSetupExtrasSection?.();")]
        self.assertIn("sessionStorage.setItem('fluencyPendingSpeechLanguage', targetLang);", speech_btn_block)
        self.assertIn("window.location.href = window.location.pathname;", speech_btn_block)

    def test_language_aware_streamline_examples_adapt_to_active_language(self) -> None:
        fast_mode = (APP_ROOT / "js" / "fast-mode.js").read_text(encoding="utf-8")
        self.assertIn("const STREAMLINE_LANGUAGE_EXAMPLES = {", fast_mode)
        self.assertIn("french:", fast_mode)
        self.assertIn("portuguese:", fast_mode)
        self.assertIn("italian:", fast_mode)
        self.assertIn("german:", fast_mode)
        self.assertIn("czech:", fast_mode)
        self.assertIn("updateStreamlineLanguageExamples()", fast_mode)
        self.assertIn("globalThis.updateStreamlineLanguageExamples = updateStreamlineLanguageExamples;", fast_mode)

    def test_desktop_keyboard_shortcut_cues_are_present(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")

        self.assertIn("desktop-front-shortcuts", html)
        self.assertIn("desktop-back-shortcuts", html)
        self.assertIn("<kbd class=\"desktop-kbd\">Space</kbd> Flip", html)
        self.assertIn(".card-desktop-shortcuts {", css)
        self.assertIn(".desktop-kbd {", css)
        self.assertIn(".cbs-thumb {", css)
        self.assertIn(".cbs-scrub {", css)

    def test_sense_prominence_mode_supports_labels_and_percentages(self) -> None:
        state = (APP_ROOT / "js" / "state.js").read_text(encoding="utf-8")
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")

        self.assertIn("senseProminenceMode: 'labels',", state)
        self.assertGreater(html.index('id="senseProminenceSelector"'), html.index('id="appDataTabContent"'))
        self.assertIn('data-prominence="labels"', html)
        self.assertIn('data-prominence="percentages"', html)
        self.assertIn("function getSenseProminenceInfo(meaning)", flashcards)
        self.assertIn(".sense-prominence-badge {", css)
        self.assertIn(".sense-prominence-badge.prominence-common", css)
        self.assertIn(".sense-prominence-badge.prominence-rare", css)

    def test_rare_dictionary_senses_expansion_and_canonical_examples(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")

        self.assertIn("function extractCanonicalDictionaryExamples(meaning)", flashcards)
        self.assertIn("function canonicalExampleHTML(meaning)", flashcards)
        self.assertIn("function getQualifyingRareSenses(card)", flashcards)
        self.assertIn("function openRareAndExpressionsCard(event)", flashcards)
        self.assertIn('class="ref-tile ref-rare-uses-btn"', flashcards)
        self.assertIn(">Rarer uses</span>", flashcards)
        self.assertIn("function clusterRareSenses(items)", flashcards)
        # The tile opens a sheet (docked beside the card on desktop); rare
        # senses never chain after a correct answer.
        self.assertIn("function ensureRareUsesModal()", flashcards)
        self.assertIn("window.sideDock?.placeById?.('rareUsesModal')", flashcards)
        self.assertNotIn("rareSensesModeEnabled", flashcards)
        self.assertIn("id: 'rareUsesModal'", (APP_ROOT / "js" / "side-dock.js").read_text(encoding="utf-8"))
        # Every row is a phrase, so no PHRASE badge on each one.
        self.assertNotIn('<span class="phrase-kind-badge">PHRASE</span>', flashcards)
        self.assertNotIn("function toggleRareSenses(event)", flashcards)
        self.assertNotIn("rare-senses-toggle-btn", flashcards)

    def test_rare_senses_dictionary_provenance_and_accordion(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        light = (APP_ROOT / "css" / "light-theme.css").read_text(encoding="utf-8")

        self.assertIn("dictionary-provenance-badge", flashcards)
        self.assertIn("dict-provenance-icon", flashcards)
        self.assertIn("meaning-row-rare", flashcards)
        self.assertIn("ref-rare-uses-btn", flashcards)
        self.assertIn("example-source-chip", flashcards)
        self.assertIn("function armOutboundLink(event)", flashcards)
        # The host holds the Visit button, so it cannot itself be a <button>:
        # the parser would hoist the inner one out and the tap did nothing.
        self.assertIn('return `<span role="button" tabindex="0" ${attrs} data-href=', flashcards)
        self.assertIn("function outboundChipKeydown(event)", flashcards)
        self.assertIn("function confirmOutboundLink(event)", flashcards)
        self.assertIn("outbound-leave-btn", flashcards)
        self.assertIn(".dictionary-provenance-badge", css)
        self.assertIn(".example-source-chip", css)
        self.assertIn(".outbound-leave-btn", css)
        self.assertIn(".meaning-row.meaning-row-rare", css)
        self.assertIn(".dictionary-provenance-badge", light)

    def test_deck_complete_circular_score_ring_and_stat_cards(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        modals = (APP_ROOT / "js" / "flashcards-modals.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        light = (APP_ROOT / "css" / "light-theme.css").read_text(encoding="utf-8")

        self.assertIn('id="deckCompleteScoreContainer"', html)
        self.assertIn('id="deckScoreRingFill"', html)
        self.assertIn('id="completeAccuracyNumber"', html)
        self.assertIn('class="deck-stat-badge"', html)

        self.assertIn("deckCompleteScoreContainer", modals)
        self.assertIn("deckScoreRingFill", modals)
        self.assertIn("ringFill.style.strokeDashoffset", modals)

        self.assertIn(".deck-score-ring", css)
        self.assertIn(".deck-score-ring-fill", css)
        self.assertIn(".deck-score-number", css)
        self.assertIn(".deck-score-ring-bg", light)

    def test_audio_playback_word_highlight_sync_states(self) -> None:
        spotify = (APP_ROOT / "js" / "spotify.js").read_text(encoding="utf-8")
        speech = (APP_ROOT / "js" / "speech.js").read_text(encoding="utf-8")
        state = (APP_ROOT / "js" / "state.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")

        self.assertIn("is-spotify-playing", spotify)
        self.assertIn("is-speaking-active", speech)
        self.assertIn("speechRate: 0.9", state)
        self.assertIn("window.getSpeechRate = getSpeechRate;", speech)
        self.assertIn("window.setSpeechRate = setSpeechRate;", speech)
        self.assertIn("body.is-spotify-playing .sentence .example-word-highlight", css)
        self.assertIn("body.is-speaking-active .sentence .example-word-highlight", css)

    def test_global_state_binding_and_ui_safety(self) -> None:
        state_js = (APP_ROOT / "js" / "state.js").read_text(encoding="utf-8")
        ui_js = (APP_ROOT / "js" / "ui.js").read_text(encoding="utf-8")
        flashcards_js = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")

        self.assertIn("globalThis.state = state;", state_js)
        self.assertNotIn("state.senseProminenceMode || 'labels'", ui_js)
        self.assertNotIn("const useProminenceLabels = state.senseProminenceMode", flashcards_js)

    def test_sense_display_and_rare_sense_attribution(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.assertIn("isRareSense: true", flashcards)
        self.assertIn("prominenceLabel: 'Rare'", flashcards)
        self.assertIn("hasOnlyRareSenses: true", flashcards)
        self.assertIn("prominence-${escapeCardText(key)}", flashcards)
        self.assertIn("escapeCardText(label)", flashcards)
        self.assertIn("groupInfo.size === 1 && Math.round(g.pct * 100) >= 100", flashcards)
        self.assertIn("window.getSenseProminenceInfo = getSenseProminenceInfo;", flashcards)

    def test_spotify_soundwave_equalizer_structure(self) -> None:
        spotify = (APP_ROOT / "js" / "spotify.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("for (let index = 0; index < 4; index++)", spotify)
        self.assertIn("spotify-music-visualizer", spotify)
        self.assertIn("spotify-playing-amplitude", css)
        self.assertNotIn("rotate(calc(var(--bar-index)", css)

    def test_perfect_set_celebration_and_confetti(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        modals = (APP_ROOT / "js" / "flashcards-modals.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn('id="deckCompleteConfetti"', html)
        self.assertIn("triggerDeckCompleteConfetti", modals)
        self.assertIn("scoreContainer.classList.add('is-perfect')", modals)
        self.assertIn("🌟 Perfect Set!", modals)
        self.assertIn(".deck-complete-confetti", css)
        self.assertIn(".deck-complete-score-container.is-perfect", css)

    def test_keyboard_shortcuts_cheat_sheet_modal(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn('id="keyboardShortcutsModal"', html)
        self.assertIn('id="closeKeyboardShortcutsModal"', html)
        self.assertIn("toggleKeyboardShortcutsModal", flashcards)
        self.assertIn("e.key === '?'", flashcards)
        self.assertIn(".keyboard-shortcuts-content", css)
        self.assertIn(".shortcut-kbd", css)
        self.assertIn("⌘F", html)
        self.assertIn("Ctrl+F", html)

    def test_find_word_filter_chips_and_prominence_badges(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        main = (APP_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        dock = (APP_ROOT / "js" / "side-dock.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn('id="findWordFilters"', html)
        self.assertIn('class="modal hidden find-word-overlay"', html)
        self.assertIn('class="find-word-spotlight"', html)
        self.assertIn('data-filter="learned"', html)
        self.assertIn('data-filter="review"', html)
        self.assertIn('data-filter="unseen"', html)
        self.assertIn("_findWordFilter", main)
        self.assertIn("fw-meaning-group", main)
        self.assertIn("const findShortcut = (e.metaKey || e.ctrlKey)", main)
        self.assertIn(".find-word-filters", css)
        self.assertIn(".find-word-filter-btn.is-active", css)
        self.assertIn("#findWordModal.find-word-overlay", css)
        self.assertNotIn("{ id: 'findWordModal'", dock)
        self.assertNotIn("label: 'Find a word'", flashcards)

    def test_back_of_card_sense_deduplication_and_2line_presentation(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")
        light = (APP_ROOT / "css" / "light-theme.css").read_text(encoding="utf-8")

        self.assertIn("function cleanSenseContext(rawContext, mainGloss)", flashcards)
        self.assertIn("window.cleanSenseContext = cleanSenseContext;", flashcards)
        self.assertIn("meaning-row-gloss", flashcards)
        self.assertIn("meaning-row-sub", flashcards)
        self.assertIn(".meaning-row-gloss", css)
        self.assertIn(".meaning-row-sub", css)
        self.assertIn(".meaning-row-sub", light)
        self.assertIn("#backContent > .meanings-scroll::-webkit-scrollbar", css)
        self.assertIn("#backContent > .meanings-scroll::-webkit-scrollbar-thumb", light)

    def test_back_of_card_declutter_prominence_and_lexicographic_extraction(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")
        css = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")

        # Checkmark removed on sense rows
        self.assertIn("function renderRowCheckSlot(isSelected) {\n    return '';\n}", flashcards)

        # Lexicographical definition prefix extraction
        self.assertIn("WIKTIONARY_PRONOUN_DEFINITION", pills)
        self.assertIn("extractedPrefixNote", pills)

        # Space efficient prominence badge font and mobile rules
        self.assertIn(".sense-prominence-badge {", css)
        self.assertIn("font-family: var(--font-reading);", css)
        self.assertIn(".sense-prominence-meter {", css)
        self.assertIn("padding-right: 28px !important;", css)

    def test_pos_summary_strict_set_and_differential_metadata_folding(self) -> None:
        flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        pills = (APP_ROOT / "js" / "card-metadata-pills.js").read_text(encoding="utf-8")

        # 4-tier metadata scoring and differentiator resolution
        self.assertIn("function scoreSenseMetadata(item)", pills)
        self.assertIn("function compactLearnerSenseMetadata(items, meaning, options = {})", pills)
        self.assertIn("function resolveMeaningDifferentiator(meaning, peerMeanings, gloss = '', cleanContextFn = null)", pills)
        self.assertIn("window.scoreSenseMetadata = scoreSenseMetadata;", pills)
        self.assertIn("window.resolveMeaningDifferentiator = resolveMeaningDifferentiator;", pills)

        # POS section summary strict Set deduplication
        self.assertIn("seenSummaryKeys = new Set()", flashcards)
        self.assertIn(r"normKey = sense.toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '').trim()", flashcards)

        # Singleton fold leader and follower precomputation
        self.assertIn("const singletonFoldFollowers = new Set();", flashcards)
        self.assertIn("const singletonFoldLeaders = new Map();", flashcards)
        self.assertIn("if (singletonFoldFollowers.has(idx)) return;", flashcards)
        self.assertIn("foldInfo.allIndices.includes(currentMeaningIndex)", flashcards)
