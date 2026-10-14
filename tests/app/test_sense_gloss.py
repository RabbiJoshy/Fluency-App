import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = (ROOT / "app/js/sense-gloss.js").as_uri()

SCRIPT = f"""
import {{ promoteSubglossTranslations }} from {json.dumps(MODULE)};
const wk = (translation, context, extra = {{}}) => ({{ source: 'wiktionary', translation, context, ...extra }});
const cases = {{
  fazer: [wk('to make', 'to create; to produce'), wk('to make', 'to do; to execute; to perform'),
          wk('to make', '(auxiliary) to cause to [with infinitive]')],
  alone: [wk('to make', 'to do; to execute; to perform')],
  explained: [wk('to have', '(auxiliary) used in forming the perfect aspect'), wk('to have', 'to own; to possess')],
  same: [wk('to have', '(transitive) to have (to be related in some way)'), wk('to have', 'to own')],
  label: [wk('piano', 'music', {{ metadata: {{ sense_provider_metadata: {{ topics: ['music'] }} }} }}), wk('piano', 'pianist')],
  wordy: [wk('bolo', 'any of various snacks made with dough'), wk('bolo', 'cake made for a party with many layers and icing')],
  spanishdict: [{{ source: 'spanishdict', translation: 'to tell', context: 'to speak' }},
                {{ source: 'spanishdict', translation: 'to tell', context: 'to order' }}],
}};
for (const meanings of Object.values(cases)) promoteSubglossTranslations(meanings);
console.log(JSON.stringify(cases));
"""


class SenseGlossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run(["node", "--input-type=module", "-e", SCRIPT], capture_output=True, text=True, check=True)
        cls.cases = json.loads(out.stdout)

    def shown(self, name):
        return [m["translation"] for m in self.cases[name]]

    def test_shared_umbrella_shows_the_sub_gloss_and_keeps_the_original(self):
        self.assertEqual(self.shown("fazer"), ["to create; to produce", "to do; to execute; to perform", "to cause to"])
        first = self.cases["fazer"][0]
        self.assertEqual((first["original_translation"], first["context"]), ("to make", "to make"))

    def test_a_lone_meaning_is_left_alone(self):
        self.assertEqual(self.shown("alone"), ["to make"])

    def test_explanations_labels_wordy_and_identical_sub_glosses_stay_notes(self):
        self.assertEqual(self.shown("explained"), ["to have", "to own; to possess"])
        self.assertEqual(self.shown("same"), ["to have", "to own"])
        self.assertEqual(self.shown("label"), ["piano", "pianist"])
        self.assertEqual(self.shown("wordy"), ["bolo", "bolo"])

    def test_spanishdict_contexts_are_never_promoted(self):
        self.assertEqual(self.shown("spanishdict"), ["to tell", "to tell"])


if __name__ == "__main__":
    unittest.main()
