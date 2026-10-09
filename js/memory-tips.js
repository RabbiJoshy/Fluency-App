// Memory tip: how a deck word maps onto English by a regular ending shift.
//
// First pass, deliberately small. It only knows suffix correspondences the
// pipeline's cognate configs already carry (config/cognates/<pair>.json
// `ending_rules`) plus their close siblings, and it is for cards the learner
// is actually shown (Smart Skip off), so a tip that is thin on a hard word is
// harmless.
//
// A rule firing on the spelling alone would teach false friends, so a tip is
// only produced when the rewritten word lands close to a word in the card's
// own English glosses. The tip names that gloss word; it never invents one.

// [target ending, English ending, plain-English note]. Longest endings first
// within a language so -ciones is read before -ones.
const RULES = {
    spanish: [
        ['idades', 'ities'], ['idad', 'ity'], ['dades', 'ties'], ['dad', 'ty'],
        ['ciones', 'tions'], ['ción', 'tion'], ['siones', 'sions'], ['sión', 'sion'],
        ['mente', 'ly'], ['osos', 'ous'], ['osas', 'ous'], ['oso', 'ous'], ['osa', 'ous'],
        ['ismo', 'ism'], ['ista', 'ist'], ['ivo', 'ive'], ['iva', 'ive'],
        ['ico', 'ic'], ['ica', 'ic'], ['ario', 'ary'], ['aria', 'ary'],
        ['ancia', 'ance'], ['encia', 'ence'], ['ante', 'ant'], ['ente', 'ent'],
        ['able', 'able'], ['ible', 'ible'], ['ura', 'ure'], ['ia', 'y'],
    ],
    portuguese: [
        ['idades', 'ities'], ['idade', 'ity'], ['dades', 'ties'], ['dade', 'ty'],
        ['ções', 'tions'], ['ção', 'tion'], ['sões', 'sions'], ['são', 'sion'],
        ['mente', 'ly'], ['osos', 'ous'], ['osas', 'ous'], ['oso', 'ous'], ['osa', 'ous'],
        ['ismo', 'ism'], ['ista', 'ist'], ['ivo', 'ive'], ['iva', 'ive'],
        ['ico', 'ic'], ['ica', 'ic'], ['ário', 'ary'], ['ária', 'ary'],
        ['ância', 'ance'], ['ência', 'ence'], ['ante', 'ant'], ['ente', 'ent'],
        ['ável', 'able'], ['ível', 'ible'], ['ura', 'ure'], ['ia', 'y'],
    ],
    french: [
        ['ités', 'ities'], ['ité', 'ity'], ['tions', 'tions'], ['tion', 'tion'],
        ['sions', 'sions'], ['sion', 'sion'], ['ment', 'ly'],
        ['euses', 'ous'], ['euse', 'ous'], ['eux', 'ous'],
        ['isme', 'ism'], ['iste', 'ist'], ['ique', 'ic'], ['aire', 'ary'],
        ['ance', 'ance'], ['ence', 'ence'], ['ant', 'ant'], ['ent', 'ent'],
        ['able', 'able'], ['ible', 'ible'], ['eur', 'or'], ['ie', 'y'],
    ],
};

// Where the shift is at the front of the word. Only French école/état-type
// words are worth the rule; kept apart because they rewrite the start.
const PREFIX_RULES = {
    french: [['é', 's'], ['ê', 'es'], ['ô', 'os']],
};

const LANGUAGE_KEY = {
    spanish: 'spanish', es: 'spanish',
    portuguese: 'portuguese', portuguese_brazilian: 'portuguese', pt: 'portuguese',
    french: 'french', fr: 'french',
};

const MIN_SIMILARITY = 0.72;

function stripAccents(value) {
    return String(value || '').normalize('NFD').replace(/[̀-ͯ]/g, '');
}

function levenshtein(a, b) {
    const prev = Array.from({ length: b.length + 1 }, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
        let diag = prev[0];
        prev[0] = i;
        for (let j = 1; j <= b.length; j++) {
            const up = prev[j];
            prev[j] = Math.min(prev[j] + 1, prev[j - 1] + 1, diag + (a[i - 1] === b[j - 1] ? 0 : 1));
            diag = up;
        }
    }
    return prev[b.length];
}

