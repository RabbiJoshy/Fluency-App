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

const IRREGULAR_ENGLISH_PAST = {
    be: ['was', 'were', 'was', 'were', 'were', 'were'],
    have: 'had', do: 'did', go: 'went', say: 'said', make: 'made',
    take: 'took', come: 'came', see: 'saw', know: 'knew', get: 'got',
    give: 'gave', find: 'found', think: 'thought', tell: 'told',
    become: 'became', leave: 'left', feel: 'felt', put: 'put',
    keep: 'kept', let: 'let', begin: 'began', hear: 'heard',
    sit: 'sat', stand: 'stood', win: 'won', lose: 'lost', run: 'ran',
    eat: 'ate', drink: 'drank', write: 'wrote', read: 'read',
    speak: 'spoke', sleep: 'slept', fall: 'fell', hold: 'held',
    bring: 'brought', buy: 'bought', catch: 'caught', teach: 'taught',
    build: 'built', send: 'sent', spend: 'spent', pay: 'paid',
    sell: 'sold', meet: 'met', lead: 'led', break: 'broke',
    choose: 'chose', drive: 'drove', grow: 'grew', hide: 'hid',
    ride: 'rode', rise: 'rose', sing: 'sang', swim: 'swam',
    throw: 'threw', wear: 'wore', forget: 'forgot', understand: 'understood',
};

const IRREGULAR_ENGLISH_PP = {
    be: 'been', have: 'had', do: 'done', go: 'gone', say: 'said',
    make: 'made', take: 'taken', come: 'come', see: 'seen', know: 'known',
    get: 'got', give: 'given', find: 'found', think: 'thought', tell: 'told',
    speak: 'spoken', write: 'written', eat: 'eaten', break: 'broken',
    choose: 'chosen', drive: 'driven', forget: 'forgotten',
};

const TENSE_KIND = {
    Presente: 'present', Present: 'present', Présent: 'present',
    Pretérito: 'past', 'Passé simple': 'past',
    Imperfecto: 'imperfect', Imperfeito: 'imperfect', Imparfait: 'imperfect',
    Futuro: 'future', Futur: 'future',
    Condicional: 'conditional', Conditionnel: 'conditional',
    Imperativo: 'imperative', Impératif: 'imperative', Imperative: 'imperative',
    'Imp. Negativo': 'imperative_neg',
    'Subj. Presente': 'present', 'Subj. Présent': 'present',
    'Subj. Imperfecto': 'imperfect', 'Subj. Imperfeito': 'imperfect',
    'Subj. Imparfait': 'imperfect', 'Subj. Futuro': 'future',
};

function thirdPersonSingular(verb) {
    const lower = String(verb || '').toLocaleLowerCase('en');
    if (/(?:s|x|z|ch|sh)$/u.test(lower)) return `${lower}es`;
    if (/[^aeiou]y$/u.test(lower)) return `${lower.slice(0, -1)}ies`;
    return `${lower}s`;
}

function inflectEnglishPresent(verb, personIdx) {
    const lower = String(verb || '').toLocaleLowerCase('en');
    const irregular = IRREGULAR_ENGLISH_PRESENT[lower];
    if (irregular) return irregular[personIdx];
    return personIdx === 2 ? thirdPersonSingular(lower) : lower;
}

function inflectEnglishPast(verb, personIdx) {
    const lower = String(verb || '').toLocaleLowerCase('en');
    const irregular = IRREGULAR_ENGLISH_PAST[lower];
    if (Array.isArray(irregular)) return irregular[personIdx];
    if (typeof irregular === 'string') return irregular;
    if (/e$/u.test(lower)) return `${lower}d`;
    if (/[^aeiou]y$/u.test(lower)) return `${lower.slice(0, -1)}ied`;
    return `${lower}ed`;
}

function englishIng(verb) {
    const lower = String(verb || '').toLocaleLowerCase('en');
    if (lower === 'be') return 'being';
    if (/ie$/u.test(lower)) return `${lower.slice(0, -2)}ying`;
    if (/e$/u.test(lower) && !/ee$/u.test(lower)) return `${lower.slice(0, -1)}ing`;
    return `${lower}ing`;
}

function englishPastParticiple(verb) {
    const lower = String(verb || '').toLocaleLowerCase('en');
    if (IRREGULAR_ENGLISH_PP[lower]) return IRREGULAR_ENGLISH_PP[lower];
    return inflectEnglishPast(lower, 0);
}

function finiteEnglishCue(kind, personIdx, head, rest) {
    const tail = rest || '';
    const base = String(head || '').toLocaleLowerCase('en');
    if (kind === 'imperative') {
        if (personIdx === 0) return null;
        return personIdx === 3 ? `let's ${base}${tail}!` : `${base}${tail}!`;
    }
    if (kind === 'imperative_neg') {
        if (personIdx === 0) return null;
        return personIdx === 3 ? `let's not ${base}${tail}!` : `don't ${base}${tail}!`;
    }
    const pronoun = ENGLISH_PRONOUNS[personIdx];
    if (!pronoun) return null;
    let body;
    if (kind === 'present') body = inflectEnglishPresent(head, personIdx);
    else if (kind === 'past') body = inflectEnglishPast(head, personIdx);
    else if (kind === 'imperfect') {
        const aux = (personIdx === 0 || personIdx === 2) ? 'was' : 'were';
        body = `${aux} ${englishIng(head)}`;
    } else if (kind === 'future') body = `will ${base}`;
    else if (kind === 'conditional') body = `would ${base}`;
    else return null;
    if (!body) return null;
    const form = `${pronoun} ${body}${tail}`;
    return personIdx === 2 ? expandThirdSingular(form) : form;
}

