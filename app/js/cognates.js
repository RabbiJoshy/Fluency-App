// Which languages the learner already reads, and how transparent each deck
// word is to them.
//
// The deck used to carry one `cognate_score` per word, which could only ever
// mean "close to English". A learner who also reads Polish gets a large part of
// a Czech deck for free, and none of that was expressible. So the release now
// ships a score per known language and the learner says which ones apply.
//
//   cognate_scores: { en: 0.76, pl: 0.85 }
//
// There is no combining. Each known language is its own exclusion, deciding at
// its own cutoff whether it already gives the learner this word; a word leaves
// the deck if any of them says so. The scores are therefore never compared
// with one another, which is what lets Spanish keep its own hand-built number
// on its own scale without the two ever having to mean the same thing.
//
// Selecting nothing leaves every word in the deck, which is the honest default
// for someone who has not said what they read.
//
// The old scalar still works. Where a release predates this, `cognate_score`
// is read as the English entry, so Spanish is untouched.
import './state.js?v=20260825ak';

const SELECTED_KEY = 'fluency_known_languages_v1';

// Named here rather than fetched: the picker must render before the scores
// arrive, and a language code with no name is not something to show a learner.
const KNOWN_LANGUAGE_NAMES = {
    en: 'English',
    pl: 'Polish',
    es: 'Spanish',
    fr: 'French',
    pt: 'Portuguese',
    de: 'German',
    it: 'Italian',
    ru: 'Russian',
    sk: 'Slovak',
    uk: 'Ukrainian',
    nl: 'Dutch',
    sv: 'Swedish',
};

// surface (lowercased) -> { known language: score }
let cognateScores = null;
// The same keying as cognateScores, but the word that produced each score. It
// ships as a sibling map from v1.1 on; a file built before that has none, and
// the app says so rather than naming a word it cannot stand behind.
let cognateMatches = null;
let cognateLanguages = [];
// The auto cutoff per known language, shipped with the scores because it is a
// property of the pair that produced them, not a user setting. An advanced
// override can come later; until then the words a slightly wrong number moves
// are not lost, only relocated to Extras.
let cognateThresholds = {};
// Which shape the loaded map is. v1 is surface -> {language: score}; v2 adds a
// lemma level between them. Read from the payload rather than sniffed, so a
// malformed file fails loudly instead of being guessed at.
let cognateSchema = 'cognate-score/v1';
// v1 and v1.1 are the flat route; v2 and v2.1 add the lemma level. The .1
// revisions differ only by carrying `matches`, so the shape tests read the
// route, never the exact string.
const isLemmaRouted = schema => String(schema).startsWith('cognate-score/v2');
// The language the loaded map was built for. Scores are keyed by bare surface,
// which several languages share, so the map must never outlive its language.
let cognateLanguage = null;
let selectedKnownLanguages = null;

function readSelected() {
    if (selectedKnownLanguages) return selectedKnownLanguages;
    try {
        const saved = JSON.parse(localStorage.getItem(SELECTED_KEY) || 'null');
        if (Array.isArray(saved)) {
            selectedKnownLanguages = saved.filter(code => typeof code === 'string');
            return selectedKnownLanguages;
        }
    } catch (_) {
        // Blocked site data. Fall through to the default rather than failing:
        // the setting is a convenience, not something to lose the deck over.
    }
    // English is the language the glosses are already written in, so a learner
    // who has said nothing is at least reading English.
    selectedKnownLanguages = ['en'];
    return selectedKnownLanguages;
}

function writeSelected(codes) {
    selectedKnownLanguages = codes.slice();
    try {
        localStorage.setItem(SELECTED_KEY, JSON.stringify(selectedKnownLanguages));
    } catch (_) {}
}

function languageLabel(code) {
    return KNOWN_LANGUAGE_NAMES[code] || String(code || '').toUpperCase();
}

// The scores a release actually shipped. A language with no scores is never
// offered, so the picker cannot promise a filter that would do nothing.
function availableKnownLanguages() {
    return cognateLanguages.slice();
}

function activeKnownLanguages() {
    const available = new Set(cognateLanguages);
    return readSelected().filter(code => available.has(code));
}