function similarity(a, b) {
    const longest = Math.max(a.length, b.length);
    return longest ? 1 - levenshtein(a, b) / longest : 0;
}

// Spelling conventions that differ regardless of ending (c/k, ph/f), so a
// correct shift is not marked down for them.
function foldForComparison(value) {
    return stripAccents(String(value).toLowerCase())
        .replace(/ph/g, 'f').replace(/ck/g, 'k').replace(/c(?=[aou])/g, 'k')
        .replace(/qu/g, 'k').replace(/y/g, 'i');
}

function glossWords(meanings) {
    const seen = new Set();
    for (const meaning of meanings || []) {
        const text = [meaning?.meaning, meaning?.translation].filter(Boolean).join(' ');
        for (const piece of text.toLowerCase().split(/[^a-z']+/)) {
            if (piece.length >= 4 && piece !== 'with' && piece !== 'that') seen.add(piece);
        }
    }
    return [...seen];
}

// The best tip for one card, or null. `card` needs a headword and `meanings`
// with English text; `language` is the app's language name or code.
export function memoryTipFor(card, language) {
    const key = LANGUAGE_KEY[String(language || '').toLowerCase()];
    if (!key) return null;
    const word = String(card?.displaySurface || card?.targetWord || card?.word || '').trim().toLowerCase();
    if (word.length < 5 || /\s/.test(word)) return null;
    const glosses = glossWords(card?.meanings);
    if (!glosses.length) return null;

    const candidates = [];
    for (const [from, to] of RULES[key] || []) {
        if (word.endsWith(from) && word.length > from.length + 1) {
            candidates.push({ kind: 'ending', from, to, built: word.slice(0, -from.length) + to });
        }
    }
    for (const [from, to] of PREFIX_RULES[key] || []) {
        if (word.startsWith(from) && word.length > from.length + 2) {
            candidates.push({ kind: 'start', from, to, built: to + word.slice(from.length) });
        }
    }

    let best = null;
    for (const candidate of candidates) {
        const built = foldForComparison(candidate.built);
        for (const gloss of glosses) {
            // The English word must actually wear the English ending the rule
            // names, or a stem that merely resembles it (chica / chick) passes.
            if (candidate.kind === 'ending' && !foldForComparison(gloss).endsWith(foldForComparison(candidate.to))) continue;
            const score = similarity(built, foldForComparison(gloss));
            if (score >= MIN_SIMILARITY && (!best || score > best.score)) {
                best = { ...candidate, english: gloss, score };
            }
        }
    }
    if (!best) return null;
    return {
        word,
        english: best.english,
        kind: best.kind,
        from: best.from,
        to: best.to,
        // Same-spelling endings (-tion/-tion) still earn a tip, but the
        // sentence is different: nothing changes, it is simply safe to trust.
        unchanged: best.from === best.to,
    };
}

export function memoryTipSentence(tip) {
    if (!tip) return '';
    const dash = value => (value ? `-${value}` : '');
    if (tip.kind === 'start') {
        return `A leading ${tip.from} usually stands for an English ${tip.to}.`;
    }
    if (tip.unchanged) {
        return `The ending ${dash(tip.from)} is spelled the same in English.`;
    }
    return `The ending ${dash(tip.from)} becomes ${dash(tip.to)} in English.`;
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
            <div class="phrase-summary-scroll" id="memoryTipBody"></div>
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

export function openMemoryTip(event) {
    event?.stopPropagation?.();
    const tip = _openTip;
    if (!tip) return;
    const modal = ensureModal();
    modal.querySelector('#memoryTipTitle').textContent = `${tip.word} → ${tip.english}`;
    modal.querySelector('#memoryTipBody').innerHTML = `
        <p style="font-size:1.05rem;line-height:1.5;margin:0 0 10px;">${escapeText(memoryTipSentence(tip))}</p>
        <p style="margin:0;opacity:.8;"><strong>${escapeText(tip.word)}</strong> → <strong>${escapeText(tip.english)}</strong></p>`;
    modal.hidden = false;
    modal.querySelector('.knowledge-overview-close')?.focus();
}

if (typeof window !== 'undefined') {
    window.openMemoryTip = openMemoryTip;
    window.closeMemoryTip = closeMemoryTip;
}
