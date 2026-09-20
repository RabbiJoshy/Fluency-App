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

function lemmaDisplayOf(item, host) {
    // The surviving card is anchored to the most frequent surface, which can
    // itself be an inflection. Show the shared headword used for grouping,
    // with a translation from that headword's sense.
    const key = lemmaKeyOf(item);
    const matches = [host, item].flatMap(entry => (entry?.meanings || []).filter(meaning =>
        String(meaning?.headword || '').normalize('NFC').toLocaleLowerCase('es').trim() === key
    ));
    const translated = matches.find(meaning => String(meaning.translation || '').trim());
    const word = matches[0]?.headword
        || [host?.lemma, item?.lemma].find(value =>
            String(value || '').normalize('NFC').toLocaleLowerCase('es').trim() === key
        )
        || key;
    return { word: String(word).trim(), translation: translated?.translation?.trim() || firstTranslation(item) };
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
    // `ready` separates "we looked and found none" from "we have not looked
    // yet". Without it a caller cannot tell the two apart, and the buttons
    // announced a verified zero while the vocabulary was still loading.
    const empty = { cognates: [], lemmas: [], ready: false };
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
    return { cognates, lemmas, ready: true };
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
        const lemma = kind === 'lemma' ? lemmaDisplayOf(item, mergedInto) : null;
        const note = kind === 'cognate' ? cognateNote(item) : `${lemma.word} ${lemma.translation}`;
        return `<li class="extras-row extras-row--${kind}" data-search-text="${escapeHtml(`${item.word} ${translation} ${note}`.toLocaleLowerCase())}">
            ${kind === 'lemma'
                ? `<span class="extras-base"><strong>${escapeHtml(lemma.word)}</strong><small>${escapeHtml(lemma.translation)}</small></span>`
                : ''}
            <span class="extras-word-stack"><button type="button" class="extras-open-card" data-card-id="${escapeHtml(item.id || '')}" aria-label="View ${escapeHtml(item.word)} card">${escapeHtml(item.word)}</button>${kind === 'lemma' ? `<span class="extras-translation">${escapeHtml(translation)}</span>` : ''}</span>
            ${kind === 'cognate' ? `<span class="extras-translation">${escapeHtml(translation)}</span>` : ''}
        </li>`;
    }).join('');
}

function renderMergedForms() {
    const { lemmas } = collectExtras();
    const body = document.getElementById('mergedFormsBody');
    if (!body) return lemmas;
    const total = document.getElementById('mergedFormsTotal');
    if (total) total.textContent = `${lemmas.length.toLocaleString()} forms`;

    if (lemmas.length === 0) {
        body.innerHTML = `<p class="extras-empty">No word forms are currently merged. Every form is shown as its own card.</p>`;
        return lemmas;
    }

    body.innerHTML = `<ul class="extras-list">${renderRows(lemmas, 'lemma')}</ul>`;
    return lemmas;
}

function renderSkippedWords() {
    const { cognates } = collectExtras();
    const body = document.getElementById('skippedWordsBody');
    if (!body) return cognates;
    const total = document.getElementById('skippedWordsTotal');
    if (total) total.textContent = `${cognates.length.toLocaleString()} words`;

    if (cognates.length === 0) {
        body.innerHTML = `<p class="extras-empty">No words are currently set aside. Obvious look-alikes remain in the deck.</p>`;
        return cognates;
    }

    body.innerHTML = `<ul class="extras-list">${renderRows(cognates, 'cognate')}</ul>`;
    return cognates;
}

function extrasSetPills(entries, kind, levelIndex, progressForItem) {
    if (!entries.length) return '';
    const pills = [];
    for (let start = 0; start < entries.length; start += 20) {
        const cards = entries.slice(start, start + 20);
        const count = cards.length;
        const setNumber = Math.floor(start / 20) + 1;
        const states = cards.map(({ item }) => progressForItem?.(item) || null);
        const seen = states.filter(state => state?.seen).length;
        const review = states.filter(state => state?.needsReview).length;
        const complete = seen === count && review === 0;
        pills.push(`<button type="button" class="extras-set-pill${complete ? ' is-complete' : review ? ' needs-review' : ''}" data-ft-kind="${kind}" data-ft-level="${levelIndex}" data-ft-start="${start}" aria-label="Study skipped set ${setNumber}, ${count} words, ${seen} seen${review ? `, ${review} to review` : ''}">
            <span class="extras-set-pill-num">${setNumber}</span>
            <small>${seen}/${count}</small>
        </button>`);
    }
    return `<div class="extras-set-pills" role="group" aria-label="Skipped word sets">${pills.join('')}</div>`;
}

