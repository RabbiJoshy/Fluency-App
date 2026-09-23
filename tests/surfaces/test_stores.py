"""Language, artist and live stores read as one stack; promotion appends, never edits."""

import json
import tempfile
import unittest
from pathlib import Path

from fluency.surfaces import trust
from fluency.surfaces.declared import Context, DeclaredEntry, DeclaredError
from fluency.surfaces.stores import (
    NoLiveFacts, append_entry, artist_layer_dir, promote, stack,
)


def raw(entry_id, surface, translation, **extra):
    return {"entry_id": entry_id, "kind": "gloss", "surface": surface,
            "payload": {"senses": [{"translation": translation}]},
            "reason": "test", "author": "test", "created_at": "2026-09-23", **extra}


def write(directory: Path, *entries):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "entries.json").write_text(json.dumps(
        {"schema": "declared-entries/v1", "language": "es", "entries": list(entries)}), encoding="utf-8")


class Live:
    def __init__(self, *entries):
        self._entries = entries

    def entries(self, language):
        return self._entries


def live_entry(surface, translation, playlist="p1", level=trust.HEURISTIC):
    return DeclaredEntry(entry_id=f"live-{surface}", kind="gloss", language="es", surface=surface,
                         payload={"senses": [{"translation": translation}]},
                         scope={"mode": "live", "playlist": playlist}, trust=level,
                         reason="seen in a playlist", author="live", created_at="2026-09-23")


class StackTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        self.workspace = Path(self.temporary.name) / "ws"
        write(self.repo / "config/declared/es", raw("es-yeh", "yeh", "yeah"))
        write(artist_layer_dir(self.workspace, "es", "bad-bunny"),
              raw("bb-yeh", "yeh", "ad-lib", scope={"mode": "lyrics", "artist": "bad-bunny"}))

    def tearDown(self):
        self.temporary.cleanup()

    def test_each_consumer_sees_only_its_stores(self):
        speech = stack(self.repo, "es")
        self.assertEqual(speech.select("yeh", "gloss", Context("es", "speech"), trust.DERIVED).entry_id, "es-yeh")
        artist = stack(self.repo, "es", workspace=self.workspace, artist="bad-bunny")
        lyrics = Context("es", "lyrics", artist="bad-bunny")
        self.assertEqual(artist.select("yeh", "gloss", lyrics, trust.DERIVED).entry_id, "bb-yeh")
        # Another artist inherits the language store, not Bad Bunny's layer.
        other = Context("es", "lyrics", artist="rosalia")
        self.assertEqual(artist.select("yeh", "gloss", other, trust.DERIVED).entry_id, "es-yeh")

    def test_an_artist_layer_holds_only_that_artist(self):
        write(artist_layer_dir(self.workspace, "es", "rosalia"), raw("wide", "uy", "oops"))
        with self.assertRaises(DeclaredError):
            stack(self.repo, "es", workspace=self.workspace, artist="rosalia")

    def test_live_facts_are_heuristic_and_invisible_to_releases(self):
        registry = stack(self.repo, "es", live=Live(live_entry("brr", "brr (ad-lib)")))
        playlist = Context("es", "live", playlist="p1")
        self.assertIsNotNone(registry.select("brr", "gloss", playlist, trust.HEURISTIC))
        self.assertIsNone(registry.select("brr", "gloss", playlist, trust.DERIVED))
        with self.assertRaises(DeclaredError):
            stack(self.repo, "es", live=Live(live_entry("brr", "brr", level=trust.CURATED)))
        self.assertEqual(list(NoLiveFacts().entries("es")), [])

    def test_promotion_appends_at_higher_trust_and_may_widen_scope(self):
        guess = live_entry("brr", "brr (ad-lib)")
        confirmed = promote(guess, to_trust=trust.CURATED, author="joshua", reason="reviewed",
                            created_at="2026-09-24", scope={"mode": "lyrics"})
        self.assertEqual((confirmed.trust, confirmed.payload["promoted_from"]), (trust.CURATED, guess.entry_id))
        self.assertEqual(guess.trust, trust.HEURISTIC)  # the guess survives as it was
        target = self.repo / "config/declared/es/lyrics.json"
        append_entry(target, confirmed)
        registry = stack(self.repo, "es")
        self.assertEqual(registry.select("brr", "gloss", Context("es", "lyrics"), trust.DERIVED).entry_id,
                         "live-brr~curated")
        with self.assertRaises(DeclaredError):
            append_entry(target, confirmed)

    def test_promotion_cannot_lower_trust_or_narrow_scope(self):
        entry = live_entry("brr", "brr")
        with self.assertRaises(DeclaredError):
            promote(entry, to_trust=trust.HEURISTIC, author="a", reason="r", created_at="d")
        with self.assertRaises(DeclaredError):
            promote(entry, to_trust=trust.CURATED, author="a", reason="r", created_at="d",
                    scope={"mode": "live", "playlist": "p1", "song": "s"})


if __name__ == "__main__":
    unittest.main()
