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

function grammarExtra(item) {
    const decide = g().isGrammarParticleItem;
    if (!decide) return false;
    return Boolean(g().excludeGrammarParticles && decide(item));
}

function slangExtra(item) {
    const decide = g().isSlangItem;
    if (!decide) return false;
    return Boolean((g().excludeNoise || g().excludeSlang) && decide(item));
}

function entityExtra(item) {
    if (!g().excludeProperNouns) return false;
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

    for (const item of vocab) {
        if (!item || !item.word || item.duplicate) continue;
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
        { id: 'all', label: 'All Skipped', icon: '⚡', count: allSkipped.length, entries: allSkipped, desc: 'All words set aside by active Fast Track shortcuts' },
        { id: 'cognate', label: 'Transparent Cognates', icon: '⚡', count: cognates.length, entries: cognates, desc: 'Words obvious from languages you already know' },
        { id: 'grammar', label: 'Grammar & Clitics', icon: '🧩', count: grammar.length, entries: grammar, desc: 'High-frequency pronouns, clitic particles & functional words' },
        { id: 'slang', label: 'Slang & Fillers', icon: '💬', count: slang.length, entries: slang, desc: 'Urban slang, conversational fillers & interjections' },
        { id: 'entity', label: 'Names & Entities', icon: '📍', count: entities.length, entries: entities, desc: 'Wikipedia-resolved entities, proper nouns & artist names' },
        { id: 'lemma', label: 'Merged Forms', icon: '📚', count: lemmas.length, entries: lemmas, desc: 'Inflections sharing a base dictionary card' },
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
                <button type="button" class="extras-row-mark-known" data-card-id="${escapeHtml(item.id || '')}" title="Mark as known">✓</button>
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

function renderLemmaGroup(group) {
    const rank = Number.isFinite(group.rank) ? String(group.rank) : '';
    const words = group.surfaces.map(item => item.word).join(' ');
    const translation = shortGloss(group.lemma.translation);
    const maxPreview = 4;
    const initialChips = group.surfaces.slice(0, maxPreview).map(item =>
        `<button type="button" class="lemma-group-chip extras-open-card" data-card-id="${escapeHtml(item.id || '')}">${escapeHtml(item.word)}</button>`
    ).join('');
    const extraCount = group.surfaces.length - maxPreview;
    const moreBtn = extraCount > 0
        ? `<button type="button" class="lemma-group-more" data-more-count="${extraCount}">+ ${extraCount}</button>`
        : '';
    const extraChips = extraCount > 0
        ? group.surfaces.slice(maxPreview).map(item =>
            `<button type="button" class="lemma-group-chip extras-open-card" data-card-id="${escapeHtml(item.id || '')}" hidden>${escapeHtml(item.word)}</button>`
          ).join('')
        : '';

    return `<li class="lemma-group-row" data-extras-id="${escapeHtml(group.host?.id || '')}" data-search-text="${escapeHtml(`${group.lemma.word} ${group.lemma.translation} ${words}`.toLocaleLowerCase())}">
        <span class="lemma-group-rank">${escapeHtml(rank)}</span>
        <span class="lemma-group-lemma"><strong>${escapeHtml(group.lemma.word)}</strong><small class="extras-translation-slot">${escapeHtml(translation)}</small></span>
        <span class="lemma-group-forms">${initialChips}${extraChips}${moreBtn}</span>
    </li>`;
}

function renderLemmaRows(groups) {
    if (!groups || groups.length === 0) return '';
    return groups.map(renderLemmaGroup).join('');
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
    return lemmas;
}

let _activeSkippedCategory = 'all';
let _currentDisplayEntries = [];
let _renderedCount = 0;
let _currentSentinelObserver = null;
const PAGE_CHUNK = 60;

async function batchMarkSkippedKnown(entries = []) {
    const list = Array.isArray(entries) ? entries : [];
    if (!list.length) return 0;
    const save = g().saveWordProgress;
    let count = 0;
    for (const entry of list) {
        const item = entry.item || entry;
        if (!item || !item.word) continue;
        const state = g().getSetupLearningState?.(item);
        if (state?.seen && !state?.needsReview) continue; // already known
        if (save) {
            save(item, true);
            count++;
        }
    }
    if (count > 0) {
        window.cacheProgressLocally?.();
        window.bumpProgressEpoch?.();
        window.refreshFastMode?.();
        window.renderFastTrackSkippedDecks?.();
    }
    return count;
}

function appendNextChunk(container, entries, isLemma) {
    if (!container || _renderedCount >= entries.length) return;
    const nextChunk = entries.slice(_renderedCount, _renderedCount + PAGE_CHUNK);
    _renderedCount += nextChunk.length;

    const html = isLemma ? renderLemmaRows(nextChunk) : renderRows(nextChunk);
    const temp = document.createElement('div');
    temp.innerHTML = html;
    const frag = document.createDocumentFragment();
    while (temp.firstChild) frag.appendChild(temp.firstChild);

    const sentinel = container.querySelector('#extrasListSentinel');
    if (sentinel) {
        container.insertBefore(frag, sentinel);
    } else {
        container.appendChild(frag);
    }

    hydrateExtrasTranslations(container, nextChunk);

    if (sentinel) {
        if (_renderedCount >= entries.length) {
            sentinel.remove();
        } else {
            const btn = sentinel.querySelector('.extras-load-more-btn');
            if (btn) btn.textContent = `Load more (${entries.length - _renderedCount} remaining)`;
        }
    }
}

function renderSkippedWords(filterCategory = _activeSkippedCategory) {
    _activeSkippedCategory = filterCategory;
    const extras = collectExtras();
    const body = document.getElementById('skippedWordsBody');
    if (!body) return extras.cognates;
    const total = document.getElementById('skippedWordsTotal');

    // Update shared category dropdown
    const select = document.getElementById('skippedCategorySelect');
    if (select && select.value !== filterCategory) {
        select.value = filterCategory;
    }

    const allCount = extras.allSkipped.length;
    const categories = [
        { id: 'all', label: 'All Skipped', icon: '⚡', count: allCount },
        { id: 'cognate', label: 'Transparent Cognates', icon: '⚡', count: extras.cognates.length },
        { id: 'lemma', label: 'Merged Word Forms', icon: '📚', count: extras.lemmas.length },
        { id: 'grammar', label: 'Grammar & Clitics', icon: '🧩', count: extras.grammar.length },
        { id: 'slang', label: 'Slang & Fillers', icon: '💬', count: extras.slang.length },
        { id: 'entity', label: 'Names & Entities', icon: '📍', count: extras.entities.length },
    ].filter(c => c.id === 'all' || c.count > 0 || c.id === filterCategory);

    // Populate dropdown options with counts
    if (select) {
        select.innerHTML = categories.map(c =>
            `<option value="${escapeHtml(c.id)}"${c.id === filterCategory ? ' selected' : ''}>${c.icon} ${escapeHtml(c.label)} (${c.count.toLocaleString()})</option>`
        ).join('');
    }

    // Resolve entries for selected category
    const isLemma = filterCategory === 'lemma';
    let entries = [];
    if (isLemma) {
        entries = groupMergedLemmas(extras.lemmas);
        const forms = entries.reduce((count, g) => count + g.surfaces.length, 0);
        if (total) total.textContent = `${entries.length.toLocaleString()} words · ${forms.toLocaleString()} forms`;
    } else if (filterCategory === 'cognate') {
        entries = groupCognatesByLemmaAndEnglish(extras.cognates);
        if (total) total.textContent = `${extras.cognates.length.toLocaleString()} words (${entries.length.toLocaleString()} groups)`;
    } else if (filterCategory === 'all') {
        const foldedCognates = groupCognatesByLemmaAndEnglish(extras.cognates);
        entries = [...foldedCognates, ...extras.grammar, ...extras.slang, ...extras.entities];
        entries.sort((a, b) => (Number(a.item?.rank ?? Infinity) - Number(b.item?.rank ?? Infinity)));
        if (total) total.textContent = `${allCount.toLocaleString()} words`;
    } else {
        entries = extras.byCategory?.[filterCategory] || [];
        if (total) total.textContent = `${entries.length.toLocaleString()} words`;
    }

    _currentDisplayEntries = entries;
    _renderedCount = 0;

    if (entries.length === 0) {
        body.innerHTML = `
            <div class="fast-track-triage-tabs" id="skippedCategoryTabs">
                ${categories.map(c => `
                    <button type="button" class="fast-track-triage-tab${c.id === filterCategory ? ' is-active' : ''}" data-cat-id="${escapeHtml(c.id)}">
                        <span>${c.icon} ${escapeHtml(c.label)}</span>
                        <span class="fast-track-tab-count">${c.count}</span>
                    </button>
                `).join('')}
            </div>
            <p class="extras-empty">No words are set aside under ${escapeHtml(filterCategory)}. Every word remains in your deck.</p>
        `;
        return extras.cognates;
    }

    const tabsHtml = `
        <div class="fast-track-triage-tabs" id="skippedCategoryTabs">
            ${categories.map(c => `
                <button type="button" class="fast-track-triage-tab${c.id === filterCategory ? ' is-active' : ''}" data-cat-id="${escapeHtml(c.id)}">
                    <span>${c.icon} ${escapeHtml(c.label)}</span>
                    <span class="fast-track-tab-count">${c.count}</span>
                </button>
            `).join('')}
        </div>
    `;

    const actionsHtml = `
        <div class="fast-track-triage-action-bar">
            <button type="button" class="fast-track-batch-action-btn fast-track-batch-study-btn" id="studyFilteredSkippedBtn">
                ⚡ Study ${escapeHtml(filterCategory === 'all' ? 'All' : filterCategory)} (${entries.length})
            </button>
        </div>
    `;

    const initialChunk = entries.slice(0, PAGE_CHUNK);
    _renderedCount = initialChunk.length;
    const initialHtml = isLemma ? renderLemmaRows(initialChunk) : renderRows(initialChunk);

    const hasMore = _renderedCount < entries.length;
    const sentinelHtml = hasMore
        ? `<li id="extrasListSentinel" class="extras-list-sentinel"><button type="button" class="extras-load-more-btn">Load more (${entries.length - _renderedCount} remaining)</button></li>`
        : '';

    const listTag = isLemma ? 'lemma-group-list' : 'extras-list';
    body.innerHTML = `
        ${tabsHtml}
        ${actionsHtml}
        <ul class="${listTag}" id="extrasRowsList">${initialHtml}${sentinelHtml}</ul>
    `;

    const listEl = body.querySelector('#extrasRowsList');
    hydrateExtrasTranslations(listEl, initialChunk);

    // Infinite scroll observer on sentinel
    if (_currentSentinelObserver) {
        _currentSentinelObserver.disconnect();
        _currentSentinelObserver = null;
    }
    const sentinelEl = body.querySelector('#extrasListSentinel');
    if (sentinelEl && typeof IntersectionObserver === 'function') {
        _currentSentinelObserver = new IntersectionObserver(records => {
            if (records.some(r => r.isIntersecting)) {
                appendNextChunk(listEl, _currentDisplayEntries, isLemma);
            }
        }, { root: body, rootMargin: '300px' });
        _currentSentinelObserver.observe(sentinelEl);
    }
    sentinelEl?.querySelector('.extras-load-more-btn')?.addEventListener('click', () => {
        appendNextChunk(listEl, _currentDisplayEntries, isLemma);
    });

    // Bind tab clicks
    body.querySelectorAll('.fast-track-triage-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            renderSkippedWords(tab.dataset.catId);
        });
    });

    // Bind study button
    body.querySelector('#studyFilteredSkippedBtn')?.addEventListener('click', () => {
        document.getElementById('skippedWordsModal')?.classList.add('hidden');
        startFastTrackSkippedSet(filterCategory);
    });

    // Bind individual mark known buttons
    body.querySelectorAll('.extras-row-mark-known').forEach(button => {
        button.addEventListener('click', async event => {
            event.stopPropagation();
            const cardId = button.dataset.cardId;
            const target = entries.find(e => (e.item?.id || e.id) === cardId);
            const item = target?.item || target;
            if (item && window.saveWordProgress) {
                window.saveWordProgress(item, true);
                window.cacheProgressLocally?.();
                window.bumpProgressEpoch?.();
                button.classList.add('is-marked');
                button.textContent = '✓ Known';
                button.disabled = true;
            }
        });
    });

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

