// Card metadata badges, chips, and sense-detail formatting.
// Handles canonical features, qualifier formatting, and grammar pill presentation
// for SpanishDict, Wiktionary, and other sense-menu providers.

export function escapeCardText(value) {
    return String(value || '').replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[character]);
}

export function legacyObjectPronounProjection(value) {
    const text = String(value || '').trim();
    const patterns = [
        /^(.+?) \(as a direct object; as an indirect object, see ([\p{L}\p{M}-]+); after prepositions, see ([\p{L}\p{M}-]+)\)$/iu,
        /^(.+?) \(as a direct object; the corresponding indirect object is ([\p{L}\p{M}-]+); the form used after prepositions is ([\p{L}\p{M}-]+)\)$/iu,
    ];
    for (const pattern of patterns) {
        const match = pattern.exec(text);
        if (!match) continue;
        return {
            display: match[1],
            references: [
                { relation: 'indirect_object', target: match[2] },
                { relation: 'after_prepositions', target: match[3] },
            ],
        };
    }
    return null;
}

const WIKTIONARY_FUNCTIONAL_NOTE = /^(?:used to |indicat(?:e|es|ing) |express(?:es|ing) |denot(?:e|es|ing) |mark(?:s|ing) |refer(?:s|ring) to |show(?:s|ing) )/i;
const WIKTIONARY_CONSTRUCTION_NOTE = /^(?:after |before |connecting |followed by |only (?:in|with) |preceding |takes? |used (?:before|in|with) |when referring to |with )/i;
const WIKTIONARY_GRAMMAR_NOTE_WORDS = new Set([
    '1st', '2nd', '3rd', 'a', 'an', 'and', 'direct', 'disjunctive', 'female',
    'familiar', 'feminine', 'first', 'formal', 'informal', 'indirect', 'male',
    'masculine', 'neuter', 'object', 'of', 'only', 'or', 'person', 'personal',
    'plural', 'possessive', 'pronoun', 'reflexive', 'second', 'singular',
    'subject', 'the', 'third', 'verb',
]);
const WIKTIONARY_GRAMMAR_NOTE_SIGNALS = new Set([
    '1st', '2nd', '3rd', 'direct', 'first', 'indirect', 'personal', 'plural',
    'possessive', 'pronoun', 'reflexive', 'second', 'singular', 'third',
]);
const WIKTIONARY_GRAMMAR_GENDER_WORDS = new Set([
    'female', 'feminine', 'male', 'masculine', 'neuter',
]);

export function isWiktionaryGrammarNote(note) {
    const words = String(note || '').toLowerCase().replace(/‑/g, '-').match(/[a-z0-9]+/g) || [];
    if (!words.length || !words.every(word => WIKTIONARY_GRAMMAR_NOTE_WORDS.has(word))) return false;
    if (words.length === 1 && WIKTIONARY_GRAMMAR_GENDER_WORDS.has(words[0])) return true;
    return words.some(word => WIKTIONARY_GRAMMAR_NOTE_SIGNALS.has(word));
}

export function projectWiktionaryGloss(meaning, value) {
    const text = String(value || '').trim();
    const metadata = meaning?.metadata || {};
    if (!text || metadata.source_adapter !== 'wiktionary-sense-menu/v1') {
        return { display: text, features: [] };
    }
    const objectPronoun = legacyObjectPronounProjection(text);
    if (objectPronoun) {
        return {
            display: objectPronoun.display,
            features: [{ family: 'construction', kind: 'object_role', value: 'direct object' }],
        };
    }

    let remaining = text;
    const notes = [];
    while (remaining.endsWith(')')) {
        let depth = 0;
        let opening = -1;
        for (let index = remaining.length - 1; index >= 0; index--) {
            if (remaining[index] === ')') depth++;
            else if (remaining[index] === '(') {
                depth--;
                if (depth === 0) { opening = index; break; }
            }
        }
        if (opening <= 0 || !/\s/u.test(remaining[opening - 1])) break;
        const note = remaining.slice(opening + 1, -1).trim();
        const family = WIKTIONARY_FUNCTIONAL_NOTE.test(note)
            ? 'functional'
            : (WIKTIONARY_CONSTRUCTION_NOTE.test(note)
                ? 'construction'
                : (isWiktionaryGrammarNote(note) ? 'grammar' : null));
        if (!family) break;
        notes.unshift({
            family,
            kind: family === 'functional' ? 'usage_note'
                : (family === 'grammar' ? 'gloss_note' : 'gloss_phrase'),
            value: note,
        });
        remaining = remaining.slice(0, opening).trimEnd();
    }
    return { display: remaining || text, features: notes };
}

