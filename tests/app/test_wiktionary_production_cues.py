"""Wiktionary inflected surfaces should show conjugated English, not the lemma gloss."""

from pathlib import Path
import json
import shutil
import subprocess
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REVERSE_CUES = REPOSITORY_ROOT / "app" / "js" / "reverse-cues.js"


class WiktionaryProductionCueTests(unittest.TestCase):
    def test_czech_jsem_becomes_i_am(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue } from %s;

const meaning = {
    pos: 'verb',
    translation: 'to be',
    headword: 'být',
    metadata: {
        specialist_features: [
            { kind: 'surface_mark', value: 'person=1' },
            { kind: 'surface_mark', value: 'number=singular' },
            { kind: 'surface_mark', value: 'tense=present' },
            { kind: 'surface_mark', value: 'mood=indicative' },
        ],
    },
};
const cases = [
    [{ targetWord: 'jsem' }, meaning, 'I am'],
    [{ targetWord: 'je' }, { ...meaning, metadata: { specialist_features: [
        { kind: 'surface_mark', value: 'person=3' },
        { kind: 'surface_mark', value: 'number=singular' },
        { kind: 'surface_mark', value: 'tense=present' },
        { kind: 'surface_mark', value: 'mood=indicative' },
    ] } }, 'he/she is'],
    [{ targetWord: 'jsme' }, { ...meaning, metadata: { specialist_features: [
        { kind: 'surface_mark', value: 'person=1' },
        { kind: 'surface_mark', value: 'number=plural' },
        { kind: 'surface_mark', value: 'tense=present' },
        { kind: 'surface_mark', value: 'mood=indicative' },
    ] } }, 'we are'],
    [{ targetWord: 'být' }, meaning, null],
    [{ targetWord: 'tem' }, {
        pos: 'verb',
        translation: 'to have',
        headword: 'ter',
        metadata: { specialist_features: [
            { kind: 'surface_mark', value: 'person=3' },
            { kind: 'surface_mark', value: 'number=singular' },
            { kind: 'surface_mark', value: 'tense=present' },
            { kind: 'surface_mark', value: 'mood=indicative' },
        ] },
    }, 'he/she has'],
];
const out = cases.map(([card, sense, expected]) => ({
    expected,
    actual: englishProductionCue(card, sense, null),
}));
console.log(JSON.stringify(out));
""" % json.dumps(REVERSE_CUES.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        rows = json.loads(result.stdout)
        for row in rows:
            self.assertEqual(row["actual"], row["expected"], row)

    def test_conjugation_table_inflects_english_without_surface_marks(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue } from %s;

const hablar = {
    gerund: 'hablando',
    past_participle: 'hablado',
    tenses: {
        Presente: ['hablo', 'hablas', 'habla', 'hablamos', 'habláis', 'hablan'],
        Pretérito: ['hablé', 'hablaste', 'habló', 'hablamos', 'hablasteis', 'hablaron'],
        Imperfecto: ['hablaba', 'hablabas', 'hablaba', 'hablábamos', 'hablabais', 'hablaban'],
        Futuro: ['hablaré', 'hablarás', 'hablará', 'hablaremos', 'hablaréis', 'hablarán'],
        Condicional: ['hablaría', 'hablarías', 'hablaría', 'hablaríamos', 'hablaríais', 'hablarían'],
        Imperativo: ['—', 'habla', 'hable', 'hablemos', 'hablad', 'hablen'],
    },
};
const tables = {
    hablar,
    ser: { tenses: { Presente: ['sou', 'és', 'é', 'somos', 'sois', 'são'] } },
    'být': { tenses: { Present: ['jsem', 'jsi', 'je', 'jsme', 'jste', 'jsou'] } },
    être: { tenses: { Présent: ['suis', 'es', 'est', 'sommes', 'êtes', 'sont'] } },
    aimer: { tenses: { Présent: ['aime', 'aimes', 'aime', 'aimons', 'aimez', 'aiment'] } },
};
const verb = (headword, translation) => ({
    pos: 'verb',
    translation,
    headword,
});
const cases = [
    [{ targetWord: 'hablo' }, verb('hablar', 'to speak'), tables, 'I speak'],
    [{ targetWord: 'habló' }, verb('hablar', 'to speak'), tables, 'he/she spoke'],
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), tables, 'I was speaking / he/she was speaking'],
    [{ targetWord: 'hablaré' }, verb('hablar', 'to speak'), tables, 'I will speak'],
    [{ targetWord: 'hablaría' }, verb('hablar', 'to speak'), tables, 'I would speak / he/she would speak'],
    [{ targetWord: 'habla' }, verb('hablar', 'to speak'), tables, 'he/she speaks / speak!'],
    [{ targetWord: 'hablando' }, verb('hablar', 'to speak'), tables, 'speaking'],
    [{ targetWord: 'hablado' }, verb('hablar', 'to speak'), tables, 'spoken'],
    [{ targetWord: 'hablar' }, verb('hablar', 'to speak'), tables, null],
    [{ targetWord: 'sou' }, verb('ser', 'to be'), tables, 'I am'],
    [{ targetWord: 'jsem' }, verb('být', 'to be'), tables, 'I am'],
    [{ targetWord: 'suis' }, verb('être', 'to be'), tables, 'I am'],
    [{ targetWord: 'hablo' }, verb('hablar', 'to speak'), null, null],
    [{
        targetWord: 'hablo',
        lemma: '',
        productionAnswer: 'hablar',
        displaySurface: 'hablar',
        citationForm: 'hablar',
        representativeSurface: 'hablo',
        mergedLemma: true,
        _activeExampleSurface: 'hablo',
    }, verb('hablar', 'to speak'), tables, 'I speak'],
    [{
        targetWord: 'hablo',
        lemma: 'hablar',
        productionAnswer: 'hablar',
        displaySurface: 'hablar',
        citationForm: 'hablar',
        representativeSurface: 'hablo',
        mergedLemma: true,
        _activeExampleSurface: 'hablo',
    }, { pos: 'verb', translation: 'to speak' }, tables, 'I speak'],
    [{
        targetWord: 'aime',
        citationForm: 'aimer',
        lemma: '',
    }, {
        pos: 'SENSE_CYCLE',
        cycle_pos: 'verb',
        translation: 'to love',
        allSenses: [{ headword: 'aimer' }],
    }, tables, 'I love / he/she loves'],
];
const out = cases.map(([card, sense, data, expected]) => ({
    expected,
    actual: englishProductionCue(card, sense, null, { conjugationData: data }),
}));
console.log(JSON.stringify(out));
""" % json.dumps(REVERSE_CUES.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        rows = json.loads(result.stdout)
        for row in rows:
            self.assertEqual(row["actual"], row["expected"], row)

    def test_time_and_weather_copulas_use_dummy_it(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue } from %s;

const tables = {
    ser: { tenses: {
        Presente: ['soy', 'eres', 'es', 'somos', 'sois', 'son'],
        Pretérito: ['fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron'],
        Futuro: ['seré', 'serás', 'será', 'seremos', 'seréis', 'serán'],
    } },
    faire: { tenses: { Présent: ['fais', 'fais', 'fait', 'faisons', 'faites', 'font'] } },
    fazer: { tenses: { Presente: ['faço', 'fazes', 'faz', 'fazemos', 'fazeis', 'fazem'] } },
    être: { tenses: { Imparfait: ['étais', 'étais', 'était', 'étions', 'étiez', 'étaient'] } },
};
const verb = (headword, translation, extra = {}) => ({
    pos: 'verb',
    translation,
    headword,
    ...extra,
});
const cases = [
    [{ targetWord: 'es' }, verb('ser', 'to be', { context: 'used to express time' }), 'it is'],
    [{ targetWord: 'es' }, verb('ser', 'to be', { context: 'used to talk about a characteristic' }), 'he/she is'],
    [{ targetWord: 'fue' }, verb('ser', 'to be', { context: 'used to express time' }), 'it was'],
    [{ targetWord: 'será' }, verb('ser', 'to be; indicates a point in time'), 'it will be'],
    [{ targetWord: 'était' }, verb('être', 'to be; indicates a point in time'), 'it was being'],
    [{ targetWord: 'fait' }, verb('faire', 'to be', { context: 'weather' }), 'it is'],
    [{ targetWord: 'faz' }, verb('fazer', 'to be; to occur (said of a weather phenomenon)'), 'it is'],
    [{ targetWord: 'faz' }, verb('fazer', 'to pass (said of time)'), 'it passes'],
    [{ targetWord: 'faz' }, verb('fazer', 'to do'), 'he/she does'],
];
const out = cases.map(([card, sense, expected]) => ({
    expected,
    actual: englishProductionCue(card, sense, null, { conjugationData: tables }),
}));
console.log(JSON.stringify(out));
""" % json.dumps(REVERSE_CUES.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        rows = json.loads(result.stdout)
        for row in rows:
            self.assertEqual(row["actual"], row["expected"], row)
