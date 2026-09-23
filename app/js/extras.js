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

// These rows are a scan-and-recognise list, not a dictionary entry. A gloss
// carries qualifiers for the card it belongs to -- "to abandon (leave behind)",
// "(interrogative) what" -- and often several senses. Both are noise at a
// glance, so the row shows the bare first sense. The full text still reaches
// data-search-text, so searching a word that was trimmed away still finds it.
function shortGloss(text) {
    return String(text || '')
        .replace(/\([^)]*\)/g, ' ')
        .split(/[;\u2022]|\s+\/\s+/)[0]
        .replace(/\s{2,}/g, ' ')
        .replace(/^[\s,;:\u2013\u2014-]+|[\s,;:\u2013\u2014-]+$/g, '')
        .trim();
}

// The shipped cognate file often has a score and no matched word (schema v1).
// The card's first gloss is then a different sense, so the pair does not look
// like a cognate. When the file names the match, that word wins. Otherwise
// pick the gloss token on this card that most resembles the surface, and only
// call it obvious past a floor — a weak resemblance would invent a pair.
const LOOKALIKE_FLOOR = 0.55;
const LOOKALIKE_STOP = new Set([
    'the', 'a', 'an', 'to', 'of', 'and', 'or', 'for', 'in', 'on', 'at', 'by',
    'with', 'from', 'as', 'is', 'are', 'be', 'it', 'its', 'that', 'this',
    'these', 'those', 'your', 'you', 'not', 'one',
]);

function foldLetters(value) {
    return String(value || '').normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase();
}

function editDistance(left, right) {
    if (left === right) return 0;
    if (!left || !right) return Math.max(left.length, right.length);
    let prev = Array.from({ length: right.length + 1 }, (_, index) => index);
    for (let i = 1; i <= left.length; i++) {
        const cur = [i];
        for (let j = 1; j <= right.length; j++) {
            cur.push(Math.min(
                cur[j - 1] + 1,
                prev[j] + 1,
                prev[j - 1] + (left[i - 1] === right[j - 1] ? 0 : 1),
            ));
        }
        prev = cur;
    }
    return prev[right.length];
}

function letterSimilarity(left, right) {
    const a = foldLetters(left);
    const b = foldLetters(right);
    if (!a || !b) return 0;
    return 1 - editDistance(a, b) / Math.max(a.length, b.length);
}

function glossTokens(text) {
    return String(text || '').split(/[^A-Za-zÀ-ÖØ-öø-ÿ]+/).filter(token => {
        const word = token.toLocaleLowerCase();
        return word.length >= 3 && !LOOKALIKE_STOP.has(word);
    });
}

function cognateEnglish(item) {
    const matched = g().matchedKnownWord?.(item);
    if (matched?.word) return { word: String(matched.word), obvious: true };
    const surface = String(item?.word || '');
    let best = '';
    let bestScore = 0;
    for (const meaning of item?.meanings || []) {
        for (const token of glossTokens(meaning?.translation)) {
            const score = letterSimilarity(surface, token);
            if (score > bestScore) {
                bestScore = score;
                best = token;
            }
        }
    }
    if (best && bestScore >= LOOKALIKE_FLOOR) return { word: best, obvious: true };
    const gloss = shortGloss(firstTranslation(item));
    return { word: gloss, obvious: false };
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
    const matched = g().matchedKnownWord?.(item);
    return `Looks like ${label}${matched?.word ? ` ${matched.word}` : ''}`;
}

function cognatePairHtml(item) {
    const choice = cognateEnglish(item);
    const eq = choice.obvious ? '' : ' hidden';
    const gloss = choice.obvious ? '' : ' is-gloss';
    return `<span class="cognate-pair">
        <button type="button" class="extras-open-card cognate-pair-surface" data-card-id="${escapeHtml(item.id || '')}" aria-label="View ${escapeHtml(item.word)} card">${escapeHtml(item.word)}</button>
        <span class="cognate-pair-eq"${eq} aria-hidden="true">=</span>
        <strong class="cognate-pair-known extras-translation-slot${gloss}">${escapeHtml(choice.word)}</strong>
    </span>`;
}

function paintCognatePair(row, item) {
    const known = row.querySelector('.cognate-pair-known');
    if (!known) return false;
    const choice = cognateEnglish(item);
    known.textContent = choice.word;
    known.classList.toggle('is-gloss', !choice.obvious);
    const eq = row.querySelector('.cognate-pair-eq');
    if (eq) eq.hidden = !choice.obvious;
    return Boolean(choice.word);
}

