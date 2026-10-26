"""Regression tests for Portuguese Wiktionary source-to-target mapping."""

import unittest
from pathlib import Path

from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.mapping import (
    MAPPING_VERSION,
    PINNED_SNAPSHOT_HASH,
    map_kaikki_sense_to_target,
    parse_raw_gloss,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class WiktionaryMappingRegressionTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_sense_menu_language_policy(
            REPO_ROOT, policy_id="pt-v1", language="pt"
        )

    def test_saber_know_how(self):
        row = {"word": "saber", "pos": "verb"}
        sense = {
            "id": "en-saber-pt-verb-G7UJN~jl",
            "glosses": ["to know", "to know how"],
            "raw_glosses": [
                "to know",
                "(catenative) to know how [with infinitive ‘to do something’]",
            ],
            "tags": ["catenative"],
            "info_templates": [
                {
                    "name": "+obj",
                    "args": {"1": "pt", "2": "inf<to do something>"},
                    "expansion": "[with infinitive ‘to do something’]",
                }
            ],
            "examples": [
                {
                    "text": "Não sei fazer isso, mas ela sabe.",
                    "english": "I don’t know how to do this, but she knows.",
                    "type": "example",
                }
            ],
        }

        record = map_kaikki_sense_to_target(
            row, sense, policy=self.policy, line_number=1788
        )

        self.assertEqual(record.source.source_sense_id, "en-saber-pt-verb-G7UJN~jl")
        self.assertEqual(record.source.locator.line_number, 1788)
        self.assertEqual(
            record.source.provenance.snapshot_content_id, PINNED_SNAPSHOT_HASH
        )
        self.assertEqual(record.wsd_target.wsd_definition, "to know how")
        self.assertEqual(record.learner.heading, "to know how")
        self.assertEqual(record.learner.context_subrow, "+ infinitive")
        self.assertTrue(record.learner.is_non_exhaustive_cue)

    def test_saber_factual_knowledge_exact_heading(self):
        row = {"word": "saber", "pos": "verb"}
        sense = {
            "id": "en-saber-pt-verb-pt:to_know_a_fact",
            "glosses": ["to know", "to be aware, to know"],
            "raw_glosses": [
                "to know",
                "(transitive or intransitive) to be aware, to know [with direct object ‘a fact’ or que (+ indicative clause when positive or subjunctive clause when negated) ‘that ...’ or indirect question]",
            ],
            "tags": ["intransitive", "transitive"],
            "info_templates": [
                {
                    "name": "+obj",
                    "args": {
                        "1": "pt",
                        "2": "dirobj<a fact>/:que(ind-cl&when positive/sub-cl&when negated)<that ...>/indirect question",
                    },
                    "expansion": "[with direct object ‘a fact’ or que (+ indicative clause when positive or subjunctive clause when negated) ‘that ...’ or indirect question]",
                }
            ],
        }

        record = map_kaikki_sense_to_target(
            row, sense, policy=self.policy, line_number=1788
        )

        # Verified: factual saber produces 'to be aware, to know', exactly matching implementation
        self.assertEqual(record.wsd_target.wsd_definition, "to be aware, to know")
        self.assertEqual(record.learner.heading, "to be aware, to know")
        self.assertEqual(
            record.learner.context_subrow,
            "+ direct object or que (+ indicative clause when positive or subjunctive clause when negated) or indirect question",
        )

    def test_unrelated_catenatives_do_not_become_know_how(self):
        """Regression test: verify unrelated catenative verbs do not gain 'know how'."""
        catenative_cases = [
            (
                "terminar",
                "en-terminar-pt-verb-pt:to_finish_doing_something",
                "(catenative) to finish [with de (+ infinitive) ‘doing something’]",
                "to finish",
                "+ de (+ infinitive)",
            ),
            (
                "terminar",
                "en-terminar-pt-verb-pt:to_end_up",
                "(catenative) to end up (to eventually (do something)) [with por (+ infinitive) ‘doing something’]",
                "to end up (to eventually (do something))",
                "+ por (+ infinitive)",
            ),
            (
                "continuar",
                "en-continuar-pt-verb-EvXWhSx-",
                "(catenative) to continue; to keep; to be still (doing something) (to not stop doing something) [with gerund or a (+ infinitive) ‘doing something’]",
                "to continue; to keep; to be still (doing something) (to not stop doing something)",
                "+ gerund or a (+ infinitive)",
            ),
            (
                "esperar",
                "en-esperar-pt-verb-pt:to_wait_for_something_to_happen",
                "(catenative) to wait [with subject pronoun ‘for someone’ (optional) and personal infinitive ‘to do something’]",
                "to wait",
                "+ subject pronoun (optional) and personal infinitive",
            ),
        ]

        for word, sid, raw_gloss, expected_def, expected_cue in catenative_cases:
            row = {"word": word, "pos": "verb"}
            sense = {
                "id": sid,
                "raw_glosses": [raw_gloss],
                "glosses": [expected_def],
                "tags": ["catenative"],
                "info_templates": [{"name": "+obj", "expansion": raw_gloss.split("[")[1].rstrip("]") if "[" in raw_gloss else ""}],
            }
            record = map_kaikki_sense_to_target(row, sense, policy=self.policy)
            self.assertEqual(record.wsd_target.wsd_definition, expected_def)
            self.assertEqual(record.learner.heading, expected_def)
            self.assertNotIn("know how", record.learner.heading.lower())
            self.assertEqual(record.learner.context_subrow, expected_cue)

    def test_unrelated_adjectives_do_not_invent_com(self):
        """Regression test: verify frames with adjective do not invent '/ com'."""
        row = {"word": "parecer", "pos": "verb"}
        sense = {
            "id": "en-parecer-pt-verb-seem",
            "glosses": ["to seem, to appear"],
            "raw_glosses": ["(copulative) to seem, to appear [with adjective]"],
            "tags": ["copulative"],
            "info_templates": [{"name": "+obj", "expansion": "[with adjective]"}],
        }

        record = map_kaikki_sense_to_target(row, sense, policy=self.policy)
        self.assertEqual(record.wsd_target.wsd_definition, "to seem, to appear")
        self.assertEqual(record.learner.context_subrow, "+ adjective")
        self.assertNotIn("com", record.learner.context_subrow)

    def test_unrelated_locations_do_not_invent_em(self):
        """Regression test: verify frames with location do not invent 'em' if not present."""
        row = {"word": "situar", "pos": "verb"}
        sense = {
            "id": "en-situar-pt-verb-situate",
            "glosses": ["to situate"],
            "raw_glosses": ["(transitive) to situate [with direct object ‘something’ and adpositional phrase ‘in a location’]"],
            "tags": ["transitive"],
            "info_templates": [
                {
                    "name": "+obj",
                    "expansion": "[with direct object ‘something’ and adpositional phrase ‘in a location’]",
                }
            ],
        }

        record = map_kaikki_sense_to_target(row, sense, policy=self.policy)
        self.assertEqual(record.wsd_target.wsd_definition, "to situate")
        self.assertEqual(
            record.learner.context_subrow,
            "+ direct object and adpositional phrase",
        )
        self.assertNotIn("em", record.learner.context_subrow)


if __name__ == "__main__":
    unittest.main()
