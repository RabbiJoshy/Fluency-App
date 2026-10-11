// Memory tip: a step-by-step, deterministic link from a deck word to English.
//
// For every English word in the card's own glosses we ask one question: how few
// plain edits turn the deck word into it? The answer is a chain of named steps
// (drop the accent, -ción becomes -tion, swap one letter ...) so the learner
// sees the link instead of being told "these are cognates".
//
// There is no single bar a pair has to clear. Each match carries a tier and the
// sheet says which one it is, so a loose link is offered as loose rather than
// withheld. Meaning is never inferred from spelling: the English word is always
// one the card itself already glosses, and the tip names the sense it came from.

const LANGUAGE_KEY = {
    spanish: 'spanish', es: 'spanish',
    portuguese: 'portuguese', portuguese_brazilian: 'portuguese', pt: 'portuguese',
    french: 'french', fr: 'french',
};

// [target ending, English ending]. Longest first so -ciones is tried before
// -ones. The endings are written with their accents; matching strips them.
const ROMANCE_VERBS = [
    ['ar', 'ate'], ['ar', 'e'], ['ar', ''], ['er', ''], ['er', 'e'], ['ir', ''], ['ir', 'e'],
];
const RULES = {
    spanish: [
        ['idades', 'ities'], ['idad', 'ity'], ['dades', 'ties'], ['dad', 'ty'],
        ['ciones', 'tions'], ['ción', 'tion'], ['siones', 'sions'], ['sión', 'sion'],
        ['mente', 'ly'], ['osos', 'ous'], ['osas', 'ous'], ['oso', 'ous'], ['osa', 'ous'],
        ['ismo', 'ism'], ['ista', 'ist'], ['ivo', 'ive'], ['iva', 'ive'],
        ['ico', 'ic'], ['ica', 'ic'], ['ario', 'ary'], ['aria', 'ary'],
        ['ancia', 'ance'], ['encia', 'ence'], ['ante', 'ant'], ['ente', 'ent'],
        ['able', 'able'], ['ible', 'ible'], ['ura', 'ure'], ['ia', 'y'],
        ['or', 'or'], ['al', 'al'], ['ar', 'ar'], ['o', ''], ['a', ''], ['e', ''],
        ...ROMANCE_VERBS,
    ],
    portuguese: [
        ['idades', 'ities'], ['idade', 'ity'], ['dades', 'ties'], ['dade', 'ty'],
        ['ções', 'tions'], ['ção', 'tion'], ['sões', 'sions'], ['são', 'sion'],
        ['mente', 'ly'], ['osos', 'ous'], ['osas', 'ous'], ['oso', 'ous'], ['osa', 'ous'],
        ['ismo', 'ism'], ['ista', 'ist'], ['ivo', 'ive'], ['iva', 'ive'],
        ['ico', 'ic'], ['ica', 'ic'], ['ário', 'ary'], ['ária', 'ary'],
        ['ância', 'ance'], ['ência', 'ence'], ['ante', 'ant'], ['ente', 'ent'],
        ['ável', 'able'], ['ível', 'ible'], ['ura', 'ure'], ['ia', 'y'],
        ['or', 'or'], ['al', 'al'], ['o', ''], ['a', ''], ['e', ''],
        ...ROMANCE_VERBS,
    ],
    french: [
        ['ités', 'ities'], ['ité', 'ity'], ['tions', 'tions'], ['tion', 'tion'],
        ['sions', 'sions'], ['sion', 'sion'], ['ment', 'ly'],
        ['euses', 'ous'], ['euse', 'ous'], ['eux', 'ous'],
        ['isme', 'ism'], ['iste', 'ist'], ['ique', 'ic'], ['aire', 'ary'],
        ['ance', 'ance'], ['ence', 'ence'], ['ant', 'ant'], ['ent', 'ent'],
        ['able', 'able'], ['ible', 'ible'], ['eur', 'or'], ['ie', 'y'],
        ['er', ''], ['er', 'e'], ['ir', ''], ['ir', 'e'], ['é', 'ed'], ['e', ''],
    ],
};

