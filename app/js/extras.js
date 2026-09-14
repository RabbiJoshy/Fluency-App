// Extras — the words the current settings keep OUT of the deck, kept browsable
// instead of vanishing.
//
// Speech mode has always dropped these silently. Artist mode already had an
// Extra scope (see artistItemMatchesScope in vocab.js), but that one is driven
// by the pipeline's `extra_category` and covers a different set: loanwords,
// proper nouns, noise. This is the speech-mode counterpart and it covers
// exactly two reasons, both of them learner-chosen rather than pipeline-tagged:
//
//   cognate  — excluded by the Cognates toggle
//   lemma    — a surface form folded into another card by Merge Lemmas
//
// Nothing here re-filters. buildFilteredVocab() has already stamped
// `_lemmaModeRepresentative` on every item by the time a deck exists, so this
// module reads the same state the filter used and reports what it discarded.
// That keeps one source of truth for the rules: if the filter changes, this
// follows without edits.
import './state.js?v=20260825ak';

// Every name below is read off globalThis rather than as a bare identifier.
// state.js defines these lazily via defineProperty, and this module can run
// before a deck exists, so a bare read is a ReferenceError rather than an
// undefined — which is exactly how the first version of this file broke.
const g = () => globalThis;

// Mirrors the two branches of getVocabularyExclusionReason() that a learner
// controls. Deliberately NOT imported from vocab.js — that module exports
// nothing, and duplicating two predicates is cheaper than widening its surface.
function cognateExtra(item) {
    // The same decision the deck filter makes: each known language judged at
    // its own cutoff, with the legacy scalar and slider for older releases.
    const decide = g().isCognateKnown;
    const known = decide
        ? Boolean(decide(item))
        : Number(item.cognate_score || 0) >= g().cognateThreshold;
    return g().excludeCognates && g().cognateFieldAvailable && known;
}

function lemmaExtra(item) {
    if (!g().useLemmaMode || !g().lemmaFieldAvailable) return false;
    // Election is done at runtime by the filter; the legacy shipped stamp is
    // not consulted, exactly as in getVocabularyExclusionReason.
    return item._lemmaModeRepresentative === false;
}

function lemmaKeyOf(item) {
    // vocab.js derives this from the assigned sense's headword; a second copy
    // here would group the Extras list differently from the deck it describes.
    const key = g().lemmaGroupKey;
    return key ? key(item) : String(item?.lemma || '').normalize('NFC').toLocaleLowerCase('es').trim();
}

function firstTranslation(item) {
    const meaning = (item?.meanings || []).find(m => String(m?.translation || '').trim());
    return meaning ? meaning.translation.trim() : '';
}

// A merged form is only meaningful next to the card that swallowed it, so map
// each lemma to the surviving representative before rendering.
function representativesByLemma(items) {
    const hosts = new Map();
    for (const item of items) {
        if (item._lemmaModeRepresentative !== true) continue;
        const key = lemmaKeyOf(item);
        if (key && !hosts.has(key)) hosts.set(key, item);
    }
    return hosts;
}

function collectExtras() {
    const empty = { cognates: [], lemmas: [] };
    // The full loaded vocabulary, stamped by the last buildFilteredVocab pass.
    // Two routes reach it and they do not overlap: on the setup screen only
    // updateExclusionBars() holds it (it publishes the snapshot), and once a
    // deck is built loadVocabularyData() caches it. `vocabularyData` itself is
    // a local in both, never a global.
    const vocab = g().setupVocabularySnapshot || g().cachedVocabularyData;
    if (!Array.isArray(vocab) || vocab.length === 0) return empty;
    // Artist releases may also have a pipeline-defined Extra scope, but that
    // is a different concept. This list reports only the learner's Fast track
    // choices and therefore stays available in both Speech and Lyrics.

    const hosts = representativesByLemma(vocab);
    const cognates = [];
    const lemmas = [];
    for (const item of vocab) {
        if (!item || !item.word || item.duplicate) continue;
        if (cognateExtra(item)) {
            cognates.push({ item, mergedInto: null });
            continue;
        }
        if (lemmaExtra(item)) {
            const host = hosts.get(lemmaKeyOf(item));
            // A form whose host did not survive the other filters is not a
            // merge — it is simply absent, and claiming otherwise would be a
            // provenance lie.
            if (host && host !== item) lemmas.push({ item, mergedInto: host });
        }
    }
    const byRank = (a, b) => (a.item.rank ?? Infinity) - (b.item.rank ?? Infinity);
    cognates.sort(byRank);
    lemmas.sort(byRank);
    return { cognates, lemmas };
}

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

