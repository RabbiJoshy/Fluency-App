"""Tests for card seek bar scrubber and level ruler scrubber."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class ScrubberTests(unittest.TestCase):
    def test_card_scrubber_smooth_proportional_tracking(self):
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

        // Touch at 0% (x = 50)
        listeners.pointerdown({ button: 0, pointerId: 1, clientX: 50 });
        assert.equal(deckScrubberActive, true);
        assert.equal(fakeCardBackPips.classes.has('is-scrubbing'), true);
        assert.equal(context.currentIndex, 0);

        // Move across the rail proportionally (50% -> x = 150)
        listeners.pointermove({ pointerId: 1, clientX: 150, preventDefault() {} });
        assert.equal(context.currentIndex, 10, 'midpoint of 21 cards (0-20) is 10');

        // Move to 75% -> x = 200
        listeners.pointermove({ pointerId: 1, clientX: 200, preventDefault() {} });
        assert.equal(context.currentIndex, 15, '75% of 20 is 15');

        // Move to 100% -> x = 250
        listeners.pointermove({ pointerId: 1, clientX: 250, preventDefault() {} });
        assert.equal(context.currentIndex, 20, 'endpoint is card 20');

        // Move past right bound -> clamps to 20
        listeners.pointermove({ pointerId: 1, clientX: 300, preventDefault() {} });
        assert.equal(context.currentIndex, 20);

        // Move past left bound -> clamps to 0
        listeners.pointermove({ pointerId: 1, clientX: 10, preventDefault() {} });
        assert.equal(context.currentIndex, 0);

        // Release
        listeners.pointerup({ pointerId: 1 });
        assert.equal(deckScrubberActive, false);
        assert.equal(fakeCardBackPips.classes.has('is-scrubbing'), false);
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
