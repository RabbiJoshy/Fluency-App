"""Search list metadata cannot override the menu fetched when opening a card."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class SearchHydratedCardTests(unittest.TestCase):
    def test_cold_and_warm_search_use_loaded_meanings_and_keep_source_identity(self):
        source = (ROOT / 'app/js/flashcards-modals.js').read_text()
        start = source.index('async function popupFoundWord(')
        end = source.index('\n}\n', start) + 3
        script = r'''
const vm = require('vm');
const source = JSON.parse(process.argv[1]);
async function open(warm, genuineEmpty) {
    const word = {id: '84fa7942', word: 'déjalo', rank: 748, meanings: [], _indexRowsPending: !warm};
    const menu = [{headword: 'dejar', pos: 'VERB', translation: 'leave it'}];
    if (warm && !genuineEmpty) word.meanings = menu;
    let captured, loads = 0;
    const context = {
        activeArtist: null, config: {languages: {spanish: {}}}, selectedLanguage: 'spanish', console,
        projectInspectableMeaning: m => ({...m, meaning: m.translation}),
        splitAwareTempCard: (item, card) => { captured = card; throw new Error('captured'); }
    };
    context.window = {
        // The active cache can move after search renders. Opening must retain the exact source entry.
        _cachedJoinedIndex: [{id: word.id, word: 'wrong source', meanings: []}],
        ensureIndexRowsForRange: async () => { loads++; if (!genuineEmpty) word.meanings = menu; word._indexRowsPending = false; },
        getWordId: () => 'es:84fa7942', generateLinks: () => [],
        _cachedExamplesData: {[word.id]: {r: [{target: 'Déjalo.', english: 'Leave it.'}]}}
    };
    vm.createContext(context); vm.runInContext(source, context);
    try { await context.popupFoundWord({id: word.id, sourceEntry: word, examplesOnly: true}); }
    catch(e) { if (e.message !== 'captured') throw e; }
    return {flag: captured.searchExamplesOnly, word: captured.targetWord, meanings: captured.meanings.map(m=>m.meaning), loads};
}
(async()=>{console.log(JSON.stringify([await open(false,false), await open(true,false), await open(false,true)]));})().catch(e=>{console.error(e);process.exit(1)});
'''
        result = subprocess.run(['node', '-e', script, json.dumps(source[start:end])], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        cold, warm, empty = json.loads(result.stdout)
        for card in [cold, warm]:
            self.assertFalse(card['flag'])
            self.assertEqual(card['word'], 'déjalo')
            self.assertEqual(card['meanings'], ['leave it'])
        self.assertEqual(cold['loads'], 1)
        self.assertEqual(warm['loads'], 0)
        self.assertTrue(empty['flag'])
