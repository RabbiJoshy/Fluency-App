import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fluency.speech.wsd_execute import (
    ExactTextGlossScorer,
    SPACY_POS_MODEL,
    _attached_companions,
    _is_conflicting_regional_leaf,
    _regional_register_penalty,
    _single_leaf_is_deterministic,
    _translation_overlap_bonus,
    detect_sentence_variety,
    occurrence_pos_tags,
)
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id


class FakeToken:
    def __init__(self, text, idx, pos, morph=None):
        self.text = text
        self.idx = idx
        self.pos_ = pos
        self.morph = SimpleNamespace(to_dict=lambda: dict(morph or {}))


class FakeModel:
    def __init__(self, documents):
        self.documents = documents
        self.batch_sizes = []

    def pipe(self, texts, batch_size):
        self.batch_sizes.append(batch_size)
        for text in texts:
            yield self.documents[text]


def work_item(
    card_id,
    surface,
    sentence_id,
    sentence,
    *,
    target_span=None,
    target_observed_form=None,
):
    card = {"card_id": card_id, "display_form": surface}
    if target_span is not None:
        card["target_span"] = target_span
    if target_observed_form is not None:
        card["target_observed_form"] = target_observed_form
    return (
        card,
        {},
        sentence_id,
        sentence,
        "",
    )


