"""v21: dictionary order confirms the gloss between analyses but cannot veto it.

Cases are the cards measured on the v15-mend and fi v12 releases: cs ty shipped
only ten "the, this, that" because Wiktionary lists ten first; fi missä lost
"where" to the tagger's POS and lemma gates before any scoring.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from fluency.core.identity import create_card_record
from fluency.wsd.bindings import pos_gate_for
from fluency.wsd.commit import CommitPolicy, cross_analysis_license, decide
from fluency.wsd.gloss_scoring import LeafScore
from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.wsd.runner import _order_vote_scores

REPO = Path(__file__).resolve().parents[2]
V21 = CommitPolicy(
    strategy="rank_agreement",
    unresolved_outcome="abstain",
    shared_translation_licenses_glosskey=True,
    cross_analysis_vote="gloss_margin",
    cross_analysis_margin=0.02,
)
V15 = CommitPolicy(
    strategy="rank_agreement",
    unresolved_outcome="abstain",
    shared_translation_licenses_glosskey=True,
)


def analysis(surface: str, headword: str, pos: str, senses, lang: str = "cs") -> MenuAnalysis:
    card = create_card_record(lang, surface)
    key = f"{lang}:{headword}:{pos}"
    return MenuAnalysis(
        menu_analysis_id=build_analysis_id(
            card_id=card.card_id, source_adapter="wiktionary-sense-menu/v1", source_analysis_key=key
        ),
        card_id=card.card_id,
        surface_form=surface,
        headword=headword,
        part_of_speech=pos,
        source_adapter="wiktionary-sense-menu/v1",
        source_analysis_key=key,
        senses=tuple(SenseLeaf(sid, translation, "", f"wikt:{sid}", {}) for sid, translation in senses),
        provider_metadata={},
    )


TEN = analysis("ty", "ten", "pron", (("ten1", "the, this, that"),))
TY = analysis("ty", "ty", "pron", (("ty1", "you"),))


def ref(item: MenuAnalysis, sense_id: str) -> tuple[str, str]:
    return (item.menu_analysis_id, sense_id)


class CrossAnalysisCommit(unittest.TestCase):
    def scores(self, ty: float, ten: float):
        return (LeafScore(TY.menu_analysis_id, "ty1", ty), LeafScore(TEN.menu_analysis_id, "ten1", ten))

    def test_v15_lets_alphabetical_order_veto_a_clear_gloss_winner(self):
        # "Ty jsi blázen": gloss says you, the first-listed analysis is ten.
        scores = self.scores(0.83, 0.76)
        decision = decide(scores, (TEN, TY), V15,
                          rank_agreement_refs=(ref(TEN, "ten1"), ref(TY, "ty1"), ref(TY, "ty1")),
                          raw_scores=scores)
        self.assertEqual(decision.level, "unresolved")

    def test_v21_commits_a_clear_gloss_winner_in_another_analysis(self):
        scores = self.scores(0.83, 0.76)
        order = _order_vote_scores(
            (LeafScore(TEN.menu_analysis_id, "ten1", 0.76), LeafScore(TY.menu_analysis_id, "ty1", 0.83)),
            scores[0], V21,
        )
        self.assertEqual([item.sense_id for item in order], ["ty1"])
        decision = decide(scores, (TEN, TY), V21,
                          rank_agreement_refs=(ref(TY, "ty1"), ref(TY, "ty1"), ref(TY, "ty1")),
                          raw_scores=scores, menu_first=ref(TEN, "ten1"))
        self.assertEqual((decision.level, decision.cross_analysis), ("leaf", "clear"))

    def test_v21_abstains_when_the_gloss_barely_prefers_another_analysis(self):
        scores = self.scores(0.770, 0.760)
        decision = decide(scores, (TEN, TY), V21,
                          rank_agreement_refs=(ref(TY, "ty1"), ref(TY, "ty1"), ref(TY, "ty1")),
                          raw_scores=scores, menu_first=ref(TEN, "ten1"))
        self.assertEqual((decision.level, decision.cross_analysis), ("unresolved", "contested"))

    def test_order_confirms_a_gloss_winner_that_is_listed_first(self):
        # que CCONJ vs PRON, querer vs quererse: split entries of one word where
        # order and gloss agree. v15 published these; a margin must not block them.
        conj = analysis("que", "que", "CCONJ", (("c1", "that"),), lang="es")
        pron = analysis("que", "que", "PRON", (("p1", "which"),), lang="es")
        scores = (LeafScore(conj.menu_analysis_id, "c1", 0.801), LeafScore(pron.menu_analysis_id, "p1", 0.800))
        refs = (ref(conj, "c1"), ref(conj, "c1"), ref(conj, "c1"))
        confirmed = decide(scores, (conj, pron), V21, rank_agreement_refs=refs, raw_scores=scores,
                           menu_first=ref(conj, "c1"))
        overriding = decide(scores, (pron, conj), V21, rank_agreement_refs=refs, raw_scores=scores,
                            menu_first=ref(pron, "p1"))
        self.assertEqual((confirmed.level, confirmed.cross_analysis), ("leaf", "order_agrees"))
        self.assertEqual((overriding.level, overriding.cross_analysis), ("unresolved", "contested"))

    def test_a_line_the_v15_rule_publishes_is_published_unchanged(self):
        # dos NUM/ADJ "two" with a third, different entry close by: v15 publishes
        # at glosskey through the shared English; v21 must not re-examine it.
        adj = analysis("dos", "dos", "ADJ", (("a1", "two"),), lang="es")
        num = analysis("dos", "dos", "NUM", (("n1", "two"),), lang="es")
        noun = analysis("dos", "dos", "NOUN", (("x1", "deuce"),), lang="es")
        scores = (LeafScore(num.menu_analysis_id, "n1", 0.80), LeafScore(noun.menu_analysis_id, "x1", 0.795),
                  LeafScore(adj.menu_analysis_id, "a1", 0.79))
        v15 = decide(scores, (adj, num, noun), V15,
                     rank_agreement_refs=(ref(adj, "a1"), ref(num, "n1"), ref(num, "n1")))
        v21 = decide(scores, (adj, num, noun), V21,
                     rank_agreement_refs=(ref(num, "n1"), ref(num, "n1"), ref(num, "n1")),
                     raw_scores=scores, menu_first=ref(adj, "a1"))
        self.assertEqual(v15.level, "glosskey")
        self.assertEqual((v21.level, v21.cross_analysis), ("glosskey", "order_agrees"))

    def test_a_close_rival_with_the_same_english_commits_at_glosskey(self):
        vy = analysis("vámi", "vy", "pron", (("vy1", "you"),))
        ty = analysis("vámi", "ty", "pron", (("ty1", "you"),))
        scores = (LeafScore(vy.menu_analysis_id, "vy1", 0.80), LeafScore(ty.menu_analysis_id, "ty1", 0.79))
        self.assertEqual(cross_analysis_license(scores, (ty, vy), ref(vy, "vy1"), 0.02), "shared_translation")
        decision = decide(scores, (ty, vy), V21,
                          rank_agreement_refs=(ref(vy, "vy1"), ref(vy, "vy1"), ref(vy, "vy1")),
                          raw_scores=scores)
        self.assertEqual(decision.level, "glosskey")

    def test_order_still_votes_inside_one_analysis(self):
        two = analysis("ty", "ty", "pron", (("a", "you"), ("b", "thou")))
        scores = (LeafScore(two.menu_analysis_id, "b", 0.9), LeafScore(two.menu_analysis_id, "a", 0.8))
        decision = decide(scores, (two,), V21,
                          rank_agreement_refs=(ref(two, "a"), ref(two, "b"), ref(two, "b")),
                          raw_scores=scores)
        self.assertEqual(decision.level, "tuple")

    def test_policy_rejects_an_unknown_vote(self):
        with self.assertRaises(ValueError):
            CommitPolicy(cross_analysis_vote="alphabet")


class SelfReadingSurvivesTheGates(unittest.TestCase):
    def test_missa_keeps_where_against_a_pron_tag_and_mika_lemma(self):
        mika = analysis("missä", "mikä", "pron", (("m1", "what, which"),), lang="fi")
        missa = analysis("missä", "missä", "adv", (("w1", "where"),), lang="fi")
        compatible, orthogonal = pos_gate_for("fi")

        def prepare(keep):
            return SpanishV5CandidatePolicy(
                language="fi", constraint_mode="filter", sense_compatible=compatible,
                pos_is_orthogonal=orthogonal, keep_self_reading_pos=keep,
            ).prepare(sentence="Missä olet?", surface_form="missä", observed_pos="PRON",
                      observed_grammar={"lemma": "mikä"}, analyses=(mika, missa))

        before = prepare(frozenset())
        after = prepare(frozenset({"adv"}))
        self.assertEqual(before.analyses, (mika,))
        self.assertEqual(after.analyses, (mika, missa))
        self.assertEqual(after.evidence["self_reading_restored_analysis_ids"], [missa.menu_analysis_id])

    def test_other_headwords_and_open_classes_stay_gated(self):
        voida = analysis("voi", "voida", "verb", (("v1", "can"),), lang="fi")
        voi = analysis("voi", "voi", "noun", (("n1", "butter"),), lang="fi")
        compatible, orthogonal = pos_gate_for("fi")
        prepared = SpanishV5CandidatePolicy(
            language="fi", constraint_mode="filter", sense_compatible=compatible,
            pos_is_orthogonal=orthogonal, keep_self_reading_pos=frozenset({"adv", "intj"}),
        ).prepare(sentence="Voit mennä.", surface_form="voi", observed_pos="VERB",
                  observed_grammar={"lemma": "voida"}, analyses=(voida, voi))
        self.assertEqual(prepared.analyses, (voida,))


class WiktionaryPostpositions(unittest.TestCase):
    def test_an_adp_tag_matches_a_finnish_postposition(self):
        compatible, _ = pos_gate_for("fi")
        self.assertTrue(compatible("postp", "ADP"))
        self.assertTrue(compatible("prep", "ADP"))
        self.assertFalse(compatible("noun", "ADP"))


class V21Profiles(unittest.TestCase):
    def test_every_v21_profile_declares_the_gloss_margin_vote_and_abstains(self):
        for lang in ("es", "pt", "cs", "fi"):
            profile = json.loads((REPO / f"config/wsd/models/{lang}-v21-1.json").read_text())
            self.assertEqual(profile["profile_id"], f"{lang}-v21-1")
            self.assertEqual(profile["commit"]["cross_analysis"]["vote"], "gloss_margin")
            self.assertEqual(profile["commit"]["cross_analysis"]["margin"], 0.02)
            self.assertEqual(profile["commit"]["cross_analysis"]["contested_outcome"], "abstain")
            # fi et won "and" over the negative verb; SpanishDict PHRASE rows let
            # está become "he's".
            for excluded in ("phrase", "conj"):
                self.assertNotIn(excluded, profile["constrain"]["keep_self_reading_pos"])


if __name__ == "__main__":
    unittest.main()
