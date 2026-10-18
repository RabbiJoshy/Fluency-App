"""Structural Spanish assignment tests, independent of editorial labels."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'research/function_word_audit'))
from syntax_assignment_es import decide_es


def case(text, word, specs):
    """Build a UD-shaped parse with exact offsets from ordered surface tokens."""
    nodes, cursor = [], 0
    for i, (surface, lemma, pos, relation, head, feats) in enumerate(specs, 1):
        start = text.index(surface, cursor)
        cursor = start + len(surface)
        nodes.append(dict(id=i, text=surface, lemma=lemma, upos=pos,
                          deprel=relation, head=head, feats=feats,
                          token=dict(start_char=start, end_char=cursor)))
    focus = next(n for n in nodes if n['text'].casefold() == word)
    row = dict(language='es', sentence=text, word=word)
    obs = dict(parser='synthetic-ud-test', spans=[[focus['token']['start_char'], focus['token']['end_char']]], sentences=[nodes])
    return row, obs


class SpanishAssignmentTests(unittest.TestCase):
    def candidate(self, args, pattern, expected):
        result = decide_es(*args)
        self.assertEqual((result['status'], result.get('pattern')), ('candidate', pattern))
        self.assertEqual([(c['slot'], c['text']) for c in result['chunks']], expected)
        for c in result['chunks']:
            self.assertEqual(args[0]['sentence'][c['start']:c['end']], c['text'])
        return result

    def test_pronominal_lemma_without_retained_label(self):
        args = case('Ana se equivoca', 'se', [
            ('Ana','Ana','PROPN','nsubj',3,None), ('se','él','PRON','expl:pv',3,'Reflex=Yes'),
            ('equivoca','equivocar','VERB','root',0,'VerbForm=Fin')])
        self.candidate(args, 0, [('connector','se'),('v','equivoca')])

    def test_llevarse_requires_full_licensed_construction(self):
        args = case('Se lleva bien con Ana', 'se', [
            ('Se','él','PRON','expl:pv',2,None), ('lleva','llevar','VERB','root',0,None),
            ('bien','bien','ADV','advmod',2,None), ('con','con','ADP','case',5,None),
            ('Ana','Ana','PROPN','obl',2,None)])
        self.candidate(args,0,[('connector','Se'),('v','lleva bien con Ana')])
        args[1]['sentences'][0][2]['lemma']='rápidamente'
        self.assertEqual(decide_es(*args)['status'],'abstain')

    def test_ambiguous_passive_not_licensed_by_parser_tag(self):
        for relation in ['expl:pv','expl:pass','obj']:
            args = case('Se lava', 'se', [('Se','él','PRON',relation,2,'Reflex=Yes'),
                                           ('lava','lavar','VERB','root',0,None)])
            self.assertEqual(decide_es(*args)['status'],'abstain')

    def test_passive_conflict_blocks_licensed_lemma(self):
        args = case('Se refiere información', 'se', [('Se','él','PRON','expl:pv',2,None),
            ('refiere','referir','VERB','root',0,None),('información','información','NOUN','nsubj:pass',2,None)])
        self.assertEqual(decide_es(*args)['status'],'abstain')

    def test_lo_tener_que_infinitive_with_parser_conj(self):
        args = case('Lo tengo que explicar', 'lo', [('Lo','él','PRON','obj',4,'Case=Acc'),
            ('tengo','tener','VERB','root',0,'VerbForm=Fin'), ('que','que','SCONJ','cc',4,None),
            ('explicar','explicar','VERB','conj',2,'VerbForm=Inf')])
        self.candidate(args,1,[('connector','Lo'),('v','tengo que explicar')])

    def test_lo_modal_and_auxiliary_complexes(self):
        args = case('Lo puedo explicar', 'lo', [('Lo','él','PRON','obj',3,'Case=Acc'),
            ('puedo','poder','VERB','root',0,None), ('explicar','explicar','VERB','xcomp',2,'VerbForm=Inf')])
        self.candidate(args,1,[('connector','Lo'),('v','puedo explicar')])
        args = case('Lo hemos explicado', 'lo', [('Lo','él','PRON','obj',3,'Case=Acc'),
            ('hemos','haber','AUX','aux',3,None), ('explicado','explicar','VERB','root',0,'VerbForm=Part')])
        self.candidate(args,1,[('connector','Lo'),('v','hemos explicado')])

    def test_unrelated_intervening_material_not_swallowed(self):
        args = case('Lo Ana explica', 'lo', [('Lo','él','PRON','obj',3,None),
            ('Ana','Ana','PROPN','nsubj',3,None), ('explica','explicar','VERB','root',0,None)])
        self.assertEqual(decide_es(*args)['status'],'abstain')

    def test_anaphoric_copula(self):
        args = case('Lo es', 'lo', [('Lo','él','PRON','root',0,'Case=Acc'),
                                   ('es','ser','AUX','cop',1,None)])
        self.candidate(args,1,[('connector','Lo'),('v','es')])
        args = case('Seguro que lo es', 'lo', [('Seguro','seguro','ADJ','root',0,None),
            ('que','que','SCONJ','mark',3,None),('lo','él','PRON','csubj',1,'Case=Acc'),
            ('es','ser','AUX','cop',3,None)])
        self.candidate(args,1,[('connector','lo'),('v','es')])

    def test_nominal_relative_lo_is_not_object(self):
        args = case('Lo que hago', 'lo', [('Lo','él','PRON','dep',3,None),
            ('que','que','PRON','obj',3,'PronType=Rel'),('hago','hacer','VERB','root',0,None)])
        self.assertEqual(decide_es(*args)['status'],'abstain')

    def test_relative_acl_with_full_complement(self):
        args = case('Un barco que nos lleve a casa', 'que', [
            ('Un','uno','DET','det',2,None),('barco','barco','NOUN','root',0,None),
            ('que','que','PRON','nsubj',5,'PronType=Int,Rel'),('nos','yo','PRON','obj',5,None),
            ('lleve','llevar','VERB','acl',2,'VerbForm=Fin'), ('a','a','ADP','case',7,None),
            ('casa','casa','NOUN','obl',5,None)])
        self.candidate(args,1,[('v','barco'),('connector','que'),('c','nos lleve a casa')])
        args[1]['sentences'][0][2]['feats']='PronType=Int'
        self.assertIsNone(decide_es(*args))

    def test_prepositional_relative_abstains(self):
        args = case('El barco en que viajo', 'que', [('El','el','DET','det',2,None),
            ('barco','barco','NOUN','root',0,None), ('en','en','ADP','case',4,None),
            ('que','que','PRON','obl',5,'PronType=Rel'), ('viajo','viajar','VERB','acl',2,None)])
        self.assertEqual(decide_es(*args)['status'],'abstain')

    def test_al_destination_and_rejected_recipient_personal_rate(self):
        args = case('Voy al parque', 'al', [('Voy','ir','VERB','root',0,None),
            ('al','al','ADP','case',3,None), ('parque','parque','NOUN','obl',1,None)])
        self.candidate(args,0,[('connector','al'),('c','parque')])
        for text, verb, noun, relation in [('Digo al jefe','decir','jefe','iobj'),
                ('Veo al jefe','ver','jefe','obj'), ('Como al día','comer','día','obl')]:
            args = case(text,'al',[(text.split()[0],verb,'VERB','root',0,None),
                ('al','al','ADP','case',3,None),(noun,noun,'NOUN',relation,1,None)])
            self.assertEqual(decide_es(*args)['status'],'abstain')

    def test_bad_focus_and_other_language(self):
        row, obs = case('Lo hago','lo',[('Lo','él','PRON','obj',2,None),('hago','hacer','VERB','root',0,None)])
        obs['spans']=[[0,1]]
        self.assertEqual(decide_es(row,obs)['status'],'abstain')
        row['language']='pt'
        self.assertIsNone(decide_es(row,obs))


if __name__ == '__main__':
    unittest.main()
