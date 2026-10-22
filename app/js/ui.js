// Setup panel UI: language tabs, stable level selector, and automatic set progress.
// Key functions: renderLanguageTabs(), renderLevelSelector(), renderRangeSelector().
import './state.js?v=3e821184';
import { openProgressOverview, closeProgressOverview } from './progress-overview.js?v=3e821184';
import { readFastTrack } from './fast-track-preferences.js?v=3e821184';
import './session-plan.js?v=3e821184';

const GLOBAL_STUDY_DEFAULTS_KEY = 'fluency_global_study_defaults_v1';
// One tap, one finishable sitting. The pool is already ordered by needfulness
// (never-right, then recent mistakes, then overdue), so this is a slice, not a
// second selection policy.
const QUICK_REVIEW_LIMIT = 20;
// The progress ring belongs to opening a deck -- a language or a mode -- where
// the wait is long enough to fill and the figure is the one worth seeing. On a
// twenty-card set it was neither, so the set load is back to a plain spinner.
// The wiring stays: flipping this back to true restores it.
const SHOW_SET_PROGRESS_RING = false;
let _setupLevelSelectionWasManual = false;

// Timing instrument for the setup path. Returning to setup rebuilds the level
// selector and has been reported as taking seconds; the obvious suspects
// (vocabulary fetch, progress lookups, knowledge lookups) all turned out to be
// cached or indexed already, so this measures instead of guessing again.
//
// It wraps two paths: the artist-Extra selector, and the speech source pick,
// where it also says how much of the deck wheel's hold is covering real work
// rather than idling. A table prints on each. Everywhere else it stays empty,
// so adding a phase means adding a timePhase() call, not just reading one.
const _setupTimings = [];

async function timePhase(label, fn) {
    const started = performance.now();
    try {
        return await fn();
    } finally {
        _setupTimings.push({ phase: label, ms: +(performance.now() - started).toFixed(1) });
    }
}

function reportSetupTimings(total) {
    if (!_setupTimings.length) return;
    const rows = [..._setupTimings, { phase: 'TOTAL', ms: +total.toFixed(1) }];
    console.table(rows);
    window.__lastSetupTimings = rows;
    _setupTimings.length = 0;
}

// Per-epoch memo for getRecordedSetupState. Building the setup screen walks
// every card twice — findFirstIncompleteLevelBtn scans all levels to pick an
// actionable one, then renderRangeSelector scans the chosen level again per
// set — and each call reaches through progress and granular knowledge. Lemma
// inheritance and the estimate are applied outside the memo, per call.
//
// Scoped to a single render on purpose: progressData is mutated in place when
// a card is answered, so a longer-lived cache keyed on object identity would
// go stale without any way to notice.
let _setupStateMemo = null;
let _setupStateMemoEpoch = -1;

function resetSetupStateMemo() {
    _setupStateMemo = new Map();
    _setupStateMemoEpoch = Number(window.__progressEpoch || 0);
}

function ensureCurrentSetupStateMemo() {
    const epoch = Number(window.__progressEpoch || 0);
    if (!_setupStateMemo || _setupStateMemoEpoch !== epoch) {
        resetSetupStateMemo();
    }
}

function readGlobalStudyDefaults() {
    try {
        const saved = JSON.parse(localStorage.getItem(GLOBAL_STUDY_DEFAULTS_KEY) || 'null');
        return saved && typeof saved === 'object' ? saved : {};
    } catch (_) {
        return {};
    }
}

function applyGlobalStudyDefaults() {
    const saved = readGlobalStudyDefaults();
    const fastTrack = readFastTrack(selectedLanguage);
    useLemmaMode = fastTrack.enabled && fastTrack.merge;
    excludeCognates = fastTrack.enabled && fastTrack.skip;
    // Smart Skip's other two switches were saved but never read back, so a
    // reload silently undid them.
    excludeGrammarParticles = fastTrack.enabled && fastTrack.skipGrammar;
    excludeSlang = fastTrack.enabled && fastTrack.skipSlang;
    excludeProperNouns = fastTrack.enabled && fastTrack.skipEntities;
    isFlipped = saved.directionFlipped === true;
    speechEnabled = saved.speechEnabled !== false;
    spacedRepetitionEnabled = saved.spacedRepetitionEnabled !== false;
    // Non-decompositional expressions are study content, not a preference.
    // They always follow a correct parent card and cannot be turned off.
    expressionsModeEnabled = true;
    phrasesModeEnabled = true;
    extraExamplesEnabled = false;
    try {
        const savedMode = localStorage.getItem('fluency_sense_prominence_mode_v1');
        if (savedMode) {
            senseProminenceMode = savedMode;
            if (globalThis.state) globalThis.state.senseProminenceMode = savedMode;
        }
    } catch (_) {}
    syncStudyPreferenceControls();
}

function syncStudyPreferenceControls() {
    document.querySelectorAll('.lemma-toggle-btn').forEach(button =>
        button.classList.toggle('selected', (button.dataset.lemma === 'on') === useLemmaMode));
    document.querySelectorAll('.cognate-toggle-btn').forEach(button =>
        button.classList.toggle('selected', (button.dataset.cognate === 'exclude') === excludeCognates));
    document.querySelectorAll('.grammar-toggle-btn').forEach(button =>
        button.classList.toggle('selected', (button.dataset.grammar === 'exclude') === Boolean(excludeGrammarParticles)));
    document.querySelectorAll('.slang-toggle-btn').forEach(button =>
        button.classList.toggle('selected', (button.dataset.slang === 'exclude') === Boolean(excludeSlang)));

    document.querySelectorAll('.entity-toggle-btn').forEach(button =>
        button.classList.toggle('selected', (button.dataset.entity === 'exclude') === Boolean(excludeProperNouns)));

    const saved = readGlobalStudyDefaults();
    const fastTrack = readFastTrack(selectedLanguage);
    const effective = {
        mergeLemmas: fastTrack.enabled && fastTrack.merge,
        excludeCognates: fastTrack.enabled && fastTrack.skip,
        directionFlipped: saved.directionFlipped === true,
        speechEnabled: saved.speechEnabled !== false,
        spacedRepetitionEnabled: saved.spacedRepetitionEnabled !== false,
        extraExamples: false
    };
    document.querySelectorAll('.global-study-default-btn').forEach(button => {
        const value = button.dataset.value === 'on';
        const selected = value === effective[button.dataset.setting];
        button.classList.toggle('selected', selected);
        button.setAttribute('aria-pressed', selected ? 'true' : 'false');
    });
    const currentProm = (typeof senseProminenceMode !== 'undefined' ? senseProminenceMode : globalThis.state?.senseProminenceMode) || 'labels';
    document.querySelectorAll('.sense-prominence-btn').forEach(button => {
        const selected = button.dataset.prominence === currentProm;
        button.classList.toggle('selected', selected);
        button.setAttribute('aria-pressed', selected ? 'true' : 'false');
    });
    const targetBtn = document.getElementById('cardFrontTargetBtn');
    if (targetBtn) {
        const langName = config?.languages?.[selectedLanguage]?.name;
        targetBtn.textContent = langName || 'Language';
    }
    const vocabDesc = document.querySelector('#vocabularySettingsTitle + p');
    if (vocabDesc) {
        const langName = config?.languages?.[selectedLanguage]?.name || 'target language';
        vocabDesc.textContent = `Already know some of these words from another app or course? Upload your list so this app starts you further in — paste it or choose a text, CSV or TSV file. Matches exact ${langName} word forms, previews every change first, and never overwrites a newer answer already saved here.`;
    }
    updateCognateSensitivityVisibility();
}

// The sensitivity threshold only means anything while cognates are actually
// being excluded, and only for languages that carry cognate scores. Hide the
// whole row (and any explanation it had open) otherwise.
function updateCognateSensitivityVisibility() {
    const row = document.getElementById('cognateSensitivityRow');
    if (!row) return;
    const visible = Boolean(cognateFieldAvailable && excludeCognates);
    row.style.display = visible ? 'flex' : 'none';
    document.querySelectorAll('#cognateSensitivitySelector .cognate-sens-btn').forEach(b => {
        b.classList.toggle('selected', Math.abs(parseFloat(b.dataset.threshold) - cognateThreshold) < 1e-6);
    });
    if (!visible) closeSettingExplanation(document.getElementById('cognateSensitivityInfoBtn'));
}

function closeSettingExplanation(infoBtn) {
    if (!infoBtn) return;
    infoBtn.setAttribute('aria-expanded', 'false');
    const inline = infoBtn.closest('.settings-default-row')?.querySelector('.settings-row-explanation');
    if (inline) inline.hidden = true;
    const controlled = infoBtn.getAttribute('aria-controls');
    const extra = controlled ? document.getElementById(controlled) : null;
    if (extra) extra.hidden = true;
}

// One "?" per study preference. It reveals that setting's one-line
// description in place; rows that also point at a longer block via
// aria-controls open both together.
function setupSettingExplanations() {
    document.querySelectorAll('.settings-default-row .settings-info-btn').forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.stopPropagation();
            const row = this.closest('.settings-default-row');
            const inline = row?.querySelector('.settings-row-explanation');
            const controlled = this.getAttribute('aria-controls');
            const extra = controlled ? document.getElementById(controlled) : null;
            const shouldOpen = this.getAttribute('aria-expanded') !== 'true';
            if (inline) inline.hidden = !shouldOpen;
            if (extra) extra.hidden = !shouldOpen;
            this.setAttribute('aria-expanded', String(shouldOpen));
        });
    });
}

function saveGlobalStudyPreference(setting, value) {
    if (setting === 'expressionsMode') return true;
    const saved = readGlobalStudyDefaults();
    saved[setting] = !!value;
    try {
        localStorage.setItem(GLOBAL_STUDY_DEFAULTS_KEY, JSON.stringify(saved));
    } catch (_) {
        return false;
    }
    syncStudyPreferenceControls();
    return true;
}

async function refreshAfterGlobalStudyDefaultChange() {
    syncStudyPreferenceControls();
    const step2 = document.getElementById('step2');
    if (!selectedLanguage || !step2 || step2.style.display === 'none') return;
    const loadingIndicator = document.getElementById('dataLoadingIndicator');
    if (useLemmaMode) loadingIndicator?.classList.add('visible');
    try {
        await renderLevelSelector(selectedLanguage);
        if (selectedLevel) await renderRangeSelector();
        await updateExclusionBars();
    } finally {
        loadingIndicator?.classList.remove('visible');
    }
}

function setupGlobalStudyDefaults() {
    setupSettingsOverview();
    syncStudyPreferenceControls();
    setupSettingExplanations();
    document.querySelectorAll('.global-study-default-btn').forEach(button => {
        button.addEventListener('click', async function() {
            const setting = this.dataset.setting;
            const enabled = this.dataset.value === 'on';
            if (!saveGlobalStudyPreference(setting, enabled)) return;
            applyGlobalStudyDefaults();
            if (setting === 'mergeLemmas' || setting === 'excludeCognates') {
                await refreshAfterGlobalStudyDefaultChange();
            } else if (setting === 'spacedRepetitionEnabled') {
                const setupPanel = document.getElementById('setupPanel');
                if (selectedLevel && setupPanel && !setupPanel.classList.contains('hidden')) {
                    await renderRangeSelector();
                }
            } else {
                document.getElementById('flashcard')?.classList.remove('flipped');
                window.updateSpeakIcons?.();
                if (flashcards.length > 0) window.updateCard?.();
            }
        });
    });
    const publication = window.getWsdPublicationProjection?.() || 'forced_leaf';
    document.querySelectorAll('.wsd-publication-btn').forEach(button => {
        const selected = button.dataset.wsdPublication === publication;
        button.classList.toggle('selected', selected);
        button.setAttribute('aria-pressed', selected ? 'true' : 'false');
        button.addEventListener('click', function() {
            if (this.dataset.wsdPublication !== publication) {
                window.setWsdPublicationProjection?.(this.dataset.wsdPublication);
            }
        });
    });
    document.querySelectorAll('.sense-prominence-btn').forEach(button => {
        button.addEventListener('click', function() {
            const mode = this.dataset.prominence;
            if (!mode) return;
            senseProminenceMode = mode;
            if (globalThis.state) globalThis.state.senseProminenceMode = mode;
            try { localStorage.setItem('fluency_sense_prominence_mode_v1', mode); } catch (_) {}
            syncStudyPreferenceControls();
            if (flashcards.length > 0) window.updateCard?.();
        });
    });
}

// Defaults must be present before either mode renders its first level.
applyGlobalStudyDefaults();

// A legend row that does not fit its line shrinks its text a little (down to
// 11px) instead of wrapping; it wraps only if even that is not enough. It is
// re-fitted when its width changes, e.g. when a folded section opens.
function fitLegendFonts(root) {
    root?.querySelectorAll?.('.home-level-stats').forEach(el => {
        const fit = () => {
            if (!el.clientWidth) return;
            el.style.fontSize = '';
            el.style.flexWrap = 'nowrap';
            let size = parseFloat(getComputedStyle(el).fontSize) || 16;
            while (el.scrollWidth > el.clientWidth + 1 && size > 11) {
                size -= 0.5;
                el.style.fontSize = size + 'px';
            }
            if (el.scrollWidth > el.clientWidth + 1) el.style.flexWrap = 'wrap';
            // The estimate line beneath uses the same size, so the two read as one block.
            const note = el.nextElementSibling;
            if (note?.classList.contains('home-level-estimate')) note.style.fontSize = el.style.fontSize;
        };
        fit();
        if (typeof ResizeObserver === 'function') {
            let lastWidth = el.clientWidth;
            new ResizeObserver(() => {
                if (el.clientWidth !== lastWidth) { lastWidth = el.clientWidth; fit(); }
            }).observe(el);
        }
    });
}
window.fitLegendFonts = fitLegendFonts;

function setupTooltipHandlers() {
    // Step help tooltip handlers — open as modal
    // Delegation also covers the progress legend rebuilt with the session.
    document.addEventListener('click', function(e) {
        const button = e.target.closest?.('.step-help-btn, .step-title-trigger');
        if (!button) return;
        const tooltip = document.getElementById(button.dataset.tooltip);
        if (!tooltip) return;
        e.stopPropagation();
        document.querySelectorAll('.step-info-tooltip').forEach(other => {
            if (other !== tooltip) other.classList.remove('visible');
        });
        tooltip.classList.toggle('visible');
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            const bar = e.target.closest?.('.study-level-bar.step-help-btn, .home-level-bar.step-help-btn');
            if (bar) {
                e.preventDefault();
                bar.click();
            }
        }
    });

    // Close tooltip modal on backdrop click (click on outer overlay, not inner content)
    document.querySelectorAll('.step-info-tooltip').forEach(tooltip => {
        tooltip.addEventListener('click', function(e) {
            if (e.target === this) this.classList.remove('visible');
        });
        tooltip.querySelector('.info-sheet-close')?.addEventListener('click', () => {
            tooltip.classList.remove('visible');
        });
    });

    // Legacy detail entry point retained for builds that still include it.
    document.getElementById('cognateRulesBtn')?.addEventListener('click', function(e) {
        e.stopPropagation();
        const step2Tip = document.getElementById('step2Tooltip');
        if (step2Tip) step2Tip.classList.remove('visible');
        document.getElementById('cognateRulesModal').classList.remove('hidden');
    });

    document.getElementById('closeCognateRulesModal').addEventListener('click', function() {
        document.getElementById('cognateRulesModal').classList.add('hidden');
    });

    // Button info icon handlers
    document.querySelectorAll('.btn-info-icon').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const infoId = this.dataset.info;
            const tooltip = document.getElementById(infoId);

            // Close all other btn-info-tooltips first
            document.querySelectorAll('.btn-info-tooltip').forEach(t => {
                if (t.id !== infoId) {
                    t.classList.remove('visible');
                }
            });

            // Toggle this tooltip
            tooltip.classList.toggle('visible');
        });
    });

    // Close btn-info-tooltips when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.btn-info-icon') && !e.target.closest('.btn-info-tooltip')) {
            document.querySelectorAll('.btn-info-tooltip').forEach(t => {
                t.classList.remove('visible');
            });
        }
    });
}

// Update incorrect button visibility - now handled by renderRangeSelector
function updateIncorrectButtonVisibility() {
    // This function is now a no-op since incorrect button is rendered dynamically
    // in renderRangeSelector. Keeping for backwards compatibility.
    if (selectedLevel) {
        renderRangeSelector().catch(err => console.error('Error refreshing ranges:', err));
    }
}

// How long the deck wheel holds before the setup screen behind it is revealed.
// Extended twice by 3 seconds (5s → 8s → 11s) per user request, for comfortable reading.
// A tap ends it at once; this is the ceiling for someone who does not tap.
const DECK_OVERVIEW_HOLD_MS = 11000;

// The big wheel: progress across the whole deck the learner just opened.
//
// Every figure is read directly from the deck's vocabulary and learning states
// so Known, Practice, and New accurately reflect the deck rather than global
// language-wide practice totals.
function showDeckOverviewLoading() {
    const snapshot = window.currentCoverageSnapshot;
    const rawCount = Number(snapshot?.totalCount) || 0;
    if (!rawCount && (!window.setupVocabularySnapshot || window.setupVocabularySnapshot.length === 0)) {
        return null;
    }

    const vocab = window.getPreparedSetupVocabulary?.(selectedLanguage, window.setupVocabularySnapshot)?.vocab
        || window.setupVocabularySnapshot
        || [];

    let knownCount = 0;
    let reviewCount = 0;
    let unseenCount = 0;
    const cardCount = vocab.length > 0 ? vocab.length : rawCount;

    if (vocab.length > 0) {
        for (let i = 0; i < vocab.length; i++) {
            const state = typeof getSetupLearningState === 'function'
                ? getSetupLearningState(vocab[i])
                : null;
            if (state?.seen) {
                if (state.needsReview) reviewCount++;
                else knownCount++;
            } else {
                unseenCount++;
            }
        }
    } else {
        knownCount = Math.min(cardCount, Number(snapshot?.coveredCount) || 0);
        const due = Number(window.getGlobalDueReviewSummary?.(selectedLanguage)?.total) || 0;
        reviewCount = Math.max(0, Math.min(due, Math.floor((cardCount - knownCount) * 0.5)));
        unseenCount = Math.max(0, cardCount - knownCount - reviewCount);
    }

    // Nothing to demonstrate if untouched (0% known and 0% review)
    if (knownCount === 0 && reviewCount === 0) return null;

    const languageName = config?.languages?.[selectedLanguage]?.name || selectedLanguage || '';
    const title = activeArtist
        ? (activeArtist.name || 'Lyrics')
        : (languageName || 'Speech');
    const percent = Number(snapshot?.percentage) || 0;

    return window.showDeckLoading?.(
        {
            cardCount,
            seenCount: knownCount + reviewCount,
            knownCount,
            reviewCount,
            unseenCount,
            speechPercentage: percent,
            speechUnit: activeArtist ? 'of these lyrics understood' : 'of speech understood'
        },
        {
            title,
            detail: '',
            holdMs: DECK_OVERVIEW_HOLD_MS,
            artist: activeArtist,
            language: selectedLanguage
        }
    );
}

async function startDailyReview(opts = {}) {
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.style.display = 'block';
        loadingMessage.textContent = 'Collecting cards ready to practise…';
    }
    window.showAppLoading?.('Loading practice', 'Preparing your cards…');
    try {
        await window.loadDailyReviewDeck?.({
            limit: opts.limit || 100,
            urgencyTier: opts.urgencyTier || 'all'
        });
    } catch (err) {
        console.error('Error starting daily review:', err);
    } finally {
        window.hideAppLoading?.();
        if (loadingMessage) loadingMessage.style.display = 'none';
    }
}

function setActiveSetupStep(stepId) {
    if (stepId === 'step4') stepId = 'step2';
    document.querySelectorAll('#step1 .step-number, #step2 .step-number, #step4 .step-number')
        .forEach(number => number.classList.toggle('--active', number.closest('.setup-step')?.id === stepId));
}

const PREFERRED_LANGUAGE_KEY = 'fluencyPreferredLanguageV1';
const LEARNING_CONTEXT_FLAGS = {
    spanish: '🇪🇸', portuguese: '🇵🇹', portuguese_brazilian: '🇧🇷', french: '🇫🇷', italian: '🇮🇹',
    swedish: '🇸🇪', dutch: '🇳🇱', finnish: '🇫🇮', polish: '🇵🇱', russian: '🇷🇺', czech: '🇨🇿'
};

function learningContextInitials(name) {
    const words = String(name || '').trim().split(/\s+/).filter(Boolean);
    if (words.length === 0) return '?';
    if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
    return (words[0][0] + words[1][0]).toUpperCase();
}

function paintLearningContextPhoto(el, artist) {
    if (!el || !artist) return;
    const art = artist.pickerImage || artist.image || artist.defaultAlbumArt || '';
    const isCustom = artist.customSongSource === true;
    el.textContent = art ? '' : (isCustom ? '♫' : learningContextInitials(artist.name));
    el.classList.toggle('learning-context-photo--fallback', !art);
    el.style.backgroundImage = art ? `url("${String(art).replace(/"/g, '%22')}")` : '';
    el.style.backgroundColor = art ? '' : (artist.colorTheme?.primary || 'var(--accent-primary)');
}

// Which vocabulary the learner is in right now, or null while they are still
// choosing. Speech counts only once it has been picked, not merely because no
// artist is active.
function currentLearningMode() {
    if (window.seriesWorkspaceActive?.()) return 'series';
    if (window.musicWorkspaceActive?.()) return 'lyrics';
    if (window.isSeriesStudy?.()) return 'series';
    if (window.playlistLiveActive?.()) return 'live';
    if (activeArtist) return 'lyrics';
    if (document.getElementById('step1')?.classList.contains('source-speech-active')) return 'speech';
    return null;
}

window.currentLearningMode = currentLearningMode;

// Everything that belongs to a chosen deck. The mode choice shows none of it —
// #reviewDeckSection sits outside #step4, so it has to be named here too.
function hideStudySurfaces() {
    ['step2', 'step4', 'extrasDeckSection', 'lemmaToggleContainer', 'cognateToggleContainer']
        .forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    const reviewSection = document.getElementById('reviewDeckSection');
    if (reviewSection) reviewSection.hidden = true;
    hideAllSelectionPills();
}

function updateLearningContextUI(snapshot = window.currentCoverageSnapshot) {
    const button = document.getElementById('learningContextBtn');
    const languageConfig = config.languages?.[selectedLanguage];
    if (!button || !languageConfig) return;

    const modeKey = currentLearningMode();
    const mode = modeKey === 'series' ? 'TV Series' : modeKey === 'live'
        ? `Live · ${window.playlistLiveDeck?.()?.playlistName || 'playlist'}`
        : modeKey === 'lyrics'
            ? 'Music'
            : modeKey === 'speech'
                ? 'Speech'
                : 'Choose…';
    const flag = languageConfig.flag || LEARNING_CONTEXT_FLAGS[selectedLanguage] || selectedLanguage.slice(0, 2).toUpperCase();

    document.getElementById('learningContextSourceBtn').hidden = !modeKey;
    button.hidden = false;
    const flagEl = document.getElementById('learningContextFlag');
    const photoEl = document.getElementById('learningContextPhoto');
    const nameEl = document.getElementById('learningContextLanguage');
    const artistRow = document.getElementById('learningContextArtistBtn');
    const songsRow = document.getElementById('learningContextSongsBtn');
    flagEl.textContent = flag;
    // The desktop sidebar names the language even in artist mode; the artist
    // gets its own chip beneath it (desktop-shell.js trail).
    const languageOnlyEl = document.getElementById('learningContextLanguageOnly');
    if (languageOnlyEl) {
        const plainLanguage = (activeArtist && activeArtist.language === selectedLanguage)
            ? activeArtist.language : selectedLanguage;
        languageOnlyEl.textContent = window._normalModeLangConfigs?.[plainLanguage]?.name
            || config.languages?.[plainLanguage]?.name || languageConfig.name || selectedLanguage;
    }
    document.getElementById('learningContextSheetFlag').textContent = flag;
    document.getElementById('learningContextSheetLanguage').textContent = languageConfig.name || selectedLanguage;
    document.getElementById('learningContextSheetMode').textContent = mode;
    const modeIcon = document.getElementById('learningContextSheetModeIcon');
    if (modeIcon) {
        modeIcon.innerHTML = modeKey === 'speech' ? MODE_ICON_SPEECH
            : modeKey === 'series' ? MODE_ICON_SERIES : modeKey ? MODE_ICON_MUSIC : '';
    }
    // Verb drills are a separate page, not a third vocabulary, so they live
    // here beside the language rather than on the vocabulary choice. Only
    // languages whose config names a drill deck get the row.
    const verbsRow = document.getElementById('learningContextVerbsBtn');
    if (verbsRow) {
        const drillLanguage = activeArtist?.language || selectedLanguage;
        const drillHref = window.fluencyRoutes?.conjugationDrillHref?.(drillLanguage, null, config.languages);
        verbsRow.hidden = !drillHref;
        verbsRow.dataset.href = drillHref || '';
    }
    const lyricsViewRow = document.getElementById('learningContextLyricsViewBtn');
    if (lyricsViewRow) {
        const lyricsActive = modeKey === 'lyrics' || modeKey === 'live';
        lyricsViewRow.hidden = !lyricsActive;
        const currentLang = (typeof activeArtist !== 'undefined' && activeArtist?.language) || (typeof selectedLanguage !== 'undefined' ? selectedLanguage : null);
        const routes = typeof window !== 'undefined' ? window.fluencyRoutes : null;
        lyricsViewRow.dataset.href = routes?.lyricsViewHref?.(null, currentLang) || (currentLang === 'portuguese' ? 'lyrics-view/?lang=pt' : 'lyrics-view/');
    }
    const activities = document.getElementById('learningContextActivities');
    if (activities) activities.hidden = Boolean(verbsRow?.hidden && lyricsViewRow?.hidden);
    // No vocabulary chosen yet means no deck to measure.
    const progressButton = document.getElementById('topBarProgressBtn');
    if (progressButton) progressButton.hidden = !modeKey;
    if (activeArtist && modeKey === 'lyrics') {
        const artistName = activeArtist.name || 'Artist';
        nameEl.textContent = artistName;
        button.setAttribute('aria-label', `Open learning settings for ${artistName}`);
        flagEl.hidden = true;
        photoEl.hidden = false;
        paintLearningContextPhoto(photoEl, activeArtist);
        paintLearningContextPhoto(document.getElementById('learningContextSheetPhoto'), activeArtist);
        artistRow.hidden = false;
        songsRow.hidden = false;
        document.getElementById('learningContextSheetArtist').textContent = artistName;
        document.getElementById('learningContextSheetSongs').textContent = window.songSelectionSummary?.() || 'Choose songs';
    } else {
        nameEl.textContent = languageConfig.name || selectedLanguage;
        button.setAttribute('aria-label', 'Open learning settings');
        flagEl.hidden = false;
        photoEl.hidden = true;
        artistRow.hidden = true;
        songsRow.hidden = true;
    }
}