class SpeechOccurrencePOSTests(unittest.TestCase):
    def test_declared_one_sense_menu_bypasses_evidence_guard_wsd(self):
        card_id = "card_fi_" + "d" * 32
        analysis = MenuAnalysis(
            menu_analysis_id=build_analysis_id(
                card_id=card_id,
                source_adapter="declared-gloss/v1",
                source_analysis_key="fi-review-ettei",
            ),
            card_id=card_id,
            surface_form="ettei",
            headword="ettei",
            part_of_speech="X",
            source_adapter="declared-gloss/v1",
            source_analysis_key="fi-review-ettei",
            provider_metadata={},
            senses=(
                SenseLeaf(
                    sense_id="declared:fi-review-ettei#1",
                    translation="that ... not; so that ... not",
                    definition="",
                    source_reference="declared:fi-review-ettei#1",
                    provider_metadata={},
                ),
            ),
        )

        self.assertTrue(
            _single_leaf_is_deterministic(
                (analysis, analysis.senses[0]),
                profile_id="fi-v21-1",
                has_multiword_alternative=False,
                declared_single_leaf_is_fact=True,
            )
        )
        # Off unless the profile file opts in: shipped profiles keep their method.
        self.assertFalse(
            _single_leaf_is_deterministic(
                (analysis, analysis.senses[0]),
                profile_id="fi-v21-1",
                has_multiword_alternative=False,
            )
        )
        self.assertFalse(
            _single_leaf_is_deterministic(
                (analysis, analysis.senses[0]),
                profile_id="fi-v21-1",
                has_multiword_alternative=True,
                declared_single_leaf_is_fact=True,
            )
        )

    def test_one_leaf_menu_does_not_require_embeddings(self):
        card_id = "card_pt_" + "b" * 32
        source_adapter = "wiktionary-sense-menu/v1"
        source_analysis_key = "pt:olá:interjection:0"
        analysis = MenuAnalysis(
            menu_analysis_id=build_analysis_id(
                card_id=card_id,
                source_adapter=source_adapter,
                source_analysis_key=source_analysis_key,
            ),
            card_id=card_id,
            surface_form="olá",
            headword="olá",
            part_of_speech="interjection",
            source_adapter=source_adapter,
            source_analysis_key=source_analysis_key,
            provider_metadata={},
            senses=(
                SenseLeaf(
                    sense_id="hello",
                    translation="hello",
                    definition="greeting",
                    source_reference="kaikki:hello",
                    provider_metadata={},
                ),
            ),
        )

        scores = ExactTextGlossScorer({}).score("Olá!", (analysis,))

        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0].sense_id, "hello")

    def test_companion_must_belong_to_the_target_occurrence(self):
        target = FakeToken("estaba", 0, "AUX")
        talking = FakeToken("hablando", 7, "VERB")
        de = FakeToken("de", 16, "ADP")
        topic = FakeToken("política", 19, "NOUN")
        target.dep_, target.head = "aux", talking
        talking.dep_, talking.head = "ROOT", talking
        de.dep_, de.head = "case", topic
        topic.dep_, topic.head = "obj", talking
        self.assertNotIn("de", _attached_companions((target, talking, de, topic), target))

        copula = FakeToken("estaba", 0, "AUX")
        de2 = FakeToken("de", 7, "ADP")
        holiday = FakeToken("vacaciones", 10, "NOUN")
        copula.dep_, copula.head = "cop", holiday
        holiday.dep_, holiday.head = "ROOT", holiday
        de2.dep_, de2.head = "case", holiday
        self.assertIn("de", _attached_companions((copula, de2, holiday), copula))

    def test_unpinned_installed_model_revision_is_rejected(self):
        model = FakeModel({})
        model.meta = {"version": "9.9.9"}
        fake_spacy = SimpleNamespace(load=lambda _name: model)

        with patch.dict(sys.modules, {"spacy": fake_spacy}):
            with self.assertRaisesRegex(RuntimeError, "pinned revision"):
                occurrence_pos_tags(
                    (work_item("card_es_" + "z" * 32, "hola", "sentence_" + "z" * 32, "Hola."),)
                )

    def test_unique_occurrence_supplies_observed_pos_and_pinned_evidence(self):
        sentence = "Yo quiero ir."
        model = FakeModel(
            {
                sentence: (
                    FakeToken("Yo", 0, "PRON"),
                    FakeToken("quiero", 3, "VERB"),
                    FakeToken("ir", 10, "VERB"),
                )
            }
        )
        key = ("card_es_" + "a" * 32, "sentence_" + "1" * 32)

        observed, evidence = occurrence_pos_tags(
            (work_item(key[0], "quiero", key[1], sentence),), model=model
        )

        self.assertEqual(observed[key], "VERB")
        self.assertEqual(evidence[key]["status"], "observed")
        self.assertEqual(evidence[key]["occurrence_tags"], ["VERB"])
        self.assertEqual(evidence[key]["model_revision"], SPACY_POS_MODEL)
        self.assertEqual(model.batch_sizes, [1], "v7 pinned batch size 1; keep it the default")

    def test_frozen_pair_pos_is_not_sent_to_spacy(self):
        sentence = "Te tomo en serio."
        model = FakeModel({})
        key = ("card_es_" + "c" * 32, "sentence_" + "3" * 32)
        observed, evidence = occurrence_pos_tags(
            (work_item(key[0], "serio", key[1], sentence),),
            model=model,
            cached_by_surface={("serio", key[1]): "ADV"},
        )
        self.assertEqual(observed[key], "ADV")
        self.assertEqual(evidence[key]["source"], "prewsd-pairs")
        self.assertEqual(model.batch_sizes, [])

    def test_repeated_occurrences_with_conflicting_pos_do_not_guess(self):
        sentence = "Como pan como siempre."
        model = FakeModel(
            {
                sentence: (
                    FakeToken("Como", 0, "SCONJ"),
                    FakeToken("pan", 5, "NOUN"),
                    FakeToken("como", 9, "VERB"),
                    FakeToken("siempre", 14, "ADV"),
                )
            }
        )
        key = ("card_es_" + "b" * 32, "sentence_" + "2" * 32)

        observed, evidence = occurrence_pos_tags(
            (work_item(key[0], "como", key[1], sentence),), model=model
        )

        self.assertIsNone(observed[key])
        self.assertEqual(evidence[key]["status"], "ambiguous_repeated_occurrence")
        self.assertEqual(evidence[key]["occurrence_tags"], ["SCONJ", "VERB"])

    def test_person_number_and_mood_are_normalized_for_the_grammar_gate(self):
        sentence = "Ven aquí."
        model = FakeModel({
            sentence: (
                FakeToken(
                    "Ven", 0, "VERB",
                    {"Mood": "Imp", "Number": "Sing", "Person": "2"},
                ),
                FakeToken("aquí", 4, "ADV"),
            )
        })
        key = ("card_es_" + "e" * 32, "sentence_" + "5" * 32)

        _observed, evidence = occurrence_pos_tags(
            (work_item(key[0], "ven", key[1], sentence),), model=model
        )

        self.assertEqual(evidence[key]["observed_grammar"], {
            "mood": "imperative", "number": "singular", "person": "2",
        })

    def test_persisted_span_tags_an_elision_under_its_canonical_surface(self):
        sentence = "Voy pa' casa."
        model_sentence = "Voy para' casa."
        model = FakeModel(
            {
                model_sentence: (
                    FakeToken("Voy", 0, "AUX"),
                    FakeToken("para", 4, "ADP"),
                    FakeToken("casa", 10, "NOUN"),
                )
            }
        )
        key = ("card_es_" + "c" * 32, "sentence_" + "3" * 32)

        observed, evidence = occurrence_pos_tags(
            (
                work_item(
                    key[0],
                    "para",
                    key[1],
                    sentence,
                    target_span=(4, 6),
                    target_observed_form="pa",
                ),
            ),
            model=model,
        )

        self.assertEqual(observed[key], "ADP")
        self.assertEqual(evidence[key]["status"], "observed")
        self.assertEqual(evidence[key]["occurrence_tags"], ["ADP"])
        self.assertTrue(evidence[key]["canonicalized_target_for_model"])

    def test_apostrophe_elision_does_not_take_the_punctuation_pos(self):
        sentence = "'Toy lista."
        model_sentence = "estoy lista."
        model = FakeModel(
            {
                model_sentence: (
                    FakeToken("estoy", 0, "AUX"),
                    FakeToken("lista", 6, "ADJ"),
                )
            }
        )
        key = ("card_es_" + "d" * 32, "sentence_" + "4" * 32)

        observed, evidence = occurrence_pos_tags(
            (
                work_item(
                    key[0],
                    "estoy",
                    key[1],
                    sentence,
                    target_span=(0, 4),
                    target_observed_form="'Toy",
                ),
            ),
            model=model,
        )

        self.assertEqual(observed[key], "AUX")
        self.assertEqual(evidence[key]["occurrence_tags"], ["AUX"])
        self.assertTrue(evidence[key]["canonicalized_target_for_model"])

