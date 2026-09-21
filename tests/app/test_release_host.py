"""Release files are served by the separate Fluency-Releases Pages site."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


APP = Path(__file__).resolve().parents[2] / "app"

RUNNER = r"""
    const fs = require('node:fs');
    const vm = require('node:vm');
    const source = fs.readFileSync(process.argv[2], 'utf8').replace(/^export /gm, '');
    const out = {};
    for (const href of JSON.parse(process.argv[3])) {
        const location = new URL(href);
        const context = { URL, window: { location } };
        vm.runInNewContext(source + '\n;globalThis.api = { releaseUrl };', context);
        out[href] = context.api.releaseUrl('releases/es/speech/r1/manifest.json');
    }
    console.log(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
class ReleaseHostTests(unittest.TestCase):
    def test_release_paths_map_to_the_release_site(self) -> None:
        pages = [
            "https://rabbijoshy.github.io/Fluency-App/",
            "http://localhost:8923/app/",
            "http://localhost:8912/",
        ]
        result = subprocess.run(
            ["node", "-", str(APP / "js/release-host.js"), json.dumps(pages)],
            input=RUNNER, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        got = json.loads(result.stdout)
        published = "https://rabbijoshy.github.io/Fluency-Releases/es/speech/r1/manifest.json"
        self.assertEqual(got[pages[0]], published)
        # The repository preview has no releases of its own.
        self.assertEqual(got[pages[1]], published)
        # The local speech pilot mounts workspace releases at /releases/.
        self.assertEqual(got[pages[2]], "releases/es/speech/r1/manifest.json")

    def test_no_module_resolves_releases_against_the_app_itself(self) -> None:
        offenders = [
            f"{path.name}:{number}"
            for path in sorted((APP / "js").glob("*.js")) if path.name != "release-host.js"
            for number, line in enumerate(path.read_text().splitlines(), 1)
            if re.search(r"appAssetPath\(\s*[`'\"]releases/", line)
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
