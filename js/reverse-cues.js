// English-first cards use several dictionary senses as a compact fingerprint
// for one exact target-language surface. Keep selection and English inflection
// pure here so homographs can be regression-tested without the card DOM.

const REVERSE_CUE_LIMIT = 4;
const SPECIAL_POS = new Set(['MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY']);
const VERB_POS = new Set(['VERB', 'AUX']);

const PERSON_TO_INDEX = { '1s': 0, '2s': 1, '3s': 2, '1p': 3, '2p': 4, '3p': 5 };
const ENGLISH_PRONOUNS = ['I', 'you', 'he', 'we', 'you (pl)', 'they'];
const NONFINITE_MOODS = new Set(['gerundio', 'participo']);

const IRREGULAR_ENGLISH_PLURALS = {
    child: 'children',
    foot: 'feet',
    goose: 'geese',
    louse: 'lice',
    man: 'men',
    mouse: 'mice',
    ox: 'oxen',
    person: 'people',
    tooth: 'teeth',
    woman: 'women',
};

const INVARIANT_ENGLISH_PLURALS = new Set([
    'deer', 'fish', 'means', 'offspring', 'series', 'sheep', 'species',
]);

const UNCOUNTABLE_ENGLISH_NOUNS = new Set([
    'dark', 'darkness', 'dusk', 'nightfall', 'daylight', 'sunlight', 'moonlight',
    'twilight', 'dawn', 'midnight', 'noon',
    'sadness', 'happiness', 'anger', 'love', 'hate', 'fear', 'grief', 'joy',
    'sorrow', 'pity', 'envy', 'pride', 'shame', 'guilt', 'hope', 'faith',
    'courage', 'patience', 'silence', 'peace', 'violence', 'justice',
    'beauty', 'ugliness', 'youth', 'age', 'childhood', 'adulthood',
    'information', 'advice', 'knowledge', 'wisdom', 'news', 'evidence',
    'research', 'progress', 'homework', 'work', 'fun',
    'furniture', 'luggage', 'baggage', 'equipment', 'machinery',
    'clothing', 'jewelry', 'mail', 'money', 'cash', 'currency',
    'music', 'art', 'poetry', 'literature', 'fiction',
    'weather', 'rain', 'snow', 'thunder', 'lightning', 'fog', 'wind', 'heat', 'cold',
    'water', 'milk', 'wine', 'beer', 'coffee', 'tea', 'juice', 'blood',
    'bread', 'rice', 'pasta', 'meat', 'fruit', 'food', 'sugar', 'salt', 'flour',
    'air', 'oxygen', 'smoke', 'dust', 'dirt', 'mud', 'sand', 'grass',
    'gold', 'silver', 'iron', 'steel', 'wood', 'cotton', 'silk', 'wool',
    'traffic', 'transport', 'travel', 'tourism',
    'help', 'luck', 'magic', 'power', 'energy', 'electricity',
    'health', 'fitness', 'strength', 'weakness',
    'space', 'room', 'time', 'sleep', 'rest',
    'laughter', 'applause', 'chaos', 'calm',
]);

function cueText(meaning) {
    return String(meaning?.meaning ?? meaning?.translation ?? '').trim();
}

function cueTextKey(meaning) {
    return cueText(meaning).toLocaleLowerCase('en');
}

function cueGroupKey(meaning) {
    const lemma = String(meaning?.headword || '').trim().toLocaleLowerCase('es');
    const pos = String(meaning?.pos || '').trim().toUpperCase();
    return `${lemma}\u0000${pos}`;
}

function cueWeight(candidate) {
    const value = Number(candidate.meaning?.percentage ?? candidate.meaning?.frequency ?? 0);
    return Number.isFinite(value) ? value : 0;
}

function byWeightThenSource(a, b) {
    return cueWeight(b) - cueWeight(a) || a.index - b.index;
}

function cardHasFiniteVerbMorphology(card) {
    const rows = (Array.isArray(card?.morphology) ? card.morphology : [card?.morphology]).filter(Boolean);
    return rows.some(row => row?.mood && !['infinitivo', 'participio', 'participo'].includes(row.mood));
}

function isNominalSurfaceOf(surface, lemma) {
    const target = String(surface || '').trim().toLocaleLowerCase('es');
    const base = String(lemma || '').trim().toLocaleLowerCase('es');
    if (!target || !base) return false;
    if (target === base) return true;

    const forms = new Set([`${base}s`, `${base}es`]);
    if (base.endsWith('z')) forms.add(`${base.slice(0, -1)}ces`);
    if (base.endsWith('o')) {
        const stem = base.slice(0, -1);
        forms.add(`${stem}a`);
        forms.add(`${stem}os`);
        forms.add(`${stem}as`);
    }
    // SpanishDict groups the article/determiner family under un or uno.
    if (base === 'un' || base === 'uno') {
        ['un', 'una', 'unos', 'unas'].forEach(form => forms.add(form));
    }
    return forms.has(target);
}

function meaningMatchesSurfaceReading(card, meaning) {
    if (!card || !cardHasFiniteVerbMorphology(card)) return true;
    const pos = String(meaning?.pos || '').toUpperCase();
    if (VERB_POS.has(pos)) return true;
    const lemma = meaning?.headword;
    if (!lemma) return true;
    const surface = card.productionAnswer || card.displaySurface || card.targetWord || card.word || '';
    return isNominalSurfaceOf(surface, lemma);
}

/**
 * Choose a bounded semantic fingerprint for an English-first card.
 *
 * A representative from each (lemma, POS) reading is considered before extra
 * senses from a frequent reading. Duplicate English text adds no useful clue,
 * so it is shown only once even when two dictionary leaves share it.
 */
export function selectReverseCueMeanings(meanings, options = {}) {
    const card = options?.card || null;
    const max = Math.max(0, Number(options?.limit ?? REVERSE_CUE_LIMIT) || 0);
    if (!max || !Array.isArray(meanings)) return [];

    const available = meanings
        .map((meaning, index) => ({ meaning, index }))
        .filter(({ meaning }) => {
            const pos = String(meaning?.pos || '').toUpperCase();
            return cueText(meaning) && !SPECIAL_POS.has(pos);
        });
    const compatible = available.filter(({ meaning }) => meaningMatchesSurfaceReading(card, meaning));
    // Compatibility removes lemma-menu leakage such as the noun `power` from
    // finite `puedes`. Older/incomplete decks can lack a compatible gloss
    // entirely; retain their best packaged gloss rather than render a blank
    // English-first face.
    const candidates = compatible.length ? compatible : available;

    const groups = new Map();
    for (const candidate of candidates) {
        const key = cueGroupKey(candidate.meaning);
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(candidate);
    }

    const rankedGroups = [...groups.values()]
        .map(group => [...group].sort(byWeightThenSource))
        .sort((a, b) => byWeightThenSource(a[0], b[0]));
    const selected = [];
    const selectedIndexes = new Set();
    const seenText = new Set();

    const add = candidate => {
        const textKey = cueTextKey(candidate.meaning);
        if (!textKey || seenText.has(textKey) || selected.length >= max) return false;
        selected.push(candidate);
        selectedIndexes.add(candidate.index);
        seenText.add(textKey);
        return true;
    };

    // Cover each distinct lemma/POS reading while there is room. If a group's
    // strongest gloss duplicates an earlier one, try its next distinct sense.
    for (const group of rankedGroups) {
        if (selected.length >= max) break;
        group.some(add);
    }

    // Then add the strongest remaining senses, preserving useful polysemy
    // without turning the front into an exhaustive dictionary dump.
    for (const candidate of [...candidates].sort(byWeightThenSource)) {
        if (selected.length >= max) break;
        if (!selectedIndexes.has(candidate.index)) add(candidate);
    }

    // Dictionary/source order is the clearest display order once selection is
    // complete; ranking affects inclusion, not the learner-facing sequence.
    return selected.sort((a, b) => a.index - b.index).map(({ meaning }) => meaning);
}

