import './state.js?v=20260825ak';

const ESTIMATION_QUESTION_LIMIT = 30;
const ESTIMATION_BAND_TARGET = 10;
const ESTIMATION_SET_DETAIL_MAX_LEVEL = 10;
const ESTIMATION_CONFIDENCE_Z = 1.645; // Approximate 90% interval.
const ESTIMATION_PRIOR = 0.5;          // Jeffreys prior for adaptive selection.
const ESTIMATION_PICK_ATTEMPTS = 48;   // Candidates tried per question before giving up.

// Always use the Speech vocabulary for placement. Artist ordering measures
// familiarity with one corpus, not general vocabulary size. In an artist deck
// the estimate is not a level: it marks the Speech words ranked within it as
// known (buildEstimatedKnownIds), which lands the learner past them.
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
        answers: [],
        placementHistory: [],
        recheck: null,
        profileKey: null,
        ownerKey: null,
        vocabularyData: null,
        placementWords: [],
        placementBaseline: [],
        placementLevels: [],
        placementChoices: [],
        langConfig: null,
        groupEstimate: null,
        validWords: [],
        bands: [],
        coverageOrder: [],
        maxLevel: 0,
        wordsTestedCount: 0,
        shownWordIds: new Set(),
        prefetched: new Map(),
        currentWord: null,
        loading: false,
        sequence: ++estimationSequence,
        currentBandIndex: null,
        translationRevealed: false,
        estimatedLevel: null,
        estimatedLevelRank: 0,
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
    const fillEl = document.getElementById('estimationProgressFill');
    if (fillEl) fillEl.style.width = '0%';
    // Words you already know can come in by list instead. Import only exists
    // for signed-in learners; it does not feed the estimate.
    const importLink = document.getElementById('estimationImportKnownBtn');
    if (importLink) importLink.hidden = !(currentUser && !currentUser.isGuest);
    estimationState = createEstimationState();
    document.getElementById('retryEstimationBtn').hidden = false;
    const keep = document.getElementById('estimationKeepPosition');
    if (keep) keep.hidden = true;
}

// Close estimation modal
function closeEstimationModal() {
    document.getElementById('estimationModal').classList.add('hidden');
    if (estimationState.recheck) finishPlacementRecheck();
    estimationState.active = false;
    estimationState.loading = false;
    estimationState.sequence = ++estimationSequence;
    if (estimationState.autoAdvanceTimer) {
        clearTimeout(estimationState.autoAdvanceTimer);
    }
}

// Keep the historical exclusions, but resolve the same merge/split decisions
// as the study deck before constructing the sampling distribution.
function estimationAssumesKnown(item) {
    if (typeof window.isCognateKnown === 'function') return window.isCognateKnown(item);
    return (item.cognate_score ?? (item.is_transparent_cognate ? 1 : 0)) >= 0.83;
}

function estimationSurfaceEligible(item) {
    return item.word && item.word.trim() !== '' && !item.duplicate
        && hasTranslatedMeaning(item)
        && !item.is_noise && !item.is_interjection && !item.is_propernoun
        && !item.is_english && !isFunctionWord(item)
        && ESTIMATION_CONTENT_POS.has(mainSensePos(item))
        && (!hideSingleOccurrence || !Object.hasOwn(item, 'corpus_count') || item.corpus_count > 1);
}

function assignedSenseWeight(item, meaning) {
    const id = meaning.sense_id || meaning.senseId;
    const count = item.wsd_distribution?.published_leaf_counts?.[id]
        ?? item.wsd_distribution?.supported_leaf_counts?.[id];
    const value = Number(meaning.frequency ?? meaning.percentage ?? meaning.display_frequency ?? count);
    return Number.isFinite(value) && value > 0 ? value : 0;
}

function estimationExampleText(meaning, example) {
    return String(example?.target || example?.spanish || example?.sentence
        || example?.text || meaning?.targetSentence || meaning?.canonical_example?.text || '').trim();
}

function attachEstimationExample(item, examples = {}) {
    if (!item.splitInfo) return;
    const source = item.estimationMembers[0].source;
    for (const meaning of item.meanings) {
        const index = meaning._masterSenseIndex ?? meaning._estimationSourceIndex;
        const candidates = [...(meaning.examples || []), ...(examples[source.id]?.m?.[index] || [])];
        for (const example of [null, ...candidates]) {
            const text = estimationExampleText(meaning, example);
            if (text) {
                item.estimationExample = text;
                return;
            }
        }
    }
}

function estimationSurfaceFrequency(item, frequencyData) {
    const surface = String(item.word).normalize('NFC').toLocaleLowerCase();
    const value = Number(frequencyData?.values?.[surface] ?? item.corpus_count);
    return Number.isFinite(value) && value > 0 ? value : 0;
}

