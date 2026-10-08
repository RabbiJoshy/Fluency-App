// Vocabulary loading, filtering, and ID generation.
// Key functions: buildFilteredVocab() (central filter), loadVocabularyData(), getWordId(),
// mergeArtistVocabularies() (multi-artist merge by hex ID).
import './state.js?v=20260825ak';
import { validateVocabularyIndex } from './data-contracts.js?v=20260825ak';
import { formatRoute } from './routes.js?v=20260923cj';
import { applyGrammarCardOverlay } from './grammar-cards.js?v=20260923gn';
import { releaseUrl } from './release-host.js?v=20260921rh';

const LAST_STUDY_SESSION_KEY = 'fluency_last_study_session_v1';
const WSD_PUBLICATION_PROJECTION_KEY = 'fluency_wsd_publication_projection_v1';
const speechSourceFrequencyCache = new Map();

async function loadSpeechSourceFrequency(langConfig) {
    const path = langConfig?.frequencyPath;
    const indexPath = langConfig?.indexPath;
    if (!path || !indexPath || activeArtist || window.playlistLiveActive?.()) return null;
    if (!speechSourceFrequencyCache.has(path)) {
        const pending = fetch(path).then(async response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            // config.js maps every release path onto the release site, so the
            // deck's indexPath is a full URL on the live app while this file
            // names the release as `releases/…`. Compare them on the same
            // footing, or every live card silently loses its frequency.
            if (data.schema !== 'speech-source-frequency/v1' || releaseUrl(data.indexPath) !== indexPath) {
                throw new Error('Source frequency file does not match this vocabulary release');
            }
            return data;
        }).catch(error => {
            speechSourceFrequencyCache.delete(path);
            console.warn('Source frequency unavailable:', error);
            return null;
        });
        speechSourceFrequencyCache.set(path, pending);
    }
    return speechSourceFrequencyCache.get(path);
}

function speechSourceFrequencyForSurface(surface, sourceData) {
    const key = String(surface || '').normalize('NFC').toLocaleLowerCase();
    const value = Number(sourceData?.values?.[key]);
    return Number.isFinite(value) && value > 0 ? value : null;
}

function speechSourceFrequencyOf(item, sourceData) {
    return speechSourceFrequencyForSurface(item?.word, sourceData);
}

function currentWsdPublicationProjection() {
    const requested = new URLSearchParams(window.location.search).get('wsdPublication');
    if (requested === 'forced_leaf' || requested === 'supported_specificity') {
        try { localStorage.setItem(WSD_PUBLICATION_PROJECTION_KEY, requested); } catch (_) {}
        return requested;
    }
    try {
        if (localStorage.getItem(WSD_PUBLICATION_PROJECTION_KEY) === 'supported_specificity') {
            return 'supported_specificity';
        }
    } catch (_) {}
    return 'forced_leaf';
}

window.getWsdPublicationProjection = currentWsdPublicationProjection;
window.selectWsdPublicationView = (projection, sourceButton = null) => {
    if (projection !== 'forced_leaf' && projection !== 'supported_specificity') {
        throw new Error('Unsupported WSD publication projection');
    }
    document.querySelectorAll('.wsd-publication-btn').forEach(button => {
        const selected = button === sourceButton || button.dataset.wsdPublication === projection;
        button.classList.toggle('selected', selected);
        button.setAttribute('aria-pressed', selected ? 'true' : 'false');
    });
    localStorage.setItem(WSD_PUBLICATION_PROJECTION_KEY, projection);
    const target = new URL(window.location.href);
    target.searchParams.set('wsdPublication', projection);
    window.location.assign(target.toString());
};
window.setWsdPublicationProjection = window.selectWsdPublicationView;

function projectedSenseFrequency(indexRow, sense, fallbackFrequency) {
    const distribution = indexRow?.wsd_distribution;
    if (!distribution || currentWsdPublicationProjection() === 'forced_leaf') {
        return Number(fallbackFrequency) || 0;
    }
    const denominator = Number(distribution.denominator) || 0;
    const counts = distribution.supported_leaf_counts;
    const senseId = sense?.id || sense?.sense_id;
    if (!denominator || !counts || !senseId) return 0;
    return (Number(counts[senseId]) || 0) / denominator;
}

function readStudySession(key) {
    try {
        const parsed = JSON.parse(localStorage.getItem(key) || 'null');
        return parsed && parsed.range && Array.isArray(parsed.order) ? parsed : null;
    } catch (error) {
        return null;
    }
}

// Scope key for a saved session. Same inputs as getProgressScopeKey so a
// snapshot and the progress rows it will resume against agree on what
// "this deck" means.
function studySessionScope({ mode, artistSlug, artistSlugs, language }) {
    return window.getProgressScopeKey?.({ mode, artistSlug, artistSlugs, language })
        || `${mode || 'speech'}:${artistSlug || language || ''}`;
}

// The deck the learner has explicitly opened, or null on a bare landing.
// Only an artist counts as explicit: arriving with no parameters is the
// landing, where offering whatever was studied last is the desired behaviour.
// A restored `selectedLanguage` is not an explicit choice and must not scope
// the prompt, or landing would stop offering a saved Lyrics set.
function activeStudySessionScope() {
    if (!activeArtist) return null;
    return studySessionScope({
        mode: 'lyrics',
        artistSlug: window._urlArtistSlug || null,
        artistSlugs: (window._selectedArtistSlugs || []).slice(),
        songIds: activeArtist ? selectedSongIds.slice() : [],
        language: activeArtist.language || selectedLanguage
    });
}

function currentLyricsReleaseId() {
    if (!activeArtist) return '';
    return String(activeArtist.releaseId || '').trim();
}

// A saved Lyrics position belongs to the immutable release that produced its
// card IDs and examples. Preview URLs are deliberately strict: a legacy
// snapshot with no release identity must never bleed into a release being
// audited. The active production release still accepts old unversioned
// snapshots once, preserving backwards compatibility for existing learners.
function studySessionMatchesCurrentRelease(snapshot) {
    if (!snapshot || snapshot.mode !== 'lyrics' || !activeArtist) return true;
    const currentReleaseId = currentLyricsReleaseId();
    if (!currentReleaseId) return true;
    if (snapshot.releaseId) return snapshot.releaseId === currentReleaseId;
    return !new URLSearchParams(window.location.search).has('lyricsRelease');
}

// Resume resolution. Inside a deck, only that deck's own saved session is
// offered — previously the single global snapshot could send a learner who had
// just opened Bad Bunny into a Speech set, redirecting the URL to get there.
function getLastStudySession() {
    const scope = activeStudySessionScope();
    if (!scope) return readStudySession(LAST_STUDY_SESSION_KEY);
    const scoped = readStudySession(`${LAST_STUDY_SESSION_KEY}:${scope}`);
    if (scoped && studySessionMatchesCurrentRelease(scoped)) return scoped;
    // Pre-migration sessions only exist under the global key; use one only
    // when it already belongs to the deck in front of the learner.
    const latest = readStudySession(LAST_STUDY_SESSION_KEY);
    return latest
        && studySessionScope(latest) === scope
        && studySessionMatchesCurrentRelease(latest)
        ? latest
        : null;
}

function renderResumeLastSetCard() {
    if (window.fluencyRoute?.kind === 'tutorial'
        || document.querySelector('#tutorialIntroModal:not(.hidden), #cardTutorialModal:not(.hidden)')) {
        document.getElementById('resumeLastSetCard')?.remove();
        return;
    }
    if (window.playlistLiveActive?.()) {
        document.getElementById('resumeLastSetCard')?.remove();
        return;
    }
    const snapshot = getLastStudySession();
    let card = document.getElementById('resumeLastSetCard');
    if (!snapshot) {
        if (card) card.remove();
        return;
    }
    // Resume is an entry decision, not a permanent setup-page advert. The
    // explicit ?resume=1 hop is already committed to resuming and skips this.
    const explicitResume = new URLSearchParams(window.location.search).get('resume') === '1';
    if (explicitResume) return;
    try {
        if (sessionStorage.getItem('fluency_resume_prompt_seen_v1') === snapshot.savedAt) return;
    } catch (_) {}
    if (card) card.remove();
    card = document.createElement('section');
    card.id = 'resumeLastSetCard';
    card.className = 'modal resume-entry-modal';
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    card.setAttribute('aria-labelledby', 'resumeEntryTitle');
    const source = snapshot.mode === 'lyrics' ? 'Lyrics' : 'Speech';
    const level = snapshot.levelNumber ? `Level ${snapshot.levelNumber}` : 'Saved level';
    const set = snapshot.setNumber ? `Set ${snapshot.setNumber}` : 'Saved set';
    const track = snapshot.studyMode === 'review' ? 'Practice' : 'Learn new';
    const forms = snapshot.useLemmaMode ? 'Merged lemmas' : 'Forms';
    const cognates = snapshot.excludeCognates ? 'Cognates excluded' : 'Cognates included';
    const title = snapshot.mode === 'lyrics'
        ? `${snapshot.artistName || 'Lyrics'}${snapshot.artistVocabularyScope === 'extra' ? ' Extra' : ''}`
        : `${snapshot.languageName || snapshot.language} speech`;
    card.innerHTML = `
        <div class="modal-content resume-entry-content">
            <span class="resume-set-eyebrow">Welcome back</span>
            <h3 id="resumeEntryTitle">Continue where you stopped?</h3>
            <strong>${title}</strong>
            <p>${source} · ${level} · ${set} · ${track}</p>
            <small>${forms} · ${cognates} · last card: ${snapshot.currentWord || 'saved card'}</small>
            <div class="resume-entry-actions">
                <button type="button" class="resume-entry-secondary" id="dismissResumeLastSetBtn">Choose a new set</button>
                <button type="button" class="resume-entry-primary" id="resumeLastSetBtn">Continue set</button>
            </div>
        </div>`;
    document.body.appendChild(card);
    const markSeenAndClose = () => {
        try { sessionStorage.setItem('fluency_resume_prompt_seen_v1', snapshot.savedAt); } catch (_) {}
        card.remove();
    };
    document.getElementById('resumeLastSetBtn')?.addEventListener('click', () => {
        markSeenAndClose();
        resumeLastStudySession();
    });
    document.getElementById('dismissResumeLastSetBtn')?.addEventListener('click', markSeenAndClose);
    card.addEventListener('click', event => {
        if (event.target === card) markSeenAndClose();
    });
}

function clearStudySessionSnapshot() {
    // Both copies have to go. Dropping only the global key would leave the
    // scoped one behind, and a finished set would keep being offered every
    // time the learner reopened that deck.
    try {
        const previous = readStudySession(LAST_STUDY_SESSION_KEY);
        localStorage.removeItem(LAST_STUDY_SESSION_KEY);
        if (previous) localStorage.removeItem(`${LAST_STUDY_SESSION_KEY}:${studySessionScope(previous)}`);
        const scope = activeStudySessionScope();
        if (scope) localStorage.removeItem(`${LAST_STUDY_SESSION_KEY}:${scope}`);
    } catch (_) {}
    document.getElementById('resumeLastSetCard')?.remove();
}

let _saveSnapshotTimer = null;

function saveStudySessionSnapshot({ immediate = false } = {}) {
    if (!flashcards.length || cardNavStack.length > 0 || !stats.rangeString) return;
    const appContent = document.getElementById('appContent');
    if (!appContent || appContent.classList.contains('hidden')) return;

    if (_saveSnapshotTimer) {
        clearTimeout(_saveSnapshotTimer);
        _saveSnapshotTimer = null;
    }

    if (immediate) {
        _writeStudySessionSnapshot();
    } else {
        _saveSnapshotTimer = setTimeout(_writeStudySessionSnapshot, 250);
    }
}

function _writeStudySessionSnapshot() {
    _saveSnapshotTimer = null;
    if (!flashcards.length || cardNavStack.length > 0 || !stats.rangeString) return;
    const appContent = document.getElementById('appContent');
    if (!appContent || appContent.classList.contains('hidden')) return;
    const card = flashcards[currentIndex];
    if (!card) return;
    const levelButtons = Array.from(document.querySelectorAll('.level-selector-buttons .level-btn, #levelSelector > .level-btn'));
    const levelNumber = Math.max(0, levelButtons.findIndex(btn => btn.dataset.level === selectedLevel)) + 1;
    const languageName = config?.languages?.[selectedLanguage]?.name?.replace(/\s*\(.*\)$/, '') || selectedLanguage;
    const snapshot = {
        savedAt: new Date().toISOString(),
        mode: activeArtist ? 'lyrics' : 'speech',
        releaseId: activeArtist ? currentLyricsReleaseId() || null : null,
        artistSlug: window._urlArtistSlug || null,
        artistSlugs: (window._selectedArtistSlugs || []).slice(),
        songIds: activeArtist ? selectedSongIds.slice() : [],
        artistName: activeArtist?.name || null,
        artistVocabularyScope: activeArtist ? artistVocabularyScope : null,
        language: selectedLanguage,
        languageName,
        selectedLevel,
        levelNumber,
        range: stats.rangeString,
        rangeBasis: stats.rangeBasis || 'display',
        setNumber: stats.setNumber || null,
        levelSetCount: stats.levelSetCount || null,
        studyMode: stats.studyMode || 'new',
        groupSize,
        useLemmaMode,
        excludeCognates,
        hideSingleOccurrence,
        excludeProperNouns,
        excludeNoise,
        excludeSlang,
        excludeGrammarParticles,
        excludeEnglishLoanwords,
        directionFlipped: isFlipped,
        speechEnabled,
        cardFaceFlipped: document.getElementById('flashcard')?.classList.contains('flipped') || false,
        currentFullId: card.fullId,
        currentVocabularyRank: card.vocabularyRank || card.rank || null,
        currentWord: card.targetWord,
        currentMeaningIndex,
        currentExampleIndex,
        currentMWEIndex,
        setSize: stats.setSize,
        previouslyKnown: stats.previouslyKnown,
        order: flashcards.map(item => item.fullId)
    };
    try {
        const serialized = JSON.stringify(snapshot);
        // Global key = "most recent anywhere", which is what the landing
        // offers. The scoped copy is what a deck resumes from, so switching
        // between Bad Bunny and Speech no longer overwrites the other's
        // place in its set.
        localStorage.setItem(LAST_STUDY_SESSION_KEY, serialized);
        localStorage.setItem(`${LAST_STUDY_SESSION_KEY}:${studySessionScope(snapshot)}`, serialized);
    } catch (error) {
        // Storage can be unavailable in hardened/private contexts.
    }
}

if (typeof window !== 'undefined') {
    window.addEventListener('pagehide', () => saveStudySessionSnapshot({ immediate: true }));
}

async function resumeLastStudySession() {
    const snapshot = getLastStudySession();
    if (!snapshot) {
        window.hideAppLoading?.();
        return;
    }
    window.showAppLoading?.('Continuing Your Set', 'Returning to the card where you stopped…', true);
    try { sessionStorage.setItem('fluency_resume_prompt_seen_v1', snapshot.savedAt); } catch (_) {}
    document.getElementById('resumeLastSetCard')?.remove();
    const currentMode = activeArtist ? 'lyrics' : 'speech';
    const currentArtist = window._urlArtistSlug || null;
    if (snapshot.mode !== currentMode || (snapshot.mode === 'lyrics' && snapshot.artistSlug !== currentArtist)) {
        const url = new URL(window.location.href);
        url.search = '';
        url.hash = '';
        if (snapshot.mode === 'lyrics' && snapshot.artistSlug) {
            url.hash = formatRoute({
                kind: 'artist',
                artist: snapshot.artistSlug,
                scope: snapshot.artistVocabularyScope === 'extra' ? 'extra' : 'main'
            });
            if (snapshot.releaseId) url.searchParams.set('lyricsRelease', snapshot.releaseId);
        }
        url.searchParams.set('resume', '1');
        window.location.href = url.toString();
        return;
    }

    const requestedExtra = snapshot.mode === 'lyrics' && snapshot.artistVocabularyScope === 'extra';
    if (requestedExtra && !window.isArtistExtraUnlocked?.(snapshot.artistSlug)) {
        clearStudySessionSnapshot();
        artistVocabularyScope = 'main';
        window.renderArtistSourceSummary?.();
        window.hideAppLoading?.();
        alert('Artist Extra unlocks after you understand 60% of this artist\'s main lyrics vocabulary.');
        return;
    }

    selectedLanguage = snapshot.language;
    window.applyLanguageColorTheme?.();
    selectedLevel = snapshot.selectedLevel;
    groupSize = snapshot.groupSize || 20;
    useLemmaMode = !!snapshot.useLemmaMode;
    excludeCognates = !!snapshot.excludeCognates;
    hideSingleOccurrence = snapshot.hideSingleOccurrence !== false;
    artistVocabularyScope = requestedExtra ? 'extra' : 'main';
    excludeProperNouns = snapshot.excludeProperNouns !== false;
    excludeNoise = snapshot.excludeNoise !== false;
    if (typeof snapshot.excludeSlang === 'boolean') excludeSlang = snapshot.excludeSlang;
    if (typeof snapshot.excludeGrammarParticles === 'boolean') excludeGrammarParticles = snapshot.excludeGrammarParticles;
    excludeEnglishLoanwords = snapshot.excludeEnglishLoanwords !== false;
    isFlipped = !!snapshot.directionFlipped;
    if (typeof snapshot.speechEnabled === 'boolean') speechEnabled = snapshot.speechEnabled;
    window.renderArtistSourceSummary?.();
    if (snapshot.mode === 'lyrics' && snapshot.artistSlugs?.length) {
        const oldKey = (window._selectedArtistSlugs || []).slice().sort().join(',');
        const newKey = snapshot.artistSlugs.slice().sort().join(',');
        if (oldKey !== newKey) {
            window._cachedMergedIndex = null;
            window._cachedMergedExamples = null;
            window._cachedExamplesData = null;
        }
        window._selectedArtistSlugs = snapshot.artistSlugs.slice();
        localStorage.setItem('selected_artists', JSON.stringify(snapshot.artistSlugs));
    }
    if (snapshot.mode === 'lyrics' && Array.isArray(snapshot.songIds) && artistSongCatalog) {
        const available = new Set(artistSongCatalog.songs.map(song => String(song.id)));
        const restored = snapshot.songIds.map(String).filter(id => available.has(id));
        if (restored.length) {
            selectedSongIds = restored;
            const cachedExamples = window._cachedExamplesDataRaw || window._cachedExamplesData;
            // Examples are deliberately lazy. A setup-page resume can restore
            // the selected songs before that optional payload has ever been
            // fetched; let loadVocabularyData fetch and filter it below.
            if (cachedExamples) {
                window.setActiveExamplesData?.(
                    cachedExamples,
                    activeArtist?.examplesPath || null,
                );
            }
        }
    }
    window.renderArtistSourceSummary?.();
    document.querySelectorAll('.lemma-toggle-btn').forEach(button =>
        button.classList.toggle('selected', (button.dataset.lemma === 'on') === useLemmaMode));
    document.querySelectorAll('.cognate-toggle-btn').forEach(button =>
        button.classList.toggle('selected', (button.dataset.cognate === 'exclude') === excludeCognates));
    const url = new URL(window.location.href);
    url.searchParams.delete('resume');
    if (snapshot.mode === 'lyrics' && snapshot.artistSlug && snapshot.artistSlug !== 'custom') {
        url.hash = formatRoute({
            kind: 'artist',
            artist: snapshot.artistSlug,
            scope: artistVocabularyScope === 'extra' ? 'extra' : 'main'
        });
    }
    history.replaceState(null, '', url);
    try {
        await loadVocabularyData(snapshot.range, {
            resumeSnapshot: snapshot,
            rankBasis: snapshot.rangeBasis || 'display',
            setNumber: snapshot.setNumber || null,
            levelSetCount: snapshot.levelSetCount || null
        });
    } finally {
        window.hideAppLoading?.();
    }
}

// ISO 639-1 codes for each language key used in config.json
const LANG_CODES = {
    spanish: 'es', swedish: 'sv', italian: 'it',
    dutch: 'nl', finnish: 'fi', polish: 'pl', french: 'fr', russian: 'ru'
};

/**
 * Compute a stable composite word ID: {2-char lang}{0=normal|1=lyrics}{surface ID}.
 * Current Spanish surface IDs are eight lowercase hex characters; the rank
 * fallback remains only for older language data that has no explicit ID.
 * Examples: "es0a1b2c3d4" (Spanish Speech), "es1a1b2c3d4" (Spanish Lyrics).
 * Always contains letters → Google Sheets never auto-converts to a number.
 */
function getWordId(item) {
    const lang = LANG_CODES[selectedLanguage] || selectedLanguage.slice(0, 2);
    const mode = activeArtist ? '1' : '0';
    const hex = item.id || Number(item.rank).toString(16).padStart(4, '0');
    const fullId = `${lang}${mode}${hex}`;
    window.registerProgressCardSurface?.(fullId, item.word);
    return fullId;
}

/**
 * Flip the mode bit in a fullId: es0... ↔ es1...
 * Returns null if the ID is too short or has no mode bit.
 */
function getCrossModeId(fullId) {
    if (!fullId || fullId.length < 4) return null;
    const modeChar = fullId[2];
    if (modeChar === '0') return fullId.slice(0, 2) + '1' + fullId.slice(3);
    if (modeChar === '1') return fullId.slice(0, 2) + '0' + fullId.slice(3);
    return null;
}

/**
 * Check if a word is currently resolved in either mode. Historical wrong
 * counts remain available, but a newer wrong moves the card back to review.
 */
function isWordKnown(fullId) {
    return getWordProgressState(fullId).learned;
}

/**
 * Build a Set of hex IDs for words covered by the level estimate.
 * Uses the normal-mode vocabulary index (general frequency ordering).
 * Cached per language + estimate so it's only computed once per session.
 */
async function buildEstimatedKnownIds(estimate) {
    if (!estimate || estimate <= 0) return new Set();

    const cacheKey = `${selectedLanguage}_${estimate}`;
    if (window._estimatedKnownIdsCache?.key === cacheKey) {
        return window._estimatedKnownIdsCache.ids;
    }

    const normalConfig = window._normalModeLangConfigs?.[selectedLanguage];
    if (!normalConfig) return new Set();

    // The estimate is a Speech source rank. Speech and Lyrics cards carry
    // different id schemes, so the set holds each word's surface as well: the
    // observed surface is the bridge between modes (see progress-identity.js).
    const normalVocab = await fetchAndJoinIndex(normalConfig, { ignoreArtist: true });
    const ids = new Set();
    normalVocab.forEach((item, index) => {
        const rank = Number(item.rank) || index + 1;
        if (rank > estimate) return;
        if (item.id) ids.add(item.id);
        const surface = window.normalizeProgressSurface?.(item.word);
        if (surface) ids.add(`surface:${surface}`);
    });

    window._estimatedKnownIdsCache = { key: cacheKey, ids };
    return ids;
}

// Whether a card is covered by the Speech-rank estimate in an artist deck.
function isCoveredByEstimatedIds(item, estimatedIds) {
    if (!item || !estimatedIds?.size) return false;
    if (item.id && estimatedIds.has(item.id)) return true;
    const surface = window.normalizeProgressSurface?.(item.word);
    return Boolean(surface && estimatedIds.has(`surface:${surface}`));
}

