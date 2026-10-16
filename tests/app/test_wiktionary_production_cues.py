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
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), tables, 'I/he/she spoke'],
    [{ targetWord: 'hablaré' }, verb('hablar', 'to speak'), tables, 'I will speak'],
    [{ targetWord: 'hablaría' }, verb('hablar', 'to speak'), tables, 'I/he/she would speak'],
    [{ targetWord: 'habla' }, verb('hablar', 'to speak'), tables, 'he/she speaks'],
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
    }, verb('hablar', 'to speak'), tables, null],
    [{
        targetWord: 'hablo',
        lemma: 'hablar',
        productionAnswer: 'hablar',
        displaySurface: 'hablar',
        citationForm: 'hablar',
        representativeSurface: 'hablo',
        mergedLemma: true,
        _activeExampleSurface: 'hablo',
    }, { pos: 'verb', translation: 'to speak' }, tables, null],
    [{
        targetWord: 'aime',
        citationForm: 'aimer',
        lemma: '',
    }, {
        pos: 'SENSE_CYCLE',
        cycle_pos: 'verb',
        translation: 'to love',
        allSenses: [{ headword: 'aimer' }],
    }, tables, 'I/he/she love(s)'],
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
    [{ targetWord: 'était' }, verb('être', 'to be; indicates a point in time'), 'it was'],
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

    def test_pronoun_detection_factoring_and_rows_ignore_the_example(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import {
    detectExamplePronoun,
    compressPronounCues,
    englishProductionCue,
} from %s;

const tables = {
    hablar: {
        tenses: {
            Presente: ['hablo', 'hablas', 'habla', 'hablamos', 'habláis', 'hablan'],
            Pretérito: ['hablé', 'hablaste', 'habló', 'hablamos', 'hablasteis', 'hablaron'],
            Imperfecto: ['hablaba', 'hablabas', 'hablaba', 'hablábamos', 'hablabais', 'hablaban'],
            Condicional: ['hablaría', 'hablarías', 'hablaría', 'hablaríamos', 'hablaríais', 'hablarían'],
            Imperativo: ['—', 'habla', 'hable', 'hablemos', 'hablad', 'hablen'],
        },
    },
};
const verb = (headword, translation) => ({
    pos: 'verb',
    translation,
    headword,
});

// 1. Pronoun detection from example sentence translations
const pronounCases = [
    ['She always listens carefully.', 'she'],
    ["He doesn't listen.", 'he'],
    ["She's listening.", 'she'],
    ["He’s listening.", 'he'],
    ['Listening to music is fun.', null],
    ['He told her that she should listen.', null],
    ['She told him to leave.', 'she'],
    ['He gave her a book.', 'he'],
];
for (const [text, expected] of pronounCases) {
    const actual = detectExamplePronoun(text);
    if (actual !== expected) {
        throw new Error(`detectExamplePronoun(${JSON.stringify(text)}): expected ${expected}, got ${actual}`);
    }
}

// 2. Predicate factoring & pronoun compression
const compressCases = [
    [['I listen', 'he/she listens'], 'I/he/she listen(s)'],
    [['I listen', 'she listens'], 'I/she listen(s)'],
    [['I listen', 'he listens'], 'I/he listen(s)'],
    [['I watch', 'he/she watches'], 'I/he/she watch(es)'],
    [['I should be', 'he/she should be'], 'I/he/she should be'],
    [['I was speaking', 'she was speaking'], 'I/she was speaking'],
    [['he/she speaks', 'speak!'], 'he/she speaks / speak!'],
    ['I listen / he/she listens', 'I/he/she listen(s)'],
    [['I listen to music', 'he/she listens to music'], 'I/he/she listen(s) to music'],
];
for (const [input, expected] of compressCases) {
    const actual = compressPronounCues(input);
    if (actual !== expected) {
        throw new Error(`compressPronounCues(${JSON.stringify(input)}): expected ${expected}, got ${actual}`);
    }
}

// 3. A row describes the word, not the sentence on screen: the example being
// shown never changes the person (was: "she speaks", "I spoke").
const cueCases = [
    [{ targetWord: 'habla' }, verb('hablar', 'to speak'), { conjugationData: tables }, 'he/she speaks'],
    [{ targetWord: 'habla' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'She speaks Spanish.' } }, 'he/she speaks'],
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), { conjugationData: tables }, 'I/he/she spoke'],
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'I was speaking to him.' } }, 'I/he/she spoke'],
    [{ targetWord: 'hablaba', _activeExample: { english: 'He was speaking.' } }, verb('hablar', 'to speak'), { conjugationData: tables }, 'I/he/she spoke'],
    [{ targetWord: 'hablaría' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'She would speak to him.' } }, 'I/he/she would speak'],
];

