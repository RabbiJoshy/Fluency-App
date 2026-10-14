"""Companion navigation and partially learned cycle rows keep their boundaries."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class UiRefinementTests(unittest.TestCase):
    def test_companion_navigation_and_cycle_knowledge(self):
        script = r"""
        const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
        const cards = fs.readFileSync('app/js/flashcards.js', 'utf8');
        const knowledge = fs.readFileSync('app/js/knowledge.js', 'utf8');
        const c = {
            window: {}, currentIndex: 0, cardNavStack: [],
            flashcards: [
                { targetWord: 'fue', splitInfo: { index: 1 } },
                { targetWord: 'fue', splitInfo: { index: 2 } },
                { targetWord: 'otro', splitInfo: { index: 2 } }
            ],
            goToDeckCard(index) { c.currentIndex = index; },
            stepToSplitSibling(direction) { c.direction = direction; return true; },
            stats: { levelNumber: 4 },
            getKnowledgeFocusItems: () => [
                { meaningIndex: 0, learned: true },
                { meaningIndex: 0, learned: false },
                { meaningIndex: 1, learned: true },
                { meaningIndex: 2, learned: false, needsReview: true, reviewReason: 'incorrect' }
            ],
            getKnowledgeItemState: (_card, item) => item
        };
        vm.createContext(c);
        vm.runInContext(cards.slice(cards.indexOf('function selectSplitCompanion('),
            cards.indexOf('function stepToSplitSibling(')), c);
        let stopped = 0;
        const event = { preventDefault() {}, stopPropagation() { stopped++; } };
        c.selectSplitCompanion(event, 2);
        assert.equal(c.currentIndex, 1);
        c.selectSplitCompanion(event, 1);
        assert.equal(c.currentIndex, 0);
        c.selectSplitCompanion(event, 1);
        assert.equal(c.currentIndex, 0);
        c.flashcards[1].targetWord = 'different';
        c.selectSplitCompanion(event, 2);
        assert.equal(c.currentIndex, 0, 'never navigate to an unrelated word');
        c.cardNavStack = [{}];
        c.flashcards[0]._splitNext = { targetWord: 'fue', splitInfo: { index: 2 } };
        c.showSplitSibling = card => { c.selected = card.splitInfo.index; };
        c.selectSplitCompanion(event, 2);
        assert.equal(c.selected, 2, 'linked word views select the requested sibling');
        assert.equal(stopped, 5);
        assert.equal(c.currentStudyLevelLabel(), 'Level 4');
        c.stats.levelNumber = null;
        assert.equal(c.currentStudyLevelLabel(), '');
        vm.runInContext(knowledge.slice(knowledge.indexOf('function getPracticeMeaningInfo('),
            knowledge.indexOf('function getPracticeMeaningIndices(')), c);
        const info = c.getPracticeMeaningInfo({});
        assert.deepEqual([...info.known], [1], 'a partly learned cycle must remain active');
        assert.deepEqual([...info.indices], [2]);
        assert.equal(info.practising, 1);
        """
        result = subprocess.run(['node', '-'], input=script, text=True,
                                capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_exact_three_companion_selection(self):
        script = r"""
        const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
        const source = fs.readFileSync('app/js/flashcards.js', 'utf8');
        const c = { window: {}, stats: {}, cardNavStack: [{}], currentIndex: 0,
            currentMeaningIndex: 2, currentExampleIndex: 2, currentMWEIndex: 2,
            currentGroupSelection: {}, document: { getElementById: () => null },
            updateCard() {}, goToDeckCard(index) { c.currentIndex = index; } };
        vm.createContext(c);
        vm.runInContext(source.slice(source.indexOf('function selectSplitCompanion('),
            source.indexOf('// Plain forward step')), c);
        const event = { preventDefault() {}, stopPropagation() {} };
        for (const order of [[1,2,3],[2,3,1],[3,1,2]]) {
            const cards = order.map(index => ({ targetWord:'fue', splitInfo:{index} }));
            cards.forEach((card, index) => {
                card._splitNext = cards[index+1]; card._splitPrev = cards[index-1];
            });
            for (const from of cards) for (const to of cards) {
                c.flashcards = [from]; c.selectSplitCompanion(event, to.splitInfo.index);
                assert.equal(c.flashcards[0], to);
                assert.equal(c.cardNavStack.length, 1);
            }
            c.flashcards = [cards[0]];
            assert(c.stepToSplitSibling()); assert(c.stepToSplitSibling());
            assert.equal(c.stepToSplitSibling(), false);
        }
        c.cardNavStack = [];
        c.flashcards = [1,2,3].map(index => ({targetWord:'fue',splitInfo:{index}}));
        for (let from=0; from<3; from++) for (let to=0; to<3; to++) {
            c.currentIndex=from; c.selectSplitCompanion(event,to+1); assert.equal(c.currentIndex,to);
        }
        """
        result = subprocess.run(['node', '-'], input=script, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