export const SENSE_CONSTRUCTION_TAGS = new Set([
    'auxiliary', 'copulative', 'ditransitive', 'impersonal', 'intransitive',
    'pronominal', 'reflexive', 'transitive'
]);
export const SENSE_REGISTER_TAGS = new Set([
    'archaic', 'colloquial', 'dated', 'euphemistic', 'formal', 'informal',
    'obsolete', 'offensive', 'poetic', 'slang', 'vulgar'
]);
export const SENSE_CONSTRUCTION_SHORT = {
    auxiliary: 'aux.',
    copulative: 'cop.',
    ditransitive: 'ditr.',
    impersonal: 'impers.',
    intransitive: 'intr.',
    pronominal: 'pronom.',
    reflexive: 'refl.',
    transitive: 'tr.'
};

export function splitSenseMetadataClauses(value) {
    const text = String(value || '');
    const parts = [];
    let depth = 0;
    let start = 0;
    for (let index = 0; index < text.length; index++) {
        const character = text[index];
        if ('([{'.includes(character)) depth++;
        else if (')]}'.includes(character) && depth) depth--;
        else if ((character === ',' || character === ';' || character === '|') && depth === 0) {
            const part = text.slice(start, index).trim();
            if (part) parts.push(part);
            start = index + 1;
        }
    }
    const final = text.slice(start).trim();
    if (final) parts.push(final);
    return parts;
}

export function compactConstructionMetadata(value) {
    const full = String(value || '').trim().replace(/^\[|\]$/g, '');
    const exact = SENSE_CONSTRUCTION_SHORT[full.toLowerCase()];
    if (exact) return { short: exact, full };
    let short = full
        .replace(/^connecting\s+/i, '')
        .replace(/^preceding adjectives?$/i, 'before adj.')
        .replace(/^used before\s+/i, 'before ')
        .replace(/^only in subordinate clauses$/i, 'subordinate only')
        .replace(/^with\s+/i, '+ ')
        .replace(/\bdirect object\b/gi, 'direct obj.')
        .replace(/\bindirect object\b/gi, 'indirect obj.')
        .replace(/\balong with\b/gi, '+')
        .replace(/[‘“][^’”]*[’”]/gu, '')
        .replace(/\s+or\s+/gi, '/')
        .replace(/\s+/g, ' ')
        .replace(/\s+([,;)])/g, '$1')
        .replace(/,\s*\+/g, ' +')
        .trim();
    return { short: short || full, full };
}