function skippedByLevel(cognates, ranges) {
    const levels = (ranges || []).map((range, index) => ({ range, index, entries: [] }));
    if (!levels.length) levels.push({ range: null, index: 0, entries: [] });
    for (const entry of cognates) {
        const match = levels.find(({ range }) => {
            if (!range) return true;
            const field = range.rankBasis === 'stable' ? 'stableRank'
                : range.rankBasis === 'display' ? 'displayRank'
                : range.rankBasis === 'category' ? 'categoryRank' : 'rank';
            const rank = Number(entry.item?.[field]);
            return rank >= Number(range.startRank) && rank < Number(range.endRank);
        });
        if (match) match.entries.push(entry);
        else {
            let other = levels.find(level => !level.range);
            if (!other) {
                other = { range: null, index: levels.length, entries: [] };
                levels.push(other);
            }
            other.entries.push(entry);
        }
    }
    return levels.filter(level => level.entries.length);
}

// A level is the stable context; within it the skipped cards form decks of 20.
// Progress stays on each original card ID, regardless of current filters.
function renderFastTrackDeck({ cognates = [], lemmas = [] }, { ranges = [], selectedLevel = null, progressForItem = null } = {}) {
    const groups = skippedByLevel(cognates, ranges);
    const currentIndex = groups.find(group => String(group.range?.level) === String(selectedLevel))?.index ?? groups[0]?.index;
    const skippedBlock = cognates.length
        ? `<section class="extras-deck-group">
            <h4>Skipped look-alikes <span class="extras-count">${cognates.length}</span></h4>
            <p class="extras-deck-hint">Study these words in decks of up to 20. Each deck belongs to its original level; your card progress carries over if you change Fast Track settings.</p>
            <div class="extras-level-list">${groups.map(({ range, index, entries }) => {
                const current = index === currentIndex;
                const label = range ? `Level ${index + 1}` : 'Skipped words';
                const deckCount = Math.ceil(entries.length / 20);
                return `<details class="extras-level-group"${current ? ' open' : ''}>
                    <summary><strong>${label}</strong><span>${entries.length} words · ${deckCount} deck${deckCount === 1 ? '' : 's'}</span></summary>
                    ${extrasSetPills(entries, 'cognate', index, progressForItem)}
                </details>`;
            }).join('')}</div>
           </section>`
        : '';
    const mergedNote = lemmas.length
        ? `<p class="extras-deck-hint extras-merged-note">Merged word forms stay on their shared cards, so they do not need separate decks.</p>`
        : '';
    return `${skippedBlock}${mergedNote}`;
}

async function startFastTrackSkippedSet(kind, start, levelIndex = 0, ranges = []) {
    const extras = collectExtras();
    const allEntries = kind === 'lemma' ? extras.lemmas : extras.cognates;
    const level = skippedByLevel(allEntries, ranges).find(group => group.index === Number(levelIndex));
    const entries = level?.entries || [];
    const slice = entries.slice(Number(start) || 0, (Number(start) || 0) + 20).map(({ item }) => item);
    if (!slice.length || !g().loadVocabularyData) return;
    const setNumber = Math.floor((Number(start) || 0) / 20) + 1;
    const levelSetCount = Math.max(1, Math.ceil(entries.length / 20));
    const levelLabel = level?.range ? `Level ${Number(levelIndex) + 1}` : 'Skipped words';
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.style.display = 'block';
        loadingMessage.textContent = `Loading ${levelLabel} skipped deck ${setNumber}...`;
    }
    window.showAppLoading?.(`Loading ${levelLabel} skipped deck ${setNumber}`, 'Preparing Fast Track cards…');
    try {
        await g().loadVocabularyData('1-50000', {
            rankBasis: 'source',
            studyMode: 'all',
            fastTrackCards: slice,
            setNumber,
            levelSetCount,
            levelNumber: level?.range ? Number(levelIndex) + 1 : null,
            setLabel: `${levelLabel} · skipped deck ${setNumber} of ${levelSetCount}`,
            isFastTrack: true,
        });
    } finally {
        window.hideAppLoading?.();
        if (loadingMessage) loadingMessage.style.display = 'none';
    }
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

// One number per setting, and only when it has been counted.
//
// The count used to appear twice -- on the button and again in an info line
// underneath, written by two different functions in two different wordings.
// The info lines are gone; the button carries the figure, because the button is
// the thing that acts on it.
//
// A count of zero is now three different states and they are no longer
// conflated: nothing loaded yet (say nothing), the filter is off (say nothing),
// and the filter is on but matched no word (say exactly that). The last one is
// what "View skipped words (0)" used to render, which read like a broken button
// rather than a result.
function applyCountedButton(button, label, none, { active, ready, count, noneText }) {
    if (!button) return;
    const show = active && ready && count > 0;
    button.style.display = show ? 'inline-flex' : 'none';
    if (label && show) label.textContent = `View ${count.toLocaleString()} ${count === 1 ? noneText.one : noneText.many}`;
    if (none) {
        const empty = active && ready && count === 0;
        none.hidden = !empty;
        if (empty) none.textContent = noneText.empty;
    }
}

