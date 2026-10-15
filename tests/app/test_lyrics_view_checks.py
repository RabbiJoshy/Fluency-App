"""Runs the Node checks for song translation mode (line playback and follow)."""

import shutil
import subprocess
import unittest
from pathlib import Path

CHECKS = Path(__file__).with_name("lyrics_line_playback_checks.mjs"), Path(__file__).with_name("lyrics_line_follow_checks.mjs")


@unittest.skipUnless(shutil.which("node"), "Node.js is needed to run the lyrics-view checks")
class LyricsViewChecks(unittest.TestCase):
    def test_node_checks_pass(self):
        for check in CHECKS:
            with self.subTest(check=check.name):
                done = subprocess.run(["node", str(check)], check=False, capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, done.stderr or done.stdout)


class CatalogueBake(unittest.TestCase):
    """The baked catalogue carries what playback needs, and nothing invented."""

    def test_baked_songs_are_playable_or_plain(self):
        import json, re
        songs = json.loads((Path(__file__).parents[2] / "app/turbo/probe_songs.json").read_text("utf-8"))
        self.assertEqual(len(songs), 30)
        for song in songs:
            with self.subTest(song=song["title"]):
                self.assertRegex(song.get("spotifyId", ""), r"^[A-Za-z0-9]{22}$")
                if song.get("syncedLyrics"):
                    self.assertGreater(len(re.findall(r"^\[\d+:\d+", song["syncedLyrics"], re.M)), 5)
                    self.assertGreater(song["lrclibDurationMs"], 60_000)
                else:
                    self.assertNotIn("lrclibDurationMs", song)

    def test_baked_portuguese_songs_are_playable_or_plain(self):
        import json, re
        songs = json.loads((Path(__file__).parents[2] / "app/turbo/pt_probe_songs.json").read_text("utf-8"))
        self.assertGreaterEqual(len(songs), 15)
        for song in songs:
            with self.subTest(song=song["title"]):
                self.assertRegex(song.get("spotifyId", ""), r"^[A-Za-z0-9]{22}$")
                if song.get("syncedLyrics"):
                    self.assertGreater(len(re.findall(r"^\[\d+:\d+", song["syncedLyrics"], re.M)), 5)
                    self.assertGreater(song["lrclibDurationMs"], 60_000)
                else:
                    self.assertNotIn("lrclibDurationMs", song)

    def test_catalogue_index_matches_its_song_files(self):
        import json, re
        root = Path(__file__).parents[2] / "app/turbo/catalogue"
        index = json.loads((root / "index.json").read_text("utf-8"))
        self.assertGreater(len(index), 100)
        ids = [entry["id"] for entry in index]
        self.assertEqual(len(ids), len(set(ids)), "one entry per track")
        curated = {s["spotifyId"] for s in json.loads(
            (Path(__file__).parents[2] / "app/turbo/probe_songs.json").read_text("utf-8"))}
        self.assertFalse(curated & set(ids), "a song is in the curated list or the index, not both")
        for entry in index:
            with self.subTest(song=entry["title"]):
                self.assertRegex(entry["id"], r"^[A-Za-z0-9]{22}$")
                self.assertTrue(entry["title"] and entry["artist"])
                detail = json.loads((root / "songs" / f"{entry['id']}.json").read_text("utf-8"))
                self.assertGreaterEqual(len(re.findall(r"^\[\d+:\d+", detail["syncedLyrics"], re.M)), 8)
                self.assertEqual(detail["lrclibDurationMs"], entry["lrclibDurationMs"])
        self.assertEqual(len(list((root / "songs").glob("*.json"))), len(index), "no orphan song files")


if __name__ == "__main__":
    unittest.main()
