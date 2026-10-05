"""Shortcut reference accuracy and keyboard focus regressions."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("node"), "Node.js required")
class KeyboardGuideTests(unittest.TestCase):
    def run_node(self, source):
        result = subprocess.run(
            ["node", "--input-type=module", "-"], cwd=ROOT,
            input=source, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_platform_account_and_conditional_references(self):
        self.run_node(r'''
import assert from 'node:assert/strict';
import { availableShortcuts, renderShortcutRows, shortcutKeys } from './app/js/keyboard-guide.js';
const ordinary = availableShortcuts();
assert(!ordinary.some(item => item.group === 'Audit tools'));
const reporter = availableShortcuts({canFlag:true});
assert(reporter.some(item => item.id === 'flag'));
assert(!reporter.some(item => item.id === 'model'));
const audit = availableShortcuts({canFlag:true,isOwner:true});
assert(audit.some(item => item.id === 'model'));
assert.equal(ordinary.filter(item => item.compact).length, 6);
const find = ordinary.find(item => item.id === 'find');
assert.equal(find.label, 'Find a word');
assert(shortcutKeys(find, true).includes('⌘'));
assert(!shortcutKeys(find, true).includes('Ctrl'));
assert(shortcutKeys(find, false).includes('Ctrl'));
const meanings = ordinary.filter(item => item.id === 'meanings');
assert(renderShortcutRows(meanings, {meaningCount:1}).includes('is-unavailable'));
assert(!renderShortcutRows(meanings, {meaningCount:2}).includes('is-unavailable'));
assert(renderShortcutRows(meanings, {meaningCount:2}).includes('multiple meanings'));
const correct = ordinary.find(item => item.id === 'correct');
assert(shortcutKeys(correct, false).includes('>C<'));
assert(!shortcutKeys(correct, false, true).includes('>C<'));
assert(!renderShortcutRows(ordinary).includes('<button'));
''')

    def test_existing_keys_and_reference_control_focus(self):
        self.run_node(r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('app/js/flashcards.js', 'utf8');
const setup = source.slice(source.indexOf('function setupKeyboardShortcuts()'), source.indexOf('function handleFlagAction()'));
const calls = [];
let handler;
const context = {
 document: {getElementById:()=>null, addEventListener:(type, fn)=>{handler=fn;}},
 window: {canUserFlag:()=>true, speakWord:word=>calls.push(['speak',word]), showFlagMenu:()=>calls.push(['flagMenu'])},
 flashcards:[{targetWord:'hola',meanings:[{},{}]}], currentIndex:0, currentMeaningIndex:0,
 isJstOwner:()=>true,
 toggleKeyboardShortcutsModal:()=>calls.push(['reference']),
 showStatsModal:()=>calls.push(['progress']),
 showSettingsModalWithTab:()=>calls.push(['preferences']),
 toggleProvenancePanel:()=>calls.push(['model']),
 previousCard:()=>calls.push(['previous']), nextCard:()=>calls.push(['next']),
 selectMeaning:index=>calls.push(['meaning',index]),
 cycleExampleForward:()=>calls.push(['example']), cycleMWEForward:()=>calls.push(['expression']),
 handleSwipeAction:grade=>calls.push(['grade',grade]), flipCard:()=>calls.push(['flip']),
 handleFlagAction:()=>calls.push(['flag']),
 getDisplayedTargetHeadword:card=>card.targetWord,
 navigateBack:()=>calls.push(['back']),
};
vm.runInNewContext(setup+';setupKeyboardShortcuts();', context);
function press(key, modifiers={}, focusedReference=false, tagName='DIV') {
 calls.length=0;
 handler({key,...modifiers,target:{tagName,closest:()=>focusedReference},preventDefault(){}});
 return [...calls];
}
assert.deepEqual(press(' '),[['flip']]);
for (const key of ['Enter','c','C']) assert.deepEqual(press(key),[['grade','correct']]);
for (const key of ['x','X','1']) assert.deepEqual(press(key),[['grade','incorrect']]);
assert.deepEqual(press('ArrowLeft'),[['previous']]);
assert.deepEqual(press('ArrowRight'),[['next']]);
assert.deepEqual(press('ArrowDown'),[['meaning',1]]);
assert.deepEqual(press('Tab'),[['example']]);
assert.deepEqual(press('Tab',{shiftKey:true}),[['next']]);
assert.deepEqual(press('a'),[['speak','hola']]);
assert.deepEqual(press('?'),[['reference']]);
for (const mod of ['ctrlKey','metaKey']) {
 assert.deepEqual(press('s',{[mod]:true}),[['progress']]);
 assert.deepEqual(press('p',{[mod]:true}),[['preferences']]);
 assert.deepEqual(press('i',{[mod]:true}),[['model']]);
 assert.deepEqual(press('f',{[mod]:true,shiftKey:true}),[['flagMenu']]);
}
assert.deepEqual(press('f'),[['flag']]);
for (const key of ['Enter',' ','Tab','ArrowRight']) assert.deepEqual(press(key,{},true),[]);
assert.deepEqual(press('Enter',{},false,'INPUT'),[]);
assert.deepEqual(press('?',{},true),[['reference']]);
''')
