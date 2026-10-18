// Memory tip: how a cognate the map already vouches for turns into its partner
// in a language the learner reads (English, or Polish for a Czech card), told
// as the regular correspondences that get you there.
//
// Two rules keep a tip honest. First, it is offered only for a card the cognate
// map scores as a cognate, and it explains only the English word the map
// matched: spelling alone never decides that two words are partners. Second,
// every step it names is a correspondence from the pair's `tip_rules`
// (config/cognates/<target>-<known>.json): -mente becomes -ly, es- becomes s-,
// f becomes ph. Whatever no rule covers is shown as a small spelling
// difference, never dressed up as a rule.

const KNOWN_NAMES = { en: 'English', pl: 'Polish' };

function knownName(code) {
    return globalThis.knownLanguageLabel?.(code) || KNOWN_NAMES[code] || String(code).toUpperCase();
}

const VOWELS = 'aeiouy';

export function stripAccents(value) {
    return String(value || '').normalize('NFD').replace(/[̀-ͯ]/g, '');
}

function isConsonant(letter) {
    return Boolean(letter) && /[a-z]/.test(letter) && !VOWELS.includes(letter);
}

// A rule written with an accent (French ê -> es) is matched on the word as
// written; any other rule on the word with its accents stripped.
function matchesAt(word, plain, index, text) {
    if (!text) return false;
    const accented = stripAccents(text) !== text;
    return (accented ? word : plain).startsWith(accented ? text : stripAccents(text), index);
}

// --- explaining a pair --------------------------------------------------------
// One alignment of a stem onto an English stem, in which a letter rule moves
// over several letters at once. Rules are almost free, so the cheapest path is
// the one that leaves the fewest letters unexplained.
const COST = { rule: 0.01, free: 0.02, leftover: 1 };

function alignStem(word, plain, english, letterRules, flags) {
    const n = plain.length;
    const m = english.length;
    const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(Infinity));
    const back = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(null));
    dp[0][0] = 0;
    const relax = (i, j, di, dj, cost, step) => {
        const value = dp[i][j] + cost;
        if (value < dp[i + di][j + dj] - 1e-9) {
            dp[i + di][j + dj] = value;
            back[i + di][j + dj] = { i, j, ...step };
        }
    };
    for (let i = 0; i <= n; i++) {
        for (let j = 0; j <= m; j++) {
            if (dp[i][j] === Infinity) continue;
            if (i < n && j < m && plain[i] === english[j]) relax(i, j, 1, 1, 0, { op: 'match' });
            for (const rule of letterRules) {
                const from = stripAccents(rule.from);
                if (i + from.length <= n && matchesAt(word, plain, i, rule.from)
                    && english.startsWith(rule.to, j)) {
                    relax(i, j, from.length, rule.to.length, COST.rule, { op: 'rule', rule });
                }
            }
            if (flags.double && i < n && j + 1 < m && isConsonant(plain[i]) && plain[i] === english[j]
                && english[j + 1] === english[j] && plain[i + 1] !== plain[i]) {
                relax(i, j, 1, 2, COST.free, { op: 'double', rule: flags.double });
            }
            if (flags.single && i + 1 < n && j < m && isConsonant(plain[i]) && plain[i] === plain[i + 1]
                && plain[i] === english[j] && english[j + 1] !== english[j]) {
                relax(i, j, 2, 1, COST.free, { op: 'single', rule: flags.single });
            }
            if (i < n && j < m) relax(i, j, 1, 1, COST.leftover, { op: 'leftover' });
            if (i < n) relax(i, j, 1, 0, COST.leftover, { op: 'leftover' });
            if (j < m) relax(i, j, 0, 1, COST.leftover, { op: 'leftover' });
        }
    }
    const ops = [];
    let i = n;
    let j = m;
    while (i > 0 || j > 0) {
        const step = back[i][j];
        ops.push({ op: step.op, rule: step.rule || null, a: word.slice(step.i, i), b: english.slice(step.j, j) });
        i = step.i;
        j = step.j;
    }
    ops.reverse();
    return { cost: dp[n][m], ops };
}

