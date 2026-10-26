"""Admin assignment filters classify by assigning model, confidence, gaps and POS, and never alter cards."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class AssignmentFilterTests(unittest.TestCase):
    def run_js(self, script):
        source = '\n'.join(
            line for line in (ROOT / 'app/js/assignment-filters.js').read_text().splitlines()
            if not line.startswith('import '))
        source = source.replace('export ', '')
        result = subprocess.run(['node', '-e', source + '\n' + script],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_precedence_filters_and_identity(self):
        self.run_js(r'''
const index = {single_sense: ['s', 'j'], sources: {decide: ['d'], jev: ['j', 'ju']},
    min_confidence: {j: 0.15, ju: 0.95}, unresolved: ['ju']};
const rows = [
    {id: 'j', surface_card_id: 'card_pt_j', rank: 1, meanings: [{pos: 'verb'}]},
    {id: 'ju', surface_card_id: 'card_pt_ju', rank: 2, meanings: [{pos: 'noun'}]},
    {id: 'd', surface_card_id: 'card_pt_d', rank: 3, meanings: [{pos: 'adj'}]},
    {id: 's', surface_card_id: 'card_pt_s', rank: 4, meanings: [{pos: 'adv'}]},
    {id: 'o', surface_card_id: 'card_pt_o', rank: 5, function_word: ['prep', 'de', 'of']}
];
stampAssignmentFilters(rows, index);
const src = Object.fromEntries(rows.map(r => [r.id, r._assignSrc]));
if (src.j !== 'jev' || src.ju !== 'jev' || src.d !== 'decide' || src.s !== 'original' || src.o !== 'original') {
    throw Error('precedence ' + JSON.stringify(src));
}
globalThis.isAuditAccount = () => true;
const keep = () => rows.filter(passesAssignmentFilters).map(r => r.id).join('');
if (keep() !== 'jjudso') throw Error('default ' + keep());

// Single sense
assignmentFilter.excludeSingleSense = true;
if (keep() !== 'judo') throw Error('single ' + keep());
assignmentFilter.excludeSingleSense = false;

// Source
assignmentFilter.source = 'original';
if (keep() !== 'so') throw Error('original ' + keep());
assignmentFilter.source = 'decide';
if (keep() !== 'd') throw Error('decide ' + keep());
assignmentFilter.source = 'jev';
if (keep() !== 'jju') throw Error('jev ' + keep());
assignmentFilter.source = 'all';

// POS
assignmentFilter.pos = 'verb';
if (keep() !== 'j') throw Error('pos verb ' + keep());
assignmentFilter.pos = 'noun';
if (keep() !== 'ju') throw Error('pos noun ' + keep());
assignmentFilter.pos = 'adj';
if (keep() !== 'd') throw Error('pos adj ' + keep());
assignmentFilter.pos = 'adv';
if (keep() !== 's') throw Error('pos adv ' + keep());
assignmentFilter.pos = 'function';
if (keep() !== 'o') throw Error('pos function ' + keep());
assignmentFilter.pos = 'all';

// Confidence
assignmentFilter.confidence = 'lowest'; // < 0.2
if (keep() !== 'j') throw Error('confidence lowest ' + keep());
assignmentFilter.confidence = 'marginal'; // < 0.3
if (keep() !== 'j') throw Error('confidence marginal ' + keep());
assignmentFilter.confidence = 'unresolved';
if (keep() !== 'ju') throw Error('confidence unresolved ' + keep());
assignmentFilter.confidence = 'high'; // >= 0.8
if (keep() !== 'ju') throw Error('confidence high ' + keep());
assignmentFilter.confidence = 'all';

// Active filter count
if (activeFilterCount() !== 0) throw Error('activeFilterCount zero');
assignmentFilter.excludeSingleSense = true;
assignmentFilter.pos = 'verb';
if (activeFilterCount() !== 2) throw Error('activeFilterCount two');
assignmentFilter.excludeSingleSense = false;
assignmentFilter.pos = 'all';

// Non-admin must be completely unfiltered
globalThis.isAuditAccount = () => false;
assignmentFilter.pos = 'verb';
assignmentFilter.source = 'jev';
if (keep() !== 'jjudso') throw Error('non-admin must be unfiltered');

if (rows.some(r => r.rank < 1 || !r.surface_card_id)) throw Error('identity integrity');
const config = {indexPath: 'https://h/pt/speech/rel/app/vocabulary.index.json'};
validateAssignmentFilterIndex({schema: 'assignment-filter-index/v2', release_id: 'rel', single_sense: [], sources: {}, min_confidence: {}, unresolved: []}, config);
let rejected = false;
try { validateAssignmentFilterIndex({schema: 'assignment-filter-index/v2', release_id: 'other', single_sense: [], sources: {}, min_confidence: {}, unresolved: []}, config); } catch (e) { rejected = true; }
if (!rejected) throw Error('release pin');
''')

    def test_shipped_index_matches_release_and_config(self):
        config = json.loads((ROOT / 'app/config/config.json').read_text())['languages']['portuguese']
        index = json.loads((ROOT / 'app' / config['assignmentFilterPath']).read_text())
        self.assertEqual(index['schema'], 'assignment-filter-index/v2')
        self.assertIn(f"/{index['release_id']}/", config['indexPath'])
        ids = [card for cards in index['sources'].values() for card in cards]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertLessEqual(set(index['min_confidence']) | set(index['unresolved']), set(ids))


if __name__ == '__main__':
    unittest.main()