function isRegularSpanishPlural(surface, lemma) {
    const target = String(surface || '').trim().toLocaleLowerCase('es');
    const base = String(lemma || '').trim().toLocaleLowerCase('es');
    if (!target || !base || target === base) return false;
    const candidates = new Set([`${base}s`, `${base}es`]);
    if (base.endsWith('z')) candidates.add(`${base.slice(0, -1)}ces`);
    return candidates.has(target);
}

function pluralizeEnglishWord(gloss) {
    const word = String(gloss || '').trim();
    if (!/^[A-Za-z]+$/u.test(word)) return null;
    const lower = word.toLocaleLowerCase('en');
    if (UNCOUNTABLE_ENGLISH_NOUNS.has(lower)) return lower;
    let plural;
    if (IRREGULAR_ENGLISH_PLURALS[lower]) {
        plural = IRREGULAR_ENGLISH_PLURALS[lower];
    } else if (INVARIANT_ENGLISH_PLURALS.has(lower)) {
        plural = lower;
    } else if (/[^aeiou]y$/u.test(lower)) {
        plural = `${lower.slice(0, -1)}ies`;
    } else if (/(?:s|x|z|ch|sh)$/u.test(lower)) {
        plural = `${lower}es`;
    } else {
        plural = `${lower}s`;
    }
    if (/^[A-Z]/u.test(word)) return plural[0].toUpperCase() + plural.slice(1);
    return plural;
}

function nounProductionCue(card, meaning, translation) {
    if (String(meaning?.pos || '').toUpperCase() !== 'NOUN') return null;
    const surface = card?.productionAnswer || card?.displaySurface || card?.targetWord || '';
    const lemma = meaning?.headword || card?.lemma || '';
    if (!isRegularSpanishPlural(surface, lemma)) return null;
    return pluralizeEnglishWord(translation);
}

// Accents tell verb forms apart (hablo / habló, está / esta): fold case and
// Unicode composition only.
function foldCueForm(value) {
    return String(value || '').normalize('NFC').toLocaleLowerCase().trim();
}

function meaningIsVerb(meaning) {
    const pos = String(meaning?.pos || '').toUpperCase();
    if (!pos) return true;
    if (VERB_POS.has(pos)) return true;
    if (pos === 'SENSE_CYCLE') {
        return VERB_POS.has(String(meaning?.cycle_pos || '').toUpperCase());
    }
    return false;
}

function conjugationLemma(card, meaning) {
    const fromSense = String(meaning?.headword || '').trim();
    if (fromSense) return fromSense;
    if (String(meaning?.pos || '').toUpperCase() === 'SENSE_CYCLE' && Array.isArray(meaning?.allSenses)) {
        const fromCycle = meaning.allSenses.find(sense => String(sense?.headword || '').trim());
        if (fromCycle) return String(fromCycle.headword).trim();
    }
    return String(card?.citationForm || card?.lemma || '').trim();
}

function conjugationEntry(conjugationData, lemma) {
    if (!conjugationData || !lemma) return null;
    if (conjugationData[lemma]) return conjugationData[lemma];
    const folded = foldCueForm(lemma);
    if (conjugationData[folded]) return conjugationData[folded];
    for (const key of Object.keys(conjugationData)) {
        if (foldCueForm(key) === folded) return conjugationData[key];
    }
    return null;
}

// Our table builder writes a Spanish -se verb as its base verb's forms with
// the reflexive pronoun in front ("me siento"), and Wiktionary does the same
// for a few always-pronominal verbs (pt arrepender). A card's word is the
// bare verb, so a cell is matched on its form without that pronoun. The
// conjugation table matches cells through the same two functions.
const LEADING_REFLEXIVE = /^(?:me|te|se|nos|os)\s+/u;

export function splitReflexiveCell(form) {
    const value = String(form || '').trim();
    const match = LEADING_REFLEXIVE.exec(value.toLocaleLowerCase());
    if (!match) return { pronoun: '', bare: value };
    return { pronoun: value.slice(0, match[0].length), bare: value.slice(match[0].length) };
}

export function conjugationCellMatches(form, surface) {
    if (!form || form === '—') return false;
    const target = foldCueForm(surface);
    if (!target) return false;
    return foldCueForm(form) === target || foldCueForm(splitReflexiveCell(form).bare) === target;
}

// Tables list the masculine singular participle; feita and hechas agree with
// their noun. Only an -o participle (Spanish, Portuguese) takes -a/-os/-as,
// so a Czech l-form (byl) is never read as one. The caller tries this only
// after every finite cell: pt pegar's short participle is pego, and pega is
// still "he/she catches".
function agreeingParticipleMatches(participle, surface) {
    const base = foldCueForm(participle);
    const target = foldCueForm(surface);
    if (!base || !target || base === target) return false;
    if (!base.endsWith('o')) return false;
    const stem = base.slice(0, -1);
    return target === `${stem}a` || target === `${stem}os` || target === `${stem}as`;
}

// A -se verb's gerund carries its pronoun and the accent that comes with it
// (sintiéndose); "me estoy sintiendo" shows the bare form.
function gerundMatches(gerund, surface) {
    const base = foldCueForm(gerund);
    const target = foldCueForm(surface);
    if (!base || !target) return false;
    if (base === target) return true;
    if (!base.endsWith('se') || base.length < 6) return false;
    const bare = base.slice(0, -2).normalize('NFD').replace(/\u0301/gu, '').normalize('NFC');
    return bare === target;
}

export function conjugationLookupSurface(card) {
    if (!card) return '';
    const lemma = String(card.citationForm || card.lemma || '').trim();
    const candidates = [
        card._activeExampleSurface,
        card.mergedLemma ? '' : card.productionAnswer,
        card.mergedLemma ? '' : card.displaySurface,
        card.representativeSurface,
        card.targetWord,
        card.word,
    ];
    for (const value of candidates) {
        const surface = String(value || '').trim();
        if (!surface) continue;
        if (lemma && foldCueForm(surface) === foldCueForm(lemma)) continue;
        return surface;
    }
    return String(
        card.targetWord || card.word || card.displaySurface || card.productionAnswer || ''
    ).trim();
}