// Splits the word into an optional start rule, a stem and an optional end
// rule, tries every split the rules allow, and keeps the one that explains the
// most. Returns the pieces in reading order.
function explain(word, english, rules) {
    let plain = stripAccents(word);
    // Rules are matched letter for letter on both spellings, which only lines
    // up when stripping accents removed marks and not whole letters.
    const accentAware = plain.length === word.length;
    if (!accentAware) word = plain;
    const starts = [null];
    const ends = [null];
    const letterRules = [];
    const flags = {};
    for (const rule of rules) {
        const from = stripAccents(rule.from || '');
        const to = String(rule.to || '');
        if (rule.where === 'double') flags.double = rule;
        else if (rule.where === 'single') flags.single = rule;
        else if (rule.where === 'any') {
            if (from && from !== to) letterRules.push({ ...rule, to });
        } else if (rule.where === 'start') {
            if (!matchesAt(word, plain, 0, rule.from) || !english.startsWith(to)) continue;
            if (rule.before === 'consonant' && !isConsonant(plain[from.length])) continue;
            starts.push({ ...rule, to, length: from.length });
        } else if (rule.where === 'end') {
            if (!english.endsWith(to) || plain.length - from.length < 2) continue;
            if (!matchesAt(word, plain, plain.length - from.length, rule.from)) continue;
            // An English word ending in the same letters has nothing dropped.
            if (!to && english.endsWith(from)) continue;
            ends.push({ ...rule, to, length: from.length });
        }
    }

    let best = null;
    for (const start of starts) {
        for (const end of ends) {
            const sourceFrom = start ? start.length : 0;
            let sourceTo = plain.length - (end ? end.length : 0);
            const englishFrom = start ? start.to.length : 0;
            const englishTo = english.length - (end ? end.to.length : 0);
            if (sourceTo - sourceFrom < 2 || englishTo < englishFrom) continue;
            let stemVowel = null;
            if (end?.stem_vowel && plain[sourceTo - 1] === end.stem_vowel
                && english[englishTo - 1] !== end.stem_vowel) {
                stemVowel = { a: word.slice(sourceTo - 1, sourceTo), rule: end };
                sourceTo -= 1;
            }
            const stem = alignStem(
                word.slice(sourceFrom, sourceTo),
                plain.slice(sourceFrom, sourceTo),
                english.slice(englishFrom, englishTo),
                letterRules,
                flags,
            );
            let cost = stem.cost;
            for (const piece of [start, end]) if (piece) cost += piece.free ? COST.free : COST.rule;
            if (stemVowel) cost += COST.free;
            if (!best || cost < best.cost - 1e-9) {
                best = { cost, start, end, stem, stemVowel, sourceFrom, sourceTo };
            }
        }
    }
    const pieces = [];
    if (best.start) pieces.push({ op: best.start.free ? 'free' : 'rule', rule: best.start, a: word.slice(0, best.sourceFrom), b: best.start.to });
    pieces.push(...best.stem.ops);
    if (best.stemVowel) pieces.push({ op: 'stemVowel', rule: best.stemVowel.rule, a: best.stemVowel.a, b: '' });
    if (best.end) {
        pieces.push({ op: best.end.free ? 'free' : 'rule', rule: best.end, a: word.slice(plain.length - best.end.length), b: best.end.to });
    }
    return { pieces, plain, cost: best.cost };
}

// --- turning the pieces into what the sheet shows ------------------------------
function ruleLabel(rule) {
    if (rule.where === 'start') return `${rule.from}- → ${rule.to}-`;
    if (rule.where === 'end') return rule.to ? `-${rule.from} → -${rule.to}` : `drop -${rule.from}`;
    return `${rule.from} → ${rule.to}`;
}

function leftoverText(a, b) {
    if (a && b) return `${a} → ${b}`;
    return a ? `drop ${a}` : `add ${b}`;
}

// Segments line the source up against the English in chunks of one kind
// (same letters, a named rule, a free step, a leftover); rows list each rule
// once, in the order its chunk appears.
function present(pieces, known) {
    const segments = [];
    const rows = [];
    const rowFor = new Map();
    const leftovers = [];
    const addRow = (key, row) => {
        if (!rowFor.has(key)) {
            rowFor.set(key, rows.length);
            rows.push(row);
        }
        return rowFor.get(key);
    };
    for (const piece of pieces) {
        let kind;
        let row = null;
        if (piece.op === 'match') {
            kind = 'same';
        } else if (piece.op === 'leftover') {
            kind = 'leftover';
        } else if (piece.op === 'rule') {
            kind = 'rule';
            row = addRow(`rule:${piece.rule.where}:${piece.rule.from}:${piece.rule.to}`, {
                kind: 'rule',
                label: ruleLabel(piece.rule),
                from: piece.rule.from,
                to: piece.rule.to,
                where: piece.rule.where,
                twins: piece.rule.twins || [],
            });
        } else {
            kind = 'free';
            let label = piece.rule.label;
            if (piece.op === 'stemVowel') label = piece.rule.stem_vowel_label || `Drop the -${piece.a}`;
            if (piece.op === 'double') label = `${known} doubles the ${piece.a}`;
            if (piece.op === 'single') label = `${known} writes ${piece.a} with one ${piece.b}`;
            row = addRow(`free:${label}`, { kind: 'free', label, twins: [] });
        }
        const last = segments[segments.length - 1];
        if (last && last.kind === kind && (kind === 'same' || kind === 'leftover')) {
            last.a += piece.a;
            last.b += piece.b;
        } else {
            segments.push({ kind, a: piece.a, b: piece.b, row });
        }
    }
    for (const segment of segments) {
        if (segment.kind === 'leftover') leftovers.push(leftoverText(segment.a, segment.b));
    }
    if (leftovers.length) {
        const row = rows.length;
        rows.push({ kind: 'spelling', label: 'Small spelling difference', detail: leftovers.join(', '), twins: [] });
        segments.forEach(segment => { if (segment.kind === 'leftover') segment.row = row; });
    }
    return { segments, rows };
}

