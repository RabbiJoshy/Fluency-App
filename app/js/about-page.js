// The About page (about.html): a page of its own, not part of the app.
//
// It loads no account, language, deck or progress, so it reads the same for
// everyone and never starts a sign-in. It renders content/about.md, mounts
// the two looping demo cards, and opens the walkthrough (walkthrough.js)
// from them. The cards are the shared replicas (card-replica.js); the
// frequency bars come from prominence-badge.js, as on the live card.

import { REPLICA_CARDS, replicaProminence, posAccentRgb } from './card-replica.js?v=41db6094';
import './prominence-badge.js?v=41db6094';
import './walkthrough.js?v=41db6094';

// Minimal Markdown → HTML renderer. Handles headings (##/###), paragraphs,
// unordered lists, bold/italic, inline code, links, and images. Enough for
// the About copy at content/about.md without a runtime dependency.
function renderMarkdown(md) {
    const escape = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Media extensions that render as <video autoplay loop muted> instead of <img>.
    // Drop a recording at the referenced path and it becomes a looping silent demo
    // clip inside the About modal.
    const VIDEO_EXT_RE = /\.(webm|mp4|mov|ogv|m4v)$/i;

    const inline = (s) => {
        let out = escape(s);
        out = out.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, src) => {
            // demo://<mode> — mount point for a live animated card demo. The mode
            // ("normal" or "artist") picks which card variant to render. alt text
            // becomes the accessible label for screen readers.
            if (src.startsWith('demo://')) {
                const mode = src.slice('demo://'.length).replace(/[^a-zA-Z0-9_-]/g, '');
                return '<div class="about-demo-card" data-mode="' + mode + '"'
                    + ' role="img" aria-label="' + alt + '"></div>';
            }
            if (VIDEO_EXT_RE.test(src)) {
                return '<figure class="about-figure about-figure-video">'
                    + '<video src="' + src + '" autoplay loop muted playsinline preload="metadata"'
                    + ' onerror="this.parentElement.classList.add(\'about-figure-missing\')">'
                    + '</video>'
                    + '<figcaption>' + alt + '</figcaption>'
                    + '</figure>';
            }
            return '<figure class="about-figure">'
                + '<img src="' + src + '" alt="' + alt + '" loading="lazy"'
                + ' onerror="this.parentElement.classList.add(\'about-figure-missing\')" />'
                + '<figcaption>' + alt + '</figcaption>'
                + '</figure>';
        });
        // example://walkthrough — opens the walkthrough (js/walkthrough.js):
        // a two-screen look at a card for a visitor, layered over About so
        // closing it lands back here. Never the learner tutorial — that is
        // for people using the app and About is for people being shown it.
        // Written as an ordinary Markdown link in about.md so its position
        // and wording stay editable there, but rendered as a button because
        // it opens a modal rather than navigating anywhere.
        out = out.replace(/\[([^\]]+)\]\(example:\/\/[^)]*\)/g,
            '<button type="button" class="about-see-example-btn" onclick="window.openWalkthrough && window.openWalkthrough()">'
            + '<span class="about-see-example-icon" aria-hidden="true">▶</span>'
            + '<span class="about-see-example-label">$1</span>'
            + '<span class="about-see-example-hint">A quick look at a card · about 30 seconds</span>'
            + '</button>');
        out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
            '<a href="$2" target="_blank" rel="noopener">$1</a>');
        out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        out = out.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
        out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
        return out;
    };

    const lines = md.split('\n');
    const html = [];
    let list = [];
    let listTag = 'ul';
    let para = [];
    const flushList = () => {
        if (list.length) {
            html.push(`<${listTag}>` + list.map(l => '<li>' + inline(l) + '</li>').join('') + `</${listTag}>`);
            list = [];
        }
    };
    // A switch between "- " and "1. " items starts a new list.
    const pushItem = (tag, text) => {
        flushPara();
        if (list.length && listTag !== tag) flushList();
        listTag = tag;
        list.push(text);
    };
    const flushPara = () => {
        if (para.length) {
            html.push('<p>' + inline(para.join(' ')) + '</p>');
            para = [];
        }
    };
    const flushAll = () => { flushList(); flushPara(); };

    // Simple HTML-comment skip so sections can be temporarily hidden in
    // about.md without deleting them. Single-line `<!-- ... -->` is dropped;
    // multi-line blocks starting with `<!--` consume lines until one ends
    // with `-->`.
    let inComment = false;
    for (const raw of lines) {
        const line = raw.trim();
        if (inComment) {
            if (line.endsWith('-->')) inComment = false;
            continue;
        }
        if (line.startsWith('<!--')) {
            if (!line.endsWith('-->')) inComment = true;
            continue;
        }
        if (!line) { flushAll(); continue; }
        if (line.startsWith(':::')) {
            flushAll();
            html.push(line === ':::' ? '</div>' : '<div class="about-' + line.slice(3).trim().replace(/[^a-z-]/gi, '') + '">');
        }
        else if (line.startsWith('~ ')) { flushAll(); html.push('<p class="about-note">' + inline(line.slice(2)) + '</p>'); }
        else if (line.startsWith('#### ')) { flushAll(); html.push('<h4>' + inline(line.slice(5)) + '</h4>'); }
        else if (line.startsWith('### ')) { flushAll(); html.push('<h3>' + inline(line.slice(4)) + '</h3>'); }
        else if (line.startsWith('## ')) { flushAll(); html.push('<h2>' + inline(line.slice(3)) + '</h2>'); }
        else if (line.startsWith('# ')) { flushAll(); html.push('<h1>' + inline(line.slice(2)) + '</h1>'); }
        else if (line.startsWith('- ') || line.startsWith('* ')) { pushItem('ul', line.slice(2)); }
        else if (/^\d+\.\s/.test(line)) { pushItem('ol', line.replace(/^\d+\.\s+/, '')); }
        else { flushList(); para.push(line); }
    }
    flushAll();
    return html.join('\n');
}

