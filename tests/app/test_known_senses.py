"""Part-known cards: known senses stay greyed, answers reach only the rest.

Runs app/js/knowledge.js against the real schedule in app/js/progress.js, in a
Node vm with the network, DOM and card renderer stubbed out.
"""

import json
from pathlib import Path
import shutil
import subprocess
import unittest


APP = Path(__file__).resolve().parents[2] / "app"

RUNNER = r"""
    const fs = require('node:fs');
    const vm = require('node:vm');
    const [progressPath, knowledgePath, flashcardsPath] = process.argv.slice(2);
    const strip = source => source.replace(/^import .*$/gm, '');
    const progress = fs.readFileSync(progressPath, 'utf8');
    const schedule = progress.slice(
        progress.indexOf('const SRS_DAY_MS'), progress.indexOf('const progressSurfaceById'));
    const flashcards = fs.readFileSync(flashcardsPath, 'utf8');
    const stepper = flashcards.slice(
        flashcards.indexOf('function stepPractisedMeaningIndex'),
        flashcards.indexOf('function isHiddenExpressionOnParent'));

    const saved = [];
    const context = {
        window: {}, console, Date, Math, JSON, Map, Set, Number, String, Array, Object, Promise,
        currentUser: { initials: 'JT' },
        progressData: {},
        itemProgressData: {},
        selectedLanguage: 'es',
        activeArtist: null,
        flashcards: [],
        currentIndex: 0,
        currentMeaningIndex: 0,
        currentMWEIndex: 0,
        currentGroupSelection: null,
        sendOrQueue: () => {},
        document: { addEventListener: () => {} },
    };
    vm.createContext(context);
    vm.runInContext(schedule, context);
    vm.runInContext(strip(fs.readFileSync(knowledgePath, 'utf8')), context);
    vm.runInContext(stepper, context);
    context.getWordProgressState = (id) => context.getProgressState(context.progressData[id]);
    context.window.getWordProgressState = context.getWordProgressState;
    context.window.saveWordProgress = async (card, isCorrect) => { saved.push(['card', isCorrect]); };
    context.renderKnowledgeOverview = () => {};
    context.updateCard = () => {};

    const DAY = 86400000;
    const iso = ms => new Date(Date.now() - ms).toISOString();
    const card = {
        fullId: 'es00001', targetWord: 'banco', isMultiMeaning: true,
        meanings: [
            { pos: 'NOUN', meaning: 'bank', senseId: 's-bank', percentage: 0.8 },
            { pos: 'NOUN', meaning: 'bench', senseId: 's-bench', percentage: 0.15 },
            { pos: 'NOUN', meaning: 'shoal', senseId: 's-shoal', percentage: 0.05 },
        ],
    };
    const items = card.meanings.map((m, i) => context.knowledgeItemsForMeaning(card, m, i)[0]);
    const state = i => context.getKnowledgeItemState(card, items[i]);
    const out = {};

    out.unseenIsUnchanged = context.buildKnowledgeAwareCard(card) === card;

    // bank known on its own schedule; bench missed; shoal never answered.
    context.itemProgressData[items[0].itemId] = {
        itemId: items[0].itemId, parentWordId: card.fullId, correct: 2, wrong: 0,
        lastCorrect: iso(DAY), lastSeen: iso(DAY), srsStage: 3,
    };
    context.itemProgressData[items[1].itemId] = {
        itemId: items[1].itemId, parentWordId: card.fullId, correct: 0, wrong: 1,
        lastWrong: iso(DAY / 24), lastSeen: iso(DAY / 24), srsStage: 0,
    };
    const fromSet = context.buildKnowledgeAwareCard(card);
    const fromReview = context.buildKnowledgeAwareCard(card, { skipWhenNothingToPractise: true });
    out.setFlags = fromSet.meanings.map(m => Boolean(m.isKnownSense));
    out.reviewFlags = fromReview.meanings.map(m => Boolean(m.isKnownSense));
    out.fronted = fromSet.translation;
    out.steps = [
        context.stepPractisedMeaningIndex(fromSet, 1, 1),
        context.stepPractisedMeaningIndex(fromSet, 2, 1),
        context.stepPractisedMeaningIndex(fromSet, 1, -1),
    ];

    (async () => {
        const bankBefore = JSON.stringify(context.itemProgressData[items[0].itemId]);
        const bankDueBefore = state(0).nextReviewAt;

        // Tapping shoal wrong on this visit survives a whole-card "yes".
        context.beginKnowledgeCardVisit(fromSet);
        await new Promise(resolve => setTimeout(resolve, 5));
        await context.saveKnowledgeProgress(fromSet, [items[2]], false);
        out.handledAsParts = await context.saveWholeCardKnowledgeAnswer(fromSet, true);
        out.afterYes = [0, 1, 2].map(i => state(i).learned);
        out.bankUntouched = JSON.stringify(context.itemProgressData[items[0].itemId]) === bankBefore;

        // Completing every sense promotes the card; the promotion must not
        // re-date bank, which keeps its own schedule.
        await context.saveKnowledgeProgress(fromSet, [items[2]], true);
        out.promoted = saved.some(([kind, ok]) => kind === 'card' && ok);
        context.progressData[card.fullId] = {
            correct: 1, wrong: 0, lastCorrect: new Date().toISOString(),
            lastSeen: new Date().toISOString(), srsStage: 1,
        };
        out.bankKeepsSchedule = state(0).nextReviewAt === bankDueBefore;

        // Nothing left and the card not due: Review skips it, a set shows it whole.
        out.reviewSkips = context.buildKnowledgeAwareCard(card, { skipWhenNothingToPractise: true }) === null;
        out.setShowsWhole = context.buildKnowledgeAwareCard(card) === card;

        // A card with no known senses answers as a whole.
        out.plainCardHandled = await context.saveWholeCardKnowledgeAnswer(card, true);

        // One-tap exception: untouched siblings become known only on leaving.
        const fresh = {
            fullId: 'es00002', targetWord: 'cabo', isMultiMeaning: true,
            meanings: [
                { pos: 'NOUN', meaning: 'end', senseId: 'c-end' },
                { pos: 'NOUN', meaning: 'corporal', senseId: 'c-corporal' },
                { pos: 'NOUN', meaning: 'cape', senseId: 'c-cape' },
            ],
        };
        const freshItems = fresh.meanings.map((m, i) => context.knowledgeItemsForMeaning(fresh, m, i)[0]);
        const freshState = i => context.getKnowledgeItemState(fresh, freshItems[i]);
        vm.runInContext('knowledgeOverviewCard = globalThis.__fresh', Object.assign(context, { __fresh: fresh }));
        await context.markKnowledgeOverviewItem(null, 0, false);
        await context.markKnowledgeOverviewItem(null, 2, false);
        out.beforeLeaving = [0, 1, 2].map(i => freshState(i).seen);
        context.beginKnowledgeCardVisit(card);
        await new Promise(resolve => setTimeout(resolve, 5));
        out.afterLeaving = [0, 1, 2].map(i => [freshState(i).learned, freshState(i).needsReview]);
        out.cornerNeverKnownThenWrong = context.itemProgressData[freshItems[2].itemId].correct;


        // A fresh card with no greyed senses must preserve a checkbox answer
        // when the learner subsequently swipes yes on the whole card.
        const selectedCard = { ...fresh, fullId: 'es00003' };
        const selectedItems = context.getKnowledgeOverviewItems(selectedCard);
        context.beginKnowledgeCardVisit(selectedCard);
        context.flashcards = [selectedCard];
        context.document.activeElement = null;
        context.document.getElementById = () => ({ hidden: true });
        vm.runInContext('knowledgeOverviewCard = globalThis.__selected', Object.assign(context, { __selected: selectedCard }));
        out.newRowsUnchecked = !context.knowledgeOverviewRowsHTML(selectedCard,
            selectedItems.map((item, index) => ({ item, index }))).includes(' checked');
        const selectEvent = { target: { checked: true }, stopPropagation() {} };
        await context.toggleKnowledgeOverviewReview(selectEvent, 1);
        const selectedBefore = JSON.stringify(context.itemProgressData[selectedItems[1].itemId]);
        await context.toggleKnowledgeOverviewReview(selectEvent, 1);
        out.duplicateSelectionIgnored = selectedBefore === JSON.stringify(context.itemProgressData[selectedItems[1].itemId]);
        out.checkboxReopensChecked = context.knowledgeOverviewRowsHTML(selectedCard,
            [{ item: selectedItems[1], index: 1 }]).includes(' checked');
        out.freshSwipeHandled = await context.saveWholeCardKnowledgeAnswer(selectedCard, true);
        out.freshSwipePreservesSelection = selectedBefore === JSON.stringify(context.itemProgressData[selectedItems[1].itemId]);
        await new Promise(resolve => setTimeout(resolve, 5));
        await context.toggleKnowledgeOverviewReview({ target: { checked: false }, stopPropagation() {} }, 1);
        out.deselectionResolves = context.getKnowledgeItemState(selectedCard, selectedItems[1]).learned;

        // Time-based review is not an explicit request to revisit a meaning.
        context.itemProgressData[selectedItems[0].itemId] = {
            correct: 1, lastCorrect: iso(3 * DAY), lastSeen: iso(3 * DAY), srsStage: 1,
        };
        out.dueIsNotSelected = !context.knowledgeOverviewRowsHTML(selectedCard,
            [{ item: selectedItems[0], index: 0 }]).includes(' checked');

        console.log(JSON.stringify(out));
    })().catch(error => { console.error(error); process.exit(1); });
"""


@unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
class KnownSenseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            ["node", "-", str(APP / "js/progress.js"), str(APP / "js/knowledge.js"),
             str(APP / "js/flashcards.js")],
            input=RUNNER, text=True, capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        cls.out = json.loads(result.stdout)

    def test_unseen_card_is_left_alone(self) -> None:
        self.assertTrue(self.out["unseenIsUnchanged"])

    def test_sets_and_review_build_the_same_part_known_card(self) -> None:
        self.assertEqual(self.out["setFlags"], [True, False, False])
        self.assertEqual(self.out["reviewFlags"], self.out["setFlags"])
        self.assertEqual(self.out["fronted"], "bench")

    def test_cycling_passes_over_known_senses(self) -> None:
        self.assertEqual(self.out["steps"], [2, 1, 2])

    def test_whole_card_answer_reaches_only_the_practised_senses(self) -> None:
        self.assertTrue(self.out["handledAsParts"])
        # bench answered yes; shoal, tapped wrong on this visit, stays wrong.
        self.assertEqual(self.out["afterYes"], [True, True, False])
        self.assertTrue(self.out["bankUntouched"])

    def test_completion_promotes_the_card_without_redating_known_senses(self) -> None:
        self.assertTrue(self.out["promoted"])
        self.assertTrue(self.out["bankKeepsSchedule"])

    def test_review_skips_a_finished_word_and_a_set_shows_it_whole(self) -> None:
        self.assertTrue(self.out["reviewSkips"])
        self.assertTrue(self.out["setShowsWhole"])
        self.assertFalse(self.out["plainCardHandled"])

    def test_one_tap_exception_marks_siblings_known_on_leaving(self) -> None:
        self.assertEqual(self.out["beforeLeaving"], [True, False, True])
        self.assertEqual(
            self.out["afterLeaving"],
            [[False, True], [True, False], [False, True]],
        )
        self.assertEqual(self.out["cornerNeverKnownThenWrong"], 0)

    def test_meaning_review_checkboxes_preserve_choices(self) -> None:
        for key in ["newRowsUnchecked", "duplicateSelectionIgnored", "checkboxReopensChecked",
                    "freshSwipeHandled", "freshSwipePreservesSelection", "deselectionResolves",
                    "dueIsNotSelected"]:
            with self.subTest(key=key):
                self.assertTrue(self.out[key])


if __name__ == "__main__":
    unittest.main()
