import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/function_word_audit'))
from syntax_assignment_basic import (ARTICLE_PATTERNS, SUBJECT_PATTERNS,
                                     SUPPORTED_PATTERNS, decide_basic)


def fixture(lang, word, text, specs):
    """Specs: surface, head (1-based), POS, dependency, features."""
    nodes, cursor = [], 0
    for i, (surface, head, pos, dep, feats) in enumerate(specs, 1):
        start = text.index(surface, cursor)
        cursor = start + len(surface)
        nodes.append(dict(id=i, head=head, lemma=surface.casefold(), upos=pos,
                          deprel=dep, feats=feats,
                          token=dict(text=surface, start_char=start, end_char=cursor)))
    focus = next(n for n in nodes if n['token']['text'].casefold() == word)
    token = focus['token']
    return (dict(language=lang, word=word, sentence=text),
            dict(parser='synthetic-ud', sentence=text,
                 spans=[[token['start_char'], token['end_char']]], sentences=[nodes]))


def article(lang='pt', word='o', surface='O', noun='livro', gender='Masc', number='Sing'):
    indefinite = word in ('um', 'uma', 'un', 'una')
    feats = f'Definite={"Ind" if indefinite else "Def"}|PronType=Art|Gender={gender}|Number={number}'
    return fixture(lang, word, f'{surface} {noun} caiu.', [
        (surface, 2, 'DET', 'det', feats),
        (noun, 3, 'NOUN', 'nsubj', f'Gender={gender}|Number={number}'),
        ('caiu', 0, 'VERB', 'root', 'VerbForm=Fin')])


