"""Unit tests for Word-by-word UI refinements in flashcards-modals.js.

Tests:
1. disambiguatePronounsInGloss:
   - Resolving he/she, his/her, himself/herself using English reference sentence
   - Resolving he/she using overt target subject pronouns (él, ella, etc.)
   - Resolving 1sg vs 3sg alternations (e.g. 'I was / he/she was')
   - Clause-level explicitSubject propagation
2. deduplicateBreakdownGlosses:
   - Redundant leading function word cut when previous word already declared it (e.g. 'a' [to] + 'tratar' [to try] -> 'try')
   - Redundant leading subject pronoun cut when previous word was that pronoun (e.g. 'yo' [I] + 'soy' [I am] -> 'am')
   - Redundant subject pronoun cut across intervening adverb in same clause (e.g. 'ella' [she] + 'no' [not] + 'tiene' [he/she has] -> 'has')
   - Resetting subject pronoun across clause boundaries
   - Safe behavior: single-word glosses never reduced to empty
3. findFixedExpressions & MWE translation confirmation:
   - Translation-confirmed bundling (e.g. 'de nuevo' bundles when English has 'again')
   - Avoiding false-positive bundling on single stopwords
"""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODALS_JS = ROOT / "app" / "js" / "flashcards-modals.js"


def run_js(code: str):
    """Executes code in node within the context of flashcards-modals.js breakdown functions."""
    wrapper = f"""
    const fs = require('fs');
    const vm = require('vm');

    const source = fs.readFileSync({json.dumps(str(MODALS_JS))}, 'utf8');

    // Minimal dummy environment for flashcards-modals.js
    const ctx = {{
        window: {{}},
        document: {{
            getElementById: () => null,
            addEventListener: () => {{}},
            querySelectorAll: () => [],
        }},
        console,
        currentIndex: 0,
        selectedLanguage: 'spanish',
        flashcards: [],
        config: {{}},
    }};
    ctx.window = ctx;
    ctx.globalThis = ctx;

    // Run the script without ES module import
    const stripped = source.replace(/import\\s+.*?from\\s+['"].*?['"];?/g, '');
    vm.createContext(ctx);
    vm.runInContext(stripped, ctx);

    const internals = ctx.window._breakdownInternals;
    {code}
    """
    res = subprocess.run(["node", "-e", wrapper], capture_output=True, text=True, check=True)
    return json.loads(res.stdout) if res.stdout.strip() else None