// One deck per level in Speech; category decks in Lyrics. Progress stays on each original card ID.
function renderFastTrackDeck({ cognates = [], lemmas = [] } = {}, { ranges = [], selectedLevel = null, progressForItem = null } = {}) {
    const isArtist = Boolean(g().activeArtist);
    if (!isArtist) {
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

    // Lyrics mode: Category decks
    const extras = collectExtras();
    const categories = (extras.categories || []).filter(c => c.id !== 'lemma' && c.count > 0);
    if (!categories.length) {
        return `<p class="fast-track-study-empty">No words are set aside with these settings. All lyrics vocabulary is in your main sets.</p>`;
    }
    return `<div class="fast-track-level-list">${categories.map(cat => {
        const entries = cat.entries || [];
        const states = entries.map(({ item }) => progressForItem?.(item) || null);
        const seen = states.filter(state => state?.seen).length;
        const review = states.filter(state => state?.needsReview).length;
        const complete = seen === entries.length && review === 0;
        const mark = complete ? ' is-complete' : review ? ' needs-review' : '';
        return `<button type="button" class="fast-track-level-deck${mark}" data-ft-kind="${cat.id}" data-ft-level="0" data-ft-start="0" aria-label="Study ${cat.label}, ${entries.length} skipped words, ${seen} seen">
            <strong>${cat.icon} ${cat.label}</strong>
            <span>${seen}/${entries.length}</span>
        </button>`;
    }).join('')}</div>`;
}

async function startFastTrackSkippedSet(kind, start, levelIndex = 0, ranges = []) {
    const extras = collectExtras();
    let entries = [];
    let label = 'Skipped words';
    if (kind === 'lemma') {
        const level = skippedByLevel(extras.lemmas, ranges).find(group => group.index === Number(levelIndex));
        entries = level?.entries || [];
        label = level?.range ? `Level ${Number(levelIndex) + 1} Merged` : 'Merged words';
    } else if (kind === 'grammar') {
        entries = extras.grammar || [];
        label = 'Grammar & clitics';
    } else if (kind === 'slang') {
        entries = extras.slang || [];
        label = 'Slang & fillers';
    } else if (kind === 'entity') {
        entries = extras.entities || [];
        label = 'Names & entities';
    } else if (kind === 'all') {
        entries = extras.allSkipped || [];
        label = 'All skipped words';
    } else {
        const allEntries = extras.cognates || [];
        if (Number.isFinite(Number(levelIndex)) && ranges && ranges.length) {
            const level = skippedByLevel(allEntries, ranges).find(group => group.index === Number(levelIndex));
            if (level) {
                entries = level.entries || [];
                label = level.range ? `Level ${Number(levelIndex) + 1}` : 'Skipped words';
            } else {
                entries = allEntries;
            }
        } else {
            entries = allEntries;
        }
    }
    const slice = entries.map(({ item }) => item);
    if (!slice.length || !g().loadVocabularyData) return;
    const levelLabel = label;
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
            levelNumber: null,
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
    const needle = String(query || '').trim().toLocaleLowerCase();
    const isLemma = _activeSkippedCategory === 'lemma';
    const listEl = document.getElementById('extrasRowsList');
    if (!listEl) return;
    if (!needle) {
        _renderedCount = 0;
        const initialChunk = _currentDisplayEntries.slice(0, PAGE_CHUNK);
        _renderedCount = initialChunk.length;
        const html = isLemma ? renderLemmaRows(initialChunk) : renderRows(initialChunk);
        const hasMore = _renderedCount < _currentDisplayEntries.length;
        const sentinelHtml = hasMore
            ? `<li id="extrasListSentinel" class="extras-list-sentinel"><button type="button" class="extras-load-more-btn">Load more (${_currentDisplayEntries.length - _renderedCount} remaining)</button></li>`
            : '';
        listEl.innerHTML = html + sentinelHtml;
        hydrateExtrasTranslations(listEl, initialChunk);
        return;
    }
    const matched = _currentDisplayEntries.filter(entry => {
        if (isLemma) {
            const words = entry.surfaces?.map(s => s.word).join(' ') || '';
            const text = `${entry.lemma?.word} ${entry.lemma?.translation} ${words}`.toLocaleLowerCase();
            return text.includes(needle);
        }
        const item = entry.item || entry;
        const translation = firstTranslation(item);
        const allWords = entry.allWords || item.word;
        const text = `${allWords} ${translation} ${entry.reason || ''}`.toLocaleLowerCase();
        return text.includes(needle);
    });
    const chunk = matched.slice(0, PAGE_CHUNK);
    const html = isLemma ? renderLemmaRows(chunk) : renderRows(chunk);
    listEl.innerHTML = html;
    hydrateExtrasTranslations(listEl, chunk);
}

function filterExtras(query) {
    filterList('extrasBody', query);
}

function openMergedForms() {
    openSkippedWords('lemma');
}

function closeMergedForms() {
    document.getElementById('mergedFormsModal')?.classList.add('hidden');
}

function openSkippedWords(initialCategory = 'all') {
    renderSkippedWords(initialCategory);
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

    document.getElementById('viewSkippedWordsBtn')?.addEventListener('click', () => openSkippedWords('cognate'));
    document.getElementById('closeSkippedWordsModal')?.addEventListener('click', closeSkippedWords);
    document.getElementById('skippedWordsModal')?.addEventListener('click', event => {
        if (event.target?.id === 'skippedWordsModal') closeSkippedWords();
    });
    document.getElementById('skippedWordsSearch')?.addEventListener('input', event => filterSkippedWords(event.currentTarget.value));
    document.getElementById('skippedCategorySelect')?.addEventListener('change', event => {
        renderSkippedWords(event.target.value);
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
globalThis.batchMarkSkippedKnown = batchMarkSkippedKnown;