async function buildSeenLemmaSet(vocabData) {
    const hasLemmas = lemmaFieldAvailable || (Array.isArray(vocabData) && vocabData.some(item => lemmaGroupKey(item)));
    if (!useLemmaMode || !hasLemmas || !progressData) return new Set();
    if (!lemmaFieldAvailable && hasLemmas) lemmaFieldAvailable = true;

    const lemmaById = new Map();
    const lemmaBySurface = new Map();
    const addEntries = entries => {
        for (const entry of entries || []) {
            const lemma = lemmaGroupKey(entry);
            if (!lemma) continue;
            if (entry.id) lemmaById.set(entry.id, lemma);
            const surface = window.normalizeProgressSurface?.(entry.word);
            if (surface) lemmaBySurface.set(surface, lemma);
        }
    };
    addEntries(vocabData);
    addEntries(Object.entries(window._cachedMasterVocab || {}).map(([id, entry]) => ({
        ...entry, id
    })));

    // The current artist master covers artist decks. Add the normal index so
    // normal-only surface forms also contribute to a merged lemma's history.
    if (activeArtist) {
        const normalConfig = window._normalModeLangConfigs?.[selectedLanguage];
        if (normalConfig) addEntries(await fetchAndJoinIndex(normalConfig));
    }

    const seenLemmas = new Set();
    const mark = (fullId, state, word = '') => {
        if (!state?.seen || !fullId) return;
        const lemma = lemmaById.get(fullId.slice(3))
            || lemmaBySurface.get(window.normalizeProgressSurface?.(word));
        if (lemma) seenLemmas.add(lemma);
    };
    for (const [fullId, progress] of Object.entries(progressData)) {
        if (progress?.language === selectedLanguage) {
            mark(fullId, getProgressState(progress), progress.word);
        }
    }
    for (const progress of Object.values(itemProgressData || {})) {
        if (progress?.language === selectedLanguage) {
            mark(progress.parentWordId, getProgressState(progress));
        }
    }
    return seenLemmas;
}

function relatedWordIds(fullId, word = '') {
    const matchedIds = window.getProgressRecordIdsForCard?.(fullId, word) || [];
    const crossId = getCrossModeId(fullId);
    return Array.from(new Set([fullId, crossId, ...matchedIds].filter(Boolean)));
}

function hasRelatedWordProgress(fullId, word = '') {
    return relatedWordIds(fullId, word).some(id =>
        getWordProgressState(id, word).seen || wordHasKnowledgeProgress(id, word));
}

function relatedWordNeedsReview(fullId, word = '') {
    return relatedWordIds(fullId, word).some(id => wordNeedsKnowledgeReview(id, word));
}

/**
 * Join per-artist index entries with the shared master vocabulary.
 * Reconstructs the full entry shape (word, lemma, meanings, flags, mwe_memberships)
 * expected by buildFilteredVocab() and the flashcard builder.
 *
 * @param {Array} indexData - Artist index entries [{id, corpus_count, most_frequent_lemma_instance, sense_frequencies}]
 * @param {Object} master - Master vocabulary {id: {word, lemma, senses, flags, mwe_memberships}}
 * @returns {Array} Denormalized entries matching the old monolith format
 */
function joinWithMaster(indexData, master) {
    const result = [];
    for (const idx of indexData) {
        const m = master[idx.id];
        if (!m) continue;

        // Keep the complete shared sense menu on the joined entry. Main cards
        // still prefer/drop to positive artist frequencies before rendering,
        // while one-off forms can reuse these dictionary senses and the
        // standard Speech evidence packaged in the examples split. This is
        // what makes Artist Extra useful without another Gemini pass.
        const methods = idx.sense_methods || [];
        const promptIds = idx.sense_prompt_ids || [];
        const runTimes = idx.sense_run_ts || [];
        const confidences = idx.sense_confidence || [];
        const bands = idx.sense_band || [];
        const modelProposed = idx.sense_model_proposed || [];
        const freqs = idx.sense_frequencies || [];
        const publicationProjection = currentWsdPublicationProjection();
        const meanings = [];
        (m.senses || []).forEach((sense, i) => {
            const freq = Number(freqs[i]) || 0;
            const displayFrequency = projectedSenseFrequency(idx, sense, freq);
            const method = freq > 0 ? methods[i] : null;
            const isAutomatic = isAutomaticSenseMethod(method);
            const meaning = {
                pos: sense.pos,
                translation: sense.translation,
                frequency: String(freq),
                display_frequency: String(displayFrequency),
                examples: []  // Attached later from examples file
            };
            // Provenance (which prompt/model produced this sense) for the
            // card's info panel — resolved against window._promptRegistry.
            if (freq > 0 && promptIds[i] && !isAutomatic) {
                meaning.prompt_id = promptIds[i];
                if (runTimes[i]) meaning.run_ts = runTimes[i];
            }
            // Model confidence for the provenance panel, aligned per sense.
            if (freq > 0 && confidences[i] != null) {
                meaning.confidence = confidences[i];
                if (bands[i]) meaning.band = bands[i];
            }
            if (freq > 0 && modelProposed[i]) meaning.model_proposed = true;
            if (sense.id || sense.sense_id) meaning.sense_id = sense.id || sense.sense_id;
            if (sense.sense_id_aliases?.length) meaning.sense_id_aliases = sense.sense_id_aliases;
            if (freq <= 0) {
                meaning.shared_fallback = true;
                meaning.unassigned = true;
            }
            if (sense.source) meaning.source = sense.source;
            if (sense.headword) meaning.headword = sense.headword;
            if (sense.source_reference) meaning.source_reference = sense.source_reference;
            if (sense.context) meaning.context = sense.context;
            if (sense.metadata) meaning.metadata = sense.metadata;
            if (Array.isArray(sense.regions) && sense.regions.length) {
                meaning.regions = [...sense.regions];
            }
            // Register/dialect tag stamped by the classify-or-propose prompt
            // (slang | regional | figurative | vulgar | loanword | proper_noun).
            // Copy-through matters: meanings are rebuilt from scratch here and
            // again in buildFilteredVocab(), so anything not carried explicitly
            // is silently dropped before it reaches the card.
            if (sense.type) meaning.type = sense.type;
            if (method) {
                meaning.assignment_method = method;
            } else if (freq > 0 && idx.unassigned) {
                meaning.unassigned = true;
            }
            meaning._masterSenseIndex = i;
            meanings.push(meaning);
        });

        // Build mwe_memberships from index entry (per-artist, not master)
        const mwe_memberships = (idx.mwe_memberships || []).map(mwe => ({
            id: mwe.id || null,
            expression: mwe.expression,
            translation: mwe.translation || '',
            family: mwe.family || '',
            variants: mwe.variants || null,
            variant_counts: mwe.variant_counts || null,
            count: Number(mwe.count) || 0,
            occurrence_count: Number(mwe.occurrence_count) || 0,
            num_songs: Number(mwe.num_songs) || 0,
            source: mwe.source || '',
            context: mwe.context || '',
            context_heuristic: mwe.context_heuristic || '',
            examples: []
        }));

        // Build clitic_memberships from index entry
        const clitic_memberships = (idx.clitic_memberships || []).map(cl => ({
            form: cl.form,
            translation: cl.translation || '',
            corpus_count: cl.corpus_count || 0,
            examples: []
        }));

        // Build sense_cycles from index entry (unassigned/cycling senses)
        const sense_cycles = (idx.sense_cycles || []).map(sc => ({
            pos: sc.pos,
            translation: sc.translation || '',
            cycle_pos: sc.cycle_pos || sc.pos,
            allSenses: sc.allSenses || [],
            unassigned: true,
            examples: []
        }));

        result.push({
            id: idx.id,
            word: m.word,
            lemma: m.lemma,
            meanings,
            _base_meanings: meanings.map(meaning => ({ ...meaning, examples: [] })),
            most_frequent_lemma_instance: idx.most_frequent_lemma_instance,
            is_english: m.is_english || false,
            // is_noise is the schema_v2 flag name; is_interjection is the
            // legacy alias kept for vocabularies built before the rename.
            // Carry both forward so downstream filters can read either.
            is_noise: m.is_noise || m.is_interjection || false,
            is_interjection: m.is_noise || m.is_interjection || false,
            is_propernoun: m.is_propernoun || false,
            // Corpus-derived proper-noun signal from cap-rate
            // (tool_8a_stamp_propernoun_corpus.py). Independent of the
            // pipeline-stamped `is_propernoun` flag — both can be true,
            // either alone is sufficient for filtering.
            is_propernoun_corpus: m.is_propernoun_corpus || false,
            propernoun_cap_rate: m.propernoun_cap_rate ?? null,
            // English loanword flag (tool_8a_stamp_loanword_flag.py --master),
            // from the Wiktionary-etymology layer. Toggleable filter.
            is_english_loanword: m.is_english_loanword || false,
            // Pipeline-assigned Extra grouping key (core / single_occurrence /
            // english / loanword / proper_noun / cognate / noise / …). Drives
            // the Artist Extra category selector; absent → "All Extra" fallback.
            extra_category: idx.extra_category || m.extra_category || null,
            cognate_score: idx.cognate_score ?? m.cognate_score ?? (m.is_transparent_cognate ? 1 : 0),
            cognet_cognate: idx.cognet_cognate || m.cognet_cognate || false,
            corpus_count: idx.corpus_count || 0,
            lemma_example_count: idx.lemma_example_count ?? idx.corpus_count ?? 0,
            display_form: m.display_form || null,
            variants: idx.variants || null,
            mwe_memberships: mwe_memberships.length > 0 ? mwe_memberships : undefined,
            clitic_memberships: clitic_memberships.length > 0 ? clitic_memberships : undefined,
            sense_cycles: sense_cycles.length > 0 ? sense_cycles : undefined,
            morphology: idx.morphology || null,
            wsd_distribution: idx.wsd_distribution || null,
            wsd_publication_projection: publicationProjection,
            wsd_supported_specificity_available: Object.values(
                idx.wsd_distribution?.supported_level_counts || {}
            ).some(value => Number(value) > 0),
            synonyms: idx.synonyms || null,
            antonyms: idx.antonyms || null,
            related_lemma: idx.related_lemma || m.related_lemma || null,
            derivation_relation: idx.derivation_relation || m.derivation_relation || null,
        });
    }
    return result;
}

function isAutomaticSenseMethod(method) {
    return typeof method === 'string' && method.endsWith('-auto');
}

function reconcileMeaningProvenanceFromExamples(meaning, examples) {
    const methods = [...new Set((examples || [])
        .map(example => example?.assignment_method)
        .filter(Boolean))];
    if (methods.length !== 1 || !isAutomaticSenseMethod(methods[0])) return;
    meaning.assignment_method = methods[0];
    delete meaning.prompt_id;
    delete meaning.run_ts;
    delete meaning.model_proposed;
}

/**
 * Lemma mode: pool the dropped sibling forms' examples onto the surviving card.
 * One-card-per-lemma keeps only the most frequent form (quiero) and drops the
 * rest (quieres, quiere, …) — but their lyric/example lines still belong on the
 * surviving card. Appends each sibling's examples to the host meaning with the
 * same translation (falling back to the first meaning), deduped by sentence so
 * repeated deck loads can't double-append.
 *
 * Sibling examples come from the split examples file (`examplesData[id].m`,
 * bucketed in master sense order) when available, else from inline
 * `meanings[].examples` (multi-artist merged entries).
 */
function exampleSentenceKey(example) {
    return (example?.target || example?.spanish || example?.sentence || '').trim().toLowerCase();
}

function examplesForMeaning(item, meaning, meaningIndex, examplesData) {
    if (meaning.examples && meaning.examples.length > 0) return meaning.examples;
    const split = examplesData && item.id ? examplesData[item.id] : null;
    const bucket = meaning._masterSenseIndex ?? meaningIndex;
    return (split && split.m && split.m[bucket]) || [];
}

function mergeArtistExtraSupport(item, splitExamples) {
    if (!activeArtist || !splitExamples) return;
    const normalize = value => String(value || '').trim().toLowerCase();
    const dedupeInto = (target, additions) => {
        target.examples = target.examples || [];
        const seen = new Set(target.examples.map(exampleSentenceKey));
        for (const raw of additions || []) {
            const key = exampleSentenceKey(raw);
            if (!key || seen.has(key)) continue;
            seen.add(key);
            target.examples.push({ ...raw });
        }
    };

    // `p` is a compact, sense-labelled subset of the already-built Speech
    // examples. It is independent of artist master-sense array positions.
    for (const shared of splitExamples.p || []) {
        let target = (item.meanings || []).find(meaning =>
            normalize(meaning.pos) === normalize(shared.pos)
            && normalize(meaning.translation) === normalize(shared.translation)
            && normalize(meaning.context) === normalize(shared.context));
        if (!target) {
            target = {
                pos: shared.pos || 'X',
                translation: shared.translation || '',
                context: shared.context || '',
                frequency: '0',
                examples: [],
                shared_fallback: true,
                unassigned: true,
            };
            item.meanings = item.meanings || [];
            item.meanings.push(target);
        }
        dedupeInto(target, shared.examples || []);
        target.has_speech_fallback = true;
    }

    // The artist lyric is deliberately not stamped as assigned to a shared
    // sense. Put it on the first usable row so it is visible immediately; the
    // example-level match treatment remains absent, honestly signalling that
    // no classifier linked this lyric to that particular meaning.
    const lyricExamples = splitExamples.r || [];
    if (lyricExamples.length > 0) {
        const target = (item.meanings || []).find(meaning => meaning.examples?.length)
            || (item.meanings || [])[0];
        if (target) {
            const existing = target.examples || [];
            target.examples = [];
            dedupeInto(target, [...lyricExamples, ...existing]);
        } else {
            item.extra_raw_examples = lyricExamples.map(example => ({ ...example }));
        }
    }
}

// lemma-merge-pure
// A lemma is the headword. Part of speech is not part of it. A spelling joins
// that lemma only when every non-expression sense names that one headword.
// Casó joins casar. Casado does not: it also names casado, so it stays its own
// card, and a yes there does not clear casó.
//
// Two more things keep a spelling on its own card, both read from the data:
//   - it is a contraction (SpanishDict's CONTRACTION part of speech, or the
//     language's Wiktionary contraction list, stamped as is_contraction):
//     pt "no" is em + o, not a form of em;
//   - it shows an expression built on this exact form, and the form is not
//     the lemma's own spelling: "no sé" keeps sé, "muchas gracias" keeps
//     muchas, while "tener cuidado" on tener or "por favor" on favor do not.
// Vocabulary cards teach meanings; conjugation mode teaches forms, so an
// irregular form is not, by itself, a reason to stay separate.
function normalizeLemmaToken(value) {
    return String(value || '').normalize('NFC').toLocaleLowerCase('es').trim();
}

function isExpressionSenseForLemma(meaning, item) {
    if (!meaning) return false;
    const pos = meaning.pos || meaning.part_of_speech;
    if (pos === 'MWE' || pos === 'CLITIC') return true;
    const adapter = String(meaning?.metadata?.source_adapter || meaning?.source || '');
    if (/mwe-merged/i.test(adapter)) return true;
    if (String(meaning.context || '').toLocaleLowerCase('en') === 'multiword expression') return true;
    const evidence = meaning.metadata?.multiword_evidence?.[0];
    const route = evidence?.wsd_routing || evidence?.route || meaning.wsd_routing || meaning.route;
    if (route === 'deterministic_bypass' || route === 'invariant'
        || route === 'competitive_wsd' || route === 'ambiguous') return true;
    if (pos === 'PHRASE') {
        const head = String(meaning.headword || meaning.expression || '').trim();
        const surface = String(item?.word || item?.targetWord || '').trim();
        if (/\s/u.test(head) && normalizeLemmaToken(head) !== normalizeLemmaToken(surface)) return true;
    }
    return false;
}

function lemmaHeadwordsOf(item) {
    const seen = new Set();
    const headwords = [];
    for (const meaning of item?.meanings || []) {
        if (!meaning?.headword || isExpressionSenseForLemma(meaning, item)) continue;
        const key = normalizeLemmaToken(meaning.headword);
        if (!key || seen.has(key)) continue;
        seen.add(key);
        headwords.push(key);
    }
    return headwords;
}

function isContractionForLemma(item) {
    if (item?.is_contraction) return true;
    return (item?.meanings || []).some(meaning =>
        String(meaning?.pos || meaning?.part_of_speech || '').toUpperCase() === 'CONTRACTION');
}

