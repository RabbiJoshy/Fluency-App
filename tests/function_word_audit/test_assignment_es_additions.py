"""Spanish patterns added 2026-10-19: todo "all the", reflexive me/te/nos, lo que."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'research/function_word_audit'))
from syntax_assignment_es_additions import decide_es_additions
from test_assignment_es import case


class SpanishAdditionTests(unittest.TestCase):
    def decide(self, text, word, specs):
        return decide_es_additions(*case(text, word, specs))

    def assertPattern(self, result, pattern, chunks):
        self.assertEqual((result['status'], result.get('pattern')), ('candidate', pattern))
        self.assertEqual([(c['slot'], c['text']) for c in result['chunks']], chunks)

    def test_reflexive_me_agrees_with_first_person_verb(self):
        result = self.decide('Me levanto tarde', 'me', [
            ('Me', 'yo', 'PRON', 'obj', 2, 'Person=1|Number=Sing'),
            ('levanto', 'levantar', 'VERB', 'root', 0, 'Person=1|Number=Sing|VerbForm=Fin'),
            ('tarde', 'tarde', 'ADV', 'advmod', 2, None)])
        self.assertPattern(result, 1, [('connector', 'Me'), ('v', 'levanto')])

    def test_object_me_with_third_person_verb_defers(self):
        # "he bought me": left for the older "me / to me" rule.
        self.assertIsNone(self.decide('Me compró un reloj', 'me', [
            ('Me', 'yo', 'PRON', 'iobj', 2, None),
            ('compró', 'comprar', 'VERB', 'root', 0, 'Person=3|Number=Sing|VerbForm=Fin'),
            ('un', 'uno', 'DET', 'det', 4, None), ('reloj', 'reloj', 'NOUN', 'obj', 2, None)]))

    def test_nos_with_first_plural_verb_is_reflexive(self):
        result = self.decide('Nos vemos mañana', 'nos', [
            ('Nos', 'yo', 'PRON', 'obj', 2, None),
            ('vemos', 'ver', 'VERB', 'root', 0, 'Person=1|Number=Plur|VerbForm=Fin'),
            ('mañana', 'mañana', 'ADV', 'advmod', 2, None)])
        self.assertPattern(result, 1, [('connector', 'Nos'), ('v', 'vemos')])

    def test_infinitive_without_person_defers(self):
        self.assertIsNone(self.decide('Quiero verte', 'te', [
            ('Quiero', 'querer', 'VERB', 'root', 0, 'Person=1|Number=Sing'),
            ('ver', 'ver', 'VERB', 'xcomp', 1, 'VerbForm=Inf'),
            ('te', 'tú', 'PRON', 'obj', 2, None)]))

    def test_todo_el_noun_hung_on_article(self):
        result = self.decide('Trabajé todo el día', 'todo', [
            ('Trabajé', 'trabajar', 'VERB', 'root', 0, None),
            ('todo', 'todo', 'DET', 'det', 3, None),
            ('el', 'el', 'DET', 'det', 4, None),
            ('día', 'día', 'NOUN', 'obl', 1, None)])
        self.assertPattern(result, 1, [('connector', 'todo'), ('c', 'el día')])

    def test_todo_el_mundo_abstains(self):
        result = self.decide('Todo el mundo lo sabe', 'todo', [
            ('Todo', 'todo', 'DET', 'det', 2, None), ('el', 'el', 'DET', 'det', 3, None),
            ('mundo', 'mundo', 'NOUN', 'nsubj', 5, None), ('lo', 'él', 'PRON', 'obj', 5, None),
            ('sabe', 'saber', 'VERB', 'root', 0, None)])
        self.assertEqual(result['status'], 'abstain')

    def test_lo_que_clause(self):
        result = self.decide('Sé lo que quieres', 'lo', [
            ('Sé', 'saber', 'VERB', 'root', 0, None),
            ('lo', 'él', 'PRON', 'obj', 1, None),
            ('que', 'que', 'PRON', 'obj', 4, 'PronType=Rel'),
            ('quieres', 'querer', 'VERB', 'acl:relcl', 2, None)])
        self.assertPattern(result, 2, [('connector', 'lo'), ('c', 'que quieres')])

    def test_lo_before_adjective_defers(self):
        self.assertIsNone(self.decide('Lo importante es participar', 'lo', [
            ('Lo', 'el', 'DET', 'det', 2, None), ('importante', 'importante', 'ADJ', 'nsubj', 4, None),
            ('es', 'ser', 'AUX', 'cop', 4, None), ('participar', 'participar', 'VERB', 'root', 0, None)]))


if __name__ == '__main__':
    unittest.main()