// Words a gloss line is full of that are never the cognate.
const STOP = new Set([
    'to', 'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'onto', 'your', 'their',
    'someone', 'something', 'oneself', 'one', 'who', 'what', 'when', 'where', 'which',
    'have', 'been', 'being', 'does', 'make', 'used', 'also', 'such', 'than', 'then',
]);

const TIER_COST = { same: 0, pattern: 0.2, close: 0.3, loose: 0.46 };

export function stripAccents(value) {
    return String(value || '').normalize('NFD').replace(/[̀-ͯ]/g, '');
}

// --- alignment ---------------------------------------------------------------
const SOUND_CLASSES = ['bpvf', 'mn', 'tdsz', 'szc', 'ckqgxj', 'lr', 'hgj'];
const VOWELS = 'aeiouy';

function substitutionCost(a, b) {
    if (a === b) return 0;
    const bothVowels = VOWELS.includes(a) && VOWELS.includes(b);
    if ((a === 'y' && b === 'i') || (a === 'i' && b === 'y')) return 0.2;
    if (bothVowels) return 0.45;
    if (SOUND_CLASSES.some(group => group.includes(a) && group.includes(b))) return 0.4;
    return 1;
}

function gapCost(letter, atEnd) {
    return atEnd && VOWELS.includes(letter) ? 0.7 : 1;
}

// Weighted edit alignment of `a` onto `b`, with the cheapest path recovered as
// a list of {op, a, b} where op is match, sub, del (letter of a has no partner)
// or ins (letter of b has no partner).
function align(a, b) {
    const n = a.length;
    const m = b.length;
    const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
    for (let i = 1; i <= n; i++) dp[i][0] = dp[i - 1][0] + gapCost(a[i - 1], i === n);
    for (let j = 1; j <= m; j++) dp[0][j] = dp[0][j - 1] + gapCost(b[j - 1], j === m);
    for (let i = 1; i <= n; i++) {
        for (let j = 1; j <= m; j++) {
            dp[i][j] = Math.min(
                dp[i - 1][j - 1] + substitutionCost(a[i - 1], b[j - 1]),
                dp[i - 1][j] + gapCost(a[i - 1], i === n && j === m),
                dp[i][j - 1] + gapCost(b[j - 1], i === n && j === m),
            );
        }
    }
    const ops = [];
    let i = n;
    let j = m;
    while (i > 0 || j > 0) {
        const here = dp[i][j];
        if (i > 0 && j > 0 && Math.abs(here - (dp[i - 1][j - 1] + substitutionCost(a[i - 1], b[j - 1]))) < 1e-9) {
            ops.push({ op: a[i - 1] === b[j - 1] ? 'match' : 'sub', a: a[i - 1], b: b[j - 1] });
            i--; j--;
        } else if (i > 0 && Math.abs(here - (dp[i - 1][j] + gapCost(a[i - 1], i === n && j === m))) < 1e-9) {
            ops.push({ op: 'del', a: a[i - 1], b: '' });
            i--;
        } else {
            ops.push({ op: 'ins', a: '', b: b[j - 1] });
            j--;
        }
    }
    ops.reverse();
    return { cost: dp[n][m], ops };
}

// --- steps -------------------------------------------------------------------
// A "string" is shown as parts so the changed letters can be highlighted.
function plainParts(text) {
    return text ? [{ t: text, hl: false }] : [];
}

function partsFor(prefix, changed, suffix) {
    const parts = [];
    if (prefix) parts.push({ t: prefix, hl: false });
    if (changed) parts.push({ t: changed, hl: true });
    if (suffix) parts.push({ t: suffix, hl: false });
    return parts;
}