function meaningFeatureList(meaning) {
    const metadata = meaning?.metadata || {};
    const listed = metadata.sense_metadata?.features
        || metadata.specialist_features
        || meaning?.specialist_features
        || [];
    return Array.isArray(listed) ? listed : [];
}

function surfaceGrammarFromMeaning(meaning) {
    const grammar = {};
    for (const feature of meaningFeatureList(meaning)) {
        if (feature?.kind !== 'surface_mark') continue;
        const value = String(feature.value || '');
        const splitAt = value.indexOf('=');
        if (splitAt <= 0) continue;
        grammar[value.slice(0, splitAt)] = value.slice(splitAt + 1);
    }
    return grammar;
}

function personIndexFromGrammar(grammar) {
    const person = String(grammar.person || '');
    if (!person) return undefined;
    const number = grammar.number === 'plural' || grammar.number === 'dual' ? 'p' : 's';
    return PERSON_TO_INDEX[`${person}${number}`];
}

const IRREGULAR_ENGLISH_PRESENT = {
    be: ['am', 'are', 'is', 'are', 'are', 'are'],
    have: ['have', 'have', 'has', 'have', 'have', 'have'],
    do: ['do', 'do', 'does', 'do', 'do', 'do'],
    go: ['go', 'go', 'goes', 'go', 'go', 'go'],
};

// base past past-participle. Regular verbs are spelled by rule below; a verb
// belongs here only when the rule would misspell it (meaned, beated, lended).
const IRREGULAR_ENGLISH_VERBS = Object.fromEntries(`
arise arose arisen|awake awoke awoken|bear bore borne|beat beat beaten
become became become|begin began begun|bend bent bent|bet bet bet|bid bid bid
bind bound bound|bite bit bitten|bleed bled bled|blow blew blown|break broke broken
breed bred bred|bring brought brought|broadcast broadcast broadcast|build built built
burst burst burst|buy bought bought|cast cast cast|catch caught caught
choose chose chosen|cling clung clung|come came come|cost cost cost|creep crept crept
cut cut cut|deal dealt dealt|dig dug dug|do did done|draw drew drawn|drink drank drunk
drive drove driven|eat ate eaten|fall fell fallen|feed fed fed|feel felt felt
fight fought fought|find found found|flee fled fled|fling flung flung|fly flew flown
forbid forbade forbidden|forecast forecast forecast|foresee foresaw foreseen
forget forgot forgotten|forgive forgave forgiven|freeze froze frozen|get got got
give gave given|go went gone|grind ground ground|grow grew grown|hang hung hung
have had had|hear heard heard|hide hid hidden|hit hit hit|hold held held|hurt hurt hurt
keep kept kept|kneel knelt knelt|know knew known|lay laid laid|lead led led
leap leapt leapt|leave left left|lend lent lent|let let let|light lit lit|lose lost lost
make made made|mean meant meant|meet met met|mislead misled misled
mistake mistook mistaken|outdo outdid outdone|overcome overcame overcome
overhear overheard overheard|oversee oversaw overseen|overtake overtook overtaken
pay paid paid|put put put|quit quit quit|read read read|rebuild rebuilt rebuilt
redo redid redone|rid rid rid|ride rode ridden|ring rang rung|rise rose risen
run ran run|say said said|see saw seen|seek sought sought|sell sold sold|send sent sent
set set set|sew sewed sewn|shake shook shaken|shed shed shed|shine shone shone
shoot shot shot|show showed shown|shrink shrank shrunk|shut shut shut|sing sang sung
sink sank sunk|sit sat sat|slay slew slain|sleep slept slept|slide slid slid
sling slung slung|slit slit slit|speak spoke spoken|speed sped sped|spend spent spent
spin spun spun|spit spat spat|split split split|spread spread spread
spring sprang sprung|stand stood stood|steal stole stolen|stick stuck stuck
sting stung stung|stink stank stunk|strike struck struck|string strung strung
strive strove striven|swear swore sworn|sweep swept swept|swell swelled swollen
swim swam swum|swing swung swung|take took taken|teach taught taught|tear tore torn
tell told told|think thought thought|throw threw thrown|thrust thrust thrust
tread trod trodden|undergo underwent undergone|understand understood understood
undertake undertook undertaken|undo undid undone|uphold upheld upheld|upset upset upset
wake woke woken|wear wore worn|weave wove woven|weep wept wept|win won won
wind wound wound|withdraw withdrew withdrawn|withhold withheld withheld
withstand withstood withstood|wring wrung wrung|write wrote written
`.trim().split(/[|\n]/u).map(row => {
    const [base, past, participle] = row.trim().split(/\s+/u);
    return [base, { past, participle }];
}));

// foretell, mistake, overthrow, retake, unwind: a prefix on an irregular
// verb keeps its forms. `lay` is left out: relay and belay are regular.
const IRREGULAR_ENGLISH_PREFIXES = ['be', 'fore', 'mis', 'out', 'over', 're', 'un', 'under', 'with'];

function irregularEnglishVerb(lower) {
    if (IRREGULAR_ENGLISH_VERBS[lower]) return IRREGULAR_ENGLISH_VERBS[lower];
    for (const prefix of IRREGULAR_ENGLISH_PREFIXES) {
        const base = lower.slice(prefix.length);
        if (!lower.startsWith(prefix) || base.length < 2 || base === 'lay') continue;
        const forms = IRREGULAR_ENGLISH_VERBS[base];
        if (forms) return { past: `${prefix}${forms.past}`, participle: `${prefix}${forms.participle}` };
    }
    return null;
}

// Final consonant doubles before -ed/-ing in a stressed closed syllable:
// one-syllable stop/plan/quit by shape, longer verbs only when listed.
const STRESS_FINAL_ENGLISH_VERBS = new Set([
    'abet', 'acquit', 'admit', 'begin', 'commit', 'compel', 'confer', 'control',
    'defer', 'deter', 'dispel', 'distil', 'emit', 'enrol', 'enthral', 'equip',
    'excel', 'expel', 'extol', 'forbid', 'forget', 'fulfil', 'incur', 'instil',
    'occur', 'omit', 'outwit', 'patrol', 'permit', 'prefer', 'program', 'propel',
    'rebel', 'recur', 'refer', 'regret', 'repel', 'submit', 'transfer', 'unwrap',
    'upset',
]);
const CK_ENGLISH_VERBS = new Set(['frolic', 'mimic', 'panic', 'picnic', 'traffic']);