// This pool is independent of the user's Merge Forms toggle. The toggle
// changes study presentation, not what a vocabulary estimate measures.
function buildEstimationPool(vocabulary, frequencyData = null, { includeAssumed = false } = {}) {
    const eligible = vocabulary.filter(estimationSurfaceEligible);
    const groups = new Map();
    const items = [];
    for (const source of eligible) {
        const meanings = source.meanings.map((meaning, index) => ({
            ...meaning, meaning: meaning.translation,
            senseId: meaning.sense_id || meaning.senseId,
            percentage: assignedSenseWeight(source, meaning),
            _estimationAssignedWeight: assignedSenseWeight(source, meaning),
            _estimationSourceIndex: index
        }));
        const finished = window.finishCardMeanings(source, meanings);
        const pair = window.buildSplitCardPair(source, {
            ...source, ...finished, targetWord: source.word,
            // Detached Speech questions must not register artist progress IDs.
            fullId: `${window.LANG_CODES[selectedLanguage] || selectedLanguage.slice(0, 2)}0${source.id}`
        }, finished.meanings, selectedLanguage);
        const frequency = estimationSurfaceFrequency(source, frequencyData);
        if (pair) {
            const tuples = window.detectSplitCardTuples(source, selectedLanguage);
            const weights = (tuples.tuples || [tuples.tuple1, tuples.tuple2]).map(tuple => tuple.meanings
                .reduce((sum, meaning) => sum + assignedSenseWeight(source, meaning), 0));
            const total = weights.reduce((sum, value) => sum + value, 0);
            // Allocate corpus frequency using assigned usage on each companion.
            // Missing evidence leaves it untested.
            if (total <= 0) continue;
            pair.forEach((card, index) => {
                const share = weights[index] / total;
                if (share <= 0) return;
                const item = {
                    ...source, id: card.id, lemma: card.citationForm,
                    meanings: card.meanings.map(m => ({ ...m, translation: m.meaning })),
                    splitInfo: card.splitInfo,
                    estimationKey: `split:${card.id}`,
                    estimationFrequency: frequency * share,
                    estimationMembers: [{ source, weight: share }]
                };
                if (!estimationSurfaceEligible(item)) return;
                attachEstimationExample(item);
                items.push(item);
            });
            continue;
        }
        const lemma = window.lemmaStudyGroupKey(source);
        if (!lemma) {
            items.push({ ...source, estimationKey: `surface:${source.id || source.word}`,
                estimationFrequency: frequency, estimationMembers: [{ source, weight: 1 }] });
            continue;
        }
        const key = `lemma:${lemma}`;
        let group = groups.get(key);
        if (!group) {
            group = { ...source, estimationKey: key, estimationFrequency: 0,
                estimationRepresentativeFrequency: -1, estimationMembers: [] };
            groups.set(key, group);
            items.push(group);
        }
        group.estimationMembers.push({ source, weight: 1 });
        group.estimationFrequency += frequency;
        if (frequency > group.estimationRepresentativeFrequency
            || (frequency === group.estimationRepresentativeFrequency && Number(source.rank) < Number(group.rank))) {
            Object.assign(group, { word: source.word, id: source.id, lemma: source.lemma,
                meanings: source.meanings, rank: source.rank, stableRank: source.stableRank,
                estimationRepresentativeFrequency: frequency });
        }
    }
    for (const item of items) {
        item.estimationMembers.forEach(member => { member.assumedKnown = estimationAssumesKnown(member.source); });
        if (item.splitInfo) {
            item.estimationAssumedKnown = estimationAssumesKnown(item);
        } else {
            item.estimationAssumedKnown = item.estimationMembers.every(({ source }) => estimationAssumesKnown(source));
            // A mixed group is asked through its most frequent non-cognate
            // member. A transparent prompt must not stand in for harder forms.
            if (!item.estimationAssumedKnown) {
                const prompts = item.estimationMembers.map(member => member.source)
                    .filter(source => !estimationAssumesKnown(source))
                    .sort((a, b) => estimationSurfaceFrequency(b, frequencyData) - estimationSurfaceFrequency(a, frequencyData)
                        || Number(a.rank) - Number(b.rank));
                const source = prompts[0];
                if (source) Object.assign(item, { estimationPrompt: source, word: source.word, id: source.id, meanings: source.meanings,
                    lemma: source.lemma, rank: source.rank, stableRank: source.stableRank });
            }
        }
    }
    const included = includeAssumed ? items : items.filter(item => !item.estimationAssumedKnown);
    included.sort((a, b) => b.estimationFrequency - a.estimationFrequency
        || Number(a.rank) - Number(b.rank) || a.estimationKey.localeCompare(b.estimationKey));
    return included;
}

