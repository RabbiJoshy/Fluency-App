// Function-word presentation (CASCADE-WSD prototype, Dutch first).
//
// Function words -- articles, prepositions, particles, clitics -- are taught by
// the construction they belong to (opgeven, aan het + verb) or by their
// grammatical role, not by a dictionary sense. The release labels each example
// by rule (no WSD) and summarises the card; this module only renders that data.
// Wording is a draft for review.

const ROLE_NAMES = {
    prep: 'preposition',
    article: 'article',
    subject_pron: 'pronoun',
    object_pron: 'pronoun',
    conj: 'conjunction',
    conj_that: 'conjunction',
    conj_if: 'conjunction',
    conj_before: 'conjunction',
    infinitive_to: 'to + verb',
    degree_too: 'too + adjective',
    existential_er: 'there is / are',
    locative_er: 'there (place)',
    pronominal_adverb: 'with a preposition',
    partitive_er: 'of them',
    possessive: 'possessive',
    aux_perfect: 'helper verb',
    aux_passive: 'helper verb (passive)',
    copula: 'linking verb',
    be: 'verb',
    adverb: 'adverb',
    demonstrative: 'pointing word',
    relative: 'relative pronoun',
};

function esc(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Dictionary glosses can be long ("what time is it? (literally ...)"); a chip shows the core.
function shortGloss(gloss) {
    return String(gloss || '').split(/\s*[(;]/)[0].trim();
}

export function functionWordLabelText(label) {
    if (!label || !label.value) return '';
    if (label.kind === 'unit') {
        const gloss = shortGloss(label.gloss);
        return gloss ? `${label.value} · ${gloss}` : label.value;
    }
    const name = ROLE_NAMES[label.value] || label.value.replace(/_/g, ' ');
    return label.gloss && label.gloss !== name ? `${name} · ${label.gloss}` : name;
}

/** Card-back block replacing the sense list: what the word does, and its constructions. */
export function functionWordBlockHTML(card) {
    const summary = card?.functionWord;
    if (!summary) return '';
    // Distinct chips only: subject and object pronoun both read "pronoun · it".
    const distinct = texts => [...new Set(texts.filter(Boolean))];
    const roleTexts = distinct((summary.roles || []).map(r => functionWordLabelText({ kind: 'role', ...r }))).slice(0, 3);
    // A pattern seen once in the card's sentences is an accident of sampling, not a pattern.
    const patternTexts = distinct((summary.patterns || []).filter(p => p.count >= 2)
        .map(p => functionWordLabelText({ kind: 'unit', ...p }))).slice(0, 4);
    const roleChips = roleTexts.map(t => `<span class="fw-chip fw-chip-role">${esc(t)}</span>`).join('');
    const patternChips = patternTexts.map(t => `<span class="fw-chip fw-chip-pattern">${esc(t)}</span>`).join('');
    return `
        <div class="fw-block">
            <div class="fw-block-head"><span class="fw-badge">Grammar word</span></div>
            ${roleChips ? `<div class="fw-row"><span class="fw-row-label">Used as</span><div class="fw-chips">${roleChips}</div></div>` : ''}
            ${patternChips ? `<div class="fw-row"><span class="fw-row-label">Patterns</span><div class="fw-chips">${patternChips}</div></div>` : ''}
        </div>`;
}

/** The label under one example's translation; empty when the rules gave none. */
export function functionWordExampleHTML(example) {
    const label = example?.metadata?.function_word;
    const text = functionWordLabelText(label);
    if (!text) return '';
    const kind = label.kind === 'unit' ? 'fw-chip-pattern' : 'fw-chip-role';
    return `<div class="fw-example-label"><span class="fw-chip ${kind}">${esc(text)}</span></div>`;
}
