import './state.js?v=20260825ak';
import {
    crossModeProgressId,
    matchingProgressRecords,
    mergeProgressRecords,
    normalizeProgressSurface
} from './progress-identity.js?v=20260831a';

const SRS_DAY_MS = 24 * 60 * 60 * 1000;
const SRS_INTERVAL_DAYS = [1, 3, 7, 14, 30, 60, 120, 240, 365];

function parseProgressTimestamp(value) {
    if (!value) return 0;
    const timestamp = new Date(value).getTime();
    return Number.isFinite(timestamp) ? timestamp : 0;
}

// Adaptive schedule: successful recalls graduate through intervals [1..365] days,
// fine-tuned by the learner's personal error rate on the card.
// Explicit stages are preserved; legacy rows derive an initial stage from lifetime totals.
function getSrsStage(progress) {
    const explicit = Number(progress?.srsStage);
    if (progress?.srsStage !== null && progress?.srsStage !== ''
            && Number.isFinite(explicit) && explicit >= 0) {
        return Math.min(Math.floor(explicit), SRS_INTERVAL_DAYS.length);
    }
    const correct = Math.max(0, Number(progress?.correct) || 0);
    const wrong = Math.max(0, Number(progress?.wrong) || 0);
    if (correct === 0) return 0;
    return Math.min(Math.max(1, correct - wrong), SRS_INTERVAL_DAYS.length);
}

function getSrsIntervalDays(progress) {
    const stage = getSrsStage(progress);
    if (stage <= 0) return null;
    const baseDays = SRS_INTERVAL_DAYS[stage - 1];
    const correct = Math.max(0, Number(progress?.correct) || 0);
    const wrong = Math.max(0, Number(progress?.wrong) || 0);
    if (correct + wrong === 0) return baseDays;
    const failRate = wrong / (correct + wrong);
    // Personal multiplier: scales between 0.75x (frequent errors) and 1.25x (clean recall)
    const factor = Math.max(0.75, Math.min(1.25, 1.25 - (failRate * 0.55)));
    return Math.max(1, Math.round(baseDays * factor));
}

function advanceSrsStage(progress, isCorrect) {
    const current = getSrsStage(progress);
    if (!isCorrect) {
        // Soft drop: drop 2 stages instead of a hard reset to 0. A never-learned card stays at 0.
        if (current === 0) return 0;
        return Math.max(1, current - 2);
    }
    return Math.min(current + 1, SRS_INTERVAL_DAYS.length);
}

