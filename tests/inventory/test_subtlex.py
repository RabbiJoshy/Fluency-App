"""Contract tests for the SUBTLEX-NL export adapter."""

from pathlib import Path
import tempfile
import unittest

from fluency.inventory.frequency_list import ranked_surfaces
from fluency.inventory.subtlex import SubtlexInventoryError, read_subtlex


HEADER = "Word\tFREQcount\tCDcount\tdominant.pos\n"


class SubtlexTests(unittest.TestCase):
    def _read(self, rows: str, header: str = HEADER):
        with tempfile.TemporaryDirectory() as raw_root:
            path = Path(raw_root) / "subtlex.tsv"
            path.write_text(header + rows, encoding="utf-8")
            return read_subtlex(path, language="nl")

    def test_reads_word_and_count_only(self) -> None:
        result = self._read("ik\t100\t8\tVNW\nje\t90\t8\tVNW\n")
        self.assertEqual(result.frequencies, {"ik": 100.0, "je": 90.0})

    def test_apostrophe_words_are_whole_surfaces(self) -> None:
        """'t and z'n are Dutch words; FrequencyWords lost them to z + n."""

        result = self._read("'t\t50\t8\tVNW\nz'n\t40\t8\tVNW\nauto's\t5\t3\tN\n")
        self.assertEqual(set(result.frequencies), {"'t", "z'n", "auto's"})

    def test_multiword_units_give_their_count_to_each_word(self) -> None:
        """SUBTLEX leaves aan_het's occurrences out of aan and het."""

        result = self._read("aan\t10\t5\tVZ\naan_het\t4\t3\tSPEC\n's_nachts\t2\t2\tBW\n")
        self.assertEqual(result.frequencies, {"aan": 14.0, "het": 4.0, "'s": 2.0, "nachts": 2.0})
        self.assertEqual(result.split_multiword_rows, 2)

    def test_a_trailing_full_stop_joins_the_bare_word(self) -> None:
        result = self._read("ben\t10\t5\tWW\nben.\t3\t2\tWW\n")
        self.assertEqual(result.frequencies, {"ben": 13.0})
        self.assertEqual(result.trailing_stop_rows, 1)

    def test_apostrophe_stand_ins_fold_to_the_apostrophe(self) -> None:
        result = self._read("'t\t50\t8\tVNW\n´t\t4\t2\tVNW\nm\u0092n\t3\t2\tVNW\n")
        self.assertEqual(result.frequencies, {"'t": 54.0, "m'n": 3.0})
        self.assertEqual(result.apostrophe_repaired_rows, 2)

    def test_numbers_symbols_and_dotted_abbreviations_are_rejected(self) -> None:
        result = self._read("ik\t9\t5\tVNW\n20\t5\t3\tTW\n$\t4\t3\tSPEC\nf.b.i.\t3\t2\tSPEC\n")
        self.assertEqual(result.frequencies, {"ik": 9.0})
        self.assertEqual(result.rejected_surface_shape, 3)

    def test_case_variants_are_summed(self) -> None:
        result = self._read("God\t10\t5\tN\ngod\t4\t2\tN\n")
        self.assertEqual(result.frequencies, {"god": 14.0})

    def test_ranks_descending_then_alphabetically(self) -> None:
        result = self._read("b\t5\t1\tN\na\t5\t1\tN\nc\t9\t1\tN\n")
        self.assertEqual([s for s, _ in ranked_surfaces(result.frequencies)], ["c", "a", "b"])

    def test_wrong_header_raises(self) -> None:
        with self.assertRaises(SubtlexInventoryError):
            self._read("ik\t9\n", header="word\tcount\n")


if __name__ == "__main__":
    unittest.main()
