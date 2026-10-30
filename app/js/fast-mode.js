// Fast mode — one decision on the setup screen, the parts behind it on a page
// of their own.
//
// Step 2 used to present Merge Lemmas and Cognates as two toggle pairs sitting
// under the level picker. Both are real choices, but neither is one a learner
// can make before they have seen a card, and together they made the landing
// screen read like a settings panel. They now sum to a single question — do you
// want fewer cards for the same coverage? — with the individual controls, their
// counts, and the explanation on the Fast mode page.
//
// This module owns only that summing. The individual toggles keep their own
// handlers in ui.js: turning fast mode on CLICKS them rather than setting the
// state directly, so there is one implementation of what changing each setting
// means and no second copy to drift.
//
// Applies to Speech and Lyrics alike. A language whose release supports only one
// of the two parts still gets fast mode — it just moves the part it has, and the
// page says which part is missing.
import './state.js?v=20260825ak';
import { readFastTrack, saveFastTrack } from './fast-track-preferences.js?v=20260920a';

let applyingMasterSwitch = false;
let returnToSettings = false;
let advancedRefreshTimer = null;
let advancedRefreshVersion = 0;
let levelNoticeTimer = null;
function showSmartSkipLevelNotice(message) {
    dismissSmartSkipActivationAnimation();
    let notice = document.getElementById('smartSkipLevelNotice');
    if (!notice) {
        notice = document.createElement('div');
        notice.id = 'smartSkipLevelNotice';
        notice.className = 'smart-skip-level-notice smart-skip-toast-inner';
        notice.setAttribute('role', 'status');
        document.body.appendChild(notice);
    }
    clearTimeout(levelNoticeTimer);
    notice.textContent = message;
    notice.hidden = false;
    levelNoticeTimer = setTimeout(() => { notice.hidden = true; }, 4500);
}
function refreshAdvancedStudyChoices(advanceFrom = null) {
    clearTimeout(advancedRefreshTimer);
    const version = ++advancedRefreshVersion;
    const language = selectedLanguage;
    const artist = globalThis.activeArtist;
    advancedRefreshTimer = setTimeout(async () => {
        if (version !== advancedRefreshVersion || selectedLanguage !== language || globalThis.activeArtist !== artist) return;
        const setup = document.getElementById('setupPanel');
        if (setup?.classList.contains('hidden')) return;
        try {
            await globalThis.renderLevelSelector?.(language);
            await globalThis.updateExclusionBars?.();
            if (advanceFrom !== null) {
                const isCurrent = () => version === advancedRefreshVersion && currentState() === 'on';
                const message = await globalThis.advanceSmartSkipLevel?.(language, advanceFrom, isCurrent);
                if (message && isCurrent()) showSmartSkipLevelNotice(message);
            }
        } catch (error) {
            console.warn('Could not refresh Smart Skip choices', error);
        }
    }, 0);
}

function lemmaAvailable() {
    return document.getElementById('lemmaToggleContainer')?.dataset.available === 'true';
}

function cognateAvailable() {
    return document.getElementById('cognateToggleContainer')?.dataset.available === 'true';
}

// Read the buttons rather than the state variables: what the learner sees is
// the truth, and this cannot drift from it.
function lemmaOn() {
    return document.querySelector('.lemma-toggle-btn.selected')?.dataset.lemma === 'on';
}

function cognatesExcluded() {
    return document.querySelector('.cognate-toggle-btn.selected')?.dataset.cognate === 'exclude';
}

// The learner's language-wide choice remains visible even if this deck lacks
// one of its optional features.
function currentState() {
    return readFastTrack(selectedLanguage).enabled ? 'on' : 'off';
}

globalThis.isFastTrackOn = () => currentState() === 'on';

function setToggleState(prefix, value) {
    const buttons = document.querySelectorAll(`.${prefix}-toggle-btn`);
    buttons.forEach(btn => {
        const matches = btn.dataset[prefix] === value;
        btn.classList.toggle('selected', matches);
    });
}

// What each shortcut's hidden control says, read from the control itself.
function shortcutOn(kind) {
    const selected = document.querySelector(`.${kind}-toggle-btn.selected`);
    if (!selected) return false;
    return kind === 'lemma' ? selected.dataset.lemma === 'on' : selected.dataset[kind] === 'exclude';
}

let _smartSkipAnimationTimer = null;
let _smartSkipFlashInterval = null;

