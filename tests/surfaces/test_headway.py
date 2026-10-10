import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from fluency.sense_menu.spanishdict import SpanishDictSenseMenuAdapter
from fluency.sense_menu.spanishdict_lemmas import SpanishDictLemmaRule, page_lemma_analyses
from fluency.sense_menu.kaikki import _semantic_senses, semantic_headword, KaikkiSenseMenuAdapter
from fluency.surfaces.lemma_revision import active_lemma_events, project_revision, REVISION_PROVIDER, stale_carried_analyses
from fluency.sense_menu.runner import _build_and_carry, SenseMenuRunError


def page(surface, target, kind='conjugation', inflection=''):
    return {'entry_lang': 'es', 'dictionary_analyses': [
        {'headword': surface, 'senses': [{'pos': 'VERB', 'translation': 'to do it'}]}],
        'possible_results': [{'headword': target, 'heuristic': kind, 'inflection_type': inflection}]}


def row(word, pos, targets=(), gloss=None):
    senses = [{'form_of': [{'word': t}], 'tags': ['form-of'], 'glosses': ['form of ' + t]} for t in targets]
    if gloss:
        senses.append({'glosses': [gloss], 'id': 'original-id-' + gloss})
    return {'word': word, 'pos': pos, 'senses': senses}


class HeadwayTests(unittest.TestCase):
    def test_sd_hay_and_clitic_keep_source_senses_and_ids(self):
        for surface, p in [('hay', page('hay', 'haber')),
                           ('hacerlo', page('hacerlo', 'hacer', 'inflection', 'infinitive + lo'))]:
            before = json.dumps(p)
            result = page_lemma_analyses(surface, p)
            self.assertEqual(result[0]['headword'], p['possible_results'][0]['headword'])
            self.assertEqual(result[0]['senses'], p['dictionary_analyses'][0]['senses'])
            self.assertEqual(result[0]['_source_headword'], surface)
            self.assertEqual(json.dumps(p), before)
            found = SpanishDictLemmaRule({}).resolve(surface, p)
            self.assertNotIn(surface, found.lemma_names)
        self.assertEqual(result[0]['_lemma_correction']['attached_pronouns'], ['lo'])

    def test_sd_noun_homograph_and_ambiguous_verbs_are_not_collapsed(self):
        p = page('cura', 'curar')
        p['dictionary_analyses'][0]['senses'].append({'pos': 'NOUN', 'translation': 'priest'})
        self.assertEqual([a['headword'] for a in page_lemma_analyses('cura', p)], ['curar', 'cura'])
        p['possible_results'].append({'headword': 'another', 'heuristic': 'conjugation'})
        self.assertEqual([a['headword'] for a in page_lemma_analyses('cura', p)], ['cura'])

    def test_sd_normalization_fixes_retained_menu_and_keeps_legacy_sense_id(self):
        adapter = object.__new__(SpanishDictSenseMenuAdapter)
        adapter.lemma_rule = None
        adapter.surface_cache = {'hacerlo': page('hacerlo', 'hacer', 'inflection', 'infinitive + lo')}
        adapter.normalized_menu = {'hacerlo': []}
        raw = adapter.surface_cache['hacerlo']['dictionary_analyses']
        raw[0]['senses'][0]['_legacy_sense_id'] = 'stable-source-id'
        raw += [{'headword': 'hacer de cuenta', 'senses': [{'pos': 'PHRASE', 'translation': 'pretend'}]}]
        result = adapter._normalize_card({'card_id': 'es-surface'}, 'hacerlo', raw)
        self.assertEqual([a.headword for a in result], ['hacer'])
        self.assertEqual(result[0].senses[0].sense_id, 'stable-source-id')
        self.assertEqual(result[0].provider_metadata['source_headword'], 'hacerlo')

    def test_sd_phrase_command_uses_mood_checked_host_and_preserves_sense_id(self):
        from fluency.sense_menu.spanishdict import _legacy_sense_ids
        reverse = {'di': [{'lemma': 'dar', 'mood': 'indicativo', 'person': '1s'},
                          {'lemma': 'decir', 'mood': 'imperativo', 'person': '2s'}],
                   'deja': [{'lemma': 'dejar', 'mood': 'imperativo', 'person': '2s'}]}
        rule = SpanishDictLemmaRule(reverse)
        for surface, lemma, pronoun in [('dime', 'decir', 'me'), ('déjalo', 'dejar', 'lo')]:
            p = {'entry_lang': 'es', 'dictionary_analyses': [{'headword': surface,
                 'senses': [{'pos': 'PHRASE', 'translation': 'hello', 'context': 'on the phone'}]}]}
            original = json.dumps(p)
            before = _legacy_sense_ids(surface, p['dictionary_analyses'][0]['senses'], set())
            a = page_lemma_analyses(surface, p, rule)[0]
            after = _legacy_sense_ids(surface, a['senses'], set())
            self.assertEqual(list(before), list(after))
            self.assertEqual(a['headword'], lemma)
            self.assertEqual(a['senses'][0]['pos'], 'VERB')
            self.assertEqual(a['_lemma_correction']['attached_pronouns'], [pronoun])
            self.assertEqual(rule.resolve(surface, p).lemma_names, [lemma])
            self.assertEqual(json.dumps(p), original)
        reverse['di'].append({'lemma': 'other', 'mood': 'imperativo', 'person': '2s'})
        p['dictionary_analyses'][0]['headword'] = 'dime'
        self.assertEqual(page_lemma_analyses('dime', p, SpanishDictLemmaRule(reverse)), p['dictionary_analyses'])

    def test_person_label_moves_verb_senses_and_keeps_distinct_verbs_and_nouns(self):
        p = page('fuimos', 'ir')
        p['possible_results'][0]['translation'] = 'we went'
        p['possible_results'].append({'headword': 'ser', 'heuristic': 'conjugation', 'translation': 'we were'})
        p['dictionary_analyses'][0]['senses'] = [
            {'pos': 'PHRASE', 'context': 'first person plural', 'translation': 'we went'},
            {'pos': 'PHRASE', 'context': 'first person plural', 'translation': 'we were'}]
        reverse = {'fuimos': [{'lemma': l, 'mood': 'indicativo', 'person': '1p'} for l in ('ser', 'ir')]}
        rule = SpanishDictLemmaRule(reverse)
        result = page_lemma_analyses('fuimos', p, rule)
        self.assertEqual([(a['headword'], a['senses'][0]['translation']) for a in result],
                         [('ir', 'we went'), ('ser', 'we were')])
        self.assertEqual(set(rule.resolve('fuimos', p).lemma_names), {'ser', 'ir'})
        p = page('sal', 'salir')
        p['dictionary_analyses'][0]['senses'] = [
            {'pos': 'PHRASE', 'context': 'imperative; second person singular', 'translation': 'leave'},
            {'pos': 'NOUN', 'translation': 'salt'}]
        rule = SpanishDictLemmaRule({'sal': [{'lemma': 'salir', 'mood': 'imperativo', 'person': '2s'}]})
        result = page_lemma_analyses('sal', p, rule)
        self.assertEqual([(a['headword'], a['senses'][0]['pos']) for a in result],
                         [('salir', 'VERB'), ('sal', 'NOUN')])

    def test_person_and_mood_mismatch_abstains_and_exact_verbal_homograph_survives(self):
        p = page('vete', 'vetar')
        p['dictionary_analyses'][0]['senses'] = [
            {'pos': 'PHRASE', 'context': 'imperative; second person singular', 'translation': 'go away'}]
        rule = SpanishDictLemmaRule({'vete': [{'lemma': 'vetar', 'person': '3s', 'mood': 'subjuntivo'}]})
        self.assertEqual(page_lemma_analyses('vete', p, rule), p['dictionary_analyses'])
        p = page('di', 'decir')
        p['dictionary_analyses'][0]['senses'] = [
            {'pos': 'PHRASE', 'context': 'imperative; second person singular', 'translation': 'say'}]
        rule = SpanishDictLemmaRule({'di': [{'lemma': 'decir', 'person': '2s', 'mood': 'imperativo'},
                                          {'lemma': 'dar', 'person': '1s', 'mood': 'indicativo'}]})
        self.assertEqual(set(rule.resolve('di', p).lemma_names), {'dar', 'decir'})

    def test_explicit_verb_relation_beats_coincidental_clitic_split(self):
        p = page('piense', 'pensar')
        p['dictionary_analyses'][0]['senses'] = [
            {'pos': 'PHRASE', 'context': 'third person singular; subjunctive', 'translation': 'think'}]
        rule = SpanishDictLemmaRule({'piense': [{'lemma': 'pensar', 'person': '3s', 'mood': 'subjuntivo'}],
                                     'píen': [{'lemma': 'piar', 'person': '3p', 'mood': 'imperativo'}]})
        self.assertEqual(rule.enclitic_split('piense')['lemma'], 'piar')
        result = page_lemma_analyses('piense', p, rule)
        self.assertEqual([a['headword'] for a in result], ['pensar'])
        self.assertEqual(set(rule.resolve('piense', p).lemma_names), {'pensar'})

    def test_reflexive_entry_nested_on_base_page_is_available_and_preserved(self):
        from fluency.sense_menu.spanishdict_lemmas import entry_index, SpanishDictHeadwordSource
        command = {'entry_lang': 'es', 'dictionary_analyses': [{'headword': 'acuérdate',
                   'senses': [{'pos': 'PHRASE', 'translation': 'remember'}]}]}
        cache = {'acuérdate': command, 'acordar': {'dictionary_analyses': [
            {'headword': 'acordar', 'senses': [{'translation': 'agree', 'pos': 'VERB'}]},
            {'headword': 'acordarse', 'senses': [{'translation': 'remember', 'pos': 'VERB'}]}]}}
        rule = SpanishDictLemmaRule({'acuerda': [{'lemma': 'acordar', 'mood': 'imperativo', 'person': '2s'}]},
                                   frozenset(entry_index(cache)))
        self.assertEqual(rule.resolve('acuérdate', command).lemma_names, ['acordar', 'acordarse'])
        self.assertEqual(page_lemma_analyses('acuérdate', command, rule)[0]['headword'], 'acordarse')
        self.assertTrue(SpanishDictHeadwordSource(rule, cache, {}).has_entry('acordarse'))

    def test_reviewed_pos_is_explicit_and_survives_projection(self):
        row = {'part_of_speech': ['PHRASE'], 'supply': {'eligible_sentence_ids': ['frozen']}}
        evidence = {'provider': REVISION_PROVIDER, 'primary': 'decir',
                    'analyses': [{'lemma': 'decir', 'pos': ['VERB']}], 'approved_pos': ['VERB']}
        self.assertEqual(project_revision(row, evidence)['part_of_speech'], ['VERB'])
        evidence.pop('approved_pos')
        self.assertEqual(project_revision(row, evidence)['part_of_speech'], ['PHRASE'])

    def test_manual_lemma_and_pos_survive_source_revision_and_later_import(self):
        manual = {'reason_code': 'lemma_resolved', 'evidence': {'provider': 'hand-written',
                  'lemmas': ['chosen'], 'pos': ['VERB']}}
        revision = {'reason_code': 'lemma_resolved', 'evidence': {'provider': REVISION_PROVIDER}}
        legacy = {'reason_code': 'lemma_is_headword', 'evidence': {'provider': 'wiktionary-self'}}
        self.assertEqual(active_lemma_events([legacy, manual, revision, legacy]), [manual])

    def test_manual_heads_without_pos_keep_compatible_reviewed_pos(self):
        from fluency.surfaces.lemma_revision import compatible_reviewed_pos
        manual = {'reason_code': 'lemma_resolved', 'evidence': {'provider': 'hand-written', 'lemmas': ['decir']}}
        source = {'evidence': {'provider': REVISION_PROVIDER, 'lemmas': ['decir'], 'approved_pos': ['VERB']}}
        self.assertEqual(compatible_reviewed_pos([manual, source], ['decir']), ['VERB'])
        self.assertIsNone(compatible_reviewed_pos([manual, source], ['other']))
        manual['evidence']['pos'] = ['NOUN']
        self.assertEqual(compatible_reviewed_pos([manual, source], ['decir']), ['NOUN'])

    def test_wiktionary_form_pages_are_not_headwords_but_homographs_are(self):
        self.assertFalse(_semantic_senses(row('és', 'verb', ['ser'])))
        r = row('vamos', 'verb', ['ir'], "let's")
        self.assertEqual(semantic_headword(r), 'ir')
        self.assertEqual(semantic_headword(row('vamos', 'intj', gloss='come on')), 'vamos')
        self.assertEqual(semantic_headword(row('conta', 'noun', gloss='account')), 'conta')
        self.assertEqual(semantic_headword(row('conta', 'verb', ['contar'])), 'contar')
        self.assertEqual(semantic_headword(row('foi', 'verb', ['ser', 'ir'], 'ambiguous')), 'foi')
        malformed = row('és', 'verb', ['ser'])
        malformed['senses'][0].pop('tags')
        self.assertFalse(_semantic_senses(malformed))

    def test_wiktionary_builder_moves_specialised_verb_sense_without_losing_it(self):
        adapter = object.__new__(KaikkiSenseMenuAdapter)
        adapter.language_code = 'pt'
        adapter.language_policy = {'display': {}}
        rows = {'vamos': [row('vamos', 'verb', ['ir'], "let's"), row('vamos', 'intj', gloss='come on')],
                'ir': [row('ir', 'verb', gloss='go')]}
        analyses = adapter._card_analyses({'card_id': 'pt-surface'}, 'vamos', ['ir', 'vamos'], rows,
            {'ir': ('vamos', 'ir'), 'vamos': ('vamos',)}, {'ir': {'verb'}, 'vamos': None}, {})
        self.assertEqual({(a.headword, a.part_of_speech) for a in analyses}, {('ir', 'verb'), ('vamos', 'intj')})
        specialised = next(s for a in analyses for s in a.senses if s.sense_id == "original-id-let's" and s.translation == "let's")
        self.assertEqual(specialised.provider_metadata['source_headword'], 'vamos')

    def test_revision_survives_later_legacy_import_and_preserves_supply(self):
        old = {'reason_code': 'lemma_resolved', 'evidence': {'provider': 'spanishdict-surface-cache', 'lemmas': ['hay']}}
        evidence = {'provider': REVISION_PROVIDER, 'analyses': [{'lemma': 'haber', 'pos': ['VERB']}], 'primary': 'haber'}
        revision = {'reason_code': 'lemma_resolved', 'evidence': evidence}
        self.assertEqual(active_lemma_events([old, revision, old]), [revision])
        supply = {'eligible_sentence_ids': ['frozen-id']}
        original = {'rank': 10, 'verdict': 'keep', 'supply': supply}
        projected = project_revision(original, evidence)
        self.assertIs(projected['supply'], supply)
        self.assertEqual(projected['lemmas'], ['haber'])
        self.assertEqual(original, {'rank': 10, 'verdict': 'keep', 'supply': supply})

    def test_observer_does_not_resurrect_form_only_or_case_collision_heads(self):
        spec = importlib.util.spec_from_file_location('headway_observer', Path(__file__).resolve().parents[2] / 'scripts/observe_lemmas.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rows.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in [row('és', 'verb', ['ser']),
                row('conta', 'noun', gloss='account'), row('conta', 'verb', ['contar']),
                row('NO', 'noun', gloss='abbreviation')]))
            forms, heads, _ = module.wiktionary_forms(path)
        self.assertEqual(forms['és'], {'ser'})
        self.assertNotIn('és', heads)
        self.assertIn('conta', heads)
        self.assertIn('NO', heads)
        self.assertNotIn('no', heads)

    def test_carry_guard_detects_old_verb_analysis_but_preserves_interjection(self):
        card = {'surface_form': 'vamos', 'analyses': [
            {'headword': 'vamos', 'part_of_speech': 'verb'},
            {'headword': 'vamos', 'part_of_speech': 'intj'},
            {'headword': 'ir', 'part_of_speech': 'verb'}]}
        revision = {'lemma_analyses': [{'lemma': 'ir', 'provenance': 'wiktionary-row-form-of'}],
                    'lemma_revision': {'removed_lemmas': []}}
        self.assertEqual(stale_carried_analyses(card, revision), [card['analyses'][0]])
        self.assertEqual(stale_carried_analyses(card, {}), [])
        card['analyses'][0]['source_adapter'] = 'declared-gloss/v1'
        self.assertEqual(stale_carried_analyses(card, revision), [])

    def test_unverified_legacy_candidate_never_becomes_a_lookup_lemma(self):
        result = project_revision({'supply': {'frozen': True}}, {
            'provider': REVISION_PROVIDER, 'primary': 'contarme',
            'analyses': [{'lemma': 'contarme', 'trust': 'unverified', 'pos': []}]})
        self.assertIsNone(result['lemma'])
        self.assertEqual(result['lemmas'], [])
        self.assertEqual(result['lemma_alternates'][0]['trust'], 'unverified')

    def test_stage_refuses_stale_carry_before_building_anything(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'runs/es/speech/prior/stages/02_sense_menu/output'
            output.mkdir(parents=True)
            (output / 'sense-menu.json').write_text(json.dumps({'cards': [{
                'surface_form': 'hay', 'analyses': [{'headword': 'hay', 'part_of_speech': 'VERB'}]}]}))
            (output / 'report.json').write_text('{}')
            ledger = root / 'raw/surfaces/es/ledger.json'
            ledger.parent.mkdir(parents=True)
            ledger.write_text(json.dumps({'surfaces': {'hay': {
                'lemma_revision': {'removed_lemmas': ['hay']}}}}))
            with self.assertRaisesRegex(SenseMenuRunError, 'superseded source analyses.*hay'):
                _build_and_carry(SimpleNamespace(root=root), None, [], snapshot_id='snapshot',
                                 language='es', mode='speech', resolved=set(), carry_run='prior')