function tierOf(plain, english, segments) {
    const left = segments.filter(segment => segment.kind === 'leftover');
    if (plain === english && !left.length) return 'same';
    if (!left.length) return 'pattern';
    const letters = left.reduce((total, segment) => total + Math.max(segment.a.length, segment.b.length), 0);
    return left.length === 1 && letters <= 2 ? 'close' : 'loose';
}

function senseText(partner, card) {
    const meaning = partner.meaning || (card?.meanings || []).find(item =>
        String(item?.translation || item?.meaning || '').toLowerCase().includes(partner.word.toLowerCase()));
    return String(meaning?.translation || meaning?.meaning || '').trim();
}

const TIER_RANK = { same: 0, pattern: 1, close: 2, loose: 3 };

// The tip for one card in one known language, or null.
function tipThrough(card, word, code) {
    const rules = globalThis.cognateTipRules?.(code) || [];
    if (!rules.length) return null;
    const partner = globalThis.cognateTipPartner?.(card, code);
    if (!partner?.word) return null;
    const known = String(partner.word).trim().toLowerCase().normalize('NFC');
    if (!/^\p{L}+$/u.test(known)) return null;

    // An inflected card (abandonaba) may match the partner through the
    // headword its cognate sense belongs to (abandonar -> abandon), or the
    // partner may be the same inflection (bloků -> bloku). Both are tried and
    // the one the rules explain best is shown: the better tier, then the
    // cheaper explanation (fewer unexplained letters, named rules over free
    // steps).
    const headword = String(partner.headword || '').trim().toLowerCase().normalize('NFC');
    const bases = [word];
    if (headword && headword !== word && !/\s/.test(headword)) bases.push(headword);
    let chosen = null;
    for (const base of bases) {
        const { pieces, plain, cost } = explain(base, known, rules);
        const { segments, rows } = present(pieces, knownName(code));
        const tier = tierOf(plain, known, segments);
        if (!chosen || TIER_RANK[tier] < TIER_RANK[chosen.tier]
            || (TIER_RANK[tier] === TIER_RANK[chosen.tier] && cost < chosen.cost - 1e-9)) {
            chosen = { base, plain, segments, rows, tier, cost };
        }
    }
    const { base, segments, rows, tier } = chosen;
    const explained = segments.filter(segment => segment.kind !== 'leftover')
        .reduce((total, segment) => total + segment.b.length, 0);
    // A pair the rules barely touch has nothing to teach, even when it is a
    // cognate: the sheet would be a list of exceptions.
    if (explained / known.length < 0.5) return null;

    const firstRule = rows.find(row => row.kind === 'rule');
    const endRule = rows.find(row => row.kind === 'rule' && row.where === 'end');
    return {
        word,
        base,
        form: base !== word ? base : null,
        english: known,
        known: code,
        knownName: knownName(code),
        sense: senseText(partner, card),
        tier,
        accents: stripAccents(base) !== base,
        segments,
        rows,
        from: endRule ? endRule.from : null,
        to: endRule ? endRule.to : null,
        twins: firstRule ? firstRule.twins : [],
    };
}

// The best tip for one card, or null. The card needs its cognate map fields
// (set by applyCognateScores). Each language the learner reads is tried; the
// most regular explanation wins, and on a tie a language other than English
// does, since the learner chose to read it and it is usually the closer one.
// `language` is the deck's language and is kept for callers; the map already
// belongs to it.
export function memoryTipFor(card, language) {
    const word = String(card?.displaySurface || card?.targetWord || card?.word || '')
        .trim().toLowerCase().normalize('NFC');
    if (word.length < 3 || /\s/.test(word)) return null;
    const codes = globalThis.cognateTipLanguages?.() || ['en'];
    let best = null;
    for (const code of codes) {
        const tip = tipThrough(card, word, code);
        if (!tip) continue;
        if (!best || TIER_RANK[tip.tier] < TIER_RANK[best.tier]
            || (TIER_RANK[tip.tier] === TIER_RANK[best.tier] && best.known === 'en' && tip.known !== 'en')) {
            best = tip;
        }
    }
    return best;
}