// Does any language the learner reads already give them this word? Each is
// asked separately, at its own cutoff.
function isCognateKnown(item) {
    if (!item) return false;
    // Every source is asked, and any one of them saying yes is enough — the
    // same shape as the languages themselves. A language can hold both: Spanish
    // has hand-built flags in its artist data and a generated map for its
    // Speech deck, and the two describe different words on different scales.
    // Preferring the map would have silently narrowed Spanish Lyrics to
    // whichever of its words happened to appear in the Speech map.
    const legacy = Number(item.cognate_score || 0);
    if (legacy > 0 && legacy >= Number(globalThis.cognateThreshold || 0)) return true;
    const perLanguage = item.cognate_scores;
    if (!perLanguage) return false;
    for (const code of activeKnownLanguages()) {
        const score = Number(perLanguage[code] || 0);
        const cutoff = Number(cognateThresholds[code] ?? globalThis.cognateThreshold ?? 1);
        if (score >= cutoff) return true;
    }
    return false;
}

// For display only — which language makes this word free, and how strongly.
// Never used to decide anything, because comparing two scales would be
// meaningless.
function strongestKnownLanguage(item) {
    const perLanguage = item && item.cognate_scores;
    if (!perLanguage) return null;
    let bestCode = null;
    let best = -1;
    for (const code of activeKnownLanguages()) {
        const score = Number(perLanguage[code] || 0);
        if (score >= Number(cognateThresholds[code] ?? 1) && score > best) {
            best = score;
            bestCode = code;
        }
    }
    return bestCode === null ? null : { code: bestCode, score: best };
}

// The known word that actually produced the score which freed this card, for
// the language that cleared its own cutoff. Display only, like
// strongestKnownLanguage above -- and null whenever the deck's cognate file
// predates v1.1, because there is then no such word to name.
function matchedKnownWord(item) {
    const strongest = strongestKnownLanguage(item);
    if (!strongest) return null;
    const word = item?.cognate_match_words?.[strongest.code];
    return word ? { code: strongest.code, word: String(word) } : null;
}

// Attach shipped scores to the loaded vocabulary. Called once per deck load,
// before any filtering, so buildFilteredVocab sees a complete item.
function applyCognateScores(vocabularyData, languageCode) {
    if (!Array.isArray(vocabularyData) || !cognateScores) return;
    // A map for another language would score words that merely look alike
    // across the two.
    if (languageCode && cognateLanguage && languageCode !== cognateLanguage) return;
    for (const item of vocabularyData) {
        const surface = String(item.word || '').toLowerCase();
        const entry = cognateScores[surface];
        if (!entry) continue;
        const matched = cognateMatches?.[surface];
        if (isLemmaRouted(cognateSchema)) {
            // v2 keys surface -> lemma -> language, because form is settled at
            // the surface and cognateness at the lemma. A card is a surface, so
            // the card's score is the best any of its lemmas can claim: if one
            // of its meanings is already free, the word is already free.
            item.cognate_lemma_scores = entry;
            const best = bestPerLanguage(entry);
            item.cognate_scores = best.scores;
            // The word has to come from the lemma that won, or it would name a
            // match other than the one the number reports.
            if (matched) {
                const words = {};
                for (const [code, lemma] of Object.entries(best.lemmas)) {
                    const word = matched[lemma]?.[code];
                    if (word) words[code] = word;
                }
                if (Object.keys(words).length) item.cognate_match_words = words;
            }
        } else {
            item.cognate_scores = entry;
            if (matched) item.cognate_match_words = matched;
        }
    }
}

// surface -> {scores: {language: best score across its lemmas},
//             lemmas: {language: the lemma that scored it}}
// The winning lemma is carried out rather than found again later, so the word
// shown and the number thresholded always come from the same match.
function bestPerLanguage(byLemma) {
    const scores = {};
    const lemmas = {};
    for (const [lemma, langs] of Object.entries(byLemma || {})) {
        for (const [code, value] of Object.entries(langs || {})) {
            const score = Number(value) || 0;
            if (!(code in scores) || score > scores[code]) {
                scores[code] = score;
                lemmas[code] = lemma;
            }
        }
    }
    return { scores, lemmas };
}

// Which of a card's lemmas a known language already gives the learner. Nothing
// reads this yet; it is what per-sense exclusion will ask, so that a card with
// one transparent sense and three opaque ones loses only the one.
function knownLemmas(item) {
    const byLemma = item && item.cognate_lemma_scores;
    if (!byLemma) return [];
    const active = activeKnownLanguages();
    const out = [];
    for (const [lemma, langs] of Object.entries(byLemma)) {
        for (const code of active) {
            const cutoff = Number(cognateThresholds[code] ?? globalThis.cognateThreshold ?? 1);
            if (Number(langs[code] || 0) >= cutoff) { out.push(lemma); break; }
        }
    }
    return out;
}