// The learner's current relationship with a card. Counts preserve history;
// timestamps decide the latest outcome and whether a resolved card is due.
// Older rows can lack timestamps, so a recorded correct is treated as current
// until a dated answer establishes a review schedule.
function getProgressState(progress, now = Date.now()) {
    const correct = Math.max(0, Number(progress?.correct) || 0);
    const wrong = Math.max(0, Number(progress?.wrong) || 0);
    const lastCorrect = parseProgressTimestamp(progress?.lastCorrect);
    const lastWrong = parseProgressTimestamp(progress?.lastWrong);
    const lastSeen = parseProgressTimestamp(progress?.lastSeen);
    const seen = correct > 0 || wrong > 0 || lastCorrect > 0 || lastWrong > 0 || lastSeen > 0;

    if (!seen) {
        return {
            status: 'unseen', seen: false, needsReview: false, learned: false,
            known: false, isDue: false, reviewReason: null, intervalDays: null,
            nextReviewAt: 0, reviewAt: 0, lastCorrect, lastWrong, lastSeen
        };
    }

    let needsReview = false;
    if (wrong > 0 || lastWrong > 0) {
        if (lastWrong > 0 || lastCorrect > 0) {
            needsReview = lastWrong > lastCorrect;
        } else {
            // Legacy count-only rows cannot reveal answer order. A card that
            // was never correct is unresolved; any recorded correct resolves
            // it until a newer dated wrong arrives.
            needsReview = correct === 0;
        }
    }

    const unresolved = needsReview;
    const intervalDays = !unresolved && lastCorrect > 0
        ? getSrsIntervalDays(progress)
        : null;
    const nextReviewAt = intervalDays ? lastCorrect + intervalDays * SRS_DAY_MS : 0;
    const nowTime = Number.isFinite(Number(now)) ? Number(now) : Date.now();
    // The schedule can be paused while the app/content are under active
    // development. Pausing suppresses only time-based due status: explicit
    // mistakes still need review, and stages/timestamps remain intact so the
    // same schedule resumes when the learner turns it back on.
    const scheduleEnabled = typeof spacedRepetitionEnabled === 'undefined'
        ? true
        : spacedRepetitionEnabled;
    const isDue = scheduleEnabled && !unresolved && nextReviewAt > 0 && nowTime >= nextReviewAt;
    needsReview = unresolved || isDue;

    let urgencyTier = null;
    let needfulnessScore = 0;
    let overdueRatio = 0;

    if (needsReview) {
        if (correct === 0 && (wrong > 0 || lastWrong > 0 || unresolved)) {
            // Level 1: Never right. Zero lifetime correct answers; maximum urgency.
            urgencyTier = 'never_right';
            needfulnessScore = 1000 + Math.min(200, wrong * 20);
        } else if (unresolved) {
            // Level 2a: Recent mistake on a previously known card.
            urgencyTier = 'critical';
            needfulnessScore = 700 + Math.min(200, wrong * 10);
        } else if (isDue) {
            const intervalMs = (intervalDays || 1) * SRS_DAY_MS;
            const overdueMs = Math.max(0, nowTime - nextReviewAt);
            overdueRatio = intervalMs > 0 ? (overdueMs / intervalMs) : 0;
            if (overdueRatio >= 2.0) {
                // Level 2b: Severely overdue (2x or more past interval). High decay risk.
                urgencyTier = 'critical';
                needfulnessScore = 500 + Math.min(190, overdueRatio * 25);
            } else if (overdueRatio >= 1.0) {
                // Level 3: Overdue by 1-2 intervals.
                urgencyTier = 'due';
                needfulnessScore = 200 + Math.min(290, overdueRatio * 100);
            } else {
                // Level 4: Due today.
                urgencyTier = 'due';
                needfulnessScore = 100 + Math.min(99, overdueRatio * 100);
            }
        }
    }

    return {
        status: needsReview ? 'review' : 'learned',
        seen: true,
        needsReview,
        learned: !needsReview,
        // `known` preserves coverage after a card becomes due; `learned`
        // means currently up to date and drives the green/amber set state.
        known: !unresolved && correct > 0,
        isDue,
        reviewReason: unresolved ? 'incorrect' : (isDue ? 'due' : null),
        intervalDays,
        nextReviewAt,
        reviewAt: unresolved ? (lastWrong || lastSeen) : (isDue ? nextReviewAt : 0),
        urgencyTier,
        needfulnessScore,
        overdueRatio,
        lastCorrect,
        lastWrong,
        lastSeen
    };
}

const progressSurfaceById = new Map();
let indexedProgressSource = null;
let indexedProgressSize = -1;
let progressIdsBySurface = new Map();

function registerProgressCardSurface(fullId, surface) {
    const normalized = normalizeProgressSurface(surface);
    if (fullId && normalized) progressSurfaceById.set(fullId, normalized);
    return fullId;
}

function getProgressRecordsForCard(fullId, surface = '') {
    const source = progressData || {};
    // O(1) staleness check: object identity catches a wholesale replacement,
    // the epoch catches in-place writes. Counting keys here was the single
    // biggest cost in rebuilding the setup screen.
    const sourceSize = window.__progressEpoch || 0;
    if (indexedProgressSource !== source || indexedProgressSize !== sourceSize) {
        progressIdsBySurface = new Map();
        for (const [id, row] of Object.entries(source)) {
            const normalized = normalizeProgressSurface(row?.word);
            if (!normalized || !row?.language) continue;
            const key = `${row.language}|${normalized}`;
            if (!progressIdsBySurface.has(key)) progressIdsBySurface.set(key, []);
            progressIdsBySurface.get(key).push(id);
        }
        indexedProgressSource = source;
        indexedProgressSize = sourceSize;
    }

    const normalizedSurface = normalizeProgressSurface(
        surface || progressSurfaceById.get(fullId)
    );
    const indexedIds = normalizedSurface
        ? (progressIdsBySurface.get(`${selectedLanguage}|${normalizedSurface}`) || [])
        : [];
    const candidates = {};
    for (const id of [fullId, crossModeProgressId(fullId), ...indexedIds]) {
        if (id && source[id]) candidates[id] = source[id];
    }
    return matchingProgressRecords(candidates, {
        fullId,
        surface,
        language: selectedLanguage,
        surfaceById: progressSurfaceById
    });
}

