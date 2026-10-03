"""Language-bound entry point to the shared closed-menu candidate engine.

The historical Spanish class contains the shared mechanics. This interface
requires linguistic callbacks so dictionary pipelines cannot accidentally use
its Spanish defaults. Existing Spanish profiles keep their original entry point.
"""
from dataclasses import replace
from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy
from fluency.wsd.grammar_gate import grammar_constraints, grammar_compatible
from fluency.wsd.candidate_policy import CandidatePreparation


class DictionaryCandidatePolicy(SpanishV5CandidatePolicy):
    method_id = 'dictionary-candidate-policy/v1'

    def __init__(self, *, language, sense_compatible, pos_is_orthogonal,
                 clitic_evidence, pronominal_base, has_clitic, surface_pos_constraints=None,
                 required_grammar_axes=(), **options):
        self.surface_pos_constraints = surface_pos_constraints or {}
        self.required_grammar_axes = frozenset(required_grammar_axes)
        options.setdefault("normalized_leaf_gates", True)
        options.setdefault("contextual_lemma_gate", True)
        super().__init__(language=language, sense_compatible=sense_compatible,
                         pos_is_orthogonal=pos_is_orthogonal,
                         clitic_evidence=clitic_evidence,
                         pronominal_base=pronominal_base, has_clitic=has_clitic,
                         **options)

    def prepare(self, *, sentence, surface_form, observed_pos, analyses, observed_grammar=None):
        grammar = observed_grammar or {}
        allowed = self.surface_pos_constraints.get(surface_form)
        constrained = []
        rejected = []
        common_noun = str(observed_pos or '').upper() in {'NOUN', 'PRON', 'DET', 'AUX', 'VERB'} and any(
            a.part_of_speech.casefold() != 'name' for a in analyses)
        for analysis in analyses:
            if common_noun and analysis.part_of_speech.casefold() == 'name':
                rejected.extend({'menu_analysis_id': analysis.menu_analysis_id, 'sense_id': s.sense_id,
                                 'reason': 'common_noun_pos_rejects_name'} for s in analysis.senses)
                continue
            if allowed is not None and analysis.part_of_speech.casefold() not in allowed:
                rejected.extend({'menu_analysis_id': analysis.menu_analysis_id, 'sense_id': s.sense_id,
                                 'reason': 'surface_grammatical_role'} for s in analysis.senses)
                continue
            leaves = []
            for leaf in analysis.senses:
                axes = grammar_constraints(leaf.specialist_features)
                # Surface redirects may attach person marks to articles. Only
                # semantic marks require person evidence; function always does.
                semantic_axes = grammar_constraints(f for f in leaf.specialist_features
                    if getattr(f, 'kind', None) != 'surface_mark')
                required = self.required_grammar_axes.intersection(semantic_axes)
                if analysis.part_of_speech.casefold() != 'pron':
                    required = required - {'person'}
                missing = required - grammar.keys()
                if missing or not grammar_compatible(leaf.specialist_features, grammar):
                    rejected.append({'menu_analysis_id': analysis.menu_analysis_id, 'sense_id': leaf.sense_id,
                                     'reason': 'missing_required_grammar' if missing else 'grammar_contradiction'})
                else:
                    leaves.append(leaf)
            if leaves:
                constrained.append(replace(analysis, senses=tuple(leaves)))
        if not constrained:
            return CandidatePreparation(analyses=(), evidence={'method_id': self.method_id,
                'reason': 'no_evidence_compatible_leaf', 'strict_rejected_leaf_refs': rejected})
        result = super().prepare(sentence=sentence, surface_form=surface_form, observed_pos=observed_pos,
                                 observed_grammar=grammar, analyses=tuple(constrained))
        return CandidatePreparation(analyses=result.analyses,
                                    evidence={**result.evidence, 'strict_rejected_leaf_refs': rejected})
