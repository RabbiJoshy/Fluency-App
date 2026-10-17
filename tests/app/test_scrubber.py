"""Tests for card seek bar scrubber and level ruler scrubber."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class ScrubberTests(unittest.TestCase):
    def test_card_scrubber_tactile_navigation_without_abrupt_skips(self):
        script = r"""
        const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
        const source = fs.readFileSync('app/js/flashcards.js', 'utf8');

        // Locate cardBackPips setup block
        const start = source.indexOf('const cardBackPips = document.getElementById(\'cardBackPips\');');
        assert.ok(start > 0, 'cardBackPips setup block must exist');
        const end = source.indexOf('// Floating buttons (desktop sidebar)', start);
        assert.ok(end > start, 'cardBackPips setup end must exist');
        const block = source.slice(start, end);

        const listeners = {};
        const visitedCards = [];
        let deckScrubberActive = false;

        // Fake track positioned at x=50 with width=200px
        const fakeTrack = {
            getBoundingClientRect: () => ({ left: 50, width: 200 })
        };

        const fakeCardBackPips = {
            querySelector: sel => (sel === '.cbs-track-wrap' ? fakeTrack : null),
            classList: {
                add: cls => fakeCardBackPips.classes.add(cls),
                remove: cls => fakeCardBackPips.classes.delete(cls)
            },
            classes: new Set(),
            hasPointerCapture: () => true,
            releasePointerCapture: () => {},
            setPointerCapture: () => {},
            addEventListener: (type, fn) => { listeners[type] = fn; }
        };

        const context = {
            document: {
                getElementById: id => (id === 'cardBackPips' ? fakeCardBackPips : null)
            },
            flashcards: Array.from({ length: 21 }, (_, i) => ({ id: i })),
            currentIndex: 0,
            cardChainReturnIndex: -1,
            get _deckScrubberActive() { return deckScrubberActive; },
            set _deckScrubberActive(v) { deckScrubberActive = v; },
            goToDeckCard: (idx) => { visitedCards.push(idx); context.currentIndex = idx; }
        };

        vm.createContext(context);
        vm.runInContext(block, context);

        assert.ok(listeners.pointerdown, 'pointerdown registered');
        assert.ok(listeners.pointermove, 'pointermove registered');
        assert.ok(listeners.pointerup, 'pointerup registered');

        // 1. Touchdown ON THE THUMB (at x = 55, thumb center is at 50 + 0 = 50, dist = 5 <= 24px)
        // MUST NOT JUMP on touchdown!
        listeners.pointerdown({ button: 0, pointerId: 1, clientX: 55 });
        assert.equal(deckScrubberActive, true);
        assert.equal(fakeCardBackPips.classes.has('is-scrubbing'), true);
        assert.equal(visitedCards.length, 0, 'Touching the thumb must not jump cards on touchdown');
        assert.equal(context.currentIndex, 0);

        // 2. Drag smoothly: 18px per card step
        // dx = 18 -> Card 1
        listeners.pointermove({ pointerId: 1, clientX: 55 + 18, preventDefault() {} });
        assert.equal(context.currentIndex, 1, '18px drag moves to Card 1');

        // dx = 36 -> Card 2
        listeners.pointermove({ pointerId: 1, clientX: 55 + 36, preventDefault() {} });
        assert.equal(context.currentIndex, 2, '36px drag moves to Card 2');

        // dx = 54 -> Card 3
        listeners.pointermove({ pointerId: 1, clientX: 55 + 54, preventDefault() {} });
        assert.equal(context.currentIndex, 3, '54px drag moves to Card 3');

        // Drag backward dx = 18 -> back to Card 1
        listeners.pointermove({ pointerId: 1, clientX: 55 + 18, preventDefault() {} });
        assert.equal(context.currentIndex, 1, 'Dragging back moves sequentially');

        // Release pointer
        listeners.pointerup({ pointerId: 1 });
        assert.equal(deckScrubberActive, false);
        assert.equal(fakeCardBackPips.classes.has('is-scrubbing'), false);

        // 3. Tapping directly on the rail far away from thumb (e.g. at 50% = x: 150, dist = 100 > 24px)
        visitedCards.length = 0;
        listeners.pointerdown({ button: 0, pointerId: 2, clientX: 150 });
        assert.equal(context.currentIndex, 10, 'Tapping away on the rail directly seeks to tapped card');
        listeners.pointerup({ pointerId: 2 });
        """
        result = subprocess.run(['node', '-'], input=script, text=True,
                                capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_level_scrubber_avoids_scroll_fights(self):
        script = r"""
        const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
        const uiSource = fs.readFileSync('app/js/ui.js', 'utf8');

        assert.ok(uiSource.includes('let _levelScrubberInitiated = false;'),
            '_levelScrubberInitiated flag must exist to coordinate scrubber-driven button clicks');
        assert.ok(uiSource.includes('if (!_levelScrubberInitiated) {\n                        _scrollLevelSegToCenter(idx, false);'),
            'button click handler must not re-center the scrubber when the click was initiated by the scrubber itself');
        assert.ok(uiSource.includes('if (_levelProgrammaticScroll || pointerActive) return;'),
            'scrubber commit must not interrupt active pointer drag gestures');
        """
        result = subprocess.run(['node', '-'], input=script, text=True,
                                capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