function getProgressRecordIdsForCard(fullId, surface = '') {
    return getProgressRecordsForCard(fullId, surface).map(record => record.id);
}

function getMergedWordProgress(fullId, surface = '') {
    return mergeProgressRecords(getProgressRecordsForCard(fullId, surface));
}

function getWordProgressState(fullId, surface = '') {
    return getProgressState(getMergedWordProgress(fullId, surface));
}

function calculateCoveragePercent() {
    if (!ppmData || ppmData.length === 0 || !progressData) return { pct: 0, wordsCovered: 0, totalWords: 0 };

    // Build compositeId→ppmEntry lookup once for performance.
    // ppmData entries have raw hex IDs (e.g. "91c4e7") but progressData keys
    // are composite IDs (e.g. "es191c4e7"), so we must build composite keys.
    const lang = (window.LANG_CODES || {})[selectedLanguage] || selectedLanguage.slice(0, 2);
    const mode = activeArtist ? '1' : '0';
    const idToPpm = {};
    let totalWords = 0;
    for (const entry of ppmData) {
        if (entry.id) {
            if (hideSingleOccurrence && entry.ppm <= 1) continue;
            const compositeId = `${lang}${mode}${entry.id}`;
            registerProgressCardSurface(compositeId, entry.word);
            idToPpm[compositeId] = entry;
            totalWords++;
        }
    }

    let coveredPpm = 0;
    let wordsCovered = 0;
    for (const [fullId, ppmEntry] of Object.entries(idToPpm)) {
        if (!getWordProgressState(fullId, ppmEntry.word).known) continue;
        coveredPpm += ppmEntry.ppm;
        wordsCovered++;
    }

    const pct = totalPpm > 0 ? (coveredPpm / totalPpm) * 100 : 0;
    return { pct, wordsCovered, totalWords };
}


// Update inline info text for lemma and cognate exclusion counts
async function updateExclusionBars() {
    const langConfig = config.languages[selectedLanguage];
    if (!langConfig || (!langConfig.dataPath && !langConfig.indexPath)) return;

    let vocabularyData = cachedVocabularyData;
    if (!vocabularyData) {
        try {
            vocabularyData = await fetchActiveVocabularyData(langConfig);
        } catch (error) {
            console.error('Failed to load vocabulary for exclusion info:', error);
            return;
        }
    }

    // Assign ranks if needed
    vocabularyData.forEach((item, index) => { if (!item.rank) item.rank = index + 1; });

    const prepared = window.getPreparedSetupVocabulary?.(selectedLanguage, vocabularyData);
    const { vocab: afterCognate, counts } = prepared || buildFilteredVocab(vocabularyData);

    // Update lemma info line
    const lemmaInfo = document.getElementById('lemmaInfoLine');
    if (lemmaInfo) {
        const lemmaExcluded = counts.lemma || 0;
        if (useLemmaMode && lemmaFieldAvailable && lemmaExcluded > 0) {
            lemmaInfo.textContent = `${afterCognate.length.toLocaleString()} cards · ${lemmaExcluded.toLocaleString()} forms merged`;
            lemmaInfo.style.display = '';
        } else {
            lemmaInfo.style.display = 'none';
        }
    }

    // Update cognate info line
    const cognateInfo = document.getElementById('cognateInfoLine');
    if (cognateInfo) {
        const cognateExcluded = counts.cognates || 0;
        if (excludeCognates && cognateFieldAvailable && cognateExcluded > 0) {
            cognateInfo.innerHTML = `${afterCognate.length.toLocaleString()} cards<br>(${cognateExcluded.toLocaleString()} cognates excluded)`;
            cognateInfo.style.display = '';
        } else {
            cognateInfo.style.display = 'none';
        }
    }

    // The Extras panel reports the words these same counts describe, and this
    // is the only place on the setup screen that holds the full vocabulary
    // after buildFilteredVocab() has stamped `_lemmaModeRepresentative` on it.
    // cachedVocabularyData is still null on this route (it is only set once a
    // deck is built), so publish the array Extras needs rather than making it
    // re-fetch and re-filter what was just computed here.
    globalThis.setupVocabularySnapshot = vocabularyData;
    globalThis.refreshExtrasButton?.();
    globalThis.refreshFastMode?.();

    // Update personal coverage bar
    updatePersonalCoverage(afterCognate);
}