const results = cueCases.map(([card, sense, options, expected]) => ({
    expected,
    actual: englishProductionCue(card, sense, null, options),
}));
console.log(JSON.stringify(results));
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

    def test_inflected_rows_read_as_natural_english(self) -> None:
        """INFLECT: cases taken from the live es/pt v23 decks (old row in comments)."""
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue } from %s;

const tables = {
    ser: { tenses: {
        Presente: ['soy', 'eres', 'es', 'somos', 'sois', 'son'],
        Imperfecto: ['era', 'eras', 'era', 'éramos', 'erais', 'eran'],
        'Subj. Presente': ['sea', 'seas', 'sea', 'seamos', 'seáis', 'sean'],
        'Subj. Imperfecto': ['fuera', 'fueras', 'fuera', 'fuéramos', 'fuerais', 'fueran'],
        Imperativo: ['—', 'sé', 'sea', 'seamos', 'sed', 'sean'],
    } },
    tener: { tenses: {
        Imperfecto: ['tenía', 'tenías', 'tenía', 'teníamos', 'teníais', 'tenían'],
        'Subj. Imperfecto': ['tuviera', 'tuvieras', 'tuviera', 'tuviéramos', 'tuvierais', 'tuvieran'],
    } },
    parecer: { tenses: {
        Presente: ['parezco', 'pareces', 'parece', 'parecemos', 'parecéis', 'parecen'],
        Imperativo: ['—', 'parece', 'parezca', 'parezcamos', 'pareced', 'parezcan'],
    } },
    ir: { tenses: {
        Presente: ['voy', 'vas', 'va', 'vamos', 'vais', 'van'],
        Imperativo: ['—', 've', 'vaya', 'vamos', 'id', 'vayan'],
    } },
    esperar: { tenses: {
        Presente: ['espero', 'esperas', 'espera', 'esperamos', 'esperáis', 'esperan'],
        Imperativo: ['—', 'espera', 'espere', 'esperemos', 'esperad', 'esperen'],
    } },
    venir: { tenses: { Imperativo: ['—', 'ven', 'venga', 'vengamos', 'venid', 'vengan'] } },
    hablar: { tenses: {
        'Subj. Presente': ['hable', 'hables', 'hable', 'hablemos', 'habléis', 'hablen'],
        'Imp. Negativo': ['—', 'no hables', 'no hable', 'no hablemos', 'no habléis', 'no hablen'],
    } },
    querer: { tenses: { Pretérito: ['quise', 'quisiste', 'quiso', 'quisimos', 'quisisteis', 'quisieron'] } },
    correr: { gerund: 'corriendo', tenses: {} },
    pensar: { past_participle: 'pensado', tenses: {} },
    dejar: { tenses: { Pretérito: ['dejé', 'dejaste', 'dejó', 'dejamos', 'dejasteis', 'dejaron'] } },
    golpear: { tenses: { Pretérito: ['golpeé', 'golpeaste', 'golpeó', 'golpeamos', 'golpeasteis', 'golpearon'] } },
    valer: { tenses: { Imperfecto: ['valía', 'valías', 'valía', 'valíamos', 'valíais', 'valían'] } },
    ver: { tenses: { Pretérito: ['vi', 'viste', 'viu', 'vimos', 'vistes', 'viram'] } },
    pertencer: { tenses: {
        Presente: ['pertenço', 'pertences', 'pertence', 'pertencemos', 'pertenceis', 'pertencem'],
        Imperativo: ['—', 'pertence', 'pertença', 'pertençamos', 'pertencei', 'pertençam'],
    } },
    fazer: { tenses: { Presente: ['faço', 'fazes', 'faz', 'fazemos', 'fazeis', 'fazem'] } },
    respeitar: { tenses: { Presente: ['respeito', 'respeitas', 'respeita', 'respeitamos', 'respeitais', 'respeitam'] } },
    pegar: { tenses: { Presente: ['pego', 'pegas', 'pega', 'pegamos', 'pegais', 'pegam'] } },
    tomar: { tenses: { 'Subj. Presente': ['tome', 'tomes', 'tome', 'tomemos', 'tomeis', 'tomem'] } },
    'ser-pt': { tenses: { 'Subj. Futuro': ['for', 'fores', 'for', 'formos', 'fordes', 'forem'] } },
    fumar: { gerund: 'fumando', tenses: {} },
    explodir: { tenses: { Pretérito: ['explodi', 'explodiste', 'explodiu', 'explodimos', 'explodistes', 'explodiram'] } },
};
const verb = (headword, translation) => ({ pos: 'verb', translation, headword });
const plain = { conjugationData: tables };
// A form that is also a command shows one reading: the command when the
// card's own sentences are two-thirds commands or the example on screen is one.
const sentences = (...english) => english.map((text, i) => ({ target: `s${i}`, english: text }));
const cases = [
    // imperfect is simple past (was: "I/he/she was being", "was having")
    ['era', verb('ser', 'to be'), plain, 'I/he/she was'],
    ['era', verb('ser', 'to be'), plain, 'I/he/she was', sentences('I was a very different person then.')],
    ['tenía', verb('tener', 'to have'), plain, 'I/he/she had'],
    // past subjunctive is simple past; be is "were" (was: "I/he/she was being")
    ['fuera', verb('ser', 'to be'), plain, 'I/he/she were'],
    ['tuviera', verb('tener', 'to have'), plain, 'I/he/she had'],
    // present subjunctive is plain present; the usted command is dropped (was: "be! / I am / he/she is")
    ['sea', verb('ser', 'to be'), plain, 'I am / he/she is'],
    // a statement wins over an identical command (was: "seem! / he/she seems")
    ['parece', verb('parecer', 'to seem'), plain, 'he/she seems'],
    ['parece', verb('parecer', 'to seem'), plain, 'he/she seems',
        sentences("It's not at all what it looks like.", 'She seems tired.', 'Seems fine to me.')],
    ['vamos', verb('ir', 'to go'), plain, 'we go'],
    // one reading per row: the command only when the card's sentences are
    // overwhelmingly commands (two-thirds) ...
    ['vamos', verb('ir', 'to go'), plain, 'we go',
        sentences("Let's go!", "Come on, let's go.", 'We go every day.', 'We are going home.')],
    ['vamos', verb('ir', 'to go'), plain, "let's go!",
        sentences("Let's go!", "Come on, let's go.", "Let's go home.", 'We are going home.')],
    ['espera', verb('esperar', 'to wait'), plain, 'he/she waits',
        sentences('Wait here, please.', 'Wait for me!', 'She waits every day.', 'He is waiting.')],
    ['espera', verb('esperar', 'to wait'), { ...plain, activeExample: { english: 'She waits every day.' } }, 'wait!',
        sentences('Wait!', 'Wait here.', 'Wait for me.', 'She waits every day.')],
    // ... or when the example on screen is a command for that row's verb
    ['vamos', verb('ir', 'to go'), { ...plain, activeExample: { english: "Come on, let's go!" } }, "let's go!"],
    ['espera', verb('esperar', 'to wait'), { ...plain, activeExample: { english: 'Wait here, please.' } }, 'wait!'],
    ['espera', verb('esperar', 'to wait'), { ...plain, activeExample: { english: 'Look at that!' } }, 'he/she waits'],
    ['hables', verb('hablar', 'to speak'), { ...plain, activeExample: { english: "Don't speak to me like that." } }, "don't speak!"],
    ['hables', verb('hablar', 'to speak'), plain, 'you speak',
        sentences("Don't speak to me like that.", 'I want you to speak.')],
    ['hables', verb('hablar', 'to speak'), plain, 'you speak'],
    // a form that is only a command stays one
    ['ven', verb('venir', 'to come'), plain, 'come!'],
    // English spelling (was: "I meaned", "runing", "planed", "I lended")
    ['quise', verb('querer', 'to mean'), plain, 'I meant'],
    ['corriendo', verb('correr', 'to run'), plain, 'running'],
    ['pensado', verb('pensar', 'to plan'), plain, 'planned'],
    ['dejé', verb('dejar', 'to lend'), plain, 'I lent'],
    ['golpeé', verb('golpear', 'to hit oneself'), plain, 'I hit myself'],
    ['explodiu', verb('explodir', 'to cause/suffer an explosion'), plain, 'he/she caused/suffered an explosion'],
    // brackets stay whole and are written once (was: "I saw (to be able to see")
    ['vi', verb('ver', 'to see (to be able to see; not to be blind or blinded)'), plain,
        'I saw (to be able to see; not to be blind or blinded)'],
    ['pertence', verb('pertencer', 'to belong (to be property (of); to be owned (by))'), plain,
        'he/she belongs (to be property (of); to be owned (by))'],
    // every gloss is kept (was: "I play", "revere! / he/she reveres")
    ['faço', verb('fazer', 'to play; to pretend to be'), plain, 'I play; pretend to be'],
    ['respeita', verb('respeitar', 'to revere, venerate'), plain, 'he/she reveres, venerates'],
    ['pega', verb('pegar', 'to start an engine, vehicle'), plain, 'he/she starts an engine, vehicle'],
    ['fumando', verb('fumar', 'to smoke, to deliberately inhale smoke'), plain, 'smoking, deliberately inhaling smoke'],
    // two readings show one clause each
    ['tome', verb('tomar', 'to take; to experience, undergo (to put oneself into, to be subjected to)'), plain,
        'I/he/she take(s)'],
    // Portuguese future subjunctive reads as present (was: "I/he/she will be")
    ['for', verb('ser-pt', 'to be'), plain, 'I am / he/she is'],
    // no verb in front: no inflection rather than "I/he/she was noting care less"
    ['valía', verb('valer', 'to not care less'), plain, null],
];
const out = cases.map(([surface, sense, options, expected, cardSentences]) => {
    const card = { targetWord: surface, meanings: [{ ...sense, allExamples: cardSentences || [] }] };
    return { surface, expected, actual: englishProductionCue(card, sense, null, options) };
});
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

    def test_verbs_only_a_thing_can_do_take_it(self) -> None:
        """INFLECT-2: pasa is "it happens", gusta "it pleases"; people keep he/she."""
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue } from %s;

