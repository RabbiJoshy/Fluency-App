import importlib.util
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _load_builder():
    path = REPOSITORY_ROOT / "scripts" / "build_conjugation_examples.py"
    spec = importlib.util.spec_from_file_location("build_conjugation_examples", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = _load_builder()

POOL = {
    "pool_id": "es-test",
    "content_id": "sha256:test",
    "sources": [{"name": "tatoeba"}, {"name": "opensubtitles"}],
}


def _deck(*verbs):
    return {
        "deck_version": "conjugation-drill/v2",
        "language": "es",
        "source": {"provider": "stub"},
        "verbs": [
            {"h": head, "p": {"Indicativo::Presente": {"f": forms}}}
            for head, forms in verbs
        ],
    }


def _record(sentence_id, target, english, source="tatoeba"):
    return {
        "sentence_id": sentence_id,
        "source": {"name": source},
        "target": {"text": target},
        "translation": {"text": english},
    }


class ConjugationExamplesTests(unittest.TestCase):
    def test_forms_point_at_shared_sentences_and_ids_go_to_the_sidecar(self) -> None:
        deck = _deck(("tener", ["tengo", "tienes"]), ("hablar", ["hablo", "he hablado"]))
        records = [
            _record("s1", "Tengo miedo de la oscuridad.", "I'm afraid of the dark."),
            _record("s2", "Yo hablo y tengo razón.", "I talk and I'm right."),
            _record("s3", "Nunca he hablado con ella.", "I've never spoken to her."),
        ]
        payload, ids, _ = builder.build_examples(deck, records, POOL)
        sentences = payload["sentences"]
        self.assertEqual(len(sentences), len(ids))
        self.assertEqual({ids[i] for i in payload["forms"]["tengo"]}, {"s1", "s2"})
        self.assertEqual([ids[i] for i in payload["forms"]["hablo"]], ["s2"])
        self.assertEqual([ids[i] for i in payload["forms"]["he hablado"]], ["s3"])
        self.assertNotIn("tienes", payload["forms"])  # absent, not guessed
        self.assertEqual(len(sentences[0]), 3)

    def test_quota_follows_the_verb_rank(self) -> None:
        filler = [(f"v{i}", [f"x{i}"]) for i in range(200)]
        deck = _deck(("ser", ["es"]), *filler, ("rarear", ["rarea"]))
        records = [
            _record(f"a{i}", f"Esto es cosa número {'uno dos tres cuatro'.split()[i]}.", "This is a thing.")
            for i in range(4)
        ] + [
            _record(f"b{i}", f"Ella rarea mucho {'hoy ayer siempre'.split()[i]}.", "She acts oddly.")
            for i in range(3)
        ]
        payload, _, _ = builder.build_examples(deck, records, POOL)
        self.assertEqual(len(payload["forms"]["es"]), 3)
        self.assertEqual(len(payload["forms"]["rarea"]), 1)

    def test_prefers_tatoeba_then_rejects_unclean_lines(self) -> None:
        deck = _deck(("tener", ["tengo"]))
        records = [
            _record("sub", "Tengo que irme ahora mismo.", "I have to go right now.", "opensubtitles"),
            _record("tat", "Tengo que irme ya, lo siento.", "I have to go now, sorry."),
            _record("song", "♪ Tengo un amor ♪", "I have a love."),
            _record("frag", "tengo que", "I have to"),
        ]
        payload, ids, stats = builder.build_examples(deck, records, POOL)
        self.assertEqual([ids[i] for i in payload["forms"]["tengo"]], ["tat", "sub"])
        self.assertEqual(stats["rejected_noise"], 1)

    def test_clean_reason_names_the_problem(self) -> None:
        self.assertIsNone(builder.clean_reason("Tengo hambre ahora.", "I'm hungry now."))
        self.assertEqual(builder.clean_reason("Tengo 3 gatos en casa.", "I have 3 cats."), "noise")
        self.assertEqual(builder.clean_reason("- Tengo hambre. - Yo también.", "Hungry. Me too."), "noise")
        self.assertEqual(builder.clean_reason("Tengo mucha hambre", "I'm very hungry"), "fragment")


if __name__ == "__main__":
    unittest.main()