// Append the footnote + data-sources section at the bottom of the About
// body. The ¹ footnote is paired with the superscript next to the Spotify
// logo on the artist demo card. The sources line credits the external
// datasets the pipeline depends on — short, reads as end-matter, same
// muted styling as the footnote above it.
function _appendAboutFootnotes(body) {
    const existing = body.querySelector('.about-footnotes');
    if (existing) existing.remove();
    const existingCta = body.querySelector('.about-bottom-cta');
    if (existingCta) existingCta.remove();

    const cta = document.createElement('div');
    cta.className = 'about-bottom-cta';
    cta.innerHTML = '<a href="./" class="about-standalone-app-link">Open app &rarr;</a>';
    body.appendChild(cta);

    const notes = document.createElement('aside');
    notes.className = 'about-footnotes';
    notes.innerHTML =
        '<p id="about-footnote-1">'
        + '<sup class="about-footnote-number">1</sup> '
        + 'Ready-made collections from Bad Bunny, Rosalía and Young Miko are built in, '
        + 'or connect Spotify and study any playlist of your own.'
        + '</p>'
        + '<p class="about-references">'
        + '<strong>Sources:</strong> lyrics from Genius, synced timestamps via LRCLIB and Spotify, '
        + 'word meanings from Wiktionary and SpanishDict, subtitle frequency from OpenSubtitles, '
        + 'examples from OpenSubtitles and Tatoeba, '
        + 'conjugations from Wiktionary, cognate detection via CogNet.'
        + '</p>';
    body.appendChild(notes);
}

// ----- About-modal card demos --------------------------------------------------
//
// Live animated cards inserted into the About modal wherever `demo://<mode>`
// appears in the Markdown. Reuses the app's .card / .card-face / .flipped CSS so
// the demo is visually identical to the real flashcard — we just drive it with
// a tiny sequential animation instead of user input. Each demo runs in its own
// async loop that exits when its container leaves the DOM (modal closes).