// Groups the non-matching runs of an alignment into one step each, applied left
// to right so every step shows the whole word as it stands after that edit.
function residualSteps(ops) {
    const steps = [];
    const done = [];
    let index = 0;
    while (index < ops.length) {
        if (ops[index].op === 'match') {
            done.push(ops[index].b);
            index++;
            continue;
        }
        const start = index;
        while (index < ops.length && ops[index].op !== 'match') index++;
        const run = ops.slice(start, index);
        const removed = run.map(item => item.a).join('');
        const added = run.map(item => item.b).join('');
        const atEnd = index === ops.length;
        const rest = ops.slice(index).filter(item => item.op !== 'ins').map(item => item.a).join('');
        const prefix = done.join('');
        let kind;
        let label;
        if (!added) {
            kind = 'drop';
            label = atEnd ? `Drop the ending -${removed}` : `Drop the ${removed}`;
        } else if (!removed) {
            kind = 'add';
            label = atEnd ? `English adds -${added}` : `English adds ${added}`;
        } else {
            kind = 'swap';
            label = atEnd && removed.length > 1
                ? `Ending -${removed} becomes -${added}`
                : `${removed} becomes ${added}`;
        }
        steps.push({
            kind,
            label,
            before: null,
            after: partsFor(prefix, added, rest),
            from: removed,
            to: added,
        });
        done.push(added);
    }
    return steps;
}

function ruleNote(from, to) {
    if (from === to) return `The ending -${from} is spelled the same in English.`;
    if (!to) return `English drops the ending -${from}.`;
    return `The ending -${from} becomes -${to} in English.`;
}

// Senses that describe another spelling or an old form of a word are not
// meanings the learner would map onto English.
const NOT_A_MEANING = /\b(spelling|misspelling|alternative|obsolete|archaic|form of|variant|abbreviation)\b/i;

