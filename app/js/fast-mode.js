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

function summaryText() {
    const preference = readFastTrack(selectedLanguage);
    if (preference.enabled && preference.merge && preference.skip) return 'Related forms share one card; familiar look-alikes are set aside';
    if (preference.enabled && preference.merge) return 'Related word forms share one card';
    if (preference.enabled && preference.skip) return 'Familiar look-alikes are set aside';
    return 'Full deck · every word form is its own card';
}

// Turning fast mode on or off drives the real controls, so every side effect
// they own — recounting the deck, invalidating the prepared vocabulary,
// re-rendering the level bands — happens exactly once and exactly as it does
// when the learner changes them by hand.
function applyFastMode(on) {
    const previous = readFastTrack(selectedLanguage);
    const hasChoices = previous.merge || previous.skip;
    let merge = hasChoices ? previous.merge : lemmaAvailable();
    let skip = hasChoices ? previous.skip : cognateAvailable();
    if (on && !((merge && lemmaAvailable()) || (skip && cognateAvailable()))) {
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
    applyingMasterSwitch = false;
    saveFastTrack(selectedLanguage, { enabled: on, merge, skip });
    window.invalidatePreparedSetupVocabulary?.();
    // The clicks above each schedule their own refresh; this only restates what
    // the buttons now say.
    setTimeout(refresh, 0);
}

function refresh() {
    const wrapper = document.getElementById('setupOptions');
    if (!wrapper) return;
    const state = currentState();
    const featureCards = ['lemmaToggleContainer', 'cognateToggleContainer']
        .map(id => document.getElementById(id));
    const availabilityResolved = featureCards.every(card => card?.dataset.available === 'true'
        || card?.dataset.available === 'false');
    wrapper.style.display = availabilityResolved ? 'block' : 'none';

    const button = document.getElementById('fastModeToggleBtn');
    const on = state === 'on';
    const languageName = config?.languages?.[selectedLanguage]?.name || selectedLanguage || 'Language';
    const status = document.getElementById('fastModeLanguageStatus');
    if (status) status.textContent = `${languageName} · ${currentUser && !currentUser.isGuest
        ? 'Saved across devices' : 'Saved on this device'}` +
        (availabilityResolved && !lemmaAvailable() && !cognateAvailable() ? ' · Unavailable in this deck' : '');
    const homeSwitch = document.getElementById('fastModeHomeSwitch');
    if (homeSwitch) homeSwitch.setAttribute('aria-pressed', String(on));
    const switchValue = document.getElementById('fastModeHomeSwitchValue');
    if (switchValue) switchValue.textContent = on ? 'On' : 'Off';
    const skipped = globalThis.collectExtras?.()?.cognates?.length || 0;
    const count = document.getElementById('fastModeSkippedCount');
    if (count) count.textContent = skipped ? `${skipped} words` : 'No words skipped';
    const skippedLink = document.getElementById('fastModeSkippedLink');
    if (skippedLink) skippedLink.hidden = skipped === 0;
    if (button) {
        button.dataset.fast = on ? 'on' : 'off';
        button.classList.toggle('selected', on);
        button.classList.remove('is-custom');
        button.setAttribute('aria-pressed', String(on));
    }
    const summary = document.getElementById('fastModeSummary');
    if (summary) summary.textContent = summaryText();
    updateMappingStatus();
    updateStreamlineRecCallout();
    updateStreamlineLanguageExamples();
    globalThis.refreshExtrasButtons?.();
    globalThis.refreshExtrasButton?.();
}

const STREAMLINE_REC_DISMISSED_KEY = 'fluency_streamline_rec_dismissed_v1';

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
    const names = { en: 'English', es: 'Spanish', fr: 'French', pt: 'Portuguese', cs: 'Czech', nl: 'Dutch', pl: 'Polish' };
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
    alert(`Fast Track mappings have not been published for ${target}. Your full deck is still available.`);
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
}

const STREAMLINE_LANGUAGE_EXAMPLES = {
    spanish: {
        name: 'Spanish',
        lemmaExplainer: 'Forms such as <em>hablo</em>, <em>habló</em> and <em>hablar</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>hablo</span><span>habló</span><span>hablar</span><b>→ hablar</b>'
    },
    french: {
        name: 'French',
        lemmaExplainer: 'Forms such as <em>parle</em>, <em>parla</em> and <em>parler</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>parle</span><span>parla</span><span>parler</span><b>→ parler</b>'
    },
    portuguese: {
        name: 'Portuguese',
        lemmaExplainer: 'Forms such as <em>falo</em>, <em>falou</em> and <em>falar</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>falo</span><span>falou</span><span>falar</span><b>→ falar</b>'
    },
    italian: {
        name: 'Italian',
        lemmaExplainer: 'Forms such as <em>parlo</em>, <em>parlò</em> and <em>parlare</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>parlo</span><span>parlò</span><span>parlare</span><b>→ parlare</b>'
    },
    german: {
        name: 'German',
        lemmaExplainer: 'Forms such as <em>spreche</em>, <em>sprach</em> and <em>sprechen</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>spreche</span><span>sprach</span><span>sprechen</span><b>→ sprechen</b>'
    },
    czech: {
        name: 'Czech',
        lemmaExplainer: 'Forms such as <em>dělám</em>, <em>dělal</em> and <em>dělat</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>dělám</span><span>dělal</span><span>dělat</span><b>→ dělat</b>'
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
        const score = Number(item?.cognate_scores?.[code] || 0);
        if (score < cutoff) continue;
        if (best === null || (item.rank ?? Infinity) < (best.rank ?? Infinity)) best = item;
    }
    return best ? best.word : null;
}