// The demo cards are the walkthrough's own cards (card-replica.js), so the
// loop a reader glances at and the annotated walkthrough behind it show the
// same `banco` and the same `cielo`. They used to carry their own data,
// which had drifted: `fuego` with a "light" line that does not show that
// meaning, and hand-written "≈50%" shares the live card no longer prints.
// Only the first example per meaning is used; the loop is a glance.
function _aboutDemoEntry(key) {
    const card = REPLICA_CARDS[key];
    return {
        word: card.word,
        pos: card.pos,
        rank: card.rank,
        corpusCount: card.corpusCount,
        // Most common meaning first, as on the live card (banco: bank, then bench).
        meanings: [...card.meanings].sort((a, b) => (Number(b.pct) || 0) - (Number(a.pct) || 0)).map(m => {
            const ex = m.examples[0];
            return {
                translation: m.translation,
                pct: m.pct,
                target: ex.target,
                english: ex.english,
                song: ex.song ? `${ex.song}${ex.vocalists ? ` · ${ex.vocalists}` : ''}` : null,
            };
        }),
    };
}

const _ABOUT_DEMO_DECKS = {
    normal: ['bancoSpeech'],
    artist: ['cielo'],
};

function _buildAboutDemoCard(mode) {
    // DOM structure mirrors what updateCard() in flashcards.js produces:
    //   .card
    //     .card-face.card-front  — card-word, card-pos, card-ranking, song (artist only)
    //     .card-face.card-back
    //       .card-details
    //         .back-header        — big word repeated at the top of the back
    //         .meanings-scroll    — list of .meaning-row.meaning-row-regular
    //         .sentence           — accent-bordered example box
    //         .translation        — english line below
    // Rows are populated and a selected index is rotated by _runAboutDemo.
    const wrap = document.createElement('div');
    wrap.className = 'about-demo-card-inner';
    // Spotify logo as an inline SVG — tiny source-of-truth copy of the
    // iconic green-circle-with-soundwaves mark. Used only on artist-mode
    // cards to indicate lyric data comes from Spotify/Genius.
    const spotifyLogo =
        '<svg class="about-demo-spotify-logo" viewBox="0 0 24 24" aria-hidden="true">'
        + '<path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34'
        + 'c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539'
        + '-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3'
        + 'c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6'
        + '-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36'
        + 'C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381'
        + ' 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/>'
        + '</svg>';
    wrap.innerHTML = `
        <div class="card">
            <div class="card-face card-front">
                <div class="card-word"></div>
                <div class="card-pos"></div>
                <div class="card-ranking"></div>
            </div>
            <div class="card-face card-back">
                <div class="card-details">
                    <div class="back-header">
                        <div class="about-demo-back-word"></div>
                    </div>
                    <div class="meanings-scroll"></div>
                    <div class="about-demo-example">
                        <div class="about-demo-example-target"></div>
                        <div class="about-demo-example-english"></div>
                    </div>
                    <div class="about-demo-spotify-row">
                        <span class="about-demo-song-back"></span>
                        <span class="about-demo-spotify-mark">
                            ${spotifyLogo}
                            <sup class="about-demo-footnote-ref" role="link" tabindex="0" aria-label="Read footnote 1">1</sup>
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `;
    return wrap;
}

// One compact row per meaning, drawn the way the live card draws it: the
// chosen meaning ticked and outlined in its part-of-speech colour, and how
// common each meaning is as the live card's four-bar meter rather than a
// percentage. Minimal on purpose — no grammar pills or section heading; the
// walkthrough is where every part gets explained.
const _DEMO_TICK = '<svg class="meaning-row-check" width="16" height="16" viewBox="0 0 24 24" fill="none" '
    + 'stroke="rgb(var(--sense-match-rgb))" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
    + 'aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>';

