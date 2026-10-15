"""Grammar classes checked against sentence-reviewed, frozen parser observations."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "research/cascade/trouble-words"
sys.path.insert(0, str(RULES))
from grammar_context import clitic_label, phrase_is_literal
from occurrence import locate

spec = importlib.util.spec_from_file_location("hinge_restore", ROOT / "research/hinge/evaluate_rules.py")
module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / "research/hinge"))
spec.loader.exec_module(module)


class ContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r["review_id"]: r for r in json.loads((Path(__file__).parent / "fixtures/context.json").read_text())}

    def hit(self, identifier):
        row = self.rows[identifier]
        return locate(module.restore(row["parse"]), row["text"], row["word"], row["target_span"])

    def test_attached_pronouns_select_component_not_host(self):
        for identifier, host in ((6044, "ouvi-a"), (6231, "Lembrem-se"), (6281, "disse-me"), (6865, "Ajudemo-nos")):
            with self.subTest(identifier=identifier):
                words, i, surface = self.hit(identifier)
                self.assertEqual(words[i].text.lower(), self.rows[identifier]["word"])
                self.assertEqual(words[i].parent.text, host)
                self.assertEqual(surface, self.rows[identifier]["word"])

    def test_literal_questions_do_not_become_interjections(self):
        for identifier, phrase in ((69, "a ver"), (272, "y qué"), (280, "qué tienes"), (281, "qué va"), (242, "por eso"), (3, "nada que ver")):
            words, i, _ = self.hit(identifier)
            tokens, seen = [], set()
            for k, word in enumerate(words):
                if id(word.parent) not in seen:
                    seen.add(id(word.parent))
                    tokens.append((word.parent.text.lower(), k, word.lemma.lower()))
            position = next(k for k, token in enumerate(tokens) if words[token[1]].parent is words[i].parent)
            with self.subTest(identifier=identifier):
                self.assertTrue(phrase_is_literal(words, tokens, position, phrase, {}))

    def test_first_dictionary_pronominal_gloss_is_never_guessed(self):
        words, i, surface = self.hit(488)
        result = clitic_label(words, i, surface, "es", {"poner": "turn on an appliance"}, self.rows[488]["reflexive_decisions"])
        self.assertEqual(result["value"], "ponerse")
        self.assertEqual(result["gloss"], "")

    def test_passive_and_explicit_reciprocal_and_reflexive_are_distinct(self):
        for identifier, expected in ((498, "passive_se"), (477, "reciprocal"), (495, "reflexive")):
            words, i, surface = self.hit(identifier)
            result = clitic_label(words, i, surface, "es", {}, self.rows[identifier]["reflexive_decisions"])
            self.assertEqual(result["value"], expected)

    def test_no_se_policy_cannot_produce_a_reflexive_claim(self):
        words, i, surface = self.hit(481)
        result = clitic_label(words, i, surface, "es", {"contar": "tell oneself"}, self.rows[481]["reflexive_decisions"])
        self.assertEqual(result["value"], "object_pron")

    def test_entry_note_does_not_erase_a_different_valid_sense(self):
        from gloss_filter import Glosses
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dictionary.jsonl"
            senses = [{"glosses": ["Used other than figuratively or idiomatically: see cada, vez."]}, {"glosses": ["every time"]}]
            path.write_text(json.dumps({"word": "cada vez", "senses": senses}) + "\n")
            glosses = Glosses(path)
            self.assertEqual(glosses.senses(senses), ["every time"])
            self.assertEqual(glosses.clean([g for s in senses for g in s["glosses"]]), [])


if __name__ == "__main__":
    unittest.main()