const TIER_NAMES = {
    same: 'Same word',
    pattern: 'Regular pattern',
    close: 'Close match',
    loose: 'Loose link',
};

export function memoryTipSentence(tip) {
    if (!tip) return '';
    if (tip.tier === 'same') return `Spelled the same in ${tip.knownName}.`;
    const named = tip.rows.filter(row => row.kind === 'rule').map(row => row.label);
    if (named.length) return `${named.join(', ')}.`;
    return tip.rows.map(row => row.label).join(', ') + '.';
}

export function memoryTipTier(tip) {
    return tip ? TIER_NAMES[tip.tier] || '' : '';
}

if (typeof globalThis !== 'undefined') {
    globalThis.memoryTipFor = memoryTipFor;
    globalThis.memoryTipSentence = memoryTipSentence;
}

// --- Card back tile and sheet ------------------------------------------------
// The tile is built while the card back renders; the tip it was built from is
// kept here so the click handler does not have to find the card again.
let _openTip = null;

function escapeText(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]
    ));
}

export function memoryTipTileHTML(card, language) {
    const tip = memoryTipFor(card, language);
    _openTip = tip;
    if (!tip) return '';
    return `<button type="button" class="headword-memory-tip-btn ref-memory-tip-btn" aria-label="Memory tip: ${escapeText(tip.word)} and ${escapeText(tip.knownName)} ${escapeText(tip.english)}" title="Memory tip" onclick="event.stopPropagation(); openMemoryTip(event);">
        <svg class="headword-memory-tip-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M9 18h6"></path><path d="M10 21h4"></path>
            <path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"></path>
        </svg>
    </button>`;
}

function ensureModal() {
    let modal = document.getElementById('memoryTipModal');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'memoryTipModal';
    modal.className = 'knowledge-overview-modal memory-tip-modal';
    modal.hidden = true;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'memoryTipTitle');
    modal.innerHTML = `
        <div class="knowledge-overview-sheet">
            <header class="knowledge-overview-header">
                <div>
                    <span class="knowledge-overview-kicker">Memory tip</span>
                    <h2 id="memoryTipTitle"></h2>
                </div>
                <button type="button" class="knowledge-overview-close" aria-label="Close memory tip" onclick="closeMemoryTip(event)">×</button>
            </header>
            <div class="phrase-summary-scroll" id="memoryTipBody" style="flex:0 1 auto;padding:10px 18px 16px;"></div>
        </div>`;
    modal.addEventListener('click', event => {
        event.stopPropagation();
        if (event.target === modal) closeMemoryTip(event);
    });
    modal.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        event.stopPropagation();
        closeMemoryTip(event);
    });
    document.body.appendChild(modal);
    return modal;
}

export function closeMemoryTip(event) {
    event?.stopPropagation?.();
    const modal = document.getElementById('memoryTipModal');
    if (modal) modal.hidden = true;
}