function mergeStandardProgressIntoLanguageStep() {
    if (activeArtist) return;
    const step = document.getElementById('step1');
    const header = document.getElementById('step1Header');
    const title = document.getElementById('step1Title');
    const inlinePill = document.getElementById('selectedLanguageInline');
    const sourcePill = document.getElementById('selectedSourceInline');
    const sourceCard = document.getElementById('standardSourceCard');
    const languageName = document.getElementById('standardSourceLanguageName');
    const languageIcon = document.getElementById('standardSourceLanguageIcon');
    if (!step || !header || !title || !inlinePill || !sourcePill
        || !sourceCard || !languageName || !languageIcon) return;

    languageName.textContent = config.languages[selectedLanguage]?.name || selectedLanguage;
    languageIcon.textContent = config.languages[selectedLanguage]?.flag || LEARNING_CONTEXT_FLAGS[selectedLanguage] || selectedLanguage.slice(0, 2).toUpperCase();
    // Progress is not shown here: until a vocabulary is chosen there is no deck
    // to measure. It lives in the chip's sheet and on the study page.
    title.textContent = 'Language';
    step.classList.add('language-summary-active');
    header.removeAttribute('role');
    header.removeAttribute('tabindex');
    header.removeAttribute('aria-haspopup');
    inlinePill.style.display = 'none';
    sourcePill.style.display = 'none';
    sourceCard.style.display = 'grid';
}

function mergeArtistProgressIntoSourceStep() {
    const wrapper = document.getElementById('personalCoverageWrapper');
    const progressSlot = document.getElementById('artistSourceProgress');
    const languageName = document.getElementById('artistSourceLanguageName');
    const languageIcon = document.getElementById('artistSourceLanguageIcon');
    const languageBtn = document.getElementById('artistSourceLanguageBtn');
    if (!wrapper || !progressSlot) return;

    const flagMap = {
        spanish: '🇪🇸', swedish: '🇸🇪', italian: '🇮🇹', dutch: '🇳🇱', finnish: '🇫🇮',
        polish: '🇵🇱', french: '🇫🇷', russian: '🇷🇺', czech: '🇨🇿',
        portuguese: '🇵🇹', portuguese_brazilian: '🇧🇷'
    };
    const lang = activeArtist?.language || selectedLanguage || 'spanish';
    if (languageName) languageName.textContent = config.languages[lang]?.name || lang;
    if (languageIcon) languageIcon.textContent = config.languages[lang]?.flag || flagMap[lang] || lang.slice(0, 2).toUpperCase();
    if (languageBtn) {
        languageBtn.onclick = () => window.showLanguagePicker?.(config.languages);
    }

    progressSlot.appendChild(wrapper);
    wrapper.classList.add('personal-coverage-wrapper--merged', 'visible');
    wrapper.classList.remove('personal-coverage-wrapper--empty');
    wrapper.style.display = 'block';
}

function unmergeArtistProgressFromSourceStep() {
    const wrapper = document.getElementById('personalCoverageWrapper');
    const cta = document.getElementById('levelEstimateCTA');
    const anchor = cta || document.getElementById('dataLoadingIndicator');
    if (!wrapper || !anchor) return;
    anchor.after(wrapper);
    wrapper.classList.remove('personal-coverage-wrapper--merged', 'personal-coverage-wrapper--empty', 'visible');
    wrapper.style.display = 'none';
}

function unmergeStandardProgressFromLanguageStep() {
    if (activeArtist) return;
    const step = document.getElementById('step1');
    const header = document.getElementById('step1Header');
    const title = document.getElementById('step1Title');
    const wrapper = document.getElementById('personalCoverageWrapper');
    const inlinePill = document.getElementById('selectedLanguageInline');
    const sourcePill = document.getElementById('selectedSourceInline');
    const cta = document.getElementById('levelEstimateCTA');
    const sourceCard = document.getElementById('standardSourceCard');
    const anchor = cta || document.getElementById('dataLoadingIndicator');
    if (!step || !header || !title || !wrapper || !inlinePill || !sourcePill || !anchor || !sourceCard) return;

    title.after(inlinePill);
    anchor.after(wrapper);
    title.textContent = 'Choose the language you’re learning';
    step.classList.remove('language-summary-active');
    header.setAttribute('role', 'button');
    header.setAttribute('tabindex', '0');
    header.setAttribute('aria-haspopup', 'dialog');
    wrapper.classList.remove('personal-coverage-wrapper--merged', 'personal-coverage-wrapper--empty', 'visible');
    wrapper.style.display = 'none';
    sourcePill.style.display = 'none';
    sourceCard.style.display = 'none';
    hideStudySurfaces();
}

window.mergeArtistProgressIntoSourceStep = mergeArtistProgressIntoSourceStep;
window.unmergeArtistProgressFromSourceStep = unmergeArtistProgressFromSourceStep;
window.unmergeStandardProgressFromLanguageStep = unmergeStandardProgressFromLanguageStep;

function renderLanguageTabs() {
    const tabsContainer = document.getElementById('languageTabs');

    // Order is a product decision (enabled languages before grayed-out ones), so
    // it is declared once in config.json rather than restated in each file that
    // renders a language list.
    const languageOrder = config.languageDisplayOrder || Object.keys(config.languages);
    const languages = languageOrder.filter(lang => config.languages[lang]);

    // Short codes live on each language's own config entry.
    const langCodeMap = Object.fromEntries(
        Object.entries(config.languages).map(([key, cfg]) => [key, cfg.shortCode || key.slice(0, 2).toUpperCase()])
    );

    // Generate language tabs dynamically - no active state initially
    const tabsHTML = languages.map((langKey, index) => {
        const langCode = langCodeMap[langKey] || langKey.substring(0, 2).toUpperCase();
        const langConfig = config.languages[langKey];
        const hasData = langConfig.hasData !== false;
        // Don't pre-select any language - user must click to select
        const activeClass = '';
        const disabledClass = !hasData ? 'disabled' : '';
        const disabledAttr = !hasData ? 'disabled' : '';
        const title = !hasData ? `${langConfig.name} - Data coming soon` : '';
        return `<button class="lang-tab ${activeClass} ${disabledClass}" data-lang="${langKey}" ${disabledAttr} title="${title}">${langCode}</button>`;
    }).join('');

    tabsContainer.innerHTML = `<div class="language-picker-options" aria-hidden="true">${tabsHTML}</div>`;

    const step = document.getElementById('step1');
    const header = document.getElementById('step1Header');
    const openLanguagePicker = () => window.showLanguagePicker?.(config.languages, { fromMainScreen: true });
    header.setAttribute('role', 'button');
    header.setAttribute('tabindex', '0');
    header.setAttribute('aria-haspopup', 'dialog');
    header.onclick = () => {
        if (!step.classList.contains('language-summary-active')) openLanguagePicker();
    };
    step.onclick = event => {
        if (!step.classList.contains('language-summary-active') && event.target !== header && !header.contains(event.target)) {
            openLanguagePicker();
        }
    };
    header.onkeydown = event => {
        if (!step.classList.contains('language-summary-active')
            && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            openLanguagePicker();
        }
    };

    setActiveSetupStep('step1');

    // Setup event listeners for tabs
    setupLanguageTabs();
}

// The vocabulary choice, worded once. The inline page and the modal picker
// (main.js openLearningSourcePicker) both read this, so they cannot drift.
const MODE_ICON_SPEECH = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.6A8 8 0 1 1 21 12z"></path></svg>';
const MODE_ICON_SERIES = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m9 2 3 3 3-3M10 10l5 3-5 3z"/></svg>';
const MODE_ICON_MUSIC = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18V5l11-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="17" cy="16" r="3"></circle></svg>';

// Music (artists, your songs, live playlists) is open in Spanish only for now.
// The admin account (SafariMS) sees it in every language to test it. Every
// entry point to Music asks this one question.
function musicOpenFor(language) {
    return language === 'spanish' || Boolean(window.isAuditAccount?.());
}
window.musicOpenFor = musicOpenFor;

function learningModeCopy(language = selectedLanguage) {
    const lyricsCatalog = config?.languages?.[language]?.capabilities?.lyrics !== false;
    const musicOpen = musicOpenFor(language);
    return {
        title: 'Choose what to learn from',
        intro: [
            'Learn the most common words in your chosen source. You can switch any time, and your progress is shared.'
        ],
        series: { label: 'TV Series', description: 'Vocabulary from a series you’re watching.', bestFor: ['Following a particular series', 'Learning its recurring words'], iconHTML: MODE_ICON_SERIES },
        speech: {
            label: 'Speech',
            description: 'Words and examples from films and TV.',
            bestFor: ['Starting from scratch', 'Everyday conversation', 'Following films and TV'],
            iconHTML: MODE_ICON_SPEECH
        },
        lyrics: {
            label: 'Music',
            description: !musicOpen ? 'Coming soon'
                : lyricsCatalog
                ? 'Words and examples from songs, artists and your playlists.'
                : 'Words and examples from your Spotify playlists.',
            bestFor: !musicOpen ? []
                : lyricsCatalog
                ? ['Understanding your favourite songs', 'Studying your own playlists', 'Learning by listening']
                : ['Studying your own playlists', 'Learning by listening'],
            iconHTML: MODE_ICON_MUSIC
        }
    };
}

window.learningModeCopy = learningModeCopy;

function paintModeButton(button, entry) {
    if (!button) return;
    const icon = button.querySelector('.choice-sheet-icon');
    const label = button.querySelector('.choice-sheet-copy strong');
    const detail = button.querySelector('.choice-sheet-copy small');
    if (icon) icon.innerHTML = entry.iconHTML;
    if (label) label.textContent = entry.label;
    if (detail) detail.textContent = entry.description;
    const copy = button.querySelector('.choice-sheet-copy');
    copy?.querySelector('.choice-sheet-bestfor')?.remove();
    if (copy && entry.bestFor?.length) copy.appendChild(window.bestForList(entry.bestFor));
}

