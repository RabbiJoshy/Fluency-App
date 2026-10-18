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

    def test_es_personal_a(self):
        sentence = "Conoce usted a ese hombre."
        words = [
            mock_token(1, "Conoce", "VERB", 0, "root", 0, 6, lemma="conocer"),
            mock_token(2, "usted", "PRON", 1, "nsubj", 7, 12, lemma="usted"),
            mock_token(3, "a", "ADP", 5, "case", 13, 14, lemma="a"),
            mock_token(4, "ese", "DET", 5, "det", 15, 18, lemma="ese"),
            mock_token(5, "hombre", "NOUN", 1, "obj", 19, 25, lemma="hombre"),
            mock_token(6, ".", "PUNCT", 1, "punct", 25, 26, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[13, 14]]}
        row = {'language': 'es', 'word': 'a', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 1)
        self.assertEqual(res['pattern_id'], 'es:a:1')

    def test_pt_a_proposito_abstains(self):
        sentence = "A propósito, não sei."
        words = [
            mock_token(1, "A", "ADP", 2, "case", 0, 1, lemma="a"),
            mock_token(2, "propósito", "NOUN", 5, "obl", 2, 11, lemma="propósito"),
            mock_token(3, ",", "PUNCT", 5, "punct", 11, 12, lemma=","),
            mock_token(4, "não", "ADV", 5, "advmod", 13, 16, lemma="não"),
            mock_token(5, "sei", "VERB", 0, "root", 17, 20, lemma="saber"),
            mock_token(6, ".", "PUNCT", 5, "punct", 20, 21, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[0, 1]]}
        row = {'language': 'pt', 'word': 'a', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'abstain')

    def test_con_cuidado_abstains(self):
        sentence = "Fale com cuidado."
        words = [
            mock_token(1, "Fale", "VERB", 0, "root", 0, 4, lemma="falar"),
            mock_token(2, "com", "ADP", 3, "case", 5, 8, lemma="com"),
            mock_token(3, "cuidado", "NOUN", 1, "obl", 9, 16, lemma="cuidado"),
            mock_token(4, ".", "PUNCT", 1, "punct", 16, 17, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[5, 8]]}
        row = {'language': 'pt', 'word': 'com', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'abstain')

    def test_por_favor_abstains(self):
        sentence = "Por favor, venha."
        words = [
            mock_token(1, "Por", "ADP", 2, "case", 0, 3, lemma="por"),
            mock_token(2, "favor", "NOUN", 4, "obl", 4, 9, lemma="favor"),
            mock_token(3, ",", "PUNCT", 4, "punct", 9, 10, lemma=","),
            mock_token(4, "venha", "VERB", 0, "root", 11, 16, lemma="vir"),
            mock_token(5, ".", "PUNCT", 4, "punct", 16, 17, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[0, 3]]}
        row = {'language': 'pt', 'word': 'por', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'abstain')

    def test_por_suas_vidas_is_motive_not_path(self):
        sentence = "Corram por suas vidas!"
        words = [
            mock_token(1, "Corram", "VERB", 0, "root", 0, 6, lemma="correr"),
            mock_token(2, "por", "ADP", 4, "case", 7, 10, lemma="por"),
            mock_token(3, "suas", "DET", 4, "det", 11, 15, lemma="seu"),
            mock_token(4, "vidas", "NOUN", 1, "obl", 16, 21, lemma="vida"),
            mock_token(5, "!", "PUNCT", 1, "punct", 21, 22, lemma="!")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[7, 10]]}
        row = {'language': 'pt', 'word': 'por', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)  # motive/cause, NOT 1 (path)
        self.assertEqual(res['pattern_id'], 'pt:por:0')

    def test_revista_sobre_cidade_is_topic_not_on_above(self):
        sentence = "Uma revista sobre a cidade."
        words = [
            mock_token(1, "Uma", "DET", 2, "det", 0, 3, lemma="um"),
            mock_token(2, "revista", "NOUN", 0, "root", 4, 11, lemma="revista"),
            mock_token(3, "sobre", "ADP", 5, "case", 12, 17, lemma="sobre"),
            mock_token(4, "a", "DET", 5, "det", 18, 19, lemma="o"),
            mock_token(5, "cidade", "NOUN", 2, "nmod", 20, 26, lemma="cidade"),
            mock_token(6, ".", "PUNCT", 2, "punct", 26, 27, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[12, 17]]}
        row = {'language': 'pt', 'word': 'sobre', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)  # topic (about), NOT 1 (on/above)
        self.assertEqual(res['pattern_id'], 'pt:sobre:0')

    def test_preguntar_si_indirect_question_abstains(self):
        sentence = "Me empiezo a preguntar si debería ir."
        words = [
            mock_token(1, "Me", "PRON", 2, "obj", 0, 2, lemma="yo"),
            mock_token(2, "empiezo", "VERB", 0, "root", 3, 10, lemma="empezar"),
            mock_token(3, "a", "ADP", 4, "mark", 11, 12, lemma="a"),
            mock_token(4, "preguntar", "VERB", 2, "xcomp", 13, 22, lemma="preguntar"),
            mock_token(5, "si", "SCONJ", 6, "mark", 23, 25, lemma="si"),
            mock_token(6, "debería", "VERB", 4, "ccomp", 26, 33, lemma="deber"),
            mock_token(7, "ir", "VERB", 6, "xcomp", 34, 36, lemma="ir"),
            mock_token(8, ".", "PUNCT", 2, "punct", 36, 37, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[23, 25]]}
        row = {'language': 'es', 'word': 'si', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'abstain')  # indirect question ("whether") abstains from conditional "if"

    def test_en_la_necesidad_abstract_noun_abstains(self):
        sentence = "Señor, ayúdanos siempre en la necesidad."
        words = [
            mock_token(1, "Señor", "NOUN", 3, "vocative", 0, 5, lemma="señor"),
            mock_token(2, ",", "PUNCT", 1, "punct", 5, 6, lemma=","),
            mock_token(3, "ayúdanos", "VERB", 0, "root", 7, 15, lemma="ayudar"),
            mock_token(4, "siempre", "ADV", 3, "advmod", 16, 23, lemma="siempre"),
            mock_token(5, "en", "ADP", 7, "case", 24, 26, lemma="en"),
            mock_token(6, "la", "DET", 7, "det", 27, 29, lemma="el"),
            mock_token(7, "necesidad", "NOUN", 3, "obl", 30, 39, lemma="necesidad"),
            mock_token(8, ".", "PUNCT", 3, "punct", 39, 40, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[24, 26]]}
        row = {'language': 'es', 'word': 'en', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'abstain')  # abstract state noun abstains from locative "en"

    def test_como_e_suposto_interrogative_abstains(self):
        sentence = "Como é suposto abateres um dos empréstimos?"
        words = [
            mock_token(1, "Como", "ADV", 3, "advmod", 0, 4, lemma="como"),
            mock_token(2, "é", "AUX", 3, "cop", 5, 6, lemma="ser"),
            mock_token(3, "suposto", "ADJ", 0, "root", 7, 14, lemma="supor"),
            mock_token(4, "abateres", "VERB", 3, "csubj", 15, 23, lemma="abater"),
            mock_token(5, "um", "NUM", 4, "obj", 24, 26, lemma="um"),
            mock_token(6, "dos", "ADP", 7, "case", 27, 30, lemma="de"),
            mock_token(7, "empréstimos", "NOUN", 5, "nmod", 31, 42, lemma="empréstimo"),
            mock_token(8, "?", "PUNCT", 3, "punct", 42, 43, lemma="?")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[0, 4]]}
        row = {'language': 'pt', 'word': 'como', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'abstain')  # interrogative "how" abstains from comparative "como"

    def test_como_comparative_with_preceding_verb(self):
        sentence = "Ele canta como um pássaro."
        words = [
            mock_token(1, "Ele", "PRON", 2, "nsubj", 0, 3, lemma="ele"),
            mock_token(2, "canta", "VERB", 0, "root", 4, 9, lemma="cantar"),
            mock_token(3, "como", "ADP", 5, "case", 10, 14, lemma="como"),
            mock_token(4, "um", "DET", 5, "det", 15, 17, lemma="um"),
            mock_token(5, "pássaro", "NOUN", 2, "obl", 18, 25, lemma="pássaro"),
            mock_token(6, ".", "PUNCT", 2, "punct", 25, 26, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[10, 14]]}
        row = {'language': 'pt', 'word': 'como', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)
        self.assertEqual(res['pattern_id'], 'pt:como:0')

    def test_entra_en_parada_cardiaca_abstains_from_locative(self):
        sentence = "El corazón entra en parada cardíaca."
        words = [
            mock_token(1, "El", "DET", 2, "det", 0, 2, lemma="el"),
            mock_token(2, "corazón", "NOUN", 3, "nsubj", 3, 10, lemma="corazón"),
            mock_token(3, "entra", "VERB", 0, "root", 11, 16, lemma="entrar"),
            mock_token(4, "en", "ADP", 5, "case", 17, 19, lemma="en"),
            mock_token(5, "parada", "NOUN", 3, "obl", 20, 26, lemma="parada"),
            mock_token(6, "cardíaca", "ADJ", 5, "amod", 27, 35, lemma="cardíaco"),
            mock_token(7, ".", "PUNCT", 3, "punct", 35, 36, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[17, 19]]}
        row = {'language': 'es', 'word': 'en', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'abstain')  # medical state "parada cardíaca" abstains from locative place

    def test_vivemos_como_os_nossos_pais_is_comparison(self):
        sentence = "Ainda somos os mesmos e vivemos como os nossos pais."
        words = [
            mock_token(1, "Ainda", "ADV", 2, "advmod", 0, 5, lemma="ainda"),
            mock_token(2, "somos", "AUX", 0, "root", 6, 11, lemma="ser"),
            mock_token(3, "os", "DET", 4, "det", 12, 14, lemma="o"),
            mock_token(4, "mesmos", "PRON", 2, "obj", 15, 21, lemma="mesmo"),
            mock_token(5, "e", "CCONJ", 6, "cc", 22, 23, lemma="e"),
            mock_token(6, "vivemos", "VERB", 2, "conj", 24, 31, lemma="viver"),
            mock_token(7, "como", "ADP", 10, "case", 32, 36, lemma="como"),
            mock_token(8, "os", "DET", 10, "det", 37, 39, lemma="o"),
            mock_token(9, "nossos", "DET", 10, "det", 40, 46, lemma="nosso"),
            mock_token(10, "pais", "NOUN", 6, "obl", 47, 51, lemma="pai"),
            mock_token(11, ".", "PUNCT", 2, "punct", 51, 52, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[32, 36]]}
        row = {'language': 'pt', 'word': 'como', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 0)  # comparison (manner), NOT 1 (role/job)
        self.assertEqual(res['pattern_id'], 'pt:como:0')

    def test_es_en_does_not_contain_parada_cardiaca(self):
        es = json.loads((ROOT / "app/data/grammar-words/es.json").read_text(encoding="utf-8"))
        en_rel0 = es["en"]["relations"][0]
        self.assertNotIn("parada", json.dumps(en_rel0))

    def test_pt_como_does_not_contain_pais_in_role(self):
        pt = json.loads((ROOT / "app/data/grammar-words/pt.json").read_text(encoding="utf-8"))
        como_rel1 = pt["como"]["relations"][1]
        self.assertNotIn("pais", json.dumps(como_rel1))
        como_rel0 = pt["como"]["relations"][0]
        self.assertIn("pais", json.dumps(como_rel0))

    def test_trabalho_como_engenheiro_is_role(self):
        sentence = "Trabalho como engenheiro."
        words = [
            mock_token(1, "Trabalho", "VERB", 0, "root", 0, 8, lemma="trabalhar"),
            mock_token(2, "como", "ADP", 3, "case", 9, 13, lemma="como"),
            mock_token(3, "engenheiro", "NOUN", 1, "obl", 14, 24, lemma="engenheiro"),
            mock_token(4, ".", "PUNCT", 1, "punct", 24, 25, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[9, 13]]}
        row = {'language': 'pt', 'word': 'como', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'candidate')
        self.assertEqual(res['pattern'], 1)  # role/job, NOT 0 (comparison)
        self.assertEqual(res['pattern_id'], 'pt:como:1')

    def test_unfamiliar_noun_and_verb_abstains_from_comparison(self):
        sentence = "Comprei o carro como novo."
        words = [
            mock_token(1, "Comprei", "VERB", 0, "root", 0, 7, lemma="comprar"),
            mock_token(2, "o", "DET", 3, "det", 8, 9, lemma="o"),
            mock_token(3, "carro", "NOUN", 1, "obj", 10, 15, lemma="carro"),
            mock_token(4, "como", "ADP", 5, "case", 16, 20, lemma="como"),
            mock_token(5, "novo", "ADJ", 1, "obl", 21, 25, lemma="novo"),
            mock_token(6, ".", "PUNCT", 1, "punct", 25, 26, lemma=".")
        ]
        obs = {'parser': 'mock', 'sentences': [words], 'spans': [[16, 20]]}
        row = {'language': 'pt', 'word': 'como', 'sentence': sentence}
        res = assign(row, obs)
        self.assertEqual(res['status'], 'abstain')  # not licensed by comparison or role verb

if __name__ == '__main__':
    unittest.main()




