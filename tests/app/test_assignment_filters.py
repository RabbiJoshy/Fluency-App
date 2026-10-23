"""Admin assignment filters classify by Jev > DeepSeek > original and never alter cards."""
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
        sidecar = (ROOT / 'app/js/wsd-ui-sidecar.js').read_text()
        sidecar = '\n'.join(l for l in sidecar.splitlines() if not l.startswith('import ')).replace('export ', '')
        result = subprocess.run(['node', '-e', sidecar + '\n' + source + '\n' + script],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_precedence_filters_and_identity(self):
        self.run_js(r'''
const sidecar = {cards: {card_pt_j: {}}, card_ids: {j: 'card_pt_j'}};
const index = {single_sense: ['s', 'j'], deepseek: ['d', 'j']};
const rows = ['j', 'd', 's', 'o'].map(id => ({id, surface_card_id: 'card_pt_' + id, rank: 1}));
stampAssignmentFilters(rows, index, sidecar);
const src = Object.fromEntries(rows.map(r => [r.id, r._assignSrc]));
if (JSON.stringify(src) !== '{"j":"jev","d":"deepseek","s":"original","o":"original"}') throw Error('precedence ' + JSON.stringify(src));
globalThis.isAuditAccount = () => true;
const keep = () => rows.filter(passesAssignmentFilters).map(r => r.id).join('');
if (keep() !== 'jdso') throw Error('default');
assignmentFilter.excludeSingleSense = true;
if (keep() !== 'do') throw Error('single ' + keep());
assignmentFilter.source = 'original';
if (keep() !== 'o') throw Error('original');
assignmentFilter.source = 'deepseek';
if (keep() !== 'd') throw Error('deepseek');
assignmentFilter.excludeSingleSense = false; assignmentFilter.source = 'jev';
if (keep() !== 'j') throw Error('jev');
globalThis.isAuditAccount = () => false;
if (keep() !== 'jdso') throw Error('non-admin must be unfiltered');
if (rows.some(r => r.rank !== 1 || r.surface_card_id !== 'card_pt_' + r.id)) throw Error('identity');
const config = {indexPath: 'https://h/pt/speech/rel/app/vocabulary.index.json'};
validateAssignmentFilterIndex({schema: 'assignment-filter-index/v1', release_id: 'rel', single_sense: [], deepseek: []}, config);
let rejected = false;
try { validateAssignmentFilterIndex({schema: 'assignment-filter-index/v1', release_id: 'other', single_sense: [], deepseek: []}, config); } catch (e) { rejected = true; }
if (!rejected) throw Error('release pin');
''')

    def test_shipped_index_matches_sidecar_scope_and_config(self):
        config = json.loads((ROOT / 'app/config/config.json').read_text())['languages']['portuguese']
        index = json.loads((ROOT / 'app' / config['assignmentFilterPath']).read_text())
        self.assertEqual(index['schema'], 'assignment-filter-index/v1')
        self.assertIn(f"/{index['release_id']}/", config['indexPath'])
        self.assertEqual(index['release_id'], config['wsdSidecarRelease'])
        self.assertEqual(len(set(index['deepseek'])), len(index['deepseek']))


if __name__ == '__main__':
    unittest.main()