export function senseMetadataItems(meaning) {
    const metadata = meaning?.metadata || {};
    const canonical = metadata.sense_metadata || {};
    const provider = canonical.source_metadata || metadata.sense_provider_metadata || {};
    const items = [];
    const seen = new Set();
    const add = (family, kind, value, sourceText = '') => {
        const clean = String(value || '').trim();
        // Source evidence is preserved in the release for audits, but the
        // learner card is not a dictionary-inspection surface. Only a concise
        // sense qualifier can help choose a meaning; etymology and provider
        // bookkeeping never belong on the card.
        if (!clean || (family === 'grammar' && kind === 'surface_mark')) return;
        if (family === 'source' && kind !== 'qualifier') return;
        const key = `${family}\u0000${clean.toLocaleLowerCase('en')}`;
        if (seen.has(key)) return;
        seen.add(key);
        items.push({ family, kind, value: clean, sourceText: String(sourceText || '').trim() });
    };

    const normalizedFeatures = [
        ...(Array.isArray(canonical.features) ? canonical.features : []),
        ...(Array.isArray(meaning?.specialist_features) ? meaning.specialist_features : []),
        ...(Array.isArray(metadata.specialist_features) ? metadata.specialist_features : []),
        ...(canonical.contract_version ? [] : projectWiktionaryGloss(
            meaning, meaning?.meaning || meaning?.translation || ''
        ).features),
    ];
    for (const feature of normalizedFeatures) {
        if (!feature || typeof feature !== 'object') continue;
        if (feature.family === 'register' || feature.family === 'domain'
            || feature.family === 'companion'
            || feature.family === 'construction' || feature.family === 'grammar'
            || feature.family === 'functional' || feature.family === 'source') {
            add(feature.family, feature.kind || '', feature.value, feature.embedding_text);
        }
    }
    // Provider-shaped fallbacks exist only for older releases. Once a release
    // carries the canonical contract, its adapter is the authority: reading
    // raw regions/tags again can resurrect values that it explicitly ignored
    // (for example SpanishDict's UK/Australia English-gloss locales).
    if (!canonical.contract_version) {
        for (const region of provider.regions || []) {
            const label = region && typeof region === 'object'
                ? (region.name || region.label || region.region)
                : region;
            add('register', 'region', label);
        }
        for (const topic of provider.topics || []) add('domain', 'topic', topic);
        if (provider.qualifier) add('source', 'qualifier', provider.qualifier);
        for (const tag of provider.tags || []) {
            const lowered = String(tag || '').toLowerCase();
            if (SENSE_REGISTER_TAGS.has(lowered)) add('register', 'usage_tag', tag);
            else if (SENSE_CONSTRUCTION_TAGS.has(lowered)) add('construction', 'grammar_tag', tag);
        }
    }

    // Compatibility for releases made before specialist_features crossed the
    // release boundary. Restrict this fallback to Wiktionary and to phrases
    // with an unmistakable grammatical frame.
    if (!canonical.contract_version
        && metadata.source_adapter === 'wiktionary-sense-menu/v1') {
        if (legacyObjectPronounProjection(meaning?.meaning || meaning?.translation)) {
            add('construction', 'object_role', 'direct object');
        }
        for (const clause of splitSenseMetadataClauses(provider.context || meaning?.context)) {
            if (/^(?:with\s|followed by\s|takes?\s|only (?:in|with)\s)/i.test(clause)) {
                add('construction', 'context_phrase', clause);
            }
        }
    }
    // Collapse qualifier pairs whose combined reading is unambiguous. This is
    // presentation-only: the underlying canonical features remain separate.
    const combine = (leftValue, rightValue, combinedValue) => {
        const left = items.findIndex(item => item.value === leftValue);
        const right = items.findIndex(item => item.value === rightValue);
        if (left < 0 || right < 0) return;
        const sourceIndex = Math.min(items[left].sourceIndex ?? left, items[right].sourceIndex ?? right);
        items.splice(Math.max(left, right), 1);
        items.splice(Math.min(left, right), 1);
        items.push({ family: 'register', kind: 'combined_qualifier', value: combinedValue, sourceIndex });
    };
    combine('Early', 'Modern', 'Early Modern');
    for (const qualifier of ['usually', 'sometimes', 'often']) {
        combine(qualifier, 'orthography=capitalized', `${qualifier} capitalized`);
    }
    combine('possibly', 'offensive', 'possibly offensive');

    // SpanishDict often expresses one grammatical reading as several atomic
    // canonical features: "imperfect indicative" becomes tense + mood and
    // "third person singular" becomes person + number. Those atoms are useful
    // to WSD, but four separate learner chips repeat the dictionary sentence
    // and make the active sense look busier than it is. Reassemble grammar
    // that belongs to this one sense into one readable, source-ordered detail.
    const grammarIndexes = items
        .map((item, index) => item.family === 'grammar' ? index : -1)
        .filter(index => index >= 0);
    if (grammarIndexes.length > 1) {
        const grammarItems = grammarIndexes.map(index => items[index]);
        const sourceLabels = [];
        for (const item of grammarItems) {
            const label = String(item.sourceText || '').trim()
                || senseMetadataDisplay(item).full;
            if (label && !sourceLabels.some(existing =>
                existing.toLocaleLowerCase('en') === label.toLocaleLowerCase('en'))) {
                sourceLabels.push(label);
            }
        }
        const firstIndex = grammarIndexes[0];
        for (const index of [...grammarIndexes].reverse()) items.splice(index, 1);
        items.splice(firstIndex, 0, {
            family: 'grammar',
            kind: 'combined_sense_mark',
            value: sourceLabels.join(' · '),
            sourceText: sourceLabels.join('; '),
        });
    }

    const familyOrder = {
        construction: 0,
        companion: 1,
        register: 2,
        domain: 3,
        grammar: 4,
        functional: 5,
        source: 6,
    };
    return items
        .map((item, sourceIndex) => ({ ...item, sourceIndex }))
        .sort((left, right) => (
            (familyOrder[left.family] ?? 9) - (familyOrder[right.family] ?? 9)
            || left.sourceIndex - right.sourceIndex
        ))
        .filter((item, index, ordered) => {
            const label = senseMetadataDisplay(item).short.toLocaleLowerCase('en');
            return ordered.findIndex(candidate => (
                senseMetadataDisplay(candidate).short.toLocaleLowerCase('en') === label
            )) === index;
        });
}