// With more than one known language a bare number says nothing about why the
// word is free, so name the language that made it so.
function cognateNote(item) {
    const strongest = g().strongestKnownLanguage?.(item);
    const fallbackCode = g().activeKnownLanguages?.()[0] || 'en';
    const code = strongest?.code || fallbackCode;
    const label = g().knownLanguageLabel ? g().knownLanguageLabel(code) : code;
    return `Looks like ${escapeHtml(label)}`;
}

function renderRows(entries, kind) {
    if (entries.length === 0) return '';
    return entries.map(({ item, mergedInto }) => {
        const translation = firstTranslation(item);
        // Cognates carry a score the learner can move with the sensitivity
        // setting, so show it rather than repeating the section's blurb on
        // every row. A merged form's useful fact is which card absorbed it.
        const note = kind === 'cognate'
            ? cognateNote(item)
            : (mergedInto?.word
                ? `On the <strong>${escapeHtml(mergedInto.word)}</strong> card`
                : 'Grouped form');
        return `<li class="extras-row" data-search-text="${escapeHtml(`${item.word} ${translation} ${note.replace(/<[^>]+>/g, '')}`.toLocaleLowerCase())}">
            <span class="extras-word">${escapeHtml(item.word)}</span>
            <span class="extras-translation">${escapeHtml(translation)}</span>
            <span class="extras-note${kind === 'cognate' ? ' extras-score' : ''}">${note}</span>
            <button type="button" class="extras-open-card" data-card-id="${escapeHtml(item.id || '')}">Open card</button>
        </li>`;
    }).join('');
}

function renderMergedForms() {
    const { lemmas } = collectExtras();
    const body = document.getElementById('mergedFormsBody');
    if (!body) return lemmas;

    if (lemmas.length === 0) {
        body.innerHTML = `<p class="extras-empty">No word forms are currently merged. Every form is shown as its own card.</p>`;
        return lemmas;
    }

    body.innerHTML = `<div class="extras-section">
        <div class="extras-section-header">
            <h4>Word forms learned together <span class="extras-count">${lemmas.length}</span></h4>
            <button type="button" class="extras-restore" data-restore-kind="lemma">Separate cards</button>
        </div>
        <p class="extras-blurb">These forms appear on their shared base card instead of repeating.</p>
        <ul class="extras-list">${renderRows(lemmas, 'lemma')}</ul>
    </div>`;
    return lemmas;
}

function renderSkippedWords() {
    const { cognates } = collectExtras();
    const body = document.getElementById('skippedWordsBody');
    if (!body) return cognates;

    if (cognates.length === 0) {
        body.innerHTML = `<p class="extras-empty">No words are currently set aside. Obvious look-alikes remain in the deck.</p>`;
        return cognates;
    }

    body.innerHTML = `<div class="extras-section">
        <div class="extras-section-header">
            <h4>Obvious look-alikes <span class="extras-count">${cognates.length}</span></h4>
            <button type="button" class="extras-restore" data-restore-kind="cognate">Show as cards</button>
        </div>
        <p class="extras-blurb">Set aside because their spelling and meaning match a language you already know.</p>
        <ul class="extras-list">${renderRows(cognates, 'cognate')}</ul>
    </div>`;
    return cognates;
}

