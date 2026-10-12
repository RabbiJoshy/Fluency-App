"""activeKnownLanguages is asked once per word; it must not re-read storage each time.

Opening a deck asked ~140,000 times, each re-reading and re-parsing saved
settings: a half-second freeze. The answer is now held for one pass and dropped
when a setting changes, so it must still never be stale.
"""

import os
import shutil
import subprocess
import unittest
from pathlib import Path

COGNATES = Path(__file__).resolve().parents[2] / "app/js/cognates.js"


class KnownLanguagesCacheTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_one_read_per_pass_and_never_stale(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const source = fs.readFileSync(process.env.COGNATES_JS, 'utf8').replace(/^import .*$/mg, '');
            const listeners = {};
            let reads = 0;
            let languages = ['en', 'pl'];
            const context = {
                console, localStorage: { getItem: () => null, setItem: () => {} },
                document: { getElementById: () => null },
                window: { addEventListener: (type, fn) => { (listeners[type] ||= []).push(fn); } },
                readLanguageProfile: () => { reads += 1; return { languages }; },
                bridgeSourceLanguages: () => ['en', 'pl', 'de'],
            };
            context.globalThis = context;
            vm.runInNewContext(source, context);
            const fail = message => { console.error(message); process.exit(1); };
            const fire = type => (listeners[type] || []).forEach(fn => fn());
            (async () => {
                for (let i = 0; i < 1000; i++) context.activeKnownLanguages();
                if (reads !== 1) fail('one pass read storage ' + reads + ' times');
                if (context.activeKnownLanguages().join() !== 'en,pl') fail('wrong languages');

                // A change in the same pass is seen at once.
                languages = ['en', 'de'];
                fire('language-profile-change');
                if (context.activeKnownLanguages().join() !== 'en,de') fail('profile change not seen');

                // Excluding a source is seen at once.
                context.readKnownLanguageSourceExclusions = () => ['de'];
                fire('fast-track-preference-change');
                if (context.activeKnownLanguages().join() !== 'en') fail('exclusion not seen');

                // Nothing survives into the next pass, even without an event.
                context.readKnownLanguageSourceExclusions = () => [];
                languages = ['pl'];
                await Promise.resolve();
                if (context.activeKnownLanguages().join() !== 'pl') fail('stale across passes');
            })().catch(error => fail(error.message));
        """
        completed = subprocess.run(
            ["node", "-e", script],
            env={**os.environ, "COGNATES_JS": str(COGNATES)},
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
