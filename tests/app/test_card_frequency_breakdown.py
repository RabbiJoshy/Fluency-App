"""The frequency figure on a card must stay checkable.

A merged card's frequency is a sum, and a sum is the one number on the card a
learner cannot verify from what is in front of them. Decision 0024 rule 4: the
card shows the source's own published per-surface figures and never an
apportioned or derived one. These tests pin the two halves of that — that the
breakdown survives aggregation, and that the copy claims only what the source
supports.
"""

from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"


class CardFrequencyBreakdownTests(unittest.TestCase):
    def setUp(self) -> None:
        self.vocab = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
        self.flashcards = (APP_ROOT / "js" / "flashcards.js").read_text(encoding="utf-8")
        self.style = (APP_ROOT / "css" / "style.css").read_text(encoding="utf-8")

    def test_lemma_aggregation_retains_each_contributing_surface(self) -> None:
        # Counting the forms is not enough: "total across 5 source-listed
        # forms" never says which five, which is the whole complaint.
        self.assertIn("total.breakdown.push({ surface: entry.word, value })", self.vocab)
        self.assertIn("sourceFrequencyBreakdown:", self.vocab)

    def test_unmerged_cards_carry_a_single_row_so_the_tooltip_has_one_path(self) -> None:
        self.assertIn("return own === null ? [] : [{ surface: item.word, value: own }];", self.vocab)

    def test_breakdown_reaches_the_button_escaped(self) -> None:
        self.assertIn("data-frequency-breakdown=", self.flashcards)
        self.assertIn("escapeCardText(JSON.stringify(", self.flashcards)

    def test_tooltip_says_it_counts_the_spelling_not_the_sense(self) -> None:
        # The published list is surface-keyed and POS-blind, which is why an
        # interjection carries a figure at all. The copy must not imply the
        # number is about this sense.
        self.assertIn("Counts how often the spelling appears in the source, ", self.flashcards)
        self.assertIn("not this sense.", self.flashcards)

    def test_no_apportioned_frequency_is_rendered(self) -> None:
        # Ordering may use a weighted split; the screen may not. If a weighting
        # helper ever reaches the render path, this should fail.
        for forbidden in ("weightedFrequency", "apportionedFrequency", "splitFrequency"):
            self.assertNotIn(forbidden, self.flashcards)

    def test_long_press_pins_the_breakdown(self) -> None:
        # A list of eight forms cannot be read inside the tap timeout, so the
        # pinned variant must not be on a timer.
        self.assertIn("{ pinned: true }", self.flashcards)
        self.assertIn("_initFreqLongPress", self.flashcards)

    def test_list_opts_out_of_the_narrow_tooltip_cap(self) -> None:
        # The base .freq-tooltip caps width at 220px, which wraps a form list
        # into unreadable ribbons.
        self.assertIn(".freq-tooltip-wide", self.style)
        self.assertIn("max-width: 340px", self.style)


if __name__ == "__main__":
    unittest.main()
