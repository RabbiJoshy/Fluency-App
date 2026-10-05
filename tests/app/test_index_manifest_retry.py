"""vocab.js loadIndexShardManifest remembers only a definite answer.

Sharded releases publish no vocabulary.index.json, so caching a transient
manifest failure as "no shards" left every later set load on a 404 until the
page was reloaded.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def manifest_loader_source() -> str:
    source = (APP_ROOT / "js" / "vocab.js").read_text(encoding="utf-8")
    start = source.index("let indexShardManifest")
    end = source.index("function hydrateIndexColumns")
    return source[start:end]


@unittest.skipUnless(shutil.which("node"), "Node.js required")
class IndexManifestRetryTests(unittest.TestCase):
    def run_js(self, body: str) -> dict:
        script = (
            "const loadedIndexRowShards = new Set();\n"
            + manifest_loader_source()
            + "\n(async () => {\n" + body + "\n})().catch(e => { console.error(e); process.exit(1); });"
        )
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_network_failure_is_retried_on_the_next_load(self) -> None:
        out = self.run_js(r"""
            const good = { shards: [{ file: 'r0' }], columns: 'vocabulary.index.columns.json' };
            const replies = [() => { throw new Error('offline'); }, () => { throw new Error('offline'); },
                             () => ({ ok: true, status: 200, json: async () => good })];
            let calls = 0;
            globalThis.fetch = async () => replies[calls++]();
            const config = { indexPath: 'https://x/app/vocabulary.index.json' };
            const first = await loadIndexShardManifest(config);
            const second = await loadIndexShardManifest(config);
            console.log(JSON.stringify({ first, second: Boolean(second), calls }));
        """)
        self.assertIsNone(out["first"])
        self.assertTrue(out["second"])
        self.assertEqual(out["calls"], 3)

    def test_one_blip_is_retried_within_the_same_load(self) -> None:
        out = self.run_js(r"""
            const good = { shards: [{ file: 'r0' }], columns: 'vocabulary.index.columns.json' };
            const replies = [() => ({ ok: false, status: 503 }),
                             () => ({ ok: true, status: 200, json: async () => good })];
            let calls = 0;
            globalThis.fetch = async () => replies[calls++]();
            const found = await loadIndexShardManifest({ indexPath: 'https://x/app/vocabulary.index.json' });
            console.log(JSON.stringify({ found: Boolean(found), calls }));
        """)
        self.assertTrue(out["found"])
        self.assertEqual(out["calls"], 2)

    def test_a_release_without_shards_is_remembered(self) -> None:
        out = self.run_js(r"""
            let calls = 0;
            globalThis.fetch = async () => { calls++; return { ok: false, status: 404 }; };
            const config = { indexPath: 'https://x/app/vocabulary.index.json' };
            await loadIndexShardManifest(config);
            await loadIndexShardManifest(config);
            console.log(JSON.stringify({ calls }));
        """)
        self.assertEqual(out["calls"], 1)


if __name__ == "__main__":
    unittest.main()