function renderRows(entries, kind) {
    if (entries.length === 0) return '';
    return entries.map(({ item, mergedInto }) => {
        const translation = firstTranslation(item);
        const shortTranslation = shortGloss(translation);
        const lemma = kind === 'lemma' ? lemmaDisplayOf(item, mergedInto) : null;
        const english = kind === 'cognate' ? cognateEnglish(item).word : '';
        const note = kind === 'cognate' ? `${cognateNote(item)} ${english}` : `${lemma.word} ${lemma.translation}`;
        // `data-extras-id` lets hydrateExtrasTranslations find this row again
        // once the meanings arrive; see the comment on that function.
        return `<li class="extras-row extras-row--${kind}" data-extras-id="${escapeHtml(item.id || '')}" data-search-text="${escapeHtml(`${item.word} ${translation} ${note}`.toLocaleLowerCase())}">
            ${kind === 'lemma'
                ? `<span class="extras-base"><strong>${escapeHtml(lemma.word)}</strong><small class="extras-translation-slot">${escapeHtml(shortGloss(lemma.translation))}</small></span>`
                : ''}
            ${kind === 'cognate'
                ? cognatePairHtml(item)
                : `<span class="extras-word-stack"><button type="button" class="extras-open-card" data-card-id="${escapeHtml(item.id || '')}" aria-label="View ${escapeHtml(item.word)} card">${escapeHtml(item.word)}</button><span class="extras-translation">${escapeHtml(shortTranslation)}</span></span>`}
        </li>`;
    }).join('');
}

function addLemmaSurface(group, item) {
    if (!item?.word) return;
    const key = String(item.word).normalize('NFC').toLocaleLowerCase();
    if (group.seen.has(key)) return;
    group.seen.add(key);
    group.surfaces.push(item);
    const rank = Number(item.rank);
    if (Number.isFinite(rank) && rank < group.rank) group.rank = rank;
}

// One row per lemma: the headword on the left, every surface of that lemma
// on the right. The rank is the most frequent surface in the group.
function groupMergedLemmas(lemmas) {
    const groups = new Map();
    for (const { item, mergedInto } of lemmas) {
        const key = lemmaKeyOf(item);
        if (!key) continue;
        let group = groups.get(key);
        if (!group) {
            group = {
                key,
                host: mergedInto || item,
                lemma: lemmaDisplayOf(item, mergedInto),
                rank: Infinity,
                surfaces: [],
                seen: new Set(),
            };
            groups.set(key, group);
            addLemmaSurface(group, mergedInto);
        }
        addLemmaSurface(group, item);
    }
    const list = [...groups.values()];
    for (const group of list) {
        group.surfaces.sort((a, b) => (a.rank ?? Infinity) - (b.rank ?? Infinity));
    }
    list.sort((a, b) => a.rank - b.rank);
    return list;
}

function renderLemmaGroup(group) {
    const rank = Number.isFinite(group.rank) ? String(group.rank) : '';
    const words = group.surfaces.map(item => item.word).join(' ');
    const translation = shortGloss(group.lemma.translation);
    const chips = group.surfaces.map(item =>
        `<span class="lemma-group-chip">${escapeHtml(item.word)}</span>`
    ).join('');
    return `<li class="lemma-group-row" data-extras-id="${escapeHtml(group.host?.id || '')}" data-search-text="${escapeHtml(`${group.lemma.word} ${group.lemma.translation} ${words}`.toLocaleLowerCase())}">
        <span class="lemma-group-rank">${escapeHtml(rank)}</span>
        <span class="lemma-group-lemma"><strong>${escapeHtml(group.lemma.word)}</strong><small class="extras-translation-slot">${escapeHtml(translation)}</small></span>
        <span class="lemma-group-forms">${chips}<button type="button" class="lemma-group-more" hidden></button></span>
    </li>`;
}

