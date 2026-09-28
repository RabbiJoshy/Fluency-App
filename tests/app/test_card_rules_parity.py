"""The pipeline's copy of the app's card rules agrees with the app.

Speech set-up filters cards before their senses load, so Merge Lemmas and
Exclude Cognates read decisions the pipeline precomputed
(fluency.enrichments.card_rules). If the two drift, a card merges or is set
aside differently depending on whether its set happened to be open.
"""

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

from fluency.enrichments.card_rules import card_cognate, lemma_group_key

ROOT = Path(__file__).resolve().parents[2]

ROWS = [
    {"word": "fue", "meanings": [
        {"headword": "ser", "pos": "VERB", "translation": "to be"},
        {"headword": "ir", "pos": "VERB", "translation": "to go"}]},
    {"word": "sé", "meanings": [
        {"headword": "ser", "pos": "VERB", "translation": "to be"},
        {"headword": "no sé", "pos": "PHRASE", "translation": "I don't know"}]},
    {"word": "tener", "meanings": [
        {"headword": "tener", "pos": "VERB", "translation": "to have"},
        {"headword": "tener cuidado", "pos": "PHRASE", "translation": "to be careful"}]},
    {"word": "al", "meanings": [{"headword": "al", "pos": "CONTRACTION", "translation": "to the"}]},
    {"word": "no", "meanings": [{"headword": "em", "pos": "prep", "translation": "in"}]},
    {"word": "estaba", "meanings": [{"headword": "estar", "pos": "VERB", "translation": "to be"}]},
    {"word": "problema", "meanings": [
        {"headword": "problema", "pos": "NOUN", "translation": "problem"},
        {"headword": "no hay problema", "pos": "PHRASE", "translation": "no problem",
         "metadata": {"multiword_evidence": [{"wsd_routing": "competitive_wsd"}]}}]},
    {"word": "idea", "meanings": [{"headword": "idea", "pos": "NOUN", "translation": "idea; notion (thought)"}]},
    {"word": "banco", "meanings": [
        {"headword": "banco", "pos": "NOUN", "translation": "bank"},
        {"headword": "banco", "pos": "NOUN", "translation": "school (of fish)"}]},
]
CONTRACTIONS = ["no"]
SCORES = {
    "problema": {"problema": {"problem": {"en": 0.88}}},
    "idea": {"idea": {"idea": {"en": 1.0, "pl": 0.9}, "notion": {"en": 0.6}}},
    "banco": {"banco": {"bank": {"en": 0.8}}},
}
MATCHES = {"idea": {"idea": {"idea": {"pl": "idea"}}}}


class ParityTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_python_and_js_decide_the_same(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const vocab = fs.readFileSync(process.env.VOCAB_JS, 'utf8');
            const pure = vocab.slice(vocab.indexOf('// lemma-merge-pure'), vocab.indexOf('// /lemma-merge-pure'));
            const cognates = fs.readFileSync(process.env.COGNATES_JS, 'utf8').replace(/^import .*$/mg, '');
            const context = { console, localStorage: { getItem: () => null, setItem: () => {} },
                document: { getElementById: () => null } };
            context.globalThis = context;
            vm.runInNewContext(pure + '\nglobalThis.isExpressionSenseForLemma = isExpressionSenseForLemma;\n' + cognates, context);
            const rows = JSON.parse(process.env.ROWS);
            const contractions = new Set(JSON.parse(process.env.CONTRACTIONS));
            const scores = JSON.parse(process.env.SCORES);
            const matches = JSON.parse(process.env.MATCHES);
            const out = rows.map(row => {
                const item = { ...row, is_contraction: contractions.has(row.word) };
                item.cognate_sense_map = scores[row.word] || null;
                item.cognate_sense_matches = matches[row.word] || null;
                const verdicts = ['en', 'pl'].map(code => {
                    const v = context.cardSenseCognate(item, code);
                    return v ? [v.score, v.word] : null;
                });
                return [context.lemmaGroupKey(item), verdicts];
            });
            process.stdout.write(JSON.stringify(out));
        """
        completed = subprocess.run(
            ["node", "-e", script], check=False, capture_output=True, text=True,
            env={**os.environ, "VOCAB_JS": str(ROOT / "app/js/vocab.js"),
                 "COGNATES_JS": str(ROOT / "app/js/cognates.js"),
                 "ROWS": json.dumps(ROWS), "CONTRACTIONS": json.dumps(CONTRACTIONS),
                 "SCORES": json.dumps(SCORES), "MATCHES": json.dumps(MATCHES)},
        )
        if completed.returncode != 0:
            self.fail(completed.stderr or completed.stdout)
        js = json.loads(completed.stdout)
        for row, (js_key, js_verdicts) in zip(ROWS, js):
            with self.subTest(word=row["word"]):
                self.assertEqual(lemma_group_key(row, CONTRACTIONS), js_key)
                for code, js_verdict in zip(("en", "pl"), js_verdicts):
                    py = card_cognate(row, SCORES.get(row["word"]), code, MATCHES.get(row["word"]))
                    self.assertEqual(list(py) if py else None, js_verdict, code)


if __name__ == "__main__":
    unittest.main()