function setupLanguageTabs() {
    const inlinePill = document.getElementById('selectedLanguageInline');
    const sourcePill = document.getElementById('selectedSourceInline');
    const sourceLabel = document.getElementById('selectedSourceInlineLabel');
    const languageCardButton = document.getElementById('standardSourceLanguageBtn');
    const speechSourceButton = document.getElementById('standardSourceSpeechBtn');
    const sourceCardButton = document.getElementById('standardSourcePickerBtn');
    const seriesButton = document.getElementById('standardSourceSeriesBtn');

    // Opening the language picker changes nothing by itself. The deck on screen
    // stays until a different language is actually chosen — the .lang-tab click
    // below does that switch — so closing the picker, or picking the language
    // already in use, leaves the learner exactly where they were.
    const reopenLanguagePicker = function(event) {
        event?.stopPropagation?.();
        window.closeRadialPicker?.('artistRadialPicker');
        window.closeChoiceSheet?.('lyricsSourceSheet');
        window.closeChoiceSheet?.('artistChoiceSheet');
        window.showLanguagePicker?.(config.languages);
    };
    window.reopenLanguagePicker = reopenLanguagePicker;
    inlinePill.onclick = reopenLanguagePicker;
    languageCardButton.onclick = reopenLanguagePicker;

    document.querySelectorAll('.lang-tab').forEach(tab => {
        tab.addEventListener('click', async function() {
            // Prevent clicking on disabled tabs
            if (this.disabled || this.classList.contains('disabled')) {
                return;
            }
            // The language already in use: nothing to switch.
            if (this.dataset.lang === selectedLanguage && currentLearningMode()
                && sessionStorage.getItem('fluencyPendingSpeechLanguage') !== this.dataset.lang) {
                return;
            }
            document.getElementById('step1')?.classList.remove('source-speech-active', 'context-ready');
            document.body.classList.remove('has-learning-context');
            document.querySelectorAll('.lang-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            const newLanguage = this.dataset.lang;

            // Drop cached frequency data when switching languages — new
            // language will reload its own ppm. percentageMode is the user's
            // preference and persists across language switches.
            if (newLanguage !== selectedLanguage) {
                ppmData = null;
                totalPpm = 0;
                // Examples and optional linguistic assets are source-scoped,
                // not universal app globals. Clear the active pointers before
                // selecting another language so a cached Spanish split cannot
                // make French cards appear to have no examples (or vice versa).
                window.clearActiveExamplesData?.();
                window.resetLanguageOptionalData?.();
                if (window.playlistLiveDeck?.()?.language !== newLanguage) {
                    window.clearPlaylistLiveSession?.();
                }
                if (window.activeArtist && window.activeArtist.language !== newLanguage) {
                    window.resetActiveArtist?.();
                }
            }

            selectedLanguage = newLanguage;
            try { localStorage.setItem(PREFERRED_LANGUAGE_KEY, newLanguage); } catch (_) {}
            selectedLevel = null;
            _setupLevelSelectionWasManual = false;
            applyGlobalStudyDefaults();

            applyLanguageColorTheme();

            // Show inline pill in the header, hide the tabs
            const langConfig = config.languages[selectedLanguage];
            inlinePill.textContent = langConfig ? langConfig.name : selectedLanguage;
            document.getElementById('languageTabs').style.display = 'none';
            inlinePill.style.display = 'inline-flex';
            sourceLabel.textContent = 'Speech';
            sourcePill.classList.add('source-pill-inline--pending');
            mergeStandardProgressIntoLanguageStep();
            updateLearningContextUI();
            document.getElementById('step1')?.classList.remove('source-speech-active');
            speechSourceButton?.classList.remove('is-selected');
            sourceCardButton?.classList.remove('is-selected');

            const languageCapabilities = langConfig?.capabilities || {};
            const speechAvailable = languageCapabilities.speech !== false;
            const lyricsCatalog = languageCapabilities.lyrics !== false;
            const musicOpen = musicOpenFor(newLanguage);
            const lyricsAvailable = (lyricsCatalog || speechAvailable) && musicOpen;
            if (speechSourceButton) {
                speechSourceButton.disabled = !speechAvailable;
                speechSourceButton.title = speechAvailable
                    ? 'Starts with the most common words in films and TV shows'
                    : `Speech vocabulary is not ready for ${langConfig?.name || newLanguage} yet`;
            }
            const modeCopy = learningModeCopy(newLanguage);
            paintModeButton(speechSourceButton, modeCopy.speech);
            paintModeButton(sourceCardButton, modeCopy.lyrics);
            const seriesAvailable = window.seriesOpenFor?.(newLanguage) === true;
            document.getElementById('standardSourceSeriesCard').hidden = !seriesAvailable;
            document.querySelector('.standard-source-choice-buttons')?.classList.toggle('has-series-choice', seriesAvailable);
            paintModeButton(seriesButton, modeCopy.series);
            seriesButton.onclick = () => window.openSeriesMode?.(newLanguage);
            const choiceTitle = document.getElementById('standardSourceChoiceTitle');
            const choiceIntro = document.getElementById('standardSourceChoiceIntro');
            if (choiceTitle) choiceTitle.textContent = modeCopy.title;
            if (choiceIntro) {
                choiceIntro.replaceChildren(...modeCopy.intro.map(text => {
                    const item = document.createElement('li');
                    item.textContent = text;
                    return item;
                }));
            }
            const spotifyFooter = document.getElementById('standardSourceSpotify');
            if (spotifyFooter) spotifyFooter.hidden = !musicOpen;
            if (musicOpen) window.renderSpotifyStatus?.(spotifyFooter);
            if (sourceCardButton) {
                sourceCardButton.disabled = !lyricsAvailable;
                sourceCardButton.title = lyricsCatalog
                    ? 'Starts with the most common words in the music you listen to'
                    : 'Look up lyrics from a playlist and study a live deck';
            }
            // Nothing belonging to a deck shows until a vocabulary is chosen.
            hideStudySurfaces();

            const continueToSpeech = async () => {
                if (selectedLanguage !== newLanguage) return;
                document.getElementById('step1')?.classList.add('source-speech-active');
                speechSourceButton?.classList.add('is-selected');
                sourceCardButton?.classList.remove('is-selected');
                window.showAppLoading?.(window.isSeriesStudy?.() ? 'Preparing TV Series vocabulary' : 'Preparing speech vocabulary', 'Loading levels and your progress…');
                const speechSetupStarted = performance.now();
                let deckOverviewHold = null;
                try {
                    if (window.playlistLiveActive?.()) {
                        const liveName = window.playlistLiveDeck?.()?.playlistName;
                        sourceLabel.textContent = window.isSeriesStudy?.() ? `TV Series · ${liveName}` : liveName ? `Live · ${liveName}` : 'Live playlist';
                        document.getElementById('step1').style.display = 'none';
                    } else {
                        sourceLabel.textContent = 'Speech';
                    }
                    sourcePill.classList.remove('source-pill-inline--pending');
                    const loadingIndicator = document.getElementById('dataLoadingIndicator');
                    loadingIndicator.classList.add('visible');

                    // Start refreshing progress from Sheets (cache loads synchronously inside).
                    let progressRefresh = Promise.resolve(false);
                    if (currentUser && !currentUser.isGuest) {
                        progressRefresh = loadUserProgressFromSheet();
                    }

                    // Spanish rank and conjugated-English assets belong to
                    // Speech setup. Do not start them merely because Spanish
                    // was chosen when the learner may be heading to Lyrics.
                    // Conjugation tables feed both the Conjugate drawer and
                    // inflected English glosses, so load them for any Speech
                    // language that declares conjugationsPath.
                    // Conjugation tables feed the Conjugate drawer. Prefetch
                    // them without blocking Speech setup: Portuguese's file is
                    // a megabyte, and the 75 MB index is the actual wait.
                    if (newLanguage === 'spanish') {
                        if (window.loadSpanishRanks) window.loadSpanishRanks();
                        if (window.loadConjugatedEnglishData) window.loadConjugatedEnglishData();
                    }
                    if (window.loadConjugationData) window.loadConjugationData();
                    if (window.loadSourceTitles) window.loadSourceTitles();

                    // Always load PPM data if available (needed for coverage bar even in CEFR mode).
                    const langPpmPath = config.languages[selectedLanguage] && config.languages[selectedLanguage].ppmDataPath;
                    if (!ppmData && langPpmPath) {
                        await timePhase('loadPpmData', () => loadPpmData(selectedLanguage));
                    }
                    await timePhase('loadReleaseStudyStructure',
                        () => loadReleaseStudyStructure(selectedLanguage));

                    loadingIndicator.classList.remove('visible');
                    document.getElementById('step2').style.display = 'block';
                    setActiveSetupStep('step2');
                    updatePercentModeButton();
                    updateStep2Tooltip();
                    updateStep5Tooltip();

                    // Order matters here. The two toggle-visibility calls run
                    // first because each can switch its filter off for a release
                    // that lacks the capability, and both filters feed the
                    // prepared-vocabulary signature the coverage figure is
                    // computed against -- reading it before them could show a
                    // number that then changes. Whichever of them touches the
                    // index first pays for it; renderLevelSelector then hits the
                    // memo. updateExclusionBars publishes the coverage snapshot,
                    // so by the time the wheel goes up its figures are final and
                    // the level selector can build behind it instead of ahead.
                    await timePhase('updateLemmaToggleVisibility',
                        () => updateLemmaToggleVisibility());
                    await timePhase('updateCognateToggleVisibility',
                        () => updateCognateToggleVisibility());
                    await timePhase('updateExclusionBars', () => updateExclusionBars());
                    deckOverviewHold = showDeckOverviewLoading();
                    // Everything below this marker runs while the wheel is up, so
                    // the table says how much of the hold covered real work.
                    _setupTimings.push({ phase: '-- deck wheel raised --', ms: 0 });
                    await timePhase('renderLevelSelector',
                        () => renderLevelSelector(selectedLanguage, { preferActionable: true }));
                    reportSetupTimings(performance.now() - speechSetupStarted);
                    updateIncorrectButtonVisibility();
                    document.getElementById('step1')?.classList.add('context-ready');
                    document.body.classList.add('has-learning-context');
                    updateLearningContextUI();

                    if (sessionStorage.getItem('fluencyPendingLiveStudy') === '1' && window.playlistLiveActive?.() && !window.musicWorkspaceActive?.()) {
                        sessionStorage.removeItem('fluencyPendingLiveStudy');
                        await startSelectedStudySession();
                    }

                    progressRefresh.then(changed => {
                        const setupPanel = document.getElementById('setupPanel');
                        if (changed && setupPanel && !setupPanel.classList.contains('hidden')) {
                            window.refreshSetupAfterProgress?.();
                        }
                    }).catch(() => {});
                    updateTotalStatsButtonVisibility();
                } finally {
                    document.getElementById('dataLoadingIndicator')?.classList.remove('visible');
                    await deckOverviewHold;
                    window.hideAppLoading?.();
                }
                window.renderResumeLastSetCard?.();
                if (!window.maybeShowKnownLanguagesIntro?.(newLanguage)) {
                    if (!window.maybeShowFrequencyIntro?.()) window.openFirstRunCardTutorial?.();
                }
            };
            window.continueToSpeechAfterLive = continueToSpeech;

            // Language selection is deliberately lightweight. The learner now
            // chooses the source before either vocabulary release is fetched.
            const openLyrics = event => {
                event.stopPropagation();
                if (sourceCardButton?.disabled) return;
                speechSourceButton?.classList.remove('is-selected');
                sourceCardButton?.classList.add('is-selected');
                updateLearningContextUI();
                window.showLyricsPicker?.(newLanguage, sourceCardButton);
            };
            sourcePill.onclick = openLyrics;
            sourceCardButton.onclick = openLyrics;
            speechSourceButton.onclick = event => {
                event.stopPropagation();
                if (speechSourceButton.disabled) return;
                continueToSpeech();
            };

            if (!window.maybeShowKnownLanguagesIntro?.(newLanguage)) {
                window.maybeShowFrequencyIntro?.();
            }

            const pendingSpeechLanguage = sessionStorage.getItem('fluencyPendingSpeechLanguage');
            if (pendingSpeechLanguage === newLanguage) {
                sessionStorage.removeItem('fluencyPendingSpeechLanguage');
                await continueToSpeech();
            }
        });
    });
}

window.updateLearningContextUI = updateLearningContextUI;

function hideAllSelectionPills() {
    document.querySelectorAll('.selection-pill').forEach(pill => {
        pill.classList.remove('visible');
    });
}

function updatePercentModeButton() {
    // CEFR is now a single on/off toggle. "Off" (the default) means
    // percentage mode — the standard experience. "On" lights up the button
    // and switches the level selector to CEFR pills.
    const toggle = document.getElementById('levelModeToggle');
    if (!toggle) return;
    toggle.classList.toggle('active', !percentageMode);
}

function updateStep2Tooltip() {
    const tooltip = document.getElementById('step2Tooltip');
    if (!tooltip) return;
    const description = document.getElementById('step2LevelDescription');
    const estimateCallout = document.getElementById('step2LevelEstimateCallout');
    const estimatedRow = document.getElementById('step2EstimatedLegend');
    if (estimatedRow) estimatedRow.hidden = !((levelEstimates[selectedLanguage] || 0) > 0);
    if (activeArtist) {
        const name = activeArtist.name;
        if (description) description.textContent = `Words from ${name}'s lyrics are ordered from most to least common.`;
        if (estimateCallout) estimateCallout.style.display = 'none';
    } else {
        if (description) {
            description.textContent = 'Words are ordered from most to least common.';
        }
        if (estimateCallout) estimateCallout.style.display = 'flex';
    }
}

function updateStep5Tooltip() {
    const description = document.getElementById('step5Description');
    if (!description) return;
    description.innerHTML = 'Words you know are marked <strong>Known</strong>. Words you don\'t know yet go to <strong>Practise</strong> for review.';
}

// Annotates every level control with its completion percentage and returns
// the first level that still has work. The visible scrubber gets a small
// partial-progress bar; its hidden .level-btn keeps the same data for setup
// logic and the non-slider fallback.
async function findFirstIncompleteLevelBtn(language, buttons) {
    const langConfig = config.languages[language];
    if (!langConfig) return null;
    const vocabularyData = await fetchActiveVocabularyData(langConfig);
    const filteredVocab = getPreparedSetupVocabulary(language, vocabularyData)?.vocab || [];
    const estimate = levelEstimates[language] || 0;
    const estimatedIds = (activeArtist && !window.playlistLiveActive?.()) && currentUser && !currentUser.isGuest
        ? await buildEstimatedKnownIds(estimate)
        : null;
    const seenLemmas = await window.buildSeenLemmaSet?.(vocabularyData) || new Set();
    const wordSeen = item => {
        // Use the exact same identity rules as the set dots and Learn New:
        // current + cross-mode surface progress, granular knowledge, merged
        // lemma inheritance, and the level estimate. The former coarse check
        // could call Level 1 incomplete while every one of its sets was 100%,
        // which then made renderRangeSelector fall back to its last set.
        return getSetupLearningState(item, {
            seenLemmas,
            estimatedIds,
            estimate,
        }).seen;
    };

    let firstIncomplete = null;
    let firstWithReview = null;
    let lastAvailable = null;

    const sliderSegmentMap = new Map();
    document.querySelectorAll('#lswSlider .lsw-seg').forEach(seg => {
        if (seg.dataset.i !== undefined) sliderSegmentMap.set(seg.dataset.i, seg);
    });

    const parsedButtons = [];
    // CEFR is deprecated; release levels or percentage frequency bands are authoritative.
    for (let buttonIndex = 0; buttonIndex < buttons.length; buttonIndex++) {
        const btn = buttons[buttonIndex];
        let minWord, maxWord;
        let rankBasis = 'source';
        if (btn.dataset.releaseLevel === 'true') {
            minWord = parseInt(btn.dataset.startRank);
            maxWord = parseInt(btn.dataset.endRank);
            rankBasis = 'source';
        } else if (btn.dataset.startRank && btn.dataset.endRank) {
            minWord = parseInt(btn.dataset.startRank);
            maxWord = parseInt(btn.dataset.endRank);
            rankBasis = btn.dataset.rankBasis || 'source';
        } else {
            continue;
        }
        parsedButtons.push({
            btn,
            buttonIndex,
            minWord,
            maxWord,
            rankFn: _levelRankAccessor(rankBasis),
            words: []
        });
    }

    if (parsedButtons.length > 0) {
        // Distribute vocabulary in a single pass, breaking as soon as the matching range is found
        for (let i = 0; i < filteredVocab.length; i++) {
            const it = filteredVocab[i];
            for (let j = 0; j < parsedButtons.length; j++) {
                const p = parsedButtons[j];
                const rank = p.rankFn(it);
                if (rank >= p.minWord && rank < p.maxWord) {
                    p.words.push(it);
                    break;
                }
            }
        }
    }

    for (let i = 0; i < parsedButtons.length; i++) {
        const { btn, buttonIndex, words: wordsInLevel } = parsedButtons[i];
        if (wordsInLevel.length === 0) continue;
        lastAvailable = btn;
        let seenCount = 0;
        let reviewCount = 0;
        let estimatedCount = 0;
        for (let w = 0; w < wordsInLevel.length; w++) {
            const st = getSetupLearningState(wordsInLevel[w], { seenLemmas, estimatedIds, estimate });
            if (st?.seen) seenCount++;
            if (st?.needsReview) reviewCount++;
            if (st?.estimated) estimatedCount++;
        }
        const completion = Math.round(100 * seenCount / wordsInLevel.length);
        const hasUnseen = seenCount < wordsInLevel.length;
        const isPartial = seenCount > 0 && hasUnseen;
        const isComplete = seenCount > 0 && !hasUnseen;
        const hasProgress = seenCount > 0;
        const hasReview = reviewCount > 0;
        const autoCompleted = isComplete && estimatedCount > 0;
        const hasStarted = seenCount > 0;
        const allGreen = wordsInLevel.length > 0 && isComplete && reviewCount === 0;
        const hasYellow = hasReview;
        const isWhite = hasStarted && !allGreen && !hasYellow;
        btn.classList.toggle('is-auto-complete', autoCompleted);
        btn.dataset.autoCompleted = String(autoCompleted);
        btn.dataset.progressPct = String(completion);
        btn.dataset.reviewCount = String(reviewCount);
        btn.classList.toggle('has-progress', hasProgress);
        btn.classList.toggle('has-partial-progress', isPartial);
        btn.classList.toggle('has-review', hasReview);
        btn.classList.toggle('is-complete', isComplete);
        btn.classList.toggle('dot-green', allGreen);
        btn.classList.toggle('dot-yellow', hasYellow);
        btn.classList.toggle('dot-white', isWhite);
        btn.style.setProperty('--level-progress', `${completion}%`);

        const visibleSegment = sliderSegmentMap.get(String(buttonIndex));
        if (visibleSegment) {
            visibleSegment.classList.toggle('is-auto-complete', autoCompleted);
            visibleSegment.dataset.autoCompleted = String(autoCompleted);
            visibleSegment.dataset.progressPct = String(completion);
            visibleSegment.classList.toggle('has-progress', hasProgress);
            visibleSegment.classList.toggle('has-partial-progress', isPartial);
            visibleSegment.classList.toggle('has-review', hasReview);
            visibleSegment.classList.toggle('is-complete', isComplete);
            visibleSegment.classList.toggle('dot-green', allGreen);
            visibleSegment.classList.toggle('dot-yellow', hasYellow);
            visibleSegment.classList.toggle('dot-white', isWhite);
            visibleSegment.style.setProperty('--level-progress', `${completion}%`);
            visibleSegment.setAttribute(
                'aria-label',
                autoCompleted ? `Level ${buttonIndex + 1}, AUTO` : `Level ${buttonIndex + 1}, ${completion}% complete`
            );
        }
        if (!firstIncomplete && hasUnseen) firstIncomplete = btn;
        if (!firstWithReview && reviewCount > 0) firstWithReview = btn;
    }
    return firstIncomplete || firstWithReview || lastAvailable || buttons[buttons.length - 1];
}

async function renderLevelSelector(language, { preferActionable = false } = {}) {
    // `preferActionable` picks the level to land on from per-level seen/unseen
    // counts, which are read from progressData. Same race as
    // renderRangeSelector: answering it before progress arrives sends the
    // learner to level 1 regardless of where they actually are.
    if (currentUser && !currentUser.isGuest) {
        await (window.whenProgressReady?.() ?? Promise.resolve(true));
    }
    resetSetupStateMemo();
    const container = document.getElementById('levelSelector');
    if (preferActionable) _setupLevelSelectionWasManual = false;

    if (useLemmaMode) {
        const baseConfig = config.languages[language] || {};
        const langConfig = activeArtist ? { ...baseConfig, ...activeArtist } : baseConfig;
        await ensureLemmaPoolingData(langConfig);
    }
    if (!selectedLevel) setActiveSetupStep('step2');

    // Artist Extra replaces frequency levels with category groups.
    if (activeArtist && artistVocabularyScope === 'extra') {
        await renderExtraCategorySelector(container, language, { preferActionable });
        return;
    }

    // Debug logging
    console.log('renderLevelSelector called:', { percentageMode, ppmDataLength: ppmData ? ppmData.length : 0, language });

    // Use percentage levels if in percentage mode with PPM data.
    // In percentage mode the user picks a level via a log-spaced slider:
    // each snap point is one of the percentageLevels (70%, 80%, …, 100%).
    // The level buttons are still rendered (hidden) because renderRangeSelector
    // and other code paths read .level-btn.selected for startRank/endRank.
    const releaseLevels = !activeArtist && !window.playlistLiveActive?.() && Array.isArray(releaseStudyStructure?.levels)
        ? releaseStudyStructure.levels
        : [];
    // Speech releases used to ship their own levels. The app now builds
    // levels for every mode (computeSmartLevelRanges), so releaseStudyStructure
    // stays null and the release-level branches below are inert.
    const usingReleaseLevels = releaseLevels.length > 0;
    if (usingReleaseLevels) {
        _smartLevelRangesCache = releaseLevels.map(level => ({
            level: level.level_id,
            startRank: level.start_rank,
            // Ranges are half-open everywhere else in setup; the release states
            // an inclusive end.
            endRank: level.end_rank + 1,
            cardCount: level.card_count,
            rankBasis: 'source',
            description: level.label,
        }));
    } else if (window.playlistLiveActive?.()) {
        const samples = await _loadLevelSliderSamples(language);
        const totalCards = samples?.length || 0;
        const targetPerLevel = STUDY_LEVEL_TARGET_CARDS;
        const levelCount = Math.max(1, Math.ceil(totalCards / targetPerLevel));
        _smartLevelRangesCache = [];
        for (let i = 0; i < levelCount; i++) {
            const startRank = i * targetPerLevel + 1;
            const endRank = Math.min((i + 1) * targetPerLevel + 1, totalCards + 1);
            _smartLevelRangesCache.push({
                level: i + 1,
                startRank,
                endRank,
                cardCount: Math.max(0, endRank - startRank),
                rankBasis: 'source',
                description: `Level ${i + 1} (${startRank}–${endRank - 1})`
            });
        }
    } else {
        _smartLevelRangesCache = null;
    }
    const preparedSamples = await _loadLevelSliderSamples(selectedLanguage);
    const cacheKey = activeArtist ? `artist:${activeArtist.slug || window._urlArtistSlug || selectedLanguage}` : selectedLanguage;
    const _raw = _levelSliderRawCache[cacheKey];
    if (_raw && !usingReleaseLevels) {
        if (!window.playlistLiveActive?.()) {
            // Level boundaries are built from the stable baseline before any
            // optional filters. Filters change the eligible card count inside
            // a level, never the level's identity or rank span.
            const prepared = getPreparedSetupVocabulary(selectedLanguage, _raw);
            _smartLevelRangesCache = computeSmartLevelRanges(prepared?.stableBaseline || []);
            const eligible = prepared?.vocab || [];
            const lastEligibleRank = eligible.reduce((maxRank, item) =>
                Math.max(maxRank, Number(item.stableRank) || 0), 0);
            // Hide only empty trailing levels (most notably the reserved 1×
            // tail while single-occurrence words are hidden). Re-enabling a
            // filter appends those levels without changing any earlier cut.
            _smartLevelRangesCache = _smartLevelRangesCache.filter(range =>
                range.startRank <= lastEligibleRank);
        }
    }
    const percentageRanges = getActiveLevelRanges();
        console.log('Using percentage levels:', percentageRanges);
        const coverageType = activeArtist
            ? 'lyrics comprehension'
            : (window.playlistLiveActive?.()
                ? (window.isSeriesStudy?.() ? 'series dialogue' : 'playlist words')
                : (globalThis.coverageAvailable?.()
                    && (usingReleaseLevels || getActiveLevelRanges()[0]?.threshold == null)
                    ? globalThis.coverageLabel()
                    : 'speech comprehension'));
        const buttonsHTML = percentageRanges.map(level => {
            const description = level.description || `${level.level} ${coverageType}`;
            const isSelected = level.level === selectedLevel;
            return `
            <button class="level-btn${isSelected ? ' selected' : ''}" data-level="${level.level}" data-short="${level.level}" data-full="${description}" data-start-rank="${level.startRank}" data-end-rank="${level.endRank}" data-rank-basis="${level.rankBasis || 'source'}"${usingReleaseLevels ? ' data-release-level="true"' : ''} title="${description}">
                ${isSelected ? description : level.level}
            </button>
        `}).join('');

        // The partition remains frequency-aware, but its controls use stable,
        // plain numbered levels. Frequency details live in the explanatory
        // line below instead of competing with navigation labels.
        const ticksHTML = percentageRanges.map((lv, i) => {
            const label = `Level ${i + 1}`;
            const tooltip = lv.description || `${lv.level} coverage → top ${lv.endRank.toLocaleString()} words`;
            return `<span data-i="${i}" title="${tooltip}">${label}</span>`;
        }).join('');

        const lastIdx = percentageRanges.length - 1;
        // Restore slider position from selectedLevel if a level is already
        // chosen — otherwise re-renders (lemma toggle, etc.) would snap the
        // thumb back to the rightmost snap and visually disagree with the
        // hidden .level-btn.selected.
        let savedIdx = selectedLevel
            ? percentageRanges.findIndex(r => r.level === selectedLevel)
            : -1;
        // Older saved selections may use a level id from the pre-stable
        // partition. Adopt the nearest baseline boundary once; current filter
        // toggles keep the exact stable id thereafter.
        if (savedIdx < 0 && selectedLevel && /^c\d+$/.test(selectedLevel)) {
            const targetCards = parseInt(selectedLevel.slice(1), 10);
            let bestD = Infinity;
            percentageRanges.forEach((r, i) => {
                const d = Math.abs((r.cardCount || 0) - targetCards);
                if (d < bestD) { bestD = d; savedIdx = i; }
            });
            if (savedIdx >= 0) selectedLevel = percentageRanges[savedIdx].level;
        }
        // Coverage levels are cumulative, so the widest is the useful default.
        // App-built levels are consecutive 100-card bands, where the last one
        // is the rarest vocabulary in the deck — a learner starts at the
        // first, and the actionable-level pass refines it from there.
        const consecutiveLevels = usingReleaseLevels || window.playlistLiveActive?.()
            || (_smartLevelRangesCache?.length > 0);
        const initialIdx = savedIdx >= 0 ? savedIdx : (consecutiveLevels ? 0 : lastIdx);
        const initial = percentageRanges[initialIdx];
        if (!initial) {
            console.warn('No level ranges available for', language);
            container.innerHTML = '<div class="level-selector-empty">No levels available</div>';
            return;
        }
        // Coverage display. Ranges built from corpus counts carry their own
        // coverage. Speech levels are a pure ordering, so the figure comes
        // from the shipped corpus shares when the
        // language has them, and the span stays hidden when it does not —
        // printing the level id where a percentage belongs read as a glitch.
        const releaseCoverage = initial.threshold == null
            ? globalThis.levelCoverage?.(preparedSamples, initial.startRank, initial.endRank)
            : null;
        const initialCoverage = initial.threshold != null
            ? `${(initial.threshold * 100).toFixed(1)}%`
            : (releaseCoverage != null ? `${(releaseCoverage * 100).toFixed(1)}%` : '');
        container.classList.add('level-selector--slider');
        container.innerHTML = `
            <div class="level-slider-wrap">
                <div class="home-level-tiles" id="homeLevelTiles" role="radiogroup" aria-label="Levels" hidden></div>
                <div class="home-level-stepper" id="homeLevelStepper">
                    <button type="button" class="home-level-step" data-level-step="-1" aria-label="Previous level">‹</button>
                    <div class="home-level-readout" aria-live="polite">
                        <span class="home-level-eyebrow">Level</span>
                        <strong id="homeLevelNumber">${initialIdx + 1}</strong>
                        <span id="homeLevelWords" class="home-level-words"></span>
                    </div>
                    <button type="button" class="home-level-step" data-level-step="1" aria-label="Next level">›</button>
                </div>
                <div id="lswSlider" class="lsw-segments lsw-scrubber" role="radiogroup" aria-label="Level scrubber" data-value="${initialIdx}">
                    ${percentageRanges.map((lv, i) => {
                        const segLabel = `${i + 1}`;
                        const metrics = _levelBandMetrics(lv);
                        const wordRange = `${metrics.start.toLocaleString()}–${metrics.end.toLocaleString()}`;
                        return `<button type="button" class="lsw-seg${i <= initialIdx ? ' filled' : ''}${i === initialIdx ? ' selected' : ''}" data-i="${i}" style="--dist:${Math.abs(i - initialIdx)}" aria-label="Level ${i + 1} of ${percentageRanges.length}, words ${wordRange}" role="radio" aria-checked="${i === initialIdx}"><span class="lsw-seg-label"><span class="lsw-seg-heading"><span class="lsw-seg-eyebrow">Level</span><span class="lsw-seg-num">${segLabel}</span></span><span class="lsw-seg-words"><small>Words</small> ${wordRange}</span><span class="lsw-seg-total">of ${_levelBandMetrics(percentageRanges[percentageRanges.length - 1]).end.toLocaleString()} words</span></span></button>`;
                    }).join('')}
                </div>
                <div class="lsw-ticks lsw-ticks--hidden">${ticksHTML}</div>
                <div class="lsw-examples" id="lswExamples">&nbsp;</div>
            </div>
            <div class="level-selector-buttons" style="display:none">${buttonsHTML}</div>
        `;
        // The deck's size lives in the level help, not on the badge (SETWISE-2).
        const deckTotalEl = document.getElementById('step2DeckTotal');
        if (deckTotalEl) {
            const liveDeck = window.playlistLiveActive?.() ? window.playlistLiveDeck?.() : null;
            const isSeries = Boolean(liveDeck?.playlistId === 'la-casa-de-papel' || (liveDeck?.playlistName && /casa de papel|series|show|tv/i.test(liveDeck.playlistName)));
            const deckWords = percentageRanges.reduce((sum, lv) => sum + (_levelBandMetrics(lv).count || 0), 0);
            if (isSeries && liveDeck) {
                deckTotalEl.textContent = `This series deck has ${deckWords.toLocaleString()} words across ${percentageRanges.length.toLocaleString()} level${percentageRanges.length === 1 ? '' : 's'} from ${Number(liveDeck.tokenCount || 0).toLocaleString()} dialogue tokens across ${liveDeck.trackCount || 1} episode${liveDeck.trackCount === 1 ? '' : 's'} in ${liveDeck.playlistName}.`;
            } else if (liveDeck) {
                deckTotalEl.textContent = `This playlist deck has ${deckWords.toLocaleString()} words across ${percentageRanges.length.toLocaleString()} level${percentageRanges.length === 1 ? '' : 's'} from ${Number(liveDeck.tokenCount || 0).toLocaleString()} words across ${liveDeck.trackCount || 1} song${liveDeck.trackCount === 1 ? '' : 's'}.`;
            } else {
                deckTotalEl.textContent = deckWords > 0
                    ? `This deck has ${deckWords.toLocaleString()} words across ${percentageRanges.length.toLocaleString()} level${percentageRanges.length === 1 ? '' : 's'}.`
                    : '';
            }
            deckTotalEl.hidden = !(deckWords > 0);
        }

    // Add click handlers for level buttons
    document.querySelectorAll('.level-btn').forEach(btn => {
        btn.addEventListener('click', function(event) {
            if (event.isTrusted) _setupLevelSelectionWasManual = true;
            // Reset all buttons to short text
            document.querySelectorAll('.level-btn').forEach(b => {
                b.classList.remove('selected');
                b.textContent = b.dataset.short;
            });
            // Set selected button to full text
            this.classList.add('selected');
            this.textContent = this.dataset.full;
            selectedLevel = this.dataset.level;

            // Show coverage info line with word count and frequency threshold
            updateLevelInfoLine(this);

            // Surface identity and learner grouping are separate. Offer Merge
            // Lemmas whenever the release can reliably map surfaces back to a
            // shared headword; otherwise keep the unavailable option hidden.
            document.getElementById('lemmaToggleContainer').style.display =
                lemmaFieldAvailable ? 'block' : 'none';

            // Show cognate toggle after lemma toggle (if available)
            setTimeout(() => {
                if (cognateFieldAvailable) {
                    document.getElementById('cognateToggleContainer').style.display = 'block';
                }
            }, 75);

            this._rangeRenderPromise = renderRangeSelector();
            this._rangeRenderPromise.catch(err => console.error('Error rendering ranges:', err));

            // Keep the segmented bar in sync when a (hidden) level button
            // is chosen programmatically — e.g. auto-select on first load,
            // or the "Next Level" range button. Segment-driven clicks are
            // a no-op here because the bar already matches.
            const segBar = document.getElementById('lswSlider');
            if (segBar) {
                const buttons = Array.from(document.querySelectorAll('.level-selector-buttons .level-btn'));
                const idx = buttons.indexOf(this);
                if (idx >= 0) {
                    if (+segBar.dataset.value !== idx) setLevelSegmentSelection(idx);
                    if (!_levelScrubberInitiated) {
                        _scrollLevelSegToCenter(idx, false); // keep the scrubber centered on the picked level
                    }
                }
            }
        });
    });

    // Wire the segmented level bar: each segment = one snap point. Clicking
    // a segment selects the range from start through that segment (the
    // "line within the line" fill) and clicks the matching hidden level
    // button, which runs the existing level-selection flow.
    const segBar = document.getElementById('lswSlider');
    if (segBar) {
        const buttons = Array.from(document.querySelectorAll('.level-selector-buttons .level-btn'));
        wireLevelScrubber(segBar, buttons);
        wireHomeLevelStepper(buttons);
        syncHomeLevelStepper(parseInt(segBar.dataset.value || '0', 10));
        // Prime the readout (examples need vocab to be loaded async).
        updateLevelSliderReadout(parseInt(segBar.dataset.value || '0', 10));
        // Center the scrubber on the initial selection once layout has settled.
        requestAnimationFrame(() =>
            _scrollLevelSegToCenter(parseInt(segBar.dataset.value || '0', 10), false));
    }

    const levelButtons = Array.from(document.querySelectorAll('.level-btn'));
    const levelProgressPromise = levelButtons.length > 0
        ? findFirstIncompleteLevelBtn(language, levelButtons)
        : Promise.resolve(null);

    // Auto-select first time only (preserves manual picks across re-renders).
    // Pick the first level that isn't fully completed so the user lands on
    // actionable work — finishing the 70% level should auto-open 80%, not
    // sit on a level whose sets are already complete. Falls back to the
    // first button on data-load failure or if there are no buttons.
    if (!selectedLevel || preferActionable) {
        if (levelButtons.length === 0) return;
        let target = levelButtons[0];
        try {
            const incomplete = await levelProgressPromise;
            if (incomplete) target = incomplete;
        } catch (err) {
            console.warn('Level auto-pick failed, using first', err);
        }
        // Re-check: the user may have clicked a level during the await above.
        if (!_setupLevelSelectionWasManual && (!selectedLevel || preferActionable)) {
            target.click();
            await target._rangeRenderPromise;
            const targetIdx = levelButtons.indexOf(target);
            if (targetIdx >= 0) {
                requestAnimationFrame(() => _scrollLevelSegToCenter(targetIdx, false));
            }
        }
    } else {
        const matchingBtn = levelButtons.find(b => b.dataset.level === selectedLevel);
        if (matchingBtn && !document.querySelector('.level-btn.selected')) {
            matchingBtn.click();
            await matchingBtn._rangeRenderPromise;
            const matchIdx = levelButtons.indexOf(matchingBtn);
            if (matchIdx >= 0) {
                requestAnimationFrame(() => _scrollLevelSegToCenter(matchIdx, false));
            }
        }
        levelProgressPromise.catch(err =>
            console.warn('Level progress indicators unavailable', err));
    }
}

function _escapeAttr(value) {
    return String(value == null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Artist Extra category picker. Replaces the frequency slider with one pickable
// group per distinct `extra_category` value. Each category is backed by a
// hidden `.level-btn` carrying its category rank block, so the existing
// renderRangeSelector()/study-set machinery pages through it unchanged. If the
// data has no categories yet, buildFilteredVocab() returns a single "All Extra"
// group and this renders one chip.
async function renderExtraCategorySelector(container, language, { preferActionable = false } = {}) {
    const langConfig = config.languages[language];
    let vocabularyData = [];
    try {
        vocabularyData = await fetchActiveVocabularyData(langConfig);
    } catch (error) {
        console.error('Failed to load vocabulary data for Extra categories:', error);
    }
    // Populate categoryRank + the ordered group metadata.
    buildFilteredVocab(vocabularyData);
    const groups = (window.getExtraCategoryGroups?.() || []);

    container.classList.remove('level-selector--slider');

    if (groups.length === 0) {
        container.innerHTML = '<div class="study-set-empty">No Extra vocabulary is available with the current settings.</div>';
        return;
    }

    const chipsHTML = groups.map((group, index) => `
        <button type="button" class="extra-category-chip" data-cat-index="${index}"
                role="radio" aria-checked="false"
                aria-label="${_escapeAttr(group.label)}, ${group.count} word${group.count === 1 ? '' : 's'}">
            <span class="extra-category-chip-label">${_escapeAttr(group.label)}</span>
            <span class="extra-category-chip-count">${group.count.toLocaleString()}</span>
        </button>
    `).join('');

    const hiddenButtonsHTML = groups.map(group => `
        <button class="level-btn" data-level="cat:${_escapeAttr(group.key)}"
                data-short="${_escapeAttr(group.label)}" data-full="${_escapeAttr(group.label)}"
                data-start-rank="${group.startRank}" data-end-rank="${group.endRank}"
                data-rank-basis="category" title="${_escapeAttr(group.label)}">
            ${_escapeAttr(group.label)}
        </button>
    `).join('');

    container.innerHTML = `
        <div class="extra-category-selector">
            <p class="extra-category-intro">Extra vocabulary is grouped by kind, not by how often it appears. Pick a group to study.</p>
            <div class="extra-category-chips" role="radiogroup" aria-label="Extra vocabulary categories">
                ${chipsHTML}
            </div>
        </div>
        <div class="level-selector-buttons" style="display:none">${hiddenButtonsHTML}</div>
    `;

    const hiddenButtons = Array.from(container.querySelectorAll('.level-selector-buttons .level-btn'));
    const chips = Array.from(container.querySelectorAll('.extra-category-chip'));

    const selectCategory = async index => {
        hiddenButtons.forEach((btn, i) => btn.classList.toggle('selected', i === index));
        chips.forEach((chip, i) => {
            const selected = i === index;
            chip.classList.toggle('selected', selected);
            chip.setAttribute('aria-checked', selected ? 'true' : 'false');
        });
        selectedLevel = hiddenButtons[index].dataset.level;
        // Merge Lemmas and Exclude Cognates are meaningless in Extra (Exclude
        // Cognates only changes which category cognates land in), so hide both.
        document.getElementById('lemmaToggleContainer').style.display = 'none';
        document.getElementById('cognateToggleContainer').style.display = 'none';
        await renderRangeSelector();
    };

    // Wire hidden buttons so getNextStudyLevelMeta()/startNextStudyLevelFirstSet()
    // (which .click() the next .level-btn) reuse this exact selection path.
    hiddenButtons.forEach((btn, index) => {
        btn.addEventListener('click', () => {
            btn._rangeRenderPromise = selectCategory(index);
            btn._rangeRenderPromise.catch(err => console.error('Error rendering Extra ranges:', err));
        });
    });
    chips.forEach((chip, index) => {
        chip.addEventListener('click', () => {
            _setupLevelSelectionWasManual = true;
            hiddenButtons[index].click();
        });
    });

    // Preserve an explicit category choice; on landing/return, route to the
    // first category that still contains unseen cards and is not skipped.
    let initialIndex = 0;
    if (selectedLevel && !preferActionable) {
        const saved = hiddenButtons.findIndex(btn => btn.dataset.level === selectedLevel);
        if (saved >= 0) initialIndex = saved;
        else selectedLevel = null;
    }
    if ((!selectedLevel || preferActionable) && !_setupLevelSelectionWasManual) {
        try {
            const actionable = await timePhase('findFirstIncompleteLevelBtn',
                () => findFirstIncompleteLevelBtn(language, hiddenButtons));
            const actionableIndex = hiddenButtons.indexOf(actionable);
            if (actionableIndex >= 0) initialIndex = actionableIndex;
        } catch (error) {
            console.warn('Extra category auto-pick failed, using first', error);
        }
    }
    const renderStarted = performance.now();
    hiddenButtons[initialIndex].click();
    await timePhase('renderRangeSelector (set dots)',
        () => hiddenButtons[initialIndex]._rangeRenderPromise);
    reportSetupTimings(performance.now() - renderStarted + (window.__setupPhaseOffset || 0));
}

// Smart-range cache: computed snap points for the active source baseline.
// Filters can change the eligible count shown inside each cached range but
// cannot change these boundaries.
let _smartLevelRangesCache = null;

// Study shape, shared by every level builder and the set slotter: levels of
// 100-card target levels with 25-position estimation regions. Sessions are
// chosen as time and built as a card count (session-plan.js, SETWISE-2).
const STUDY_LEVEL_TARGET_CARDS = 100;
const STUDY_LEVEL_MIN_COUNT = 10;
const STUDY_LEVEL_MAX_COUNT = 120;
const STABLE_SET_SLOT_COUNT = 25; // Internal placement regions, not visible groups or sessions.
const STUDY_SESSION_LIMIT = 20;
// Go asks "practise or learn new?" only when a level's Practise words outnumber
// its new words left and there are at least this many of them (a guess, to be
// checked against real progress). Once declined, it stays quiet for that level
// until the app reloads.
const LEVEL_CHOICE_MIN_PRACTICE = 10;
const _levelChoiceDeclined = new Set();
let _studySessionStarting = false;

// Build finishable study levels of STUDY_LEVEL_TARGET_CARDS cards each, with
// ten levels for small decks and a ceiling of STUDY_LEVEL_MAX_COUNT for very
// large ones. Each level is subdivided into stable STABLE_SET_SLOT_COUNT-position
// progress regions. Every mode (Speech, Lyrics, artist) uses these app-built levels.
//
// Boundaries always use the form-level corpus frequency baseline. Merge
// Lemmas anchors a merged card to its highest-frequency form, and every
// optional exclusion simply leaves a hole inside the fixed region.
// The estimator and picker share these exact half-open, fixed baseline slots.
function buildStableSetRanges(startRank, endRank, rankBasis = 'stable') {
    if (!Number.isFinite(startRank) || !Number.isFinite(endRank) || endRank <= startRank) return [];
    return Array.from({ length: Math.ceil((endRank - startRank) / STABLE_SET_SLOT_COUNT) }, (_, index) => ({
        setNumber: index + 1,
        startRank: startRank + index * STABLE_SET_SLOT_COUNT,
        endRank: Math.min(startRank + (index + 1) * STABLE_SET_SLOT_COUNT, endRank),
        rankBasis
    }));
}
window.buildStableSetRanges = buildStableSetRanges;

function computeSmartLevelRanges(filteredVocab) {
    if (!filteredVocab || filteredVocab.length === 0) return [];
    const items = filteredVocab;
    const total = items.length;
    const frequencyOf = (item) => {
        const raw = item.corpus_count;
        const value = Number(raw);
        return Number.isFinite(value) ? Math.max(0, value) : 0;
    };
    const fmtCompact = (n) => n >= 1000
        ? (n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(/\.0$/, '') + 'k'
        : String(Math.round(n));

    // Fixed-size levels: every level is STUDY_LEVEL_TARGET_CARDS cards, so
    // each splits into whole study sets. Small decks still get ten (smaller)
    // levels; decks past the level cap get larger levels, rounded up to whole
    // sets. Levels no longer snap to frequency cliffs.
    const naturalCount = Math.ceil(total / STUDY_LEVEL_TARGET_CARDS);
    let bandSize = STUDY_LEVEL_TARGET_CARDS;
    if (naturalCount > STUDY_LEVEL_MAX_COUNT) {
        bandSize = Math.ceil(total / STUDY_LEVEL_MAX_COUNT / STABLE_SET_SLOT_COUNT) * STABLE_SET_SLOT_COUNT;
    } else if (naturalCount < STUDY_LEVEL_MIN_COUNT) {
        bandSize = Math.max(1, Math.ceil(total / STUDY_LEVEL_MIN_COUNT));
    }
    const boundaryCounts = [];
    for (let count = bandSize; count < total; count += bandSize) boundaryCounts.push(count);
    boundaryCounts.push(total);

    let totalFreq = 0;
    for (const item of items) totalFreq += frequencyOf(item);
    // Speech decks carry no per-card corpus counts. Their levels then have no
    // frequency or coverage of their own: the readout takes coverage from the
    // language's shipped corpus shares, or hides it, rather than printing 0.
    const hasFrequency = totalFreq > 0;

    const ranges = [];
    let cumFreq = 0;
    let previousBoundary = 0;
    for (const cardCount of boundaryCounts) {
        const endIdx = cardCount - 1;
        for (let j = previousBoundary; j <= endIdx; j++) cumFreq += frequencyOf(items[j]);
        const coverage = totalFreq > 0 ? cumFreq / totalFreq : 0;
        const freqMin = frequencyOf(items[endIdx]);
        const splitTier = cardCount < total && frequencyOf(items[cardCount]) === freqMin;
        const startRank = previousBoundary + 1;
        const endRank = cardCount + 1;
        const bandCardCount = cardCount - previousBoundary;

        // Level identifier — keyed by cardCount so selectedLevel round-trips
        // stably across re-renders even when several cuts share a frequency.
        const level = `c${cardCount}`;
        const tickLabel = splitTier
            ? `${fmtCompact(freqMin)}× · ${fmtCompact(cardCount)}`
            : `≥${fmtCompact(freqMin)}`;
        const basisDescription = 'baseline corpus occurrences';
        const rankDescription = `Ranks ${startRank.toLocaleString()}–${cardCount.toLocaleString()} · ${bandCardCount.toLocaleString()} cards`;
        const description = !hasFrequency
            ? rankDescription
            : splitTier
            ? `${rankDescription} · cutoff partway through the ${fmtCompact(freqMin)}× tier · ${(coverage * 100).toFixed(1)}% cumulative coverage by ${basisDescription}`
            : `${rankDescription} · frequency ≥${fmtCompact(freqMin)} · ${(coverage * 100).toFixed(1)}% cumulative coverage by ${basisDescription}`;

        ranges.push({
            level,
            startRank,
            endRank,
            rankBasis: 'stable',
            cardCount,
            bandCardCount,
            threshold: hasFrequency ? coverage : null,
            kind: splitTier ? 'tie-split' : 'freq-cliff',
            freqMin: hasFrequency ? freqMin : null,
            splitTier,
            tickLabel: hasFrequency ? tickLabel : null,
            description,
        });
        previousBoundary = cardCount;
    }
    return ranges;
}

// Synchronous accessor used by updateLevelSliderReadout and friends.
// Returns the cached smart ranges if renderLevelSelector has computed
// them, otherwise falls back to the coverage-based legacy ranges.
function getActiveLevelRanges() {
    return _smartLevelRangesCache && _smartLevelRangesCache.length > 0
        ? _smartLevelRangesCache
        : getPercentageLevelRanges();
}

// Raw-vocab cache (network fetch is the slow part). Keyed by language;
// the filter pass runs fresh every call so toggling lemma/cognate/proper
// noun/noise/single-occurrence immediately reflects in the slider's
// rank counts and tick labels — no stale cache shows pre-toggle numbers.
const _levelSliderRawCache = {};

// Filtering restores/clones sense menus, assigns stable ranks and (in lemma
// mode) scans the examples corpus. Setup previously repeated that full pass in
// the slider, progress annotation, range selector and exclusion summary. Keep
// one prepared result until the source/settings/examples identity changes.
let _preparedSetupVocabulary = null;

function _setupVocabularySignature(language) {
    const baseConfig = config.languages[language] || {};
    const langConfig = activeArtist ? { ...baseConfig, ...activeArtist } : baseConfig;
    return [
        language,
        activeArtist ? (activeArtist.slug || window._urlArtistSlug || '') : 'none',
        langConfig.indexPath || langConfig.dataPath || '',
        (window._selectedArtistSlugs || []).slice().sort().join(','),
        activeArtist ? artistVocabularyScope : (window.playlistLiveActive?.() ? 'playlist-live' : 'speech'),
        window.playlistLiveActive?.() ? `${window.playlistLiveDeck?.()?.playlistId}:${window.playlistLiveDeck?.()?.builtAt}` : 'none',
        percentageMode,
        useLemmaMode,
        excludeCognates,
        cognateThreshold,
        Boolean(window.isBridgeEnabled?.()),
        window.isBridgeEnabled?.() ? (window.__progressEpoch || 0) : 0,
        // Which languages the learner reads changes which words count as
        // cognates, so it changes the deck. Without it here the prepared
        // vocabulary is reused across a selection change and the setup counts
        // report the previous selection.
        (globalThis.activeKnownLanguages?.() || []).join(','),
        hideSingleOccurrence,
        excludeProperNouns,
        excludeNoise,
        excludeSlang,
        excludeGrammarParticles,
        excludeEnglishLoanwords,
    ].join('|');
}

let _levelExamplesSeq = 0;

// The bare first English sense of a card, for the level box's example words:
// no qualifiers, no second sense. Empty while the card's meanings are unloaded.
function _plainEnglishGloss(item) {
    const meaning = (item?.meanings || []).find(m => String(m?.translation || '').trim());
    if (!meaning) return '';
    return meaning.translation.replace(/\([^)]*\)/g, ' ').split(/[,;/]/)[0].replace(/\s+/g, ' ').trim();
}

window.computeSmartLevelRanges = computeSmartLevelRanges;

function getPreparedSetupVocabulary(language, rawVocab) {
    if (!rawVocab) return null;
    const signature = _setupVocabularySignature(language);
    if (_preparedSetupVocabulary
        && _preparedSetupVocabulary.raw === rawVocab
        && _preparedSetupVocabulary.signature === signature
        && _preparedSetupVocabulary.examples === window._cachedExamplesData) {
        return _preparedSetupVocabulary.result;
    }
    let result;
    if (window.playlistLiveActive?.()) {
        const liveVocab = window.applyPlaylistLiveVocabulary?.(rawVocab) || rawVocab;
        result = {
            vocab: liveVocab,
            stableBaseline: liveVocab,
            counts: { english: 0, cognates: 0, singleOcc: 0, lemma: 0 }
        };
    } else {
        result = buildFilteredVocab(rawVocab);
    }
    result.samples = result.vocab.map(item => ({
        rank: item.rank,
        displayRank: item.displayRank,
        stableRank: item.stableRank,
        word: item.lemma || item.targetWord || item.word || '',
        item
    })).filter(sample => sample.word);
    _preparedSetupVocabulary = {
        raw: rawVocab,
        signature,
        examples: window._cachedExamplesData,
        result,
    };
    return result;
}

function invalidatePreparedSetupVocabulary() {
    _preparedSetupVocabulary = null;
}

function invalidateLyricsSourceCaches(language = selectedLanguage) {
    delete _levelSliderRawCache[language];
    if (activeArtist) {
        delete _levelSliderRawCache[`artist:${activeArtist.slug || window._urlArtistSlug || language}`];
    }
    _smartLevelRangesCache = null;
    invalidatePreparedSetupVocabulary();
}

window.getPreparedSetupVocabulary = getPreparedSetupVocabulary;
window.invalidatePreparedSetupVocabulary = invalidatePreparedSetupVocabulary;
window.invalidateLyricsSourceCaches = invalidateLyricsSourceCaches;

function _samplesFromRaw(rawVocab, language = selectedLanguage) {
    return getPreparedSetupVocabulary(language, rawVocab)?.samples || [];
}

// Synchronous fast path used by the slider readout/tick labels — returns
// post-filter samples if the raw vocab is already cached, otherwise null
// so the caller can fall back to raw rank numbers until the async load
// resolves.
function _levelSliderSamplesSync(language) {
    const cacheKey = activeArtist ? `artist:${activeArtist.slug || window._urlArtistSlug || language}` : language;
    const raw = _levelSliderRawCache[cacheKey];
    return raw ? _samplesFromRaw(raw, language) : null;
}

async function _loadLevelSliderSamples(language) {
    const cacheKey = activeArtist ? `artist:${activeArtist.slug || window._urlArtistSlug || language}` : language;
    let raw = _levelSliderRawCache[cacheKey];
    if (!raw) {
        const baseConfig = config.languages[language] || {};
        const langConfig = activeArtist ? { ...baseConfig, ...activeArtist } : baseConfig;
        if (!langConfig) return null;
        try {
            raw = await fetchActiveVocabularyData(langConfig);
            _levelSliderRawCache[cacheKey] = raw;
        } catch (err) {
            console.warn('Slider sample fetch failed:', err);
            return null;
        }
    }
    return _samplesFromRaw(raw, language);
}

// Count post-filter items whose original rank is ≤ endRank — i.e. how
// many cards the user actually gets at this coverage threshold given the
// active filter set.
function _filteredCountUpTo(samples, endRank) {
    let n = 0;
    for (const s of samples) if (s.rank <= endRank) n++;
    return n;
}

function _formatTickRank(n) {
    if (n >= 1000) return (n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(/\.0$/, '') + 'k';
    return String(n);
}

// The level loader treats endRank as an exclusive boundary. Keep the setup
// readout on that same contract so every level reports its own real band
// (for example 201–400), rather than presenting every band as Ranks 1–X.
function _levelBandMetrics(level, samples = null) {
    const start = Math.max(1, Number(level?.startRank) || 1);
    const endExclusive = Math.max(start + 1, Number(level?.endRank) || start + 1);
    const end = endExclusive - 1;
    let count;
    if (samples) {
        const rankOf = _levelRankAccessor(level?.rankBasis);
        count = samples.filter(sample => {
            const rank = rankOf(sample);
            return rank >= start && rank < endExclusive;
        }).length;
    } else {
        count = Number(level?.bandCardCount);
        if (!Number.isFinite(count)) count = endExclusive - start;
    }
    return { start, end, count: Math.max(0, count) };
}

function _levelRankAccessor(rankBasis) {
    if (rankBasis === 'category') return item => item.categoryRank;
    if (rankBasis === 'stable') return item => item.stableRank;
    if (rankBasis === 'display') return item => item.displayRank;
    return item => item.rank;
}

// Patch the rank readout + tick labels with post-filter counts. Called
// both synchronously (with cached samples) and asynchronously after a
// fresh load, so the rank counts stay accurate across filter toggles.
//
// For smart ranges (artist mode) the snap points are already computed
// from the post-filter vocab, so cardCount is authoritative — we use it
// directly. For legacy coverage-based ranges we still need to count
// items at runtime to convert raw rank → filtered count.
function _applyFilteredRankCounts(samples) {
    if (!samples) return;
    const ranges = getActiveLevelRanges();
    document.querySelectorAll('#levelSelector .lsw-ticks span').forEach((el) => {
        const i = parseInt(el.dataset.i, 10);
        const lv = ranges[i];
        if (!lv) return;
        const n = lv.cardCount != null ? lv.cardCount : _filteredCountUpTo(samples, lv.endRank);
        el.textContent = lv.tickLabel || _formatTickRank(n);
        el.title = lv.description || `${lv.level} coverage → top ${n.toLocaleString()} words`;
    });
}

// Update the segmented level bar's selection state. Highlights all
// segments up to (and including) the chosen index — the "line within
// the line" fill — and stores the value on the bar's dataset so other
// code can read it back synchronously the way it used to read
// slider.value. Also re-runs the readout so headline + tick labels
// follow the new selection.
function setLevelSegmentSelection(idx, preserveCenter = false) {
    const segBar = document.getElementById('lswSlider');
    if (!segBar) return;
    const oldIdx = parseInt(segBar.dataset.value ?? '-1', 10);
    const newSeg = segBar.querySelector(`.lsw-seg[data-i="${idx}"]`);
    const oldCenter = (preserveCenter && newSeg) ? (newSeg.offsetLeft + newSeg.offsetWidth / 2) : 0;

    segBar.dataset.value = String(idx);
    segBar.querySelectorAll('.lsw-seg').forEach(seg => {
        const i = parseInt(seg.dataset.i, 10);
        seg.classList.toggle('filled', i <= idx);
        seg.classList.toggle('selected', i === idx);
        seg.style.setProperty('--dist', String(Math.abs(i - idx)));
        seg.setAttribute('aria-checked', i === idx ? 'true' : 'false');
    });

    if (preserveCenter && newSeg && oldIdx !== idx && oldIdx >= 0) {
        const newCenter = newSeg.offsetLeft + newSeg.offsetWidth / 2;
        const shift = newCenter - oldCenter;
        if (shift !== 0) {
            segBar.scrollLeft += shift;
        }
    }

    const levelEl = document.getElementById('lswLevelVal');
    if (levelEl) levelEl.textContent = `Level ${idx + 1}`;
    syncHomeLevelStepper(idx);
    updateLevelSliderReadout(idx);
    globalThis.refreshFastMode?.();
}

// --- Home level stepper ----------------------------------------------------
// ‹ Level N › replaces the scrubber on screen. The scrubber stays in the DOM,
// hidden, because selection still runs through it and the hidden .level-btn.
function syncHomeLevelStepper(idx) {
    const stepper = document.getElementById('homeLevelStepper');
    if (!stepper) return;
    const ranges = getActiveLevelRanges();
    const lv = ranges[idx];
    const numberEl = document.getElementById('homeLevelNumber');
    if (numberEl) numberEl.textContent = String(idx + 1);
    const wordsEl = document.getElementById('homeLevelWords');
    if (wordsEl && lv) {
        const metrics = _levelBandMetrics(lv);
        wordsEl.textContent = `Words ${metrics.start.toLocaleString()}–${metrics.end.toLocaleString()}`;
    }
    stepper.querySelector('[data-level-step="-1"]').disabled = idx <= 0;
    stepper.querySelector('[data-level-step="1"]').disabled = idx >= ranges.length - 1;
}

// --- Home level tiles ------------------------------------------------------
// Once the learner has started two levels, a row of tiles (each with its own
// progress bar) sits above the stepper: the levels they have started, the one
// after the furthest, and the selected one, at most eight at a time. The ‹ ›
// arrows stay beside the level number, the easier target.
// With one level started the row would say no more than ‹ 1 ›, so it stays hidden.
const HOME_LEVEL_TILE_MIN_STARTED = 2;
const HOME_LEVEL_TILE_MAX = 8;
const HOME_LEVEL_TILE_MAX_PHONE = 6;

function renderHomeLevelTiles({ vocab, baseline, seenLemmas, estimatedIds, estimate, smartSkipOn }) {
    const row = document.getElementById('homeLevelTiles');
    const step2 = document.getElementById('step2');
    if (!row) return;
    const ranges = getActiveLevelRanges();
    const hide = () => { row.hidden = true; row.innerHTML = ''; step2?.classList.remove('has-level-tiles'); };
    if (ranges.length < 2 || ranges[0]?.rankBasis === 'category') return hide();

    const rankOf = _levelRankAccessor(ranges[0].rankBasis);
    const starts = ranges.map(lv => Number(lv.startRank));
    const levelOf = rank => {
        let lo = 0, hi = starts.length - 1, found = -1;
        while (lo <= hi) {
            const mid = (lo + hi) >> 1;
            if (starts[mid] <= rank) { found = mid; lo = mid + 1; } else hi = mid - 1;
        }
        return found >= 0 && rank < Number(ranges[found].endRank) ? found : -1;
    };
    const counts = ranges.map(() => ({ cards: 0, seen: 0, review: 0, estimated: 0, baseline: 0 }));
    for (const item of vocab) {
        const i = levelOf(rankOf(item));
        if (i < 0) continue;
        const state = getSetupLearningState(item, { seenLemmas, estimatedIds, estimate });
        const c = counts[i];
        c.cards++;
        if (state?.seen) c.seen++;
        if (state?.needsReview) c.review++;
        if (state?.estimated) c.estimated++;
    }
    if (smartSkipOn) {
        for (const item of baseline) {
            const i = levelOf(rankOf(item));
            if (i >= 0) counts[i].baseline++;
        }
    }

    const started = counts.map((c, i) => c.seen > 0 ? i : -1).filter(i => i >= 0);
    if (started.length < HOME_LEVEL_TILE_MIN_STARTED) return hide();

    const levelButtons = Array.from(document.querySelectorAll('.level-selector-buttons .level-btn'));
    const selectedIdx = Math.max(0, levelButtons.findIndex(btn => btn.dataset.level === selectedLevel));
    const shown = new Set(started);
    const next = started[started.length - 1] + 1;
    if (next < ranges.length) shown.add(next);
    shown.add(selectedIdx);
    let tiles = [...shown].sort((a, b) => a - b);
    const maxTiles = window.matchMedia?.('(max-width: 1023px)').matches ? HOME_LEVEL_TILE_MAX_PHONE : HOME_LEVEL_TILE_MAX;
    if (tiles.length > maxTiles) {
        const pos = tiles.indexOf(selectedIdx);
        const from = Math.max(0, Math.min(pos - Math.floor(maxTiles / 2), tiles.length - maxTiles));
        tiles = tiles.slice(from, from + maxTiles);
    }

    const tileHTML = tiles.map(i => {
        const c = counts[i];
        const skipped = Math.max(0, c.baseline - c.cards);
        const known = Math.max(0, c.seen - c.review - c.estimated);
        const segments = [['known', known], ['seen', c.review], ['estimated', c.estimated], ['new', c.cards - c.seen], ['skipped', skipped]]
            .filter(([, n]) => n > 0)
            .map(([kind, n]) => `<span class="is-${kind}" style="flex-grow:${n}"></span>`).join('');
        const metrics = _levelBandMetrics(ranges[i]);
        // Phones show one dot per tile, the least-learned colour present:
        // any new word → white, else any seen → yellow, else green.
        const dot = c.cards - c.seen > 0 ? 'new' : c.review > 0 ? 'seen' : 'known';
        return `<button type="button" class="home-level-tile${i === selectedIdx ? ' is-selected' : ''}" data-dot="${dot}" data-level-index="${i}" role="radio" aria-checked="${i === selectedIdx}" aria-label="Level ${i + 1}, words ${metrics.start.toLocaleString()}–${metrics.end.toLocaleString()}">
                <span class="home-level-tile-num">${i + 1}</span>
                <span class="home-level-tile-bar" aria-hidden="true">${segments}</span>
                <span class="home-level-tile-dot" aria-hidden="true"></span>
            </button>`;
    }).join('');
    row.innerHTML = `<div class="home-level-tile-list">${tileHTML}</div>`;
    row.hidden = false;
    step2?.classList.add('has-level-tiles');

    const pick = idx => {
        const btn = levelButtons[idx];
        if (!btn) return;
        _setupLevelSelectionWasManual = true;
        btn.click();
    };
    row.querySelectorAll('[data-level-index]').forEach(tile => {
        tile.addEventListener('click', () => pick(Number(tile.dataset.levelIndex)));
    });
}

function wireHomeLevelStepper(buttons) {
    const stepper = document.getElementById('homeLevelStepper');
    if (!stepper) return;
    const step = delta => {
        const current = parseInt(document.getElementById('lswSlider')?.dataset.value || '0', 10);
        const btn = buttons[current + delta];
        if (!btn) return;
        _setupLevelSelectionWasManual = true;
        btn.click();
    };
    stepper.querySelectorAll('[data-level-step]').forEach(button => {
        button.addEventListener('click', () => step(Number(button.dataset.levelStep)));
    });
    // A horizontal swipe across the number steps one level.
    let startX = null;
    stepper.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
    stepper.addEventListener('touchend', e => {
        if (startX == null) return;
        const dx = e.changedTouches[0].clientX - startX;
        startX = null;
        if (Math.abs(dx) > 40) step(dx < 0 ? 1 : -1);
    }, { passive: true });
}

// --- Horizontal level scrubber ---------------------------------------------
// The level segments render as a horizontal scroll-snap "ruler": you scrub
// left→right (touch swipe / trackpad) and the CENTERED segment is the selected
// level (magnified). It reuses setLevelSegmentSelection + the hidden .level-btn,
// so all downstream selection logic is unchanged — only the presentation is.
let _levelProgrammaticScroll = false;
let _levelScrubberInitiated = false;

function _levelCenteredIdx(bar) {
    const mid = bar.scrollLeft + bar.clientWidth / 2;
    let best = 0, bestD = Infinity;
    bar.querySelectorAll('.lsw-seg').forEach(s => {
        const i = parseInt(s.dataset.i, 10);
        const c = s.offsetLeft + s.offsetWidth / 2;
        const d = Math.abs(c - mid);
        if (d < bestD) { bestD = d; best = i; }
    });
    return best;
}

function _scrollLevelSegToCenter(idx, smooth) {
    const bar = document.getElementById('lswSlider');
    if (!bar) return;
    const seg = bar.querySelector('.lsw-seg[data-i="' + idx + '"]');
    if (!seg) return;
    _levelProgrammaticScroll = true;
    const target = seg.offsetLeft + seg.offsetWidth / 2 - bar.clientWidth / 2;
    bar.scrollTo({ left: Math.max(0, target), behavior: smooth ? 'smooth' : 'auto' });
    setTimeout(() => { _levelProgrammaticScroll = false; }, smooth ? 500 : 250);
}

function wireLevelScrubber(segBar, buttons) {
    let commitTimer = null;
    let pointerActive = false;

    segBar.addEventListener('pointerdown', () => { pointerActive = true; }, { passive: true });
    window.addEventListener('pointerup', () => {
        if (!pointerActive) return;
        pointerActive = false;
        clearTimeout(commitTimer);
        commitTimer = setTimeout(commit, 80);
    }, { passive: true });
    window.addEventListener('pointercancel', () => { pointerActive = false; }, { passive: true });

    const commit = () => {
        if (_levelProgrammaticScroll || pointerActive) return;
        const targetIdx = _levelCenteredIdx(segBar);
        const btn = buttons[targetIdx];
        if (btn) {
            _setupLevelSelectionWasManual = true;
            _levelScrubberInitiated = true;
            try {
                btn.click(); // → renderRangeSelector (resets the set options)
            } finally {
                _levelScrubberInitiated = false;
            }
            _scrollLevelSegToCenter(targetIdx, true);
        }
    };
    // While the learner scrubs, the badge swaps its word range for the level
    // total, and keeps it for a second after the bar stops (SETWISE-2).
    let totalTimer = null;
    const showTotalWhileScrubbing = () => {
        segBar.classList.add('is-scrubbing');
        clearTimeout(totalTimer);
        totalTimer = setTimeout(() => segBar.classList.remove('is-scrubbing'), 1000);
    };
    segBar.addEventListener('scroll', () => {
        showTotalWhileScrubbing();
        const i = _levelCenteredIdx(segBar);
        if (+segBar.dataset.value !== i) setLevelSegmentSelection(i, true); // live magnify + readout
        if (_levelProgrammaticScroll) return;
        clearTimeout(commitTimer);
        if (!pointerActive) {
            commitTimer = setTimeout(commit, 200);
        }
    }, { passive: true });
    // scrollend fires once the snap animation settles — the reliable commit.
    segBar.addEventListener('scrollend', () => {
        if (_levelProgrammaticScroll) return;
        clearTimeout(commitTimer);
        if (!pointerActive) commit();
    }, { passive: true });
    // Tapping a segment commits it directly. We must NOT rely on the scroll
    // handler to commit here: _scrollLevelSegToCenter marks the scroll as
    // programmatic, and both scroll listeners early-return on programmatic
    // scrolls — so a tap would magnify the segment but never refresh the set
    // options. The .level-btn click both re-renders the ranges AND re-centres
    // the scrubber (via the sync block in the button handler).
    segBar.querySelectorAll('.lsw-seg').forEach(seg => {
        seg.addEventListener('click', () => {
            const idx = parseInt(seg.dataset.i, 10);
            if (!Number.isNaN(idx) && buttons[idx]) {
                _setupLevelSelectionWasManual = true;
                buttons[idx].click();
            }
        });
    });
}

// Prefer lexical words near the beginning, plus one later word for variety.
// Unknown parts of speech remain eligible; sparse levels stay within their band.
function _pickLevelExampleWords(samples, level) {
    const rankOf = _levelRankAccessor(level.rankBasis);
    const functionPOS = new Set(['ADP', 'AUX', 'CCONJ', 'SCONJ', 'CONJ', 'DET', 'PRON', 'PART', 'CLITIC',
        'ARTICLE', 'DETERMINER', 'PRONOUN', 'PREPOSITION', 'CONJUNCTION', 'PARTICLE', 'AUXILIARY']);
    const seen = new Set();
    const band = samples.filter(sample => {
        const rank = rankOf(sample);
        return rank >= level.startRank && rank < level.endRank && !/\s/u.test(sample.word.trim());
    }).sort((a, b) => rankOf(a) - rankOf(b)).filter(sample => {
        const key = sample.word.trim().toLocaleLowerCase();
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    });
    const lexical = band.filter(sample => {
        const item = sample.item || {};
        const tags = [item.pos, item.part_of_speech,
            ...(item.meanings || []).map(meaning => meaning.pos || meaning.part_of_speech)]
            .filter(Boolean).map(pos => String(pos).trim().toUpperCase())
            .filter(pos => !['X', 'SENSE_CYCLE', 'EXAMPLE_ONLY'].includes(pos));
        return !tags.length || tags.some(pos => !functionPOS.has(pos));
    });
    const pool = lexical.length ? lexical : band;
    const early = pool.slice(0, 4);
    const lateStart = level.startRank + (level.endRank - level.startRank) * 0.75;
    const later = pool.slice(early.length).find(sample => rankOf(sample) >= lateStart);
    // The first five are also the mobile preview, so keep the later word there.
    const picked = [...early, ...(later ? [later] : [])];
    for (const sample of pool) {
        if (picked.length >= 8) break;
        if (!picked.includes(sample)) picked.push(sample);
    }
    return picked.map(sample => sample.word);
}

// Update the slider's rank/coverage text + example words for snap index `i`.
// Examples are loaded lazily; the readout updates synchronously and examples
// fill in when the vocab fetch resolves.
function updateLevelSliderReadout(i) {
    const ranges = getActiveLevelRanges();
    const lv = ranges[i];
    if (!lv) return;
    const covEl  = document.getElementById('lswCovVal');
    const exEl   = document.getElementById('lswExamples');
    // Synchronous range and card count for this level's own band. Smart
    // ranges carry the exact band count; legacy ranges are counted against
    // the filtered samples when available.
    const _syncSamples = _levelSliderSamplesSync(selectedLanguage);
    const usingReleaseLevels = !activeArtist && !window.playlistLiveActive?.() && Array.isArray(releaseStudyStructure?.levels) && releaseStudyStructure.levels.length > 0;
    const coverageType = activeArtist
        ? 'lyrics comprehension'
        : (window.playlistLiveActive?.()
            ? (window.isSeriesStudy?.() ? 'series dialogue' : 'playlist words')
            : (globalThis.coverageAvailable?.()
                && (usingReleaseLevels || ranges[0]?.threshold == null)
                ? globalThis.coverageLabel()
                : 'speech comprehension'));

    // Cumulative: what finishing this level (and those before it) reaches.
    const shipped = lv.threshold == null
        ? globalThis.cumulativeCoverage?.(_syncSamples, lv.endRank)
        : null;
    const coveragePct = lv.threshold != null
        ? `${(lv.threshold * 100).toFixed(1)}%`
        : (shipped != null ? `${(shipped * 100).toFixed(1)}%` : '');
    if (covEl) covEl.textContent = coveragePct;

    // Patch tick labels too if the cache is warm — keeps the row of
    // "100, 300, 700, 1.5k…" honest about how many cards each snap point
    // actually yields under the current filters.
    if (_syncSamples) _applyFilteredRankCounts(_syncSamples);

    if (!exEl) return;

    // Frequency at this rank ceiling — the actual corpus_count of the
    // rarest card in this segment. Smart ranges carry it directly on
    // lv.freqMin; legacy normal-mode ranges derive it from ppmData.
    // Rendered as a plain sentence (no ≥ sign), with the examples for
    // this level on their own line beneath it.
    let freqValue = null;
    let freqUnit = '';
    let displayedWordCount = _levelBandMetrics(lv, _syncSamples).count;
    if (lv.freqMin != null) {
        freqValue = lv.freqMin;
        freqUnit = activeArtist
            ? `time${freqValue === 1 ? '' : 's'} in the lyrics`
            : `time${freqValue === 1 ? '' : 's'} per million words`;
    } else if (ppmData && ppmData.length > 0) {
        const _e = ppmData.find(p => p.rank === lv.endRank);
        if (_e) {
            freqValue = Math.round(_e.ppm);
            freqUnit = activeArtist
                ? `time${freqValue === 1 ? '' : 's'} in the lyrics`
                : `time${freqValue === 1 ? '' : 's'} per million words`;
        }
    }

    const _renderLine = (examplesText) => {
        // Frequency as a full sentence on its own line, then the example
        // words with speech coverage directly after them.
        const wordLabel = `${displayedWordCount.toLocaleString()} word${displayedWordCount === 1 ? '' : 's'}`;
        // Keep frequency calculations available for a future detail view.
        const showLevelFrequency = false;
        const freqHTML = showLevelFrequency && freqValue !== null
            ? `<div class="lsw-freq-sentence"><strong>${wordLabel}</strong> appear${displayedWordCount === 1 ? 's' : ''} <strong>${freqValue.toLocaleString()}</strong> ${freqUnit}</div>`
            : '';
        const coverageRounded = coveragePct ? `${Math.round(parseFloat(coveragePct))}%` : '';
        const levelsLabel = i === 0 ? 'Level 1 makes' : `Levels 1–${i + 1} make`;
        const covHTML = coverageRounded
            ? `<span class="lsw-coverage-inline">${levelsLabel} up <strong>${coverageRounded}</strong> of ${activeArtist ? 'lyric words' : (window.playlistLiveActive?.() ? (window.isSeriesStudy?.() ? 'series dialogue' : 'playlist words') : 'speech')}</span>`
            : '';
        const egHTML = (examplesText || covHTML)
            ? `<div class="lsw-egs">${examplesText || ''}${covHTML}</div>`
            : '';
        // Never let the line get shorter while the learner steps through levels:
        // the box would grow, shrink and grow again as each level's examples load.
        exEl.style.minHeight = Math.max(parseFloat(exEl.style.minHeight) || 0, exEl.offsetHeight) + 'px';
        exEl.innerHTML = freqHTML + egHTML;
    };
    _renderLine('');

    _loadLevelSliderSamples(selectedLanguage).then(samples => {
        // A previous level's fetch may finish after the learner has moved on.
        if (Number(document.getElementById('lswSlider')?.dataset.value) !== i
            || getActiveLevelRanges()[i] !== lv) return;
        if (!samples || samples.length === 0) { _renderLine(''); return; }
        // Replace any raw-rank fallback with the real filtered count now
        // that we've actually loaded the vocab.
        _applyFilteredRankCounts(samples);
        displayedWordCount = _levelBandMetrics(lv, samples).count;
        const targetWords = _pickLevelExampleWords(samples, lv);

        const render = labels => {
            const out = [];
            for (const label of labels) if (label && !out.includes(label)) out.push(label);
            const shown = out.slice(0, 8);
            _renderLine(shown.length
                ? 'e.g. ' + shown.map((label, k) => `<span class="${k >= 5 ? 'lsw-eg-extra' : 'lsw-eg'}">${k ? ', ' : ''}${String(label).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))}</span>`).join('')
                : '');
        };
        render(targetWords);
    });
}

function updateLevelInfoLine(btn) {
    // Step 2 used to render a separate "Most common N words / Words appear
    // N+ times" line in the header. The slider readout now covers the rank
    // count, and the frequency is rendered inline with the example words
    // (see updateLevelSliderReadout). This stays as a no-op so legacy
    // callers don't break.
    const infoLine = document.getElementById('levelInfoLine');
    if (infoLine) infoLine.style.display = 'none';
}

function setupCognateToggle() {
    syncStudyPreferenceControls();
    document.querySelectorAll('.cognate-toggle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Don't allow selecting "exclude" mode if cognate field not available
            if (this.dataset.cognate === 'exclude' && !cognateFieldAvailable) {
                globalThis.showFastModeUnavailable?.('cognates');
                return;
            }
            // Reset all buttons to short text
            document.querySelectorAll('.cognate-toggle-btn').forEach(b => {
                b.classList.remove('selected');
                b.textContent = b.dataset.short;
            });
            // Set selected button to full text
            this.classList.add('selected');
            this.textContent = this.dataset.full;
            excludeCognates = this.dataset.cognate === 'exclude';

            _refreshAfterCognateChange();
        });
    });
    // Cognate sensitivity (Loose / Default / Strict) lives in Study settings.
    // Higher threshold = only the most obvious
    // cognates excluded; lower threshold = more aggressive exclusion.
    document.querySelectorAll('#cognateSensitivitySelector .cognate-sens-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const t = parseFloat(this.dataset.threshold);
            if (Number.isNaN(t)) return;
            cognateThreshold = t;
            document.querySelectorAll('#cognateSensitivitySelector .cognate-sens-btn')
                .forEach(b => b.classList.toggle('selected', b === this));
            if (excludeCognates) _refreshAfterCognateChange();
        });
    });
    // The sensitivity row's "?" is wired by setupSettingExplanations(), which
    // opens both its one-line description and the longer aria-controls block.
    updateCognateSensitivityVisibility();
}