// Tables name tenses in the target language. Each maps to one English
// rendering and one mood, which decides which readings a row shows.
const TENSE_KIND = {
    Presente: 'present', Present: 'present', Présent: 'present',
    Pretérito: 'past', 'Passé simple': 'past',
    Imperfecto: 'imperfect', Imperfeito: 'imperfect', Imparfait: 'imperfect',
    Futuro: 'future', Futur: 'future',
    Condicional: 'conditional', Conditionnel: 'conditional',
    Imperativo: 'imperative', Impératif: 'imperative', Imperative: 'imperative',
    'Imp. Negativo': 'imperative_neg',
    'Subj. Presente': 'subj_present', 'Subj. Présent': 'subj_present',
    'Subj. Imperfecto': 'subj_past', 'Subj. Imperfeito': 'subj_past',
    'Subj. Imparfait': 'subj_past', 'Subj. Futuro': 'subj_future',
};
const KIND_RANK = {
    present: 0, past: 1, imperfect: 2, future: 3, conditional: 4,
    subj_present: 5, subj_past: 6, subj_future: 7, imperative: 8, imperative_neg: 9,
};
const KIND_MOOD = {
    present: 'indicative', past: 'indicative', imperfect: 'indicative',
    future: 'indicative', conditional: 'indicative',
    subj_present: 'subjunctive', subj_past: 'subjunctive', subj_future: 'subjunctive',
    imperative: 'command', imperative_neg: 'command',
};
// Distinct tenses one row may show (hablamos: "we speak / we spoke").
const MAX_ROW_TENSES = 2;

function cleanVerb(verb) {
    return String(verb || '').replace(/[^\p{L}\p{N}]+$/gu, '').trim();
}

function lowerVerb(verb) {
    return cleanVerb(verb).toLocaleLowerCase('en');
}

function doublesFinalConsonant(lower) {
    if (STRESS_FINAL_ENGLISH_VERBS.has(lower)) return true;
    return /^[^aeiou]*(?:qu)?[aeiou][^aeiouwxy]$/u.test(lower);
}

function thirdPersonSingular(verb) {
    const lower = lowerVerb(verb);
    if (!lower) return '';
    if (lower === 'be') return 'is';
    if (/(?:s|x|z|ch|sh|[^aeiou]o)$/u.test(lower)) return `${lower}es`;
    if (/[^aeiou]y$/u.test(lower)) return `${lower.slice(0, -1)}ies`;
    return `${lower}s`;
}

function inflectEnglishPresent(verb, personIdx) {
    const lower = lowerVerb(verb);
    const irregular = IRREGULAR_ENGLISH_PRESENT[lower];
    if (irregular) return irregular[personIdx];
    return personIdx === 2 ? thirdPersonSingular(lower) : lower;
}

function regularEnglishEd(lower) {
    if (/e$/u.test(lower)) return `${lower}d`;
    if (/[^aeiou]y$/u.test(lower)) return `${lower.slice(0, -1)}ied`;
    if (CK_ENGLISH_VERBS.has(lower)) return `${lower}ked`;
    if (doublesFinalConsonant(lower)) return `${lower}${lower.slice(-1)}ed`;
    return `${lower}ed`;
}

function inflectEnglishPast(verb, personIdx, rest = '') {
    const lower = lowerVerb(verb);
    if (lower === 'be') return (personIdx === 0 || personIdx === 2) ? 'was' : 'were';
    // "lie down" is the irregular verb; "lie" alone (mentir) is regular.
    if (lower === 'lie' && /^\s+down\b/u.test(rest)) return 'lay';
    return irregularEnglishVerb(lower)?.past || regularEnglishEd(lower);
}

function englishIng(verb) {
    const lower = lowerVerb(verb);
    if (lower === 'be') return 'being';
    if (/ie$/u.test(lower)) return `${lower.slice(0, -2)}ying`;
    if (/(?:ee|oe|ye)$/u.test(lower)) return `${lower}ing`;
    if (/e$/u.test(lower)) return `${lower.slice(0, -1)}ing`;
    if (CK_ENGLISH_VERBS.has(lower)) return `${lower}king`;
    if (doublesFinalConsonant(lower)) return `${lower}${lower.slice(-1)}ing`;
    return `${lower}ing`;
}

function englishPastParticiple(verb, rest = '') {
    const lower = lowerVerb(verb);
    if (lower === 'be') return 'been';
    if (lower === 'lie' && /^\s+down\b/u.test(rest)) return 'lain';
    return irregularEnglishVerb(lower)?.participle || regularEnglishEd(lower);
}

// Split at top-level `;` and `,` only, so a parenthetical keeps its own
// punctuation: "to see (to be able to see; not to be blind)" is one clause.
function splitTopLevelClauses(text) {
    const clauses = [];
    let depth = 0;
    let start = 0;
    for (let index = 0; index < text.length; index++) {
        const char = text[index];
        if (char === '(' || char === '[') depth++;
        else if ((char === ')' || char === ']') && depth > 0) depth--;
        else if (depth === 0 && (char === ';' || char === ',')) {
            clauses.push({ text: text.slice(start, index).trim(), sep: char });
            start = index + 1;
        }
    }
    clauses.push({ text: text.slice(start).trim(), sep: '' });
    return clauses.filter(clause => clause.text);
}

function peelTrailingParenthetical(text) {
    const value = String(text || '').trim();
    if (!value.endsWith(')')) return { core: value, paren: '' };
    let depth = 0;
    for (let index = value.length - 1; index >= 0; index--) {
        if (value[index] === ')') depth++;
        else if (value[index] === '(') {
            depth--;
            if (depth === 0) {
                const core = value.slice(0, index).trim();
                return core ? { core, paren: value.slice(index) } : { core: value, paren: '' };
            }
        }
    }
    return { core: value, paren: '' };
}

const ENGLISH_LY_VERBS = new Set([
    'ally', 'apply', 'bully', 'comply', 'dally', 'fly', 'imply', 'multiply',
    'rally', 'rely', 'reply', 'sully', 'supply', 'tally',
]);

function verbClause(core) {
    // "to (angrily) discuss", "to (do) again": the verb is not the first word.
    if (core.startsWith('(')) return null;
    const words = core.split(' ');
    // "to deliberately inhale" keeps its adverb in front: "deliberately inhaling".
    let lead = '';
    if (words.length > 1 && /ly$/u.test(words[0]) && !ENGLISH_LY_VERBS.has(words[0].toLocaleLowerCase('en'))) {
        if (/^(?:and|or)$/iu.test(words[1])) return null;
        lead = `${words.shift()} `;
    }
    const head = cleanVerb(words[0]);
    // "to not care less" has no verb to inflect in front.
    if (!head || /^(?:not|never)$/iu.test(head)) return null;
    // "to stick or attach": both verbs inflect ("sticks or attaches").
    if (words.length === 3 && words[1] === 'or' && head !== 'be' && /^[a-z]+$/u.test(words[2])) {
        return { lead, head: `${head} or ${words[2]}`, rest: '' };
    }
    return { lead, head, rest: words.length > 1 ? ` ${words.slice(1).join(' ')}` : '' };
}

