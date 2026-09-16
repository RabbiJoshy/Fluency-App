// Lazy-loaded conjugation table for js/flashcards.js. Loaded on first
// click of the conjugation toggle. The data cache (window._conjugationData)
// is populated by core's loadConjugationData on Speech boot; this module
// reads it through globalThis.
//
// Render-on-toggle pattern: updateCard renders only an empty placeholder
// `<div id="conjugationTable" data-lemma="..." data-related="..." data-target="...">`
// for every verb card. The first time the user clicks the toggle, this
// module reads those data attributes, looks up the verb's paradigm, calls
// buildConjugationTableHTML, and injects the result into the placeholder.
// The built panel is cached by (ownerLemma, targetWord, isRelatedParadigm)
// so re-opening the same card's panel skips the rebuild — and so does
// re-opening a sibling card with the same lemma but different target form
// (e.g. "soy" → "eres" for ser). Cards are torn down on every updateCard,
// so the cache lives in this module's scope, not on the DOM.

const CONJ_UI = {
    spanish: {
        pronouns: ['yo', 'tú', 'él / ella', 'nosotros', 'vosotros', 'ellos / ellas'],
        defaultTense: 'Presente',
        infinitiveEndings: ['ar', 'er', 'ir'],
        moodOrder: ['Indicative', 'Subjunctive', 'Imperative'],
        moodGroups: {
            Indicative: { tenses: ['Presente', 'Pretérito', 'Imperfecto', 'Futuro', 'Condicional'], accent: 'rgba(0, 212, 170, 0.72)' },
            Subjunctive: { tenses: ['Subj. Presente', 'Subj. Imperfecto', 'Subj. Futuro'], accent: 'rgba(52, 211, 153, 0.62)' },
            Imperative: { tenses: ['Imperativo', 'Imp. Negativo'], accent: 'rgba(13, 148, 136, 0.72)' },
        },
        tenseDisplay: {
            Presente: 'pres', Pretérito: 'pret', Imperfecto: 'imperf', Futuro: 'fut', Condicional: 'cond',
            'Subj. Presente': 'pres', 'Subj. Imperfecto': 'imperf', 'Subj. Futuro': 'fut',
            Imperativo: 'affirm', 'Imp. Negativo': 'neg',
        },
    },
    portuguese: {
        pronouns: ['eu', 'tu', 'ele / ela', 'nós', 'vós', 'eles / elas'],
        defaultTense: 'Presente',
        infinitiveEndings: ['ar', 'er', 'ir', 'or', 'ôr'],
        moodOrder: ['Indicative', 'Subjunctive', 'Imperative'],
        moodGroups: {
            Indicative: { tenses: ['Presente', 'Pretérito', 'Imperfeito', 'Futuro', 'Condicional'], accent: 'rgba(0, 212, 170, 0.72)' },
            Subjunctive: { tenses: ['Subj. Presente', 'Subj. Imperfeito', 'Subj. Futuro'], accent: 'rgba(52, 211, 153, 0.62)' },
            Imperative: { tenses: ['Imperativo', 'Imp. Negativo'], accent: 'rgba(13, 148, 136, 0.72)' },
        },
        tenseDisplay: {
            Presente: 'pres', Pretérito: 'pret', Imperfeito: 'imperf', Futuro: 'fut', Condicional: 'cond',
            'Subj. Presente': 'pres', 'Subj. Imperfeito': 'imperf', 'Subj. Futuro': 'fut',
            Imperativo: 'affirm', 'Imp. Negativo': 'neg',
        },
    },
    french: {
        pronouns: ['je', 'tu', 'il / elle', 'nous', 'vous', 'ils / elles'],
        defaultTense: 'Présent',
        infinitiveEndings: ['er', 'ir', 're'],
        moodOrder: ['Indicative', 'Subjunctive', 'Imperative'],
        moodGroups: {
            Indicative: { tenses: ['Présent', 'Imparfait', 'Passé simple', 'Futur', 'Conditionnel'], accent: 'rgba(0, 212, 170, 0.72)' },
            Subjunctive: { tenses: ['Subj. Présent', 'Subj. Imparfait'], accent: 'rgba(52, 211, 153, 0.62)' },
            Imperative: { tenses: ['Impératif'], accent: 'rgba(13, 148, 136, 0.72)' },
        },
        tenseDisplay: {
            Présent: 'prés', Imparfait: 'impf', 'Passé simple': 'ps', Futur: 'fut', Conditionnel: 'cond',
            'Subj. Présent': 'prés', 'Subj. Imparfait': 'impf', Impératif: 'impér',
        },
    },
    czech: {
        pronouns: ['já', 'ty', 'on / ona', 'my', 'vy', 'oni / ony'],
        defaultTense: 'Present',
        infinitiveEndings: [],
        moodOrder: ['Indicative', 'Imperative'],
        moodGroups: {
            Indicative: { tenses: ['Present'], accent: 'rgba(0, 212, 170, 0.72)' },
            Imperative: { tenses: ['Imperative'], accent: 'rgba(13, 148, 136, 0.72)' },
        },
        tenseDisplay: { Present: 'pres', Imperative: 'imp' },
    },
    dutch: {
        pronouns: ['ik', 'jij', 'hij / zij', 'wij', 'jullie', 'zij'],
        defaultTense: 'Present',
        infinitiveEndings: ['en'],
        moodOrder: ['Indicative', 'Imperative'],
        moodGroups: {
            Indicative: { tenses: ['Present', 'Past'], accent: 'rgba(0, 212, 170, 0.72)' },
            Imperative: { tenses: ['Imperative'], accent: 'rgba(13, 148, 136, 0.72)' },
        },
        tenseDisplay: { Present: 'pres', Past: 'past', Imperative: 'imp' },
    },
};

