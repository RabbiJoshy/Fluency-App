import './state.js?v=3bdda143';

const ESTIMATION_QUESTION_LIMIT = 30;
const ESTIMATION_BAND_TARGET = 10;
const ESTIMATION_CONFIDENCE_Z = 1.645; // Approximate 90% interval.
const ESTIMATION_PRIOR = 0.5;          // Jeffreys prior for adaptive selection.
const ESTIMATION_PICK_ATTEMPTS = 8;    // Candidates tried per question before giving up.

// Always use the normal-mode vocabulary for placement. Artist ordering measures
// familiarity with one corpus, not general vocabulary size.
function getEstimationLangConfig() {
    const langConfig = config.languages[selectedLanguage];
    if (!activeArtist) return langConfig;
    return window._normalModeLangConfigs?.[selectedLanguage] || langConfig;
}

// Every state gets a fresh sequence number, so a word still loading when the
// check is closed or retried is dropped instead of landing in the new run.
let estimationSequence = 0;

function createEstimationState() {
    return {
        active: false,
        vocabularyData: null,
        validWords: [],
        bands: [],
        coverageOrder: [],
        maxLevel: 0,
        wordsTestedCount: 0,
        shownWordIds: new Set(),
        shownLemmaKeys: new Set(),
        prefetched: new Map(),
        currentWord: null,
        loading: false,
        sequence: ++estimationSequence,
        currentBandIndex: null,
        translationRevealed: false,
        estimatedLevel: null,
        estimateInterval: null,
        autoAdvanceTimer: null
    };
}

// Open estimation modal
function openEstimationModal() {
    document.getElementById('estimationModal').classList.remove('hidden');
    document.getElementById('estimationIntro').style.display = 'block';
    document.getElementById('estimationTest').style.display = 'none';
    document.getElementById('estimationResult').style.display = 'none';
    estimationState = createEstimationState();
}

// Close estimation modal
function closeEstimationModal() {
    document.getElementById('estimationModal').classList.add('hidden');
    estimationState.active = false;
    estimationState.sequence = ++estimationSequence;
    if (estimationState.autoAdvanceTimer) {
        clearTimeout(estimationState.autoAdvanceTimer);
    }
}

// Keep the estimator independent of optional pipeline enrichments. It uses the
// same broad exclusions as before, but does not require CEFR labels, calibrated
// item difficulty, morphology, or sense-assignment metadata.
function buildEstimationWordList() {
    const vocabData = estimationState.vocabularyData;
    if (!vocabData) return [];

    // Lean columnar indexes ship every card with empty meanings until its
    // study-set row shard lands, so a pending row counts as a candidate and is
    // hydrated just before it is shown. Requiring meanings here left only the
    // landing set's cards -- for Spanish, a pool of clitics and pronouns.
    const valid = vocabData.filter(item =>
        item.word && item.word.trim() !== '' &&
        !item.duplicate &&
        (item._indexRowsPending === true || hasTranslatedMeaning(item)) &&
        (item.cognate_score ?? 0) < 0.83 &&
        !item.is_noise && !item.is_interjection &&
        !item.is_propernoun &&
        !item.is_english &&
        !isFunctionWord(item) &&
        (!hideSingleOccurrence || !item.hasOwnProperty('corpus_count') || item.corpus_count > 1)
    );

    // Candidates keep a reference to the deck card rather than a copy, so the
    // meanings a row shard merges into the deck reach the estimator too.
    // estimationRank is the position among candidates; results are mapped back
    // to deck ranks by deckRankForCount.
    valid.forEach((item, index) => { item.estimationRank = index + 1; });
    return valid;
}

function hasTranslatedMeaning(item) {
    return Array.isArray(item?.meanings)
        && item.meanings.some(meaning => meaning?.translation && String(meaning.translation).trim());
}

// Clitics, articles, pronouns and prepositions are known by every learner who
// can open the app, so they measure nothing. Before hydration this sees the
// clitic flags and function-word list; afterwards it also sees sense POS.
function isFunctionWord(item) {
    return globalThis.isGrammarParticleItem?.(item) === true;
}