function renderExtras() {
    renderMergedForms();
    renderSkippedWords();

    const { cognates, lemmas } = collectExtras();
    const body = document.getElementById('extrasBody');
    if (!body) return { cognates, lemmas };

    const sections = [];
    if (cognates.length > 0) {
        sections.push(`<section class="extras-section">
            <div class="extras-section-header">
                <h4>Obvious look-alikes <span class="extras-count">${cognates.length}</span></h4>
                <button type="button" class="extras-restore" data-restore-kind="cognate">Show as cards</button>
            </div>
            <p class="extras-blurb">Set aside because their spelling and meaning closely match a language you already know.</p>
            <ul class="extras-list">${renderRows(cognates, 'cognate')}</ul>
        </section>`);
    }
    if (lemmas.length > 0) {
        sections.push(`<section class="extras-section">
            <div class="extras-section-header">
                <h4>Word forms learned together <span class="extras-count">${lemmas.length}</span></h4>
                <button type="button" class="extras-restore" data-restore-kind="lemma">Separate cards</button>
            </div>
            <p class="extras-blurb">These forms are still included, but appear on one shared card instead of being repeated.</p>
            <ul class="extras-list">${renderRows(lemmas, 'lemma')}</ul>
        </section>`);
    }
    body.innerHTML = sections.length > 0
        ? sections.join('')
        : `<p class="extras-empty">Nothing is being skipped. Fast Track is currently showing every word as its own card.</p>`;
    return { cognates, lemmas };
}

function refreshExtrasButtons() {
    const { cognates, lemmas } = collectExtras();
    const mergedBtn = document.getElementById('viewMergedFormsBtn');
    const mergedCount = document.getElementById('mergedFormsCount');
    if (mergedBtn) {
        const canShowMerged = lemmas.length > 0 && g().useLemmaMode;
        mergedBtn.style.display = canShowMerged ? 'inline-flex' : 'none';
        if (mergedCount) mergedCount.textContent = `(${lemmas.length})`;
    }

    const skippedBtn = document.getElementById('viewSkippedWordsBtn');
    const skippedCount = document.getElementById('skippedWordsCount');
    if (skippedBtn) {
        const canShowSkipped = cognates.length > 0 && g().excludeCognates;
        skippedBtn.style.display = canShowSkipped ? 'inline-flex' : 'none';
        if (skippedCount) skippedCount.textContent = `(${cognates.length})`;
    }

    refreshExtrasButton();
}

// Keep the audit route discoverable even before anything is skipped.
function refreshExtrasButton() {
    const button = document.getElementById('extrasBtn');
    const { cognates, lemmas } = collectExtras();
    const total = cognates.length + lemmas.length;
    if (button) {
        button.style.display = 'inline-flex';
        button.textContent = total === 0
            ? 'See Fast Track words'
            : total === 1 ? 'See 1 Fast Track word' : `See ${total} Fast Track words`;
    }
    window.renderSetupExtrasSection?.();
}

function filterList(bodyId, query) {
    const needle = String(query || '').trim().toLocaleLowerCase();
    document.querySelectorAll(`#${bodyId} .extras-row`).forEach(row => {
        row.hidden = Boolean(needle) && !String(row.dataset.searchText || '').includes(needle);
    });
}

function filterMergedForms(query) {
    filterList('mergedFormsBody', query);
}

function filterSkippedWords(query) {
    filterList('skippedWordsBody', query);
}

function filterExtras(query) {
    filterList('extrasBody', query);
}

function openMergedForms() {
    renderMergedForms();
    const search = document.getElementById('mergedFormsSearch');
    if (search) search.value = '';
    document.getElementById('mergedFormsModal')?.classList.remove('hidden');
}

function closeMergedForms() {
    document.getElementById('mergedFormsModal')?.classList.add('hidden');
}