const tables = {
    pasar: { past_participle: 'pasado', tenses: {
        Presente: ['paso', 'pasas', 'pasa', 'pasamos', 'pasáis', 'pasan'],
        Imperfecto: ['pasaba', 'pasabas', 'pasaba', 'pasábamos', 'pasabais', 'pasaban'],
    } },
    gustar: { past_participle: 'gustado', tenses: {
        Presente: ['gusto', 'gustas', 'gusta', 'gustamos', 'gustáis', 'gustan'],
    } },
    encantar: { tenses: { Presente: ['encanto', 'encantas', 'encanta', 'encantamos', 'encantáis', 'encantan'] } },
    valer: { tenses: { Presente: ['valgo', 'vales', 'vale', 'valemos', 'valéis', 'valen'] } },
    hablar: { tenses: { Presente: ['hablo', 'hablas', 'habla', 'hablamos', 'habláis', 'hablan'] } },
};
const verb = (headword, translation) => ({ pos: 'verb', translation, headword });
const plain = { conjugationData: tables };
const cases = [
    ['pasa', verb('pasar', 'to happen'), 'it happens'],
    ['pasa', verb('pasar', 'to spend'), 'he/she spends'],
    ['pasan', verb('pasar', 'to happen'), 'they happen'],
    ['pasaba', verb('pasar', 'to happen'), 'it happened'],
    ['vale', verb('valer', 'to cost'), 'it costs'],
    ['vale', verb('valer', 'to be worth'), 'it is worth'],
    ['gusta', verb('gustar', 'to like'), 'it pleases'],
    ['gustan', verb('gustar', 'to like'), 'they please'],
    ['gustado', verb('gustar', 'to like'), 'liked'],
    ['encanta', verb('encantar', 'to love'), 'it delights'],
    ['habla', verb('hablar', 'to speak'), 'he/she speaks'],
];
console.log(JSON.stringify(cases.map(([surface, sense, expected]) => ({
    surface, expected,
    actual: englishProductionCue({ targetWord: surface, meanings: [sense] }, sense, null, plain),
}))));
""" % json.dumps(REVERSE_CUES.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        for row in json.loads(result.stdout):
            self.assertEqual(row["actual"], row["expected"], row)

    def test_reflexive_tables_and_agreeing_participles_inflect(self) -> None:
        """INFLECT pass 2: -se tables are "me siento"; participles agree (feita)."""
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue, conjugationCellMatches } from %s;

const tables = {
    sentirse: { gerund: 'sintiéndose', past_participle: 'sentido', tenses: {
        Presente: ['me siento', 'te sientes', 'se siente', 'nos sentimos', 'os sentís', 'se sienten'],
    } },
    irse: { tenses: {
        Pretérito: ['me fui', 'te fuiste', 'se fue', 'nos fuimos', 'os fuisteis', 'se fueron'],
        Imperativo: ['—', 'vete', 'váyase', 'vámonos', 'idos', 'váyanse'],
    } },
    acordarse: { tenses: { Presente: ['me acuerdo', 'te acuerdas', 'se acuerda', 'nos acordamos', 'os acordáis', 'se acuerdan'] } },
    lastimarse: { tenses: { Pretérito: ['me lastimé', 'te lastimaste', 'se lastimó', 'nos lastimamos', 'os lastimasteis', 'se lastimaron'] } },
    arrepender: { tenses: { 'Subj. Presente': ['me arrependa', 'te arrependas', 'se arrependa', 'nos arrependamos', 'vos arrependais', 'se arrependam'] } },
    fazer: { past_participle: 'feito', tenses: {} },
    hacer: { past_participle: 'hecho', tenses: {} },
    morir: { past_participle: 'muerto', tenses: {} },
    'být': { past_participle: 'byl', tenses: {} },
};
const verb = (headword, translation) => ({ pos: 'verb', translation, headword });
const plain = { conjugationData: tables };
const cases = [
    // -se rows (were: the infinitive)
    ['siento', verb('sentirse', 'to feel'), 'I feel'],
    ['fue', verb('irse', 'to leave'), 'he/she left'],
    ['acuerdo', verb('acordarse', 'to remember'), 'I remember'],
    ['lastimé', verb('lastimarse', 'to hurt oneself'), 'I hurt myself'],
    ['sintiendo', verb('sentirse', 'to feel'), 'feeling'],
    ['vete', verb('irse', 'to leave'), 'leave!'],
    ['arrependa', verb('arrepender', 'to regret'), 'I/he/she regret(s)'],
    // agreeing participles (were: the infinitive)
    ['feita', verb('fazer', 'to make'), 'made'],
    ['feitos', verb('fazer', 'to make'), 'made'],
    ['hechas', verb('hacer', 'to do'), 'done'],
    ['muertos', verb('morir', 'to die'), 'died'],
    // a Czech l-form is not a participle with an ending
    ['byla', verb('být', 'to be'), null],
];
const out = cases.map(([surface, sense, expected]) => ({
    surface, expected, actual: englishProductionCue({ targetWord: surface }, sense, null, plain),
}));
const matches = [
    ['me siento', 'siento', true], ['se fue', 'fue', true], ['siento', 'siento', true],
    ['no te sientas', 'sientas', false], ['—', 'siento', false], ['meto', 'to', false],
].map(([form, surface, expected]) => ({ surface: `${form} ~ ${surface}`, expected, actual: conjugationCellMatches(form, surface) }));
console.log(JSON.stringify([...out, ...matches]));
""" % json.dumps(REVERSE_CUES.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        for row in json.loads(result.stdout):
            self.assertEqual(row["actual"], row["expected"], row)

    def test_conjugation_table_opens_on_a_reflexive_form(self) -> None:
        """The table matches cells as the sense rows do: fue opens irse's Pretérito."""
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute flashcards-conj.js")
        conj = REPOSITORY_ROOT / "app" / "js" / "flashcards-conj.js"
        script = r"""
globalThis.window = globalThis;
globalThis.selectedLanguage = 'spanish';
const { buildConjugationTableHTML } = await import(%s);
const irse = { tenses: {
    Presente: ['me voy', 'te vas', 'se va', 'nos vamos', 'os vais', 'se van'],
    Pretérito: ['me fui', 'te fuiste', 'se fue', 'nos fuimos', 'os fuisteis', 'se fueron'],
} };
const sentirse = { tenses: { Presente: ['me siento', 'te sientes', 'se siente', 'nos sentimos', 'os sentís', 'se sienten'] } };
const hablar = { tenses: { Presente: ['hablo', 'hablas', 'habla', 'hablamos', 'habláis', 'hablan'] } };
const read = html => ({
    shown: [...html.matchAll(/class="conj-table" data-tense="([^"]+)"/g)].map(m => m[1]),
    active: [...html.matchAll(/<tr class=" conj-active">(.*?)<\/tr>/g)]
        .map(m => m[1].replace(/<td class="conj-pronoun">[^<]*<\/td>/, '').replace(/<[^>]+>/g, '')),
    pronounKept: html.includes('<span class="conj-stem">me </span><span class="conj-stem">s</span><span class="conj-ending">iento</span>'),
});
console.log(JSON.stringify({
    fue: read(buildConjugationTableHTML(irse, 'fue', 'irse')),
    siento: read(buildConjugationTableHTML(sentirse, 'siento', 'sentirse')),
    hablo: read(buildConjugationTableHTML(hablar, 'hablo', 'hablar')),
}));
""" % json.dumps(conj.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        out = json.loads(result.stdout)
        self.assertEqual(out["fue"]["shown"], ["Pretérito"])
        self.assertEqual(out["fue"]["active"], ["se fue"])
        self.assertEqual(out["siento"]["active"], ["me siento"])
        self.assertTrue(out["siento"]["pronounKept"])
        self.assertEqual(out["hablo"]["active"], ["hablo"])

    def test_gloss_notes_drop_and_bare_meanings_inflect(self) -> None:
        """A dictionary note is left off an inflected row; a meaning without "to" inflects."""
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue } from %s;

const pres3 = forms => ({ tenses: { Presente: forms } });
const tables = {
    estar: pres3(['estou', 'estás', 'está', 'estamos', 'estais', 'estão']),
    ir: pres3(['vou', 'vais', 'vai', 'vamos', 'ides', 'vão']),
    buscar: pres3(['busco', 'buscas', 'busca', 'buscamos', 'buscais', 'buscam']),
    tirar: pres3(['tiro', 'tiras', 'tira', 'tiramos', 'tirais', 'tiram']),
    colar: pres3(['colo', 'colas', 'cola', 'colamos', 'colais', 'colam']),
    pegar: pres3(['pego', 'pegas', 'pega', 'pegamos', 'pegais', 'pegam']),
    faltar: pres3(['falto', 'faltas', 'falta', 'faltamos', 'faltais', 'faltam']),
    cantar: pres3(['canto', 'cantas', 'canta', 'cantamos', 'cantais', 'cantam']),
    moldar: pres3(['moldo', 'moldas', 'molda', 'moldamos', 'moldais', 'moldam']),
    olhar: pres3(['olho', 'olhas', 'olha', 'olhamos', 'olhais', 'olham']),
};
const verb = (headword, translation) => ({ pos: 'verb', translation, headword });
const plain = { conjugationData: tables };
const cases = [
    // notes leave the row (was: "he/she is; forms the progressive aspect")
    ['está', verb('estar', 'to be; forms the progressive aspect'), 'he/she is'],
    ['vai', verb('ir', 'to be doing; formula used in greetings'), 'he/she is doing'],
    ['vou', verb('ir', 'to keep on; to go on; ~ on; forms the continuative aspect'), 'I keep on; go on'],
    ['cola', verb('colar', 'to stick or attach, not necessarily using glue'), 'he/she sticks or attaches'],
    // meanings without "to" inflect (was: "he/she fetches, pick up")
    ['busca', verb('buscar', 'to fetch, pick up'), 'he/she fetches, picks up'],
    ['tira', verb('tirar', 'to take, take out, take away'), 'he/she takes, takes out, takes away'],
    ['canta', verb('cantar', 'to say with rhythm, chant'), 'he/she says with rhythm, chants'],
    // an object alternate and "be" predicates stay as they are
    ['pega', verb('pegar', 'to start an engine, vehicle'), 'he/she starts an engine, vehicle'],
    ['falta', verb('faltar', 'to be absent, not present'), 'he/she is absent, not present'],
    // "form" and "see" are verbs, not notes
    ['molda', verb('moldar', 'to shape, form'), 'he/she shapes, forms'],
    ['olha', verb('olhar', 'to look, see'), 'he/she looks, sees'],
];
console.log(JSON.stringify(cases.map(([surface, sense, expected]) => ({
    surface, expected, actual: englishProductionCue({ targetWord: surface }, sense, null, plain),
}))));
""" % json.dumps(REVERSE_CUES.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        for row in json.loads(result.stdout):
            self.assertEqual(row["actual"], row["expected"], row)

    def test_merged_lemma_disables_verb_and_noun_inflection(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required to execute reverse-cues.js")
        script = r"""
import { englishProductionCue } from %s;

const tables = {
    hablar: {
        tenses: {
            Presente: ['hablo', 'hablas', 'habla', 'hablamos', 'habláis', 'hablan'],
        },
    },
};
const verbSense = { pos: 'verb', translation: 'to speak', headword: 'hablar' };
const nounSense = { pos: 'noun', translation: 'house', headword: 'casa' };

// 1. Verbs: regular card inflects, mergedLemma card returns null in both directions
const verbUnmerged = { targetWord: 'hablo', lemma: 'hablar' };
const verbMerged = { targetWord: 'hablo', lemma: 'hablar', mergedLemma: true, displaySurface: 'hablar' };

// 2. Plural nouns: regular card pluralizes to 'houses', mergedLemma card returns null in both directions
const nounUnmerged = { targetWord: 'casas', lemma: 'casa', productionAnswer: 'casas' };
const nounMerged = { targetWord: 'casas', lemma: 'casa', productionAnswer: 'casas', mergedLemma: true, displaySurface: 'casa' };

const cases = [
    // Unmerged verb
    { actual: englishProductionCue(verbUnmerged, verbSense, null, { conjugationData: tables }), expected: 'I speak' },
    // Merged verb - normal direction
    { actual: englishProductionCue(verbMerged, verbSense, null, { conjugationData: tables }), expected: null },
    // Merged verb - reverse direction
    { actual: englishProductionCue(verbMerged, verbSense, null, { conjugationData: tables, reverseDirection: true }), expected: null },

    // Unmerged plural noun
    { actual: englishProductionCue(nounUnmerged, nounSense, null), expected: 'houses' },
    // Merged plural noun - normal direction
    { actual: englishProductionCue(nounMerged, nounSense, null), expected: null },
    // Merged plural noun - reverse direction
    { actual: englishProductionCue(nounMerged, nounSense, null, { reverseDirection: true }), expected: null },
];

console.log(JSON.stringify(cases));
""" % json.dumps(REVERSE_CUES.as_uri())
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        for row in json.loads(result.stdout):
            self.assertEqual(row["actual"], row["expected"], row)