// A candidate is ready once its meanings are loaded and it still qualifies.
function isShowableWord(word) {
    return word && word._indexRowsPending !== true
        && hasTranslatedMeaning(word) && !isFunctionWord(word);
}

async function hydrateEstimationWord(word) {
    if (!word || word._indexRowsPending !== true) return;
    try {
        await window.ensureIndexRowsForRange?.(
            getEstimationLangConfig(), 0, 0, [Number(word.rank)]
        );
    } catch (error) {
        console.warn('Level check could not load a word:', error);
    }
}

// The deck position of the count-th candidate: learners who know the first
// k candidates also know the cognates and function words ranked among them.
// stableRank is the basis of the level buttons; source rank is the fallback
// when the deck has not yet assigned stable ranks, and keeps the same order.
function deckRankForCount(words, count) {
    if (!words.length || count <= 0) return 0;
    const word = words[Math.min(words.length, Math.round(count)) - 1];
    const rank = Number(word?.stableRank) || Number(word?.rank);
    return Number.isFinite(rank) && rank > 0 ? rank : Math.round(count);
}

function buildCoverageOrder(count) {
    const order = [];
    const queue = [[0, count - 1]];
    while (queue.length > 0) {
        const [start, end] = queue.shift();
        if (start > end) continue;
        const middle = Math.floor((start + end) / 2);
        order.push(middle);
        queue.push([start, middle - 1], [middle + 1, end]);
    }
    return order;
}

function buildEstimationBands(words) {
    if (!words.length) return [];
    const bandCount = Math.max(1, Math.min(
        ESTIMATION_BAND_TARGET,
        Math.floor(words.length / 40) || 1
    ));

    return Array.from({ length: bandCount }, (_, index) => {
        const start = Math.floor(index * words.length / bandCount);
        const end = Math.floor((index + 1) * words.length / bandCount);
        return {
            index,
            start,
            end,
            size: end - start,
            answers: 0,
            known: 0
        };
    });
}

function getWordKey(word) {
    return String(word.id || `${word.word}|${word.lemma || ''}|${word.estimationRank}`);
}

function getLemmaKey(word) {
    return String(word.lemma || word.word || '').trim().toLocaleLowerCase();
}

// Pool adjacent violations so estimated knowledge cannot rise as words become
// less frequent. Each returned value corresponds to one frequency band.
function fitMonotonicProbabilities(values, weights) {
    const blocks = values.map((value, index) => ({
        start: index,
        end: index,
        value,
        weight: Math.max(Number(weights[index]) || 0, 0.0001)
    }));

    for (let index = 0; index < blocks.length - 1;) {
        if (blocks[index].value >= blocks[index + 1].value) {
            index++;
            continue;
        }

        const left = blocks[index];
        const right = blocks[index + 1];
        const weight = left.weight + right.weight;
        blocks.splice(index, 2, {
            start: left.start,
            end: right.end,
            value: ((left.value * left.weight) + (right.value * right.weight)) / weight,
            weight
        });
        if (index > 0) index--;
    }

    const fitted = new Array(values.length);
    blocks.forEach(block => {
        for (let index = block.start; index <= block.end; index++) {
            fitted[index] = block.value;
        }
    });
    return fitted;
}

function getPosteriorBandProbabilities(bands) {
    const values = bands.map(band =>
        (band.known + ESTIMATION_PRIOR) /
        (band.answers + (2 * ESTIMATION_PRIOR))
    );
    const weights = bands.map(band => band.answers + (2 * ESTIMATION_PRIOR));
    return fitMonotonicProbabilities(values, weights);
}