function foldConjForm(value) {
    return String(value || '').normalize('NFC').toLocaleLowerCase().trim();
}

function lookupConjEntry(data, lemma) {
    if (!data || !lemma) return null;
    if (data[lemma]) return data[lemma];
    const folded = foldConjForm(lemma);
    if (data[folded]) return data[folded];
    for (const key of Object.keys(data)) {
        if (foldConjForm(key) === folded) return data[key];
    }
    return null;
}

function conjUiForLanguage() {
    const lang = (typeof selectedLanguage === 'string' && selectedLanguage) || 'spanish';
    return CONJ_UI[lang] || CONJ_UI.spanish;
}

function conjugationLookupUrl(lemma) {
    const lang = (typeof selectedLanguage === 'string' && selectedLanguage) || 'spanish';
    const cfg = (typeof config !== 'undefined' && config) || window.config;
    const template = cfg?.languages?.[lang]?.referenceLinks?.conjugation;
    const word = lemma || '';
    if (template && template.includes('{word}')) return template.replaceAll('{word}', encodeURIComponent(word));
    if (lang === 'portuguese') return `https://conjugator.reverso.net/conjugation-portuguese-verb-${encodeURIComponent(word)}.html`;
    if (lang === 'french') return `https://conjugator.reverso.net/conjugation-french-verb-${encodeURIComponent(word)}.html`;
    if (lang === 'czech') return `https://en.wiktionary.org/wiki/${encodeURIComponent(word)}#Czech`;
    if (lang === 'dutch') return `https://www.verbix.com/webverbix/Dutch/${encodeURIComponent(word)}`;
    return `https://www.spanishdict.com/conjugate/${encodeURIComponent(word)}`;
}

function conjugationLookupHost(url) {
    try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return 'reference'; }
}

// Built-panel HTML cache, keyed by `${ownerLemma}::${targetWord}::${isRelated}`.
// targetWord is part of the key because buildConjugationTableHTML picks the
// default open-tense based on which tense contains targetWord, AND highlights
// individual cells where form === targetWord — two cards sharing lemma but
// different target forms need different built HTML.
const _builtPanelCache = new Map();

