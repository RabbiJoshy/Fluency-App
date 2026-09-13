from datetime import UTC, datetime
import json
import bz2
from pathlib import Path
import tempfile
import unittest

from fluency.core.identity import build_card_id
from fluency.core.workspace import Workspace
from fluency.harvest.pooling import phrase_set, redundancy_penalty, token_set
from fluency.harvest.runner import HarvestRunError, harvest_run_stage
from fluency.pipeline.planning import create_pipeline_plan, load_pipeline_profile


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = (
    REPOSITORY_ROOT
    / "config/pipelines/fr/speech/rehearsal-20x3.json"
)
SURFACES = (
    "amour",
    "avec",
    "bonjour",
    "chat",
    "dans",
    "encore",
    "femme",
    "grand",
    "homme",
    "ici",
    "jamais",
    "jour",
    "maison",
    "monde",
    "nuit",
    "petit",
    "prendre",
    "sans",
    "temps",
    "voir",
)

# Three unrelated frames, so a card can legitimately hold three examples.
FRAMES = (
    "Voici vraiment {surface} devant nous maintenant.",
    "Personne ne comprend pourquoi {surface} arrive si tard.",
    "Elle a dit que {surface} changerait tout cette semaine.",
)


class HarvestRunnerTests(unittest.TestCase):
    def _build_run(self, root: Path) -> tuple[Workspace, Path, Path]:
        workspace = Workspace.initialize(root / "workspace")
        profile = load_pipeline_profile(PROFILE_PATH)
        run = create_pipeline_plan(
            workspace,
            profile,
            started_at=datetime(2026, 8, 22, 13, 0, tzinfo=UTC),
            suffix="1234abcd",
        )
        inventory_root = run / "stages/01_inventory/output"
        inventory_root.mkdir(parents=True)
        cards = [
            {
                "card_id": build_card_id("fr", surface),
                "surface_key": surface,
                "display_form": surface,
                "rank": rank,
            }
            for rank, surface in enumerate(SURFACES, start=1)
        ]
        (inventory_root / "inventory.json").write_text(
            json.dumps(
                {
                    "inventory_version": "surface-inventory/v1",
                    "language": "fr",
                    "cards": cards,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        frequency = {
            token: rank
            for rank, token in enumerate(
                (*SURFACES, "voici", "vraiment", "devant", "nous", "maintenant", "souvent", "ensemble"),
                start=1,
            )
        }
        (inventory_root / "frequency-ranks.json").write_text(
            json.dumps(frequency, ensure_ascii=False), encoding="utf-8"
        )

        snapshot = workspace.root / "raw/tatoeba/fr-en/tatoeba-2026-08-22-fr-en"
        snapshot.mkdir(parents=True)
        metadata = {
            "snapshot_version": "tatoeba-weekly-snapshot/v1",
            "snapshot_id": "tatoeba-2026-08-22-fr-en",
            "target_language": "fr",
            "target_code": "fra",
            "translation_language": "en",
            "translation_code": "eng",
            "license": "CC BY 2.0 FR",
            "license_url": "https://creativecommons.org/licenses/by/2.0/fr/",
            "attribution": "Tatoeba contributors",
            "source_url": "https://tatoeba.org/en/downloads",
            "source_files": {
                "target_sentences": {
                    "filename": "fra_sentences_detailed.tsv.bz2",
                    "url": "https://downloads.tatoeba.org/exports/per_language/fra/fra_sentences_detailed.tsv.bz2",
                },
                "translation_sentences": {
                    "filename": "eng_sentences_detailed.tsv.bz2",
                    "url": "https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences_detailed.tsv.bz2",
                },
                "links": {
                    "filename": "eng-fra_links.tsv.bz2",
                    "url": "https://downloads.tatoeba.org/exports/per_language/eng/eng-fra_links.tsv.bz2",
                },
            },
        }
        (snapshot / "snapshot.json").write_text(json.dumps(metadata), encoding="utf-8")
        target_rows: list[str] = []
        translation_rows: list[str] = []
        link_rows: list[str] = []
        sentence_number = 1000
        for surface in SURFACES:
            # Structurally different sentences, not one sentence three ways.
            # These used to differ only in a trailing adverb, which is precisely
            # the agreement family the redundancy rule now collapses -- so the
            # fixture was testing that rule rather than the pool mechanics it
            # means to cover. test_collapses_agreement_families pins the
            # collapse itself.
            for variant in FRAMES:
                sentence_number += 2
                translation_id = sentence_number - 1
                target_id = sentence_number
                translation_rows.append(
                    f"{translation_id}\teng\tThis shows {surface} very clearly.\t"
                    "EnglishUser\t2026-08-01 10:00:00\t\\N"
                )
                target_rows.append(
                    f"{target_id}\tfra\t{variant.format(surface=surface)}\t"
                    "FrenchUser\t2026-08-01 10:00:00\t\\N"
                )
                link_rows.append(f"{translation_id}\t{target_id}")
        for filename, rows in (
            ("fra_sentences_detailed.tsv.bz2", target_rows),
            ("eng_sentences_detailed.tsv.bz2", translation_rows),
            ("eng-fra_links.tsv.bz2", link_rows),
        ):
            with bz2.open(snapshot / filename, "wt", encoding="utf-8") as stream:
                stream.write("\n".join(rows) + "\n")
        return workspace, run, snapshot

    def test_builds_auditable_run_owned_candidate_pool(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, run, snapshot = self._build_run(Path(directory))
            output = harvest_run_stage(
                REPOSITORY_ROOT,
                workspace,
                run_id=run.name,
                language="fr",
                mode="speech",
                source_snapshots={"tatoeba": snapshot},
                started_at=datetime(2026, 8, 22, 13, 5, tzinfo=UTC),
            )
            candidates = json.loads((output / "candidates.json").read_text(encoding="utf-8"))
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            records = [
                json.loads(line)
                for line in (output / "sentence-bank.jsonl").read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(candidates["sources"], ["tatoeba"])
            self.assertEqual(len(candidates["cards"]), 20)
            self.assertTrue(all(len(card["candidates"]) == 3 for card in candidates["cards"]))
            self.assertEqual(report["retained_candidate_matches"], 60)
            self.assertFalse(report["release_blocked_by_shortfall"])
            self.assertEqual(len(records), 60)
            self.assertTrue(all(record["source"]["attribution"] for record in records))
            self.assertEqual(report["fallbacks"], [])
            self.assertIn("source_tatoeba", manifest["inputs"])
            contract = json.loads(
                (run / "stages/03_sentence_harvest/contract.json").read_text(encoding="utf-8")
            )
            self.assertEqual(contract["status"], "complete")

            with self.assertRaises(HarvestRunError):
                harvest_run_stage(
                    REPOSITORY_ROOT,
                    workspace,
                    run_id=run.name,
                    language="fr",
                    mode="speech",
                    source_snapshots={"tatoeba": snapshot},
                )

    def test_rejects_source_snapshot_outside_workspace_raw(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, run, snapshot = self._build_run(root)
            outside = root / "old-repo-copy"
            outside.mkdir()
            with self.assertRaisesRegex(HarvestRunError, "workspace raw"):
                harvest_run_stage(
                    REPOSITORY_ROOT,
                    workspace,
                    run_id=run.name,
                    language="fr",
                    mode="speech",
                    source_snapshots={"tatoeba": outside},
                )

    def test_rejects_source_not_selected_by_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace, run, snapshot = self._build_run(Path(directory))
            with self.assertRaisesRegex(HarvestRunError, "exactly match"):
                harvest_run_stage(
                    REPOSITORY_ROOT,
                    workspace,
                    run_id=run.name,
                    language="fr",
                    mode="speech",
                    source_snapshots={"opensubtitles": snapshot},
                )


if __name__ == "__main__":
    unittest.main()


class RedundancyTests(unittest.TestCase):
    """An agreement family is one example, however many rows carry it.

    Tatoeba contributors write these on purpose, and they arrived on cards in
    force: three of `nada`'s five Spanish examples were "Yo no tengo nada que
    ver con esto/eso/en eso", and a 100-card audit found one sentence repeated
    on 43 French cards and 22 Portuguese.

    Vocabulary overlap alone cannot see it. On sentences this short the two or
    three words that differ are a large share of the vocabulary, so any
    threshold loose enough to catch the family also merges unrelated sentences.
    The word-for-word run they share is what identifies it.
    """

    def _redundant(self, first: str, second: str) -> int:
        return redundancy_penalty(
            token_set(first),
            [token_set(second)],
            subject_phrases=phrase_set(first),
            other_phrases=[phrase_set(second)],
        )

    def test_collapses_agreement_families(self) -> None:
        for first, second in (
            ("No tengo nada que ver con este asunto", "No tengo nada que ver con él"),
            ("Vous etes plus grand que moi", "Vous etes plus grande que moi"),
        ):
            with self.subTest(first=first):
                self.assertTrue(self._redundant(first, second))

    def test_keeps_distinct_uses_of_one_expression(self) -> None:
        # Both use `de vez en cuando`, which is four tokens and so cannot on its
        # own make two sentences the same example. A card must still be able to
        # show an expression more than once in different company.
        self.assertFalse(
            self._redundant(
                "Es bueno saber que de vez en cuando",
                "Estás aquí por mí de vez en cuando",
            )
        )

    def test_keeps_unrelated_sentences(self) -> None:
        self.assertFalse(
            self._redundant(
                "Le he visto una vez en el tren",
                "Él me llamó al teléfono una y otra vez",
            )
        )