function conjugationTableCue(card, meaning, translation, conjugationData) {
    if (!conjugationData || !meaning) return null;
    if (isUsageNoteGloss(translation)) return null;
    const lemma = conjugationLemma(card, meaning);
    const surface = conjugationLookupSurface(card);
    if (!lemma || !surface || foldCueForm(surface) === foldCueForm(lemma)) return null;
    const entry = conjugationEntry(conjugationData, lemma);
    if (!entry || typeof entry !== 'object') return null;
    const parts = infinitiveParts(translation);
    if (!parts) return null;
    const surfaceFold = foldCueForm(surface);
    if (entry.gerund && foldCueForm(entry.gerund) === surfaceFold) {
        return `${englishIng(parts.head)}${parts.rest}`;
    }
    if (entry.past_participle && foldCueForm(entry.past_participle) === surfaceFold) {
        return `${englishPastParticiple(parts.head)}${parts.rest}`;
    }
    const cues = [];
    const seen = new Set();
    for (const [tenseName, forms] of Object.entries(entry.tenses || {})) {
        const kind = TENSE_KIND[tenseName];
        if (!kind || !Array.isArray(forms)) continue;
        forms.forEach((form, personIdx) => {
            if (!form || form === '—' || foldCueForm(form) !== surfaceFold) return;
            const cue = finiteEnglishCue(kind, personIdx, parts.head, parts.rest);
            if (cue && !seen.has(cue)) {
                seen.add(cue);
                cues.push(cue);
            }
        });
    }
    return cues.length ? cues.join(' / ') : null;
}

function isUsageNoteGloss(translation) {
    return /^(?:see |used |indicates |forms? )/i.test(String(translation || '').trim());
}

/**
 * Inflect a Wiktionary infinitive gloss from the person/number already on
 * the sense. SpanishDict cards do not carry those surface marks; they keep
 * using the optional conjugated-English table when one is present.
 */
export function grammarProductionCue(card, meaning, translation) {
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

    const parts = infinitiveParts(translation);
    if (!parts) return null;
    const inflected = inflectEnglishPresent(parts.head, personIdx);
    if (!inflected) return null;
    const form = `${ENGLISH_PRONOUNS[personIdx]} ${inflected}${parts.rest}`;
    return personIdx === 2 ? expandThirdSingular(form) : form;
}

function normalizeAnalysis(morph) {
    let mood = String(morph?.mood || '').toLocaleLowerCase('es');
    let tense = String(morph?.tense || '').toLocaleLowerCase('es');
    if (mood === 'participio' || mood === 'participio-pasado') mood = 'participo';
    if (tense === 'participio' || tense === 'participio-pasado') tense = 'participo';
    return { mood, tense, key: mood && tense ? `${mood}/${tense}` : '' };
}

function expandThirdSingular(form) {
    if (/^he\s/iu.test(form)) return form.replace(/^he\s/iu, 'he/she/it ');
    if (/^he'/iu.test(form)) return form.replace(/^he'/iu, "he/she/it'");
    return form;
}

function infinitiveParts(translation) {
    const value = String(translation || '').trim();
    if (!value.startsWith('to ')) return null;
    const body = value.slice(3).trim();
    if (!body) return null;
    const splitAt = body.indexOf(' ');
    return splitAt === -1
        ? { head: body, rest: '' }
        : { head: body.slice(0, splitAt), rest: body.slice(splitAt) };
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

function cueForAnalysis(analysisRows, morph, translation) {
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
            ? expandThirdSingular(derived)
            : derived;
    }

    if (NONFINITE_MOODS.has(analysis.mood)) return row[0] || null;
    if (personIdx === undefined) return null;
    const form = row[personIdx] || null;
    if (!form) return null;

    // Spanish indicative/conditional 3sg covers he, she, it, and formal you.
    // Imperative 3sg is instead an usted command, so its subject stays implicit.
    return personIdx === 2 && analysis.mood !== 'imperativo'
        ? expandThirdSingular(form)
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

    const tableCue = meaning
        ? conjugationTableCue(card, meaning, translation, options.conjugationData)
        : null;
    if (tableCue) return tableCue;

    if (conjugatedEnglishData) {
        const lemma = foldCueForm(conjugationLemma(card, meaning));
        const analysisRows = conjugatedEnglishData?.[lemma]?.[translation];
        if (analysisRows) {
            const rawMorph = card.mergedLemma ? card._activeExampleMorphology : card.morphology;
            const morphCandidates = (Array.isArray(rawMorph) ? rawMorph : [rawMorph]).filter(Boolean);
            const forms = morphCandidates
                .map(morph => cueForAnalysis(analysisRows, morph, translation))
                .filter((form, index, all) => form && all.indexOf(form) === index);
            if (forms.length) {
                // Some Spanish surfaces genuinely encode more than one supported
                // reading (da = indicative "gives" or command "give!"). Showing
                // both compactly is more useful than reverting the entire card
                // to an uninflected dictionary gloss.
                return forms.join(' / ');
            }
        }
    }

    return meaning ? grammarProductionCue(card, meaning, translation) : null;
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
