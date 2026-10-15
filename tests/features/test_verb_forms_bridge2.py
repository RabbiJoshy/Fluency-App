import unittest
from fluency.features.verb_forms import signatures, read_verb_forms, compatible_forms


class VerbFormsBridge2Tests(unittest.TestCase):
    def test_czech_polish_present_agreement(self):
        # Czech vidím vs Polish widzę (both 1sg pres impf)
        cs_vidim = signatures(['first-person', 'form-of', 'present', 'singular'])
        pl_widze = signatures(['first-person', 'form-of', 'present', 'singular'])
        self.assertTrue(cs_vidim)
        self.assertEqual(cs_vidim, pl_widze)

        # Polish widźmy is 1pl imperative, must NOT match 1sg indicative
        pl_widzmy = signatures(['first-person', 'form-of', 'plural', 'imperative'])
        self.assertFalse(cs_vidim & pl_widzmy)

    def test_czech_polish_past_l_form_agreement(self):
        # Czech viděl (active past participle masc sg) vs Polish widział (3sg past masc)
        cs_videl = signatures(['active', 'form-of', 'masculine', 'participle', 'past', 'singular'])
        pl_widzial = signatures(['form-of', 'masculine', 'past', 'singular', 'third-person'])
        self.assertTrue(cs_videl)
        self.assertEqual(cs_videl, pl_widzial)

        # Gender mismatch: Czech feminine viděla vs Polish masculine widział
        cs_videla = signatures(['active', 'form-of', 'feminine', 'participle', 'past', 'singular'])
        self.assertFalse(cs_videla & pl_widzial)

        # Polish widać is impersonal/predicative, must NOT match finite past
        pl_widac = signatures(['predicative', 'form-of'])
        self.assertFalse(cs_videl & pl_widac)

    def test_spanish_portuguese_form_agreement(self):
        # Spanish escribo vs Portuguese escrevo (both 1sg pres ind)
        es_escribo = signatures(['first-person', 'form-of', 'indicative', 'present', 'singular'])
        pt_escrevo = signatures(['first-person', 'form-of', 'indicative', 'present', 'singular'])
        self.assertTrue(es_escribo)
        self.assertEqual(es_escribo, pt_escrevo)

        # Spanish escribió (3sg pret) must NOT match Portuguese escrevo (1sg pres) or infinitive
        es_escribio = signatures(['form-of', 'indicative', 'preterite', 'singular', 'third-person'])
        pt_escrever = signatures(['infinitive'])
        self.assertFalse(es_escribio & pt_escrevo)
        self.assertFalse(es_escribio & pt_escrever)

        # Portuguese escreveu (3sg pret) matches Spanish escribió (3sg pret)
        pt_escreveu = signatures(['form-of', 'indicative', 'preterite', 'singular', 'third-person'])
        self.assertEqual(es_escribio, pt_escreveu)

    def test_infinitives_match_infinitives(self):
        inf_es = signatures(['infinitive'])
        inf_pt = signatures(['infinitive'])
        self.assertEqual(inf_es, inf_pt)

    def test_read_verb_forms_czech_and_polish_enrichment(self):
        entries_cs = [
            {'word': 'vidět', 'pos': 'verb', 'senses': [{'tags': ['imperfective']}],
             'forms': [{'form': 'vidět', 'tags': ['infinitive']},
                       {'form': 'vidím', 'tags': ['first-person', 'present', 'singular']},
                       {'form': 'viděl', 'tags': ['active', 'masculine', 'participle', 'past', 'singular']}]}
        ]
        entries_pl = [
            {'word': 'widzieć', 'pos': 'verb', 'senses': [{'tags': ['imperfective']}],
             'forms': [{'form': 'widzieć', 'tags': ['infinitive']},
                       {'form': 'widzę', 'tags': ['first-person', 'present', 'singular']},
                       {'form': 'widział', 'tags': ['masculine', 'past', 'singular', 'third-person']},
                       {'form': 'widźmy', 'tags': ['first-person', 'plural', 'imperative']}]}
        ]
        forms_cs = read_verb_forms(entries_cs)
        forms_pl = read_verb_forms(entries_pl)

        # 1sg present matches
        self.assertTrue(compatible_forms(forms_cs, forms_pl, 'vidím', 'vidět', 'widzę', 'widzieć'))
        # 1sg present does NOT match 1pl imperative
        self.assertFalse(compatible_forms(forms_cs, forms_pl, 'vidím', 'vidět', 'widźmy', 'widzieć'))
        # 3sg past masc matches
        self.assertTrue(compatible_forms(forms_cs, forms_pl, 'viděl', 'vidět', 'widział', 'widzieć'))
        # Infinitive matches infinitive
        self.assertTrue(compatible_forms(forms_cs, forms_pl, 'vidět', 'vidět', 'widzieć', 'widzieć'))