function dismissSmartSkipActivationAnimation() {
    if (_smartSkipAnimationTimer) clearTimeout(_smartSkipAnimationTimer);
    if (_smartSkipFlashInterval) clearInterval(_smartSkipFlashInterval);
    const toast = document.getElementById('smartSkipAnimationToast');
    if (toast) toast.classList.remove('visible', 'fade-out');
    const backdrop = document.getElementById('smartSkipBackdrop');
    if (backdrop) backdrop.classList.remove('visible', 'fade-out');
}

function triggerSmartSkipActivationAnimation() {
    const extras = globalThis.collectExtras?.() || {};
    const skippedCardsCount = (extras.allSkipped ? extras.allSkipped.length : (extras.cognates?.length || 0))
        + (extras.lemmas?.length || 0);
    const candidates = [...(extras.allSkipped || extras.cognates || []), ...(extras.lemmas || [])]
        .map(entry => entry.item || entry);
    let words = [...new Set(candidates.map(item => String(item?.word || '').trim()).filter(Boolean))].slice(0, 15);
    if (!words.length) {
        const previewCandidates = lookAlikeCandidates();
        words = [...new Set(previewCandidates.map(item => String(item?.word || '').trim()).filter(Boolean))].slice(0, 15);
    }

    let backdrop = document.getElementById('smartSkipBackdrop');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.id = 'smartSkipBackdrop';
        backdrop.className = 'smart-skip-backdrop';
        document.body.appendChild(backdrop);
    }

    let toast = document.getElementById('smartSkipAnimationToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'smartSkipAnimationToast';
        toast.className = 'smart-skip-animation-toast';
        document.body.appendChild(toast);
    }

    if (_smartSkipAnimationTimer) clearTimeout(_smartSkipAnimationTimer);
    if (_smartSkipFlashInterval) clearInterval(_smartSkipFlashInterval);

    const countText = skippedCardsCount > 0 ? `${skippedCardsCount.toLocaleString()}` : '';
    const initialWord = words[0] || '';

    toast.innerHTML = `
        <div class="smart-skip-toast-inner">
            <div class="smart-skip-toast-spinner" aria-hidden="true"></div>
            <div class="smart-skip-toast-content">
                <div class="smart-skip-toast-title">Skipping ${countText ? countText + ' words...' : 'words...'}</div>
                <div class="smart-skip-toast-flasher">
                    <span class="smart-skip-flashed-word" id="smartSkipFlashedWord">${initialWord}</span>
                </div>
            </div>
        </div>
    `;

    backdrop.classList.remove('fade-out');
    backdrop.classList.add('visible');
    toast.classList.remove('fade-out');
    toast.classList.add('visible');

    let wordIdx = 0;
    const wordEl = document.getElementById('smartSkipFlashedWord');
    if (words.length > 1 && wordEl) {
        _smartSkipFlashInterval = setInterval(() => {
            wordIdx = (wordIdx + 1) % words.length;
            wordEl.textContent = words[wordIdx];
            wordEl.classList.remove('word-pop');
            void wordEl.offsetWidth;
            wordEl.classList.add('word-pop');
        }, 220);
    }

    _smartSkipAnimationTimer = setTimeout(() => {
        if (_smartSkipFlashInterval) clearInterval(_smartSkipFlashInterval);
        const spinner = toast.querySelector('.smart-skip-toast-spinner');
        if (spinner) {
            spinner.className = 'smart-skip-toast-check';
            spinner.textContent = '✓';
        }
        const freshExtras = globalThis.collectExtras?.() || {};
        const freshCount = (freshExtras.allSkipped ? freshExtras.allSkipped.length : (freshExtras.cognates?.length || 0))
            + (freshExtras.lemmas?.length || 0);
        const finalCountText = freshCount > 0 ? freshCount.toLocaleString() : countText;
        const titleEl = toast.querySelector('.smart-skip-toast-title');
        if (titleEl) {
            titleEl.textContent = finalCountText ? `${finalCountText} words skipped` : 'Smart Skip active';
        }
        const flasherEl = toast.querySelector('.smart-skip-toast-flasher');
        if (flasherEl) flasherEl.style.opacity = '0.7';

        setTimeout(() => {
            toast.classList.add('fade-out');
            backdrop.classList.add('fade-out');
            setTimeout(() => {
                toast.classList.remove('visible', 'fade-out');
                backdrop.classList.remove('visible', 'fade-out');
            }, 300);
        }, 850);
    }, 1800);
}

