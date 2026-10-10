"""Merged lemmas keep only spellings that name one headword."""

import os
import shutil
import subprocess
import unittest
from pathlib import Path


VOCAB = Path(__file__).resolve().parents[2] / "app/js/vocab.js"


class LemmaMergeKeyTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_ambiguous_spelling_does_not_join_either_lemma(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const source = fs.readFileSync(process.env.LEMMA_VOCAB, 'utf8');
            const start = source.indexOf('// lemma-merge-pure');
            const end = source.indexOf('// /lemma-merge-pure');
            if (start < 0 || end < 0) throw new Error('lemma merge helpers missing');
            const context = {};
            vm.runInNewContext(source.slice(start, end), context);
            const { lemmaGroupKey, lemmaSeenKey, lemmaHeadwordsOf, dedupeLemmaMenu } = context;

            const caso = { word: 'casó', meanings: [
                { headword: 'casar', pos: 'VERB', translation: 'to marry' },
            ]};
            const casar = { word: 'casar', lemma: 'casar', meanings: [
                { headword: 'casar', pos: 'VERB', translation: 'to marry' },
            ]};
            const casado = { word: 'casado', lemma: 'casar', meanings: [
                { headword: 'casar', pos: 'VERB', translation: 'to marry' },
                { headword: 'casado', pos: 'NOUN', translation: 'husband' },
                { headword: 'casado', pos: 'ADJ', translation: 'married' },
            ]};
            const casada = { word: 'casada', meanings: [
                { headword: 'casado', pos: 'NOUN', translation: 'wife' },
                { headword: 'casado', pos: 'ADJ', translation: 'married' },
            ]};
            const fue = { word: 'fue', meanings: [
                { headword: 'ser', pos: 'VERB', translation: 'to be' },
                { headword: 'ir', pos: 'VERB', translation: 'to go' },
            ]};
            const withPhrase = { word: 'favor', meanings: [
                { headword: 'favor', pos: 'NOUN', translation: 'favor' },
                { headword: 'por favor', pos: 'PHRASE', translation: 'please' },
            ]};
            const legacy = { word: 'casa', lemma: 'casar', meanings: [] };

            if (lemmaGroupKey(caso) !== 'casar') throw new Error('casó should join casar');
            if (lemmaGroupKey(casar) !== 'casar') throw new Error('casar should join casar');
            if (lemmaGroupKey(casado) !== '') throw new Error('casado must stay outside both lemmas');
            if (lemmaSeenKey(casado) !== '') throw new Error('casado must not inherit casar from the shipped lemma');
            if (lemmaGroupKey(casada) !== '') throw new Error('noun merging needs complete-menu proof');
            if (lemmaHeadwordsOf(casada).length !== 1) throw new Error('POS must not split the headword');
            if (lemmaGroupKey(fue) !== '') throw new Error('fue must not fold into ser or ir');
            withPhrase.noun_merge = { rule_version: 'noun-merge/v2', allowed: true, lemma: 'favor' };
            if (lemmaGroupKey(withPhrase) !== 'favor') throw new Error('a phrase sense must not count as a second lemma');
            if (lemmaGroupKey(legacy) !== '') throw new Error('unloaded rows need a verified merge key');

            const menu = dedupeLemmaMenu([
                { pos: 'VERB', translation: 'to give', source_reference: 'spanishdict-menu:dar:1' },
                { pos: 'VERB', translation: 'to give', source_reference: 'spanishdict-menu:dar:1' },
                { pos: 'VERB', translation: 'to hit', source_reference: 'spanishdict-menu:dar:2' },
            ]);
            if (menu.length !== 2) throw new Error('duplicate headword senses must collapse');
        """
        completed = subprocess.run(
            ["node", "-e", script],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "LEMMA_VOCAB": str(VOCAB)},
        )
        if completed.returncode != 0:
            self.fail(completed.stderr or completed.stdout)


class LemmaMergeExceptionTests(unittest.TestCase):
    """Contractions and expressions frozen on one form keep their own card."""

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_contractions_frozen_forms_and_the_lemma_host(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const source = fs.readFileSync(process.env.LEMMA_VOCAB, 'utf8');
            const pure = source.slice(source.indexOf('// lemma-merge-pure'), source.indexOf('// /lemma-merge-pure'));
            const hostStart = source.indexOf('function selectLemmaModeRepresentatives');
            const host = source.slice(hostStart, source.indexOf('\n}\n', hostStart) + 3);
            const context = {};
            vm.runInNewContext(pure + host, context);
            const { lemmaGroupKey, selectLemmaModeRepresentatives } = context;
            const fail = message => { throw new Error(message); };

            // SpanishDict marks a contraction in its part of speech.
            const al = { word: 'al', meanings: [{ headword: 'a', pos: 'CONTRACTION', translation: 'to the' }] };
            if (lemmaGroupKey(al) !== '') fail('al is a contraction');
            // Wiktionary languages are stamped from their exceptions file.
            const no = { word: 'no', is_contraction: true, meanings: [{ headword: 'em', pos: 'prep', translation: 'in' }] };
            if (lemmaGroupKey(no) !== '') fail('pt no = em + o must not fold into em');
            const nao = { word: 'na', meanings: [{ headword: 'em', pos: 'prep', translation: 'in' }] };
            if (lemmaGroupKey(nao) !== 'em') fail('an unstamped form still merges');

            // An expression frozen on this exact form keeps it.
            const se = { word: 'sé', meanings: [
                { headword: 'ser', pos: 'VERB', translation: 'to be' },
                { headword: 'no sé', pos: 'PHRASE', translation: "I don't know" },
            ]};
            if (lemmaGroupKey(se) !== '') fail('no sé keeps sé');
            // A construction headed by the lemma's own spelling does not.
            const tener = { word: 'tener', meanings: [
                { headword: 'tener', pos: 'VERB', translation: 'to have' },
                { headword: 'tener cuidado', pos: 'PHRASE', translation: 'to be careful' },
            ]};
            if (lemmaGroupKey(tener) !== 'tener') fail('tener cuidado must not keep tener apart');
            const favor = { word: 'favor', meanings: [
                { headword: 'favor', pos: 'NOUN', translation: 'favor' },
                { headword: 'por favor', pos: 'PHRASE', translation: 'please' },
            ]};
            favor.noun_merge = { rule_version: 'noun-merge/v2', allowed: true, lemma: 'favor' };
            if (lemmaGroupKey(favor) !== 'favor') fail('por favor must not keep favor apart');

            // A Speech card whose senses have not loaded uses the shipped key.
            const pending = { word: 'fue', lemma: 'ser', merge_key: '', meanings: [] };
            if (lemmaGroupKey(pending) !== '') fail('a shipped key beats the lemma column');
            const columnOnly = { word: 'fue', lemma: 'ser', meanings: [] };
            if (lemmaGroupKey(columnOnly) !== '') fail('unloaded rows cannot approve a merge from the lemma alone');

            // The lemma's own spelling fronts the merged card.
            const estaba = { word: 'estaba', stableRank: 1, rank: 1, meanings: [{ headword: 'estar', pos: 'VERB', translation: 'to be' }] };
            const estar = { word: 'estar', stableRank: 9, rank: 9, meanings: [{ headword: 'estar', pos: 'VERB', translation: 'to be' }] };
            const kept = selectLemmaModeRepresentatives([estaba, estar]);
            if (kept.length !== 1 || kept[0] !== estar) fail('estar should host the merged card');
            const alone = selectLemmaModeRepresentatives([{ ...estaba }]);
            if (alone.length !== 1 || alone[0].word !== 'estaba') fail('without estar the most frequent form hosts');
        """
        completed = subprocess.run(
            ["node", "-e", script],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "LEMMA_VOCAB": str(VOCAB)},
        )
        if completed.returncode != 0:
            self.fail(completed.stderr or completed.stdout)