function _renderDemoMeaningRows(meanings, selectedIdx) {
    return meanings.map((m, idx) => {
        const isSelected = idx === selectedIdx;
        const prominence = replicaProminence(m.pct);
        const meter = prominence && typeof window.prominenceBadgeHTML === 'function'
            ? window.prominenceBadgeHTML(prominence)
            : '';
        return `
            <div class="meaning-row meaning-row-regular${isSelected ? ' is-selected' : ''}">
                <span class="about-demo-row-tick">${isSelected ? _DEMO_TICK : ''}</span>
                <div class="meaning-row-body">
                    <span class="meaning-row-translation">${_escapeDemoText(m.translation)}</span>
                </div>
                <span class="about-demo-row-meter">${meter}</span>
            </div>`;
    }).join('');
}

function _escapeDemoText(value) {
    return String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

const _POS_CLASS_MAP = {
    VERB: 'pos-verb', NOUN: 'pos-noun', ADJ: 'pos-adj', ADV: 'pos-adv',
    PREP: 'pos-prep', ADP: 'pos-prep', CONJ: 'pos-conj', CCONJ: 'pos-conj',
    SCONJ: 'pos-conj', PRON: 'pos-pron', DET: 'pos-det', INT: 'pos-int',
    INTJ: 'pos-int', NUM: 'pos-num', MWE: 'pos-mwe',
};

function _posColorClass(pos) {
    const key = (pos || '').trim().toUpperCase().split(/[\s·]+/)[0];
    return _POS_CLASS_MAP[key] || '';
}

function _posDisplayName(pos) {
    const key = (pos || '').trim().toUpperCase().split(/[\s·]+/)[0];
    const names = {
        VERB: 'verb', NOUN: 'noun', ADJ: 'adjective', ADV: 'adverb',
        PREP: 'preposition', ADP: 'preposition', CONJ: 'conjunction',
        CCONJ: 'conjunction', SCONJ: 'conjunction', PRON: 'pronoun',
        DET: 'determiner', INT: 'interjection', INTJ: 'interjection',
        NUM: 'number', MWE: 'expression',
    };
    return names[key] || String(pos || '').toLowerCase();
}

function _sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

// Wrap any occurrence of `word` in the example sentence with a highlight span.
// Matches the real flashcard app's behaviour in updateCard() — word-boundary
// regex using unicode property escapes so it handles Spanish letters cleanly,
// case-insensitive so "Fuego" at sentence start still catches. Escapes HTML
// up-front so the raw sentence can't inject markup.
function _highlightTargetWord(sentence, word) {
    if (!sentence) return '';
    const escaped = sentence
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    if (!word) return escaped;
    const wordEsc = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    try {
        const re = new RegExp(`(?<![\\p{L}\\p{N}])(${wordEsc})(?![\\p{L}\\p{N}])`, 'giu');
        return escaped.replace(re, '<span class="about-demo-highlight">$1</span>');
    } catch (_) {
        // Older browsers without \p{...} support — just return the escaped text.
        return escaped;
    }
}

async function _runAboutDemo(container, mode) {
    const deck = _ABOUT_DEMO_DECKS[mode] || _ABOUT_DEMO_DECKS.normal;
    const card = container.querySelector('.card');
    const wordEl = container.querySelector('.card-word');
    const posEl = container.querySelector('.card-pos');
    const rankEl = container.querySelector('.card-ranking');
    const backWordEl = container.querySelector('.about-demo-back-word');
    const meaningsEl = container.querySelector('.meanings-scroll');
    const exampleTargetEl = container.querySelector('.about-demo-example-target');
    const exampleEnglishEl = container.querySelector('.about-demo-example-english');
    const spotifyRowEl = container.querySelector('.about-demo-spotify-row');
    const songBackEl = container.querySelector('.about-demo-song-back');

    const stillMounted = () => container.isConnected
        && !document.getElementById('aboutProjectModal').classList.contains('hidden');

    const setFrontPos = (pos) => {
        posEl.className = 'card-pos';
        const cls = _posColorClass(pos);
        if (cls) posEl.classList.add(cls);
        posEl.style.setProperty('--front-pos-rgb', posAccentRgb(pos));
        posEl.textContent = _posDisplayName(pos);
    };

    while (stillMounted()) {
        for (const entry of deck.map(_aboutDemoEntry)) {
            if (!stillMounted()) return;

            // -------- Front face --------
            card.classList.remove('flipped');
            wordEl.textContent = entry.word;
            // Every colour on the back reads this one property, as on a live card.
            const accent = posAccentRgb(entry.pos);
            container.style.setProperty('--sense-match-rgb', accent);
            card.style.setProperty('--card-pos-rgb', accent);
            card.style.setProperty('--card-ambient-glow', `radial-gradient(circle at 50% 20%, rgba(${accent}, 0.18), transparent 70%)`);
            setFrontPos(entry.pos);
            // Mirror the live labels while keeping this small demo on one line.
            if (entry.rank && entry.corpusCount) {
                rankEl.textContent = mode === 'artist'
                    ? `Vocabulary Rank: ${entry.rank.toLocaleString()} · Song Lines: ${entry.corpusCount.toLocaleString()}`
                    : `Vocabulary rank: ${entry.rank.toLocaleString()} · Frequency: ${entry.corpusCount.toLocaleString()}/million`;
            } else if (entry.rank) {
                rankEl.textContent = `Vocabulary rank: ${entry.rank}`;
            } else {
                rankEl.textContent = '';
            }
            backWordEl.textContent = entry.word;
            // Spotify row on the back — only artist-mode entries carry a
            // `song` field; for normal-mode cards hide the row entirely.
            const firstSong = entry.meanings.find(m => m.song)?.song;
            if (firstSong && songBackEl && spotifyRowEl) {
                songBackEl.textContent = firstSong;
                spotifyRowEl.style.display = '';
            } else if (spotifyRowEl) {
                spotifyRowEl.style.display = 'none';
            }

            await _sleep(4000);
            if (!stillMounted()) return;

            // -------- Flip and cycle through senses --------
            card.classList.add('flipped');
            await _sleep(1100); // matches .card transition + settle

            for (let i = 0; i < entry.meanings.length; i++) {
                if (!stillMounted()) return;
                const m = entry.meanings[i];
                meaningsEl.innerHTML = _renderDemoMeaningRows(entry.meanings, i);
                if (songBackEl && spotifyRowEl && m.song) {
                    songBackEl.textContent = m.song;
                    spotifyRowEl.style.display = '';
                }
                // Target sentence is HTML (with the target word wrapped in a
                // highlight span); the helper escapes the rest first so raw
                // data can't inject markup.
                exampleTargetEl.innerHTML = _highlightTargetWord(m.target, entry.word);
                exampleEnglishEl.textContent = m.english;
                // Dwell long enough to actually read the example sentence. A
                // single-sense entry sits longer since there's nothing else
                // to cycle to.
                const dwell = entry.meanings.length === 1 ? 5500 : 4500;
                await _sleep(dwell);
            }

            if (!stillMounted()) return;
            card.classList.remove('flipped');
            await _sleep(1500);
        }
    }
}

// The tooltip a demo card shows: on a mouse it appears as the pointer moves
// over the card, and a click opens the walkthrough on that card. Touch has no
// hover, so the first tap shows the tooltip and a second tap opens.
function _closeExplainTips() {
    document.querySelectorAll('.about-demo-tip').forEach(tip => tip.remove());
}

function _showExplainTip(card, text) {
    _closeExplainTips();
    const tip = document.createElement('div');
    tip.className = 'about-demo-tip';
    tip.setAttribute('role', 'tooltip');
    tip.innerHTML = `<span class="about-demo-tip-label">${text}</span>`;
    card.appendChild(tip);
}

document.addEventListener('pointerdown', event => {
    if (!event.target.closest('.about-demo-card')) _closeExplainTips();
});
document.addEventListener('keydown', event => {
    if (event.key === 'Escape') _closeExplainTips();
});

function mountAboutDemos(root) {
    const placeholders = root.querySelectorAll('.about-demo-card[data-mode]');
    placeholders.forEach(el => {
        if (el.dataset.mounted === '1') return;
        el.dataset.mounted = '1';
        const mode = el.dataset.mode;
        const inner = _buildAboutDemoCard(mode);
        el.appendChild(inner);

        // The loop is the trailer; the walkthrough is the film. A tap on
        // either card shows a small tooltip offering the walkthrough on that
        // same card, annotated. No separate button under the cards.
        const start = mode === 'artist' ? 'lyrics' : null;
        el.classList.add('is-walkthrough-link');
        el.setAttribute('role', 'button');
        el.setAttribute('tabindex', '0');
        el.setAttribute('aria-label', 'See every part of this card explained');
        const open = () => { _closeExplainTips(); window.openWalkthrough?.({ start }); };
        let lastPointer = 'mouse';
        el.addEventListener('pointerenter', event => {
            if (event.pointerType !== 'touch') _showExplainTip(el, 'Click to see every part explained');
        });
        el.addEventListener('pointerleave', event => {
            if (event.pointerType !== 'touch') _closeExplainTips();
        });
        el.addEventListener('pointerdown', event => { lastPointer = event.pointerType; });
        el.addEventListener('click', event => {
            if (event.target.closest('.about-demo-footnote-ref')) return;
            if (lastPointer === 'touch' && !el.querySelector('.about-demo-tip')) {
                _showExplainTip(el, 'Tap again to see every part explained');
                return;
            }
            open();
        });
        el.addEventListener('focus', () => _showExplainTip(el, 'Press Enter to see every part explained'));
        el.addEventListener('blur', _closeExplainTips);
        el.addEventListener('keydown', event => {
            if (event.target !== el || (event.key !== 'Enter' && event.key !== ' ')) return;
            event.preventDefault();
            open();
        });

        // Wire the ¹ superscript next to the Spotify logo so clicking (or
        // pressing Enter on) it scrolls to the matching footnote. The modal
        // body owns its own scroll, so href="#..." anchors don't work — do
        // it explicitly with scrollIntoView.
        const ref = inner.querySelector('.about-demo-footnote-ref');
        if (ref) {
            const jumpToFootnote = (e) => {
                if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
                e.preventDefault();
                const note = root.querySelector('#about-footnote-1');
                if (note) note.scrollIntoView({ behavior: 'smooth', block: 'center' });
            };
            ref.addEventListener('click', jumpToFootnote);
            ref.addEventListener('keydown', jumpToFootnote);
        }

        _runAboutDemo(inner, mode);
    });
}

// Feature rows (`:::feature`) put the heading in a left column and the rest in
// a right one; a `:::compare` block splits at each #### into side-by-side
// columns. The renderer emits them flat, so group the children here.
function layoutAboutFeatures(root) {
    root.querySelectorAll('.about-feature').forEach(feature => {
        const head = feature.querySelector(':scope > h3');
        if (!head || feature.querySelector(':scope > .about-feature-body')) return;
        const bodyEl = document.createElement('div');
        bodyEl.className = 'about-feature-body';
        while (head.nextSibling) bodyEl.appendChild(head.nextSibling);
        feature.appendChild(bodyEl);
    });
    root.querySelectorAll('.about-compare').forEach(compare => {
        let col = null;
        Array.from(compare.children).forEach(child => {
            if (child.tagName === 'H4') {
                col = document.createElement('div');
                col.className = 'about-compare-col';
                compare.appendChild(col);
            }
            if (col) col.appendChild(child);
        });
    });
    root.querySelectorAll('.about-music-group').forEach(group => {
        group.querySelectorAll('.about-feature').forEach(feature => {
            if (feature.querySelector('.about-music-label')) return;
            const label = document.createElement('div');
            label.className = 'about-music-label';
            label.textContent = 'Music';
            feature.insertBefore(label, feature.firstChild);
        });

        const checkMusicScroll = () => {
            const rect = group.getBoundingClientRect();
            if (rect.top < window.innerHeight * 0.85) {
                group.classList.add('is-revealed');
            }
        };
        const modal = document.querySelector('.about-project-modal') || window;
        modal.addEventListener('scroll', checkMusicScroll, { passive: true });
        window.addEventListener('scroll', checkMusicScroll, { passive: true });
        checkMusicScroll();
    });
}

// Rewire the two source-section <h3>s so they sit side by side on desktop.
// The Markdown source stays linear (easier to edit); we detect the
// "Speech" / "Lyrics" pair after rendering and wrap each h3 +
// its following siblings (up to the next h2 or h3) into a column. The
// "artist" alternative is matched for backward compatibility with any
// older about.md copy.
function layoutAboutTwoModes(root) {
    if (root.querySelector('.about-modes-row')) return;  // already laid out

    const h3s = Array.from(root.querySelectorAll('h3'));
    // Match current copy plus prior headings for cached/older About content.
    const normal = h3s.find(h => /^(?:speech\b|standard mode\b|normal mode\b)/i.test(h.textContent.trim()));
    const lyrics = h3s.find(h => /^(?:music\b|lyrics\b|artist mode\b)/i.test(h.textContent.trim()));
    if (!normal || !lyrics) return;

    // Drop a comment placeholder at the Standard-mode h3's position BEFORE
    // we start detaching its siblings, so we have a stable anchor to swap
    // the finished row into afterwards.
    const anchor = document.createComment('about-modes-anchor');
    normal.parentNode.insertBefore(anchor, normal);

    const collectSection = (h3) => {
        const out = [h3];
        let el = h3.nextElementSibling;
        while (el && el.tagName !== 'H3' && el.tagName !== 'H2') {
            out.push(el);
            el = el.nextElementSibling;
        }
        return out;
    };
    const sections = [collectSection(normal), collectSection(lyrics)];

    // Each mode splits into its card (heading + demo) and its text, so the
    // grid can put both cards side by side with one caption directly under
    // them, and the two texts below. On a phone the CSS interleaves them
    // again: card, caption, text, card, text.
    const holdsDemo = el => el.matches('.about-demo-card') || el.querySelector('.about-demo-card');
    const row = document.createElement('div');
    row.className = 'about-modes-row is-split';
    const heads = [];
    const bodies = [];
    sections.forEach((section, i) => {
        const head = document.createElement('div');
        head.className = `about-modes-column about-modes-head about-modes-${i ? 'lyrics' : 'speech'}`;
        const body = document.createElement('div');
        body.className = `about-modes-column about-modes-body about-modes-${i ? 'lyrics' : 'speech'}`;
        section.forEach(child => {
            (child.tagName === 'H3' || holdsDemo(child) ? head : body).appendChild(child);
        });
        heads.push(head);
        bodies.push(body);
    });

    row.append(bodies[0], heads[0], heads[1], bodies[1]);
    anchor.parentNode.replaceChild(row, anchor);

    const modal = document.querySelector('.about-project-modal') || window;
    const checkScroll = () => {
        const top = (modal === window ? window.scrollY : modal.scrollTop) || 0;
        row.classList.toggle('is-revealed', top > 25);
    };
    modal.addEventListener('scroll', checkScroll, { passive: true });
    window.addEventListener('scroll', checkScroll, { passive: true });
    checkScroll();
}

async function renderAboutPage() {
    const body = document.getElementById('aboutProjectBody');
    if (!body) return;
    try {
        const resp = await fetch('content/about.md?v=41db6094', { cache: 'no-cache' });
        if (!resp.ok) throw new Error('Failed to load about.md');
        body.innerHTML = renderMarkdown(await resp.text());
        layoutAboutFeatures(body);
        layoutAboutTwoModes(body);
        mountAboutDemos(body);
        _appendAboutFootnotes(body);
    } catch (e) {
        console.error('About: failed to load markdown', e);
        body.innerHTML = '<p style="color: var(--text-muted);">Could not load project description.</p>';
    }
    // about.html#walkthrough opens straight onto the walkthrough.
    if (window.location.hash === '#walkthrough') window.openWalkthrough?.();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderAboutPage);
else renderAboutPage();
