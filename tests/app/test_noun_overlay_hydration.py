"""Loading the original row cannot discard checked supplemental noun proof."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class NounOverlayHydrationTests(unittest.TestCase):
    def test_hydration_keeps_overlay_and_restores_original_on_release_change(self):
        source = (ROOT / 'app/js/vocab.js').read_text()
        def function(name):
            start = source.index('function ' + name + '(')
            return source[start:source.index('\n}\n', start) + 3]
        pure = source[source.index('// lemma-merge-pure'):source.index('// /lemma-merge-pure')]
        script = pure + function('mergeIndexRowPayload') + function('stampMergeExceptionValues') + r'''
const original = {rule_version:'noun-merge/v2', allowed:false, lemma:'perro'};
const proof = {rule_version:'noun-merge/v2', allowed:true, lemma:'perro'};
const card = {id:'dogs', word:'perros', meanings:[], _indexRowsPending:true};
globalThis.window = {_cachedJoinedIndex:[card]};
stampMergeExceptionValues([card], new Set(), {perros:'perro'}, {perros:proof});
if (lemmaGroupKey(card) !== 'perro') throw new Error('cold merge');
mergeIndexRowPayload({dogs:{noun_merge:original,meanings:[{headword:'perro',pos:'NOUN',translation:'dog'}]}});
if (lemmaGroupKey(card) !== 'perro' || card._indexRowsPending) throw new Error('loaded merge');
if (card._nounMergeOriginal !== original) throw new Error('hydrated original lost');
stampMergeExceptionValues([card], new Set(), null, null);
if (card.noun_merge !== original || lemmaGroupKey(card) !== '') throw new Error('release change retained overlay');
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_default_decks_retain_checked_noun_pairs_and_exceptions(self):
        import json
        cfg = json.loads((ROOT / 'app/config/config.json').read_text())
        for language, pair, kept in [('spanish', ('años', 'año'), ['sé', 'fue', 'al', 'del']),
                                     ('portuguese', ('horas', 'hora'), ['no', 'do', 'conta', 'poderes', 'seres'])]:
            with self.subTest(language=language):
                asset = json.loads((ROOT / 'app' / cfg['languages'][language]['mergeExceptionsPath']).read_text())
                plural, singular = pair
                self.assertEqual(asset['keys'][plural], singular)
                self.assertEqual(asset['keys'][singular], singular)
                for word in pair:
                    proof = asset['noun_verdicts'][word]
                    self.assertTrue(proof['allowed'])
                    self.assertEqual(proof['rule_version'], 'noun-merge/v2')
                self.assertEqual(asset['noun_verdicts'][plural]['sense_set'], asset['noun_verdicts'][singular]['sense_set'])
                self.assertTrue(asset.get('evidence'))
                for word in kept:
                    self.assertEqual(asset['keys'][word], '')
