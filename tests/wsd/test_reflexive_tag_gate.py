"""The fluency.reflexive tag narrows the pronominal family; abstentions keep v21."""

import unittest

from fluency.core.identity import create_card_record
from fluency.features import SpecialistFeature
from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy, reflexive_families
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id


def analysis(card_id, key, headword, senses, adapter="spanishdict-sense-menu/v1"):
    return MenuAnalysis(
        menu_analysis_id=build_analysis_id(card_id=card_id, source_adapter=adapter, source_analysis_key=key),
        card_id=card_id,
        surface_form="sentarte",
        headword=headword,
        part_of_speech="VERB",
        source_adapter=adapter,
        source_analysis_key=key,
        senses=tuple(senses),
        provider_metadata={},
    )


def feature(family, value):
    return SpecialistFeature.from_dict({"family": family, "kind": "tag", "value": value, "embedding_text": value})


def leaf(sense_id, translation, pronominal=False, transitive=False):
    features = ((feature("grammar", "pronominal"),) if pronominal else ()) + (
        (feature("construction", "transitive"),) if transitive else ())
    return SenseLeaf(sense_id, translation, "", f"t:{sense_id}", {}, specialist_features=features)


def policy(tag):
    return SpanishV5CandidatePolicy(reflexive_tag=lambda surface, sentence: tag)


class HeadwordFamilyTests(unittest.TestCase):
    """SpanishDict: X and Xse are separate headwords."""

    def setUp(self):
        card = create_card_record("es", "sentarte").card_id
        self.base = analysis(card, "sentar", "sentar", (leaf("a", "to seat"),))
        self.pron = analysis(card, "sentarse", "sentarse", (leaf("b", "to sit down"),))
        self.menu = (self.base, self.pron)

    def headwords(self, tag, sentence):
        prepared = policy(tag).prepare(sentence=sentence, surface_form="sentarte",
                                       observed_pos="VERB", analyses=self.menu)
        return {a.headword for a in prepared.analyses}, prepared.evidence

    def test_families(self):
        self.assertEqual(reflexive_families(self.menu), "headword")

    def test_se_firm_keeps_only_the_pronominal_headword(self):
        kept, evidence = self.headwords("SE_FIRM", "¿No vas a sentarte?")
        self.assertEqual(kept, {"sentarse"})
        self.assertEqual(evidence["reflexive_tag"], "SE_FIRM")

    def test_no_se_keeps_only_the_base_headword(self):
        kept, _ = self.headwords("NO_SE", "Voy a sentarte aquí.")
        self.assertEqual(kept, {"sentar"})

    def test_both_keeps_the_older_se_evidence(self):
        # v21's se-only gate reads "se" before the verb as pronominal; an
        # abstaining tag must not undo it.
        kept, evidence = self.headwords("BOTH", "Se sentarte")
        self.assertEqual(evidence["reflexive_tag"], "BOTH")
        self.assertEqual(kept, {"sentarse"})

    def test_no_tag_is_v21(self):
        prepared = SpanishV5CandidatePolicy().prepare(
            sentence="¿No vas a sentarte?", surface_form="sentarte", observed_pos="VERB", analyses=self.menu)
        self.assertNotIn("reflexive_tag", prepared.evidence)
        self.assertEqual(prepared.evidence["method_id"], "spanish-v5-candidate-policy/v1")


class SenseFamilyTests(unittest.TestCase):
    """Wiktionary: one headword, pronominal senses tagged."""

    def setUp(self):
        card = create_card_record("pt", "virou").card_id
        self.menu = (analysis(card, "virar", "virar", (
            leaf("a", "to turn (something)", transitive=True),
            leaf("b", "to get by", pronominal=True),
            leaf("c", "to turn around"),
        ), adapter="kaikki-sense-menu/v1"),)

    def senses(self, tag, sentence):
        prepared = policy(tag).prepare(sentence=sentence, surface_form="virou",
                                       observed_pos="VERB", analyses=self.menu)
        return {s.sense_id for a in prepared.analyses for s in a.senses}

    def test_families(self):
        self.assertEqual(reflexive_families(self.menu), "sense")

    def test_se_firm_drops_only_transitive_senses(self):
        # Wiktionary leaves "to turn around" untagged; a reflexive clitic
        # rules out only the transitive reading.
        self.assertEqual(self.senses("SE_FIRM", "Ele virou-se."), {"b", "c"})

    def test_no_se_drops_pronominal_senses(self):
        self.assertEqual(self.senses("NO_SE", "Se ele virar, vemos."), {"a", "c"})

    def test_both_with_a_clitic_keeps_every_sense(self):
        self.assertEqual(self.senses("BOTH", "Virou-se a mesa."), {"a", "b", "c"})


if __name__ == "__main__":
    unittest.main()