export function senseMetadataDisplay(item) {
    if (item.family === 'companion') {
        return { short: `+ ${item.value}`, full: `used with ${item.value}` };
    }
    if (item.family === 'construction') {
        // Canonical frame kinds are intentionally provider-neutral. Give their
        // atomic values enough syntax to remain clear to a learner: a bare
        // "infinitive" is ambiguous, while "+ infinitive" reads as a frame.
        if (item.kind === 'complement_form') {
            return { short: `+ ${item.value}`, full: `used with ${item.value}` };
        }
        return compactConstructionMetadata(item.value);
    }
    if (item.family === 'functional') {
        return { short: item.value, full: item.value };
    }
    if (item.family === 'grammar') {
        const exact = ({
            'reflexive=true': 'refl.',
            'person=1': '1st person',
            'person=2': '2nd person',
            'person=3': '3rd person',
            'number=singular': 'singular',
            'number=plural': 'plural',
            'number=plural-only': 'plural only',
            'form=participle': 'participle',
            'form=personal-infinitive': 'personal infinitive',
            'pronoun-class=personal': 'personal pronoun',
            'countability=countable': 'countable',
            'countability=uncountable': 'uncountable',
            'inflection=invariable': 'invariable',
            'definiteness=definite': 'definite',
            'definiteness=indefinite': 'indefinite',
            'gender=variable-by-person': 'varies by gender',
            'adjective-class=relational': 'relational adj.',
            'gender=virile': 'virile',
            'gender=nonvirile': 'nonvirile',
            'voice=active': 'active voice',
            'voice=passive': 'passive voice',
            'form=adjectival': 'adjectival',
            'form=adverbial': 'adverbial',
            'case=partitive': 'partitive',
            'derivation=diminutive': 'diminutive',
            'derivation=augmentative': 'augmentative',
            'noun-class=collective': 'collective',
            'animacy=animal-not-person': 'animal, not person',
            'tense=past-historic': 'past historic',
            'orthography=capitalized': 'capitalized',
            'orthography=lowercase': 'lowercase',
            'orthography=uppercase': 'uppercase',
            'inflection=no-first-person-singular-present': 'no 1st-person singular present',
            'gender=usually-feminine': 'usually feminine',
            'pronoun-use=standalone': 'standalone pronoun',
        })[item.value];
        if (exact) return { short: exact, full: exact };
        const assignment = /^([^=]+)=(.+)$/u.exec(item.value);
        if (assignment) {
            const [, property, rawValue] = assignment;
            const value = rawValue.replace(/-/g, ' ');
            const full = value === 'true'
                ? property.replace(/-/g, ' ')
                : (property === 'declension' && value === 'none' ? 'indeclinable' : value);
            return { short: full, full };
        }
        const short = item.value
            .replace(/\bfirst[- ]person\b/gi, '1st')
            .replace(/\bsecond[- ]person\b/gi, '2nd')
            .replace(/\bthird[- ]person\b/gi, '3rd')
            .replace(/\bpersonal pronoun\b/gi, 'pers. pron.')
            .replace(/\bpersonal\b/gi, 'pers.')
            .replace(/\bpronoun\b/gi, 'pron.')
            .replace(/\bindirect object\b/gi, 'indirect obj.')
            .replace(/\bdirect object\b/gi, 'direct obj.')
            .replace(/\bsingular\b/gi, 'sg.')
            .replace(/\bplural\b/gi, 'pl.')
            .replace(/\bmasculine\b/gi, 'masc.')
            .replace(/\bfeminine\b|\bfemale\b/gi, 'fem.')
            .replace(/\bneuter\b/gi, 'neut.');
        return { short, full: item.value };
    }
    if (item.family === 'source') {
        const prefix = item.kind === 'etymology' ? 'Etymology' : 'Source note';
        return { short: `${prefix}: ${item.value}`, full: `${prefix}: ${item.value}` };
    }
    return {
        short: item.value.replace(/-/g, ' '),
        full: item.value.replace(/-/g, ' '),
    };
}

