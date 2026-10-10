"""Tests for staging environment detection, storage isolation, and deliberate promotion."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"


@unittest.skipUnless(shutil.which("node"), "Node.js required for JS evaluation checks")
class StagingEnvJsTests(unittest.TestCase):
    def test_candidate_paths_use_matching_deck_and_merge_data_only_in_staging(self) -> None:
        script = r"""
        const fs = require('node:fs');
        const vm = require('node:vm');
        const source = fs.readFileSync(process.argv[2], 'utf8').replace(/^import .*\n/gm, '');
        async function run(staging) {
            const original = { languages: { spanish: { routeCode: 'es',
                indexPath: 'production-index', mergeExceptionsPath: 'production-merges' } } };
            const context = { URLSearchParams, IS_STAGING: staging,
                window: { location: { search: '?esRelease=es-headway-candidate' } },
                config: {}, cefrLevelsConfig: null, activeArtist: null,
                getCandidateDeckOverrides: () => ({}), releaseUrl: p => p,
                fetch: async p => ({ json: async () => p.startsWith('config/config.json')
                    ? structuredClone(original) : {} }),
                console, alert: m => { throw Error(m); } };
            vm.runInNewContext(source, context);
            await context.window.loadConfig();
            return context.config.languages.spanish;
        }
        Promise.all([run(true), run(false)]).then(([staging, production]) =>
            console.log(JSON.stringify({ staging, production })));
        """
        res = subprocess.run(['node', '-', str(APP / 'js/config.js')], input=script,
                             text=True, capture_output=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        base = 'releases/es/speech/es-headway-candidate/app/'
        self.assertEqual(data['staging']['indexPath'], base + 'vocabulary.index.json')
        self.assertEqual(data['staging']['studyStructurePath'], base + 'study-structure.json')
        self.assertEqual(data['staging']['mergeExceptionsPath'], base + 'merge-exceptions.json')
        self.assertEqual(data['production']['indexPath'], 'production-index')
        self.assertEqual(data['production']['mergeExceptionsPath'], 'production-merges')

    def test_environment_detection_and_user_isolation(self) -> None:
        script = r"""
        const fs = require('node:fs');
        const vm = require('node:vm');
        const source = fs.readFileSync(process.argv[2], 'utf8').replace(/^export /gm, '');

        function runInHost(hostname, explicitEnv) {
            const context = {
                window: {
                    location: { hostname },
                    ...(explicitEnv ? { __FLUENCY_ENV__: explicitEnv } : {})
                },
                localStorage: {
                    store: {},
                    getItem(k) { return this.store[k] || null; },
                    setItem(k, v) { this.store[k] = String(v); },
                    removeItem(k) { delete this.store[k]; }
                }
            };
            vm.runInNewContext(source + '; globalThis.out = { ' +
                'env: detectEnvironment(), ' +
                'syncUser: getIsolatedSyncUser("JST"), ' +
                'syncUserAlreadyPrefixed: getIsolatedSyncUser("stg_JST")' +
            '};', context);
            return context.out;
        }

        const prod = runInHost('rabbijoshy.github.io', null);
        const stgHost = runInHost('fluency-staging.pages.dev', null);
        const stgExplicit = runInHost('localhost', 'staging');

        console.log(JSON.stringify({ prod, stgHost, stgExplicit }));
        """
        res = subprocess.run(["node", "-", str(APP / "js/env.js")], input=script, text=True, capture_output=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)

        # Production assertions
        self.assertFalse(data["prod"]["env"]["isStaging"])
        self.assertEqual(data["prod"]["env"]["env"], "production")
        self.assertEqual(data["prod"]["syncUser"], "JST")

        # Staging on Cloudflare Pages assertions
        self.assertTrue(data["stgHost"]["env"]["isStaging"])
        self.assertEqual(data["stgHost"]["env"]["env"], "staging")
        self.assertEqual(data["stgHost"]["syncUser"], "stg_JST")
        self.assertEqual(data["stgHost"]["syncUserAlreadyPrefixed"], "stg_JST")

        # Explicit staging flag assertions
        self.assertTrue(data["stgExplicit"]["env"]["isStaging"])
        self.assertEqual(data["stgExplicit"]["syncUser"], "stg_JST")

    def test_candidate_deck_overrides(self) -> None:
        script = r"""
        const fs = require('node:fs');
        const vm = require('node:vm');
        const source = fs.readFileSync(process.argv[2], 'utf8').replace(/^export /gm, '');

        const storage = {};
        const context = {
            window: {
                location: { hostname: 'fluency-staging.pages.dev' },
                __FLUENCY_ENV__: 'staging'
            },
            localStorage: {
                getItem(k) { return storage[k] || null; },
                setItem(k, v) { storage[k] = String(v); },
                removeItem(k) { delete storage[k]; }
            }
        };

        vm.runInNewContext(source + '; ' +
            'setCandidateDeckOverride("spanish", "es-speech-v24-candidate"); ' +
            'const afterSet = getCandidateDeckOverrides(); ' +
            'clearCandidateDeckOverrides(); ' +
            'const afterClear = getCandidateDeckOverrides(); ' +
            'globalThis.out = { afterSet, afterClear };', context);

        console.log(JSON.stringify(context.out));
        """
        res = subprocess.run(["node", "-", str(APP / "js/env.js")], input=script, text=True, capture_output=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["afterSet"].get("spanish"), "es-speech-v24-candidate")
        self.assertEqual(data["afterClear"], {})


class StagingBuildTests(unittest.TestCase):
    def test_staging_build_stamps_environment_and_generates_manifest(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_pages_site", ROOT / "scripts/build_pages_site.py")
        build_pages_site = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_pages_site)

        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            build_pages_site.build(site, "HEAD", version="stg-test1234", env="staging")

            # Check index.html carries staging environment injection
            index_content = (site / "index.html").read_text(encoding="utf-8")
            self.assertIn("window.__FLUENCY_ENV__ = 'staging';", index_content)
            self.assertIn("?v=stg-test1234", index_content)

            # Check app_environment.json is generated
            env_file = site / "config/app_environment.json"
            self.assertTrue(env_file.exists())
            env_data = json.loads(env_file.read_text(encoding="utf-8"))
            self.assertEqual(env_data["environment"], "staging")
            self.assertEqual(env_data["version"], "stg-test1234")

    def test_env_badge_hidden_in_css(self) -> None:
        css = (APP / "css/style.css").read_text(encoding="utf-8")
        self.assertIn(".env-badge[hidden]", css)
        self.assertIn("display: none !important;", css)


class StagingScriptsTests(unittest.TestCase):
    def test_staging_scripts_exist_and_are_executable(self) -> None:
        deploy_script = ROOT / "scripts/deploy_staging.py"
        promote_script = ROOT / "scripts/promote_to_production.py"
        self.assertTrue(deploy_script.is_file())
        self.assertTrue(promote_script.is_file())

        res_deploy = subprocess.run([sys.executable, str(deploy_script), "--help"], capture_output=True, text=True)
        self.assertEqual(res_deploy.returncode, 0)
        self.assertIn("Staging", res_deploy.stdout)

        res_promote = subprocess.run([sys.executable, str(promote_script), "--help"], capture_output=True, text=True)
        self.assertEqual(res_promote.returncode, 0)
        self.assertIn("promote", res_promote.stdout.lower())


if __name__ == "__main__":
    unittest.main()