function openSkippedWords() {
    renderSkippedWords();
    const search = document.getElementById('skippedWordsSearch');
    if (search) search.value = '';
    document.getElementById('skippedWordsModal')?.classList.remove('hidden');
}

function closeSkippedWords() {
    document.getElementById('skippedWordsModal')?.classList.add('hidden');
}

function openExtras() {
    renderExtras();
    const search = document.getElementById('extrasSearch');
    if (search) search.value = '';
    document.getElementById('extrasModal')?.classList.remove('hidden');
}

function closeExtras() {
    document.getElementById('extrasModal')?.classList.add('hidden');
}

function restoreSection(kind) {
    const selector = kind === 'cognate'
        ? '.cognate-toggle-btn[data-cognate="include"]'
        : kind === 'lemma'
            ? '.lemma-toggle-btn[data-lemma="off"]'
            : '';
    const control = selector ? document.querySelector(selector) : null;
    if (!control) return;
    control.click();
    setTimeout(() => {
        renderMergedForms();
        renderSkippedWords();
        renderExtras();
        refreshExtrasButtons();
    }, 0);
}

function initExtras() {
    document.getElementById('viewMergedFormsBtn')?.addEventListener('click', openMergedForms);
    document.getElementById('closeMergedFormsModal')?.addEventListener('click', closeMergedForms);
    document.getElementById('mergedFormsModal')?.addEventListener('click', event => {
        if (event.target?.id === 'mergedFormsModal') closeMergedForms();
    });
    document.getElementById('mergedFormsSearch')?.addEventListener('input', event => filterMergedForms(event.currentTarget.value));

    document.getElementById('viewSkippedWordsBtn')?.addEventListener('click', openSkippedWords);
    document.getElementById('closeSkippedWordsModal')?.addEventListener('click', closeSkippedWords);
    document.getElementById('skippedWordsModal')?.addEventListener('click', event => {
        if (event.target?.id === 'skippedWordsModal') closeSkippedWords();
    });
    document.getElementById('skippedWordsSearch')?.addEventListener('input', event => filterSkippedWords(event.currentTarget.value));

    // Fallback extras modal
    document.getElementById('extrasBtn')?.addEventListener('click', openExtras);
    document.getElementById('closeExtrasModal')?.addEventListener('click', closeExtras);
    document.getElementById('extrasModal')?.addEventListener('click', event => {
        if (event.target?.id === 'extrasModal') closeExtras();
    });
    document.getElementById('extrasSearch')?.addEventListener('input', event => filterExtras(event.currentTarget.value));

    const handleModalBodyClick = async (event, closeFn) => {
        const restore = event.target.closest('.extras-restore');
        if (restore) {
            restoreSection(restore.dataset.restoreKind);
            return;
        }
        const button = event.target.closest('.extras-open-card');
        const id = button?.dataset.cardId;
        if (!id || !globalThis.popupFoundWord) return;
        closeFn();
        document.getElementById('fastModeModal')?.classList.add('hidden');
        await globalThis.popupFoundWord({ id }, { reopenSearchOnBack: false, startFlipped: true });
    };

    document.getElementById('mergedFormsBody')?.addEventListener('click', e => handleModalBodyClick(e, closeMergedForms));
    document.getElementById('skippedWordsBody')?.addEventListener('click', e => handleModalBodyClick(e, closeSkippedWords));
    document.getElementById('extrasBody')?.addEventListener('click', e => handleModalBodyClick(e, closeExtras));

    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            closeMergedForms();
            closeSkippedWords();
            closeExtras();
        }
    });

    refreshExtrasButtons();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initExtras);
} else {
    initExtras();
}

globalThis.refreshExtrasButtons = refreshExtrasButtons;
globalThis.refreshExtrasButton = refreshExtrasButtons;
globalThis.openMergedForms = openMergedForms;
globalThis.openSkippedWords = openSkippedWords;
globalThis.openExtras = openExtras;
globalThis.collectExtras = collectExtras;