class CitationFormTests(unittest.TestCase):
    """A card's citation form is never an expression the word occurs in."""

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_phrase_senses_do_not_name_the_card(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const source = fs.readFileSync(process.env.LEMMA_VOCAB, 'utf8');
            const pure = source.slice(source.indexOf('// lemma-merge-pure'), source.indexOf('// /lemma-merge-pure'));
            const modelStart = source.indexOf('function buildCardFormModel');
            const model = source.slice(modelStart, source.indexOf('\n}\n', modelStart) + 3);
            const context = { selectedLanguage: 'portuguese' };
            vm.runInNewContext(pure + model, context);
            const { assignedHeadwordOf, buildCardFormModel } = context;
            const fail = message => { throw new Error(message); };
            const merged = item => buildCardFormModel(item, item.meanings, { mergedLemma: true });

            // pt-speech-v23: "não é" was é's single most frequent meaning.
            const e = { word: 'é', meanings: [
                { headword: 'ser', pos: 'verb', frequency: '0.2' },
                { headword: 'ser', pos: 'verb', frequency: '0.2' },
                { headword: 'não é', pos: 'PHRASE', frequency: '0.3' },
            ]};
            if (assignedHeadwordOf(e.meanings, 'é') !== 'ser') fail('é cites ser, not não é');
            const eForm = buildCardFormModel(e, e.meanings, { mergedLemma: false });
            if (eForm.citationForm !== 'ser' || eForm.displaySurface !== 'é') fail(`é: ${JSON.stringify(eForm)}`);
            const nao = { word: 'não', meanings: [
                { headword: 'não', pos: 'adv', frequency: '0.2' },
                { headword: 'não é', pos: 'PHRASE', frequency: '0.3' },
            ]};
            const naoForm = merged(nao);
            if (naoForm.displaySurface !== 'não' || naoForm.productionAnswer !== 'não') fail('merged não is titled não');
            // Wiktionary gives some multiword headwords an ordinary part of speech.
            const cinto = [
                { headword: 'cinto', pos: 'noun', frequency: '0.28' },
                { headword: 'cinto de segurança', pos: 'noun', frequency: '0.42' },
            ];
            if (assignedHeadwordOf(cinto, 'cinto') !== 'cinto') fail('cinto cites cinto');
            const repente = { word: 'repente', meanings: [{ headword: 'de repente', pos: 'adv', frequency: '1' }] };
            if (assignedHeadwordOf(repente.meanings, 'repente') !== '') fail('only an expression: no citation');
            if (merged(repente).citationForm !== 'repente') fail('repente falls back to its own spelling');
            if (assignedHeadwordOf([{ headword: 'por favor', pos: 'PHRASE', frequency: '1' }], 'porfavor') !== 'por favor') {
                fail('the same spelling written apart is the citation');
            }

            // A spelling that merges still wears the lemma.
            const estaba = { word: 'estaba', meanings: [{ headword: 'estar', pos: 'VERB', frequency: '1' }] };
            const estabaForm = merged(estaba);
            if (estabaForm.displaySurface !== 'estar' || !estabaForm.mergedLemma) fail('estaba merges into estar');
        """
        completed = subprocess.run(
            ["node", "-e", script],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "LEMMA_VOCAB": str(VOCAB)},
        )
        if completed.returncode != 0:
            self.fail(completed.stderr or completed.stdout)