// Split a form into (stem, ending) using longest-common-prefix vs the
// infinitive's STEM (infinitive minus the -ar/-er/-ir ending). For regular
// verbs this gives the expected pattern ("habl|o", "habl|as", "habl|a"...).
// For stem-changing irregulars the shared prefix stops earlier, so more
// of the word lands in the accent-colored "ending" span — which surfaces
// the stem change (e.g. "t|engo" from "tener", showing only the "t" as
// the preserved stem).
//
// Using the full infinitive as the reference was wrong: the "a" in the
// middle of "hablar" matched the "a" ending of "habla", stealing it into
// the stem.
function splitStemEnding(form, infinitive, endings) {
    if (!form) return { stem: '', ending: '' };
    const src = (infinitive || '').toLowerCase();
    const dst = form.toLowerCase();
    const listed = Array.isArray(endings) ? endings : [];
    const matched = listed.find(end => src.endsWith(end));
    const stemLen = matched ? src.length - matched.length
        : (listed.length === 0 ? src.length : (src.length >= 2 ? src.length - 2 : src.length));
    let i = 0;
    while (i < stemLen && i < dst.length && src[i] === dst[i]) i++;
    return { stem: form.slice(0, i), ending: form.slice(i) };
}

function buildConjugationTableHTML(conjEntry, targetWord, lemma, opts) {
    opts = opts || {};
    const relatedLemma = opts.relatedLemma || null;
    const isRelatedParadigm = !!opts.isRelatedParadigm;

    const ui = conjUiForLanguage();
    const pronouns = ui.pronouns;
    const hasData = conjEntry && Object.keys(conjEntry.tenses || {}).length > 0;
    if (!hasData) {
        const displayLemma = (lemma || targetWord || '').toLowerCase();
        const sdTarget = relatedLemma || displayLemma;
        const lookupUrl = conjugationLookupUrl(sdTarget);
        const lookupHost = conjugationLookupHost(lookupUrl);
        const emptyMsg = relatedLemma
            ? `<strong>${displayLemma}</strong> is a lexicalised form related to <strong>${relatedLemma}</strong>. We don't have its conjugation inline.`
            : `No conjugation data available for this verb.`;
        const lookupLabel = relatedLemma
            ? `Conjugate ${relatedLemma} on ${lookupHost}`
            : `Conjugate on ${lookupHost}`;
        return `
            <div id="conjugationTable" class="conjugation-panel">
                <button class="conj-close-btn" onclick="toggleConjugationTable()" aria-label="Close">&times;</button>
                <div class="conj-header">
                    <div class="conj-title">
                        <span class="conj-infinitive">${displayLemma}</span>
                    </div>
                </div>
                <div class="conj-empty-msg">
                    ${emptyMsg}
                </div>
                <a href="${lookupUrl}" target="_blank" class="conj-sd-link conj-sd-link-prominent" title="${lookupLabel}">
                    <img src="https://www.google.com/s2/favicons?domain=${encodeURIComponent(lookupHost)}&sz=64" width="18" height="18" alt="" style="border-radius:3px">
                    <span>${lookupLabel}</span>
                </a>
            </div>
        `;
    }
    const tenses = conjEntry.tenses;
    const tenseNames = Object.keys(tenses);
    const targetLower = foldConjForm(targetWord);
    // Prefer an explicit infinitive on the conj entry; fall back to
    // the lemma (or relatedLemma when we're rendering a related
    // verb's paradigm), then targetWord as a last resort.
    const conjOwnerLemma = isRelatedParadigm ? (relatedLemma || lemma || targetWord || '') : (lemma || targetWord || '');
    const infinitive = (conjEntry.infinitive || conjOwnerLemma).toLowerCase();

    // Pick the tense containing targetWord as the default; Presente otherwise.
    let defaultTense = tenses[ui.defaultTense] ? ui.defaultTense : tenseNames[0];
    if (targetLower) {
        for (const [tenseName, forms] of Object.entries(tenses)) {
            if (Array.isArray(forms) && forms.some(f => f !== '—' && foldConjForm(f) === targetLower)) {
                defaultTense = tenseName;
                break;
            }
        }
    }

    // Group tenses by mood (Indicativo / Subjuntivo / Imperativo / Otras).
    // Tenses not covered by the known groups slot under "Otras" so the UI
    // never drops data on the floor.
    const grouped = [];
    const seen = new Set();
    for (const moodName of ui.moodOrder) {
        const cfg = ui.moodGroups[moodName];
        const present = cfg.tenses.filter(t => tenses[t]);
        if (!present.length) continue;
        grouped.push({ mood: moodName, accent: cfg.accent, tenses: present });
        present.forEach(t => seen.add(t));
    }
    const orphanTenses = tenseNames.filter(t => !seen.has(t));
    if (orphanTenses.length) {
        grouped.push({ mood: 'Other', accent: 'rgba(148, 163, 184, 0.55)', tenses: orphanTenses });
    }

    // The mood that owns the default tense is the one we open on.
    const defaultMood = (grouped.find(g => g.tenses.includes(defaultTense)) || grouped[0] || {}).mood;

    // Mood toggle — segmented control, rendered only when more than one
    // mood is present. When there's just one (e.g. only Indicativo tenses
    // shipped), the toggle is redundant and hidden.
    const moodToggleHTML = grouped.length > 1 ? `
        <div class="conj-mood-toggle">
            ${grouped.map(g => {
                const active = g.mood === defaultMood ? ' conj-mood-toggle-active' : '';
                return `<button class="conj-mood-toggle-btn${active}" data-mood="${g.mood}" style="--mood-accent: ${g.accent};" onclick="switchConjMood('${g.mood}')">${g.mood}</button>`;
            }).join('')}
        </div>` : '';

    // One tense-toggle row per mood; only the active mood's row is
    // visible (display toggled by switchConjMood). This keeps the tense
    // list to a single horizontal row instead of stacking a label +
    // buttons for every mood.
    //
    // The hide-inactive-rows logic merges into one style attribute:
    // putting `display:none` in a second `style` silently drops it
    // (browsers take the first `style` attribute only), which is why
    // subjunctive tenses were showing at initial render.
    const tenseToggleHTML = grouped.map(g => {
        const isActiveMood = g.mood === defaultMood;
        const styleStr = `--mood-accent: ${g.accent};${isActiveMood ? '' : ' display: none;'}`;
        const btns = g.tenses.map(t => {
            const active = t === defaultTense ? ' conj-tense-active' : '';
            const display = ui.tenseDisplay[t] || t;
            return `<button class="conj-tense-btn${active}" data-tense="${t}" onclick="switchConjTense('${t}')">${display}</button>`;
        }).join('');
        return `<div class="conj-tense-toggle" data-mood="${g.mood}" style="${styleStr}">${btns}</div>`;
    }).join('');

    // Per-tense table. Each form is split stem/ending so the pattern pops.
    let tenseTables = '';
    for (const [tenseName, forms] of Object.entries(tenses)) {
        const hidden = tenseName !== defaultTense ? ' style="display:none"' : '';
        let rows = '';
        for (let i = 0; i < forms.length; i++) {
            const form = forms[i];
            const isActive = !!(targetLower && form && form !== '—' && foldConjForm(form) === targetLower);
            const cls = isActive ? ' conj-active' : '';
            const { stem, ending } = splitStemEnding(form, infinitive, ui.infinitiveEndings);
            // Stem is muted; ending is accent-colored — makes regular
            // patterns rhyme and irregular stems stand out.
            const formHTML = stem
                ? `<span class="conj-stem">${stem}</span><span class="conj-ending">${ending}</span>`
                : `<span class="conj-ending conj-ending-full">${ending}</span>`;
            rows += `<tr class="${cls}"><td class="conj-pronoun">${pronouns[i] || ''}</td><td class="conj-form">${formHTML}</td></tr>`;
        }
        tenseTables += `<table class="conj-table" data-tense="${tenseName}"${hidden}>${rows}</table>`;
    }

    // --- Header block ---
    // Infinitive + translation on top; -ar/-er/-ir type badge on the right.
    // The gerund and past participle are reference detail rather than a
    // paradigm the learner is drilling, so they sit in a quiet strip below
    // the table instead of competing with the headword.
    const matchedEnding = (ui.infinitiveEndings || []).find(end => infinitive.endsWith(end));
    const typeBadge = matchedEnding
        ? `<span class="conj-type-badge">-${matchedEnding.toUpperCase()}</span>`
        : '';
    const translation = conjEntry.translation || '';
    const gerActive = conjEntry.gerund && targetLower && foldConjForm(conjEntry.gerund) === targetLower ? ' is-active' : '';
    const ppActive = conjEntry.past_participle && targetLower && foldConjForm(conjEntry.past_participle) === targetLower ? ' is-active' : '';
    const nonFiniteHTML = (conjEntry.gerund || conjEntry.past_participle) ? `
        <div class="conj-nonfinite">
            ${conjEntry.gerund ? `<div class="conj-nf-item${gerActive}">
                <span class="conj-nf-label">gerund</span>
                <span class="conj-nf-form">${conjEntry.gerund}</span>
            </div>` : ''}
            ${conjEntry.past_participle ? `<div class="conj-nf-item${ppActive}">
                <span class="conj-nf-label">past participle</span>
                <span class="conj-nf-form">${conjEntry.past_participle}</span>
            </div>` : ''}
        </div>` : '';

    // Link to the language's full paradigm page — the in-app panel covers
    // the high-frequency tenses; this covers "I want to see every tense
    // incl. compound + imperative forms we don't ship locally".
    const lookupUrl = conjugationLookupUrl(infinitive);
    const lookupHost = conjugationLookupHost(lookupUrl);
    const sdLinkHTML = `
        <a href="${lookupUrl}" target="_blank" class="conj-sd-link" title="Full paradigm on ${lookupHost}">
            <img src="https://www.google.com/s2/favicons?domain=${encodeURIComponent(lookupHost)}&sz=64" width="16" height="16" alt="" style="border-radius:3px">
            <span>Full paradigm on ${lookupHost}</span>
        </a>`;

    // When we're rendering a related verb's paradigm (e.g. haber for a
    // hay card), add a note above the header so the user knows the
    // table isn't the card's own verb. Keeps the panel honest: the
    // paradigm belongs to the related verb, not the lexicalised word
    // on the card.
    const relatedNoteHTML = isRelatedParadigm && lemma && relatedLemma ? `
        <div class="conj-related-note">
            <strong>${lemma.toLowerCase()}</strong> is a lexicalised form related to <strong>${relatedLemma.toLowerCase()}</strong>. Showing <strong>${relatedLemma.toLowerCase()}</strong>'s full paradigm below.
        </div>` : '';

    return `
        <div id="conjugationTable" class="conjugation-panel">
            <button class="conj-close-btn" onclick="toggleConjugationTable()" aria-label="Close">&times;</button>
            ${relatedNoteHTML}
            <div class="conj-header">
                <div class="conj-title">
                    <span class="conj-infinitive">${infinitive}</span>
                    ${typeBadge}
                </div>
                ${translation ? `<div class="conj-translation">${translation}</div>` : ''}
            </div>
            ${moodToggleHTML}
            <div class="conj-tense-toggles">
                ${tenseToggleHTML}
            </div>
            <div class="conj-tables-wrap">
                ${tenseTables}
            </div>
            ${nonFiniteHTML}
            ${sdLinkHTML}
        </div>
    `;
}