// A dictionary note beside the meanings ("to be; forms the progressive
// aspect", "to cost, especially of something whose price changes often") is
// not English to learn; an inflected row leaves it out.
const GLOSS_NOTE = /^(?:forms?\s+the|formula|introduc(?:es|ing)|especially|esp\.|contrasting|usually|often|typically|generally|mainly|mostly|chiefly|such as|in order to|as in|not necessarily|causing|why|even|used\s+(?:as|for|in|to|when|with)|indicat(?:es|ing)|express(?:es|ing)|denot(?:es|ing)|e\.g\.|i\.e\.|~)(?![\p{L}])/iu;
// Words that never open a verb phrase: "valid or acceptable", "not present",
// "on the fritz", a modal such as "can" or "must".
const BARE_ALTERNATE_STOPWORDS = new Set([
    'a', 'again', 'also', 'an', 'and', 'as', 'at', 'by', 'can', 'could', 'esp', 'etc',
    'for', 'in', 'may', 'might', 'more', 'must', 'no', 'not', 'of', 'off', 'on', 'one',
    'oneself', 'or', 'ought', 'shall', 'should', 'so', 'someone', 'something',
    'somebody', 'the', 'too', 'very', 'will', 'with', 'would',
]);
// A one-word alternate is another object, not a verb, when the "to" verb
// before it has one: "to start an engine, vehicle". A prepositional or
// particle tail is not an object: "to say with rhythm, chant", "to go
// forward, advance".
const NON_OBJECT_REST = /^(?:\s+(?:about|across|after|again|ahead|along|apart|around|at|away|back|by|down|for|forward|from|in|into|off|on|out|over|through|to|together|up|upon|with)\b.*)?$/u;

// A meaning written without "to" ("to fetch, pick up"; "to occur, take
// place, happen") is a verb when it follows one. After "to be" the
// alternates are predicates ("to be absent, not present") and stay as they
// are unless they repeat be.
function bareAlternateClause(core, anchor) {
    if (!anchor) return null;
    if (lowerVerb(anchor.head) === 'be' && !/^be\b/u.test(core)) return null;
    const first = (/^([a-z]+)(?:\s|$)/u.exec(core) || [])[1];
    if (!first || /ly$/u.test(first) && !ENGLISH_LY_VERBS.has(first) || BARE_ALTERNATE_STOPWORDS.has(first)) return null;
    if (!core.includes(' ') && !NON_OBJECT_REST.test(anchor.rest)) return null;
    return verbClause(core);
}

/**
 * Parse an infinitive gloss into clauses the renderer can inflect.
 *
 * Every `to X` clause is a verb, and so is a single-word alternate after one
 * ("to revere, venerate"); anything else is kept verbatim. The gloss's
 * trailing parenthetical is lifted into `tail`, written once after every
 * reading, so a pronoun or `!` never lands inside it.
 */
function inflectableGloss(translation, meaning) {
    const value = String(translation || '').trim().replace(/[.]+$/u, '');
    if (!value.startsWith('to ')) return null;
    const dummyIt = isDummyItCopulaSense(meaning);
    // Clock/weather copulas keep only the copula: "to be; indicates a point
    // in time" is "it was", not "it was; indicates a point in time".
    if (dummyIt && /^to be\b/iu.test(value)) return { clauses: [{ head: 'be', rest: '' }], tail: '' };

    const clauses = [];
    let anchor = null;      // the latest "to" verb
    let previousVerb = false;
    for (const part of splitTopLevelClauses(value)) {
        const { core, paren } = peelTrailingParenthetical(part.text);
        if (clauses.length && GLOSS_NOTE.test(core)) {
            // Drop the note and keep the separator that followed it.
            clauses[clauses.length - 1].sep = part.sep;
            continue;
        }
        let verb = null;
        if (core.startsWith('to ')) {
            verb = verbClause(core.slice(3).trim());
            anchor = verb;
        } else if (previousVerb) {
            verb = bareAlternateClause(core, anchor);
        }
        clauses.push(verb ? { ...verb, paren, sep: part.sep } : { text: part.text, sep: part.sep });
        previousVerb = Boolean(verb);
    }
    if (!clauses[0]?.head) return null;
    if (dummyIt) return { clauses: [{ lead: clauses[0].lead, head: clauses[0].head, rest: clauses[0].rest }], tail: '' };

    const last = clauses[clauses.length - 1];
    let tail = '';
    if (last.head && last.paren) {
        tail = last.paren;
        last.paren = '';
    }
    return { clauses, tail };
}

function renderGlossClauses(clauses, renderVerb) {
    return clauses.map((clause, index) => {
        const body = clause.head
            ? `${renderVerb(clause.head, clause.rest, index === 0, clause.lead || '')}${clause.paren ? ` ${clause.paren}` : ''}`
            : clause.text;
        return index < clauses.length - 1 && clause.sep ? `${body}${clause.sep} ` : body;
    }).join('');
}

// A row with two readings shows only the first clause of each, so
// "tome" is "I take / he/she takes", not both readings of every alternate.
function firstClauseGloss(gloss) {
    if (!gloss || gloss.clauses.length < 2) return gloss;
    const [first] = gloss.clauses;
    return { clauses: [{ lead: first.lead, head: first.head, rest: first.rest, paren: '', sep: '' }], tail: first.paren || '' };
}

// "to cause/suffer" inflects both verbs: "causes/suffers".
function eachVerb(head, inflect) {
    return String(head || '').split(/(\/| or )/u)
        .map(part => (part === '/' || part === ' or ' ? part : inflect(part))).join('');
}

function withGlossTail(cue, gloss) {
    if (!cue) return null;
    return gloss?.tail ? `${cue} ${gloss.tail}` : cue;
}

const REFLEXIVE_BY_SUBJECT = {
    I: ['myself', 'my'],
    you: ['yourself', 'your'],
    he: ['himself', 'his'],
    she: ['herself', 'her'],
    it: ['itself', 'its'],
    'he/she': ['himself/herself', 'his/her'],
    we: ['ourselves', 'our'],
    'you (pl)': ['yourselves', 'your'],
    they: ['themselves', 'their'],
};