function fitLemmaGroupForms(root) {
    if (!root) return;
    root.querySelectorAll('.lemma-group-forms:not([data-expanded="true"])').forEach(box => {
        const chips = [...box.querySelectorAll('.lemma-group-chip')];
        const more = box.querySelector('.lemma-group-more');
        if (!more || !chips.length) return;
        chips.forEach(chip => { chip.hidden = false; });
        more.hidden = true;
        const available = box.clientWidth;
        if (available < 8) return;
        // Measure the chips themselves. A right-aligned row overflows to the
        // left, and then scrollWidth stays equal to the box, so the overflow
        // is invisible to that test.
        const gap = 6;
        const moreWidth = 48;
        const widths = chips.map(chip => chip.offsetWidth);
        let used = 0;
        let visible = 0;
        for (let index = 0; index < chips.length; index++) {
            const remaining = chips.length - index - 1;
            const reserve = remaining > 0 ? moreWidth + gap : 0;
            if (visible > 0 && used + widths[index] + reserve > available) break;
            used += widths[index] + gap;
            visible += 1;
        }
        const hidden = chips.length - visible;
        chips.forEach((chip, index) => { chip.hidden = index >= visible; });
        if (hidden > 0) {
            more.hidden = false;
            more.textContent = `+ ${hidden}`;
        }
    });
}

function scheduleFitLemmaForms(root) {
    const run = () => fitLemmaGroupForms(root);
    requestAnimationFrame(run);
    document.fonts?.ready?.then(run).catch(() => {});
    if (typeof ResizeObserver === 'function' && root && !root.dataset.fitObserved) {
        root.dataset.fitObserved = '1';
        const observer = new ResizeObserver(run);
        observer.observe(root);
    }
}

// The setup screen loads the *skinny* index — id, word, rank, surface_card_id,
// lemma and nothing else — so `firstTranslation` has nothing to read and every
// row in this list came out with a blank English column. French looked fine
// only because it is still on the older single-file index, which ships
// `meanings` inline; es, pt and cs are on the sharded v15 format and were all
// equally blank. It reads as a Portuguese bug because Portuguese is where you
// happen to look.
//
// The fat rows are already fetchable per study set, and mergeIndexRowPayload
// assigns them onto the very objects this list is holding — so fetching a
// shard fills `item.meanings` in place. Fetch them as rows scroll into view
// rather than up front: the excluded list runs to thousands of words and
// eagerly pulling every shard would download most of the deck to label a list.
function hydrateExtrasTranslations(listEl, entries) {
    if (!listEl) return;
    const pending = new Map();
    for (const { item } of entries) {
        if (!item?.id || firstTranslation(item)) continue;
        pending.set(String(item.id), item);
    }
    if (!pending.size) return;

    const langConfig = g().config?.languages?.[g().selectedLanguage];
    const fetchRows = g().ensureIndexRowsForRange;
    if (!langConfig || typeof fetchRows !== 'function') return;

    const fill = (row, item) => {
        const translation = firstTranslation(item);
        if (!translation) return false;
        if (row.classList.contains('extras-row--cognate')) {
            paintCognatePair(row, item);
        } else {
            const shown = shortGloss(translation);
            row.querySelectorAll('.extras-translation-slot').forEach(slot => {
                slot.textContent = shown;
            });
        }
        // The filter box reads data-search-text, so a hydrated row has to be
        // findable by the English word it now shows.
        const search = row.getAttribute('data-search-text') || '';
        row.setAttribute('data-search-text',
            `${search} ${translation}`.toLocaleLowerCase());
        return true;
    };

    const request = async (rows) => {
        const pairs = [];
        const ranks = [];
        for (const row of rows) {
            const item = pending.get(row.getAttribute('data-extras-id') || '');
            if (!item) continue;
            pairs.push([row, item]);
            const rank = Number(item.rank);
            if (Number.isFinite(rank)) ranks.push(rank);
        }
        if (!ranks.length) return;
        try {
            await fetchRows(langConfig, 0, 0, ranks);
        } catch {
            return;
        }
        for (const [row, item] of pairs) {
            if (fill(row, item)) pending.delete(String(item.id));
        }
    };

    const rows = [...listEl.querySelectorAll('[data-extras-id]')];
    if (typeof IntersectionObserver !== 'function') {
        request(rows.slice(0, 120));
        return;
    }
    const observer = new IntersectionObserver(records => {
        const visible = records.filter(record => record.isIntersecting)
            .map(record => record.target);
        if (!visible.length) return;
        visible.forEach(row => observer.unobserve(row));
        request(visible);
    }, { rootMargin: '250px' });
    rows.forEach(row => observer.observe(row));
}