class TranslationOverlapTests(unittest.TestCase):
    def test_overlap_matches_irregular_verb_forms(self) -> None:
        leaf = SenseLeaf(
            sense_id="sense_spend",
            translation="to spend",
            definition="time",
            source_reference="wiktionary:spend",
            provider_metadata={},
        )
        bonus = _translation_overlap_bonus(leaf, "We spent the whole night talking.")
        self.assertEqual(bonus, 0.04)

    def test_overlap_matches_pronoun_expansions(self) -> None:
        leaf = SenseLeaf(
            sense_id="sense_you",
            translation="you",
            definition="",
            source_reference="wiktionary:you",
            provider_metadata={},
        )
        bonus = _translation_overlap_bonus(leaf, "Take care of yourself.")
        self.assertEqual(bonus, 0.04)

    def test_overlap_matches_conjunction_that(self) -> None:
        leaf_that = SenseLeaf(
            sense_id="sense_that",
            translation="that",
            definition="",
            source_reference="wiktionary:that",
            provider_metadata={},
        )
        leaf_because = SenseLeaf(
            sense_id="sense_because",
            translation="because",
            definition="",
            source_reference="wiktionary:because",
            provider_metadata={},
        )
        sentence = "I think that you need help."
        self.assertEqual(_translation_overlap_bonus(leaf_that, sentence), 0.04)
        self.assertEqual(_translation_overlap_bonus(leaf_because, sentence), 0.0)

    def test_regional_register_penalty_and_filtering(self) -> None:
        brazil_leaf = SenseLeaf(
            sense_id="sense_cê",
            translation="you",
            definition="",
            source_reference="wiktionary:cê",
            provider_metadata={"regions": ["Brazil"], "tags": ["colloquial", "informal"]},
        )
        portugal_leaf = SenseLeaf(
            sense_id="sense_se_refl",
            translation="yourself",
            definition="",
            source_reference="wiktionary:se",
            provider_metadata={"regions": ["Portugal"]},
        )
        proscribed_leaf = SenseLeaf(
            sense_id="sense_mim",
            translation="I",
            definition="nonstandard, highly proscribed",
            source_reference="wiktionary:mim",
            provider_metadata={"tags": ["proscribed", "nonstandard"], "qualifier": "highly proscribed"},
        )

        # In pt-PT:
        self.assertTrue(_is_conflicting_regional_leaf(brazil_leaf, "pt-PT"))
        self.assertFalse(_is_conflicting_regional_leaf(portugal_leaf, "pt-PT"))
        self.assertTrue(_is_conflicting_regional_leaf(proscribed_leaf, "pt-PT"))

        # Penalties:
        self.assertAlmostEqual(_regional_register_penalty(brazil_leaf, "pt-PT"), 0.06)
        self.assertAlmostEqual(_regional_register_penalty(portugal_leaf, "pt-PT"), 0.0)
        self.assertAlmostEqual(_regional_register_penalty(proscribed_leaf, "pt-PT"), 0.08)

    def test_sentence_variety_detection(self) -> None:
        # Brazilian cues: progressive gerund, proclisis, lexis, vocês
        self.assertEqual(detect_sentence_variety("Você está fazendo o quê?", target_word="fazendo"), "br")
        self.assertEqual(detect_sentence_variety("Me dá isso agora!", target_word="dá"), "br")
        self.assertEqual(detect_sentence_variety("Eu peguei o ônibus cedo.", target_word="ônibus"), "neutral") # ônibus excluded as target
        self.assertEqual(detect_sentence_variety("Você pegou o ônibus cedo.", target_word="pegou"), "br")

        # European cues: estar a + inf, enclisis, tu
        self.assertEqual(detect_sentence_variety("Está a fazer frio lá fora.", target_word="fazer"), "eu")
        self.assertEqual(detect_sentence_variety("Dá-me o livro, por favor.", target_word="Dá"), "eu")
        self.assertEqual(detect_sentence_variety("Tu tens a certeza?", target_word="tens"), "eu")

    def test_dynamic_regional_scoring_based_on_sentence_variety(self) -> None:
        brazil_leaf = SenseLeaf(
            sense_id="sense_liga_br",
            translation="to care (about)",
            definition="",
            source_reference="wiktionary:ligar",
            provider_metadata={"regions": ["Brazil"], "tags": ["colloquial"]},
        )

        # In pt-PT for a European/neutral sentence: penalized
        self.assertTrue(_is_conflicting_regional_leaf(brazil_leaf, "pt-PT", sentence_variety="eu"))
        self.assertAlmostEqual(_regional_register_penalty(brazil_leaf, "pt-PT", sentence_variety="eu"), 0.06)

        # In pt-PT for an authentic Brazilian sentence: NOT penalized, and not conflicting
        self.assertFalse(_is_conflicting_regional_leaf(brazil_leaf, "pt-PT", sentence_variety="br"))
        self.assertAlmostEqual(_regional_register_penalty(brazil_leaf, "pt-PT", sentence_variety="br"), 0.0)


if __name__ == "__main__":
    unittest.main()