function finalizeEstimationPool(items) {
    const valid = items.filter(item => !item.splitInfo || item.estimationExample);
    valid.forEach((item, index) => { item.estimationRank = index + 1; });
    const surfaces = new Map();
    for (const item of valid) {
        for (const { source } of item.estimationMembers) surfaces.set(source.id || source.word, source);
    }
    return { items: valid, placementWords: [...surfaces.values()].sort((a, b) => Number(a.rank) - Number(b.rank)) };
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

// Only content words measure vocabulary size. A word is tested when its main
// sense (the most frequent, else the first) is one of these; pronouns,
// clitics, articles, prepositions, conjunctions, auxiliaries, numbers,
// interjections, names, contractions and phrases are all skipped.
const ESTIMATION_CONTENT_POS = new Set(['NOUN', 'VERB', 'ADJ', 'ADV']);

function mainSensePos(word) {
    const meanings = (word?.meanings || []).filter(m => m?.translation && String(m.translation).trim());
    if (!meanings.length) return '';
    const share = m => parseFloat(m.display_frequency ?? m.frequency ?? m.percentage) || 0;
    const main = meanings.reduce((best, m) => (share(m) > share(best) ? m : best), meanings[0]);
    const rawPos = (main.pos === 'SENSE_CYCLE' ? main.cycle_pos : main.pos) || '';
    return String(rawPos).toUpperCase();
}

// A candidate is ready once its meanings are loaded and it still qualifies.
function isShowableWord(word) {
    return word && !word.estimationAssumedKnown && !estimationAssumesKnown(word) && (!word.splitInfo || Boolean(word.estimationExample)) && word._indexRowsPending !== true
        && hasTranslatedMeaning(word) && !isFunctionWord(word)
        && ESTIMATION_CONTENT_POS.has(mainSensePos(word));
}

async function hydrateEstimationWord(word) {
    // Metadata is complete before bands are built; examples for split readings
    // were fetched separately without hydrating the rest of the deck.
    return word;
}

function isSpeechMode() {
    return !activeArtist && !window.playlistLiveActive?.();
}

function candidateForCount(words, count) {
    if (!words.length || count <= 0) return null;
    return words[Math.min(words.length, Math.round(count)) - 1] || null;
}

// The saved estimate is the Speech source rank of the count-th candidate:
// learners who know the first k candidates also know the cognates and function
// words ranked among them. Source rank is what setup and Learn New compare
// (item.rank <= estimate) and what buildEstimatedKnownIds walks.
function deckRankForCount(words, count) {
    const rank = Number(candidateForCount(words, count)?.rank);
    return Number.isFinite(rank) && rank > 0 ? rank : Math.max(0, Math.round(count));
}

// Level buttons span stable ranks, which skip cards the deck leaves out, so
// the level is looked up by the same candidate's stable rank.
function levelRankOf(word) {
    return Number(word?.stableRank) || Number(word?.rank) || 0;
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

    // Narrower early bands give the first few sets meaningful resolution,
    // while still sampling the entire pool within the same 30-question check.
    const edges = [0];
    for (let index = 0; index < bandCount; index++) {
        const end = bandCount === 1 || index === bandCount - 1 ? words.length
            : Math.round(40 * Math.pow(words.length / 40, index / (bandCount - 1)));
        edges.push(Math.min(words.length, Math.max(edges[index] + 1, end)));
    }
    return Array.from({ length: bandCount }, (_, index) => {
        const start = edges[index];
        const end = edges[index + 1];
        return {
            index,
            start,
            end,
            size: end - start,
            sampleSize: words.slice(start, end).filter(item => !item.estimationAssumedKnown).length,
            assumedCount: words.slice(start, end).filter(item => item.estimationAssumedKnown).length,
            answers: 0,
            known: 0
        };
    });
}

function getWordKey(word) {
    return word.estimationKey || String(word.id || `${word.word}|${word.estimationRank}`);
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
    const untested = !estimationState.recheck ? estimationState.coverageOrder.find(index => bands[index] && bands[index].answers === 0 && bands[index].sampleSize !== 0) : undefined;
    if (untested !== undefined) return untested;

    const fitted = getPosteriorBandProbabilities(bands);
    const rawPosterior = bands.map(band =>
        (band.known + ESTIMATION_PRIOR) /
        (band.answers + (2 * ESTIMATION_PRIOR))
    );
    const targets = estimationState.recheck ? [estimationState.recheck.choice.target] : [0.9, 0.8];
    const boundaries = targets.map(target => {
        const index = fitted.findIndex(probability => probability < target);
        return index < 0 ? bands.length - 1 : index;
    });
    const adaptiveCount = estimationState.wordsTestedCount - bands.filter(b => b.sampleSize > 0).length;
    const gapCheck = !estimationState.recheck && adaptiveCount >= 0 && (adaptiveCount + 1) % 5 === 0;
    const earlierBoundary = Math.min(...boundaries);
    let bestIndex = 0;
    let bestScore = -Infinity;
    bands.forEach((band, index) => {
        if (band.sampleSize === 0 || (estimationState.recheck && !pickWordFromBand(index))) return;
        const alpha = band.known + ESTIMATION_PRIOR;
        const beta = (band.answers - band.known) + ESTIMATION_PRIOR;
        const total = alpha + beta;
        const variance = (alpha * beta) / ((total * total) * (total + 1));
        const probability = alpha / total;
        const uncertainty = 1 + (1 - Math.min(1, Math.min(...targets.map(target => Math.abs(probability - target))) * 2));
        const boundaryProximity = 1 + (1.5 / (1 + Math.min(...boundaries.map(boundary => Math.abs(index - boundary)))));

        // Recheck local reversals instead of allowing one anomalous response to
        // pull a whole stretch of the fitted curve in the wrong direction.
        const left = index > 0 ? rawPosterior[index - 1] : rawPosterior[index];
        const right = index < rawPosterior.length - 1
            ? rawPosterior[index + 1]
            : rawPosterior[index];
        const reversalBonus = (left < rawPosterior[index] || rawPosterior[index] < right)
            ? 1.35
            : 1;
        if (gapCheck && index > earlierBoundary && reversalBonus === 1) return;
        const score = variance * uncertainty * boundaryProximity * reversalBonus;

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
    if (prefetched && isShowableWord(prefetched) && recheckWordEligible(prefetched) && !estimationState.shownWordIds.has(getWordKey(prefetched))) {
        return prefetched;
    }

    const words = estimationState.validWords.slice(band.start, band.end);
    const unused = words.filter(word => isShowableWord(word) && recheckWordEligible(word) && !estimationState.shownWordIds.has(getWordKey(word)));
    if (!unused.length) return null;

    return unused[Math.floor(Math.random() * unused.length)];
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
// Glosses read as the card back's sense rows do: inflected for this surface
// (tengo -> "I have") where the conjugation data supports it, the dictionary
// gloss otherwise. The same (POS, gloss) pair is listed once.
function getWordTranslation(word) {
    if (!word?.meanings?.length) return '';
    const meanings = word.meanings
        .filter(m => m?.translation && String(m.translation).trim())
        .map(m => ({
            pos: m.pos,
            meaning: m.translation,
            ...(m.context ? { context: m.context } : {}),
            ...(m.headword ? { headword: m.headword } : {}),
            ...(m.metadata ? { metadata: m.metadata } : {})
        }));
    let card = null;
    try {
        card = {
            targetWord: word.word,
            lemma: word.lemma || '',
            ...(window.buildCardFormModel?.(word, meanings) || {}),
            id: word.id,
            meanings
        };
    } catch (_) {
        card = null;
    }
    const seen = new Set();
    const parts = [];
    for (const meaning of meanings) {
        let gloss = meaning.meaning;
        if (card && typeof window.getProductionEnglishCue === 'function') {
            try {
                gloss = String(window.getProductionEnglishCue(card, meaning, {
                    activeExample: null,
                    reverseDirection: false
                }) || '').trim() || gloss;
            } catch (_) {}
        }
        gloss = String(gloss).trim();
        const rawPos = (meaning.pos === 'SENSE_CYCLE' ? meaning.cycle_pos : meaning.pos) || '';
        const cleanPos = rawPos && rawPos !== 'SENSE_CYCLE' ? rawPos : '';
        const key = `${cleanPos}|${gloss.toLocaleLowerCase()}`;
        if (!gloss || seen.has(key)) continue;
        seen.add(key);
        parts.push(cleanPos ? `(${cleanPos}) ${gloss}` : gloss);
    }
    return parts.join(', ');
}

// Shown with the meaning, never before it, so it cannot sway the answer.
function getWordRankLabel(word) {
    const rank = Number(word?.rank);
    if (!Number.isFinite(rank) || rank <= 0) return '';
    if (!isSpeechMode()) return `Speech #${rank.toLocaleString()}`;
    const level = levelButtonForRank(levelRankOf(word));
    return level
        ? `Level ${level.number} · #${rank.toLocaleString()}`
        : `#${rank.toLocaleString()}`;
}

// Start the estimation test
async function startEstimation(recheck = null) {
    estimationState = createEstimationState();
    const state = estimationState;
    state.recheck = recheck;
    state.ownerKey = placementStorageKey();
    const sequence = state.sequence;
    state.langConfig = { ...getEstimationLangConfig() };
    state.loading = true;
    document.getElementById('estimationIntro').style.display = 'none';
    document.getElementById('estimationTest').style.display = 'flex';
    document.getElementById('estimationResult').style.display = 'none';
    setEstimationLoading(true);
    const current = () => estimationState === state && state.sequence === sequence;
    const progress = text => {
        if (current()) document.getElementById('estimationLevel').textContent = text;
    };
    progress('Preparing vocabulary groups…');
    try {
        Promise.resolve(window.loadConjugationData?.()).catch(() => {});

        // v1 pools bake in one cognate profile and omit source/sense metadata.
        // They cannot safely answer for the current learner; use the cached
        // detached vocabulary instead until a profile-independent format exists.
        const [vocabulary, frequency] = await Promise.all([
            window.loadEstimationVocabulary(state.langConfig, (done, total) =>
                progress(`Preparing vocabulary groups · ${Math.round(done / total * 100)}%`)),
            window.loadSpeechSourceFrequency(state.langConfig, { detached: true })
        ]);
        if (!current()) return;
        if (state.langConfig.frequencyPath && !frequency) {
            throw new Error('Speech source frequencies are unavailable or do not match this release');
        }
        // The cached detached release is reused on retry; keep per-check
        // scoring and rank preparation on fresh rows.
        const rows = vocabulary.map(item => ({ ...item }));
        await window.prepareEstimationCognates?.(rows, state.langConfig);
        if (!current()) return;
        state.vocabularyData = rows;
        state.placementBaseline = window.assignStableVocabularyRanks
            ? window.assignStableVocabularyRanks(rows, new Set(), { detached: true }) : rows;
        state.placementLevels = getEstimationPlacementLevels(state.placementBaseline);
        const pool = buildEstimationPool(rows, frequency, { includeAssumed: true });
        const ranks = [...new Set(pool.filter(item => item.splitInfo && !item.estimationExample)
            .map(item => Number(item.rank)))];
        if (ranks.length) {
            progress('Preparing examples for separate readings…');
            const examples = await window.loadEstimationExamples(state.langConfig, ranks);
            if (!current()) return;
            pool.forEach(item => attachEstimationExample(item, examples));
        }
        const prepared = finalizeEstimationPool(pool);
        state.validWords = prepared.items;
        state.placementWords = prepared.placementWords;
        state.maxLevel = state.validWords.length;
        state.bands = buildEstimationBands(state.validWords);
        state.coverageOrder = buildCoverageOrder(state.bands.length);
        if (!state.validWords.length) throw new Error('No eligible vocabulary groups');
        state.profileKey = placementProfileKey();
        if (recheck) seedPlacementRecheck(state, recheck);
        state.active = true;
        setEstimationLoading(false);
        await showNextWord();
    } catch (error) {
        if (!current()) return;
        console.warn('Level check preparation failed:', error);
        if (recheck) finishPlacementRecheck();
        state.active = false;
        setEstimationLoading(false);
        document.getElementById('estimationTest').style.display = 'none';
        document.getElementById('estimationIntro').style.display = 'block';
        alert('The level check could not prepare the vocabulary. Please try again.');
    }
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
        const exampleEl = document.getElementById('estimationExample');
        if (exampleEl) { exampleEl.textContent = ''; exampleEl.hidden = true; }
        document.getElementById('estimationLemma').style.visibility = 'hidden';
        const posEl = document.getElementById('estimationPOS');
        if (posEl) {
            posEl.textContent = '';
            posEl.style.display = 'none';
        }
        document.getElementById('estimationTranslation').classList.remove('visible');
        document.getElementById('estimationRank')?.classList.remove('visible');
        document.getElementById('estimationReveal').style.display = 'none';
        document.getElementById('estimationButtons').style.display = 'none';
    }
}

// Show the next word
async function showNextWord() {
    if (!estimationState.active || estimationState.loading) return;

    if (estimationState.profileKey && (estimationState.profileKey !== placementProfileKey() || estimationState.ownerKey !== placementStorageKey())) {
        closeEstimationModal();
        alert('Your vocabulary settings changed. Please start a fresh level check.');
        return;
    }
    if (estimationState.wordsTestedCount >= estimationQuestionLimit() || placementIsStable()) {
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

    document.getElementById('estimationWord').textContent = word.word;
    const lemmaEl = document.getElementById('estimationLemma');
    // Recognition is of this form in this reading. A dictionary headword on
    // the front would give away an irregular form before the learner answers.
    lemmaEl.textContent = '';
    lemmaEl.style.visibility = 'hidden';

    const exampleEl = document.getElementById('estimationExample');
    if (exampleEl) {
        exampleEl.textContent = word.estimationExample || '';
        exampleEl.hidden = !word.estimationExample;
    }

    const displayPos = mainSensePos(word);
    const posEl = document.getElementById('estimationPOS');
    if (posEl) {
        if (displayPos && displayPos !== 'SENSE_CYCLE') {
            posEl.textContent = displayPos.toLowerCase();
            posEl.style.display = 'inline-block';
        } else {
            posEl.textContent = '';
            posEl.style.display = 'none';
        }
    }
    // The gloss is written at reveal, by which time the conjugation tables
    // that inflect it have usually arrived.
    const translationEl = document.getElementById('estimationTranslation');
    translationEl.textContent = '';
    translationEl.classList.remove('visible');
    const rankEl = document.getElementById('estimationRank');
    if (rankEl) {
        rankEl.textContent = '';
        rankEl.classList.remove('visible');
    }
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
    const word = estimationState.currentWord;
    const translationEl = document.getElementById('estimationTranslation');
    translationEl.textContent = getWordTranslation(word);
    translationEl.classList.add('visible');
    const rankEl = document.getElementById('estimationRank');
    if (rankEl) {
        rankEl.textContent = getWordRankLabel(word);
        rankEl.classList.add('visible');
    }
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
    estimationState.answers.push({ key: getWordKey(estimationState.currentWord), known: Boolean(known) });
    estimationState.wordsTestedCount++;
    estimationState.placementHistory.push(placementSignature());
    estimationState.translationRevealed = false;
    showNextWord();
}

function roundEstimate(value, maxLevel) {
    const increment = maxLevel >= 2000 ? 100 : (maxLevel >= 100 ? 50 : 1);
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

// Update progress display with dynamic phase status and progress bar.
function updateEstimationProgress() {
    const count = estimationState.wordsTestedCount;
    let phase = 'Broad sampling';
    if (count > 20) {
        phase = 'Calibrating level';
    } else if (count > 10) {
        phase = 'Narrowing range';
    }
    const levelEl = document.getElementById('estimationLevel');
    if (levelEl) levelEl.textContent = phase;

    const countEl = document.getElementById('estimationCount');
    if (countEl) countEl.textContent = `${count}/${estimationQuestionLimit()}`;

    const fillEl = document.getElementById('estimationProgressFill');
    if (fillEl) {
        const pct = Math.min(100, Math.round((count / estimationQuestionLimit()) * 100));
        fillEl.style.width = `${pct}%`;
    }
}

// Speech placement uses the same level boundaries as the picker. Artist and
// playlist checks use detached Speech boundaries, never the active corpus.
function getEstimationPlacementLevels(baseline) {
    if (isSpeechMode()) {
        const buttons = Array.from(document.querySelectorAll(
            '.level-selector-buttons .level-btn, #levelSelector > .level-btn'));
        const levels = buttons.map((button, index) => ({
            number: index + 1, startRank: Number(button.dataset.startRank),
            endRank: Number(button.dataset.endRank), rankBasis: button.dataset.rankBasis || 'source'
        })).filter(level => level.startRank > 0 && level.endRank > level.startRank
            && baseline.some(source => {
                const rank = level.rankBasis === 'stable' ? levelRankOf(source) : Number(source.rank);
                return rank >= level.startRank && rank < level.endRank;
            }));
        if (levels.length) return levels;
    }
    return (window.computeSmartLevelRanges?.(baseline) || []).map((level, index) =>
        ({ ...level, number: index + 1 }));
}

function interpolateRecognition(anchors, position) {
    if (!anchors.length) return 0;
    if (position <= anchors[0].position) return anchors[0].probability;
    for (let index = 1; index < anchors.length; index++) {
        const right = anchors[index];
        if (position <= right.position) {
            const left = anchors[index - 1];
            const fraction = (position - left.position) / (right.position - left.position);
            return left.probability + fraction * (right.probability - left.probability);
        }
    }
    return anchors[anchors.length - 1].probability;
}

// Only the early levels need set detail. Beyond the cutoff, retain the
// whole-level boundary and avoid implying finer placement precision.
function buildEstimationPlacementRegions(levels) {
    return levels.flatMap(level => {
        const sets = level.number <= ESTIMATION_SET_DETAIL_MAX_LEVEL
            ? window.buildStableSetRanges?.(level.startRank, level.endRank, level.rankBasis) || [] : [];
        return sets.length > 1 ? sets.map(set => ({ ...level, ...set, levelStartRank: level.startRank, levelEndRank: level.endRank })) : [{ ...level, setNumber: null }];
    });
}

// Every eligible group counts once within a level, regardless of how many
// inflections it has. Split siblings remain distinct groups. The recognition
// curve is interpolated between sampled bands so a sparse sample cannot turn
// a single answer into a sharp placement cliff.
function calculateRecognitionPlacement(items, bands, levels, baseline, targets = [0.9, 0.8]) {
    const regions = buildEstimationPlacementRegions(levels);
    const sampled = bands.filter(band => (band.sampleSize ?? band.size) > 0);
    const fitted = fitMonotonicProbabilities(sampled.map(band =>
        band.answers ? band.known / band.answers : 0.5), sampled.map(band => Math.max(1, band.answers)));
    const anchors = sampled.map((band, index) => ({
        position: (band.start + band.end - 1) / 2, probability: fitted[index]
    }));
    const perLevel = regions.map(() => new Map());
    items.forEach((item, index) => {
        const probability = item.estimationAssumedKnown ? 1 : interpolateRecognition(anchors, index);
        item.estimationMembers.forEach(member => {
            const levelIndex = regions.findIndex(level => {
                const rank = level.rankBasis === 'stable' ? levelRankOf(member.source) : Number(member.source.rank);
                return rank >= level.startRank && rank < level.endRank;
            });
            if (levelIndex < 0) return;
            const map = perLevel[levelIndex];
            const group = map.get(getWordKey(item)) || { total: 0, weight: 0 };
            // For an unsplit mixed group only the qualifying surfaces receive
            // assumed recognition. A split is scored from its own meanings.
            const known = item.estimationAssumedKnown || (!item.splitInfo && member.assumedKnown);
            group.total += member.weight * (known ? 1 : probability);
            group.weight += member.weight;
            map.set(getWordKey(item), group);
        });
    });
    const occupied = perLevel.map((groups, index) => ({ index, groups })).filter(row => row.groups.size);
    const probabilities = fitMonotonicProbabilities(occupied.map(({ groups }) =>
        [...groups.values()].reduce((sum, group) => sum + group.total / group.weight, 0) / groups.size),
        occupied.map(({ groups }) => groups.size));
    const levelAnchors = occupied.map((row, index) => ({ position: row.index, probability: probabilities[index] }));
    const profile = regions.map((level, index) => ({ ...level,
        probability: interpolateRecognition(levelAnchors, index), groups: perLevel[index].size }));
    const choices = targets.map(target => {
        const index = profile.findIndex(level => level.probability + 1e-10 < target);
        const level = profile[index < 0 ? profile.length - 1 : index];
        if (!level) return null;
        const earlier = baseline.filter(source =>
            (level.rankBasis === 'stable' ? levelRankOf(source) : Number(source.rank)) < level.startRank);
        const sourceRank = earlier.reduce((rank, source) => Math.max(rank, Number(source.rank) || 0), 0);
        return { target, levelNumber: level.number, setNumber: level.setNumber, sourceRank,
            levelStartRank: level.levelStartRank ?? level.startRank, levelEndRank: level.levelEndRank ?? level.endRank,
            startRank: level.startRank, rankBasis: level.rankBasis, probability: level.probability };
    }).filter(Boolean);
    return { profile, choices: choices.filter((choice, index) =>
        !index || choice.sourceRank !== choices[0].sourceRank || choice.startRank !== choices[0].startRank) };
}

function calculateGroupEstimate(bands, maxLevel) {
    const assumed = bands.reduce((sum, band) => sum + (band.assumedCount || 0), 0);
    const sampled = bands.filter(band => (band.sampleSize ?? band.size) > 0)
        .map(band => ({ ...band, size: band.sampleSize ?? band.size }));
    const counts = calculateEstimationResult(sampled, maxLevel - assumed);
    return Object.fromEntries(Object.entries(counts).map(([key, value]) => [key, value + assumed]));
}

function estimationChoiceLocation(choice) {
    const fraction = (choice.startRank - (choice.levelStartRank ?? choice.startRank))
        / Math.max(1, (choice.levelEndRank ?? choice.endRank ?? choice.startRank + 1) - (choice.levelStartRank ?? choice.startRank));
    const position = fraction >= 0.7 ? 'near the end of'
        : fraction >= 0.45 ? 'around halfway through'
        : fraction >= 0.2 ? 'about a quarter of the way through' : 'near the beginning of';
    return `${position} Level ${choice.levelNumber}`;
}

function showEstimationResult() {
    if (estimationState.recheck) return showPlacementRecheckResult();
    estimationState.active = false;
    estimationState.sequence = ++estimationSequence;
    const counts = calculateGroupEstimate(estimationState.bands, estimationState.maxLevel);
    estimationState.groupEstimate = counts;
    const baseline = estimationState.placementBaseline.length
        ? estimationState.placementBaseline : estimationState.placementWords;
    const levels = estimationState.placementLevels.length
        ? estimationState.placementLevels : getEstimationPlacementLevels(baseline);
    const placement = calculateRecognitionPlacement(estimationState.validWords, estimationState.bands, levels, baseline);
    estimationState.placementChoices = placement.choices;
    const first = placement.choices[0];
    estimationState.estimatedLevel = first?.sourceRank || 0;
    estimationState.estimatedLevelRank = Math.max(0, (first?.startRank || 1) - 1);
    if (estimationState.autoAdvanceTimer) {
        clearTimeout(estimationState.autoAdvanceTimer);
        estimationState.autoAdvanceTimer = null;
    }
    document.getElementById('estimationTest').style.display = 'none';
    document.getElementById('estimationResult').style.display = 'block';
    const levelEl = document.getElementById('estimationResultLevel');
    levelEl.textContent = placement.choices.length > 1 ? 'Choose where to begin'
        : (isSpeechMode() && first ? `Start ${estimationChoiceLocation(first)}` : 'Your starting point');
    const range = `${Math.round(counts.low).toLocaleString()}–${Math.round(counts.high).toLocaleString()}`;
    const shortCheck = estimationState.wordsTestedCount < ESTIMATION_QUESTION_LIMIT
        ? ` The check used ${estimationState.wordsTestedCount} groups.` : '';
    document.getElementById('estimationResultDesc').textContent =
        `Estimated vocabulary groups: about ${Math.round(counts.point).toLocaleString()} (range ${range}). The range reflects uncertainty from a short check.${shortCheck}`;
    const multiple = placement.choices.length > 1;
    document.getElementById('estimationPlacementOptions').innerHTML = placement.choices.map((choice, index) => {
        const percentage = Math.round(choice.probability * 100 / 5) * 5;
        const title = isSpeechMode() ? `Start ${estimationChoiceLocation(choice)}` : 'Use this starting point';
        const label = multiple ? (index === 0 ? 'Start earlier · More review' : 'Start further ahead · More new vocabulary') : 'Your suggested starting point';
        const detail = multiple ? (index === 0 ? 'More review, with fewer gaps left behind.' : 'More new vocabulary, with less review.') : 'A useful place to begin; you can change levels at any time.';
        return `<button type="button" class="estimation-placement-choice" onclick="useEstimatedLevel(${index})"><span class="estimation-choice-label">${label}</span><strong>${title}</strong><span>Around ${percentage}% of the vocabulary here is likely familiar. ${detail}</span></button>`;
    }).join('');
    document.getElementById('useEstimatedLevelBtn').hidden = placement.choices.length > 0;
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
async function useEstimatedLevel(choiceIndex = 0) {
    if (estimationState.ownerKey && estimationState.ownerKey !== placementStorageKey()) return closeEstimationModal();
    if (estimationState.profileKey && estimationState.profileKey !== placementProfileKey()) return closeEstimationModal();
    if (estimationState.recheck && !estimationState.placementChoices.length) return closeEstimationModal();
    const index = Number.isInteger(choiceIndex) ? choiceIndex : 0;
    const choice = estimationState.placementChoices[index];
    const level = choice?.sourceRank ?? estimationState.estimatedLevel;
    estimationState.estimatedLevel = level;
    if (choice) estimationState.estimatedLevelRank = Math.max(0, choice.startRank - 1);
    if (estimationState.recheck) finishPlacementRecheck();
    else if (choice) armPlacementChecker(choice);
    levelEstimates[selectedLanguage] = level;
    saveLevelEstimateToSheet(level);
    closeEstimationModal();
    // Rebuild completion annotations immediately, without altering real
    // progress. Answers to this check are never written as learned words.
    await window.renderLevelSelector?.(selectedLanguage, { preferActionable: true });
    if (isSpeechMode()) {
        const targetRank = choice?.startRank ?? ((estimationState.estimatedLevelRank || level) + 1);
        await selectLevelForRank(targetRank);
    }
}

function retryEstimation() {
    if (estimationState.recheck) return closeEstimationModal();
    estimationState = createEstimationState();
    document.getElementById('estimationResult').style.display = 'none';
    const fillEl = document.getElementById('estimationProgressFill');
    if (fillEl) fillEl.style.width = '0%';
    startEstimation();
}

// Placement opens the containing level; the saved rank preserves the finer start point.
async function selectLevelForRank(rank) {
    const target = levelButtonForRank(rank);
    if (!target) return false;
    target.button.click();
    await target.button._rangeRenderPromise;
    return true;
}

// Handle keyboard interaction when estimation modal is open
function handleEstimationKeydown(event) {
    const modal = document.getElementById('estimationModal');
    if (!modal || modal.classList.contains('hidden')) return;

    if (event.key === 'Escape') {
        event.preventDefault();
        closeEstimationModal();
        return;
    }

    const intro = document.getElementById('estimationIntro');
    const test = document.getElementById('estimationTest');
    const result = document.getElementById('estimationResult');

    if (intro && intro.style.display !== 'none') {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            startEstimation();
        }
        return;
    }

    if (test && test.style.display !== 'none' && estimationState.active && !estimationState.loading) {
        if (!estimationState.translationRevealed) {
            if (event.key === ' ' || event.key === 'Enter' || event.key === 'ArrowDown') {
                event.preventDefault();
                revealTranslation();
            }
        } else {
            if (event.key === 'ArrowRight' || event.key === 'Enter' || event.key === '2' || event.key === 'y' || event.key === 'Y') {
                event.preventDefault();
                handleAnswer(true);
            } else if (event.key === 'ArrowLeft' || event.key === '1' || event.key === 'x' || event.key === 'X' || event.key === 'n' || event.key === 'N') {
                event.preventDefault();
                handleAnswer(false);
            }
        }
        return;
    }

    if (result && result.style.display !== 'none') {
        if (event.key === 'Enter') {
            event.preventDefault();
            useEstimatedLevel();
        } else if (event.key === 'r' || event.key === 'R') {
            event.preventDefault();
            retryEstimation();
        }
    }
}

if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
    document.addEventListener('keydown', handleEstimationKeydown);
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

// Placement evidence is local to an account, language, release and profile.
// It never writes individual words into the learner's progress.
function placementStorageKey() {
    const account = currentUser && !currentUser.isGuest
        ? `account:${currentUser.initials || currentUser.id || currentUser.email}` : 'guest';
    return `fluency-placement-v1:${encodeURIComponent(account)}:${selectedLanguage}`;
}
function placementFastTrackProfile() {
    try {
        const account = currentUser && !currentUser.isGuest ? String(currentUser.initials) : 'guest';
        const value = JSON.parse(localStorage.getItem(`fluency_fast_track_v1|${account}|${selectedLanguage.toLowerCase()}`) || 'null');
        return value ? { enabled: value.enabled, skip: value.skip, bridge: value.bridge,
            excludedKnownLanguages: value.excludedKnownLanguages } : null;
    } catch (_) { return null; }
}
function placementProfileKey() {
    const cfg = getEstimationLangConfig() || {};
    return JSON.stringify({ release: cfg.indexPath || cfg.dataPath, pool: cfg.estimationPoolPath,
        frequency: cfg.frequencyPath, cognates: cfg.cognatesPath, bridge: cfg.bridgePath,
        languages: [...(window.activeKnownLanguages?.() || [])].sort(),
        thresholds: window.getCognateAlgorithmInfo?.().thresholds || {},
        threshold: globalThis.cognateThreshold, single: globalThis.hideSingleOccurrence,
        fastTrack: placementFastTrackProfile() });
}
function writePlacementSession(session) {
    try { localStorage.setItem(placementStorageKey(), JSON.stringify(session)); }
    catch (error) { console.warn('Could not retain placement check:', error); }
}
function readPlacementSession() {
    try {
        const session = JSON.parse(localStorage.getItem(placementStorageKey()) || 'null');
        if (!session || session.version !== 1 || session.profile !== placementProfileKey()
            || session.choice.sourceRank !== levelEstimates[selectedLanguage]) return null;
        return session;
    } catch (_) { return null; }
}
function currentPlacementChoices(bands = estimationState.bands) {
    const state = estimationState;
    return calculateRecognitionPlacement(state.validWords, bands, state.placementLevels,
        state.placementBaseline, state.recheck ? [state.recheck.choice.target] : [0.9, 0.8]).choices;
}
function placementSignature(bands) {
    return JSON.stringify(currentPlacementChoices(bands).map(c => [c.startRank, c.rankBasis]));
}
function placementIsStable() {
    const state = estimationState;
    if (state.wordsTestedCount < (state.recheck ? 8 : 20) || !state.placementLevels.length) return false;
    const signature = placementSignature();
    if (state.placementHistory.length < 5 || !state.placementHistory.slice(-5).every(s => s === signature)) return false;
    const fitted = getPosteriorBandProbabilities(state.bands);
    const targets = state.recheck ? [state.recheck.choice.target] : [0.9, 0.8];
    const indices = new Set(targets.map(target => {
        const index = fitted.findIndex(p => p < target);
        return index < 0 ? state.bands.length - 1 : index;
    }));
    for (const index of indices) {
        for (const known of [0, 1]) {
            const bands = state.bands.map(b => ({ ...b }));
            if (!bands[index] || !bands[index].sampleSize) return false;
            bands[index].answers++;
            bands[index].known += known;
            if (placementSignature(bands) !== signature) return false;
        }
    }
    return true;
}
function estimationQuestionLimit() { return estimationState.recheck ? 15 : ESTIMATION_QUESTION_LIMIT; }
function recheckWordEligible(word) {
    const choice = estimationState.recheck?.choice;
    if (!choice) return true;
    return word.estimationMembers.every(({ source }) =>
        (choice.rankBasis === 'stable' ? levelRankOf(source) : Number(source.rank)) < choice.startRank);
}
function armPlacementChecker(choice) {
    const state = estimationState;
    const members = [];
    for (const item of state.validWords) {
        if (item.estimationAssumedKnown) continue;
        for (const { source } of item.estimationMembers) {
            members.push({ rank: Number(source.rank), key: getWordKey(item),
                id: String(item.splitInfo ? item.id : source.id || ''), split: Boolean(item.splitInfo) });
        }
    }
    writePlacementSession({ version: 1, profile: placementProfileKey(), choice,
        answers: state.answers, members, evidence: [], status: 'armed', set: null });
}
function placementStudyContextAllowed(context) {
    return isSpeechMode() && !window.isSeriesStudy?.() && context?.studyMode === 'new'
        && !context.isFastTrack && !context.isDailyReview;
}
function placementSetIdentity(cards, context) {
    return JSON.stringify([context.rangeString, cards.map(c => c.fullId).sort()]);
}
function beginPlacementStudySet(cards, context) {
    const session = readPlacementSession();
    if (!session || !['armed', 'collecting'].includes(session.status) || !placementStudyContextAllowed(context)) return;
    const identity = placementSetIdentity(cards, context);
    if (session.status === 'collecting') {
        if (identity !== session.set) { session.status = 'done'; writePlacementSession(session); }
        else context.placementSet = identity;
        return;
    }
    const [start, end] = String(context.rangeString).split('-').map(Number);
    if (!(start <= session.choice.startRank && session.choice.startRank < end)
        || (context.rangeBasis || 'source') !== (session.choice.rankBasis || 'source')) {
        session.status = 'done'; writePlacementSession(session); return;
    }
    session.status = 'collecting'; session.set = identity;
    context.placementSet = identity;
    session.cards = {};
    for (const card of cards) {
        const matches = session.members.filter(m => m.rank === Number(card.rank));
        const member = matches.find(m => m.split ? String(card.fullId).endsWith(m.id) || String(card.id) === m.id : !card.splitInfo);
        if (!member || card.previewOnly || card.isChainChild || estimationAssumesKnown(card)
            || window.getWordProgressState?.(card.fullId, card.targetWord)?.seen
            || card.meanings?.some(m => m.isKnownSense)) continue;
        session.cards[card.fullId] = member.key;
    }
    writePlacementSession(session);
}
function observePlacementStudyCard(card, recognition) {
    if (recognition && !card?.previewOnly && !card?.isChainChild) return;
    recordPlacementStudyAnswer(card, false, { recognition: false, exposed: true });
}
function recordPlacementStudyAnswer(card, known, { recognition = false, exposed = false } = {}) {
    const session = readPlacementSession();
    if (!session || session.status !== 'collecting' || !isSpeechMode() || window.isSeriesStudy?.()) return;
    const key = session.cards?.[card?.fullId];
    if (!key || session.evidence.some(a => a.key === key) || session.answers.some(a => a.key === key)) return;
    // Consume the first encounter even when it cannot supply placement evidence.
    for (const id of Object.keys(session.cards)) if (session.cards[id] === key) delete session.cards[id];
    if (recognition && !exposed && !card.previewOnly && !card.isChainChild && !estimationAssumesKnown(card)
        && !window.getWordProgressState?.(card.fullId, card.targetWord)?.seen) {
        session.evidence.push({ key, known: Boolean(known) });
    }
    writePlacementSession(session);
}
function completePlacementStudySet(context) {
    const panel = document.getElementById('placementRecheckOffer');
    if (panel) panel.hidden = true;
    const session = readPlacementSession();
    if (!session || !placementStudyContextAllowed(context) || context.placementSet !== session.set) return;
    if (session.status === 'collecting') {
        const n = session.evidence.length;
        session.status = n >= 10 && session.evidence.filter(a => a.known).length / n <= 0.2 ? 'offered' : 'done';
        writePlacementSession(session);
    }
    if (panel) panel.hidden = session.status !== 'offered';
}
function finishPlacementRecheck() {
    const session = readPlacementSession();
    if (session) { session.status = 'done'; writePlacementSession(session); }
    const panel = document.getElementById('placementRecheckOffer');
    if (panel) panel.hidden = true;
}
async function startPlacementRecheck() {
    const session = readPlacementSession();
    if (!session || session.status !== 'offered') return;
    session.status = 'rechecking'; writePlacementSession(session);
    window.hideDeckCompleteModal?.();
    openEstimationModal();
    await startEstimation(session);
}
function seedPlacementRecheck(state, session) {
    if (session.profile !== placementProfileKey()) throw new Error('Placement profile changed');
    const answers = new Map([...session.answers, ...session.evidence].map(a => [a.key, a]));
    state.answers = [];
    state.validWords.forEach((word, index) => {
        const answer = answers.get(getWordKey(word));
        if (!answer || word.estimationAssumedKnown) return;
        const band = state.bands.find(b => index >= b.start && index < b.end);
        band.answers++; if (answer.known) band.known++;
        state.answers.push(answer); state.shownWordIds.add(answer.key);
    });
}
function showPlacementRecheckResult() {
    const state = estimationState;
    state.active = false;
    const choice = currentPlacementChoices()[0];
    const earlier = choice && choice.startRank < state.recheck.choice.startRank;
    const supported = earlier && placementIsStable();
    state.placementChoices = supported ? [choice] : [];
    document.getElementById('estimationTest').style.display = 'none';
    document.getElementById('estimationResult').style.display = 'block';
    document.getElementById('estimationResultLevel').textContent = supported
        ? `Try starting ${estimationChoiceLocation(choice)}` : 'Keep your current starting point';
    document.getElementById('estimationResultDesc').textContent = supported
        ? 'Your follow-up answers suggest more familiar vocabulary alongside new words. Your learning progress stays saved.'
        : 'This short check did not establish a clearer earlier starting point. Your current position is unchanged.';
    const options = document.getElementById('estimationPlacementOptions');
    options.innerHTML = supported ? `<button type="button" class="estimation-placement-choice" onclick="useEstimatedLevel(0)">Start ${estimationChoiceLocation(choice)}</button>` : '';
    document.getElementById('useEstimatedLevelBtn').hidden = true;
    const keep = document.getElementById('estimationKeepPosition');
    if (keep) keep.hidden = false;
    document.getElementById('retryEstimationBtn').hidden = true;
    finishPlacementRecheck();
}
Object.assign(window, { observePlacementStudyCard, beginPlacementStudySet, recordPlacementStudyAnswer, completePlacementStudySet,
    startPlacementRecheck, finishPlacementRecheck });

// Pure helpers are exported for lightweight regression checks without a DOM.
export {
    buildEstimationPool,
    finalizeEstimationPool,
    attachEstimationExample,
    deckRankForCount,
    buildCoverageOrder,
    buildEstimationBands,
    fitMonotonicProbabilities,
    calculateEstimationResult,
    calculateRecognitionPlacement,
    buildEstimationPlacementRegions,
    calculateGroupEstimate
};
