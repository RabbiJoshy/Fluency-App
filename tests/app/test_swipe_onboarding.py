"""One-time swipe guidance survives skipped tutorials and keyboard grades."""
from pathlib import Path
import shutil
import subprocess
import unittest
ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class SwipeOnboardingTests(unittest.TestCase):
    def test_reveal_swipe_and_later_visit(self):
        script = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('app/js/swipe-onboarding.js','utf8').replaceAll('export function','function');
const storage=new Map();let hint=null;
const context={localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},
 document:{getElementById:id=>id==='firstSwipeHint'?hint:{classList:{contains:()=>false}},
 querySelector:()=>null,createElement:()=>({style:{},setAttribute(){},remove(){hint=null;}}),
 body:{appendChild:el=>{hint=el;}}}};
vm.runInNewContext(source,context);
context.showSwipeHint({realCard:false});assert.equal(hint,null);
context.showSwipeHint();assert.equal(hint.textContent,'← Needs practice · Got it →');
context.refreshSwipeHint();assert.equal(hint.hidden,false);
assert.equal(storage.size,0); // Revealing does not count as learning.
context.rememberGradingSwipe();assert.equal(hint,null);assert.equal(storage.size,1);
context.showSwipeHint();assert.equal(hint,null);
vm.runInNewContext(source,{...context});
context.showSwipeHint();assert.equal(hint,null);
'''
        result=subprocess.run(['node','-'],input=script,text=True,capture_output=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_quick_tour_keeps_full_help_tour(self):
        source=(ROOT/'app/js/tutorial.js').read_text()
        self.assertIn('openCardTutorial({ quick: true })',source)
        self.assertIn('function openCardTutorial({ quick = false } = {})',source)
        for title in ['Recall, then reveal','Hear the pronunciation','Grade your answer','Move on']:
            self.assertIn(title,source)