async function _refreshAfterCognateChange() {
    invalidatePreparedSetupVocabulary();
    await renderLevelSelector(selectedLanguage);
    if (selectedLevel) {
        const levelBtn = document.querySelector(`.level-btn[data-level="${selectedLevel}"]`);
        if (levelBtn) {
            levelBtn.classList.add('selected');
            levelBtn.textContent = levelBtn.dataset.full;
        }
        await renderRangeSelector().catch(err => console.error('Error rendering ranges:', err));
    }
    updateExclusionBars();
    updateCognateSensitivityVisibility();
}

function setupLemmaToggle() {
    syncStudyPreferenceControls();
    document.querySelectorAll('.lemma-toggle-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            // Don't allow selecting "1" mode if lemma field not available
            if (this.dataset.lemma === 'on' && !lemmaFieldAvailable) {
                globalThis.showFastModeUnavailable?.('lemmas');
                return;
            }
            // Reset all buttons to short text
            document.querySelectorAll('.lemma-toggle-btn').forEach(b => {
                b.classList.remove('selected');
                b.textContent = b.dataset.short;
            });
            // Set selected button to full text
            this.classList.add('selected');
            this.textContent = this.dataset.full;
            useLemmaMode = this.dataset.lemma === 'on';
            invalidatePreparedSetupVocabulary();

            // Re-render level selector with new word counts, and re-render range selector if a level is selected
            const loadingIndicator = document.getElementById('dataLoadingIndicator');
            if (useLemmaMode) loadingIndicator?.classList.add('visible');
            try {
                await renderLevelSelector(selectedLanguage);
            } finally {
                loadingIndicator?.classList.remove('visible');
            }
            // Re-select the current level if one was selected
            if (selectedLevel) {
                const levelBtn = document.querySelector(`.level-btn[data-level="${selectedLevel}"]`);
                if (levelBtn) {
                    levelBtn.classList.add('selected');
                    levelBtn.textContent = levelBtn.dataset.full;
                }
                renderRangeSelector().catch(err => console.error('Error rendering ranges:', err));
            }
            updateExclusionBars();
        });
    });
}