class BasicAssignmentTests(unittest.TestCase):
    def test_registry_matches_suite_formulas(self):
        suites = {l: json.loads((ROOT / f'app/data/grammar-words/{l}.json').read_text())
                  for l in ('pt', 'es')}
        for (lang, word), index in SUPPORTED_PATTERNS.items():
            relation = suites[lang][word]['relations'][index]
            slot = 'v' if word in SUBJECT_PATTERNS.get(lang, {}) else 'c'
            self.assertIn(f'fw-token-{slot}', relation['formulaHTML'])
            self.assertTrue(relation['formulaHTML'].startswith('<span class="fw-token-connector">'))

    def test_every_article_registered_with_agreement(self):
        for lang, words in ARTICLE_PATTERNS.items():
            for word, (pattern, gender, number) in words.items():
                row, obs = article(lang, word, word.capitalize(), 'casas' if number == 'Plur' else 'casa', gender, number)
                result = decide_basic(row, obs)
                self.assertEqual(result['status'], 'candidate', (lang, word, result))
                self.assertEqual(result['pattern'], pattern)
                self.assertEqual([c['slot'] for c in result['chunks']], ['connector', 'c'])

    def test_possessives_require_singular_nouns(self):
        for word in ('mi', 'su', 'tu'):
            row, obs = fixture('es', word, f'{word.capitalize()} casa existe.', [
                (word.capitalize(), 2, 'DET', 'det', 'Poss=Yes|PronType=Prs|Number=Sing'),
                ('casa', 3, 'NOUN', 'nsubj', 'Gender=Fem|Number=Sing'),
                ('existe', 0, 'VERB', 'root', 'VerbForm=Fin')])
            self.assertEqual(decide_basic(row, obs)['status'], 'candidate')
            obs['sentences'][0][1]['feats'] = 'Number=Plur'
            self.assertEqual(decide_basic(row, obs)['status'], 'abstain')

    def test_personal_subjects_and_accented_tu(self):
        for lang, words in SUBJECT_PATTERNS.items():
            for word, (_, person, number) in words.items():
                row, obs = fixture(lang, word, f'{word.capitalize()} canta.', [
                    (word.capitalize(), 2, 'PRON', 'nsubj', f'PronType=Prs|Person={person}|Number={number}'),
                    ('canta', 0, 'VERB', 'root', f'VerbForm=Fin|Person={person}|Number={number}')])
                self.assertEqual(decide_basic(row, obs)['status'], 'candidate')
                obs['sentences'][0][0]['deprel'] = 'obj'
                self.assertEqual(decide_basic(row, obs)['status'], 'abstain')

    def test_article_object_preposition_and_adjective_ambiguities(self):
        for lang, word in [('pt', 'o'), ('pt', 'a'), ('pt', 'os'), ('es', 'la'), ('es', 'los')]:
            row, obs = fixture(lang, word, f'{word} veo.', [
                (word, 2, 'PRON', 'obj', 'PronType=Prs'),
                ('veo', 0, 'VERB', 'root', 'VerbForm=Fin')])
            self.assertIsNone(decide_basic(row, obs))
            # A contradictory article-like dependency is uncertain, rather
            # than positive evidence for a different adapter.
            obs['sentences'][0][0]['deprel'] = 'det'
            self.assertEqual(decide_basic(row, obs)['status'], 'abstain')
        row, obs = article()
        obs['sentences'][0][1]['upos'] = 'ADJ'
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')
        row, obs = article(word='a', surface='A', gender='Fem')
        obs['sentences'][0][0].update(upos='ADP', deprel='case')
        self.assertIsNone(decide_basic(row, obs))
        obs['sentences'][0][0]['deprel'] = 'det'
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')

    def test_gender_number_and_missing_features_abstain(self):
        row, obs = article('es', 'el', 'El', 'agua')
        obs['sentences'][0][1]['feats'] = 'Gender=Fem|Number=Sing'
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')
        for feats in ('Gender=Masc|Number=Plur', None):
            row, obs = article()
            obs['sentences'][0][1]['feats'] = feats
            self.assertEqual(decide_basic(row, obs)['status'], 'abstain')

    def test_multiword_token_and_multiple_occurrences_abstain(self):
        row, obs = article()
        split = deepcopy(obs['sentences'][0][0])
        split.update(id=4, upos='ADP', deprel='case')
        obs['sentences'][0].append(split)
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')
        row, obs = article()
        obs['spans'].append([1, 2])
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')
        row['sentence'] += ' O outro.'
        obs['sentence'] = row['sentence']
        obs['spans'] = obs['spans'][:1]
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')

    def test_accent_surfaces_are_not_interchangeable(self):
        row, obs = fixture('es', 'tú', 'Tú cantas.', [
            ('Tú', 2, 'PRON', 'nsubj', 'PronType=Prs|Person=2|Number=Sing'),
            ('cantas', 0, 'VERB', 'root', 'VerbForm=Fin|Person=2|Number=Sing')])
        row['word'] = 'tu'
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')
        row, obs = article('es', 'el', 'El')
        row['sentence'] = obs['sentence'] = 'Él libro caiu.'
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')

    def test_noun_modifiers_and_source_offsets(self):
        row, obs = fixture('pt', 'uma', 'Uma casa antiga caiu.', [
            ('Uma', 2, 'DET', 'det', 'Definite=Ind|PronType=Art|Gender=Fem|Number=Sing'),
            ('casa', 4, 'NOUN', 'nsubj', 'Gender=Fem|Number=Sing'),
            ('antiga', 2, 'ADJ', 'amod', 'Gender=Fem|Number=Sing'),
            ('caiu', 0, 'VERB', 'root', 'VerbForm=Fin')])
        before = deepcopy(obs)
        result = decide_basic(row, obs)
        self.assertEqual(result['chunks'][1]['text'], 'casa antiga')
        for c in result['chunks']:
            self.assertEqual(c['text'], row['sentence'][c['start']:c['end']])
        self.assertEqual(obs, before)
        row['automatic_label'] = {'value': 'object_pron'}
        self.assertEqual(result, decide_basic(row, obs))

    def test_subject_auxiliary_and_intervening_material(self):
        row, obs = fixture('es', 'yo', 'Yo he cantado.', [
            ('Yo', 3, 'PRON', 'nsubj', 'PronType=Prs|Person=1|Number=Sing'),
            ('he', 3, 'AUX', 'aux', 'VerbForm=Fin|Person=1|Number=Sing'),
            ('cantado', 0, 'VERB', 'root', 'VerbForm=Part')])
        self.assertEqual(decide_basic(row, obs)['chunks'][1]['text'], 'he cantado')
        obs['sentences'][0][1]['feats'] = 'VerbForm=Fin|Person=2|Number=Sing'
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')
        row, obs = fixture('pt', 'eu', 'Eu não canto.', [
            ('Eu', 3, 'PRON', 'nsubj', 'PronType=Prs|Person=1|Number=Sing'),
            ('não', 3, 'ADV', 'advmod', ''),
            ('canto', 0, 'VERB', 'root', 'VerbForm=Fin|Person=1|Number=Sing')])
        self.assertEqual(decide_basic(row, obs)['chunks'][1]['text'], 'não canto')
        obs['sentences'][0][1]['deprel']='nsubj'
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')

    def test_postverbal_subject_and_numeral_are_not_forced(self):
        row, obs = fixture('pt', 'ele', 'Chegou ele.', [
            ('Chegou', 0, 'VERB', 'root', 'VerbForm=Fin|Person=3|Number=Sing'),
            ('ele', 1, 'PRON', 'nsubj', 'PronType=Prs|Person=3|Number=Sing')])
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')
        row, obs = article(word='um', surface='Um')
        obs['sentences'][0][0].update(upos='NUM', deprel='nummod', feats='NumType=Card')
        self.assertEqual(decide_basic(row, obs)['status'], 'abstain')

    def test_unrelated_surface_and_missing_parse(self):
        self.assertIsNone(decide_basic({'language': 'pt', 'word': 'que'}, None))
        self.assertEqual(decide_basic({'language': 'pt', 'word': 'eu'}, None)['status'], 'abstain')


if __name__ == '__main__':
    unittest.main()
