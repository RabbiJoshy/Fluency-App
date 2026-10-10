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

    def test_dynamic_pronoun_tracking_and_predicate_factoring(self) -> None:
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

// 3. Dynamic 3sg resolution and factoring through englishProductionCue
const cueCases = [
    // 3sg present: the command reading is dropped; he vs she follows the example
    [{ targetWord: 'habla' }, verb('hablar', 'to speak'), { conjugationData: tables }, 'he/she speaks'],
    [{ targetWord: 'habla' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'She speaks Spanish.' } }, 'she speaks'],
    [{ targetWord: 'habla' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'He speaks Spanish.' } }, 'he speaks'],
    // 1s/3s homophonous imperfect: the example's subject picks one person
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), { conjugationData: tables }, 'I/he/she spoke'],
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'She was speaking Spanish.' } }, 'she spoke'],
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'He was speaking Spanish.' } }, 'he spoke'],
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'I was speaking to him.' } }, 'I spoke'],
    [{ targetWord: 'hablaba' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'He said I was speaking.' } }, 'I/he spoke'],
    // Card with card._activeExample set directly
    [{ targetWord: 'hablaba', _activeExample: { english: 'She was speaking.' } }, verb('hablar', 'to speak'), { conjugationData: tables }, 'she spoke'],
    [{ targetWord: 'hablaba', _activeExample: { english: 'He was speaking.' } }, verb('hablar', 'to speak'), { conjugationData: tables }, 'he spoke'],
    // Conditional
    [{ targetWord: 'hablaría' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'She would speak to him.' } }, 'she would speak'],
    [{ targetWord: 'hablaría' }, verb('hablar', 'to speak'), { conjugationData: tables, activeExample: { english: 'He would speak to her.' } }, 'he would speak'],
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
const ex = english => ({ conjugationData: tables, activeExample: { english } });
const plain = { conjugationData: tables };
const cases = [
    // imperfect is simple past (was: "I/he/she was being", "was having")
    ['era', verb('ser', 'to be'), plain, 'I/he/she was'],
    ['era', verb('ser', 'to be'), ex('I was a very different person then.'), 'I was'],
    ['tenía', verb('tener', 'to have'), plain, 'I/he/she had'],
    // past subjunctive is simple past; be is "were" (was: "I/he/she was being")
    ['fuera', verb('ser', 'to be'), plain, 'I/he/she were'],
    ['tuviera', verb('tener', 'to have'), plain, 'I/he/she had'],
    // present subjunctive is plain present; the usted command is dropped (was: "be! / I am / he/she is")
    ['sea', verb('ser', 'to be'), plain, 'I am / he/she is'],
    // a statement wins over an identical command (was: "seem! / he/she seems")
    ['parece', verb('parecer', 'to seem'), plain, 'he/she seems'],
    ['parece', verb('parecer', 'to seem'), ex("It's not at all what it looks like, all right?"), 'he/she seems'],
    ['vamos', verb('ir', 'to go'), plain, 'we go'],
    // ...unless the example is a command
    ['vamos', verb('ir', 'to go'), ex("Come on, let's go!"), "let's go!"],
    ['espera', verb('esperar', 'to wait'), ex('Wait here, please.'), 'wait!'],
    ['hables', verb('hablar', 'to speak'), ex("Don't speak to me like that."), "don't speak!"],
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
const out = cases.map(([surface, sense, options, expected]) => ({
    surface,
    expected,
    actual: englishProductionCue({ targetWord: surface }, sense, null, options),
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
