"""Decision 0034: verb-led expressions match in any inflection; frozen ones stay exact."""
import unittest

from fluency.wsd.multiword import (ExpressionInflector, expression_already_on_menu, index_multiword_senses,
                                   multiword_matches)

PARADIGM = {
    form: [[lemma, "x", "x", "", ""]]
    for lemma, forms in {
        "ficar": ["ficar", "fico", "ficou", "fique", "ficamos"],
        "tomar": ["tomar", "toma", "tomou", "tomo"],
        "dar": ["dar", "dei", "deu", "di", "dio", "doy", "dando", "dar"],
        "echar": ["echar", "echo", "echas", "echamos", "echaba"],
        "querer": ["querer", "quer", "quero"],
        "saber": ["saber", "sé", "sei"],
    }.items()
    for form in forms
}
INVENTORY = {"mwes": {
    expression: {"attach_words": attach, "translations": [gloss], "corpus_freq": 5, "verdict": "keep"}
    for expression, attach, gloss in [
        ("ficar com", ["ficar", "com"], "to keep"),
        ("tomar conta", ["tomar", "conta"], "to look after"),
        ("dar-se conta", ["dar", "conta"], "to realise"),
        ("darse cuenta", ["dar", "cuenta"], "to realize"),
        ("echar de menos", ["echar", "menos"], "to miss"),
        ("quer dizer", ["quer", "dizer"], "that is"),
        ("no sé", ["sé"], "I don't know"),
    ]
}}


class InflectedExpressionTests(unittest.TestCase):
    def setUp(self):
        self.inflector = ExpressionInflector(PARADIGM)
        self.index = index_multiword_senses(INVENTORY)

    def found(self, surface, sentence):
        return {(entry.expression, sentence[span[0]:span[1]])
                for entry, span in multiword_matches(surface_form=surface, sentence=sentence,
                                                     index=self.index, inflector=self.inflector)}

    def test_inflected_head_found_from_its_own_card(self):
        self.assertEqual(self.found("fico", "Eu fico com sono depois de comer."), {("ficar com", "fico com")})
        self.assertEqual(self.found("tomou", "Ela tomou conta das crianças."), {("tomar conta", "tomou conta")})
        self.assertEqual(self.found("echo", "Te echo mucho de menos."), {("echar de menos", "echo mucho de menos")})

    def test_moved_pronouns(self):
        self.assertEqual(self.found("di", "Me di cuenta tarde."), {("darse cuenta", "Me di cuenta")})
        self.assertEqual(self.found("cuenta", "No me di cuenta."), {("darse cuenta", "me di cuenta")})
        self.assertEqual(self.found("dei-me", "Dei-me conta do erro."), {("dar-se conta", "Dei-me conta")})
        self.assertEqual(self.found("dei", "Não me dei conta."), {("dar-se conta", "me dei conta")})
        self.assertEqual(self.found("dándome", "Estoy dándome cuenta ahora."), {("darse cuenta", "dándome cuenta")})

    def test_reflexive_needs_its_pronoun(self):
        self.assertEqual(self.found("dio", "Dio cuenta de todo al juez."), set())

    def test_no_match_across_punctuation_or_wider_gaps(self):
        self.assertEqual(self.found("fico", "Eu fico, com certeza."), set())
        self.assertEqual(self.found("toma", "Toma a sopa toda conta."), set())
        self.assertEqual(self.found("ficou", "Ela ficou muito feliz com isso."), set())
        self.assertEqual(self.found("tomou", "Ela tomou de conta."), set())

    def test_frozen_forms_match_exactly(self):
        self.assertIsNone(self.inflector.head("quer dizer"))
        self.assertIsNone(self.inflector.head("no sé"))
        self.assertEqual(self.found("quer", "Isso quer dizer sim."), {("quer dizer", "quer dizer")})
        self.assertEqual(self.found("quero", "Eu quero dizer sim."), set())

    def test_expression_already_on_the_verbs_menu_is_not_offered(self):
        # Measured relabels (pilot 2026-10-26) are skipped; idioms the menu lacks are kept.
        self.assertTrue(expression_already_on_menu(["to have just"], ["to finish", "to have just"]))
        self.assertTrue(expression_already_on_menu(["to have to; must"], ["to have", "to have to"]))
        self.assertTrue(expression_already_on_menu(["to pay attention"], ["to pay (attention, respect etc.)"]))
        self.assertFalse(expression_already_on_menu(["to be worthwhile"], ["to be worth, valid or acceptable"]))
        self.assertFalse(expression_already_on_menu(["to mind; to look after; to take care"],
                                                    ["to take; to receive", "to take into the body"]))

    def test_without_inflector_behaviour_is_unchanged(self):
        found = multiword_matches(surface_form="fico", sentence="Eu fico com sono.", index=self.index)
        self.assertEqual(found, ())


if __name__ == "__main__":
    unittest.main()