function setupPercentModeButton() {
    const toggle = document.getElementById('levelModeToggle');
    if (!toggle) return;

    // Hide the toggle entirely in artist mode — artist mode is always
    // % coverage of lyrics, so there's no choice to expose.
    // CEFR is deliberately hidden in both modes for now. Keep the handler
    // and data path intact so the mode can be restored later without a
    // migration or reimplementation.
    toggle.style.display = 'none';
    toggle.setAttribute('aria-hidden', 'true');
    toggle.tabIndex = -1;
    return;

    toggle.addEventListener('click', async function() {
        // Tapping the CEFR button flips between "% coverage" (default, off)
        // and "CEFR pills" (on). It's a binary switch — same behavior the
        // old segmented two-button control had, just collapsed into one.
        const wantPercent = !percentageMode;  // currently in CEFR? → switch to %
        const langConfig = config.languages[selectedLanguage];
        if (wantPercent && (!langConfig || !langConfig.ppmDataPath)) {
            alert('Percentage mode is not available for this language yet.');
            return;
        }

        percentageMode = wantPercent;
        updatePercentModeButton();

        if (percentageMode && !ppmData) {
            await loadPpmData(selectedLanguage);
        }

        updateStep2Tooltip();
        updateStep5Tooltip();

        // Hide level info line (re-shown on level click)
        const infoLine = document.getElementById('levelInfoLine');
        if (infoLine) infoLine.style.display = 'none';

        // Re-render the level selector for the new mode
        selectedLevel = null;
        renderLevelSelector(selectedLanguage);
        document.getElementById('lemmaToggleContainer').style.display = 'none';
        document.getElementById('cognateToggleContainer').style.display = 'none';
        document.getElementById('step4').style.display = 'none';
    });
}

function setupEstimationModal() {
    // Close modal on X button or backdrop click
    document.getElementById('closeEstimationModal').addEventListener('click', closeEstimationModal);
    document.getElementById('estimationModal')?.addEventListener('click', event => {
        if (event.target === event.currentTarget) closeEstimationModal();
    });

    // Start estimation button
    document.getElementById('startEstimationBtn').addEventListener('click', function() {
        startEstimation();
    });
    document.getElementById('estimationImportKnownBtn')?.addEventListener('click', () => {
        closeEstimationModal();
        window.openVocabularyImportModal?.();
    });

    // Use estimated level
    document.getElementById('useEstimatedLevelBtn').addEventListener('click', useEstimatedLevel);
}

async function updateLemmaToggleVisibility() {
    const langConfig = config.languages[selectedLanguage];
    const lemmaContainer = document.getElementById('lemmaToggleContainer');
    const lemmaSelector = document.getElementById('lemmaToggleSelector');
    const rangeStepNumber = document.getElementById('rangeStepNumber');

    // Prefer the release/config contract. Older releases without an explicit
    // declaration retain the data inspection fallback during migration.
    const declaredCapability = window._activeReleaseCapabilities?.mergeLemmas
        ?? langConfig?.capabilities?.mergeLemmas;
    lemmaFieldAvailable = declaredCapability === true;
    if (langConfig && typeof declaredCapability !== 'boolean') {
        try {
            const vocabData = await fetchActiveVocabularyData(langConfig);
            lemmaFieldAvailable = vocabData.some(item =>
                item.hasOwnProperty('most_frequent_lemma_instance')
            );
        } catch (error) {
            console.error('Error checking lemma field availability:', error);
        }
    }

    // Keep the explanation and its control visible even before a mapping has
    // been published. The attempted action then explains the missing mapping
    // in ordinary language instead of making the feature mysteriously vanish.
    lemmaContainer.dataset.available = String(lemmaFieldAvailable);
    lemmaContainer.style.display = 'block';
    rangeStepNumber.textContent = '3';

    if (lemmaFieldAvailable) {
        // Enable both options
        lemmaSelector.classList.remove('lemma-toggle-unavailable');
    } else {
        // Disable merging while retaining surface-card study.
        lemmaSelector.classList.add('lemma-toggle-unavailable');
        useLemmaMode = false;
        document.querySelectorAll('.lemma-toggle-btn').forEach(b => b.classList.remove('selected'));
        document.querySelector('.lemma-toggle-btn[data-lemma="off"]').classList.add('selected');
    }
}

async function updateCognateToggleVisibility() {
    const langConfig = config.languages[selectedLanguage];
    const cognateContainer = document.getElementById('cognateToggleContainer');
    const cognateSelector = document.getElementById('cognateToggleSelector');

    // The capability is declared per LANGUAGE while the data is per language
    // AND mode, so a declaration alone cannot answer this. Spanish carries its
    // cognate flags in the artist master: true for Lyrics, nothing for Speech.
    // French's live in one artist playlist while French has lyrics disabled, so
    // the flag was true over no reachable data at all. Both showed a toggle
    // that silently did nothing.
    //
    // The declaration is now read as permission, not as presence: it can keep a
    // filter off, but only the loaded deck can turn it on.
    const declaredCapability = window._activeReleaseCapabilities?.cognateFilter
        ?? langConfig?.capabilities?.cognateFilter;
    cognateFieldAvailable = false;
    if (declaredCapability !== false && langConfig) {
        try {
            const vocabData = await fetchActiveVocabularyData(langConfig);
            cognateFieldAvailable = vocabData.some(item =>
                (item.cognate_score > 0)
                || item.cognate_scores
                || item.cognate_sense_map
                || item.cognet_cognate
                || item.is_transparent_cognate
            );
        } catch (error) {
            console.error('Error checking cognate field availability:', error);
            // Unknown is not the same as absent, but showing a control we
            // cannot back is what caused this; stay off.
            cognateFieldAvailable = false;
        }
    }

    cognateContainer.dataset.available = String(cognateFieldAvailable);
    cognateContainer.style.display = 'block';
    if (cognateFieldAvailable) {
        // Enable both options
        cognateSelector.classList.remove('cognate-toggle-unavailable');
    } else {
        // Retain the explanation and control; trying to exclude gives a clear
        // language-pair error through showFastModeUnavailable().
        cognateSelector.classList.add('cognate-toggle-unavailable');
        excludeCognates = false;
    }
}

function hexToRgbChannels(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '0, 0, 0';
}

