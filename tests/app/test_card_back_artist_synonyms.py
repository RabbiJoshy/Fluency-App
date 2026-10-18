"""Tests for card-back scrubber cleanup, synonym strength ordering, loading album art, and artist mode sense policies."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class CardBackArtistSynonymsTests(unittest.TestCase):
    def test_card_back_scrubber_endpoint_and_spacing(self):
        script = r"""
        const fs = require('node:fs'), assert = require('node:assert/strict');
        const indexHtml = fs.readFileSync('app/index.html', 'utf8');
        const styleCss = fs.readFileSync('app/css/style.css', 'utf8');
        const uiRefinements = fs.readFileSync('app/css/ui-refinements.css', 'utf8');

        // 1. Scrubber end label removed from cardBackPips
        assert.ok(!indexHtml.includes('class="cbs-end-label"'), 'cbs-end-label must not be in app/index.html');
        assert.ok(uiRefinements.includes('.cbs-end-label { display: none !important; }'), 'cbs-end-label hidden in ui-refinements');

        // 2. Symmetric track-wrap margins (16px left and right)
        assert.ok(styleCss.includes('margin: 0 16px;'), 'cbs-track-wrap must have symmetric 16px margins (half the 32px thumb)');

        // 3. Clean circular 44px gear button
        assert.ok(styleCss.includes('.cbs-gear {\n            flex: 0 0 44px;\n            width: 44px;\n            height: 44px;'),
            'cbs-gear must be 44x44 circular button');
        """
        result = subprocess.run(['node', '-'], input=script, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_study_and_practice_buttons_centered(self):
        script = r"""
        const fs = require('node:fs'), assert = require('node:assert/strict');
        const uiRefinements = fs.readFileSync('app/css/ui-refinements.css', 'utf8');
        const styleCss = fs.readFileSync('app/css/style.css', 'utf8');

        assert.ok(uiRefinements.includes('justify-self: center;'), 'Study button in #step4 must be centered');
        assert.ok(uiRefinements.includes('align-self: center;'), 'Practice button in review deck must be centered');
        """
        result = subprocess.run(['node', '-'], input=script, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_synonyms_strength_ordering_and_pill_layout(self):
        script = r"""
        const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
        const flashcards = fs.readFileSync('app/js/flashcards.js', 'utf8');
        const styleCss = fs.readFileSync('app/css/style.css', 'utf8');

        const context = {
            window: {},
            jumpToSynonym: () => {},
            selectSynonymsTab: () => {},
            toggleSynonymsPanel: () => {}
        };
        vm.createContext(context);
        const start = flashcards.indexOf('function buildSynonymsPanelHTML(');
        const end = flashcards.indexOf('function selectSynonymsTab(', start);
        vm.runInContext(flashcards.slice(start, end), context);

        const synonyms = [
            { word: 'contento', strength: 1 },
            { word: 'alegre', strength: 2 },
            { word: 'radiante', strength: 2 },
            { word: 'dichoso' },
            { word: 'jubiloso', strength: 1 }
        ];

        const html = context.buildSynonymsPanelHTML(synonyms, [], 'feliz');

        // alegre and radiante (strength 2) must precede contento and jubiloso (strength 1), which precede dichoso (0)
        const alegreIdx = html.indexOf('alegre');
        const radianteIdx = html.indexOf('radiante');
        const contentoIdx = html.indexOf('contento');
        const jubilosoIdx = html.indexOf('jubiloso');
        const dichosoIdx = html.indexOf('dichoso');

        assert.ok(alegreIdx < contentoIdx, 'Strength 2 (alegre) must precede strength 1 (contento)');
        assert.ok(radianteIdx < contentoIdx, 'Strength 2 (radiante) must precede strength 1 (contento)');
        assert.ok(alegreIdx < radianteIdx, 'Equal strength ties broken alphabetically: alegre before radiante');
        assert.ok(contentoIdx < jubilosoIdx, 'Equal strength 1 ties broken alphabetically: contento before jubiloso');
        assert.ok(jubilosoIdx < dichosoIdx, 'Strength 1 (jubiloso) must precede strength 0 (dichoso)');

        // Pill layout styling in style.css
        assert.ok(styleCss.includes('flex: 1 1 calc(50% - 10px);'), 'syn-item must have responsive flex basis');
        assert.ok(styleCss.includes('margin-left: auto;'), 'syn-go chevron must align to right');
        """
        result = subprocess.run(['node', '-'], input=script, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_artist_loading_mark_album_art_rotation(self):
        script = r"""
        const fs = require('node:fs'), assert = require('node:assert/strict');
        const mainSource = fs.readFileSync('app/js/main.js', 'utf8');

        // Check updateLoadingMark handles artist mode rotation from albumImageMap
        assert.ok(mainSource.includes('effectiveArtist.albumImageMap'), 'updateLoadingMark must read albumImageMap');
        assert.ok(mainSource.includes('loadingMarkRotationKey = `artist:${artistKey}`;'), 'updateLoadingMark must key timer by artist');
        assert.ok(mainSource.includes('currentLoadingImages = images;'), 'must cache image list for rotation');
        """
        result = subprocess.run(['node', '-'], input=script, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_artist_mode_senses_and_canonical_rules(self):
        script = r"""
        const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
        const vocabSource = fs.readFileSync('app/js/vocab.js', 'utf8');
        const flashcards = fs.readFileSync('app/js/flashcards.js', 'utf8');

        // 1. finishCardMeanings pruning when total uses >= 5
        const vocabCtx = {
            window: {},
            activeArtist: { slug: 'bad-bunny', name: 'Bad Bunny' },
            isCorpusDisplayExample: ex => Boolean(ex && !ex.canonical && ex.evidence !== 'dictionary' && !ex.reference_example),
            stampShownShares: (item, meanings) => meanings,
            normalizeMeaningShares: meanings => meanings,
            splitLowShareMeanings: meanings => ({ meanings, rare: [] }),
            unusedMenuSensesOf: () => []
        };
        vm.createContext(vocabCtx);
        const startFinish = vocabSource.indexOf('function finishCardMeanings(');
        const endFinish = vocabSource.indexOf('window.finishCardMeanings = finishCardMeanings;', startFinish);
        vm.runInContext(vocabSource.slice(startFinish, endFinish), vocabCtx);

        // Word with 6 total uses across 2 senses: Sense A has 5 examples, Sense B has 1 example.
        // Sense B should be pruned because total uses >= 5.
        const polysemousItem = { targetWord: 'test' };
        const meaningsHigh = [
            { translation: 'meaning A', allExamples: Array(5).fill({ spanish: 'A', english: 'A' }) },
            { translation: 'meaning B', allExamples: [{ spanish: 'B', english: 'B' }] }
        ];
        const resHigh = vocabCtx.finishCardMeanings(polysemousItem, meaningsHigh);
        assert.equal(resHigh.meanings.length, 1, 'Isolated 1-example sense must be pruned when total uses >= 5');
        assert.equal(resHigh.meanings[0].translation, 'meaning A');

        // Word with 3 total uses across 2 senses: Sense A has 2 examples, Sense B has 1 example.
        // Total uses < 5: Sense B is kept!
        const meaningsLow = [
            { translation: 'meaning A', allExamples: Array(2).fill({ spanish: 'A', english: 'A' }) },
            { translation: 'meaning B', allExamples: [{ spanish: 'B', english: 'B' }] }
        ];
        const resLow = vocabCtx.finishCardMeanings(polysemousItem, meaningsLow);
        assert.equal(resLow.meanings.length, 2, 'Senses must NOT be pruned when total uses < 5');

        // 2. getCyclableExamples canonical supplement when total uses < 5
        const cardsCtx = {
            window: {},
            activeArtist: { slug: 'bad-bunny', name: 'Bad Bunny' },
            isCorpusDisplayExample: ex => Boolean(ex && !ex.canonical && ex.evidence !== 'dictionary' && !ex.reference_example),
            findCanonicalForCard: (card, meaning) => ({
                target: 'Canonical sentence',
                english: 'Canonical translation',
                canonical: true,
                evidence: 'dictionary'
            }),
            dedupeExamples: exs => exs,
            sortExamplesByRelevance: exs => exs,
            currentMeaningIndex: 0,
            currentMWEIndex: 0,
            currentGroupSelection: null
        };
        vm.createContext(cardsCtx);
        const startCyclable = flashcards.indexOf('function getCyclableExamples(');
        const endCyclable = flashcards.indexOf('function cycleExample(', startCyclable);
        vm.runInContext(flashcards.slice(startCyclable, endCyclable), cardsCtx);

        const cardUnder5 = {
            meanings: [
                {
                    translation: 'meaning B',
                    allExamples: [{ spanish: 'Lyric line 1', english: 'Translation 1' }]
                }
            ]
        };
        const cyclable = cardsCtx.getCyclableExamples(cardUnder5, cardUnder5.meanings[0]);
        assert.equal(cyclable.length, 2, 'Canonical dictionary example must be added when total uses < 5 and only 1 lyric example exists');
        assert.equal(cyclable[0].spanish, 'Lyric line 1');
        assert.equal(cyclable[1].canonical, true);
        assert.equal(cyclable[1].target, 'Canonical sentence');
        """
        result = subprocess.run(['node', '-'], input=script, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
