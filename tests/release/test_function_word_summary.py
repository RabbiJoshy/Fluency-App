import unittest

from fluency.release.run_candidate import function_word_label, function_word_summary


def row(kind, value, gloss):
    return {"status": "abstained", "evidence": {"function_word": {"kind": kind, "value": value, "gloss": gloss}}}


class FunctionWordSummaryTests(unittest.TestCase):
    def test_same_role_with_different_glosses_stays_apart(self):
        rows = [row("role", "subject_pron", "she")] * 6 + [row("role", "subject_pron", "they")] * 4
        summary = function_word_summary(rows)
        self.assertEqual(
            [(r["gloss"], r["count"]) for r in summary["roles"]], [("she", 6), ("they", 4)]
        )

    def test_unlabelled_rows_are_counted_as_considered_only(self):
        rows = [row("unit", "aan het", "be ...-ing"), {"status": "abstained", "evidence": {}}]
        summary = function_word_summary(rows)
        self.assertEqual((summary["labelled"], summary["considered"]), (1, 2))
        self.assertEqual(summary["patterns"][0]["value"], "aan het")

    def test_no_labels_means_no_summary(self):
        self.assertIsNone(function_word_summary([{"evidence": {}}]))
        self.assertIsNone(function_word_label({"evidence": {"function_word": {"kind": "none", "value": None}}}))


if __name__ == "__main__":
    unittest.main()
