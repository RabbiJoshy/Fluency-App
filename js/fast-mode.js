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

let requestedFastMode = null;
let applyingMasterSwitch = false;

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

// Fast mode is on when every part the release supports is on. With one part
// available it is that part's state; with neither, there is nothing to report.
function currentState() {
    if (requestedFastMode !== null) return requestedFastMode ? 'on' : 'off';
    const parts = [];
    if (lemmaAvailable()) parts.push(lemmaOn());
    if (cognateAvailable()) parts.push(cognatesExcluded());
    if (parts.length === 0) return 'off';
    if (parts.every(Boolean)) return 'on';
    if (parts.every(part => !part)) return 'off';
    // A learner who set the parts individually is in neither state, and saying
    // "on" or "off" would be a lie about their deck.
    return 'custom';
}

// Describes only the parts this release supports. Czech has no lemma mapping,
// so a fixed "forms merged, familiar words set aside" would claim something
// the deck cannot do.
function summaryText() {
    const state = currentState();
    if (state === 'on') return 'Active · skipping repeats';
    if (state === 'off') return 'Off · full deck';
    return 'Custom';
}

// Turning fast mode on or off drives the real controls, so every side effect
// they own — recounting the deck, invalidating the prepared vocabulary,
// re-rendering the level bands — happens exactly once and exactly as it does
// when the learner changes them by hand.
function applyFastMode(on) {
    requestedFastMode = on;
    applyingMasterSwitch = true;
    if (lemmaAvailable() && lemmaOn() !== on) {
        document.querySelector(`.lemma-toggle-btn[data-lemma="${on ? 'on' : 'off'}"]`)?.click();
    }
    if (cognateAvailable() && cognatesExcluded() !== on) {
        document.querySelector(
            `.cognate-toggle-btn[data-cognate="${on ? 'exclude' : 'include'}"]`
        )?.click();
    }
    applyingMasterSwitch = false;
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
    if (button) {
        button.dataset.fast = on ? 'on' : 'off';
        button.classList.toggle('selected', on);
        button.classList.toggle('is-custom', state === 'custom');
        button.setAttribute('aria-pressed', String(on));
    }
    const summary = document.getElementById('fastModeSummary');
    if (summary) summary.textContent = summaryText();
    updateMappingStatus();
    updateStreamlineRecCallout();
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
    const names = { en: 'English', es: 'Spanish', fr: 'French', pt: 'Portuguese', cs: 'Czech' };
    return names[code] || String(code || '').toUpperCase();
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
    alert(`Streamline mappings have not been published for ${target}. Your full deck is still available.`);
}

function updateMappingStatus() {
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

function openFastModePage() {
    refresh();
    document.getElementById('fastModeModal')?.classList.remove('hidden');
}

function closeFastModePage() {
    document.getElementById('fastModeModal')?.classList.add('hidden');
}

function init() {
    document.getElementById('fastModeToggleBtn')?.addEventListener('click', () => {
        try { localStorage.setItem(STREAMLINE_REC_DISMISSED_KEY, '1'); } catch (_) {}
        updateStreamlineRecCallout();
        applyFastMode(currentState() !== 'on');
    });
    document.getElementById('dismissStreamlineRecBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        try { localStorage.setItem(STREAMLINE_REC_DISMISSED_KEY, '1'); } catch (_) {}
        updateStreamlineRecCallout();
    });
    document.getElementById('fastModeDetailBtn')?.addEventListener('click', () => {
        try { localStorage.setItem(STREAMLINE_REC_DISMISSED_KEY, '1'); } catch (_) {}
        updateStreamlineRecCallout();
        openFastModePage();
    });
    document.getElementById('closeFastModeModal')?.addEventListener('click', closeFastModePage);
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
            if (!applyingMasterSwitch) requestedFastMode = null;
            setTimeout(refresh, 0);
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
