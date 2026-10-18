import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/function_word_audit'))
from syntax_assignment import assign

def mock_token(id_num, text, upos, head, deprel, start, end, lemma=None, feats=None):
    return {
        'id': id_num,
        'text': text,
        'lemma': lemma or text.lower(),
        'upos': upos,
        'head': head,
        'deprel': deprel,
        'feats': feats or '',
        'token': {'text': text, 'start_char': start, 'end_char': end}
    }

class AllPatternsAssignmentTests(unittest.TestCase):
    def test_es_demonstrative_subject_eso(self):
        sentence = "Eso es verdad."
        # Eso (0..3) es (4..6) verdad (7..13) . (13..14)
        words = [
            mock_token(1, "Eso", "PRON", 2, "nsubj", 0, 3, lemma="eso", feats="PronType=Dem"),
            mock_token(2, "es", "AUX", 0, "root", 4, 6, lemma="ser", feats="VerbForm=Fin|Person=3|Number=Sing"),
            mock_token(3, "verdad", "NOUN", 2, "obj", 7, 13, lemma="verdad"),
            mock_token(4, ".", "PUNCT", 2, "punct", 13, 14, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[0, 3]]}
        row = {'language': 'es', 'word': 'eso', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)
        self.assertEqual(res['pattern_id'], 'es:eso:0')
        self.assertIn("<span class=\"fw-token-connector\">Eso</span>", res['targetHTML'])
        self.assertIn("<span class=\"fw-token-v\">es</span>", res['targetHTML'])

    def test_pt_demonstrative_subject_isso(self):
        sentence = "Isso faz sentido."
        words = [
            mock_token(1, "Isso", "PRON", 2, "nsubj", 0, 4, lemma="isso", feats="PronType=Dem"),
            mock_token(2, "faz", "VERB", 0, "root", 5, 8, lemma="fazer", feats="VerbForm=Fin|Person=3|Number=Sing"),
            mock_token(3, "sentido", "NOUN", 2, "obj", 9, 16, lemma="sentido"),
            mock_token(4, ".", "PUNCT", 2, "punct", 16, 17, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[0, 4]]}
        row = {'language': 'pt', 'word': 'isso', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)
        self.assertEqual(res['pattern_id'], 'pt:isso:0')

    def test_es_clitic_le(self):
        sentence = "Le dije la verdad."
        words = [
            mock_token(1, "Le", "PRON", 2, "iobj", 0, 2, lemma="él", feats="Case=Dat|Person=3|Number=Sing"),
            mock_token(2, "dije", "VERB", 0, "root", 3, 7, lemma="decir", feats="VerbForm=Fin|Person=1|Number=Sing"),
            mock_token(3, "la", "DET", 4, "det", 8, 10, lemma="el"),
            mock_token(4, "verdad", "NOUN", 2, "obj", 11, 17, lemma="verdad"),
            mock_token(5, ".", "PUNCT", 2, "punct", 17, 18, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[0, 2]]}
        row = {'language': 'es', 'word': 'le', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)
        self.assertEqual(res['pattern_id'], 'es:le:0')

    def test_pt_clitic_lhe(self):
        sentence = "Lhe dei o livro."
        words = [
            mock_token(1, "Lhe", "PRON", 2, "iobj", 0, 3, lemma="ele", feats="Case=Dat|Person=3|Number=Sing"),
            mock_token(2, "dei", "VERB", 0, "root", 4, 7, lemma="dar", feats="VerbForm=Fin|Person=1|Number=Sing"),
            mock_token(3, "o", "DET", 4, "det", 8, 9, lemma="o"),
            mock_token(4, "livro", "NOUN", 2, "obj", 10, 15, lemma="livro"),
            mock_token(5, ".", "PUNCT", 2, "punct", 15, 16, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[0, 3]]}
        row = {'language': 'pt', 'word': 'lhe', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)
        self.assertEqual(res['pattern_id'], 'pt:lhe:0')

    def test_es_preposition_para_infinitive(self):
        sentence = "Vino para hablar."
        words = [
            mock_token(1, "Vino", "VERB", 0, "root", 0, 4, lemma="venir", feats="VerbForm=Fin|Person=3|Number=Sing"),
            mock_token(2, "para", "ADP", 3, "mark", 5, 9, lemma="para"),
            mock_token(3, "hablar", "VERB", 1, "advcl", 10, 16, lemma="hablar", feats="VerbForm=Inf"),
            mock_token(4, ".", "PUNCT", 1, "punct", 16, 17, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[5, 9]]}
        row = {'language': 'es', 'word': 'para', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)
        self.assertEqual(res['pattern_id'], 'es:para:0')
        self.assertIn("<span class=\"fw-token-connector\">para</span>", res['targetHTML'])
        self.assertIn("<span class=\"fw-token-c\">hablar</span>", res['targetHTML'])

    def test_pt_preposition_para_infinitive(self):
        sentence = "Veio para falar."
        words = [
            mock_token(1, "Veio", "VERB", 0, "root", 0, 4, lemma="vir", feats="VerbForm=Fin|Person=3|Number=Sing"),
            mock_token(2, "para", "ADP", 3, "mark", 5, 9, lemma="para"),
            mock_token(3, "falar", "VERB", 1, "advcl", 10, 15, lemma="falar", feats="VerbForm=Inf"),
            mock_token(4, ".", "PUNCT", 1, "punct", 15, 16, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[5, 9]]}
        row = {'language': 'pt', 'word': 'para', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 1)  # pt:para:1 is what for (infinitive)
        self.assertEqual(res['pattern_id'], 'pt:para:1')

    def test_es_preposition_en_place(self):
        sentence = "Vivo en Sevilla."
        words = [
            mock_token(1, "Vivo", "VERB", 0, "root", 0, 4, lemma="vivir", feats="VerbForm=Fin|Person=1|Number=Sing"),
            mock_token(2, "en", "ADP", 3, "case", 5, 7, lemma="en"),
            mock_token(3, "Sevilla", "PROPN", 1, "obl", 8, 15, lemma="Sevilla"),
            mock_token(4, ".", "PUNCT", 1, "punct", 15, 16, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[5, 7]]}
        row = {'language': 'es', 'word': 'en', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)  # en:0 is Where (place)
        self.assertEqual(res['pattern_id'], 'es:en:0')

    def test_pt_preposition_em_place(self):
        sentence = "Moro em Lisboa."
        words = [
            mock_token(1, "Moro", "VERB", 0, "root", 0, 4, lemma="morar", feats="VerbForm=Fin|Person=1|Number=Sing"),
            mock_token(2, "em", "ADP", 3, "case", 5, 7, lemma="em"),
            mock_token(3, "Lisboa", "PROPN", 1, "obl", 8, 14, lemma="Lisboa"),
            mock_token(4, ".", "PUNCT", 1, "punct", 14, 15, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[5, 7]]}
        row = {'language': 'pt', 'word': 'em', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)  # em:0 is Where (place)
        self.assertEqual(res['pattern_id'], 'pt:em:0')

    def test_es_del_contraction(self):
        sentence = "Es el coche del profesor."
        words = [
            mock_token(1, "Es", "AUX", 3, "cop", 0, 2, lemma="ser"),
            mock_token(2, "el", "DET", 3, "det", 3, 5, lemma="el"),
            mock_token(3, "coche", "NOUN", 0, "root", 6, 11, lemma="coche"),
            mock_token(4, "del", "ADP", 5, "case", 12, 15, lemma="del"),
            mock_token(5, "profesor", "NOUN", 3, "nmod", 16, 24, lemma="profesor", feats="Gender=Masc|Number=Sing"),
            mock_token(6, ".", "PUNCT", 3, "punct", 24, 25, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[12, 15]]}
        row = {'language': 'es', 'word': 'del', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)
        self.assertEqual(res['pattern_id'], 'es:del:0')

    def test_pt_do_contraction(self):
        sentence = "É o carro do professor."
        words = [
            mock_token(1, "É", "AUX", 3, "cop", 0, 1, lemma="ser"),
            mock_token(2, "o", "DET", 3, "det", 2, 3, lemma="o"),
            mock_token(3, "carro", "NOUN", 0, "root", 4, 9, lemma="carro"),
            mock_token(4, "do", "ADP", 5, "case", 10, 12, lemma="de"),
            mock_token(5, "professor", "NOUN", 3, "nmod", 13, 22, lemma="professor", feats="Gender=Masc|Number=Sing"),
            mock_token(6, ".", "PUNCT", 3, "punct", 22, 23, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[10, 12]]}
        row = {'language': 'pt', 'word': 'do', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)
        self.assertEqual(res['pattern_id'], 'pt:do:0')

if __name__ == '__main__':
    unittest.main()
