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


if __name__ == "__main__":
    unittest.main()
