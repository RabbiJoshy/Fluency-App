import unittest

from fluency.sense_menu.canonical import choose, is_proper


def wikt(**kw):
    return {"provider_metadata": {"examples": list(kw["examples"])}}


class CanonicalExampleTests(unittest.TestCase):
    def test_a_quotation_is_not_a_use_example(self):
        self.assertFalse(is_proper(
            {"type": "quotation", "text": "Assim falou", "english": "Thus spoke",
             "ref": "Camoes"}))

    def test_a_collocation_is_a_pattern_not_a_sentence(self):
        self.assertFalse(is_proper(
            {"type": "example", "tags": ["collocation"],
             "text": "setkat se s nekym", "english": "to meet someone"}))

    def test_an_example_without_english_is_unusable_on_a_bilingual_card(self):
        self.assertFalse(is_proper({"type": "example", "text": "Que belo!"}))

    def test_exactly_one_is_returned_however_many_are_offered(self):
        sense = wikt(examples=[
            {"type": "example", "text": "a b c", "english": "x"},
            {"type": "example", "text": "d e f", "english": "y"},
            {"type": "example", "text": "g h i", "english": "z"},
        ])
        chosen = choose(sense)
        self.assertIsInstance(chosen, dict)
        self.assertIn(chosen["text"], {"a b c", "d e f", "g h i"})

    def test_marked_offsets_win_over_an_otherwise_identical_example(self):
        sense = wikt(examples=[
            {"type": "example", "text": "um dois tres", "english": "one two three"},
            {"type": "example", "text": "um dois tres", "english": "one two three",
             "bold_text_offsets": [[0, 2]]},
        ])
        self.assertEqual(choose(sense)["bold_text_offsets"], [[0, 2]])

    def test_an_unmarked_variety_is_preferred_to_a_regional_one(self):
        sense = wikt(examples=[
            {"type": "example", "text": "o comboio parte", "english": "the train leaves",
             "tags": ["Portugal"]},
            {"type": "example", "text": "o trem parte", "english": "the train leaves"},
        ])
        self.assertEqual(choose(sense)["text"], "o trem parte")

    def test_spanishdict_shape_is_read_without_knowing_the_provider(self):
        sense = {"provider_metadata": {"spanishdict": {"examples": [
            {"original": "Tenga en cuenta que es diferente.",
             "translated": "Note that it is different."}]}}}
        self.assertEqual(choose(sense)["translation"], "Note that it is different.")

    def test_a_sense_with_only_unusable_examples_gets_none(self):
        sense = wikt(examples=[{"type": "quotation", "text": "x", "english": "y"}])
        self.assertIsNone(choose(sense))


if __name__ == "__main__":
    unittest.main()