function expressionTokens(value) {
    return normalizeLemmaToken(value).split(/[^\p{L}\p{M}'’]+/u).filter(Boolean);
}

// An expression frozen on this very spelling. The lemma's own spelling never
// counts: a construction headed by the lemma (tener cuidado, dejar de) belongs
// on the merged card as one of its senses, and argues for no form in particular.
function hasFrozenFormExpression(item, lemma) {
    const surface = normalizeLemmaToken(item?.word || item?.targetWord);
    if (!surface || surface === lemma) return false;
    return (item?.meanings || []).some(meaning => {
        if (!isExpressionSenseForLemma(meaning, item)) return false;
        const phrase = meaning.headword || meaning.expression || '';
        const tokens = expressionTokens(phrase);
        return tokens.length > 1 && tokens.includes(surface);
    });
}

function lemmaGroupKey(item) {
    // Derived, not shipped. Identity stays the surface card. This key only
    // decides which unambiguous spellings share a merged card.
    //
    // No headword at all: the shipped lemma is the legacy fallback. Two or
    // more headwords: this spelling is the clash, and it must not inherit the
    // shipped lemma or a yes on casado would clear casó.
    const headwords = lemmaHeadwordsOf(item);
    if (headwords.length > 1) return '';
    // A Speech card whose senses have not loaded yet carries the key the
    // pipeline computed from those same senses by this same rule
    // (fluency.enrichments.card_rules); without it only the shipped lemma
    // column would be left, and fue would fold into ser.
    if (headwords.length === 0 && typeof item?.merge_key === 'string') return item.merge_key;
    const lemma = headwords[0] || normalizeLemmaToken(item?.lemma);
    if (!lemma) return '';
    if (isContractionForLemma(item) || hasFrozenFormExpression(item, lemma)) return '';
    return lemma;
}

function lemmaSeenKey(item) {
    if (lemmaHeadwordsOf(item).length > 1) return '';
    return lemmaGroupKey(item);
}

function lemmaSenseDedupeKey(meaning) {
    const ref = String(meaning?.source_reference || '').trim();
    if (ref && ref !== 'mwe-merged/v1') return `ref:${ref}`;
    const pos = String(meaning?.pos || '').trim().toLocaleLowerCase('en');
    const translation = String(meaning?.translation || meaning?.meaning || '').trim().toLocaleLowerCase('en');
    const context = String(meaning?.context || '').trim().toLocaleLowerCase('en');
    return `sig:${pos}|${translation}|${context}`;
}

function dedupeLemmaMenu(meanings) {
    const seen = new Set();
    const kept = [];
    for (const meaning of meanings || []) {
        const key = lemmaSenseDedupeKey(meaning);
        if (seen.has(key)) continue;
        seen.add(key);
        kept.push(meaning);
    }
    return kept;
}

function cleanHeadwordToken(hw) {
    const token = normalizeLemmaToken(hw);
    if (token.endsWith('se') && token.length > 3) {
        return token.slice(0, -2);
    }
    return token;
}

function detectSplitCardTuples(item, lang = 'es') {
    const word = normalizeLemmaToken(item?.word || item?.targetWord);
    const meanings = Array.isArray(item?.meanings) ? item.meanings : [];
    const lex = meanings.filter(m => m && !isExpressionSenseForLemma(m, item));
    if (lex.length < 4) return null;

    // Class 1: True Homograph (Distinct base headwords, e.g. ser vs ir, paso vs pasar)
    const hws = new Map();
    for (const m of lex) {
        const hw = cleanHeadwordToken(m.headword || word);
        if (!hws.has(hw)) hws.set(hw, []);
        hws.get(hw).push(m);
    }

    const collapsed = new Map();
    for (const [hw, ms] of hws.entries()) {
        let matched = false;
        for (const c of collapsed.keys()) {
            const cRoot = c.replace(/[osae]+$/u, '');
            const hwRoot = hw.replace(/[osae]+$/u, '');
            if (cRoot === hwRoot && cRoot.length >= 3) {
                collapsed.get(c).push(...ms);
                matched = true;
                break;
            }
        }
        if (!matched) collapsed.set(hw, [...ms]);
    }

    const totalLen = lex.length;
    const viable = [];
    for (const [hw, ms] of collapsed.entries()) {
        if (ms.length / totalLen >= 0.14 && ms.length >= 1) {
            viable.push([hw, ms]);
        }
    }

    if (viable.length >= 2) {
        viable.sort((a, b) => b[1].length - a[1].length);
        const [hw1, ms1] = viable[0];
        const [hw2, ms2] = viable[1];
        const tr1 = String(ms1[0]?.translation || ms1[0]?.meaning || '').trim();
        const tr2 = String(ms2[0]?.translation || ms2[0]?.meaning || '').trim();
        const pos1 = String(ms1[0]?.pos || 'X').toUpperCase();
        const pos2 = String(ms2[0]?.pos || 'X').toUpperCase();
        return {
            kind: 'homograph',
            tuple1: {
                headword: hw1,
                pos: pos1,
                label: `${hw1} (${tr1})`,
                meanings: ms1,
                share: Math.round((ms1.length / totalLen) * 100) / 100,
                isReflexive: false
            },
            tuple2: {
                headword: hw2,
                pos: pos2,
                label: `${hw2} (${tr2})`,
                meanings: ms2,
                share: Math.round((ms2.length / totalLen) * 100) / 100,
                isReflexive: false
            }
        };
    }

    // Class 2: Pronominal / Reflexive Shift (Attested base vs pronominal headword)
    const baseM = lex.filter(m => !normalizeLemmaToken(m.headword).endsWith('se'));
    const reflM = lex.filter(m => normalizeLemmaToken(m.headword).endsWith('se'));
    if (baseM.length >= 1 && reflM.length >= 1) {
        const baseHws = baseM.map(m => normalizeLemmaToken(m.headword || word));
        const reflHws = reflM.map(m => normalizeLemmaToken(m.headword));
        let matchedRoot = null;
        for (const rHw of reflHws) {
            const rBase = rHw.endsWith('se') && rHw.length > 3 ? rHw.slice(0, -2) : null;
            if (rBase && (baseHws.includes(rBase) || rBase === word || baseHws.some(b => b.startsWith(rBase)))) {
                matchedRoot = rBase;
                break;
            }
        }
        if (!matchedRoot && baseHws.length > 0) {
            for (const bHw of baseHws) {
                if (reflHws.includes(`${bHw}se`)) {
                    matchedRoot = bHw;
                    break;
                }
            }
        }
        if (matchedRoot && (reflM.length / totalLen >= 0.14)) {
            const tr1 = String(baseM[0]?.translation || baseM[0]?.meaning || '').trim();
            const tr2 = String(reflM[0]?.translation || reflM[0]?.meaning || '').trim();
            const pos1 = String(baseM[0]?.pos || 'VERB').toUpperCase();
            const pos2 = String(reflM[0]?.pos || 'VERB').toUpperCase();
            return {
                kind: 'reflexive',
                root: matchedRoot,
                tuple1: {
                    headword: matchedRoot,
                    pos: pos1,
                    label: `${matchedRoot} (${tr1})`,
                    meanings: baseM,
                    share: Math.round((baseM.length / totalLen) * 100) / 100,
                    isReflexive: false
                },
                tuple2: {
                    headword: `${matchedRoot}se`,
                    pos: pos2,
                    label: `${matchedRoot}se (${tr2})`,
                    meanings: reflM,
                    share: Math.round((reflM.length / totalLen) * 100) / 100,
                    isReflexive: true
                }
            };
        }
    }

    return null;
}

// /lemma-merge-pure

// A surface split into a companion pair (detectSplitCardTuples) becomes two
// study cards, Flashcard 1 of 2 and 2 of 2, built from the finished card of
// the whole surface. Shared by the deck builder and every path that opens one
// word on its own (search, word links, lyric breakdown), so a split word is
// never shown as one combined card. Returns null for a word that does not
// split.
function buildSplitCardPair(item, card, meanings, lang = selectedLanguage) {
    const splitTuples = detectSplitCardTuples(item, lang);
    if (!splitTuples || !splitTuples.tuple1 || !splitTuples.tuple2) return null;
    const t1 = splitTuples.tuple1;
    const t2 = splitTuples.tuple2;
    const baseFullId = getWordId(item);
    const baseId = item.id;

    const firstEx1 = t1.meanings.length > 0
        ? {
            targetSentence: t1.meanings[0].targetSentence || '',
            englishSentence: t1.meanings[0].englishSentence || '',
        }
        : { targetSentence: '', englishSentence: '' };
    const firstEx2 = t2.meanings.length > 0
        ? {
            targetSentence: t2.meanings[0].targetSentence || '',
            englishSentence: t2.meanings[0].englishSentence || '',
        }
        : { targetSentence: '', englishSentence: '' };

    // Each sense goes to the card its split put it on: detectSplitCardTuples
    // assigned every sense id to one reading. Only a sense outside the split
    // (an expression) falls back to its headword. Comparing cleaned headwords
    // alone put ponerse's senses on poner's card too, since cleaning drops -se.
    const ids1 = new Set(t1.meanings.map(m => m.sense_id || m.senseId).filter(Boolean));
    const ids2 = new Set(t2.meanings.map(m => m.sense_id || m.senseId).filter(Boolean));
    const readingOf = m => {
        const id = m.senseId || m.sense_id;
        if (id && ids1.has(id)) return 1;
        if (id && ids2.has(id)) return 2;
        if (splitTuples.kind === 'reflexive') {
            return normalizeLemmaToken(m.headword || item.word).endsWith('se') ? 2 : 1;
        }
        const hw = cleanHeadwordToken(m.headword || item.word);
        if (hw === cleanHeadwordToken(t1.headword)) return 1;
        if (hw === cleanHeadwordToken(t2.headword)) return 2;
        return 0;
    };
    const belongs1 = m => readingOf(m) === 1;
    const belongs2 = m => readingOf(m) === 2;
    const m1 = meanings.filter(belongs1);
    const m2 = meanings.filter(belongs2);
    const rarerOf = belongs => (card.unusedMenuSenses || []).filter(m => m.lowShare && belongs(m));
    const meanings1 = m1.length > 0 ? stampSplitShownShares(item, m1, rarerOf(belongs1)) : meanings;
    const meanings2 = m2.length > 0 ? stampSplitShownShares(item, m2, rarerOf(belongs2)) : meanings;

    const card1 = {
        ...card,
        id: `${baseId}::split::${t1.headword}_${t1.pos}`,
        fullId: `${baseFullId}::split::${t1.headword}_${t1.pos}`,
        citationForm: t1.headword,
        partOfSpeech: t1.pos,
        meanings: meanings1,
        translation: meanings1[0]?.meaning || '',
        targetSentence: meanings1[0]?.targetSentence || firstEx1.targetSentence,
        englishSentence: meanings1[0]?.englishSentence || firstEx1.englishSentence,
        splitInfo: {
            index: 1,
            total: 2,
            kind: splitTuples.kind,
            headword: t1.headword,
            pos: t1.pos,
            label: t1.label,
            share: t1.share,
            siblingHeadword: t2.headword,
            siblingPos: t2.pos,
            siblingLabel: t2.label,
            siblingShare: t2.share
        }
    };

    const card2 = {
        ...card,
        id: `${baseId}::split::${t2.headword}_${t2.pos}`,
        fullId: `${baseFullId}::split::${t2.headword}_${t2.pos}`,
        citationForm: t2.headword,
        partOfSpeech: t2.pos,
        meanings: meanings2,
        translation: meanings2[0]?.meaning || '',
        targetSentence: meanings2[0]?.targetSentence || firstEx2.targetSentence,
        englishSentence: meanings2[0]?.englishSentence || firstEx2.englishSentence,
        splitInfo: {
            index: 2,
            total: 2,
            kind: splitTuples.kind,
            headword: t2.headword,
            pos: t2.pos,
            label: t2.label,
            share: t2.share,
            siblingHeadword: t1.headword,
            siblingPos: t1.pos,
            siblingLabel: t1.label,
            siblingShare: t1.share
        }
    };
    return [card1, card2];
}
globalThis.buildSplitCardPair = buildSplitCardPair;

// Cognate mode asks the same question per sense: an expression is never a
// free cognate, so it reads the one definition of "expression" there is.
globalThis.isExpressionSenseForLemma = isExpressionSenseForLemma;
globalThis.detectSplitCardTuples = detectSplitCardTuples;
globalThis.cleanHeadwordToken = cleanHeadwordToken;

function computeLemmaExampleCounts(vocabData, examplesData) {
    const linesByLemma = new Map();
    let hasExampleBasis = false;
    for (const item of vocabData) {
        const lemmaKey = lemmaGroupKey(item);
        if (!lemmaKey || item.is_english || item.is_noise || item.is_interjection || item.duplicate) continue;
        if (!linesByLemma.has(lemmaKey)) linesByLemma.set(lemmaKey, new Set());
        const lines = linesByLemma.get(lemmaKey);
        (item.meanings || []).forEach((meaning, i) => {
            for (const example of examplesForMeaning(item, meaning, i, examplesData)) {
                const key = exampleSentenceKey(example);
                if (!key) continue;
                hasExampleBasis = true;
                lines.add(key);
            }
        });
    }
    return {
        counts: new Map(Array.from(linesByLemma, ([lemma, lines]) => [lemma, lines.size])),
        hasExampleBasis
    };
}

function poolLemmaSiblingExamples(filteredData, allVocabData, examplesData) {
    const hosts = new Map();
    for (const item of filteredData) {
        const lemmaKey = lemmaGroupKey(item);
        if (lemmaKey && !hosts.has(lemmaKey)) hosts.set(lemmaKey, item);
    }
    if (hosts.size === 0) return;

    const normalize = t => (t || '').trim().toLowerCase();
    for (const sib of allVocabData) {
        // An ambiguous spelling never donates its examples or its sense rows.
        if (lemmaHeadwordsOf(sib).length !== 1) continue;
        const host = hosts.get(lemmaGroupKey(sib));
        if (!host || sib === host || (sib.id && sib.id === host.id)) continue;
        if (sib.is_english || sib.is_noise || sib.is_interjection || sib.duplicate) continue;
        if (!sib.meanings || sib.meanings.length === 0) continue;

        for (let i = 0; i < sib.meanings.length; i++) {
            const sm = sib.meanings[i];
            // Prefer inline examples (multi-artist merged entries carry the
            // cross-artist union); fall back to the split examples file.
            const sibExamples = examplesForMeaning(sib, sm, i, examplesData);
            if (sibExamples.length === 0) continue;

            // Match on the sense itself first. Each form's gloss is inflected
            // for that form (despeja "clear!", despejas "you clear"), so the
            // same sense no longer shares its translation text across forms.
            const target = (sm.sense_id && host.meanings.find(hm => hm.sense_id === sm.sense_id))
                || host.meanings.find(hm => normalize(hm.translation) === normalize(sm.translation))
                || host.meanings[0];
            if (!target) continue;
            if (!target.examples) target.examples = [];
            const seen = new Set(target.examples.map(exampleSentenceKey));
            for (const e of sibExamples) {
                const key = exampleSentenceKey(e);
                if (!key || seen.has(key)) continue;
                seen.add(key);
                target.examples.push({
                    ...e,
                    pooledFrom: sib.word,
                    // Keep the grammar of the exact sibling surface beside
                    // its pooled example. Merged cards can then present the
                    // evidenced form (dieron) while retaining the shared
                    // lemma (dar) as their stable identity.
                    pooledMorphology: e.pooledMorphology || sib.morphology || null,
                    // The sibling form's own gloss, shown while this example
                    // is the active one (flashcards.js applyPooledExampleGloss).
                    pooledTranslation: e.pooledTranslation || sm.translation || null
                });
            }
        }

        // One-off surface forms can carry their unclassified artist line in
        // the compact `r` bucket rather than a master-sense `m` bucket. They
        // still belong in the recurring lemma host's example pool.
        const rawSiblingExamples = examplesData?.[sib.id]?.r || [];
        const rawTarget = host.meanings.find(meaning => meaning.examples?.length)
            || host.meanings[0];
        if (rawTarget && rawSiblingExamples.length > 0) {
            rawTarget.examples = rawTarget.examples || [];
            const seen = new Set(rawTarget.examples.map(exampleSentenceKey));
            for (const example of rawSiblingExamples) {
                const key = exampleSentenceKey(example);
                if (!key || seen.has(key)) continue;
                seen.add(key);
                rawTarget.examples.push({
                    ...example,
                    pooledFrom: example.pooledFrom || sib.word,
                    pooledMorphology: example.pooledMorphology || sib.morphology || null
                });
            }
        }
    }

    // The card-front pooled frequency uses this exact attached-example
    // union. Count across meanings once so a line assigned to two senses
    // does not inflate the lemma total.
    for (const host of hosts.values()) {
        const seen = new Set();
        for (const meaning of (host.meanings || [])) {
            for (const example of (meaning.examples || [])) {
                const key = exampleSentenceKey(example);
                if (key) seen.add(key);
            }
        }
        host.lemma_example_count = seen.size;
        host.pooled_frequency = seen.size;
    }
}

/**
 * Keep the three jobs historically performed by `targetWord` separate:
 * - displaySurface: the corpus form used for a target-language prompt;
 * - citationForm: the dictionary/lemma form that explains the lexeme;
 * - productionAnswer: the preferred target-language answer used by the
 *   English→target direction.
 *
 * The snake_case aliases make this an adapter for future pipeline fields while
 * the lemma/word fallbacks preserve every currently shipped deck.
 */
// The headword of the sense the card is actually about, weighted by assigned
// frequency. Display and grouping both read this, so a merged card can never be
// filed under one lemma and titled with another.
function assignedHeadwordOf(meanings) {
    const scored = (meanings || [])
        .filter(mn => mn && mn.headword && Number(mn.percentage ?? mn.frequency ?? 0) > 0)
        .map(mn => [Number(mn.percentage ?? mn.frequency ?? 0), String(mn.headword).trim()])
        .filter(pair => pair[1]);
    if (!scored.length) {
        // No frequencies yet (an unassigned deck): fall back to the first
        // headword the provider gave rather than losing the grouping entirely.
        const first = (meanings || []).find(mn => mn && mn.headword);
        return first ? String(first.headword).trim() : '';
    }
    return scored.reduce((a, b) => (b[0] > a[0] ? b : a))[1];
}

function buildCardFormModel(item, meanings = [], options = {}) {
    const representativeSurface = String(
        item?.dominant_surface
        || item?.dominantSurface
        || item?.display_surface
        || item?.displaySurface
        || item?.word
        || item?.targetWord
        || ''
    ).trim();
    // The headword SpanishDict attached to the sense that was actually picked.
    // `item.lemma` is decided upstream by the inventory/lemma layer, entirely
    // independently of WSD, so the two can disagree: the `mate` card was
    // lemmatised `matar` while its winning sense is `mate`/NOUN "checkmate".
    // There must not be two lemmatisations telling the learner different things,
    // and the assigned sense is the one with evidence behind it, so it wins.
    // Ties are broken by assigned frequency — the sense the card is actually about.
    const assignedHeadword = assignedHeadwordOf(meanings);
    const citationForm = String(
        assignedHeadword
        || item?.citation_form
        || item?.citationForm
        || item?.lemma
        || representativeSurface
    ).trim();
    // Merge Lemmas still uses the most frequent surface entry as its stable
    // rank/progress host, but the learner is studying the lexeme, not that
    // accidental representative inflection. Present the citation form while
    // retaining targetWord/representativeSurface for IDs and exact examples.
    // Only an unambiguous spelling is a merged lemma. Casado names casar and
    // casado, so it stays the surface card and does not wear the verb's title.
    const unambiguousLemma = lemmaHeadwordsOf(item).length === 1;
    const mergedLemma = options.mergedLemma === true && unambiguousLemma && Boolean(citationForm);
    const displaySurface = mergedLemma ? citationForm : representativeSurface;
    const hasVerbSense = meanings.some(meaning => {
        const pos = String(meaning?.pos || '').toLocaleLowerCase('en');
        return pos === 'v' || pos === 'vb' || pos.includes('verb');
    });
    const explicitPronominal = item?.is_pronominal ?? item?.isPronominal;
    const isPronominal = explicitPronominal !== undefined
        ? Boolean(explicitPronominal)
        : selectedLanguage === 'spanish'
            && hasVerbSense
            && /se$/iu.test(citationForm);
    const productionAnswer = String(
        item?.production_answer
        || item?.productionAnswer
        // A standalone surface-form card tests that surface. A merged card
        // tests the shared lemma. Pronominal verbs fall back to their complete
        // `-se` citation rather than presenting an incomplete bare form when
        // old data lacks enough morphology to choose me/te/se/nos/os safely.
        || (mergedLemma || isPronominal ? citationForm : representativeSurface)
        || citationForm
        || displaySurface
    ).trim();

    return {
        displaySurface,
        representativeSurface,
        citationForm,
        productionAnswer,
        isPronominal,
        mergedLemma
    };
}

/**
 * Fetch the artist/language index and join with master vocabulary if needed.
 * Caches the master and the joined result. Returns denormalized entries with all fields
 * (word, lemma, meanings, flags) that buildFilteredVocab() and other consumers expect.
 */
// Record the newest Last-Modified across the vocab data files, plus when we
// fetched. The service worker preserves the original response headers, so a
// stale cached file keeps its old date — the settings-modal footer surfaces
// this so "am I seeing cached data?" is answerable at a glance. Called at
// every vocab data fetch site (index, master, examples, merge, CSV ranges).
function trackDataFreshness(resp) {
    if (!resp || !resp.headers) return;
    const lm = resp.headers.get('last-modified');
    if (!lm) return;
    const t = new Date(lm).getTime();
    if (isNaN(t)) return;
    if (!window._vocabDataLastModified || t > window._vocabDataLastModified) {
        window._vocabDataLastModified = t;
    }
    window._vocabDataLoadedAt = Date.now();
    // Per-file breakdown for the JST dev footer.
    try {
        const name = decodeURIComponent(new URL(resp.url).pathname.split('/').pop());
        window._vocabDataFreshness = window._vocabDataFreshness || {};
        window._vocabDataFreshness[name] = t;
    } catch (e) { /* resp.url unset in some test contexts — breakdown only */ }
}
window.trackDataFreshness = trackDataFreshness;

// Keep parsed/joined indexes per path. A level-estimate lookup may need the
// Speech index while the learner is in Lyrics mode; the old single-slot cache
// evicted the artist index and forced another multi-megabyte parse immediately
// afterwards.
const joinedIndexCacheByPath = new Map();
const loadedExampleShards = new Set();
const exampleShardInflight = new Map();
let exampleShardManifest = null;
let exampleShardManifestFor = null;
let exampleShardsActive = false;

function examplesDirectory(examplesPath) {
    if (!examplesPath) return '';
    return examplesPath.slice(0, examplesPath.lastIndexOf('/') + 1);
}

let exampleShardManifestInflight = null;
let exampleShardManifestInflightPath = null;

async function loadExampleShardManifest(langConfig) {
    const examplesPath = langConfig?.examplesPath;
    if (!examplesPath) return null;
    if (exampleShardManifestFor === examplesPath) return exampleShardManifest;
    if (exampleShardManifestInflight && exampleShardManifestInflightPath === examplesPath) {
        return exampleShardManifestInflight;
    }
    const pending = (async () => {
        const manifestPath = `${examplesDirectory(examplesPath)}vocabulary.examples.manifest.json`;
        try {
            const response = await fetch(manifestPath);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const manifest = await response.json();
            if (!manifest || !Array.isArray(manifest.shards) || !manifest.shards.length) {
                throw new Error('empty example shard manifest');
            }
            loadedExampleShards.clear();
            exampleShardManifest = manifest;
            exampleShardManifestFor = examplesPath;
            exampleShardsActive = true;
            return manifest;
        } catch (_) {
            exampleShardManifest = null;
            exampleShardManifestFor = examplesPath;
            exampleShardsActive = false;
            return null;
        }
    })();
    exampleShardManifestInflight = pending;
    exampleShardManifestInflightPath = examplesPath;
    try {
        return await pending;
    } finally {
        if (exampleShardManifestInflightPath === examplesPath) {
            exampleShardManifestInflight = null;
            exampleShardManifestInflightPath = null;
        }
    }
}

function exampleShardsForRange(manifest, rangeStart, rangeEnd) {
    return (manifest?.shards || []).filter(shard =>
        Number(shard.start_rank) < rangeEnd && Number(shard.end_rank) >= rangeStart
    );
}

// slim-example-pure
// Slim shards (example-shards/v2, fluency.release.example_shards.slim_example)
// carry only what the app reads, keyed short, with each source's shared
// attribution, licence and URL in the manifest. Expand back to the full
// record shape here so nothing downstream knows the difference.
const SLIM_EXAMPLE_FORMAT = 'slim-example/v1';

function slimId(value, prefix) {
    if (value == null || value === '') return undefined;
    return value[0] === '=' ? value.slice(1) : prefix + value;
}

function expandSlimExample(record, sources) {
    const shared = (sources && sources[record.s]) || {};
    const attribution = record.b ?? shared.attribution;
    const license = record.l ?? shared.license;
    const url = record.o ?? shared.url;
    const example = {
        target: record.t,
        english: record.e,
        source: record.s,
        assignment_method: record.a ?? record.s,
    };
    const exampleId = slimId(record.x, 'example_');
    if (exampleId) example.example_id = exampleId;
    if (attribution) example.attribution = attribution;
    if (license) example.license = license;
    if (record.r) example.source_record_id = record.r;
    if (record.c) example.contributor = record.c;
    if (record.su) example.source_url = record.su;
    if (record.ul) example.sentence_url = record.ul;
    if (record.ts) example.translation_source = record.ts;
    const source = { name: record.s };
    if (url) source.url = url;
    if (attribution) source.attribution = attribution;
    if (license) source.license = license;
    if (record.r) source.source_record_id = record.r;
    const metadata = { source };
    const sentenceId = slimId(record.i, 'sentence_');
    if (sentenceId) metadata.sentence_id = sentenceId;
    if (Array.isArray(record.d)) {
        const [title_id, subtitle_id, line] = record.d;
        source.document = { title_id, subtitle_id, line };
        example.provenance = { corpus: record.pc || record.s, title_id, subtitle_id, line };
    }
    const targetUrl = record.tu === 1 ? url : record.tu;
    const targetContributor = record.tc ?? record.c;
    if (targetUrl || targetContributor) {
        metadata.target = {};
        if (targetUrl) metadata.target.url = targetUrl;
        if (targetContributor) metadata.target.contributor = targetContributor;
    }
    if (record.st) {
        example.source_title = record.st;
        metadata.source_title = record.st;
    }
    if (Array.isArray(record.w)) {
        const [level, agree] = record.w;
        metadata.wsd = {};
        if (level) metadata.wsd.supported_level = level;
        if (agree) metadata.wsd.gemini_recommendation = { reason: 'cheap_leaf_choices_agree' };
    }
    example.metadata = metadata;
    return example;
}

function expandSlimExamplePayload(payload, manifest) {
    if (manifest?.example_format !== SLIM_EXAMPLE_FORMAT || !payload) return payload;
    const sources = manifest.sources || {};
    const expanded = {};
    for (const [id, card] of Object.entries(payload)) {
        expanded[id] = {
            ...card,
            m: (card?.m || []).map(group => (group || []).map(record => expandSlimExample(record, sources))),
        };
    }
    return expanded;
}
// /slim-example-pure

function mergeExamplePayload(payload, examplesPath) {
    const existing = (
        window._cachedExamplesDataPath === examplesPath
            ? (window._cachedExamplesDataRaw || window._cachedExamplesData)
            : null
    ) || {};
    const merged = Object.assign({}, existing, payload);
    window.setActiveExamplesData?.(merged, examplesPath)
        || (window._cachedExamplesData = merged, window._cachedExamplesDataPath = examplesPath);
}

function exampleShardsForRanks(manifest, ranks) {
    const needed = ranks.filter(rank => Number.isFinite(rank));
    if (!needed.length) return [];
    return (manifest?.shards || []).filter(shard => {
        const start = Number(shard.start_rank);
        const end = Number(shard.end_rank);
        return needed.some(rank => rank >= start && rank <= end);
    });
}

async function fetchExampleShard(langConfig, shard) {
    const examplesPath = langConfig.examplesPath;
    const key = `${examplesPath}:${shard.path}`;
    if (loadedExampleShards.has(key)) return;
    if (exampleShardInflight.has(key)) return exampleShardInflight.get(key);
    const pending = fetch(`${examplesDirectory(examplesPath)}${shard.path}`).then(async response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        trackDataFreshness(response);
        const manifest = exampleShardManifestFor === examplesPath ? exampleShardManifest : null;
        mergeExamplePayload(expandSlimExamplePayload(await response.json(), manifest), examplesPath);
        loadedExampleShards.add(key);
    }).finally(() => exampleShardInflight.delete(key));
    exampleShardInflight.set(key, pending);
    return pending;
}

async function ensureExampleShardsForRange(langConfig, rangeStart, rangeEnd, ranks) {
    const manifest = await loadExampleShardManifest(langConfig);
    if (!manifest) return false;
    const shards = ranks?.length
        ? exampleShardsForRanks(manifest, ranks)
        : exampleShardsForRange(manifest, rangeStart, rangeEnd);
    await Promise.all([
        ...shards.map(shard => fetchExampleShard(langConfig, shard)),
        window.loadSourceTitles?.() || Promise.resolve(),
    ]);
    return true;
}

function prefetchExampleShardsForRange(langConfig, rangeStart, rangeEnd) {
    ensureExampleShardsForRange(langConfig, rangeStart, rangeEnd).catch(() => {});
}

function prefetchExampleShardsForRangeString(langConfig, rangeString) {
    if (!rangeString) return;
    const [rangeStart, rangeEnd] = String(rangeString).split('-').map(Number);
    if (!Number.isFinite(rangeStart) || !Number.isFinite(rangeEnd)) return;
    prefetchExampleShardsForRange(langConfig, rangeStart, rangeEnd);
}

async function loadMonolithExamples(langConfig) {
    const examplesPath = langConfig?.examplesPath;
    if (!examplesPath) return null;
    if (window._cachedExamplesData && window._cachedExamplesDataPath === examplesPath && !exampleShardsActive) {
        return window._cachedExamplesData;
    }
    const [response] = await Promise.all([
        fetch(examplesPath),
        window.loadSourceTitles?.() || Promise.resolve(),
    ]);
    if (!response.ok) {
        throw new Error(`Configured examples file ${examplesPath} returned HTTP ${response.status}`);
    }
    trackDataFreshness(response);
    const examples = await response.json();
    return window.setActiveExamplesData?.(examples, examplesPath)
        || (window._cachedExamplesData = examples);
}

async function ensureExamplesForRange(langConfig, rangeStart, rangeEnd, ranks) {
    if (!langConfig?.examplesPath) return null;
    if (await ensureExampleShardsForRange(langConfig, rangeStart, rangeEnd, ranks)) {
        return window._cachedExamplesData;
    }
    return loadMonolithExamples(langConfig);
}

const loadedIndexRowShards = new Set();
const indexRowShardInflight = new Map();
let indexShardManifest = null;
let indexShardManifestFor = null;
let indexShardsActive = false;
let indexShardManifestInflight = null;
let indexShardManifestInflightPath = null;

function indexDirectory(indexPath) {
    if (!indexPath) return '';
    return indexPath.slice(0, indexPath.lastIndexOf('/') + 1);
}

async function loadIndexShardManifest(langConfig) {
    const indexPath = langConfig?.indexPath || langConfig?.dataPath;
    if (!indexPath) return null;
    if (indexShardManifestFor === indexPath) return indexShardManifest;
    if (indexShardManifestInflight && indexShardManifestInflightPath === indexPath) {
        return indexShardManifestInflight;
    }
    // Only a definite answer is remembered for the session: a manifest, or a
    // release that has none (404, or an empty manifest). A network failure or
    // a server error is tried once more and then left unremembered, so the
    // next load asks again. Remembering it sent every later load to the
    // monolith vocabulary.index.json, which sharded releases do not publish.
    const settle = manifest => {
        if (manifest) loadedIndexRowShards.clear();
        indexShardManifest = manifest;
        indexShardManifestFor = indexPath;
        indexShardsActive = Boolean(manifest);
        return manifest;
    };
    const pending = (async () => {
        const url = `${indexDirectory(indexPath)}vocabulary.index.manifest.json`;
        for (let attempt = 0; attempt < 2; attempt++) {
            let response;
            try {
                response = await fetch(url);
            } catch (_) {
                continue;
            }
            if (response.status === 404) return settle(null);
            if (!response.ok) continue;
            let manifest = null;
            try {
                manifest = await response.json();
            } catch (_) {
                return settle(null);
            }
            if (!manifest || !Array.isArray(manifest.shards) || !manifest.shards.length || !manifest.columns) {
                return settle(null);
            }
            return settle(manifest);
        }
        indexShardsActive = false;
        return null;
    })();
    indexShardManifestInflight = pending;
    indexShardManifestInflightPath = indexPath;
    try {
        return await pending;
    } finally {
        if (indexShardManifestInflightPath === indexPath) {
            indexShardManifestInflight = null;
            indexShardManifestInflightPath = null;
        }
    }
}

function hydrateIndexColumns(columns) {
    const n = Number(columns?.n) || 0;
    const fields = Object.keys(columns || {}).filter(key => key !== 'schema' && key !== 'n' && Array.isArray(columns[key]));
    const cards = new Array(n);
    for (let i = 0; i < n; i++) {
        const card = { meanings: [] };
        for (const field of fields) {
            const value = columns[field][i];
            if (value !== undefined && value !== null && value !== '') card[field] = value;
        }
        cards[i] = card;
    }
    return cards;
}

function mergeIndexRowPayload(payload) {
    if (!payload || !window._cachedJoinedIndex) return;
    for (const card of window._cachedJoinedIndex) {
        const fat = payload[card.id];
        if (!fat) continue;
        Object.assign(card, fat);
        card._indexRowsPending = false;
    }
}

async function fetchIndexRowShard(langConfig, shard) {
    const indexPath = langConfig.indexPath || langConfig.dataPath;
    const key = `${indexPath}:${shard.path}`;
    if (loadedIndexRowShards.has(key)) return;
    if (indexRowShardInflight.has(key)) return indexRowShardInflight.get(key);
    const pending = fetch(`${indexDirectory(indexPath)}${shard.path}`).then(async response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        trackDataFreshness(response);
        mergeIndexRowPayload(await response.json());
        loadedIndexRowShards.add(key);
    }).finally(() => indexRowShardInflight.delete(key));
    indexRowShardInflight.set(key, pending);
    return pending;
}

