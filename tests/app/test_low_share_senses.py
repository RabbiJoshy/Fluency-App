"""Senses under 10% of a card's assigned sentences leave the main card.

vocab.js finishCardMeanings runs for every card builder (study sets and the
search/peek cards in flashcards-modals.js): shares are normalised over the
card's assigned sentences, then a sense whose near-synonym group holds under
10% moves to Rarer uses with its sentences.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("node"), "Node.js required")
class LowShareSenseTests(unittest.TestCase):
    def run_js(self, body: str) -> dict:
        vocab = (ROOT / "app/js/vocab.js").read_text(encoding="utf-8")
        pure = vocab[vocab.index("// low-share-pure"):vocab.index("// /low-share-pure")]
        script = pure + "\n" + body
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def test_que_keeps_what_and_that_and_moves_how(self) -> None:
        # Raw frequencies as the release ships them: counts over 80 candidates.
        out = self.run_js(r"""
            const m = (pos, meaning, n, extra = {}) => ({ pos, meaning, headword: 'que', percentage: n / 80,
                                                          allExamples: Array(n).fill({ target: 'x' }), ...extra });
            const meanings = [m('det', 'what', 7), m('conj', 'that', 6), m('PHRASE', 'why', 4),
                              m('PHRASE', 'the thing is', 2), m('adv', 'how', 1)];
            const item = { unused_menu_senses: [{ pos: 'pron', translation: 'whose', sense_id: 's9' }] };
            const done = finishCardMeanings(item, meanings);
            console.log(JSON.stringify({
              main: done.meanings.map(x => [x.meaning, +x.percentage.toFixed(3)]),
              rare: done.unusedMenuSenses.map(x => [x.meaning, !!x.lowShare, x.allExamples.length]),
            }));
        """)
        self.assertEqual([name for name, _ in out["main"]], ["what", "that", "why", "the thing is"])
        self.assertAlmostEqual(dict(out["main"])["what"], 0.35)
        self.assertEqual(out["rare"], [["how", True, 1], ["whose", False, 0]])

    def test_three_of_thirty_stays_and_synonyms_pool(self) -> None:
        out = self.run_js(r"""
            const m = (meaning, n) => ({ pos: 'prep', meaning, headword: 'de', percentage: n / 30 });
            const meanings = [m('of', 20), m('from', 3), m('by', 2), m('in', 1), m('in', 2), m('with', 2)];
            const done = finishCardMeanings({}, meanings);
            console.log(JSON.stringify({ main: done.meanings.map(x => x.meaning),
                                         rare: done.unusedMenuSenses.map(x => x.meaning) }));
        """)
        self.assertEqual(out["main"], ["of", "from", "in", "in"])
        self.assertEqual(out["rare"], ["by", "with"])

    def test_each_subsense_row_needs_the_bar(self) -> None:
        # estuve: five "I was" rows hold 35% together; "to fit" rests on one
        # misread "estuve pensando" and must not ride on its siblings.
        out = self.run_js(r"""
            const m = (context, n) => ({ pos: 'VERB', meaning: 'to be', headword: 'estar', context, percentage: n / 80 });
            const meanings = [m('quality', 9), m('emotion', 7), m('located', 2), m('present', 9), m('to fit', 1)];
            const done = finishCardMeanings({}, meanings);
            console.log(JSON.stringify({ main: done.meanings.map(x => x.context),
                                         rare: done.unusedMenuSenses.map(x => x.context) }));
        """)
        self.assertEqual(out["main"], ["quality", "emotion", "present"])
        self.assertEqual(out["rare"], ["located", "to fit"])

    def test_a_spanishdict_context_is_measured_whole(self) -> None:
        # kilo: "kilo" and "kilogram" are one meaning under "kilogram"; WSD
        # splits its sentences at random, so neither half may fall alone.
        out = self.run_js(r"""
            const m = (meaning, context, n, source = 'spanishdict') =>
                ({ pos: 'NOUN', meaning, headword: 'kilo', context, source, percentage: n / 30 });
            const meanings = [m('kilo', 'kilogram', 2), m('kilogram', 'kilogram', 2), m('loads', 'a lot', 26),
                              m('x', 'shared label', 2, 'wiktionary'), m('y', 'shared label', 2, 'wiktionary')];
            const done = finishCardMeanings({}, meanings);
            console.log(JSON.stringify(done.meanings.map(x => x.meaning)));
        """)
        self.assertEqual(out, ["kilo", "kilogram", "loads"])

    def test_a_translation_that_clears_the_bar_keeps_its_largest_row(self) -> None:
        out = self.run_js(r"""
            const m = (meaning, context, n) => ({ pos: 'VERB', meaning, headword: 'ter', context, percentage: n / 30 });
            const meanings = [m('to have', 'to own', 2), m('to have', 'perfect', 1), m('to say', '', 27)];
            const done = finishCardMeanings({}, meanings);
            console.log(JSON.stringify(done.meanings.map(x => x.context)));
        """)
        self.assertEqual(out, ["to own", ""])

    def test_a_card_is_never_left_without_a_sense(self) -> None:
        out = self.run_js(r"""
            const meanings = [{ pos: 'adv', meaning: 'how', percentage: 0.05 },
                              { pos: 'PHRASE', meaning: 'why', percentage: 0.95 }];
            const done = finishCardMeanings({}, meanings);
            console.log(JSON.stringify(done.meanings.map(x => x.meaning)));
        """)
        self.assertEqual(out, ["how", "why"])


if __name__ == "__main__":
    unittest.main()
