import json
import tempfile
import unittest
from pathlib import Path

from fluency.release.ranked_assigners import (
    NORMAL,
    RankedAssignerError,
    RankedAssignments,
    load_assigner,
)

MENU_ID = "sha256:" + "a" * 64
MENUS = {
    "card_x": {"analyses": [
        {"menu_analysis_id": "an_verb", "senses": [{"sense_id": "own"}, {"sense_id": "have_to"}]},
    ]},
}


def stage04(status="assigned", sense="own", evidence=None):
    return {"card_id": "card_x", "status": status, "sense_menu_content_id": MENU_ID,
            "menu_analysis_id": "an_verb" if sense else None, "selected_sense_id": sense,
            "selected_tuple": {"headword": "ter", "part_of_speech": "verb"} if sense else None,
            "emitted_level": "leaf" if sense else None, "evidence": evidence or {}}


def assigner_row(sentence, sense="have_to", menu=MENU_ID, analysis="an_verb"):
    return {"row_version": "wsd-assigner-row/v1", "card_id": "card_x", "sentence_id": sentence,
            "sense_menu_content_id": menu, "menu_analysis_id": analysis, "selected_sense_id": sense,
            "selected_tuple": {"headword": "ter", "part_of_speech": "verb"}, "emitted_level": "leaf"}


class RankedAssignerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write_assigner(self, rows, label="DEEPSEEK", version="v25", language="pt"):
        path = Path(self.tmp.name) / f"{label}-{version}"
        path.mkdir()
        (path / "manifest.json").write_text(json.dumps({
            "assigner_version": "wsd-assigner/v1", "assigner_id": path.name,
            "label": label, "version": version, "language": language}))
        (path / "assignments.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        return path

    def test_assigner_above_normal_replaces_the_sense_but_not_the_row(self):
        base = {
            ("card_x", "s1"): stage04(evidence={"function_word": {"kind": "role"}, "selected_multiword": "ter que"}),
            ("card_x", "s2"): stage04(),
        }
        ranked = RankedAssignments(base, [self.write_assigner([assigner_row("s1")]), NORMAL], MENUS, "pt")
        row = ranked.get(("card_x", "s1"))
        self.assertEqual(row["selected_sense_id"], "have_to")
        self.assertEqual(row["status"], "assigned")
        self.assertEqual(row["evidence"]["function_word"], {"kind": "role"})
        self.assertNotIn("selected_multiword", row["evidence"])
        self.assertEqual(row["evidence"]["assigner"]["label"], "DEEPSEEK")
        self.assertEqual(ranked.get(("card_x", "s2"))["selected_sense_id"], "own")
        self.assertEqual(ranked.get("card_x")["s1"]["selected_sense_id"], "have_to")
        self.assertEqual(ranked.stats["DEEPSEEK v25"]["applied_changed"], 1)
        self.assertEqual(base[("card_x", "s1")]["selected_sense_id"], "own", "stage 04 itself is untouched")

    def test_normal_above_assigner_only_fills_rows_normal_did_not_assign(self):
        base = {("card_x", "s1"): stage04(), ("card_x", "s2"): stage04(status="abstained", sense=None)}
        ranked = RankedAssignments(
            base, [NORMAL, self.write_assigner([assigner_row("s1"), assigner_row("s2")])], MENUS, "pt")
        self.assertEqual(ranked.get(("card_x", "s1"))["selected_sense_id"], "own")
        filled = ranked.get(("card_x", "s2"))
        self.assertEqual((filled["status"], filled["selected_sense_id"]), ("assigned", "have_to"))
        self.assertEqual(ranked.counts["assigned"], 2)
        self.assertEqual(ranked.stats["DEEPSEEK v25"]["outranked_by_normal"], 1)

    def test_rows_for_a_changed_menu_or_an_unknown_sense_are_skipped(self):
        base = {("card_x", "s1"): stage04(), ("card_x", "s2"): stage04()}
        rows = [assigner_row("s1", menu="sha256:" + "b" * 64), assigner_row("s2", sense="not_on_menu")]
        ranked = RankedAssignments(base, [self.write_assigner(rows), NORMAL], MENUS, "pt")
        self.assertEqual(ranked.get(("card_x", "s1"))["selected_sense_id"], "own")
        self.assertEqual(ranked.get(("card_x", "s2"))["selected_sense_id"], "own")
        stats = ranked.stats["DEEPSEEK v25"]
        self.assertEqual((stats["skipped_menu_changed"], stats["skipped_sense_not_on_menu"]), (1, 1))

    def test_higher_assigner_wins_over_lower(self):
        base = {("card_x", "s1"): stage04()}
        high = self.write_assigner([assigner_row("s1", sense="have_to")], label="NORMAL-NEXT", version="v26")
        low = self.write_assigner([assigner_row("s1", sense="own")])
        ranked = RankedAssignments(base, [high, low, NORMAL], MENUS, "pt")
        self.assertEqual(ranked.get(("card_x", "s1"))["evidence"]["assigner"]["version"], "v26")
        self.assertEqual(ranked.stats["DEEPSEEK v25"]["outranked"], 1)

    def test_order_must_name_normal_once_and_match_the_language(self):
        path = self.write_assigner([assigner_row("s1")])
        with self.assertRaises(RankedAssignerError):
            RankedAssignments({}, [path], MENUS, "pt")
        with self.assertRaises(RankedAssignerError):
            RankedAssignments({}, [path, NORMAL], MENUS, "es")

    def test_layers_follow_the_release_layer_contract(self):
        base = {("card_x", "s1"): stage04()}
        ranked = RankedAssignments(base, [self.write_assigner([assigner_row("s1")]), NORMAL], MENUS, "pt")
        layer = ranked.layers("sha256:" + "c" * 64)["wsd_assigner:DEEPSEEK v25"]
        self.assertEqual(layer["selection_version"], "layer-selection/v1")
        self.assertEqual(layer["record_count"], 1)
        self.assertEqual(layer["parameters"]["rank"], 1)
        self.assertEqual(layer["requires"], {"sense_menu": "sha256:" + "c" * 64})

    def test_bad_rows_are_refused_on_load(self):
        bad = assigner_row("s1")
        del bad["selected_tuple"]
        with self.assertRaises(RankedAssignerError):
            load_assigner(self.write_assigner([bad]))


if __name__ == "__main__":
    unittest.main()