// Level estimate CTA is now housed contextually in the Step 2 Level info modal
// ("Choose where to begin") rather than displaying as a banner on the landing screen.
function _toggleLevelEstimateCTA(hasCoverage) {
    const cta = document.getElementById('levelEstimateCTA');
    if (cta) cta.style.display = 'none';
}

// Personal coverage bar: what % of the lyrics the user has covered,
// weighted by word frequency (corpus_count). A common word contributes
// more to coverage than a rare one, matching the "% lyrics coverage" logic.
function getCurrentCoverageSnapshot(filteredVocab = window.setupVocabularySnapshot || []) {
    let coveredFreq = 0;
    let totalFreq = 0;
    let coveredCount = 0;
    for (const item of filteredVocab || []) {
        const freq = item.corpus_count || 1;
        totalFreq += freq;
        const progress = getMergedWordProgress(getWordId(item), item.word);
        if (progress && progress.language === selectedLanguage) {
            const lastCorrect = progress.lastCorrect ? new Date(progress.lastCorrect).getTime() : 0;
            const lastWrong = progress.lastWrong ? new Date(progress.lastWrong).getTime() : 0;
            if (lastCorrect > 0 && lastCorrect >= lastWrong) {
                coveredFreq += freq;
                coveredCount++;
            }
        }
    }
    return {
        percentage: totalFreq > 0 ? (coveredFreq / totalFreq) * 100 : 0,
        wordPercentage: filteredVocab?.length ? (coveredCount / filteredVocab.length) * 100 : 0,
        coveredCount,
        totalCount: filteredVocab?.length || 0,
        label: activeArtist
            ? (artistVocabularyScope === 'extra' ? `${activeArtist.name || 'Artist'} Extra explored` : 'Lyrics understood')
            : 'Speech understood'
    };
}

function publishCoverageSnapshot(snapshot) {
    window.currentCoverageSnapshot = snapshot;
    const setupVisible = !document.getElementById('setupPanel')?.classList.contains('hidden');
    if (setupVisible) window.lastSetupCoverageSnapshot = { ...snapshot };
    window.updateLearningContextUI?.(snapshot);
}

function updatePersonalCoverage(filteredVocab) {
    const wrapper = document.getElementById('personalCoverageWrapper');
    const fill = document.getElementById('personalCoverageFill');
    const label = document.getElementById('personalCoverageLabel');
    if (!wrapper || !fill || !label) return;

    const showEmptyStandardSummary = () => {
        const merged = (!activeArtist && document.getElementById('step1')?.classList.contains('language-summary-active'))
            || (activeArtist && document.getElementById('artistSourceStep')?.style.display !== 'none');
        if (merged) {
            wrapper.style.display = 'block';
            wrapper.classList.add('personal-coverage-wrapper--empty', 'visible');
            fill.style.width = '0%';
            label.innerHTML = '';
        } else {
            wrapper.style.display = 'none';
        }
    };

    if (!progressData || !filteredVocab || filteredVocab.length === 0) {
        publishCoverageSnapshot(getCurrentCoverageSnapshot(filteredVocab || []));
        if (activeArtist && artistVocabularyScope === 'main') window.updateArtistExtraUnlock?.(0);
        showEmptyStandardSummary();
        _toggleLevelEstimateCTA(false);
        return;
    }

    const snapshot = getCurrentCoverageSnapshot(filteredVocab);
    const { coveredCount } = snapshot;
    publishCoverageSnapshot(snapshot);

    if (coveredCount === 0) {
        if (activeArtist && artistVocabularyScope === 'main') window.updateArtistExtraUnlock?.(0);
        showEmptyStandardSummary();
        _toggleLevelEstimateCTA(false);
        return;
    }

    const coveragePct = snapshot.percentage;
    if (activeArtist && artistVocabularyScope === 'main') {
        window.updateArtistExtraUnlock?.(coveragePct);
    }

    // Animate the bar
    _toggleLevelEstimateCTA(true);
    wrapper.style.display = 'block';
    wrapper.classList.remove('personal-coverage-wrapper--empty');
    wrapper.classList.remove('visible');
    fill.style.transition = 'none';
    fill.style.width = '0%';

    const coverageType = snapshot.label;
    const wordPct = snapshot.wordPercentage.toFixed(1);
    // Two-column rows so the percentages right-align to the same edge —
    // labels on the left, numbers stacked on the right. Drops the italic
    // styling for a cleaner read.
    label.innerHTML = `
        <span class="ppi-row"><span class="ppi-label">${coverageType}</span><span class="ppi-value">${coveragePct.toFixed(1)}%</span></span>
        <span class="ppi-row"><span class="ppi-label">flashcards learned</span><span class="ppi-value">${wordPct}%</span></span>
    `;

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            fill.style.transition = 'width 1s ease-out';
            fill.style.width = Math.min(coveragePct, 100) + '%';
            wrapper.classList.add('visible');
            window.updateReviewAccess?.();
        });
    });
}