// The words worth comparing are the head of each gloss ("to take", "quickly"),
// not the explanatory tail ("(to move something to a destination)").
function glossWords(meanings) {
    const found = [];
    const seen = new Set();
    (meanings || []).forEach(meaning => {
        const text = String(meaning?.meaning || meaning?.translation || '');
        if (!text || NOT_A_MEANING.test(text)) return;
        const bare = text.replace(/\([^)]*\)/g, ' ');
        for (const clause of bare.split(/[;,/]/)) {
            const words = clause.toLowerCase().split(/[^a-z']+/).filter(Boolean).slice(0, 3);
            for (const piece of words) {
                if (piece.length < 3 || STOP.has(piece) || seen.has(piece)) continue;
                seen.add(piece);
                found.push({ word: piece, sense: text });
            }
        }
    });
    return found;
}

// Cost normalised by the longer word, so a one-letter slip in a 3-letter word
// is not treated like one in a 12-letter word.
function normalised(cost, a, b) {
    return cost / Math.max(a.length, b.length, 1);
}

// `kept` is the share of the English word's letters that line up unchanged. A
// low weighted cost alone lets vowel- and sound-class swaps stack up into a
// word that merely has the same shape (cumplir / come), so a looser tier also
// has to keep most of the English word's letters.
function tierFor(cost, ruleUsed, identical, anchored, kept, keptCount, englishLength) {
    if (identical) return 'same';
    if (ruleUsed && cost <= TIER_COST.pattern) return 'pattern';
    if (cost <= TIER_COST.close && kept >= 0.5) return 'close';
    if (cost <= TIER_COST.loose && anchored && kept >= 0.6 && keptCount >= 3 && englishLength >= 4) return 'loose';
    return null;
}

function evaluate(word, plain, gloss, rules) {
    const english = gloss.word;
    const options = [{ built: plain, rule: null }];
    for (const [from, to] of rules) {
        const stem = stripAccents(from);
        if (plain.endsWith(stem) && plain.length - stem.length >= 2) {
            // A rule only counts when the English word actually wears the
            // ending it names, otherwise it is just a re-spelling.
            if (to && !english.endsWith(to)) continue;
            if (!to && english.length > plain.length - stem.length + 2) continue;
            options.push({ built: plain.slice(0, plain.length - stem.length) + to, rule: { from, to, stem } });
        }
    }
    let best = null;
    for (const option of options) {
        const result = align(option.built, english);
        const cost = normalised(result.cost, option.built, english);
        const ruleBonus = option.rule ? -0.001 : 0;
        const score = cost + ruleBonus;
        if (!best || score < best.score) best = { ...option, result, cost, score };
    }
    const anchored = SOUND_CLASSES.some(g => g.includes(plain[0]) && g.includes(english[0])) || plain[0] === english[0];
    // A gloss that is only the front of the word and no rule explains is a
    // clipped token (protecção / prote), not a partner.
    if (best.cost > 0 && english.length >= 3 && plain.startsWith(english)
        && plain.length - english.length <= 3) return null;
    const keptCount = best.result.ops.filter(item => item.op === 'match').length;
    const kept = keptCount / english.length;
    const tier = tierFor(best.cost, Boolean(best.rule), plain === english, anchored, kept, keptCount, english.length);
    if (!tier) return null;
    return { ...best, tier, english, sense: gloss.sense };
}

// The best tip for one card, or null. `card` needs a headword and `meanings`
// with English text; `language` is the app's language name or code.
export function memoryTipFor(card, language) {
    const key = LANGUAGE_KEY[String(language || '').toLowerCase()];
    if (!key) return null;
    const word = String(card?.displaySurface || card?.targetWord || card?.word || '').trim().toLowerCase();
    if (word.length < 4 || /\s/.test(word)) return null;
    const plain = stripAccents(word);
    // Words that are the deck language's own lemma, never an English partner.
    // The spelling of the card itself is allowed: that is how a same-spelled
    // word (animal, hotel) is recognised.
    const own = new Set();
    for (const value of [card?.lemma, card?.citationForm, card?.representativeSurface]) {
        if (value) own.add(stripAccents(String(value).toLowerCase()));
    }
    for (const meaning of card?.meanings || []) {
        if (meaning?.headword) own.add(stripAccents(String(meaning.headword).toLowerCase()));
    }
    own.delete(plain);
    const glosses = glossWords(card?.meanings).filter(item => !own.has(item.word));
    if (!glosses.length) return null;

    const tierRank = { same: 0, pattern: 1, close: 2, loose: 3 };
    let best = null;
    for (const gloss of glosses) {
        const found = evaluate(word, plain, gloss, RULES[key] || []);
        if (!found) continue;
        if (!best
            || tierRank[found.tier] < tierRank[best.tier]
            || (found.tier === best.tier && found.cost < best.cost)) {
            best = found;
        }
    }
    if (!best) return null;

    const steps = [];
    let current = plain;
    if (plain !== word) {
        const changed = [];
        for (let i = 0; i < word.length; i++) if (word[i] !== plain[i]) changed.push(`${word[i]} → ${plain[i]}`);
        steps.push({
            kind: 'accent',
            label: 'Ignore the accent mark',
            note: 'It only shows stress or length; it does not change the word.',
            after: plainParts(plain),
            from: changed.join(', '),
            to: '',
        });
    }
    if (best.rule) {
        const prefix = plain.slice(0, plain.length - best.rule.stem.length);
        current = prefix + best.rule.to;
        steps.push({
            kind: 'rule',
            label: best.rule.from === best.rule.to
                ? `-${best.rule.from} stays -${best.rule.to}`
                : (best.rule.to ? `-${best.rule.from} becomes -${best.rule.to}` : `Drop -${best.rule.from}`),
            note: ruleNote(best.rule.from, best.rule.to),
            after: partsFor(prefix, best.rule.to, ''),
            from: best.rule.from,
            to: best.rule.to,
        });
    }
    const residual = residualSteps(best.result.ops);
    // -mente is added to the feminine adjective (rápida + mente), and English
    // has no feminine, so the vowel left over is that -a.
    if (best.rule && (best.rule.from === 'mente' || best.rule.from === 'ment')
        && residual[0] && residual[0].kind === 'drop' && residual[0].from === 'a') {
        residual[0].label = 'Drop the feminine -a';
        residual[0].note = 'Adverbs are built on the feminine adjective, which English does not have.';
    }
    steps.push(...residual);

    // The strip shows the whole word against its English partner in columns,
    // independent of how the steps were grouped.
    // A named ending shows as one block (mente -> ly) instead of a run of
    // single letters, because the point is that the ending moves as a unit.
    let columns;
    if (best.rule && best.english.endsWith(best.rule.to)) {
        const englishStem = best.rule.to ? best.english.slice(0, -best.rule.to.length) : best.english;
        columns = align(plain.slice(0, plain.length - best.rule.stem.length), englishStem).ops;
        columns.push({ op: 'rule', a: best.rule.from, b: best.rule.to });
    } else {
        columns = align(plain, best.english).ops;
    }
    return {
        word,
        english: best.english,
        sense: best.sense,
        tier: best.tier,
        steps,
        columns,
        // Kept for callers that only want the named ending shift.
        kind: best.rule ? 'ending' : 'spelling',
        from: best.rule ? best.rule.from : null,
        to: best.rule ? best.rule.to : null,
        unchanged: Boolean(best.rule && best.rule.from === best.rule.to),
    };
}

const TIER_TEXT = {
    same: ['Same word', 'Spelled the same apart from accents.'],
    pattern: ['Regular pattern', 'A standard ending shift. Once you know it, it works on many words.'],
    close: ['Close match', 'A few small letter changes.'],
    loose: ['Loose link', 'Looks alike, but check the meaning: it may only be a lookalike.'],
};

export function memoryTipSentence(tip) {
    if (!tip) return '';
    if (tip.from !== null && tip.from !== undefined) return ruleNote(tip.from, tip.to);
    return TIER_TEXT[tip.tier]?.[1] || '';
}

export function memoryTipTier(tip) {
    return tip ? TIER_TEXT[tip.tier]?.[0] || '' : '';
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
    return `<button type="button" class="ref-tile ref-memory-tip-btn" aria-label="Memory tip: ${escapeText(tip.word)} and ${escapeText(tip.english)}" title="Memory tip" onclick="event.stopPropagation(); openMemoryTip(event);">
        <div class="ref-tile-icon-wrap">
            <svg class="ref-tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M9 18h6"></path><path d="M10 21h4"></path>
                <path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"></path>
            </svg>
        </div>
        <span class="ref-tile-label">Memory tip</span>
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

const STYLE = `
.memory-tip-modal .mt-badge { display:inline-block; font-size:.72rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; padding:3px 9px; border-radius:999px; margin-bottom:12px; border:1px solid currentColor; }
.memory-tip-modal .mt-badge[data-tier="same"], .memory-tip-modal .mt-badge[data-tier="pattern"] { color:#5ec98a; }
.memory-tip-modal .mt-badge[data-tier="close"] { color:#7aa7ff; }
.memory-tip-modal .mt-badge[data-tier="loose"] { color:#e0b25a; }
.memory-tip-modal .mt-strip { display:flex; gap:3px; overflow-x:auto; padding:2px 0 12px; justify-content:center; }
.memory-tip-modal .mt-col { display:flex; flex-direction:column; align-items:center; gap:3px; }
.memory-tip-modal .mt-cell { width:26px; height:32px; display:flex; align-items:center; justify-content:center; border-radius:7px; font-size:1.15rem; font-weight:600; background:rgba(255,255,255,.05); }
.memory-tip-modal .mt-cell.is-changed-top { background:rgba(224,178,90,.22); color:#f0c878; }
.memory-tip-modal .mt-cell.is-changed-bottom { background:rgba(94,201,138,.22); color:#7fe0a6; }
.memory-tip-modal .mt-cell.is-dropped { background:rgba(224,178,90,.16); color:#f0c878; text-decoration:line-through; }
.memory-tip-modal .mt-cell.is-rule-top { width:auto; min-width:26px; padding:0 9px; white-space:nowrap; background:rgba(224,178,90,.22); color:#f0c878; }
.memory-tip-modal .mt-cell.is-rule-bottom { width:auto; min-width:26px; padding:0 9px; white-space:nowrap; background:rgba(94,201,138,.22); color:#7fe0a6; }
.memory-tip-modal .mt-cell.is-empty { background:transparent; border:1px dashed rgba(255,255,255,.18); }
.memory-tip-modal .mt-tick { font-size:.7rem; line-height:1; opacity:.55; height:10px; }
.memory-tip-modal .mt-steps { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:10px; }
.memory-tip-modal .mt-step { display:grid; grid-template-columns:26px 1fr; gap:10px; align-items:start; }
.memory-tip-modal .mt-num { width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:.8rem; font-weight:700; background:rgba(255,255,255,.08); }
.memory-tip-modal .mt-label { font-weight:650; }
.memory-tip-modal .mt-note { font-size:.86rem; opacity:.72; margin-top:1px; }
.memory-tip-modal .mt-chain { font-size:1.02rem; margin-top:4px; }
.memory-tip-modal .mt-chain mark { background:rgba(94,201,138,.25); color:inherit; border-radius:4px; padding:0 2px; }
.memory-tip-modal .mt-prev { opacity:.6; }
.memory-tip-modal .mt-result { margin-top:14px; padding:10px 12px; border-radius:10px; background:rgba(94,201,138,.12); font-size:1.05rem; }
.memory-tip-modal .mt-caution { margin-top:12px; font-size:.86rem; opacity:.78; }
`;

function ensureStyles() {
    if (document.getElementById('memoryTipStyles')) return;
    const style = document.createElement('style');
    style.id = 'memoryTipStyles';
    style.textContent = STYLE;
    document.head.appendChild(style);
}

function joinParts(parts) {
    return (parts || []).map(part => part.t).join('');
}

function partsHTML(parts) {
    return (parts || []).map(part => (
        part.hl ? `<mark>${escapeText(part.t)}</mark>` : escapeText(part.t)
    )).join('');
}

function stripHTML(tip) {
    const cols = tip.columns.map(item => {
        if (item.op === 'rule') {
            return `<div class="mt-col">
                <div class="mt-cell is-rule-top">${escapeText('-' + item.a)}</div>
                <div class="mt-tick">↓</div>
                <div class="mt-cell is-rule-bottom">${item.b ? escapeText('-' + item.b) : '—'}</div>
            </div>`;
        }
        const topCls = item.op === 'sub' ? 'is-changed-top'
            : item.op === 'del' ? 'is-dropped' : (item.op === 'ins' ? 'is-empty' : '');
        const botCls = item.op === 'sub' || item.op === 'ins' ? 'is-changed-bottom'
            : (item.op === 'del' ? 'is-empty' : '');
        const tick = item.op === 'match' ? '' : '↓';
        return `<div class="mt-col">
            <div class="mt-cell ${topCls}">${escapeText(item.a)}</div>
            <div class="mt-tick">${tick}</div>
            <div class="mt-cell ${botCls}">${escapeText(item.b)}</div>
        </div>`;
    });
    return `<div class="mt-strip" aria-hidden="true">${cols.join('')}</div>`;
}

function stepsHTML(tip) {
    let previous = tip.word;
    const items = tip.steps.map((step, index) => {
        const chain = `<span class="mt-prev">${escapeText(previous)}</span> → ${partsHTML(step.after)}`;
        previous = joinParts(step.after) || previous;
        return `<li class="mt-step">
            <span class="mt-num">${index + 1}</span>
            <div>
                <div class="mt-label">${escapeText(step.label)}</div>
                ${step.note ? `<div class="mt-note">${escapeText(step.note)}</div>` : ''}
                <div class="mt-chain">${chain}</div>
            </div>
        </li>`;
    });
    return items.length ? `<ol class="mt-steps">${items.join('')}</ol>` : '';
}

export function openMemoryTip(event) {
    event?.stopPropagation?.();
    const tip = _openTip;
    if (!tip) return;
    ensureStyles();
    const modal = ensureModal();
    modal.querySelector('#memoryTipTitle').textContent = `${tip.word} → ${tip.english}`;
    const [tierName, tierNote] = TIER_TEXT[tip.tier] || ['', ''];
    const caution = tip.tier === 'loose'
        ? `<div class="mt-caution">Check this one against the meaning before you rely on it. It matches the sense “${escapeText(tip.sense.split(/[;(]/)[0].trim())}”.</div>`
        : '';
    modal.querySelector('#memoryTipBody').innerHTML = `
        <span class="mt-badge" data-tier="${escapeText(tip.tier)}">${escapeText(tierName)}</span>
        <p style="margin:0 0 10px;opacity:.8;">${escapeText(tierNote)}</p>
        ${stripHTML(tip)}
        ${stepsHTML(tip)}
        <div class="mt-result"><strong>${escapeText(tip.word)}</strong> ≈ <strong>${escapeText(tip.english)}</strong></div>
        ${caution}`;
    modal.hidden = false;
    modal.querySelector('.knowledge-overview-close')?.focus();
}

if (typeof window !== 'undefined') {
    window.openMemoryTip = openMemoryTip;
    window.closeMemoryTip = closeMemoryTip;
}