async function loadCognateScores(langConfig) {
    cognateScores = null;
    cognateMatches = null;
    cognateLanguages = [];
    cognateThresholds = {};
    cognateLanguage = null;
    cognateSchema = 'cognate-score/v1';
    const path = langConfig && langConfig.cognatesPath;
    if (!path) return;
    try {
        const response = await fetch(path, { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        const scores = payload && payload.scores;
        if (!scores || typeof scores !== 'object') throw new Error('no scores in cognate file');
        cognateScores = scores;
        cognateSchema = String(payload.schema || 'cognate-score/v1');
        cognateMatches = (payload.matches && typeof payload.matches === 'object')
            ? payload.matches
            : null;
        cognateLanguage = payload.language || null;
        cognateLanguages = Array.isArray(payload.known_languages)
            ? payload.known_languages.slice()
            : Object.keys(Object.values(scores)[0] || {});
        if (isLemmaRouted(cognateSchema) && !Array.isArray(payload.known_languages)) {
            // v2's first value is a lemma map, so its keys are lemmas, not
            // languages. Only a declared list is trustworthy here.
            cognateLanguages = [];
        }
        cognateThresholds = (payload.thresholds && typeof payload.thresholds === 'object')
            ? payload.thresholds
            : {};
    } catch (error) {
        // Absence is declared, not inferred: with no scores the picker stays
        // hidden and the deck keeps every word, rather than silently filtering
        // against whatever happened to be left in memory.
        console.warn('Cognate scores unavailable:', error);
        cognateScores = null;
        cognateMatches = null;
        cognateLanguages = [];
        cognateThresholds = {};
        cognateLanguage = null;
        cognateSchema = 'cognate-score/v1';
    }
    renderKnownLanguagePicker();
}

// ---------------------------------------------------------------- the picker

function renderKnownLanguagePicker() {
    const container = document.getElementById('knownLanguagesContainer');
    const selector = document.getElementById('knownLanguagesSelector');
    if (!container || !selector) return;
    const available = availableKnownLanguages();
    // One language is not a choice — with English alone this is the old
    // behaviour and the picker would only be noise.
    if (available.length < 2) {
        container.style.display = 'none';
        return;
    }
    container.style.display = 'block';
    const active = new Set(activeKnownLanguages());
    selector.innerHTML = available.map(code => `
        <button type="button" class="known-language-btn${active.has(code) ? ' selected' : ''}"
                data-known-language="${code}" aria-pressed="${active.has(code)}">
            ${active.has(code) ? '✓ ' : ''}${languageLabel(code)}
        </button>`).join('');
    selector.querySelectorAll('.known-language-btn').forEach(button => {
        button.addEventListener('click', () => toggleKnownLanguage(button.dataset.knownLanguage));
    });
}

function toggleKnownLanguage(code) {
    if (!code) return;
    const current = new Set(activeKnownLanguages());
    if (current.has(code)) {
        current.delete(code);
    } else {
        current.add(code);
    }
    writeSelected(availableKnownLanguages().filter(item => current.has(item)));
    renderKnownLanguagePicker();
    // The deck composition just changed, so every count on the setup screen is
    // now stale. These are the same refreshes a cognate-toggle click performs.
    // The explainer copy names the selected languages, so it is as stale as the
    // counts are until it is told.
    globalThis.updateKnownLanguageCopy?.();
    globalThis.updateExclusionBars?.();
    globalThis.updateLevelSelector?.();
    globalThis.refreshFastMode?.();
}

// The cutoff a single language decides at. Exposed because the explainer copy
// has to name a word this language actually sets aside, and asking
// isCognateKnown() would answer for the whole active set instead of for one.
function cognateThresholdFor(code) {
    const shipped = cognateThresholds[code];
    return Number.isFinite(Number(shipped)) ? Number(shipped) : null;
}

globalThis.cognateThresholdFor = cognateThresholdFor;
globalThis.isCognateKnown = isCognateKnown;
globalThis.strongestKnownLanguage = strongestKnownLanguage;
globalThis.matchedKnownWord = matchedKnownWord;
globalThis.applyCognateScores = applyCognateScores;
globalThis.loadCognateScores = loadCognateScores;
globalThis.availableKnownLanguages = availableKnownLanguages;
globalThis.activeKnownLanguages = activeKnownLanguages;
globalThis.renderKnownLanguagePicker = renderKnownLanguagePicker;
globalThis.knownLemmas = knownLemmas;
globalThis.knownLanguageLabel = languageLabel;