function switchConjTense(tenseName) {
    const panel = document.getElementById('conjugationTable');
    if (!panel) return;
    // Match tables + buttons by data-tense (button text now has the
    // "Subj."/"Imp." prefix stripped for display under the mood label, so
    // text-based matching no longer works).
    panel.querySelectorAll('.conj-table').forEach(t => {
        t.style.display = t.dataset.tense === tenseName ? '' : 'none';
    });
    panel.querySelectorAll('.conj-tense-btn').forEach(b => {
        b.classList.toggle('conj-tense-active', b.dataset.tense === tenseName);
    });
}

function switchConjMood(moodName) {
    const panel = document.getElementById('conjugationTable');
    if (!panel) return;
    // Swap mood-toggle active state.
    panel.querySelectorAll('.conj-mood-toggle-btn').forEach(b => {
        b.classList.toggle('conj-mood-toggle-active', b.dataset.mood === moodName);
    });
    // Show only the active mood's tense-toggle row.
    panel.querySelectorAll('.conj-tense-toggle').forEach(t => {
        t.style.display = t.dataset.mood === moodName ? '' : 'none';
    });
    // Switch the visible tense to the mood's first (or already-active) one.
    const activeRow = panel.querySelector(`.conj-tense-toggle[data-mood="${moodName}"]`);
    if (activeRow) {
        const active = activeRow.querySelector('.conj-tense-active') || activeRow.querySelector('.conj-tense-btn');
        if (active) switchConjTense(active.dataset.tense);
    }
}