// Turning fast mode on or off drives the real controls, so every side effect
// they own — recounting the deck, invalidating the prepared vocabulary,
// re-rendering the level bands — happens exactly once and exactly as it does
// when the learner changes them by hand.
function applyFastMode(on) {
    const advanceFrom = on ? globalThis.selectedLevel ?? null : null;
    const notice = document.getElementById('smartSkipLevelNotice');
    if (notice) notice.hidden = true;
    if (on) triggerSmartSkipActivationAnimation();
    else dismissSmartSkipActivationAnimation();
    const previous = readFastTrack(selectedLanguage);
    const hasChoices = previous.merge || previous.skip || previous.bridge || previous.skipGrammar || previous.skipSlang || previous.skipEntities;
    let merge = hasChoices ? previous.merge : lemmaAvailable();
    let skip = hasChoices ? previous.skip : cognateAvailable();
    let skipGrammar = hasChoices ? (previous.skipGrammar ?? false) : false;
    let skipSlang = previous.skipSlang === true;
    let skipEntities = previous.skipEntities === true;

    if (on && !((merge && lemmaAvailable()) || (skip && cognateAvailable()) || skipGrammar || skipSlang || skipEntities || (previous.bridge && window.bridgeSourceLanguages?.().length))) {
        if (lemmaAvailable()) merge = true;
        else if (cognateAvailable()) skip = true;
        else { showUnavailableMessage('all'); return; }
    }
    applyingMasterSwitch = true;
    if (lemmaAvailable() && lemmaOn() !== (on && merge)) {
        document.querySelector(`.lemma-toggle-btn[data-lemma="${on && merge ? 'on' : 'off'}"]`)?.click();
    }
    if (cognateAvailable() && cognatesExcluded() !== (on && skip)) {
        document.querySelector(
            `.cognate-toggle-btn[data-cognate="${on && skip ? 'exclude' : 'include'}"]`
        )?.click();
    }
    setToggleState('grammar', on && skipGrammar ? 'exclude' : 'include');
    setToggleState('slang', on && skipSlang ? 'exclude' : 'include');
    setToggleState('entity', on && skipEntities ? 'exclude' : 'include');
    globalThis.excludeGrammarParticles = on && skipGrammar;
    globalThis.excludeSlang = on && skipSlang;
    globalThis.excludeProperNouns = on && skipEntities;
    applyingMasterSwitch = false;
    refreshAdvancedStudyChoices(advanceFrom);

    saveFastTrack(selectedLanguage, { enabled: on, merge, skip, skipGrammar, skipSlang, skipEntities });

    window.invalidatePreparedSetupVocabulary?.();
    // The clicks above each schedule their own refresh; this only restates what
    // the buttons now say.
    setTimeout(refresh, 0);
}

// Phone sheets: a rule's description (behind its ⓘ) and the More rules
// group. Both are blocks already on the page; on a phone CSS lifts the open one
// into a sheet over the list. A wide screen shows them in place, so there is
// nothing to open there.
function openSmartSkipSheet(sheet, opener) {
    closeSmartSkipSheets();
    if (!sheet) return;
    sheet.classList.add('is-sheet-open');
    opener?.setAttribute('aria-expanded', 'true');
    const backdrop = document.getElementById('smartSkipSheetBackdrop');
    if (backdrop) backdrop.hidden = false;
    sheet.focus?.({ preventScroll: true });
}

function closeSmartSkipSheets() {
    document.querySelectorAll('#fastModeModal .is-sheet-open').forEach(sheet => sheet.classList.remove('is-sheet-open'));
    document.querySelectorAll('#fastModeModal .smart-skip-info').forEach(info => info.setAttribute('aria-expanded', 'false'));
    const backdrop = document.getElementById('smartSkipSheetBackdrop');
    if (backdrop) backdrop.hidden = true;
}

function isSmartSkipSheetOpen() {
    return Boolean(document.querySelector('#fastModeModal .is-sheet-open'));
}