export function isSenseDefiningGrammar(item) {
    return item.kind === 'combined_sense_mark'
        || /^(?:countability|definiteness|formation|function|mood|noun-class|number|person|polarity|position|pronoun-class|pronoun-use|tense|verb-class|voice|word-class)=/u.test(item.value)
        || new Set([
            'reflexive=true',
            'form=personal-infinitive',
            'number=plural-only',
            'number=no-plural',
            'number=singular-only',
        ]).has(item.value);
}

const SUPPORTING_REGISTER_VALUES = new Set([
    'broadly',
    'especially',
    'figuratively',
    'literally',
    'metonymically',
    'mildly',
    'often',
    'possibly',
    'sometimes',
    'specifically',
    'standard',
    'usually',
]);

export function isSupportingSenseMetadata(item) {
    return (item.family === 'grammar' && !isSenseDefiningGrammar(item))
        || item.family === 'functional'
        || item.family === 'source'
        || (item.family === 'construction' && item.kind === 'optional_companion')
        || (item.family === 'register'
            && SUPPORTING_REGISTER_VALUES.has(item.value.toLocaleLowerCase('en')));
}

export function senseMetadataHTML(meaning, active) {
    if (!active) return '';
    const items = senseMetadataItems(meaning);
    const renderItems = (values) => values.map((item) => {
        const display = senseMetadataDisplay(item);
        const family = escapeCardText(item.family);
        const shortLabel = escapeCardText(display.short);
        const fullLabel = escapeCardText(display.full);
        return `<span class="sense-metadata-detail" data-family="${family}" title="${family}: ${fullLabel}" aria-label="${fullLabel}">${shortLabel}</span>`;
    }).join('');
    const primary = items.filter(item => (
        ['construction', 'companion', 'register', 'domain'].includes(item.family)
        && !isSupportingSenseMetadata(item)
    ));
    // Grammar that changes which sense applies is a navigation cue. Routine
    // inflectional detail is still available, but does not compete with the
    // gloss and example until the learner asks for it.
    const grammar = items.filter(item => item.family === 'grammar' && isSenseDefiningGrammar(item));
    const supporting = items.filter(isSupportingSenseMetadata);
    if (!primary.length && !grammar.length && !supporting.length) return '';
    const primaryHTML = primary.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--primary">${renderItems(primary)}</span>`
        : '';
    const grammarHTML = grammar.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--grammar">${renderItems(grammar)}</span>`
        : '';
    const supportingHTML = supporting.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--details${supporting.length === 1 ? ' is-single' : ''}"${supporting.length > 1 ? ' hidden' : ''}>${renderItems(supporting)}</span>`
        : '';
    const more = supporting.length > 1
        ? `<button type="button" class="sense-metadata-more" aria-expanded="false" onclick="toggleSenseMetadataOverflow(event, this)" data-count="${supporting.length}" aria-label="Show ${supporting.length} supporting details"><span class="sense-metadata-more-label">More details</span><span class="sense-metadata-more-count">${supporting.length}</span></button>`
        : '';
    return `<span class="sense-metadata-list" aria-label="Sense details">${primaryHTML}${grammarHTML}${more}${supportingHTML}</span>`;
}

