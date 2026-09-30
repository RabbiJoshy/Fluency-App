"""Slim index rows render exactly like full ones in the app.

slim_index_row removes fields no app code reads and the second copy of data
the release carries twice. The guarantee: every app function that reads a
row's senses -- sense pills and notes, reverse cues, cross references,
dictionary examples and provider, WSD frequency -- returns the same result for
the slim row as for the full one. The fixture is real rows from the es
(SpanishDict), pt, cs and fi 30-example releases.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

from fluency.release.index_shards import slim_index_row

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name("fixtures") / "full_index_rows.json"


def _function_source(text: str, name: str) -> str:
    start = text.index(f"function {name}(")
    depth, i = 0, text.index("{", start)
    while True:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
        if depth == 0:
            return text[start:i]


class SlimIndexRowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_slim_rows_are_smaller_and_only_remove(self) -> None:
        full = slim = 0
        for rows in self.rows.values():
            for row in rows:
                reduced = slim_index_row(row)
                self.assertEqual(set(reduced), set(row))
                full += len(json.dumps(row, ensure_ascii=False))
                slim += len(json.dumps(reduced, ensure_ascii=False))
        self.assertLess(slim * 3, full * 2)

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_app_reads_the_same_values(self) -> None:
        cards = (ROOT / "app/js/flashcards.js").read_text(encoding="utf-8")
        vocab = (ROOT / "app/js/vocab.js").read_text(encoding="utf-8")
        cues = (ROOT / "app/js/reverse-cues.js").read_text(encoding="utf-8")
        sliced = "\n".join([
            _function_source(cards, "canonicalRecord"),
            _function_source(cards, "dictionaryProviderForMeaning"),
            _function_source(cards, "extractCanonicalDictionaryExamples"),
            _function_source(cards, "senseCrossReferences"),
            _function_source(vocab, "referenceExamplesForMeaning"),
            _function_source(vocab, "projectedSenseFrequency"),
            _function_source(cues, "meaningFeatureList"),
            "function currentWsdPublicationProjection() { return 'supported_leaf'; }",
        ])
        pairs = {lang: [[row, slim_index_row(row)] for row in rows] for lang, rows in self.rows.items()}
        script = r"""
import fs from 'node:fs';
import vm from 'node:vm';
import * as ui from './app/js/card-metadata-pills.js';
import { selectReverseCueMeanings } from './app/js/reverse-cues.js';
const context = { ...ui };
vm.createContext(context);
vm.runInContext(process.env.SLICED + `
  this.api = { dictionaryProviderForMeaning, extractCanonicalDictionaryExamples, senseCrossReferences,
               referenceExamplesForMeaning, projectedSenseFrequency, meaningFeatureList };`, context);
const api = context.api;
const asMeaning = sense => ({ ...sense, meaning: sense.translation, pos: sense.pos || sense.part_of_speech,
                              id: sense.sense_id });
function project(row) {
  const meanings = (row.meanings || []).map(asMeaning);
  const unused = (row.unused_menu_senses || []).map(asMeaning);
  const all = [...meanings, ...unused];
  return {
    // It returns the chosen meaning objects; which ones, in which order, is the result.
    cues: JSON.stringify(selectReverseCueMeanings(meanings).map(m => m.sense_id)),
    senses: all.map(meaning => {
      const gloss = ui.projectWiktionaryGloss(meaning, meaning.translation).display;
      const options = { gloss, peerMeanings: ui.senseMetadataPeers(meaning, all, gloss), cardMeanings: all,
                        senseCount: all.length, allowInactivePrimary: true };
      return JSON.stringify({
        items: ui.senseMetadataItems(meaning),
        closed: ui.senseMetadataHTML(meaning, false, options),
        open: ui.senseMetadataHTML(meaning, true, options),
        presentation: ui.learnerSensePresentation(meaning, true, options),
        context: ui.contextWithoutSenseMetadata(meaning, true, options),
        provider: api.dictionaryProviderForMeaning(meaning),
        dictionary: api.extractCanonicalDictionaryExamples(meaning),
        references: api.senseCrossReferences(meaning),
        reference: api.referenceExamplesForMeaning(meaning),
        features: api.meaningFeatureList(meaning),
        frequency: api.projectedSenseFrequency(row, meaning, 0),
      });
    }),
  };
}
const pairs = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = [];
for (const [lang, list] of Object.entries(pairs)) {
  list.forEach(([full, slim], index) => out.push({ lang, index, full: project(full), slim: project(slim) }));
}
process.stdout.write(JSON.stringify(out));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script], cwd=ROOT,
            input=json.dumps(pairs), capture_output=True, text=True,
            env={"PATH": shutil.os.environ["PATH"], "SLICED": sliced},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        compared = json.loads(result.stdout)
        self.assertEqual(len(compared), sum(len(rows) for rows in self.rows.values()))
        senses = 0
        for case in compared:
            with self.subTest(lang=case["lang"], row=case["index"]):
                self.assertEqual(case["slim"]["cues"], case["full"]["cues"])
                self.assertEqual(len(case["slim"]["senses"]), len(case["full"]["senses"]))
                for full, slim in zip(case["full"]["senses"], case["slim"]["senses"]):
                    self.assertEqual(slim, full)
                    senses += 1
        self.assertGreater(senses, 100)


if __name__ == "__main__":
    unittest.main()
