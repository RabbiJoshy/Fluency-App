"""Wiktionary parity with the fields SpanishDict publishes.

SpanishDict gives every sense a `context` and marks `regions` on some. Wiktionary
carries both, but embedded: context in the prose of a raw gloss, regions among a
flat tag list. These are derived so the two providers publish one shape.
"""

import unittest
import json
from pathlib import Path

from fluency.sense_menu.kaikki import _context, _regions


PT_POLICY = {"region_tags": ["Angola", "Brazil", "Mozambique", "Portugal"]}


class ContextDerivationTests(unittest.TestCase):
    def test_nested_subgloss_wins(self) -> None:
        sense = {"glosses": ["not; don't", "used in double negatives"]}
        self.assertEqual(_context(sense), "used in double negatives")

    def test_leading_parenthetical_of_raw_gloss(self) -> None:
        sense = {
            "glosses": ["what"],
            "raw_glosses": ["(interrogative) what (used to ask for a specific thing)"],
        }
        self.assertEqual(_context(sense), "interrogative")

    def test_topics_are_labels_not_sense_context(self) -> None:
        sense = {"glosses": ["bank"], "topics": ["finance", "business"]}
        self.assertEqual(_context(sense), "")

    def test_qualifier_is_label_not_sense_context(self) -> None:
        sense = {"glosses": ["thing"], "qualifier": "archaic"}
        self.assertEqual(_context(sense), "")

    def test_absent_context_is_empty_not_missing(self) -> None:
        self.assertEqual(_context({"glosses": ["thing"]}), "")

    def test_parenthetical_must_precede_real_text(self) -> None:
        """A gloss that is only a parenthetical carries no separable context."""

        self.assertEqual(_context({"glosses": ["x"], "raw_glosses": ["(alone)"]}), "")

    def test_overlong_parenthetical_is_not_a_context_label(self) -> None:
        long = "(" + "x" * 80 + ") word"
        self.assertEqual(_context({"glosses": ["w"], "raw_glosses": [long]}), "")

    def test_nested_parenthetical_is_balanced_not_truncated(self) -> None:
        sense = {
            "glosses": ["to misbehave"],
            "raw_glosses": ["(said of people (especially children), slang) to misbehave"],
        }
        self.assertEqual(_context(sense), "said of people (especially children)")

    def test_pure_label_parenthetical_leaves_secondary_glosses_as_context(self) -> None:
        sense = {
            "glosses": ["to abandon", "to desert", "to leave behind"],
            "raw_glosses": ["(transitive) to abandon, to desert, to leave behind"],
        }
        self.assertEqual(_context(sense), "to desert | to leave behind")

    def test_leading_semantic_parenthetical_takes_priority_over_secondary_glosses(self) -> None:
        sense = {
            "glosses": ["to abandon", "to desert", "to leave behind"],
            "raw_glosses": ["(of a child) to abandon, to desert, to leave behind"],
        }
        self.assertEqual(_context(sense), "of a child")

    def test_companion_takes_precedence_as_context(self) -> None:
        sense = {
            "glosses": ["to talk"],
            "raw_glosses": ["(intransitive) to talk [with com ‘to, with’]"],
        }
        self.assertEqual(_context(sense), "+ com")

    def test_overlong_secondary_glosses_not_used_as_context(self) -> None:
        sense = {
            "glosses": [
                "to abandon",
                "to completely give up or cease to support or look after someone, leaving them entirely without aid",
            ],
            "raw_glosses": [
                "to abandon",
                "to completely give up or cease to support or look after someone, leaving them entirely without aid",
            ],
        }
        self.assertEqual(_context(sense), "")


class RegionDerivationTests(unittest.TestCase):
    def test_regional_tags_are_extracted(self) -> None:
        sense = {"tags": ["Brazil", "informal", "Portugal"]}
        self.assertEqual(_regions(sense, PT_POLICY), ["Brazil", "Portugal"])

    def test_non_regional_tags_are_ignored(self) -> None:
        self.assertEqual(_regions({"tags": ["informal", "slang"]}, PT_POLICY), [])

    def test_regions_inside_a_nested_parenthetical_are_extracted(self) -> None:
        sense = {
            "raw_glosses": [
                "(transitive (Portugal) or intransitive (Brazil), colloquial) to score"
            ]
        }
        self.assertEqual(_regions(sense, PT_POLICY), ["Brazil", "Portugal"])

    def test_language_declaring_no_regions_gets_an_empty_list(self) -> None:
        """Empty is a statement, not an absence: the field is always present."""

        self.assertEqual(_regions({"tags": ["Brazil"]}, {"region_tags": []}), [])
        self.assertEqual(_regions({"tags": ["Brazil"]}, {}), [])

    def test_czech_policy_does_not_inherit_portuguese_regions(self) -> None:
        root = Path(__file__).resolve().parents[2]
        policy = json.loads(
            (root / "config/sense_menu/languages/cs-v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(policy["region_tags"], ["Moravia"])
        self.assertEqual(_regions({"tags": ["Brazil", "Moravia"]}, policy), ["Moravia"])


if __name__ == "__main__":
    unittest.main()
