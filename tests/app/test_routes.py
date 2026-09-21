"""Shareable links: route parsing, formatting and old query-link translation."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


APP = Path(__file__).resolve().parents[2] / "app"
ROUTES = APP / "js/routes.js"

# routes.js is an ES module; strip `export` and run its pure functions in a vm
# context. With no `window`, it installs no browser hooks.
RUNNER = r"""
    const fs = require('node:fs');
    const vm = require('node:vm');
    const source = fs.readFileSync(process.argv[2], 'utf8').replace(/^export /gm, '');
    const context = { URLSearchParams };
    vm.runInNewContext(source + '\n;globalThis.api = { parseRoute, formatRoute, legacyRoute, languageKeyFor, routeCodeFor };', context);
    const cases = JSON.parse(process.argv[3]);
    const out = cases.map(([fn, ...args]) => context.api[fn](...args));
    console.log(JSON.stringify(out));
"""

LANGUAGES = {
    "spanish": {"routeCode": "es"},
    "portuguese": {"routeCode": "pt"},
    "portuguese_brazilian": {"routeCode": "pt-br"},
}


@unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
class RouteTests(unittest.TestCase):
    def run_js(self, *cases):
        result = subprocess.run(
            ["node", "-", str(ROUTES), json.dumps(cases)], input=RUNNER,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_parse_each_route(self) -> None:
        got = self.run_js(
            ["parseRoute", ""],
            ["parseRoute", "#/"],
            ["parseRoute", "#/es"],
            ["parseRoute", "#/es/w/unidos"],
            ["parseRoute", "#/es/w/%C3%A9l"],
            ["parseRoute", "#/artist/bad-bunny"],
            ["parseRoute", "#/artist/bad-bunny/extra"],
            ["parseRoute", "#/es/songs"],
            ["parseRoute", "#/about"],
            ["parseRoute", "#/tutorial"],
            ["parseRoute", "#/walkthrough"],
            ["parseRoute", "#/es/x/y/z"],
            ["parseRoute", "#/fr/live"],
        )
        self.assertEqual(got[0], {"kind": "home"})
        self.assertEqual(got[1], {"kind": "home"})
        self.assertEqual(got[2], {"kind": "language", "language": "es"})
        self.assertEqual(got[3], {"kind": "word", "language": "es", "surface": "unidos"})
        self.assertEqual(got[4]["surface"], "él")
        self.assertEqual(got[5], {"kind": "artist", "artist": "bad-bunny", "scope": "main"})
        self.assertEqual(got[6]["scope"], "extra")
        self.assertEqual(got[7], {"kind": "songs", "language": "es"})
        self.assertEqual([g["kind"] for g in got[8:11]], ["about", "tutorial", "walkthrough"])
        self.assertEqual(got[11], {"kind": "unknown"})
        self.assertEqual(got[12], {"kind": "live", "language": "fr"})

    def test_format_round_trips(self) -> None:
        hashes = ["#/es", "#/es/w/unidos", "#/pt-br/w/%C3%A9l", "#/artist/bad-bunny",
                  "#/artist/bad-bunny/extra", "#/es/songs", "#/fr/live", "#/about",
                  "#/tutorial", "#/walkthrough"]
        parsed = self.run_js(*[["parseRoute", h] for h in hashes])
        formatted = self.run_js(*[["formatRoute", p] for p in parsed])
        self.assertEqual(formatted, hashes)
        self.assertEqual(self.run_js(["formatRoute", {"kind": "home"}]), [""])

    def test_old_query_links_translate(self) -> None:
        got = self.run_js(
            ["legacyRoute", "?artist=bad-bunny"],
            ["legacyRoute", "?mode=badbunny"],
            ["legacyRoute", "?artist=bad-bunny&scope=extra&lyricsRelease=r1"],
            ["legacyRoute", "?artist=custom&language=spanish"],
            ["legacyRoute", "?about=1&speechRelease=abc"],
            ["legacyRoute", "?language=french"],
            ["legacyRoute", "?playlistLive=1&language=spanish"],
            ["legacyRoute", "?speechRelease=abc&perf=1"],
        )
        routes = [g["route"] for g in got]
        searches = [g["search"] for g in got]
        self.assertEqual(routes[0], {"kind": "artist", "artist": "bad-bunny", "scope": "main"})
        self.assertEqual(routes[1], routes[0])
        self.assertEqual(searches[1], "")
        self.assertEqual(routes[2]["scope"], "extra")
        self.assertEqual(searches[2], "?lyricsRelease=r1")
        self.assertEqual(routes[3], {"kind": "songs", "language": "spanish"})
        self.assertEqual(searches[3], "")
        self.assertEqual(routes[4], {"kind": "about"})
        self.assertEqual(searches[4], "?speechRelease=abc")
        self.assertEqual(routes[5], {"kind": "language", "language": "french"})
        self.assertEqual(routes[6], {"kind": "live", "language": "spanish"})
        self.assertEqual(searches[6], "")
        # Developer switches are not routes and are left exactly as they were.
        self.assertIsNone(routes[7])
        self.assertEqual(searches[7], "?speechRelease=abc&perf=1")

    def test_language_tokens(self) -> None:
        got = self.run_js(
            ["languageKeyFor", "es", LANGUAGES],
            ["languageKeyFor", "ES", LANGUAGES],
            ["languageKeyFor", "spanish", LANGUAGES],
            ["languageKeyFor", "pt-br", LANGUAGES],
            ["languageKeyFor", "pt", LANGUAGES],
            ["languageKeyFor", "xx", LANGUAGES],
            ["routeCodeFor", "portuguese_brazilian", LANGUAGES],
            ["routeCodeFor", "klingon", LANGUAGES],
        )
        self.assertEqual(got, ["spanish", "spanish", "spanish", "portuguese_brazilian",
                               "portuguese", None, "pt-br", "klingon"])


class RouteWiringTests(unittest.TestCase):
    def test_every_language_declares_a_unique_route_code(self) -> None:
        languages = json.loads((APP / "config/config.json").read_text())["languages"]
        codes = [cfg.get("routeCode") for cfg in languages.values()]
        self.assertTrue(all(codes), codes)
        self.assertEqual(len(codes), len(set(codes)))

    def test_no_module_still_builds_old_query_links(self) -> None:
        old_forms = re.compile(
            r"searchParams\.(?:get|has|set)\('(?:artist|scope|about|playlistLive)'\)|\?artist=\$|mode=badbunny'")
        offenders = [
            f"{path.name}:{number}"
            for path in sorted((APP / "js").glob("*.js")) if path.name != "routes.js"
            for number, line in enumerate(path.read_text().splitlines(), 1)
            if old_forms.search(line) and not line.lstrip().startswith("//")
        ]
        self.assertEqual(offenders, [])

    def test_routes_module_is_imported_under_one_version(self) -> None:
        tags = set()
        for path in (APP / "js").glob("*.js"):
            tags.update(re.findall(r"routes\.js\?v=([0-9A-Za-z]+)", path.read_text()))
        self.assertEqual(len(tags), 1, tags)


if __name__ == "__main__":
    unittest.main()