function chooseNextBandIndex() {
    const bands = estimationState.bands;
    if (!bands.length) return null;

    // First cover the whole frequency distribution in a centre-out order. A
    // learner is never estimated from a narrow run of unusually easy/hard words.
    const untested = estimationState.coverageOrder.find(index => bands[index].answers === 0);
    if (untested !== undefined) return untested;

    const fitted = getPosteriorBandProbabilities(bands);
    const rawPosterior = bands.map(band =>
        (band.known + ESTIMATION_PRIOR) /
        (band.answers + (2 * ESTIMATION_PRIOR))
    );
    const firstMostlyUnknown = fitted.findIndex(probability => probability < 0.5);
    let boundaryIndex;
    if (firstMostlyUnknown < 0) {
        boundaryIndex = fitted.length - 1;
    } else if (firstMostlyUnknown === 0) {
        boundaryIndex = 0;
    } else {
        const knownSide = firstMostlyUnknown - 1;
        boundaryIndex = Math.abs(fitted[knownSide] - 0.5) <=
            Math.abs(fitted[firstMostlyUnknown] - 0.5)
            ? knownSide
            : firstMostlyUnknown;
    }

    let bestIndex = 0;
    let bestScore = -Infinity;
    bands.forEach((band, index) => {
        const alpha = band.known + ESTIMATION_PRIOR;
        const beta = (band.answers - band.known) + ESTIMATION_PRIOR;
        const total = alpha + beta;
        const variance = (alpha * beta) / ((total * total) * (total + 1));
        const probability = alpha / total;
        const uncertainty = 1 + (1 - Math.min(1, Math.abs(probability - 0.5) * 2));
        const boundaryProximity = 1 + (1.5 / (1 + Math.abs(index - boundaryIndex)));

        // Recheck local reversals instead of allowing one anomalous response to
        // pull a whole stretch of the fitted curve in the wrong direction.
        const left = index > 0 ? rawPosterior[index - 1] : rawPosterior[index];
        const right = index < rawPosterior.length - 1
            ? rawPosterior[index + 1]
            : rawPosterior[index];
        const reversalBonus = (left < rawPosterior[index] || rawPosterior[index] < right)
            ? 1.35
            : 1;
        const score = variance * uncertainty * boundaryProximity * reversalBonus * band.size;

        if (score > bestScore) {
            bestScore = score;
            bestIndex = index;
        }
    });
    return bestIndex;
}

function pickWordFromBand(bandIndex) {
    const band = estimationState.bands[bandIndex];
    if (!band) return null;

    const prefetched = estimationState.prefetched.get(bandIndex);
    if (prefetched && !estimationState.shownWordIds.has(getWordKey(prefetched))) {
        return prefetched;
    }

    const words = estimationState.validWords.slice(band.start, band.end);
    const unused = words.filter(word => !estimationState.shownWordIds.has(getWordKey(word)));
    if (!unused.length) return null;

    // Never test the same lemma twice unless this band has no other unused
    // vocabulary left. Surface forms are otherwise sampled without pipeline-
    // specific preferences so the check reflects the deck it will place into.
    const freshLemmas = unused.filter(word =>
        !estimationState.shownLemmaKeys.has(getLemmaKey(word))
    );
    const candidates = freshLemmas.length ? freshLemmas : unused;
    return candidates[Math.floor(Math.random() * candidates.length)];
}

function findAvailableWord(preferredBandIndex) {
    const bandCount = estimationState.bands.length;
    for (let distance = 0; distance < bandCount; distance++) {
        const indices = distance === 0
            ? [preferredBandIndex]
            : [preferredBandIndex - distance, preferredBandIndex + distance];
        for (const index of indices) {
            if (index < 0 || index >= bandCount) continue;
            const word = pickWordFromBand(index);
            if (word) return { word, bandIndex: index };
        }
    }
    return null;
}

// Get translation for a word
function getWordTranslation(word) {
    if (!word?.meanings?.length) return '';
    return word.meanings.map(meaning => {
        const pos = meaning.pos ? `(${meaning.pos}) ` : '';
        return meaning.translation ? pos + meaning.translation : '';
    }).filter(Boolean).join(', ');
}

// Start the estimation test
async function startEstimation() {
    estimationState = createEstimationState();

    try {
        estimationState.vocabularyData = await fetchAndJoinIndex(getEstimationLangConfig());
    } catch (error) {
        alert('Failed to load vocabulary for estimation.');
        return;
    }

    estimationState.validWords = buildEstimationWordList();
    estimationState.maxLevel = estimationState.validWords.length;
    estimationState.bands = buildEstimationBands(estimationState.validWords);
    estimationState.coverageOrder = buildCoverageOrder(estimationState.bands.length);

    if (!estimationState.validWords.length) {
        alert('There are not enough vocabulary entries to run the level check.');
        return;
    }

    estimationState.active = true;
    document.getElementById('estimationIntro').style.display = 'none';
    document.getElementById('estimationTest').style.display = 'flex';
    document.getElementById('estimationResult').style.display = 'none';
    showNextWord();
}