function refreshExtrasButtons() {
    const { cognates, lemmas, ready } = collectExtras();

    applyCountedButton(
        document.getElementById('viewMergedFormsBtn'),
        document.getElementById('mergedFormsCount'),
        document.getElementById('lemmaNoneLine'),
        {
            active: Boolean(g().useLemmaMode && g().lemmaFieldAvailable),
            ready,
            count: lemmas.length,
            noneText: {
                one: 'merged form',
                many: 'merged forms',
                empty: 'No forms shared a word here, so nothing was merged.',
            },
        }
    );

    applyCountedButton(
        document.getElementById('viewSkippedWordsBtn'),
        document.getElementById('skippedWordsCount'),
        document.getElementById('cognateNoneLine'),
        {
            active: Boolean(g().excludeCognates && g().cognateFieldAvailable),
            ready,
            count: cognates.length,
            noneText: {
                one: 'skipped word',
                many: 'skipped words',
                empty: 'No word in this deck was close enough to skip, so every word stayed in.',
            },
        }
    );

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
            closeSavedWords();
        }
    });

    document.getElementById('closeSavedWordsModal')?.addEventListener('click', closeSavedWords);
    document.getElementById('savedWordsModal')?.addEventListener('click', event => {
        if (event.target?.id === 'savedWordsModal') closeSavedWords();
    });
    document.getElementById('downloadSavedWordsBtn')?.addEventListener('click', downloadSavedWords);
    document.getElementById('settingsSavedWordsBtn')?.addEventListener('click', () => {
        document.getElementById('settingsModal')?.classList.add('hidden');
        openSavedWords();
    });

    refreshExtrasButtons();
}

const SAVED_WORDS_KEY = 'fluency_saved_words_v1';

function loadSavedWords() {
    try {
        const raw = localStorage.getItem(SAVED_WORDS_KEY);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
        return [];
    }
}

function writeSavedWords(items) {
    localStorage.setItem(SAVED_WORDS_KEY, JSON.stringify(items));
}

function savedWordKey(item) {
    return `${item.language || ''}\0${item.surface || ''}\0${item.sentence || ''}`;
}

function isWordSaved(surface, sentence, language) {
    const key = savedWordKey({ language, surface, sentence });
    return loadSavedWords().some(item => savedWordKey(item) === key);
}

function toggleSavedWord(entry) {
    const language = entry.language || g().selectedLanguage || '';
    const next = {
        language,
        surface: entry.surface,
        gloss: entry.gloss || '',
        pos: entry.pos || '',
        sentence: entry.sentence || '',
        english: entry.english || '',
        savedAt: new Date().toISOString(),
    };
    const items = loadSavedWords();
    const key = savedWordKey(next);
    const index = items.findIndex(item => savedWordKey(item) === key);
    if (index >= 0) items.splice(index, 1);
    else items.unshift(next);
    writeSavedWords(items);
    renderSavedWords();
    return index < 0;
}

function renderSavedWords() {
    const body = document.getElementById('savedWordsBody');
    if (!body) return;
    const items = loadSavedWords();
    if (items.length === 0) {
        body.innerHTML = '<p class="saved-words-empty">No saved words yet. Save one from Word by word on a sentence.</p>';
        return;
    }
    body.innerHTML = `<ul class="extras-list">${items.map(item => `
        <li class="extras-row">
            <span class="extras-word">${_escapeHtml(item.surface)}</span>
            <span class="extras-note">${_escapeHtml([item.gloss, item.language].filter(Boolean).join(' · '))}</span>
            <span class="extras-note">${_escapeHtml(item.sentence)}</span>
        </li>`).join('')}</ul>`;
}

function _escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function openSavedWords() {
    renderSavedWords();
    document.getElementById('savedWordsModal')?.classList.remove('hidden');
}

function closeSavedWords() {
    document.getElementById('savedWordsModal')?.classList.add('hidden');
}

function downloadSavedWords() {
    const blob = new Blob([JSON.stringify(loadSavedWords(), null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fluency-saved-words.json';
    a.click();
    URL.revokeObjectURL(url);
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
globalThis.openSavedWords = openSavedWords;
globalThis.toggleSavedWord = toggleSavedWord;
globalThis.isWordSaved = isWordSaved;
globalThis.collectExtras = collectExtras;
globalThis.renderFastTrackDeck = renderFastTrackDeck;
globalThis.startFastTrackSkippedSet = startFastTrackSkippedSet;
