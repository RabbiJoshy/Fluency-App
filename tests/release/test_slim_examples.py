"""Slim example shards read exactly like full ones in the app.

A slim shard drops everything the app never reads. The guarantee is that the
app's own accessors -- provenance, confidence tier, report ids -- return the
same values for a slim record expanded by vocab.js as for the full record.
The fixture is real records from the es, pt, cs and fi 30-example releases.
"""

import copy
import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from fluency.release.example_shards import ExampleShardError, _source_defaults, slim_example

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name("fixtures") / "full_examples.json"


def _function_source(text: str, name: str) -> str:
    start = text.index(f"function {name}(")
    depth, i = 0, text.index("{", start)
    while True:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
        if depth == 0:
            return text[start:i]


def _variants(examples: list[dict]) -> list[dict]:
    """Edge cases the real sample may not contain."""

    base = next(e for e in examples if e["source"] == "opensubtitles")
    odd = copy.deepcopy(base)
    odd["attribution"] = "someone else"
    odd["license"] = "CC0"
    odd["assignment_method"] = "manual"
    odd["example_id"] = "custom-id"
    odd["source_url"] = "https://example.org/a"
    odd["sentence_url"] = "https://example.org/b"
    odd["metadata"]["source_title"] = {"title": "A Film", "series": "A Show"}
    bare = copy.deepcopy(base)
    bare.pop("provenance", None)
    bare["metadata"].pop("wsd", None)
    return [odd, bare]


class SlimExampleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.examples = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.examples += _variants(self.examples)

    def test_unknown_fields_fail_rather_than_vanish(self) -> None:
        example = copy.deepcopy(self.examples[0])
        example["new_field"] = 1
        with self.assertRaises(ExampleShardError):
            slim_example(example, {})

    def test_slim_records_are_much_smaller(self) -> None:
        defaults = _source_defaults({"c": {"m": [self.examples]}})
        full = len(json.dumps(self.examples, ensure_ascii=False))
        slim = len(json.dumps([slim_example(e, defaults) for e in self.examples], ensure_ascii=False))
        self.assertLess(slim * 5, full)

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_app_reads_the_same_values(self) -> None:
        defaults = _source_defaults({"c": {"m": [self.examples]}})
        slim = [slim_example(e, defaults) for e in self.examples]
        vocab = (ROOT / "app/js/vocab.js").read_text(encoding="utf-8")
        pure = vocab[vocab.index("// slim-example-pure"):vocab.index("// /slim-example-pure")]
        cards = (ROOT / "app/js/flashcards.js").read_text(encoding="utf-8")
        tiers = re.search(r"const WSD_CONFIDENCE_TIER = .*?;\nconst WSD_CONFIDENCE_UNKNOWN = \d+;", cards, re.S)
        accessors = "\n".join([
            tiers.group(0),
            _function_source(cards, "exampleWsdMeta"),
            _function_source(cards, "exampleConfidenceTier"),
            _function_source(cards, "normalizedExampleProvenance"),
        ])
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const context = {};
            vm.createContext(context);
            vm.runInContext(process.env.PURE + '\n' + process.env.ACCESSORS + `
                function project(x) {
                    return {
                        target: x.target, english: x.english, source: x.source,
                        method: x.assignment_method, exampleId: x.example_id || '',
                        reportRecordId: x.source_record_id || x.sentence_id || '',
                        sentenceId: x.metadata?.sentence_id || '',
                        title: x.source_title || x.metadata?.source_title || null,
                        translationSource: x.translation_source || '',
                        urls: [x.source_url || '', x.sentence_url || ''],
                        provenance: normalizedExampleProvenance(x),
                        tier: exampleConfidenceTier(x),
                    };
                }
                this.project = project;
                this.expand = expandSlimExamplePayload;
            `, context);
            const input = JSON.parse(fs.readFileSync(0, 'utf8'));
            const manifest = { example_format: 'slim-example/v1', sources: input.sources };
            const expanded = context.expand({ c: { m: [input.slim] } }, manifest).c.m[0];
            process.stdout.write(JSON.stringify({
                full: input.full.map(x => context.project(x)),
                slim: expanded.map(x => context.project(x)),
            }));
        """
        result = subprocess.run(
            ["node", "-e", script],
            input=json.dumps({"full": self.examples, "slim": slim, "sources": defaults}),
            capture_output=True, text=True, check=True,
            env={**os.environ, "PURE": pure, "ACCESSORS": accessors},
        )
        projected = json.loads(result.stdout)
        self.assertEqual(len(projected["full"]), len(self.examples))
        for index, (full, expanded) in enumerate(zip(projected["full"], projected["slim"])):
            with self.subTest(index=index, source=self.examples[index]["source"]):
                self.assertEqual(expanded, full)


if __name__ == "__main__":
    unittest.main()
