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

function getCognateExamples(maxCount = 3) {
    const vocab = globalThis.setupVocabularySnapshot || globalThis.cachedVocabularyData;
    if (!Array.isArray(vocab) || vocab.length === 0) return [];

    let startRank = 0;
    let endRank = Infinity;
    const selectedBtn = document.querySelector('.level-btn.selected');
    if (selectedBtn?.dataset.startRank && selectedBtn?.dataset.endRank) {
        startRank = parseInt(selectedBtn.dataset.startRank, 10);
        endRank = parseInt(selectedBtn.dataset.endRank, 10);
    } else {
        const segBar = document.getElementById('lswSlider');
        const idx = segBar ? parseInt(segBar.dataset.value || '', 10) : NaN;
        if (!isNaN(idx) && Array.isArray(window.lastRenderedPercentageRanges) && window.lastRenderedPercentageRanges[idx]) {
            const range = window.lastRenderedPercentageRanges[idx];
            startRank = range.startRank ?? range.start ?? 0;
            endRank = range.endRank ?? range.end ?? Infinity;
        }
    }

    const decide = globalThis.isCognateKnown;
    const isKnown = item => {
        if (!item || !item.word || item.duplicate) return false;
        if (decide) return Boolean(decide(item));
        const legacy = Number(item.cognate_score || 0);
        return legacy > 0 && legacy >= Number(globalThis.cognateThreshold || 0.7);
    };

    const levelCognates = [];
    const allCognates = [];
    for (const item of vocab) {
        if (!isKnown(item)) continue;
        allCognates.push(item);
        const rank = Number(item.rank ?? item.frequency_rank ?? -1);
        if (rank >= startRank && rank <= endRank) {
            levelCognates.push(item);
        }
    }

    const source = levelCognates.length > 0 ? levelCognates : allCognates;
    const seen = new Set();
    const words = [];
    for (const item of source) {
        const w = String(item.word || '').trim();
        const lower = w.toLowerCase();
        if (!w || seen.has(lower)) continue;
        seen.add(lower);
        words.push(w);
        if (words.length >= maxCount) break;
    }
    return words;
}

// Offers concrete examples of excluded cognates in the current level/deck
// rather than repeating that the switch is active.
function summaryText() {
    const state = currentState();
    const words = getCognateExamples(3);
    const examples = words.length > 0 ? ` (e.g. ${words.join(', ')})` : '';

    if (state === 'on') {
        return words.length > 0
            ? `Skipping obvious words${examples}`
            : 'Skipping obvious look-alikes';
    }
    if (state === 'off') {
        return words.length > 0
            ? `Full deck · includes obvious words${examples}`
            : 'Off · full deck';
    }
    return words.length > 0 ? `Custom · e.g. skipping ${words.join(', ')}` : 'Custom';
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
    updateStreamlineLanguageExamples();
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

const STREAMLINE_LANGUAGE_EXAMPLES = {
    spanish: {
        name: 'Spanish',
        lemmaExplainer: 'Forms such as <em>hablo</em>, <em>habló</em> and <em>hablar</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>hablo</span><span>habló</span><span>hablar</span><b>→ hablar</b>',
        cognateExample: '<span><b>chocolate</b><small>Spanish</small></span><strong>=</strong><span><b>chocolate</b><small>English</small></span>'
    },
    french: {
        name: 'French',
        lemmaExplainer: 'Forms such as <em>parle</em>, <em>parla</em> and <em>parler</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>parle</span><span>parla</span><span>parler</span><b>→ parler</b>',
        cognateExample: '<span><b>important</b><small>French</small></span><strong>=</strong><span><b>important</b><small>English</small></span>'
    },
    portuguese: {
        name: 'Portuguese',
        lemmaExplainer: 'Forms such as <em>falo</em>, <em>falou</em> and <em>falar</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>falo</span><span>falou</span><span>falar</span><b>→ falar</b>',
        cognateExample: '<span><b>hotel</b><small>Portuguese</small></span><strong>=</strong><span><b>hotel</b><small>English</small></span>'
    },
    italian: {
        name: 'Italian',
        lemmaExplainer: 'Forms such as <em>parlo</em>, <em>parlò</em> and <em>parlare</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>parlo</span><span>parlò</span><span>parlare</span><b>→ parlare</b>',
        cognateExample: '<span><b>problema</b><small>Italian</small></span><strong>=</strong><span><b>problema</b><small>English</small></span>'
    },
    german: {
        name: 'German',
        lemmaExplainer: 'Forms such as <em>spreche</em>, <em>sprach</em> and <em>sprechen</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>spreche</span><span>sprach</span><span>sprechen</span><b>→ sprechen</b>',
        cognateExample: '<span><b>musik</b><small>German</small></span><strong>=</strong><span><b>music</b><small>English</small></span>'
    },
    czech: {
        name: 'Czech',
        lemmaExplainer: 'Forms such as <em>dělám</em>, <em>dělal</em> and <em>dělat</em> belong to the same word. Put them on one card so you learn it once while keeping every example.',
        lemmaExample: '<span>dělám</span><span>dělal</span><span>dělat</span><b>→ dělat</b>',
        cognateExample: '<span><b>film</b><small>Czech</small></span><strong>=</strong><span><b>film</b><small>English</small></span>'
    }
};

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
        cognateExample.innerHTML = config.cognateExample;
        cognateExample.setAttribute('aria-label', `Example of a ${config.name} word that is obvious in English`);
    }
}

function openFastModePage() {
    refresh();
    updateStreamlineLanguageExamples();
    document.getElementById('fastModeModal')?.classList.remove('hidden');
}

function closeFastModePage() {
    document.getElementById('fastModeModal')?.classList.add('hidden');
}

function init() {
    document.getElementById('fastModeToggleBtn')?.addEventListener('click', () => {
        applyFastMode(currentState() !== 'on');
    });
    document.getElementById('dismissStreamlineRecBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        try { localStorage.setItem(STREAMLINE_REC_DISMISSED_KEY, '1'); } catch (_) {}
        updateStreamlineRecCallout();
    });
    document.getElementById('fastModeDetailBtn')?.addEventListener('click', () => {
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
globalThis.updateStreamlineLanguageExamples = updateStreamlineLanguageExamples;
