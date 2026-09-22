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

// Languages that have a built conjugation-drill deck under app/conjugation/.
// A language appears here once its deck file exists; until then the drill
// link is simply absent rather than pointing at a 404.
const CONJ_DRILL_DECKS = { spanish: 'es', portuguese: 'pt', czech: 'cs' };

// Single entry point into conjugation mode. Returns null when this language
// has no deck, so the caller omits the link instead of guessing.
function conjugationDrillUrl(infinitive) {
    const lang = (typeof selectedLanguage === 'string' && selectedLanguage) || 'spanish';
    const code = CONJ_DRILL_DECKS[lang];
    if (!code || !infinitive) return null;
    return `conjugation/?lang=${code}&verb=${encodeURIComponent(String(infinitive).toLowerCase())}`;
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
    const targetLower = foldConjForm(targetWord);
    const conjOwnerLemma = isRelatedParadigm ? (relatedLemma || lemma || targetWord || '') : (lemma || targetWord || '');
    const infinitive = (conjEntry.infinitive || conjOwnerLemma).toLowerCase();

    // The drawer only shows tenses that contain this card's surface. The
    // full paradigm lives in conjugation mode.
    const matchingTenses = Object.keys(tenses).filter(name => {
        const forms = tenses[name];
        return Array.isArray(forms) && forms.some(f => f && f !== '—' && foldConjForm(f) === targetLower);
    });
    const shownTenses = matchingTenses.length
        ? matchingTenses
        : [tenses[ui.defaultTense] ? ui.defaultTense : Object.keys(tenses)[0]].filter(Boolean);
    const defaultTense = shownTenses[0];

    const tenseToggleHTML = shownTenses.length > 1 ? `
        <div class="conj-tense-toggle">
            ${shownTenses.map(t => {
                const active = t === defaultTense ? ' conj-tense-active' : '';
                return `<button class="conj-tense-btn${active}" data-tense="${t}" onclick="switchConjTense('${t}')">${t}</button>`;
            }).join('')}
        </div>` : `<div class="conj-match-tense">${shownTenses[0] || ''}</div>`;

    let tenseTables = '';
    for (const tenseName of shownTenses) {
        const forms = tenses[tenseName] || [];
        const hidden = tenseName !== defaultTense ? ' style="display:none"' : '';
        let rows = '';
        for (let i = 0; i < forms.length; i++) {
            const form = forms[i];
            const isActive = !!(targetLower && form && form !== '—' && foldConjForm(form) === targetLower);
            const cls = isActive ? ' conj-active' : '';
            const { stem, ending } = splitStemEnding(form, infinitive, ui.infinitiveEndings);
            const formHTML = stem
                ? `<span class="conj-stem">${stem}</span><span class="conj-ending">${ending}</span>`
                : `<span class="conj-ending conj-ending-full">${ending}</span>`;
            rows += `<tr class="${cls}"><td class="conj-pronoun">${pronouns[i] || ''}</td><td class="conj-form">${formHTML}</td></tr>`;
        }
        tenseTables += `<table class="conj-table" data-tense="${tenseName}"${hidden}>${rows}</table>`;
    }

    const drillUrl = conjugationDrillUrl(infinitive);
    const drillLinkHTML = drillUrl ? `
        <a href="${drillUrl}" class="conj-drill-link" title="Drill ${infinitive} in conjugation mode">
            <span>All tenses in conjugation mode</span>
        </a>` : '';

    const relatedNoteHTML = isRelatedParadigm && lemma && relatedLemma ? `
        <div class="conj-related-note">
            Showing <strong>${relatedLemma.toLowerCase()}</strong> for <strong>${lemma.toLowerCase()}</strong>.
        </div>` : '';

    return `
        <div id="conjugationTable" class="conjugation-panel">
            <button class="conj-close-btn" onclick="toggleConjugationTable()" aria-label="Close">&times;</button>
            ${relatedNoteHTML}
            <div class="conj-header">
                <div class="conj-title">
                    <span class="conj-infinitive">${infinitive}</span>
                </div>
            </div>
            ${tenseToggleHTML}
            <div class="conj-tables-wrap">
                ${tenseTables}
            </div>
            ${drillLinkHTML}
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

// Render-on-toggle. The placeholder (rendered by core's updateCard) is an
// empty #conjugationTable div carrying data-lemma / data-related /
// data-target attributes. First open builds the panel from those attrs +
// window._conjugationData, caches the inner HTML by (lemma, target,
// isRelated), and slides the panel in. Subsequent opens of the same panel
// (without a card change) are pure CSS toggle. Card changes blow away the
// DOM, so the next open hits the cache and rebuilds-from-cache instead of
// re-running the templating.
// On a wide desktop in a study session the panel docks in the right-hand
// gutter beside the card (side-dock.js); anywhere narrower it covers the whole
// viewport. Either way it cannot stay inside the card: .card-face clips its
// children and the card carries a 3D flip transform, which makes even
// position:fixed resolve against the card rather than the viewport. So it is
// hosted on <body> while open and stowed back into the card's back face when
// closed, where updateCard() owns it.
function hostConjPanel(panel) {
    if (window.sideDock?.openCardPanel(panel)) return;
    panel.classList.remove('is-docked');
    if (panel.parentElement !== document.body) document.body.appendChild(panel);
}

function stowConjPanel(panel) {
    panel.classList.remove('is-docked');
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
    // A freshly moved node has no committed layout, so the slide-in would be
    // skipped. Reading a layout property commits the "from" state; unlike a
    // requestAnimationFrame it cannot be deferred by a backgrounded tab.
    hostConjPanel(panel);
    void panel.offsetWidth;
    panel.classList.add('visible');
}

window.toggleConjugationTable = toggleConjugationTable;
window.stowConjPanel = stowConjPanel;
window.switchConjTense = switchConjTense;