async function ensureIndexRowsForRange(langConfig, rangeStart, rangeEnd, ranks) {
    const manifest = await loadIndexShardManifest(langConfig);
    if (!manifest) return false;
    const shards = ranks?.length
        ? exampleShardsForRanks(manifest, ranks)
        : exampleShardsForRange(manifest, rangeStart, rangeEnd);
    await Promise.all(shards.map(shard => fetchIndexRowShard(langConfig, shard)));
    return true;
}

async function loadColumnarIndex(langConfig, indexPath) {
    const manifest = await loadIndexShardManifest(langConfig);
    if (!manifest) return null;
    const response = await fetch(`${indexDirectory(indexPath)}${manifest.columns}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    trackDataFreshness(response);
    const cards = hydrateIndexColumns(await response.json());
    if (!cards.length) throw new Error('empty index columns');
    cards.forEach(card => { card._indexRowsPending = true; });
    return cards;
}

function parseStudyRangeString(rangeString) {
    if (!rangeString) return null;
    const [rangeStart, rangeEnd] = String(rangeString).split('-').map(Number);
    if (!Number.isFinite(rangeStart) || !Number.isFinite(rangeEnd)) return null;
    return [rangeStart, rangeEnd];
}

function prefetchStudySetPayload(langConfig, rangeString) {
    const range = parseStudyRangeString(rangeString);
    if (!langConfig || !range) return;
    const [rangeStart, rangeEnd] = range;
    ensureIndexRowsForRange(langConfig, rangeStart, rangeEnd).catch(() => {});
    prefetchExampleShardsForRange(langConfig, rangeStart, rangeEnd);
}

function rememberLyricsReleaseVocabulary(indexPath, data) {
    const releaseId = activeArtist?.releaseId;
    if (!releaseId || !indexPath || !Array.isArray(data)) return;
    window._lyricsReleaseVocabularyCache = { releaseId, indexPath, data };
}

// `ignoreArtist` reads the Speech deck as it is, whatever mode is active: the
// level check and the estimate's known-word set are measured against Speech
// frequency. While an artist or playlist is active that read is detached: it
// leaves the active-source pointers and the lyrics release cache alone, and
// takes the monolith, whose rows carry their meanings without set shards.
async function fetchAndJoinIndex(langConfig, { ignoreArtist = false } = {}) {
    const detached = ignoreArtist && (Boolean(activeArtist) || Boolean(window.playlistLiveActive?.()));
    if (detached) return fetchDetachedIndex(langConfig);
    const effectiveConfig = (!ignoreArtist && activeArtist && (activeArtist.language || 'spanish') === (langConfig?.language || selectedLanguage))
        ? { ...(langConfig || {}), ...activeArtist }
        : langConfig;
    const indexPath = effectiveConfig.indexPath || effectiveConfig.dataPath;

    const cacheKey = window.playlistLiveActive?.() ? `${indexPath}:playlist-live` : indexPath;
    // Preserve the legacy active-source pointers for search/modal consumers,
    // while retaining other sources in the path-keyed cache.
    if (window._cachedJoinedIndex && window._cachedJoinedIndexPath === cacheKey) {
        rememberLyricsReleaseVocabulary(indexPath, window._cachedJoinedIndex);
        return window._cachedJoinedIndex;
    }
    if (joinedIndexCacheByPath.has(cacheKey)) {
        const cached = joinedIndexCacheByPath.get(cacheKey);
        window._cachedJoinedIndex = cached;
        window._cachedJoinedIndexPath = cacheKey;
        rememberLyricsReleaseVocabulary(indexPath, cached);
        return cached;
    }

    let data = null;
    if (!activeArtist && !window.playlistLiveActive?.()) {
        try {
            data = await loadColumnarIndex(effectiveConfig, indexPath);
        } catch (error) {
            console.warn('Columnar index unavailable, falling back to the monolith:', error);
            data = null;
        }
    }
    if (!data) {
        const response = await fetch(indexPath);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        trackDataFreshness(response);
        data = await response.json();
    }

    // Detect new master-based format and join if needed
    const masterPath = effectiveConfig.masterPath || langConfig?.masterPath;
    if (activeArtist && masterPath && data.length > 0 && data[0].sense_frequencies) {
        if (!window._cachedMasterVocab || window._cachedMasterVocabPath !== masterPath) {
            try {
                const masterResp = await fetch(masterPath);
                if (masterResp.ok) {
                    trackDataFreshness(masterResp);
                    window._cachedMasterVocab = await masterResp.json();
                    window._cachedMasterVocabPath = masterPath;
                }
            } catch (e) {
                console.warn('Failed to load master vocabulary:', e);
            }
        }
        if (window._cachedMasterVocab) {
            data = joinWithMaster(data, window._cachedMasterVocab);
        }
    }

    validateVocabularyIndex(data, { source: indexPath });

    window._cachedJoinedIndex = data;
    window._cachedJoinedIndexPath = cacheKey;
    joinedIndexCacheByPath.set(cacheKey, data);
    rememberLyricsReleaseVocabulary(indexPath, data);
    return data;
}

async function fetchDetachedIndex(langConfig) {
    const indexPath = langConfig?.indexPath || langConfig?.dataPath;
    if (!indexPath) throw new Error('No index path');
    const cacheKey = `${indexPath}:detached`;
    if (joinedIndexCacheByPath.has(cacheKey)) return joinedIndexCacheByPath.get(cacheKey);
    const response = await fetch(indexPath);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    trackDataFreshness(response);
    const data = await response.json();
    validateVocabularyIndex(data, { source: indexPath });
    joinedIndexCacheByPath.set(cacheKey, data);
    return data;
}

// Every route to a deck — setup counts, deck build, resume — passes through
// here, so this is the one place per-language cognate scores have to be
// attached. Loading is memoised per language config; a release without a
// cognates file simply attaches nothing and the deck keeps every word.
let _cognateScoresLoadedFor = null;
let _coverageLoadedFor = null;
let _cognateScoresLoading = null;
// Which path the in-flight load is for. Without it, a call for a second
// language joined whichever load happened to be running and then recorded that
// language's path as loaded, so the second language attached no scores while
// believing it had -- every word "not a cognate", and a Fast Track page that
// reported nothing to skip.
let _cognateScoresLoadingFor = null;

async function fetchActiveVocabularyData(langConfig) {
    const vocabulary = await fetchActiveVocabularyIndex(langConfig);
    // Switching to a language with no mapping must CLEAR the previous one, not
    // skip the loader and leave it in place. Scores are keyed by bare surface,
    // so a stale Czech map scored six Spanish words — a, to, je and friends
    // exist in both languages.
    const path = langConfig?.cognatesPath || null;
    if (_cognateScoresLoadedFor !== path && globalThis.loadCognateScores) {
        if (_cognateScoresLoadingFor !== path) {
            _cognateScoresLoadingFor = path;
            _cognateScoresLoading = Promise.resolve(globalThis.loadCognateScores(langConfig))
                .then(() => { _cognateScoresLoadedFor = path; })
                .finally(() => {
                    if (_cognateScoresLoadingFor === path) {
                        _cognateScoresLoadingFor = null;
                        _cognateScoresLoading = null;
                    }
                });
        }
        await _cognateScoresLoading;
    }
    // speechLang is the only language code the app config carries ("cs-CZ").
    const languageCode = String(langConfig?.speechLang || '').split('-')[0] || null;
    globalThis.applyCognateScores?.(vocabulary, languageCode);
    // Corpus shares are per-language and tiny; load them on the same pass so
    // the level readout has them before the first render.
    const coveragePath = langConfig?.coveragePath || null;
    if (_coverageLoadedFor !== coveragePath) {
        _coverageLoadedFor = coveragePath;
        await globalThis.loadCoverage?.(langConfig);
    }
    await stampContractions(vocabulary, langConfig);
    return vocabulary;
}

// A small per-language file carries what Merge Lemmas cannot read from a card
// whose senses have not loaded: the Wiktionary contractions (pt no = em + o),
// and each release card's merge key, computed from its full senses. A language
// without one keeps the old behaviour; stamps are cleared, never carried over
// from the previous language.
let _mergeExceptionsFor;
let _contractionSurfaces = null;
let _mergeKeys = null;

async function stampContractions(vocabulary, langConfig) {
    const path = langConfig?.mergeExceptionsPath || null;
    if (_mergeExceptionsFor !== path) {
        _mergeExceptionsFor = path;
        _contractionSurfaces = null;
        _mergeKeys = null;
        if (path) {
            try {
                const response = await fetch(path);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const payload = await response.json();
                _contractionSurfaces = new Set((payload?.contractions || []).map(normalizeLemmaToken));
                // The keys describe one release's senses; another release's
                // deck falls back to reading senses as they load.
                const built = payload?.release_id;
                const sameRelease = !built || [langConfig?.indexPath, langConfig?.releaseManifestPath]
                    .some(value => String(value || '').includes(`/${built}/`));
                _mergeKeys = (sameRelease && payload?.keys && typeof payload.keys === 'object') ? payload.keys : null;
                if (!sameRelease) console.warn(`Merge keys were built for ${built}; ignoring them for this release.`);
            } catch (error) {
                console.warn('Merge exceptions unavailable:', error);
            }
        }
    }
    if (!Array.isArray(vocabulary)) return;
    for (const item of vocabulary) {
        const surface = normalizeLemmaToken(item?.word);
        item.is_contraction = Boolean(_contractionSurfaces?.has(surface));
        const key = _mergeKeys?.[surface];
        if (typeof key === 'string') item.merge_key = key;
        else delete item.merge_key;
    }
}

async function fetchActiveVocabularyIndex(langConfig) {
    const selectedSlugs = window._selectedArtistSlugs || [];
    const allConfigs = window._allArtistsConfig;
    const effectiveConfig = (activeArtist && (activeArtist.language || 'spanish') === (langConfig?.language || selectedLanguage))
        ? { ...(langConfig || {}), ...activeArtist }
        : langConfig;
    if (!(activeArtist && selectedSlugs.length > 1 && allConfigs)) {
        const indexPath = effectiveConfig.indexPath || effectiveConfig.dataPath;
        const exactReleaseCache = window._lyricsReleaseVocabularyCache;
        const vocabulary = activeArtist?.releaseId
            && exactReleaseCache?.releaseId === activeArtist.releaseId
            && exactReleaseCache.indexPath === indexPath
            ? exactReleaseCache.data
            : await fetchAndJoinIndex(effectiveConfig);
        return window.filterActiveSongVocabulary?.(vocabulary) || vocabulary;
    }

    if (!window._cachedMasterVocab) {
        // The primary artist fetch also loads the shared master.
        await fetchAndJoinIndex(effectiveConfig);
    }
    if (!window._cachedMergedIndex) {
        const artistConfigs = selectedSlugs
            .map(slug => allConfigs[slug] ? { ...allConfigs[slug], slug } : null)
            .filter(Boolean);
        const { mergedIndex, mergedExamples } = await mergeArtistVocabularies(
            artistConfigs,
            window._cachedMasterVocab
        );
        window._cachedMergedIndex = mergedIndex;
        window._cachedMergedExamples = mergedExamples;
    }
    window.setActiveExamplesData?.(window._cachedMergedExamples, `artist-merge:${selectedSlugs.slice().sort().join(',')}`)
        || (window._cachedExamplesData = window._cachedMergedExamples);
    return window.filterActiveSongVocabulary?.(window._cachedMergedIndex) || window._cachedMergedIndex;
}

async function ensureLemmaPoolingData(langConfig) {
    await fetchActiveVocabularyData(langConfig);
    if (!langConfig?.examplesPath) return window._cachedExamplesData || null;
    if (window._cachedExamplesData && window._cachedExamplesDataPath === langConfig.examplesPath) {
        return window._cachedExamplesData;
    }
    try {
        if (await loadExampleShardManifest(langConfig)) {
            return window._cachedExamplesData || null;
        }
        return await loadMonolithExamples(langConfig);
    } catch (error) {
        console.warn('Failed to load examples for lemma pooling:', error);
        return null;
    }
}

// Assign a filter-independent frequency position to every teachable source
// entry. Optional settings may hide an entry or merge it into a lemma host,
// but they must never cause the remaining cards to migrate between levels or
// study sets. The source array position is the deterministic tie-breaker.
function artistLemmaEvidenceCount(item) {
    const stamped = Number(item?.lemma_example_count);
    if (Number.isFinite(stamped)) return Math.max(0, stamped);
    const fallback = Number(item?.corpus_count);
    return Number.isFinite(fallback) ? Math.max(0, fallback) : 0;
}

// Extra membership is by TAG, not frequency. Extra = anything the tagger
// classified as not-core-Spanish (loanword / English / proper noun / cognate /
// noise), plus unresolved routing abstentions. Everything else — including
// one-off real Spanish words like `alguna` / `adelante` — is core → Main only
// when the pipeline has positive lexical/morphological evidence. `single_occurrence` and the old
// `lemma_example_count <= 1` frequency rule are retired (a rare word is still
// real vocab; frequent loanwords like `baby` belong in Extra regardless of count).
const ARTIST_EXTRA_CATEGORIES = new Set(
    ['loanword', 'english', 'proper_noun', 'cognate', 'noise', 'unresolved']);
const ARTIST_MIN_SENSE_FREQ = 0.05;
function artistItemMatchesScope(item) {
    if (!activeArtist) return true;
    const cat = String(item?.extra_category || '').toLowerCase();
    // Backward-compatible fallback for old unstamped entries. New routing must
    // stamp uncertainty explicitly as `unresolved`; absence is not new proof
    // that a token is core Spanish.
    const isExtra = ARTIST_EXTRA_CATEGORIES.has(cat);
    return artistVocabularyScope === 'extra' ? isExtra : !isExtra;
}

// --- Artist Extra category grouping ---------------------------------------
// Extra vocabulary is supplementary and has no meaningful frequency ranking,
// so it is grouped by the pipeline-supplied `extra_category` string instead of
// frequency levels. The list of possible categories is intentionally NOT
// hardcoded: whatever distinct values the data carries are rendered, mapped to
// a readable label where known and title-cased otherwise. If no entry carries
// an `extra_category` yet, everything falls back to one "All Extra" group so
// the UI keeps working before the pipeline populates the field.
const EXTRA_CATEGORY_LABELS = {
    core: 'Core words',
    loanword: 'Loanwords',
    english: 'English words',
    cognate: 'Cognates',
    proper_noun: 'Names & places',
    propernoun: 'Names & places',
    proper_nouns: 'Names & places',
    slang: 'Slang & informal',
    single_occurrence: 'One-off words',
    interjection: 'Interjections',
    noise: 'Interjections & filler',
    onomatopoeia: 'Sound words',
    abbreviation: 'Abbreviations',
    unresolved: 'Needs classification',
    name: 'Names',
};
const EXTRA_CATEGORY_ALL_KEY = '__all_extra__';

function extraCategoryKeyOf(item) {
    const raw = item && typeof item.extra_category === 'string'
        ? item.extra_category.trim().toLowerCase()
        : '';
    return raw;
}

function extraCategoryLabelFor(key) {
    if (!key || key === EXTRA_CATEGORY_ALL_KEY) return 'All Extra';
    if (EXTRA_CATEGORY_LABELS[key]) return EXTRA_CATEGORY_LABELS[key];
    // Default: title-case the raw key, turning separators into spaces.
    return key
        .replace(/[_-]+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .replace(/\b\w/g, ch => ch.toUpperCase());
}

// Stamp a contiguous, category-blocked `categoryRank` on every Extra entry and
// return ordered group metadata the setup UI can turn into pickable groups.
// Each category occupies one continuous rank block; sets page through a block
// with the same STABLE_SET_SLOT machinery the frequency levels use. Order of
// items WITHIN a block is preserved from the incoming (frequency/pooled) sort
// so set membership is deterministic.
function assignExtraCategoryRanks(orderedVocab) {
    const groupsByKey = new Map();
    let anyCategory = false;
    for (const item of orderedVocab) {
        const key = extraCategoryKeyOf(item);
        if (key) anyCategory = true;
        const bucketKey = key || EXTRA_CATEGORY_ALL_KEY;
        if (!groupsByKey.has(bucketKey)) groupsByKey.set(bucketKey, []);
        groupsByKey.get(bucketKey).push(item);
    }

    // No entry carries a category yet → single "All Extra" group.
    let bucketEntries = Array.from(groupsByKey.entries());
    if (!anyCategory) {
        bucketEntries = [[EXTRA_CATEGORY_ALL_KEY, orderedVocab.slice()]];
    }

    // Deterministic group order: larger categories first, then by label. The
    // "All Extra" fallback always sits last if it somehow coexists with real
    // categories (e.g. some entries missing the field).
    bucketEntries.sort((a, b) => {
        const aAll = a[0] === EXTRA_CATEGORY_ALL_KEY;
        const bAll = b[0] === EXTRA_CATEGORY_ALL_KEY;
        if (aAll !== bAll) return aAll ? 1 : -1;
        const sizeDiff = b[1].length - a[1].length;
        if (sizeDiff !== 0) return sizeDiff;
        return extraCategoryLabelFor(a[0]).localeCompare(extraCategoryLabelFor(b[0]));
    });

    const groups = [];
    let cursor = 0;
    for (const [key, items] of bucketEntries) {
        if (items.length === 0) continue;
        const startRank = cursor + 1;
        for (const item of items) {
            cursor += 1;
            item.categoryRank = cursor;
            item.extraCategoryKey = key;
        }
        groups.push({
            key,
            label: extraCategoryLabelFor(key),
            startRank,
            endRank: cursor + 1, // exclusive, matches range-loader contract
            count: items.length,
        });
    }
    return groups;
}

// Ordered group metadata from the most recent Extra-scope buildFilteredVocab().
let _extraCategoryGroups = [];
const vocabularySourcesNeedingRestore = new WeakSet();
function getExtraCategoryGroups() {
    return _extraCategoryGroups.map(group => ({ ...group }));
}
window.getExtraCategoryGroups = getExtraCategoryGroups;

function _morphologyRows(item) {
    if (!item?.morphology) return [];
    return Array.isArray(item.morphology) ? item.morphology : [item.morphology];
}

function _foldSpanishForm(value) {
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/gu, '')
        .toLocaleLowerCase('es').trim();
}

function findSpuriousSelfInfinitives(vocabData) {
    const validConjugations = new Set();
    for (const item of vocabData) {
        const word = _foldSpanishForm(item?.word);
        const lemma = _foldSpanishForm(item?.lemma);
        if (!word || !lemma || word === lemma) continue;
        if (_morphologyRows(item).some(row => row?.mood && row.mood !== 'infinitivo')) {
            validConjugations.add(word);
        }
    }
    const rejected = new Set();
    for (const item of vocabData) {
        const word = _foldSpanishForm(item?.word);
        const lemma = _foldSpanishForm(item?.lemma);
        const hasVerb = (item?.meanings || []).some(meaning => meaning?.pos === 'VERB');
        const claimsInfinitive = _morphologyRows(item).some(row => row?.mood === 'infinitivo');
        const looksInfinitive = /(?:ar|er|ir)(?:se)?$/u.test(word);
        // Gap-fill senses can accidentally mint `quité|quité` beside the
        // authoritative `quité|quitar` analysis. Assembly then used to stamp
        // the self-lemma as an infinitive purely because word === lemma.
        // Suppress only when a valid same-surface conjugation is present.
        if (word && word === lemma && hasVerb && claimsInfinitive
            && !looksInfinitive && validConjugations.has(word)) {
            rejected.add(item);
        }
    }
    return rejected;
}

function assignStableVocabularyRanks(vocabData, spuriousSelfInfinitives = new Set()) {
    vocabData.forEach((item, index) => {
        item.rank = index + 1;
        if (item.cognate_score === undefined && item.is_transparent_cognate) {
            item.cognate_score = 1;
        }
    });
    const candidates = vocabData.filter(item => {
        if (!item.word || item.word.trim() === '' || item.duplicate || item.is_english
            || spuriousSelfInfinitives.has(item)) return false;
        if (!artistItemMatchesScope(item)) return false;
        // Skinny index columns ship with empty meanings until the study-set
        // row shard lands; those cards still hold their place in the order.
        const hasTranslation = item._indexRowsPending === true || (Array.isArray(item.meanings)
            && item.meanings.some(meaning => meaning.translation && meaning.translation.trim()));
        // Artist Extra deliberately includes raw lyric-only entries. A one-off
        // surface form inside a recurring lemma stays in Main and receives the
        // same fallback treatment, so it must also keep its stable slot.
        return hasTranslation || (activeArtist && (
            artistVocabularyScope === 'extra' || Number(item.corpus_count) <= 1
        ));
    });
    const hasCorpusFrequency = candidates.some(item => item.hasOwnProperty('corpus_count'));
    candidates.sort((a, b) => hasCorpusFrequency
        ? (((b.corpus_count || 0) - (a.corpus_count || 0)) || ((a.rank || 0) - (b.rank || 0)))
        : ((a.rank || 0) - (b.rank || 0)));
    candidates.forEach((item, index) => { item.stableRank = index + 1; });
    return candidates;
}

// Upstream artist indexes historically stamped the representative per build
// path, and a late-restored surface could leave two rows marked `true` for the
// same lemma (Bad Bunny's trepó + trepados is one shipped example). Elect the
// host from the entries that actually survived the current source/song/filter
// pass. The smallest stable rank is the highest-frequency available surface,
// with source rank as a deterministic final tie-breaker.
function selectLemmaModeRepresentatives(items) {
    const representativeByLemma = new Map();
    for (const item of items) {
        item._lemmaModeRepresentative = false;
        const lemmaKey = lemmaGroupKey(item);
        if (!lemmaKey) {
            item._lemmaModeRepresentative = true;
            continue;
        }
        const previous = representativeByLemma.get(lemmaKey);
        // The lemma's own spelling fronts the merged card whenever it is in
        // the deck (estar, not estaba), so the face does not move when a rule
        // keeps some other form apart.
        const itemIsLemma = normalizeLemmaToken(item.word) === lemmaKey;
        const previousIsLemma = previous ? normalizeLemmaToken(previous.word) === lemmaKey : false;
        if (previous && itemIsLemma !== previousIsLemma) {
            if (itemIsLemma) representativeByLemma.set(lemmaKey, item);
            continue;
        }
        const itemStable = Number.isFinite(item.stableRank) ? item.stableRank : Infinity;
        const previousStable = Number.isFinite(previous?.stableRank) ? previous.stableRank : Infinity;
        const itemRank = Number.isFinite(item.rank) ? item.rank : Infinity;
        const previousRank = Number.isFinite(previous?.rank) ? previous.rank : Infinity;
        if (!previous
            || itemStable < previousStable
            || (itemStable === previousStable && (item.corpus_count || 0) > (previous.corpus_count || 0))
            || (itemStable === previousStable
                && (item.corpus_count || 0) === (previous.corpus_count || 0)
                && itemRank < previousRank)) {
            representativeByLemma.set(lemmaKey, item);
        }
    }
    for (const representative of representativeByLemma.values()) {
        representative._lemmaModeRepresentative = true;
    }
    return items.filter(item => item._lemmaModeRepresentative === true);
}

// Each language the learner reads excludes on its own, at its own cutoff, so
// there is no single score to compare against a single threshold. cognates.js
// owns that decision; this falls back to the shipped scalar and the slider for
// decks that predate the per-language contract.
function isCognateAlreadyKnown(item) {
    const decide = globalThis.isCognateKnown;
    if (decide) return Boolean(decide(item));
    return Number(item?.cognate_score || 0) >= cognateThreshold;
}

function getVocabularyExclusionReason(item) {
    if (!item || !item.word || item.duplicate) return 'unavailable entry';
    const meanings = Array.isArray(item.meanings)
        ? item.meanings.filter(meaning => String(meaning?.translation || '').trim())
        : [];
    if (activeArtist) {
        if (!artistItemMatchesScope(item)) {
            return artistVocabularyScope === 'extra' ? 'main artist vocabulary' : 'Artist Extra';
        }
        if (item.is_english) return 'English-language item';
        if (excludeSlang && isSlangItem(item)) return 'slang or filler';
        if (excludeEnglishLoanwords && item.is_english_loanword) return 'English loanword';
        if (excludeProperNouns) {
            const allProperNoun = meanings.length > 0
                && meanings.every(meaning => meaning.pos === 'PROPN');
            if (item.is_propernoun || item.is_propernoun_corpus || allProperNoun) {
                return 'proper noun';
            }
        }
    }
    if (excludeCognates && isCognateAlreadyKnown(item)) {
        return 'cognate';
    }
    // Election happens at runtime in selectLemmaModeRepresentatives, over the
    // cards that actually survived this filter pass. The shipped
    // `most_frequent_lemma_instance` stamp is not consulted: it was elected
    // against a different card set and could mark two rows for one lemma.
    if (useLemmaMode && lemmaFieldAvailable && item._lemmaModeRepresentative === false) {
        return 'merged lemma form';
    }
    return null;
}

const GRAMMAR_FUNCTIONAL_POS = new Set(['PRON', 'DET', 'ADP', 'CCONJ', 'SCONJ', 'AUX', 'PART']);
const COMMON_SPANISH_FUNCTION_WORDS = new Set([
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'lo',
    'de', 'del', 'al', 'a', 'en', 'con', 'por', 'para', 'sin', 'sobre', 'hacia', 'desde', 'hasta', 'entre',
    'y', 'e', 'o', 'u', 'pero', 'mas', 'sino', 'aunque', 'que', 'si', 'como', 'porque',
    'yo', 'tu', 'tú', 'el', 'él', 'ella', 'nosotros', 'vosotros', 'ellos', 'ellas', 'usted', 'ustedes',
    'me', 'te', 'se', 'nos', 'os', 'le', 'les',
    'mi', 'mis', 'tu', 'tus', 'su', 'sus', 'nuestro', 'nuestra', 'nuestros', 'nuestras',
    'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella'
]);

function isGrammarParticleItem(item) {
    if (!item || !item.word) return false;
    if (item.is_clitic || item.clitic_form) return true;
    const cat = String(item.extra_category || '').toLowerCase();
    if (cat === 'grammar' || cat === 'particle' || cat === 'clitic') return true;
    const w = String(item.word).toLowerCase().trim();
    if (COMMON_SPANISH_FUNCTION_WORDS.has(w)) return true;
    if (Array.isArray(item.meanings) && item.meanings.length > 0) {
        if (item.meanings.some(m => Array.isArray(m.allClitics) && m.allClitics.length > 0)) return true;
        const allFunctional = item.meanings.every(m => {
            const pos = String(m.pos || '').toUpperCase();
            return GRAMMAR_FUNCTIONAL_POS.has(pos);
        });
        if (allFunctional) return true;
    }
    return false;
}

function isSlangItem(item) {
    if (!item) return false;
    if (item.is_noise || item.is_interjection) return true;
    const cat = String(item.extra_category || '').toLowerCase();
    if (cat === 'slang' || cat === 'noise' || cat === 'interjection') return true;
    // Every sense, not any: a word with one interjection or slang sense among
    // ordinary ones (sí, bueno, hombre) is a word to learn, not a filler.
    if (Array.isArray(item.meanings) && item.meanings.length > 0) {
        return item.meanings.every(m => {
            const pos = String(m.pos || '').toUpperCase();
            if (pos === 'INTJ' || pos === 'SLANG' || pos === 'FILLER') return true;
            const src = String(m.source || '').toLowerCase();
            if (src.includes('overlay:slang') || src.includes('overlay:conversational_filler') || src.includes('caribbean')) return true;
            if (Array.isArray(m.tags) && m.tags.some(t => /slang|colloquial|filler/i.test(t))) return true;
            const ctx = String(m.context || '').toLowerCase();
            if (ctx.includes('slang') || ctx.includes('colloquial') || ctx.includes('filler')) return true;
            return false;
        });
    }
    return false;
}

globalThis.isGrammarParticleItem = isGrammarParticleItem;
globalThis.isSlangItem = isSlangItem;

function buildFilteredVocab(vocabData) {
    // Deck construction attaches examples and prunes senses in place. Restore
    // the joined master template only after a deck actually mutated it.
    // Setup calls this function several times; cloning every sense tree on
    // every pass was one of the largest avoidable mobile allocations.
    if (vocabularySourcesNeedingRestore.has(vocabData)) {
        for (const item of vocabData) {
            if (Array.isArray(item._base_meanings)) {
                item.meanings = item._base_meanings.map(meaning => ({
                    ...meaning,
                    examples: (meaning.examples || []).map(example => ({ ...example })),
                }));
                if (Array.isArray(item._base_extra_raw_examples)) {
                    item.extra_raw_examples = item._base_extra_raw_examples.map(example => ({ ...example }));
                } else {
                    delete item.extra_raw_examples;
                }
            }
        }
        vocabularySourcesNeedingRestore.delete(vocabData);
    }
    const spuriousSelfInfinitives = findSpuriousSelfInfinitives(vocabData);
    // Assign stable rank from array position (pipeline sort order)
    const stableBaseline = assignStableVocabularyRanks(vocabData, spuriousSelfInfinitives);

    if (!cognateFieldAvailable && Array.isArray(vocabData)) {
        cognateFieldAvailable = vocabData.some(item =>
            (item.cognate_score > 0) || item.cognate_scores || item.cognate_sense_map || item.cognet_cognate || item.is_transparent_cognate
        );
    }
    if (!lemmaFieldAvailable && Array.isArray(vocabData)) {
        lemmaFieldAvailable = vocabData.some(item => lemmaGroupKey(item));
    }

    // Single-pass filter combining: basic validity → POS=X placeholder
    // strip → artist scope → artist-mode flags → cognates → lemma mode.
    // Order is preserved so counts reflect what the chained .filter() calls
    // used to produce (e.g. an item failing both artist and cognate is
    // counted under "english" only, since the artist check ran first).
    const counts = { english: 0, cognates: 0, singleOcc: 0, lemma: 0 };
    const hasCorpusFrequency = vocabData.length > 0
        && vocabData[0].hasOwnProperty('corpus_count');
    let result = [];
    for (const item of vocabData) {
        if (!item.word || item.word.trim() === '' || item.duplicate
            || spuriousSelfInfinitives.has(item)) continue;
        if (!artistItemMatchesScope(item)) {
            counts.singleOcc++;
            continue;
        }
        const allowsRawArtistCard = activeArtist && (
            artistVocabularyScope === 'extra' || Number(item.corpus_count) <= 1
        );
        // Skinny index columns ship with empty meanings until the study-set
        // row shard lands. Search hydrates one card; set setup must still
        // count these rows or every set looks empty.
        const rowsPending = item._indexRowsPending === true;
        if ((!item.meanings || item.meanings.length === 0) && !allowsRawArtistCard && !rowsPending) continue;
        // Strip any meaning with no translation (POS=X placeholders from
        // --no-gemini runs, plus SpanishDict rows that captured a usage label
        // but an empty gloss). Mutates the item, matching prior behavior.
        if (!rowsPending) {
            item.meanings = (item.meanings || []).filter(m => m.translation && m.translation.trim());
            if (item.meanings.length === 0 && !allowsRawArtistCard) continue;
        }
        // Artist Extra deliberately KEEPS the over-tagged words (English,
        // loanwords, proper nouns, noise) instead of dropping them, so they
        // surface grouped by their `extra_category` rather than vanishing.
        // Main scope is unchanged — it still drops them so it stays clean.
        const isExtraScope = activeArtist && artistVocabularyScope === 'extra';
        if (!isExtraScope) {
            // English borrowings — always filtered for artists (no toggle; they're not
            // Spanish words at all and have no Spanish meaning to teach).
            if (activeArtist && item.is_english) {
                counts.english++;
                continue;
            }
            // Slang, fillers and interjections: Smart Skip's switch alone decides.
            // The old always-on noise flag also caught every word with one
            // interjection sense (sí, bueno, claro), so they never reached a set.
            if (excludeSlang && isSlangItem(item)) {
                counts.english++;
                continue;
            }
            // Grammar particles & clitics
            if (excludeGrammarParticles && isGrammarParticleItem(item)) {
                counts.english++;
                continue;
            }
            // English loanwords / code-switches (hey, baby, shot, panty),
            // flagged from Wiktionary etymology. Toggleable via
            // excludeEnglishLoanwords in Advanced settings.
            if (activeArtist && excludeEnglishLoanwords && item.is_english_loanword) {
                counts.english++;
                continue;
            }
            // Proper nouns — three signals, any one is sufficient:
            //   1. `is_propernoun` — pipeline-stamped from step_4a curation
            //      (Wiktionary-only-name + manual proper_nouns.json drops).
            //   2. `is_propernoun_corpus` — corpus capitalization rate ≥
            //      threshold, stamped by tool_8a_stamp_propernoun_corpus.py.
            //      Catches frequent proper nouns Wiktionary/curation miss
            //      (Bunny, Mercedes, Dios, LeBron, …).
            //   3. Runtime POS=PROPN bridge — every meaning POS-tagged as
            //      PROPN by Gemini. Kept for backwards-compat with vocab
            //      builds that haven't been corpus-stamped yet.
            if (excludeProperNouns) {
                const allPropn = Array.isArray(item.meanings) && item.meanings.length > 0 && item.meanings.every(m => m.pos === 'PROPN');
                if (item.is_propernoun || item.is_propernoun_corpus || allPropn || item.extra_category === 'proper_noun' || item.extra_category === 'name') {
                    counts.english++;
                    continue;
                }
            }
            // Setup and deck construction must agree on whether an artist
            // card exists. Multi-occurrence rows with no assigned artist
            // sense are discarded later after examples attach; discard them
            // here too so they never appear as phantom new cards in a set.
            if (activeArtist) {
                const hasAssignedArtistSense = item.meanings.some(meaning =>
                    Number(meaning.frequency || 0) >= ARTIST_MIN_SENSE_FREQ);
                if (Number(item.corpus_count) > 1 && !hasAssignedArtistSense) {
                    counts.singleOcc++;
                    continue;
                }
            }
        }
        // Cognates: dropped in Main/normal per the toggle, but KEPT in Extra so
        // they populate the Cognates category (the toggle is hidden there and
        // only decides which group cognates land in, not deck inclusion).
        if (!isExtraScope && excludeCognates && cognateFieldAvailable && isCognateAlreadyKnown(item)) {
            counts.cognates++;
            continue;
        }
        result.push(item);
    }

    // Apply lemma collapsing only after every other inclusion rule. This
    // guarantees one host inside the active song/source subset even when the
    // pipeline's preferred surface is absent or conflicting flags are shipped.
    if (useLemmaMode && lemmaFieldAvailable) {
        const beforeLemmaMerge = result.length;
        result = selectLemmaModeRepresentatives(result);
        counts.lemma += beforeLemmaMerge - result.length;
    }

    // In lemma mode, pool each surviving representative's frequency across all
    // its collapsed sibling forms (same lemma) and order the deck by that total,
    // so the most common LEMMAS surface first — mirrors the example pooling in
    // poolLemmaSiblingExamples.
    if (useLemmaMode && lemmaFieldAvailable) {
        // A merged lemma lives wherever its highest-frequency surface form
        // lived in the baseline deck. This is the stable anchor that keeps
        // Merge Lemmas from moving the card to a different level or set.
        const lemmaStableRanks = new Map();
        for (const entry of vocabData) {
            const lemmaKey = lemmaGroupKey(entry);
            if (!lemmaKey || !Number.isFinite(entry.stableRank)) continue;
            const previous = lemmaStableRanks.get(lemmaKey);
            if (previous === undefined || entry.stableRank < previous) {
                lemmaStableRanks.set(lemmaKey, entry.stableRank);
            }
        }
        const lemmaTotals = new Map();
        for (const e of vocabData) {
            const lemmaKey = lemmaGroupKey(e);
            if (!lemmaKey || e.is_english || e.is_noise || e.is_interjection || e.duplicate) continue;
            lemmaTotals.set(lemmaKey, (lemmaTotals.get(lemmaKey) || 0) + (e.corpus_count || 0));
        }
        const exampleBasis = computeLemmaExampleCounts(vocabData, window._cachedExamplesData);
        for (const item of result) {
            const lemmaKey = lemmaGroupKey(item);
            item.stableRank = lemmaStableRanks.get(lemmaKey) || item.stableRank;
            item.lemma_total_count = lemmaTotals.get(lemmaKey) || item.corpus_count || 0;
            // The pipeline stamp includes raw one-off lyric evidence that may
            // intentionally have no assigned sense and therefore no `m`
            // bucket. Never erase it with the smaller assigned-example count.
            item.lemma_example_count = Math.max(
                artistLemmaEvidenceCount(item),
                exampleBasis.counts.get(lemmaKey) || 0
            );
            item.pooled_frequency = exampleBasis.hasExampleBasis
                ? item.lemma_example_count
                : item.lemma_total_count;
        }
        result.sort((a, b) => (b.pooled_frequency || 0) - (a.pooled_frequency || 0));
    } else if (percentageMode && hasCorpusFrequency) {
        // Artist indexes are usually frequency-sorted, but that is not a safe
        // contract (the current Young Miko index has dozens of upward jumps).
        // Percentage mode's scrubber and deck must share a genuinely
        // frequency-descending order. Preserve item.rank as the source ID and
        // use it as the stable tie-breaker.
        result.sort((a, b) =>
            ((b.corpus_count || 0) - (a.corpus_count || 0))
            || ((a.rank || 0) - (b.rank || 0)));
    }

    // Assign corpus-wide display ranks so set numbering is continuous across levels
    result.forEach((item, idx) => { item.displayRank = idx + 1; });

    // Artist Extra is grouped by category rather than frequency levels. Stamp
    // the contiguous per-category rank now so setup and deck-build slice on the
    // same basis. Main scope (and normal mode) leave categoryRank untouched.
    if (activeArtist && artistVocabularyScope === 'extra') {
        _extraCategoryGroups = assignExtraCategoryRanks(result);
    } else {
        _extraCategoryGroups = [];
    }

    return { vocab: result, counts, stableBaseline };
}

async function loadVocabularyData(rangeString, opts = {}) {
    const updateResumeLoading = detail => {
        if (!opts.resumeSnapshot) return;
        const element = document.getElementById('appLoadingDetail');
        if (element) element.textContent = detail;
    };
    // Keep the current deck intact until its replacement has been proved
    // usable. This matters most for end-of-set continuation: a stale queued
    // range can legitimately build zero cards after the last answer, and the
    // learner must not be stranded on the old final-card DOM with its backing
    // flashcards/stats already erased.
    const previousDeckState = {
        flashcards,
        stats,
        currentIndex,
        currentSentenceIndex,
        currentMeaningIndex,
        currentExampleIndex,
        currentMWEIndex,
        isFlipped,
        cardNavStack
    };
    const restorePreviousDeckState = () => {
        flashcards = previousDeckState.flashcards;
        stats = previousDeckState.stats;
        currentIndex = previousDeckState.currentIndex;
        currentSentenceIndex = previousDeckState.currentSentenceIndex;
        currentMeaningIndex = previousDeckState.currentMeaningIndex;
        currentExampleIndex = previousDeckState.currentExampleIndex;
        currentMWEIndex = previousDeckState.currentMWEIndex;
        isFlipped = previousDeckState.isFlipped;
        cardNavStack = previousDeckState.cardNavStack;
    };

    // Deck construction mutates the selected entries while attaching examples
    // and trimming artist senses. Force setup to rebuild its immutable view
    // when the learner returns to the menu.
    window.invalidatePreparedSetupVocabulary?.();
    const includeWordId = opts.includeWordId || null;
    let studyMode = opts.resumeSnapshot ? 'resume' : (opts.studyMode || 'new');
    // Completely clear all previous data and state
    flashcards = [];
    stats = {
        studied: new Set(),
        correct: 0,
        incorrect: 0,
        total: 0,
        cardStats: {},
        setSize: 0,
        previouslyKnown: 0,
        setLabel: '',
        rangeString: '',
        rangeBasis: opts.rankBasis || opts.resumeSnapshot?.rangeBasis || 'display',
        setNumber: opts.setNumber || opts.resumeSnapshot?.setNumber || null,
        levelSetCount: opts.levelSetCount || opts.resumeSnapshot?.levelSetCount || null,
        nextRange: null,
        nextSetNumber: null,
        nextRankBasis: 'display',
        studyMode,
        levelNumber: opts.levelNumber || opts.resumeSnapshot?.levelNumber || null,
        allWords: []
    };
    currentIndex = 0;
    currentSentenceIndex = 0;
    currentMeaningIndex = 0;
    currentExampleIndex = 0;
    currentMWEIndex = 0;
    isFlipped = false;
    cardNavStack = [];

    // Reset card flip state
    const flashcardEl = document.getElementById('flashcard');
    if (flashcardEl) {
        flashcardEl.classList.remove('flipped');
    }

    const baseConfig = config.languages[selectedLanguage] || {};
    const langConfig = activeArtist ? { ...baseConfig, ...activeArtist } : baseConfig;
    const [rangeStart, rangeEnd] = rangeString.split('-').map(Number);
    const rangeBasis = opts.rankBasis || opts.resumeSnapshot?.rangeBasis || 'display';

    // Use lightweight index for filtering when available
    const indexPath = langConfig.indexPath || langConfig.dataPath;

    try {
        // Single/multi-artist selection shares one source so setup ranges and
        // the committed deck see identical merged entries and examples.
        const vocabularyData = await fetchActiveVocabularyData(langConfig);
        const speechFrequency = await loadSpeechSourceFrequency(baseConfig);
        const lemmaSourceFrequencies = new Map();
        if (speechFrequency && useLemmaMode) {
            for (const entry of vocabularyData) {
                if (entry.is_english || entry.is_noise || entry.is_interjection || entry.duplicate) continue;
                const lemmaKey = lemmaGroupKey(entry);
                const value = speechSourceFrequencyOf(entry, speechFrequency);
                if (!lemmaKey || value === null) continue;
                // Keep the individual surfaces, not just how many there were.
                // "total across 5 source-listed forms" states a sum without
                // saying what went into it, and the sum is the one number on
                // this card a learner cannot check. Decision 0024 rule 4: the
                // published per-surface figures are what the card shows when
                // asked, because those are the only frequencies the source
                // actually publishes.
                const total = lemmaSourceFrequencies.get(lemmaKey) || { value: 0, forms: 0, breakdown: [] };
                total.value += value;
                total.forms += 1;
                total.breakdown.push({ surface: entry.word, value });
                lemmaSourceFrequencies.set(lemmaKey, total);
            }
        }
        updateResumeLoading('Matching the saved cards to this exact release…');
        // Derived from the data we already hold, so it costs nothing to keep
        // current on every deck build. It used to be recomputed only for
        // resume snapshots, which left it at its `false` default on any route
        // that skipped the setup panel (Continue set, direct deck start). A
        // false flag silently disables Merge Lemmas while the toggle still
        // reads "on": buildCardFormModel gets mergedLemma: false, so the card
        // keeps its surface form and the front falls through to the unmerged
        // variant list — every recorded spelling of the word.
        // A deck supports merging when its cards can be grouped at all. The old
        // test asked for `most_frequent_lemma_instance`, a pipeline-stamped
        // election this app re-does at runtime anyway, which made the feature
        // unavailable on every deck the current pipeline builds.
        lemmaFieldAvailable = vocabularyData.some(item => lemmaGroupKey(item));
        cognateFieldAvailable = vocabularyData.some(item =>
            (item.cognate_score > 0) || item.cognate_scores || item.cognate_sense_map || item.cognet_cognate || item.is_transparent_cognate
        );
        if (useLemmaMode) await ensureLemmaPoolingData(langConfig);
        cachedVocabularyData = vocabularyData;

        // Store original index/rank from vocabulary file - this is the unique identifier
        vocabularyData.forEach((item, index) => {
            item.rank = index + 1; // Use original position as the rank (unique identifier)
        });

        const { vocab: _baseVocab, counts: exCounts } = buildFilteredVocab(vocabularyData);
        let filteredData = window.applyPlaylistLiveVocabulary?.(_baseVocab) || _baseVocab;
        // This is the complete vocabulary after the active source + filter
        // configuration, before level, set, and mastery slicing. Card rank
        // metadata must use this same basis so it remains stable when the
        // active set is shuffled or previously-known cards are omitted.
        const configurationVocabSize = filteredData.length;
        const excludedEnglish = exCounts.english;
        const excludedCognates = exCounts.cognates;
        const excludedSingleOcc = exCounts.singleOcc;
        const excludedLemma = exCounts.lemma;
        let excludedMastered = 0;

        // Exact resume owns deck membership and order. This deliberately
        // bypasses the current mastery filter: a card answered just before
        // closing must still exist when the same session is continued. Match
        // IDs against the full configured vocabulary, not today's saved rank
        // range, because a refreshed corpus may move those cards across a
        // level boundary while their stable IDs remain valid.
        const resumeSnapshot = opts.resumeSnapshot || null;
        let totalInRange;
        let allInRange;
        if (Array.isArray(opts.fastTrackCards) && opts.fastTrackCards.length) {
            // Skipped Fast Track words are already excluded from the ordinary
            // filtered deck. Study them as their own set without re-applying
            // the cognate/lemma gates that set them aside.
            filteredData = opts.fastTrackCards.slice();
            totalInRange = filteredData.length;
            allInRange = filteredData.slice();
        } else if (opts.targetReviewWords) {
            // Instant fast path for daily review: target words are already pre-selected
            // and prioritized from user progress. Just extract them from vocabularyData.
            filteredData = filteredData.filter(item => {
                const itemId = getWordId(item);
                return (opts.targetReviewIds && (opts.targetReviewIds.has(itemId) || opts.targetReviewIds.has(item.id)))
                    || opts.targetReviewWords.has(String(item.word || '').toLowerCase());
            });
            if (Array.isArray(opts.targetReviewOrder)) {
                const orderMap = new Map(opts.targetReviewOrder.map((w, idx) => [w, idx]));
                filteredData.sort((a, b) => {
                    const aKey = String(a.word || '').toLowerCase();
                    const bKey = String(b.word || '').toLowerCase();
                    const aIdx = orderMap.has(aKey) ? orderMap.get(aKey) : 9999;
                    const bIdx = orderMap.has(bKey) ? orderMap.get(bKey) : 9999;
                    return aIdx - bIdx;
                });
            }
            if (opts.limit && opts.limit > 0 && filteredData.length > opts.limit) {
                filteredData = filteredData.slice(0, opts.limit);
            }
            totalInRange = opts.totalAvailableReview || filteredData.length;
            stats.totalAvailableReview = totalInRange;
            allInRange = filteredData.slice();
        } else if (resumeSnapshot?.order?.length) {
            const orderIndex = new Map(resumeSnapshot.order.map((id, index) => [id, index]));
            filteredData = filteredData
                .filter(item => orderIndex.has(getWordId(item)))
                .sort((a, b) => orderIndex.get(getWordId(a)) - orderIndex.get(getWordId(b)));
            totalInRange = resumeSnapshot.setSize || filteredData.length;
            allInRange = filteredData.slice();
        } else {
            // New stable sets slice on the pre-filter baseline rank. Legacy
            // sessions retain display-rank slicing so saved sessions remain
            // resumable across the UI migration.
            filteredData = filteredData.filter(item => {
                const rangeRank = rangeBasis === 'category' ? item.categoryRank
                    : rangeBasis === 'stable' ? item.stableRank
                    : rangeBasis === 'source' ? item.rank
                    : item.displayRank;
                return rangeRank >= rangeStart && rangeRank < rangeEnd;
            });
            totalInRange = filteredData.length;
            allInRange = filteredData.slice(); // preserve for "study anyway"

            // Ordinary set study contains genuinely unseen cards only. A
            // wrong or partial answer therefore advances the new-card track
            // and enters the separate review queue instead of trapping this
            // set as unfinished. Review is current-source/current-settings and
            // current-level scoped because _baseVocab and the range slice
            // have already established those boundaries.
            if (currentUser && !currentUser.isGuest && progressData) {
                const beforeFiltered = filteredData.length;
                const estimate = levelEstimates[selectedLanguage] || 0;
                const estimatedIds = activeArtist && studyMode === 'new'
                    ? await buildEstimatedKnownIds(estimate)
                    : null;
                const seenLemmas = studyMode === 'new'
                    ? await buildSeenLemmaSet(vocabularyData)
                    : new Set();

                filteredData = filteredData.filter(item => {
                    // Never filter out a word the caller explicitly asked to
                    // include (for example a search jump target).
                    const itemId = getWordId(item);
                    if (includeWordId && (itemId === includeWordId || item.id === includeWordId)) {
                        return true;
                    }
                    const hasRelatedProgress = hasRelatedWordProgress(itemId, item.word);
                    if (studyMode === 'review') return relatedWordNeedsReview(itemId, item.word);
                    if (studyMode === 'all') return true;

                    const coveredByEstimate = !hasRelatedProgress && (activeArtist
                        ? isCoveredByEstimatedIds(item, estimatedIds)
                        : item.rank <= estimate);
                    return !coveredByEstimate
                        && !hasRelatedProgress
                        && !seenLemmas.has(lemmaSeenKey(item));
                });
                excludedMastered = beforeFiltered - filteredData.length;
                if (studyMode === 'review') {
                    const reviewCache = new Map();
                    const getCachedReview = (item) => {
                        const key = getWordId(item) || item.word;
                        let rev = reviewCache.get(key);
                        if (!rev) {
                            rev = getWordKnowledgeReviewInfo(getWordId(item), item.word);
                            reviewCache.set(key, rev);
                        }
                        return rev;
                    };
                    if (opts.urgencyTier && opts.urgencyTier !== 'all') {
                        filteredData = filteredData.filter(item => {
                            const rev = getCachedReview(item);
                            if (opts.urgencyTier === 'never_right') return rev.urgencyTier === 'never_right';
                            if (opts.urgencyTier === 'critical') return rev.urgencyTier === 'critical';
                            if (opts.urgencyTier === 'due') return rev.urgencyTier === 'due' || rev.urgencyTier === 'upcoming';
                            return true;
                        });
                    }
                    filteredData.sort((a, b) => {
                        const aReview = getCachedReview(a);
                        const bReview = getCachedReview(b);
                        return ((bReview.needfulnessScore || 0) - (aReview.needfulnessScore || 0))
                            || ((a.displayRank || a.rank || 0) - (b.displayRank || b.rank || 0))
                            || ((aReview.reviewAt || 0) - (bReview.reviewAt || 0));
                    });
                    if (opts.limit && opts.limit > 0 && filteredData.length > opts.limit) {
                        stats.totalAvailableReview = filteredData.length;
                        filteredData = filteredData.slice(0, opts.limit);
                    }
                }
                if (excludedMastered > 0) {
                    console.log(`Filtered out ${excludedMastered} cards outside ${studyMode} mode`);
                }
            }
        }

        // Resolve an empty selection before attaching examples and building
        // cards. Progress can refresh between rendering a Learn New button and
        // tapping it; never turn that action into an implicit Study Again that
        // unexpectedly opens the complete set.
        if (filteredData.length === 0) {
            restorePreviousDeckState();
            document.getElementById('loadingMessage').style.display = 'none';
            // An empty selection is normally a progress race, not an error:
            // the setup count was rendered before a remote refresh or before
            // a related form was answered. Recount in place and let the user
            // choose the newly highlighted actionable set without a popup.
            if (!opts.silentIfEmpty) await window.refreshSetupAfterProgress?.();
            return false;
        }
        updateResumeLoading('Restoring examples and sense assignments…');

        // Everything below may attach examples, pool lemma siblings, or prune
        // the artist sense menu. The next setup/filter pass will restore the
        // canonical joined template once; repeated setup passes before then
        // remain allocation-free.
        if (vocabularyData.some(item => Array.isArray(item._base_meanings))) {
            vocabularySourcesNeedingRestore.add(vocabularyData);
        }

        // Convert to flashcards format
        const exampleTargetField = langConfig.exampleTargetField || 'example_spanish';
        const exampleEnglishField = langConfig.exampleEnglishField || 'example_english';

        // Load Spotify track mapping (fire-and-forget, non-blocking)
        if (!window._spotifyTracks) {
            const spotifyPath = activeArtist?.spotifyPath || 'Artists/spotify_tracks.json';
            fetch(spotifyPath).then(r => r.ok ? r.json() : {}).then(d => {
                window._spotifyTracks = d;
            }).catch(() => { window._spotifyTracks = {}; });
        }

        // Fat index rows belong to the cards in this set, not the
        // language-pick payload. Examples stay on the same study-set shards.
        const ranks = filteredData.map(item => Number(item.rank));
        if (!window.playlistLiveActive?.() && !activeArtist) {
            await ensureIndexRowsForRange(langConfig, rangeStart, rangeEnd, ranks);
        }
        filteredData = filteredData.filter(item => {
            if (window.playlistLiveActive?.()) return true;
            const allowsRawArtistCard = activeArtist && (
                artistVocabularyScope === 'extra' || Number(item.corpus_count) <= 1
            );
            if (item._indexRowsPending && !allowsRawArtistCard) return false;
            if (!allowsRawArtistCard) {
                item.meanings = (item.meanings || []).filter(m =>
                    m.translation && String(m.translation).trim()
                );
                return item.meanings.length > 0;
            }
            return true;
        });
        if (filteredData.length === 0) {
            restorePreviousDeckState();
            document.getElementById('loadingMessage').style.display = 'none';
            if (!opts.silentIfEmpty) await window.refreshSetupAfterProgress?.();
            return false;
        }
        let allCorpusExamples = [];
        if (langConfig.examplesPath && !window.playlistLiveActive?.()) {
            await ensureExamplesForRange(langConfig, rangeStart, rangeEnd, ranks);
            const examplesData = window._cachedExamplesData;
            if (examplesData) {
                // Merge examples back into filtered entries
                for (const item of filteredData) {
                    const ex = examplesData[item.id];
                    if (ex && ex.m && Array.isArray(item.meanings)) {
                        item.meanings.forEach((m, i) => {
                            // ex.m is indexed against the master sense order;
                            // honor the explicit source index so future sense
                            // filtering cannot make the arrays drift apart.
                            const bucket = m._masterSenseIndex ?? i;
                            m.examples = ex.m[bucket] || [];
                            reconcileMeaningProvenanceFromExamples(m, m.examples);
                        });
                    }
                    if (ex && ex.w && item.mwe_memberships) {
                        item.mwe_memberships.forEach((mwe, i) => {
                            mwe.examples = ex.w[i] || [];
                        });
                    }
                    if (ex && ex.c && item.clitic_memberships) {
                        item.clitic_memberships.forEach((clitic, i) => {
                            clitic.examples = ex.c[i] || [];
                        });
                    }
                    if (ex && ex.s && item.sense_cycles) {
                        item.sense_cycles.forEach((sc, i) => {
                            sc.examples = ex.s[i] || [];
                        });
                    }
                    if (ex) mergeArtistExtraSupport(item, ex);
                }
                // MWE examples are pre-computed by the pipeline and stored in the "w"
                // field of the examples file. No need to build a corpus pool here.
            }
        } else {
            // Fallback: monolith path — examples are inline in vocabularyData
        }
        updateResumeLoading('Rebuilding your saved card order…');

        // Lemma mode: dropped sibling forms contribute their example lines to
        // the surviving one-card-per-lemma card (deduped inside the helper).
        if (useLemmaMode && lemmaFieldAvailable) {
            poolLemmaSiblingExamples(filteredData, vocabularyData, window._cachedExamplesData);
        }

        // Artist mode: filter sense pills for cleaner display.
        // Must happen AFTER examples are attached (above) so positional indices are correct,
        // but BEFORE card building (below) so cards only show relevant senses.
        if (activeArtist) {
            const MAX_SENSES = 6;
            for (const item of filteredData) {
                const artistMeanings = item.meanings.filter(m =>
                    !m.shared_fallback && parseFloat(m.frequency) >= ARTIST_MIN_SENSE_FREQ);
                const supportedFallbacks = item.meanings.filter(m =>
                    m.shared_fallback && Array.isArray(m.examples) && m.examples.length > 0);
                if (artistVocabularyScope === 'extra') {
                    // Extra may have no artist-side assignment at all. Prefer
                    // shared senses that carry Speech evidence, then retain a
                    // small dictionary menu even when only the lyric exists.
                    item.meanings = artistMeanings.length > 0
                        ? artistMeanings
                        : (supportedFallbacks.length > 0
                            ? supportedFallbacks
                            : item.meanings.filter(m => m.translation).slice(0, MAX_SENSES));
                } else {
                    // Main normally retains the existing artist-assigned
                    // menu. A one-off surface form inside a recurring lemma
                    // is allowed to use its shared Speech support instead.
                    item.meanings = artistMeanings.length > 0
                        ? artistMeanings
                        : (Number(item.corpus_count) <= 1 ? supportedFallbacks : []);
                }
                // Hard cap: keep top N by frequency
                if (item.meanings.length > MAX_SENSES) {
                    item.meanings.sort((a, b) => parseFloat(b.frequency) - parseFloat(a.frequency));
                    item.meanings = item.meanings.slice(0, MAX_SENSES);
                }
            }
            filteredData = filteredData.filter(item =>
                item.meanings.length > 0
                || (item.extra_raw_examples?.length && (
                    artistVocabularyScope === 'extra' || Number(item.corpus_count) <= 1
                )));
        }

        for (const item of filteredData) {
            applyGrammarCardOverlay(item, selectedLanguage);
            item.meanings = item.meanings || [];
        }

        for (const item of filteredData) {
            const menuSource = useLemmaMode && lemmaHeadwordsOf(item).length === 1
                ? dedupeLemmaMenu(item.meanings)
                : item.meanings;
            const meanings = menuSource.map(m => {
                const { targetSentence, englishSentence, allExamples } = getExampleFromMeaning(m, exampleTargetField, exampleEnglishField);
                const meaning = {
                    pos: m.pos,
                    meaning: m.translation,
                    percentage: parseFloat(m.display_frequency ?? m.frequency),
                    targetSentence,
                    englishSentence,
                    allExamples
                };
                if (m.canonical_example) meaning.canonicalExample = m.canonical_example;
                if (m.unassigned) meaning.unassigned = true;
                if (m.assignment_method) meaning.assignment_method = m.assignment_method;
                if (m.prompt_id) meaning.prompt_id = m.prompt_id;
                if (m.run_ts) meaning.run_ts = m.run_ts;
                // Model confidence for the provenance panel. Rebuilt meanings
                // drop anything not explicitly copied here — the same trap that
                // silently lost assignment_method once already.
                if (m.confidence != null) meaning.confidence = m.confidence;
                if (m.band) meaning.band = m.band;
                if (m.model_proposed) meaning.modelProposed = true;
                if (m.source) meaning.source = m.source;
                if (m.sense_id || m.id) meaning.senseId = m.sense_id || m.id;
                if (m.sense_id_aliases?.length) meaning.senseIdAliases = m.sense_id_aliases;
                if (m.context) meaning.context = m.context;
                if (m.headword) meaning.headword = m.headword;
                if (m.source_reference) meaning.source_reference = m.source_reference;
                if (m.metadata) meaning.metadata = m.metadata;
                if (Array.isArray(m.regions) && m.regions.length) meaning.regions = [...m.regions];
                if (m.type) meaning.type = m.type;
                if (m.allSenses) meaning.allSenses = m.allSenses;
                if (m.cycle_pos) meaning.cycle_pos = m.cycle_pos;
                if (m.shared_fallback) meaning.sharedFallback = true;
                return meaning;
            });

            if (meanings.length === 0 && item.extra_raw_examples?.length) {
                const first = item.extra_raw_examples[0];
                meanings.push({
                    pos: 'EXAMPLE_ONLY',
                    meaning: '',
                    percentage: 1,
                    targetSentence: first.target || first.spanish || '',
                    englishSentence: first.english || '',
                    allExamples: item.extra_raw_examples,
                    exampleOnly: true,
                    unassigned: true,
                });
            }

            const finished = finishCardMeanings(item, meanings);
            meanings.splice(0, meanings.length, ...finished.meanings);

            // Synthesize a single MWE meaning that cycles through all expressions
            if (item.mwe_memberships && item.mwe_memberships.length > 0) {
                const allMWEs = [];
                // Sort artist-sourced MWEs first (including artist-curated /
                // artist-pmi tags from step_2a lyric counting), then shared
                // sources (spanishdict / wiktionary / legacy).
                const sortedMWEs = [...item.mwe_memberships].sort((a, b) => {
                    const aSrc = a.source || 'artist';
                    const bSrc = b.source || 'artist';
                    const aArtist = aSrc === 'artist' || aSrc.startsWith('artist-') ? 0 : 1;
                    const bArtist = bSrc === 'artist' || bSrc.startsWith('artist-') ? 0 : 1;
                    return aArtist - bArtist;
                });
                // Strip elision markers for fuzzy MWE matching
                const stripElisions = (s) => s.replace(/['\u2019]/g, '').replace(/\s+/g, ' ');
                for (const mwe of sortedMWEs) {
                    // Use pre-attached examples if available (from examples.json "w" field),
                    // only fall back to corpus scan when needed (artist mode)
                    let matched = mwe.examples || [];
                    if (matched.length === 0 && allCorpusExamples.length > 0) {
                        const exprLower = mwe.expression.toLowerCase();
                        const exprNorm = stripElisions(exprLower);
                        // Word-boundary regex to avoid substring false positives
                        // (e.g. "solo que" matching "solo quedan")
                        const SP = 'a-zA-Z\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00fc\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\u00dc';
                        const escExpr = exprLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const escNorm = exprNorm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const exprRe = new RegExp('(?<![' + SP + '])' + escExpr + '(?![' + SP + '])', 'i');
                        const normRe = new RegExp('(?<![' + SP + '])' + escNorm + '(?![' + SP + '])', 'i');
                        matched = allCorpusExamples.filter(ex => {
                            const text = (ex.spanish || ex.target || '').toLowerCase();
                            return exprRe.test(text);
                        });
                        if (matched.length === 0) {
                            matched = allCorpusExamples.filter(ex => {
                                const text = stripElisions((ex.spanish || ex.target || '').toLowerCase());
                                return normRe.test(text);
                            });
                        }
                    }
                    allMWEs.push({
                        id: mwe.id || null,
                        expression: mwe.expression,
                        translation: mwe.translation || '',
                        family: mwe.family || '',
                        variants: mwe.variants || null,
                        variantCounts: mwe.variant_counts || null,
                        corpusCount: Number(mwe.count) || 0,
                        occurrenceCount: Number(mwe.occurrence_count) || 0,
                        songCount: Number(mwe.num_songs) || 0,
                        // Two context tiers:
                        //   context           — real/scraped (authoritative)
                        //   context_heuristic — regex-split from quickdef
                        // Renderer prefers real over heuristic.
                        context: mwe.context || '',
                        context_heuristic: mwe.context_heuristic || '',
                        // Build-time provenance (wiktionary / spanishdict /
                        // artist-*). Empty for decks assembled before the
                        // stamp existed; the renderer shows no pill then.
                        source: mwe.source || '',
                        examples: matched.length > 0 ? matched : [{ spanish: '', english: '' }]
                    });
                }
                const firstEx = allMWEs[0].examples[0];
                meanings.push({
                    pos: 'MWE',
                    meaning: allMWEs[0].translation,
                    expression: allMWEs[0].expression,
                    allMWEs: allMWEs,
                    percentage: 0,
                    targetSentence: firstEx.spanish || firstEx.target || '',
                    englishSentence: firstEx.english || '',
                    allExamples: allMWEs[0].examples
                });
            }

            // Synthesize clitic meaning (parallel to MWE, cycles through forms)
            if (item.clitic_memberships && item.clitic_memberships.length > 0) {
                const allClitics = [];
                for (const cl of item.clitic_memberships) {
                    const matched = cl.examples || [];
                    allClitics.push({
                        form: cl.form,
                        translation: cl.translation || '',
                        corpus_count: cl.corpus_count || 0,
                        examples: matched
                    });
                }
                allClitics.sort((a, b) => b.corpus_count - a.corpus_count);
                const firstEx = allClitics[0].examples[0] || { spanish: '', english: '' };
                meanings.push({
                    pos: 'CLITIC',
                    meaning: allClitics[0].form,
                    allClitics: allClitics,
                    percentage: 0,
                    targetSentence: firstEx.spanish || firstEx.target || '',
                    englishSentence: firstEx.english || '',
                    allExamples: allClitics[0].examples
                });
            }

            // Synthesize SENSE_CYCLE meanings (unassigned senses grouped by POS)
            if (item.sense_cycles && item.sense_cycles.length > 0) {
                for (const sc of item.sense_cycles) {
                    const scExamples = sc.examples || [];
                    const firstEx = scExamples[0] || { spanish: '', english: '' };
                    const meaning = {
                        pos: sc.pos === 'SENSE_CYCLE' ? 'SENSE_CYCLE' : sc.pos,
                        meaning: sc.translation || '',
                        percentage: 0,
                        unassigned: true,
                        targetSentence: firstEx.spanish || firstEx.target || '',
                        englishSentence: firstEx.english || '',
                        allExamples: scExamples
                    };
                    if (sc.allSenses && sc.allSenses.length > 0) {
                        meaning.allSenses = sc.allSenses;
                        meaning.cycle_pos = sc.cycle_pos || sc.pos;
                    }
                    meanings.push(meaning);
                }
            }

            // Sort meanings: frequency senses first, then SENSE_CYCLE, CLITIC, MWE
            const specialOrder = { 'SENSE_CYCLE': 1, 'CLITIC': 2, 'MWE': 3 };
            meanings.sort((a, b) => {
                const aOrder = specialOrder[a.pos] || 0;
                const bOrder = specialOrder[b.pos] || 0;
                if (aOrder !== bOrder) return aOrder - bOrder;
                return (b.percentage || 0) - (a.percentage || 0);
            });

            const firstExample = meanings.length > 0
                ? {
                    targetSentence: meanings[0].targetSentence || '',
                    englishSentence: meanings[0].englishSentence || '',
                }
                : { targetSentence: '', englishSentence: '' };
            const cardForm = buildCardFormModel(item, meanings, {
                mergedLemma: useLemmaMode && lemmaFieldAvailable
            });
            // The totals are accumulated from the skinny index columns, whose
            // meanings are still empty (see the note at the `_indexRowsPending`
            // filter), so lemmaGroupKey keyed them by `lemma`. By the time a
            // card is built its row shard has landed and the same call returns
            // the assigned *headword*, which need not match — `mate` is
            // lemmatised `matar`. Try both rather than silently missing.
            const lemmaFallbackKey = String(item?.lemma || '')
                .normalize('NFC').toLocaleLowerCase('es').trim();
            const sourceFrequency = useLemmaMode && lemmaFieldAvailable
                ? (lemmaSourceFrequencies.get(lemmaGroupKey(item))
                    ?? (lemmaFallbackKey ? lemmaSourceFrequencies.get(lemmaFallbackKey) : undefined))
                : null;
            // The figure must describe the word printed on the card. A merged
            // card prints the citation form, so the group's sum put ~141 per
            // million under "unir" when the verb's own figure is 8.0 and most
            // of that sum is the adjective *unidos*. Decision 0024 rule 4:
            // only a published per-surface figure may be presented as this
            // word's frequency. Never fall back to the representative
            // surface's own value — that relabels one form's measurement with
            // another form's name, which is the defect being removed.
            //
            // 22% of merged citation forms (605 of 2,716 on es-v15) are absent
            // from the list — *estarse*, *tenerse*, rare infinitives. Their
            // group total is still worth showing, but it is labelled as the
            // family's rather than attributed to a form the source never
            // measured. Absence is declared, not filled.
            // Three bases, in order, and the card names which one it is
            // showing. There is no fourth: a card must never go blank because
            // its citation form happens to be unlisted — that regressed the
            // frequency off merged cards once already.
            const displayedOwnFrequency =
                speechSourceFrequencyForSurface(cardForm.displaySurface, speechFrequency);
            const groupFrequencyTotal = sourceFrequency?.value ?? null;
            const representativeFrequency = speechSourceFrequencyOf(item, speechFrequency);
            const frequencyBasis = displayedOwnFrequency !== null ? 'own'
                : groupFrequencyTotal !== null ? 'total'
                : representativeFrequency !== null ? 'other-surface'
                : 'none';
            const showsGroupTotal = frequencyBasis === 'total';
            const card = {
                targetWord: item.word,
                lemma: item.lemma || '',
                ...cardForm,
                id: item.id,
                fullId: getWordId(item),
                rank: item.rank,
                vocabularyRank: item.displayRank,
                vocabularySize: configurationVocabSize,
                sourceFrequency: displayedOwnFrequency ?? groupFrequencyTotal ?? representativeFrequency,
                sourceFrequencyGroupTotal: groupFrequencyTotal,
                sourceFrequencyIsGroupTotal: showsGroupTotal,
                sourceFrequencyBasis: frequencyBasis,
                // Named on the card when the figure belongs to a form other
                // than the one printed, so the number is never read as this
                // word's own measurement.
                sourceFrequencyBasisSurface: frequencyBasis === 'other-surface' ? item.word : '',
                sourceFrequencyForms: sourceFrequency?.forms || 1,
                // Commonest surface first: the breakdown is read to check a
                // total, and the form carrying most of it is the one worth
                // seeing. Unmerged cards carry their own single figure so the
                // tooltip has one code path.
                sourceFrequencyBreakdown: (sourceFrequency?.breakdown
                    ? [...sourceFrequency.breakdown].sort((a, b) => b.value - a.value)
                    : (() => {
                        const own = speechSourceFrequencyOf(item, speechFrequency);
                        return own === null ? [] : [{ surface: item.word, value: own }];
                    })()),
                sourceFrequencyUnit: speechFrequency?.unit || '',
                sourceFrequencySource: speechFrequency?.source || '',
                // Lemma mode uses the same unique pooled example-line basis
                // as the examples attached above. Raw token totals stay on
                // item.lemma_total_count for diagnostics only.
                corpusCount: artistVocabularyScope === 'extra'
                    ? (item.lemma_example_count || item.corpus_count || null)
                    : (useLemmaMode
                        ? (item.pooled_frequency ?? item.lemma_example_count ?? null)
                        : (item.corpus_count || null)),
                meanings: meanings,
                grammarPairs: item._grammarCard?.pairs || [],
                unusedMenuSenses: finished.unusedMenuSenses,
                translation: meanings[0]?.meaning || '',
                targetSentence: firstExample.targetSentence,
                englishSentence: firstExample.englishSentence,
                links: generateLinks(
                    cardForm.displaySurface || item.word,
                    cardForm.citationForm || item.lemma || item.word,
                    langConfig.referenceLinks
                ),
                isMultiMeaning: true,
                displayForm: item.display_form || null,
                variants: item.variants || null,
                homographIds: item.homograph_ids || null,
                morphology: item.morphology || null,
                synonyms: item.synonyms || null,
                antonyms: item.antonyms || null,
                // SpanishDict's morphological pointer (e.g. hay → haber).
                // Set when the word's semantic lemma is lexicalised but
                // SD also flags it as a conjugation of some verb. The
                // conjugation panel uses this as a fallback when the
                // card's own lemma has no inline paradigm.
                relatedLemma: item.related_lemma || null,
                derivationRelation: item.derivation_relation || null
            };
            // Retain routing diagnostics on the study card so a one-tap
            // classification report can state both the requested correction
            // and what the current pipeline actually stamped.
            card.is_english = item.is_english ?? null;
            card.is_english_loanword = item.is_english_loanword ?? null;
            card.cognate_score = item.cognate_score ?? null;
            card.cognate_scores = item.cognate_scores ?? null;
            card.translationUnavailable = meanings.every(meaning => !String(meaning.meaning || '').trim());
            card.artistVocabularyScope = activeArtist ? artistVocabularyScope : null;

            const splitPair = buildSplitCardPair(item, card, meanings);
            if (splitPair) {
                const [card1, card2] = splitPair;
                const deckCard1 = buildKnowledgeAwareCard(card1, {
                    skipWhenNothingToPractise: studyMode === 'review'
                });
                const deckCard2 = buildKnowledgeAwareCard(card2, {
                    skipWhenNothingToPractise: studyMode === 'review'
                });
                if (deckCard1) flashcards.push(deckCard1);
                if (deckCard2) flashcards.push(deckCard2);
            } else {
                // Sets and Review share one card shape: known senses greyed,
                // the rest fronted and answered. Review skips a word with
                // nothing left to practise.
                const deckCard = buildKnowledgeAwareCard(card, {
                    skipWhenNothingToPractise: studyMode === 'review'
                });
                if (deckCard) flashcards.push(deckCard);
            }
        }

        // A surface split into a companion pair is studied as exactly those
        // two cards. Card identity is the surface, so any other card for the
        // same surface in this deck (a duplicate item, a merged parent) would
        // read as a third card and is dropped.
        const splitSurfaces = new Set(flashcards
            .filter(c => c && c.splitInfo)
            .map(c => normalizeLemmaToken(c.targetWord)));
        if (splitSurfaces.size > 0) {
            for (let i = flashcards.length - 1; i >= 0; i--) {
                const c = flashcards[i];
                if (c && !c.splitInfo && splitSurfaces.has(normalizeLemmaToken(c.targetWord))) {
                    flashcards.splice(i, 1);
                }
            }
        }

        if (flashcards.length === 0) {
            // Report rather than dead-end. The auto-continue path passes
            // silentIfEmpty because it has somewhere else to go: a set that
            // looked incomplete when the dots were rendered can be finished by
            // the time the current set ends (lemma merging marks siblings seen
            // across sets), and alerting there stranded the learner on an
            // empty deck with the completion modal already dismissed.
            restorePreviousDeckState();
            document.getElementById('loadingMessage').style.display = 'none';
            if (!opts.silentIfEmpty) await window.refreshSetupAfterProgress?.();
            return false;
        }

        // New-card decks report how many cards in the stable set were already
        // seen. Review decks report the queue itself, not every card in the
        // containing level.
        stats.setSize = studyMode === 'review' ? flashcards.length : totalInRange;
        stats.previouslyKnown = studyMode === 'new' ? excludedMastered : 0;
        if (resumeSnapshot) {
            stats.setSize = resumeSnapshot.setSize || resumeSnapshot.order.length;
            stats.previouslyKnown = resumeSnapshot.previouslyKnown || 0;
        }
        stats.rangeString = rangeString;
        stats.rangeBasis = rangeBasis;
        stats.setNumber = opts.setNumber || resumeSnapshot?.setNumber || null;
        stats.levelSetCount = opts.levelSetCount || resumeSnapshot?.levelSetCount || null;
        stats.studyMode = resumeSnapshot?.studyMode || studyMode;
        stats.levelNumber = opts.levelNumber || resumeSnapshot?.levelNumber || stats.levelNumber || null;
        const nextSet = stats.studyMode === 'new' && window.getNextStudySetMeta
            ? window.getNextStudySetMeta(rangeString)
            : null;
        stats.nextRange = nextSet?.range || null;
        stats.nextSetNumber = nextSet?.setNumber || null;
        stats.nextRankBasis = nextSet?.rankBasis || rangeBasis;
        prefetchStudySetPayload(langConfig, stats.nextRange);
        // Inclusive label for display, e.g. "475-499" for rangeString "475-500"
        // (rangeEnd is exclusive in the filter above).
        const rankLabel = `${rangeStart}-${rangeEnd - 1}`;
        if (opts.setLabel) {
            stats.setLabel = opts.setLabel;
            stats.isFastTrack = Boolean(opts.isFastTrack);
        } else if (opts.isDailyReview) {
            const tierNames = {
                never_right: 'Never Mastered',
                critical: 'Critical Review',
                due: 'Routine Due',
                all: 'Daily Review'
            };
            const tierLabel = tierNames[opts.urgencyTier] || 'Daily Review';
            stats.setLabel = `${tierLabel} · ${flashcards.length} cards`;
            stats.isDailyReview = true;
            stats.dailyReviewTier = opts.urgencyTier || 'all';
            stats.dailyReviewLimit = opts.limit || 100;
            const remaining = (stats.totalAvailableReview || flashcards.length) - flashcards.length;
            stats.remainingDueCount = Math.max(0, remaining);
        } else {
            stats.setLabel = stats.studyMode === 'review'
                ? `Level ${stats.levelNumber || ''} review · ranks ${rankLabel}`.replace('Level  review', 'Level review')
                : stats.setNumber
                ? `Set ${stats.setNumber}${stats.levelSetCount ? `/${stats.levelSetCount}` : ''} · ranks ${rankLabel}`
                : rankLabel;
        }
        const statsWords = stats.studyMode === 'review' ? filteredData : allInRange;
        stats.allWords = statsWords.map(it => ({
            id: it.id,
            word: it.word,
            translation: (it.meanings && it.meanings[0] && it.meanings[0].translation) || '',
            displayRank: it.displayRank
        }));

        // Build exclusion summary message (only report in-range exclusions)
        const totalExcluded = excludedLemma + (studyMode === 'new' ? excludedMastered : 0);
        const loadingMsg = document.getElementById('loadingMessage');
        if (totalExcluded > 0) {
            const parts = [];
            if (excludedLemma > 0) parts.push(`${excludedLemma} lemma dup${excludedLemma > 1 ? 's' : ''}`);
            if (studyMode === 'new' && excludedMastered > 0) parts.push(`${excludedMastered} already seen`);
            loadingMsg.textContent = `✓ ${flashcards.length} cards from ${totalInRange} (${parts.join(', ')} excluded)`;
        } else {
            loadingMsg.textContent = `✓ ${flashcards.length} cards`;
        }
        loadingMsg.style.display = 'block';

        // Swap the completed deck into view immediately. Callers that need a
        // transition keep the app-level loading screen above this atomic DOM
        // update, so the previous card never flashes between sets.
        // Race a timeout: requestAnimationFrame never fires while the tab is
        // hidden, so starting a set and switching away left this awaiting
        // forever with the deck half-swapped and the loading screen up.
        await new Promise(resolve => {
            requestAnimationFrame(resolve);
            setTimeout(resolve, 50);
        });
        updateResumeLoading('Opening the card where you stopped…');
        document.getElementById('setupPanel').classList.add('hidden');
        document.getElementById('appContent').classList.remove('hidden');
        loadingMsg.style.display = 'none';

        // Show mobile floating buttons
        showFloatingBtns(true);

        if (resumeSnapshot) {
            let resumeIndex = flashcards.findIndex(card => card.fullId === resumeSnapshot.currentFullId);
            if (resumeIndex < 0 && Number.isFinite(Number(resumeSnapshot.currentVocabularyRank))) {
                const targetRank = Number(resumeSnapshot.currentVocabularyRank);
                resumeIndex = flashcards.reduce((best, card, index) => {
                    const distance = Math.abs(Number(card.vocabularyRank || card.rank) - targetRank);
                    return distance < best.distance ? { index, distance } : best;
                }, { index: 0, distance: Infinity }).index;
            }
            currentIndex = Math.max(0, resumeIndex);
            const resumedCard = flashcards[currentIndex];
            const maxMeaningIndex = Math.max(0, (resumedCard?.meanings?.length || 1) - 1);
            currentMeaningIndex = Math.min(
                maxMeaningIndex,
                Math.max(0, resumeSnapshot.currentMeaningIndex || 0)
            );
            currentExampleIndex = Math.max(0, resumeSnapshot.currentExampleIndex || 0);
            currentMWEIndex = Math.max(0, resumeSnapshot.currentMWEIndex || 0);
            isFlipped = !!resumeSnapshot.directionFlipped;
            if (typeof resumeSnapshot.speechEnabled === 'boolean') {
                speechEnabled = resumeSnapshot.speechEnabled;
            }
        }

        // Initialize card display
        initializeApp();
        window.updateSpeakIcons?.();
        if (resumeSnapshot?.cardFaceFlipped) flashcardEl?.classList.add('flipped');
        else flashcardEl?.classList.remove('flipped');
        saveStudySessionSnapshot();
        buildWordLookupMap();
        return true;
    } catch (error) {
        restorePreviousDeckState();
        console.error(`Failed to load vocabulary data:`, error);
        document.getElementById('loadingMessage').style.display = 'none';
        const detail = error instanceof Error && error.message
            ? `\n\n${error.message}`
            : '';
        alert(`This deck could not be loaded.${detail}`);
        return false;
    }
}

// Build a lookup map from word/lemma → flashcard index for lyric breakdown
function buildWordLookupMap() {
    const map = new Map();
    for (let i = 0; i < flashcards.length; i++) {
        const card = flashcards[i];
        const word = card.targetWord.toLowerCase().trim();
        if (!map.has(word)) map.set(word, i);
        if (card.lemma) {
            const lemma = card.lemma.toLowerCase().trim();
            if (!map.has(lemma)) map.set(lemma, i);
        }
    }
    window._wordLookupMap = map;
}


// Build the unresolved-mistake queue from the active vocabulary and the
// selected level. The ordinary loader owns source/settings filtering and card
// construction, keeping review behavior identical to Learn new.
async function loadLevelReviewSet(rangeString, opts = {}) {
    if (!currentUser || currentUser.isGuest) {
        alert('Please log in to review previous mistakes.');
        return;
    }
    return loadVocabularyData(rangeString, {
        ...opts,
        studyMode: 'review',
        setNumber: null,
        levelSetCount: null
    });
}

// Global level-agnostic review deck across all due words in the language
async function loadDailyReviewDeck(opts = {}) {
    if (!currentUser || currentUser.isGuest) {
        alert('Please log in to review due cards.');
        return false;
    }
    const summary = window.getGlobalDueReviewSummary?.(selectedLanguage) || { all: [], neverRight: [], critical: [], due: [] };
    const tier = opts.urgencyTier || 'all';
    let pool = summary.all;
    if (tier === 'never_right') pool = summary.neverRight;
    else if (tier === 'critical') pool = summary.critical;
    else if (tier === 'due') pool = summary.due;

    if (!pool || pool.length === 0) {
        alert('No cards are ready to practise in this queue.');
        return false;
    }

    const limit = opts.limit !== undefined ? opts.limit : 100;
    const targetSlice = pool.slice(0, limit);
    const targetIds = new Set(targetSlice.map(w => w.id));
    const targetWords = new Set(targetSlice.map(w => String(w.word || '').toLowerCase()));
    const totalAvailableReview = pool.length;

    return loadVocabularyData('1-50000', {
        ...opts,
        studyMode: 'review',
        rankBasis: 'source',
        setNumber: null,
        levelSetCount: null,
        limit,
        urgencyTier: tier,
        isDailyReview: true,
        targetReviewIds: targetIds,
        targetReviewWords: targetWords,
        targetReviewOrder: targetSlice.map(w => String(w.word || '').toLowerCase()),
        totalAvailableReview
    });
}

// Truncate text to a maximum number of words, adding ellipsis if truncated
function truncateText(text, maxWords) {
    if (!text) return '';
    const words = text.split(/\s+/);
    if (words.length <= maxWords) return text;
    return words.slice(0, maxWords).join(' ') + '...';
}

function cleanValue(value) {
    return value ? value.replace(/^"|"$/g, '').trim() : '';
}

function generateLinks(word, lemma, linkTemplates) {
    const cleanWord = encodeURIComponent(lemma || word);
    const links = {};

    for (const [key, template] of Object.entries(linkTemplates)) {
        links[key] = template.replace('{word}', cleanWord);
    }

    return links;
}

// Dictionary illustrations live on meaning.canonical_example. They must never
// be merged into corpus ticks: they are not WSD observations and must not
// enter frequency, hardness, or commonness. The helpers below remain only so
// older decks that still nest provider example lists can be read at the UI
// boundary without counting those lists as usage.
function referenceExamplesForMeaning(meaning) {
    const senses = [meaning, ...(Array.isArray(meaning?.allSenses) ? meaning.allSenses : [])];
    const examples = [];
    for (const sense of senses) {
        const metadata = sense?.metadata?.sense_provider_metadata || {};
        const spanishDict = metadata?.spanishdict?.examples;
        if (Array.isArray(spanishDict)) {
            for (const example of spanishDict) {
                const target = String(example?.original || '').trim();
                const english = String(example?.translated || '').trim();
                if (target) examples.push({
                    target,
                    english,
                    source: 'spanishdict',
                    source_mode: 'reference',
                    reference_example: true,
                });
            }
        }
        if (Array.isArray(metadata?.examples)) {
            for (const example of metadata.examples) {
                const target = String(example?.text || '').trim();
                const english = String(example?.english || example?.translation || '').trim();
                if (target) examples.push({
                    target,
                    english,
                    source: 'wiktionary',
                    source_mode: 'reference',
                    reference_example: true,
                    reference: String(example?.ref || '').trim() || undefined,
                });
            }
        }
    }
    return examples;
}

function mergeReferenceExamples(corpusExamples, meaning) {
    const merged = [...corpusExamples, ...referenceExamplesForMeaning(meaning)];
    const seen = new Set();
    return merged.filter(example => {
        const key = `${String(example?.target || example?.spanish || '').trim()}\u0000${String(example?.english || '').trim()}`;
        if (!key.replace('\u0000', '') || seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

// Helper to extract example sentences from a meaning object
// Supports new format (examples array) and legacy format (exampleTargetField/exampleEnglishField)
function getExampleFromMeaning(meaning, exampleTargetField, exampleEnglishField) {
    // Check for new examples array format
    if (meaning.examples && meaning.examples.length > 0) {
        const example = meaning.examples[0];
        // Support both 'target'/'english' and language-specific keys like 'spanish'/'english'
        const targetSentence = example.target || example.spanish || example.swedish ||
                               example.dutch || example.finnish || example.italian || example.polish || '';
        const englishSentence = example.english || '';
        return { targetSentence, englishSentence, allExamples: meaning.examples };
    }
    // Fall back to legacy format
    return {
        targetSentence: meaning[exampleTargetField] || '',
        englishSentence: meaning[exampleEnglishField] || '',
        allExamples: []
    };
}


// Merge vocabulary arrays from multiple artists by hex ID.
// With master vocab: IDs are guaranteed consistent, so merge is straightforward.
// Without master: falls back to legacy POS+translation union (backwards compat).
// Returns { mergedIndex: [...], mergedExamples: {...} }
async function mergeArtistVocabularies(artistConfigs, master) {
    const byId = new Map(); // id → merged entry
    const mergedExamples = {}; // id → { m: [...], w: [...] }
    const combinedLemmaCounts = new Map();

    for (const cfg of artistConfigs) {
        // Load lightweight index for word metadata
        const indexPath = cfg.indexPath || cfg.dataPath;
        let indexData;
        try {
            const resp = await fetch(indexPath);
            trackDataFreshness(resp);
            indexData = await resp.json();
        } catch (e) {
            console.warn(`Failed to load index for ${cfg.name}:`, e);
            continue;
        }

        // If master available and data is new format, join first
        const isNewFormat = indexData.length > 0 && indexData[0].sense_frequencies;
        if (master && isNewFormat) {
            indexData = joinWithMaster(indexData, master);
        }

        // Every surface entry in an artist carries the same pooled count for
        // its lemma. Add that count once per artist, not once per form.
        const thisArtistLemmaCounts = new Map();
        for (const entry of indexData) {
            if (!entry.lemma) continue;
            thisArtistLemmaCounts.set(
                entry.lemma,
                Math.max(
                    thisArtistLemmaCounts.get(entry.lemma) || 0,
                    artistLemmaEvidenceCount(entry)
                )
            );
        }
        for (const [lemma, count] of thisArtistLemmaCounts) {
            combinedLemmaCounts.set(lemma, (combinedLemmaCounts.get(lemma) || 0) + count);
        }

        // Load separate examples file
        let examplesData = null;
        if (cfg.examplesPath) {
            try {
                const resp = await fetch(cfg.examplesPath);
                trackDataFreshness(resp);
                examplesData = await resp.json();
            } catch (e) {
                console.warn(`Failed to load examples for ${cfg.name}:`, e);
            }
        }

        for (const entry of indexData) {
            const id = entry.id;
            if (!id) continue;

            // Tag examples with artist slug
            const tagExamples = (examples) => {
                if (!examples) return [];
                return examples.map(ex => ({ ...ex, artist: cfg.slug }));
            };

            // Attach examples from split file onto meanings BEFORE merge,
            // so examples travel with their meaning
            if (examplesData && examplesData[id] && entry.meanings) {
                const ex = examplesData[id];
                if (ex.m) {
                    entry.meanings.forEach((m, i) => {
                        const bucket = m._masterSenseIndex ?? i;
                        m.examples = ex.m[bucket] || [];
                        reconcileMeaningProvenanceFromExamples(m, m.examples);
                    });
                }
                if (ex.w && entry.mwe_memberships) {
                    entry.mwe_memberships.forEach((mwe, i) => {
                        mwe.examples = ex.w[i] || [];
                    });
                }
                if (ex.c && entry.clitic_memberships) {
                    entry.clitic_memberships.forEach((cl, i) => {
                        cl.examples = ex.c[i] || [];
                    });
                }
                if (ex.s && entry.sense_cycles) {
                    entry.sense_cycles.forEach((sc, i) => {
                        sc.examples = ex.s[i] || [];
                    });
                }
                mergeArtistExtraSupport(entry, ex);
            }

            if (byId.has(id)) {
                // Merge into an existing entry. Master-based senses retain
                // their stable source index across artists.
                const existing = byId.get(id);
                existing.corpus_count = (existing.corpus_count || 0) + (entry.corpus_count || 0);

                if (master && isNewFormat) {
                    // Merge on the preserved master-sense index rather than
                    // trusting whatever filtering a caller may later apply.
                    if (entry.meanings) {
                        const byMasterSense = new Map(existing.meanings.map((m, i) => [m._masterSenseIndex ?? i, m]));
                        entry.meanings.forEach((newM, i) => {
                            const masterSenseIndex = newM._masterSenseIndex ?? i;
                            const existingM = byMasterSense.get(masterSenseIndex);
                            if (existingM) {
                                existingM.examples = (existingM.examples || []).concat(tagExamples(newM.examples || []));
                                // Any assigned observation outweighs an
                                // unassigned bucket from another artist.
                                if (!newM.unassigned) delete existingM.unassigned;
                                if (!existingM.assignment_method && newM.assignment_method) {
                                    existingM.assignment_method = newM.assignment_method;
                                }
                                // Register tags come from the shared master, so
                                // whichever artist carries one is authoritative.
                                if (!existingM.type && newM.type) existingM.type = newM.type;
                                // Carry provenance from whichever artist first
                                // classified this shared master sense.
                                if (!existingM.prompt_id && newM.prompt_id) {
                                    existingM.prompt_id = newM.prompt_id;
                                    if (newM.run_ts) existingM.run_ts = newM.run_ts;
                                }
                                if (newM.model_proposed) existingM.model_proposed = true;
                            } else {
                                const added = structuredClone(newM);
                                added.examples = tagExamples(added.examples || []);
                                existing.meanings.push(added);
                                byMasterSense.set(masterSenseIndex, added);
                            }
                        });
                        existing.meanings.sort((a, b) =>
                            (a._masterSenseIndex ?? 0) - (b._masterSenseIndex ?? 0));
                    }
                } else {
                    // Legacy merge: union by POS+translation
                    const existingHasAnalysis = existing.meanings.some(m => m.pos !== 'X' && m.translation);
                    const newHasAnalysis = entry.meanings && entry.meanings.some(m => m.pos !== 'X' && m.translation);

                    if (entry.meanings) {
                        if (!existingHasAnalysis && newHasAnalysis) {
                            existing.meanings = entry.meanings.map(m => {
                                const tagged = { ...m };
                                if (tagged.examples) tagged.examples = tagExamples(tagged.examples);
                                return tagged;
                            });
                        } else if (existingHasAnalysis && !newHasAnalysis) {
                            // skip
                        } else {
                            for (const newM of entry.meanings) {
                                const existingM = existing.meanings.find(m => m.pos === newM.pos && m.translation === newM.translation);
                                if (existingM) {
                                    if (newM.examples) {
                                        existingM.examples = (existingM.examples || []).concat(tagExamples(newM.examples));
                                    }
                                } else {
                                    const tagged = { ...newM };
                                    if (tagged.examples) tagged.examples = tagExamples(tagged.examples);
                                    existing.meanings.push(tagged);
                                }
                            }
                        }
                    }
                }
                if (entry.extra_raw_examples?.length) {
                    existing.extra_raw_examples = (existing.extra_raw_examples || [])
                        .concat(tagExamples(entry.extra_raw_examples));
                }
                if (entry.mwe_memberships?.length) {
                    const existingByExpression = new Map((existing.mwe_memberships || [])
                        .map(mwe => [String(mwe.id || mwe.expression || '').toLocaleLowerCase('es'), mwe]));
                    for (const incoming of entry.mwe_memberships) {
                        const key = String(incoming.id || incoming.expression || '').toLocaleLowerCase('es');
                        const current = existingByExpression.get(key);
                        if (current) {
                            current.examples = (current.examples || [])
                                .concat(tagExamples(incoming.examples || []));
                        } else {
                            const added = structuredClone(incoming);
                            added.examples = tagExamples(added.examples || []);
                            if (!existing.mwe_memberships) existing.mwe_memberships = [];
                            existing.mwe_memberships.push(added);
                            existingByExpression.set(key, added);
                        }
                    }
                }
                if (entry.clitic_memberships?.length) {
                    const existingByForm = new Map((existing.clitic_memberships || [])
                        .map(clitic => [String(clitic.form || '').toLocaleLowerCase('es'), clitic]));
                    for (const incoming of entry.clitic_memberships) {
                        const key = String(incoming.form || '').toLocaleLowerCase('es');
                        const current = existingByForm.get(key);
                        if (current) {
                            current.corpus_count = Number(current.corpus_count || 0)
                                + Number(incoming.corpus_count || 0);
                            current.examples = (current.examples || [])
                                .concat(tagExamples(incoming.examples || []));
                        } else {
                            const added = structuredClone(incoming);
                            added.examples = tagExamples(added.examples || []);
                            if (!existing.clitic_memberships) existing.clitic_memberships = [];
                            existing.clitic_memberships.push(added);
                            existingByForm.set(key, added);
                        }
                    }
                }
                if (entry.sense_cycles?.length) {
                    const existingBySense = new Map((existing.sense_cycles || [])
                        .map(cycle => [`${cycle.pos || ''}\u0000${cycle.translation || ''}`, cycle]));
                    for (const incoming of entry.sense_cycles) {
                        const key = `${incoming.pos || ''}\u0000${incoming.translation || ''}`;
                        const current = existingBySense.get(key);
                        if (current) {
                            current.examples = (current.examples || [])
                                .concat(tagExamples(incoming.examples || []));
                        } else {
                            const added = structuredClone(incoming);
                            added.examples = tagExamples(added.examples || []);
                            if (!existing.sense_cycles) existing.sense_cycles = [];
                            existing.sense_cycles.push(added);
                            existingBySense.set(key, added);
                        }
                    }
                }
            } else {
                // First time seeing this word — clone and tag.
                // structuredClone is the native deep-clone primitive; ~2-3×
                // faster than JSON round-trip on the entry shapes here and
                // doesn't lose `undefined` values or non-JSON types.
                const clone = structuredClone(entry);
                if (clone.meanings) {
                    for (const m of clone.meanings) {
                        if (m.examples) m.examples = tagExamples(m.examples);
                    }
                }
                if (clone.extra_raw_examples) {
                    clone.extra_raw_examples = tagExamples(clone.extra_raw_examples);
                }
                for (const mwe of (clone.mwe_memberships || [])) {
                    mwe.examples = tagExamples(mwe.examples || []);
                }
                for (const clitic of (clone.clitic_memberships || [])) {
                    clitic.examples = tagExamples(clitic.examples || []);
                }
                for (const cycle of (clone.sense_cycles || [])) {
                    cycle.examples = tagExamples(cycle.examples || []);
                }
                byId.set(id, clone);
            }

        }
    }

    // Recalculate sense frequency from the same unique example lines the UI
    // cycles through. This also removes duplicate cross-artist/collab lines.
    for (const entry of byId.values()) {
        entry.lemma_example_count = combinedLemmaCounts.get(entry.lemma)
            || entry.lemma_example_count
            || entry.corpus_count
            || 0;
        for (const meaning of (entry.meanings || [])) {
            const seen = new Set();
            meaning.examples = (meaning.examples || []).filter(example => {
                const key = exampleSentenceKey(example);
                if (!key || seen.has(key)) return false;
                seen.add(key);
                return true;
            });
        }
        if (entry.extra_raw_examples?.length) {
            const seen = new Set();
            entry.extra_raw_examples = entry.extra_raw_examples.filter(example => {
                const key = exampleSentenceKey(example);
                if (!key || seen.has(key)) return false;
                seen.add(key);
                return true;
            });
        }
        for (const clitic of (entry.clitic_memberships || [])) {
            const seen = new Set();
            clitic.examples = (clitic.examples || []).filter(example => {
                const key = exampleSentenceKey(example);
                if (!key || seen.has(key)) return false;
                seen.add(key);
                return true;
            });
        }
        for (const membership of [
            ...(entry.mwe_memberships || []),
            ...(entry.sense_cycles || [])
        ]) {
            const seen = new Set();
            membership.examples = (membership.examples || []).filter(example => {
                const key = exampleSentenceKey(example);
                if (!key || seen.has(key)) return false;
                seen.add(key);
                return true;
            });
        }
        if (entry.meanings && entry.meanings.length > 1) {
            const counts = entry.meanings.map(m => (m.examples || []).length);
            const total = counts.reduce((a, b) => a + b, 0);
            if (total > 0) {
                entry.meanings.forEach((m, i) => {
                    m.frequency = (counts[i] / total).toFixed(2);
                });
            }
        }
        entry._base_meanings = (entry.meanings || []).map(meaning => ({
            ...meaning,
            examples: (meaning.examples || []).map(example => ({ ...example })),
        }));
        entry._base_extra_raw_examples = entry.extra_raw_examples?.map(example => ({ ...example }));
    }

    // Per-artist representative flags are incompatible after union: two
    // artists can choose different surface forms for the same lemma. Stamp
    // exactly one combined-corpus representative per lemma.
    const representativeByLemma = new Map();
    for (const entry of byId.values()) {
        if (!entry.lemma) continue;
        entry.most_frequent_lemma_instance = false;
        const previous = representativeByLemma.get(entry.lemma);
        if (!previous || (entry.corpus_count || 0) > (previous.corpus_count || 0)) {
            representativeByLemma.set(entry.lemma, entry);
        }
    }
    for (const representative of representativeByLemma.values()) {
        representative.most_frequent_lemma_instance = true;
    }

    // Rebuild split-example buckets only after every artist has merged.
    // Master-format buckets stay keyed by _masterSenseIndex, including holes.
    for (const [id, merged] of byId) {
        mergedExamples[id] = { m: [] };
        (merged.meanings || []).forEach((meaning, i) => {
            const bucket = meaning._masterSenseIndex ?? i;
            mergedExamples[id].m[bucket] = meaning.examples || [];
        });
        if (merged.mwe_memberships) {
            mergedExamples[id].w = [];
            merged.mwe_memberships.forEach((mwe, i) => {
                mergedExamples[id].w[i] = mwe.examples || [];
            });
        }
        if (merged.clitic_memberships) {
            mergedExamples[id].c = [];
            merged.clitic_memberships.forEach((clitic, i) => {
                mergedExamples[id].c[i] = clitic.examples || [];
            });
        }
        if (merged.sense_cycles) {
            mergedExamples[id].s = [];
            merged.sense_cycles.forEach((cycle, i) => {
                mergedExamples[id].s[i] = cycle.examples || [];
            });
        }
        if (merged.extra_raw_examples?.length) {
            mergedExamples[id].r = merged.extra_raw_examples;
        }
    }

    // Sort by combined corpus_count descending
    const mergedIndex = Array.from(byId.values()).sort((a, b) => (b.corpus_count || 0) - (a.corpus_count || 0));

    return { mergedIndex, mergedExamples };
}

// Synthesize MWE / CLITIC / SENSE_CYCLE meanings on a card's meanings array.
// Mirrors the inline blocks in loadVocabularyData (line 484+) and
// Review and ordinary decks both consume the assembled membership examples.
// (and the sense_cycles equivalents) are already populated by the caller —
// no corpus-scan fallback. Used by the popup/temp-card paths in
// flashcards.js (popupFoundWord, navigateToVocabCard) which previously
// skipped this synthesis entirely, hiding all MWEs (including curated ones)
// on cards reached via search or click-through.
// low-share-pure
// A sense needs this share of the card's assigned sentences to sit on the
// main card; below it, it moves to Rarer uses with its sentences. With ~30
// assigned sentences per card that is three: a sense resting on one or two is
// as often a WSD slip as a real use (que "how", from a single "that" line).
// The bar is per subsense row: estuve "I was (to fit)" rested on one
// misread "estuve pensando" while its "I was" siblings held 35% between them.
// Function words keep pooling by translation; their grouping is curated.
const MAIN_CARD_MIN_SHARE = 0.10;
const NON_SENSE_POS = new Set(['PHRASE', 'MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY']);

function normalizeMeaningShares(meanings) {
    const total = meanings.reduce((sum, m) => sum + (m.percentage || 0), 0);
    if (total === 0 || isNaN(total)) {
        meanings.forEach(m => { m.percentage = 1.0 / meanings.length; });
    } else if (total !== 1.0) {
        meanings.forEach(m => { m.percentage = (m.percentage || 0) / total; });
    }
    return meanings;
}

const POOLED_FLOOR_POS = /^(?:adp|prep|preposition|det|determiner|article|pron|pronoun|cconj|sconj|conj|conjunction|part|particle)$/i;

function splitLowShareMeanings(meanings) {
    const eligible = m => m && !m.unassigned && !m.exampleOnly
        && !NON_SENSE_POS.has(String(m.pos || '').toUpperCase()) && Number(m.percentage) > 0;
    const fold = values => values.map(v => String(v || '').trim().toLocaleLowerCase('en')).join('\u0000');
    const poolKey = m => fold([m.pos, m.headword, m.meaning]);
    // A SpanishDict context is one meaning however many English words it
    // lists (kilo / kilogram), so it is measured whole, as the card shows it.
    const key = m => (POOLED_FLOOR_POS.test(String(m.pos || '')) ? poolKey(m)
        : m.source === 'spanishdict' && m.context ? fold([m.pos, m.headword, '', m.context])
        : fold([m.pos, m.headword, m.meaning, m.context]));
    const shares = new Map();
    for (const m of meanings) {
        if (eligible(m)) shares.set(key(m), (shares.get(key(m)) || 0) + Number(m.percentage));
    }
    // Shares are ratios of small counts: 3 of 30 arrives as 0.0999…, and three
    // sentences is exactly the bar.
    const below = m => eligible(m) && shares.get(key(m)) < MAIN_CARD_MIN_SHARE - 1e-9;
    // A translation whose rows clear the bar together keeps its largest row.
    const byPool = new Map();
    for (const m of meanings) if (eligible(m)) byPool.set(poolKey(m), [...(byPool.get(poolKey(m)) || []), m]);
    const rescued = new Set();
    for (const rows of byPool.values()) {
        const total = rows.reduce((sum, m) => sum + Number(m.percentage), 0);
        if (total >= MAIN_CARD_MIN_SHARE - 1e-9 && rows.every(below)) {
            rescued.add(rows.reduce((a, b) => (Number(b.percentage) > Number(a.percentage) ? b : a)));
        }
    }
    const low = m => below(m) && !rescued.has(m);
    const kept = meanings.filter(m => !low(m));
    // Never leave a card without a sense of its own on the front.
    if (!kept.some(eligible)) return { meanings, rare: [] };
    return { meanings: kept, rare: meanings.filter(low).map(m => ({ ...m, lowShare: true })) };
}

function unusedMenuSensesOf(item) {
    return (item?.unused_menu_senses || []).map(m => ({
        pos: m.pos,
        meaning: m.translation || '',
        percentage: 0,
        unassigned: true,
        assignment_method: m.assignment_method || 'unassigned',
        source: m.source || '',
        senseId: m.sense_id || '',
        context: m.context || '',
        headword: m.headword || '',
        regions: Array.isArray(m.regions) ? [...m.regions] : [],
        metadata: m.metadata || null,
        canonicalExample: m.canonical_example || null,
        allExamples: [],
    }));
}

// Commonness is read against the senses a learner can see: everything except
// expressions, which are studied on their own card. Rarer senses stay in the
// base, so moving one to Rarer uses never inflates the rest. `percentage`
// keeps the share of all assigned sentences; `shownShare` is the label's.
function isShownSense(m, item) {
    return !NON_SENSE_POS.has(String(m.pos || '').toUpperCase())
        && !globalThis.isExpressionSenseForLemma?.(m, item);
}

function stampShownShares(item, meanings) {
    const isSense = m => isShownSense(m, item);
    const base = meanings.filter(isSense).reduce((sum, m) => sum + (Number(m.percentage) || 0), 0);
    if (base <= 0) return meanings;
    return meanings.map(m => (isSense(m) ? { ...m, shownShare: (Number(m.percentage) || 0) / base } : m));
}

// A split card shows one reading of its surface, so its shares are read
// against that reading alone: its own senses plus its own rarer senses. The
// sibling card's senses are not part of what this card shows. When a reading
// is all expressions (vamos = "let's go"), those are what it shows.
function stampSplitShownShares(item, meanings, rare) {
    const pool = meanings.some(m => isShownSense(m, item))
        ? meanings.filter(m => isShownSense(m, item))
        : meanings;
    const base = [...pool, ...rare].reduce((sum, m) => sum + (Number(m.percentage) || 0), 0);
    if (base <= 0) return meanings;
    return meanings.map(m => (pool.includes(m) ? { ...m, shownShare: (Number(m.percentage) || 0) / base } : m));
}

// The last step every card builder shares: shares over the card's assigned
// sentences, then low-share senses moved beside the unused menu senses.
function finishCardMeanings(item, meanings) {
    const shares = stampShownShares(item, normalizeMeaningShares(meanings));
    const { meanings: kept, rare } = splitLowShareMeanings(shares);
    return { meanings: kept, unusedMenuSenses: [...rare, ...unusedMenuSensesOf(item)] };
}
// /low-share-pure
window.finishCardMeanings = finishCardMeanings;

function synthesizeSpecialMeanings(item, meanings) {
    if (item.mwe_memberships && item.mwe_memberships.length > 0) {
        const sortedMWEs = [...item.mwe_memberships].sort((a, b) => {
            const aSrc = a.source || 'artist';
            const bSrc = b.source || 'artist';
            const aArtist = aSrc === 'artist' || aSrc.startsWith('artist-') ? 0 : 1;
            const bArtist = bSrc === 'artist' || bSrc.startsWith('artist-') ? 0 : 1;
            return aArtist - bArtist;
        });
        const allMWEs = sortedMWEs.map(mwe => {
            const matched = mwe.examples || [];
            return {
                id: mwe.id || null,
                expression: mwe.expression,
                translation: mwe.translation || '',
                family: mwe.family || '',
                variants: mwe.variants || null,
                variantCounts: mwe.variant_counts || null,
                corpusCount: Number(mwe.count) || 0,
                occurrenceCount: Number(mwe.occurrence_count) || 0,
                songCount: Number(mwe.num_songs) || 0,
                context: mwe.context || '',
                context_heuristic: mwe.context_heuristic || '',
                source: mwe.source || '',
                examples: matched.length > 0 ? matched : [{ spanish: '', english: '' }],
            };
        });
        const firstEx = allMWEs[0].examples[0];
        meanings.push({
            pos: 'MWE',
            meaning: allMWEs[0].translation,
            expression: allMWEs[0].expression,
            allMWEs,
            percentage: 0,
            targetSentence: firstEx.spanish || firstEx.target || '',
            englishSentence: firstEx.english || '',
            allExamples: allMWEs[0].examples,
        });
    }
    if (item.clitic_memberships && item.clitic_memberships.length > 0) {
        const allClitics = item.clitic_memberships.map(cl => {
            const matched = cl.examples || [];
            return {
                form: cl.form,
                translation: cl.translation || '',
                corpus_count: cl.corpus_count || 0,
                examples: matched,
            };
        });
        allClitics.sort((a, b) => b.corpus_count - a.corpus_count);
        const firstEx = allClitics[0].examples[0] || { spanish: '', english: '' };
        meanings.push({
            pos: 'CLITIC',
            meaning: allClitics[0].form,
            allClitics,
            percentage: 0,
            targetSentence: firstEx.spanish || firstEx.target || '',
            englishSentence: firstEx.english || '',
            allExamples: allClitics[0].examples,
        });
    }
    if (item.sense_cycles && item.sense_cycles.length > 0) {
        for (const sc of item.sense_cycles) {
            const scExamples = sc.examples || [];
            const firstEx = scExamples[0] || { spanish: '', english: '' };
            const meaning = {
                pos: sc.pos === 'SENSE_CYCLE' ? 'SENSE_CYCLE' : sc.pos,
                meaning: sc.translation || '',
                percentage: 0,
                unassigned: true,
                targetSentence: firstEx.spanish || firstEx.target || '',
                englishSentence: firstEx.english || '',
                allExamples: scExamples,
            };
            if (sc.allSenses && sc.allSenses.length > 0) {
                meaning.allSenses = sc.allSenses;
                meaning.cycle_pos = sc.cycle_pos || sc.pos;
            }
            meanings.push(meaning);
        }
    }
    const order = { 'SENSE_CYCLE': 1, 'CLITIC': 2, 'MWE': 3 };
    meanings.sort((a, b) => {
        const aOrd = order[a.pos] || 0;
        const bOrd = order[b.pos] || 0;
        if (aOrd !== bOrd) return aOrd - bOrd;
        return (b.percentage || 0) - (a.percentage || 0);
    });
}

window.synthesizeSpecialMeanings = synthesizeSpecialMeanings;
window.buildCardFormModel = buildCardFormModel;
window.mergeArtistVocabularies = mergeArtistVocabularies;
window.joinWithMaster = joinWithMaster;
window.fetchAndJoinIndex = fetchAndJoinIndex;
window.fetchActiveVocabularyData = fetchActiveVocabularyData;
window.ensureLemmaPoolingData = ensureLemmaPoolingData;
window.getWordId = getWordId;
window.getCrossModeId = getCrossModeId;
window.isWordKnown = isWordKnown;
window.buildEstimatedKnownIds = buildEstimatedKnownIds;
window.isCoveredByEstimatedIds = isCoveredByEstimatedIds;
window.buildSeenLemmaSet = buildSeenLemmaSet;
window.LANG_CODES = LANG_CODES;
window.buildFilteredVocab = buildFilteredVocab;
window.assignStableVocabularyRanks = assignStableVocabularyRanks;
window.findSpuriousSelfInfinitives = findSpuriousSelfInfinitives;
window.loadVocabularyData = loadVocabularyData;
window.ensureExamplesForRange = ensureExamplesForRange;
window.ensureIndexRowsForRange = ensureIndexRowsForRange;
window.prefetchStudySetPayload = prefetchStudySetPayload;
window.exampleShardsActive = () => exampleShardsActive;
window.renderResumeLastSetCard = renderResumeLastSetCard;
window.resumeLastStudySession = resumeLastStudySession;
window.saveStudySessionSnapshot = saveStudySessionSnapshot;
window.clearStudySessionSnapshot = clearStudySessionSnapshot;
window.loadLevelReviewSet = loadLevelReviewSet;
window.loadDailyReviewDeck = loadDailyReviewDeck;
window.truncateText = truncateText;
window.cleanValue = cleanValue;
window.generateLinks = generateLinks;
window.getExampleFromMeaning = getExampleFromMeaning;
window.getVocabularyExclusionReason = getVocabularyExclusionReason;
window.buildWordLookupMap = buildWordLookupMap;
window.detectSplitCardTuples = detectSplitCardTuples;

// Extras reports the forms merging absorbed, and must group them exactly as
// the filter did. Exporting the rule keeps one definition of it.
globalThis.lemmaGroupKey = lemmaGroupKey;
globalThis.lemmaSeenKey = lemmaSeenKey;
globalThis.lemmaHeadwordsOf = lemmaHeadwordsOf;