function relativeLuminance(hex) {
    const [r, g, b] = hex.replace('#', '').match(/.{2}/g).map(x => {
        const c = parseInt(x, 16) / 255;
        return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrastRatio(hexA, hexB) {
    const l1 = relativeLuminance(hexA);
    const l2 = relativeLuminance(hexB);
    const [hi, lo] = l1 > l2 ? [l1, l2] : [l2, l1];
    return (hi + 0.05) / (lo + 0.05);
}

function hexToHsl(hex) {
    const [r, g, b] = hex.replace('#', '').match(/.{2}/g).map(x => parseInt(x, 16) / 255);
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const l = (max + min) / 2;
    if (max === min) return { h: 0, s: 0, l };
    const d = max - min;
    const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    let h;
    switch (max) {
        case r: h = ((g - b) / d) + (g < b ? 6 : 0); break;
        case g: h = ((b - r) / d) + 2; break;
        default: h = ((r - g) / d) + 4; break;
    }
    return { h: h / 6, s, l };
}

function hslToHex(h, s, l) {
    const hue = (p, q, t) => {
        let tt = t;
        if (tt < 0) tt += 1;
        if (tt > 1) tt -= 1;
        if (tt < 1 / 6) return p + (q - p) * 6 * tt;
        if (tt < 1 / 2) return q;
        if (tt < 2 / 3) return p + (q - p) * (2 / 3 - tt) * 6;
        return p;
    };
    let r;
    let g;
    let b;
    if (s === 0) {
        r = g = b = l;
    } else {
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue(p, q, h + 1 / 3);
        g = hue(p, q, h);
        b = hue(p, q, h - 1 / 3);
    }
    const channel = (c) => Math.round(Math.min(1, Math.max(0, c)) * 255).toString(16).padStart(2, '0');
    return `#${channel(r)}${channel(g)}${channel(b)}`;
}

function inkForFill(hex) {
    const dark = '#10141b';
    const light = '#ffffff';
    return contrastRatio(hex, light) >= contrastRatio(hex, dark) ? light : dark;
}

// Flag colours stay at their own hue and saturation. Dark mode lifts
// lightness only until the colour separates from the page, then stops, so a
// red stays red instead of turning pink. Light mode darkens until the colour
// clears a pale page. Ink is whichever of white or near-black still reads.
function readableFlagColor(hex, theme) {
    const page = theme === 'light' ? '#eef2f5' : '#0b0f14';
    const { h, s, l } = hexToHsl(hex);
    const sat = Math.min(1, Math.max(s, 0.82));
    const darker = theme === 'light';
    const pageTarget = darker ? 5 : 5.5;
    const limit = darker ? 0.16 : Math.max(l, 0.5);
    let lightness = l;
    let color = hslToHex(h, sat, lightness);
    const readable = (candidate) => (
        contrastRatio(candidate, page) >= 3.4
        && contrastRatio(candidate, inkForFill(candidate)) >= 4.5
    );
    for (let i = 0; i < 20; i += 1) {
        const next = darker
            ? Math.max(limit, lightness - 0.02)
            : Math.min(limit, lightness + 0.02);
        if (next === lightness) break;
        const nextColor = hslToHex(h, sat, next);
        if (readable(nextColor) && contrastRatio(nextColor, page) >= pageTarget) {
            lightness = next;
            color = nextColor;
            break;
        }
        if (!readable(nextColor) && readable(color)) break;
        lightness = next;
        color = nextColor;
    }
    return { color, ink: inkForFill(color) };
}

function paintAccent(el, primary, secondary) {
    if (!el) return;
    el.style.setProperty('--accent-primary', primary.color);
    el.style.setProperty('--accent-primary-text', primary.ink);
    el.style.setProperty('--accent-primary-rgb', hexToRgbChannels(primary.color));
    el.style.setProperty('--accent-secondary', secondary.color);
    el.style.setProperty('--accent-secondary-text', secondary.ink);
    el.style.setProperty('--accent-secondary-rgb', hexToRgbChannels(secondary.color));
}

function applyLanguageColorTheme() {
    const langConfig = config.languages[selectedLanguage];
    if (!langConfig || !langConfig.colorTheme) return;
    const theme = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
    const primary = readableFlagColor(langConfig.colorTheme.primary, theme);
    // The second flag colour stays recognisable. It is a thin stripe, not a
    // second fill, so it does not need the same lift as the buttons.
    const secondaryHex = langConfig.colorTheme.secondary;
    const secondary = {
        color: secondaryHex,
        ink: relativeLuminance(secondaryHex) < 0.4 ? '#ffffff' : '#10141b',
    };
    const root = document.documentElement;
    paintAccent(root, primary, secondary);
    // The stylesheet pins the setup panel to a neutral indigo. An inline
    // value wins, so the main-page buttons follow this language instead.
    paintAccent(document.getElementById('setupPanel'), primary, secondary);
    root.style.setProperty('--lang-trim', primary.color);
    root.style.setProperty('--lang-trim-rgb', hexToRgbChannels(primary.color));
    root.style.setProperty('--lang-secondary-ui', secondary.color);
    root.style.setProperty('--lang-trim-secondary', secondary.color);
}

window.addEventListener('fluency-theme-change', () => {
    applyLanguageColorTheme();
});

// Shared vocabulary filter pipeline used by renderRangeSelector and loadVocabularyData.
// Applies all active exclusions in the correct order and assigns corpus-wide display ranks.
// Returns { vocab: filteredArray, counts: { english, cognates, singleOcc, lemma } }



function getSetupLearningState(item, { seenLemmas = new Set(), estimatedIds = null, estimate = 0 } = {}) {
    if (currentUser?.isGuest) return window.getGuestSessionLearningState?.(item) || false;
    if (!currentUser || !progressData) return false;

    // Only the answer recorded against this card is memoised. Lemma
    // inheritance and the level estimate depend on the caller's options and on
    // Fast Track, neither of which moves the progress epoch: memoising them
    // let one caller's answer (no lemma set, or merge off) stand for the next,
    // so setup advertised new cards the deck loader then removed. When that
    // was every remaining card, Learn New bounced to a different set.
    const recordedState = getRecordedSetupState(item);
    if (recordedState.seen) return recordedState;

    // Merge Lemmas treats progress on any surface form as progress on the
    // shared lemma. This is the same set used by Learn New during deck build,
    // so the button count cannot advertise cards that will then be removed.
    const lemmaKey = typeof globalThis.lemmaSeenKey === 'function'
        ? globalThis.lemmaSeenKey(item)
        : (globalThis.lemmaGroupKey?.(item) || item.lemma);
    if (lemmaKey && seenLemmas.has(lemmaKey)) {
        return { ...recordedState, seen: true, needsReview: false, learned: true, inheritedLemma: true };
    }

    if (window.playlistLiveActive?.()) {
        return recordedState;
    }

    if (activeArtist) {
        if (window.isCoveredByEstimatedIds?.(item, estimatedIds)) {
            return { seen: true, needsReview: false, learned: true, estimated: true };
        }
    } else if (item.rank <= estimate) {
        return { seen: true, needsReview: false, learned: true, estimated: true };
    }
    return recordedState;
}

// What this card's own progress says, across its related and cross-mode
// records. Depends only on progress, so it is memoised per progress epoch.
function getRecordedSetupState(item) {
    // Progress changes in place after every answer and after a background
    // Sheets refresh. A set render can therefore outlive the memo created by
    // renderLevelSelector. Never let yesterday's "unseen" result disagree
    // with the deck loader's current progress snapshot.
    ensureCurrentSetupStateMemo();
    const wordId = getWordId(item);
    if (_setupStateMemo?.has(wordId)) return _setupStateMemo.get(wordId);
    const memoise = value => {
        _setupStateMemo?.set(wordId, value);
        return value;
    };
    const relatedIds = window.getProgressRecordIdsForCard?.(wordId, item.word) || [wordId];
    const recorded = getWordProgressState(wordId, item.word);
    const reviewInfo = getWordKnowledgeReviewInfo(wordId, item.word);

    // A real answer is more specific than the estimated starting level;
    // in particular, a later wrong must remain reviewable. Setup and deck
    // construction must inspect the same current/cross-mode identities.
    // getWordKnowledgeReviewInfo always returns an object ({needsReview,
    // reason, reviewAt}), never null — every other caller reads .needsReview.
    // Testing the object itself made this branch unconditional, so every card
    // reported seen + needsReview and the setup screen showed 0 known and
    // 0 unseen for the whole deck.
    if (reviewInfo?.needsReview) {
        return memoise({
            ...recorded,
            seen: true,
            needsReview: true,
            learned: false,
            reviewReason: reviewInfo.reason,
            reviewAt: reviewInfo.reviewAt
        });
    }
    if (recorded?.seen) return memoise(recorded);
    if (relatedIds.some(id => getWordProgressState(id).seen || wordHasKnowledgeProgress(id))) {
        return memoise({ ...recorded, seen: true });
    }
    return memoise(recorded || { seen: false });
}

async function renderRangeSelector({ landingRowsChecked = 0 } = {}) {
    // Every set count below is computed from `progressData`, and an empty
    // `progressData` reads identically whether the learner has studied nothing
    // or the progress fetch simply has not landed. Rendering on the second
    // marks every set unseen, lands the learner on set 1 of level 1, and then
    // corrects itself on the next render — the "it sends me to the wrong place
    // and then the boxes fill in" behaviour. Wait for the answer, with a cap
    // so an unreachable Sheets never leaves the screen empty.
    if (currentUser && !currentUser.isGuest) {
        await (window.whenProgressReady?.() ?? Promise.resolve(true));
    }
    // This function is also called directly after progress refreshes and when
    // returning from a completed deck, without passing through the level
    // renderer. Give every visible set count one coherent, current snapshot.
    resetSetupStateMemo();
    const baseConfig = config.languages[selectedLanguage] || {};
    const langConfig = activeArtist ? { ...baseConfig, ...activeArtist } : baseConfig;
    const container = document.getElementById('rangeSelector');
    window.__studySessionContext = null;
    const reviewSection = document.getElementById('reviewDeckSection');
    if (reviewSection) reviewSection.hidden = true;
    let minWord, maxWord;
    let rankBasis = 'source';

    let selectedLevelBtn = document.querySelector('.level-btn.selected');
    if (!selectedLevelBtn && selectedLevel) {
        selectedLevelBtn = document.querySelector(`.level-btn[data-level="${selectedLevel}"]`);
        if (selectedLevelBtn) {
            selectedLevelBtn.classList.add('selected');
            selectedLevelBtn.textContent = selectedLevelBtn.dataset.full || selectedLevelBtn.textContent;
        }
    }
    // Artist Extra category groups carry their own rank block on the selected
    // level button and are independent of percentage/CEFR mode.
    if (selectedLevelBtn?.dataset.releaseLevel === 'true') {
        minWord = parseInt(selectedLevelBtn.dataset.startRank);
        maxWord = parseInt(selectedLevelBtn.dataset.endRank);
        rankBasis = 'source';
    } else if (selectedLevelBtn?.dataset.rankBasis === 'category') {
        minWord = parseInt(selectedLevelBtn.dataset.startRank);
        maxWord = parseInt(selectedLevelBtn.dataset.endRank);
        rankBasis = 'category';
    } else if (percentageMode && ppmData && ppmData.length > 0) {
        const selectedBtn = selectedLevelBtn;
        if (!selectedBtn) return;
        minWord = parseInt(selectedBtn.dataset.startRank);
        maxWord = parseInt(selectedBtn.dataset.endRank);
        rankBasis = selectedBtn.dataset.rankBasis || 'source';
    } else if (!activeArtist && !window.playlistLiveActive?.() && releaseStudyStructure?.levels) {
        const rLevel = releaseStudyStructure.levels.find(item => item.level === selectedLevel || item.level_id === selectedLevel);
        if (rLevel) {
            minWord = rLevel.startRank;
            maxWord = rLevel.endRank;
            rankBasis = rLevel.rankBasis || 'source';
        } else {
            const ranges = getActiveLevelRanges();
            const found = ranges.find(item => String(item.level) === String(selectedLevel)) || ranges[0];
            if (!found) return;
            minWord = found.startRank;
            maxWord = found.endRank;
            rankBasis = found.rankBasis || 'source';
        }
    } else {
        const ranges = getActiveLevelRanges();
        const found = ranges.find(item => String(item.level) === String(selectedLevel)) || ranges[0];
        if (!found) return;
        minWord = found.startRank;
        maxWord = found.endRank;
        rankBasis = found.rankBasis || 'source';
    }
    if (!Number.isFinite(minWord) || !Number.isFinite(maxWord)) {
        console.warn('renderRangeSelector: bad level boundary', { minWord, maxWord, selectedLevel });
        container.innerHTML = '';
        return;
    }

    let vocabularyData = [];
    try {
        vocabularyData = await fetchActiveVocabularyData(langConfig);
    } catch (error) {
        console.error('Failed to load vocabulary data:', error);
    }
    const preparedVocabulary = getPreparedSetupVocabulary(selectedLanguage, vocabularyData);
    const filteredVocab = preparedVocabulary?.vocab || [];
    // The merged/excluded counts used to be restated here, in a second wording,
    // under controls whose own buttons already carry them. extras.js owns that
    // figure now so there is one of it.

    const rankOf = _levelRankAccessor(rankBasis);
    const wordsInLevel = filteredVocab.filter(item => {
        const rank = rankOf(item);
        return rank >= minWord && rank < maxWord;
    });
    if (wordsInLevel.length === 0 && !(preparedVocabulary?.stableBaseline || []).some(item => {
        const rank = rankOf(item);
        return rank >= minWord && rank < maxWord;
    })) {
        container.innerHTML = '<div class="study-set-empty">No cards remain in this level with the current settings.</div>';
        document.getElementById('step4').style.display = 'block';
        return;
    }

    const estimate = levelEstimates[selectedLanguage] || 0;
    for (const id of ['levelEstimatedLegend', 'step2EstimatedLegend']) {
        const legend = document.getElementById(id);
        if (legend) legend.hidden = estimate <= 0;
    }
    const estimatedIds = (activeArtist && !window.playlistLiveActive?.()) && currentUser && !currentUser.isGuest
        ? await buildEstimatedKnownIds(estimate)
        : null;
    const seenLemmas = await window.buildSeenLemmaSet?.(vocabularyData) || new Set();
    renderHomeLevelTiles({
        vocab: filteredVocab, baseline: preparedVocabulary?.stableBaseline || [],
        seenLemmas, estimatedIds, estimate, smartSkipOn: Boolean(window.isFastTrackOn?.())
    });

    // Fixed rank regions retain estimation and legacy-session compatibility.
    // The visible progress bar aggregates the whole level by learning status.
    const slotRanges = buildStableSetRanges(minWord, maxWord, rankBasis);
    const slotCount = slotRanges.length;
    const slots = Array.from({ length: slotCount }, () => []);
    for (let i = 0; i < wordsInLevel.length; i++) {
        const item = wordsInLevel[i];
        const rank = rankOf(item);
        const slotIdx = Math.floor((rank - minWord) / STABLE_SET_SLOT_COUNT);
        if (slotIdx >= 0 && slotIdx < slotCount) {
            slots[slotIdx].push(item);
        }
    }

    const smartSkipOn = Boolean(window.isFastTrackOn?.());
    // Cards Smart Skip set aside, per slot: what the unfiltered baseline holds
    // in the slot that the filtered deck does not.
    const baselineSlotCounts = new Array(slotCount).fill(0);
    for (const item of (preparedVocabulary?.stableBaseline || [])) {
        const slotIdx = Math.floor((rankOf(item) - minWord) / STABLE_SET_SLOT_COUNT);
        if (slotIdx >= 0 && slotIdx < slotCount) baselineSlotCounts[slotIdx]++;
    }
    const ranges = [];
    const levelUpcomingTimes = [];
    const upcomingNow = Date.now();
    for (let slotIdx = 0; slotIdx < slotCount; slotIdx++) {
        const { startRank: start, endRank: end } = slotRanges[slotIdx];
        const words = slots[slotIdx];
        let seenCount = 0;
        let reviewCount = 0;
        let dueCount = 0;
        let estimatedCount = 0;
        for (let i = 0; i < words.length; i++) {
            const state = getSetupLearningState(words[i], {
                seenLemmas,
                estimatedIds,
                estimate
            });
            if (state?.seen) seenCount++;
            if (state?.estimated) estimatedCount++;
            if (state?.needsReview) reviewCount++;
            if (state?.reviewReason === 'due') dueCount++;
            if (state && !state.needsReview && state.nextReviewAt > upcomingNow) levelUpcomingTimes.push(state.nextReviewAt);
        }
        const skippedCount = smartSkipOn ? Math.max(0, baselineSlotCounts[slotIdx] - words.length) : 0;
        const slotTotal = words.length + skippedCount;
        const knownCount = Math.max(0, seenCount - reviewCount - estimatedCount);
        const unseenCount = words.length - seenCount;
        ranges.push({
            range: `${start}-${end}`,
            start,
            end,
            available: words.length > 0,
            cardCount: words.length,
            seenCount,
            knownCount,
            unseenCount,
            reviewCount,
            dueCount,
            estimatedCount,
            skippedCount,
            pct: words.length > 0 ? Math.round(100 * seenCount / words.length) : 100,
            // The bar covers the whole slot: skipped cards take the right-hand
            // share, so a level with Smart Skip on starts partly filled.
            knownPct: slotTotal > 0 ? 100 * knownCount / slotTotal : 100,
            reviewEndPct: slotTotal > 0 ? 100 * (knownCount + reviewCount) / slotTotal : 100,
            estimatedEndPct: slotTotal > 0 ? 100 * (knownCount + reviewCount + estimatedCount) / slotTotal : 100,
            newEndPct: slotTotal > 0 ? 100 * words.length / slotTotal : 100
        });
    }
    const firstUnseen = ranges.findIndex(range => range.available && range.unseenCount > 0);
    const initialIndex = Math.max(0, firstUnseen);

    // Until a set's row file loads, its cards are counted without their
    // meanings, and the deck builder later drops any card whose meanings have
    // no translation. A set whose only unseen cards were such rows advertised
    // "Learn 1 new card", built nothing, and bounced the learner to another
    // set on every fresh load. Load the landing set's rows (the file Start
    // would fetch anyway) and count again before offering it. Capped so a run
    // of such sets cannot hold the screen.
    const landingWords = wordsInLevel.filter(item => !getSetupLearningState(item, {
        seenLemmas, estimatedIds, estimate
    })?.seen).slice(0, STUDY_SESSION_LIMIT);
    if (landingRowsChecked < 3 && ranges[initialIndex]?.unseenCount > 0
        && landingWords.some(item => item._indexRowsPending)) {
        const loaded = await window.ensureIndexRowsForRange?.(
            langConfig, 0, 0, landingWords.map(item => item.sourceRank || item.rank)
        ).catch(() => false);
        if (loaded) {
            invalidatePreparedSetupVocabulary();
            return renderRangeSelector({ landingRowsChecked: landingRowsChecked + 1 });
        }
    }

    const levelReviewCount = ranges.reduce((sum, range) => sum + range.reviewCount, 0);
    const levelDueCount = ranges.reduce((sum, range) => sum + range.dueCount, 0);
    const levelUnfinishedCount = Math.max(0, levelReviewCount - levelDueCount);
    const levelKnownCount = ranges.reduce((sum, range) => sum + range.knownCount, 0);
    const levelSeenCount = ranges.reduce((sum, range) => sum + range.seenCount, 0);
    const levelCardCount = ranges.reduce((sum, range) => sum + range.cardCount, 0);
    const levelButtonsForNumber = Array.from(document.querySelectorAll(
        '.level-selector-buttons .level-btn, #levelSelector > .level-btn'
    ));
    const levelNumber = levelButtonsForNumber.findIndex(button => button.dataset.level === selectedLevel) + 1;

    // The language context lets the Practice sheet read the same global queue as
    // the setup screen without depending on the currently selected set.
    window.__reviewHomeContext = {
        language: selectedLanguage,
        range: `${minWord}-${maxWord}`,
        rankBasis,
        levelNumber,
        levelLabel: levelNumber > 0 ? `Level ${levelNumber}` : 'This level',
        levelReviewCount,
        levelDueCount,
        levelUnfinishedCount,
        levelKnownCount,
        levelSeenCount,
        levelCardCount
    };

    // SETWISE-2: Practise is the language-wide queue, with its own length chip.
    const plan = window.SessionPlan;
    const lengthInfo = plan?.sessionLengthInfo?.() || { label: `${STUDY_SESSION_LIMIT} cards`, spoken: `${STUDY_SESSION_LIMIT} cards` };
    const lengthChip = (available, kind) => {
        const cap = plan?.sessionCardLimit?.(kind) || STUDY_SESSION_LIMIT;
        if (available <= 0 || (lengthInfo.minutes && available < cap)) return '';
        return `<button type="button" class="session-length-chip" data-session-length-toggle
            aria-label="Session length: ${lengthInfo.spoken}. Tap to change.">${lengthInfo.label}</button>`;
    };
    // The home button: optional length segment, then the action. One per section.
    const homeCta = (chip, buttonAttrs, label, disabled) => `<div class="home-cta${disabled ? ' is-disabled' : ''}">
            ${chip.replace('class="session-length-chip"', 'class="home-cta-length"')}
            <button type="button" class="home-cta-main" ${buttonAttrs} ${disabled ? 'disabled' : ''}>${label}</button>
        </div>`;
    let reviewHTML = '';
    let practiseMistakes = 0;
    let practiseTotal = 0;
    let practiseDue = 0;
    // Practise appears once the learner has answered anything at all; before
    // that the home screen is Learn alone. Caught up later, it stays and says so.
    const hasAnswered = typeof progressData !== 'undefined' && progressData && Object.keys(progressData).length > 0;
    if (currentUser && !currentUser.isGuest && hasAnswered) {
        const summary = window.getGlobalDueReviewSummary?.(selectedLanguage) || null;
        const globalTotal = Number(summary?.total) || 0;
        const mistakes = (summary?.neverRight?.length || 0) + (summary?.critical?.length || 0);
        const dueCount = summary?.due?.length || 0;
        practiseMistakes = mistakes;
        practiseTotal = globalTotal;
        practiseDue = dueCount;
        const srsOn = typeof spacedRepetitionEnabled === 'undefined' || spacedRepetitionEnabled !== false;
        const upcoming = plan?.summariseUpcoming?.(window.getUpcomingReviewTimes?.(selectedLanguage) || []) || null;
        // What comes back later only matters once nothing is waiting.
        const upcomingText = plan?.describeUpcoming?.(upcoming) || '';

        const practiseCap = plan?.sessionCardLimit?.('practice') || QUICK_REVIEW_LIMIT;
        const practiseCount = Math.min(globalTotal, practiseCap);
        const row = (tone, label, count) => `<div class="home-practise-row is-${tone}">
                <i aria-hidden="true"></i><span>${label}</span><b>${count.toLocaleString()}</b>
            </div>`;
        let body;
        if (globalTotal > 0) {
            const peekBar = [['is-mistake', mistakes], ['is-due', dueCount]].filter(([, n]) => n > 0)
                .map(([kind, n]) => `<span class="${kind}" style="flex-grow:${n}"></span>`).join('');
            body = `<div class="home-practise-total"><p><strong>${globalTotal.toLocaleString()}</strong> ${globalTotal === 1 ? 'word' : 'words'} waiting <span>· all levels</span></p>
                    <div class="home-practise-bar" aria-hidden="true">${peekBar}</div></div>
                <div class="home-practise-rows">
                    ${mistakes > 0 ? row('mistake', 'Mistakes', mistakes) : ''}
                    ${dueCount > 0 ? row('due', 'Time to review', dueCount) : ''}
                </div>`;
        } else {
            const empty = !srsOn
                ? 'Review schedule paused: only mistakes come back.'
                : (upcomingText || 'Words you miss will collect here.');
            body = `<div class="home-practise-total is-empty"><strong>All caught up</strong><span>${empty}</span></div>`;
        }
        reviewHTML = `<div class="home-practise">
                ${body}
                <button class="home-practise-browse" type="button" id="openReviewHomeBtn">Browse all <span aria-hidden="true">›</span></button>
            </div>
            <div class="home-section-footer">
                ${mistakes > 0 && dueCount > 0 ? '<p class="home-footer-hint">Mistakes first</p>' : ''}
                ${homeCta(lengthChip(globalTotal, 'practice'), 'id="quickReviewBtn"',
                    globalTotal > 0 ? `Practise<span class="home-cta-count"> · ${practiseCount.toLocaleString()}</span>` : 'Practise', globalTotal === 0)}
            </div>`;
    }

    const levelNewCount = ranges.reduce((sum, range) => sum + range.unseenCount, 0);
    const levelEstimatedCount = ranges.reduce((sum, range) => sum + range.estimatedCount, 0);
    const levelSkippedCount = ranges.reduce((sum, range) => sum + range.skippedCount, 0);
    // Group each status once across the whole level; this bar is not a rank map.
    const levelTotal = levelCardCount + levelSkippedCount;
    const percent = count => levelTotal > 0 ? 100 * count / levelTotal : 0;
    const progressStyle = `--level-new-end:${percent(levelNewCount)}%;`
        + `--level-review-end:${percent(levelNewCount + levelReviewCount)}%;`
        + `--level-known-end:${percent(levelNewCount + levelReviewCount + levelKnownCount)}%;`
        + `--level-estimated-end:${percent(levelCardCount)}%`;
    // What Go does for this level (SETWISE-2):
    //   new     new words left, Practise small: start straight away
    //   choice  new words left, but more of the level waits in Practise
    //   met     every word met, some waiting in Practise
    //   done    every word met and up to date
    const levelKey = `${selectedLanguage}|${minWord}-${maxWord}`;
    const levelState = levelNewCount > 0
        ? (levelReviewCount >= LEVEL_CHOICE_MIN_PRACTICE && levelReviewCount > levelNewCount
            && !_levelChoiceDeclined.has(levelKey) ? 'choice' : 'new')
        : levelReviewCount > 0 ? 'met' : 'done';
    const context = {
        range: `${minWord}-${maxWord}`, rankBasis, levelNumber, levelKey, levelState,
        unseenCount: levelNewCount, reviewCount: levelReviewCount, cardCount: levelCardCount, ranges,
        knownCount: levelKnownCount,
        levelUpcoming: plan?.summariseUpcoming?.(levelUpcomingTimes) || null,
        studyMode: levelNewCount > 0 ? 'new' : levelReviewCount > 0 ? 'review' : 'all'
    };
    window.__studySessionContext = context;
    const scopeLabel = document.getElementById('studySessionLevel');
    if (scopeLabel) scopeLabel.textContent = levelNumber > 0 ? ` · Level ${levelNumber}` : ' · Selected level';
    const nextCount = Math.min(plan?.sessionCardLimit?.(context.studyMode === 'review' ? 'practice' : 'new') || STUDY_SESSION_LIMIT,
        levelNewCount || levelReviewCount || levelCardCount);
    // Start this session's downloads (word rows, example sentences) while the
    // learner reads the home screen, so Go finds them here instead of waiting
    // ~2.5 s. Repeat renders reuse the loaded or in-flight shards.
    if (nextCount > 0) {
        const baseConfig = config.languages[selectedLanguage] || {};
        window.prefetchStudySetPayload?.(activeArtist ? { ...baseConfig, ...activeArtist } : baseConfig, context.range);
    }
    // Practise is language-wide, so this level's words that are waiting there
    // are shown as "Seen" here rather than as a per-level Practice count.
    const description = `${levelNewCount} new, ${levelReviewCount} seen, ${levelKnownCount} known, ${levelEstimatedCount} estimated, ${levelSkippedCount} skipped`;
    const goDisabled = nextCount === 0 || _studySessionStarting;
    const segments = [
        ['new', 'New', levelNewCount],
        ['seen', 'Seen', levelReviewCount],
        ['known', 'Known', levelKnownCount],
        ['estimated', 'Estimated', levelEstimatedCount],
        ['skipped', 'Skipped', levelSkippedCount]
    ];
    const barHTML = segments.filter(([, , n]) => n > 0)
        .map(([kind, , n]) => `<span class="is-${kind}" style="flex-grow:${n}"></span>`).join('');
    // Estimated words get a line of their own: with them the legend no longer fits a phone.
    const statsHTML = segments.filter(([kind, , n]) => kind !== 'estimated' && (n > 0 || kind === 'new'))
        .map(([kind, label, n]) => `<span class="home-level-stat is-${kind}"><i aria-hidden="true"></i>${n.toLocaleString()} ${label}</span>`).join('');
    const estimateHTML = levelEstimatedCount > 0
        ? `<p class="home-level-estimate"><i aria-hidden="true"></i>${levelEstimatedCount.toLocaleString()} skipped by your level estimate</p>`
        : '';
    container.innerHTML = `
        <div class="home-level-progress">
            <div class="home-level-bar step-help-btn" role="button" tabindex="0" data-tooltip="levelColoursTooltip" aria-label="Level progress: ${description}. Click for details" aria-haspopup="dialog" title="Level progress details">${barHTML}</div>
            <div class="home-level-stats">${statsHTML}</div>
            ${estimateHTML}
        </div>`;
    window.fitLegendFonts?.(container);
    const learnLabel = nextCount === 0
        ? 'No cards available'
        : `Learn${levelNewCount > 0 ? `<span class="home-cta-count"> · ${nextCount.toLocaleString()} new</span>` : ''}`;
    const learnSlot = document.getElementById('learnActionSlot');
    if (learnSlot) {
        learnSlot.innerHTML = homeCta(levelNewCount > 0 && nextCount > 0 ? lengthChip(levelNewCount, 'new') : '',
            `id="studySetStartBtn" data-range="${context.range}" data-rank-basis="${rankBasis}" data-level-state="${levelState}"
             data-study-mode="${context.studyMode}" data-level-number="${levelNumber}"`,
            learnLabel, goDisabled);
    }
    if (reviewSection) {
        const reviewBody = document.getElementById('reviewDeckBody');
        if (reviewBody) reviewBody.innerHTML = reviewHTML;
        reviewSection.hidden = !reviewHTML;
    }
    // The folded section keeps a one-line version of itself: Learn its level
    // and words, Practise how many are waiting.
    const learnMeta = document.getElementById('learnSectionMeta');
    if (learnMeta) {
        const wordsText = document.getElementById('homeLevelWords')?.textContent || '';
        learnMeta.textContent = `${levelNumber > 0 ? `Level ${levelNumber}` : 'This level'}${wordsText ? ` · ${wordsText}` : ''}`;
    }
    const learnPeek = document.getElementById('learnSectionPeek');
    if (learnPeek) {
        // Folded (Practise open), Learn says only its level and words (the meta
        // line above), so the open Practise has the attention.
        learnPeek.innerHTML = '';
        learnPeek.hidden = true;
    }
    const practiseMeta = document.getElementById('practiseSectionMeta');
    if (practiseMeta) {
        practiseMeta.textContent = practiseTotal > 0 ? `${practiseTotal.toLocaleString()} waiting` : 'All caught up';
    }
    const practisePeek = document.getElementById('practiseSectionPeek');
    if (practisePeek) {
        // Folded, Practise says only how many are waiting (in the meta line above);
        // the mistakes / due breakdown is for the open section.
        practisePeek.innerHTML = '';
        practisePeek.hidden = !practisePeek.innerHTML;
    }
    applyHomeSection(reviewHTML ? practiseMistakes : -1);
    document.getElementById('step4').style.display = 'block';
    setActiveSetupStep('step4');
    document.getElementById('studySetStartBtn').addEventListener('click', async function() {
        if (this.disabled || _studySessionStarting) return;
        if (window.__studySessionContext?.levelState && window.__studySessionContext.levelState !== 'new') {
            openLevelChoice(window.__studySessionContext);
            return;
        }
        await runLevelSession(this, 'new');
    });
    reviewSection?.querySelector('#openReviewHomeBtn')?.addEventListener('click', () => {
        window.openReviewHome?.();
    });
    reviewSection?.querySelector('#quickReviewBtn')?.addEventListener('click', async () => {
        const summary = window.getGlobalDueReviewSummary?.(selectedLanguage) || null;
        const cap = window.SessionPlan?.sessionCardLimit?.('practice') || QUICK_REVIEW_LIMIT;
        const limit = Math.min(Number(summary?.total) || 0, cap);
        if (limit <= 0) return;
        const loadingMessage = document.getElementById('loadingMessage');
        loadingMessage.style.display = 'block';
        loadingMessage.textContent = `Loading ${limit} practice card${limit === 1 ? '' : 's'}...`;
        await startDailyReview({ limit, urgencyTier: 'all' });
    });
    document.querySelectorAll('#step4 [data-session-length-toggle], #reviewDeckSection [data-session-length-toggle]')
        .forEach(chip => chip.addEventListener('click', () => {
            window.SessionPlan?.cycleSessionLength?.();
            refreshSessionLengthChips();
        }));

    renderSetupExtrasSection();
}

function refreshSessionLengthChips() {
    // The selected length changes both the advertised count and whether the
    // time choice is relevant to the available cards.
    return renderRangeSelector();
}

// Recount after sync, then start the level session the learner asked for.
// A recount that removes the cards (answers synced from another device) only
// re-renders; it never swaps one kind of session for another.
async function runLevelSession(button, studyMode) {
    if (_studySessionStarting) return;
    _studySessionStarting = true;
    if (button) button.disabled = true;
    window.showAppLoading?.('Preparing your session', 'Loading your cards…');
    try {
        await window.progressRefreshSettled?.(5000);
        await renderRangeSelector();
        const fresh = window.__studySessionContext;
        if (!fresh) return;
        if (studyMode === 'new' && !(fresh.unseenCount > 0)) return;
        if (studyMode === 'review' && !(fresh.reviewCount > 0)) return;
        await startSelectedStudySession({ studyMode });
    } finally {
        _studySessionStarting = false;
        const current = document.getElementById('studySetStartBtn');
        if (current && window.__studySessionContext) current.disabled = !(window.__studySessionContext.cardCount > 0);
        window.hideAppLoading?.();
    }
}

function closeLevelChoice() {
    document.getElementById('levelChoiceModal')?.classList.add('hidden');
}

let _levelChoiceWired = false;
function wireLevelChoice() {
    if (_levelChoiceWired) return;
    _levelChoiceWired = true;
    document.getElementById('closeLevelChoiceModal')?.addEventListener('click', closeLevelChoice);
    document.getElementById('levelChoiceModal')?.addEventListener('click', event => {
        if (event.target?.id === 'levelChoiceModal') closeLevelChoice();
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') closeLevelChoice();
    });
    document.getElementById('levelChoiceActions')?.addEventListener('click', async event => {
        const action = event.target.closest('[data-level-choice]')?.dataset.levelChoice;
        if (!action) return;
        closeLevelChoice();
        const context = window.__studySessionContext;
        if (action === 'practise') {
            await runLevelSession(document.getElementById('studySetStartBtn'), 'review');
        } else if (action === 'learn-new') {
            if (context?.levelKey) _levelChoiceDeclined.add(context.levelKey);
            await runLevelSession(document.getElementById('studySetStartBtn'), 'new');
        } else if (action === 'redo') {
            await runLevelSession(document.getElementById('studySetStartBtn'), 'all');
        } else if (action === 'next-level') {
            window.showAppLoading?.('Preparing your next session', 'Finding your next cards…');
            try {
                await startNextStudyLevelFirstSet();
            } catch (error) {
                console.warn('Could not open the next level:', error);
            } finally {
                window.hideAppLoading?.();
            }
        }
    });
}

// Learn and Practise share the home screen and one is open at a time. Learn
// opens first; Practise stays folded (with its short version) until the
// learner opens it this visit. `mistakes` is -1 when there is no Practise.
let _homeSectionChosen = null;
let _homeSectionWired = false;
function applyHomeSection(mistakes) {
    const panel = document.getElementById('setupPanel');
    if (!panel?.querySelectorAll) return;
    if (!_homeSectionWired) {
        _homeSectionWired = true;
        panel.addEventListener('click', event => {
            const toggle = event.target.closest('.home-section-toggle');
            if (!toggle) return;
            if (event.target.closest('.home-section-info')) return; // opens its info sheet instead
            _homeSectionChosen = toggle.dataset.homeSection;
            setHomeSectionOpen(panel, _homeSectionChosen);
        });
    }
    const open = mistakes < 0 ? 'learn' : (_homeSectionChosen || 'learn');
    setHomeSectionOpen(panel, open);
}

function setHomeSectionOpen(panel, open) {
    panel.dataset.homeOpen = open;
    panel.querySelectorAll('.home-section-toggle').forEach(toggle =>
        toggle.setAttribute('aria-expanded', String(toggle.dataset.homeSection === open)));
}

// The screen Go opens when a level has little or nothing new to give.
function openLevelChoice(context) {
    const modal = document.getElementById('levelChoiceModal');
    if (!modal || !context) return;
    wireLevelChoice();
    const plan = window.SessionPlan;
    const length = plan?.sessionLengthInfo?.();
    const practiseCap = plan?.sessionCardLimit?.('practice') || STUDY_SESSION_LIMIT;
    const level = context.levelNumber > 0 ? `Level ${context.levelNumber}` : 'this level';
    const Level = context.levelNumber > 0 ? `Level ${context.levelNumber}` : 'This level';
    const words = count => `${count.toLocaleString()} word${count === 1 ? '' : 's'}`;
    const review = Number(context.reviewCount) || 0;
    const fresh = Number(context.unseenCount) || 0;
    const practiseLabel = review <= practiseCap || !length?.minutes
        ? `Practise ${review === 1 ? 'this word' : `these ${review.toLocaleString()}`}`
        : `Practise · ${length.label}`;
    const next = getNextStudyLevelMeta();
    const nextLabel = next ? (next.label ? `Go to ${next.label}` : `Go to Level ${next.levelNumber}`) : '';
    const upcoming = context.levelUpcoming;
    const button = (action, label, kind) => `<button type="button" class="level-choice-btn is-${kind}" data-level-choice="${action}">${_escapeHtml(label)}</button>`;

    let title = '';
    let text = '';
    let actions = '';
    if (context.levelState === 'choice') {
        title = `${Level}: ${fresh.toLocaleString()} new ${fresh === 1 ? 'word' : 'words'} left, ${review.toLocaleString()} waiting in Practise.`;
        text = 'Practise first to keep what you have met, or carry on with the new words.';
        actions = button('practise', practiseLabel, 'practice')
            + button('learn-new', `Learn the ${fresh === 1 ? 'new one' : `${fresh.toLocaleString()} new`}`, 'secondary');
    } else if (context.levelState === 'met') {
        title = `No new words left in ${level}.`;
        const later = plan?.describeUpcoming?.(upcoming) || '';
        text = `${words(review)} ${review === 1 ? 'is' : 'are'} waiting in Practise. ${later || 'The rest come back when they are due.'}`;
        actions = button('practise', practiseLabel, 'practice')
            + (next ? button('next-level', nextLabel, 'secondary') : '')
            + button('redo', `Redo ${level} anyway`, 'link');
    } else {
        const answered = Number(context.knownCount) > 0;
        title = answered ? `You've mastered all the words in ${level}.` : `Nothing new in ${level}.`;
        const when = upcoming?.nextLabel ? ` The first ones come back ${upcoming.nextLabel}.` : '';
        text = answered
            ? `They'll come back for review when they're due.${when}`
            : 'Every word here is marked familiar or skipped.';
        if (!next) text += ` You've finished the deck.`;
        actions = (next ? button('next-level', nextLabel, 'primary') : '')
            + button('redo', `Redo ${level} anyway`, 'link');
    }
    document.getElementById('levelChoiceEyebrow').textContent = 'Your next session';
    document.getElementById('levelChoiceTitle').textContent = title;
    document.getElementById('levelChoiceText').textContent = text;
    document.getElementById('levelChoiceActions').innerHTML = actions;
    modal.classList.remove('hidden');
    modal.querySelector('.level-choice-btn')?.focus();
}
window.openLevelChoice = openLevelChoice;

function _escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function renderSetupExtrasSection() {
    // All excluded and supplementary vocabulary now lives in Smart Skip.
    const section = document.getElementById('extrasDeckSection');
    if (section) section.style.display = 'none';
    renderFastTrackSkippedDecks();
}

// The Smart Skip page's word list. extras.js owns it; this only hands over the
// level ranges, which live here.
function renderFastTrackSkippedDecks() {
    globalThis.renderSkippedWords?.();
}

function _findLevelButtonIndex(buttons, targetLevel) {
    if (!targetLevel && targetLevel !== 0) return -1;
    const targetStr = String(targetLevel);
    let idx = buttons.findIndex(b => b.dataset.level === targetStr || b.dataset.short === targetStr);
    if (idx >= 0) return idx;
    const num = parseInt(targetStr.replace(/\D/g, ''), 10);
    if (!Number.isNaN(num)) {
        idx = buttons.findIndex((b, i) => {
            const bNum = parseInt(b.dataset.level?.replace(/\D/g, '') || '', 10);
            return bNum === num || (i + 1) === num;
        });
        if (idx >= 0) return idx;
    }
    return -1;
}

// Compatibility accessor for legacy saved sets. Fresh sessions use a whole level.
function getNextStudySetMeta(rangeString, studyMode = 'new') {
    const context = window.__studySessionContext;
    if (!context) return null;
    const end = Number(rangeString.split('-')[1]);
    const remaining = context.ranges.filter(range => range.start >= end);
    const next = remaining.find(range => studyMode === 'review' ? range.reviewCount > 0 : range.unseenCount > 0);
    return next ? { range: context.range, rankBasis: context.rankBasis,
        setNumber: null, levelSetCount: null, hasUnseen: next.unseenCount > 0,
        hasReview: next.reviewCount > 0 } : null;
}

async function startSelectedStudySession({ studyMode } = {}) {
    const context = window.__studySessionContext;
    if (!context) return false;
    return loadVocabularyData(context.range, {
        rankBasis: context.rankBasis, levelNumber: context.levelNumber,
        studyMode: studyMode || context.studyMode, levelSession: true,
        sessionLimit: window.SessionPlan?.sessionCardLimit?.(
            (studyMode || context.studyMode) === 'review' ? 'practice' : 'new') || STUDY_SESSION_LIMIT,
        silentIfEmpty: true
    });
}
window.startSelectedStudySession = startSelectedStudySession;

function getNextStudyLevelMeta() {
    const buttons = Array.from(document.querySelectorAll(
        '.level-selector-buttons .level-btn, #levelSelector > .level-btn'
    ));
    const currentIndex = _findLevelButtonIndex(buttons, selectedLevel);
    const remaining = currentIndex >= 0 ? buttons.slice(currentIndex + 1) : buttons;
    const next = remaining.find(button => {
        const completion = Number(button.dataset.progressPct || 0);
        return completion < 100 || currentIndex < 0;
    }) || null;
    if (!next) return null;
    const nextIndex = buttons.indexOf(next);
    return {
        level: next.dataset.level,
        levelNumber: nextIndex + 1,
        // In Extra scope the next "level" is another category — carry its label
        // so the finish button can name the group instead of a level number.
        label: activeArtist && artistVocabularyScope === 'extra'
            ? (next.dataset.full || null)
            : null
    };
}

async function startNextStudyLevelFirstSet() {
    // Recount after answers/sync; continue within this level before moving on.
    // Never silently replay a completed level or pull practice into new learning.
    await window.progressRefreshSettled?.(5000);
    await renderRangeSelector();
    if (window.__studySessionContext?.unseenCount > 0) {
        if (await startSelectedStudySession({ studyMode: 'new' }) !== false) return;
    }

    const visitedLevels = new Set();
    while (true) {
        const nextMeta = getNextStudyLevelMeta();
        if (!nextMeta) throw new Error('No next study level with new cards is available');
        if (nextMeta.scope === 'extra') {
            await window.goBackToSetup?.();
            await window.setArtistVocabularyScope?.('extra', { autoStart: true });
            return;
        }
        if (!nextMeta.level || visitedLevels.has(nextMeta.level)) {
            throw new Error('Could not resolve a distinct next study level');
        }
        visitedLevels.add(nextMeta.level);

        // Render the candidate level before selecting its next eligible batch.
        const next = document.querySelector(
            `.level-btn[data-level="${CSS.escape(nextMeta.level)}"]`);
        if (!next) throw new Error(`Could not find next level ${nextMeta.level}`);

        next.click();
        if (!next._rangeRenderPromise) {
            throw new Error('Next level did not begin rendering its progress');
        }
        await next._rangeRenderPromise;
        if (!(window.__studySessionContext?.unseenCount > 0)) continue;
        const built = await startSelectedStudySession({ studyMode: 'new' });
        if (built === false) continue;
        return;
    }
}


function showStatsModal() {
    document.getElementById('statsModal').classList.remove('hidden');
    updateStatsModal();
}

function hideStatsModal() {
    document.getElementById('statsModal').classList.add('hidden');
}

function showSettingsModal() {
    currentSettingsPane = 'study';
    showSettingsModalWithTab('study');
}

// Where the settings header's ‹ goes. Sub-pages go back to the Settings list;
// a caller that opened settings from somewhere else (Study options mid-set)
// passes onBack so the page can go back there instead of only closing.
let settingsBackHandler = null;
let currentSettingsTab = 'study';
// Which of the Settings page's three tabs shows. Kept while a detail page is
// open, so its ‹ lands back on the tab it was opened from.
let currentSettingsPane = 'study';
// Words & data is part of the Your words tab now; 'vocabulary' still names it.
const SETTINGS_PANE_FOR_TAB = { study: 'study', review: 'study', appearance: 'app', lookup: 'words', vocabulary: 'words' };
const SETTINGS_PANE_FOR_DETAIL = { account: 'app', about: 'app', appData: 'app', offline: 'app' };

function showSettingsPane(pane) {
    const content = document.getElementById('studyTabContent');
    if (!content) return;
    currentSettingsPane = pane;
    content.querySelectorAll('.settings-pane-tab').forEach(tab => {
        const on = tab.dataset.settingsPane === pane;
        tab.classList.toggle('selected', on);
        tab.setAttribute('aria-selected', String(on));
        tab.tabIndex = on ? 0 : -1;
    });
    content.querySelectorAll('.settings-pane').forEach(section =>
        section.classList.toggle('is-active', section.dataset.settingsPane === pane));
}

function showSettingsModalWithTab(tabName, { singleTab = false, onBack = null } = {}) {
    setupSettingsOverview();
    // Show/hide refresh set option based on whether a study set is loaded and user is logged in
    const refreshSetToggle = document.getElementById('refreshSetToggle');
    if (currentUser && !currentUser.isGuest && flashcards.length > 0) {
        refreshSetToggle.style.display = 'flex';
    } else {
        refreshSetToggle.style.display = 'none';
    }

    // Sensitivity only applies while cognates are being excluded on a
    // language that has cognate-score data; reflects the live threshold too.
    updateCognateSensitivityVisibility();

    // Update account tab with current user
    window.renderAccountPanel?.();
    // Spotify's controls live in a sizeable module that normal Speech-mode
    // startup never loads (see main.js). The settings panel is the one place
    // a Speech-mode learner can still connect ahead of switching to Lyrics,
    // so load it here on demand instead — a repeat import of the same
    // versioned URL just resolves to the already-loaded module.
    if (window.refreshSpotifyConnectionUI) {
        window.refreshSpotifyConnectionUI();
    } else {
        import('./spotify.js?v=3e821184')
            .then(() => window.refreshSpotifyConnectionUI?.())
            .catch(error => console.warn('Spotify controls deferred:', error));
    }
    const isJstAccount = Boolean(window.isAuditAccount?.());
    const storageTabBtn = document.getElementById('storageTabBtn');
    const appDataTabBtn = document.getElementById('appDataTabBtn');
    const adminLabel = document.getElementById('settingsAdminLabel');
    if (storageTabBtn) storageTabBtn.hidden = !isJstAccount;
    if (appDataTabBtn) appDataTabBtn.hidden = !isJstAccount;
    if (adminLabel) adminLabel.hidden = !isJstAccount;
    document.getElementById('settingsAdminBtn').hidden = !isJstAccount;
    window.renderSavedWords?.();
    const canImport = Boolean(currentUser && !currentUser.isGuest);
    for (const id of ['settingsImportKnownBtn']) {
        const button = document.getElementById(id);
        if (button) button.disabled = !canImport;
    }
    const importNote = document.getElementById('settingsImportNote');
    if (importNote) importNote.textContent = canImport ? ''
        : 'Sign in to import known words.';

    // Show/hide clear level estimate row
    const estimate = levelEstimates[selectedLanguage] || 0;
    const clearRow = document.getElementById('clearLevelEstimateRow');
    if (currentUser && !currentUser.isGuest && estimate > 0) {
        document.getElementById('levelEstimateDisplay').textContent = `~${estimate} words`;
        clearRow.style.display = 'flex';
    } else {
        clearRow.style.display = 'none';
    }

    // Switch to the requested settings surface. Storage and app data are
    // operational audits and must never be exposed outside the JST account.
    const settingsModal = document.getElementById('settingsModal');
    const tabContentIds = {
        account: 'accountTabContent',
        study: 'studyTabContent',
        lookup: 'lookupTabContent',
        review: 'reviewTabContent',
        vocabulary: 'vocabularyTabContent',
        appearance: 'appearanceTabContent',
        offline: 'offlineTabContent',
        about: 'aboutTabContent',
        appData: 'appDataTabContent'
    };
    const adminOnlyTabs = new Set(['offline', 'appData']);
    const requestedTab = tabContentIds[tabName] && (!adminOnlyTabs.has(tabName) || isJstAccount)
        ? ({ lookup: 'study', review: 'study', appearance: 'study', vocabulary: 'study' }[tabName] || tabName)
        : 'study';
    settingsModal.classList.toggle('settings-single-tab', requestedTab === 'study');
    // Opened from a study session: only the study controls, not the whole
    // settings page with account, theme and word tools.
    const studyOnly = singleTab && requestedTab === 'study';
    settingsModal.classList.toggle('settings-study-only', studyOnly);
    if (requestedTab === 'study') {
        showSettingsPane(studyOnly ? 'study' : (SETTINGS_PANE_FOR_TAB[tabName] && tabName !== 'study'
            ? SETTINGS_PANE_FOR_TAB[tabName] : currentSettingsPane));
    } else if (SETTINGS_PANE_FOR_DETAIL[requestedTab]) {
        currentSettingsPane = SETTINGS_PANE_FOR_DETAIL[requestedTab];
    }
    settingsModal.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    settingsModal.querySelector(`.settings-tab[data-tab="${requestedTab}"]`)?.classList.add('active');
    settingsModal.querySelectorAll('.settings-tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(tabContentIds[requestedTab]).classList.add('active');
    const title = studyOnly ? 'Study settings' : ({ study: 'Settings', vocabulary: 'Words & data', account: 'Account',
        offline: 'Storage', appData: 'Owner tools', about: 'About this app' }[requestedTab] || 'Settings');
    document.getElementById('settingsTitle').textContent = title;
    settingsBackHandler = requestedTab === 'study' && typeof onBack === 'function' ? onBack : null;
    currentSettingsTab = requestedTab;
    const settingsBackBtn = document.getElementById('settingsBackBtn');
    settingsBackBtn.hidden = requestedTab === 'study' && !settingsBackHandler;
    settingsBackBtn.setAttribute('aria-label', settingsBackHandler ? 'Back' : 'Back to Settings');
    settingsModal.querySelector('.settings-modal-content').scrollTop = 0;
    syncStudyPreferenceControls();
    window.refreshBridge?.();

    // Data-freshness footer: newest Last-Modified across the vocab files
    // (set in vocab.js trackDataFreshness). An old date = the service
    // worker served cached data; "not loaded yet" = no deck fetched.
    // This entire audit surface is JST-only: newest data freshness, per-file
    // dates, app version, and recent development changelog entries.
    const freshnessEl = document.getElementById('dataFreshnessFooter');
    if (freshnessEl && isJstAccount) {
        if (window._vocabDataLastModified) {
            const upd = new Date(window._vocabDataLastModified).toLocaleString(undefined,
                { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
            const loaded = window._vocabDataLoadedAt
                ? new Date(window._vocabDataLoadedAt).toLocaleTimeString(undefined,
                    { hour: '2-digit', minute: '2-digit' })
                : null;
            freshnessEl.textContent = `Data last refreshed ${upd}` +
                (loaded ? ` · fetched ${loaded}` : '');
        } else {
            freshnessEl.textContent = 'Data not loaded yet';
        }
        renderDevFooter(freshnessEl);   // async, appends below basic line
    }

    settingsModal.classList.remove('hidden');
}

function setupSettingsOverview() {
    const modal = document.getElementById('settingsModal');
    if (!modal || modal.dataset.overviewReady === 'true') return;
    modal.dataset.overviewReady = 'true';
    const go = (id, tab) => document.getElementById(id)?.addEventListener('click', () => showSettingsModalWithTab(tab));
    document.getElementById('settingsBackBtn')?.addEventListener('click', () => {
        const back = settingsBackHandler;
        if (!back) {
            showSettingsModalWithTab('study');
            return;
        }
        hideSettingsModal();
        back();
    });
    const paneTabs = Array.from(modal.querySelectorAll('.settings-pane-tab'));
    paneTabs.forEach((tab, index) => {
        tab.addEventListener('click', () => {
            showSettingsPane(tab.dataset.settingsPane);
            modal.querySelector('.settings-modal-content').scrollTop = 0;
        });
        tab.addEventListener('keydown', event => {
            const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
            if (!step) return;
            event.preventDefault();
            const next = paneTabs[(index + step + paneTabs.length) % paneTabs.length];
            next.click();
            next.focus();
        });
    });
    document.getElementById('settingsSrsInfoBtn')?.addEventListener('click', event => {
        event.stopPropagation();
        window.openSpacedRepetitionInfo?.({ fromSettings: true });
    });
    go('settingsAccountBtn', 'account');
    go('settingsAdminBtn', 'appData');
    // About opens in its own tab, leaving Settings as it was.
    document.getElementById('settingsAboutBtn')?.addEventListener('click', () => window.openAboutPage?.());
    const runImport = () => {
        if (!currentUser || currentUser.isGuest) return;
        window.openVocabularyImportModal?.();
    };
    const runExport = statusId => window.exportMistakes?.(statusId);
    document.getElementById('settingsImportKnownBtn')?.addEventListener('click', runImport);
    document.getElementById('settingsExportMistakesBtn')?.addEventListener('click', () => runExport('settingsDataActionStatus'));
}

window.addEventListener('fast-track-preference-change', event => {
    if (event.detail?.language !== selectedLanguage) return;
    syncStudyPreferenceControls();
    if (event.detail?.source !== 'remote') return;
    const setupPanel = document.getElementById('setupPanel');
    if (setupPanel && !setupPanel.classList.contains('hidden')) {
        applyGlobalStudyDefaults();
        refreshAfterGlobalStudyDefaultChange().catch(error => console.warn('Fast Track refresh failed', error));
    }
});

function escapeDevText(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Verbose data-provenance block for the JST (dev) account only:
// Top hero card shows the most recent deploy with exact date/time, authoring LLM agent,
// human summary in normal text font, and active SW cache.
// Below that: per-file Last-Modified dates, running asset version, and previous changelog entries.
async function renderDevFooter(freshnessEl) {
    const heroEl = document.getElementById('devLatestDeployHero');
    let devEl = document.getElementById('devFooterDetail');
    if (!devEl) {
        devEl = document.createElement('div');
        devEl.id = 'devFooterDetail';
        devEl.className = 'dev-footer-detail';
        freshnessEl.insertAdjacentElement('afterend', devEl);
    }

    const fmt = t => new Date(t).toLocaleString(undefined,
        { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    const lines = [];

    // Service-worker cache name — lets you see if the SW has picked up
    // the latest deploy or is still serving a stale shell.
    let swCache = null;
    try {
        const cacheNames = await caches.keys();
        swCache = cacheNames.find(n => n.startsWith('flashcards-v')) || null;
    } catch (_) {}

    // Running asset version, from the modulepreload tags (single source of
    // truth is service-worker.js ASSET_VERSION; the tags mirror it).
    const pre = document.querySelector('link[rel="modulepreload"]');
    const vMatch = pre && pre.href.match(/[?&]v=([\w.-]+)/);
    const appVersion = vMatch ? vMatch[1] : null;

    // Latest changelog entries.
    let entries = [];
    try {
        if (!window._devChangelog) {
            const resp = await fetch('config/dev_changelog.json');
            if (resp.ok) window._devChangelog = await resp.json();
        }
        entries = (window._devChangelog && window._devChangelog.entries) || [];
    } catch (e) { /* changelog missing is fine — dev-only nicety */ }

    // Render prominent Hero Card at the very top of Developer tab
    if (heroEl && entries.length) {
        const latest = entries[0];
        const agentName = latest.agent || 'Agent';

        let exactDateTime = latest.date || '';
        if (latest.timestamp) {
            try {
                const dt = new Date(latest.timestamp);
                if (!isNaN(dt.getTime())) {
                    exactDateTime = dt.toLocaleString(undefined, {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        timeZoneName: 'short'
                    });
                }
            } catch (_) {}
        }

        const bullets = (latest.detail || latest.details || []).map(b =>
            `<li class="dev-deploy-bullet">${escapeDevText(b)}</li>`
        ).join('');

        const commitText = latest.commit && latest.commit !== 'pending'
            ? `commit ${escapeDevText(latest.commit)}`
            : '';

        heroEl.innerHTML = `
            <div class="dev-deploy-card">
                <div class="dev-deploy-top-row">
                    <div class="dev-deploy-meta">
                        <span class="dev-deploy-agent-badge">${escapeDevText(agentName)}</span>
                        <span class="dev-deploy-time">${escapeDevText(exactDateTime)}</span>
                    </div>
                    <div class="dev-deploy-cache-pill" title="Active Service Worker Cache">
                        <span class="dev-status-dot"></span>
                        <span>${escapeDevText(swCache || 'No SW Cache')}</span>
                    </div>
                </div>
                <div class="dev-deploy-summary">${escapeDevText(latest.summary)}</div>
                ${bullets ? `<ul class="dev-deploy-bullets">${bullets}</ul>` : ''}
                <div class="dev-deploy-footer-bar">
                    <div class="dev-deploy-footer-stats">
                        ${appVersion ? `<span>v=${escapeDevText(appVersion)}</span>` : ''}
                        ${commitText ? `<span>${commitText}</span>` : ''}
                    </div>
                    <button type="button" class="dev-deploy-refresh-btn" id="devForceRefreshBtn" title="Check for Service Worker updates and reload">
                        Check cache &amp; reload
                    </button>
                </div>
            </div>
        `;

        const refreshBtn = document.getElementById('devForceRefreshBtn');
        if (refreshBtn) {
            refreshBtn.onclick = async () => {
                refreshBtn.disabled = true;
                refreshBtn.textContent = 'Updating...';
                try {
                    if ('serviceWorker' in navigator) {
                        const reg = await navigator.serviceWorker.getRegistration();
                        if (reg) await reg.update();
                    }
                } catch (_) {}
                window.location.reload();
            };
        }
    }

    // Cognate scorer algorithm details for Developer tab
    const cognateAlgoBadge = document.getElementById('cognateAlgorithmBadge');
    const cognateAlgoExplanation = document.getElementById('cognateAlgorithmExplanation');
    if (cognateAlgoBadge && cognateAlgoExplanation) {
        const info = globalThis.getCognateAlgorithmInfo?.();
        if (info && info.hasScores) {
            const knowns = (info.knownLanguages && info.knownLanguages.length)
                ? info.knownLanguages
                : (globalThis.activeKnownLanguages?.() || ['en']);
            const scorers = knowns.map(code => info.surfaceScorers?.[code] || 'learner-align/v1');
            const uniqueScorers = Array.from(new Set(scorers));
            cognateAlgoBadge.textContent = uniqueScorers.join(', ');

            const cuts = knowns.map(code => {
                const s = info.surfaceScorers?.[code] || 'learner-align/v1';
                const t = info.thresholds?.[code] ?? globalThis.cognateThresholdFor?.(code) ?? '–';
                return `${code.toUpperCase()}: ${s} (threshold: ${t})`;
            }).join(' · ');
            cognateAlgoExplanation.textContent = `${cuts} · schema: ${info.schema || 'cognate-score/v4'}`;
        } else {
            cognateAlgoBadge.textContent = 'None / Inactive';
            cognateAlgoExplanation.textContent = 'No cognate scores loaded for the active language/release.';
        }
    }

    // Per-file freshness (which file is stale, not just the newest).
    const perFile = window._vocabDataFreshness || {};
    const fileNames = Object.keys(perFile).sort((a, b) => perFile[b] - perFile[a]);
    if (fileNames.length) {
        lines.push('<div class="dev-footer-label">Loaded data files (Last-Modified)</div>');
        for (const f of fileNames.slice(0, 6)) {
            lines.push(`<div class="dev-footer-row"><span>${f}</span><span>${fmt(perFile[f])}</span></div>`);
        }
    }

    if (appVersion) {
        lines.push(`<div class="dev-footer-row"><span>app version</span><span>${appVersion}</span></div>`);
    }

    // Previous changes
    const pastEntries = entries.slice(1, 5);
    if (pastEntries.length) {
        lines.push('<div class="dev-footer-label">Previous app/data changes</div>');
        for (const e of pastEntries) {
            const author = e.agent ? `[${escapeDevText(e.agent)}] ` : '';
            lines.push(`<div class="dev-footer-entry"><b>${escapeDevText(e.date)}</b> · ${author}${escapeDevText(e.summary)}` +
                (e.commit ? ` <span class="dev-footer-commit">(${escapeDevText(e.commit)})</span>` : '') + '</div>');
            for (const d of (e.detail || e.details || []).slice(0, 3)) {
                lines.push(`<div class="dev-footer-bullet">– ${escapeDevText(d)}</div>`);
            }
        }
    }

    if (swCache) {
        lines.push(`<div class="dev-footer-row"><span>SW cache</span><span>${swCache}</span></div>`);
    }

    devEl.innerHTML = lines.join('');
}

async function checkAndShowAdminUpdateModal() {
    if (!window.isAuditAccount?.()) return;

    let entries = [];
    try {
        if (!window._devChangelog) {
            const resp = await fetch('config/dev_changelog.json');
            if (resp.ok) window._devChangelog = await resp.json();
        }
        entries = (window._devChangelog && window._devChangelog.entries) || [];
    } catch (_) { return; }

    if (!entries.length) return;
    const latest = entries[0];
    const updateKey = latest.timestamp || latest.date || '';

    const isPendingFromUpdate = sessionStorage.getItem('fluency_admin_update_pending') === 'true';
    const lastSeenUpdate = localStorage.getItem('fluency_last_seen_dev_update');

    if (!isPendingFromUpdate && lastSeenUpdate === updateKey) {
        return;
    }

    sessionStorage.removeItem('fluency_admin_update_pending');
    localStorage.setItem('fluency_last_seen_dev_update', updateKey);

    const modal = document.getElementById('adminUpdateModal');
    const bodyEl = document.getElementById('adminUpdateModalBody');
    const cacheText = document.getElementById('adminUpdateCacheText');
    if (!modal || !bodyEl) return;

    let swCache = null;
    try {
        const cacheNames = await caches.keys();
        swCache = cacheNames.find(n => n.startsWith('flashcards-v')) || null;
    } catch (_) {}

    if (cacheText) {
        cacheText.textContent = swCache || latest.cache || 'Active Cache';
    }

    const agentName = latest.agent || 'Agent';
    let exactDateTime = latest.date || '';
    if (latest.timestamp) {
        try {
            const dt = new Date(latest.timestamp);
            if (!isNaN(dt.getTime())) {
                exactDateTime = dt.toLocaleString(undefined, {
                    weekday: 'short',
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    timeZoneName: 'short'
                });
            }
        } catch (_) {}
    }

    const bullets = (latest.detail || latest.details || []).map(b =>
        `<li class="dev-deploy-bullet">${escapeDevText(b)}</li>`
    ).join('');

    const commitText = latest.commit && latest.commit !== 'pending'
        ? `commit ${escapeDevText(latest.commit)}`
        : '';

    bodyEl.innerHTML = `
        <div class="dev-deploy-card">
            <div class="dev-deploy-top-row">
                <div class="dev-deploy-meta">
                    <span class="dev-deploy-agent-badge">${escapeDevText(agentName)}</span>
                    <span class="dev-deploy-time">${escapeDevText(exactDateTime)}</span>
                </div>
            </div>
            <div class="dev-deploy-summary">${escapeDevText(latest.summary)}</div>
            ${bullets ? `<ul class="dev-deploy-bullets">${bullets}</ul>` : ''}
            ${commitText ? `
            <div class="dev-deploy-footer-bar">
                <div class="dev-deploy-footer-stats">
                    <span>${commitText}</span>
                </div>
            </div>` : ''}
        </div>
    `;

    modal.classList.remove('hidden');

    const closeBtn = document.getElementById('closeAdminUpdateModal');
    const dismissBtn = document.getElementById('dismissAdminUpdateBtn');
    const hide = () => modal.classList.add('hidden');
    if (closeBtn) closeBtn.onclick = hide;
    if (dismissBtn) dismissBtn.onclick = hide;
    modal.onclick = (e) => { if (e.target === modal) hide(); };
}

window.checkAndShowAdminUpdateModal = checkAndShowAdminUpdateModal;


function hideSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.classList.add('hidden');
    settingsBackHandler = null;
    const search = document.getElementById('settingsSearch');
    if (search?.value) {
        search.value = '';
        search.dispatchEvent(new Event('input'));
    }
}

async function showTotalStatsModal() {
    const language = selectedLanguage;
    const artist = activeArtist;
    const scope = artistVocabularyScope;
    const user = currentUser;
    const langConfig = config.languages?.[language];
    const mode = currentLearningMode();
    const smartSkipOn = Boolean(window.isFastTrackOn?.());
    const options = {
        flag: langConfig?.flag || LEARNING_CONTEXT_FLAGS[language] || '',
        identity: artist ? {
            image: artist.pickerImage || artist.image || artist.defaultAlbumArt || '',
            fallback: artist.customSongSource ? '♫' : learningContextInitials(artist.name)
        } : null,
        contentNoun: mode === 'series' ? 'this series' : mode === 'speech' ? 'everyday speech' : mode === 'live' ? 'your playlist' : 'lyrics',
        smartSkipOn,
        source: artist?.name || langConfig?.name || language,
        mode: mode === 'series' ? 'TV Series' : mode === 'speech' ? 'Speech' : mode === 'live' ? 'Your playlist' : 'Music',
        coverageLabel: mode === 'series' ? 'Estimated series coverage' : mode === 'live' ? 'Estimated playlist coverage' : artist ? (scope === 'extra' ? 'Extra vocabulary explored' : 'Estimated lyrics coverage') : 'Estimated speech coverage',
        isCurrent: () => selectedLanguage === language && activeArtist === artist && artistVocabularyScope === scope && currentLearningMode() === mode && currentUser === user,
        loadVocabulary: async () => {
            if (!langConfig || !mode) throw new Error('Choose a vocabulary source first.');
            const raw = await fetchActiveVocabularyData(langConfig);
            if (selectedLanguage !== language || activeArtist !== artist || artistVocabularyScope !== scope) return [];
            const prepared = getPreparedSetupVocabulary(language, raw);
            options.skippedCount = smartSkipOn
                ? Math.max(0, (prepared.stableBaseline?.length || 0) - prepared.vocab.length) : 0;
            return prepared.vocab;
        },
        getId: item => getWordId(item),
        getState: item => getRecordedSetupState(item),
        getProgress: item => getMergedWordProgress(getWordId(item), item.word),
        skippedCount: 0
    };
    return openProgressOverview(options);
}

function hideTotalStatsModal() {
    closeProgressOverview();
}

function updateTotalStatsButtonVisibility() {
    // No longer needed - stats are in settings modal
}

function updateStatsModal() {
    const labelEl = document.getElementById('statsSetLabel');
    if (labelEl) labelEl.textContent = stats.setLabel ? `· ${stats.setLabel}` : '';
    renderActiveSetProgress();
}

function formatStudyProgressTimestamp(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat('en-GB', {
        day: '2-digit', month: '2-digit', year: '2-digit',
        hour: '2-digit', minute: '2-digit', hour12: false
    }).format(date).replace(',', '');
}

function getActiveSetCardResult(inDeckIdx, session) {
    const correct = Number(session?.correct || 0);
    const incorrect = Number(session?.incorrect || 0);
    const attempts = Array.isArray(session?.attempts) ? session.attempts : [];
    if (correct > 0 && incorrect > 0) {
        const latest = attempts.at(-1)?.result;
        return { key: 'mixed', label: latest === 'incorrect' ? 'Mixed · latest incorrect' : 'Mixed · latest correct' };
    }
    if (correct > 0) return { key: 'correct', label: 'Correct' };
    if (incorrect > 0) return { key: 'incorrect', label: 'Incorrect' };
    if (inDeckIdx === -1) return { key: 'known', label: 'Already seen' };
    if (inDeckIdx === currentIndex) return { key: 'current', label: 'Current' };
    if (stats.studied?.has?.(inDeckIdx)) return { key: 'skipped', label: 'Skipped' };
    return { key: 'unanswered', label: 'Not answered' };
}

function _studyProgressEl(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
}

function _appendStudyProgressDatum(host, label, value, valueClass = '') {
    const row = _studyProgressEl('div', 'active-set-history-row');
    row.append(
        _studyProgressEl('span', 'active-set-history-label', label),
        _studyProgressEl('span', `active-set-history-value ${valueClass}`.trim(), value)
    );
    host.appendChild(row);
}

function _appendSavedProgressRecord(host, label, record) {
    const card = _studyProgressEl('div', 'active-set-saved-record');
    card.appendChild(_studyProgressEl('strong', 'active-set-saved-record-title', label));
    _appendStudyProgressDatum(card, 'Answers', `${Number(record.correct || 0)} correct · ${Number(record.wrong || 0)} wrong`);
    _appendStudyProgressDatum(card, 'Latest correct', formatStudyProgressTimestamp(record.lastCorrect), 'active-set-history-time');
    _appendStudyProgressDatum(card, 'Latest incorrect', formatStudyProgressTimestamp(record.lastWrong), 'active-set-history-time');
    _appendStudyProgressDatum(card, 'Latest seen', formatStudyProgressTimestamp(record.lastSeen), 'active-set-history-time');
    _appendStudyProgressDatum(card, 'SRS stage', String(Number(record.srsStage || 0)));
    host.appendChild(card);
}

function renderActiveSetProgress() {
    const host = document.getElementById('activeSetProgressList');
    if (!host) return;
    host.innerHTML = '';

    const words = stats.allWords || [];
    if (words.length === 0) {
        host.appendChild(_studyProgressEl('p', 'active-set-progress-empty', 'No cards are loaded in this session.'));
        return;
    }

    // A picked Learn New set includes both its active cards and cards removed
    // because they are already complete. Keep both visible here so this panel
    // can answer “have I done this card before?” without hiding the evidence.
    const activeIdToIndex = new Map();
    flashcards.forEach((c, i) => {
        if (c && c.id) activeIdToIndex.set(c.id, i);
        if (c && c.fullId) activeIdToIndex.set(c.fullId, i);
    });

    words.forEach((w, position) => {
        const fullId = getWordId(w);
        const inDeckIdx = activeIdToIndex.has(w.id) ? activeIdToIndex.get(w.id) : -1;
        const session = inDeckIdx >= 0 ? (stats.cardStats || {})[inDeckIdx] : null;
        const result = getActiveSetCardResult(inDeckIdx, session);
        const details = _studyProgressEl('details', `active-set-card-progress is-${result.key}`);
        details.dataset.cardId = fullId;
        if (inDeckIdx === currentIndex) details.open = true;

        const summary = _studyProgressEl('summary', 'active-set-card-summary');
        summary.appendChild(_studyProgressEl('span', 'active-set-card-number', String(position + 1)));
        const identity = _studyProgressEl('span', 'active-set-card-identity');
        identity.appendChild(_studyProgressEl('strong', 'active-set-card-word', w.word || '(untitled card)'));
        if (w.translation) identity.appendChild(_studyProgressEl('small', 'active-set-card-translation', w.translation));
        summary.append(identity, _studyProgressEl('span', `active-set-card-result is-${result.key}`, result.label));
        details.appendChild(summary);

        const body = _studyProgressEl('div', 'active-set-card-history');
        const sessionSection = _studyProgressEl('section', 'active-set-history-section');
        sessionSection.appendChild(_studyProgressEl('h4', '', 'This session'));
        const attempts = Array.isArray(session?.attempts) ? session.attempts : [];
        if (attempts.length) {
            attempts.forEach((attempt, index) => {
                const label = attempt.result === 'correct' ? 'Correct' : 'Incorrect';
                _appendStudyProgressDatum(sessionSection, `Attempt ${index + 1} · ${label}`, formatStudyProgressTimestamp(attempt.at), 'active-set-history-time');
            });
        } else {
            sessionSection.appendChild(_studyProgressEl('p', 'active-set-history-empty', 'No answer recorded in this session.'));
        }
        body.appendChild(sessionSection);

        const modeIds = [{ id: fullId, label: activeArtist ? 'Music card' : 'Speech card' }];
        const crossModeId = getCrossModeId(fullId);
        if (crossModeId) modeIds.push({ id: crossModeId, label: activeArtist ? 'Speech card' : 'Music card' });
        const savedRecords = getProgressRecordsForCard(fullId, w.word).map(({ id, progress }) => ({
            id,
            progress,
            label: id[2] === '1' ? 'Music card' : 'Speech card'
        }));
        const savedSection = _studyProgressEl('section', 'active-set-history-section');
        savedSection.appendChild(_studyProgressEl('h4', '', 'Saved card progress'));
        if (savedRecords.length) {
            savedRecords.forEach(({ label, progress }) => _appendSavedProgressRecord(savedSection, label, progress));
        } else {
            savedSection.appendChild(_studyProgressEl('p', 'active-set-history-empty', 'No saved card history yet.'));
        }
        body.appendChild(savedSection);

        const parentIds = new Set([
            ...modeIds.map(({ id }) => id),
            ...savedRecords.map(({ id }) => id)
        ]);
        const savedItems = Object.values(itemProgressData || {})
            .filter(item => parentIds.has(item?.parentWordId))
            .sort((a, b) => String(a.label || '').localeCompare(String(b.label || '')));
        if (savedItems.length) {
            const itemSection = _studyProgressEl('section', 'active-set-history-section');
            itemSection.appendChild(_studyProgressEl('h4', '', 'Saved sense and expression progress'));
            savedItems.forEach(item => {
                const type = item.itemType === 'mwe' || item.itemType === 'expression' ? 'Expression' : 'Sense';
                _appendSavedProgressRecord(itemSection, `${type} · ${item.label || 'Unnamed'}`, item);
            });
            body.appendChild(itemSection);
        }

        body.appendChild(_studyProgressEl(
            'p',
            'active-set-history-retention',
            'Progress keeps cumulative totals and the latest correct, incorrect, and seen times—not a timestamp for every older answer.'
        ));
        details.appendChild(body);
        host.appendChild(details);
    });
}


window.setupTooltipHandlers = setupTooltipHandlers;
window.updateIncorrectButtonVisibility = updateIncorrectButtonVisibility;
window.renderLanguageTabs = renderLanguageTabs;
window.setActiveSetupStep = setActiveSetupStep;
window.mergeStandardProgressIntoLanguageStep = mergeStandardProgressIntoLanguageStep;
window.setupLanguageTabs = setupLanguageTabs;
window.hideAllSelectionPills = hideAllSelectionPills;
window.updatePercentModeButton = updatePercentModeButton;
window.updateStep2Tooltip = updateStep2Tooltip;
window.updateStep5Tooltip = updateStep5Tooltip;
window.renderLevelSelector = renderLevelSelector;
window.refreshSetupAfterProgress = async function() {
    if (_setupLevelSelectionWasManual) return renderRangeSelector();
    return renderLevelSelector(selectedLanguage, { preferActionable: true });
};
window.setupCognateToggle = setupCognateToggle;
// Open the help modal — always reset to About tab, update content for mode
function openHelpModal() {
    const modal = document.getElementById('helpModal');
    modal.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    modal.querySelectorAll('.settings-tab-content').forEach(c => c.classList.remove('active'));
    const aboutTab = modal.querySelector('[data-tab="helpAbout"]');
    if (aboutTab) aboutTab.classList.add('active');
    const aboutContent = document.getElementById('helpAboutTabContent');
    if (aboutContent) {
        aboutContent.classList.add('active');
        const helpContent = aboutContent.querySelector('.help-content');
        if (helpContent) helpContent.innerHTML = activeArtist ? getArtistHelpContent() : getNormalHelpContent();
    }
    // Show/hide the lyrics-specific line in the study tab
    const lyricsLine = document.getElementById('helpStudyLyricsLine');
    if (lyricsLine) lyricsLine.style.display = activeArtist ? '' : 'none';
    modal.classList.remove('hidden');
}

function get70pctWordCount() {
    const ranges = getPercentageLevelRanges();
    const level70 = ranges.find(r => r.level === '70%');
    if (level70) {
        return `With only ${level70.endRank.toLocaleString()} words, you know enough to understand roughly 70% of the words in any song. That's what's meant by 70% coverage.`;
    }
    return `For example, at 70% coverage you know enough words to understand roughly 70% of the words in any song. That's what's meant by 70% coverage.`;
}

function getArtistHelpContent() {
    const language = config.languages[activeArtist.language || selectedLanguage]?.name || 'your language';
    const name = _escapeHtml(activeArtist.name || 'your selected songs');
    return `
        <p><strong>What is this?</strong></p>
        <p><strong>Music</strong> teaches ${_escapeHtml(language)} vocabulary from ${name}'s selected songs, starting with the most frequent words.</p>
        <p><strong>Why frequency order?</strong></p>
        <p>Learning common words first helps you understand more of your selected lyrics sooner. Changing your songs changes the vocabulary and its order.</p>
        <p><strong>How does it work?</strong></p>
        ${getSharedStudyHelpContent()}
        <p>Each card uses real song lines, with song credits and Spotify playback where available. Song Lines counts lines containing the word; tap the figure for details.</p>
        <p><strong>Smart Skip</strong> combines related forms and can skip familiar words. Its word browser also includes supplementary song vocabulary, such as loanwords, names and fillers. You can search, preview and study these words at any time.</p>
        <p>Estimated lyrics coverage measures words you recognise in your selected songs, weighted by how often they occur. It does not measure comprehension of every song.</p>
    `;
}

function getSharedStudyHelpContent() {
    return `<p>Choose a level, then Go starts new cards for as long as you choose: 5 minutes, 10 minutes or no limit. The level bar shows New, Practice, Known, Estimated and Skipped words. When a level has few or no new words left, Go explains what to do next.</p>
        <p>Practise collects incorrect, partly learned and due cards across the language, and says when the next ones come back. It runs for the same length you chose for Go. Spaced repetition in Study settings schedules future practice.</p>
        <p>Smart Skip changes which cards you study while keeping the level boundaries stable. An unfinished session can be restored from the Welcome back prompt, with its card order and settings.</p>`;
}

function getNormalHelpContent() {
    return `
        <p><strong>What is this?</strong></p>
        <p><strong>Speech</strong> teaches vocabulary from film and TV dialogue, ordered by how frequently each word occurs.</p>
        <p><strong>Why frequency order?</strong></p>
        <p>A small number of common words make up a large share of everyday speech. Learning these first builds practical comprehension faster.</p>
        <p><strong>How does it work?</strong></p>
        ${getSharedStudyHelpContent()}
        <p>Choose Speech or Music in learning settings at any time. Music lets you choose artists and songs; Speech uses your language's frequency-ranked deck.</p>
        <p>Estimated speech coverage measures words you recognise, weighted by frequency. Tap a card's Frequency figure for its source and any combined forms.</p>
    `;
}

// Generic tab switching for any modal that uses .settings-tab / .settings-tab-content pattern
function setupTabSwitching(modalEl) {
    const tabs = modalEl.querySelectorAll('.settings-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Deactivate all tabs and contents within this modal
            modalEl.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
            modalEl.querySelectorAll('.settings-tab-content').forEach(c => c.classList.remove('active'));
            // Activate clicked tab
            tab.classList.add('active');
            const tabName = tab.dataset.tab;
            const contentId = tabName + 'TabContent';
            const content = document.getElementById(contentId);
            if (content) content.classList.add('active');
        });
    });
}

function setupSettingsSearch() {
    const modal = document.getElementById('settingsModal');
    const input = document.getElementById('settingsSearch');
    if (!modal || !input || input.dataset.ready === 'true') return;
    input.dataset.ready = 'true';
    input.addEventListener('input', () => {
        const query = input.value.trim().toLocaleLowerCase();
        const tabs = Array.from(modal.querySelectorAll('.settings-tab'));
        let firstMatch = null;
        tabs.forEach(tab => {
            const content = document.getElementById(`${tab.dataset.tab}TabContent`);
            const matches = !query || `${tab.textContent} ${content?.textContent || ''}`
                .toLocaleLowerCase().includes(query);
            tab.classList.toggle('settings-search-hidden', !matches);
            if (matches && !tab.hidden && !firstMatch) firstMatch = tab;
        });
        const active = modal.querySelector('.settings-tab.active');
        if (query && active?.classList.contains('settings-search-hidden') && firstMatch) {
            showSettingsModalWithTab(firstMatch.dataset.tab);
            input.focus();
        }
    });
}

window.openHelpModal = openHelpModal;
window.setupTabSwitching = setupTabSwitching;
window.setupSettingsSearch = setupSettingsSearch;
window.setupLemmaToggle = setupLemmaToggle;
window.setupGlobalStudyDefaults = setupGlobalStudyDefaults;
window.setupPercentModeButton = setupPercentModeButton;
window.setupEstimationModal = setupEstimationModal;
window.updateLemmaToggleVisibility = updateLemmaToggleVisibility;
window.updateCognateToggleVisibility = updateCognateToggleVisibility;
window.applyLanguageColorTheme = applyLanguageColorTheme;
window.renderRangeSelector = renderRangeSelector;
window.getNextStudySetMeta = getNextStudySetMeta;
window.getNextStudyLevelMeta = getNextStudyLevelMeta;
window.startNextStudyLevelFirstSet = startNextStudyLevelFirstSet;
// A panel opened from Settings (Saved words, Import) gets a ‹ in its header
// that returns to the settings page it came from, so a sub-page never offers
// only a way out. Returns the reopen function, or null when settings was not
// open, and clears the button in that case.
function attachSettingsReturn(modalId, closePanel) {
    const settingsModal = document.getElementById('settingsModal');
    const fromSettings = Boolean(settingsModal && !settingsModal.classList.contains('hidden'));
    const header = document.querySelector(`#${modalId} .modal-header`);
    if (!header) return null;
    let button = header.querySelector('.settings-return-back');
    if (!button) {
        button = document.createElement('button');
        button.type = 'button';
        button.className = 'settings-return-back';
        button.setAttribute('aria-label', 'Back to Settings');
        button.textContent = '‹';
        button.addEventListener('click', () => button._back?.());
        header.prepend(button);
    }
    const tab = currentSettingsTab;
    const reopen = fromSettings ? () => showSettingsModalWithTab(tab) : null;
    button._back = reopen ? () => { closePanel(); reopen(); } : null;
    button.hidden = !reopen;
    return reopen;
}

window.attachSettingsReturn = attachSettingsReturn;
window.showStatsModal = showStatsModal;
window.hideStatsModal = hideStatsModal;
window.showSettingsModal = showSettingsModal;
window.showSettingsModalWithTab = showSettingsModalWithTab;
window.applyGlobalStudyDefaults = applyGlobalStudyDefaults;
window.saveGlobalStudyPreference = saveGlobalStudyPreference;
window.hideSettingsModal = hideSettingsModal;
window.showTotalStatsModal = showTotalStatsModal;
window.hideTotalStatsModal = hideTotalStatsModal;
window.updateTotalStatsButtonVisibility = updateTotalStatsButtonVisibility;
window.updateStatsModal = updateStatsModal;
window.renderSetupExtrasSection = renderSetupExtrasSection;
window.startDailyReview = startDailyReview;
window.renderFastTrackSkippedDecks = renderFastTrackSkippedDecks;
window.getActiveLevelRanges = getActiveLevelRanges;
window.showDeckOverviewLoading = showDeckOverviewLoading;
