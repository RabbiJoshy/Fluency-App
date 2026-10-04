"""Verb drill progress: the Leitner store in app/conjugation/progress.js."""

import json
from pathlib import Path
import shutil
import subprocess
import unittest


APP = Path(__file__).resolve().parents[2] / "app"
PROGRESS = APP / "conjugation/progress.js"

# progress.js is a plain script that installs window.ConjugationProgress; run it
# in a vm with a fake localStorage.
RUNNER = r"""
    const fs = require('node:fs');
    const vm = require('node:vm');
    const data = {};
    const localStorage = {
        getItem: k => (k in data ? data[k] : null),
        setItem: (k, v) => { data[k] = String(v); },
        removeItem: k => { delete data[k]; },
    };
    const window = { localStorage };
    vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), { window, JSON, Date, Math });
    const P = window.ConjugationProgress;
    const DAY = 86400000, t0 = 1e12;
    const out = {};
    let r = P.grade(null, true, t0);
    out.firstHit = [r.box, r.due - t0];
    r = P.grade(r, true, t0 + 1); r = P.grade(r, true, t0 + 2);
    out.threeHits = [r.box, P.status(r, t0 + 3).state, P.status(r, t0 + 4 * DAY).due];
    r = P.grade(r, false, t0 + 5);
    out.miss = [r.box, r.wrong, r.right, P.status(r, t0 + 5).state, P.status(r, t0 + 5).due];
    out.newStatus = P.status(undefined, t0);
    out.order = [P.priority(r, t0 + 5)[0], P.priority(null, t0)[0],
                 P.priority(P.grade(null, true, t0), t0 + DAY)[0],
                 P.priority(P.grade(null, true, t0), t0 + 1)[0]];
    P.record('es', P.formKey('tener', 'indicative::present', '1s'), false, t0);
    P.record('es', P.formKey('tener', 'indicative::present', '1p'), true, t0);
    out.summary = P.summarise(P.load('es'), [
        'tener|indicative::present|1s', 'tener|indicative::present|1p', 'ser|indicative::present|1s'
    ], t0 + DAY);
    out.keys = Object.keys(data).sort();
    data.flashcardUser = JSON.stringify({ initials: 'JT' });
    out.accountSplit = Object.keys(P.load('es').forms).length;
    P.saveSession('es', { keys: ['a|b|c'], position: 0, results: {} });
    out.session = Object.keys(data).filter(k => k.startsWith('conj_session')).sort();
    P.resetLanguage('es');
    out.afterReset = [P.loadSession('es'), Object.keys(data).filter(k => k.includes('_JT_'))];
    P.saveSettings('es', { focus: 'due' });
    out.settings = P.loadSettings('es');
    // Flashcard mistakes come from the study app's cache, signed-in users only.
    const iso = ms => new Date(ms).toISOString();
    out.missesNoCache = P.flashcardMisses('es', t0);
    data.progress_cache_JT = JSON.stringify({ progress: {
        es1: { word: 'Tuvimos', language: 'spanish', wrong: 1, lastWrong: iso(t0 - DAY) },
        es2: { word: 'casa', language: 'spanish', wrong: 2, lastWrong: iso(t0 - 8 * DAY) },
        es3: { word: 'fue', language: 'spanish', wrong: 0, lastWrong: null },
        pt1: { word: 'tivemos', language: 'portuguese', wrong: 1, lastWrong: iso(t0 - DAY) },
    } });
    out.misses = P.flashcardMisses('es', t0);
    data.flashcardUser = JSON.stringify({ isGuest: true });
    out.missesGuest = P.flashcardMisses('es', t0);
    console.log(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
class ConjugationProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            ["node", "-", str(PROGRESS)], input=RUNNER,
            text=True, capture_output=True, check=False,
        )
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.out = json.loads(result.stdout)

    def test_hits_climb_the_ladder(self):
        self.assertEqual(self.out["firstHit"], [1, 10 * 60 * 1000])
        box, state, due_later = self.out["threeHits"]
        self.assertEqual((box, state, due_later), (3, "known", True))

    def test_a_miss_resets_and_is_due_now(self):
        self.assertEqual(self.out["miss"], [0, 1, 3, "missed", True])

    def test_absent_record_is_declared_new(self):
        self.assertEqual(self.out["newStatus"], {"state": "new", "due": True})

    def test_priority_puts_missed_then_due_then_new_then_waiting(self):
        self.assertEqual(self.out["order"], [0, 2, 1, 3])

    def test_summary_counts(self):
        s = self.out["summary"]
        self.assertEqual((s["total"], s["missed"], s["learning"], s["new"], s["due"]), (3, 1, 1, 1, 1))

    def test_storage_is_per_account_and_language(self):
        self.assertEqual(self.out["keys"], ["conj_progress_v2_guest_es"])
        self.assertEqual(self.out["accountSplit"], 0)
        self.assertEqual(self.out["session"], ["conj_session_v2_JT_es"])

    def test_reset_clears_progress_and_round_only(self):
        self.assertEqual(self.out["afterReset"], [None, []])
        self.assertEqual(self.out["settings"], {"focus": "due"})

    def test_flashcard_misses_are_recent_wrong_answers_in_this_language(self):
        self.assertIsNone(self.out["missesNoCache"])
        self.assertEqual(list(self.out["misses"]), ["tuvimos"])
        self.assertIsNone(self.out["missesGuest"])

    def test_page_loads_the_store_before_the_drill(self):
        html = (APP / "conjugation/index.html").read_text()
        self.assertLess(html.index('src="progress.js'), html.index('src="app.js'))


if __name__ == "__main__":
    unittest.main()