function renderMergedForms() {
    const { lemmas } = collectExtras();
    const body = document.getElementById('mergedFormsBody');
    if (!body) return lemmas;
    const groups = groupMergedLemmas(lemmas);
    const total = document.getElementById('mergedFormsTotal');
    const forms = groups.reduce((count, group) => count + group.surfaces.length, 0);
    if (total) {
        const wordLabel = groups.length === 1 ? 'word' : 'words';
        const formLabel = forms === 1 ? 'form' : 'forms';
        total.textContent = groups.length
            ? `${groups.length.toLocaleString()} ${wordLabel} · ${forms.toLocaleString()} ${formLabel}`
            : '';
    }

    if (groups.length === 0) {
        body.innerHTML = `<p class="extras-empty">No word forms are currently merged. Every form is shown as its own card.</p>`;
        return lemmas;
    }

    body.innerHTML = `<ul class="lemma-group-list">${groups.map(renderLemmaGroup).join('')}</ul>`;
    hydrateExtrasTranslations(
        body.querySelector('.lemma-group-list'),
        groups.map(group => ({ item: group.host })),
    );
    scheduleFitLemmaForms(body);
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
    hydrateExtrasTranslations(body.querySelector('.extras-list'), cognates);
    return cognates;
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

// One deck per level. Progress stays on each original card ID.
function renderFastTrackDeck({ cognates = [], lemmas = [] }, { ranges = [], selectedLevel = null, progressForItem = null } = {}) {
    const groups = skippedByLevel(cognates, ranges);
    const currentIndex = groups.find(group => String(group.range?.level) === String(selectedLevel))?.index ?? groups[0]?.index;
    const skippedBlock = cognates.length
        ? `<div class="fast-track-level-list">${groups.map(({ range, index, entries }) => {
                const label = range ? `Level ${index + 1}` : 'Skipped words';
                const states = entries.map(({ item }) => progressForItem?.(item) || null);
                const seen = states.filter(state => state?.seen).length;
                const review = states.filter(state => state?.needsReview).length;
                const complete = seen === entries.length && review === 0;
                const mark = complete ? ' is-complete' : review ? ' needs-review' : '';
                const current = index === currentIndex ? ' is-current' : '';
                return `<button type="button" class="fast-track-level-deck${mark}${current}" data-ft-kind="cognate" data-ft-level="${index}" data-ft-start="0" aria-label="Study ${label}, ${entries.length} skipped words, ${seen} seen">
                    <strong>${label}</strong>
                    <span>${seen}/${entries.length}</span>
                </button>`;
            }).join('')}</div>`
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
    const slice = entries.map(({ item }) => item);
    if (!slice.length || !g().loadVocabularyData) return;
    const levelLabel = level?.range ? `Level ${Number(levelIndex) + 1}` : 'Skipped words';
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.style.display = 'block';
        loadingMessage.textContent = `Loading ${levelLabel} skipped words...`;
    }
    window.showAppLoading?.(`Loading ${levelLabel} skipped words`, 'Preparing Fast Track cards…');
    document.getElementById('fastTrackStudyModal')?.classList.add('hidden');
    document.getElementById('fastModeModal')?.classList.add('hidden');
    try {
        await g().loadVocabularyData('1-50000', {
            rankBasis: 'source',
            studyMode: 'all',
            fastTrackCards: slice,
            setNumber: 1,
            levelSetCount: 1,
            levelNumber: level?.range ? Number(levelIndex) + 1 : null,
            setLabel: `${levelLabel} · ${slice.length} skipped words`,
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
    body.querySelectorAll('.extras-list').forEach((list, index) => {
        hydrateExtrasTranslations(list, index === 0 && cognates.length ? cognates : lemmas);
    });
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
    document.querySelectorAll(`#${bodyId} .extras-row, #${bodyId} .lemma-group-row`).forEach(row => {
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
    requestAnimationFrame(() => fitLemmaGroupForms(document.getElementById('mergedFormsBody')));
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
        const more = event.target.closest('.lemma-group-more');
        if (more) {
            const box = more.closest('.lemma-group-forms');
            if (box) {
                box.dataset.expanded = 'true';
                box.classList.add('is-expanded');
                box.querySelectorAll('.lemma-group-chip').forEach(chip => { chip.hidden = false; });
                more.hidden = true;
            }
            return;
        }
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
        // On a wide screen saved words stacks over settings (side-dock.js),
        // so closing it returns to settings; elsewhere it replaces settings,
        // and its ‹ is the way back.
        window.attachSettingsReturn?.('savedWordsModal', closeSavedWords);
        if (!window.sideDock?.keepsSettingsOpen()) {
            document.getElementById('settingsModal')?.classList.add('hidden');
        }
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