// Pick the next word, loading its meanings if the index shipped it lean. A
// candidate that turns out to have no translation, or only function-word
// senses, is set aside and another is tried.
async function selectNextWord() {
    for (let attempt = 0; attempt < ESTIMATION_PICK_ATTEMPTS; attempt++) {
        const selection = findAvailableWord(chooseNextBandIndex());
        if (!selection) return null;
        const sequence = estimationState.sequence;
        await hydrateEstimationWord(selection.word);
        if (sequence !== estimationState.sequence) return null;
        if (isShowableWord(selection.word)) return selection;
        estimationState.shownWordIds.add(getWordKey(selection.word));
        estimationState.prefetched.delete(selection.bandIndex);
    }
    return null;
}

// While the learner reads a word, load a candidate for each band the next
// answer could send them to, so the following word appears without a wait.
function prefetchLikelyNextWords() {
    const bandIndex = estimationState.currentBandIndex;
    const band = estimationState.bands[bandIndex];
    if (!band) return;
    const targets = new Set();
    for (const known of [true, false]) {
        band.answers++;
        if (known) band.known++;
        targets.add(chooseNextBandIndex());
        band.answers--;
        if (known) band.known--;
    }
    targets.forEach(index => {
        if (index === null || index === undefined) return;
        const existing = estimationState.prefetched.get(index);
        if (existing && !estimationState.shownWordIds.has(getWordKey(existing))) return;
        estimationState.prefetched.delete(index);
        const word = pickWordFromBand(index);
        if (!word) return;
        estimationState.prefetched.set(index, word);
        hydrateEstimationWord(word);
    });
}

// loading blocks reveal and answers for the whole hand-over to the next word;
// showPlaceholder also blanks the card when that hand-over waits on a fetch.
function setEstimationLoading(loading, showPlaceholder = loading) {
    estimationState.loading = loading;
    if (showPlaceholder) {
        document.getElementById('estimationWord').textContent = 'Loading…';
        document.getElementById('estimationLemma').style.visibility = 'hidden';
        document.getElementById('estimationPOS').textContent = '';
        document.getElementById('estimationTranslation').classList.remove('visible');
        document.getElementById('estimationReveal').style.display = 'none';
        document.getElementById('estimationButtons').style.display = 'none';
    }
}

// Show the next word
async function showNextWord() {
    if (!estimationState.active || estimationState.loading) return;

    if (estimationState.wordsTestedCount >= ESTIMATION_QUESTION_LIMIT) {
        showEstimationResult();
        return;
    }

    const sequence = estimationState.sequence;
    const preferredBand = chooseNextBandIndex();
    const ready = findAvailableWord(preferredBand);
    setEstimationLoading(true, !(ready && isShowableWord(ready.word)));
    let selection;
    try {
        selection = await selectNextWord();
    } finally {
        if (sequence === estimationState.sequence) setEstimationLoading(false);
    }
    if (sequence !== estimationState.sequence || !estimationState.active) return;
    if (!selection) {
        showEstimationResult();
        return;
    }

    const { word, bandIndex } = selection;
    estimationState.prefetched.delete(bandIndex);
    estimationState.currentWord = word;
    estimationState.currentBandIndex = bandIndex;
    estimationState.translationRevealed = false;
    estimationState.shownWordIds.add(getWordKey(word));
    estimationState.shownLemmaKeys.add(getLemmaKey(word));

    document.getElementById('estimationWord').textContent = word.word;
    const lemmaEl = document.getElementById('estimationLemma');
    const lemma = word.lemma || '';
    if (lemma && lemma !== word.word) {
        lemmaEl.textContent = lemma;
        lemmaEl.style.visibility = 'visible';
    } else {
        lemmaEl.textContent = '';
        lemmaEl.style.visibility = 'hidden';
    }

    document.getElementById('estimationPOS').textContent = word.meanings?.[0]?.pos || '';
    const translationEl = document.getElementById('estimationTranslation');
    translationEl.textContent = getWordTranslation(word);
    translationEl.classList.remove('visible');
    document.getElementById('estimationReveal').style.display = 'block';
    document.getElementById('estimationButtons').style.display = 'none';
    updateEstimationProgress();
    prefetchLikelyNextWords();
}