function refresh() {
    window.refreshBridge?.();
    const wrapper = document.getElementById('setupOptions');
    if (!wrapper) return;
    const isArtist = Boolean(globalThis.activeArtist);
    const state = currentState();
    const featureCards = ['lemmaToggleContainer', 'cognateToggleContainer']
        .map(id => document.getElementById(id));
    const availabilityResolved = featureCards.every(card => card?.dataset.available === 'true'
        || card?.dataset.available === 'false');
    wrapper.style.display = availabilityResolved || isArtist ? 'block' : 'none';

    const on = state === 'on';
    const extras = globalThis.collectExtras?.() || {};

    // A shortcut is listed only where it can do something: look-alikes and
    // combined forms need the release's mapping, the other three need at least
    // one word of their kind in this deck.
    // The two main shortcuts lead. The other three sit under More rules, which
    // is listed only where one of them can do something.
    let advancedAvailable = 0;
    let advancedOn = 0;
    for (const kind of ['grammar', 'slang', 'entity']) {
        const container = document.getElementById(`${kind}ToggleContainer`);
        if (!container) continue;
        const available = (extras.potential?.[kind] || 0) > 0;
        if (available) {
            advancedAvailable++;
            if (shortcutOn(kind)) advancedOn++;
        }
        container.style.display = available ? 'block' : 'none';
    }
    const moreButton = document.getElementById('smartSkipMoreOptions');
    if (moreButton) moreButton.hidden = advancedAvailable === 0;
    const moreGroup = document.getElementById('smartSkipMore');
    if (moreGroup) moreGroup.hidden = advancedAvailable === 0;
    const moreState = document.getElementById('smartSkipMoreState');
    if (moreState) moreState.textContent = advancedOn ? `${advancedOn} on` : '';

    const counts = {
        cognate: extras.cognates?.length || 0,
        lemma: extras.lemmas?.length || 0,
        grammar: extras.grammar?.length || 0,
        slang: extras.slang?.length || 0,
        entity: extras.entities?.length || 0,
    };
    for (const kind of Object.keys(counts)) {
        const active = shortcutOn(kind);
        const toggle = document.querySelector(`[data-ss-toggle="${kind}"]`);
        if (toggle) toggle.setAttribute('aria-checked', String(active));
        // A rule that is on shows how many words it takes out of the deck.
        const count = document.querySelector(`[data-ss-count="${kind}"]`);
        if (count) {
            const n = counts[kind];
            count.textContent = active && n ? n.toLocaleString() : '';
        }
    }

    // The home row exposes two explicit, mutually exclusive choices.
    document.querySelectorAll('[data-ss-master]').forEach(button => {
        button.setAttribute('aria-pressed', String((button.dataset.ssMaster === 'on') === on));
    });
    const toggleBtn = document.getElementById('smartSkipToggleBtn');
    const stateLabel = document.getElementById('smartSkipStateLabel');
    if (toggleBtn) {
        toggleBtn.setAttribute('aria-checked', String(on));
        toggleBtn.classList.toggle('is-on', on);
    }
    if (stateLabel) {
        stateLabel.textContent = on ? 'On' : 'Off';
    }
    const hubRow = document.getElementById('setupOptions')?.querySelector('.home-smart-skip, .fast-track-hub-row');
    if (hubRow) {
        hubRow.classList.toggle('is-unseen', !hasSeenFastTrackPage());
        hubRow.classList.toggle('is-on', on);
    }
    // The page header: the master switch, and how many words the rules skip
    // (combined forms included, as the setup row has always counted them).
    const totalSkipped = (extras.allSkipped?.length || 0) + (extras.lemmas?.length || 0);
    // Home strip: one line, so the count replaces the description when on.
    const homeSummary = document.getElementById('fastTrackHubSummary');
    if (homeSummary) homeSummary.textContent = on && totalSkipped ? `${totalSkipped.toLocaleString()} fewer cards` : 'fewer cards';
    const heroBadge = document.getElementById('smartSkipHeroBadgeText');
    if (heroBadge) heroBadge.textContent = on && totalSkipped ? `${totalSkipped.toLocaleString()} skipped` : '';
    const pageSwitch = document.getElementById('smartSkipPageSwitch');
    if (pageSwitch) pageSwitch.setAttribute('aria-checked', String(on));
    const pageState = document.getElementById('smartSkipPageState');
    if (pageState) pageState.textContent = on ? 'On' : 'Off';
    updateMappingStatus();
    updateStreamlineRecCallout();
    updateStreamlineLanguageExamples();
    globalThis.renderFastTrackSkippedDecks?.();
    globalThis.refreshExtrasButtons?.();
    globalThis.refreshExtrasButton?.();
}

const STREAMLINE_REC_DISMISSED_KEY = 'fluency_streamline_rec_dismissed_v1';
// One visit retires the hint. Same best-effort storage shape as the callout
// above: a blocked localStorage means the hint simply keeps showing, which is
// the harmless direction to fail in.
const FAST_TRACK_PAGE_SEEN_KEY = 'fluency_fast_track_page_seen_v1';

function hasSeenFastTrackPage() {
    try { return localStorage.getItem(FAST_TRACK_PAGE_SEEN_KEY) === '1'; }
    catch (_) { return false; }
}

function markFastTrackPageSeen() {
    try { localStorage.setItem(FAST_TRACK_PAGE_SEEN_KEY, '1'); } catch (_) {}
}

function updateStreamlineRecCallout() {
    const callout = document.getElementById('streamlineRecCallout');
    if (!callout) return;
    let dismissed = false;
    try {
        dismissed = localStorage.getItem(STREAMLINE_REC_DISMISSED_KEY) === '1';
    } catch (_) {}
    callout.style.display = dismissed ? 'none' : 'flex';
}