let _cachedDueSummary = null;
let _cachedDueSummaryLang = null;
let _cachedDueSummaryEpoch = -1;

function getGlobalDueReviewWords(language = '') {
    const data = typeof progressData !== 'undefined' ? progressData : (window.progressData || {});
    if (!data) return [];
    const dueWords = [];
    const seenSurfaces = new Set();
    const targetLang = String(language || window.selectedLanguage || '').trim().toLowerCase();

    for (const [id, record] of Object.entries(data)) {
        if (!record || !record.word) continue;
        const recLang = String(record.language || '').trim().toLowerCase();
        if (targetLang && recLang && recLang !== targetLang) {
            continue;
        }
        const surface = record.word.toLowerCase();
        if (seenSurfaces.has(surface)) continue;

        const reviewInfo = typeof window.getWordKnowledgeReviewInfo === 'function'
            ? window.getWordKnowledgeReviewInfo(id, record.word)
            : null;
        const state = !reviewInfo && typeof window.getProgressState === 'function'
            ? window.getProgressState(record)
            : null;

        const needsReview = reviewInfo ? reviewInfo.needsReview : (state && state.needsReview);
        if (needsReview) {
            seenSurfaces.add(surface);
            const reviewAt = reviewInfo?.reviewAt || state?.reviewAt || 0;
            const urgencyTier = reviewInfo?.urgencyTier || state?.urgencyTier || 'due';
            const needfulnessScore = reviewInfo?.needfulnessScore ?? state?.needfulnessScore ?? 100;
            dueWords.push({
                id,
                word: record.word,
                record,
                reviewAt,
                urgencyTier,
                needfulnessScore
            });
        }
    }
    dueWords.sort((a, b) => (b.needfulnessScore || 0) - (a.needfulnessScore || 0) || (a.reviewAt || 0) - (b.reviewAt || 0));
    return dueWords;
}

function getGlobalDueReviewSummary(language = '') {
    const targetLang = String(language || window.selectedLanguage || '').trim().toLowerCase();
    const currentEpoch = window.__progressEpoch || 0;
    if (_cachedDueSummary && _cachedDueSummaryLang === targetLang && _cachedDueSummaryEpoch === currentEpoch) {
        return _cachedDueSummary;
    }
    const all = getGlobalDueReviewWords(targetLang);
    _cachedDueSummary = {
        total: all.length,
        neverRight: all.filter(w => w.urgencyTier === 'never_right'),
        critical: all.filter(w => w.urgencyTier === 'critical'),
        due: all.filter(w => w.urgencyTier === 'due' || w.urgencyTier === 'upcoming'),
        all
    };
    _cachedDueSummaryLang = targetLang;
    _cachedDueSummaryEpoch = currentEpoch;
    return _cachedDueSummary;
}

window.getCurrentCoverageSnapshot = getCurrentCoverageSnapshot;

// Setup tooltip handlers (needs to run early, before any set is picked)

window.calculateCoveragePercent = calculateCoveragePercent;
window.parseProgressTimestamp = parseProgressTimestamp;
window.getSrsStage = getSrsStage;
window.getSrsIntervalDays = getSrsIntervalDays;
window.advanceSrsStage = advanceSrsStage;
window.getProgressState = getProgressState;
window.normalizeProgressSurface = normalizeProgressSurface;
window.registerProgressCardSurface = registerProgressCardSurface;
window.getProgressRecordsForCard = getProgressRecordsForCard;
window.getProgressRecordIdsForCard = getProgressRecordIdsForCard;
window.getMergedWordProgress = getMergedWordProgress;
window.getWordProgressState = getWordProgressState;
window.getGlobalDueReviewWords = getGlobalDueReviewWords;
window.getGlobalDueReviewSummary = getGlobalDueReviewSummary;
window.updateExclusionBars = updateExclusionBars;
window.updatePersonalCoverage = updatePersonalCoverage;