function agreeReflexive(rest, subject) {
    const forms = REFLEXIVE_BY_SUBJECT[subject];
    if (!forms || !/\bone(?:self|['’]s)\b/u.test(rest)) return rest;
    return rest.replace(/\boneself\b/gu, forms[0]).replace(/\bone['’]s\b/gu, forms[1]);
}

function thirdPersonSubject(meaning, options = {}) {
    // Clock/weather copulas take dummy it; other 3sg follows the example.
    if (isDummyItCopulaSense(meaning)) return 'it';
    return detectExamplePronoun(options?.activeExample || options?.example) || 'he/she';
}

function imperativeSubject(personIdx) {
    if (personIdx === 3) return 'we';
    return personIdx >= 4 ? 'you (pl)' : 'you';
}

function finiteEnglishCue(kind, personIdx, gloss, meaning, options = {}) {
    if (kind === 'imperative' || kind === 'imperative_neg') {
        if (personIdx === 0) return null;
        const prefix = kind === 'imperative'
            ? (personIdx === 3 ? "let's " : '')
            : (personIdx === 3 ? "let's not " : "don't ");
        const subject = imperativeSubject(personIdx);
        const body = renderGlossClauses(gloss.clauses,
            (head, rest, first, lead) => `${lead}${eachVerb(head, lowerVerb)}${agreeReflexive(rest, subject)}`);
        return `${prefix}${body}!`;
    }
    const subject = personIdx === 2 ? thirdPersonSubject(meaning, options) : ENGLISH_PRONOUNS[personIdx];
    if (!subject) return null;
    const body = renderGlossClauses(gloss.clauses, (head, rawRest, first, lead) => {
        const rest = agreeReflexive(rawRest, subject);
        const base = eachVerb(head, lowerVerb);
        const past = verb => inflectEnglishPast(verb, personIdx, rawRest);
        switch (kind) {
        case 'present':
        case 'subj_present':
        case 'subj_future':
            return `${lead}${eachVerb(head, verb => inflectEnglishPresent(verb, personIdx))}${rest}`;
        // English simple past is right for both Spanish pasts: "was being",
        // "was having" are not, so the imperfect is never progressive.
        case 'past':
        case 'imperfect':
            return `${lead}${eachVerb(head, past)}${rest}`;
        case 'subj_past':
            return `${lead}${eachVerb(head, verb => (lowerVerb(verb) === 'be' ? 'were' : past(verb)))}${rest}`;
        // The auxiliary is written once: "I will play; pretend to be".
        case 'future':
            return `${first ? 'will ' : ''}${lead}${base}${rest}`;
        case 'conditional':
            return `${first ? 'would ' : ''}${lead}${base}${rest}`;
        default:
            return '';
        }
    });
    return body ? `${subject} ${body}` : null;
}

function exampleEnglishText(options = {}) {
    const example = options?.activeExample || options?.example;
    if (!example) return '';
    if (typeof example === 'string') return example;
    return String(example.english || example.translation || '');
}

function sentenceOpening(text) {
    return String(text || '')
        .replace(/^[\s"'“‘«¡¿(\-–—]+/u, '')
        .replace(/^(?:(?:oh|hey|please|now|okay|ok|well|so|just|come on)[,!]?\s+)+/iu, '');
}

/**
 * When a form is both a statement and a command (parece: "he/she seems" or
 * "seem!"), the command is shown only when the example's English is one.
 * Spanish negative commands are subjunctive forms, so "Don't speak." turns a
 * subjunctive reading into "don't speak!".
 */
function commandReadingsShownByExample(readings, gloss, options) {
    const text = sentenceOpening(exampleEnglishText(options));
    const head = lowerVerb(String(gloss?.clauses?.[0]?.head || '').split(/\/| or /u)[0]);
    if (!text || !head) return null;
    const lower = text.toLocaleLowerCase('en');
    if (/\blet['’]?s\b|\blet us\b/u.test(lower)) {
        const hortative = readings.filter(r => r.kind === 'imperative' && r.personIdx === 3);
        if (hortative.length) return hortative;
    }
    const negative = /^(?:don['’]t|do not)\s+([a-z]+)/u.exec(lower);
    if (negative && negative[1] === head) {
        const addressee = readings.find(r =>
            (r.kind === 'imperative_neg' || r.kind === 'subj_present') && ![0, 3].includes(r.personIdx));
        if (addressee) return [{ kind: 'imperative_neg', personIdx: addressee.personIdx }];
    }
    const firstWord = (/^([a-z]+)/u.exec(lower) || [])[1];
    if (firstWord === head) {
        const commands = readings.filter(r => r.kind === 'imperative' && ![0, 3].includes(r.personIdx));
        if (commands.length) return commands.slice(0, 1);
    }
    return null;
}

const FIRST_PERSON_SUBJECT = /(?:^|[^\p{L}])I(?:['’](?:m|d|ll|ve))?(?![\p{L}])/u;

// 1sg and 3sg share a form in several tenses (era, hablaría, aime). Keep the
// one the example's English uses; keep both when it does not say.
function narrowPersonFromExample(readings, options) {
    const persons = new Set(readings.map(r => r.personIdx));
    if (!persons.has(0) || !persons.has(2)) return readings;
    const text = exampleEnglishText(options);
    if (!text) return readings;
    const first = FIRST_PERSON_SUBJECT.test(text);
    const third = Boolean(detectExamplePronoun(text));
    if (first === third) return readings;
    const keep = first ? 0 : 2;
    return readings.filter(r => r.personIdx === keep || (r.personIdx !== 0 && r.personIdx !== 2));
}

function chooseTableReadings(readings, gloss, options) {
    if (!readings.length) return [];
    const exampleCommand = commandReadingsShownByExample(readings, gloss, options);
    let pool = exampleCommand || readings.filter(r => KIND_MOOD[r.kind] !== 'command');
    // A form that is only a command (ven, haz, sé) stays a command.
    if (!pool.length) pool = readings;
    const indicative = pool.filter(r => KIND_MOOD[r.kind] === 'indicative');
    if (indicative.length) pool = indicative;
    const kinds = [...new Set(pool.map(r => r.kind))]
        .sort((a, b) => KIND_RANK[a] - KIND_RANK[b])
        .slice(0, MAX_ROW_TENSES);
    pool = pool
        .filter(r => kinds.includes(r.kind))
        .sort((a, b) => KIND_RANK[a.kind] - KIND_RANK[b.kind] || a.personIdx - b.personIdx);
    return narrowPersonFromExample(pool, options);
}

function conjugationTableCue(card, meaning, translation, conjugationData, options = {}) {
    if (!conjugationData || !meaning) return null;
    if (isUsageNoteGloss(translation)) return null;
    const lemma = conjugationLemma(card, meaning);
    const surface = conjugationLookupSurface(card);
    if (!lemma || !surface || foldCueForm(surface) === foldCueForm(lemma)) return null;
    const entry = conjugationEntry(conjugationData, lemma);
    if (!entry || typeof entry !== 'object') return null;
    const gloss = inflectableGloss(translation, meaning);
    if (!gloss) return null;
    if (entry.gerund && gerundMatches(entry.gerund, surface)) {
        return withGlossTail(renderGlossClauses(gloss.clauses,
            (head, rest, first, lead) => `${lead}${eachVerb(head, englishIng)}${rest}`), gloss);
    }
    const participleCue = () => withGlossTail(renderGlossClauses(gloss.clauses,
        (head, rest, first, lead) => `${lead}${eachVerb(head, verb => englishPastParticiple(verb, rest))}${rest}`), gloss);
    if (entry.past_participle && foldCueForm(entry.past_participle) === foldCueForm(surface)) return participleCue();
    const readings = [];
    for (const [tenseName, forms] of Object.entries(entry.tenses || {})) {
        const kind = TENSE_KIND[tenseName];
        if (!kind || !Array.isArray(forms)) continue;
        forms.forEach((form, personIdx) => {
            if (!conjugationCellMatches(form, surface)) return;
            readings.push({ kind, personIdx });
        });
    }
    if (!readings.length && agreeingParticipleMatches(entry.past_participle, surface)) return participleCue();
    const chosen = chooseTableReadings(readings, gloss, options);
    const render = rowGloss => {
        const cues = [];
        for (const reading of chosen) {
            const cue = finiteEnglishCue(reading.kind, reading.personIdx, rowGloss, meaning, options);
            if (cue && !cues.includes(cue)) cues.push(cue);
        }
        return cues.length ? compressPronounCues(cues) : null;
    };
    let cue = render(gloss);
    let rowGloss = gloss;
    if (cue && cue.includes(' / ') && gloss.clauses.length > 1) {
        rowGloss = firstClauseGloss(gloss);
        cue = render(rowGloss);
    }
    return withGlossTail(cue, rowGloss);
}

function isUsageNoteGloss(translation) {
    return /^(?:see |used |indicates |forms? )/i.test(String(translation || '').trim());
}

/**
 * Inflect a Wiktionary infinitive gloss from the person/number already on
 * the sense. SpanishDict cards do not carry those surface marks; they keep
 * using the optional conjugated-English table when one is present.
 */
export function grammarProductionCue(card, meaning, translation, options = {}) {
    if (!card || !meaning) return null;
    if (!meaningIsVerb(meaning)) return null;
    if (isUsageNoteGloss(translation)) return null;

    const surface = conjugationLookupSurface(card);
    const lemma = conjugationLemma(card, meaning);
    if (!surface || !lemma || foldCueForm(surface) === foldCueForm(lemma)) return null;

    const grammar = surfaceGrammarFromMeaning(meaning);
    if (grammar.mood && grammar.mood !== 'indicative') return null;
    if (grammar.tense && grammar.tense !== 'present') return null;
    const personIdx = personIndexFromGrammar(grammar);
    if (personIdx === undefined) return null;

    const gloss = inflectableGloss(translation, meaning);
    if (!gloss) return null;
    return withGlossTail(finiteEnglishCue('present', personIdx, gloss, meaning, options), gloss);
}

export function detectExamplePronoun(example) {
    if (!example) return null;
    const text = typeof example === 'string'
        ? example
        : String(example.english || example.translation || example.sentence || '');
    if (!text.trim()) return null;
    const hasShe = /\b(?:she|she['’](?:s|d|ll))\b/iu.test(text);
    const hasHe = /\b(?:he|he['’](?:s|d|ll))\b/iu.test(text);
    if (hasShe && !hasHe) return 'she';
    if (hasHe && !hasShe) return 'he';
    return null;
}

const CUE_PRONOUN_RE = /^((?:I|you|he\/she|he|she|it|we|you \(pl\)|they)(?:\/(?:I|you|he\/she|he|she|it|we|you \(pl\)|they))*)\s+(.+)$/i;

function canMergePredicates(a, b) {
    if (!a.pronoun || !b.pronoun) return null;
    const aLower = a.pronoun.toLowerCase();
    const bLower = b.pronoun.toLowerCase();
    if (aLower === bLower) return null;

    const combinePronouns = (p1, p2) => {
        const parts = [...new Set([...p1.split('/'), ...p2.split('/')])];
        return parts.join('/');
    };

    if (a.predicate === b.predicate) {
        return `${combinePronouns(a.pronoun, b.pronoun)} ${a.predicate}`;
    }

    const aParts = aLower.split('/');
    const bParts = bLower.split('/');
    const aHas1s = aParts.includes('i');
    const bHas1s = bParts.includes('i');
    const aHas3s = aParts.some(p => ['he/she', 'he', 'she'].includes(p));
    const bHas3s = bParts.some(p => ['he/she', 'he', 'she'].includes(p));

    if ((aHas1s && !aHas3s && bHas3s && !bHas1s) || (bHas1s && !bHas3s && aHas3s && !aHas1s)) {
        const first = aHas1s ? a : b;
        const third = aHas1s ? b : a;

        const head1 = first.predicate.split(' ')[0];
        const rest1 = first.predicate.slice(head1.length);
        const head3 = third.predicate.split(' ')[0];
        const rest3 = third.predicate.slice(head3.length);

        if (rest1 === rest3) {
            let factoredHead = null;
            if (head3 === `${head1}s`) {
                factoredHead = `${head1}(s)`;
            } else if (head3 === `${head1}es`) {
                factoredHead = `${head1}(es)`;
            }
            if (factoredHead) {
                return `${combinePronouns(first.pronoun, third.pronoun)} ${factoredHead}${rest1}`;
            }
        }
    }

    return null;
}

export function compressPronounCues(cuesInput) {
    if (!cuesInput) return null;
    const cues = Array.isArray(cuesInput)
        ? cuesInput.filter(Boolean)
        : String(cuesInput).split(/\s+\/\s+/).filter(Boolean);
    if (cues.length === 0) return null;
    if (cues.length === 1) return cues[0];

    const parsed = cues.map(cue => {
        const m = String(cue || '').trim().match(CUE_PRONOUN_RE);
        if (m) {
            return { raw: cue, pronoun: m[1], predicate: m[2], merged: false };
        }
        return { raw: cue, pronoun: null, predicate: cue, merged: false };
    });

    const result = [];
    for (let i = 0; i < parsed.length; i++) {
        if (parsed[i].merged) continue;
        let current = parsed[i];
        for (let j = i + 1; j < parsed.length; j++) {
            if (parsed[j].merged) continue;
            const mergedText = canMergePredicates(current, parsed[j]);
            if (mergedText) {
                parsed[j].merged = true;
                const m = mergedText.match(CUE_PRONOUN_RE);
                current = {
                    raw: mergedText,
                    pronoun: m ? m[1] : null,
                    predicate: m ? m[2] : current.predicate,
                    merged: false,
                };
            }
        }
        result.push(current.raw);
    }

    return result.join(' / ');
}

function normalizeAnalysis(morph) {
    let mood = String(morph?.mood || '').toLocaleLowerCase('es');
    let tense = String(morph?.tense || '').toLocaleLowerCase('es');
    if (mood === 'participio' || mood === 'participio-pasado') mood = 'participo';
    if (tense === 'participio' || tense === 'participio-pasado') tense = 'participo';
    return { mood, tense, key: mood && tense ? `${mood}/${tense}` : '' };
}

function dummyItSenseBlob(meaning) {
    if (!meaning || typeof meaning !== 'object') return '';
    return [meaning.context, cueText(meaning)].filter(Boolean).join(' ').toLowerCase();
}

function isDummyItCopulaSense(meaning) {
    const blob = dummyItSenseBlob(meaning);
    if (!blob) return false;
    if (blob.includes('used to express time')) return true;
    if (blob.includes('point in time')) return true;
    if (blob.includes('denote time')) return true;
    if (blob.includes('said of time')) return true;
    if (blob.includes('weather phenomenon')) return true;
    if (blob.includes('of the weather')) return true;
    return /(?:^|[\s;([])weather(?:$|[\s;)\]])/.test(blob);
}

export function expandThirdSingular(form, meaning, options = {}) {
    // Clock/weather copulas take dummy it; other 3sg stays he/she or dynamically tracks example.
    if (isDummyItCopulaSense(meaning)) {
        if (/^he\/she\s/iu.test(form)) return form.replace(/^he\/she\s/iu, 'it ');
        if (/^he\/she'/iu.test(form)) return form.replace(/^he\/she'/iu, "it'");
        if (/^he\s/iu.test(form)) return form.replace(/^he\s/iu, 'it ');
        if (/^he'/iu.test(form)) return form.replace(/^he'/iu, "it'");
        return form;
    }
    const pronoun = detectExamplePronoun(options?.activeExample || options?.example) || 'he/she';
    if (/^he\/she\s/iu.test(form)) return form.replace(/^he\/she\s/iu, `${pronoun} `);
    if (/^he\/she'/iu.test(form)) return form.replace(/^he\/she'/iu, `${pronoun}'`);
    if (/^he\s/iu.test(form)) return form.replace(/^he\s/iu, `${pronoun} `);
    if (/^he'/iu.test(form)) return form.replace(/^he'/iu, `${pronoun}'`);
    return form;
}

function infinitiveParts(translation) {
    const value = String(translation || '').trim().replace(/[.]+$/u, '');
    if (!value.startsWith('to ')) return null;
    const body = value.slice(3).trim();
    if (!body) return null;
    // Strip any trailing semicolon or comma separated alternatives before parsing
    // the head verb. E.g. "to matter; to mind", "to be, to exist"
    const firstClause = body.split(/\s*[;,]\s*/)[0].trim();
    if (!firstClause) return null;
    const splitAt = firstClause.indexOf(' ');
    const rawHead = splitAt === -1 ? firstClause : firstClause.slice(0, splitAt);
    const head = cleanVerb(rawHead);
    const rest = splitAt === -1 ? '' : firstClause.slice(splitAt);
    if (!head) return null;
    return { head, rest };
}

function deriveRegularAnalysisCue(translation, analysis, personIdx) {
    const parts = infinitiveParts(translation);
    if (!parts || personIdx === undefined) return null;
    const verb = `${parts.head}${parts.rest}`;
    if (analysis.mood === 'condicional' && analysis.tense === 'presente') {
        return `${ENGLISH_PRONOUNS[personIdx]} would ${verb}`;
    }
    if (analysis.mood !== 'imperativo' || personIdx === 0) return null;
    if (analysis.tense === 'negativo') {
        return personIdx === 3 ? `let's not ${verb}!` : `don't ${verb}!`;
    }
    if (analysis.tense !== 'afirmativo') return null;
    return personIdx === 3 ? `let's ${verb}!` : `${verb}!`;
}

function cueForAnalysis(analysisRows, morph, translation, meaning, options = {}) {
    const analysis = normalizeAnalysis(morph);
    if (!analysis.key) return null;

    // Step 5e v3 uses full mood/tense keys. Retain the indicative-tense
    // fallback so an already-open client with the v2 data layer still works
    // while the cache update arrives.
    const row = analysisRows?.[analysis.key]
        || (analysis.mood === 'indicativo' ? analysisRows?.[analysis.tense] : null);
    const personIdx = PERSON_TO_INDEX[morph?.person];
    if (!Array.isArray(row)) {
        const derived = deriveRegularAnalysisCue(translation, analysis, personIdx);
        return derived && personIdx === 2 && analysis.mood !== 'imperativo'
            ? expandThirdSingular(derived, meaning || { translation }, options)
            : derived;
    }

    if (NONFINITE_MOODS.has(analysis.mood)) return row[0] || null;
    if (personIdx === undefined) return null;
    const form = row[personIdx] || null;
    if (!form) return null;

    // 3sg English is labelled he/she (matching él/ella). Imperative 3sg is
    // an usted command, so its subject stays implicit.
    return personIdx === 2 && analysis.mood !== 'imperativo'
        ? expandThirdSingular(form, meaning || { translation }, options)
        : form;
}

/**
 * Return a surface-appropriate English cue, or null when the available data
 * cannot support one confidently. Each meaning's own lemma is authoritative;
 * card.lemma is only a legacy fallback for decks without sense-level identity.
 */
export function englishProductionCue(card, meaningOrTranslation, conjugatedEnglishData, options = {}) {
    if (!card || !meaningOrTranslation) return null;
    const meaning = typeof meaningOrTranslation === 'object' ? meaningOrTranslation : null;
    const translation = meaning ? cueText(meaning) : String(meaningOrTranslation || '').trim();
    if (!translation) return null;

    // Merged reverse cards ask for the lemma rather than the visible surface,
    // so surface morphology would be a misleading prompt in that direction.
    if (card.mergedLemma && options.reverseDirection) return null;

    const nounCue = meaning ? nounProductionCue(card, meaning, translation) : null;
    if (nounCue) return nounCue;

    if (meaning && !meaningIsVerb(meaning)) return null;

    const activeExample = options?.activeExample || options?.example || card?._activeExample || null;
    const resolvedOptions = { ...options, activeExample };

    const tableCue = meaning
        ? conjugationTableCue(card, meaning, translation, options.conjugationData, resolvedOptions)
        : null;
    if (tableCue) return tableCue;

    if (conjugatedEnglishData) {
        const lemma = foldCueForm(conjugationLemma(card, meaning));
        const analysisRows = conjugatedEnglishData?.[lemma]?.[translation];
        if (analysisRows) {
            const rawMorph = card.mergedLemma ? card._activeExampleMorphology : card.morphology;
            const morphCandidates = (Array.isArray(rawMorph) ? rawMorph : [rawMorph]).filter(Boolean);
            const forms = morphCandidates
                .map(morph => cueForAnalysis(analysisRows, morph, translation, meaning, resolvedOptions))
                .filter((form, index, all) => form && all.indexOf(form) === index);
            if (forms.length) {
                // Some Spanish surfaces genuinely encode more than one supported
                // reading (da = indicative "gives" or command "give!"). Showing
                // both compactly is more useful than reverting the entire card
                // to an uninflected dictionary gloss.
                return compressPronounCues(forms);
            }
        }
    }

    return meaning ? grammarProductionCue(card, meaning, translation, resolvedOptions) : null;
}

/**
 * Split one real target-language sentence around an exact answer occurrence.
 * The renderer escapes the returned text and substitutes its own blank, so
 * this helper stays presentation-neutral and straightforward to test.
 */
export function splitProductionCloze(sentence, answerSurface) {
    const text = String(sentence || '');
    const answer = String(answerSurface || '').trim();
    if (!text || !answer) return null;
    const body = answer
        .replace(/[.*+?^${}()|[\]\\]/gu, '\\$&')
        .replace(/[’']/gu, "[’']")
        .replace(/\s+/gu, '\\s+');
    let match;
    try {
        match = text.match(new RegExp(`(?<![\\p{L}\\p{N}])(${body})(?![\\p{L}\\p{N}])`, 'iu'));
    } catch (_) {
        return null;
    }
    if (!match || match.index === undefined) return null;
    return {
        before: text.slice(0, match.index),
        matched: match[0],
        after: text.slice(match.index + match[0].length),
    };
}

/**
 * Keep the sentence prompt immutable for one card attempt. Back-side example
 * browsing rerenders the card, but only a new entry or direction change may
 * capture a different prompt.
 */
export function retainProductionPromptAttempt(previous, {
    direction,
    reset = false,
    createHTML,
} = {}) {
    const normalizedDirection = Boolean(direction);
    if (previous && !reset && previous.direction === normalizedDirection) return previous;
    return {
        direction: normalizedDirection,
        html: normalizedDirection && typeof createHTML === 'function'
            ? String(createHTML() || '')
            : '',
    };
}