function languageName(code) {
    const names = { en: 'English', es: 'Spanish', fi: 'Finnish', fr: 'French', pt: 'Portuguese', cs: 'Czech', nl: 'Dutch', pl: 'Polish' };
    return names[code] || String(code || '').toUpperCase();
}

// Every string below used to say "English", because English was the only
// language a map had ever shipped scores for. Czech now ships Polish too, so
// the copy has to read the learner's actual choice or it describes a filter
// they have not switched on. cognates.js owns the names; this falls back to
// them only when it has not loaded yet.
function knownLanguageLabels() {
    const active = globalThis.activeKnownLanguages?.() || [];
    const label = globalThis.knownLanguageLabel || languageName;
    return active.map(code => label(code));
}

// "English", "Polish", "English or Polish" -- the phrase that reads correctly
// inside a sentence about what gets set aside.
function knownLanguagePhrase(joiner = 'or') {
    const labels = knownLanguageLabels();
    if (labels.length === 0) return 'a language you already know';
    if (labels.length === 1) return labels[0];
    return `${labels.slice(0, -1).join(', ')} ${joiner} ${labels[labels.length - 1]}`;
}

function showUnavailableMessage(feature) {
    const target = config?.languages?.[selectedLanguage]?.name || languageName(selectedLanguage);
    if (feature === 'lemmas') {
        alert(`Word-form mapping not found for ${target}. Each form will stay on its own card.`);
        return;
    }
    if (feature === 'cognates') {
        const knownCode = globalThis.activeKnownLanguages?.()[0] || 'en';
        alert(`${languageName(knownCode)} to ${target} familiar-word mapping not found. Every word will stay in your deck.`);
        return;
    }
    alert(`Smart Skip is not available for ${target} yet. Your full deck is still available.`);
}

function updateMappingStatus() {
    const adminDetails = document.getElementById('fastModeAdminDetails');
    const isAdmin = Boolean(window.isAuditAccount?.());
    if (adminDetails) {
        adminDetails.style.display = isAdmin ? 'block' : 'none';
    }
    if (!isAdmin) return;

    const target = config?.languages?.[selectedLanguage]?.name || languageName(selectedLanguage);
    const lemmaStatus = document.getElementById('lemmaMappingStatus');
    if (lemmaStatus) {
        lemmaStatus.hidden = lemmaAvailable();
        lemmaStatus.textContent = lemmaAvailable()
            ? ''
            : `Word-form mapping not found for ${target}. This shortcut is currently unavailable.`;
    }
    const cognateStatus = document.getElementById('cognateMappingStatus');
    if (cognateStatus) {
        const knownCode = globalThis.activeKnownLanguages?.()[0] || 'en';
        cognateStatus.hidden = cognateAvailable();
        cognateStatus.textContent = cognateAvailable()
            ? ''
            : `${languageName(knownCode)} → ${target} mapping not found. Look-alike words will remain in the deck.`;
    }
    const algoStatus = document.getElementById('cognateAlgorithmStatus');
    if (algoStatus) {
        const info = globalThis.getCognateAlgorithmInfo?.();
        if (info && info.hasScores) {
            const knowns = (info.knownLanguages && info.knownLanguages.length)
                ? info.knownLanguages
                : (globalThis.activeKnownLanguages?.() || ['en']);
            const details = knowns.map(code => {
                const scorer = info.surfaceScorers?.[code] || 'learner-align/v1';
                const thresh = info.thresholds?.[code] ?? globalThis.cognateThresholdFor?.(code) ?? '–';
                return `${languageName(code)} (${code}): scorer=${scorer}, threshold=${thresh}`;
            }).join(' · ');
            algoStatus.hidden = false;
            algoStatus.innerHTML = `<strong>Cognate Algorithm:</strong> ${details} (schema: ${info.schema || 'v4'})`;
        } else {
            algoStatus.hidden = true;
            algoStatus.textContent = '';
        }
    }
}