export function contextWithoutSenseMetadata(meaning, active) {
    const context = String(meaning?.context || '').trim();
    if (!context) return context;
    const metadata = meaning?.metadata || {};
    const canonical = metadata.sense_metadata || {};
    const provider = canonical.source_metadata || metadata.sense_provider_metadata || {};
    // For canonical Wiktionary releases, `context` is the source's leading
    // parenthetical. The extractor accounts for every top-level clause as a
    // typed feature, so repeating the original prose beside those features is
    // pure duplication. It remains preserved in source metadata and details.
    if (metadata.source_adapter === 'wiktionary-sense-menu/v1'
        && canonical.contract_version
        && String(provider.context || '').trim() === context) return '';
    const represented = new Set();
    const metadataItems = senseMetadataItems(meaning);
    let residual = context;
    // A SpanishDict context can mix an ordinary gloss and metadata in one
    // string ("to remove; used with de"). Remove only the source span that
    // produced a canonical feature, leaving the semantic clarification intact.
    // Do this for inactive rows as well: those rows are navigation labels, so
    // repeating tense/person/region prose there is especially noisy. The
    // selected row renders the same facts through the structured detail tier.
    for (const item of [...metadataItems].sort((a, b) => (
        String(b.sourceText || '').length - String(a.sourceText || '').length
    ))) {
        const sourceText = String(item.sourceText || '').trim();
        if (!sourceText) continue;
        const index = residual.toLocaleLowerCase('en').indexOf(sourceText.toLocaleLowerCase('en'));
        if (index >= 0) residual = `${residual.slice(0, index)}${residual.slice(index + sourceText.length)}`;
    }
    residual = residual
        .replace(/^\s*[,;|:]\s*|\s*[,;|:]\s*$/gu, '')
        .replace(/\s*[,;|:]\s*[,;|:]\s*/gu, '; ')
        .replace(/\s{2,}/gu, ' ')
        .trim();
    for (const item of metadataItems) {
        const display = senseMetadataDisplay(item);
        for (const value of [item.value, item.sourceText, display.short, display.full]) {
            represented.add(String(value || '').trim().toLocaleLowerCase('en'));
        }
    }
    return splitSenseMetadataClauses(residual)
        .filter(clause => !represented.has(clause.toLocaleLowerCase('en')))
        .join(', ');
}

export function toggleSenseMetadataChip(event, chip) {
    event?.preventDefault?.();
    event?.stopPropagation?.();
    if (!chip) return;
    const expanded = chip.getAttribute('aria-expanded') === 'true';
    chip.textContent = decodeURIComponent(expanded ? chip.dataset.short : chip.dataset.full);
    chip.setAttribute('aria-expanded', String(!expanded));
}

export function toggleSenseMetadataOverflow(event, control) {
    event?.preventDefault?.();
    event?.stopPropagation?.();
    const list = control?.closest?.('.sense-metadata-list');
    if (!list) return;
    const expand = control.getAttribute('aria-expanded') !== 'true';
    const details = list.querySelector('.sense-metadata-tier--details');
    if (details) details.hidden = !expand;
    const count = Number(control.dataset.count) || 0;
    control.setAttribute('aria-expanded', String(expand));
    control.setAttribute('aria-label', expand ? 'Hide supporting details' : `Show ${count} supporting details`);
    const label = control.querySelector('.sense-metadata-more-label');
    if (label) label.textContent = expand ? 'Hide details' : 'More details';
}

// Window attachments for inline HTML onclick handlers
if (typeof window !== 'undefined') {
    window.toggleSenseMetadataChip = toggleSenseMetadataChip;
    window.toggleSenseMetadataOverflow = toggleSenseMetadataOverflow;
}
