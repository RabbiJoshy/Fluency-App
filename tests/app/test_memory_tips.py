"""Memory tips explain only map-vouched cognates, and only with named rules."""

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "app/js/memory-tips.js"
COGNATES = ROOT / "app/js/cognates.js"
POLICIES = ROOT / "config/cognates"


def _rules(pair: str) -> list:
    return json.loads((POLICIES / f"{pair}.json").read_text(encoding="utf-8"))["tip_rules"]


def _node(script: str, **env: str) -> str:
    return subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, check=True, env={**os.environ, **env},
    ).stdout.strip()


class MemoryTipTests(unittest.TestCase):
    """The cognate map is stubbed: `partners` is what it vouches for."""

    def _run(self, body: str, partners: dict, pair: str = "es-en") -> str:
        script = (
            f"const RULES = {json.dumps(_rules(pair), ensure_ascii=False)};"
            f"const PARTNERS = {json.dumps(partners, ensure_ascii=False)};"
            "globalThis.cognateTipRules = code => code === 'en' ? RULES : [];"
            "globalThis.cognateTipPartner = card => PARTNERS[card.word] || null;"
            f"const m = await import('{MODULE.as_uri()}');"
            "const tip = w => m.memoryTipFor({word: w, meanings: []}, 'spanish');"
            "const rows = t => t.rows.map(r => r.kind + ':' + r.label).join(' | ');"
            f"{body}"
        )
        return _node(script)

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_no_tip_without_the_maps_verdict(self) -> None:
        # hace glosses "has", and the two look alike, but the map does not call
        # them cognates, so there is nothing to explain.
        out = self._run("console.log(tip('hace'), tip('chica'));", {})
        self.assertEqual(out, "null null")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_adverb_is_named_rules_only(self) -> None:
        out = self._run(
            "const t = tip('rápidamente'); console.log(t.english, t.tier, rows(t), t.accents);",
            {"rápidamente": {"score": 0.9, "word": "rapidly", "headword": "rápidamente"}},
        )
        self.assertEqual(out, "rapidly pattern free:Drop the feminine -a | rule:-mente → -ly true")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_prefix_suffix_and_letter_rules(self) -> None:
        out = self._run(
            "console.log([tip('estación'), tip('foto'), tip('cuestión')]"
            ".map(t => t.tier + ' ' + rows(t)).join(' / '));",
            {
                "estación": {"score": 1, "word": "station"},
                "foto": {"score": 1, "word": "photo"},
                "cuestión": {"score": 1, "word": "question"},
            },
        )
        self.assertEqual(
            out,
            "pattern rule:es- → s- | rule:-ción → -tion / pattern rule:f → ph"
            " / pattern rule:cu → qu",
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_unexplained_letters_are_a_spelling_difference_not_a_rule(self) -> None:
        out = self._run(
            "const t = tip('negociación'); console.log(t.tier, rows(t), t.rows.at(-1).detail);",
            {"negociación": {"score": 0.9, "word": "negotiation"}},
        )
        self.assertEqual(
            out, "close rule:-ción → -tion | spelling:Small spelling difference c → t"
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_same_word_doubled_letter_and_inflected_form(self) -> None:
        out = self._run(
            "console.log(tip('hotel').tier, rows(tip('acceso')),"
            " tip('accidentes').form, rows(tip('accidentes')));",
            {
                "hotel": {"score": 1, "word": "hotel"},
                "acceso": {"score": 0.8, "word": "access"},
                "accidentes": {"score": 0.8, "word": "accident", "headword": "accidente"},
            },
        )
        self.assertEqual(
            out,
            "same free:English doubles the s | free:Drop the final -o accidente rule:-ente → -ent",
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_a_pair_the_rules_barely_touch_has_no_tip(self) -> None:
        out = self._run(
            "console.log(tip('ojo'), tip('perro'));",
            {"ojo": {"score": 0.8, "word": "eye"}, "perro": {"score": 0.8, "word": "dog"}},
        )
        self.assertEqual(out, "null null")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_no_rules_for_the_pair_means_no_tip(self) -> None:
        out = _node(
            "globalThis.cognateTipRules = () => [];"
            "globalThis.cognateTipPartner = () => ({score: 1, word: 'hotel'});"
            f"const m = await import('{MODULE.as_uri()}');"
            "console.log(m.memoryTipFor({word: 'hotel', meanings: []}, 'czech'));"
        )
        self.assertEqual(out, "null")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_french_circumflex_and_accented_prefix(self) -> None:
        out = self._run(
            "console.log(rows(tip('forêt')), '/', rows(tip('école')));",
            {"forêt": {"score": 1, "word": "forest"}, "école": {"score": 1, "word": "school"}},
            pair="fr-en",
        )
        self.assertEqual(
            out,
            "rule:ê → es / rule:é- → s- | free:Drop the final -e | spelling:Small spelling difference",
        )


class OtherPairsTests(unittest.TestCase):
    """Dutch, Finnish and Czech read through English, and Czech through Polish."""

    def _run(self, body: str, rules: dict, partners: dict, languages: list) -> str:
        script = (
            f"const RULES = {json.dumps(rules, ensure_ascii=False)};"
            f"const PARTNERS = {json.dumps(partners, ensure_ascii=False)};"
            f"globalThis.cognateTipLanguages = () => {json.dumps(languages)};"
            "globalThis.cognateTipRules = code => RULES[code] || [];"
            "globalThis.cognateTipPartner = (card, code) => PARTNERS[code]?.[card.word] || null;"
            f"const m = await import('{MODULE.as_uri()}');"
            "const tip = w => m.memoryTipFor({word: w, meanings: []});"
            "const say = t => t ? `${t.known}:${t.english} ${t.tier} ` + t.rows.map(r => r.label).join(' | ') : 'null';"
            f"{body}"
        )
        return _node(script)

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_dutch_and_finnish_endings(self) -> None:
        out = self._run(
            "console.log(say(tip('universiteit')), '/', say(tip('pensioen')));",
            {"en": _rules("nl-en")},
            {"en": {"universiteit": {"score": 1, "word": "university"},
                    "pensioen": {"score": 1, "word": "pension"}}},
            ["en"],
        )
        self.assertEqual(out, "en:university pattern -iteit → -ity / en:pension pattern -ioen → -ion")
        out = self._run(
            "console.log(say(tip('presidentti')));",
            {"en": _rules("fi-en")},
            {"en": {"presidentti": {"score": 0.9, "word": "president"}}},
            ["en"],
        )
        self.assertEqual(out, "en:president pattern -tti → -t")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_czech_card_through_polish_only_when_the_learner_reads_it(self) -> None:
        rules = {"en": _rules("cs-en"), "pl": _rules("cs-pl")}
        partners = {
            "en": {"kriminální": {"score": 0.9, "word": "criminal"}},
            "pl": {"kriminální": {"score": 0.9, "word": "kryminalny"},
                   "bloků": {"score": 0.9, "word": "bloku", "headword": "blok"}},
        }
        body = "console.log(say(tip('kriminální')), '/', say(tip('bloků')));"
        self.assertEqual(
            self._run(body, rules, partners, ["en"]),
            "en:criminal pattern k → c | -ální → -al / null",
        )
        # Both are regular patterns; Polish wins the tie. The Polish word is
        # the same inflection as the card, so the card is explained as is.
        self.assertEqual(
            self._run(body, rules, partners, ["en", "pl"]),
            "pl:kryminalny pattern i → y / pl:bloku same",
        )


class TipPartnerTests(unittest.TestCase):
    """cognates.js names the partner from the strongest sense over the cutoff."""

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_partner_comes_from_a_sense_over_the_cutoff(self) -> None:
        script = r"""
            import fs from 'node:fs';
            import vm from 'node:vm';
            const source = fs.readFileSync(process.env.COGNATES_JS, 'utf8').replace(/^import .*$/mg, '');
            const payload = {
                schema: 'cognate-score/v4', language: 'es', known_languages: ['en', 'pl'],
                thresholds: { en: 0.75, pl: 0.8 },
                tip_rules: {
                    en: [{ from: 'o', to: '', where: 'end', free: true, label: 'x', twins: [] }],
                    pl: [{ from: 'v', to: 'w', where: 'any', twins: [] }],
                },
                scores: {
                    hace: { hacer: { do: { en: 0.2 } } },
                    banco: { banco: { bank: { en: 0.8 } } },
                    accidentes: { accidente: { accident: { en: 0.78 } } },
                },
                matches: {},
            };
            const context = {
                console, localStorage: { getItem: () => null, setItem: () => {} },
                document: { getElementById: () => null },
                fetch: async () => ({ ok: true, json: async () => payload }),
            };
            context.globalThis = context;
            vm.runInNewContext(source, context);
            await context.loadCognateScores({ cognatesPath: 'x' });
            const deck = [
                { word: 'hace', meanings: [{ headword: 'hacer', translation: 'to do; has' }] },
                { word: 'banco', meanings: [
                    { headword: 'banco', translation: 'bank' },
                    { headword: 'banco', translation: 'school (of fish)' },
                ]},
                { word: 'accidentes', meanings: [{ headword: 'accidente', translation: 'accident' }] },
            ];
            context.applyCognateScores(deck, 'es');
            const out = deck.map(item => {
                const p = context.cognateTipPartner(item, 'en');
                return p ? `${p.word}:${p.headword}:${p.meaning.translation}` : 'null';
            });
            out.push(context.cognateTipRules('en').length, context.cognateTipRules('pl').length);
            out.push(context.cognateTipLanguages().join('+'));
            context.writeKnownLanguages(['en', 'pl']);
            await Promise.resolve();
            out.push(context.cognateTipLanguages().join('+'));
            console.log(out.join(' '));
        """
        out = _node(script, COGNATES_JS=str(COGNATES))
        # Polish is offered only once the learner reads it.
        self.assertEqual(out, "null bank:banco:bank accident:accidente:accident 1 1 en en+pl")


class ShippedRulesTests(unittest.TestCase):
    def test_shipped_maps_carry_the_configs_tip_rules(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/sync_cognate_tip_rules.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_every_rule_is_well_formed(self) -> None:
        for pair in ("es-en", "pt-en", "fr-en", "nl-en", "fi-en", "cs-en", "cs-pl"):
            for rule in _rules(pair):
                self.assertIn(rule["where"], {"start", "end", "any", "double", "single"}, (pair, rule))
                if rule.get("free"):
                    self.assertTrue(rule.get("label"), (pair, rule))
                else:
                    self.assertGreaterEqual(len(rule["twins"]), 2, (pair, rule))
                    self.assertNotEqual(rule["from"], rule["to"], (pair, rule))


if __name__ == "__main__":
    unittest.main()