const STREAMLINE_LANGUAGE_EXAMPLES = {
    spanish: {
        name: 'Spanish',
        lemmaExplainer: '<em>hablo</em>, <em>habló</em> and <em>hablar</em> share one flashcard.',
        lemmaKeeps: '<em>fue</em> or <em>al</em>'
    },
    french: {
        name: 'French',
        lemmaExplainer: '<em>parle</em>, <em>parla</em> and <em>parler</em> share one flashcard.',
        lemmaKeeps: '<em>au</em> or <em>aux</em>'
    },
    portuguese: {
        name: 'Portuguese',
        lemmaExplainer: '<em>falo</em>, <em>falou</em> and <em>falar</em> share one flashcard.',
        lemmaKeeps: '<em>no</em> or <em>do</em>'
    },
    italian: {
        name: 'Italian',
        lemmaExplainer: '<em>parlo</em>, <em>parlò</em> and <em>parlare</em> share one flashcard.',
        lemmaKeeps: '<em>al</em> or <em>del</em>'
    },
    german: {
        name: 'German',
        lemmaExplainer: '<em>spreche</em>, <em>sprach</em> and <em>sprechen</em> share one flashcard.'
    },
    czech: {
        name: 'Czech',
        lemmaExplainer: '<em>dělám</em>, <em>dělal</em> and <em>dělat</em> share one flashcard.'
    }
};

// A worked pair needs BOTH languages, so it is keyed by target and known
// language together. Only pairs that are genuinely cognate are listed; where
// none is listed the example is drawn from the deck instead, which is honest
// about what it knows rather than inventing a counterpart spelling.
const COGNATE_EXAMPLES = {
    'spanish:en': { target: 'chocolate', known: 'chocolate' },
    'french:en': { target: 'important', known: 'important' },
    'portuguese:en': { target: 'hotel', known: 'hotel' },
    'italian:en': { target: 'problema', known: 'problema' },
    'german:en': { target: 'musik', known: 'music' },
    'czech:en': { target: 'film', known: 'film' },
    'czech:pl': { target: 'ale', known: 'ale' },
    'dutch:en': { target: 'water', known: 'water' },
};

// The highest-ranked word this one language sets aside, read from the deck the
// learner is actually looking at. Used when no pair is curated, so a newly
// shipped language pair still shows a true example on its first day.
function liveCognateExample(code) {
    const vocab = globalThis.setupVocabularySnapshot || globalThis.cachedVocabularyData;
    const cutoff = globalThis.cognateThresholdFor?.(code);
    if (!Array.isArray(vocab) || !Number.isFinite(cutoff)) return null;
    let best = null;
    for (const item of vocab) {
        const score = globalThis.cognateScoreFor
            ? globalThis.cognateScoreFor(item, code)
            : Number(item?.cognate_scores?.[code] || 0);
        if (score < cutoff) continue;
        if (best === null || (item.rank ?? Infinity) < (best.rank ?? Infinity)) best = item;
    }
    return best ? best.word : null;
}

// The look-alikes Smart Skip would set aside if it were on, commonest first:
// the same decision the deck filter makes, run over the loaded vocabulary.
function lookAlikeCandidates() {
    const vocab = globalThis.setupVocabularySnapshot || globalThis.cachedVocabularyData;
    const decide = globalThis.isCognateKnown;
    if (!Array.isArray(vocab) || !decide || !globalThis.cognateFieldAvailable) return [];
    return vocab
        .filter(item => item?.word && !item.duplicate && decide(item))
        .sort((a, b) => (a.rank ?? Infinity) - (b.rank ?? Infinity));
}

