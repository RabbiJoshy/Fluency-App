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
import './state.js?v=3b6be711';

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

function grammarExtra(item) {
    const decide = g().isGrammarParticleItem;
    if (!decide) return false;
    return Boolean(g().excludeGrammarParticles && decide(item));
}

function slangExtra(item) {
    const decide = g().isSlangItem;
    if (!decide) return false;
    return Boolean(g().excludeSlang && decide(item));
}

function entityExtra(item) {
    return Boolean(g().excludeProperNouns) && isEntityItem(item);
}

function isEntityItem(item) {
    if (item.is_propernoun || item.is_propernoun_corpus || item.extra_category === 'proper_noun' || item.extra_category === 'name') return true;
    if (Array.isArray(item.meanings) && item.meanings.length > 0 && item.meanings.every(m => m.pos === 'PROPN')) return true;
    return false;
}

function grammarNote(item) {
    return item.is_clitic || item.clitic_form ? 'Attached clitic form' : 'Grammar particle / functional word';
}

function slangNote() {
    return 'Slang & conversational filler';
}

function entityNote() {
    return 'Named entity / proper noun';
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

const _editDistBuf = new Int32Array(128);

function editDistance(left, right) {
    if (left === right) return 0;
    const n = left.length;
    const m = right.length;
    if (!n) return m;
    if (!m) return n;
    if (m >= 127) {
        let prev = Array.from({ length: m + 1 }, (_, index) => index);
        for (let i = 1; i <= n; i++) {
            const cur = [i];
            for (let j = 1; j <= m; j++) {
                cur.push(Math.min(
                    cur[j - 1] + 1,
                    prev[j] + 1,
                    prev[j - 1] + (left[i - 1] === right[j - 1] ? 0 : 1),
                ));
            }
            prev = cur;
        }
        return prev[m];
    }
    for (let j = 0; j <= m; j++) _editDistBuf[j] = j;
    for (let i = 1; i <= n; i++) {
        let prevDiag = _editDistBuf[0];
        _editDistBuf[0] = i;
        const leftChar = left[i - 1];
        for (let j = 1; j <= m; j++) {
            const temp = _editDistBuf[j];
            const cost = leftChar === right[j - 1] ? 0 : 1;
            _editDistBuf[j] = Math.min(
                _editDistBuf[j - 1] + 1,
                _editDistBuf[j] + 1,
                prevDiag + cost,
            );
            prevDiag = temp;
        }
    }
    return _editDistBuf[m];
}

function letterSimilarity(left, right) {
    const a = foldLetters(left);
    const b = foldLetters(right);
    if (!a || !b) return 0;
    if (a === b) return 1;
    const maxLen = Math.max(a.length, b.length);
    const lenDiff = Math.abs(a.length - b.length);
    if (1 - (lenDiff / maxLen) < LOOKALIKE_FLOOR) return 0;
    return 1 - editDistance(a, b) / maxLen;
}

function glossTokens(text) {
    return String(text || '').split(/[^A-Za-zÀ-ÖØ-öø-ÿ]+/).filter(token => {
        const word = token.toLocaleLowerCase();
        return word.length >= 3 && !LOOKALIKE_STOP.has(word);
    });
}

function cognateEnglish(item) {
    if (!item) return { word: '', obvious: false };
    if (item._cachedCognateEnglish) return item._cachedCognateEnglish;
    const matched = g().matchedKnownWord?.(item);
    if (matched?.word) {
        const res = { word: String(matched.word), obvious: true };
        item._cachedCognateEnglish = res;
        return res;
    }
    const surface = String(item?.word || '');
    let best = '';
    let bestScore = 0;
    for (const meaning of item?.meanings || []) {
        for (const token of glossTokens(meaning?.translation)) {
            const score = letterSimilarity(surface, token);
            if (score > bestScore) {
                bestScore = score;
                best = token;
                if (score >= 0.95) break;
            }
        }
        if (bestScore >= 0.95) break;
    }
    let res;
    if (best && bestScore >= LOOKALIKE_FLOOR) {
        res = { word: best, obvious: true };
    } else {
        const gloss = shortGloss(firstTranslation(item));
        res = { word: gloss, obvious: false };
    }
    item._cachedCognateEnglish = res;
    return res;
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
    const empty = {
        cognates: [],
        lemmas: [],
        grammar: [],
        slang: [],
        entities: [],
        byCategory: {},
        categories: [],
        allSkipped: [],
        potential: { grammar: 0, slang: 0, entity: 0 },
        ready: false
    };
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
    const grammar = [];
    const slang = [];
    const entities = [];
    const allSkipped = [];
    const seenItemIds = new Set();
    // How many words each optional shortcut WOULD skip, whether or not it is
    // on, so the page can list only the shortcuts that do something here.
    const potential = { grammar: 0, slang: 0, entity: 0 };

    for (const item of vocab) {
        if (!item || !item.word || item.duplicate) continue;
        if (g().isGrammarParticleItem?.(item)) potential.grammar++;
        if (g().isSlangItem?.(item)) potential.slang++;
        if (isEntityItem(item)) potential.entity++;
        if (cognateExtra(item)) {
            const entry = { item, mergedInto: null, category: 'cognate', reason: cognateNote(item) };
            cognates.push(entry);
            if (!seenItemIds.has(item.id || item.word)) {
                seenItemIds.add(item.id || item.word);
                allSkipped.push(entry);
            }
            continue;
        }
        if (lemmaExtra(item)) {
            const host = hosts.get(lemmaKeyOf(item));
            if (host && host !== item) {
                const entry = { item, mergedInto: host, category: 'lemma', reason: `Merged into ${host.word}` };
                lemmas.push(entry);
            }
            continue;
        }
        if (grammarExtra(item)) {
            const entry = { item, mergedInto: null, category: 'grammar', reason: grammarNote(item) };
            grammar.push(entry);
            if (!seenItemIds.has(item.id || item.word)) {
                seenItemIds.add(item.id || item.word);
                allSkipped.push(entry);
            }
            continue;
        }
        if (slangExtra(item)) {
            const entry = { item, mergedInto: null, category: 'slang', reason: slangNote(item) };
            slang.push(entry);
            if (!seenItemIds.has(item.id || item.word)) {
                seenItemIds.add(item.id || item.word);
                allSkipped.push(entry);
            }
            continue;
        }
        if (entityExtra(item)) {
            const entry = { item, mergedInto: null, category: 'entity', reason: entityNote(item) };
            entities.push(entry);
            if (!seenItemIds.has(item.id || item.word)) {
                seenItemIds.add(item.id || item.word);
                allSkipped.push(entry);
            }
            continue;
        }
    }
    const byRank = (a, b) => (a.item.rank ?? Infinity) - (b.item.rank ?? Infinity);
    cognates.sort(byRank);
    lemmas.sort(byRank);
    grammar.sort(byRank);
    slang.sort(byRank);
    entities.sort(byRank);
    allSkipped.sort(byRank);

    const categories = [
        { id: 'all', label: 'All skipped', count: allSkipped.length, entries: allSkipped },
        { id: 'cognate', label: 'Look-alikes', count: cognates.length, entries: cognates },
        { id: 'grammar', label: 'Pronouns & particles', count: grammar.length, entries: grammar },
        { id: 'slang', label: 'Slang & fillers', count: slang.length, entries: slang },
        { id: 'entity', label: 'Names & places', count: entities.length, entries: entities },
        { id: 'lemma', label: 'Combined forms', count: lemmas.length, entries: lemmas },
    ].filter(c => c.id === 'all' || c.count > 0);

    const byCategory = {
        all: allSkipped,
        cognate: cognates,
        lemma: lemmas,
        grammar,
        slang,
        entity: entities
    };

    return {
        cognates,
        lemmas,
        grammar,
        slang,
        entities,
        categories,
        byCategory,
        allSkipped,
        potential,
        ready: true
    };
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

function groupCognatesByLemmaAndEnglish(cognates) {
    if (!cognates || !cognates.length) return [];
    const groups = new Map();
    for (const entry of cognates) {
        const item = entry.item || entry;
        const lemma = lemmaKeyOf(item);
        const english = cognateEnglish(item);
        const englishKey = (english.word || '').trim().toLocaleLowerCase();
        const groupKey = `${lemma}:::${englishKey}`;
        let group = groups.get(groupKey);
        if (!group) {
            group = {
                groupKey,
                lemma,
                english,
                primaryEntry: entry,
                surfaces: [item],
                entries: [entry],
                rank: Number(item.rank ?? Infinity)
            };
            groups.set(groupKey, group);
        } else {
            group.surfaces.push(item);
            group.entries.push(entry);
            const r = Number(item.rank ?? Infinity);
            if (r < group.rank) {
                group.rank = r;
                group.primaryEntry = entry;
            }
        }
    }
    const result = Array.from(groups.values());
    result.sort((a, b) => a.rank - b.rank);
    return result.map(g => {
        const primary = g.primaryEntry;
        const otherSurfaces = g.surfaces.filter(s => s !== primary.item);
        return {
            ...primary,
            item: primary.item,
            category: 'cognate',
            extraSurfaces: otherSurfaces,
            allWords: g.surfaces.map(s => s.word).join(' '),
            cognateGroup: g
        };
    });
}

function cognatePairHtml(item, extraSurfaces = []) {
    const choice = cognateEnglish(item);
    const eq = choice.obvious ? '' : ' hidden';
    const gloss = choice.obvious ? '' : ' is-gloss';
    const isFlipped = Boolean(g().isFlipped);
    const extraCount = extraSurfaces.length;
    const badge = extraCount > 0
        ? `<button type="button" class="cognate-extra-count" data-extra-toggle="true" title="Show all ${extraCount + 1} forms of this word">+${extraCount}</button>`
        : '';
    const chipsHtml = extraCount > 0
        ? `<div class="cognate-folded-chips" hidden>
            ${extraSurfaces.map(s => `<button type="button" class="cognate-folded-chip extras-open-card" data-card-id="${escapeHtml(s.id || '')}">${escapeHtml(s.word)}</button>`).join('')}
          </div>`
        : '';

    if (isFlipped) {
        return `<span class="cognate-pair cognate-pair--flipped">
            <strong class="cognate-pair-known extras-translation-slot${gloss}">${escapeHtml(choice.word)}</strong>
            <span class="cognate-pair-eq"${eq} aria-hidden="true">=</span>
            <button type="button" class="extras-open-card cognate-pair-surface" data-card-id="${escapeHtml(item.id || '')}" aria-label="View ${escapeHtml(item.word)} card">${escapeHtml(item.word)}</button>
            ${badge}
            ${chipsHtml}
        </span>`;
    }
    return `<span class="cognate-pair">
        <button type="button" class="extras-open-card cognate-pair-surface" data-card-id="${escapeHtml(item.id || '')}" aria-label="View ${escapeHtml(item.word)} card">${escapeHtml(item.word)}</button>
        ${badge}
        <span class="cognate-pair-eq"${eq} aria-hidden="true">=</span>
        <strong class="cognate-pair-known extras-translation-slot${gloss}">${escapeHtml(choice.word)}</strong>
        ${chipsHtml}
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
    if (!entries || entries.length === 0) return '';
    return entries.map(entry => {
        const item = entry.item || entry;
        const mergedInto = entry.mergedInto;
        const category = entry.category;
        const reason = entry.reason;
        const extraSurfaces = entry.extraSurfaces || [];
        const itemKind = category || kind || 'cognate';
        const translation = firstTranslation(item);
        const shortTranslation = shortGloss(translation);
        const lemma = itemKind === 'lemma' ? lemmaDisplayOf(item, mergedInto) : null;
        const english = itemKind === 'cognate' ? cognateEnglish(item).word : '';
        const note = reason || (itemKind === 'cognate' ? `${cognateNote(item)} ${english}` : itemKind === 'lemma' ? `${lemma.word} ${lemma.translation}` : '');
        const badgeLabel = itemKind === 'cognate' ? 'Cognate'
            : itemKind === 'grammar' ? 'Grammar & Clitic'
            : itemKind === 'slang' ? 'Slang & Filler'
            : itemKind === 'entity' ? 'Named Entity'
            : itemKind === 'lemma' ? 'Merged' : 'Skipped';

        const wordsToSearch = entry.allWords || item.word;

        return `<li class="extras-row extras-row--${itemKind}" data-extras-id="${escapeHtml(item.id || '')}" data-category="${escapeHtml(itemKind)}" data-search-text="${escapeHtml(`${wordsToSearch} ${translation} ${note} ${badgeLabel}`.toLocaleLowerCase())}">
            ${itemKind === 'lemma'
                ? `<span class="extras-base"><strong>${escapeHtml(lemma.word)}</strong><small class="extras-translation-slot">${escapeHtml(shortGloss(lemma.translation))}</small></span>`
                : ''}
            ${itemKind === 'cognate'
                ? cognatePairHtml(item, extraSurfaces)
                : `<span class="extras-word-stack"><button type="button" class="extras-open-card" data-card-id="${escapeHtml(item.id || '')}" aria-label="View ${escapeHtml(item.word)} card">${escapeHtml(item.word)}</button><span class="extras-translation">${escapeHtml(shortTranslation)}</span></span>`}
            <div class="extras-row-actions">
                <span class="extras-badge extras-badge--${itemKind}">${escapeHtml(badgeLabel)}</span>
            </div>
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

// The setup screen loads the *skinny* index — id, word, rank, surface_card_id,
// lemma and nothing else — so `firstTranslation` has nothing to read and every
// row in this list came out with a blank English column.
function hydrateExtrasTranslations(listEl, entries) {
    if (!listEl) return;
    const pending = new Map();
    for (const entry of entries) {
        const item = entry.item || entry.host || entry;
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
        request(rows.slice(0, 100));
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

// ---------------------------------------------------------------- Smart Skip
//
// The Smart Skip page's word list. One menu picks what to look at; the list
// runs in rank order with a row wherever the level changes, and each of those
// rows studies that level alone. There is deliberately no "study everything":
// a whole category can run to thousands of cards.
//
// Rows are one line each and never carry controls of their own. Tapping one
// opens a quick preview (openSmartSkipPreview); the full card is one tap past
// that, and leaving it comes back to this exact spot.

const SKIP_KINDS = [
    { id: 'cognate', menu: 'Look-alikes', tag: 'look-alike', why: 'Look-alike' },
    { id: 'grammar', menu: 'Pronouns & particles', tag: 'grammar', why: 'Pronoun or particle' },
    { id: 'slang', menu: 'Slang & fillers', tag: 'slang', why: 'Slang or filler' },
    { id: 'entity', menu: 'Names & places', tag: 'name', why: 'Name or place' },
];
const KIND_BY_ID = Object.fromEntries(SKIP_KINDS.map(kind => [kind.id, kind]));
const PAGE_CHUNK = 80;

let _activeSkippedCategory = 'all';
let _ssQuery = '';
let _ssItems = [];          // flat display list: level dividers and rows
let _ssRows = [];           // row payloads, indexed by data-ss-row
let _ssLevels = [];         // level payloads, indexed by data-ss-level
let _ssRendered = 0;
let _ssObserver = null;
let _ssSignature = '';

function skipEntriesFor(extras, category) {
    if (category === 'all') return extras.allSkipped || [];
    return extras.byCategory?.[category] || [];
}

function smartSkipMenu(extras) {
    const skips = SKIP_KINDS
        .map(kind => ({ ...kind, count: skipEntriesFor(extras, kind.id).length }))
        .filter(kind => kind.count > 0);
    const options = [];
    // "All" only earns its place when there is more than one thing to mix.
    if (skips.length > 1) {
        options.push({ id: 'all', label: `All skipped (${(extras.allSkipped || []).length.toLocaleString()})` });
    }
    skips.forEach(kind => options.push({ id: kind.id, label: `${kind.menu} (${kind.count.toLocaleString()})` }));
    const combined = groupMergedLemmas(extras.lemmas || []);
    if (combined.length) {
        options.push({ id: 'lemma', label: `Combined forms (${combined.length.toLocaleString()} cards)` });
    }
    return { options, combined };
}

function entryMatches(entry, needle) {
    if (!needle) return true;
    if (entry.group) {
        const words = entry.group.surfaces.map(item => item.word).join(' ');
        return `${entry.group.lemma.word} ${entry.group.lemma.translation} ${words}`
            .toLocaleLowerCase().includes(needle);
    }
    const item = entry.item || entry;
    return `${item.word} ${firstTranslation(item)}`.toLocaleLowerCase().includes(needle);
}

function levelLabel(range, index) {
    return range ? `Level ${index + 1}` : 'Other words';
}

// Level groups are cut from the unfolded entries, so each divider's count is
// exactly what "Study these" loads. Look-alikes are folded only for display.
function buildSmartSkipItems(extras, category, combined, needle) {
    const ranges = g().getActiveLevelRanges?.() || [];
    const isLemma = category === 'lemma';
    const source = isLemma
        ? combined.map(group => ({ item: group.host, group }))
        : skipEntriesFor(extras, category);
    const matched = source.filter(entry => entryMatches(entry, needle));
    const items = [];
    const rows = [];
    const levels = [];
    for (const { range, index, entries } of skippedByLevel(matched, ranges)) {
        const levelIndex = levels.length;
        levels.push({ range, index, label: levelLabel(range, index), entries, category });
        items.push({ type: 'level', levelIndex });
        let display;
        if (isLemma) {
            display = entries.map(entry => ({ kind: 'lemma', item: entry.item, group: entry.group }));
        } else {
            const cognates = groupCognatesByLemmaAndEnglish(entries.filter(entry => entry.category === 'cognate'))
                .map(entry => ({ kind: 'cognate', item: entry.item, extra: entry.extraSurfaces || [] }));
            const others = entries.filter(entry => entry.category !== 'cognate')
                .map(entry => ({ kind: entry.category, item: entry.item, extra: [] }));
            display = [...cognates, ...others]
                .sort((a, b) => Number(a.item.rank ?? Infinity) - Number(b.item.rank ?? Infinity));
        }
        for (const row of display) {
            row.levelIndex = levelIndex;
            items.push({ type: 'row', rowIndex: rows.length });
            rows.push(row);
        }
    }
    return { items, rows, levels };
}

function smartSkipRowHtml(row, index, showTag) {
    const item = row.item;
    const id = escapeHtml(item.id || '');
    if (row.kind === 'lemma') {
        const lemma = row.group.lemma;
        const forms = row.group.surfaces.map(surface => escapeHtml(surface.word)).join(' · ');
        return `<li><button type="button" class="smart-skip-row smart-skip-row--lemma" data-ss-row="${index}" data-extras-id="${id}">
            <span class="smart-skip-w">${escapeHtml(lemma.word)}</span>
            <span class="smart-skip-g extras-translation-slot">${escapeHtml(shortGloss(lemma.translation))}</span>
            <span class="smart-skip-forms">${forms}</span>
        </button></li>`;
    }
    const tag = showTag ? escapeHtml(KIND_BY_ID[row.kind]?.tag || '') : '';
    const more = row.extra.length ? `<span class="smart-skip-more">+${row.extra.length}</span>` : '';
    let gloss;
    if (row.kind === 'cognate') {
        const choice = cognateEnglish(item);
        gloss = `<span class="smart-skip-g"><span class="cognate-pair-eq"${choice.obvious ? '' : ' hidden'} aria-hidden="true">=</span><span class="cognate-pair-known${choice.obvious ? '' : ' is-gloss'}">${escapeHtml(choice.word)}</span></span>`;
    } else {
        gloss = `<span class="smart-skip-g is-gloss extras-translation-slot">${escapeHtml(shortGloss(firstTranslation(item)))}</span>`;
    }
    return `<li><button type="button" class="smart-skip-row extras-row--${escapeHtml(row.kind)}" data-ss-row="${index}" data-extras-id="${id}">
        <span class="smart-skip-w">${escapeHtml(item.word)}${more}</span>
        ${gloss}
        <span class="smart-skip-tag">${tag}</span>
    </button></li>`;
}

// Each level is its own group so its sticky header is pushed off by the
// next one instead of staying stuck above it.
function smartSkipLevelHtml(level, index) {
    const isLemma = level.category === 'lemma';
    const count = level.entries.length;
    const unit = isLemma ? (count === 1 ? 'card' : 'cards') : (count === 1 ? 'word' : 'words');
    const study = isLemma ? ''
        : (window.isAuditAccount?.()
            // Admin only for now: loading a skipped level as a set confused
            // learners more than it helped.
            ? `<button type="button" class="smart-skip-study" data-ss-level="${index}">Study these</button>` : '');
    return `<li class="smart-skip-group" data-ss-group="${index}">
        <div class="smart-skip-level"><b>${escapeHtml(level.label)}</b><span>${count.toLocaleString()} ${unit}</span>${study}</div>
        <ul class="smart-skip-group-rows"></ul>
    </li>`;
}

function smartSkipScroller() {
    return document.querySelector('#fastModeModal > .modal-content');
}

function appendSmartSkipChunk(list) {
    if (!list || _ssRendered >= _ssItems.length) return;
    const chunk = _ssItems.slice(_ssRendered, _ssRendered + PAGE_CHUNK);
    _ssRendered += chunk.length;
    const showTag = _activeSkippedCategory === 'all';
    const sentinel = list.querySelector(':scope > .smart-skip-sentinel');
    let rows = null;
    let pending = '';
    const flush = () => {
        if (rows && pending) rows.insertAdjacentHTML('beforeend', pending);
        pending = '';
    };
    for (const entry of chunk) {
        if (entry.type === 'level') {
            flush();
            sentinel.insertAdjacentHTML('beforebegin', smartSkipLevelHtml(_ssLevels[entry.levelIndex], entry.levelIndex));
            rows = list.querySelector(`[data-ss-group="${entry.levelIndex}"] > .smart-skip-group-rows`);
        } else {
            if (!rows) {
                const row = _ssRows[entry.rowIndex];
                rows = list.querySelector(`[data-ss-group="${row.levelIndex}"] > .smart-skip-group-rows`);
            }
            pending += smartSkipRowHtml(_ssRows[entry.rowIndex], entry.rowIndex, showTag);
        }
    }
    flush();
    hydrateExtrasTranslations(list, chunk.filter(entry => entry.type === 'row')
        .map(entry => ({ item: _ssRows[entry.rowIndex].item })));
    if (_ssRendered >= _ssItems.length) sentinel?.remove();
}

// Re-rendering resets the list, so it happens only when what the list shows
// has changed. fast-mode.js refreshes on every toggle and mutation.
function renderSkippedWords(filterCategory = _activeSkippedCategory, { force = false } = {}) {
    const extras = collectExtras();
    const body = document.getElementById('skippedWordsBody');
    const select = document.getElementById('skippedCategorySelect');
    if (!body) return extras.cognates;

    const { options, combined } = smartSkipMenu(extras);
    const category = options.some(option => option.id === filterCategory)
        ? filterCategory
        : (options[0]?.id || 'all');
    const needle = _ssQuery.trim().toLocaleLowerCase();
    const signature = JSON.stringify([
        g().selectedLanguage, Boolean(g().activeArtist), category, needle, extras.ready,
        options.map(option => option.label), (g().getActiveLevelRanges?.() || []).length,
    ]);
    if (!force && signature === _ssSignature) return extras.cognates;
    _ssSignature = signature;
    _activeSkippedCategory = category;

    if (select) {
        select.innerHTML = options.map(option =>
            `<option value="${escapeHtml(option.id)}"${option.id === category ? ' selected' : ''}>${escapeHtml(option.label)}</option>`
        ).join('');
        select.closest('.smart-skip-toolbar')?.toggleAttribute('hidden', options.length === 0);
    }
    _ssObserver?.disconnect();
    _ssObserver = null;

    if (!options.length) {
        _ssItems = []; _ssRows = []; _ssLevels = [];
        body.innerHTML = extras.ready
            ? '<p class="smart-skip-empty">Nothing is skipped, so every word is in your sets.</p>'
            : '';
        return extras.cognates;
    }

    ({ items: _ssItems, rows: _ssRows, levels: _ssLevels } = buildSmartSkipItems(extras, category, combined, needle));
    if (!_ssItems.length) {
        body.innerHTML = `<p class="smart-skip-empty">No matches for “${escapeHtml(_ssQuery.trim())}”.</p>`;
        return extras.cognates;
    }
    body.innerHTML = '<ul class="smart-skip-list" id="extrasRowsList"><li class="smart-skip-sentinel" aria-hidden="true"></li></ul>';
    const list = body.querySelector('.smart-skip-list');
    _ssRendered = 0;
    appendSmartSkipChunk(list);
    const sentinel = list.querySelector('.smart-skip-sentinel');
    if (sentinel && typeof IntersectionObserver === 'function') {
        _ssObserver = new IntersectionObserver(records => {
            if (records.some(record => record.isIntersecting)) appendSmartSkipChunk(list);
        }, { root: smartSkipScroller(), rootMargin: '400px' });
        _ssObserver.observe(sentinel);
    } else {
        while (_ssRendered < _ssItems.length) appendSmartSkipChunk(list);
    }
    return extras.cognates;
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

// One level of one category becomes a deck. Progress stays on each original
// card id, so studying here and in the main sets is the same progress.
async function startFastTrackSkippedSet(kind, start, levelIndex = 0, ranges = []) {
    const extras = collectExtras();
    const entries = skipEntriesFor(extras, kind);
    const level = skippedByLevel(entries, ranges).find(group => group.index === Number(levelIndex));
    const slice = (level?.entries || []).map(({ item }) => item);
    if (!slice.length || !g().loadVocabularyData) return;
    const what = kind === 'all' ? 'skipped words' : (KIND_BY_ID[kind]?.menu || 'Skipped words').toLocaleLowerCase();
    const levelLabelText = levelLabel(level.range, level.index);
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.style.display = 'block';
        loadingMessage.textContent = `Loading ${levelLabelText}: ${what}…`;
    }
    window.showAppLoading?.(`Loading ${levelLabelText}: ${what}`, 'Preparing Smart Skip cards…');
    closeSmartSkipPreview();
    document.getElementById('fastModeModal')?.classList.add('hidden');
    try {
        await g().loadVocabularyData('1-50000', {
            rankBasis: 'source',
            studyMode: 'all',
            fastTrackCards: slice,
            setNumber: 1,
            levelSetCount: 1,
            levelNumber: null,
            setLabel: `${levelLabelText} · ${slice.length} ${what}`,
            isFastTrack: true,
        });
    } finally {
        window.hideAppLoading?.();
        if (loadingMessage) loadingMessage.style.display = 'none';
    }
}

// ---------------------------------------------------------------- preview

let _ssPreviewRow = null;
let _ssPreviewToken = 0;

function markWord(sentence, word) {
    const safe = escapeHtml(sentence);
    const target = escapeHtml(word).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (!target) return safe;
    return safe.replace(new RegExp(`(^|[^\\p{L}])(${target})(?![\\p{L}])`, 'iu'), '$1<mark>$2</mark>');
}

// The setup screen holds the skinny index, so both the gloss and the example
// may need fetching. popupFoundWord reads the same two sources.
async function previewExample(item) {
    const langConfig = g().config?.languages?.[g().selectedLanguage] || {};
    const rank = Number(item.rank) || 1;
    if (!firstTranslation(item) && g().ensureIndexRowsForRange) {
        try { await g().ensureIndexRowsForRange(langConfig, rank, rank + 1, [rank]); } catch (_) {}
    }
    if (langConfig.examplesPath && g().ensureExamplesForRange) {
        try { await g().ensureExamplesForRange(langConfig, rank, rank + 1); } catch (_) {}
    }
    const stored = g()._cachedExamplesData?.[item.id];
    const targetField = langConfig.exampleTargetField || 'example_spanish';
    const englishField = langConfig.exampleEnglishField || 'example_english';
    const meanings = item.meanings || [];
    for (let i = 0; i < meanings.length; i++) {
        const meaning = meanings[i];
        const examples = meaning.examples?.length ? meaning.examples : (stored?.m?.[meaning._masterSenseIndex ?? i] || []);
        const example = g().getExampleFromMeaning?.({ ...meaning, examples }, targetField, englishField);
        if (example?.targetSentence) return example;
    }
    return null;
}

function paintPreviewGloss(row) {
    const gloss = document.getElementById('smartSkipPreviewGloss');
    if (!gloss) return;
    if (row.kind === 'cognate') {
        const choice = cognateEnglish(row.item);
        gloss.textContent = choice.obvious ? `= ${choice.word}` : choice.word;
    } else if (row.kind === 'lemma') {
        gloss.textContent = shortGloss(row.group.lemma.translation || firstTranslation(row.item));
    } else {
        gloss.textContent = shortGloss(firstTranslation(row.item));
    }
}

async function openSmartSkipPreview(rowIndex) {
    const row = _ssRows[rowIndex];
    const modal = document.getElementById('smartSkipPreview');
    if (!row || !modal) return;
    _ssPreviewRow = row;
    const token = ++_ssPreviewToken;
    const level = _ssLevels[row.levelIndex];
    const why = row.kind === 'lemma' ? 'Combined forms' : (KIND_BY_ID[row.kind]?.why || 'Skipped');
    const word = row.kind === 'lemma' ? row.group.lemma.word : row.item.word;
    document.getElementById('smartSkipPreviewWhy').textContent = level ? `${why} · ${level.label}` : why;
    document.getElementById('smartSkipPreviewWord').textContent = word;
    paintPreviewGloss(row);
    const forms = document.getElementById('smartSkipPreviewForms');
    const others = row.kind === 'lemma'
        ? row.group.surfaces.map(surface => surface.word).filter(surface => surface !== word)
        : row.extra.map(surface => surface.word);
    forms.textContent = others.length
        ? `${row.kind === 'lemma' ? 'On this card' : 'Also'}: ${others.join(' · ')}`
        : '';
    forms.hidden = !others.length;
    const exampleBox = document.getElementById('smartSkipPreviewExample');
    exampleBox.hidden = true;
    modal.hidden = false;
    modal.querySelector('.smart-skip-preview-card')?.focus();

    const example = await previewExample(row.item);
    if (token !== _ssPreviewToken || modal.hidden) return;
    paintPreviewGloss(row);
    if (example) {
        document.getElementById('smartSkipPreviewTarget').innerHTML = markWord(example.targetSentence, row.item.word);
        document.getElementById('smartSkipPreviewEnglish').textContent = example.englishSentence || '';
        exampleBox.hidden = false;
    }
}

function closeSmartSkipPreview() {
    const modal = document.getElementById('smartSkipPreview');
    if (modal) modal.hidden = true;
    _ssPreviewRow = null;
    _ssPreviewToken++;
}

// The page is only hidden while the card is up, so everything on it -- menu,
// search, rendered rows -- is still there to come back to. Only the scroll
// position is lost with display:none, so it is carried across by hand.
async function openSmartSkipCard() {
    const row = _ssPreviewRow;
    const id = row?.item?.id;
    if (!id || !g().popupFoundWord) return;
    const page = document.getElementById('fastModeModal');
    const scroller = smartSkipScroller();
    const scrollTop = scroller?.scrollTop || 0;
    closeSmartSkipPreview();
    page?.classList.add('hidden');
    const comeBack = () => {
        page?.classList.remove('hidden');
        requestAnimationFrame(() => { if (scroller) scroller.scrollTop = scrollTop; });
    };
    try {
        await g().popupFoundWord({ id }, { reopenSearchOnBack: false, startFlipped: true, onClose: comeBack, returnLabel: 'Smart Skip' });
    } catch (error) {
        console.error('Could not open the card', error);
        comeBack();
    }
}

function renderExtras() {
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
        : `<p class="extras-empty">Nothing is being skipped. Every word is its own card.</p>`;
    body.querySelectorAll('.extras-list').forEach((list, index) => {
        hydrateExtrasTranslations(list, index === 0 && cognates.length ? cognates : lemmas);
    });
    return { cognates, lemmas };
}

// A switched-on shortcut that matched nothing says so under its row. The
// three states stay apart: nothing loaded yet (say nothing), the shortcut is
// off (say nothing), and on but empty (say exactly that). The counts
// themselves sit on each shortcut's row, written by fast-mode.js.
function applyNoneLine(none, { active, ready, count, text }) {
    if (!none) return;
    const empty = active && ready && count === 0;
    none.hidden = !empty;
    if (empty) none.textContent = text;
}

function refreshExtrasButtons() {
    const { cognates, lemmas, ready } = collectExtras();
    applyNoneLine(document.getElementById('lemmaNoneLine'), {
        active: Boolean(g().useLemmaMode && g().lemmaFieldAvailable),
        ready,
        count: lemmas.length,
        text: 'No forms share a word here, so nothing was combined.',
    });
    applyNoneLine(document.getElementById('cognateNoneLine'), {
        active: Boolean(g().excludeCognates && g().cognateFieldAvailable),
        ready,
        count: cognates.length,
        text: 'No word in this deck was close enough to skip.',
    });
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
            ? 'See skipped words'
            : total === 1 ? 'See 1 skipped word' : `See ${total} skipped words`;
    }
    window.renderSetupExtrasSection?.();
}

function filterList(bodyId, query) {
    const needle = String(query || '').trim().toLocaleLowerCase();
    document.querySelectorAll(`#${bodyId} .extras-row, #${bodyId} .lemma-group-row`).forEach(row => {
        row.hidden = Boolean(needle) && !String(row.dataset.searchText || '').includes(needle);
    });
}

function filterSkippedWords(query) {
    _ssQuery = String(query || '');
    renderSkippedWords(_activeSkippedCategory);
}

function filterExtras(query) {
    filterList('extrasBody', query);
}

function openMergedForms() {
    openSkippedWords('lemma');
}

// The word lists live on the Smart Skip page now. Opening one opens the page
// with the menu already on that category.
function openSkippedWords(initialCategory = 'all') {
    _ssQuery = '';
    const search = document.getElementById('skippedWordsSearch');
    if (search) search.value = '';
    _activeSkippedCategory = initialCategory;
    if (g().openFastModePage) g().openFastModePage({ section: 'decks' });
    renderSkippedWords(initialCategory, { force: true });
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
        renderSkippedWords();
        renderExtras();
        refreshExtrasButtons();
    }, 0);
}

function initExtras() {
    document.getElementById('skippedWordsSearch')?.addEventListener('input', event => filterSkippedWords(event.currentTarget.value));
    document.getElementById('skippedCategorySelect')?.addEventListener('change', event => {
        closeSmartSkipPreview();
        renderSkippedWords(event.target.value);
    });
    document.getElementById('skippedWordsBody')?.addEventListener('click', event => {
        const study = event.target.closest('.smart-skip-study');
        if (study) {
            const level = _ssLevels[Number(study.dataset.ssLevel)];
            if (level) startFastTrackSkippedSet(level.category, 0, level.index, g().getActiveLevelRanges?.() || []);
            return;
        }
        const row = event.target.closest('.smart-skip-row');
        if (row) openSmartSkipPreview(Number(row.dataset.ssRow));
    });
    document.getElementById('smartSkipPreviewClose')?.addEventListener('click', closeSmartSkipPreview);
    document.getElementById('smartSkipPreviewOpen')?.addEventListener('click', openSmartSkipCard);
    document.getElementById('smartSkipPreview')?.addEventListener('click', event => {
        if (event.target?.id === 'smartSkipPreview') closeSmartSkipPreview();
    });

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
        const extraToggle = event.target.closest('[data-extra-toggle]');
        if (extraToggle) {
            const pair = extraToggle.closest('.cognate-pair');
            const chips = pair?.querySelector('.cognate-folded-chips');
            if (chips) chips.hidden = !chips.hidden;
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

    document.getElementById('extrasBody')?.addEventListener('click', e => handleModalBodyClick(e, closeExtras));

    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            closeExtras();
        }
    });

    document.getElementById('downloadSavedWordsBtn')?.addEventListener('click', downloadSavedWords);

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

// Saved words live in Settings → Your words, under the other word tools,
// rather than in a sheet of their own. Download appears only when there is
// something to download.
function renderSavedWords() {
    const body = document.getElementById('savedWordsBody');
    if (!body) return;
    const items = loadSavedWords();
    const download = document.getElementById('downloadSavedWordsBtn');
    if (download) download.hidden = items.length === 0;
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
    globalThis.showSettingsModalWithTab?.('vocabulary');
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
globalThis.renderSavedWords = renderSavedWords;
globalThis.toggleSavedWord = toggleSavedWord;
globalThis.isWordSaved = isWordSaved;
globalThis.collectExtras = collectExtras;
globalThis.startFastTrackSkippedSet = startFastTrackSkippedSet;
globalThis.renderSkippedWords = renderSkippedWords;
globalThis.closeSmartSkipPreview = closeSmartSkipPreview;
globalThis.isSmartSkipPreviewOpen = () => !document.getElementById('smartSkipPreview')?.hidden;
