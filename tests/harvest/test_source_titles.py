import gzip
from pathlib import Path
import tempfile
import unittest

from fluency.harvest.source_titles import (
    collect_title_ids_from_ids_file,
    resolve_source_titles,
)
from fluency.harvest.sources.opensubtitles import OpenSubtitlesAdapter
from fluency.release.source_titles import attach_title_to_example


class SourceTitleTests(unittest.TestCase):
    def test_ids_line_yields_the_imdb_title_id(self) -> None:
        self.assertEqual(
            OpenSubtitlesAdapter.title_id_from_ids_line(
                "x\tpt/2016/5884078/6916203.xml.gz\tx\t200\n"
            ),
            "5884078",
        )
        self.assertIsNone(OpenSubtitlesAdapter.title_id_from_ids_line("not-a-row\n"))

    def test_ids_file_collects_every_distinct_title(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "OpenSubtitles.en-pt.ids"
            path.write_text(
                "x\tpt/2016/5884078/1.xml.gz\tx\t1\n"
                "x\tpt/2017/6303088/2.xml.gz\tx\t2\n"
                "x\tpt/2016/5884078/3.xml.gz\tx\t3\n",
                encoding="utf-8",
            )
            self.assertEqual(
                collect_title_ids_from_ids_file(path),
                {"5884078", "6303088"},
            )

    def test_imdb_dump_resolves_films_and_parent_series(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            basics = root / "title.basics.tsv.gz"
            episodes = root / "title.episode.tsv.gz"
            with gzip.open(basics, "wt", encoding="utf-8") as stream:
                stream.write(
                    "tconst\ttitleType\tprimaryTitle\toriginalTitle\tisAdult\tstartYear\tendYear\truntimeMinutes\tgenres\n"
                    "tt1256443\ttvEpisode\tFriends and Neighbors\tFriends and Neighbors\t0\t2009\t\\N\t43\tDrama\n"
                    "tt0256443\ttvSeries\tWithout a Trace\tWithout a Trace\t0\t2002\t2009\t43\tDrama\n"
                    "tt0361748\tmovie\tInglourious Basterds\tInglourious Basterds\t0\t2009\t\\N\t153\tWar\n"
                    "tt0999999\tmovie\tUncited\tUncited\t0\t2010\t\\N\t90\tDrama\n"
                )
            with gzip.open(episodes, "wt", encoding="utf-8") as stream:
                stream.write(
                    "tconst\tparentTconst\tseasonNumber\tepisodeNumber\n"
                    "tt1256443\ttt0256443\t7\t16\n"
                )
            resolved = resolve_source_titles(
                {"1256443", "361748", "404"},
                basics_path=basics,
                episodes_path=episodes,
            )

        self.assertEqual(resolved["361748"]["title"], "Inglourious Basterds")
        self.assertEqual(resolved["361748"]["year"], "2009")
        self.assertEqual(resolved["1256443"]["series"], "Without a Trace")
        self.assertEqual(resolved["1256443"]["title"], "Friends and Neighbors")
        self.assertEqual(resolved["1256443"]["season"], "7")
        self.assertNotIn("404", resolved)

    def test_example_receives_the_human_title(self) -> None:
        example = {
            "source": "opensubtitles",
            "metadata": {
                "source": {
                    "name": "opensubtitles",
                    "document": {"title_id": "361748"},
                }
            },
        }
        self.assertEqual(
            attach_title_to_example(
                example, {"361748": {"title": "Inglourious Basterds", "year": "2009"}}
            ),
            "resolved",
        )
        self.assertEqual(example["metadata"]["source_title"]["title"], "Inglourious Basterds")

    def test_unresolved_title_is_declared_not_invented(self) -> None:
        example = {
            "metadata": {
                "source": {"name": "opensubtitles", "document": {"title_id": "1"}}
            }
        }
        self.assertEqual(attach_title_to_example(example, {}), "unresolved")
        self.assertNotIn("source_title", example["metadata"])


if __name__ == "__main__":
    unittest.main()