class TestWordByWordRefinements(unittest.TestCase):
    def test_disambiguate_pronouns_using_english_sentence(self):
        cases = [
            # gloss, target, english, expected
            ("he/she has", "Tiene un perro.", "She has a dog.", "she has"),
            ("he/she has", "Tiene un perro.", "He has a dog.", "he has"),
            ("he/she is", "Es inteligente.", "It is intelligent.", "it is"),
            ("he/she's", "Está feliz.", "She's happy.", "she's"),
            ("his/her dog", "Su perro", "Her dog is small.", "her dog"),
            ("his/her dog", "Su perro", "His dog is small.", "his dog"),
            ("himself/herself", "Se mira", "She looks at herself.", "herself"),
            ("he/she has", "Tiene un perro.", "Someone has a dog.", "he/she has"),
        ]
        code = f"""
        const cases = {json.dumps(cases)};
        const results = cases.map(([gloss, target, eng]) =>
            internals.disambiguatePronounsInGloss(gloss, target, eng)
        );
        process.stdout.write(JSON.stringify(results));
        """
        results = run_js(code)
        for (_, _, _, expected), actual in zip(cases, results):
            self.assertEqual(actual, expected)

    def test_disambiguate_pronouns_using_overt_target_pronouns(self):
        cases = [
            ("he/she has", "Ella tiene un perro.", "Has a dog.", "she has"),
            ("he/she has", "Él tiene un perro.", "Has a dog.", "he has"),
            ("he/she is", "Ela é bonita.", "Is pretty.", "she has".replace("has", "is")),
            ("he/she is", "Ele é legal.", "Is cool.", "he is"),
        ]
        code = f"""
        const cases = {json.dumps(cases)};
        const results = cases.map(([gloss, target, eng]) =>
            internals.disambiguatePronounsInGloss(gloss, target, eng)
        );
        process.stdout.write(JSON.stringify(results));
        """
        results = run_js(code)
        for (_, _, _, expected), actual in zip(cases, results):
            self.assertEqual(actual, expected)

    def test_disambiguate_1sg_vs_3sg_alternation(self):
        cases = [
            ("I was / he/she was", "Yo estaba en casa.", "I was home.", "I was"),
            ("I was / he/she was", "Ella estaba en casa.", "She was home.", "she was"),
            ("I was / he/she was", "Él estaba en casa.", "He was home.", "he was"),
            ("I take / he/she takes", "Yo tome agua.", "I took water.", "I take"),
            ("I take / he/she takes", "Ella tome agua.", "She took water.", "she takes"),
        ]
        code = f"""
        const cases = {json.dumps(cases)};
        const results = cases.map(([gloss, target, eng]) =>
            internals.disambiguatePronounsInGloss(gloss, target, eng)
        );
        process.stdout.write(JSON.stringify(results));
        """
        results = run_js(code)
        for (_, _, _, expected), actual in zip(cases, results):
            self.assertEqual(actual, expected)

    def test_deduplicate_adjacent_function_words(self):
        # a tratar -> to + to try -> try
        # yo soy -> I + I am -> am
        # para ir -> to / for + to go -> go
        code = """
        ctx.currentBreakdownSentence = { target: 'Voy a tratar', english: 'I will try' };
        const rows = [
            { text: 'voy', gloss: 'I go', result: { token: { clean: 'voy' } } },
            { text: 'a', gloss: 'to', result: { token: { clean: 'a' } } },
            { text: 'tratar', gloss: 'to try', result: { token: { clean: 'tratar' } } },
        ];
        const out = internals.deduplicateBreakdownGlosses(rows);
        process.stdout.write(JSON.stringify(out.map(r => [r.text, r.gloss])));
        """
        rows = run_js(code)
        self.assertEqual(rows, [["voy", "I go"], ["a", "to"], ["tratar", "try"]])

    def test_deduplicate_subject_pronoun_adjacent(self):
        code = """
        ctx.currentBreakdownSentence = { target: 'Yo soy feliz', english: 'I am happy' };
        const rows = [
            { text: 'yo', gloss: 'I', result: { token: { clean: 'yo' } } },
            { text: 'soy', gloss: 'I am', result: { token: { clean: 'soy' } } },
            { text: 'feliz', gloss: 'happy', result: { token: { clean: 'feliz' } } },
        ];
        const out = internals.deduplicateBreakdownGlosses(rows);
        process.stdout.write(JSON.stringify(out.map(r => [r.text, r.gloss])));
        """
        rows = run_js(code)
        self.assertEqual(rows, [["yo", "I"], ["soy", "am"], ["feliz", "happy"]])

    def test_deduplicate_subject_pronoun_across_adverb_in_clause(self):
        code = """
        ctx.currentBreakdownSentence = { target: 'Ella no tiene dinero', english: "She doesn't have money" };
        const rows = [
            { text: 'ella', gloss: 'she', result: { token: { clean: 'ella' } } },
            { text: 'no', gloss: 'not', result: { token: { clean: 'no' } } },
            { text: 'tiene', gloss: 'he/she has', result: { token: { clean: 'tiene' } } },
            { text: 'dinero', gloss: 'money', result: { token: { clean: 'dinero' } } },
        ];
        const out = internals.deduplicateBreakdownGlosses(rows);
        process.stdout.write(JSON.stringify(out.map(r => [r.text, r.gloss])));
        """
        rows = run_js(code)
        self.assertEqual(rows, [["ella", "she"], ["no", "not"], ["tiene", "has"], ["dinero", "money"]])

    def test_deduplicate_resets_across_clause_boundary(self):
        code = """
        ctx.currentBreakdownSentence = { target: 'Ella canta y él baila', english: 'She sings and he dances' };
        const rows = [
            { text: 'ella', gloss: 'she', result: { token: { clean: 'ella' } } },
            { text: 'canta', gloss: 'he/she sings', result: { token: { clean: 'canta' } } },
            { text: 'y', gloss: 'and', result: { token: { clean: 'y' } } },
            { text: 'él', gloss: 'he', result: { token: { clean: 'él' } } },
            { text: 'baila', gloss: 'he/she dances', result: { token: { clean: 'baila' } } },
        ];
        const out = internals.deduplicateBreakdownGlosses(rows);
        process.stdout.write(JSON.stringify(out.map(r => [r.text, r.gloss])));
        """
        rows = run_js(code)
        self.assertEqual(rows, [["ella", "she"], ["canta", "sings"], ["y", "and"], ["él", "he"], ["baila", "dances"]])

    def test_deduplicate_never_reduces_to_empty(self):
        code = """
        ctx.currentBreakdownSentence = { target: 'De a pie', english: 'On foot' };
        const rows = [
            { text: 'de', gloss: 'to', result: { token: { clean: 'de' } } },
            { text: 'a', gloss: 'to', result: { token: { clean: 'a' } } },
        ];
        const out = internals.deduplicateBreakdownGlosses(rows);
        process.stdout.write(JSON.stringify(out.map(r => [r.text, r.gloss])));
        """
        rows = run_js(code)
        # 'a' with gloss 'to' should NOT be reduced to empty string
        self.assertEqual(rows, [["de", "to"], ["a", "to"]])

    def test_mwe_translation_confirmation(self):
        # 'de nuevo' with 'again' in English sentence should bundle
        code = """
        ctx.currentBreakdownSentence = { target: 'Voy de nuevo allí', english: 'I go there again' };
        const results = [
            { token: { clean: 'voy' }, source: 'vocab', entry: { meanings: [] } },
            { token: { clean: 'de' }, source: 'vocab', entry: { meanings: [] } },
            {
                token: { clean: 'nuevo' },
                source: 'vocab',
                entry: {
                    meanings: [{
                        meaning: 'new',
                        metadata: {
                            multiword_evidence: [{
                                expression: 'de nuevo',
                                translation: 'again',
                                additional_translations: ['anew', 'once more'],
                                flexibility: 'fixed',
                                wsd_routing: 'competitive_wsd', // Not deterministic_bypass!
                            }]
                        }
                    }]
                }
            },
            { token: { clean: 'allí' }, source: 'vocab', entry: { meanings: [] } },
        ];
        const groups = internals.findFixedExpressions(results);
        process.stdout.write(JSON.stringify(groups));
        """
        groups = run_js(code)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["start"], 1)
        self.assertEqual(groups[0]["end"], 3)
        self.assertEqual(groups[0]["gloss"], "again")
        self.assertTrue(groups[0]["isConfirmed"])

    def test_mwe_not_bundled_without_translation_confirmation_if_not_bypass(self):
        # 'de nuevo' without 'again' in English should NOT bundle if competitive_wsd
        code = """
        ctx.currentBreakdownSentence = { target: 'Es un libro de nuevo diseño', english: 'It is a book of new design' };
        const results = [
            { token: { clean: 'es' }, source: 'vocab', entry: { meanings: [] } },
            { token: { clean: 'un' }, source: 'vocab', entry: { meanings: [] } },
            { token: { clean: 'libro' }, source: 'vocab', entry: { meanings: [] } },
            { token: { clean: 'de' }, source: 'vocab', entry: { meanings: [] } },
            {
                token: { clean: 'nuevo' },
                source: 'vocab',
                entry: {
                    meanings: [{
                        meaning: 'new',
                        metadata: {
                            multiword_evidence: [{
                                expression: 'de nuevo',
                                translation: 'again',
                                additional_translations: ['anew', 'once more'],
                                flexibility: 'fixed',
                                wsd_routing: 'competitive_wsd',
                            }]
                        }
                    }]
                }
            },
            { token: { clean: 'diseño' }, source: 'vocab', entry: { meanings: [] } },
        ];
        const groups = internals.findFixedExpressions(results);
        process.stdout.write(JSON.stringify(groups));
        """
        groups = run_js(code)
        self.assertEqual(groups, [])

    def test_deterministic_bypass_always_bundles_even_without_translation_match(self):
        code = """
        ctx.currentBreakdownSentence = { target: 'Por favor, ven', english: 'Come here' };
        const results = [
            {
                token: { clean: 'por' },
                source: 'vocab',
                entry: {
                    meanings: [{
                        meaning: 'for',
                        metadata: {
                            multiword_evidence: [{
                                expression: 'por favor',
                                translation: 'please',
                                flexibility: 'frozen',
                                wsd_routing: 'deterministic_bypass',
                            }]
                        }
                    }]
                }
            },
            { token: { clean: 'favor' }, source: 'vocab', entry: { meanings: [] } },
            { token: { clean: 'ven' }, source: 'vocab', entry: { meanings: [] } },
        ];
        const groups = internals.findFixedExpressions(results);
        process.stdout.write(JSON.stringify(groups));
        """
        groups = run_js(code)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["start"], 0)
        self.assertEqual(groups[0]["end"], 2)
        self.assertEqual(groups[0]["gloss"], "please")


if __name__ == "__main__":
    unittest.main()