function escapeExample(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

// Prefer a curated pair for a language the learner has actually selected; fall
// back to a real excluded word; show nothing rather than an English pair the
// setting does not describe.
function cognateExampleHtml(langKey, targetName) {
    const active = globalThis.activeKnownLanguages?.() || [];
    const label = globalThis.knownLanguageLabel || languageName;
    for (const code of active) {
        const pair = COGNATE_EXAMPLES[`${langKey}:${code}`];
        if (!pair) continue;
        return {
            html: `<span><b>${escapeExample(pair.target)}</b><small>${escapeExample(targetName)}</small></span>`
                + `<strong>=</strong>`
                + `<span><b>${escapeExample(pair.known)}</b><small>${escapeExample(label(code))}</small></span>`,
            note: `Example of a ${targetName} word that is obvious in ${label(code)}`,
        };
    }
    for (const code of active) {
        const word = liveCognateExample(code);
        if (!word) continue;
        return {
            html: `<span><b>${escapeExample(word)}</b><small>${escapeExample(targetName)}</small></span>`
                + `<strong>=</strong>`
                + `<span><small>already clear in ${escapeExample(label(code))}</small></span>`,
            note: `Example of a ${targetName} word that is obvious in ${label(code)}`,
        };
    }
    return null;
}

function updateStreamlineLanguageExamples() {
    const langKey = String(globalThis.selectedLanguage || 'spanish').toLowerCase();
    const config = STREAMLINE_LANGUAGE_EXAMPLES[langKey] || STREAMLINE_LANGUAGE_EXAMPLES.spanish;

    const lemmaExplainer = document.querySelector('#lemmaToggleContainer .fast-mode-explainer');
    if (lemmaExplainer) {
        lemmaExplainer.innerHTML = config.lemmaExplainer;
    }
    const lemmaExample = document.querySelector('#lemmaToggleContainer .fast-mode-example');
    if (lemmaExample) {
        lemmaExample.innerHTML = config.lemmaExample;
    }
    const cognateExample = document.querySelector('#cognateToggleContainer .fast-mode-example--cognate');
    if (cognateExample) {
        const example = cognateExampleHtml(langKey, config.name);
        cognateExample.innerHTML = example ? example.html : '';
        cognateExample.hidden = !example;
        if (example) cognateExample.setAttribute('aria-label', example.note);
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
        callout.textContent = `Related word forms share one card, and obvious look-alikes from ${phrase} are set aside, `
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

function openFastModePage() {
    returnToSettings = !document.getElementById('settingsModal')?.classList.contains('hidden');
    refresh();
    updateStreamlineLanguageExamples();
    document.getElementById('fastModeModal')?.classList.remove('hidden');
}

function closeFastModePage({ reopenSettings = true } = {}) {
    document.getElementById('fastModeModal')?.classList.add('hidden');
    if (reopenSettings && returnToSettings) window.showSettingsModalWithTab?.('study');
    returnToSettings = false;
}

function init() {
    document.getElementById('fastModeToggleBtn')?.addEventListener('click', () => {
        applyFastMode(currentState() !== 'on');
    });
    document.getElementById('fastModeHomeSwitch')?.addEventListener('click', () => applyFastMode(currentState() !== 'on'));
    document.getElementById('fastModeFineTuneBtn')?.addEventListener('click', event => {
        const details = document.getElementById('fastModeFineTune');
        details.hidden = !details.hidden;
        event.currentTarget.setAttribute('aria-expanded', String(!details.hidden));
    });
    document.getElementById('fastModeSkippedLink')?.addEventListener('click', async () => {
        closeFastModePage({ reopenSettings: false });
        await window.goBackToSetup?.();
        document.getElementById('extrasDeckSection')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    document.getElementById('dismissStreamlineRecBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        try { localStorage.setItem(STREAMLINE_REC_DISMISSED_KEY, '1'); } catch (_) {}
        updateStreamlineRecCallout();
    });
    document.getElementById('fastModeDetailBtn')?.addEventListener('click', () => {
        openFastModePage();
    });
    document.getElementById('closeFastModeModal')?.addEventListener('click', () => closeFastModePage());
    document.getElementById('fastModeModal')?.addEventListener('click', event => {
        if (event.target?.id === 'fastModeModal') closeFastModePage();
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') closeFastModePage();
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
                    saveFastTrack(selectedLanguage, { enabled: merge || skip, merge, skip });
                }
                refresh();
            }, 0);
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