// Reveal first, then self-score whether the meaning was known before reveal.
function revealTranslation() {
    if (!estimationState.active || estimationState.loading
        || estimationState.translationRevealed) return;
    estimationState.translationRevealed = true;
    document.getElementById('estimationTranslation').classList.add('visible');
    document.getElementById('estimationReveal').style.display = 'none';
    document.getElementById('estimationButtons').style.display = 'flex';
}

// Handle answer
function handleAnswer(known) {
    if (!estimationState.active || estimationState.loading
        || !estimationState.translationRevealed) return;
    const band = estimationState.bands[estimationState.currentBandIndex];
    if (!band) return;

    band.answers++;
    if (known) band.known++;
    estimationState.wordsTestedCount++;
    estimationState.translationRevealed = false;
    showNextWord();
}

function roundEstimate(value, maxLevel) {
    const increment = maxLevel >= 2000 ? 100 : 50;
    return Math.max(0, Math.min(maxLevel, Math.round(value / increment) * increment));
}

function calculateEstimationResult(bands, maxLevel) {
    if (!bands.length || !bands.some(band => band.answers > 0)) {
        return { point: 0, low: 0, high: 0 };
    }

    // Every band is sampled before adaptive repeats begin. Empirical rates keep
    // the point estimate capable of reaching the genuine endpoints; the prior is
    // reserved for selection and uncertainty rather than forcing every learner
    // toward 50%.
    const empirical = bands.map(band => band.answers ? band.known / band.answers : 0.5);
    const weights = bands.map(band => Math.max(1, band.answers));
    const fitted = fitMonotonicProbabilities(empirical, weights);
    const pointRaw = bands.reduce((total, band, index) =>
        total + (band.size * fitted[index]), 0);

    // Sum independent beta-binomial band uncertainty. It is intentionally a
    // conservative approximation: the result is presented as a useful range,
    // not as calibrated IRT precision that Fluency does not yet possess.
    const variance = bands.reduce((totalVariance, band) => {
        const alpha = band.known + ESTIMATION_PRIOR;
        const beta = (band.answers - band.known) + ESTIMATION_PRIOR;
        const total = alpha + beta;
        const probabilityVariance = (alpha * beta) /
            ((total * total) * (total + 1));
        return totalVariance + (band.size * band.size * probabilityVariance);
    }, 0);
    const margin = ESTIMATION_CONFIDENCE_Z * Math.sqrt(variance);

    return {
        point: roundEstimate(pointRaw, maxLevel),
        low: roundEstimate(Math.max(0, pointRaw - margin), maxLevel),
        high: roundEstimate(Math.min(maxLevel, pointRaw + margin), maxLevel)
    };
}

// Update progress display. Avoid presenting a volatile pseudo-precise rank while
// the sample is still being collected.
function updateEstimationProgress() {
    document.getElementById('estimationLevel').textContent = 'Finding your range';
    document.getElementById('estimationCount').textContent =
        `${estimationState.wordsTestedCount}/${ESTIMATION_QUESTION_LIMIT}`;
}

