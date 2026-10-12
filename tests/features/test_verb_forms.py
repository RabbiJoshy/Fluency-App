import unittest
from fluency.features.verb_forms import signatures, read_verb_forms, compatible_forms


class VerbFormTests(unittest.TestCase):
    def test_finite_forms_need_matching_person_number_tense_and_mood(self):
        first = signatures(['first-person', 'singular', 'present', 'indicative', 'form-of'])
        third = signatures(['third-person', 'singular', 'present', 'indicative', 'form-of'])
        past = signatures(['first-person', 'singular', 'preterite', 'indicative', 'form-of'])
        self.assertTrue(first)
        self.assertFalse(first & third)
        self.assertFalse(first & past)
        self.assertFalse(first & signatures(['infinitive']))

    def test_personal_infinitives_and_undeclared_forms_are_retained(self):
        self.assertEqual(signatures(['infinitive', 'first-person', 'singular']), set())
        self.assertEqual(signatures(['form-of']), set())
        self.assertEqual(signatures(['participle', 'past']), set())

    def test_dictionary_forms_supply_base_and_inflected_evidence(self):
        entries = [{'word': 'hablar', 'pos': 'verb', 'forms': [{'form': 'hablar', 'tags': ['infinitive']}], 'senses': []},
                   {'word': 'hablo', 'pos': 'verb', 'senses': [{'form_of': [{'word': 'hablar'}], 'tags': ['first-person', 'singular', 'present', 'indicative']}]}]
        forms = read_verb_forms(entries)
        self.assertTrue(compatible_forms(forms, forms, 'hablar', 'hablar', 'hablar', 'hablar'))
        self.assertFalse(compatible_forms(forms, forms, 'hablo', 'hablar', 'hablar', 'hablar'))
        self.assertFalse(compatible_forms(forms, forms, 'unknown', 'hablar', 'hablar', 'hablar'))

    def test_lexical_aspect_is_preserved_on_infinitives_and_finite_forms(self):
        def entries(aspect):
            return [{'word': 'verb', 'pos': 'verb', 'senses': [{'tags': [aspect]}],
                     'forms': [{'form': 'verb', 'tags': ['infinitive']},
                               {'form': 'finite', 'tags': ['first-person', 'singular', 'present']}]}]
        imperfective = read_verb_forms(entries('imperfective'))
        perfective = read_verb_forms(entries('perfective'))
        self.assertFalse(compatible_forms(imperfective, perfective, 'verb', 'verb', 'verb', 'verb'))
        self.assertFalse(compatible_forms(imperfective, perfective, 'finite', 'verb', 'finite', 'verb'))