// Amber is the language's letters a rule changes, green what English makes of
// them; grey is a free step; a dashed outline is a leftover no rule explains.
const STYLE = `
.memory-tip-modal .mt-flow { display:flex; align-items:center; justify-content:center; flex-wrap:wrap; gap:8px 12px; padding:14px 12px; border-radius:12px; background:rgba(0,0,0,.28); border:1px solid rgba(255,255,255,.1); }
.memory-tip-modal .mt-word { display:inline-flex; align-items:baseline; font-size:1.3rem; font-weight:600; font-family:var(--font-mono, ui-monospace, SFMono-Regular, monospace); }
.memory-tip-modal .mt-seg { padding:1px 1px; border-radius:5px; }
.memory-tip-modal .mt-seg.is-rule.is-src { color:#f0c878; background:rgba(224,178,90,.18); padding:1px 4px; }
.memory-tip-modal .mt-seg.is-rule.is-en { color:#7fe0a6; background:rgba(94,201,138,.18); padding:1px 4px; }
.memory-tip-modal .mt-seg.is-free { color:rgba(255,255,255,.55); background:rgba(255,255,255,.08); padding:1px 4px; }
.memory-tip-modal .mt-seg.is-free.is-src { text-decoration:line-through; text-decoration-color:rgba(255,255,255,.4); }
.memory-tip-modal .mt-seg.is-leftover { outline:1px dashed rgba(255,255,255,.4); outline-offset:-1px; padding:1px 4px; color:rgba(255,255,255,.75); }
.memory-tip-modal .mt-seg.is-empty { display:none; }
.memory-tip-modal .mt-arrow { color:rgba(255,255,255,.45); font-size:1.15rem; }
.memory-tip-modal .mt-hint { text-align:center; font-size:.76rem; opacity:.55; margin-top:6px; }
.memory-tip-modal .mt-rows { list-style:none; margin:14px 0 0; padding:0; display:flex; flex-direction:column; gap:8px; }
.memory-tip-modal .mt-row { display:flex; flex-wrap:wrap; align-items:baseline; gap:4px 12px; font-size:.95rem; }
.memory-tip-modal .mt-rule { font-weight:650; white-space:nowrap; }
.memory-tip-modal .mt-row.is-rule .mt-rule { color:#f0c878; }
.memory-tip-modal .mt-row.is-free .mt-rule { font-weight:500; opacity:.7; }
.memory-tip-modal .mt-row.is-spelling .mt-rule { font-weight:500; opacity:.75; border:1px dashed rgba(255,255,255,.35); border-radius:6px; padding:0 6px; }
.memory-tip-modal .mt-row.is-form .mt-rule { font-weight:500; opacity:.8; }
.memory-tip-modal .mt-twins { font-size:.84rem; opacity:.6; }
.memory-tip-modal .mt-meaning { margin-top:14px; font-size:.86rem; opacity:.7; }
.memory-tip-modal .mt-caution { margin-top:8px; font-size:.84rem; color:#f0c878; opacity:.85; }
`;

function ensureStyles() {
    if (document.getElementById('memoryTipStyles')) return;
    const style = document.createElement('style');
    style.id = 'memoryTipStyles';
    style.textContent = STYLE;
    document.head.appendChild(style);
}

function wordHTML(tip, side) {
    const key = side === 'src' ? 'a' : 'b';
    return tip.segments.map(segment => {
        const text = segment[key];
        if (!text) return '';
        const cls = segment.kind === 'same' ? '' : `is-${segment.kind} is-${side}`;
        return `<span class="mt-seg ${cls}">${escapeText(text)}</span>`;
    }).join('');
}

function rowHTML(row) {
    const label = row.kind === 'spelling'
        ? `${escapeText(row.label)}: ${escapeText(row.detail)}`
        : escapeText(row.label);
    const twins = row.twins?.length
        ? `<span class="mt-twins">like ${row.twins.map(escapeText).join(', ')}</span>`
        : '';
    return `<li class="mt-row is-${escapeText(row.kind)}"><span class="mt-rule">${label}</span>${twins}</li>`;
}

export function openMemoryTip(event) {
    event?.stopPropagation?.();
    const tip = _openTip;
    if (!tip) return;
    ensureStyles();
    const modal = ensureModal();
    modal.querySelector('#memoryTipTitle').textContent = `${tip.word} → ${tip.english}`;
    modal.querySelector('.knowledge-overview-kicker').textContent = tip.known === 'en'
        ? 'Memory tip'
        : `Memory tip · ${tip.knownName}`;

    const rows = [];
    if (tip.form) rows.push({ kind: 'form', label: `A form of ${tip.form}`, twins: [] });
    if (tip.tier === 'same') rows.push({ kind: 'free', label: `Same word in ${tip.knownName}`, twins: [] });
    rows.push(...tip.rows);
    const hint = tip.accents ? '<div class="mt-hint">accents ignored</div>' : '';
    const sense = tip.sense ? `<div class="mt-meaning">Meaning: “${escapeText(tip.sense)}”</div>` : '';
    const caution = tip.tier === 'loose'
        ? '<div class="mt-caution">Several letters differ, so treat this as a loose link.</div>'
        : '';

    modal.querySelector('#memoryTipBody').innerHTML = `
        <div class="mt-flow" aria-hidden="true">
            <span class="mt-word">${wordHTML(tip, 'src')}</span>
            <span class="mt-arrow">→</span>
            <span class="mt-word">${wordHTML(tip, 'en')}</span>
        </div>
        ${hint}
        <ul class="mt-rows">${rows.map(rowHTML).join('')}</ul>
        ${sense}
        ${caution}
    `;
    modal.hidden = false;
    modal.querySelector('.knowledge-overview-close')?.focus();
}

if (typeof window !== 'undefined') {
    window.openMemoryTip = openMemoryTip;
    window.closeMemoryTip = closeMemoryTip;
}
