"""Wiktionary inflected surfaces should show conjugated English, not the lemma gloss."""

from pathlib import Path
import json
import shutil
import subprocess
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REVERSE_CUES = REPOSITORY_ROOT / "app" / "js" / "reverse-cues.js"


class WiktionaryProductionCueTests(unittest.TestCase):
    def test_czech_jsem_becomes_i_am(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue } from %s;

const meaning = {
    pos: 'verb',
    translation: 'to be',
    headword: 'být',
    metadata: {
        specialist_features: [
            { kind: 'surface_mark', value: 'person=1' },
            { kind: 'surface_mark', value: 'number=singular' },
            { kind: 'surface_mark', value: 'tense=present' },
            { kind: 'surface_mark', value: 'mood=indicative' },
        ],
    },
};
const cases = [
    [{ targetWord: 'jsem' }, meaning, 'I am'],
    [{ targetWord: 'je' }, { ...meaning, metadata: { specialist_features: [
        { kind: 'surface_mark', value: 'person=3' },
        { kind: 'surface_mark', value: 'number=singular' },
        { kind: 'surface_mark', value: 'tense=present' },
        { kind: 'surface_mark', value: 'mood=indicative' },
    ] } }, 'he/she/it is'],
    [{ targetWord: 'jsme' }, { ...meaning, metadata: { specialist_features: [
        { kind: 'surface_mark', value: 'person=1' },
        { kind: 'surface_mark', value: 'number=plural' },
        { kind: 'surface_mark', value: 'tense=present' },
        { kind: 'surface_mark', value: 'mood=indicative' },
    ] } }, 'we are'],
    [{ targetWord: 'být' }, meaning, null],
    [{ targetWord: 'tem' }, {
        pos: 'verb',
        translation: 'to have',
        headword: 'ter',
        metadata: { specialist_features: [
            { kind: 'surface_mark', value: 'person=3' },
            { kind: 'surface_mark', value: 'number=singular' },
            { kind: 'surface_mark', value: 'tense=present' },
            { kind: 'surface_mark', value: 'mood=indicative' },
        ] },
    }, 'he/she/it has'],
];
const out = cases.map(([card, sense, expected]) => ({
    expected,
    actual: englishProductionCue(card, sense, null),
}));
console.log(JSON.stringify(out));
""" % json.dumps(REVERSE_CUES.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        rows = json.loads(result.stdout)
        for row in rows:
            self.assertEqual(row["actual"], row["expected"], row)
