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
            if (lemmaGroupKey(casada) !== 'casado') throw new Error('noun and adjective casado are one lemma');
            if (lemmaHeadwordsOf(casada).length !== 1) throw new Error('POS must not split the headword');
            if (lemmaGroupKey(fue) !== '') throw new Error('fue must not fold into ser or ir');
            if (lemmaGroupKey(withPhrase) !== 'favor') throw new Error('a phrase sense must not count as a second lemma');
            if (lemmaGroupKey(legacy) !== 'casar') throw new Error('a headword-less row keeps the shipped lemma');

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