// Show the estimation result
function showEstimationResult() {
    estimationState.active = false;
    estimationState.sequence = ++estimationSequence;
    const counts = calculateEstimationResult(
        estimationState.bands,
        estimationState.maxLevel
    );
    // The fit counts known candidates; levels and the saved estimate are deck
    // ranks, which also cover the cognates and function words left out here.
    const candidates = estimationState.validWords;
    const result = {
        point: deckRankForCount(candidates, counts.point),
        low: deckRankForCount(candidates, counts.low),
        high: deckRankForCount(candidates, counts.high)
    };
    const shown = value => roundEstimate(value, Infinity).toLocaleString();
    estimationState.estimatedLevel = result.point;
    estimationState.estimateInterval = result;

    if (estimationState.autoAdvanceTimer) {
        clearTimeout(estimationState.autoAdvanceTimer);
        estimationState.autoAdvanceTimer = null;
    }

    document.getElementById('estimationTest').style.display = 'none';
    document.getElementById('estimationResult').style.display = 'block';

    const levelEl = document.getElementById('estimationResultLevel');
    const descEl = document.getElementById('estimationResultDesc');
    const pointLevel = levelButtonForRank(result.point);
    const ranOut = estimationState.wordsTestedCount < ESTIMATION_QUESTION_LIMIT;
    if (result.point <= 0) {
        levelEl.textContent = 'Start at Level 1';
        descEl.textContent = ranOut
            ? `The check ran out of words after ${estimationState.wordsTestedCount}, so it could not place you.`
            : 'Most of the words sampled were new to you.';
    } else if (pointLevel) {
        // The estimate is stored as a rank; the level is only derived here,
        // against the levels on screen, so it follows any change to level size.
        const lowLevel = levelButtonForRank(result.low)?.number ?? pointLevel.number;
        const highLevel = levelButtonForRank(result.high)?.number ?? pointLevel.number;
        const words = `${shown(result.low)}–${shown(result.high)} words`;
        levelEl.textContent = `Start at Level ${pointLevel.number}`;
        descEl.textContent = lowLevel === highLevel
            ? `About ${words} you'd recognise.`
            : `Likely somewhere in Levels ${lowLevel}–${highLevel} (about ${words}).`;
    } else {
        levelEl.textContent = `${shown(result.low)}–${shown(result.high)} words`;
        descEl.textContent =
            `Best estimate: about ${shown(result.point)} receptive words. ` +
            'The range reflects uncertainty from a short check.';
    }
}

// The level button whose [startRank, endRank) span holds a rank, clamped to the
// first and last levels. Both the result screen and the landing use it, so the
// level named is the level that opens.
function levelButtonForRank(rank) {
    const buttons = Array.from(document.querySelectorAll(
        '.level-selector-buttons .level-btn, #levelSelector > .level-btn'
    )).filter(button => Number.isFinite(Number(button.dataset.startRank))
        && Number.isFinite(Number(button.dataset.endRank))
        && button.dataset.startRank !== '' && button.dataset.endRank !== '');
    if (!buttons.length) return null;
    let index = buttons.findIndex(button =>
        rank >= Number(button.dataset.startRank) && rank < Number(button.dataset.endRank));
    if (index < 0) index = rank < Number(buttons[0].dataset.startRank) ? 0 : buttons.length - 1;
    return { button: buttons[index], number: index + 1 };
}

// Apply the point estimate. The interval remains explanatory UI; the existing
// progress contract intentionally stores one backwards-compatible rank value.
function useEstimatedLevel() {
    const level = estimationState.estimatedLevel;
    levelEstimates[selectedLanguage] = level;
    saveLevelEstimateToSheet(level);
    closeEstimationModal();

    if (level === 0) {
        document.querySelector('.level-btn')?.click();
    } else {
        selectLevelForRank(level);
    }
}

function retryEstimation() {
    estimationState = createEstimationState();
    document.getElementById('estimationResult').style.display = 'none';
    startEstimation();
}

// Open the level containing a given rank; the level's own routing then lands
// on its first set with unseen cards.
function selectLevelForRank(rank) {
    levelButtonForRank(rank)?.button.click();
}

window.openEstimationModal = openEstimationModal;
window.closeEstimationModal = closeEstimationModal;
window.startEstimation = startEstimation;
window.handleAnswer = handleAnswer;
window.revealTranslation = revealTranslation;
window.showEstimationResult = showEstimationResult;
window.useEstimatedLevel = useEstimatedLevel;
window.retryEstimation = retryEstimation;
window.selectLevelForRank = selectLevelForRank;

// Pure helpers are exported for lightweight regression checks without a DOM.
export {
    buildCoverageOrder,
    buildEstimationBands,
    fitMonotonicProbabilities,
    calculateEstimationResult
};