// Render-on-toggle. The placeholder (rendered by core's updateCard) is an
// empty #conjugationTable div carrying data-lemma / data-related /
// data-target attributes. First open builds the panel from those attrs +
// window._conjugationData, caches the inner HTML by (lemma, target,
// isRelated), and slides the panel in. Subsequent opens of the same panel
// (without a card change) are pure CSS toggle. Card changes blow away the
// DOM, so the next open hits the cache and rebuilds-from-cache instead of
// re-running the templating.
// The panel covers the whole viewport, not just the card. It cannot do that
// from inside the card: .card-face clips its children and the card carries a
// 3D flip transform, which makes even position:fixed resolve against the card
// rather than the viewport. So it is hosted on <body> while open and stowed
// back into the card's back face when closed, where updateCard() owns it.
function hostConjPanelFullScreen(panel) {
    if (panel.parentElement !== document.body) document.body.appendChild(panel);
}

function stowConjPanel(panel) {
    const host = document.getElementById('backContent');
    if (host && panel.parentElement !== host) host.appendChild(panel);
}

async function toggleConjugationTable() {
    const panel = document.getElementById('conjugationTable');
    if (!panel) return;
    if (panel.classList.contains('visible')) {
        panel.classList.remove('visible');
        // Wait out the slide-out before re-parenting: moving it mid-transition
        // restarts layout inside the card and the panel jumps.
        setTimeout(() => {
            if (!panel.classList.contains('visible')) stowConjPanel(panel);
        }, 260);
        return;
    }
    if (!panel.firstChild) {
        // Defensive: a fast click on a verb card before the boot-time
        // prefetch completes should wait for the in-flight load instead
        // of rendering an empty cache as "no data". loadConjugationData
        // returns the in-flight promise so concurrent callers share it.
        if (typeof window.loadConjugationData === 'function') {
            await window.loadConjugationData();
        }
        const lemma = panel.dataset.lemma || '';
        const related = panel.dataset.related || '';
        const target = panel.dataset.target || '';
        const data = window._conjugationData;
        let conjEntry = lookupConjEntry(data, lemma);
        let isRelated = false;
        if (!conjEntry && related) {
            conjEntry = lookupConjEntry(data, related);
            isRelated = !!conjEntry;
        }
        const ownerLemma = isRelated ? (related || lemma) : lemma;
        const cacheKey = `${ownerLemma}::${target}::${isRelated ? 1 : 0}`;
        let inner = _builtPanelCache.get(cacheKey);
        if (inner == null) {
            const fullHtml = buildConjugationTableHTML(conjEntry, target, lemma,
                { relatedLemma: related, isRelatedParadigm: isRelated });
            // buildConjugationTableHTML returns a wrapper `<div id="conjugationTable">…</div>`.
            // The existing placeholder IS the #conjugationTable element — strip the
            // wrapper and inject just the inner content so we don't nest divs.
            const wrapper = document.createElement('div');
            wrapper.innerHTML = fullHtml;
            const built = wrapper.firstElementChild;
            inner = built ? built.innerHTML : fullHtml;
            _builtPanelCache.set(cacheKey, inner);
        }
        panel.innerHTML = inner;
    }
    // requestAnimationFrame guards against browsers optimising away the
    // slide-in transition on a freshly-injected node (no committed layout
    // means the transition's "from" state isn't observed).
    hostConjPanelFullScreen(panel);
    requestAnimationFrame(() => panel.classList.add('visible'));
}

window.toggleConjugationTable = toggleConjugationTable;
window.stowConjPanel = stowConjPanel;
window.switchConjMood = switchConjMood;
window.switchConjTense = switchConjTense;
