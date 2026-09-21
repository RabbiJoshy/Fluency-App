// Card rendering, flip, swipe, keyboard shortcuts.
// Main function: updateCard() (~line 950) renders the current flashcard front + back.
// Key exports: updateCard, flipCard, nextCard, handleSwipeAction, selectMeaning, cycleExample.
import './state.js?v=20260825ak';
import './speech.js?v=20260825ak';
import './side-dock.js?v=20260921sd';
import {
    collectRecentWrongWords,
    exampleReinforcesRecentMistake,
    filterPersonalisedExamples,
} from './example-personalisation.js?v=20260825ak';
import {
    parseSpanishDictUsageContext,
    spanishDictUsageCandidateForms,
} from './spanishdict-usage.js?v=20260825ak';
import {
    conjugationLookupSurface,
    englishProductionCue,
    retainProductionPromptAttempt,
    selectReverseCueMeanings,
    splitProductionCloze,
} from './reverse-cues.js?v=20260917a';
import {
    compactConstructionMetadata,
    contextWithoutSenseMetadata,
    escapeCardText,
    isSenseDefiningGrammar,
    isSupportingSenseMetadata,
    isWiktionaryGrammarNote,
    legacyObjectPronounProjection,
    projectWiktionaryGloss,
    compactLearnerSenseMetadata,
    contextCollidesWithMetadata,
    metadataTextIsRedundant,
    resolveMeaningDifferentiator,
    scoreSenseMetadata,
    readableSenseNote,
    senseMetadataPeers,
    senseMetadataDisplay,
    senseMetadataHTML,
    senseMetadataItems,
    splitSenseMetadataClauses,
    toggleSenseMetadataChip,
    toggleSenseMetadataOverflow,
    SENSE_CONSTRUCTION_TAGS,
    SENSE_REGISTER_TAGS,
    SENSE_CONSTRUCTION_SHORT,
} from './card-metadata-pills.js?v=20260921details';

// --- Spanish rank lookup for personal easiness ---
let _spanishRanks = null;  // word -> rank (loaded once)
let _spanishRanksLoading = false;
let _conjugationData = null;  // lemma -> {tenses, gerund, past_participle, translation}
let _conjugationLoadPromise = null;  // shared in-flight promise so concurrent callers don't double-fetch
let _conjugatedEnglishData = null;  // lemma -> translation -> mood/tense -> person row (or one nonfinite form)
let _conjugatedEnglishLoading = false;
let _deckScrubberActive = false;
let _suppressDeckScrubberClickUntil = 0;

// Regex cache for the render hot path. Word/MWE/clitic highlight + filter
// patterns are deterministic in their inputs, so compiling once per unique
// (pattern, flags) and reusing avoids thousands of RegExp constructions
// per card render — especially the deck-word highlight loop which scales
// with deck size. Safe to share: callers use .test() on non-/g regexes
// and .replace() on /g ones, both of which are stateless across calls.
const _regexCache = new Map();
// One immutable front-side sentence prompt per card attempt. Weak keys keep
// this render-only state out of card/session serialization.
const _productionPromptByCard = new WeakMap();
function _cachedRegex(pattern, flags) {
    const key = flags + ':' + pattern;
    let re = _regexCache.get(key);
    if (re === undefined) {
        re = new RegExp(pattern, flags);
        _regexCache.set(key, re);
    }
    return re;
}

function _mweCandidateForms(mwe, preferred = '') {
    const rawVariants = mwe?.variants || [];
    const variants = Array.isArray(rawVariants) ? rawVariants : Object.keys(rawVariants);
    const forms = [preferred, mwe?.expression, ...variants]
        .map(value => String(value || '').trim())
        .filter(Boolean);
    return forms.filter((form, index) =>
        forms.findIndex(candidate => candidate.toLocaleLowerCase('es') === form.toLocaleLowerCase('es')) === index);
}

function _mweRegex(form, flags = 'iu') {
    const tokens = String(form || '').trim().split(/\s+/u).filter(Boolean);
    const body = tokens.map((token, index) => {
        const literal = /^\[pron\]$/iu.test(token)
            ? '(?:me|te|se|le|les|nos|lo|la|los|las)'
            : token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/['’]/gu, "['’]");
        if (index === 0) return literal;
        // Caribbean elisions are inconsistently spaced in source lyrics:
        // the curated ``vo' a`` form must also match the displayed ``vo'a``.
        const separator = /['’]$/u.test(tokens[index - 1]) ? '\\s*' : '\\s+';
        return separator + literal;
    }).join('');
    return _cachedRegex(`(?<![\\p{L}\\p{N}])(${body})(?![\\p{L}\\p{N}])`, flags);
}

function _matchedMweForm(mwe, text, preferred = '') {
    const plain = String(text || '').replace(/<[^>]*>/g, '');
    for (const form of _mweCandidateForms(mwe, preferred)) {
        if (_mweRegex(form, 'iu').test(plain)) return form;
    }
    return '';
}

function getProductionEnglishCue(card, meaningOrTranslation) {
    return englishProductionCue(card, meaningOrTranslation, _conjugatedEnglishData, {
        reverseDirection: isFlipped,
        conjugationData: _conjugationData,
    });
}

function joinSpokenGlossAndContext(gloss, context) {
    const cleanGloss = String(gloss || '').trim().replace(/[.,;:\s]+$/u, '');
    const cleanContext = String(context || '').trim().replace(/^[,;:\s]+/u, '');
    if (!cleanGloss) return cleanContext;
    if (!cleanContext) return cleanGloss;
    if (cleanGloss.toLocaleLowerCase('en').includes(cleanContext.toLocaleLowerCase('en'))) {
        return cleanGloss;
    }
    return `${cleanGloss}, ${cleanContext}`;
}

// Keep spoken English aligned with the full visible sense, including the
// smaller disambiguating context. The underlying translation is
// infinitive-shaped ("to deserve"), while a conjugated surface such as
// "merezco" is displayed as "I deserve".
function getSpokenEnglish(card, meaning) {
    const translation = meaning && (meaning.meaning || meaning.translation);
    if (!translation) return '';
    const gloss = getProductionEnglishCue(card, meaning) || translation;
    return joinSpokenGlossAndContext(gloss, meaning.context);
}

function getAutoplaySpokenEnglish(card, meaning, cycleIndex = 0) {
    if (!meaning) return '';
    if (meaning.allMWEs?.length) {
        const item = meaning.allMWEs[cycleIndex] || meaning.allMWEs[0];
        if (!item) return '';
        let gloss = String(item.translation || '').replace(/\s*\(elided\)/giu, '').trim();
        let context = item.context || item.context_heuristic || '';
        if (!context && gloss) {
            const split = splitMWETranslation(gloss);
            gloss = split.primary || gloss;
            context = split.context || '';
        }
        return joinSpokenGlossAndContext(gloss, context);
    }
    if (meaning.allClitics?.length) {
        const item = meaning.allClitics[cycleIndex] || meaning.allClitics[0];
        const detail = describeCliticForm(item, card);
        return [detail.displayTranslation || item?.form || '', detail.spokenDetail]
            .filter(Boolean).join(', ');
    }
    if (meaning.pos === 'SENSE_CYCLE' && meaning.allSenses?.length) {
        const item = meaning.allSenses[cycleIndex] || meaning.allSenses[0];
        return joinSpokenGlossAndContext(item?.translation || meaning.meaning, item?.context);
    }
    return getSpokenEnglish(card, meaning);
}

function getCurrentSpokenEnglish(card) {
    const meaning = card?.meanings?.[currentMeaningIndex];
    if (!meaning) return '';
    if (!currentGroupSelection?.members?.length) return getSpokenEnglish(card, meaning);
    if (currentGroupSelection.axis === 'translation') {
        return getProductionEnglishCue(card, meaning) || meaning.meaning || '';
    }
    const glosses = currentGroupSelection.members
        .map(index => card.meanings[index])
        .filter(Boolean)
        .map(member => getProductionEnglishCue(card, member) || member.meaning || '')
        .filter((gloss, index, all) => gloss && all.indexOf(gloss) === index);
    return joinSpokenGlossAndContext(glosses.join(', '), currentGroupSelection.groupKey);
}

function formatMorphMood(mood) {
    const moodMap = {
        indicativo: '',
        subjuntivo: 'subjunctive',
        imperativo: 'imperative',
        gerundio: 'gerund',
        participio: 'past participle',
        participo: 'past participle',
        'participio-pasado': 'past participle',
        condicional: 'conditional',
        infinitivo: 'infinitive',
    };
    // The source layer uses Spanish grammar keys. Never leak an unmapped
    // source-language token into otherwise-English card metadata.
    return moodMap[mood] || '';
}

function formatMorphTense(tense) {
    const tenseMap = {
        presente: 'present',
        afirmativo: '',
        negativo: 'negative',
        futuro: 'future',
        'futuro-perfecto': 'future perfect',
        'pretérito-perfecto-simple': 'preterite',
        'pretérito-imperfecto': 'imperfect',
        'pretérito-imperfecto-1': 'imperfect',
        'pretérito-imperfecto-2': 'imperfect',
        'pretérito-perfecto': 'present perfect',
        'pretérito-pluscuamperfecto-1': 'pluperfect',
        'pretérito-pluscuamperfecto-2': 'pluperfect',
        infinitivo: '',        // infinitive is implied by mood, omit
        gerundio: '',
        participo: '',
    };
    const mapped = tenseMap[tense];
    return mapped !== undefined ? mapped : '';
}

function formatMorphPerson(person) {
    const personMap = {
        '1s': 'Yo',
        '2s': 'Tú',
        '3s': 'Él(la)',
        '1p': 'Nosotros',
        '2p': 'Vosotros',
        '3p': 'Ellos',
    };
    return personMap[person] || '';
}

function formatMorphLabel(m) {
    const person = formatMorphPerson(m.person);
    const grammar = [
        formatMorphTense(m.tense),
        formatMorphMood(m.mood),
    ].filter(Boolean).join(' ');
    if (!person && !grammar) return null;
    return {
        key: `${person}|${grammar}`,
        personCode: m.person || '',
        person,
        grammar,
        tense: formatMorphTense(m.tense),
        mood: formatMorphMood(m.mood),
        moodCode: m.mood || '',
    };
}

function formatMorphPersonGroup(personCodes, fallbackLabels = []) {
    const people = [...new Set(personCodes
        .map(formatMorphPerson)
        .filter(Boolean))];
    return people.join('/') || fallbackLabels.filter(Boolean).join('/');
}

// One Spanish surface can legitimately represent several complete analyses.
// Compact person ambiguity within one analysis (sea = 1st/3rd singular), keep
// grammatical permutations coupled, and rank indicative ahead of imperative so
// the initially visible row is the ordinary reading when both are possible.
function compactMorphLabels(morphologyRows) {
    const unique = [...new Map(morphologyRows
        .map(formatMorphLabel)
        .filter(Boolean)
        .map(label => [label.key, label])).values()];
    const groups = new Map();
    for (const label of unique) {
        const number = label.personCode.endsWith('s')
            ? 'SING'
            : (label.personCode.endsWith('p') ? 'PLURAL' : '');
        const groupKey = `${number}|${label.tense}|${label.mood}`;
        if (!groups.has(groupKey)) {
            groups.set(groupKey, {
                grammar: label.grammar,
                number,
                tense: label.tense,
                mood: label.mood,
                moodCode: label.moodCode,
                labels: []
            });
        }
        groups.get(groupKey).labels.push(label);
    }
    return [...groups.values()].map(group => {
        const personCodes = group.labels.map(label => label.personCode).filter(Boolean);
        const person = formatMorphPersonGroup(
            personCodes,
            group.labels.map(label => label.person)
        );
        return {
            key: `${person}|${group.grammar}`,
            person,
            grammar: group.grammar,
            number: group.number,
            tense: group.tense,
            mood: group.mood,
            moodCode: group.moodCode
        };
    }).sort((a, b) => {
        const moodPriority = moodCode => ({
            indicativo: 0,
            '': 1,
            subjuntivo: 2,
            condicional: 3,
            infinitivo: 4,
            gerundio: 5,
            participio: 5,
            participo: 5,
            'participio-pasado': 5,
            imperativo: 6,
        })[moodCode] ?? 4;
        return moodPriority(a.moodCode) - moodPriority(b.moodCode);
    });
}

const CLITIC_ROLES = {
    me: 'me / myself',
    te: 'you / yourself',
    se: 'himself / herself / yourself / themselves',
    nos: 'us / ourselves',
    os: 'you / yourselves',
    lo: 'him / it / you',
    la: 'her / it / you',
    los: 'them / you',
    las: 'them / you',
    le: 'to him / her / you',
    les: 'to them / you',
};

const CLITIC_GRAMMAR = {
    me: '1st singular object / reflexive',
    te: '2nd singular object / reflexive',
    se: '3rd person reflexive / indirect object',
    nos: '1st plural object / reflexive',
    os: '2nd plural object / reflexive',
    lo: '3rd singular masculine direct object',
    la: '3rd singular feminine direct object',
    los: '3rd plural masculine direct object',
    las: '3rd plural feminine direct object',
    le: '3rd singular indirect object',
    les: '3rd plural indirect object',
};

const CLITIC_ROLE_PATTERNS = {
    me: /\b(?:me|myself)\b/iu,
    te: /\b(?:you|yourself)\b/iu,
    se: /\b(?:himself|herself|itself|yourself|themselves)\b/iu,
    nos: /\b(?:us|ourselves)\b/iu,
    os: /\b(?:you|yourselves)\b/iu,
    lo: /\b(?:him|it|you)\b/iu,
    la: /\b(?:her|it|you)\b/iu,
    los: /\b(?:them|you)\b/iu,
    las: /\b(?:them|you)\b/iu,
    le: /\b(?:him|her|you)\b/iu,
    les: /\b(?:them|you)\b/iu,
};

function splitAttachedClitics(form) {
    let stem = String(form || '').trim().toLocaleLowerCase('es');
    if (!stem) return { stem: '', clitics: [] };
    const clitics = [];
    const direct = ['los', 'las', 'lo', 'la'].find(value => stem.endsWith(value));
    if (direct) {
        clitics.unshift(direct);
        stem = stem.slice(0, -direct.length);
        const indirect = ['nos', 'les', 'me', 'te', 'se', 'os', 'le']
            .find(value => stem.endsWith(value));
        if (indirect) {
            clitics.unshift(indirect);
            stem = stem.slice(0, -indirect.length);
        }
    } else {
        const single = ['nos', 'les', 'los', 'las', 'me', 'te', 'se', 'os', 'lo', 'la', 'le']
            .find(value => stem.endsWith(value));
        if (single) {
            clitics.push(single);
            stem = stem.slice(0, -single.length);
        }
    }
    return { stem, clitics };
}

function describeCliticForm(item, card) {
    const form = item?.form || '';
    const { stem, clitics } = splitAttachedClitics(form);
    const lemma = String(card?.lemma || card?.citationForm || '')
        .toLocaleLowerCase('es').replace(/((?:ar|er|ir))se$/u, '$1');
    const foldedStem = foldSurfaceForm(stem);
    const foldedLemma = foldSurfaceForm(lemma);
    let formType = 'attached pronoun';
    if (foldedStem && foldedLemma && foldedStem === foldedLemma) {
        formType = 'infinitive';
    } else if (/(?:ando|iendo|yendo)$/u.test(foldedStem)) {
        formType = 'gerund';
    } else if (clitics.length) {
        // In modern Spanish, an attached pronoun on a finite verb is an
        // affirmative command. Infinitives and gerunds were handled above.
        formType = 'command';
    }
    const pronounText = clitics.map(value => `${value}, ${CLITIC_GRAMMAR[value] || 'attached pronoun'}, ${CLITIC_ROLES[value] || ''}`)
        .join(' + ');
    const pronounDetail = clitics.map(value => CLITIC_GRAMMAR[value]).filter(Boolean).join(' + ');
    const baseTranslation = String(item?.translation || '').trim();
    const missingRoles = clitics.filter(value => !CLITIC_ROLE_PATTERNS[value]?.test(baseTranslation))
        .map(value => CLITIC_ROLES[value]).filter(Boolean);
    const displayTranslation = [baseTranslation, ...missingRoles]
        .filter(Boolean).join(' · ');
    return {
        formType,
        pronounText,
        displayTranslation,
        visualDetail: [clitics.length ? `${formType} + ${clitics.join(' + ')}` : formType,
            pronounDetail]
            .filter(Boolean).join(' · '),
        spokenDetail: pronounText ? `${formType}; ${pronounText}` : formType,
    };
}

async function loadSpanishRanks() {
    if (_spanishRanks || _spanishRanksLoading) return;
    _spanishRanksLoading = true;
    try {
        const resp = await fetch('Data/Spanish/spanish_ranks.json');
        if (resp.ok) _spanishRanks = await resp.json();
    } catch (e) {
        // Non-fatal — falls back to static easiness
    }
    _spanishRanksLoading = false;
}

// Returns a promise that resolves when the data is loaded (or has already
// been loaded). Concurrent callers share the in-flight promise, so a fast
// conj-toggle click before the boot-time prefetch completes will wait for
// the same fetch instead of seeing an empty cache and rendering "no data".
// window._conjugationData is set on success so flashcards-conj.js (which
// has no module import of this file) can read the cache via globalThis.
async function loadConjugationData() {
    if (_conjugationData) return _conjugationData;
    if (_conjugationLoadPromise) return _conjugationLoadPromise;
    const langConfig = config.languages[selectedLanguage];
    if (!langConfig || !langConfig.conjugationsPath) return null;
    _conjugationLoadPromise = (async () => {
        try {
            const resp = await fetch(langConfig.conjugationsPath);
            if (resp.ok) {
                _conjugationData = await resp.json();
                window._conjugationData = _conjugationData;
                if (Array.isArray(flashcards) && flashcards.length) {
                    try { updateCard(); } catch (_) { /* first paint may precede card DOM */ }
                }
            }
        } catch (e) {
            // Non-fatal — conjugation panel just won't have inline data
        }
        _conjugationLoadPromise = null;
        return _conjugationData;
    })();
    return _conjugationLoadPromise;
}

async function loadConjugatedEnglishData() {
    if (_conjugatedEnglishData || _conjugatedEnglishLoading) return;
    const langConfig = config.languages[selectedLanguage];
    if (!langConfig || !langConfig.conjugatedEnglishPath) return;
    _conjugatedEnglishLoading = true;
    try {
        const resp = await fetch(langConfig.conjugatedEnglishPath);
        if (resp.ok) _conjugatedEnglishData = await resp.json();
    } catch (e) {
        // Non-fatal — falls back to infinitive display
    }
    _conjugatedEnglishLoading = false;
}

function resetLanguageOptionalData() {
    _conjugationData = null;
    _conjugationLoadPromise = null;
    _conjugatedEnglishData = null;
    _conjugatedEnglishLoading = false;
    window._conjugationData = null;
}

// Register/dialect tag stamped by the classify-or-propose prompt. Only the
// tags that tell a learner something about HOW a word is used are surfaced:
// `other` says nothing, and `proper_noun` is already expressed by the PROPN
// part of speech and the Extra routing, so both stay hidden.
const REGISTER_TAG_LABELS = {
    slang: 'slang',
    vulgar: 'vulgar',
    regional: 'regional',
    figurative: 'figurative',
    loanword: 'loanword',
    idiomatic: 'idiomatic'
};

function registerTagHTML(meaning) {
    const label = REGISTER_TAG_LABELS[meaning?.type];
    if (!label) return '';
    if (senseMetadataItems(meaning).some(item => item.family === 'register' && item.value.toLowerCase() === label)) return '';
    return ` <span class="meaning-register" data-register="${meaning.type}">${label}</span>`;
}

// Parenthetical ad-libs in lyric transcriptions — "(Eh-eh)", "(Wuh)", "(Yeah)",
// "(Prr)". They appear on 27% of Bad Bunny example lines and cost about 10 of a
// 49-character line, which is the difference between one line and two in the
// example area.
//
// The threshold is empirical, not a guess: at 2 words / 10 characters this
// removes 2,647 parentheticals across the deck with ZERO real-lyric casualties.
// Loosening to 3 words / 14 characters gains ~320 more but starts eating actual
// sung lines ("Que se mueve", "Toda la noche"), so it stays tight — a stray
// "(Ey, ey)" surviving costs a few pixels, a deleted lyric costs meaning.
const _ADLIB_PAREN_RE = /\s*\(([^()]*)\)/g;
const ADLIB_MAX_WORDS = 2;
const ADLIB_MAX_CHARS = 10;

function stripAdlibParentheticals(text) {
    if (!text || typeof text !== 'string' || text.indexOf('(') === -1) return text;
    const cleaned = text.replace(_ADLIB_PAREN_RE, (whole, inner) => {
        const trimmed = inner.trim();
        if (trimmed.length > ADLIB_MAX_CHARS) return whole;
        const words = trimmed.match(/[\wáéíóúüñ'’-]+/gi) || [];
        return words.length <= ADLIB_MAX_WORDS ? '' : whole;
    });
    // Tidy punctuation left stranded by a removal (", ," / trailing comma).
    return cleaned.replace(/\s+([,.;!?])/g, '$1').replace(/,\s*(?=[,.;!?])/g, '')
                  .replace(/[ \t]{2,}/g, ' ').replace(/[\s,;]+$/, '').trim();
}

// --- MWE translation split (JS mirror of pipeline/util_5c_spanishdict.split_mwe_translation) ---
// Applied at render time so existing decks (whose mwe_memberships predate the
// pipeline-side split) still get the two-line layout. New builds set m.context
// directly and skip this parser.
const _MWE_UOTFI_RE = /^\s*Used other than figuratively or idiomatically:\s*see[^.]*\.\s*/i;
const _MWE_USED_PREFIX_RE = /^\s*(Used [^:]+?):\s*/i;

function splitMWETranslation(raw) {
    if (typeof raw !== 'string' || !raw.trim()) return { primary: raw || '', context: '' };
    let s = raw.replace(_MWE_UOTFI_RE, '').trim();
    if (!s) return { primary: '', context: '' };
    let context = '';
    const pm = s.match(_MWE_USED_PREFIX_RE);
    if (pm) {
        context = pm[1].trim();
        s = s.slice(pm[0].length).trim();
        if (!s) return { primary: context, context: '' };
    }
    // Trailing balanced ``(...)`` split.
    if (s.endsWith(')')) {
        let depth = 0, start = -1;
        for (let i = s.length - 1; i >= 0; i--) {
            const c = s[i];
            if (c === ')') depth++;
            else if (c === '(') {
                depth--;
                if (depth === 0) { start = i; break; }
            }
        }
        if (start > 0) {
            const before = s.slice(0, start).trimEnd();
            const inside = s.slice(start + 1, -1).trim();
            if (before && inside) {
                context = context ? context + '; ' + inside : inside;
                s = before;
            }
        }
    }
    return { primary: s, context };
}

// --- Fit-text-to-single-line helper ---
// Shrinks ``el``'s inline font-size until the text fits on one line inside
// its constrained width. Starts from the element's computed (CSS-driven)
// font-size and steps down in 2px increments until the content no longer
// overflows with ``white-space: nowrap`` applied, or ``minPx`` is reached.
// CSS-level ``overflow-wrap: anywhere`` remains the last-resort fallback
// if the text still doesn't fit at ``minPx``.
//
// Called after setting ``textContent`` on front-of-card word + lemma so
// rare long words like "Sandungueo" shrink to fit instead of wrapping.
// Idempotent: clears any prior inline font-size on each call.
function shrinkToFit(el, minPx) {
    if (!el || !el.textContent) return;
    // Reset to CSS-driven baseline so repeated calls start from the same
    // maxPx. Without this, the previous card's shrunk size would become
    // the next card's starting point.
    el.style.fontSize = '';
    const maxPx = parseFloat(getComputedStyle(el).fontSize);
    if (!maxPx || maxPx <= minPx) return;
    const prevWS = el.style.whiteSpace;
    // Disable wrapping to expose intrinsic content width via scrollWidth.
    el.style.whiteSpace = 'nowrap';
    // A zero client width means the element is not laid out yet — an ancestor
    // is still hidden, or this ran before the card reached the screen. There
    // is nothing to measure against, and the loop below compares scrollWidth
    // against 0, which is always greater, so it would step all the way to the
    // floor and leave a two-letter word at 18px. That is the "randomly tiny
    // headword": it tracked when the measurement happened, not how long the
    // word was. Keep the CSS baseline instead.
    if (!el.clientWidth) {
        el.style.whiteSpace = prevWS;
        return;
    }
    let size = maxPx;
    // scrollWidth is the content's ideal width; clientWidth is the
    // constrained element width (capped by max-width: 100% of parent).
    // When the former exceeds the latter, the text would need to wrap.
    while (size > minPx && el.scrollWidth > el.clientWidth) {
        size -= 2;
        el.style.fontSize = size + 'px';
    }
    el.style.whiteSpace = prevWS;
}

/**
 * Keep the lemma visually subordinate to the word it belongs to.
 *
 * The two are shrunk independently — the word from a 70px ceiling, the lemma
 * from 35px — and nothing related the results. A long surface form such as
 * "atiendes" steps a long way down from 70 to fit the card, while its lemma
 * "atender" already fits at 35 and never moves, so the inflected word the card
 * is actually asking about ended up smaller than the dictionary form beneath
 * it. Which word shrank had no visible logic from the outside: it depended
 * purely on how far each had to travel from its own starting size.
 *
 * Cap the lemma against the word's *final* size instead, then let it shrink
 * further if it still overflows.
 */
const LEMMA_MAX_SHARE_OF_WORD = 0.62;

function fitLemmaUnderWord(wordEl, lemmaEl, minPx) {
    if (!wordEl || !lemmaEl || !lemmaEl.textContent) return;
    const wordSize = parseFloat(getComputedStyle(wordEl).fontSize);
    if (!wordSize) return;
    const baseline = parseFloat(getComputedStyle(lemmaEl).fontSize);
    const capped = Math.max(minPx, Math.min(baseline || wordSize, wordSize * LEMMA_MAX_SHARE_OF_WORD));
    lemmaEl.style.fontSize = capped + 'px';
    // Re-measure from the capped size: a long lemma may still need to step
    // down, and shrinkToFit reads its starting point from the computed style.
    shrinkToFit(lemmaEl, minPx);
}

// The back headword shares its line with the POS pill(s) in the top right.
// Character count alone cannot decide whether they collide — a wide pill
// ("preposition", or a multi-POS tab group) crowds even a short word, while
// "noun" leaves plenty — so the headword's larger baseline is capped against
// the width the legend actually occupies rather than guessed from length.
// Without this the legend wrapped to a second line and the header grew.
// Two passes: the first shrink frees width, which may let a legend that had
// wrapped internally lay itself out narrower, so the budget is re-measured.
function fitBackHeadword(root) {
    const el = root?.querySelector('.back-headword');
    const row = el?.closest('.back-headword-row');
    if (!el || !row) return;
    const legend = row.querySelector('.back-pos-legend');
    const surface = el.querySelector('.back-surface-name');
    const lemmaChip = el.querySelector('.back-lemma-chip');
    const minPx = surface ? 20 : 24;
    const gapPx = 12;
    const prevWS = el.style.whiteSpace;
    el.style.whiteSpace = 'nowrap';
    // A paired surface and lemma are separate flex children. The flex item's
    // scrollWidth can report its shrunk width even while the surface wraps;
    // measure both children's unwrapped content to keep the pair on one line.
    if (surface) surface.style.whiteSpace = 'nowrap';
    for (let pass = 0; pass < 2; pass++) {
        const legendWidth = legend ? legend.offsetWidth + gapPx : 0;
        const budget = row.clientWidth - legendWidth;
        // Zero/negative means the card isn't laid out yet (hidden container);
        // leave the baseline alone rather than shrinking against a bad read.
        if (budget <= 0) break;
        let size = parseFloat(el.style.fontSize)
            || parseFloat(getComputedStyle(el).fontSize);
        if (!size) break;
        const contentWidth = () => surface && lemmaChip
            ? surface.scrollWidth + lemmaChip.scrollWidth + gapPx
            : el.scrollWidth;
        while (size > minPx && contentWidth() > budget) {
            size -= 2;
            el.style.fontSize = size + 'px';
        }
        if (contentWidth() <= budget) break;
    }
    el.style.whiteSpace = prevWS;
}

// POS headers are a map of the available meanings, not another metadata row.
// Remove balanced parenthetical asides from this one-line summary while the
// full gloss/context remains untouched in the expanded subsense below.
function senseSummaryText(value) {
    let text = String(value || '').trim();
    let previous = '';
    while (text !== previous) {
        previous = text;
        text = text.replace(/\s*\([^()]*\)/gu, ' ');
    }
    return text
        .replace(/\s+([,;:.])/gu, '$1')
        .replace(/^[,;:.\s]+|[,;:.\s]+$/gu, '')
        .replace(/\s{2,}/gu, ' ')
        .trim();
}

// A collapsed (POS, headword) row is a useful sense overview, not merely an
// expand control. Show every short sense that genuinely fits in the available
// width and collapse only the measured overflow behind +N. This deliberately
// uses rendered width rather than a fixed item/character limit, so compact
// glosses such as "to go · to leave" are not reduced to "to go +1".
function fitPosSectionSummaries(root) {
    root?.querySelectorAll('.pos-section-summary').forEach(summary => {
        const senses = Array.from(summary.querySelectorAll('.pos-summary-sense'));
        const more = summary.querySelector('.pos-pill-more');
        if (!more || senses.length < 2 || summary.clientWidth <= 0) return;

        senses.forEach(sense => { sense.hidden = true; });
        more.hidden = false;
        summary.classList.add('is-measuring');

        let shownCount = 0;
        for (let index = 0; index < senses.length; index++) {
            senses[index].hidden = false;
            const remaining = senses.length - index - 1;
            more.hidden = remaining === 0;
            more.textContent = `+${remaining}`;
            if (summary.scrollWidth > summary.clientWidth + 1) {
                senses[index].hidden = true;
                more.hidden = false;
                more.textContent = `+${senses.length - shownCount}`;
                break;
            }
            shownCount++;
        }
        summary.classList.remove('is-measuring');
    });
}

// A short shared gloss must not split a word merely to preserve two columns.
// Measure the rendered cell; longer labels already request a stacked layout.
function fitSenseRowLayouts(root) {
    root?.querySelectorAll('.group-card-body').forEach(body => {
        body.classList.remove('is-stacked');
        const shared = body.querySelector('.group-card-shared');
        if (shared && shared.clientWidth > 0 && shared.scrollWidth > shared.clientWidth + 1) {
            body.classList.add('is-stacked');
        }
    });
}

let posSummaryResizeFrame = 0;
window.addEventListener('resize', () => {
    cancelAnimationFrame(posSummaryResizeFrame);
    posSummaryResizeFrame = requestAnimationFrame(() => {
        fitSenseRowLayouts(document.getElementById('backContent'));
        fitPosSectionSummaries(document.getElementById('backContent'));
        refitMeaningScroll();
    });
});

// Measure the vertical room that belongs to the meanings scroller after every
// other in-flow child has taken its rendered space. Both auto-expansion and the
// final overflow cap use this same live budget, so "open when it fits" cannot
// disagree with the point where the card becomes scrollable.
function availableHeightForMeaningScroll(backEl, scroll) {
    if (!backEl || !scroll) return 0;
    let overhead = 0;
    let otherFlowChildren = 0;
    for (const child of backEl.children) {
        if (child === scroll || child.classList.contains('conjugation-panel')) continue;
        const cs = getComputedStyle(child);
        if (cs.display === 'none' || cs.position === 'absolute' || cs.position === 'fixed') continue;
        otherFlowChildren++;
        overhead += child.offsetHeight
            // The links' auto margin is spare space, not occupied content.
            + (child.classList.contains('links-section') ? 0 : (parseFloat(cs.marginTop) || 0))
            + (parseFloat(cs.marginBottom) || 0);
    }
    // With the scroller included, N other children create N gaps in the flex
    // column. (The old cap counted N - 1 and could overestimate spare room.)
    const backStyle = getComputedStyle(backEl);
    overhead += otherFlowChildren
        * (parseFloat(backStyle.rowGap || backStyle.gap) || 0);
    return backEl.clientHeight - overhead
        - (parseFloat(backStyle.paddingTop) || 0) - (parseFloat(backStyle.paddingBottom) || 0);
}

// Disclosures change row height without rendering the card again. Release the
// previous cap before measuring so spare space can move the example down.
function refitMeaningScroll(backEl = document.getElementById('backContent')) {
    const scroll = backEl?.querySelector('.meanings-scroll');
    if (!scroll) return;
    scroll.style.maxHeight = '';
    const available = availableHeightForMeaningScroll(backEl, scroll);
    if (scroll.scrollHeight > available) scroll.style.maxHeight = Math.max(100, available) + 'px';
}
document.addEventListener('sense-details-change', () => refitMeaningScroll());
document.addEventListener('toggle', event => {
    if (event.target.matches?.('.sense-definition-detail')) refitMeaningScroll();
}, true);

// Cache of known words built from progressData — rebuilt when progress changes
let _knownWordsCache = null;
let _knownWordsCacheSize = -1;

function getKnownWords() {
    const pdSize = Object.keys(progressData).length;
    if (_knownWordsCache && _knownWordsCacheSize === pdSize) return _knownWordsCache;
    _knownWordsCache = new Set();
    for (const p of Object.values(progressData)) {
        if (p.correct > 0 && p.word) _knownWordsCache.add(p.word.toLowerCase());
    }
    _knownWordsCacheSize = pdSize;
    return _knownWordsCache;
}

function computePersonalEasiness(spanishText) {
    if (!_spanishRanks || !spanishText) return 999999;
    // Strip ad-libs/brackets
    const cleaned = spanishText.replace(/\[[^\]]*\]|\([^\)]*\)/g, '').trim();
    if (!cleaned) return 999999;
    const tokens = cleaned.toLowerCase().replace(/[^\w\s']/g, ' ').split(/\s+/).filter(Boolean);
    if (!tokens.length) return 999999;

    // Get level estimate high-water mark
    const lang = selectedLanguage || 'spanish';
    const estimate = (levelEstimates && levelEstimates[lang]) || 0;
    const knownWords = getKnownWords();

    const unknownRanks = [];
    for (const t of tokens) {
        const rank = _spanishRanks[t];
        if (rank === undefined) continue;  // skip unrecognized tokens
        // Known if: rank <= level estimate, or word has been marked correct
        if (rank <= estimate || knownWords.has(t)) continue;
        unknownRanks.push(rank);
    }
    if (!unknownRanks.length) return 999999;  // all known — sort last
    unknownRanks.sort((a, b) => a - b);
    return unknownRanks[Math.floor(unknownRanks.length / 2)];  // median
}

// Compute % of example lines where every vocabulary word is known.
// Returns { understood, total, pct } or null if data not available.
function computeLinesUnderstood(allowedEntryIds = null) {
    if (!_spanishRanks || !progressData) return null;
    const examplesData = window._cachedExamplesData;
    if (!examplesData) return null;

    const lang = selectedLanguage || 'spanish';
    const estimate = (levelEstimates && levelEstimates[lang]) || 0;
    const knownWords = getKnownWords();

    let understood = 0;
    let total = 0;

    for (const [entryId, entry] of Object.entries(examplesData)) {
        if (allowedEntryIds && !allowedEntryIds.has(entryId)) continue;
        const lineBuckets = [...(entry.m || [])];
        if (Array.isArray(entry.r) && entry.r.length > 0) lineBuckets.push(entry.r);
        if (lineBuckets.length === 0) continue;
        for (const meaningExamples of lineBuckets) {
            if (!meaningExamples) continue;
            for (const ex of meaningExamples) {
                // Normal-mode example files use `target`, artist-mode files
                // use `spanish` — same field, different key. Read whichever
                // is present so this metric works for both modes.
                const targetText = ex.target || ex.spanish;
                if (!targetText) continue;
                total++;
                const cleaned = targetText.replace(/\[[^\]]*\]|\([^\)]*\)/g, '').trim();
                if (!cleaned) { understood++; continue; }
                const tokens = cleaned.toLowerCase().replace(/[^\w\s']/g, ' ').split(/\s+/).filter(Boolean);
                if (!tokens.length) { understood++; continue; }
                let allKnown = true;
                for (const t of tokens) {
                    const rank = _spanishRanks[t];
                    if (rank === undefined) continue;  // not in vocab — skip
                    if (rank <= estimate || knownWords.has(t)) continue;
                    allKnown = false;
                    break;
                }
                if (allKnown) understood++;
            }
        }
    }

    return { understood, total, pct: total > 0 ? (understood / total * 100) : 0 };
}

// --- Example relevance sorting ---
let _cachedDeckWords = null;
let _cachedDeckRef = null;
let _cachedDeckLength = -1;
let _cachedDeckFirstId = null;
let _cachedDeckLastId = null;

function getDeckWords() {
    if (!flashcards || flashcards.length === 0) return new Set();
    const firstId = flashcards[0]?.fullId;
    const lastId = flashcards[flashcards.length - 1]?.fullId;
    if (_cachedDeckWords && _cachedDeckRef === flashcards && _cachedDeckLength === flashcards.length
        && _cachedDeckFirstId === firstId && _cachedDeckLastId === lastId) {
        return _cachedDeckWords;
    }
    _cachedDeckWords = new Set();
    for (let i = 0; i < flashcards.length; i++) {
        const card = flashcards[i];
        if (card.targetWord) _cachedDeckWords.add(String(card.targetWord).toLowerCase());
        if (card.lemma) _cachedDeckWords.add(String(card.lemma).toLowerCase());
        if (card.displaySurface) _cachedDeckWords.add(String(card.displaySurface).toLowerCase());
        if (card.citationForm) _cachedDeckWords.add(String(card.citationForm).toLowerCase());
        if (card.productionAnswer) _cachedDeckWords.add(String(card.productionAnswer).toLowerCase());
    }
    _cachedDeckRef = flashcards;
    _cachedDeckLength = flashcards.length;
    _cachedDeckFirstId = firstId;
    _cachedDeckLastId = lastId;
    return _cachedDeckWords;
}

let _cachedWrongWordsEpoch = -1;
let _cachedWrongWords = null;
let _cachedWrongWordsTime = 0;

function getRecentWrongWords() {
    const epoch = window.__progressEpoch || 0;
    const now = Date.now();
    if (_cachedWrongWords && _cachedWrongWordsEpoch === epoch && (now - _cachedWrongWordsTime) < 60000) {
        return _cachedWrongWords;
    }
    _cachedWrongWords = collectRecentWrongWords(progressData, now);
    _cachedWrongWordsEpoch = epoch;
    _cachedWrongWordsTime = now;
    return _cachedWrongWords;
}

// Count "content" tokens after stripping ad-libs/brackets/parentheticals —
// used to prefer a first example line in a readable length window rather than
// whichever line is simply the longest.
function contentTokenCount(spanishText) {
    if (!spanishText) return 0;
    const cleaned = spanishText.replace(/\[[^\]]*\]|\([^\)]*\)/g, ' ');
    const tokens = cleaned.toLowerCase().replace(/[^\w\s']/g, ' ').split(/\s+/).filter(Boolean);
    return tokens.length;
}

function normalizeArtistCredit(value) {
    return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, ' ')
        .trim();
}

function exampleSungByActiveArtist(example) {
    if (!activeArtist || !Array.isArray(example.vocalists)) return false;
    const activeName = normalizeArtistCredit(activeArtist.name);
    return !!activeName && example.vocalists.some(credit => {
        const singer = normalizeArtistCredit(credit);
        return singer === activeName || singer.includes(activeName);
    });
}

function getSpotifyTrackIdForExample(example) {
    if (!example || !example.song_name) return null;
    // Playlist builds carry the exact source Spotify track ID. This avoids
    // resolving a mixed playlist against its deck name (and avoids a race
    // with the legacy global mapping fetch).
    if (example.spotify_track_id) return example.spotify_track_id;
    if (!window._spotifyTracks) return null;
    let artistName = null;
    if (example.artist) {
        artistName = window._allArtistsConfig?.[example.artist]?.name || null;
    }
    if (!artistName) artistName = activeArtist?.name || null;
    return artistName ? (window._spotifyTracks[artistName] || {})[example.song_name] || null : null;
}

function isExampleSnippetEligible(example) {
    const start = Number(example?.timestamp_ms);
    const end = Number(example?.end_timestamp_ms);
    const duration = end - start;
    return !!getSpotifyTrackIdForExample(example)
        && Number.isFinite(start)
        && Number.isFinite(end)
        && duration >= 350
        && duration <= 30000;
}

let _exampleAutoplayActive = false;
let _exampleAutoplayRunId = 0;
let _exampleAutoplayQueue = [];
let _exampleAutoplayQueuePos = 0;
let _explicitMeaningSelectionKey = null;

function meaningSelectionKey(card, meaningIndex) {
    return `${card?.fullId || card?.id || card?.targetWord || ''}:${meaningIndex}`;
}

function selectInitialMeaningGroup(card, grouping) {
    if (_exampleAutoplayActive || currentGroupSelection || !card?.meanings?.[currentMeaningIndex]) return;
    if (_explicitMeaningSelectionKey === meaningSelectionKey(card, currentMeaningIndex)) return;
    const { axisOf, groupKeyOf, groupMembers } = grouping || {};
    const axis = axisOf?.get(currentMeaningIndex);
    if (axis !== 'translation' && axis !== 'context') return;
    const groupKey = groupKeyOf.get(currentMeaningIndex);
    const meaning = card.meanings[currentMeaningIndex];
    const compKey = `${meaning.pos}\u0000${meaning.headword || ''}\u0000${axis}\u0000${groupKey}`;
    const members = groupMembers.get(compKey);
    if (!members || members.length < 2) return;
    currentGroupSelection = {
        axis,
        groupKey,
        pos: meaning.pos,
        headword: meaning.headword || '',
        members: [...members]
    };
}

function buildExampleAutoplayOrder(examples, requestedStartIndex = currentExampleIndex) {
    if (!Array.isArray(examples) || examples.length === 0) return [];
    const startIndex = ((requestedStartIndex % examples.length) + examples.length) % examples.length;
    const byTrack = new Map();

    // Rotate from the visible example, then group by track in first-seen
    // order. Each song is visited once instead of A → B → A; lines from
    // the same song can use the SDK's quick seek/resume path.
    for (let offset = 0; offset < examples.length; offset++) {
        const index = (startIndex + offset) % examples.length;
        const example = examples[index];
        if (!isExampleSnippetEligible(example)) continue;
        const trackId = getSpotifyTrackIdForExample(example);
        if (!trackId) continue;
        if (!byTrack.has(trackId)) byTrack.set(trackId, []);
        byTrack.get(trackId).push(index);
    }
    return Array.from(byTrack.values()).flat();
}

function getAutoplayExamplesForItem(meaning, cycleIndex = 0) {
    if (!meaning) return [];
    let examples;
    if (meaning.allMWEs?.length) {
        const item = meaning.allMWEs[cycleIndex] || meaning.allMWEs[0];
        examples = dedupeExamples(item?.examples || []);
        if (item?.expression) {
            examples = examples.filter(example => _matchedMweForm(
                item,
                example.target || example.spanish || '',
                example.matched_surface || example.matched_variant
            ));
        }
    } else if (meaning.allClitics?.length) {
        const item = meaning.allClitics[cycleIndex] || meaning.allClitics[0];
        examples = dedupeExamples(item?.examples || []);
        if (item?.form) {
            const escaped = item.form.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            try {
                const re = _cachedRegex(`(?<![\\p{L}])${escaped}(?![\\p{L}])`, 'iu');
                examples = examples.filter(example => re.test(example.target || example.spanish || ''));
            } catch (_) {
                // Older browsers without Unicode property escapes retain the
                // unfiltered list, matching the ordinary renderer fallback.
            }
        }
    } else if (meaning.pos === 'SENSE_CYCLE' && meaning.allSenses?.length) {
        const item = meaning.allSenses[cycleIndex] || meaning.allSenses[0];
        // Current decks generally pool unassigned evidence on the cycle row,
        // rather than assigning it to each remainder gloss. Play that pooled
        // evidence once, while still announcing every gloss.
        const itemExamples = Array.isArray(item?.examples) && item.examples.length
            ? item.examples
            : (cycleIndex === 0 ? meaning.allExamples : []);
        examples = dedupeExamples(itemExamples || []);
    } else {
        examples = dedupeExamples(meaning.allExamples || []);
    }
    return examples.length > 1 ? sortExamplesByRelevance(examples) : examples;
}

function buildCardAutoplayItems(card) {
    if (!card?.meanings?.length) return [];
    const items = [];
    card.meanings.forEach((meaning, meaningIndex) => {
        if (!meaning || meaning.exampleOnly) return;
        const cycleCount = meaning.allMWEs?.length
            || meaning.allClitics?.length
            || (meaning.pos === 'SENSE_CYCLE' && meaning.allSenses?.length)
            || 1;
        for (let cycleIndex = 0; cycleIndex < cycleCount; cycleIndex++) {
            items.push({
                meaningIndex,
                cycleIndex,
                spokenText: getAutoplaySpokenEnglish(card, meaning, cycleIndex),
                examples: getAutoplayExamplesForItem(meaning, cycleIndex)
            });
        }
    });
    return items;
}

function cardHasPlayableAutoplay(card) {
    return buildCardAutoplayItems(card).some(item =>
        item.examples.some(isExampleSnippetEligible));
}

function buildCardAutoplayQueue(card) {
    const items = buildCardAutoplayItems(card);
    if (items.length === 0) return [];
    const requestedCycleIndex = currentGroupSelection ? 0 : currentMWEIndex;
    let startItem = items.findIndex(item =>
        item.meaningIndex === currentMeaningIndex && item.cycleIndex === requestedCycleIndex);
    if (startItem < 0) startItem = 0;
    const rotated = [...items.slice(startItem), ...items.slice(0, startItem)];
    const queue = [];
    rotated.forEach((item, itemOffset) => {
        if (item.spokenText) {
            queue.push({
                type: 'sense',
                meaningIndex: item.meaningIndex,
                cycleIndex: item.cycleIndex,
                spokenText: item.spokenText
            });
        }
        const exampleStart = itemOffset === 0 ? currentExampleIndex : 0;
        for (const exampleIndex of buildExampleAutoplayOrder(item.examples, exampleStart)) {
            queue.push({
                type: 'example',
                meaningIndex: item.meaningIndex,
                cycleIndex: item.cycleIndex,
                exampleIndex
            });
        }
    });
    return queue;
}

function stopExampleAutoplay(pause = true) {
    const wasActive = _exampleAutoplayActive;
    _exampleAutoplayActive = false;
    _exampleAutoplayQueue = [];
    _exampleAutoplayQueuePos = 0;
    _exampleAutoplayRunId++;
    if (wasActive) {
        window.cancelSpotifySnippet?.(pause);
        window.speechSynthesis?.cancel();
    }
    const button = document.getElementById('exampleAutoplayBtn');
    if (button) {
        button.classList.remove('is-active');
        button.setAttribute('aria-pressed', 'false');
        button.title = 'Play lyric examples';
        const icon = button.querySelector('.example-autoplay-icon');
        if (icon) icon.textContent = '▶';
    }
}

function advanceExampleAutoplay(runId) {
    if (!_exampleAutoplayActive || runId !== _exampleAutoplayRunId) return;
    _exampleAutoplayQueuePos++;
    if (_exampleAutoplayQueuePos >= _exampleAutoplayQueue.length) {
        stopExampleAutoplay(false);
        return;
    }
    playExampleAutoplayStep(runId);
}

function setExampleAutoplayLoading(isLoading) {
    const button = document.getElementById('exampleAutoplayBtn');
    if (!button || !_exampleAutoplayActive) return;
    button.classList.toggle('is-loading', isLoading);
    button.title = isLoading ? 'Loading lyric…' : 'Stop lyric autoplay';
    const icon = button.querySelector('.example-autoplay-icon');
    if (icon) icon.textContent = isLoading ? '…' : '■';
}

async function playExampleAutoplayStep(runId) {
    if (!_exampleAutoplayActive || runId !== _exampleAutoplayRunId) return;
    const step = _exampleAutoplayQueue[_exampleAutoplayQueuePos];
    const card = flashcards[currentIndex];
    if (!step || !card?.meanings?.[step.meaningIndex]) {
        advanceExampleAutoplay(runId);
        return;
    }

    currentGroupSelection = null;
    currentMeaningIndex = step.meaningIndex;
    currentMWEIndex = step.cycleIndex;
    if (step.type === 'example') currentExampleIndex = step.exampleIndex;
    else currentExampleIndex = 0;
    updateCard();

    if (step.type === 'sense') {
        setExampleAutoplayLoading(true);
        speakWord(step.spokenText, true, () => {
            if (_exampleAutoplayActive && runId === _exampleAutoplayRunId) {
                setExampleAutoplayLoading(false);
                setTimeout(() => advanceExampleAutoplay(runId), 0);
            }
        });
        return;
    }

    const example = window._currentDisplayedExample;
    const trackId = getSpotifyTrackIdForExample(example);
    const startMs = Number(example?.timestamp_ms);
    const endMs = Number(example?.end_timestamp_ms);
    if (!isExampleSnippetEligible(example) || !trackId
            || !Number.isFinite(startMs) || !Number.isFinite(endMs)) {
        advanceExampleAutoplay(runId);
        return;
    }
    setExampleAutoplayLoading(true);
    const started = await window.spotifyPlaySnippet?.(trackId, startMs, endMs, () => {
        advanceExampleAutoplay(runId);
    });
    if (_exampleAutoplayActive && runId === _exampleAutoplayRunId) {
        setExampleAutoplayLoading(false);
    }
    if (!started && _exampleAutoplayActive && runId === _exampleAutoplayRunId) {
        stopExampleAutoplay(true);
    }
}

// Long-press popover on the card headword. Same contract as the Spotify
// button's autoplay popover: the hold reveals a small rounded control that
// says what it does, its button performs the switch, and a tap anywhere else
// dismisses it without changing the direction.
let _directionPopover = null;
let _directionPopoverArm = null;

function closeDirectionPopover() {
    if (!_directionPopover) return;
    _directionPopover.remove();
    _directionPopover = null;
    if (_directionPopoverArm) {
        document.removeEventListener('click', _directionPopoverArm, true);
        _directionPopoverArm = null;
    }
    document.removeEventListener('click', dismissDirectionPopover, true);
    window.removeEventListener('scroll', closeDirectionPopover, true);
    window.removeEventListener('resize', closeDirectionPopover);
}

function dismissDirectionPopover(event) {
    if (_directionPopover && _directionPopover.contains(event.target)) return;
    closeDirectionPopover();
}

function openDirectionPopover(anchor) {
    closeDirectionPopover();
    const targetLanguage = (config?.languages?.[selectedLanguage]?.name || selectedLanguage || 'the other language')
        .replace(/\s*\(.*\)$/, '');
    // Label the direction this will switch TO, matching the study menu's entry.
    const switchLabel = isFlipped ? `${targetLanguage} → English` : `English → ${targetLanguage}`;
    const popover = document.createElement('div');
    popover.className = 'direction-popover';
    popover.setAttribute('role', 'dialog');
    popover.setAttribute('aria-label', 'Card language direction');
    popover.innerHTML = `
        <span class="direction-popover-text">Choose which language every card asks you first.</span>
        <button type="button" class="direction-popover-btn">
            <span class="direction-popover-btn-icon" aria-hidden="true">⇄</span>
            <span class="direction-popover-btn-label">${escapeCardText(switchLabel)}</span>
        </button>`;
    document.body.appendChild(popover);
    _directionPopover = popover;

    // Fixed positioning keeps this out of the card's preserve-3d context.
    const rect = anchor.getBoundingClientRect();
    const width = popover.offsetWidth;
    const left = Math.min(
        Math.max(8, rect.left + rect.width / 2 - width / 2),
        Math.max(8, window.innerWidth - width - 8)
    );
    let top = rect.top - popover.offsetHeight - 10;
    if (top < 8) top = Math.min(rect.bottom + 10, window.innerHeight - popover.offsetHeight - 8);
    popover.style.left = `${Math.round(left)}px`;
    popover.style.top = `${Math.round(top)}px`;

    popover.querySelector('.direction-popover-btn').addEventListener('click', (event) => {
        event.stopPropagation();
        event.preventDefault();
        closeDirectionPopover();
        flipDirection();
    });

    // The pointerup that ends the long press still emits a click on the
    // headword. Forgive exactly that one click, so the popover cannot dismiss
    // itself the instant it appears; any other tap outside closes it at once.
    const armDismiss = (event) => {
        document.removeEventListener('click', armDismiss, true);
        _directionPopoverArm = null;
        document.addEventListener('click', dismissDirectionPopover, true);
        if (!anchor.contains(event.target) && !popover.contains(event.target)) closeDirectionPopover();
    };
    _directionPopoverArm = armDismiss;
    document.addEventListener('click', armDismiss, true);
    window.addEventListener('scroll', closeDirectionPopover, true);
    window.addEventListener('resize', closeDirectionPopover);
}

// Long-press on the Spotify button toggles card-wide lyric autoplay,
// folding the old standalone autoplay button into the Spotify button
// wherever both would otherwise appear side by side. A quick tap still
// plays the track in Spotify as before.
let _spotifyBtnLongPressTimer = null;
let _spotifyBtnLongPressFired = false;
const SPOTIFY_LONG_PRESS_MS = 500;

function spotifyBtnPressStart(event) {
    clearTimeout(_spotifyBtnLongPressTimer);
    _spotifyBtnLongPressFired = false;
    _spotifyBtnLongPressTimer = setTimeout(() => {
        _spotifyBtnLongPressFired = true;
        toggleExampleAutoplay(event);
    }, SPOTIFY_LONG_PRESS_MS);
}

function spotifyBtnPressEnd() {
    clearTimeout(_spotifyBtnLongPressTimer);
}

function spotifyBtnActivate(event, trackId, positionMs) {
    event.stopPropagation();
    if (event.cancelable) event.preventDefault();
    clearTimeout(_spotifyBtnLongPressTimer);
    if (_spotifyBtnLongPressFired) {
        _spotifyBtnLongPressFired = false;
        return;
    }
    stopExampleAutoplay(true);
    spotifyPlayTrack(trackId, positionMs);
}

function toggleExampleAutoplay(event) {
    event?.stopPropagation();
    if (_exampleAutoplayActive) {
        stopExampleAutoplay(true);
        return;
    }
    if (!window.spotifySnippetSupported?.()) return;
    const queue = buildCardAutoplayQueue(flashcards[currentIndex]);
    // Sense announcements alone are not autoplay. Refuse to enter an active
    // state unless at least one bounded Spotify lyric can actually play.
    if (!queue.some(step => step.type === 'example')) return;
    _exampleAutoplayActive = true;
    _exampleAutoplayQueue = queue;
    _exampleAutoplayQueuePos = 0;
    const runId = ++_exampleAutoplayRunId;
    playExampleAutoplayStep(runId);
}

// Example ordering. Four keys, compared in order, with no arithmetic score:
//   1. has an English translation  — an untranslated first line teaches nothing
//   2. is a single sentence        — 0.5% of corpus lines run to two
//   3. WSD confidence tier         — cheap-agree > leaf > glosskey > tuple
//   4. reinforces a recent mistake — local progress state, no pipeline data
// Ties keep deck order, so the result is stable.
//
// Confidence RANKS, it does not gate. Measured on the live v15 deck:
// `cheap_leaf_choices_agree` covers only ~25% of examples, so gating on it
// would hand 79.8% of cards a dictionary example as their first line — and a
// canonical example contains the card's own surface form only 44.6% of the
// time, so most cards would open on a sentence with nothing to underline.
// Ranking instead leaves just 1.1% of senses with no usable corpus line.
//
// Deliberately dropped: `easiness` (identical to selection_metrics.score, an
// opaque composite of frequency burden, length penalty and harder-token count
// that cannot be explained on screen — and `ex.easiness || 999999` inverted
// the 15.9% of examples scoring exactly 0, sorting the easiest lines last),
// the 6–14 token length window (the pipeline already caps length at 4–15 and
// charges length_penalty into the score) and deck-word overlap (at ~3.5k
// visible cards nearly every token is a deck word, making it sentence length
// in disguise).
const EXAMPLE_SENTENCE_BREAK_RE = /[.!?\u2026](?:["\u00bb\u201d')\]]+)?\s+[\u00bf\u00a1"\u00ab\u201c(\[]?\p{Lu}/u;

// An abbreviation's full stop is not a sentence break. Without this, lines
// like "Vino el Sr. Perez ayer." are demoted; they are 10.9% of everything
// the break pattern catches.
const EXAMPLE_ABBREVIATION_RE = /\b(?:sr|sra|srta|dr|dra|lic|ing|ud|uds|vd|vds|ee|uu|av|pág|núm|etc|mr|mrs|ms|st)\./gi;

function exampleIsSingleSentence(example) {
    const text = String(example?.target || example?.spanish || '').trim();
    if (!text) return false;
    return !EXAMPLE_SENTENCE_BREAK_RE.test(text.replace(EXAMPLE_ABBREVIATION_RE, 'x'));
}

// Lower is better. 0 is the strongest signal the release ships: two cheap
// methods independently picked the same leaf for THIS sentence. Below that,
// fall back to how deeply the assignment resolved.
const WSD_CONFIDENCE_TIER = { leaf: 1, glosskey: 2, tuple: 3 };
const WSD_CONFIDENCE_UNKNOWN = 4;

function exampleConfidenceTier(example) {
    const wsd = exampleWsdMeta(example);
    if (!wsd) return WSD_CONFIDENCE_UNKNOWN;
    if (wsd.gemini_recommendation?.reason === 'cheap_leaf_choices_agree') return 0;
    return WSD_CONFIDENCE_TIER[wsd.supported_level] || WSD_CONFIDENCE_UNKNOWN;
}

// 2 = a purpose-built personalised line; 1 = the sentence merely contains a
// word missed in the last week. Half of all senses still have two or more
// examples tied after the first three keys, so this decides the first line
// about as often as confidence does.
function exampleReinforcementScore(example, wrongWords) {
    if (!wrongWords?.size) return 0;
    if (exampleReinforcesRecentMistake(example, wrongWords)) return 2;
    const text = String(example?.target || example?.spanish || '');
    if (!text) return 0;
    const tokens = text.toLowerCase()
        .match(/[\p{L}\p{N}]+(?:['\u2019][\p{L}\p{N}]+)*/gu) || [];
    for (const token of tokens) {
        if (wrongWords.has(token)) return 1;
    }
    return 0;
}

function sortExamplesByRelevance(examples) {
    const wrongWords = getRecentWrongWords();
    const scored = filterPersonalisedExamples(examples, wrongWords).map((ex, index) => ({
        ex,
        index,
        hasEnglish: !!(ex.english && ex.english.trim()),
        singleSentence: exampleIsSingleSentence(ex),
        confidence: exampleConfidenceTier(ex),
        reinforcement: exampleReinforcementScore(ex, wrongWords),
        activeArtistSinger: exampleSungByActiveArtist(ex),
        spotifyAvailable: ex.spotify_available === true,
        standardVersion: ex.is_variant !== true,
    }));
    // Lyrics keep their own precedence: who sang it and whether it can play
    // outrank everything else, and lyric rows carry no WSD metadata at all,
    // so the confidence tier is constant there and falls through harmlessly.
    scored.sort((a, b) => activeArtist
        ? ((Number(b.activeArtistSinger) - Number(a.activeArtistSinger))
            || (Number(b.spotifyAvailable) - Number(a.spotifyAvailable))
            || (Number(b.standardVersion) - Number(a.standardVersion))
            || (Number(b.hasEnglish) - Number(a.hasEnglish))
            || (Number(b.singleSentence) - Number(a.singleSentence))
            || (b.reinforcement - a.reinforcement)
            || (a.index - b.index))
        : ((Number(b.hasEnglish) - Number(a.hasEnglish))
            || (Number(b.singleSentence) - Number(a.singleSentence))
            || (a.confidence - b.confidence)
            || (b.reinforcement - a.reinforcement)
            || (a.index - b.index))
    );
    return scored.map(s => s.ex);
}

function dedupeExamples(examples) {
    const seen = new Set();
    return filterPersonalisedExamples(examples, getRecentWrongWords()).filter(ex => {
        const key = (ex.target || ex.spanish || '').trim();
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

function compactCounterHTML(current, total, label = 'example') {
    if (total < 2) return '';
    const text = `${current + 1} of ${total}`;
    return `<span class="compact-example-counter" aria-label="${escapeCardText(`${label} ${current + 1} of ${total}`)}">${text}</span>`;
}

function exampleTicksHTML(current, total, label = 'example') {
    if (total < 2) return '';
    const dense = total > 16;
    const ticks = Array.from({ length: total }, (_, i) =>
        `<span class="example-tick${i === current ? ' is-current' : ''}"></span>`
    ).join('');
    // The class here is a first guess from the count alone. fitExampleCreditRow
    // tightens it further against the width the strip actually got, which the
    // count cannot know — half a phone card and half a desktop card are very
    // different amounts of room for the same thirty ticks.
    return `<div class="example-ticks${dense ? ' is-dense' : ''}" role="img" aria-label="${escapeCardText(`${label} ${current + 1} of ${total}`)}">${ticks}</div>`;
}

// The credit row is two halves that used to compete for one row: the source
// credit on the left, the tick strip and play controls on the right. A long
// film title or a thirty-example strip would push the other out entirely.
// Each half is now capped at 50% in CSS; this pass decides what happens to
// the ticks inside their half — squeeze through the density tiers first, and
// only once the tightest tier still overflows, clip, keeping the current tick
// in view so the position cue survives the clipping.
function fitExampleCreditRow(root) {
    if (!root) return;
    root.querySelectorAll('.example-ticks').forEach(strip => {
        strip.classList.remove('is-dense', 'is-tight');
        const fits = () => strip.scrollWidth <= strip.clientWidth + 1;
        if (fits()) return;
        strip.classList.add('is-dense');
        if (fits()) return;
        strip.classList.add('is-tight');
        if (fits()) return;
        // Still too many. Centre the current tick in the visible window.
        const current = strip.querySelector('.example-tick.is-current');
        if (!current) return;
        strip.scrollLeft = current.offsetLeft
            - (strip.clientWidth / 2)
            + (current.offsetWidth / 2);
    });
}

function initializeApp() {
    updateCard({ announceHeadword: true });
    updateStats();

    // Ensure modal is hidden on initialization
    document.getElementById('statsModal').classList.add('hidden');

    // Only set up event listeners once
    if (isAppInitialized) {
        return;
    }
    isAppInitialized = true;

    const showStudyMenu = (event) => {
        if (event) event.stopPropagation();
        if (!window.showChoiceSheet) return;
        const targetLanguage = (config.languages[selectedLanguage]?.name || selectedLanguage || 'Target language')
            .replace(/\s*\(.*\)$/, '');
        // Label the direction this action will switch TO, rather than the
        // ambiguous language that will merely appear "first".
        const switchOrderLabel = isFlipped
            ? `${targetLanguage} → English`
            : `English → ${targetLanguage}`;
        const icon = body => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
        const entries = [
            { label: 'Main menu', iconHTML: icon('<path d="M9 7H5v12h12v-4"></path><path d="m9 11-4-4 4-4"></path><path d="M5 7h9a5 5 0 0 1 5 5"></path>'), onSelect: () => goBackToSetup() },
            { label: switchOrderLabel, iconHTML: icon('<path d="M7 7h11"></path><path d="m15 4 3 3-3 3"></path><path d="M17 17H6"></path><path d="m9 14-3 3 3 3"></path>'), onSelect: () => flipDirection() },
            { label: speechEnabled ? 'Mute automatic speech' : 'Enable automatic speech', iconHTML: speechEnabled
                ? icon('<path d="M11 5 6 9H3v6h3l5 4z"></path><path d="M15 9a4 4 0 0 1 0 6"></path><path d="M18 6a8 8 0 0 1 0 12"></path>')
                : icon('<path d="M11 5 6 9H3v6h3l5 4z"></path><path d="m16 10 5 5"></path><path d="m21 10-5 5"></path>'), onSelect: () => toggleAutoSpeak() },
            { label: 'Set progress', iconHTML: icon('<path d="M4 19V9"></path><path d="M10 19V5"></path><path d="M16 19v-7"></path><path d="M22 19H2"></path>'), onSelect: () => showStatsModal() },
            { label: 'Study preferences', iconHTML: icon('<path d="M4 6h10"></path><path d="M18 6h2"></path><circle cx="16" cy="6" r="2"></circle><path d="M4 12h2"></path><path d="M10 12h10"></path><circle cx="8" cy="12" r="2"></circle><path d="M4 18h8"></path><path d="M16 18h4"></path><circle cx="14" cy="18" r="2"></circle>'), onSelect: () => showSettingsModalWithTab('study', { singleTab: true }) },
            { label: 'Find a word', iconHTML: icon('<circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>'), onSelect: () => window.openFindWord?.() },
            { label: 'Saved words', iconHTML: icon('<path d="M6 4h12v16l-6-3-6 3z"></path>'), onSelect: () => window.openSavedWords?.() }
        ];
        // Card data is a product-level audit surface: it stays available when
        // optional model stamps are absent and does not require an owner login.
        entries.push({ label: 'Card data', iconHTML: icon('<circle cx="12" cy="12" r="9"></circle><path d="M12 11v6"></path><path d="M12 7.5h.01"></path>'), onSelect: () => window.toggleProvenancePanel?.() });
        // Reporting remains an owner/reviewer diagnostic until it has a public
        // submission boundary.
        if (window.canUserFlag ? window.canUserFlag() : isJstOwner()) {
            entries.push({ label: 'Report a card issue', iconHTML: icon('<path d="M5 21V4"></path><path d="M5 5h11l-2 4 2 4H5"></path>'), onSelect: () => window.showFlagMenu?.() });
        }
        window.showChoiceSheet({
            id: 'studyChoiceSheet',
            ariaLabel: 'Study options',
            title: 'Study options',
            variant: 'list',
            entries
        });
    };

    // Event listeners
    // Flip button on front
    document.getElementById('flipBtn').addEventListener('click', function(e) {
        e.stopPropagation();
        flipCard();
    });

    // The back header remains an invisible flip target. Holding the headword
    // itself opens the direction popover. Reversal remains an explicit second
    // choice inside that popover; movement cancels the hold so horizontal card
    // swipes never reveal it accidentally.
    const flashcard = document.getElementById('flashcard');
    let backWordHoldTimer = null;
    let backWordHoldStart = null;
    let suppressCardFlipUntil = 0;
    const cancelBackWordHold = () => {
        if (backWordHoldTimer) clearTimeout(backWordHoldTimer);
        backWordHoldTimer = null;
        backWordHoldStart = null;
    };
    flashcard.addEventListener('pointerdown', event => {
        const headword = event.target.closest('.back-headword');
        if (!headword || (event.button !== undefined && event.button !== 0)) return;
        backWordHoldStart = { x: event.clientX, y: event.clientY };
        backWordHoldTimer = setTimeout(() => {
            backWordHoldTimer = null;
            backWordHoldStart = null;
            // The pointerup that ends the hold still produces a click on the
            // card; this window swallows it so the card never flips.
            suppressCardFlipUntil = Date.now() + 800;
            navigator.vibrate?.(20);
            openDirectionPopover(headword);
        }, 600);
    });
    flashcard.addEventListener('pointermove', event => {
        if (!backWordHoldStart) return;
        if (Math.hypot(event.clientX - backWordHoldStart.x, event.clientY - backWordHoldStart.y) > 10) {
            cancelBackWordHold();
        }
    });
    flashcard.addEventListener('pointerup', cancelBackWordHold);
    flashcard.addEventListener('pointercancel', cancelBackWordHold);
    flashcard.addEventListener('contextmenu', event => {
        if (event.target.closest('.back-headword')) event.preventDefault();
    });

    // Flip on back side
    flashcard.addEventListener('click', function(e) {
        if (Date.now() < suppressCardFlipUntil) {
            e.preventDefault();
            e.stopPropagation();
            return;
        }
        // Don't flip if clicking on buttons, links, or elements with onclick handlers
        if (e.target.closest('.nav-btn-inline') ||
            e.target.closest('.link-btn') ||
            e.target.closest('.ref-icon-btn') ||
            e.target.closest('.card-action-small') ||
            e.target.closest('.breakdown-btn') ||
            e.target.closest('.card-btn-pill') ||
            e.target.closest('.card-control-btn') ||
            e.target.closest('#flipBtn') ||
            e.target.closest('[onclick]')) {
            return;
        }

        // Allow flipping anywhere else on the card (including front/back content)
        flipCard();
    });

    // Arrow buttons on the card faces
    document.getElementById('prevBtnFront').addEventListener('click', function(e) {
        e.stopPropagation();
        previousCard();
    });
    document.getElementById('nextBtnFront').addEventListener('click', function(e) {
        e.stopPropagation();
        nextCard();
    });
    // Top card buttons + their mobile-popup counterparts. The popup variant
    // lives in the single fixed #cardActionsPopup outside the card; tapping
    // it runs the same handler as the desktop sidebar button.
    ['reverseLangBtn', 'reverseLangBtnPopup'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', function(e) {
            e.stopPropagation();
            flipDirection();
        });
    });
    // Lyric breakdown modal
    document.getElementById('closeLyricBreakdown').addEventListener('click', hideLyricBreakdown);
    document.getElementById('lyricBreakdownModal').addEventListener('click', function(e) {
        if (e.target === this) hideLyricBreakdown();
    });

    // Mobile button listeners
    document.getElementById('prevBtnFrontMobile').addEventListener('click', function(e) {
        e.stopPropagation();
        previousCard();
    });
    document.getElementById('nextBtnFrontMobile').addEventListener('click', function(e) {
        e.stopPropagation();
        nextCard();
    });
    // Mic / auto-speak toggle: the desktop centred speaker (#speakBtn) is
    // wired further down; the mobile copy lives in the fixed actions popup
    // as #speakBtnPopup. Iterator handles both ids gracefully.
    ['speakBtnMobile', 'speakBtnPopup'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleAutoSpeak();
        });
    });

    // Mobile actions popup — single fixed #cardActionsPopup outside the card,
    // so it's never inside the preserve-3d context. Both gear buttons toggle
    // the same popup; tapping any inner button performs the action AND
    // dismisses; tapping outside dismisses.
    const _popup = document.getElementById('cardActionsPopup');
    ['actionsGearFront', 'actionsGearBack'].forEach(gearId => {
        const gear = document.getElementById(gearId);
        if (gear) gear.addEventListener('click', showStudyMenu);
    });
    if (_popup) {
        _popup.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', function() {
                _popup.classList.remove('visible');
            });
        });
    }
    document.addEventListener('click', function(e) {
        if (!_popup || !_popup.classList.contains('visible')) return;
        const gearFront = document.getElementById('actionsGearFront');
        const gearBack  = document.getElementById('actionsGearBack');
        if (_popup.contains(e.target)) return;
        if (gearFront && gearFront.contains(e.target)) return;
        if (gearBack  && gearBack.contains(e.target))  return;
        _popup.classList.remove('visible');
    });

    document.getElementById('studyMenuBtn')?.addEventListener('click', showStudyMenu);

    // The connected number rail is also a real scrub control. Horizontal
    // movement advances relative to the card where the drag began; taps still
    // use the individual numbered buttons. Intermediate cards stay silent.
    const deckScrubber = document.getElementById('deckProgressSegments');
    if (deckScrubber) {
        let scrubPointerId = null;
        let scrubStartX = 0;
        let scrubStartIndex = 0;
        let scrubMoved = false;
        const finishScrub = event => {
            if (scrubPointerId === null || (event && event.pointerId !== scrubPointerId)) return;
            if (scrubMoved) _suppressDeckScrubberClickUntil = Date.now() + 350;
            const finishedPointerId = scrubPointerId;
            scrubPointerId = null;
            if (deckScrubber.hasPointerCapture?.(finishedPointerId)) {
                deckScrubber.releasePointerCapture(finishedPointerId);
            }
            scrubMoved = false;
            _deckScrubberActive = false;
            deckScrubber.classList.remove('is-scrubbing');
        };
        deckScrubber.addEventListener('pointerdown', event => {
            if (!window.matchMedia('(max-width: 767px)').matches) return;
            if (event.button !== undefined && event.button !== 0) return;
            scrubPointerId = event.pointerId;
            scrubStartX = event.clientX;
            scrubStartIndex = currentIndex;
            scrubMoved = false;
            _deckScrubberActive = true;
            deckScrubber.classList.add('is-scrubbing');
            deckScrubber.setPointerCapture?.(event.pointerId);
        });
        deckScrubber.addEventListener('pointermove', event => {
            if (event.pointerId !== scrubPointerId) return;
            const delta = event.clientX - scrubStartX;
            if (Math.abs(delta) < 6) return;
            scrubMoved = true;
            event.preventDefault();
            const targetIndex = Math.max(0, Math.min(
                flashcards.length - 1,
                scrubStartIndex + Math.round(delta / 24)
            ));
            goToDeckCard(targetIndex, { announceHeadword: false });
        });
        deckScrubber.addEventListener('pointerup', finishScrub);
        deckScrubber.addEventListener('pointercancel', finishScrub);
        deckScrubber.addEventListener('lostpointercapture', finishScrub);
    }

    // Card-position seek bar: a short drag is one card; a wide plateau
    // holds that step so skipping farther takes a longer pull.
    const cardBackPips = document.getElementById('cardBackPips');
    if (cardBackPips) {
        let pipPointerId = null;
        let scrubOriginIndex = 0;
        let scrubOriginX = 0;
        const endPipDrag = event => {
            if (pipPointerId === null || (event && event.pointerId !== pipPointerId)) return;
            if (cardBackPips.hasPointerCapture?.(pipPointerId)) {
                cardBackPips.releasePointerCapture(pipPointerId);
            }
            pipPointerId = null;
            cardBackPips.classList.remove('is-scrubbing');
        };
        cardBackPips.addEventListener('pointerdown', event => {
            if (event.button !== undefined && event.button !== 0) return;
            const card = flashcards[currentIndex];
            pipPointerId = event.pointerId;
            scrubOriginX = event.clientX;
            scrubOriginIndex = (card?.isChainChild && cardChainReturnIndex >= 0)
                ? cardChainReturnIndex
                : currentIndex;
            cardBackPips.classList.add('is-scrubbing');
            cardBackPips.setPointerCapture?.(event.pointerId);
        });
        cardBackPips.addEventListener('pointermove', event => {
            if (event.pointerId !== pipPointerId) return;
            event.preventDefault();
            const last = Math.max(0, flashcards.length - 1);
            const nextIndex = Math.max(0, Math.min(
                last,
                scrubOriginIndex + cardOffsetFromScrubDelta(event.clientX - scrubOriginX)
            ));
            goToDeckCard(nextIndex, { announceHeadword: false });
        });
        cardBackPips.addEventListener('pointerup', endPipDrag);
        cardBackPips.addEventListener('pointercancel', endPipDrag);
        cardBackPips.addEventListener('lostpointercapture', endPipDrag);
    }

    // Floating buttons (desktop sidebar) + on-card mobile copies share handlers.
    // Back uses navigateBack() which falls through to goBackToSetup() when
    // cardNavStack is empty — single smart-back affordance for normal decks
    // and synonym/search/lyrics popup chains alike.
    ['backBtnFloating', 'backBtnFrontMobile'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', function(e) {
            e.stopPropagation();
            navigateBack();
        });
    });

    // Exit routes off a child card: the top-bar "Back to …" control, plus the
    // legacy on-face X ids (now hidden by CSS, kept wired so nothing depends
    // on which affordance is current).
    ['stackedExitFront', 'stackedExitBack', 'cardBackReturn'].forEach(function(id) {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', function(e) { e.stopPropagation(); navigateBack(); });
    });
    ['statsBtnFloating', 'statsBtnPopup'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', function(e) {
            e.stopPropagation();
            showStatsModal();
        });
    });
    // Desktop speak button — toggles auto-speak
    document.getElementById('speakBtn').addEventListener('click', function(e) {
        e.stopPropagation();
        toggleAutoSpeak();
    });

    document.getElementById('closeStatsModal').addEventListener('click', hideStatsModal);

    // Settings modal interactions

    // Percentage mode toggle
    // Refresh study set - delete progress for words in current set
    document.getElementById('refreshSetToggle').addEventListener('click', async function() {
        if (!currentUser || currentUser.isGuest) {
            alert('You must be logged in to refresh your progress.');
            return;
        }

        if (flashcards.length === 0) {
            alert('No study set is currently loaded.');
            return;
        }

        // Get the word IDs that are in the current flashcard set
        const wordsInSet = flashcards.map(card => ({
            rank: card.rank,
            id: card.id,
            fullId: card.fullId,
            word: card.targetWord
        }));

        const confirmMsg = `This will reset your progress for ${wordsInSet.length} words in the current study set. These words will appear again when you study this set. Continue?`;
        if (!confirm(confirmMsg)) {
            return;
        }

        // Delete progress for each word in the set
        try {
            for (const wordInfo of wordsInSet) {
                // Remove from local progressData
                if (progressData[wordInfo.fullId]) {
                    delete progressData[wordInfo.fullId];
                }

                // Delete from Google Sheets
                await fetch(GOOGLE_SCRIPT_URL, {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'delete',
                        user: currentUser.initials,
                        wordId: wordInfo.fullId,
                        sheet: window.getProgressSheetName?.()
                            || (activeArtist ? 'Lyrics' : 'UserProgress'),
                        mode: window.getProgressMode?.() || (activeArtist ? 'artist' : 'normal')
                    })
                });
            }

            const parentWordIds = wordsInSet.map(word => word.fullId);
            for (const [itemId, item] of Object.entries(itemProgressData || {})) {
                if (parentWordIds.includes(item.parentWordId)) delete itemProgressData[itemId];
            }
            await fetch(GOOGLE_SCRIPT_URL, {
                method: 'POST',
                body: JSON.stringify({
                    action: 'deleteItems',
                    sheet: 'Progress',
                    user: currentUser.initials,
                    parentWordIds
                })
            });
            cacheItemProgress();

            alert(`Progress reset for ${wordsInSet.length} words. Go back to the menu and re-select this set to study the refreshed words.`);
            hideSettingsModal();
        } catch (error) {
            console.error('Failed to reset progress:', error);
            alert('Failed to reset progress. Please try again.');
        }
    });

    // Click outside modal to close
    document.getElementById('statsModal').addEventListener('click', function(e) {
        if (e.target === this) {
            hideStatsModal();
        }
    });

    // Deck complete modal buttons
    document.getElementById('restartAllBtn').addEventListener('click', async function() {
        if (this.dataset.action === 'review-level') {
            const completedLevel = selectedLevel;
            hideDeckCompleteModal();
            await goBackToSetup();
            const completedLevelButton = Array.from(document.querySelectorAll(
                '.level-selector-buttons .level-btn, #levelSelector > .level-btn'
            )).find(button => button.dataset.level === completedLevel);
            if (completedLevelButton && !completedLevelButton.classList.contains('selected')) {
                completedLevelButton.click();
            }
            for (let attempt = 0; attempt < 30; attempt++) {
                const reviewButton = document.querySelector('.study-set-review');
                if (reviewButton && !reviewButton.disabled) {
                    reviewButton.click();
                    return;
                }
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            return;
        }
        hideDeckCompleteModal();
        restartAllCards();
    });

    document.getElementById('markCompleteBtn').addEventListener('click', async function() {
        if (this.dataset.loading === 'true') return;
        const action = this.dataset.action;
        if (!action) return;
        this.dataset.loading = 'true';
        this.disabled = true;
        const nextRange = stats.nextRange;
        const nextRankBasis = stats.nextRankBasis || stats.rangeBasis || 'stable';
        const nextSetNumber = stats.nextSetNumber;
        const levelSetCount = stats.levelSetCount;
        const loadingTitle = action === 'next-set' && nextSetNumber
            ? `Loading Set ${nextSetNumber}`
            : 'Loading the Next Level';
        hideDeckCompleteModal();
        if (action === 'next-daily-review') {
            window.showAppLoading?.('Loading Daily Review', 'Preparing your next review cards…');
            try {
                await window.loadDailyReviewDeck?.({
                    urgencyTier: stats.dailyReviewTier,
                    limit: stats.dailyReviewLimit
                });
            } catch (error) {
                console.error('Could not continue daily review:', error);
                await window.showEndOfDeckOptions?.({ autoContinue: false });
            } finally {
                window.hideAppLoading?.();
            }
            return;
        }
        try {
            // The set dots were counted when setup last rendered, which can be
            // several sets ago: lemma merging marks siblings seen across sets,
            // so the set queued as "next" may have finished in the meantime.
            // loadVocabularyData reports that with false rather than alerting,
            // and we walk on to the next level instead of stranding the
            // learner on an empty deck with the modal already dismissed.
            let advanced = false;
            if (action === 'next-set' && nextRange) {
                advanced = await loadVocabularyData(nextRange, {
                    rankBasis: nextRankBasis,
                    setNumber: nextSetNumber,
                    levelSetCount,
                    silentIfEmpty: true
                }) !== false;
            }
            if (!advanced) {
                await window.startNextStudyLevelFirstSet?.();
            }
        } catch (error) {
            console.error('Could not continue from completed set:', error);
            // Reopen as a stable state. Retrying automatically would loop when
            // there genuinely is nothing left, so distinguish "finished
            // everything" from a real failure and say which.
            await window.showEndOfDeckOptions?.({ autoContinue: false });
            const message = document.getElementById('completeMessage');
            const exhausted = /no next study level|distinct next study level/i
                .test(String(error && error.message));
            if (message) {
                message.textContent = exhausted
                    ? 'Nothing left to study here — pick another level from the main menu.'
                    : 'Could not open the next level. Please try again.';
            }
        } finally {
            this.dataset.loading = 'false';
            this.disabled = false;
            window.hideAppLoading?.();
        }
    });

    document.getElementById('deckCompleteMenuBtn').addEventListener('click', async function() {
        hideDeckCompleteModal();
        await goBackToSetup();
    });

    // Click outside deck complete modal to close
    document.getElementById('deckCompleteModal').addEventListener('click', function(e) {
        if (e.target === this) {
            hideDeckCompleteModal();
        }
    });

    // Swipe gestures
    setupSwipeGestures();

    // Keyboard shortcuts
    setupKeyboardShortcuts();
}

// Toggles the swipe-legend's commit state: null restores "← Again / Got it
// →"; 'correct'/'incorrect' fills the strip and swaps to a single release
// label. Only the back-face legend exists in the DOM (see index.html).
function setSwipeLegendCommit(direction) {
    const legend = document.querySelector('.card-back .swipe-legend');
    if (!legend) return;
    legend.classList.toggle('legend-commit-correct', direction === 'correct');
    legend.classList.toggle('legend-commit-incorrect', direction === 'incorrect');
    const label = legend.querySelector('.swipe-legend-commit');
    if (label) {
        label.textContent = direction === 'correct' ? 'Release to mark correct'
            : direction === 'incorrect' ? 'Release to mark incorrect'
            : '';
    }
}

function setupSwipeGestures() {
    const card = document.getElementById('flashcard');
    const incorrectIndicator = document.getElementById('incorrectIndicator');
    const correctIndicator = document.getElementById('correctIndicator');
    let touchStartX = 0;
    let touchStartY = 0;
    let currentX = 0;
    let currentY = 0;
    let isDragging = false;
    let hasMoved = false;
    let touchStartTime = 0;
    let maxMovement = 0; // Track maximum movement during touch
    let startedOnCircle = false; // Track if touch started on flip circle
    let touchZone = null; // Track which zone touch started in
    let wasFlippedAtStart = false; // Track flip state at touch start

    // Helper to determine touch zone (center vs edges)
    function getTouchZone(touchX, cardRect) {
        const relativeX = (touchX - cardRect.left) / cardRect.width;
        if (relativeX < 0.25) return 'left-edge';
        if (relativeX > 0.75) return 'right-edge';
        return 'center';
    }

    card.addEventListener('touchstart', function(e) {
        // Don't handle if touch is on buttons, links, or specific interactive elements
        if (e.target.closest('.nav-btn-inline') ||
            e.target.closest('.gear-btn') ||
            e.target.closest('.link-btn') ||
            e.target.closest('.ref-icon-btn') ||
            e.target.closest('.card-control-btn') ||
            e.target.closest('.card-action-small') ||
            e.target.closest('.desktop-answer-btn') ||
            // Inline set scrubber (chevrons, pip drag surface, gear) — its
            // own pointerdown/click handlers own this touch entirely.
            e.target.closest('.card-back-scrubber') ||
            e.target.closest('[onclick]')) {
            return;
        }

        // Check if touch started on flip button or flip-back-area
        startedOnCircle = !!(e.target.closest('#flipBtn') || e.target.closest('.flip-back-area'));

        // Track flip state at start of touch
        wasFlippedAtStart = card.classList.contains('flipped');

        // Get touch zone for zone-based gesture handling
        const cardRect = card.getBoundingClientRect();
        touchZone = getTouchZone(e.touches[0].clientX, cardRect);

        // On back side, allow swiping from card-details area (remove the restriction)
        // Only block actual interactive elements like onclick handlers
        if (wasFlippedAtStart) {
            // Back side: allow swipe from anywhere except buttons/links
            // This enables swiping even from card-details area
        } else {
            // Front side: standard handling
            if (e.target.closest('.card-front') || e.target.closest('#flipBtn')) {
                // Allow touch to proceed
            } else {
                return;
            }
        }

        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        currentX = touchStartX;
        currentY = touchStartY;
        isDragging = true;
        hasMoved = false;
        maxMovement = 0;
        touchStartTime = Date.now();
        card.classList.add('swiping');
    }, { passive: true });

    card.addEventListener('touchmove', function(e) {
        if (!isDragging) return;

        currentX = e.touches[0].clientX;
        currentY = e.touches[0].clientY;

        const diffX = currentX - touchStartX;
        const diffY = currentY - touchStartY;
        const totalMovement = Math.abs(diffX) + Math.abs(diffY);
        maxMovement = Math.max(maxMovement, totalMovement);

        // Only mark as moved if significant movement (raised threshold)
        if (Math.abs(diffX) > 5 || Math.abs(diffY) > 5) {
            hasMoved = true;
        }

        // Horizontal swipes - move card and show indicators
        if (Math.abs(diffX) > Math.abs(diffY) && hasMoved) {
            const rotation = diffX / 20; // Rotate based on swipe distance

            // Preserve flip state when moving card
            const isFlipped = card.classList.contains('flipped');
            if (isFlipped) {
                card.style.transform = `translateX(${diffX}px) rotate(${rotation}deg) rotateY(180deg)`;
            } else {
                card.style.transform = `translateX(${diffX}px) rotate(${rotation}deg)`;
            }

            // Show indicators based on swipe direction
            if (diffX > 50) {
                correctIndicator.classList.add('visible');
                incorrectIndicator.classList.remove('visible');
            } else if (diffX < -50) {
                incorrectIndicator.classList.add('visible');
                correctIndicator.classList.remove('visible');
            } else {
                correctIndicator.classList.remove('visible');
                incorrectIndicator.classList.remove('visible');
            }

            // Swipe legend reacts once the drag passes ~40% of the card's
            // width — independent of the 50px auto-commit threshold above,
            // this is purely the visual "you're about to release this" cue.
            const progress = Math.abs(diffX) / (card.offsetWidth || 1);
            if (progress > 0.4) {
                setSwipeLegendCommit(diffX > 0 ? 'correct' : 'incorrect');
            } else {
                setSwipeLegendCommit(null);
            }
        }
    }, { passive: true });

    card.addEventListener('touchend', function(e) {
        if (!isDragging) return;
        isDragging = false;
        setSwipeLegendCommit(null);

        const diffX = currentX - touchStartX;
        const diffY = currentY - touchStartY;
        const touchDuration = Date.now() - touchStartTime;

        // Check if indicator is visible BEFORE removing it
        const indicatorWasVisible = correctIndicator.classList.contains('visible') || incorrectIndicator.classList.contains('visible');
        const swipeDirection = correctIndicator.classList.contains('visible') ? 'correct' : 'incorrect';

        card.classList.remove('swiping');
        correctIndicator.classList.remove('visible');
        incorrectIndicator.classList.remove('visible');

        // Reset card transform
        card.style.transform = '';

        // If indicator was visible, auto-complete the swipe
        if (indicatorWasVisible) {
            handleSwipeAction(swipeDirection);
            return;
        }

        // Tap detection
        const isTap = touchDuration < 250 && maxMovement < 10;
        const isQuickTap = touchDuration < 350 && maxMovement < 18;

        // ========== FRONT SIDE LOGIC (flip priority) ==========
        if (!wasFlippedAtStart) {
            // If touch started on flip circle, only allow flipping
            if (startedOnCircle) {
                if (touchDuration < 500 && maxMovement < 100) {
                    flipCard();
                }
                return;
            }

            // Center zone: flip is priority, ignore swipes
            if (touchZone === 'center') {
                // Only flip on clear taps, not on any small movement
                if (isTap || isQuickTap) {
                    flipCard();
                }
                return;
            }

            // Edge zones: intentional swipe takes priority
            const edgeSwipeThreshold = 14;
            const isEdgeSwipe = Math.abs(diffX) > edgeSwipeThreshold && Math.abs(diffX) > Math.abs(diffY);

            if (isEdgeSwipe) {
                handleSwipeAction(diffX > 0 ? 'correct' : 'incorrect');
            } else if (isTap) {
                flipCard(); // Tap on edge still flips
            }
            return;
        }

        // ========== BACK SIDE LOGIC (swipe priority) ==========
        const backSwipeThreshold = 12;
        const isHorizontalSwipe = Math.abs(diffX) > backSwipeThreshold && Math.abs(diffX) > Math.abs(diffY) * 1.15;
        const isVerticalSwipe = Math.abs(diffY) > backSwipeThreshold && Math.abs(diffY) > Math.abs(diffX) * 1.15;

        if (isHorizontalSwipe) {
            // Horizontal swipe - correct/incorrect
            handleSwipeAction(diffX > 0 ? 'correct' : 'incorrect');
        } else if (isVerticalSwipe) {
            // Vertical swipe - cycle through meanings for multi-meaning cards
            const currentCard = flashcards[currentIndex];
            if (currentCard && currentCard.isMultiMeaning) {
                if (diffY < 0) {
                    currentMeaningIndex = (currentMeaningIndex + 1) % currentCard.meanings.length;
                } else {
                    currentMeaningIndex = (currentMeaningIndex - 1 + currentCard.meanings.length) % currentCard.meanings.length;
                }
                updateCard();
            } else if (currentCard && currentCard.sentences) {
                if (diffY < 0) {
                    currentSentenceIndex = (currentSentenceIndex + 1) % currentCard.sentences.length;
                } else {
                    currentSentenceIndex = (currentSentenceIndex - 1 + currentCard.sentences.length) % currentCard.sentences.length;
                }
                updateCard();
            }
        } else if (startedOnCircle && maxMovement < 50) {
            // Only flip back if specifically tapping the flip area
            flipCard();
        } else if (isTap) {
            // A tap anywhere else on the back flips back to front
            flipCard();
        }
    }, { passive: true });
}

function pressAnswerBtn(id) {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.classList.remove('pressed');
    // Force reflow to restart animation if pressed rapidly
    void btn.offsetWidth;
    btn.classList.add('pressed');
    btn.addEventListener('animationend', () => btn.classList.remove('pressed'), { once: true });
}

function toggleAutoSpeak() {
    speechEnabled = !speechEnabled;
    window.saveGlobalStudyPreference?.('speechEnabled', speechEnabled);
    updateSpeakIcons();
    window.saveStudySessionSnapshot?.();
}

function updateSpeakIcons() {
    // Update desktop centred speaker icon + mobile actions-popup speak icon.
    ['speakBtnIcon', 'speakBtnPopupIcon'].forEach(id => {
        const svg = document.getElementById(id);
        if (!svg) return;
        svg.querySelectorAll('.speak-on-indicator').forEach(el => {
            el.style.display = speechEnabled ? '' : 'none';
        });
        svg.querySelectorAll('.speak-off-indicator').forEach(el => {
            el.style.display = speechEnabled ? 'none' : '';
        });
    });
}

function toggleKeyboardShortcutsModal(force) {
    const modal = document.getElementById('keyboardShortcutsModal');
    if (!modal) return;
    const shouldOpen = typeof force === 'boolean' ? force : modal.classList.contains('hidden');
    if (shouldOpen) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}
window.toggleKeyboardShortcutsModal = toggleKeyboardShortcutsModal;

function setupKeyboardShortcuts() {
    const shortcutsModal = document.getElementById('keyboardShortcutsModal');
    if (shortcutsModal && !shortcutsModal._shortcutsWired) {
        shortcutsModal._shortcutsWired = true;
        document.getElementById('closeKeyboardShortcutsModal')?.addEventListener('click', () => {
            toggleKeyboardShortcutsModal(false);
        });
        shortcutsModal.addEventListener('click', (ev) => {
            if (ev.target === shortcutsModal) toggleKeyboardShortcutsModal(false);
        });
    }

    document.addEventListener('keydown', function(e) {
        // Ignore if typing in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        // Completion owns the interaction layer. Without this guard, global
        // card shortcuts continue changing the exhausted deck behind the
        // modal, so dismissing it can reveal a different card/state.
        const deckCompleteModal = document.getElementById('deckCompleteModal');
        if (deckCompleteModal && !deckCompleteModal.classList.contains('hidden')) {
            e.preventDefault();
            if (e.key === 'Escape') {
                hideDeckCompleteModal();
            } else if (e.key === 'Enter' && window.matchMedia('(min-width: 768px)').matches) {
                const continueBtn = document.getElementById('markCompleteBtn');
                if (continueBtn?.dataset.action && continueBtn.dataset.loading !== 'true' && !continueBtn.disabled) {
                    continueBtn.click();
                }
            }
            return;
        }

        // While the sense-level flag menu is open it owns the keyboard: ↑/↓
        // pick a sense, Enter submits, Esc cancels (handled by the menu's own
        // listener in flashcards-modals.js). Bail so we don't also cycle the
        // card underneath.
        const _flagMenuEl = document.getElementById('flagMenu');
        if (_flagMenuEl && !_flagMenuEl.hidden) return;

        // Toggle keyboard shortcuts cheat sheet
        if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
            e.preventDefault();
            toggleKeyboardShortcutsModal();
            return;
        }

        const commandModifier = e.ctrlKey || e.metaKey;
        const commandKey = String(e.key || '').toLowerCase();
        const canFlag = Boolean(window.canUserFlag ? window.canUserFlag() : window.isAuditAccount?.());
        if (commandModifier && !e.altKey && commandKey === 'i' && !e.shiftKey && isJstOwner()) {
            e.preventDefault();
            toggleProvenancePanel();
            return;
        }
        if (commandModifier && !e.altKey && commandKey === 's' && !e.shiftKey) {
            e.preventDefault();
            showStatsModal();
            return;
        }
        if (commandModifier && !e.altKey && commandKey === 'p' && !e.shiftKey) {
            e.preventDefault();
            showSettingsModalWithTab('study', { singleTab: true });
            return;
        }
        if (commandModifier && !e.altKey && commandKey === 'f' && canFlag) {
            e.preventDefault();
            if (e.shiftKey) window.showFlagMenu?.();
            else window.sendWholeCardFlag?.();
            return;
        }

        // Left arrow = previous card
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            previousCard();
        }
        // Right arrow = next card
        else if (e.key === 'ArrowRight') {
            e.preventDefault();
            nextCard();
        }
        // Up arrow = previous meaning
        else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const card = flashcards[currentIndex];
            if (card && card.meanings && card.meanings.length > 1 && currentMeaningIndex > 0) {
                selectMeaning(currentMeaningIndex - 1);
            }
        }
        // Down arrow = next meaning
        else if (e.key === 'ArrowDown') {
            e.preventDefault();
            const card = flashcards[currentIndex];
            if (card && card.meanings && card.meanings.length > 1 && currentMeaningIndex < card.meanings.length - 1) {
                selectMeaning(currentMeaningIndex + 1);
            }
        }
        // Shift+Tab = next card (alternative to right arrow)
        else if (e.key === 'Tab' && e.shiftKey) {
            e.preventDefault();
            nextCard();
        }
        // Tab = cycle examples / MWE expressions
        else if (e.key === 'Tab') {
            e.preventDefault();
            const card = flashcards[currentIndex];
            if (!card || !card.meanings) return;
            const m = card.meanings[currentMeaningIndex];
            if (m && m.allMWEs && m.allMWEs.length > 1) {
                // MWE meaning: cycle expressions
                cycleMWEForward();
            } else {
                // Regular meaning: cycle examples
                cycleExampleForward();
            }
        }
        // Enter or C = correct
        else if (e.key === 'Enter' || e.key === 'c' || e.key === 'C') {
            e.preventDefault();
            handleSwipeAction('correct');
        }
        // X or 1 = incorrect
        else if (e.key === 'x' || e.key === 'X' || e.key === '1') {
            e.preventDefault();
            handleSwipeAction('incorrect');
        }
        // A = pronounce headword
        else if (e.key === 'a' || e.key === 'A') {
            e.preventDefault();
            const card = flashcards[currentIndex];
            if (card && typeof window.speakWord === 'function') {
                window.speakWord(getDisplayedTargetHeadword(card));
            }
        }
        // F = open find a word modal (for non-audit users)
        else if ((e.key === 'f' || e.key === 'F') && !canFlag) {
            e.preventDefault();
            window.openFindWord?.();
        }
        // Legacy single-key shortcut retained for the owner audit workflow.
        else if ((e.key === 'f' || e.key === 'F') && canFlag) {
            e.preventDefault();
            handleFlagAction();
        }
        // Space = flip card
        else if (e.key === ' ') {
            e.preventDefault();
            flipCard();
        }
        // Escape = close modal or smart-back (pop nav stack, else return to setup)
        else if (e.key === 'Escape') {
            e.preventDefault();
            // A side panel stays open while you study, so Escape must close
            // it rather than fall through to navigateBack and leave the set.
            if (window.sideDock?.closeTopmost()) return;
            const scModal = document.getElementById('keyboardShortcutsModal');
            const deckModal = document.getElementById('deckCompleteModal');
            const statsModal = document.getElementById('statsModal');
            const provenancePanel = document.getElementById('provenancePanel');
            if (scModal && !scModal.classList.contains('hidden')) {
                toggleKeyboardShortcutsModal(false);
            } else if (provenancePanel && provenancePanel.style.display !== 'none') {
                toggleProvenancePanel(false);
            } else if (deckModal && !deckModal.classList.contains('hidden')) {
                hideDeckCompleteModal();
            } else if (statsModal && !statsModal.classList.contains('hidden')) {
                hideStatsModal();
            } else {
                navigateBack();
            }
        }
    });
}

function handleFlagAction() {
    const currentCard = flashcards[currentIndex];
    if (!currentCard || !currentCard.rank) return;

    // Primary path: open the sense-level flag menu (lazy-loaded from
    // flashcards-modals.js). It lets the user target a specific word→meaning
    // pairing and navigate senses with ↑/↓, then calls advanceAfterFlag() on
    // submit. If the menu module can't be reached, fall back to the original
    // instant whole-word flag so flagging never breaks.
    if (typeof window.showFlagMenu === 'function') {
        window.showFlagMenu();
        return;
    }

    flagWord(currentCard);
    advanceAfterFlag();
}

// Flag animation + advance to the next card. Extracted from the old
// handleFlagAction so the sense-level flag menu can reuse the exact same
// post-flag behavior after the user submits a pairing.
function advanceAfterFlag() {
    const card = document.getElementById('flashcard');
    if (!card) return;
    card.classList.add('swipe-flag');

    setTimeout(() => {
        card.classList.remove('swipe-flag');
        card.style.transform = '';

        if (cardNavStack.length > 0) {
            navigateBack();
            return;
        }

        if (currentIndex < flashcards.length - 1) {
            currentIndex++;
            currentSentenceIndex = 0;
            currentMeaningIndex = 0;
            currentExampleIndex = 0;
            currentMWEIndex = 0;
            currentGroupSelection = null;
            updateCard({ announceHeadword: true });
            document.getElementById('flashcard').classList.remove('flipped');
        } else {
            showEndOfDeckOptions();
        }
    }, 300);
}
window.advanceAfterFlag = advanceAfterFlag;

function handleSwipeAction(result) {
    stopExampleAutoplay(true);
    const card = document.getElementById('flashcard');
    const isFlipped = card.classList.contains('flipped');

    // A correct grade on an ordinary deck card (not already inside a nav-
    // stack popup/peek) with pending MWE/CLITIC entries starts the phrase
    // chain instead of advancing normally. Captured before recordCardResult
    // in case it mutates card state.
    const swipedCard = flashcards[currentIndex];
    const isChainChild = swipedCard?.isChainChild === true;
    // Automatic chain child: rare senses and expressions appear after a
    // correct parent card when their own study preference is on.
    const mayChain = (expressionsModeEnabled || rareSensesModeEnabled) && !isChainChild
        && cardNavStack.length === 0 && result === 'correct';

    // Record the result
    recordCardResult(result);

    // Animate the card off screen (maintain flip state during animation)
    if (result === 'correct') {
        card.classList.add('swipe-correct');
    } else {
        card.classList.add('swipe-incorrect');
    }

    // Wait for animation to complete, then move to next card
    setTimeout(async () => {
        card.classList.remove('swipe-correct', 'swipe-incorrect');
        card.style.transform = '';

        // One swipe on a chain child grades that child (phrases only) and
        // either moves to the next child or returns to the deck.
        if (isChainChild) {
            finishPhraseChain(result === 'correct');
            return;
        }

        // Starting a chain off the just-graded parent card. Building the plan
        // awaits a shard fetch the first time a level is opened; it is
        // memoised after that, and a failed fetch yields an empty plan rather
        // than blocking the swipe.
        if (mayChain) {
            const children = await buildCardChildren(swipedCard);
            if (children.length > 0) {
                startCardChain(children);
                return;
            }
        }

        // If we're on a linked card (nav stack), go back instead of advancing
        if (cardNavStack.length > 0) {
            navigateBack();
            return;
        }

        advanceToNextDeckCard();
    }, 300);
}

// Plain forward step through the deck, shared by the ordinary swipe path and
// by the chain unwinding after its last child.
function advanceToNextDeckCard() {
    if (currentIndex < flashcards.length - 1) {
        currentIndex++;
        currentSentenceIndex = 0;
        currentMeaningIndex = 0;
        currentExampleIndex = 0;
        currentMWEIndex = 0;
        currentGroupSelection = null;
        updateCard({ announceHeadword: true });
        document.getElementById('flashcard').classList.remove('flipped');
    } else {
        showEndOfDeckOptions();
    }
}

function recordCardResult(result) {
    const isCorrect = result === 'correct';

    // Skip session stats for peek/stacked cards and phrase-chain children —
    // a phrase isn't a deck word, so it shouldn't inflate "X/Y correct".
    if (cardNavStack.length === 0 && !flashcards[currentIndex]?.isChainChild) {
        if (!stats.cardStats[currentIndex]) {
            stats.cardStats[currentIndex] = { correct: 0, incorrect: 0, attempts: [] };
        }
        if (!Array.isArray(stats.cardStats[currentIndex].attempts)) {
            stats.cardStats[currentIndex].attempts = [];
        }
        stats.cardStats[currentIndex].attempts.push({
            result: isCorrect ? 'correct' : 'incorrect',
            at: new Date().toISOString()
        });
        if (isCorrect) {
            stats.correct++;
            stats.cardStats[currentIndex].correct++;
        } else {
            stats.incorrect++;
            stats.cardStats[currentIndex].incorrect++;
        }
        stats.total++;
    }

    // Save progress to Google Sheets or LocalStorage
    const currentCard = flashcards[currentIndex];
    if (currentCard?.previewOnly) return;
    if (currentCard && currentCard.rank) {
        saveWordProgress(currentCard, isCorrect);
    }
}

function showFloatingBtns(show) {
    const btns = document.getElementById('floatingBtns');
    const userInfo = document.getElementById('userInfo');
    if (btns) {
        if (show) {
            btns.classList.add('visible');
        } else {
            btns.classList.remove('visible');
        }
    }
    // The only visible study control now lives beside the deck progress rail;
    // retain the legacy buttons as hidden handler targets without showing an
    // empty desktop/mobile toolbar container.
    if (userInfo) userInfo.classList.add('hidden');
}

async function goBackToSetup() {
    // Rebuilding the level selector takes long enough to notice, and every
    // other transition in the app announces itself. Without this the tap read
    // as the app stalling rather than working — the same overlay Learn New and
    // Review already use.
    window.showAppLoading?.('Main menu', 'Updating your levels…');
    stopExampleAutoplay(true);
    // Hide app content, show setup
    const appContent = document.getElementById('appContent');
    const setupPanel = document.getElementById('setupPanel');

    appContent.classList.add('hidden');
    setupPanel.classList.remove('hidden');
    setupPanel.style.display = 'block';

    // Hide mobile floating buttons
    showFloatingBtns(false);

    // Clear nav stack and vocab lookup
    cardNavStack = [];
    fullVocabLookup = null;
    vocabByIdLookup = null;

    // Scroll to top
    document.querySelector('.container').scrollTop = 0;

    // Keep the language selected and show subsequent steps
    // Show inline language pill, hide tabs
    document.getElementById('languageTabs').style.display = 'none';
    const inlinePill = document.getElementById('selectedLanguageInline');
    const langConfig = config.languages[selectedLanguage];
    inlinePill.textContent = langConfig ? langConfig.name : selectedLanguage;
    inlinePill.style.display = 'inline-flex';

    // Show step 2 and keep level selected if one was selected
    document.getElementById('step2').style.display = 'block';
    document.getElementById('step4').style.display = 'none';

    // Reset only the active set selection, not the level
    document.querySelectorAll('.range-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    document.querySelectorAll('.range-btn-new').forEach(btn => {
        btn.classList.remove('selected');
    });
    selectedRanges = [];
    flashcards = [];
    currentIndex = 0;
    currentSentenceIndex = 0;
    currentMeaningIndex = 0;
    currentExampleIndex = 0;
    currentMWEIndex = 0;

    // Everything above is cheap DOM work; everything below rebuilds the level
    // selector, which walks every card in the deck. Without a paint in
    // between, the browser applies both in one frame, so the tap appeared to
    // do nothing for seconds and then jumped. Yield once so the setup panel is
    // on screen first, and show progress while the rest runs.
    const levelSelectorEl = document.getElementById('levelSelector');
    if (levelSelectorEl) levelSelectorEl.setAttribute('aria-busy', 'true');
    // Yield once so the panel paints before the rebuild blocks. requestAnimationFrame
    // alone is not safe here: a hidden or backgrounded tab never fires it, so
    // switching away mid-navigation left this awaiting forever with the loading
    // overlay stuck on screen. The timeout guarantees the yield ends either way.
    await new Promise(resolve => {
        requestAnimationFrame(resolve);
        setTimeout(resolve, 50);
    });

    // Always load PPM data if available (needed for coverage bar even in CEFR mode)
    const ppmStarted = performance.now();
    if (!ppmData || ppmData.length === 0) {
        await loadPpmData(selectedLanguage);
    }
    window.__setupPhaseOffset = performance.now() - ppmStarted;

    // Main-menu return is a fresh suggestion decision, not restoration of the
    // level that owned the set we just left. Route past levels whose available
    // cards are all seen or which the learner explicitly skipped.
    await renderLevelSelector(selectedLanguage, { preferActionable: true });
    levelSelectorEl?.removeAttribute('aria-busy');

    updateLemmaToggleVisibility();
    updateCognateToggleVisibility();
    updateExclusionBars();

    // Reset card state
    const flashcardEl = document.getElementById('flashcard');
    if (flashcardEl) {
        flashcardEl.classList.remove('flipped');
    }

    stats = {
        studied: new Set(),
        correct: 0,
        incorrect: 0,
        total: 0,
        cardStats: {}
    };
    window.hideAppLoading?.();
}

function foldSurfaceForm(value) {
    return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLocaleLowerCase('es')
        .trim();
}

// Letters that fold together for matching purposes. `foldSurfaceForm` already
// strips accents everywhere else in this file; the occurrence regex was the
// one comparison that did not, so a card on *estás* found nothing in a line
// spelling it *estas* — and subtitles and lyrics drop accents constantly. The
// card then showed no underline, and on a merged card the wrong headword.
const SURFACE_FOLD_CLASSES = {
    a: 'aáàäâãå', e: 'eéèëê', i: 'iíìïî', o: 'oóòöôõ', u: 'uúùüû',
    n: 'nñ', c: 'cç', y: 'yý',
};

function exampleOccurrenceSurfaceRegex(form, flags = 'giu') {
    const normalized = String(form || '').trim();
    if (!normalized) return null;
    const body = Array.from(normalized).map(char => {
        if (/\s/.test(char)) return '\\s+';
        if (char === '’' || char === "'") return "['’]";
        const base = char.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
        const cls = SURFACE_FOLD_CLASSES[base];
        if (cls) return `[${cls}]`;
        return char.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }).join('').replace(/(?:\\s\+)+/g, '\\s+');
    return _cachedRegex(`(?<![\\p{L}\\p{N}])(${body})(?![\\p{L}\\p{N}])`, flags);
}

// Object pronouns that attach to the end of an infinitive, gerund or
// imperative. A card keyed on `verte` is asking about `ver`; the sentence may
// carry the bare verb with the pronoun somewhere else entirely, or attached to
// a different form of it, and the card surface then matches nothing at all.
const ENCLITIC_PRONOUNS = [
    'melo', 'mela', 'melos', 'melas', 'telo', 'tela', 'telos', 'telas',
    'selo', 'sela', 'selos', 'selas', 'noslo', 'nosla', 'noslos', 'noslas',
    'oslo', 'osla', 'oslos', 'oslas',
    'me', 'te', 'se', 'nos', 'os', 'le', 'les', 'lo', 'la', 'los', 'las',
];

// Every form worth looking for, given the card surface: the surface itself,
// then the stem left behind by peeling one enclitic and then two. Longest
// pronouns first so `dármelo` peels `melo`, not `lo`.
function encliticCandidates(form) {
    const out = [];
    const peel = (value) => {
        const folded = foldSurfaceForm(value);
        for (const pronoun of ENCLITIC_PRONOUNS) {
            if (!folded.endsWith(pronoun)) continue;
            const stem = value.slice(0, value.length - pronoun.length);
            // Below four letters a "stem" is as likely to be coincidence as
            // morphology — `lo` peeled off `solo` leaves `so`, not a verb.
            if (foldSurfaceForm(stem).length >= 3) return stem;
        }
        return '';
    };
    let current = form;
    for (let i = 0; i < 2; i++) {
        current = peel(current);
        if (!current) break;
        out.push(current);
    }
    return out;
}

// Last resort when nothing the data declared appears in the sentence: find the
// word in the sentence that is most plausibly another form of this surface.
// Deliberately conservative — a wrong guess underlines the wrong word, which
// is worse than underlining nothing.
function inferOccurrenceFromSentence(surface, sentence) {
    const target = foldSurfaceForm(surface);
    // Short words are function words far more often than they are inflections,
    // and their stems collide with everything: `que` would claim `querer`.
    if (target.length < 4) return '';
    const text = String(sentence || '').replace(/<[^>]*>/g, '');
    const tokens = text.match(/[\p{L}\p{N}]+(?:['\u2019][\p{L}\p{N}]+)*/gu) || [];
    const minPrefix = Math.max(3, target.length - 3);
    let best = '';
    let bestPrefix = 0;
    for (const token of tokens) {
        const candidate = foldSurfaceForm(token);
        if (!candidate || candidate === target) continue;
        if (Math.abs(candidate.length - target.length) > 3) continue;
        let shared = 0;
        while (shared < candidate.length && shared < target.length
            && candidate[shared] === target[shared]) shared++;
        if (shared < minPrefix) continue;
        // Both remainders must be short: a shared stem with a long tail on
        // either side is a different word that happens to start the same way.
        if (target.length - shared > 3 || candidate.length - shared > 3) continue;
        if (shared > bestPrefix) {
            bestPrefix = shared;
            best = token;
        }
    }
    return best;
}

// The one place that answers "which word is this example actually about?".
// The card header and the sentence underline both read this, because when they
// answered it separately they could disagree: a pooled example missing
// `pooledFrom` sent the header to the representative surface (showing *buena*)
// while the sentence read *buenos*, and the underline — which does check the
// sentence — matched nothing and highlighted nothing. One bug, both halves.
function resolveExampleOccurrence(card, example, sentence) {
    // `surface` is the immutable spelling attached to this occurrence;
    // `pooledFrom` is the canonical sibling form that contributed the example
    // to a merged lemma. Prefer what was actually said, then preserve legacy
    // decks through their pooled/card fallbacks.
    const declared = [
        example?.surface,
        example?.matched_surface,
        example?.pooledFrom,
        card?.representativeSurface,
        card?.targetWord
    ];
    const seen = new Set();
    const tried = [];
    // Always answer with the spelling the sentence actually carries, not the
    // candidate that matched it. The two differ whenever the corpus dropped an
    // accent (*estas* for *estás*), and peeling an enclitic can leave a stem
    // that is not a word at all — `dármelo` minus `melo` is `dár`, and
    // printing that above the card would be nonsense. `dar` is in the line.
    const text = String(sentence || '');
    const matched = (form) => {
        const regex = exampleOccurrenceSurfaceRegex(form, 'iu');
        const hit = regex ? regex.exec(text) : null;
        return hit ? hit[1] : '';
    };
    for (const candidate of declared) {
        const form = String(candidate || '').trim();
        const key = foldSurfaceForm(form);
        if (!form || seen.has(key)) continue;
        seen.add(key);
        tried.push(form);
        const hit = matched(form);
        if (hit) return { surface: hit, kind: 'declared' };
    }
    // Nothing declared is in the sentence. Peel enclitics off each candidate —
    // a card on `verte` against a line carrying `ver`.
    for (const form of tried) {
        for (const stem of encliticCandidates(form)) {
            const hit = matched(stem);
            if (hit) return { surface: hit, kind: 'enclitic' };
        }
    }
    for (const form of tried) {
        const inferred = inferOccurrenceFromSentence(form, sentence);
        if (inferred) return { surface: inferred, kind: 'inferred' };
    }
    return { surface: '', kind: 'none' };
}

function getExampleOccurrenceSurface(card, example, sentence) {
    return resolveExampleOccurrence(card, example, sentence).surface;
}

// 18px-wide slot on the left of every sense row. Selected rows get a teal
// checkmark; unselected rows get nothing — but the slot is always reserved
// (via CSS padding on .meaning-row) so text stays aligned across rows.
// Color alone no longer carries the selection state.
// Checkmarks removed per learner request to maximize horizontal width
// and eliminate visual clutter; row highlight and border already convey selection.
function renderRowCheckSlot(isSelected) {
    return '';
}

// Note: escapeCardText, legacyObjectPronounProjection, isWiktionaryGrammarNote,
// and projectWiktionaryGloss are now imported from ./card-metadata-pills.js


// A subsense that is not selected is a navigation label, not the place to
// reproduce Wiktionary's full editorial aside. Keep that detail verbatim on
// the active subsense, where the matching example gives it context.
function displaySenseGloss(meaning, value, active = true) {
    // A parenthetical may be the only semantic distinction (e.g. location
    // versus direction). Selection must not decide whether it is readable.
    return projectWiktionaryGloss(meaning, value).display;
}

function senseGlossDetailHTML(meaning, active) {
    if (!active) return '';
    const original = String(meaning?.meaning || meaning?.translation || '');
    const match = /\((the definite grammatical article[^]*)\)$/i.exec(original);
    if (!match) return '';
    return `<details class="sense-definition-detail" onclick="event.stopPropagation()"><summary>Full definition</summary>${escapeCardText(match[1])}</details>`;
}

function senseCrossReferences(meaning) {
    const metadata = meaning?.metadata || {};
    const candidates = [
        metadata.sense_metadata?.source_metadata?.cross_references,
        metadata.cross_references,
        metadata.sense_provider_metadata?.cross_references,
    ];
    const referencesOut = [];
    const seen = new Set();
    for (const references of candidates) {
        if (!Array.isArray(references)) continue;
        for (const reference of references) {
            const relation = String(reference?.relation || '').trim();
            const target = String(reference?.target || '').trim();
            if (!['see', 'indirect_object', 'after_prepositions'].includes(relation) || !target) continue;
            const key = `${relation}\u0000${target.toLocaleLowerCase('en')}`;
            if (seen.has(key)) continue;
            seen.add(key);
            referencesOut.push({ relation, target });
        }
    }
    if (referencesOut.length) return referencesOut;

    // Current releases predate the structured field. Keep their behaviour
    // correct with the same deliberately narrow shape used by the parser.
    const fallback = /^See ([^.]+)\.$/.exec(String(meaning?.meaning || '').trim());
    if (fallback) {
        return fallback[1].split(',').map(value => value.trim()).filter(Boolean)
            .map(target => ({ relation: 'see', target }));
    }
    return legacyObjectPronounProjection(meaning?.meaning || meaning?.translation)?.references || [];
}

function senseCrossReferenceHTML(meaning, fallbackText, active = true) {
    // Related cards are supporting navigation, not part of the gloss. Keep
    // them off inactive rows, then give them their own quiet line once this
    // sense is selected. This prevents a compact menu label from reading like
    // one long, malformed definition.
    if (!active) return fallbackText;
    const references = senseCrossReferences(meaning);
    if (!references.length) return fallbackText;
    const link = ({ target }) => {
        const encoded = encodeURIComponent(target);
        return `<button type="button" class="sense-cross-reference" data-reference-target="${encoded}" onclick="openSenseCrossReference(event, decodeURIComponent(this.dataset.referenceTarget))" title="Open ${escapeCardText(target)}">${escapeCardText(target)}</button>`;
    };
    if (references.every(reference => reference.relation === 'see')) {
        const links = references.map(reference => (
            `<span class="sense-cross-reference-item"><span class="sense-cross-reference-prefix">Related</span>${link(reference)}</span>`
        )).join('');
        return `<span class="sense-cross-reference-related" aria-label="Related cards">${links}</span>`;
    }
    const labels = {
        indirect_object: 'Indirect form',
        after_prepositions: 'After prepositions',
        see: 'Related',
    };
    const related = references.map(reference => (
        `<span class="sense-cross-reference-item"><span class="sense-cross-reference-prefix">${labels[reference.relation]}</span>${link(reference)}</span>`
    )).join('');
    const projected = legacyObjectPronounProjection(meaning?.meaning || meaning?.translation);
    return `<span class="sense-cross-reference-gloss">${projected?.display || fallbackText}</span><span class="sense-cross-reference-related" aria-label="Related cards">${related}</span>`;
}

async function openSenseCrossReference(event, target) {
    event?.preventDefault?.();
    event?.stopPropagation?.();
    const cleanTarget = String(target || '').trim();
    const preferredSource = (activeArtist && window._cachedMergedIndex)
        ? window._cachedMergedIndex
        : window._cachedJoinedIndex;
    const vocabSource = [preferredSource, window._cachedJoinedIndex]
        .filter(Array.isArray)
        .flat();
    if (!cleanTarget || !Array.isArray(vocabSource)) return;

    const foldedTarget = foldSurfaceForm(cleanTarget);
    const exactEntry = vocabSource.find(entry => foldSurfaceForm(entry?.word) === foldedTarget)
        || vocabSource.find(entry => foldSurfaceForm(entry?.lemma) === foldedTarget);
    const phraseOwner = vocabSource.find(entry =>
        Array.isArray(entry?.mwe_memberships)
        && entry.mwe_memberships.some(mwe => foldSurfaceForm(mwe?.expression) === foldedTarget));
    const headword = cleanTarget.split(/\s+/u)[0];
    const foldedHeadword = foldSurfaceForm(headword);
    const headwordEntry = vocabSource.find(entry => foldSurfaceForm(entry?.word) === foldedHeadword)
        || vocabSource.find(entry => foldSurfaceForm(entry?.lemma) === foldedHeadword);
    const entry = exactEntry || phraseOwner || headwordEntry;
    if (!entry?.id || !window.popupFoundWord) return;

    await window.popupFoundWord(
        { id: entry.id, sourceEntry: entry },
        { reopenSearchOnBack: false, startFlipped: true, focusExpression: cleanTarget }
    );
}

/**
 * Condense a sense context for display. The stored text is untouched; this is
 * only how it reads on the card.
 *
 * Measured over the Spanish speech and Bad Bunny lyrics decks — 3,389 contexts,
 * 1,524 distinct — two families account for nearly all the bulk while the
 * median context is already only 12 characters:
 *
 *   343 (10%)  exactly "multiword expression", every one of them on a row
 *              whose POS is already PHRASE, so it repeats the row's own label
 *   221 (7%)   open "used to …" / "used in …", averaging ~30 characters
 *
 * On a card where every context is a usage note, "used to" is a frame that
 * says nothing: "used to indicate origin" carries no more than "indicates
 * origin". Rewriting to the plain verb keeps the relation that "origin" alone
 * would lose. Together these cut context text by ~17%.
 */
function condenseSenseContext(raw) {
    const text = String(raw || '').trim();
    if (!text) return '';
    // The row's POS pill already reads PHRASE; repeating it as a context adds
    // a line of text to 343 rows and distinguishes none of them.
    //
    // TODO(pipeline): this belongs upstream, not here. The string is a
    // hardcoded placeholder from our own pipeline, not editorial content —
    // MULTIWORD_DEFINITION in src/fluency/wsd/multiword.py, written out by
    // release/run_candidate.py alongside part_of_speech: "PHRASE". Checked
    // against the shipped decks: all 343 come from source "mwe-merged" and
    // all 3,046 real contexts come from "spanishdict". Stop emitting it there
    // and this branch can go; deferred so it lands with a deck rebuild rather
    // than mid-session.
    if (text.toLowerCase() === 'multiword expression') return '';
    return readableSenseNote(text);
}

function cleanSenseContext(rawContext, mainGloss) {
    let raw = String(rawContext || '').trim();
    if (!raw) return '';
    const gloss = String(mainGloss || '').trim();
    if (!gloss) return raw;

    // 1. Deduplicate identical clauses separated by semicolons
    if (raw.includes(';')) {
        const clauses = raw.split(';').map(c => c.trim()).filter(Boolean);
        const seen = new Set();
        const deduped = [];
        for (const c of clauses) {
            const key = c.toLowerCase();
            if (!seen.has(key)) {
                seen.add(key);
                deduped.push(c);
            }
        }
        raw = deduped.join('; ');
    }

    const normRaw = raw.toLowerCase().replace(/^[^\w]+|[^\w]+$/g, '');
    const normGloss = gloss.toLowerCase().replace(/^[^\w]+|[^\w]+$/g, '');

    // 2. Direct identity or trivial punctuation/case difference, including
    // construction aliases such as intransitive / intr.
    if (normRaw === normGloss || metadataTextIsRedundant(raw, gloss)) return '';

    // 3. Exact substring match where gloss already encapsulates the entire context
    if (normGloss.includes(normRaw) && normGloss.length >= normRaw.length) return '';

    // 4. Context starts with the gloss, e.g. gloss: "to be", context: "to be located" -> "located"
    const glossRegex = new RegExp('^' + normGloss.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b\\s*[-:·]?\\s*', 'i');
    if (glossRegex.test(raw)) {
        raw = raw.replace(glossRegex, '').trim();
    } else if (normGloss.startsWith('to ')) {
        // Also handle infinitive "to X": e.g. gloss "to be", context "to be located" or gloss "be"
        const verbOnly = normGloss.slice(3).trim();
        const verbRegex = new RegExp('^(?:to\\s+)?' + verbOnly.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b\\s*[-:·]?\\s*', 'i');
        if (verbRegex.test(raw)) {
            raw = raw.replace(verbRegex, '').trim();
        }
    }

    // 5. Context starts with headword of gloss (e.g. gloss: "of", context: "of (being a part of)" -> "being a part of")
    const headGloss = normGloss.split(/[;,(]/)[0].trim();
    if (headGloss && headGloss.length >= 2) {
        const headRegex = new RegExp('^' + headGloss.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b\\s*[-:·;]?\\s*', 'i');
        if (headRegex.test(raw)) {
            raw = raw.replace(headRegex, '').trim();
        }
    }

    // 6. Unwrap outer parentheses if remaining text is enclosed: "(being a part of)" -> "being a part of"
    if (raw.startsWith('(') && raw.endsWith(')')) {
        raw = raw.slice(1, -1).trim();
    }

    // 7. "act of [gloss]" e.g. gloss: "wait", context: "act of waiting"
    if (/^act of\s+/i.test(raw)) {
        const afterAct = raw.replace(/^act of\s+/i, '').trim().toLowerCase();
        if (normGloss.startsWith(afterAct.slice(0, 4)) || afterAct.startsWith(normGloss.slice(0, 4))) {
            return '';
        }
    }

    // 9. If the remaining text is trivial (1 char or punctuation), discard it
    if (raw.replace(/[^\w]/g, '').length <= 1) return '';

    return raw;
}
window.cleanSenseContext = cleanSenseContext;

function renderSenseContextHTML(context, { leadingDot = true, gloss = null } = {}) {
    let raw = String(context || '').trim();
    if (!raw) return '';
    if (gloss) {
        raw = cleanSenseContext(raw, gloss);
        if (!raw) return '';
    }
    const usage = selectedLanguage === 'spanish'
        ? parseSpanishDictUsageContext(raw)
        : null;
    if (!usage) {
        // Condense after the usage parse, so the SpanishDict matcher still
        // sees the original wording.
        const shown = condenseSenseContext(raw);
        if (!shown) return '';
        return `<span class="meaning-context">${leadingDot ? '· ' : ''}${escapeCardText(shown)}</span>`;
    }

    const shownDetail = condenseSenseContext(usage.detail);
    const detail = shownDetail
        ? `<span class="meaning-context">${leadingDot ? '· ' : ''}${escapeCardText(shownDetail)}</span> `
        : '';
    const title = escapeCardText(`SpanishDict usage note: ${usage.raw}`);
    const label = escapeCardText(usage.label);
    return `${detail}<span class="meaning-usage-pill" data-source="spanishdict" title="${title}" aria-label="${title}"><span class="meaning-usage-label">${label}</span></span>`;
}

// Note: SENSE_CONSTRUCTION_TAGS, SENSE_REGISTER_TAGS, SENSE_CONSTRUCTION_SHORT,
// splitSenseMetadataClauses, compactConstructionMetadata, senseMetadataItems,
// senseMetadataDisplay, isSenseDefiningGrammar, isSupportingSenseMetadata,
// senseMetadataHTML, contextWithoutSenseMetadata, toggleSenseMetadataChip,
// and toggleSenseMetadataOverflow are now imported from ./card-metadata-pills.js


function highlightPossibleSpanishDictUsage(sentenceHTML, usage, targetWord = '') {
    const candidates = spanishDictUsageCandidateForms(usage);
    const target = String(targetWord || '').toLocaleLowerCase('es');
    let html = String(sentenceHTML || '');
    const protectedMatches = [];
    for (const form of candidates) {
        if (form.toLocaleLowerCase('es') === target) continue;
        const tokens = form.trim().split(/\s+/u).filter(Boolean);
        if (!tokens.length) continue;
        const body = tokens
            .map(token => token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
            .join('\\s+');
        const regex = _cachedRegex(
            `(?<![\\p{L}\\p{N}])(${body})(?![\\p{L}\\p{N}])(?![^<]*>)`,
            'giu'
        );
        html = html.replace(regex, (_whole, matched) => {
            const index = protectedMatches.length;
            protectedMatches.push(`<span class="example-usage-highlight" title="Possible match for this SpanishDict usage note; grammatical attachment is not verified">${matched}</span>`);
            // Protect a longer match such as `a por` from being re-matched by
            // its shorter alternatives (`por`, `a`) later in the same pass.
            return `\uE000${index}\uE001`;
        });
    }
    html = html.replace(/\uE000(\d+)\uE001/gu, (_whole, index) => protectedMatches[Number(index)] || '');
    return { html, candidates };
}

// Choose a type scale from the amount of visible copy in a sense row. Short
// glosses should use the room the card gives them; long glosses step down
// before the existing wrap/clamp rules take over. Considering both the
// longest individual fragment and the combined copy keeps bilingual MWE rows
// large when both halves are compact without letting a single long fragment
// dominate the row.
function adaptiveRowTextClass(...parts) {
    const fragments = parts
        .flat(Infinity)
        .filter(value => value !== null && value !== undefined)
        .map(value => String(value)
            .replace(/<[^>]*>/g, ' ')
            .replace(/&[a-z0-9#]+;/gi, ' ')
            .replace(/\s+/g, ' ')
            .trim())
        .filter(Boolean);
    const longest = fragments.reduce((max, value) => Math.max(max, value.length), 0);
    const combined = fragments.join(' ').length;
    const density = Math.max(longest, combined * 0.65);
    if (density <= 24) return 'row-text-xl';
    if (density <= 44) return 'row-text-lg';
    if (density <= 72) return 'row-text-md';
    return 'row-text-sm';
}

function getExampleProductionForm(card, meaning, example, targetSentence) {
    const sentence = String(targetSentence || '').replace(/<[^>]*>/g, '');
    if (!sentence || !card) return '';
    if (meaning?.allMWEs?.length) {
        const item = meaning.allMWEs[currentMWEIndex % meaning.allMWEs.length];
        return _matchedMweForm(
            item,
            sentence,
            example?.matched_surface || example?.matched_variant
        );
    }
    if (meaning?.allClitics?.length) {
        return meaning.allClitics[currentMWEIndex % meaning.allClitics.length]?.form || '';
    }

    const surface = String(
        example?.pooledFrom
        || card.representativeSurface
        || card.targetWord
        || ''
    ).trim();
    if (!surface) return '';
    const escaped = surface.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (card.isPronominal) {
        const withPronoun = _cachedRegex(
            `(?<![\\p{L}\\p{N}])((?:me|te|se|nos|os)\\s+${escaped})(?![\\p{L}\\p{N}])`,
            'iu'
        );
        const prefixed = sentence.match(withPronoun);
        if (prefixed) return prefixed[1];
        const enclitic = _cachedRegex(
            `(?<![\\p{L}\\p{N}])(${escaped}(?:me|te|se|nos|os))(?![\\p{L}\\p{N}])`,
            'iu'
        );
        const attached = sentence.match(enclitic);
        if (attached) return attached[1];
    }
    const exact = sentence.match(_cachedRegex(
        `(?<![\\p{L}\\p{N}])(${escaped})(?![\\p{L}\\p{N}])`,
        'iu'
    ));
    // The label says “In this example”, so do not invent a form when the
    // supplied sentence does not actually contain it.
    return exact ? exact[1] : '';
}

function buildFrontProductionHint(card, meaning, activeAnswer) {
    // The hint must blank the same surface the learner is expected to produce.
    // Merged-lemma and restored/elided cards can deliberately answer with a
    // different form from the example, so they wait for a future framed hint
    // rather than quietly changing the task under the learner.
    if (!card || !meaning || card.mergedLemma || !activeAnswer) return '';

    let examples;
    if (meaning.allMWEs?.length) {
        const active = meaning.allMWEs[currentMWEIndex % meaning.allMWEs.length];
        examples = active?.examples || [];
    } else if (meaning.allClitics?.length) {
        const active = meaning.allClitics[currentMWEIndex % meaning.allClitics.length];
        examples = active?.examples || [];
    } else {
        examples = getCyclableExamples(card, meaning);
    }
    examples = dedupeExamples(examples);
    if (examples.length > 1) examples = sortExamplesByRelevance(examples);
    const example = examples.length
        ? examples[currentExampleIndex % examples.length]
        : null;
    const sentence = stripAdlibParentheticals(
        example?.target || example?.spanish || meaning.targetSentence || card.targetSentence || ''
    );
    if (!sentence) return '';

    const answerInSentence = (meaning.allMWEs || meaning.allClitics || card.isPronominal)
        ? getExampleProductionForm(card, meaning, example, sentence)
        : (getExampleOccurrenceSurface(card, example, sentence)
            || getExampleProductionForm(card, meaning, example, sentence));
    if (!answerInSentence
        || foldSurfaceForm(answerInSentence) !== foldSurfaceForm(activeAnswer)) return '';

    const cloze = splitProductionCloze(sentence, answerInSentence);
    if (!cloze) return '';
    return `${escapeCardText(cloze.before)}<span class="production-cloze-blank" aria-label="missing Spanish answer">______</span>${escapeCardText(cloze.after)}`;
}

function getActiveProductionAnswer(card, meaning = null) {
    if (!card) return '';
    const activeMeaning = meaning
        || (card.isMultiMeaning ? card.meanings?.[currentMeaningIndex] : null);
    if (activeMeaning?.allMWEs?.length) {
        const item = activeMeaning.allMWEs[currentMWEIndex % activeMeaning.allMWEs.length];
        return item?.expression || card.productionAnswer || card.targetWord || '';
    }
    if (activeMeaning?.allClitics?.length) {
        const item = activeMeaning.allClitics[currentMWEIndex % activeMeaning.allClitics.length];
        return item?.form || card.productionAnswer || card.targetWord || '';
    }
    return card.productionAnswer || card.targetWord || '';
}

// A merged lemma remains one stable progress/rank card, but its teaching
// surface follows the currently displayed pooled example. Keep a lightweight
// in-session cursor so returning to a card advances through its evidence
// instead of always starting on the same inflection.
const _mergedExampleCursorByCard = new Map();

function getMergedLemmaExampleFocus(card, meaning, { advanceOnEntry = false } = {}) {
    if (!card?.mergedLemma || !meaning || meaning.allMWEs || meaning.allClitics) return null;

    const examples = getCyclableExamples(card, meaning);
    if (examples.length === 0) return null;

    const cursorKey = card.fullId || card.id || card.citationForm || card.targetWord;
    if (advanceOnEntry && examples.length > 1) {
        const previous = _mergedExampleCursorByCard.get(cursorKey);
        if (previous !== undefined) currentExampleIndex = (previous + 1) % examples.length;
    }
    const exampleIndex = currentExampleIndex % examples.length;
    const example = examples[exampleIndex];
    _mergedExampleCursorByCard.set(cursorKey, exampleIndex);

    // Resolve against the sentence rather than trusting `pooledFrom` alone.
    // When it is missing this used to fall through to the representative
    // surface and print a form the example does not contain — the header said
    // *buena* over a line reading *buenos*. The underline already checked the
    // sentence, so the two disagreed; now they are the same answer.
    const sentence = stripAdlibParentheticals(
        example?.target || example?.spanish || ''
    );
    const resolved = sentence
        ? resolveExampleOccurrence(card, example, sentence)
        : { surface: '', kind: 'none' };
    const surface = String(
        resolved.surface
        || example?.pooledFrom
        || card.representativeSurface
        || card.targetWord
        || card.displaySurface
        || ''
    ).trim();
    const isRepresentative = foldSurfaceForm(surface)
        === foldSurfaceForm(card.representativeSurface || card.targetWord);
    const morphology = example?.pooledMorphology
        || (isRepresentative ? card.morphology : null);
    return { example, examples, surface, morphology };
}

function getDisplayedTargetHeadword(card) {
    if (!card) return '';
    if (!isFlipped && card.mergedLemma && card._activeExampleSurface) {
        return card._activeExampleSurface;
    }
    return card.displaySurface || card.targetWord;
}

function isTrivialPlural(surface, canonical) {
    const form = foldSurfaceForm(surface);
    const base = foldSurfaceForm(canonical);
    if (!form || !base || form === base) return false;
    return form === `${base}s`
        || form === `${base}es`
        || (base.endsWith('z') && form === `${base.slice(0, -1)}ces`);
}

function isTrivialElision(surface, canonical) {
    const rawSurface = String(surface || '').trim();
    if (!/[’']$/.test(rawSurface)) return false;
    const shortened = foldSurfaceForm(rawSurface.slice(0, -1));
    const full = foldSurfaceForm(canonical);
    // Covers transparent final-letter drops such as vamos -> vamo' and
    // después -> despué'. More substantial forms such as para -> pa' and
    // todo -> to' remain visible because they are worth learning.
    return shortened.length > 0
        && full.startsWith(shortened)
        && full.length - shortened.length === 1;
}

function isTrivialCanonicalRelation(surface, canonical) {
    return isTrivialPlural(surface, canonical)
        || isTrivialElision(surface, canonical);
}

// Surface spellings belong in their example sentence, where the exact
// occurrence is highlighted. Only these deliberately reviewed restorations
// need a persistent cue beside the card's own word; generic variants,
// conjugation families, plurals, and transparent final-letter drops must not
// replace the headword again.
const NOTABLE_SURFACE_RELATIONS = Object.freeze({
    para: "pa'",
    nada: "na'",
    cometamos: "cometamo'",
});

function relationSurfaceKey(value) {
    return foldSurfaceForm(value).replace(/[’']/g, '');
}

function getNotableSurfaceRelation(card) {
    if (!card || card.mergedLemma) return null;
    const canonical = String(card.targetWord || card.displaySurface || '').trim();
    const surface = NOTABLE_SURFACE_RELATIONS[foldSurfaceForm(canonical)];
    const recorded = String(card.displayForm || '').trim();
    if (!surface || !recorded
        || relationSurfaceKey(recorded) !== relationSurfaceKey(surface)) {
        return null;
    }
    return { surface, canonical };
}

// ---------------------------------------------------------------------------
// Phrase / clitic chaining — MWE/CLITIC entries leave the card's pinned tray
// and are studied as standalone child cards immediately after the parent is
// ---------------------------------------------------------------------------
// Phrase / clitic chaining — Invariant MWEs (deterministic bypass) and CLITIC
// entries leave the card's pinned tray / scroll view and are studied as
// standalone child cards immediately after the parent is marked correct.
// Ambiguous MWEs (competitive WSD) stay on the primary card back.
// Bound root cards (e.g. "repente", "obstante") whose ONLY meanings are
// invariant MWEs keep the phrase on the card back so the card is never blank.
// ---------------------------------------------------------------------------

function isInvariantMweMeaning(meaning) {
    if (!meaning) return false;
    if (meaning.pos === 'MWE') return true;
    if (meaning.pos === 'PHRASE' || meaning.part_of_speech === 'PHRASE') {
        const ev = meaning.metadata?.multiword_evidence?.[0];
        if (ev) {
            return ev.wsd_routing === 'deterministic_bypass' || ev.route === 'invariant';
        }
        if (meaning.wsd_routing === 'deterministic_bypass' || meaning.route === 'invariant') return true;
    }
    return false;
}

function isAmbiguousMweMeaning(meaning) {
    if (!meaning) return false;
    if (meaning.pos === 'PHRASE' || meaning.part_of_speech === 'PHRASE') {
        const ev = meaning.metadata?.multiword_evidence?.[0];
        if (ev) {
            return ev.wsd_routing === 'competitive_wsd' || ev.route === 'ambiguous';
        }
        if (meaning.wsd_routing === 'competitive_wsd' || meaning.route === 'ambiguous') return true;
    }
    return false;
}

function cardHasOnlyInvariantMwes(card) {
    if (!card || !Array.isArray(card.meanings) || !card.meanings.length) return false;
    return card.meanings.every(m => isInvariantMweMeaning(m));
}

// Ordered list of chainable children for a real deck card. Source of truth
// is card.meanings entries for invariant MWEs/CLITICs. Chain-child cards
// themselves are excluded — their single MWE/CLITIC meaning is the card's
// own content, not something to chain further.
function collectChainItems(card) {
    if (!card || card.isChainChild) return [];
    if (cardHasOnlyInvariantMwes(card)) return [];
    return (card.meanings || [])
        .map((m, idx) => ({ m, idx }))
        .filter(({ m }) => m.pos === 'MWE' || m.pos === 'CLITIC' || isInvariantMweMeaning(m))
        .flatMap(({ m, idx }) => {
            const list = m.allMWEs || m.allClitics || [m];
            return list.map((item, sub) => {
                const ev = item.metadata?.multiword_evidence?.[0];
                const expr = item.expression || item.form || item.headword || ev?.expression || '';
                const trans = item.translation || item.meaning || m.meaning || m.translation || ev?.translation || '';
                const ctx = item.context || item.context_heuristic || '';
                const src = item.source || ev?.sources?.[0] || 'mwe-merged';
                const exs = item.examples || item.allExamples || m.allExamples || m.examples || [];
                return {
                    parentCard: card,
                    parentWord: card.displaySurface || card.targetWord || card.word || '',
                    meaningIndex: idx,
                    subIndex: sub,
                    kind: m.pos === 'CLITIC' ? 'CLITIC' : 'MWE',
                    expression: expr,
                    translation: trans,
                    context: ctx,
                    source: src,
                    examples: exs
                };
            });
        })
        .filter(c => c.expression);
}

function collectExpressionItems(card) {
    if (!card || card.isChainChild) return [];
    const chainItems = collectChainItems(card);
    if (chainItems.length > 0) return chainItems;
    if (Array.isArray(card.mwe_memberships) && card.mwe_memberships.length > 0) {
        return card.mwe_memberships.map((mwe, sub) => ({
            parentCard: card,
            parentWord: card.displaySurface || card.targetWord,
            meaningIndex: -1,
            subIndex: sub,
            kind: 'MWE',
            expression: mwe.expression || '',
            translation: mwe.translation || '',
            context: mwe.context || '',
            source: mwe.source || '',
            examples: mwe.examples || []
        })).filter(c => c.expression);
    }
    return [];
}

function collectRareSenseItems(card) {
    if (!card || card.isChainChild) return [];
    const qualifying = typeof getQualifyingRareSenses === 'function' ? getQualifyingRareSenses(card) : [];
    const seenSenseIds = new Set();
    const items = [];

    for (const q of qualifying) {
        const id = q.senseId || q.sense_id || '';
        if (id) seenSenseIds.add(id);
        const trans = q.meaning || q.translation || '';
        if (!trans) continue;
        const ex = typeof extractCanonicalDictionaryExamples === 'function'
            ? extractCanonicalDictionaryExamples(q)
            : [];
        items.push({
            parentCard: card,
            parentWord: card.displaySurface || card.targetWord,
            kind: 'RARE_SENSE',
            senseId: id,
            pos: q.pos || '',
            translation: trans,
            context: q.context || '',
            examples: ex.length > 0 ? ex : (q.canonicalExample ? [q.canonicalExample] : [])
        });
    }

    if (Array.isArray(card.unusedMenuSenses)) {
        for (const unused of card.unusedMenuSenses) {
            const id = unused.senseId || unused.sense_id || '';
            if (id && seenSenseIds.has(id)) continue;
            const trans = unused.meaning || unused.translation || '';
            if (!trans) continue;
            if (id) seenSenseIds.add(id);
            const ex = typeof extractCanonicalDictionaryExamples === 'function'
                ? extractCanonicalDictionaryExamples(unused)
                : [];
            items.push({
                parentCard: card,
                parentWord: card.displaySurface || card.targetWord,
                kind: 'RARE_SENSE',
                senseId: id,
                pos: unused.pos || '',
                translation: trans,
                context: unused.context || '',
                examples: ex.length > 0 ? ex : (unused.canonicalExample ? [unused.canonicalExample] : [])
            });
        }
    }
    return items;
}

function collectRareAndExpressionItems(card) {
    if (!card || card.isChainChild) return [];
    const expressions = collectExpressionItems(card);
    const rareSenses = collectRareSenseItems(card);
    return [...expressions, ...rareSenses];
}

// Builds the synthetic card rendered after the parent — one card holding
// every rare sense and phrase/clitic together in a scrollable list.
function phraseSummaryCard(items) {
    const parent = items[0]?.parentCard;
    const word = items[0]?.parentWord || parent?.displaySurface || parent?.targetWord || '';
    const hasRare = items.some(item => item.kind === 'RARE_SENSE');
    const hasExpr = items.some(item => item.kind && item.kind !== 'RARE_SENSE');
    const kind = hasRare && hasExpr ? 'rare_and_expressions'
        : hasRare ? 'rare_senses'
        : 'expressions';
    return {
        id: `${parent?.id || 'synthetic'}::${kind}`,
        isChainChild: true,
        chainChildKind: kind,
        chainParentWord: word,
        targetWord: word,
        isMultiMeaning: true,
        meanings: [],
        links: {}
    };
}

// Dedicated back-face template for the phrase-summary card — every item's
// badge/expression/translation/example stacked in one scrollable column.
// Deliberately does not go through the shared meaning-row renderer: that
// renderer assumes fields (m.expression, m.allClitics) a synthesized
// meaning doesn't carry, which silently produced "undefined" text.
function exampleTargetText(example) {
    if (!example) return '';
    return example.target || example.spanish || example.swedish
        || example.dutch || example.italian || example.polish || '';
}

// The base verb every attached form on this card shares. Taken from the parent
// card's lemma/citation rather than the form's own stem, so an infinitive
// (`alejarme`) and a gerund (`alejándome`) stay in one block instead of
// splitting into `alejar` and `alejando`.
function cliticBaseVerb(item) {
    const parent = item?.parentCard;
    const raw = String(parent?.lemma || parent?.citationForm || parent?.targetWord
        || item?.parentWord || '').trim().toLocaleLowerCase('es');
    const base = raw.replace(/((?:ar|er|ir))se$/u, '$1');
    return base || splitAttachedClitics(item?.expression).stem;
}

// Highlights the exact attached form inside its lyric. Escaping happens first,
// so the inserted markup is the only HTML in the string.
function highlightAttachedForm(sentence, form) {
    const safe = escapeCardText(sentence);
    const token = String(form || '').trim();
    if (!token) return safe;
    try {
        const pattern = token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        return safe.replace(new RegExp(`(${pattern})`, 'giu'),
            '<strong class="clitic-form-hit">$1</strong>');
    } catch (e) {
        return safe;
    }
}

// Open/close one part-of-speech group on the card back. State lives on the
// card, not the DOM, because selecting a sense re-renders — a DOM-only toggle
// would close the group the moment you clicked a row inside it.
function toggleBackPosSection(key) {
    const card = flashcards?.[currentIndex];
    if (!card) return;
    // The group key is POS + NUL + headword; NUL cannot survive an inline
    // onclick attribute, so it travels as ~~ and is restored here.
    const real = String(key).replace(/~~/g, '\u0000');
    if (!card._expandedPos) card._expandedPos = new Set();
    // Once the learner expresses a preference, preserve it. The automatic
    // "open everything if it fits" pass is only a first-presentation default.
    card._backSectionsManuallySet = true;
    if (card._expandedPos.has(real)) card._expandedPos.delete(real);
    else card._expandedPos.add(real);
    updateCard();
}
window.toggleBackPosSection = toggleBackPosSection;

function lemmaPosGroupKeyForMeaning(meaning) {
    if (!meaning) return '';
    const pos = meaning.pos === 'SENSE_CYCLE'
        ? (meaning.cycle_pos || 'X')
        : meaning.pos;
    return `${pos || 'X'}\u0000${meaning.headword || ''}`;
}

// A lemma–POS heading is a selection control, not only an accordion label.
// Switching it moves the card's complete active state (lemma, sense, examples,
// and POS colour) in one operation. The selected group is always left open so
// a chosen low-frequency sense cannot disappear behind a collapsed section.
function selectLemmaPosGroup(event, key, meaningIndex) {
    event?.stopPropagation();
    stopExampleAutoplay(true);
    const card = flashcards?.[currentIndex];
    const meaning = card?.meanings?.[meaningIndex];
    if (!card || !meaning) return;
    const real = String(key).replace(/~~/g, '\u0000');
    card._backSectionsManuallySet = true;
    card._expandedPos = card._expandedPos || new Set();
    if (card._expandedPos.has(real)) {
        card._expandedPos.delete(real);
    } else {
        card._expandedPos.add(real);
    }

    const alreadyActive = lemmaPosGroupKeyForMeaning(card.meanings[currentMeaningIndex]) === real
        && !currentGroupSelection;
    if (alreadyActive) return;

    currentGroupSelection = null;
    currentMeaningIndex = meaningIndex;
    const selectedPos = meaning.pos === 'SENSE_CYCLE'
        ? (meaning.cycle_pos || 'X')
        : meaning.pos;
    if (selectedPos) card._activePosTab = selectedPos;
    currentExampleIndex = 0;
    currentMWEIndex = 0;
    _explicitMeaningSelectionKey = meaningSelectionKey(card, meaningIndex);
    updateCard();
}
window.selectLemmaPosGroup = selectLemmaPosGroup;

// Rendering order is stable. Selecting a lower-frequency sense changes only
// its highlight; when the meaning region genuinely overflows, the layout pass
// scrolls that stable row into view. Reordering on every selection made short,
// fully visible menus jump even though no navigation assistance was needed.
function orderMeaningEntriesForDisplay(meanings) {
    return (meanings || []).map((meaning, index) => ({ meaning, index }));
}

// Normalize source evidence once. Fresh releases retain the complete typed
// record under metadata.source.document; older decks put the same fields
// directly in example.provenance. Supporting both here prevents presentation
// code from silently losing IMDb evidence during a schema migration.
function normalizedExampleProvenance(example) {
    const legacy = example?.provenance && typeof example.provenance === 'object'
        ? example.provenance : {};
    const source = example?.metadata?.source || {};
    const document = source.document || {};
    const target = example?.metadata?.target || {};
    return {
        corpus: legacy.corpus || source.name || example?.source || '',
        title_id: legacy.title_id || document.title_id || '',
        subtitle_id: legacy.subtitle_id || document.subtitle_id || '',
        line: legacy.line || document.line || '',
        source_title: example?.source_title || example?.metadata?.source_title || null,
        source_record_id: example?.source_record_id || source.source_record_id || '',
        url: example?.source_url || example?.sentence_url || source.url || target.url || '',
        attribution: example?.attribution || source.attribution || '',
        contributor: example?.contributor || target.contributor || '',
        license: example?.license || source.license || '',
    };
}

function sourceTitleRecord(provenance) {
    const attached = provenance?.source_title;
    if (attached && attached.title) return attached;
    const titleId = provenance?.title_id;
    if (!titleId || !_sourceTitles) return null;
    return _sourceTitles[titleId] || _sourceTitles[String(titleId)] || null;
}

function sourceTitleLabel(provenance) {
    const metadata = sourceTitleRecord(provenance);
    if (!metadata) return '';
    // Learner-facing credit is the work people recognise: the series or film.
    // Episode titles and years live on the IMDb page behind the link.
    if (metadata.series) return String(metadata.series).trim();
    return String(metadata.title || '').trim();
}

let _sourceTitles = null;
let _sourceTitlesPromise = null;

async function loadSourceTitles() {
    if (_sourceTitles) return _sourceTitles;
    if (_sourceTitlesPromise) return _sourceTitlesPromise;
    const path = (typeof config !== 'undefined' && config?.sourceTitlesPath)
        || 'data/source_titles.json';
    _sourceTitlesPromise = fetch(path).then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        _sourceTitles = await response.json();
        return _sourceTitles;
    }).catch((error) => {
        console.warn('Source titles unavailable:', error);
        _sourceTitles = {};
        return _sourceTitles;
    }).finally(() => {
        _sourceTitlesPromise = null;
    });
    return _sourceTitlesPromise;
}

function exampleLinkHTML(href, label) {
    if (!href) return escapeCardText(label);
    return outboundChipHTML(href, escapeCardText(label), label);
}

const OUTBOUND_LEAVE_ICON = `<svg class="outbound-leave-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`;

function outboundLeaveButton(href, label) {
    return `<button type="button" class="outbound-leave-btn" hidden data-href="${escapeCardText(href)}" aria-label="Open ${escapeCardText(label)} in a new tab" onclick="event.stopPropagation(); confirmOutboundLink(event);">${OUTBOUND_LEAVE_ICON}</button>`;
}

function outboundChipHTML(href, inner, label, attrs = '') {
    return `<button type="button" ${attrs} data-href="${escapeCardText(href)}" aria-expanded="false" onclick="event.stopPropagation(); armOutboundLink(event)">${inner}${outboundLeaveButton(href, label)}</button>`;
}

function disarmOutboundLinks(exceptHost = null) {
    document.querySelectorAll('.is-armed-outbound').forEach(host => {
        if (host === exceptHost) return;
        host.classList.remove('is-armed-outbound');
        host.setAttribute('aria-expanded', 'false');
        host.querySelectorAll('.outbound-leave-btn').forEach(btn => { btn.hidden = true; });
    });
}

function armOutboundLink(event) {
    const host = event.currentTarget;
    if (event.target.closest('.outbound-leave-btn')) return;
    const leave = host.querySelector('.outbound-leave-btn');
    if (!leave) return;
    const opening = leave.hidden;
    disarmOutboundLinks(opening ? host : null);
    leave.hidden = !opening;
    host.classList.toggle('is-armed-outbound', opening);
    host.setAttribute('aria-expanded', String(opening));
    if (opening) {
        setTimeout(() => {
            document.addEventListener('click', function dismiss(e) {
                if (!host.contains(e.target)) disarmOutboundLinks();
                document.removeEventListener('click', dismiss);
            });
        }, 0);
    }
}

function confirmOutboundLink(event) {
    event.stopPropagation();
    const href = event.currentTarget?.dataset?.href
        || event.currentTarget?.closest('[data-href]')?.dataset?.href;
    if (href) window.open(href, '_blank', 'noopener,noreferrer');
    disarmOutboundLinks();
}

if (typeof window !== 'undefined') {
    window.armOutboundLink = armOutboundLink;
    window.confirmOutboundLink = confirmOutboundLink;
}

function exampleFaviconHTML(domain) {
    const localIcon = {
        'tatoeba.org': 'icons/tatoeba.svg',
        'wiktionary.org': 'icons/wikipedia-w.svg',
    }[domain];
    const src = localIcon || `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`;
    const className = domain === 'wiktionary.org' ? ' example-source-favicon--wikipedia' : '';
    return `<img class="example-source-favicon dict-provenance-icon${className}" src="${src}" width="34" height="34" alt="" aria-hidden="true">`;
}

function exampleSourceChipHTML({ href, label, domain, text = '', extraClass = '' }) {
    const icon = domain ? exampleFaviconHTML(domain) : '';
    const named = Boolean(text);
    const classes = [
        'example-source-chip',
        named ? 'example-source-chip--named' : 'example-source-chip--icon',
        extraClass,
    ].filter(Boolean).join(' ');
    const title = named ? `${text}` : label;
    // Icon first. The mark says where the line came from; the title is the
    // detail that follows it, and it is the part that gets truncated, so
    // putting the icon after it meant a long title pushed the icon off.
    const inner = `${icon}${named ? `<span class="example-source-text">${escapeCardText(text)}</span>` : ''}`;
    const attrs = `class="${classes}" title="${escapeCardText(title)}" aria-label="${escapeCardText(named ? `${text} on ${label}` : label)}"`;
    if (!href) return `<span ${attrs}>${inner}</span>`;
    return outboundChipHTML(href, inner, named ? `${text} on ${label}` : label, attrs);
}

function dictionaryProviderCredit(name, href) {
    const raw = String(name || '').trim();
    const lower = raw.toLowerCase();
    if (lower.includes('spanishdict')) {
        return exampleSourceChipHTML({
            href,
            label: 'SpanishDict',
            domain: 'spanishdict.com',
            extraClass: 'dictionary-provenance-badge',
        });
    }
    if (lower.includes('wiktionary') || lower.includes('kaikki')) {
        return exampleSourceChipHTML({
            href,
            label: 'Wiktionary',
            domain: 'wiktionary.org',
            extraClass: 'dictionary-provenance-badge',
        });
    }
    return exampleSourceChipHTML({
        href,
        label: raw || 'Dictionary',
        domain: 'wiktionary.org',
        extraClass: 'dictionary-provenance-badge',
    });
}

function dictionaryProviderForMeaning(meaning) {
    const meta = meaning?.metadata || {};
    if (meta?.sense_provider_metadata?.spanishdict) return 'SpanishDict';
    const raw = String(meta.source_provider || meaning?.source || '').toLowerCase();
    if (raw.includes('spanishdict')) return 'SpanishDict';
    if (raw.includes('wiktionary') || raw.includes('kaikki')) return 'Wiktionary';
    return 'Dictionary';
}

// Where a corpus example actually came from. Every displayed sentence should
// name its source: OpenSubtitles with a film/series title when the IMDb map
// has one, Tatoeba with a sentence link, or the dictionary that filed it.
function exampleProvenanceHTML(example) {
    const p = normalizedExampleProvenance(example);
    const corpus = String(p?.corpus || '').toLowerCase();
    if (corpus === 'opensubtitles' || p.title_id) {
        if (p.title_id) {
            const tt = 'tt' + String(p.title_id).padStart(7, '0');
            const title = sourceTitleLabel(p);
            return exampleSourceChipHTML({
                href: `https://www.imdb.com/title/${tt}/`,
                label: 'IMDb',
                domain: 'imdb.com',
                text: title,
            });
        }
        return exampleSourceChipHTML({
            label: 'OpenSubtitles',
            domain: 'opensubtitles.org',
        });
    }
    if (corpus === 'tatoeba') {
        return exampleSourceChipHTML({
            href: p.url,
            label: 'Tatoeba',
            domain: 'tatoeba.org',
        });
    }
    if (corpus === 'wiktionary') {
        return dictionaryProviderCredit('Wiktionary', p.url);
    }
    if (corpus === 'spanishdict') {
        return dictionaryProviderCredit('SpanishDict', p.url);
    }
    if (corpus) return escapeCardText(corpus);
    return null;
}

function cliticExampleHTML(example, form) {
    const target = exampleTargetText(example);
    if (!target) return '';
    const englishHTML = example.english
        ? `<div class="phrase-example-translation">${escapeCardText(example.english)}</div>` : '';
    return `<div class="phrase-example clitic-example">
            <div class="phrase-example-target">${highlightAttachedForm(target, form)}</div>
            ${englishHTML}
        </div>`;
}

// One block per base verb: a neutral `verb + pronominal` header (we cannot tell
// reflexive from dative reliably, so the header must not claim either) over one
// row per attached pronoun. Each row keeps its own translation and its own
// examples — the granularity is the point, so nothing is collapsed or picked as
// a winner. Grading identity is untouched: rows still address the same
// cardChainQueue entries by index.
function renderCliticGroup(base, entries) {
    const rows = entries.map(({ item, index }) => {
        const detail = describeCliticForm(
            { form: item.expression, translation: item.translation }, item.parentCard);
        const { clitics } = splitAttachedClitics(item.expression);
        const rowKey = clitics.join('') || item.expression;
        const examples = item.examples || [];
        const first = examples[0];
        const more = examples.slice(1).filter(ex => exampleTargetText(ex));
        const translation = detail.displayTranslation || item.translation || '';
        // Everything describeCliticForm() knows stays on the row: the exact
        // attached form plus verb shape / person / case / English role.
        const roleDetail = [item.expression, detail.visualDetail].filter(Boolean).join(' · ');
        const toggle = more.length
            ? `<button type="button" class="clitic-more-toggle" aria-expanded="false"
                    aria-controls="cliticMore${index}" data-more-label="+${more.length} more"
                    onclick="toggleCliticExamples(event, ${index})">+${more.length} more</button>`
            : '';
        return `<div class="clitic-row">
            <div class="clitic-row-head">
                <span class="clitic-row-key">${escapeCardText(rowKey)}:</span>
                <span class="clitic-row-translation">${translation
                    ? escapeCardText(translation)
                    : '<em>Translation unavailable</em>'}</span>
                ${toggle}
            </div>
            ${roleDetail ? `<div class="clitic-row-detail">${escapeCardText(roleDetail)}</div>` : ''}
            ${first ? cliticExampleHTML(first, item.expression) : ''}
            ${more.length ? `<div class="clitic-more" id="cliticMore${index}" hidden>${
                more.map(ex => cliticExampleHTML(ex, item.expression)).join('')}</div>` : ''}
        </div>`;
    }).join('');
    return `<div class="phrase-summary-item clitic-group">
        <span class="phrase-kind-badge pos-clitic">PRONOMINAL</span>
        <div class="phrase-expression clitic-group-title">${escapeCardText(base)}<span class="clitic-group-suffix"> + pronominal</span></div>
        <div class="clitic-group-rows">${rows}</div>
    </div>`;
}

function toggleCliticExamples(event, index) {
    event?.stopPropagation();
    const panel = document.getElementById(`cliticMore${index}`);
    if (!panel) return;
    const opening = panel.hidden;
    panel.hidden = !opening;
    const button = event?.currentTarget;
    if (!button) return;
    button.setAttribute('aria-expanded', String(opening));
    button.textContent = opening ? 'Show less' : (button.dataset.moreLabel || 'More');
}

// --- Phrase provenance pill (JST-only diagnostic) ---------------------------
//
// Where a phrase row actually came from, stamped into the deck at assembly
// time (step_8a_assemble_vocabulary / step_8b_assemble_artist_vocabulary) —
// the front end never reads the layer files, so this is the only place the
// answer survives. It is a build-quality diagnostic, not learner content, so
// it is scoped to the owner account exactly like the report icon and the
// App-data settings tab.
//
// Deliberately a single letter: the phrase row already carries a PHRASE badge,
// the expression, its gloss and an example, and a second word-shaped label
// there would read as content.
const PHRASE_SOURCE_PILLS = {
    'wiktionary': { letter: 'W', label: 'Wiktionary phrase list', theme: 'wiktionary' },
    // Pre-stamp alias: step_2a copied shared-layer phrases through with
    // source "shared" back when only the SpanishDict builder stamped itself.
    // That layer was Wiktionary-only, so the letter is the same.
    'shared': { letter: 'W', label: 'Wiktionary phrase list (legacy tag)', theme: 'wiktionary' },
    'spanishdict': { letter: 'S', label: 'SpanishDict phrase page', theme: 'spanishdict' },
    'artist-pmi-lexicon': { letter: 'C', label: 'Corpus collocation (PMI, glossed)', theme: 'corpus' },
    'artist-pmi-candidate': { letter: 'C', label: 'Corpus collocation (PMI)', theme: 'corpus' },
    'artist-curated': { letter: 'K', label: 'Curated conjugation family', theme: 'curated' },
    'artist-construction': { letter: 'T', label: 'Construction template', theme: 'construction' },
};

function phraseSourcePillHTML(item) {
    if (!window.isAuditAccount?.()) return '';
    const raw = String(item?.source || '').trim().toLowerCase();
    if (!raw) return '';
    // Unknown/legacy tags render nothing rather than guessing. A wrong
    // provenance letter is worse than an absent one.
    const pill = PHRASE_SOURCE_PILLS[raw];
    if (!pill) return '';
    return `<span class="phrase-source-pill phrase-source-${pill.theme}" title="${escapeCardText(pill.label)}"
        aria-label="Source: ${escapeCardText(pill.label)}">${pill.letter}</span>`;
}

function posDisplayName(pos) {
    const labels = {
        NOUN: 'Noun', VERB: 'Verb', AUX: 'Auxiliary', ADJ: 'Adjective', ADV: 'Adverb',
        PREP: 'Preposition', ADP: 'Preposition', CONJ: 'Conjunction', CCONJ: 'Conjunction',
        SCONJ: 'Conjunction', PRON: 'Pronoun', DET: 'Determiner', INTJ: 'Interjection',
        NUM: 'Number', PROPN: 'Proper noun'
    };
    return labels[String(pos || '').toUpperCase()]
        || String(pos || '').toLowerCase().replace(/^./, char => char.toUpperCase());
}

function rareSenseFieldKey(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';
    const text = typeof senseSummaryText === 'function' ? senseSummaryText(raw) : raw;
    return text
        .toLocaleLowerCase('en')
        .replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '')
        .replace(/\s+/g, ' ')
        .trim() || raw.toLocaleLowerCase('en');
}

function rareSenseGlossKey(item) {
    return rareSenseFieldKey(item?.translation || item?.expression);
}

function rareSenseContextKey(item) {
    return rareSenseFieldKey(item?.context);
}

function clusterRareSenses(items) {
    const n = items.length;
    const parent = items.map((_, i) => i);
    const find = (i) => (parent[i] === i ? i : (parent[i] = find(parent[i])));
    const union = (a, b) => {
        a = find(a);
        b = find(b);
        if (a !== b) parent[b] = a;
    };
    for (let i = 0; i < n; i++) {
        const glossI = rareSenseGlossKey(items[i]);
        const ctxI = rareSenseContextKey(items[i]);
        for (let j = i + 1; j < n; j++) {
            const glossJ = rareSenseGlossKey(items[j]);
            const ctxJ = rareSenseContextKey(items[j]);
            if ((glossI && glossI === glossJ) || (ctxI && ctxI === ctxJ)) union(i, j);
        }
    }
    const groups = new Map();
    items.forEach((item, i) => {
        const root = find(i);
        if (!groups.has(root)) groups.set(root, []);
        groups.get(root).push(item);
    });
    return [...groups.values()];
}

function compactPhraseExampleHTML(example, posAccentRgb) {
    const target = exampleTargetText(example) || example?.text || example?.targetSentence || '';
    if (!target) return '';
    const english = example?.english || example?.translation || example?.englishSentence || '';
    const englishHTML = english
        ? `<div class="phrase-example-translation">${escapeCardText(english)}</div>` : '';
    const accent = posAccentRgb || 'var(--accent-primary-rgb)';
    return `<div class="phrase-example phrase-example--compact" style="--sense-match-rgb: ${accent};">
            <div class="phrase-example-target">${escapeCardText(target)}</div>
            ${englishHTML}
        </div>`;
}

function rareSenseLeafHTML(item, posAccentRgb, { hideGloss = false, hideContext = false } = {}) {
    const gloss = item.translation || item.expression || '';
    const example = (item.examples || [])[0];
    const exampleHTML = compactPhraseExampleHTML(example, posAccentRgb);
    const glossHTML = (!hideGloss && gloss)
        ? `<div class="other-uses-gloss">${escapeCardText(gloss)}</div>` : '';
    const ctxHTML = (!hideContext && item.context)
        ? `<div class="phrase-context">${escapeCardText(item.context)}</div>` : '';
    if (!glossHTML && !ctxHTML && !exampleHTML) return '';
    return `<div class="other-uses-leaf">${glossHTML}${ctxHTML}${exampleHTML}</div>`;
}

function cycleRarerShade(event, clusterKey, count, delta) {
    event?.stopPropagation?.();
    const card = flashcards?.[currentIndex];
    if (!card || !count) return;
    const scroller = document.querySelector('#backContent .phrase-summary-scroll');
    const top = scroller?.scrollTop || 0;
    if (!card._rarerShade) card._rarerShade = {};
    const cur = Number(card._rarerShade[clusterKey] || 0);
    card._rarerShade[clusterKey] = ((cur + Number(delta || 1)) % count + count) % count;
    updateCard();
    requestAnimationFrame(() => {
        const again = document.querySelector('#backContent .phrase-summary-scroll');
        if (again) again.scrollTop = top;
    });
}
if (typeof window !== 'undefined') window.cycleRarerShade = cycleRarerShade;

function renderRareSenseCluster(group, pos, posAccentRgb, clusterId) {
    const unique = (values) => {
        const seen = new Set();
        return values.filter((value) => {
            if (!value || seen.has(value)) return false;
            seen.add(value);
            return true;
        });
    };
    const glosses = unique(group.map((item) => String(item.translation || item.expression || '').trim()));
    const contexts = unique(group.map((item) => String(item.context || '').trim()));
    const sharedGloss = glosses.length === 1 ? glosses[0] : '';
    const sharedContext = contexts.length === 1 ? contexts[0] : '';

    if (group.length === 1) {
        return `<div class="other-uses-gloss-group">${rareSenseLeafHTML(group[0], posAccentRgb)}</div>`;
    }

    // Same gloss and same context: one block, cycle the dictionary examples.
    if (sharedGloss && (sharedContext || contexts.length === 0)) {
        const shade = Number((flashcards?.[currentIndex]?._rarerShade || {})[clusterId] || 0) % group.length;
        const item = group[shade];
        const pager = group.length > 1
            ? `<div class="rarer-uses-pager">
                <button type="button" aria-label="Previous matching sense" onclick="event.stopPropagation(); cycleRarerShade(event, '${clusterId}', ${group.length}, -1)">‹</button>
                <span>${shade + 1} / ${group.length}</span>
                <button type="button" aria-label="Next matching sense" onclick="event.stopPropagation(); cycleRarerShade(event, '${clusterId}', ${group.length}, 1)">›</button>
               </div>`
            : '';
        return `<div class="rarer-uses-cluster" style="--sense-match-rgb: ${posAccentRgb};">
            <div class="rarer-uses-cluster-meta">Matching senses</div>
            <div class="other-uses-gloss">${escapeCardText(sharedGloss)}</div>
            ${sharedContext ? `<div class="phrase-context">${escapeCardText(sharedContext)}</div>` : ''}
            ${compactPhraseExampleHTML((item.examples || [])[0], posAccentRgb)}
            ${pager}
        </div>`;
    }

    const head = sharedGloss
        ? `<div class="other-uses-gloss">${escapeCardText(sharedGloss)}</div>`
        : (sharedContext ? `<div class="phrase-context">${escapeCardText(sharedContext)}</div>` : '');
    const leaves = group.map((item) => rareSenseLeafHTML(item, posAccentRgb, {
        hideGloss: Boolean(sharedGloss),
        hideContext: Boolean(sharedContext),
    })).join('');
    return `<div class="rarer-uses-cluster" style="--sense-match-rgb: ${posAccentRgb};">
        <div class="rarer-uses-cluster-meta">${sharedGloss ? 'Same gloss' : (sharedContext ? 'Same context' : 'Linked senses')}</div>
        ${head}
        ${leaves}
    </div>`;
}

function renderRareSenseGroups(rareItems) {
    const byPos = new Map();
    for (const item of rareItems) {
        const pos = String(item.pos || 'OTHER').toUpperCase();
        if (!byPos.has(pos)) byPos.set(pos, []);
        byPos.get(pos).push(item);
    }
    const posOrder = ['NOUN', 'VERB', 'AUX', 'ADJ', 'ADV', 'PREP', 'ADP', 'PRON', 'DET', 'CONJ', 'CCONJ', 'SCONJ', 'INTJ', 'NUM', 'PROPN'];
    const posKeys = [...byPos.keys()].sort((a, b) => {
        const ia = posOrder.indexOf(a);
        const ib = posOrder.indexOf(b);
        return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib) || a.localeCompare(b);
    });
    return posKeys.map(pos => {
        const clusters = clusterRareSenses(byPos.get(pos));
        const posAccentRgb = getPosAccentRgb(pos);
        const groups = clusters.map((group, index) => {
            const clusterId = `${pos}-${index}`;
            return renderRareSenseCluster(group, pos, posAccentRgb, clusterId);
        }).join('');
        return `<section class="other-uses-pos">
            <h4 class="other-uses-pos-heading" style="color: rgb(${posAccentRgb});">${escapeCardText(posDisplayName(pos))}</h4>
            ${groups}
        </section>`;
    }).join('');
}

function renderPhraseRow(item) {
    const example = (item.examples || [])[0];
    const exampleHTML = compactPhraseExampleHTML(example);
    return `<div class="phrase-summary-item">
        <div class="phrase-badge-row"><span class="phrase-kind-badge">PHRASE</span>${phraseSourcePillHTML(item)}</div>
        <div class="phrase-expression">${escapeCardText(item.expression)}</div>
        ${item.translation ? `<div class="phrase-translation">${escapeCardText(item.translation)}</div>` : ''}
        ${item.context ? `<div class="phrase-context">${escapeCardText(item.context)}</div>` : ''}
        ${exampleHTML}
    </div>`;
}

function renderPhraseSummaryBack(card) {
    const items = cardChainQueue || [];
    const cliticGroups = new Map();
    items.forEach((item, index) => {
        if (item.kind !== 'CLITIC') return;
        const base = cliticBaseVerb(item);
        if (!cliticGroups.has(base)) cliticGroups.set(base, []);
        cliticGroups.get(base).push({ item, index });
    });
    const emittedGroups = new Set();
    const cliticHTML = items.map(item => {
        if (item.kind !== 'CLITIC') return '';
        const base = cliticBaseVerb(item);
        if (emittedGroups.has(base)) return '';
        emittedGroups.add(base);
        return renderCliticGroup(base, cliticGroups.get(base));
    }).join('');
    const phraseItems = items.filter(item => item.kind !== 'CLITIC' && item.kind !== 'RARE_SENSE');
    const rareItems = items.filter(item => item.kind === 'RARE_SENSE');
    const phraseHTML = phraseItems.length
        ? `<section class="other-uses-pos">
            <h4 class="other-uses-pos-heading">Expressions</h4>
            ${phraseItems.map(renderPhraseRow).join('')}
           </section>`
        : '';
    const rareHTML = rareItems.length ? renderRareSenseGroups(rareItems) : '';

    const rareCount = rareItems.length;
    const phraseCount = items.length - rareCount;
    const bits = [];
    if (rareCount) bits.push(`${rareCount} rarer sense${rareCount === 1 ? '' : 's'}`);
    if (phraseCount) bits.push(`${phraseCount} expression${phraseCount === 1 ? '' : 's'}`);
    let subtitle;
    if (rareCount && !phraseCount) {
        subtitle = `Rarer senses — meanings that show up less often in speech${bits.length ? ` · ${bits.join(' · ')}` : ''}`;
    } else if (phraseCount && !rareCount) {
        subtitle = `Expressions that use this word${bits.length ? ` · ${bits.join(' · ')}` : ''}`;
    } else {
        subtitle = `Rarer uses — senses that show up less often in speech${bits.length ? ` · ${bits.join(' · ')}` : ''}`;
    }
    const rareKnowledgeButton = rareCount && typeof currentUser !== 'undefined' && currentUser && !currentUser.isGuest
        ? '<button type="button" class="rare-knowledge-btn" onclick="openRareSenseKnowledge(event)">Mark rarer senses Known or Review</button>'
        : '';

    return `<div class="back-header other-uses-header">
            <div class="back-headword-row">
                <span class="back-headword other-uses-headword">${escapeCardText(card.chainParentWord || '')}</span>
            </div>
            <div class="phrase-summary-subtitle">${subtitle}</div>
        </div>
        ${rareKnowledgeButton}
        <div class="phrase-summary-scroll">${rareHTML}${phraseHTML}${cliticHTML}</div>`;
}

function openRareSenseKnowledge(event) {
    event?.stopPropagation();
    const parent = cardChainQueue.find(item => item.kind === 'RARE_SENSE')?.parentCard;
    if (parent) window.showKnowledgeOverview?.(event, { card: parent, showRare: true });
}
if (typeof window !== 'undefined') window.openRareSenseKnowledge = openRareSenseKnowledge;

// ---------------------------------------------------------------------------
// Backup example sentences — the second chain child.
//
// Sense-free corpus sentences built by tool_5a_build_backup_examples, sharded
// by deck position so opening the list costs one fetch per level rather than
// one per card. Nothing here consults sense assignment; a sentence is attached
// to a word, so this survives sense-assignment rework untouched.
// ---------------------------------------------------------------------------
const _backupExampleShards = new Map();   // shard index -> {wordId: [sentence]}
let _backupExampleManifest = null;
let _backupExampleShardById = null;       // wordId -> shard index
let _backupExampleUnavailable = false;

// Always the language directory, never the artist one. Artist decks share the
// same word-id space as the language deck (4,479 of 4,481 overlapping ids
// resolve to the same word), so a lyrics card can read the language's corpus
// sentences directly — which is the point: a lyrics deck is often thin even on
// common words, and seeing a word used outside it is most of the value.
function backupExampleBaseDir() {
    const indexPath = config?.languages?.[selectedLanguage]?.indexPath || '';
    return indexPath.slice(0, indexPath.lastIndexOf('/') + 1);
}

// Resolves shards by word id, not by deck position. Position arithmetic only
// held for the deck the shards were built from: an artist deck orders the same
// ids differently, so the derived shard was wrong and the card silently showed
// nothing. The id map costs ~44 KB gzipped once per session.
async function loadBackupExampleShardForIds(wordIds) {
    if (_backupExampleUnavailable || !wordIds.length) return null;
    const base = backupExampleBaseDir();
    if (!base) return null;
    try {
        if (!_backupExampleShardById) {
            const manifestResponse = await fetch(`${base}vocabulary.backup_examples.index.json`);
            if (!manifestResponse.ok) throw new Error(`HTTP ${manifestResponse.status}`);
            _backupExampleManifest = await manifestResponse.json();
            const indexFile = _backupExampleManifest.shardIndexFile;
            if (!indexFile) throw new Error('manifest has no shardIndexFile');
            const indexResponse = await fetch(`${base}${indexFile}`);
            if (!indexResponse.ok) throw new Error(`HTTP ${indexResponse.status}`);
            _backupExampleShardById = await indexResponse.json();
        }
        // A merged lemma family can straddle shards, so gather every shard the
        // requested ids land in.
        const needed = new Set();
        for (const id of wordIds) {
            const shard = _backupExampleShardById[id];
            if (shard !== undefined) needed.add(shard);
        }
        if (needed.size === 0) return {};
        const merged = {};
        for (const shardIndex of needed) {
            let payload = _backupExampleShards.get(shardIndex);
            if (!payload) {
                const entry = (_backupExampleManifest.shards || [])
                    .find(item => item.shard === shardIndex);
                if (!entry) continue;
                const response = await fetch(`${base}${entry.file}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                payload = await response.json();
                _backupExampleShards.set(shardIndex, payload);
            }
            Object.assign(merged, payload);
        }
        return merged;
    } catch (error) {
        // A missing layer is not an error worth blocking study for — the child
        // simply doesn't offer itself.
        console.warn('Backup examples unavailable:', error);
        _backupExampleUnavailable = true;
        return null;
    }
}

// What navigateBack() will land on from the current child card, phrased for
// the top-bar return control. The nav stack holds either a popup-only frame
// (nothing underneath — back means the setup panel) or the index of the card
// the detour started from.
function describeNavReturnTarget() {
    const previous = cardNavStack[cardNavStack.length - 1];
    if (!previous) return 'the set';
    if (previous.popupOnly) return previous.wasOnSetup ? 'the menu' : 'the set';
    const parent = flashcards[previous.index];
    const word = parent?.displaySurface || parent?.targetWord || '';
    return word || 'the set';
}

// id → source vocabulary entry, over the full unfiltered array. Core owns it
// because updateCard()'s homograph chips resolve sibling ids through it and
// goBackToSetup() clears it; the lazy lyric-breakdown module is a second
// consumer and reaches it through the window export below. The cache itself
// is a state.js entry so both files see the same one.
function getVocabByIdLookup() {
    if (vocabByIdLookup) return vocabByIdLookup;
    if (!cachedVocabularyData) return new Map();
    vocabByIdLookup = new Map();
    for (const entry of cachedVocabularyData) {
        if (entry.id) vocabByIdLookup.set(entry.id, entry);
    }
    return vocabByIdLookup;
}

// In Merge Lemmas mode the card stands for the whole lemma family, so pool the
// siblings' sentences the way poolLemmaSiblingExamples does for sense examples.
function backupExampleIdsFor(card) {
    const ids = [card.id].filter(Boolean);
    if (!card.mergedLemma || !card.lemma) return ids;
    // The full source array, not the filtered deck: siblings of a merged lemma
    // are excluded from the deck by definition, and their sentences are
    // exactly what pooling is after.
    const source = cachedVocabularyData || [];
    for (const item of source) {
        if (item.lemma === card.lemma && item.id && !ids.includes(item.id)) ids.push(item.id);
    }
    return ids;
}

async function collectBackupExamples(card) {
    // Retired: WSD and authentic example scaling supersede un-disambiguated backup sentences.
    return [];
}

function examplesChildCard(parentCard) {
    return {
        id: `${parentCard.id}::examples`,
        isChainChild: true,
        chainChildKind: 'examples',
        chainParentWord: parentCard.displaySurface || parentCard.targetWord,
        targetWord: parentCard.targetWord,
        isMultiMeaning: true,
        meanings: [],
        links: {}
    };
}

function renderExamplesChildBack(card) {
    const sentences = cardChainExamples;
    if (!sentences.length) {
        return `<div class="back-header">
                <div class="back-headword-row">
                    <span class="back-headword" style="font-size: 32px; font-weight: bold;">${escapeCardText(card.chainParentWord || '')}</span>
                </div>
                <div class="phrase-summary-subtitle">No corpus sentences for this word yet</div>
            </div>`;
    }
    const rows = sentences.map((sentence, index) => {
        // Collapsed, a row is the sentence plus the words the learner has not
        // met yet, glossed inline — that is the part they cannot work out for
        // themselves. Expanding adds the sentence translation, which they can
        // often infer once the unknown words are named.
        const glosses = Array.isArray(sentence.new) ? sentence.new : [];
        const newHTML = glosses.length
            ? `<div class="wild-new"><span class="wild-new-label">New words:</span>
                    ${glosses.map(([word, translation]) => `<span class="wild-gloss-item">
                        <span class="wild-gloss-word">${escapeCardText(word)}</span>
                        <span class="wild-gloss-translation">${escapeCardText(translation)}</span>
                    </span>`).join('')}
               </div>`
            : '';
        return `<button type="button" class="wild-row" aria-expanded="false" onclick="revealWildTranslation(event, ${index})">
            <div class="wild-target">${escapeCardText(sentence.target)}</div>
            ${newHTML}
            <div class="wild-reveal" id="wildReveal${index}" hidden>
                <div class="wild-english">${escapeCardText(sentence.english)}</div>
            </div>
        </button>`;
    }).join('');
    return `<div class="back-header">
            <div class="back-headword-row">
                <span class="back-headword" style="font-size: 32px; font-weight: bold; line-height: 1.1;">${escapeCardText(card.chainParentWord || '')}</span>
            </div>
            <div class="phrase-summary-subtitle">${sentences.length} sentence${sentences.length === 1 ? '' : 's'} in the wild · tap for the translation</div>
        </div>
        <div class="phrase-summary-scroll wild-scroll">${rows}</div>`;
}

function revealWildTranslation(event, index) {
    event?.stopPropagation();
    const panel = document.getElementById(`wildReveal${index}`);
    if (!panel) return;
    const opening = panel.hidden;
    panel.hidden = !opening;
    const row = event.currentTarget;
    row?.classList.toggle('is-revealed', opening);
    row?.setAttribute('aria-expanded', String(opening));
}

// Shows the summary card: appends it as a temp card (search-popup pattern)
// and remembers the parent's real deck index so finishing resumes at
// parent+1 directly. Deliberately does NOT use cardNavStack/navigateBack —
// returning to the parent card left it unflipped and ungraded-looking, so a
// swipe there re-triggered collectChainItems and started an identical
// summary card again (an infinite loop). Finishing now behaves like the
// parent's own correct swipe just kept going before reaching the next card.
// The ordered plan for one parent card. Phrases come first because they are
// graded content the learner owes an answer on; the sentence list is reading,
// so it reads better as the last thing before moving on. A child that has
// nothing to show is simply absent from the plan.
async function buildCardChildren(card) {
    const children = [];
    if (expressionsModeEnabled) {
        const expressions = collectExpressionItems(card);
        if (expressions.length > 0) children.push({ type: 'phrases', items: expressions });
    }
    if (rareSensesModeEnabled) {
        const rareSenses = collectRareSenseItems(card);
        if (rareSenses.length > 0) children.push({ type: 'phrases', items: rareSenses });
    }
    return children;
}

function startCardChain(children) {
    cardChainChildren = children;
    cardChainIndex = -1;
    cardChainReturnIndex = currentIndex;
    // The temp slot is appended once and reused by each child in turn, so the
    // deck length is the same whichever child is showing and the scrubber's
    // flashcards.length - 1 arithmetic holds throughout.
    flashcards.push(null);
    advanceCardChain();
}

// Swaps the temp slot to the next child, or unwinds the chain when the plan is
// exhausted. Returns false once there is nothing left to show.
function advanceCardChain() {
    const parentCard = flashcards[cardChainReturnIndex];
    cardChainIndex += 1;
    const child = cardChainChildren[cardChainIndex];
    if (!child || !parentCard) return false;

    cardChainQueue = child.type === 'phrases' ? child.items : [];
    cardChainExamples = child.type === 'examples' ? child.sentences : [];

    const tempIndex = flashcards.length - 1;
    flashcards[tempIndex] = child.type === 'phrases'
        ? phraseSummaryCard(child.items)
        : examplesChildCard(parentCard);

    currentIndex = tempIndex;
    currentMeaningIndex = 0;
    currentExampleIndex = 0;
    currentMWEIndex = 0;
    currentGroupSelection = null;
    // Chain children have no front face worth showing — the prompt was the
    // parent word the learner just answered. Open straight onto the back
    // rather than asking for a flip that reveals nothing new. flipCard() also
    // refuses to turn a chain card back over.
    document.getElementById('flashcard').classList.add('flipped');
    updateCard({ announceHeadword: true });
    return true;
}

// Records one item's grade against the same per-meaning knowledge store the
// tray rows wrote to (knowledge.js), keyed on the parent card + the
// meaning/cycle index the item came from.
function recordChainChildResult(item, isCorrect) {
    if (typeof knowledgeItemsForMeaning !== 'function' || typeof saveKnowledgeProgress !== 'function') return;
    const parentCard = item.parentCard;
    const meaning = parentCard?.meanings?.[item.meaningIndex];
    if (!meaning) return;
    const knowledgeItems = knowledgeItemsForMeaning(parentCard, meaning, item.meaningIndex)
        .filter(k => k.cycleIndex === item.subIndex);
    if (knowledgeItems.length === 0) return;
    saveKnowledgeProgress(parentCard, knowledgeItems, isCorrect);
}

// Leaves the chain without grading it — the learner scrubbed to another card
// instead of swiping the summary. The temp card must come off `flashcards` on
// the way out or it survives as a phantom slot at the end of the deck (and, in
// the scrubber, as an unreachable extra number). Always the last element, so
// splicing it cannot shift any real card's index.
function abandonPhraseChain() {
    if (!flashcards[currentIndex]?.isChainChild) return;
    flashcards.splice(currentIndex, 1);
    cardChainQueue = [];
    cardChainExamples = [];
    cardChainChildren = [];
    cardChainIndex = 0;
    cardChainReturnIndex = -1;
}

// Grades every phrase in the summary at once (the single swipe covers the
// whole card) and resumes exactly where the parent would have left off had
// it not had any phrases — the next real deck card, or end-of-deck.
function finishPhraseChain(isCorrect) {
    // If opened on-demand via cardNavStack, return to parent card
    if (cardNavStack.length > 0) {
        navigateBack();
        return;
    }

    // Only phrases/expressions carry gradeable items; rare dictionary senses
    // are unassigned so swiping them records no meaning progress.
    for (const item of cardChainQueue) {
        if (item.kind !== 'RARE_SENSE') {
            recordChainChildResult(item, isCorrect);
        }
    }

    // Hand over to the next child before unwinding, so a word with both
    // phrases and sentences shows them in sequence off one parent answer.
    if (advanceCardChain()) return;

    const tempIndex = currentIndex;
    flashcards.splice(tempIndex, 1);
    const resumeIndex = cardChainReturnIndex + 1;
    cardChainQueue = [];
    cardChainExamples = [];
    cardChainChildren = [];
    cardChainIndex = 0;
    cardChainReturnIndex = -1;

    if (resumeIndex < flashcards.length) {
        currentIndex = resumeIndex;
        currentSentenceIndex = 0;
        currentMeaningIndex = 0;
        currentExampleIndex = 0;
        currentMWEIndex = 0;
        currentGroupSelection = null;
        document.getElementById('flashcard').classList.remove('flipped');
        updateCard({ announceHeadword: true });
    } else {
        showEndOfDeckOptions();
    }
}

// On-demand trigger from the card back: opens rare senses and expressions
// as an interactive peek/child card pushed onto cardNavStack.
function openRareAndExpressionsCard(event) {
    event?.stopPropagation?.();
    const parentCard = flashcards[currentIndex];
    if (!parentCard) return;
    const items = collectRareAndExpressionItems(parentCard);
    if (!items.length) return;

    cardChainQueue = items;
    cardChainExamples = [];
    cardChainReturnIndex = currentIndex;

    const tempChild = phraseSummaryCard(items);
    const tempIndex = flashcards.length;

    cardNavStack.push({
        index: currentIndex,
        meaningIndex: currentMeaningIndex,
        exampleIndex: currentExampleIndex,
        mweIndex: currentMWEIndex,
        tempCard: true,
        tempIndex: tempIndex,
        wasFlipped: true
    });

    flashcards.push(tempChild);
    currentIndex = tempIndex;
    currentMeaningIndex = 0;
    currentExampleIndex = 0;
    currentMWEIndex = 0;
    currentGroupSelection = null;

    document.getElementById('flashcard').classList.add('flipped');
    updateCard({ announceHeadword: true });
}
window.openRareAndExpressionsCard = openRareAndExpressionsCard;

function canonicalRecord(meaning) {
    if (!meaning) return null;
    if (meaning.pos === 'SENSE_CYCLE' && meaning.allSenses?.length) {
        const item = meaning.allSenses[currentMWEIndex % meaning.allSenses.length]
            || meaning.allSenses[0];
        return item?.canonicalExample || item?.canonical_example || null;
    }
    return meaning.canonicalExample || meaning.canonical_example || null;
}

function highlightWithDeclaredOffsets(text, offsets) {
    const raw = String(text || '');
    if (!raw) return '';
    const ranges = (Array.isArray(offsets) ? offsets : [])
        .map(item => Array.isArray(item) ? [Number(item[0]), Number(item[1])] : null)
        .filter(item => (
            item
            && Number.isFinite(item[0])
            && Number.isFinite(item[1])
            && item[1] > item[0]
            && item[0] >= 0
            && item[1] <= raw.length
        ))
        .sort((a, b) => a[0] - b[0]);
    if (!ranges.length) return escapeCardText(raw);
    let html = '';
    let cursor = 0;
    for (const [start, end] of ranges) {
        if (start < cursor) continue;
        html += escapeCardText(raw.slice(cursor, start));
        html += `<span class="example-word-highlight">${escapeCardText(raw.slice(start, end))}</span>`;
        cursor = end;
    }
    html += escapeCardText(raw.slice(cursor));
    return html;
}

function canonicalExampleHTML(meaning) {
    const canonical = canonicalRecord(meaning);
    const text = String(canonical?.text || '').trim();
    const translation = String(canonical?.translation || canonical?.english || '').trim();
    if (!text || !translation) return '';
    return `<div class="sentence canonical-example">
        <div class="breakdown-trigger" style="margin-bottom: 8px;">${highlightWithDeclaredOffsets(text, canonical.bold_text_offsets)}</div>
        <div class="translation">${highlightWithDeclaredOffsets(translation, canonical.bold_translation_offsets)}</div>
        <div class="example-credit-row" style="display: flex; justify-content: flex-end; align-items: center; font-size: 13px; margin-top: 8px;">
            <span class="example-song-credit" style="margin-right:auto;">${dictionaryProviderCredit(dictionaryProviderForMeaning(meaning), canonical?.url)}</span>
        </div>
    </div>`;
}

function extractCanonicalDictionaryExamples(meaning) {
    const canonical = canonicalRecord(meaning);
    const text = String(canonical?.text || canonical?.target || canonical?.spanish || '').trim();
    const translation = String(canonical?.translation || canonical?.english || '').trim();
    if (text && translation) {
        return [{
            target: text,
            english: translation,
            targetSentence: text,
            englishSentence: translation,
            source: 'dictionary',
            evidence: 'dictionary',
            dictionarySource: dictionaryProviderForMeaning(meaning),
            canonical: true,
            url: canonical.url,
            bold_text_offsets: canonical.bold_text_offsets,
            bold_translation_offsets: canonical.bold_translation_offsets,
        }];
    }
    const meta = meaning?.metadata;
    const isSd = Boolean(
        meta?.sense_provider_metadata?.spanishdict?.examples
        || meta?.sense_metadata?.source_metadata?.spanishdict?.examples
    );
    const examples = meta?.sense_provider_metadata?.spanishdict?.examples
        || meta?.sense_metadata?.source_metadata?.spanishdict?.examples
        || meta?.source_metadata?.examples
        || [];
    if (!Array.isArray(examples)) return [];
    const dictName = isSd ? 'SpanishDict' : (meta?.source_provider || meaning?.source || 'Wiktionary');
    return examples.map(ex => ({
        target: ex.original || ex.target || ex.spanish || '',
        english: ex.translated || ex.english || '',
        targetSentence: ex.original || ex.target || ex.spanish || '',
        englishSentence: ex.translated || ex.english || '',
        source: dictName.toLowerCase(),
        evidence: 'dictionary',
        dictionarySource: dictName,
        canonical: true
    })).filter(ex => ex.target && ex.english);
}

// Default sentence (tick 1): a corpus line when WSD `supported_level` is
// leaf, glosskey, or tuple; otherwise the dictionary canonical if it exists.
// Always preserve the canonical dictionary example in the cycling sequence.
const WSD_EXAMPLE_LEVEL_RANK = { leaf: 3, glosskey: 2, tuple: 1 };

function exampleWsdMeta(example) {
    return example?.metadata?.wsd || example?.wsd || null;
}

function exampleWsdLevel(example) {
    return exampleWsdMeta(example)?.supported_level || null;
}

function isCorpusDisplayExample(example) {
    return Boolean(
        example
        && !example.canonical
        && example.evidence !== 'dictionary'
        && !example.reference_example
    );
}

function isReliableWsdExample(example) {
    if (!isCorpusDisplayExample(example)) return false;
    const target = String(example.target || example.spanish || '').trim();
    const english = String(example.english || '').trim();
    if (!target || !english) return false;
    // assignment_method on these rows is the corpus name (tatoeba /
    // opensubtitles), not a WSD verdict. Only supported_level is the gate.
    return Boolean(WSD_EXAMPLE_LEVEL_RANK[exampleWsdLevel(example)]);
}

// One ordering, not two. This used to sort by relevance and then re-sort by
// supported_level, silently discarding the first result; confidence is now a
// key inside sortExamplesByRelevance instead.
function rankConfidentWsdExamples(examples) {
    const reliable = (examples || []).filter(isReliableWsdExample);
    if (!reliable.length) return [];
    return sortExamplesByRelevance([...reliable]);
}

function canonicalAsDisplayExample(meaning) {
    const extracted = extractCanonicalDictionaryExamples(meaning);
    if (extracted && extracted.length > 0) return extracted[0];
    return null;
}

function findCanonicalForCard(card, meaning) {
    if (meaning) {
        const direct = canonicalAsDisplayExample(meaning);
        if (direct) return direct;
    }
    if (card) {
        if (card.canonicalExample || card.canonical_example) {
            const cardCan = canonicalAsDisplayExample(card);
            if (cardCan) return cardCan;
        }
        if (Array.isArray(card.meanings)) {
            for (const m of card.meanings) {
                const ex = canonicalAsDisplayExample(m);
                if (ex) return ex;
            }
        }
        if (Array.isArray(card.unusedMenuSenses)) {
            for (const u of card.unusedMenuSenses) {
                const ex = canonicalAsDisplayExample(u);
                if (ex) return ex;
            }
        }
    }
    return null;
}

function exampleLooksLikeLyric(example) {
    return Boolean(
        example?.song_name
        || example?.artist
        || example?.timestamp_ms != null
        || example?.spotify_available
    );
}

function examplesAllowCycling(examples) {
    if (typeof activeArtist !== 'undefined' && activeArtist) return true;
    return (examples || []).some(exampleLooksLikeLyric);
}

function displayExamplesForSense(meaning, examples, card = null) {
    const corpus = (examples || []).filter(isCorpusDisplayExample);
    const confident = rankConfidentWsdExamples(corpus);
    const activeCard = card || (typeof flashcards !== 'undefined' && flashcards ? flashcards[currentIndex] : null);
    const canonical = findCanonicalForCard(activeCard, meaning);

    const isSameText = (a, b) => {
        if (!a || !b) return false;
        const norm = s => String(s || '').trim().toLowerCase().replace(/[.,/#!$%^&*;:{}=\-_`~()?"'«»¡¿]/g, '');
        return norm(a.target || a.spanish || a.targetSentence) === norm(b.target || b.spanish || b.targetSentence);
    };

    // The canonical dictionary line is the SECOND example, not the last. It is
    // the dictionary's own illustration of this exact sense, so it is the right
    // thing to reach for once the best real sentence has been shown — but it is
    // not a neutral fallback: 9.3% of canonical lines run to two sentences and
    // only 44.6% contain the card's own surface form, so it never leads while a
    // usable corpus line exists.
    if (confident.length) {
        const result = [...confident];
        if (canonical && !result.some(ex => isSameText(ex, canonical))) {
            result.splice(1, 0, canonical);
        }
        return result;
    }

    if (canonical) {
        const others = (corpus.length > 1 ? sortExamplesByRelevance(corpus) : corpus)
            .filter(ex => !isSameText(ex, canonical));
        return [canonical, ...others];
    }

    return corpus.length > 1 ? sortExamplesByRelevance(corpus) : corpus;
}

function chooseSingleDisplayExample(meaning, examples, card = null) {
    return displayExamplesForSense(meaning, examples, card)[0] || null;
}

function getQualifyingRareSenses(card) {
    if (!card || !Array.isArray(card.unusedMenuSenses)) return [];
    if (!card._cachedQualifyingRareSenses) {
        card._cachedQualifyingRareSenses = card.unusedMenuSenses.filter(unused => {
            const examples = extractCanonicalDictionaryExamples(unused);
            return examples.length > 0 && (unused.meaning || unused.translation);
        }).map(unused => {
            const firstEx = extractCanonicalDictionaryExamples(unused)[0];
            const canonical = unused.canonicalExample || unused.canonical_example || {
                text: firstEx.target,
                translation: firstEx.english,
            };
            return {
                ...unused,
                meaning: unused.meaning || unused.translation || '',
                unassigned: false,
                isRareSense: true,
                percentage: 0,
                prominenceLabel: 'Rare',
                canonicalExample: canonical,
                targetSentence: unused.targetSentence || '',
                englishSentence: unused.englishSentence || '',
                allExamples: unused.allExamples || [],
            };
        });
    }
    return card._cachedQualifyingRareSenses;
}

function getSenseProminenceInfo(meaning) {
    if (meaning.prominenceLabel) {
        const label = String(meaning.prominenceLabel).trim();
        return { label, key: label.toLowerCase() };
    }
    if (meaning.unassigned || meaning.isRareSense) {
        return { label: 'Rare', key: 'rare' };
    }
    return prominenceInfoFromShare([meaning]);
}

// Learner-facing frequency is the share of a meaning cluster, not the WSD
// mass of one dictionary shade. Near-synonym leaves (fantastic / brilliant)
// must not fight Common vs Rare; sum the assigned members and bucket once.
// 4-category scale: Rare (unassigned/dictionary-only), Uncommon (0-20%),
// Common (20-60%), Dominant (>= 60%).
function prominenceInfoFromShare(meanings) {
    const list = Array.isArray(meanings) ? meanings.filter(Boolean) : [];
    const used = list.filter(m => !m.unassigned && !m.isRareSense);
    if (!used.length) return { label: 'Rare', key: 'rare' };
    const p = used.reduce((acc, m) => acc + (Number(m.percentage) || 0), 0);
    if (p <= 0) return { label: 'Rare', key: 'rare' };
    if (p >= 0.60) return { label: 'Dominant', key: 'dominant' };
    if (p >= 0.20) return { label: 'Common', key: 'common' };
    return { label: 'Uncommon', key: 'uncommon' };
}

// A leaf is separable inside a shared gloss only when, after renormalising
// scores onto those siblings, one shade clearly wins. Full-menu confidence
// is the wrong number: most of that gap is a different meaning. Prefer
// per-leaf model confidence when at least two siblings carry it; otherwise
// committed usage share is the available proxy.
const GLOSS_LEAF_DOMINANCE = 0.70;
const GLOSS_LEAF_MARGIN = 0.35;

function glossClusterKey(card, meaning) {
    if (!meaning || meaning.exampleOnly) return null;
    const pos = meaning.pos === 'SENSE_CYCLE' ? (meaning.cycle_pos || 'X') : meaning.pos;
    if (!pos || pos === 'MWE' || pos === 'CLITIC' || pos === 'EXAMPLE_ONLY') return null;
    const raw = String(getProductionEnglishCue(card, meaning) || meaning.meaning || meaning.translation || '').trim();
    const gloss = senseSummaryText(projectWiktionaryGloss(meaning, raw).display)
        .toLocaleLowerCase('en')
        .replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '')
        .replace(/\s+/g, ' ')
        .trim();
    if (!gloss) return null;
    return `${pos}\u0000${meaning.headword || ''}\u0000${gloss}`;
}

function contextClusterKey(card, meaning) {
    if (!meaning || meaning.exampleOnly) return null;
    const pos = meaning.pos === 'SENSE_CYCLE' ? (meaning.cycle_pos || 'X') : meaning.pos;
    if (!pos || pos === 'MWE' || pos === 'CLITIC' || pos === 'EXAMPLE_ONLY') return null;
    const rawCtx = String(meaning.context || '').trim();
    if (!rawCtx) return null;
    const ctx = senseSummaryText(rawCtx)
        .toLocaleLowerCase('en')
        .replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '')
        .replace(/\s+/g, ' ')
        .trim();
    if (!ctx) return null;
    return `${pos}\u0000${meaning.headword || ''}\u0000ctx:${ctx}`;
}

function withinGlossLeafWeight(meaning, useConfidence) {
    if (!meaning || meaning.unassigned || meaning.isRareSense) return 0;
    if (useConfidence) {
        const confidence = Number(meaning.confidence);
        return Number.isFinite(confidence) && confidence > 0 ? confidence : 0;
    }
    return Number(meaning.percentage) || 0;
}

function withinGlossLeafSeparationIsReliable(meanings) {
    const list = (Array.isArray(meanings) ? meanings : []).filter(m => m && !m.unassigned && !m.isRareSense);
    if (list.length < 2) return false;
    const confidenceCount = list.filter(m => Number.isFinite(Number(m.confidence)) && Number(m.confidence) > 0).length;
    if (confidenceCount < 2) {
        // Without calibrated per-leaf model confidence, raw assignment counts
        // between near-synonym leaves under a shared gloss or context are
        // classifier artifacts (e.g. "error" vs "mistake"). Do not split them
        // into Common vs Rare on usage share alone.
        return false;
    }
    const weights = list.map(m => withinGlossLeafWeight(m, true));
    const total = weights.reduce((acc, weight) => acc + weight, 0);
    if (total <= 0) return false;
    const shares = weights.map(weight => weight / total).sort((a, b) => b - a);
    return shares[0] >= GLOSS_LEAF_DOMINANCE && (shares[0] - (shares[1] || 0)) >= GLOSS_LEAF_MARGIN;
}

function glossClusterProminenceState(card) {
    const groups = new Map();
    (card?.meanings || []).forEach((meaning, index) => {
        const key = glossClusterKey(card, meaning);
        if (key) {
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(index);
        }
        const ctxKey = contextClusterKey(card, meaning);
        if (ctxKey) {
            if (!groups.has(ctxKey)) groups.set(ctxKey, []);
            if (!groups.get(ctxKey).includes(index)) groups.get(ctxKey).push(index);
        }
    });
    const infoByIndex = new Map();
    const pooledIndexes = new Set();
    const pooledShareByIndex = new Map();
    for (const indexes of groups.values()) {
        const members = indexes.map(index => card.meanings[index]);
        const pooled = indexes.length >= 2 && !withinGlossLeafSeparationIsReliable(members);
        const pooledInfo = prominenceInfoFromShare(members);
        const pooledShare = members.reduce((acc, meaning) => acc + (Number(meaning.percentage) || 0), 0);
        indexes.forEach(index => {
            const meaning = card.meanings[index];
            if (meaning.isRareSense || (meaning.prominenceLabel === 'Rare' && !pooled)) {
                infoByIndex.set(index, getSenseProminenceInfo(meaning));
                return;
            }
            if (pooled) {
                pooledIndexes.add(index);
                infoByIndex.set(index, pooledInfo);
                pooledShareByIndex.set(index, pooledShare);
            } else if (!pooledIndexes.has(index)) {
                infoByIndex.set(index, getSenseProminenceInfo(meaning));
            }
        });
    }
    return { infoByIndex, pooledIndexes, pooledShareByIndex };
}
window.prominenceInfoFromShare = prominenceInfoFromShare;
window.withinGlossLeafSeparationIsReliable = withinGlossLeafSeparationIsReliable;
window.glossClusterProminenceState = glossClusterProminenceState;
window.getSenseProminenceInfo = getSenseProminenceInfo;

const PROMINENCE_BLURBS = {
    dominant: 'used most often',
    common: 'used often',
    uncommon: 'used sometimes',
    rare: 'used rarely',
};

function prominenceMeterHTML(key) {
    const filled = key === 'dominant' ? 4 : key === 'common' ? 3 : key === 'uncommon' ? 2 : 1;
    return `<span class="sense-prominence-meter" aria-hidden="true">${[1, 2, 3, 4].map(i => `<i${i <= filled ? ' class="is-on"' : ''}></i>`).join('')}</span>`;
}

function prominenceBadgeHTML(promInfo, extraStyle = '') {
    if (!promInfo) return '';
    const key = promInfo.key || 'rare';
    const label = promInfo.label || 'Rare';
    const blurb = PROMINENCE_BLURBS[key] || PROMINENCE_BLURBS.rare;
    const style = extraStyle ? ` style="${extraStyle}"` : '';
    return `<span class="sense-prominence-badge prominence-${escapeCardText(key)}"${style} role="button" tabindex="0" aria-expanded="false" aria-label="${escapeCardText(label)}. Tap to explain." onclick="toggleProminenceBadge(event, this)" onkeydown="if (event.key === 'Enter' || event.key === ' ') toggleProminenceBadge(event, this)">${prominenceMeterHTML(key)}<span class="sense-prominence-detail">${escapeCardText(label)} · ${escapeCardText(blurb)}</span></span>`;
}

function toggleProminenceBadge(event, button) {
    event?.stopPropagation?.();
    event?.preventDefault?.();
    if (!button) return;
    const open = button.getAttribute('aria-expanded') === 'true';
    document.querySelectorAll('.sense-prominence-badge[aria-expanded="true"]').forEach(el => {
        if (el !== button) el.setAttribute('aria-expanded', 'false');
    });
    button.setAttribute('aria-expanded', open ? 'false' : 'true');
}
window.prominenceBadgeHTML = prominenceBadgeHTML;
window.toggleProminenceBadge = toggleProminenceBadge;

// True when at least one sense on this card would print a lemma under the
// word. Read across every meaning rather than the selected one: the point is
// to know whether the line can appear at all during this card's lifetime.
function cardLemmaSlotIsLoadBearing(card, displayedTargetHeadword) {
    if (!card) return false;
    const shown = foldSurfaceForm(displayedTargetHeadword);
    if (!shown) return false;
    const forms = (card.meanings || []).map(m => m && m.headword).filter(Boolean);
    if (!forms.length) {
        const fallback = card.citationForm || card.lemma;
        return Boolean(fallback) && foldSurfaceForm(fallback) !== shown;
    }
    return forms.some(form => foldSurfaceForm(form) !== shown);
}

function updateCard({ announceHeadword = false } = {}) {
    const card = flashcards[currentIndex];
    const langConfig = config.languages[selectedLanguage];
    const displaySurface = card.displaySurface || card.targetWord;
    // A surface-keyed card can hold senses from several headwords. Start with
    // the only unambiguous card-level citation; once currentMeaning is resolved
    // below, the selected lemma–POS group becomes authoritative instead.
    const cardHeadwords = [...new Set(
        (card.meanings || [])
            .map(m => m && m.headword)
            .filter(Boolean)
    )];
    let citationForm = cardHeadwords.length > 1
        ? ''
        : (cardHeadwords[0] || card.citationForm || card.lemma || displaySurface);
    const formNote = card.isPronominal ? 'verb with se' : '';
    window._currentDisplayedExample = null;
    const reportShortcut = document.getElementById('cardMetaBtn');
    if (reportShortcut) {
        const canReport = Boolean(window.canUserFlag ? window.canUserFlag() : window.isAuditAccount?.());
        const section = reportShortcut.closest('.kb-section');
        if (section) section.style.display = canReport ? '' : 'none';
    }

    // A card entry starts from its structural group selection. An explicit
    // sub-sense choice lasts only while the learner remains on this card.
    if (announceHeadword) _explicitMeaningSelectionKey = null;

    // Most updateCard() calls are in-card rerenders: cycling an example,
    // selecting a sense/expression, starting autoplay, or changing a display
    // option. They must be silent and must clear a delayed browser utterance.
    // Genuine card-entry paths opt in explicitly below.
    if (!announceHeadword) {
        window.speechSynthesis?.cancel();
    }

    // Update artist album artwork background
    updateArtistBackground();

    // Update reverse button text
    updateReverseButton();

    // Reset meaning index if out of bounds or pointing to a detached invariant MWE
    if (card.isMultiMeaning && (currentMeaningIndex >= card.meanings.length
        || (!cardHasOnlyInvariantMwes(card) && isInvariantMweMeaning(card.meanings[currentMeaningIndex])))) {
        const firstVisible = card.meanings.findIndex(m => !isInvariantMweMeaning(m));
        currentMeaningIndex = firstVisible >= 0 ? firstVisible : 0;
        currentGroupSelection = null;
    }

    // On first entry, start multi-POS cards on the part of speech carrying
    // the most corpus weight. Source order remains the stable tie-breaker.
    if (announceHeadword && card.isMultiMeaning && card.meanings?.length && !card._activePosTab) {
        const posWeights = new Map();
        card.meanings.forEach((meaning, index) => {
            const pos = meaning.pos === 'SENSE_CYCLE' ? (meaning.cycle_pos || 'X') : meaning.pos;
            if (!pos || ['MWE', 'CLITIC', 'EXAMPLE_ONLY'].includes(pos)) return;
            if (!cardHasOnlyInvariantMwes(card) && isInvariantMweMeaning(meaning)) return;
            const weight = Number(meaning.percentage ?? meaning.frequency ?? meaning.count) || 0;
            const entry = posWeights.get(pos) || { pos, weight: 0, firstIndex: index };
            entry.weight += weight;
            posWeights.set(pos, entry);
        });
        const primaryPos = [...posWeights.values()].sort((a, b) =>
            (b.weight - a.weight) || (a.firstIndex - b.firstIndex)
        )[0];
        if (primaryPos) {
            card._activePosTab = primaryPos.pos;
            currentMeaningIndex = primaryPos.firstIndex;
            currentGroupSelection = null;
        }
    }

    // Validate the group selection against the current card. If any member
    // index is out of range, or the anchor's meaning/context no longer
    // matches the stored groupKey/POS (data shifted under us), drop the
    // selection and fall back to per-meaning rendering.
    if (currentGroupSelection) {
        const sel = currentGroupSelection;
        const inRange = card.isMultiMeaning && sel.members && sel.members.length >= 2
            && sel.members.every(i => i >= 0
                && i < card.meanings.length
                && card.meanings[i].pos === sel.pos
                && (card.meanings[i].headword || '') === (sel.headword || ''));
        if (!inRange) {
            currentGroupSelection = null;
        } else {
            const a = card.meanings[sel.members[0]];
            const expectedKey = sel.axis === 'translation'
                ? (a.meaning || '')
                : (a.context || '');
            if (expectedKey !== sel.groupKey) {
                currentGroupSelection = null;
            }
        }
    }

    // Get the current meaning for multi-meaning cards
    const currentMeaning = card.isMultiMeaning ? card.meanings[currentMeaningIndex] : null;
    if (currentMeaning) {
        // The sentence belongs to one active lemma/POS group. Keeping only
        // that group's detail rows visible makes the relationship explicit.
        card._expandedPos = new Set([lemmaPosGroupKeyForMeaning(currentMeaning)]);
    }
    // Keep the lemma in the header synchronized with the selected group. This
    // is especially important for homographic surfaces such as fue (ser/ir):
    // changing the lemma–POS group must change the label and example together.
    if (currentMeaning?.headword) citationForm = currentMeaning.headword;
    const activeDisplayPos = currentMeaning?.pos === 'SENSE_CYCLE'
        ? (currentMeaning.cycle_pos || 'X')
        : (currentMeaning?.pos || card.partOfSpeech || '');
    document.getElementById('flashcard')?.style.setProperty('--card-pos-rgb', getPosAccentRgb(activeDisplayPos));
    const activeProductionAnswer = getActiveProductionAnswer(card, currentMeaning);
    const mergedExampleFocus = getMergedLemmaExampleFocus(card, currentMeaning, {
        advanceOnEntry: announceHeadword
    });
    card._activeExampleSurface = mergedExampleFocus?.surface || '';
    card._activeExampleMorphology = mergedExampleFocus?.morphology || null;
    const displayedTargetHeadword = getDisplayedTargetHeadword(card) || displaySurface;

    // Determine what to show on front and back based on flip direction
    let frontText, backWord, backTranslation, exampleSentence, exampleTranslation;
    let flippedFrontMeanings = null; // structured front for EN→Target multi-meaning

    if (card.isChainChild) {
        // Phrase-summary chain-child cards render entirely through
        // renderPhraseSummaryBack() further down and carry no real
        // meanings (phraseSummaryCard() sets meanings: []). Skip the
        // meaning-driven computation below entirely instead of crashing
        // on an undefined currentMeaning (card.meanings[0]) — the front
        // still shows the parent word so it isn't blank before flipping.
        frontText = card.chainParentWord || '';
        backWord = card.chainParentWord || '';
        backTranslation = '';
        exampleSentence = '';
        exampleTranslation = '';
    } else if (card.isMultiMeaning) {
        // Multi-meaning format
        if (isFlipped && !card.searchExamplesOnly && !card.translationUnavailable) {
            // English → Target language: build structured front with POS badges
            let normalMeanings;
            if (currentMeaning?.allMWEs?.length) {
                const activeExpression = currentMeaning.allMWEs[currentMWEIndex % currentMeaning.allMWEs.length];
                normalMeanings = [{
                    pos: 'MWE',
                    meaning: activeExpression?.translation || currentMeaning.meaning || '',
                    percentage: 1
                }];
            } else if (currentMeaning?.allClitics?.length) {
                const activeClitic = currentMeaning.allClitics[currentMWEIndex % currentMeaning.allClitics.length];
                normalMeanings = [{
                    pos: 'CLITIC',
                    meaning: activeClitic?.translation || currentMeaning.meaning || '',
                    percentage: 1
                }];
            } else {
                normalMeanings = card.meanings.filter(m =>
                    m.pos !== 'MWE' && m.pos !== 'CLITIC' && m.pos !== 'SENSE_CYCLE');
            }

            // English-first cards use several senses as a semantic fingerprint
            // for one exact surface. Cover each lemma/POS reading before adding
            // extra frequent senses; four concise cues keep the front scannable.
            const frontMeanings = selectReverseCueMeanings(normalMeanings, { card });

            const uniquePOS = new Set(frontMeanings.map(m => m.pos));
            const multiPOS = uniquePOS.size > 1;

            flippedFrontMeanings = { meanings: frontMeanings, multiPOS };
            frontText = null; // will use structured display instead
            backWord = activeProductionAnswer;
            backTranslation = currentMeaning.meaning;
            exampleSentence = currentMeaning.englishSentence;
            exampleTranslation = currentMeaning.targetSentence;
        } else {
            // Target language → English (normal)
            frontText = displayedTargetHeadword;
            backWord = displayedTargetHeadword;
            backTranslation = currentMeaning.meaning;
            exampleSentence = currentMeaning.targetSentence;
            exampleTranslation = currentMeaning.englishSentence;
        }
    } else {
        // Legacy format - get current sentence from sentences array
        const currentSentence = card.sentences && card.sentences.length > 0
            ? card.sentences[currentSentenceIndex % card.sentences.length]
            : { target: card.targetSentence, english: card.englishSentence };

        if (isFlipped) {
            // English → Target language
            frontText = card.translation;
            backWord = card.productionAnswer || card.targetWord;
            backTranslation = card.translation;
            exampleSentence = currentSentence.english;
            exampleTranslation = currentSentence.target;
        } else {
            // Target language → English (normal)
            frontText = displaySurface;
            backWord = displaySurface;
            backTranslation = card.translation;
            exampleSentence = currentSentence.target;
            exampleTranslation = currentSentence.english;
        }
    }

    // Lyric transcriptions carry parenthetical ad-libs — "(Eh-eh)", "(Wuh)",
    // "(Yeah)" — on 27% of example lines, costing ~10 of a 49-character line.
    // Stripped at render only: the stored lyric stays intact, so search,
    // highlighting against the original, and any future re-analysis are
    // unaffected.
    exampleSentence = stripAdlibParentheticals(exampleSentence);
    exampleTranslation = stripAdlibParentheticals(exampleTranslation);

    const frontProductionHintEl = document.getElementById('frontProductionHint');
    // Fix one sense-linked sentence to the card attempt. Example browsing on
    // the revealed back may change currentExampleIndex/currentMeaningIndex, but
    // it must not retroactively rewrite the prompt the learner already answered.
    let productionPrompt = _productionPromptByCard.get(card);
    const retainedProductionPrompt = retainProductionPromptAttempt(productionPrompt, {
        direction: isFlipped,
        reset: announceHeadword,
        createHTML: () => flippedFrontMeanings
            ? buildFrontProductionHint(card, currentMeaning, activeProductionAnswer)
            : '',
    });
    if (retainedProductionPrompt !== productionPrompt) {
        productionPrompt = retainedProductionPrompt;
        _productionPromptByCard.set(card, productionPrompt);
    }
    const productionHintHTML = productionPrompt?.html || '';
    if (frontProductionHintEl) {
        frontProductionHintEl.hidden = !productionHintHTML;
        frontProductionHintEl.innerHTML = productionHintHTML
            ? `<button type="button" class="front-production-hint-toggle" aria-expanded="false" aria-controls="frontProductionCloze" onclick="toggleFrontProductionHint(event)">
                    <span class="front-production-hint-icon" aria-hidden="true">⌁</span>
                    <span class="front-production-hint-label">Sentence hint</span>
               </button>
               <div class="front-production-cloze" id="frontProductionCloze" aria-label="Spanish sentence with the answer blanked" hidden>${productionHintHTML}</div>`
            : '';
    }

    const notableSurfaceRelation = getNotableSurfaceRelation(card);
    const frontSurfaceRelationEl = document.getElementById('frontSurfaceRelation');
    if (frontSurfaceRelationEl) {
        const showRelation = Boolean(notableSurfaceRelation && !isFlipped && !flippedFrontMeanings);
        frontSurfaceRelationEl.hidden = !showRelation;
        frontSurfaceRelationEl.textContent = showRelation
            ? `${notableSurfaceRelation.surface} → ${notableSurfaceRelation.canonical}`
            : '';
    }

    const frontWordEl = document.getElementById('frontWord');
    const frontMeaningsEl = document.getElementById('frontMeanings');

    // Morphology belongs to the verb POS rather than forming a separate
    // metadata strip. Build it once so both front directions can nest it
    // beneath the relevant verb badge.
    const displayedMorphology = card.mergedLemma
        ? card._activeExampleMorphology
        : card.morphology;
    const morphLabels = displayedMorphology
        ? compactMorphLabels(Array.isArray(displayedMorphology)
            ? displayedMorphology
            : [displayedMorphology])
        : [];
    const isVerbPos = pos => {
        const p = String(pos || '').toLowerCase();
        return p.includes('verb') || p === 'v' || p === 'vb';
    };
    const posLabelHTML = pos => `<span class="pos-full-label">${posDisplayName(pos)}</span>`;
    // The verb POS pill retains the complete popover on every face. In the
    // production direction its coupled subject + tense/mood rows are also
    // repeated as a compact, always-visible cue beneath the English senses;
    // knowing which surface to produce should not depend on discovering a tap.
    //
    // Each analysis is ONE row that owns both halves: the Spanish subject on
    // the left, the tense/mood it belongs to on the right. Person and tense
    // used to render as sibling pills, which read as two independent facts and
    // made "Yo | present | imperative" ambiguous once a second analysis was
    // listed. The tense is therefore always spelled out here — the implicit
    // "present" shorthand is correct on the card face but destroys the pairing
    // inside a list of competing readings. Extra complete analyses stay behind
    // a "+" so the preferred reading is never buried.
    const describeMorphForm = label => {
        const mood = label.mood
            || (label.moodCode === 'indicativo' ? 'indicative' : '');
        return [label.tense, mood].filter(Boolean).join(' ')
            || label.grammar
            || 'base form';
    };
    const renderMorphPopover = () => {
        if (!morphLabels.length) return '';
        const renderRow = (label, isPrimary) => {
            const form = describeMorphForm(label);
            if (!label.person && !form) return null;
            const subject = label.person
                ? `<span class="morph-pop-subject">${escapeCardText(label.person)}</span>`
                : '<span class="morph-pop-subject is-empty" aria-hidden="true">—</span>';
            return `<li class="morph-pop-row${isPrimary ? ' is-primary' : ''}">
                ${subject}
                <span class="morph-pop-form">${escapeCardText(form)}</span>
            </li>`;
        };
        const usable = morphLabels.filter(label => renderRow(label, false));
        if (!usable.length) return '';
        const primary = renderRow(usable[0], true);
        const alternatives = usable.slice(1).map(label => renderRow(label, false));
        const altCount = alternatives.length;
        const altBlock = altCount
            ? `<button type="button" class="morph-pop-more" aria-expanded="false"
                    aria-label="Show ${altCount} other possible reading${altCount > 1 ? 's' : ''}"
                    onclick="toggleMorphAlternatives(event)">
                    <span class="morph-pop-more-sign" aria-hidden="true">+</span>
                    ${altCount} other reading${altCount > 1 ? 's' : ''}
                </button>
                <ul class="morph-pop-list morph-pop-alts" hidden>${alternatives.join('')}</ul>`
            : '';
        const heading = altCount ? 'Preferred reading' : 'Form';
        return `<div class="morph-popover" hidden role="dialog" aria-label="Verb morphology">
            <div class="morph-pop-title">${heading}</div>
            <ul class="morph-pop-list">${primary}</ul>
            ${altBlock}
        </div>`;
    };
    // The pill remains a press-to-reveal control for the complete explanation.
    // English-first cards additionally receive the compact persistent rendering
    // below; Spanish-first recognition keeps the quieter popover-only treatment.
    const renderFrontPosUnit = (
        pos,
        includeMorph = false,
        pillClass = 'card-pos',
        stackState = ''
    ) => {
        const hasMorph = includeMorph && isVerbPos(pos) && morphLabels.length > 0;
        const colour = getPosColorClass(pos);
        const pill = hasMorph
            ? `<button type="button" class="${pillClass} ${colour} has-morph-toggle" aria-expanded="false" aria-label="${posDisplayName(pos)}. Show verb morphology" onclick="toggleMorphPopover(event)">${posLabelHTML(pos)}</button>`
            : `<span class="${pillClass} ${colour}" aria-label="${posDisplayName(pos)}">${posLabelHTML(pos)}</span>`;
        return `<span class="front-pos-unit${stackState ? ` ${stackState}` : ''}">${pill}${hasMorph ? renderMorphPopover() : ''}</span>`;
    };

    if (flippedFrontMeanings) {
        // EN→Target structured display: the glosses to produce from.
        frontWordEl.style.display = 'none';
        const { meanings: fMeanings } = flippedFrontMeanings;
        const fontSize = fMeanings.length > 2 ? 28 : (fMeanings.length > 1 ? 36 : 52);
        let html = '';
        for (const m of fMeanings) {
            const productionGloss = getProductionEnglishCue(card, m) || m.meaning;
            const posChip = m.pos && !['MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY'].includes(m.pos)
                ? renderFrontPosUnit(m.pos, isVerbPos(m.pos), 'card-pos front-meaning-pos')
                : '';
            html += `<div class="front-meaning-row">
                ${posChip}
                <span class="front-meaning-text" style="font-size: ${fontSize}px;">${escapeCardText(productionGloss)}</span>
            </div>`;
        }
        frontMeaningsEl.innerHTML = html;
        frontMeaningsEl.style.display = 'flex';
    } else {
        // Normal single-word/text display
        frontMeaningsEl.innerHTML = '';
        frontMeaningsEl.style.display = 'none';
        frontWordEl.style.display = '';
        frontWordEl.innerHTML = frontText;
        // Auto-shrink the word font so it fits on a single line instead of
        // wrapping. The old heuristic keyed off character count (>13 chars),
        // which missed cases where the chars were wide enough to overflow a
        // narrower container ("Sandungueo" at 10 chars overflows on a phone-
        // width card). shrinkToFit measures intrinsic content width and
        // steps the font-size down until it fits.
        shrinkToFit(frontWordEl, window.innerWidth < 768 ? 18 : 22);
    }

    // Display part of speech on front with color coding
    const frontPOSEl = document.getElementById('frontPOS');
    frontPOSEl.className = 'card-pos-list';
    frontPOSEl.innerHTML = '';
    const posSource = flippedFrontMeanings
        ? flippedFrontMeanings.meanings
        : ((card.isMultiMeaning && card.meanings) || []);
    if (flippedFrontMeanings) {
        // Production: POS sits on each gloss row, not in the corner stack.
        frontPOSEl.style.display = 'none';
    } else if (posSource.length > 0 || card.partOfSpeech) {
        const pairs = [];
        const seenPairs = new Set();
        (posSource.length ? posSource : [{ pos: card.partOfSpeech, headword: citationForm }]).forEach(meaning => {
            if (['MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY'].includes(meaning.pos)) return;
            const lemma = String(meaning.headword || citationForm || displayedTargetHeadword || '').trim();
            const key = `${lemma}\0${meaning.pos}`;
            if (!meaning.pos || seenPairs.has(key)) return;
            seenPairs.add(key);
            pairs.push({ lemma, pos: meaning.pos });
        });
        if (pairs.length === 0) {
            frontPOSEl.style.display = 'none';
        } else {
            frontPOSEl.classList.add('is-lemma-map', `pos-count-${Math.min(pairs.length, 4)}`);
            if (pairs.length > 4) frontPOSEl.classList.add('pos-count-many');
            frontPOSEl.innerHTML = pairs.map(pair => {
                const posUnit = renderFrontPosUnit(pair.pos, isVerbPos(pair.pos));
                if (!pair.lemma) return posUnit;
                // POS is the iconographic pill; the lemma is the label it
                // governs, sitting to its right inside the same capsule.
                return `<span class="front-lemma-pair">${posUnit}<span class="front-lemma-name">${escapeCardText(pair.lemma)}</span></span>`;
            }).join('');
            frontPOSEl.style.display = 'grid';
            // Keep every label in a group at the same size. The grid reserves
            // equal space per pair; only unusually long lemmas reduce the
            // group's type size, so neighbouring cards retain a steady rhythm.
            const names = [...frontPOSEl.querySelectorAll('.front-lemma-name')];
            const baseSize = pairs.length === 1 ? 16 : pairs.length === 2 ? 15 : pairs.length === 3 ? 14 : 13;
            const floorSize = pairs.length > 3 ? 10.5 : 11.5;
            let labelSize = window.innerWidth < 768 ? baseSize - 1 : baseSize;
            for (; labelSize > floorSize && names.some(name => name.scrollWidth > name.clientWidth + 1); labelSize -= 0.5) {
                names.forEach(name => { name.style.fontSize = `${labelSize - 0.5}px`; });
            }
            names.forEach(name => { name.title = name.textContent; });
        }
    } else {
        frontPOSEl.style.display = 'none';
    }

    // Display lemma on front if different from target word and the POS map
    // is not already naming that lemma.
    const frontLemmaEl = document.getElementById('frontLemma');
    const lemmaMapNamesLemma = !flippedFrontMeanings
        && frontPOSEl.classList.contains('is-lemma-map')
        && frontPOSEl.querySelector('.front-lemma-name');
    if (!isFlipped && citationForm
        && foldSurfaceForm(citationForm) !== foldSurfaceForm(displayedTargetHeadword)
        && !lemmaMapNamesLemma) {
        frontLemmaEl.textContent = citationForm;
        frontLemmaEl.dataset.formNote = formNote;
        frontLemmaEl.classList.toggle('has-form-note', Boolean(formNote));
        frontLemmaEl.classList.remove('is-reserved');
        frontLemmaEl.style.display = 'block';
        // Sized against the word's final size, not its own ceiling, so the
        // lemma can never come out larger than the form being asked about.
        fitLemmaUnderWord(frontWordEl, frontLemmaEl, 18);
    } else if (!isFlipped && !lemmaMapNamesLemma
        && cardLemmaSlotIsLoadBearing(card, displayedTargetHeadword)) {
        // Some other sense on this same card does name a lemma. Hold the slot
        // open with an invisible stand-in so selecting that sense does not
        // shove the surface form up the card and back down again.
        frontLemmaEl.textContent = '\u00A0';
        frontLemmaEl.dataset.formNote = '';
        frontLemmaEl.classList.remove('has-form-note');
        frontLemmaEl.classList.add('is-reserved');
        frontLemmaEl.style.display = 'block';
        fitLemmaUnderWord(frontWordEl, frontLemmaEl, 18);
    } else {
        frontLemmaEl.textContent = '';
        frontLemmaEl.dataset.formNote = '';
        frontLemmaEl.classList.remove('has-form-note');
        frontLemmaEl.classList.remove('is-reserved');
        frontLemmaEl.style.display = 'none';
    }

    // English-first production needs the form constraint in sight. Keep each
    // possible analysis coupled (subject + tense/mood) and let it wrap as one
    // compact row; the verb pill still opens the fuller labelled popover.
    const frontMorphEl = document.getElementById('frontMorph');
    if (frontMorphEl) {
        const frontHasVerb = Boolean(flippedFrontMeanings?.meanings?.some(
            meaning => isVerbPos(meaning.pos)));
        const showFrontMorph = Boolean(isFlipped && frontHasVerb && morphLabels.length);
        frontMorphEl.classList.toggle('front-morph-visible', showFrontMorph);
        frontMorphEl.innerHTML = showFrontMorph
            ? `<span class="front-morph-title">Form</span>
               <span class="front-morph-analyses">${morphLabels.map(label => {
                    const form = label.grammar || describeMorphForm(label);
                    const subject = label.person
                        ? `<strong>${escapeCardText(label.person)}</strong>`
                        : '';
                    return `<span class="front-morph-analysis">${subject}<span>${escapeCardText(form)}</span></span>`;
                }).join('')}</span>`
            : '';
        frontMorphEl.style.display = showFrontMorph ? 'flex' : 'none';
    }

    const vocabularyRank = card.vocabularyRank || card.rank;
    const vocabularySize = card.vocabularySize || null;

    // Store source + configuration-relative ranking for diagnostics.
    const flashcardEl = document.getElementById('flashcard');
    if (card.rank !== undefined) {
        flashcardEl.setAttribute('data-rank', card.rank);
    } else {
        flashcardEl.setAttribute('data-rank', '');
    }
    flashcardEl.setAttribute('data-vocabulary-rank', vocabularyRank || '');

    // Display configuration-relative vocabulary rank (not position in the
    // study set) and frequency on the card front.
    const frontRankingEl = document.getElementById('frontRanking');
    if (card.searchExclusionReason) {
        frontRankingEl.innerHTML = `<span class="card-exclusion-label">Excluded: ${card.searchExclusionReason}</span>`;
        frontRankingEl.style.display = 'flex';
    } else if (card.searchExamplesOnly) {
        frontRankingEl.innerHTML = '<span class="card-exclusion-label card-exclusion-label--examples">Examples only · no matched sense</span>';
        frontRankingEl.style.display = 'flex';
    } else if (vocabularyRank !== undefined) {
        let freqHtml = '';
        // The count and the rank are the figures worth reading; the wording
        // around them and the total-vocabulary denominator are context. Only
        // the former get the bold white treatment.
        if (activeArtist && card.corpusCount) {
            const count = `<strong class="card-stat-value">${Number(card.corpusCount).toLocaleString()}</strong>`;
            freqHtml = `<span class="card-freq-label">Lyric lines: ${count}</span>`;
        } else if (!activeArtist && Number(card.sourceFrequency) > 0) {
            const perMillion = card.sourceFrequencyUnit === 'per_million';
            const count = `<strong class="card-stat-value">${Number(card.sourceFrequency).toLocaleString(undefined, { maximumFractionDigits: perMillion ? 2 : 0 })}</strong>`;
            const source = escapeCardText(card.sourceFrequencySource || 'Published frequency list');
            const label = perMillion ? `Frequency: ${count}/million` : `List occurrences: ${count}`;
            freqHtml = `<button class="card-freq-btn" onclick="window.showFreqInfo(event)" data-frequency-source="${source}" data-frequency-unit="${card.sourceFrequencyUnit || ''}" data-frequency-forms="${Number(card.sourceFrequencyForms) || 1}" aria-label="Source frequency information">${label}</button>`;
        }
        const denominator = vocabularySize ? ` / ${vocabularySize.toLocaleString()}` : '';
        const rankLabel = card.artistVocabularyScope === 'extra' ? 'Extra rank' : 'Vocabulary rank';
        frontRankingEl.innerHTML =
            `<span class="card-rank-label">${rankLabel}: <strong class="card-stat-value">${Number(vocabularyRank).toLocaleString()}</strong>${denominator}</span>${freqHtml}`;
        frontRankingEl.style.display = 'flex';
    } else {
        frontRankingEl.style.display = 'none';
    }

    let backWordText = backWord;
    let wordDisplay = backWordText;
    let backHeadwordPairClass = '';
    let backCitationHTML = '';
    let backDerivationHTML = '';
    // Surface stays the large answer; the lemma is a compact chip on its
    // right — the same pairing as the front, without wrapping the title in
    // a second filled capsule. Skip transparent plurals/elisions.
    const showBackLemmaPair = Boolean(citationForm)
        && foldSurfaceForm(citationForm) !== foldSurfaceForm(backWordText)
        && !isTrivialCanonicalRelation(backWordText, citationForm);
    if (showBackLemmaPair) {
        backHeadwordPairClass = ' back-surface-pair';
        const lemmaAlreadySe = /se$/i.test(String(citationForm).replace(/[\s-]+/g, ''));
        const seMark = formNote && !lemmaAlreadySe
            ? `<span class="back-lemma-se" title="${escapeCardText(formNote)}">se</span>`
            : '';
        wordDisplay = `<span class="back-surface-name">${escapeCardText(backWordText)}</span><span class="back-lemma-chip">${escapeCardText(citationForm)}${seMark}</span>`;
    }
    const derivation = card.derivationRelation;
    if (derivation?.base_lemma) {
        const relationLabel = derivation.relation === 'diminutive'
            ? 'diminutive of'
            : derivation.relation === 'superlative'
                ? 'superlative of'
                : 'derived from';
        backDerivationHTML = `<div class="back-derivation-line"><span>${relationLabel}</span><strong>${escapeCardText(derivation.base_lemma)}</strong></div>`;
    }
    const backWordLength = backWordText.replace(/<[^>]+>/g, '').length;
    // Headword baseline on the back, raised from 42. The old length ramp is
    // kept as a cheap first guess so a very long word never renders huge for
    // one frame, but it is deliberately generous: the authoritative cap is
    // fitBackHeadword(), which measures the room the top-right POS pill(s)
    // actually leave and steps this down only as far as that requires.
    const BACK_HEADWORD_MAX = 48;
    const backHeadwordSize = backWordLength > 14
        ? Math.max(26, BACK_HEADWORD_MAX - (backWordLength - 14) * 1.6)
        : BACK_HEADWORD_MAX;

    // Build homograph chip HTML if siblings exist
    let homographChipHTML = '';
    if (card.homographIds && card.homographIds.length > 0) {
        const lookup = getVocabByIdLookup();
        const chips = [];
        for (const sibId of card.homographIds) {
            const sib = lookup.get(sibId);
            if (!sib) continue;
            const sibLemma = sib.lemma || sib.word;
            const sibTranslation = (sib.meanings && sib.meanings.length > 0) ? sib.meanings[0].translation : '';
            const label = sibTranslation ? `${sibLemma} (${sibTranslation})` : sibLemma;
            chips.push(`<span class="homograph-chip" onclick="peekHomograph('${sibId}')">also: ${label}</span>`);
        }
        if (chips.length > 0) {
            homographChipHTML = `<div class="homograph-chips">${chips.join('')}</div>`;
        }
    }

    // One compact POS legend sits directly beneath the word/lemma. Rows keep
    // their POS colour through the surrounding section, so repeating the pill
    // above every section would add labels without adding information.
    let backPosLegendHTML = '';
    let activeBackPos = null;
    let hasBackPosTabs = false;
    if ((card.isMultiMeaning && card.meanings) || card.partOfSpeech) {
        const posItems = [];
        const posMeanings = card.isMultiMeaning && card.meanings
            ? card.meanings
            : [{ pos: card.partOfSpeech }];
        const posWeights = new Map();
        posMeanings.forEach((meaning, meaningIndex) => {
            const pos = meaning.pos === 'SENSE_CYCLE'
                ? (meaning.cycle_pos || 'X')
                : meaning.pos;
            if (pos === 'MWE' || pos === 'CLITIC' || pos === 'EXAMPLE_ONLY') return;
            if (!cardHasOnlyInvariantMwes(card) && isInvariantMweMeaning(meaning)) return;
            if (!pos) return;
            const weight = Number(meaning.percentage ?? meaning.frequency ?? meaning.count) || 0;
            const entry = posWeights.get(pos) || { pos, meaningIndex, weight: 0 };
            entry.weight += weight;
            posWeights.set(pos, entry);
        });
        posItems.push(...[...posWeights.values()].sort((a, b) =>
            (b.weight - a.weight) || (a.meaningIndex - b.meaningIndex)
        ));
        hasBackPosTabs = posItems.length > 1;
        if (posItems.length > 0) {
            const currentPos = currentMeaning?.pos === 'SENSE_CYCLE'
                ? (currentMeaning.cycle_pos || 'X')
                : currentMeaning?.pos;
            const rememberedPos = posItems.some(item => item.pos === card._activePosTab)
                ? card._activePosTab
                : null;
            activeBackPos = posItems.some(item => item.pos === currentPos)
                ? currentPos
                : (rememberedPos || posItems[0].pos);
            card._activePosTab = activeBackPos;
            const onlyPos = posItems.length === 1 ? posItems[0].pos : '';
            const onlyPosHasAction = isVerbPos(onlyPos) && morphLabels.length > 0;
            // A multi-meaning back already starts with a (POS, headword)
            // section. Repeating one inert POS in the top-right corner adds no
            // information; retain the corner control for multiple POS choices
            // and for the single verb button that opens morphology.
            const hideRedundantSingleBackPos = card.isMultiMeaning
                && posItems.length === 1
                && !onlyPosHasAction;
            const posPills = posItems.map(({ pos, meaningIndex }) => {
                if (hasBackPosTabs) {
                    const stackState = pos === activeBackPos ? 'is-active' : 'is-inactive';
                    return `<button type="button" class="card-pos back-pos-tab ${stackState} ${getPosColorClass(pos)}${pos === activeBackPos ? ' selected' : ''}" role="tab" aria-selected="${pos === activeBackPos}" aria-label="${posDisplayName(pos)}" onclick="selectPartOfSpeech(event, ${meaningIndex}, '${pos}')"><span class="back-pos-dot" aria-hidden="true"></span>${posLabelHTML(pos)}</button>`;
                }
                // Verb morphology is hidden until the pill is pressed, rather
                // than showing permanently; a non-verb pill (nothing to
                // toggle) renders as a plain, non-interactive pill instead.
                const pillHasMorph = isVerbPos(pos) && morphLabels.length > 0;
                if (!pillHasMorph) {
                    return `<span class="card-pos ${getPosColorClass(pos)}"><span class="back-pos-dot" aria-hidden="true"></span>${posDisplayName(pos)}</span>`;
                }
                // The popover rides inside the pill's own wrapper so it can be
                // positioned against it without measuring anything.
                return `<span class="back-pos-unit">
                    <button type="button" class="card-pos has-morph-toggle ${getPosColorClass(pos)}" aria-expanded="false" aria-label="${posDisplayName(pos)}. Show verb morphology" onclick="toggleMorphPopover(event)"><span class="back-pos-dot" aria-hidden="true"></span>${posDisplayName(pos)}</button>
                    ${renderMorphPopover()}
                </span>`;
            });
            // The back carries no POS legend. Every part of speech already has
            // its own section below, whose header holds the same POS plus the
            // lemma it belongs to, its glosses and its share — a stronger link
            // than a detached legend, and one row per POS rather than a
            // parallel list. The codebase already made this argument for a
            // single POS ("repeating one inert POS in the top-right corner
            // adds no information"); it holds just as well for three.
            const suppressBackPosLegend = true;
            if (!suppressBackPosLegend && !hideRedundantSingleBackPos) {
                backPosLegendHTML = `<div class="back-pos-legend${hasBackPosTabs ? ' has-tabs' : ''} pos-count-${Math.min(posItems.length, 4)}"${hasBackPosTabs ? ' role="tablist"' : ''} aria-label="Filter senses by part of speech">${posPills.join('')}</div>`;
            }
        }
    }

    // Left-aligned header: word + its POS pill(s) share the top line —
    // flex-wrap lets the legend sit to the right of the word when it fits
    // and drop to its own line only when it doesn't. The lemma/citation, if
    // any, is the secondary line beneath, with verb morphology inline to
    // its right (not stacked on its own row).
    const backGrammarHTML = backCitationHTML
        ? `<div class="back-grammar-block">
                <div class="back-lemma-row">${backCitationHTML}</div>
           </div>`
        : '';

    // line-height: 1.1 keeps multi-line wraps tight (long word + lemma
    // on narrow viewports) so the header grows by a reasonable amount
    // rather than adding a full line of whitespace each wrap. Single-line
    // cards are unaffected — line-height only matters when there are two
    // or more rendered lines.
    let backHTML = card.isChainChild
        ? (card.chainChildKind === 'examples'
            ? renderExamplesChildBack(card)
            : renderPhraseSummaryBack(card))
        : `
        <div class="back-header">
            <div class="flip-back-area" id="flipBackArea">
                <div class="back-headword-row">
                    <span class="back-headword${backHeadwordPairClass}" style="font-size: ${backHeadwordSize}px; font-weight: bold; line-height: ${showBackLemmaPair ? 1 : 1.1};">${wordDisplay}</span>
                    ${backPosLegendHTML}
                </div>
                ${notableSurfaceRelation
                    ? `<div class="surface-relation-cue back-surface-relation">${escapeCardText(notableSurfaceRelation.surface)} <span aria-hidden="true">→</span> ${escapeCardText(notableSurfaceRelation.canonical)}</div>`
                    : ''}
                ${backGrammarHTML}
            </div>
            ${backDerivationHTML}
            ${homographChipHTML}
        </div>
    `;
    if (card.translationUnavailable) {
        backHTML += `<div class="extra-translation-unavailable"><strong>No translation available yet.</strong><br>This one-off lyric remains available as corpus evidence.</div>`;
    }

    // Multi-meaning cards keep a compact active-item view for large merged
    // inventories; smaller and unmerged cards retain the full inline menu.
    // Chain-child cards skip this entirely — renderPhraseChildHeader already
    // rendered the expression/translation, and renderPhraseChildExample
    // (below) is a self-contained example panel, not a sense-row list.
    if (card.isMultiMeaning && !card.isChainChild) {
        // Merged-lemma cards can carry a large learnable inventory (dictionary
        // senses plus Expressions/clitics). Once that inventory grows beyond a
        // small glanceable menu, keep the ordinary card focused on the active
        // item. The bottom knowledge-map button remains the explicit route to
        // the complete list and can focus any other item directly.
        const knowledgeItemCount = getCardKnowledgeItems(card).length;
        const compactKnowledgeView = useLemmaMode
            && currentUser && !currentUser.isGuest
            && knowledgeItemCount > 4;

        // Two POS-section maps:
        //   - scrollSections: regular meanings + SENSE_CYCLE (these scroll)
        //   - traySections: MWE + CLITIC (always visible, pinned below the
        //     scroll area so the user doesn't have to hunt for them)
        // Map insertion order preserves the source's first-seen POS order.
        const scrollSections = new Map();
        const traySections = new Map();
        const rowsForSection = (sections, pos) => {
            if (!sections.has(pos)) sections.set(pos, []);
            return sections.get(pos);
        };
        // One group per (POS, headword). Those are not independent axes: only
        // 201 POS groups in the deck contain more than one headword, so opening
        // a part of speech almost always resolves the lemma too. Keying on the
        // pair collapses them into one level instead of nesting two, and still
        // splits `fue` into ser and ir, which POS alone cannot.
        //
        // 75% of cards produce a single group, 98% two or fewer, so the pill row
        // is always short.
        const groupInfo = new Map();
        (card.meanings || []).forEach((m, meaningIndex) => {
            if (!m || m.exampleOnly) return;
            const pos = m.pos === 'SENSE_CYCLE' ? (m.cycle_pos || 'X') : m.pos;
            if (!pos || pos === 'MWE' || pos === 'CLITIC') return;
            const key = pos + '\u0000' + (m.headword || '');
            if (!groupInfo.has(key)) {
                groupInfo.set(key, {
                    pos,
                    headword: m.headword || '',
                    senses: [],
                    mainMeanings: [],
                    pct: 0,
                    hasAssignedEvidence: false,
                    hasOnlyRareSenses: true,
                    firstMeaningIndex: meaningIndex,
                });
            }
            const g = groupInfo.get(key);
            if (!m.isRareSense) {
                g.hasOnlyRareSenses = false;
            }
            if (!m.unassigned) {
                if (!m.isRareSense) {
                    g.pct += Number(m.percentage || 0);
                    g.mainMeanings.push(m);
                }
                g.hasAssignedEvidence = true;
            } else if (m.isRareSense) {
                g.hasAssignedEvidence = true;
            }
            const rawText = String(getProductionEnglishCue(card, m) || m.meaning || m.translation || '').trim();
            const text = senseSummaryText(projectWiktionaryGloss(m, rawText).display);
            // Main senses only. Store as a strict normalized Set so no duplicate
            // gloss strings are ever added.
            if (text) {
                const normKey = text.toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '').trim();
                const alreadyPresent = g.senses.some(s => s.toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '').trim() === normKey);
                if (!alreadyPresent) g.senses.push(text);
            }
        });

        if (!card._expandedPos) {
            const cur = currentMeaning
                ? (currentMeaning.pos === 'SENSE_CYCLE'
                    ? (currentMeaning.cycle_pos || 'X') : currentMeaning.pos)
                    + '\u0000' + (currentMeaning.headword || '')
                : null;
            card._expandedPos = new Set(cur ? [cur] : []);
        }
        const activeLemmaPosKey = lemmaPosGroupKeyForMeaning(currentMeaning);
        const activeGroupSenseRaw = String(
            getProductionEnglishCue(card, currentMeaning) || currentMeaning?.meaning || currentMeaning?.translation || ''
        ).trim();
        const activeGroupSense = senseSummaryText(projectWiktionaryGloss(
            currentMeaning,
            activeGroupSenseRaw
        ).display);

        // Build headers from rows that were actually emitted, including filtering
        // for compact knowledge views. Hidden inventory must not inflate +N.
        const recordSectionMeanings = (rows, meanings) => {
            rows.summarySenses ||= [];
            for (const meaning of meanings) {
                const raw = getProductionEnglishCue(card, meaning) || meaning.meaning || meaning.translation || '';
                rows.summarySenses.push(senseSummaryText(projectWiktionaryGloss(meaning, raw).display));
            }
        };
        const renderSections = (sections) => Array.from(sections)
            .map(([key, rows]) => {
                const g = groupInfo.get(key);
                const pos = g ? g.pos : String(key).split('\u0000')[0];
                const accent = `--sense-match-rgb: ${getPosAccentRgb(pos)};`;
                if (!g) {
                    return `
                <section class="meaning-pos-section" data-pos="${pos}" style="${accent}">
                    <div class="meaning-pos-rows">${rows.join('')}</div>
                </section>`;
                }
                const open = card._expandedPos.has(key);
                // The surface form already identifies an identical lemma in
                // the centred card header; repeat the lemma only when it adds
                // information (for example, an inflected surface).
                const hw = g.headword
                    ? `<span class="pos-pill-lemma">${escapeCardText(g.headword)}</span>` : '';
                const visibleSenses = rows.summarySenses || [];
                const summarySense = key === activeLemmaPosKey && visibleSenses.includes(activeGroupSense)
                    ? activeGroupSense
                    : (visibleSenses[0] || '');
                // Keep the active sense first, then offer the rest in source
                // order. A post-render measurement decides how many fit; +N
                // is a genuine overflow indicator rather than a hard-coded
                // substitute for every sense after the first.
                // Strict normalized Set deduplication ensures no duplicate sense ever renders.
                const candidateSenses = [summarySense, ...visibleSenses];
                const summarySenses = [];
                const seenSummaryKeys = new Set();
                for (const sense of candidateSenses) {
                    if (!sense) continue;
                    const normKey = sense.toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '').trim();
                    if (!normKey || seenSummaryKeys.has(normKey)) continue;
                    seenSummaryKeys.add(normKey);
                    summarySenses.push(sense);
                }
                const summaryHTML = summarySenses
                    .map(sense => `<span class="pos-summary-sense">${escapeCardText(sense)}</span>`)
                    .join('');
                const extra = summarySenses.length > 1
                    ? `<span class="pos-pill-more" hidden>+${summarySenses.length - 1}</span>` : '';
                const useProminenceLabels = (typeof senseProminenceMode !== 'undefined' ? senseProminenceMode : globalThis.state?.senseProminenceMode) !== 'percentages';
                // Only show percentage in percentage mode, and don't show a redundant "100%" if this is the only POS group
                const pct = (!useProminenceLabels && g.pct > 0 && !(groupInfo.size === 1 && Math.round(g.pct * 100) >= 100))
                    ? `<span class="pos-pill-pct sense-percentage">${Math.round(g.pct * 100)}%</span>` : '';
                // Don't label genuine rare dictionary senses as "Unassigned"
                const assignmentState = (!g.hasAssignedEvidence && !g.hasOnlyRareSenses)
                    ? '<span class="pos-pill-unassigned">Unassigned</span>'
                    : (rows.length <= 1 ? '' : g.hasOnlyRareSenses
                        ? prominenceBadgeHTML({ label: 'Rare', key: 'rare' })
                        : (useProminenceLabels && g.pct > 0
                            ? prominenceBadgeHTML(prominenceInfoFromShare(g.mainMeanings)) : ''));
                // No known-tick here. A check mark on this row read as "you
                // answered this", which is what the tick means everywhere else
                // on the card; here it meant something narrower and only added
                // a third symbol to an already dense line.
                return `
                <section class="meaning-pos-section pos-collapsible${open ? ' is-open' : ''}"
                         data-pos="${pos}" data-group-key="${escapeCardText(key.replace(/\u0000/g, '~~'))}" style="${accent}">
                    <button type="button" class="pos-section-head"
                            aria-label="${escapeCardText(`${pos} ${g.headword}: ${summarySenses.join('; ')}`)}"
                            onclick="selectLemmaPosGroup(event, '${key.replace(/\u0000/g, '~~')}', ${g.firstMeaningIndex})">
                        <span class="pos-section-label">${escapeCardText(posDisplayName(pos))}</span>
                        ${hw}
                        <span class="pos-section-summary">${summaryHTML}${extra}</span>
                        ${assignmentState}${pct}
                        <span class="pos-section-chevron">${open ? '\u25BE' : '\u25B8'}</span>
                    </button>
                    <div class="meaning-pos-rows">${rows.join('')}</div>
                </section>`;
            }).join('');

        // Render-side grouping: collapse rows that share either
        // translation OR context into a single "group card" — shared
        // field on one side, list of varying values on the other.
        // POS is part of the grouping key because sections are now true
        // structural groups: duplicate text can collapse within a section,
        // but never merge meanings from two different parts of speech.
        // Examples:
        //   `dice` → 3 senses share "to say" → translation-axis group
        //            shared = "to say", varying = contexts
        //   `su`   → 5 senses share possessive context → context-axis group
        //            shared = context,  varying = translations
        const activeMeaningsCount = (card.meanings || []).filter(m => m && !m.exampleOnly).length;
        // A pair can share one gloss or context too (for example "no" and
        // "not" under negation). The grouping pass leaves unrelated pairs as
        // singletons, so there is no reason to require a third sense.
        const GROUP_DUPLICATE_MEANINGS = activeMeaningsCount >= 2;
        // Per-meaning-idx axis assignment: 'translation' | 'context' |
        // 'singleton' | 'special' (MWE/CLITIC/SENSE_CYCLE — opted out).
        // Cached on the card after first compute — meanings don't mutate
        // post-load, so flips/cycles/selects can reuse the same maps.
        let axisOf, groupKeyOf, groupMembers, groupFirstIdx, groupPctSum;
        if (card._grouping) {
            ({ axisOf, groupKeyOf, groupMembers, groupFirstIdx, groupPctSum } = card._grouping);
        } else {
            axisOf = new Map();
            groupKeyOf = new Map();
            groupMembers = new Map();
            groupFirstIdx = new Map();
            groupPctSum = new Map();
            if (GROUP_DUPLICATE_MEANINGS) {
                // Pass 1: tally raw sizes per axis (used only to make the
                // per-meaning axis decision in pass 2). Keys include POS so
                // each duplicate group remains inside one section.
                const transRawSize = new Map();
                const ctxRawSize = new Map();
                card.meanings.forEach((m, idx) => {
                    if (m.pos === 'MWE' || m.pos === 'CLITIC' || m.pos === 'SENSE_CYCLE' || (!cardHasOnlyInvariantMwes(card) && isInvariantMweMeaning(m))) {
                        axisOf.set(idx, 'special');
                        return;
                    }
                    const groupPrefix = `${m.pos}\u0000${m.headword || ''}\u0000`;
                    const tk = `${groupPrefix}${m.meaning || m.translation || ''}`;
                    transRawSize.set(tk, (transRawSize.get(tk) || 0) + 1);
                    if (m.context) {
                        const ck = `${groupPrefix}${m.context}`;
                        ctxRawSize.set(ck, (ctxRawSize.get(ck) || 0) + 1);
                    }
                });
                // Pass 2: pick the dominant axis per meaning. Ties go to
                // translation (the more common failure mode is classifier slop
                // on a single sense, which manifests as duplicate translations).
                card.meanings.forEach((m, idx) => {
                    if (axisOf.get(idx) === 'special') return;
                    const tk = m.meaning || m.translation || '';
                    const groupPrefix = `${m.pos}\u0000${m.headword || ''}\u0000`;
                    const ts = transRawSize.get(`${groupPrefix}${tk}`) || 0;
                    const ck = m.context || null;
                    const cs = ck ? (ctxRawSize.get(`${groupPrefix}${ck}`) || 0) : 0;
                    if (ts > 1 && cs > 1) {
                        if (ts >= cs) { axisOf.set(idx, 'translation'); groupKeyOf.set(idx, tk); }
                        else { axisOf.set(idx, 'context'); groupKeyOf.set(idx, ck); }
                    } else if (ts > 1) {
                        axisOf.set(idx, 'translation'); groupKeyOf.set(idx, tk);
                    } else if (cs > 1) {
                        axisOf.set(idx, 'context'); groupKeyOf.set(idx, ck);
                    } else {
                        axisOf.set(idx, 'singleton');
                    }
                });
                // Pass 3: rebuild effective members per (axis, key). If a
                // group's effective size has shrunk below 2 (because some of
                // its candidates were stolen by the other axis), downgrade
                // those meanings to singletons. Iterate until stable so a
                // chain of demotions converges.
                let changed = true;
                while (changed) {
                    changed = false;
                    groupMembers.clear();
                    groupFirstIdx.clear();
                    groupPctSum.clear();
                    card.meanings.forEach((m, idx) => {
                        const ax = axisOf.get(idx);
                        if (ax !== 'translation' && ax !== 'context') return;
                        const k = groupKeyOf.get(idx);
                        const compKey = `${m.pos}\u0000${m.headword || ''}\u0000${ax}\u0000${k}`;
                        if (!groupMembers.has(compKey)) groupMembers.set(compKey, []);
                        groupMembers.get(compKey).push(idx);
                        if (!groupFirstIdx.has(compKey)) groupFirstIdx.set(compKey, idx);
                        groupPctSum.set(compKey, (groupPctSum.get(compKey) || 0) + (m.percentage || 0));
                    });
                    for (const [compKey, members] of groupMembers) {
                        if (members.length < 2) {
                            for (const i of members) {
                                axisOf.set(i, 'singleton');
                                groupKeyOf.delete(i);
                            }
                            changed = true;
                        }
                    }
                }
            }
            card._grouping = { axisOf, groupKeyOf, groupMembers, groupFirstIdx, groupPctSum };
        }

        // When the current meaning is one member of a collapsed row, the
        // initial state represents the overarching grouped sense. A learner
        // can still click any sub-row to pin that narrower sense; autoplay
        // deliberately opts out because it walks those sub-senses itself.
        selectInitialMeaningGroup(card, card._grouping);
        const glossProminence = glossClusterProminenceState(card);

        // Precompute singleton fold leaders and followers for identical display senses
        // within the same POS section. If differentiators between identical glosses score
        // >= 60, they remain separate rows and show the differentiator; otherwise they
        // fold together into a single clean row taking the highest prominence badge.
        const singletonFoldFollowers = new Set();
        const singletonFoldLeaders = new Map();
        const singletonDiffByMeaningIndex = new Map();
        const singletonsBySectionGloss = new Map();

        card.meanings.forEach((m, idx) => {
            if (!m || m.exampleOnly) return;
            const ax = GROUP_DUPLICATE_MEANINGS ? (axisOf.get(idx) || 'singleton') : 'singleton';
            if (ax !== 'singleton') return;
            const pos = m.pos === 'SENSE_CYCLE' ? (m.cycle_pos || 'X') : m.pos;
            if (pos === 'MWE' || pos === 'CLITIC' || (!cardHasOnlyInvariantMwes(card) && isInvariantMweMeaning(m))) return;
            const rawGloss = String(getProductionEnglishCue(card, m) || m.meaning || m.translation || '').trim();
            const proj = projectWiktionaryGloss(m, rawGloss);
            const normKey = `${pos}\u0000${m.headword || ''}\u0000${proj.display.toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '').replace(/\s+/g, ' ').trim()}`;
            if (!singletonsBySectionGloss.has(normKey)) singletonsBySectionGloss.set(normKey, []);
            singletonsBySectionGloss.get(normKey).push({ m, idx });
        });

        for (const [, entries] of singletonsBySectionGloss) {
            if (entries.length < 2) continue;
            const groupMeanings = entries.map(e => e.m);
            const diffs = entries.map(e => resolveMeaningDifferentiator(
                e.m,
                groupMeanings,
                e.m.meaning || e.m.translation || '',
                (m, g) => cleanSenseContext(contextWithoutSenseMetadata(m, false), g)
            ));

            entries.forEach((e, i) => {
                if (diffs[i]) singletonDiffByMeaningIndex.set(e.idx, diffs[i]);
            });

            const lowScoreEntries = entries.filter((e, i) => !diffs[i] || diffs[i].score < 60);
            if (lowScoreEntries.length >= 2) {
                const bestEntry = lowScoreEntries.find(e => getSenseProminenceInfo(e.m).key === 'common')
                    || lowScoreEntries.find(e => getSenseProminenceInfo(e.m).key === 'uncommon')
                    || lowScoreEntries[0];
                const leaderIdx = bestEntry.idx;
                const followers = lowScoreEntries.filter(e => e.idx !== leaderIdx).map(e => e.idx);
                followers.forEach(fi => singletonFoldFollowers.add(fi));

                const allFoldIndices = [leaderIdx, ...followers];
                const allFoldMeanings = allFoldIndices.map(i => card.meanings[i]);
                const bestPromInfo = prominenceInfoFromShare(allFoldMeanings);
                const sumPctVal = Math.min(100, Math.round(allFoldMeanings.reduce((acc, m) => acc + (Number(m.percentage) || 0), 0) * 100));
                const hasOnlyRare = allFoldMeanings.every(m => m.unassigned || m.isRareSense || m.prominenceLabel === 'Rare');

                const pooled = dedupeExamples(allFoldMeanings.flatMap(m => m.allExamples || m.examples || []));
                if (pooled.length) {
                    card.meanings[leaderIdx].allExamples = pooled;
                }

                singletonFoldLeaders.set(leaderIdx, {
                    allIndices: allFoldIndices,
                    bestPromInfo,
                    sumPctVal,
                    hasOnlyRare,
                });
            }
        }

        orderMeaningEntriesForDisplay(card.meanings).forEach(({ meaning: m, index: idx }) => {
            if (m.exampleOnly) return;
            if (singletonFoldFollowers.has(idx)) return;
            const isSelected = idx === currentMeaningIndex;
            const rowStateClasses = isSelected ? ' is-current-sense' : '';
            // One flat fill for every row, matching the POS header above them
            // and the active row below. Activeness is the outline, not a
            // different shade.
            const bgColor = 'rgba(var(--sense-match-rgb), 0.10)';
            const textColor = isSelected ? 'var(--text-primary)' : 'var(--text-primary)';
            const borderStyle = '';
            const isInvariantMWE = !cardHasOnlyInvariantMwes(card) && isInvariantMweMeaning(m);
            const isMWE = m.pos === 'MWE' || isInvariantMWE;
            const isClitic = m.pos === 'CLITIC';
            const isSenseCycle = m.pos === 'SENSE_CYCLE';
            const sectionPos = isSenseCycle ? (m.cycle_pos || 'X') : (isInvariantMWE ? 'MWE' : m.pos);
            // Route this row to the pinned tray (MWE/CLITIC) or the scroll
            // region (regular + SENSE_CYCLE). Chain-child cards carry their
            // own single MWE/CLITIC meaning as the card's main content, not
            // a tray row — the tray no longer renders for anyone else since
            // those entries leave via the phrase handoff instead.
            const target = rowsForSection(
                (isMWE || isClitic) && !card.isChainChild ? traySections : scrollSections,
                (isMWE || isClitic) ? sectionPos
                    : sectionPos + '\u0000' + (m.headword || '')
            );

            // For MWE pill, show the current expression/translation based on MWE index
            const mweIdx = (isMWE && isSelected) ? currentMWEIndex % (m.allMWEs ? m.allMWEs.length : 1) : 0;
            const mweExpr = isMWE && m.allMWEs ? m.allMWEs[mweIdx].expression : (m.expression || m.headword || m.metadata?.multiword_expression || '');
            const mweMeaning = isMWE && m.allMWEs ? m.allMWEs[mweIdx].translation : (m.translation || m.meaning || '');
            const mweCount = isMWE && m.allMWEs ? m.allMWEs.length : 0;
            const mweCounter = (isMWE && mweCount > 1) ? ` <span class="example-counter-group"><button class="mwe-cycle-btn" onclick="cycleMWEBackward(event)" title="Previous expression">‹</button>${compactCounterHTML(mweIdx, mweCount, 'expression')}<button class="mwe-cycle-btn" onclick="cycleMWEForward(event)" title="Next expression">›</button></span>` : '';
            // For Clitic pill, reuse MWE cycling with allClitics
            const cliticIdx = (isClitic && isSelected) ? currentMWEIndex % (m.allClitics ? m.allClitics.length : 1) : 0;
            const cliticForm = isClitic && m.allClitics ? m.allClitics[cliticIdx].form : '';
            const cliticCount = isClitic && m.allClitics ? m.allClitics.length : 0;
            const cliticCounter = (isClitic && cliticCount > 1) ? ` <span class="example-counter-group"><button class="mwe-cycle-btn" onclick="cycleMWEBackward(event)" title="Previous form">‹</button>${compactCounterHTML(cliticIdx, cliticCount, 'form')}<button class="mwe-cycle-btn" onclick="cycleMWEForward(event)" title="Next form">›</button></span>` : '';
            const cleanMweMeaning = isMWE ? mweMeaning.replace(/\s*\(elided\)/gi, '') : '';
            const rawDisplayMeaning = isMWE
                ? (cleanMweMeaning || '<span style="font-style: italic; opacity: 0.5;">Translation unavailable</span>')
                : (getProductionEnglishCue(card, m) || m.meaning || m.translation || '');
            const displayMeaning = isMWE
                ? rawDisplayMeaning
                : displaySenseGloss(m, rawDisplayMeaning, isSelected);
            const displayMeaningHTML = isMWE
                ? displayMeaning
                : senseCrossReferenceHTML(m, displayMeaning, isSelected);
            if (isMWE) {
                if (compactKnowledgeView && !isSelected) return;
                // Expression row: plain bold expression (left), translation
                // (middle), counter (right). The row tint already provides
                // enough structure; an inner capsule only adds clutter.
                // Two context tiers — renderer prefers real over heuristic:
                //   1. ``context``           — structured data from the
                //      SpanishDict phrase-page scrape (tool_5c_scrape_spanishdict_phrases).
                //      Authoritative — same shape as the sense-level context.
                //   2. ``context_heuristic`` — split off the quickdef string
                //      (tool_5d_build_spanishdict_mwes → split_mwe_translation).
                //      Best-effort regex extraction; the text is real SpanishDict
                //      quickdef content but the paren-split is our guess.
                // The JS splitter at splitMWETranslation() is a render-time
                // fallback for decks whose membership entries predate the
                // pipeline change above.
                const activeMwe = (isMWE && m.allMWEs && m.allMWEs[mweIdx]) || null;
                const realCtx = activeMwe ? (activeMwe.context || '') : '';
                const heurCtx = activeMwe ? (activeMwe.context_heuristic || '') : '';
                let mwePrimary = cleanMweMeaning;
                let mweContext = realCtx || heurCtx;
                let mweContextIsHeuristic = !realCtx && !!heurCtx;
                if (!mweContext && cleanMweMeaning) {
                    // Legacy fallback — no split fields on the membership at all.
                    const sp = splitMWETranslation(cleanMweMeaning);
                    mwePrimary = sp.primary;
                    mweContext = sp.context;
                    mweContextIsHeuristic = !!sp.context;
                } else if (mweContext) {
                    // When we have a split field, recompute the primary by
                    // stripping the trailing paren that contains the heuristic
                    // note (real context never lives inline in the quickdef).
                    if (mweContextIsHeuristic) {
                        const sp = splitMWETranslation(cleanMweMeaning);
                        mwePrimary = sp.primary || cleanMweMeaning;
                    } else {
                        mwePrimary = cleanMweMeaning;
                    }
                }
                const primaryDisplay = mwePrimary || '<span style="font-style: italic; opacity: 0.5;">Translation unavailable</span>';
                // Heuristic context is the same typographic tier as real
                // context — the text is legitimate, only its structural
                // guarantee differs. No visual distinction is exposed to the
                // reader (a subtle one could be added later if needed).
                const contextHTML = mweContext ? `<small class="special-meaning-context">· ${mweContext}</small>` : '';
                const mweTextClass = adaptiveRowTextClass(mweExpr, mwePrimary, mweContext);
                target.push(`
                <div class="meaning-row meaning-row-mwe ${mweTextClass}${isSelected ? ' selected' : ''}${rowStateClasses}" style="position: relative; display: flex; align-items: center; padding: 6px 8px; margin-bottom: 6px; background: ${bgColor}; ${borderStyle} border-radius: 8px; cursor: pointer; min-height: 40px;" onclick="selectMeaning(${idx})">
                    ${renderRowCheckSlot(isSelected)}
                    <span class="special-meaning-copy bilingual-meaning-copy${mweCount > 1 ? ' has-counter' : ''}">
                        <span class="mwe-expression">${mweExpr}</span>
                        <strong class="mwe-translation">${primaryDisplay}</strong>
                        ${contextHTML}
                    </span>
                    ${mweCounter}
                </div>
                `);
            } else if (isClitic) {
                if (compactKnowledgeView && !isSelected) return;
                // Clitic row mirrors expressions: plain bold form, translation,
                // counter. The outer row already supplies grouping and color.
                const activeClitic = m.allClitics ? m.allClitics[cliticIdx] : null;
                const cliticTrRaw = activeClitic?.translation || '';
                const cliticDetail = describeCliticForm(activeClitic, card);
                const cliticTextClass = adaptiveRowTextClass(cliticForm, cliticDetail.displayTranslation || cliticTrRaw, cliticDetail.visualDetail);
                target.push(`
                <div class="meaning-row meaning-row-clitic ${cliticTextClass}${isSelected ? ' selected' : ''}${rowStateClasses}" style="position: relative; display: flex; align-items: center; padding: 6px 8px; margin-bottom: 6px; background: ${bgColor}; ${borderStyle} border-radius: 8px; cursor: pointer; min-height: 40px;" onclick="selectMeaning(${idx})">
                    ${renderRowCheckSlot(isSelected)}
                    <span class="special-meaning-copy clitic-meaning${cliticCount > 1 ? ' has-counter' : ''}">
                        <span class="mwe-expression clitic-form">${cliticForm}</span>
                        <strong>${escapeCardText(cliticDetail.displayTranslation || cliticTrRaw || 'Translation unavailable')}</strong>
                        ${cliticDetail.visualDetail ? `<small class="special-meaning-context">· ${escapeCardText(cliticDetail.visualDetail)}</small>` : ''}
                    </span>
                    ${cliticCounter}
                </div>
                `);
            } else if (isSenseCycle) {
                if (compactKnowledgeView && !isSelected) return;
                // Sense cycle row: all unassigned/remainder senses for this
                // POS; the shared POS pill now lives in the header legend.
                const rawTranslations = m.allSenses
                    ? m.allSenses.map(s => projectWiktionaryGloss(s, s.translation).display)
                    : [projectWiktionaryGloss(m, m.meaning).display];
                // Prettify the remainder bucket:
                //   1. Split any semicolon-packed gloss into atomic translations
                //      (Wiktionary often bundles synonyms: "to pull out; to remove; to extract").
                //   2. Dedupe exact (case-insensitive) duplicates across senses while preserving order.
                //   3. If every remaining entry starts with "to ", factor the prefix and comma-join.
                //      Otherwise keep the pipe-joined display.
                const splitPieces = [];
                for (const t of rawTranslations) {
                    if (typeof t !== 'string') continue;
                    for (const piece of t.split(';')) {
                        const trimmed = piece.trim();
                        if (trimmed) splitPieces.push(trimmed);
                    }
                }
                const dedupSeen = new Set();
                const dedupedTranslations = [];
                for (const p of splitPieces) {
                    const key = p.toLowerCase();
                    if (!dedupSeen.has(key)) { dedupSeen.add(key); dedupedTranslations.push(p); }
                }
                let allTranslations = dedupedTranslations.length ? dedupedTranslations : rawTranslations;
                let joinSep = ' | ';
                const allToInfinitive = allTranslations.length >= 2 &&
                    allTranslations.every(t => typeof t === 'string' && /^to\s+\S/i.test(t.trim()));
                if (allToInfinitive) {
                    const stripped = allTranslations.map(t => t.trim().replace(/^to\s+/i, ''));
                    // Dedupe again after stripping the prefix (e.g. "to get" + "to get" via semicolons)
                    const seen2 = new Set();
                    const unique = [];
                    for (const s of stripped) {
                        const key = s.toLowerCase();
                        if (!seen2.has(key)) { seen2.add(key); unique.push(s); }
                    }
                    // First piece keeps "to "; subsequent pieces are bare, joined with ", "
                    allTranslations = unique.map((s, i) => i === 0 ? 'to ' + s : s);
                    joinSep = ', ';
                }
                const joinedFull = allTranslations.join(joinSep);
                const MAX_SENSE_CHARS = 120;
                let joinedDisplay = joinedFull;
                let isTruncated = false;
                if (joinedFull.length > MAX_SENSE_CHARS) {
                    // Truncate at a sense boundary
                    let truncated = '';
                    for (let si = 0; si < allTranslations.length; si++) {
                        const candidate = si === 0 ? allTranslations[si] : truncated + joinSep + allTranslations[si];
                        if (candidate.length > MAX_SENSE_CHARS) break;
                        truncated = candidate;
                    }
                    joinedDisplay = truncated;
                    isTruncated = true;
                }
                const ellipsisBtn = isTruncated
                    ? ` <span class="sense-cycle-expand" style="cursor: pointer; opacity: 0.7; font-size: 12px;" onclick="event.stopPropagation(); this.parentElement.querySelector('.sense-cycle-short').style.display='none'; this.parentElement.querySelector('.sense-cycle-full').style.display='inline'; this.style.display='none';" title="Show all senses">…</span>`
                    : '';
                const cycleTextClass = adaptiveRowTextClass(joinedFull);
                recordSectionMeanings(target, m.allSenses || [m]);
                target.push(`
                <div class="meaning-row meaning-row-cycle ${cycleTextClass}${isSelected ? ' selected' : ''}${rowStateClasses}" style="position: relative; display: flex; align-items: center; padding: 1px 2px; margin-bottom: 4px; background: ${bgColor}; ${borderStyle} border-radius: 8px; cursor: pointer; min-height: 39px; opacity: 0.75;" onclick="selectMeaning(${idx})">
                    ${renderRowCheckSlot(isSelected)}
                    <span class="row-adaptive-text" style="flex: 1; font-weight: 600; color: white; min-width: 0; text-align: center; line-height: 1.4; padding: 0 8px;">${isTruncated ? `<span class="sense-cycle-short">${joinedDisplay}</span><span class="sense-cycle-full" style="display:none">${joinedFull}</span>${ellipsisBtn}` : joinedDisplay}</span>
                </div>
                `);
            } else {
                // Regular meaning row. Three layouts:
                //   axis === 'singleton' → flat one-row card (translation
                //                          centred, optional inline context)
                //   axis === 'translation' → group card; shared = translation,
                //                          varying list = contexts
                //   axis === 'context'   → group card; shared = context,
                //                          varying list = translations
                // Continuations of a group are skipped; the leader emits a
                // single card containing all members.
                const pctVal = Math.round(m.percentage * 100);
                const prominenceText = m.prominenceLabel
                    ? escapeCardText(m.prominenceLabel)
                    : '';
                const axis = GROUP_DUPLICATE_MEANINGS ? (axisOf.get(idx) || 'singleton') : 'singleton';
                const isGrouped = axis === 'translation' || axis === 'context';
                const groupKey = isGrouped ? groupKeyOf.get(idx) : null;
                const compKey = isGrouped
                    ? `${m.pos}\u0000${m.headword || ''}\u0000${axis}\u0000${groupKey}`
                    : null;
                if (isGrouped) {
                    const firstIdx = groupFirstIdx.get(compKey);
                    const members = groupMembers.get(compKey) || [];
                    const displayLeader = members.includes(currentMeaningIndex)
                        ? currentMeaningIndex
                        : firstIdx;
                    if (displayLeader !== idx) return;
                }
                if (isGrouped) {
                    const members = groupMembers.get(compKey);
                    // Sub-senses keep their source order too. Selection is a
                    // highlight, not a request to reshuffle a visible family.
                    const orderedMembers = members;
                    const pctSumRaw = groupPctSum.get(compKey);
                    const sumPct = Math.round((pctSumRaw || 0) * 100);
                    const isTransAxis = axis === 'translation';
                    const sharedText = isTransAxis
                        ? displayMeaning
                        : String(m.context || '').replace(/"/g, '&quot;');
                    const sharedTextHTML = isTransAxis
                        ? displayMeaningHTML
                        : sharedText;
                    const maxMemberLength = orderedMembers.reduce((max, mi) => {
                        const member = card.meanings[mi];
                        const memberText = isTransAxis
                            ? (member.context || '')
                            : (getProductionEnglishCue(card, member) || member.meaning || member.translation || '');
                        return Math.max(max, String(memberText || '').replace(/<[^>]*>/g, '').trim().length);
                    }, 0);
                    const sharedCleanLength = String(sharedText || '').replace(/<[^>]*>/g, '').trim().length;
                    const longestFragment = Math.max(sharedCleanLength, maxMemberLength);
                    const worstRowLength = sharedCleanLength + maxMemberLength;
                    const groupDensity = Math.max(longestFragment, worstRowLength * 0.7);
                    let groupedTextClass = 'row-text-sm';
                    if (groupDensity <= 24) groupedTextClass = 'row-text-xl';
                    else if (groupDensity <= 44) groupedTextClass = 'row-text-lg';
                    else if (groupDensity <= 72) groupedTextClass = 'row-text-md';
                    // Group-level selection: clicking the shared field selects
                    // the whole group (examples become union of members);
                    // clicking any sub-item reverts to per-meaning selection.
                    const groupSelected = !!(currentGroupSelection
                        && currentGroupSelection.axis === axis
                        && currentGroupSelection.pos === m.pos
                        && (currentGroupSelection.headword || '') === (m.headword || '')
                        && currentGroupSelection.groupKey === groupKey);
                    // Outer row mirrors singleton: body | pct.
                    // The body's internal grid stays simple (shared + varying):
                    //   trans-axis: shared trans | varying ctx
                    //   ctx-axis:   varying trans | shared ctx
                    const anyMemberSelected = orderedMembers.some(mi => mi === currentMeaningIndex);
                    const groupIsCurrent = groupSelected || anyMemberSelected;
                    if (compactKnowledgeView && !groupIsCurrent) return;
                    recordSectionMeanings(target, orderedMembers.map(i => card.meanings[i]));
                    const groupStateClasses = groupIsCurrent ? ' is-current-sense' : '';
                    const cardBg = 'rgba(var(--sense-match-rgb), 0.08)';
                    // The outer row is the complete-family selection marker.
                    // Do not repeat it on the shared cell: an inner marker is
                    // reserved for a specific member selected within a family.
                    const sharedBg = 'transparent';
                    const sharedBorder = '';

                    const memberCells = orderedMembers.map((memberIdx, rowIdx) => {
                        const mm = card.meanings[memberIdx];
                        const isMemberSelected = !groupSelected && memberIdx === currentMeaningIndex;
                        const cellBg = isMemberSelected
                            ? 'rgba(var(--sense-match-rgb), 0.2)'
                            : 'rgba(255, 255, 255, 0.03)';
                        const cellBorder = (isMemberSelected && !mm.unassigned)
                            ? 'box-shadow: inset 3px 0 0 rgb(var(--sense-match-rgb)), inset -3px 0 0 rgb(var(--sense-match-rgb));'
                            : '';
                        const baseCell = `grid-row: ${rowIdx + 1}; padding: 2px 6px; background: ${cellBg}; ${cellBorder} border-radius: 6px; cursor: pointer; min-height: 25px; display: flex; align-items: center; justify-content: center;`;
                        // Varying cell.
                        let varyingHtml;
                        if (isTransAxis) {
                            const metaOptions = {
                                senseCount: card.meanings?.length || orderedMembers.length,
                                gloss: sharedText,
                                peerMeanings: orderedMembers.filter(mi => mi !== memberIdx).map(mi => card.meanings[mi]),
                                allowInactivePrimary: true,
                            };
                            const rawCtx = contextWithoutSenseMetadata(mm, isMemberSelected, metaOptions);
                            let cleanedCtx = cleanSenseContext(rawCtx, sharedText);
                            if (cleanedCtx && contextCollidesWithMetadata(
                                cleanedCtx,
                                compactLearnerSenseMetadata(senseMetadataItems(mm), mm, metaOptions)
                            )) {
                                cleanedCtx = '';
                            }
                            const metadataHTML = senseMetadataHTML(mm, isMemberSelected, metaOptions);
                            if (cleanedCtx || metadataHTML) {
                                varyingHtml = `<span class="meaning-context-cell" style="line-height: 1.3; min-width: 0; overflow-wrap: anywhere; word-break: break-word;">${renderSenseContextHTML(cleanedCtx, { leadingDot: false })}${metadataHTML}</span>`;
                            } else {
                                const diff = resolveMeaningDifferentiator(
                                    mm,
                                    orderedMembers.filter(mi => mi !== memberIdx).map(mi => card.meanings[mi]),
                                    sharedText,
                                    (m, g) => cleanSenseContext(contextWithoutSenseMetadata(m, false), g)
                                );
                                if (diff && diff.score >= 60) {
                                    if (diff.type === 'context') {
                                        varyingHtml = `<span class="meaning-context-cell" style="line-height: 1.3; min-width: 0; overflow-wrap: anywhere; word-break: break-word;">${renderSenseContextHTML(diff.label, { leadingDot: false })}</span>`;
                                    } else {
                                        const family = escapeCardText(diff.type);
                                        const shortLabel = escapeCardText(diff.label);
                                        varyingHtml = `<span class="meaning-context-cell" style="line-height: 1.3; min-width: 0; overflow-wrap: anywhere; word-break: break-word;"><span class="sense-metadata-detail sense-pill sense-pill--${family}" data-family="${family}"><span class="sense-pill-label">${shortLabel}</span></span></span>`;
                                    }
                                } else {
                                    // The unqualified source gloss is the honest fallback for
                                    // a reading without its own qualifier; never an empty dash.
                                    varyingHtml = `<span class="meaning-context-cell">${escapeCardText(displaySenseGloss(mm, mm.meaning || mm.translation || sharedText))}</span>`;
                                }
                            }
                        } else {
                            const transRaw = displaySenseGloss(
                                mm,
                                getProductionEnglishCue(card, mm) || mm.meaning || '',
                                isMemberSelected
                            );
                            const transSafe = String(transRaw).replace(/"/g, '&quot;');
                            varyingHtml = `<span class="row-adaptive-text" style="font-weight: 600; color: var(--text-primary); line-height: 1.25; min-width: 0; overflow: hidden; text-overflow: ellipsis;">${senseCrossReferenceHTML(mm, transSafe, isMemberSelected)}${senseMetadataHTML(mm, isMemberSelected, { senseCount: card.meanings?.length || orderedMembers.length, gloss: transRaw, peerMeanings: senseMetadataPeers(mm, card.meanings, transRaw), sharedContext: m.context, allowInactivePrimary: true })}${modelProposalMarkerHTML(mm)}</span>`;
                        }
                        const varyingCol = isTransAxis ? 2 : 1;
                        const varyingCell = `<div class="group-card-varying-cell${isMemberSelected ? ' is-active-subsense' : ''}" onclick="event.stopPropagation(); selectMeaning(${memberIdx})" style="${baseCell} grid-column: ${varyingCol}; min-width: 0; overflow: hidden;">${varyingHtml}</div>`;
                        return varyingCell;
                    }).join('');

                    const groupMeanings = orderedMembers.map(memberIdx => card.meanings[memberIdx]);
                    const useProminenceLabels = (typeof senseProminenceMode !== 'undefined' ? senseProminenceMode : globalThis.state?.senseProminenceMode) !== 'percentages';
                    // Senses sharing the same English gloss or same context: pool Common/Rare
                    // unless the within-family leaf split is peaked and reliable.
                    const splitLeaves = withinGlossLeafSeparationIsReliable(groupMeanings);
                    const groupPromInfo = prominenceInfoFromShare(groupMeanings);
                    const groupPctVal = Math.min(100, Math.round(groupMeanings.reduce((acc, mm) => acc + (Number(mm.percentage) || 0), 0) * 100));
                    let pctColumnHtml;
                    if (useProminenceLabels && splitLeaves) {
                        const pctStackHtml = orderedMembers.map((memberIdx) => {
                            const mm = card.meanings[memberIdx];
                            const pInfo = glossProminence.infoByIndex.get(memberIdx) || getSenseProminenceInfo(mm);
                            return `<div class="sense-prominence-cell" onclick="event.stopPropagation(); selectMeaning(${memberIdx})" style="min-height: 25px; padding: 2px 6px; display: flex; align-items: center; justify-content: flex-end; cursor: pointer;">${prominenceBadgeHTML(pInfo)}</div>`;
                        }).join('');
                        pctColumnHtml = `<div class="pct-column" style="display: flex; flex-direction: column; gap: 3px; padding-left: 4px;">${pctStackHtml}</div>`;
                    } else if (useProminenceLabels) {
                        pctColumnHtml = `<div class="pct-column pct-column--group" style="display: flex; align-items: center; padding-left: 4px;">${prominenceBadgeHTML(groupPromInfo)}</div>`;
                    } else if (splitLeaves) {
                        const pctStackHtml = orderedMembers.map((memberIdx) => {
                            const mm = card.meanings[memberIdx];
                            const memberPct = Math.round((mm.percentage || 0) * 100);
                            if (mm.unassigned || memberPct >= 100) {
                                return '<div style="min-height: 25px; padding: 2px 6px;"></div>';
                            }
                            return `<div class="sense-percentage sense-percentage-cell" onclick="event.stopPropagation(); selectMeaning(${memberIdx})" style="min-height: 25px; padding: 2px 6px; display: flex; align-items: center; justify-content: flex-end; cursor: pointer;">${memberPct}%</div>`;
                        }).join('');
                        pctColumnHtml = `<div class="pct-column" style="display: flex; flex-direction: column; gap: 3px; padding-left: 4px;">${pctStackHtml}</div>`;
                    } else {
                        pctColumnHtml = (groupPctVal > 0 && groupPctVal < 100
                            ? `<div class="pct-column pct-column--group" style="display: flex; align-items: center; padding-left: 4px;"><span class="sense-percentage sense-percentage-cell">${groupPctVal}%</span></div>`
                            : `<div class="pct-column"></div>`);
                    }

                    // Shared cell — spans all body rows.
                    const sharedCol = isTransAxis ? 1 : 2;
                    const sharedSpan = `grid-column: ${sharedCol}; grid-row: 1 / span ${orderedMembers.length}; align-self: center;`;
                    const sharedCellHtml = isTransAxis
                        ? `<div class="group-card-shared row-adaptive-text" style="${sharedSpan} font-weight: 600; color: var(--text-primary); text-align: center; line-height: 1.25; min-width: 0; word-break: break-word;">${sharedTextHTML}${senseGlossDetailHTML(m, groupIsCurrent)}${modelProposalMarkerHTML(orderedMembers.some(memberIdx => card.meanings[memberIdx].modelProposed) ? { modelProposed: true } : null)}</div>`
                        : `<div class="group-card-shared" style="${sharedSpan} text-align: center; line-height: 1.25; min-width: 0; word-break: break-word;">${renderSenseContextHTML(m.context, { leadingDot: false })}</div>`;

                    // Body grid: shared + varying. The pct column lives in the
                    // outer grid; POS lives in the header legend.
                    const gridCols = isTransAxis ? 'fit-content(30%) minmax(0, 1fr)' : 'minmax(0, 1fr) fit-content(30%)';

                    // Outer row is body | pct stack. POS is represented once
                    // by the header legend and repeated through row colour.
                    const outerGridCols = '1fr auto';

                    target.push(`
                    <div class="meaning-row meaning-row-group ${groupedTextClass}${groupIsCurrent ? ' selected' : ''}${groupStateClasses}" data-axis="${axis}" onclick="selectGroup('${axis}', ${idx})" style="position: relative; display: grid; grid-template-columns: ${outerGridCols}; align-items: center; padding: 1px 2px; margin-bottom: 4px; background: ${cardBg}; border-radius: 8px; cursor: pointer;">
                        ${renderRowCheckSlot(groupIsCurrent)}
                        <div class="meaning-row-body group-card-body${sharedCleanLength > 48 ? ' has-long-shared' : ''}${maxMemberLength > 80 ? ' has-long-context' : ''}" style="display: grid; grid-template-columns: ${gridCols}; align-items: center; gap: 3px 6px; min-width: 0; width: 100%; max-width: 100%; box-sizing: border-box; padding: 4px 8px; background: ${sharedBg}; ${sharedBorder} border-radius: 6px; justify-self: center;">
                            ${memberCells}
                            ${sharedCellHtml}
                        </div>
                        ${pctColumnHtml}
                    </div>
                    `);
                } else {
                    if (compactKnowledgeView && !isSelected) return;
                    recordSectionMeanings(target, [m]);
                    const foldInfo = singletonFoldLeaders.get(idx);
                    const isFoldedLeader = !!foldInfo;
                    const isFoldActive = isFoldedLeader && foldInfo.allIndices.includes(currentMeaningIndex);
                    const isRowSelected = isFoldedLeader ? isFoldActive : isSelected;
                    const rowSelectedClasses = isRowSelected ? ' is-current-sense' : '';

                    // Individual sense row: 2-line presentation when space permits
                    // Primary gloss on top, cleaned context underneath (no redundant repetition of the gloss).
                    const metadataOptions = {
                        senseCount: card.meanings?.length || 1,
                        gloss: displayMeaning,
                        peerMeanings: senseMetadataPeers(m, card.meanings, displayMeaning),
                        allowInactivePrimary: true,
                    };
                    const rawContext = contextWithoutSenseMetadata(m, isRowSelected, metadataOptions);
                    let cleanedContext = cleanSenseContext(rawContext, displayMeaning);
                    if (cleanedContext && contextCollidesWithMetadata(
                        cleanedContext,
                        compactLearnerSenseMetadata(senseMetadataItems(m), m, metadataOptions)
                    )) {
                        cleanedContext = '';
                    }
                    let subContent = '';
                    if (cleanedContext) {
                        subContent += renderSenseContextHTML(cleanedContext, { leadingDot: false });
                    }
                    const metadataHtml = senseMetadataHTML(m, isRowSelected, metadataOptions);
                    if (metadataHtml) subContent += (subContent ? ' ' : '') + metadataHtml;
                    subContent += senseGlossDetailHTML(m, isRowSelected);
                    const regTag = registerTagHTML(m);
                    if (regTag) subContent += (subContent ? ' ' : '') + regTag;
                    const aiTag = modelProposalMarkerHTML(m);
                    if (aiTag) subContent += (subContent ? ' ' : '') + aiTag;

                    const differentiator = singletonDiffByMeaningIndex.get(idx);
                    if (differentiator && differentiator.score >= 60 && !subContent) {
                        if (differentiator.type === 'context') {
                            subContent = renderSenseContextHTML(differentiator.label, { leadingDot: false });
                        } else {
                            const family = escapeCardText(differentiator.type);
                            const shortLabel = escapeCardText(differentiator.label);
                            subContent = `<span class="sense-metadata-detail sense-pill sense-pill--${family}" data-family="${family}"><span class="sense-pill-label">${shortLabel}</span></span>`;
                        }
                    }

                    const singletonTextClass = adaptiveRowTextClass(displayMeaning, cleanedContext || differentiator?.label || '');
                    const useProminenceLabels = (typeof senseProminenceMode !== 'undefined' ? senseProminenceMode : globalThis.state?.senseProminenceMode) !== 'percentages';
                    const clusterInfo = glossProminence.infoByIndex.get(idx);
                    const clusterPooled = glossProminence.pooledIndexes.has(idx);
                    const promInfo = clusterInfo || (isFoldedLeader ? foldInfo.bestPromInfo : getSenseProminenceInfo(m));
                    const displayPctVal = clusterPooled
                        ? Math.min(100, Math.round((glossProminence.pooledShareByIndex.get(idx) || 0) * 100))
                        : (isFoldedLeader ? foldInfo.sumPctVal : pctVal);
                    const rareRowClass = isFoldedLeader
                        ? (foldInfo.hasOnlyRare ? ' meaning-row-rare' : '')
                        : ((m.unassigned || m.isRareSense || m.prominenceLabel === 'Rare') ? ' meaning-row-rare' : '');
                    const pctTail = useProminenceLabels
                        ? prominenceBadgeHTML(promInfo, 'position: absolute; right: 8px; top: 50%; transform: translateY(-50%);')
                        : (!m.unassigned && displayPctVal < 100
                            ? `<span class="sense-percentage sense-percentage-tail" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); pointer-events: none;">${displayPctVal}%</span>`
                            : (m.unassigned ? prominenceBadgeHTML({ label: 'Rare', key: 'rare' }, 'position: absolute; right: 8px; top: 50%; transform: translateY(-50%);') : ''));
                    const sidePad = useProminenceLabels ? '32px' : (!m.unassigned && displayPctVal < 100 ? '42px' : '10px');
                    target.push(`
                    <div class="meaning-row meaning-row-regular ${singletonTextClass}${isRowSelected ? ' selected' : ''}${rowSelectedClasses}${rareRowClass}" style="position: relative; display: flex; align-items: center; padding: 2px 2px; margin-bottom: 4px; background: ${bgColor}; ${borderStyle} border-radius: 8px; cursor: pointer; min-height: 44px;" onclick="selectMeaning(${idx})">
                        ${renderRowCheckSlot(isRowSelected)}
                        <div class="meaning-row-body" style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-width: 0; width: 100%; padding: 2px ${sidePad} 2px ${sidePad};">
                            <span class="meaning-row-translation meaning-row-gloss row-adaptive-text" style="font-weight: ${isRowSelected ? 700 : 600}; color: ${textColor}; text-align: center; width: 100%; line-height: 1.25;">${displayMeaningHTML}</span>
                            ${subContent ? `<span class="meaning-row-sub" style="text-align: center; width: 100%;">${subContent}</span>` : ''}
                        </div>
                        ${pctTail}
                    </div>
                    `);
                }
            }
        });
        // Emit the scroll region first, then the pinned tray underneath
        // (MWE/CLITIC rows that stay visible when the user scrolls).
        if (scrollSections.size > 0) {
            backHTML += `<div class="meanings-scroll">${renderSections(scrollSections)}</div>`;
        }
        // Expressions mode off keeps the pinned tray; on, MWE/CLITIC entries
        // leave silently as chain children (no on-card announcement).
        if (!expressionsModeEnabled && traySections.size > 0) {
            backHTML += `<div class="meanings-tray">${renderSections(traySections)}</div>`;
        }
        // Show current sentence
        // For MWE/Clitic senses, suppress the sentence block entirely when the
        // current expression has no matching examples — otherwise the card
        // keeps showing whatever was rendered for the previous expression.
        const isMWEOrCliticCycle = currentMeaning && (currentMeaning.allMWEs || currentMeaning.allClitics);
        let cycleHasExamples = true;
        if (isMWEOrCliticCycle) {
            const cycleList = currentMeaning.allMWEs || currentMeaning.allClitics;
            const cycleIdx = currentMWEIndex % cycleList.length;
            cycleHasExamples = (cycleList[cycleIdx].examples || []).length > 0;
        }

        const cardAutoplayAvailable = window.spotifySnippetSupported?.()
            && cardHasPlayableAutoplay(card);
        const cardAutoplayButton = cardAutoplayAvailable
            ? `<button type="button" id="exampleAutoplayBtn" class="example-autoplay-btn${_exampleAutoplayActive ? ' is-active' : ''}" aria-label="${_exampleAutoplayActive ? 'Stop lyric example autoplay' : 'Play lyric examples'}" aria-pressed="${_exampleAutoplayActive ? 'true' : 'false'}" title="${_exampleAutoplayActive ? 'Stop lyric autoplay' : 'Play lyric examples'}" onclick="toggleExampleAutoplay(event)"><span class="example-autoplay-icon" aria-hidden="true">${_exampleAutoplayActive ? '■' : '▶'}</span></button>`
            : '';

        // Keep the card-wide control reachable while autoplay passes through
        // a sense with no sentence box (or when the initially selected sense
        // has none but a later sense has a playable lyric).
        if ((!currentMeaning?.targetSentence || !cycleHasExamples) && cardAutoplayButton) {
            backHTML += `<div class="example-autoplay-fallback">${cardAutoplayButton}</div>`;
        }

        if (currentMeaning && cycleHasExamples) {
            // For MWE senses, get examples from the current MWE expression's own array
            let activeMweIdx = 0;
            if (currentMeaning.allMWEs) {
                activeMweIdx = currentMWEIndex % currentMeaning.allMWEs.length;
            } else if (currentMeaning.allClitics) {
                activeMweIdx = currentMWEIndex % currentMeaning.allClitics.length;
            }
            const activeExamples = getCyclableExamples(card, currentMeaning);

            // Nothing left to show? Skip emitting the sentence box below.
            // Same effect as `cycleHasExamples=false`: the row sits in the
            // tray with its expression pill + translation only, until the
            // user advances to an expression with matching evidence.
            // We still complete the variable computation here because
            // nothing in it is expensive or has side-effects — the only
            // suppression point is the `backHTML +=` at the bottom.
            const suppressSentenceBlock = (isMWEOrCliticCycle && activeExamples.length === 0)
                || (!isMWEOrCliticCycle && activeExamples.length === 0 && !currentMeaning.targetSentence);

            const hasMultipleExamples = activeExamples.length > 1;
            const exampleCount = activeExamples.length;

            // Get current example (for cycling through multiple examples)
            let displayTargetSentence = currentMeaning.targetSentence;
            let displayEnglishSentence = currentMeaning.englishSentence;
            let songName = null;
            let vocalistCredit = null;
            let exampleSourceLabel = null;
            let currentExample = null;

            let spotifyUrl = null;
            let spotifyTrackId = null;
            let positionMs = 60000;
            let endPositionMs = null;
            if (activeExamples.length > 0) {
                const exIdx = currentExampleIndex % activeExamples.length;
                const example = activeExamples[exIdx];
                currentExample = example;
                const dictName = example.dictionarySource
                    || (example.source === 'wiktionary' ? 'Wiktionary'
                        : (example.source === 'spanishdict' ? 'SpanishDict'
                            : (example.evidence === 'dictionary'
                                ? dictionaryProviderForMeaning(currentMeaning)
                                : null)));
                exampleSourceLabel = example.personalised
                    ? `Personalised practice · ${example.reinforcement_word}`
                    : (dictName
                        ? dictionaryProviderCredit(dictName, example.source_url || example.sentence_url)
                        : exampleProvenanceHTML(example));
                window._currentDisplayedExample = example;
                const exTarget = example.target || example.spanish || '';
                const exEnglish = example.english || '';
                if (exTarget) {
                    displayTargetSentence = exTarget;
                    displayEnglishSentence = exEnglish;
                }
                songName = example.song_name || null;
                vocalistCredit = Array.isArray(example.vocalists) && example.vocalists.length
                    ? example.vocalists.join(' & ')
                    : null;
                positionMs = example.timestamp_ms ?? 60000;
                endPositionMs = example.end_timestamp_ms ?? null;

                // Look up Spotify track URL for this song
                spotifyTrackId = getSpotifyTrackIdForExample(example);
                if (spotifyTrackId) {
                    spotifyUrl = `https://open.spotify.com/track/${spotifyTrackId}`;
                }

                if (songName && example.artist) {
                    const allConfigs = window._allArtistsConfig;
                    const selectedSlugs = window._selectedArtistSlugs || [];
                    if (selectedSlugs.length > 1 && allConfigs && allConfigs[example.artist]) {
                        songName = allConfigs[example.artist].name + ' \u2014 ' + songName;
                    }
                }
            }

            // In production direction the answer may intentionally be the
            // shared lemma (merged cards) or the complete pronominal citation
            // (`quejarse`). Preserve the exact form evidenced by this example
            // (`está`, `se queja`) as a compact secondary answer cue.
            const exampleProductionForm = isFlipped
                ? getExampleProductionForm(
                    card,
                    currentMeaning,
                    currentExample,
                    displayTargetSentence
                )
                : '';
            const showExampleProductionForm = Boolean(
                exampleProductionForm
                && foldSurfaceForm(exampleProductionForm) !== foldSurfaceForm(activeProductionAnswer)
            );

            const useCanonicalMarkup = Boolean(currentExample?.canonical);
            if (useCanonicalMarkup) {
                displayTargetSentence = highlightWithDeclaredOffsets(
                    currentExample.target || displayTargetSentence,
                    currentExample.bold_text_offsets
                );
                displayEnglishSentence = highlightWithDeclaredOffsets(
                    currentExample.english || displayEnglishSentence,
                    currentExample.bold_translation_offsets
                );
            } else {
            // Truncate sentences longer than 20 words
            displayTargetSentence = truncateText(displayTargetSentence, 20);
            displayEnglishSentence = truncateText(displayEnglishSentence, 20);

            // Locate the studied word with the active POS colour. A low tint
            // plus underline keeps the sentence readable; related deck words
            // use the quieter companion treatment below.
            if (currentMeaning.allMWEs) {
                // Expression families keep their familiar canonical label,
                // but the lyric may contain another observed morphological
                // form. Highlight the form that this exact example carries.
                const activeMwe = currentMeaning.allMWEs[activeMweIdx];
                const matchedForm = _matchedMweForm(
                    activeMwe, displayTargetSentence,
                    currentExample?.matched_surface || currentExample?.matched_variant);
                if (matchedForm) {
                    displayTargetSentence = displayTargetSentence.replace(
                        _mweRegex(matchedForm, 'giu'),
                        '<span class="example-word-highlight">$1</span>');
                }
            } else if (currentMeaning.allClitics) {
                const activeClitic = currentMeaning.allClitics[activeMweIdx];
                if (activeClitic?.form) {
                    const escaped = activeClitic.form.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const regex = _cachedRegex(
                        `(?<![\\p{L}\\p{N}])(${escaped})(?![\\p{L}\\p{N}])`, 'giu');
                    displayTargetSentence = displayTargetSentence.replace(
                        regex, '<span class="example-word-highlight">$1</span>');
                }
            } else {
                // Highlight the exact occurrence spelling supplied by the
                // evidence layer. POS and sense work used its restored
                // canonical form, but the sentence still contains what was
                // sung (cometamo’, pa’, vo’a, etc.).
                const occurrence = resolveExampleOccurrence(
                    card, currentExample, displayTargetSentence);
                const regex = exampleOccurrenceSurfaceRegex(occurrence.surface);
                if (regex) {
                    const nonCanonical = foldSurfaceForm(occurrence.surface)
                        !== foldSurfaceForm(card.targetWord);
                    // How the form was found is part of what the learner is
                    // being shown. A declared occurrence is evidence; a stem
                    // left by peeling an enclitic, or a form matched by
                    // resemblance, is this app's inference and says so.
                    const title = occurrence.kind === 'enclitic'
                        ? 'The verb this form attaches a pronoun to'
                        : occurrence.kind === 'inferred'
                            ? 'Closest form to this word in this example'
                            : 'Recorded form in this example';
                    const inferredClass = occurrence.kind === 'declared'
                        ? '' : ' example-inferred-form';
                    displayTargetSentence = displayTargetSentence.replace(
                        regex,
                        nonCanonical
                            ? `<span class="example-word-highlight example-pooled-form${inferredClass}" title="${title}">$1</span>`
                            : '<span class="example-word-highlight">$1</span>'
                    );
                }
            }

            // Surface a literal companion match as a possible realization of
            // the SpanishDict note, not as proven WSD evidence. Same-sentence
            // co-occurrence does not establish that a/de/con/etc. attaches to
            // the target; the distinct style and tooltip make that limitation
            // explicit until a future syntax-aware evidence layer exists.
            const spanishDictUsage = selectedLanguage === 'spanish'
                ? parseSpanishDictUsageContext(currentMeaning.context)
                : null;
            const usageMatch = spanishDictUsage
                ? highlightPossibleSpanishDictUsage(
                    displayTargetSentence, spanishDictUsage, card.targetWord)
                : { html: displayTargetSentence, candidates: [] };
            displayTargetSentence = usageMatch.html;
            const usageCandidateKeys = new Set(usageMatch.candidates.map(
                form => form.toLocaleLowerCase('es')));

            // Highlight other study set words in the sentence (same style for now)
            const deckWords = getDeckWords();
            const targetLower = card.targetWord.toLowerCase();
            for (const dw of deckWords) {
                if (dw === targetLower || dw.length <= 2
                    || usageCandidateKeys.has(dw.toLocaleLowerCase('es'))) continue;
                // Skip if already inside a <span> tag (already highlighted)
                const dwEscaped = dw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const dwRegex = _cachedRegex(`(?<![\\p{L}\\p{N}])(${dwEscaped})(?![\\p{L}\\p{N}])(?![^<]*>)`, 'giu');
                displayTargetSentence = displayTargetSentence.replace(dwRegex,
                    '<span class="example-related-highlight">$1</span>');
            }

            // Highlight the English translation in the English sentence for keyword-assigned examples
            const exampleMethod = currentExample && currentExample.assignment_method;
            if (exampleMethod && exampleMethod.includes('keyword') && currentMeaning && currentMeaning.meaning && displayEnglishSentence) {
                // Split on commas/semicolons to try each translation fragment
                const fragments = currentMeaning.meaning.split(/[,;]/).map(f => f.trim()).filter(f => f.length > 1);
                for (const frag of fragments) {
                    const fragEscaped = frag.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const fragRegex = _cachedRegex(`(?<![\\p{L}\\p{N}])(${fragEscaped})(?![\\p{L}\\p{N}])(?![^<]*>)`, 'giu');
                    displayEnglishSentence = displayEnglishSentence.replace(fragRegex,
                        '<span class="example-related-highlight">$1</span>');
                }
            }
            }

            // Build example counter: shows count for current MWE's examples, not total MWEs
            // The dotted strip is the only visible position cue; the fraction
            // lived next to it and forced the learner to read "5 of 30".
            const exampleTicks = hasMultipleExamples
                ? exampleTicksHTML(currentExampleIndex % exampleCount, exampleCount)
                : '';
            // Breakdown button removed — English translation is now clickable instead
            const spotifySvg = `<svg width="44" height="44" viewBox="0 0 24 24" fill="#1DB954"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>`;
            // A press-and-hold on the Spotify button toggles card-wide
            // autoplay (merged from the old standalone button); a quick tap
            // still plays the track. Only wire the long-press when autoplay
            // is actually available — otherwise behave exactly as before.
            const spotifyBtnActiveClass = cardAutoplayAvailable && _exampleAutoplayActive ? ' autoplay-active' : '';
            const spotifyBtn = spotifyTrackId
                ? `<button type="button" class="spotify-btn${spotifyBtnActiveClass}" data-track-id="${spotifyTrackId}" data-position-ms="${positionMs}" title="${cardAutoplayAvailable ? 'Play in Spotify · hold to toggle lyric autoplay' : 'Play in Spotify'}" style="cursor:pointer; margin:0;" onclick="spotifyBtnActivate(event, '${spotifyTrackId}', ${positionMs})" ontouchend="spotifyBtnActivate(event, '${spotifyTrackId}', ${positionMs})"${cardAutoplayAvailable ? ` onmousedown="spotifyBtnPressStart(event)" onmouseup="spotifyBtnPressEnd()" onmouseleave="spotifyBtnPressEnd()" ontouchstart="spotifyBtnPressStart(event)" ontouchcancel="spotifyBtnPressEnd()"` : ''}>${spotifySvg}</button>`
                : (spotifyUrl ? `<a href="${spotifyUrl}" target="_blank" class="spotify-btn" title="Open in Spotify">${spotifySvg}</a>` : '');
            // Card-wide availability keeps this visible even when only a
            // later sense has a playable clip. Once a Spotify button is on
            // screen, autoplay control is reached by holding it instead of a
            // second icon — this fallback stays only for senses with no
            // Spotify link at all.
            const autoplayBtn = spotifyTrackId ? '' : cardAutoplayButton;
            const creditStart = songName
                ? `<span class="example-song-credit">— ${songName}${vocalistCredit ? `<span class="example-vocalist-credit"> · ${vocalistCredit}</span>` : ''}</span>`
                : (exampleSourceLabel
                    ? `<span class="example-song-credit">${exampleSourceLabel}</span>`
                    : '');
            const creditEnd = `${autoplayBtn}${spotifyBtn}`;
            const songNameDisplay = (creditStart || creditEnd || exampleTicks) ? `
                <div class="example-credit-row${songName ? ' is-lyric' : ''}">
                    <span class="example-credit-start">${creditStart}</span>
                    <span class="example-credit-end">${exampleTicks}${creditEnd}</span>
                </div>
            ` : '';

            const cycleHandler = hasMultipleExamples ? 'onclick="cycleExample(event)"' : '';
            const cursorStyle = hasMultipleExamples ? 'cursor: pointer;' : '';

            // Determine if this example is genuinely assigned to this sense.
            // Per-example assignment_method is authoritative when present;
            // fall back to per-meaning for non-keyword methods (Gemini/biencoder).
            let exampleAssigned = false;
            if (currentExample && (currentExample.assignment_method || currentExample.canonical || currentExample.evidence === 'dictionary')) {
                exampleAssigned = true;  // this specific example was classified or is dictionary canonical
            } else if (currentMeaning && !currentMeaning.unassigned && !currentMeaning.assignment_method) {
                exampleAssigned = true;  // strong method (Gemini/biencoder) — all examples assigned
            }
            // MWE: check if the expression appears in the example sentence
            if (currentMeaning && currentMeaning.allMWEs && displayTargetSentence) {
                const activeMwe = currentMeaning.allMWEs[currentMWEIndex % currentMeaning.allMWEs.length];
                if (activeMwe?.expression) {
                    exampleAssigned = Boolean(_matchedMweForm(
                        activeMwe, displayTargetSentence,
                        currentExample?.matched_surface || currentExample?.matched_variant));
                }
            }
            // Clitic: check if the clitic form appears in the example sentence
            if (currentMeaning && currentMeaning.allClitics && displayTargetSentence) {
                const activeClitic = currentMeaning.allClitics[currentMWEIndex % currentMeaning.allClitics.length];
                if (activeClitic && activeClitic.form) {
                    const escaped = activeClitic.form.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const re = _cachedRegex('(?<![\\p{L}])' + escaped + '(?![\\p{L}])', 'iu');
                    exampleAssigned = re.test(displayTargetSentence.replace(/<[^>]*>/g, ''));
                }
            }
            const examplePos = currentMeaning.pos === 'SENSE_CYCLE'
                ? (currentMeaning.cycle_pos || 'X')
                : currentMeaning.pos;
            const sentenceStyle = `--sense-match-rgb: ${getPosAccentRgb(examplePos)}; border-color: transparent;`;

            // Only emit the sentence block if we have something worth
            // showing. For MWE / Clitic cycles where the filter left us
            // with zero examples that actually contain the expression,
            // suppressSentenceBlock is true and we skip entirely — the
            // row waits in the tray until the user moves to an expression
            // whose evidence carries a matching sentence.
            if (!suppressSentenceBlock) {
                backHTML += `
                    <div class="sentence${exampleAssigned ? ' example-is-matched' : ''}" style="text-align: center; ${cursorStyle} ${sentenceStyle}" ${cycleHandler}>
                        ${showExampleProductionForm ? `<div class="reverse-example-form"><span>In this example</span><strong>${escapeCardText(exampleProductionForm)}</strong></div>` : ''}
                        <div class="breakdown-trigger" style="margin-bottom: 8px; cursor: pointer;" onclick="showLyricBreakdown(event); event.stopPropagation();" title="Word by word">${displayTargetSentence}</div>
                        <div class="translation">${displayEnglishSentence}</div>
                        ${songNameDisplay}
                    </div>
                `;
            } else if (cardAutoplayButton) {
                // Raw Expression/clitic evidence can all disappear after the
                // exact-form filter. The ordinary sentence row is then hidden,
                // but card-wide autoplay must remain startable/stoppable.
                backHTML += `<div class="example-autoplay-fallback">${cardAutoplayButton}</div>`;
            }
        } else if (currentMeaning?.exampleOnly) {
            backHTML += `<div class="sentence search-example-empty">No example is available for this source entry yet.</div>`;
        }
    } else if (card.isChainChild) {
        // renderPhraseSummaryBack already rendered every phrase's example.
    } else {
        // Legacy format
        backHTML += `<div style="font-size: 28px; color: var(--text-primary); margin-top: 12px; font-weight: 600; text-align: center; margin-bottom: 20px;">${backTranslation}${modelProposalMarkerHTML(currentMeaning)}</div>`;

        // Show base form if different from displayed word
        if (card.inflectedForm && card.baseForm !== card.targetWord) {
            backHTML += `<div style="margin-bottom: 15px; font-size: 16px; text-align: center; color: #ffffff;"><strong style="color: var(--accent-secondary);">Base form:</strong> ${card.baseForm}</div>`;
        }

        // Show example sentences if available
        const sentenceCount = card.sentences ? card.sentences.length : 1;
        if (sentenceCount > 0) {
            const showEmpty = !exampleSentence && !exampleTranslation;
            const exampleProductionForm = isFlipped
                ? getExampleProductionForm(card, null, null, exampleTranslation)
                : '';
            const showExampleProductionForm = Boolean(
                exampleProductionForm
                && foldSurfaceForm(exampleProductionForm) !== foldSurfaceForm(card.productionAnswer)
            );
            const sentenceIndicator = sentenceCount > 1 ? `
                <div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 8px;">
                    <span style="color: var(--accent-primary); font-size: 18px;">↑</span>
                    <span style="color: var(--text-muted); font-size: 12px;">${currentSentenceIndex + 1} / ${sentenceCount}</span>
                    <span style="color: var(--accent-primary); font-size: 18px;">↓</span>
                </div>
            ` : '';

            backHTML += `
                ${sentenceIndicator}
                <div class="sentence" style="min-height: 80px; text-align: center;">
                    ${showExampleProductionForm ? `<div class="reverse-example-form"><span>In this example</span><strong>${escapeCardText(exampleProductionForm)}</strong></div>` : ''}
                    ${exampleSentence ? `<div class="example-sentence-text" style="margin-bottom: 8px;">${exampleSentence}</div>` : ''}
                    ${exampleTranslation ? `<div class="translation">${exampleTranslation}</div>` : ''}
                    ${showEmpty ? `<div style="color: var(--text-muted); text-align: center; padding: 20px;">(No example sentence)</div>` : ''}
                </div>
            `;
        }
    }

    // Reference links as icon buttons — real favicons via Google's proxy.
    // `conjugation` is not in this map: verb cards always get the unified
    // in-app conjugation toggle (red/yellow AR/ER/IR icon) instead of an
    // external link. The toggle's panel handles the no-data case with a
    // friendly message + SpanishDict link, so there's a single entry
    // point regardless of whether we ship inline conjugations for a
    // given lemma.
    const linkIcons = {
        'spanishDict': `<img src="https://www.google.com/s2/favicons?domain=spanishdict.com&sz=64" width="40" height="40" alt="SpanishDict" style="border-radius:4px">`,
        'reverso': `<img src="https://www.google.com/s2/favicons?domain=reverso.net&sz=64" width="40" height="40" alt="Reverso" style="border-radius:4px">`
    };
    const linkTitles = {
        'spanishDict': 'SpanishDict',
        'reverso': 'Reverso Context',
        'conjugation': 'Conjugate'
    };

    // Determine if current word is a verb
    let isVerb = false;
    if (card.isMultiMeaning && currentMeaning) {
        // Unassigned releases wrap browsable dictionary leaves in a
        // SENSE_CYCLE row. Its cycle POS remains the real grammatical POS and
        // must keep optional verb tools available without claiming WSD.
        const rawPos = currentMeaning.pos === 'SENSE_CYCLE'
            ? currentMeaning.cycle_pos
            : currentMeaning.pos;
        const pos = rawPos ? rawPos.toLowerCase() : '';
        isVerb = pos.includes('verb') || pos === 'v' || pos === 'vb';
    }

    if (card.isChainChild) {
        // No external reference links on the phrase-summary card — every
        // phrase's own content is already shown in the scrollable list.
    } else {
    const rareAndExprItems = collectRareAndExpressionItems(card);

    // Labelled tiles rather than a strip of near-identical circles — a name
    // under each icon reads faster. Fixed order left to right: rare uses,
    // known, synonyms, conjugate. Look up is emitted last and pinned to the
    // right edge (see .ref-lookup-btn's auto margin), so its position never
    // shifts with how many of the optional tiles a given card happens to have.
    // The tile row is dropped entirely on small phones (see @media in
    // style.css); the handoff row / example already earn that vertical
    // space there.
    backHTML += `<div class="links-section" id="linksSection">`;

    if (rareAndExprItems.length > 0) {
        const rCount = rareAndExprItems.filter(it => it.kind === 'RARE_SENSE').length;
        const eCount = rareAndExprItems.length - rCount;
        const parts = [];
        if (rCount) parts.push(`${rCount} rare sense${rCount === 1 ? '' : 's'}`);
        if (eCount) parts.push(`${eCount} expression${eCount === 1 ? '' : 's'}`);
        const detail = parts.join(' and ');
        backHTML += `<button type="button" class="ref-tile ref-rare-uses-btn" aria-label="Rarer uses: ${escapeCardText(detail)}" title="${escapeCardText(detail)}" onclick="event.stopPropagation(); openRareAndExpressionsCard(event);">
            <div class="ref-tile-icon-wrap">
                <svg class="ref-tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M12 3 13.2 8.1 18 9.3 13.2 10.5 12 15.6 10.8 10.5 6 9.3 10.8 8.1 12 3z"></path>
                    <path d="M19 14.2 19.6 16.4 21.8 17 19.6 17.6 19 19.8 18.4 17.6 16.2 17 18.4 16.4 19 14.2z"></path>
                    <path d="M16.4 4.2 16.8 5.6 18.2 6 16.8 6.4 16.4 7.8 16 6.4 14.6 6 16 5.6 16.4 4.2z"></path>
                </svg>
                ${rareAndExprItems.length > 0 ? `<span class="ref-tile-count-badge">${rareAndExprItems.length}</span>` : ''}
            </div>
            <span class="ref-tile-label">Rarer uses</span>
        </button>`;
    }

    // Granular sense/expression knowledge belongs in one card-wide overview,
    // not a persistent two-button strip under every meaning. The compact
    // trigger keeps the full inventory reachable without stealing sentence
    // space from the ordinary study flow.
    backHTML += renderKnowledgeOverviewButton(card);

    const hasSpanishDictData = canInspectSpanishDictData()
        && spanishDictMeaningsForCard(card).length > 0;
    if (hasSpanishDictData) {
        backHTML += `<button class="ref-tile ref-dictionary-btn" onclick="event.stopPropagation(); toggleSpanishDictPanel();">
            <svg class="ref-tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5z"></path>
                <path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5z"></path>
            </svg>
            <span class="ref-tile-label">Dictionary</span>
        </button>`;
    }

    const hasSynonyms = (card.synonyms && card.synonyms.length) || (card.antonyms && card.antonyms.length);
    if (hasSynonyms) {
        backHTML += `<button class="ref-tile ref-syn-btn" onclick="toggleSynonymsPanel()">
            <svg class="ref-tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M3.5 9.25q4.25-4 8.5 0t8.5 0"></path>
                <path d="M3.5 15.75q4.25-4 8.5 0t8.5 0"></path>
            </svg>
            <span class="ref-tile-label">Synonyms</span>
        </button>`;
    }

    const hasConjugationTable = Boolean(config.languages?.[selectedLanguage]?.conjugationsPath);
    if (isVerb && hasConjugationTable) {
        backHTML += `<button class="ref-tile ref-conj-btn" onclick="toggleConjugationTable()">
            <svg class="ref-tile-icon" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <g font-family="system-ui, -apple-system, sans-serif" font-weight="700" font-size="9.4" text-anchor="middle" letter-spacing="0.3" fill="currentColor">
                    <text x="16" y="10.5">-AR</text>
                    <text x="16" y="20">-ER</text>
                    <text x="16" y="29.5">-IR</text>
                </g>
            </svg>
            <span class="ref-tile-label">Conjugate</span>
        </button>`;
    }

    // Every external reference collapses into one "Look up" tile that opens
    // a small sheet — replaces the old per-favicon icon strip.
    const lookupLinks = Object.entries(card.links)
        .filter(([key]) => key !== 'wordReference' && key !== 'conjugation');
    if (lookupLinks.length > 0) {
        backHTML += `<button class="ref-tile ref-lookup-btn" onclick="event.stopPropagation(); toggleLookupSheet(event);">
            <svg class="ref-tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                <polyline points="15 3 21 3 21 9"></polyline>
                <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
            <span class="ref-tile-label">Look up</span>
        </button>
        <div class="lookup-sheet" id="lookupSheet" hidden>
            ${lookupLinks.map(([key, url]) => outboundChipHTML(
                url,
                `${linkIcons[key] || `<span class="lookup-sheet-initial">${(linkTitles[key] || key).charAt(0)}</span>`}`,
                linkTitles[key] || key,
                `class="lookup-sheet-icon" title="${linkTitles[key] || key}" aria-label="${linkTitles[key] || key}"`
            )).join('')}
        </div>`;
    }

    // Card Data + flag ("Card data" / "Report a card issue") now
    // live inside the study-options gear menu (see showStudyMenu in
    // initializeApp) instead of a second button on the card.

    backHTML += `</div>`;

    // Conjugation placeholder — empty div carrying the data needed to
    // build the panel lazily on first toggle. Lemma / related-lemma /
    // target-word land in data-attributes so flashcards-conj.js's
    // toggleConjugationTable() can read them, look up _conjugationData,
    // and call buildConjugationTableHTML on demand. See conj.js for the
    // per-(lemma, targetWord, isRelated) build cache.
    if (isVerb) {
        const attr = (s) => String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
        // Surface-only cards intentionally have no identity lemma. The
        // selected dictionary headword is lookup/display metadata and is the
        // correct join key for an optional conjugation layer.
        const conjugationHeadword = currentMeaning?.headword
            || (currentMeaning?.pos === 'SENSE_CYCLE'
                ? currentMeaning.allSenses?.find(sense => sense?.headword)?.headword
                : '')
            || card.citationForm
            || card.lemma
            || card.targetWord;
        const conjugationTarget = conjugationLookupSurface(card);
        backHTML += `<div id="conjugationTable" class="conjugation-panel" data-lemma="${attr(conjugationHeadword)}" data-related="${attr(card.relatedLemma)}" data-target="${attr(conjugationTarget)}"></div>`;
    }

    if (hasSynonyms) {
        backHTML += buildSynonymsPanelHTML(card.synonyms || [], card.antonyms || [], card.lemma || card.targetWord);
    }

    if (hasSpanishDictData) {
        backHTML += buildSpanishDictPanelHTML(card);
    }

    backHTML += buildProvenancePanelHTML(card);
    }

    const renderedBack = document.getElementById('backContent');
    const backDomChanged = renderedBack?._fluencyRenderedHTML !== backHTML;
    if (renderedBack && backDomChanged) {
        // The conjugation panel is hosted on <body> while open (it covers the
        // viewport, which it cannot do from inside the clipped, 3D-transformed
        // card). backHTML re-creates its placeholder, so drop any open copy
        // first — otherwise the previous card's paradigm survives the swap and
        // two nodes claim the same id.
        if (document.getElementById('conjugationTable')?.parentElement === document.body) {
            document.getElementById('conjugationTable').remove();
        }
        // Same for every docked card panel, and when the card itself changed,
        // the side sheets that described the old one (side-dock.js).
        window.sideDock?.beforeBackRender(card);
        renderedBack.innerHTML = backHTML;
        renderedBack._fluencyRenderedHTML = backHTML;
    }

    // Post-render layout pass:
    //   1. Flag meaning rows whose translation+context actually overflows the
    //      3-line clamp so the span becomes tap-to-expand. We only flag what
    //      measures as clipped, not everything past an arbitrary char count.
    //   2. If the total (meanings + tray + sentence + links) would overflow
    //      the card's content area, cap .meanings-scroll to the remaining
    //      space so IT scrolls — not the whole card. If everything fits, no
    //      cap is applied and flex-layout centres the block as normal.
    //
    // The cap is measured live: we sum every non-scroll child's rendered
    // height (+ its top/bottom margins) and subtract from backContent's
    // client height. That way the scroll threshold adapts to:
    //   - header wrapping to two lines (long word + lemma)
    //   - example sentence growing with longer lines
    //   - MWE / clitic tray being present or empty
    //   - expanded (tap-to-expand) sense rows taking more vertical space
    //
    // Previously there was a hardcoded "> 3 rows → cap at 3 rows" rule that
    // forced scrolling even when the card had plenty of room; this replaces
    // it with a genuine content-vs-space check.
    if (backDomChanged) {
        const backEl = document.getElementById('backContent');
        if (backEl) {
            // Cap the headword against the POS pill first: it can change the
            // header's height, which the scroll-cap measurement below reads.
            fitBackHeadword(backEl);
            fitSenseRowLayouts(backEl);
            fitPosSectionSummaries(backEl);
            fitExampleCreditRow(backEl);

            const scroll = backEl.querySelector('.meanings-scroll');
            if (scroll) {
                // Clear any prior cap before measuring the active group.
                scroll.style.maxHeight = '';
            }

            // Two-phase: collect overflowing rows in a read-only pass, then
            // add the .is-clamped class in a separate write pass. Mixing
            // reads and writes per row would force layout flush per row;
            // splitting keeps it to one flush total. The click handler
            // lives at module scope as a delegated listener (see bottom of
            // file), so no per-row addEventListener here.
            const toClamp = [];
            backEl.querySelectorAll('.meaning-row-translation').forEach(el => {
                if (el.scrollHeight > el.clientHeight + 1) toClamp.push(el);
            });
            for (const el of toClamp) el.classList.add('is-clamped');

            if (scroll) {
                const availableForScroll = availableHeightForMeaningScroll(backEl, scroll);
                // Cap meanings-scroll whenever its natural content overflows
                // the remaining room. Floor the cap value (not the gate) at
                // 60px so the scroller stays usable even when overhead is
                // tight, instead of silently disabling the cap.
                if (scroll.scrollHeight > availableForScroll) {
                    scroll.style.maxHeight = Math.max(100, availableForScroll) + 'px';
                    // Keep the stable menu order and move only the viewport.
                    // `nearest` avoids a jump when the selected row is already
                    // visible while still exposing a selection below the fold.
                    const activeSense = scroll.querySelector('.meaning-row.is-current-sense');
                    if (activeSense) requestAnimationFrame(() => activeSense.scrollIntoView({
                        behavior: 'auto', block: 'nearest', inline: 'nearest'
                    }));
                }
            }
        }
    }

    // Visual cue: this card was opened via search/synonym/lyric breakdown.
    // The .is-stacked class drives a peek-tab pseudo above the card.
    document.getElementById('flashcard').classList.toggle('is-stacked', cardNavStack.length > 0);
    // Chain-child cards (phrase/clitic handoff) swap the ordinary mobile nav
    // banner for a breadcrumb header — see .is-chain-child rules in style.css.
    document.getElementById('flashcard').classList.toggle('is-chain-child', card.isChainChild === true);

    // Child cards name their way out in the top bar rather than offering a
    // bare X on the card face: the learner should not have to remember which
    // card a search or synonym detour started from.
    const returnBtn = document.getElementById('cardBackReturn');
    if (returnBtn) {
        const onChildCard = cardNavStack.length > 0;
        returnBtn.hidden = !onChildCard;
        if (onChildCard) {
            const label = describeNavReturnTarget();
            document.getElementById('cardBackReturnLabel').textContent = label;
            returnBtn.setAttribute('aria-label', `Back to ${label}`);
        }
    }

    // Update frequency display (skip for peek/stacked cards and phrase-chain children)
    if (cardNavStack.length === 0 && !card.isChainChild) {
        stats.studied.add(currentIndex);
        updateStats();
    }

    // Update disabled state for all nav buttons
    const isPrevDisabled = currentIndex === 0;
    const isNextDisabled = currentIndex === flashcards.length - 1;
    document.getElementById('prevBtnFront').disabled = isPrevDisabled;
    document.getElementById('nextBtnFront').disabled = isNextDisabled;
    document.getElementById('prevBtnFrontMobile').disabled = isPrevDisabled;
    document.getElementById('nextBtnFrontMobile').disabled = isNextDisabled;

    // The phrase summary is a temporary card appended past the end of the deck
    // (see startPhraseChain). Scrubbing to it would send the marker to the far
    // end of the set and straight back again, which reads as a glitch rather
    // than as progress. Both scrubbers instead hold the parent's position and
    // recolour that marker for the duration of the chain.
    const onPhraseCard = card.isChainChild === true && cardChainReturnIndex >= 0;
    const scrubCount = onPhraseCard ? flashcards.length - 1 : flashcards.length;
    const scrubIndex = onPhraseCard ? cardChainReturnIndex : currentIndex;

    // Numbered active-set scrubber. It mirrors the level picker: the current
    // position is magnified, while any visible number can be selected directly.
    const progressSegments = document.getElementById('deckProgressSegments');
    if (progressSegments) {
        const segmentCount = scrubCount;
        if (progressSegments.childElementCount !== segmentCount) {
            progressSegments.replaceChildren(...Array.from({ length: segmentCount }, (_, i) => {
                const segment = document.createElement('button');
                segment.type = 'button';
                segment.className = 'deck-progress-segment';
                segment.textContent = String(i + 1);
                segment.dataset.cardIndex = String(i);
                segment.setAttribute('aria-label', `Go to card ${i + 1} of ${segmentCount}`);
                segment.addEventListener('click', event => {
                    event.stopPropagation();
                    if (Date.now() < _suppressDeckScrubberClickUntil) return;
                    goToDeckCard(i);
                });
                return segment;
            }));
        }
        Array.from(progressSegments.children).forEach((segment, i) => {
            const distance = Math.abs(i - scrubIndex);
            const result = stats.cardStats[i] || null;
            const hasCorrect = Number(result?.correct || 0) > 0;
            const hasIncorrect = Number(result?.incorrect || 0) > 0;
            const resultState = hasCorrect && hasIncorrect
                ? 'mixed'
                : (hasCorrect ? 'correct' : (hasIncorrect ? 'incorrect' : 'unanswered'));
            const isScrubCurrent = i === scrubIndex;
            segment.classList.toggle('is-visited', stats.studied.has(i));
            segment.classList.toggle('is-current', isScrubCurrent);
            // The marker stays put; its colour is what says "you're in phrases".
            segment.classList.toggle('is-phrases', onPhraseCard && isScrubCurrent);
            segment.classList.toggle('is-result-correct', resultState === 'correct');
            segment.classList.toggle('is-result-incorrect', resultState === 'incorrect');
            segment.classList.toggle('is-result-mixed', resultState === 'mixed');
            segment.dataset.distance = String(Math.min(distance, 4));
            segment.dataset.result = resultState;
            segment.setAttribute('aria-current', isScrubCurrent ? 'step' : 'false');
            segment.setAttribute('aria-label', onPhraseCard && isScrubCurrent
                ? `Card ${i + 1} of ${segmentCount} · phrases`
                : `Go to card ${i + 1} of ${segmentCount} · ${resultState}`);
        });
        const currentSegment = progressSegments.children[scrubIndex];
        if (currentSegment && !progressSegments.dataset.userScrolling) {
            requestAnimationFrame(() => currentSegment.scrollIntoView({
                behavior: _deckScrubberActive ? 'auto' : 'smooth', block: 'nearest', inline: 'center'
            }));
        }
    }

    // Seek bar above the card: current index on the thumb, ‹ › for ±1.
    const cardBackPips = document.getElementById('cardBackPips');
    if (cardBackPips) {
        const last = Math.max(0, scrubCount - 1);
        const t = last === 0 ? 0.5 : (scrubIndex / last);
        cardBackPips.style.setProperty('--cbs-t', String(t));
        const thumb = cardBackPips.querySelector('.cbs-thumb');
        const thumbNum = cardBackPips.querySelector('.cbs-thumb-num');
        if (thumbNum) thumbNum.textContent = String(scrubIndex + 1);
        thumb?.classList.toggle('is-phrases', onPhraseCard);
        cardBackPips.setAttribute('aria-valuenow', String(scrubIndex + 1));
        cardBackPips.setAttribute('aria-valuemax', String(Math.max(1, scrubCount)));
        cardBackPips.setAttribute('aria-valuetext', onPhraseCard
            ? `Card ${scrubIndex + 1} of ${scrubCount} · phrases`
            : `Card ${scrubIndex + 1} of ${scrubCount}`);
        cardBackPips.setAttribute('aria-label', onPhraseCard
            ? `Card ${scrubIndex + 1} of ${scrubCount} · phrases`
            : `Card ${scrubIndex + 1} of ${scrubCount}`);
    }

    // Drive ghost card visibility based on how many real cards exist behind each side
    const cardContainer = document.querySelector('.card-container');
    if (cardContainer) {
        cardContainer.classList.toggle('at-deck-start',   scrubIndex === 0);
        cardContainer.classList.toggle('at-deck-start-2', scrubIndex === 1);
        cardContainer.classList.toggle('at-deck-end',     scrubIndex === scrubCount - 1);
        cardContainer.classList.toggle('at-deck-end-2',   scrubIndex === scrubCount - 2);
    }

    // Setup outside nav buttons (desktop)
    const prevBtnOutside = document.getElementById('prevBtnFrontOutside');
    const nextBtnOutside = document.getElementById('nextBtnFrontOutside');
    if (prevBtnOutside) {
        prevBtnOutside.disabled = isPrevDisabled;
        prevBtnOutside.onclick = function(e) {
            e.stopPropagation();
            previousCard();
        };
    }
    if (nextBtnOutside) {
        nextBtnOutside.disabled = isNextDisabled;
        nextBtnOutside.onclick = function(e) {
            e.stopPropagation();
            nextCard();
        };
    }

    // Setup outside answer buttons (desktop only, hidden via CSS on mobile)
    const correctBtnOutside = document.getElementById('correctBtnOutside');
    const incorrectBtnOutside = document.getElementById('incorrectBtnOutside');

    if (correctBtnOutside && incorrectBtnOutside) {
        correctBtnOutside.onclick = function(e) {
            e.stopPropagation();
            handleSwipeAction('correct');
        };
        incorrectBtnOutside.onclick = function(e) {
            e.stopPropagation();
            handleSwipeAction('incorrect');
        };
    }

    if (announceHeadword && !isFlipped) {
        speakWord(getDisplayedTargetHeadword(card));
    }

    window.saveStudySessionSnapshot?.();
}

// A learner prompt into the tutorial (tutorial.js), not the visitor walkthrough.
// The stored key names predate that split; renaming them would re-prompt.
const CARD_TUTORIAL_PROMPT_KEY = 'fluencyCardTutorialPromptV1';
const CARD_TUTORIAL_SEEN_KEY = 'fluencyCardWalkthroughSeenV1';
let _cardTutorialPromptHandled = false;

function rememberCardTutorialPrompt() {
    _cardTutorialPromptHandled = true;
    try { localStorage.setItem(CARD_TUTORIAL_PROMPT_KEY, '1'); } catch (_) {}
}

function hasHandledCardTutorialPrompt() {
    if (_cardTutorialPromptHandled) return true;
    try {
        return localStorage.getItem(CARD_TUTORIAL_PROMPT_KEY) === '1'
            || localStorage.getItem(CARD_TUTORIAL_SEEN_KEY) === '1';
    } catch (_) { return false; }
}

function _cardTutorialPromptKeydown(event) {
    if (event.key !== 'Escape') return;
    event.stopPropagation();
    closeCardTutorialPrompt();
}

function closeCardTutorialPrompt({ immediate = false } = {}) {
    const modal = document.getElementById('cardTutorialPrompt');
    if (!modal) return;
    document.removeEventListener('keydown', _cardTutorialPromptKeydown, true);
    if (immediate || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
        modal.hidden = true;
        modal.classList.remove('is-closing');
        return;
    }
    modal.classList.add('is-closing');
    setTimeout(() => {
        modal.hidden = true;
        modal.classList.remove('is-closing');
    }, 180);
}

function ensureCardTutorialPrompt() {
    let modal = document.getElementById('cardTutorialPrompt');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'cardTutorialPrompt';
    modal.className = 'knowledge-overview-modal syn-leave-modal';
    modal.hidden = true;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'cardTutorialPromptTitle');
    modal.innerHTML = `
        <div class="knowledge-overview-sheet syn-leave-sheet">
            <div class="knowledge-overview-header">
                <div>
                    <span class="knowledge-overview-kicker">Quick card tour</span>
                    <h2 id="cardTutorialPromptTitle">Want to see how the back works?</h2>
                </div>
            </div>
            <p class="syn-leave-body">The tutorial explains sense rows, example sentences, percentages, and the controls you can tap.</p>
            <div class="syn-leave-actions">
                <button type="button" class="auth-cancel-btn" data-card-tutorial="dismiss">Not now</button>
                <button type="button" class="auth-submit-btn" data-card-tutorial="show">Show me</button>
            </div>
        </div>`;
    modal.addEventListener('click', event => {
        event.stopPropagation();
        const action = event.target.closest('[data-card-tutorial]')?.dataset.cardTutorial;
        if (action === 'show') {
            closeCardTutorialPrompt({ immediate: true });
            window.openCardTutorial?.();
        } else if (action === 'dismiss') {
            closeCardTutorialPrompt();
        }
    });
    document.body.appendChild(modal);
    return modal;
}

function maybeShowCardTutorialPrompt() {
    if (hasHandledCardTutorialPrompt()) return;
    // Do not stack onboarding over a dialog the learner opened during the flip.
    if (document.querySelector('.modal:not(.hidden), .knowledge-overview-modal:not([hidden])')) return;
    const modal = ensureCardTutorialPrompt();
    rememberCardTutorialPrompt();
    modal.hidden = false;
    document.addEventListener('keydown', _cardTutorialPromptKeydown, true);
    modal.querySelector('[data-card-tutorial="show"]')?.focus();
}

function flipCard() {
    // Chain children are back-only: there is no front content, so every flip
    // route (tap, keyboard, control button) is a no-op rather than a turn
    // onto a blank face.
    if (flashcards[currentIndex]?.isChainChild) return;
    stopExampleAutoplay(true);
    const flashcardEl = document.getElementById('flashcard');
    const wasFlipped = flashcardEl.classList.contains('flipped');
    flashcardEl.classList.toggle('flipped');
    const isNowFlipped = flashcardEl.classList.contains('flipped');
    // Docked panels live on <body>, outside the card, so they do not turn away
    // with the back face. Close them on the way to the front: a headword, a
    // dictionary entry or a paradigm would give the answer away.
    if (!isNowFlipped) window.sideDock?.closeForFront();

    const card = flashcards[currentIndex];
    if (!card) return;

    // Auto-speak based on flip state and language direction
    if (isNowFlipped) {
        // Just flipped to BACK of card
        if (isFlipped) {
            // English → Target mode: back shows target word, speak target
            speakWord(getActiveProductionAnswer(card), false);
        } else {
            // Target → English mode: back shows English, speak English meaning
            const spokenEnglish = getCurrentSpokenEnglish(card);
            if (spokenEnglish) speakWord(spokenEnglish, true);
        }
    } else {
        // Just flipped to FRONT of card
        if (isFlipped) {
            // English → Target mode: front shows English, speak English
            const spokenEnglish = getCurrentSpokenEnglish(card);
            if (spokenEnglish) speakWord(spokenEnglish, true);
        } else {
            // Target → English mode: front shows target word, speak target
            speakWord(getDisplayedTargetHeadword(card), false);
        }
    }
    if (!wasFlipped && isNowFlipped) setTimeout(maybeShowCardTutorialPrompt, 650);
    window.saveStudySessionSnapshot?.();
}

function getCyclableExamples(card, currentMeaning) {
    let examples;
    let activeMweIdx = 0;
    if (currentMeaning.allMWEs) {
        activeMweIdx = currentMWEIndex % currentMeaning.allMWEs.length;
        examples = dedupeExamples(currentMeaning.allMWEs[activeMweIdx].examples || []);
    } else if (currentMeaning.allClitics) {
        activeMweIdx = currentMWEIndex % currentMeaning.allClitics.length;
        examples = dedupeExamples(currentMeaning.allClitics[activeMweIdx].examples || []);
    } else if (currentGroupSelection?.members) {
        const merged = [];
        for (const meaningIndex of currentGroupSelection.members) {
            const member = card.meanings[meaningIndex];
            if (member?.allExamples) merged.push(...member.allExamples);
        }
        examples = dedupeExamples(merged);
    } else {
        examples = dedupeExamples(currentMeaning.allExamples || []);
    }

    if (examples.length > 1) examples = sortExamplesByRelevance(examples);

    if (currentMeaning.allMWEs) {
        const activeMwe = currentMeaning.allMWEs[activeMweIdx];
        if (activeMwe?.expression) {
            examples = examples.filter(example => {
                const target = example.target || example.spanish || '';
                return Boolean(_matchedMweForm(
                    activeMwe, target, example.matched_surface || example.matched_variant));
            });
        }
    } else if (currentMeaning.allClitics) {
        const cliticForm = currentMeaning.allClitics[activeMweIdx].form;
        if (cliticForm) {
            const escaped = cliticForm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            try {
                const matcher = _cachedRegex(
                    `(?<![\\p{L}])${escaped}(?![\\p{L}])`, 'iu');
                examples = examples.filter(example => {
                    const target = example.target || example.spanish || '';
                    return matcher.test(target);
                });
            } catch (_) {
                // Older browsers without Unicode property escapes keep the
                // unfiltered list, matching the renderer's previous fallback.
            }
        }
    }

    if (currentMeaning.allMWEs || currentMeaning.allClitics) return examples;
    if (examplesAllowCycling(examples)) return examples;
    return displayExamplesForSense(currentMeaning, examples, card);
}

function cycleExample(event) {
    // Don't cycle if tap was on the Spotify button or other interactive elements
    if (event.target.closest('.spotify-btn') || event.target.closest('.example-autoplay-btn')
            || event.target.closest('.breakdown-trigger')) return;
    stopExampleAutoplay(true);
    event.stopPropagation(); // Prevent card flip
    const card = flashcards[currentIndex];
    if (!card || !card.meanings) return;
    const currentMeaning = card.meanings[currentMeaningIndex];
    if (!currentMeaning) return;

    const examples = getCyclableExamples(card, currentMeaning);

    if (examples.length <= 1) return;

    currentExampleIndex = (currentExampleIndex + 1) % examples.length;
    updateCard();
}

function cycleExampleForward(event) {
    if (event) event.stopPropagation();
    stopExampleAutoplay(true);
    const card = flashcards[currentIndex];
    if (!card || !card.meanings) return;
    const currentMeaning = card.meanings[currentMeaningIndex];
    if (!currentMeaning) return;
    const examples = getCyclableExamples(card, currentMeaning);
    if (examples.length <= 1) return;
    currentExampleIndex = (currentExampleIndex + 1) % examples.length;
    updateCard();
}

function cycleExampleBackward(event) {
    if (event) event.stopPropagation();
    stopExampleAutoplay(true);
    const card = flashcards[currentIndex];
    if (!card || !card.meanings) return;
    const currentMeaning = card.meanings[currentMeaningIndex];
    if (!currentMeaning) return;
    const examples = getCyclableExamples(card, currentMeaning);
    if (examples.length <= 1) return;
    currentExampleIndex = (currentExampleIndex - 1 + examples.length) % examples.length;
    updateCard();
}

function cycleMWEForward(event) {
    if (event) event.stopPropagation();
    stopExampleAutoplay(true);
    const card = flashcards[currentIndex];
    const m = card && card.meanings[currentMeaningIndex];
    const items = m && (m.allMWEs || m.allClitics);
    if (items && items.length > 1) {
        currentMWEIndex = (currentMWEIndex + 1) % items.length;
        currentExampleIndex = 0;
        updateCard();
    }
}

function cycleMWEBackward(event) {
    if (event) event.stopPropagation();
    stopExampleAutoplay(true);
    const card = flashcards[currentIndex];
    const m = card && card.meanings[currentMeaningIndex];
    const items = m && (m.allMWEs || m.allClitics);
    if (items && items.length > 1) {
        currentMWEIndex = (currentMWEIndex - 1 + items.length) % items.length;
        currentExampleIndex = 0;
        updateCard();
    }
}

function selectMeaning(index) {
    stopExampleAutoplay(true);
    // Picking a sense collapses whichever other part of speech was open, the
    // same way choosing from a section header does. Without this, selecting
    // through the rows left every previously visited section expanded and the
    // back grew a screen at a time.
    const selecting = flashcards[currentIndex];
    if (selecting?.meanings?.[index] && !selecting.isChainChild) {
        const key = lemmaPosGroupKeyForMeaning(selecting.meanings[index]);
        if (key) {
            selecting._expandedPos = selecting._expandedPos || new Set();
            selecting._expandedPos.add(key);
            selecting._backSectionsManuallySet = true;
        }
    }
    if (index === currentMeaningIndex && !currentGroupSelection) {
        // Already selected — cycle if this is a cycling pill (MWE/clitic/sense cycle)
        const card = flashcards[currentIndex];
        const m = card && card.meanings[index];
        if (m && m.allMWEs && m.allMWEs.length > 1) {
            currentMWEIndex = (currentMWEIndex + 1) % m.allMWEs.length;
            currentExampleIndex = 0;
            updateCard();
            return;
        }
        if (m && m.allClitics && m.allClitics.length > 1) {
            currentMWEIndex = (currentMWEIndex + 1) % m.allClitics.length;
            currentExampleIndex = 0;
            updateCard();
            return;
        }
        if (m && m.allSenses && m.allSenses.length > 1) {
            currentMWEIndex = (currentMWEIndex + 1) % m.allSenses.length;
            currentExampleIndex = 0;
            updateCard();
            return;
        }
    }
    // Clicking a sub-row exits group-selection mode and pins the chosen meaning.
    currentGroupSelection = null;
    currentMeaningIndex = index;
    const selectedCard = flashcards[currentIndex];
    const selectedMeaning = selectedCard?.meanings?.[index];
    const selectedPos = selectedMeaning?.pos === 'SENSE_CYCLE'
        ? (selectedMeaning.cycle_pos || 'X')
        : selectedMeaning?.pos;
    if (selectedPos && !['MWE', 'CLITIC', 'EXAMPLE_ONLY'].includes(selectedPos)) {
        selectedCard._activePosTab = selectedPos;
    }
    _explicitMeaningSelectionKey = meaningSelectionKey(flashcards[currentIndex], index);
    currentExampleIndex = 0;
    currentMWEIndex = 0;
    updateCard();
}

function selectPartOfSpeech(event, meaningIndex, pos) {
    event?.stopPropagation();
    stopExampleAutoplay(true);
    const card = flashcards[currentIndex];
    if (!card?.meanings?.[meaningIndex]) return;
    card._activePosTab = pos;
    currentGroupSelection = null;
    currentMeaningIndex = meaningIndex;
    currentExampleIndex = 0;
    currentMWEIndex = 0;
    _explicitMeaningSelectionKey = meaningSelectionKey(card, meaningIndex);
    // Choosing a part of speech expands that section and collapses the rest,
    // rather than adding to whatever was already open. Only one set of senses
    // is ever on screen, which is what pays for the legend's own line above —
    // and it makes the legend a real chooser rather than a filter that
    // accumulates.
    card._expandedPos = new Set([lemmaPosGroupKeyForMeaning(card.meanings[meaningIndex])]);
    card._backSectionsManuallySet = true;
    updateCard();
}

// Single (non-tab) POS pill: toggles the hidden-by-default verb morphology
// row beneath it. Only rendered as a button when morphology exists to show.
// One handler for both faces. The popover is always the pill's own next
// sibling, so there is no measuring, no card state, and no re-render — the old
// version round-tripped through updateCard() to flip a flag, which rebuilt the
// whole face just to reveal three words.
function toggleMorphPopover(event) {
    event?.stopPropagation();
    event?.preventDefault();
    const pill = event?.currentTarget;
    const popover = pill?.parentElement?.querySelector('.morph-popover');
    if (!popover) return;

    const opening = popover.hidden;
    document.querySelectorAll('.morph-popover').forEach(other => {
        other.hidden = true;
        other.parentElement?.querySelector('.has-morph-toggle')
            ?.setAttribute('aria-expanded', 'false');
    });
    popover.hidden = !opening;
    pill.setAttribute('aria-expanded', String(opening));

    if (opening) {
        // Same dismiss pattern as the lookup sheet: next outside click closes
        // it. Deferred so this very click doesn't immediately dismiss.
        setTimeout(() => {
            document.addEventListener('click', function dismiss(e) {
                if (popover.contains(e.target) || pill.contains(e.target)) return;
                popover.hidden = true;
                pill.setAttribute('aria-expanded', 'false');
                document.removeEventListener('click', dismiss);
            });
        }, 0);
    }
}

// The "+" inside the morphology popover reveals the remaining complete
// analyses. They are whole coupled rows (subject + tense/mood), never loose
// tokens, so expanding cannot make it ambiguous which person belongs to which
// tense. Local DOM toggle only — no re-render, and the outside-click dismiss
// installed by toggleMorphPopover() ignores clicks inside the popover.
function toggleMorphAlternatives(event) {
    event?.stopPropagation();
    event?.preventDefault();
    const button = event?.currentTarget;
    const list = button?.parentElement?.querySelector('.morph-pop-alts');
    if (!list) return;
    const opening = list.hidden;
    list.hidden = !opening;
    button.setAttribute('aria-expanded', String(opening));
    button.classList.toggle('is-open', opening);
    const sign = button.querySelector('.morph-pop-more-sign');
    if (sign) sign.textContent = opening ? '−' : '+';
}

function toggleFrontProductionHint(event) {
    event?.stopPropagation();
    event?.preventDefault();
    const button = event?.currentTarget;
    const host = button?.closest('.front-production-hint');
    const cloze = host?.querySelector('.front-production-cloze');
    if (!button || !cloze) return;
    const opening = cloze.hidden;
    cloze.hidden = !opening;
    button.setAttribute('aria-expanded', String(opening));
    button.classList.toggle('is-open', opening);
    const label = button.querySelector('.front-production-hint-label');
    if (label) label.textContent = opening ? 'Hide hint' : 'Sentence hint';
}

// The card-wide knowledge overview can jump directly to any individual item,
// including a later Expression/clitic in a shared cycling row. Stamp the same
// explicit-selection key as a sub-row click so updateCard() does not
// immediately expand that sense back into its overarching duplicate group.
function focusKnowledgeCardItem(meaningIndex, cycleIndex = 0) {
    stopExampleAutoplay(true);
    const card = flashcards[currentIndex];
    if (!card?.meanings?.[meaningIndex]) return;
    currentGroupSelection = null;
    currentMeaningIndex = meaningIndex;
    currentMWEIndex = Math.max(0, Number(cycleIndex) || 0);
    currentExampleIndex = 0;
    _explicitMeaningSelectionKey = meaningSelectionKey(card, meaningIndex);
    updateCard();
}

// Click handler for the shared field of a group card. It uses the renderer's
// effective member set (with a derivation fallback) so the inline onclick
// stays trivial and overlapping duplicate groups do not absorb one another.
// The anchor remains currentMeaning for downstream code that expects one.
//
// Group membership includes the anchor's lemma and POS so a grouped row never
// crosses the lemma–POS section boundary rendered above it.
function selectGroup(axis, anchorIdx) {
    stopExampleAutoplay(true);
    const card = flashcards[currentIndex];
    if (!card || !card.meanings || !card.meanings[anchorIdx]) return;
    const anchor = card.meanings[anchorIdx];
    let groupKey;
    let members;
    if (axis === 'translation') {
        groupKey = anchor.meaning || '';
    } else {
        groupKey = anchor.context || '';
    }
    const effectiveKey = `${anchor.pos}\u0000${anchor.headword || ''}\u0000${axis}\u0000${groupKey}`;
    members = card._grouping?.groupMembers?.get(effectiveKey);
    if (!members) {
        const field = axis === 'translation' ? 'meaning' : 'context';
        members = card.meanings
            .map((mm, i) => ({ mm, i }))
            .filter(({ mm }) => mm.pos === anchor.pos
                && (mm.headword || '') === (anchor.headword || '')
                && (mm[field] || '') === groupKey)
            .map(({ i }) => i);
    }
    if (members.length < 2) return;
    _explicitMeaningSelectionKey = null;
    currentGroupSelection = {
        axis,
        groupKey,
        pos: anchor.pos,
        headword: anchor.headword || '',
        members,
    };
    currentMeaningIndex = anchorIdx;
    currentExampleIndex = 0;
    currentMWEIndex = 0;
    updateCard();
}

function _navCard(direction) {
    stopExampleAutoplay(true);
    const cardEl = document.getElementById('flashcard');
    if (!cardEl || cardEl.classList.contains('nav-exiting')) return false;
    const isNext = direction === 'next';

    // Animation only runs on desktop — on mobile skip straight to update
    if (window.innerWidth < 768) {
        if (isNext) currentIndex++;
        else currentIndex--;
        currentMeaningIndex = 0;
        currentExampleIndex = 0;
        currentMWEIndex = 0;
        currentGroupSelection = null;
        cardEl.classList.remove('flipped');
        updateCard({ announceHeadword: true });
        return true;
    }

    const wasFlipped = cardEl.classList.contains('flipped');
    const exitClass = isNext
        ? (wasFlipped ? 'nav-exit-left-f' : 'nav-exit-left')
        : (wasFlipped ? 'nav-exit-right-f' : 'nav-exit-right');
    const exitAnim = isNext
        ? (wasFlipped ? 'card-exit-left-f' : 'card-exit-left')
        : (wasFlipped ? 'card-exit-right-f' : 'card-exit-right');
    const enterClass = isNext ? 'nav-enter-right' : 'nav-enter-left';
    const enterAnim = isNext ? 'card-enter-right' : 'card-enter-left';

    cardEl.classList.add('nav-exiting', exitClass);
    cardEl.addEventListener('animationend', function onExit(e) {
        if (e.animationName !== exitAnim) return;
        cardEl.removeEventListener('animationend', onExit);
        cardEl.classList.remove('nav-exiting', exitClass, 'flipped');

        if (isNext) currentIndex++;
        else currentIndex--;
        currentMeaningIndex = 0;
        currentExampleIndex = 0;
        currentMWEIndex = 0;
        currentGroupSelection = null;
        updateCard({ announceHeadword: true });

        void cardEl.offsetWidth;
        cardEl.classList.add(enterClass);
        cardEl.addEventListener('animationend', function onEnter(e2) {
            if (e2.animationName !== enterAnim) return;
            cardEl.classList.remove(enterClass);
            cardEl.removeEventListener('animationend', onEnter);
        });
    });
    return true;
}

// Relative scrub: a short pull is one card; a long plateau keeps that
// step until the drag is clearly meant to skip farther.
const CBS_SCRUB_COMMIT_PX = 18;
const CBS_SCRUB_HOLD_PX = 72;
const CBS_SCRUB_SKIP_PX = 36;

function cardOffsetFromScrubDelta(dx) {
    const sign = dx < 0 ? -1 : 1;
    const distance = Math.abs(dx);
    if (distance < CBS_SCRUB_COMMIT_PX) return 0;
    if (distance < CBS_SCRUB_HOLD_PX) return sign;
    return sign * (2 + Math.floor((distance - CBS_SCRUB_HOLD_PX) / CBS_SCRUB_SKIP_PX));
}

// Arrow/button navigation off an ungraded phrase card is an exit from the
// chain, not a step within the deck array: the temp card sits past the end, so
// plain index arithmetic would strand it. Resolve both directions against the
// parent's real position and let goToDeckCard do the cleanup.
function previousCard() {
    if (flashcards[currentIndex]?.isChainChild) return goToDeckCard(cardChainReturnIndex);
    if (currentIndex > 0) _navCard('prev');
}

function nextCard() {
    if (flashcards[currentIndex]?.isChainChild) return goToDeckCard(cardChainReturnIndex + 1);
    if (currentIndex < flashcards.length - 1) _navCard('next');
}

function goToDeckCard(index, { announceHeadword = true } = {}) {
    const nextIndex = Number(index);
    if (!Number.isInteger(nextIndex) || nextIndex < 0) return;
    // Drop the ungraded phrase card first: its slot is past the end of the real
    // deck, so the bounds check below has to run against the restored length.
    abandonPhraseChain();
    if (nextIndex >= flashcards.length || nextIndex === currentIndex) return;
    stopExampleAutoplay(true);
    currentIndex = nextIndex;
    currentMeaningIndex = 0;
    currentExampleIndex = 0;
    currentMWEIndex = 0;
    currentGroupSelection = null;
    document.getElementById('flashcard')?.classList.remove('flipped');
    updateCard({ announceHeadword });
}

function shuffleCards() {
    for (let i = flashcards.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [flashcards[i], flashcards[j]] = [flashcards[j], flashcards[i]];
    }
    currentIndex = 0;
    updateCard({ announceHeadword: true });
}

function flipDirection() {
    isFlipped = !isFlipped;
    window.saveGlobalStudyPreference?.('directionFlipped', isFlipped);
    document.getElementById('flashcard').classList.remove('flipped');
    updateCard();
}

function getPosColorClass(pos) {
    if (!pos) return 'pos-other';
    const posLower = String(pos).trim().toLowerCase().replace(/[\s-]+/g, '_');
    if (posLower === 'propn' || posLower === 'proper_noun' || posLower === 'propernoun') return 'pos-propn';
    if (posLower.includes('noun') || posLower === 'n' || posLower === 'nn') return 'pos-noun';
    if (posLower === 'aux' || posLower === 'auxiliary') return 'pos-aux';
    if (posLower.includes('verb') || posLower === 'v' || posLower === 'vb') return 'pos-verb';
    if (posLower.includes('adj') || posLower === 'a' || posLower === 'jj') return 'pos-adj';
    if (posLower.includes('adv') || posLower === 'rb') return 'pos-adv';
    if (posLower.includes('prep') || posLower === 'in' || posLower === 'adp') return 'pos-prep';
    if (posLower === 'cconj' || posLower === 'coordinating_conjunction' || posLower === 'cc') return 'pos-cconj';
    if (posLower === 'sconj' || posLower === 'subordinating_conjunction') return 'pos-sconj';
    if (posLower.includes('conj')) return 'pos-conj';
    if (posLower.includes('pron') || posLower === 'prp') return 'pos-pron';
    if (posLower.includes('det') || posLower === 'dt') return 'pos-det';
    if (posLower.includes('int') || posLower === 'uh') return 'pos-int';
    if (posLower.includes('num') || posLower === 'cd') return 'pos-num';
    if (posLower === 'mwe' || posLower === 'phrase') return 'pos-mwe';
    if (posLower === 'clitic') return 'pos-clitic';
    if (posLower === 'part' || posLower === 'particle') return 'pos-part';
    if (posLower === 'prefix') return 'pos-prefix';
    if (posLower === 'suffix') return 'pos-suffix';
    if (posLower === 'contraction') return 'pos-contraction';
    return 'pos-other';
}

function getPosAccentRgb(pos) {
    const accents = {
        'pos-noun': '74, 158, 255',
        'pos-propn': '14, 165, 233',
        'pos-verb': '0, 212, 170',
        'pos-aux': '45, 212, 191',
        'pos-adj': '245, 166, 35',
        'pos-adv': '168, 85, 247',
        'pos-prep': '236, 72, 153',
        'pos-conj': '20, 184, 166',
        'pos-cconj': '34, 197, 94',
        'pos-sconj': '132, 204, 22',
        'pos-pron': '99, 102, 241',
        'pos-det': '244, 63, 94',
        'pos-int': '234, 179, 8',
        'pos-num': '6, 182, 212',
        'pos-mwe': '251, 191, 36',
        'pos-clitic': '249, 115, 22',
        'pos-part': '192, 132, 252',
        'pos-prefix': '163, 230, 53',
        'pos-suffix': '74, 222, 128',
        'pos-contraction': '248, 113, 113',
        'pos-other': '148, 163, 184'
    };
    return accents[getPosColorClass(pos)] || 'var(--accent-primary-rgb)';
}

function updateReverseButton() {
    const reverseBtn = document.getElementById('reverseLangBtn');
    if (!reverseBtn) return;

    // Map language codes to flag emojis
    const flagMap = {
        'dutch': '🇳🇱',
        'polish': '🇵🇱',
        'spanish': '🇪🇸',
        'italian': '🇮🇹',
        'french': '🇫🇷',
        'russian': '🇷🇺',
        'swedish': '🇸🇪',
        'portuguese': '🇵🇹',
        'czech': '🇨🇿'
    };

    const targetFlag = config.languages?.[selectedLanguage]?.flag || flagMap[selectedLanguage] || '🇵🇹';
    const englishFlag = '🇬🇧';

    const fromFlag = isFlipped ? englishFlag : targetFlag;
    const toFlag = isFlipped ? targetFlag : englishFlag;
    const title = isFlipped
        ? `Reverse to ${config.languages[selectedLanguage]?.name || selectedLanguage} → English`
        : `Reverse to English → ${config.languages[selectedLanguage]?.name || selectedLanguage}`;
    const renderKey = `${fromFlag}|${toFlag}|${title}`;
    if (reverseBtn.dataset.renderKey === renderKey) return;
    reverseBtn.dataset.renderKey = renderKey;
    reverseBtn.innerHTML = `<span class="reverse-flag-from">${fromFlag}</span><span class="reverse-swap-glyph" aria-hidden="true">⇄</span><span class="reverse-flag-to" aria-hidden="true">${toFlag}</span>`;
    reverseBtn.title = title;
}

function updateStats() {
    // Stats are now displayed in modal only
}



// Scan the cached vocab index for a card matching the given word.
// Matches surface, lemma, or meaning headword, case-insensitive.
// Used by the synonyms panel: tap-a-synonym should jump to its card if we
// have one, otherwise fall back to the language's dictionary lookup.
function findCardIdForWord(word) {
    const target = (word || '').toLowerCase();
    if (!target) return null;
    const source = (activeArtist && window._cachedMergedIndex)
        ? window._cachedMergedIndex
        : window._cachedJoinedIndex;
    if (!source) return null;
    for (const it of source) {
        const w = (it.word || it.targetWord || '').toLowerCase();
        const l = (it.lemma || '').toLowerCase();
        if (w === target || l === target) {
            return it.id || (window.getWordId ? window.getWordId(it) : null);
        }
        const meanings = it.meanings || [];
        for (const meaning of meanings) {
            if ((meaning.headword || '').toLowerCase() === target) {
                return it.id || (window.getWordId ? window.getWordId(it) : null);
            }
        }
    }
    return null;
}

function synonymExternalLookup(word) {
    const links = config.languages?.[selectedLanguage]?.referenceLinks || {};
    const named = [
        ['wordReference', 'WordReference'],
        ['spanishDict', 'SpanishDict'],
        ['reverso', 'Reverso'],
    ];
    for (const [key, label] of named) {
        const template = links[key];
        if (!template) continue;
        return {
            label,
            url: String(template).replaceAll('{word}', encodeURIComponent((word || '').toLowerCase())),
        };
    }
    return null;
}

function jumpToSynonym(word) {
    const id = findCardIdForWord(word);
    if (id && window.popupFoundWord) {
        // Close the panel before navigating so back-button returns cleanly.
        const panel = document.getElementById('synonymsPanel');
        if (panel) panel.classList.remove('visible');
        // reopenSearchOnBack: false — back should return to the originating
        // card, not pop up the find-word search modal.
        // startFlipped: true — synonyms panel lives on the back, so land on
        // the back of the new card (where ↩ lives) for continuity.
        window.popupFoundWord({ id }, { reopenSearchOnBack: false, startFlipped: true });
        return;
    }
    const lookup = synonymExternalLookup(word);
    if (!lookup) return;
    confirmLeaveForSynonymLookup(word || '', lookup);
}

// Leave-the-app confirmation for synonyms with no card in the deck. Reuses the
// knowledge-overview modal's sheet chrome (backdrop, sheet, header, close) and
// the auth form's button pair so it reads as the same dialog system rather
// than a second bespoke popup. Lives on document.body, not inside the card, so
// it is not trapped in the card face's stacking context.
let _synLeaveTargetUrl = null;

function _synLeaveKeydown(event) {
    if (event.key === 'Escape') {
        event.stopPropagation();
        closeSynLeaveConfirm();
    }
}

function ensureSynLeaveConfirmModal() {
    let modal = document.getElementById('synLeaveConfirmModal');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'synLeaveConfirmModal';
    modal.className = 'knowledge-overview-modal syn-leave-modal';
    modal.hidden = true;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'synLeaveConfirmTitle');
    modal.innerHTML = `
        <div class="knowledge-overview-sheet syn-leave-sheet">
            <div class="knowledge-overview-header">
                <div>
                    <span class="knowledge-overview-kicker">Leaving Fluency</span>
                    <h2 id="synLeaveConfirmTitle">No card for “<span class="syn-leave-word"></span>”</h2>
                </div>
                <button type="button" class="knowledge-overview-close" aria-label="Cancel" data-syn-leave="cancel">&times;</button>
            </div>
            <p class="syn-leave-body">This word isn't in your deck, so there's no card to open.
                Continuing leaves the app and opens <span class="syn-leave-destination">the dictionary</span> in a new tab.</p>
            <div class="syn-leave-actions">
                <button type="button" class="auth-cancel-btn" data-syn-leave="cancel">Cancel</button>
                <button type="button" class="auth-submit-btn" data-syn-leave="continue">Continue</button>
            </div>
        </div>`;
    modal.addEventListener('click', (event) => {
        event.stopPropagation();
        const action = event.target.closest('[data-syn-leave]')?.dataset.synLeave;
        if (action === 'continue') {
            const url = _synLeaveTargetUrl;
            closeSynLeaveConfirm();
            // Opened from inside this click handler, so it stays a user
            // gesture and is not treated as an unsolicited popup.
            if (url) window.open(url, '_blank', 'noopener');
            return;
        }
        // Cancel button, close button, or a tap on the backdrop itself.
        if (action === 'cancel' || event.target === modal) closeSynLeaveConfirm();
    });
    document.body.appendChild(modal);
    return modal;
}

function closeSynLeaveConfirm() {
    _synLeaveTargetUrl = null;
    const modal = document.getElementById('synLeaveConfirmModal');
    if (!modal) return;
    document.removeEventListener('keydown', _synLeaveKeydown, true);
    // This sheet now enters from the top with the shared knowledge-overview
    // animation, so it has to leave the same way instead of vanishing.
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reduced) { modal.hidden = true; modal.classList.remove('is-closing'); return; }
    modal.classList.add('is-closing');
    setTimeout(() => {
        modal.hidden = true;
        modal.classList.remove('is-closing');
    }, 180);
}

function confirmLeaveForSynonymLookup(word, lookup) {
    const modal = ensureSynLeaveConfirmModal();
    _synLeaveTargetUrl = lookup.url;
    modal.querySelector('.syn-leave-word').textContent = word;
    const dest = modal.querySelector('.syn-leave-destination');
    if (dest) dest.textContent = lookup.label;
    modal.hidden = false;
    // Capture phase: the card's global keyboard shortcuts must not act on the
    // Escape that dismisses this dialog.
    document.addEventListener('keydown', _synLeaveKeydown, true);
    modal.querySelector('[data-syn-leave="continue"]')?.focus();
}

function confirmLeaveForSpanishDict(word, url) {
    confirmLeaveForSynonymLookup(word, { label: 'SpanishDict', url });
}

function isJstOwner() {
    return Boolean(window.isAuditAccount?.());
}

function modelProposalMarkerHTML(meaning) {
    if (!isJstOwner() || !meaning?.modelProposed) return '';
    return `<span class="model-proposed-marker" title="Gemini proposed this definition because it was not in the SpanishDict sense menu" aria-label="Gemini-proposed definition">AI</span>`;
}

function canInspectSpanishDictData() {
    // Scrape inspector, not a learner dictionary. Same gate as other audit
    // chrome: signed-in JST / JSTA only.
    return Boolean(window.isAuditAccount?.());
}

function spanishDictMeaningsForCard(card) {
    return [...(card?.meanings || []), ...(card?.unusedMenuSenses || [])].filter(meaning => (
        String(meaning?.source || '').toLocaleLowerCase('en') === 'spanishdict'
    ));
}

function buildSpanishDictPanelHTML(card) {
    const meanings = spanishDictMeaningsForCard(card);
    const field = (label, value, { code = false, wide = false } = {}) => {
        const rendered = Array.isArray(value) ? value.filter(Boolean).join(' · ') : String(value || '').trim();
        if (!rendered) return '';
        return `<div class="sd-meta-field${wide ? ' sd-meta-field--wide' : ''}">
            <dt>${escapeCardText(label)}</dt>
            <dd${code ? ' class="sd-meta-code"' : ''}>${escapeCardText(rendered)}</dd>
        </div>`;
    };

    const rows = meanings.map((meaning, index) => {
        const translation = meaning.meaning || meaning.translation || '(no English gloss)';
        const headword = meaning.headword || card?.lemma || card?.targetWord || '';
        const rawContext = String(meaning.context || '').trim();
        const usage = rawContext ? parseSpanishDictUsageContext(rawContext) : null;
        const candidates = usage ? spanishDictUsageCandidateForms(usage) : [];
        const dictionaryExamples = extractCanonicalDictionaryExamples(meaning);
        const exampleHTML = dictionaryExamples.length
            ? dictionaryExamples.map(example => `<div class="sd-meta-example">
                <div class="sd-meta-example-target">${escapeCardText(example.target || example.spanish || '')}</div>
                ${example.english ? `<div class="sd-meta-example-english">${escapeCardText(example.english)}</div>` : ''}
            </div>`).join('')
            : '<div class="sd-meta-empty">No SpanishDict example is packaged in this deck for this sense.</div>';
        const usageHTML = usage
            ? `<div class="sd-meta-usage">
                <div class="sd-meta-usage-heading">
                    <span>Parsed usage</span>
                    <strong>${escapeCardText(usage.label)}</strong>
                </div>
                ${usage.detail ? `<div class="sd-meta-usage-detail">Semantic detail: ${escapeCardText(usage.detail)}</div>` : ''}
                ${candidates.length ? `<div class="sd-meta-candidates"><span>Possible text matches</span>${candidates.map(candidate => `<code>${escapeCardText(candidate)}</code>`).join('')}</div>` : ''}
                <div class="sd-meta-caveat">Display aid only · same-sentence presence does not verify grammatical attachment.</div>
            </div>`
            : '';

        return `<details class="sd-meta-sense"${index === 0 ? ' open' : ''}>
            <summary>
                <span class="sd-meta-summary-gloss">${escapeCardText(translation)}</span>
                <span class="sd-meta-summary-identity">${escapeCardText([meaning.pos, headword].filter(Boolean).join(' · '))}</span>
            </summary>
            <dl class="sd-meta-grid">
                ${field('Headword', headword)}
                ${field('Part of speech', meaning.pos)}
                ${field('Sense ID', meaning.senseId, { code: true })}
                ${field('Regions', meaning.regions)}
                ${field('Raw context', rawContext, { wide: true })}
            </dl>
            ${usageHTML}
            <div class="sd-meta-examples-heading">Dictionary example</div>
            ${exampleHTML}
        </details>`;
    }).join('');

    const sourceLink = card?.links?.spanishDict
        ? outboundChipHTML(
            card.links.spanishDict,
            'Open this entry on SpanishDict',
            'SpanishDict',
            'class="sd-meta-source-link"'
        )
        : '';
    return `<div id="spanishDictPanel" class="provenance-panel spanish-dict-panel" hidden
            role="region" aria-labelledby="spanishDictPanelTitle"
            onclick="event.stopPropagation();">
        <button class="prov-close" title="Close" aria-label="Close SpanishDict data" onclick="event.stopPropagation(); toggleSpanishDictPanel(false);">&times;</button>
        <div id="spanishDictPanelTitle" class="prov-title">SpanishDict data</div>
        <p class="sd-meta-intro">Raw dictionary fields that reached this card, plus the app’s presentation-only parsing. They describe the source menu; they do not prove which sense an example uses.</p>
        ${rows || '<div class="prov-empty">No SpanishDict sense metadata is packaged on this card.</div>'}
        ${sourceLink}
    </div>`;
}

function ensureSpanishDictPanelForCurrentCard() {
    if (!canInspectSpanishDictData()) return null;
    let panel = document.getElementById('spanishDictPanel');
    if (panel) return panel;
    const card = flashcards[currentIndex];
    const back = document.getElementById('backContent');
    if (!card || !back || !spanishDictMeaningsForCard(card).length) return null;
    back.insertAdjacentHTML('beforeend', buildSpanishDictPanelHTML(card));
    return document.getElementById('spanishDictPanel');
}

function toggleSpanishDictPanel(forceOpen) {
    if (!canInspectSpanishDictData()) return;
    const panel = ensureSpanishDictPanelForCurrentCard();
    if (!panel) return;
    const shouldOpen = forceOpen == null ? panel.hidden : Boolean(forceOpen);
    panel.hidden = !shouldOpen;
    if (!shouldOpen) window.sideDock?.stowCardPanel(panel);
    if (shouldOpen) {
        const provenancePanel = document.getElementById('provenancePanel');
        if (provenancePanel) provenancePanel.style.display = 'none';
        document.getElementById('flashcard')?.classList.add('flipped');
        window.sideDock?.openCardPanel(panel);
        panel.querySelector('.prov-close')?.focus();
    }
}
window.toggleSpanishDictPanel = toggleSpanishDictPanel;

// Card-data panel. Lists every ordinary
// meaning and resolves stamped prompts against window._promptRegistry (loaded
// in config.js). A missing prompt is identified as deterministic/retained
// evidence rather than making the entire control disappear.
function buildProvenancePanelHTML(card) {
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, c => (
        {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
    const registry = (window._promptRegistry) || {};
    const activeRelease = window._activeReleaseProvenance || {};
    const releaseId = activeRelease.releaseId || activeRelease.release_id || '';
    const assignmentStatus = activeRelease.wsd?.status || '';
    const historicalRelease = /historical|retained|parity/i.test(assignmentStatus);
    const readableAssignmentStatus = String(assignmentStatus || '')
        .replace(/[_-]+/g, ' ').trim();
    const releaseSummary = releaseId
        ? `<div class="prov-notes"><strong>Release ${esc(releaseId)}</strong>${readableAssignmentStatus
            ? ` · ${esc(readableAssignmentStatus)}` : ''}</div>`
        : '<div class="prov-notes">Release identity unavailable · card-level evidence only</div>';

    function fmtTs(ts) {
        if (!ts) return '';
        const d = new Date(ts);
        if (isNaN(d.getTime())) return esc(ts);
        // Date + HH:MM, not date alone. run_ts has always stored minutes
        // (2026-08-19T20:57Z) and two classifier runs on the same day are
        // routine while a change is being evaluated — printing only the date
        // makes the two indistinguishable on the card, which is exactly the
        // thing the panel exists to show.
        const day = d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
        const time = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
        return `${day} ${time}`;
    }

    const rows = (card.meanings || []).map(m => {
            // Meaning-level provenance can be lost between the index and the
            // card. buildFilteredVocab() and mergeArtistVocabularies() rebuild
            // meanings from scratch, and lemma mode pools sibling forms onto a
            // host — any of those can drop prompt_id while the evidence itself
            // is intact. The examples split stamps prompt_id / run_ts /
            // assignment_method on every assigned example, so fall back to the
            // example rather than reporting "No model prompt" for a sense that
            // plainly has a model behind it.
            // Card meanings expose `allExamples`; the joined/index shape uses
            // `examples`. Read both — the panel is rendered from the card.
            const pex = m.allExamples || m.examples || [];
            const psrc = pex.find(e => e && (e.prompt_id || e.assignment_method || e.confidence != null)) || {};
            const promptId = m.prompt_id || psrc.prompt_id || null;
            const runTs = m.run_ts || psrc.run_ts || null;
            const method = m.assignment_method || psrc.assignment_method || null;
            const reg = registry[promptId] || {};
            const isAutomatic = typeof method === 'string' && method.endsWith('-auto');
            const hasPrompt = Boolean(promptId) && !isAutomatic;
            const automaticLabel = method === 'shared-register-auto'
                ? 'Shared sense register auto · no model call'
                : method === 'pos-auto'
                    ? 'POS-filtered auto · no model call'
                    : 'SpanishDict auto · no model call';
            const automaticDetail = method === 'shared-register-auto'
                ? 'exact line reused from another registered artist'
                : method === 'pos-auto'
                    ? 'one menu sense remained after occurrence POS filtering'
                    : 'single available dictionary sense';
            const model = isAutomatic
                ? automaticLabel
                : (hasPrompt
                    ? (reg.model || (historicalRelease
                        ? 'Historical retained assignment'
                        : 'Unregistered model'))
                    : 'Deterministic or retained evidence');
            const family = reg.family || '';
            const tier = (reg.capability_tier != null) ? `tier ${reg.capability_tier}` : '';
            const ts = fmtTs(runTs);
            const meta = [family, tier, ts].filter(Boolean).join(' · ');
            const notes = reg.notes ? `<div class="prov-notes">${esc(reg.notes)}</div>` : '';
            const proposal = m.modelProposed
                ? '<div class="prov-proposal">AI-proposed definition · outside the SpanishDict menu</div>'
                : '';
            // A SpanishDict example sentence is filed under its sense BY THE
            // DICTIONARY, so no model was ever involved and "No model prompt"
            // reads as a gap when it is actually the strongest provenance on the
            // card. step_8a already marks these `evidence: "dictionary"`; say so
            // rather than leaving the line blank-looking.
            const isDictionary = !hasPrompt && !isAutomatic
                && pex.some(e => e && e.evidence === 'dictionary');
            const stamp = hasPrompt
                ? `<div class="prov-meta"><code>${esc(promptId)}</code>${meta ? ` · ${esc(meta)}` : ''}</div>`
                : isDictionary
                    ? '<div class="prov-meta">SpanishDict example · filed by the dictionary, no model involved</div>'
                    : `<div class="prov-meta">${esc(method || 'No model prompt')}${isAutomatic ? ` · ${esc(automaticDetail)}` : ''}</div>`;
            // Confidence, when the assigning method reports one. The band cuts
            // are absolute values transferred from the hand-labelled panel in
            // Data/Spanish/Intermediates/wsd_sense_harness, not quantiles of a
            // run: high is the gap at which that panel measured 100% acceptable.
            // Confidence means different things per method and must not be
            // labelled identically. step_6d reports a COSINE GAP between the top
            // two lemma+POS tuples; step_6e reports a calibrated P(correct) from
            // a learned ranker. Showing "gap 0.9857" for a probability would be
            // actively misleading, so the unit follows the prompt family.
            const cVal = (m.confidence != null) ? m.confidence : psrc.confidence;
            const cBand = m.band || psrc.band || null;
            const calibrated = typeof promptId === 'string' && promptId.startsWith('sd-beto-cal');
            const conf = (cVal != null)
                ? `<div class="prov-conf prov-conf--${esc(cBand || 'low')}">
                       <span class="prov-conf-band">${esc(cBand || '?')}</span>
                       <span class="prov-conf-val">${calibrated
                           ? `P(correct) ${esc((Number(cVal) * 100).toFixed(1))}%`
                           : `gap ${esc(Number(cVal).toFixed(4))}`}</span>
                       <span class="prov-conf-note">${calibrated
                           ? (cBand === 'high' ? 'held-out: 99% lemma+POS correct at this cut'
                               : cBand === 'medium' ? 'held-out: 95% lemma+POS correct at this cut'
                               : 'below the 95% cut — least reliable band')
                           : (cBand === 'high' ? '100% acceptable on the 150-sentence panel'
                               : cBand === 'medium' ? '91.9% acceptable on that panel'
                               : '84.5% acceptable on that panel')}</span>
                   </div>`
                : '';
            // The sentences this sense was actually assigned to. Without these
            // the panel says a model made a decision but never shows the
            // evidence it decided on, which is the only thing worth auditing.
            const exs = pex.map((x, exampleIndex) => {
                const pv = normalizedExampleProvenance(x);
                let src = exampleProvenanceHTML(x) || '';
                if (src) {
                    src = src.replace('<a ', '<a class="prov-ex-src" ');
                } else if (x.source) {
                    src = `<span class="prov-ex-src">${esc(x.source)}</span>`;
                }
                const al = (x.alignment != null)
                    ? `<span class="prov-ex-align">align ${esc(Number(x.alignment).toFixed(3))}</span>` : '';
                const metadata = [
                    ['Run', x.run_id], ['Example', x.example_id],
                    ['Occurrence', x.occurrence_id], ['Analysis unit', x.analysis_unit_id],
                    ['Route', x.route_id], ['Lexical candidate', x.lexical_candidate_id],
                    ['Menu analysis', x.menu_analysis_id], ['Menu snapshot', x.menu_content_id],
                    ['Sense', x.sense_id], ['WSD request', x.wsd_request_id],
                    ['WSD result', x.wsd_result_id], ['Method', x.assignment_method],
                    ['Decision path', Array.isArray(x.decision_path) ? x.decision_path.join(' → ') : x.decision_path],
                    ['Source record', x.source_record_id || pv.source_record_id], ['Source snapshot', x.source_snapshot_content_id],
                    ['Source URL', x.source_url || pv.url], ['Attribution', x.attribution || pv.attribution],
                    ['Contributor', x.contributor || pv.contributor], ['License', x.license || pv.license],
                    ['Alignment', x.alignment_id], ['Alignment snapshot', x.alignment_snapshot_content_id],
                    ['Translation source', x.translation_source], ['Song ID', x.song],
                    ['Vocalists', Array.isArray(x.vocalists) ? x.vocalists.join(', ') : x.vocalists],
                ].filter(([, value]) => value != null && String(value).trim() !== '');
                const metadataHTML = metadata.map(([label, value]) =>
                    `<div class="prov-ex-field"><dt>${esc(label)}</dt><dd><code>${esc(value)}</code></dd></div>`
                ).join('');
                const rawRecord = esc(JSON.stringify(x, null, 2));
                return `<details class="prov-ex-record"${exampleIndex === 0 ? ' open' : ''}>
                    <summary>Example ${exampleIndex + 1} of ${pex.length}${x.song_name ? ` · ${esc(x.song_name)}` : ''}</summary>
                    <div class="prov-ex">
                    <div class="prov-ex-target">${esc(x.target || x.spanish || '')}</div>
                    <div class="prov-ex-english">${x.english ? esc(x.english) : '<em>Translation unavailable</em>'}</div>
                    <div class="prov-ex-meta">${src}${al}</div>
                    <dl class="prov-ex-fields">${metadataHTML}</dl>
                    <details class="prov-ex-raw"><summary>Raw example record</summary><pre>${rawRecord}</pre></details>
                    </div>
                </details>`;
            }).join('');
            const exBlock = exs
                ? `<div class="prov-examples">${exs}</div>`
                : '<div class="prov-examples prov-examples--empty">No sentence attached to this sense.</div>';
            return `<div class="prov-row">
                <div class="prov-gloss">${esc(m.meaning || m.translation || '')}
                    <span class="prov-pos">${esc(m.pos || '')}</span></div>
                <div class="prov-model">${esc(model)}</div>
                ${stamp}
                ${conf}
                ${exBlock}
                ${proposal}
                ${notes}
            </div>`;
        }).join('');

    return `<div id="provenancePanel" class="provenance-panel" style="display:none;">
        <button class="prov-close" title="Close" aria-label="Close" onclick="event.stopPropagation(); toggleProvenancePanel();">&times;</button>
        <div class="prov-title">Card data</div>
        ${releaseSummary}
        ${rows || '<div class="prov-empty">No sense assignments on this card.</div>'}
    </div>`;
}

function ensureProvenancePanelForCurrentCard() {
    let panel = document.getElementById('provenancePanel');
    if (panel) return panel;
    const card = flashcards[currentIndex];
    const back = document.getElementById('backContent');
    if (!card || !back) return null;
    back.insertAdjacentHTML('beforeend', buildProvenancePanelHTML(card));
    return document.getElementById('provenancePanel');
}

function toggleProvenancePanel(forceOpen) {
    const panel = ensureProvenancePanelForCurrentCard();
    if (!panel) return;
    const shouldOpen = forceOpen == null
        ? (panel.style.display === 'none' || !panel.style.display)
        : Boolean(forceOpen);
    panel.style.display = shouldOpen ? 'block' : 'none';
    if (!shouldOpen) window.sideDock?.stowCardPanel(panel);
    if (shouldOpen) {
        const dictionaryPanel = document.getElementById('spanishDictPanel');
        if (dictionaryPanel) dictionaryPanel.hidden = true;
        document.getElementById('flashcard')?.classList.add('flipped');
        window.sideDock?.openCardPanel(panel);
    }
}
window.toggleProvenancePanel = toggleProvenancePanel;

function buildSynonymsPanelHTML(synonyms, antonyms, headword) {
    const headwordLower = (headword || '').toLowerCase();
    function renderItem(item) {
        const word = item && item.word ? item.word : '';
        if (!word) return '';
        const strength = item.strength === 2 ? 'syn-strong' : 'syn-weak';
        const escaped = word.replace(/'/g, "\\'");
        const ctx = item.context ? `<span class="syn-context">${item.context}</span>` : '';
        // Every row navigates, so every row gets the same affordance. The old
        // accent outline on in-deck words read as "this one is special"
        // rather than "this one is tappable", and dimming the rest made the
        // majority look disabled.
        return `<a class="syn-item ${strength}" href="javascript:void(0)" onclick="jumpToSynonym('${escaped}')">
            <span class="syn-word">${word}</span>${ctx}
            <span class="syn-go" aria-hidden="true">›</span>
        </a>`;
    }
    const tab = (id, label, items) => `
        <button type="button" class="syn-tab" data-syn-tab="${id}"
                onclick="selectSynonymsTab(event, '${id}')">
            ${label}<span class="syn-tab-count">${items.length}</span>
        </button>`;
    const panelFor = (id, items, empty) => `
        <div class="syn-panel" data-syn-panel="${id}">
            ${items.length
                ? `<div class="syn-list">${items.map(renderItem).join('')}</div>`
                : `<p class="syn-empty">${empty}</p>`}
        </div>`;

    return `
        <div id="synonymsPanel" class="synonyms-panel">
            <button class="syn-close-btn" onclick="toggleSynonymsPanel()" aria-label="Close">&times;</button>
            <div class="syn-header">
                <span class="syn-headword">${headwordLower}</span>
                <div class="syn-tabs" role="tablist">
                    ${tab('synonyms', 'Synonyms', synonyms)}
                    ${tab('antonyms', 'Antonyms', antonyms)}
                </div>
            </div>
            <div class="syn-body">
                ${panelFor('synonyms', synonyms, 'No synonyms recorded for this word.')}
                ${panelFor('antonyms', antonyms, 'No antonyms recorded for this word.')}
            </div>
        </div>
    `;
}

// Opens on whichever tab actually has content, so a word with only antonyms
// doesn't present an empty panel on open.
function selectSynonymsTab(event, tabId) {
    event?.stopPropagation();
    const panel = document.getElementById('synonymsPanel');
    if (!panel) return;
    panel.querySelectorAll('[data-syn-tab]').forEach(button =>
        button.classList.toggle('selected', button.dataset.synTab === tabId));
    panel.querySelectorAll('[data-syn-panel]').forEach(section =>
        section.classList.toggle('selected', section.dataset.synPanel === tabId));
}

// On a wide desktop the panel docks in the right-hand gutter so the card
// stays in view (side-dock.js). Below that it keeps sliding over the card.
function toggleSynonymsPanel() {
    const panel = document.getElementById('synonymsPanel');
    if (!panel) return;
    const opening = !panel.classList.contains('visible');
    if (!opening) {
        panel.classList.remove('visible');
        if (panel.parentElement === document.body) {
            // Wait out the slide before re-parenting, or the panel jumps.
            setTimeout(() => {
                if (!panel.classList.contains('visible')) window.sideDock?.stowCardPanel(panel);
            }, 260);
        }
        return;
    }
    if (!panel.querySelector('[data-syn-tab].selected')) {
        const hasSynonyms = panel.querySelector('[data-syn-panel="synonyms"] .syn-item');
        selectSynonymsTab(null, hasSynonyms ? 'synonyms' : 'antonyms');
    }
    if (window.sideDock?.openCardPanel(panel)) {
        // A freshly moved node has no committed "from" state, so the slide
        // would be skipped. Reading a layout property commits it; unlike a
        // requestAnimationFrame this cannot be deferred indefinitely by a
        // backgrounded tab, leaving the panel hosted but never shown.
        void panel.offsetWidth;
        panel.classList.add('visible');
        return;
    }
    panel.classList.add('visible');
}

// Small sheet listing every external reference link (SpanishDict, Reverso,
// etc.), opened from the single "Look up" tile. Dismisses on an outside tap,
// mirroring the word-search popup's dismiss pattern.
function toggleLookupSheet(event) {
    event?.stopPropagation();
    const sheet = document.getElementById('lookupSheet');
    if (!sheet) return;
    const opening = sheet.hidden;
    sheet.hidden = !opening;
    if (opening) {
        setTimeout(() => {
            document.addEventListener('click', function dismiss(e) {
                if (!sheet.contains(e.target)) sheet.hidden = true;
                document.removeEventListener('click', dismiss);
            });
        }, 0);
    }
}
window.toggleLookupSheet = toggleLookupSheet;

window.computeLinesUnderstood = computeLinesUnderstood;
window.loadSpanishRanks = loadSpanishRanks;
window.loadConjugationData = loadConjugationData;
window.loadSourceTitles = loadSourceTitles;
window.loadConjugatedEnglishData = loadConjugatedEnglishData;
window.resetLanguageOptionalData = resetLanguageOptionalData;
window.toggleSynonymsPanel = toggleSynonymsPanel;
window.revealWildTranslation = revealWildTranslation;
window.toggleCliticExamples = toggleCliticExamples;
window.selectSynonymsTab = selectSynonymsTab;
window.jumpToSynonym = jumpToSynonym;
window.closeSynLeaveConfirm = closeSynLeaveConfirm;
window.initializeApp = initializeApp;
window.setupSwipeGestures = setupSwipeGestures;
window.setupKeyboardShortcuts = setupKeyboardShortcuts;
window.handleSwipeAction = handleSwipeAction;
window.recordCardResult = recordCardResult;
window.showFloatingBtns = showFloatingBtns;
window.getVocabByIdLookup = getVocabByIdLookup;
window.goBackToSetup = goBackToSetup;
window.updateCard = updateCard;
window.flipCard = flipCard;
window.cycleExample = cycleExample;
window.getCyclableExamples = getCyclableExamples;
window.cycleExampleForward = cycleExampleForward;
window.cycleExampleBackward = cycleExampleBackward;
window.toggleExampleAutoplay = toggleExampleAutoplay;
window.spotifyBtnPressStart = spotifyBtnPressStart;
window.spotifyBtnPressEnd = spotifyBtnPressEnd;
window.spotifyBtnActivate = spotifyBtnActivate;
window.stopExampleAutoplay = stopExampleAutoplay;
window.cycleMWEForward = cycleMWEForward;
window.cycleMWEBackward = cycleMWEBackward;
window.selectMeaning = selectMeaning;
window.selectPartOfSpeech = selectPartOfSpeech;
window.toggleMorphPopover = toggleMorphPopover;
window.toggleMorphAlternatives = toggleMorphAlternatives;
window.toggleFrontProductionHint = toggleFrontProductionHint;
window.focusKnowledgeCardItem = focusKnowledgeCardItem;
window.selectGroup = selectGroup;
window.previousCard = previousCard;
window.nextCard = nextCard;
window.advanceToNextDeckCard = advanceToNextDeckCard;
window.shuffleCards = shuffleCards;

window.showFreqInfo = function showFreqInfo(event) {
    event.stopPropagation();
    let tip = document.getElementById('freqTooltip');
    if (!tip) {
        tip = document.createElement('div');
        tip.id = 'freqTooltip';
        tip.className = 'freq-tooltip';
        document.body.appendChild(tip);
    }
    const button = event.currentTarget || event.target.closest('.card-freq-btn');
    const source = button?.dataset.frequencySource || 'Published frequency list';
    const unit = button?.dataset.frequencyUnit === 'per_million'
        ? 'occurrences per million words' : 'occurrences in the source list';
    const forms = Number(button?.dataset.frequencyForms) || 1;
    tip.textContent = `${source} · ${unit}${forms > 1 ? ` · total across ${forms} source-listed forms` : ''}. This does not count harvested example sentences.`;
    const rect = button.getBoundingClientRect();
    const tipWidth = Math.min(300, window.innerWidth - 16);
    let left = rect.left + rect.width / 2 - tipWidth / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tipWidth - 8));
    tip.style.left = left + 'px';
    tip.style.width = tipWidth + 'px';
    const above = rect.top - tip.offsetHeight - 10;
    tip.style.top = (above >= 8 ? above : rect.bottom + 10) + 'px';
    tip.classList.remove('hiding');
    clearTimeout(tip._hideTimer);
    tip._hideTimer = setTimeout(function() {
        tip.classList.add('hiding');
        tip._hideTimer = setTimeout(function() {
            tip.remove();
        }, 320);
    }, 2200);
};
window.flipDirection = flipDirection;
window.toggleAutoSpeak = toggleAutoSpeak;
window.updateSpeakIcons = updateSpeakIcons;
window.getPosColorClass = getPosColorClass;
window.updateReverseButton = updateReverseButton;
window.updateStats = updateStats;
window.dedupeExamples = dedupeExamples;

// ---------------------------------------------------------------------------
// Report button wiring — eager, button is in the desktop guide from boot.
// The modern audit sheet itself remains lazily loaded with the other modals.
// ---------------------------------------------------------------------------
(function _initCardMetaButton() {
    function attach() {
        const btn = document.getElementById('cardMetaBtn');
        if (!btn) return;
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (!(window.canUserFlag ? window.canUserFlag() : window.isAuditAccount?.())) return;
            window.showFlagMenu();
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attach, { once: true });
    } else {
        attach();
    }
})();

// Delegated tap-to-expand for clamped meaning rows. One listener at the
// document root replaces the per-row addEventListener that updateCard()
// used to attach inside its post-render layout pass — saves ~5-15 listener
// registrations per card flip.
document.addEventListener('click', (e) => {
    const el = e.target.closest && e.target.closest('.meaning-row-translation.is-clamped');
    if (!el) return;
    e.stopPropagation();
    el.classList.remove('is-clamped');
    el.classList.add('is-expanded');
}, true);

// Keyboard-shortcut guide: collapse/expand with localStorage persistence.
// Toggled from the right-edge sidebar button (#kbToggleSidebar).
// Defaults to collapsed (off) for new users; existing localStorage value wins.
(function _initKbGuideCollapse() {
    const LS_KEY = 'fluency.kbGuideCollapsed';
    function attach() {
        const guide = document.getElementById('desktopKeyboardGuide');
        const btn = document.getElementById('kbToggleSidebar');
        if (!guide || !btn) return;
        const setCollapsed = (collapsed) => {
            guide.classList.toggle('collapsed', collapsed);
            btn.title = collapsed ? 'Show keyboard shortcuts' : 'Hide keyboard shortcuts';
            btn.setAttribute('aria-label', btn.title);
            try { localStorage.setItem(LS_KEY, collapsed ? '1' : '0'); } catch (e) {}
        };
        let initial = true;
        try {
            const stored = localStorage.getItem(LS_KEY);
            if (stored !== null) initial = stored === '1';
        } catch (e) {}
        setCollapsed(initial);
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            setCollapsed(!guide.classList.contains('collapsed'));
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attach, { once: true });
    } else {
        attach();
    }
})();

// ===========================================================================
// Lazy-load stubs for extras modules
// ===========================================================================
//
// flashcards-modals.js holds the audit sheet, lyric breakdown, POS popup,
// nav stack, homograph peek, and end-of-deck modal — all event-driven, none
// needed at boot. These stubs install on boot; the dynamic import resolves
// on first user interaction; the loaded module's top-level `window.X = X`
// overwrites each stub with the real function. Subsequent calls hit the
// real function directly.
//
// On rejection (e.g. transient network failure) the cached promise is nulled
// so the next click retries — a flaky cellular connection shouldn't lock
// the user out of reporting or other modal actions for the session.
//
// The STUB symbol marker + post-resolve assertion catches the case where a
// name in the stub list isn't actually exported by the lazy module (typo /
// drift); without it, the stub would infinite-recurse into itself.

// Keep this in lockstep with service-worker.js. These lazy modules own search
// result cards and conjugation; a stale URL here can keep running an old modal
// implementation even after the eagerly loaded app has updated.
const ASSET_VERSION = '20260921x';
const MODALS_ASSET_VERSION = '20260921rt';

let _modalsModulePromise = null;
const lazyModals = () => _modalsModulePromise || (_modalsModulePromise =
    import('./flashcards-modals.js?v=' + MODALS_ASSET_VERSION).catch(err => {
        _modalsModulePromise = null;
        throw err;
    }));

let _conjModulePromise = null;
const lazyConj = () => _conjModulePromise || (_conjModulePromise =
    import('./flashcards-conj.js?v=' + ASSET_VERSION).catch(err => {
        _conjModulePromise = null;
        throw err;
    }));

const STUB = Symbol('lazyStub');
const stubFor = (name, loader) => {
    const fn = (...args) => loader().then(() => {
        if (window[name] === fn) {
            console.error('Lazy module loaded but did not export', name);
            return;
        }
        return window[name](...args);
    }).catch(err => {
        console.error('Lazy load failed for', name, err);
        throw err;
    });
    fn[STUB] = true;
    window[name] = fn;
};

['showFlagMenu', 'hideFlagMenu', 'sendWholeCardFlag',
 'showPOSInfo',
 'showLyricBreakdown', 'hideLyricBreakdown',
 'showWordPopup', 'hideWordPopup',
 'navigateToCard', 'navigateToVocabCard', 'navigateBack',
 'popupFoundWord', 'peekHomograph',
 'showEndOfDeckOptions', 'hideDeckCompleteModal',
 'restartAllCards']
    .forEach(name => stubFor(name, lazyModals));

['toggleConjugationTable', 'switchConjMood', 'switchConjTense']
    .forEach(name => stubFor(name, lazyConj));

window.describeCliticForm = describeCliticForm;
window.openSenseCrossReference = openSenseCrossReference;
window.toggleSenseMetadataChip = toggleSenseMetadataChip;
window.toggleProminenceBadge = toggleProminenceBadge;
window.toggleSenseMetadataOverflow = toggleSenseMetadataOverflow;
