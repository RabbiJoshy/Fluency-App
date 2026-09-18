from pathlib import Path
import json
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from fluency.lyrics.playlist_live import store_playlist_live


class PlaylistLiveStoreTests(unittest.TestCase):
    def test_appends_tracks_and_writes_deck(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            track = store_playlist_live(
                workspace,
                {
                    "action": "savePlaylistLiveTracks",
                    "user": "JST",
                    "language": "portuguese",
                    "playlistId": "0ubVKl2OeeqSa5C0I3zbq7",
                    "records": [
                        {
                            "spotifyId": "abc",
                            "title": "Song",
                            "status": "lyrics",
                            "plainLyrics": "olá mundo",
                        }
                    ],
                },
            )
            deck = store_playlist_live(
                workspace,
                {
                    "action": "savePlaylistLiveDeck",
                    "user": "JST",
                    "language": "portuguese",
                    "playlistId": "0ubVKl2OeeqSa5C0I3zbq7",
                    "deck": {"id": "live", "matchedCount": 1},
                },
            )
            root = workspace / "raw" / "playlists" / "JST" / "portuguese" / "0ubVKl2OeeqSa5C0I3zbq7"
            self.assertEqual(track["count"], 1)
            self.assertTrue(Path(track["path"]).is_file())
            self.assertTrue(Path(deck["path"]).is_file())
            lines = (root / "tracks.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(json.loads(lines[0])["spotifyId"], "abc")
            self.assertEqual(json.loads((root / "deck.json").read_text(encoding="utf-8"))["matchedCount"], 1)

    def test_rejects_unknown_action(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(ValueError):
                store_playlist_live(
                    Path(raw),
                    {"action": "nope", "user": "JST", "language": "fr", "playlistId": "x"},
                )