function escapeExample(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

// Prefer a curated word for a language the learner has actually selected; fall
// back to a real skipped word; name no example rather than one the setting
// does not describe.
function cognateExampleWord(langKey) {
    const active = globalThis.activeKnownLanguages?.() || [];
    for (const code of active) {
        const pair = COGNATE_EXAMPLES[`${langKey}:${code}`];
        if (pair) return pair.target;
    }
    for (const code of active) {
        const word = liveCognateExample(code);
        if (word) return word;
    }
    return '';
}

function updateStreamlineLanguageExamples() {
    const langKey = String(globalThis.selectedLanguage || 'spanish').toLowerCase();
    const config = STREAMLINE_LANGUAGE_EXAMPLES[langKey] || STREAMLINE_LANGUAGE_EXAMPLES.spanish;

    const lemmaExplainer = document.querySelector('#lemmaToggleContainer .fast-mode-explainer');
    if (lemmaExplainer) {
        lemmaExplainer.innerHTML = `Related forms, such as ${config.lemmaExplainer.replace(' share one flashcard.', ', share one flashcard.')}`;
    }
    const cognateExplainer = document.querySelector('#cognateToggleContainer .fast-mode-explainer');
    if (cognateExplainer) {
        const word = cognateExampleWord(langKey);
        cognateExplainer.innerHTML = `Words that look similar <em>and</em> mean the same in ${escapeExample(knownLanguagePhrase())}`
            + (word ? `, like <em>${escapeExample(word)}</em>.` : '.');
    }
    updateKnownLanguageCopy();
}

// The three sentences that named English outright. Each is rewritten in place
// from the learner's selection, so turning English off and Polish on changes
// what the page says it will do as well as what it does.
function updateKnownLanguageCopy() {
    const phrase = knownLanguagePhrase();
    const callout = document.getElementById('streamlineRecCalloutText');
    if (callout) {
        callout.textContent = `Related word forms share one flashcard, and obvious look-alikes from ${phrase} are set aside, `
            + 'so you study fewer cards without missing examples.';
    }
    const familiar = document.getElementById('cognateSettingExplanation');
    if (familiar) {
        familiar.textContent = `Sets aside words whose meaning is already obvious from ${phrase}.`;
    }
    const sensitivity = document.getElementById('cognateSensitivityExplanationText');
    if (sensitivity) {
        sensitivity.textContent = `Sets how similar to ${phrase} a word must be before it is skipped: `
            + 'Loose skips only identical words; Strict skips looser look-alikes.';
    }
}

// `section` is the seam for the unified UI: the setup button, a skipped-count
// link and a future lyrics "extras" entry can all deep-link into one part of
// this sheet without each knowing how it is laid out.
function openFastModePage({ section } = {}) {
    returnToSettings = !document.getElementById('settingsModal')?.classList.contains('hidden');
    markFastTrackPageSeen();
    if (!section) globalThis.resetSkippedCategory?.();
    closeSmartSkipSheets();
    document.getElementById('smartSkipMore')?.classList.remove('is-expanded');
    document.getElementById('smartSkipMoreOptions')?.setAttribute('aria-expanded', 'false');
    refresh();
    updateStreamlineLanguageExamples();
    globalThis.renderFastTrackSkippedDecks?.();
    document.getElementById('fastModeModal')?.classList.remove('hidden');
    if (section) {
        document.querySelector(`.fast-mode-section[data-section="${section}"]`)
            ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function closeFastModePage({ reopenSettings = true } = {}) {
    globalThis.closeSmartSkipPreview?.();
    closeSmartSkipSheets();
    document.getElementById('fastModeModal')?.classList.add('hidden');
    if (reopenSettings && returnToSettings) window.showSettingsModalWithTab?.('study');
    returnToSettings = false;
}

function init() {
    // A sheet is a phone arrangement; widening the window puts its content
    // back in place.
    // The list also changes scroller (its own column on a wide screen, the page
    // on a phone), so it is rebuilt to watch the right one.
    window.matchMedia('(max-width: 899px)').addEventListener('change', () => {
        closeSmartSkipSheets();
        refresh();
        globalThis.renderSkippedWords?.(undefined, { force: true });
    });
    document.getElementById('smartSkipPageSwitch')?.addEventListener('click', () => {
        applyFastMode(currentState() !== 'on');
    });
    document.getElementById('fastTrackHubBtn')?.addEventListener('click', () => openFastModePage());
    document.getElementById('smartSkipToggleBtn')?.addEventListener('click', () => {
        applyFastMode(currentState() !== 'on');
    });
    document.querySelectorAll('[data-ss-master]').forEach(button => {
        button.addEventListener('click', () => {
            const on = button.dataset.ssMaster === 'on';
            if (on !== (currentState() === 'on')) applyFastMode(on);
        });
    });
    document.getElementById('dismissStreamlineRecBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        try { localStorage.setItem(STREAMLINE_REC_DISMISSED_KEY, '1'); } catch (_) {}
        updateStreamlineRecCallout();
    });
    document.getElementById('closeFastModeModal')?.addEventListener('click', () => closeFastModePage());
    document.getElementById('fastModeModal')?.addEventListener('click', event => {
        if (event.target?.id === 'fastModeModal') closeFastModePage();
    });
    document.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        if (globalThis.isSmartSkipPreviewOpen?.()) {
            globalThis.closeSmartSkipPreview?.();
            return;
        }
        if (isSmartSkipSheetOpen()) {
            closeSmartSkipSheets();
            return;
        }
        if (document.getElementById('fastModeModal')?.classList.contains('hidden')) return;
        closeFastModePage();
    });

    // ui.js and main.js show and hide the two containers directly, in about a
    // dozen places, and none of them raises an event. Watching the attribute
    // they actually set is the one hook that cannot fall out of sync.
    const observer = new MutationObserver(refresh);
    for (const id of ['lemmaToggleContainer', 'cognateToggleContainer']) {
        const element = document.getElementById(id);
        if (element) observer.observe(element, { attributes: true, attributeFilter: ['style', 'data-available'] });
    }
    document.querySelectorAll('.lemma-toggle-btn, .cognate-toggle-btn').forEach(button => {
        button.addEventListener('click', () => {
            const fromMaster = applyingMasterSwitch;
            // ui.js owns the actual toggle and may have registered its click
            // handler after ours. Read its result on the next task.
            setTimeout(() => {
                if (!fromMaster) {
                    const previous = readFastTrack(selectedLanguage);
                    const merge = lemmaAvailable() ? lemmaOn() : previous.merge;
                    const skip = cognateAvailable() ? cognatesExcluded() : previous.skip;
                    saveFastTrack(selectedLanguage, { enabled: merge || skip || previous.bridge || previous.skipGrammar || previous.skipSlang || previous.skipEntities, merge, skip });
                }
                refresh();
            }, 0);
        });
    });

    // Each shortcut's switch clicks its hidden control, so what a change means
    // stays in the handlers above and in ui.js.
    document.querySelectorAll('[data-ss-toggle]').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const kind = toggle.dataset.ssToggle;
            const turnOn = !shortcutOn(kind);
            const value = kind === 'lemma' ? (turnOn ? 'on' : 'off') : (turnOn ? 'exclude' : 'include');
            document.querySelector(`.${kind}-toggle-btn[data-${kind}="${value}"]`)?.click();
        });
    });
    // ⓘ opens a rule's description as a sheet on a phone. A wide screen
    // always shows the description and hides the ⓘ.
    document.querySelectorAll('#fastModeModal .smart-skip-info').forEach(info => {
        info.addEventListener('click', () => {
            const detail = info.closest('.smart-skip-shortcut')?.querySelector('.smart-skip-shortcut-detail');
            openSmartSkipSheet(detail, info);
        });
    });
    // More rules: on a wide screen it unfolds in place (folded each time the
    // page opens, since they are optional); on a phone it opens as a sheet.
    document.getElementById('smartSkipMoreOptions')?.addEventListener('click', event => {
        const group = document.getElementById('smartSkipMore');
        if (!group) return;
        if (window.matchMedia('(min-width: 900px)').matches) {
            const open = !group.classList.contains('is-expanded');
            group.classList.toggle('is-expanded', open);
            event.currentTarget.setAttribute('aria-expanded', String(open));
            return;
        }
        openSmartSkipSheet(group);
    });
    document.querySelectorAll('#fastModeModal .smart-skip-sheet-done').forEach(done => {
        done.addEventListener('click', closeSmartSkipSheets);
    });
    document.getElementById('smartSkipSheetBackdrop')?.addEventListener('click', closeSmartSkipSheets);

    document.querySelectorAll('.grammar-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const exclude = btn.dataset.grammar === 'exclude';
            setToggleState('grammar', btn.dataset.grammar);
            globalThis.excludeGrammarParticles = exclude;
            const prev = readFastTrack(selectedLanguage);
            saveFastTrack(selectedLanguage, { ...prev, skipGrammar: exclude, enabled: prev.merge || prev.skip || prev.bridge || exclude || prev.skipSlang || prev.skipEntities });
            window.invalidatePreparedSetupVocabulary?.();
            refreshAdvancedStudyChoices();
            refresh();
        });
    });
    document.querySelectorAll('.slang-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const exclude = btn.dataset.slang === 'exclude';
            setToggleState('slang', btn.dataset.slang);
            globalThis.excludeSlang = exclude;
            const prev = readFastTrack(selectedLanguage);
            saveFastTrack(selectedLanguage, { ...prev, skipSlang: exclude, enabled: prev.merge || prev.skip || prev.bridge || prev.skipGrammar || exclude || prev.skipEntities });
            window.invalidatePreparedSetupVocabulary?.();
            refreshAdvancedStudyChoices();
            refresh();
        });
    });
    document.querySelectorAll('.entity-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const exclude = btn.dataset.entity === 'exclude';
            setToggleState('entity', btn.dataset.entity);
            globalThis.excludeProperNouns = exclude;
            const prev = readFastTrack(selectedLanguage);
            saveFastTrack(selectedLanguage, { ...prev, skipEntities: exclude, enabled: prev.merge || prev.skip || prev.bridge || prev.skipGrammar || prev.skipSlang || exclude });
            window.invalidatePreparedSetupVocabulary?.();
            refreshAdvancedStudyChoices();
            refresh();
        });
    });

    refresh();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

globalThis.refreshFastMode = refresh;
globalThis.openFastModePage = openFastModePage;
globalThis.showFastModeUnavailable = showUnavailableMessage;
globalThis.updateStreamlineLanguageExamples = updateStreamlineLanguageExamples;
globalThis.updateKnownLanguageCopy = updateKnownLanguageCopy;
