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

const WIKTIONARY_PRONOUN_DEFINITION = /^(?:(?:first|second|third)-person[a-z0-9\s,–-]+(?:pronoun|determiner|article)(?:,\s*when\s+used\s+with\s+[^\;]+)?);\s*(.+)$/i;

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
    const pronounMatch = WIKTIONARY_PRONOUN_DEFINITION.exec(remaining);
    if (pronounMatch) {
        const extractedPrefixNote = remaining.slice(0, remaining.length - pronounMatch[1].length).replace(/;\s*$/, '').trim();
        remaining = pronounMatch[1].trim();
        notes.push({
            family: 'grammar',
            kind: 'gloss_note',
            value: extractedPrefixNote,
        });
    }

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
        if (family) {
            const canonical = metadata.sense_metadata;
            if (canonical?.contract_version && !(canonical.features || []).some(feature =>
                [feature.value, feature.embedding_text].some(value => String(value || '').toLowerCase() === note.toLowerCase()))) break;
            notes.unshift({
                family,
                kind: family === 'functional' ? 'usage_note'
                    : (family === 'grammar' ? 'gloss_note' : 'gloss_phrase'),
                value: note,
            });
            remaining = remaining.slice(0, opening).trimEnd();
        } else if (/^the definite grammatical article\b/i.test(note)) {
            // The article's general dictionary definition is available in
            // selected-row details. Semantic parentheses stay in the gloss.
            remaining = remaining.slice(0, opening).trimEnd();
        } else {
            break;
        }
    }
    return {
        display: remaining || text,
        features: notes,
        qualifier: notes.find(n => n.family === 'context' || n.kind === 'gloss_note')?.value || '',
    };
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
        if (family === 'companion' && /^(?:nominative|accusative|genitive|dative|instrumental|locative|vocative)$/i.test(clean)) {
            family = 'construction';
            kind = 'required_case';
        }
        // Source evidence is preserved in the release for audits, but the
        // learner card is not a dictionary-inspection surface. Only a concise
        // sense qualifier can help choose a meaning; etymology and provider
        // bookkeeping never belong on the card.
        if (!clean || (family === 'grammar' && kind === 'surface_mark')) return;
        if (family === 'functional' && kind === 'semantic_scope') return;
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
        .map((item, index) => item.family === 'grammar' && /^(?:person|number|mood|tense)=/.test(item.value) ? index : -1)
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
            components: grammarItems,
        });
    }

    const familyOrder = {
        companion: 0,
        construction: 1,
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

const METADATA_SYNONYM_GROUPS = [
    ['intransitive', 'intr', 'intrans'],
    ['transitive', 'tr', 'trans'],
    ['ditransitive', 'ditr', 'ditrans'],
    ['reflexive', 'refl'],
    ['pronominal', 'pronom'],
    ['impersonal', 'impers'],
    ['auxiliary', 'aux'],
    ['copulative', 'cop'],
    ['direct object', 'direct obj'],
];

export function foldMetadataComparable(text) {
    let value = String(text || '').toLocaleLowerCase('en')
        .replace(/['’"]/g, '')
        .replace(/[^\p{L}\p{N}+=]+/gu, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    if (!value) return '';
    value = value.replace(/^used with /, 'with ');
    for (const group of METADATA_SYNONYM_GROUPS) {
        const canonical = group[0];
        for (const alias of [...group].sort((left, right) => right.length - left.length)) {
            const pattern = alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            value = value.replace(new RegExp(`\\b${pattern}\\.?\\b`, 'gu'), canonical);
        }
    }
    return value.replace(/\s+/g, ' ').trim();
}

const CONSTRUCTION_LABELS = new Set(METADATA_SYNONYM_GROUPS.map(group => group[0]));

export function metadataTextIsRedundant(left, right) {
    const first = foldMetadataComparable(left);
    const second = foldMetadataComparable(right);
    if (!first || !second) return false;
    if (first === second) return true;
    const shorter = first.length <= second.length ? first : second;
    const longer = first.length <= second.length ? second : first;
    if (!CONSTRUCTION_LABELS.has(shorter)) return false;
    return ` ${longer} `.includes(` ${shorter} `);
}

function meaningHasObjectFormLinks(meaning) {
    const metadata = meaning?.metadata || {};
    const lists = [
        metadata.sense_metadata?.source_metadata?.cross_references,
        metadata.sense_provider_metadata?.cross_references,
        metadata.cross_references,
    ];
    for (const list of lists) {
        if (!Array.isArray(list)) continue;
        if (list.some(reference => (
            reference?.relation === 'indirect_object'
            || reference?.relation === 'after_prepositions'
        ) && reference?.target)) return true;
    }
    return Boolean(legacyObjectPronounProjection(meaning?.meaning || meaning?.translation));
}

function isInflectionalPersonNumber(item) {
    if (item?.family !== 'grammar') return false;
    const parts = String(item.value || '').toLowerCase().split(/\s*·\s*/);
    if (!parts.length) return false;
    return parts.every(part => (
        /^(?:person|number)=/.test(part)
        || /^(?:singular|plural|plural only|1st person|2nd person|3rd person)$/.test(part.trim())
    ));
}

function metadataItemKey(item) {
    return `${item.family}\u0000${String(item.value || '').toLowerCase()}`;
}

export const LEARNER_METADATA_MIN_SCORE = 60;
export const LEARNER_METADATA_MAX_CHIPS = 2;

// Metadata is compared only with other readings of this same visible gloss.
// A feature occurring on a different translation is not a reason to hide it.
export function senseMetadataPeers(meaning, meanings, gloss = '') {
    const key = foldMetadataComparable(projectWiktionaryGloss(meaning,
        gloss || meaning?.meaning || meaning?.translation || '').display);
    return (meanings || []).filter(peer => peer !== meaning
        && peer.pos === meaning.pos && (peer.headword || '') === (meaning.headword || '')
        && foldMetadataComparable(projectWiktionaryGloss(peer,
            peer.meaning || peer.translation || '').display) === key);
}

function usefulRegister(item) {
    return item.family === 'register' && !SUPPORTING_REGISTER_VALUES.has(item.value.toLowerCase());
}

function grammarIsAlreadyInGloss(item, gloss) {
    const text = foldMetadataComparable(gloss);
    if (item.value === 'definiteness=indefinite' && /^(?:a an|a|an)$/.test(text)) return true;
    if (item.value === 'definiteness=definite' && text === 'the') return true;
    if (item.value === 'possessive=true' && /^(?:my|your|his|her|its|our|their)$/.test(text)) return true;
    return false;
}

export function compactLearnerSenseMetadata(items, meaning, options = {}) {
    const gloss = String(options.gloss || meaning?.meaning || meaning?.translation || '');
    const peers = Array.isArray(options.peerMeanings) ? options.peerMeanings.filter(p => p !== meaning) : [];
    const peerKeys = peers.map(peer => new Set(senseMetadataItems(peer).map(metadataItemKey)));
    const differs = item => peerKeys.length > 0 && peerKeys.some(keys => !keys.has(metadataItemKey(item)));
    const hasCompanion = items.some(item => item.family === 'companion' || item.kind === 'required_case');
    const kept = (items || []).filter(item => {
        const display = senseMetadataDisplay(item, { gloss });
        if (item.family === 'register' && SUPPORTING_REGISTER_VALUES.has(item.value.toLowerCase())) return false;
        if (options.sharedContext && [item.value, item.sourceText, display.short, display.full].some(value => metadataTextIsRedundant(value, options.sharedContext))) return false;
        if (grammarIsAlreadyInGloss(item, gloss)) return false;
        if (gloss && [display.short, display.full, item.value].some(value => metadataTextIsRedundant(value, gloss))) return false;
        if (item.family === 'functional' && functionalAlreadyInGloss(item, gloss)) return false;
        if (isInflectionalPersonNumber(item) && !differs(item) && !/\byour\b/i.test(gloss)) return false;
        if (hasCompanion && item.family === 'construction' && /^(?:intransitive|transitive|ditransitive)$/.test(item.value) && !differs(item)) return false;
        if (usefulRegister(item)) return true;
        // A routine grammatical mark may be useful in details, but is not a
        // substitute for the semantic context that distinguishes these rows.
        if (item.family === 'grammar' && !isSenseDefiningGrammar(item)
            && (!differs(item) || String(meaning?.context || '').trim())) return false;
        if (peerKeys.length && peerKeys.every(keys => keys.has(metadataItemKey(item)))
            && item.family === 'grammar') return false;
        return scoreSenseMetadata(item) >= LEARNER_METADATA_MIN_SCORE || differs(item);
    });
    // Suppress only known parent topics, never unrelated subject qualifiers.
    const topicParents = { 'card games': ['games'], linguistics: ['human sciences'], anatomy: ['biology'] };
    const domains = new Set(kept.filter(i => i.family === 'domain').map(i => i.value.replace(/-/g, ' ').toLowerCase()));
    const redundantTopics = new Set([...domains].flatMap(value => topicParents[value] || []));
    return kept.filter(item => item.family !== 'domain' || !redundantTopics.has(item.value.replace(/-/g, ' ').toLowerCase()))
        .sort((a, b) => Number(usefulRegister(b)) - Number(usefulRegister(a))
            || scoreSenseMetadata(b) - scoreSenseMetadata(a)
            || (a.sourceIndex ?? 0) - (b.sourceIndex ?? 0));
}

const FUNCTION_LABELS = {
    location: 'place', time: 'time', manner: 'manner', material: 'material',
    characteristic: 'characteristics', content: 'contents', origin: 'origin',
    destination: 'destination', direction: 'direction', purpose: 'expresses purpose',
};

function functionalAlreadyInGloss(item, gloss) {
    const value = item.value.toLowerCase().replace(/^indicates? /, '');
    const text = String(gloss || '').toLowerCase();
    return (value === 'purpose' && /\b(?:in order to|so that)\b/.test(text))
        || (value === 'destination' && /\b(?:towards|in the direction of|homewards)\b/.test(text));
}

export function readableSenseNote(value) {
    const text = String(value || '').trim();
    const match = /^(?:used to indicate|indicating|indicates) (place|time|mode|material|characteristics|content)$/i.exec(text);
    if (match) return ({place: 'place', time: 'time', mode: 'manner', material: 'material', characteristics: 'characteristics', content: 'contents'})[match[1].toLowerCase()];
    return text
        .replace(/^used to indicate\s+/i, 'indicates ')
        .replace(/^used to express\s+/i, 'expresses ')
        .replace(/^used to (ask|introduce|describe|refer|define)\b/i, (_, verb) => ({ask:'asks', introduce:'introduces', describe:'describes', refer:'refers', define:'defines'}[verb.toLowerCase()]))
        .replace(/^used with\s+/i, 'with ')
        .replace(/^used in\s+/i, 'in ');
}

export function contextCollidesWithMetadata(context, items) {
    const text = String(context || '').trim();
    if (!text) return false;
    return (items || []).some(item => {
        const display = senseMetadataDisplay(item);
        return metadataTextIsRedundant(text, display.short)
            || metadataTextIsRedundant(text, display.full)
            || metadataTextIsRedundant(text, item.value);
    });
}

export function senseMetadataDisplay(item, options = {}) {
    if (item.family === 'companion') {
        const token = String(item.value || '').trim();
        return { short: `with ${token}`, full: `with ${token}` };
    }
    if (item.family === 'construction') {
        if (item.kind === 'required_case') return { short: `takes ${item.value} case`, full: `takes ${item.value} case` };
        // Canonical frame kinds are intentionally provider-neutral. Give their
        // atomic values enough syntax to remain clear to a learner: a bare
        // "infinitive" is ambiguous, while "+ infinitive" reads as a frame.
        if (item.kind === 'complement_form') {
            return { short: `followed by ${item.value === "infinitive" ? "an infinitive" : item.value}`, full: `used with ${item.value}` };
        }
        if (item.kind === 'argument_type') {
            return { short: `with ${item.value}`, full: `used with ${item.value}` };
        }
        if (item.kind === 'polarity_context') {
            return { short: `in ${item.value} forms`, full: `used in ${item.value} forms` };
        }
        if (item.kind === 'clause_context') {
            return { short: `in ${item.value}`, full: `used in ${item.value}` };
        }
        const full = String(item.value || '').replace(/^\[|\]$/g, '');
        return { short: readableSenseNote(full), full };
    }
    if (item.family === 'functional') {
        const label = item.sourceText || item.value;
        const canonical = item.value.replace(/^indicates? /i, '').toLowerCase();
        const distinctSource = (options.peerMeanings || []).some(peer => senseMetadataItems(peer).some(other =>
            other.family === 'functional' && other.value === item.value
            && other.sourceText && other.sourceText !== item.sourceText));
        if (distinctSource) return { short: readableSenseNote(label), full: label };
        return { short: FUNCTION_LABELS[canonical] || readableSenseNote(label), full: label };
    }
    if (item.family === 'grammar') {
        if (item.components?.length) {
            const values = item.components.map(part => part.value);
            const imperative = values.includes('mood=imperative');
            if (imperative) return { short: 'command', full: item.sourceText || item.value };
            if (values.includes('person=2') && values.includes('number=plural') && /\byour\b/i.test(options.gloss || '')) {
                return { short: 'addressing several people', full: item.sourceText || item.value };
            }
            const labels = item.components.map(part => senseMetadataDisplay(part).short);
            return { short: [...new Set(labels)].join(' · '), full: item.sourceText || item.value };
        }
        const exact = ({
            'reflexive=true': 'reflexive',
            'mood=imperative': 'command',
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
        return { short: item.value, full: item.value };
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
        || (item.family === 'functional' && item.kind !== 'semantic_relation' && item.kind !== 'discourse_function')
        || item.family === 'source'
        || (item.family === 'construction' && item.kind === 'optional_companion')
        || (item.family === 'register'
            && SUPPORTING_REGISTER_VALUES.has(item.value.toLocaleLowerCase('en')));
}

export function senseMetadataHTML(meaning, active, options = {}) {
    if (!active && !options.allowInactivePrimary) return '';
    const items = compactLearnerSenseMetadata(senseMetadataItems(meaning), meaning, options);
    const senseCount = Number(options?.senseCount) || 1;
    const isDense = senseCount >= 3;
    const isVeryDense = senseCount >= 5;

    const renderItems = (values, isPillTier = true) => values.map((item) => {
        const display = senseMetadataDisplay(item, options);
        const family = escapeCardText(item.family);
        const shortLabel = escapeCardText(display.short);
        const fullLabel = escapeCardText(display.full);
        if (!isPillTier || display.short.length > 28 || item.family === 'functional') {
            return `<span class="sense-metadata-detail" data-family="${family}" title="${family}: ${fullLabel}" aria-label="${fullLabel}">${shortLabel}</span>`;
        }
        const isCompanion = item.family === 'companion';
        const isSyntax = item.family === 'construction';
        const pillClass = `sense-metadata-detail sense-pill sense-pill--${family}${isSyntax ? ' sense-pill--syntax' : ''}${isCompanion ? ' sense-pill--companion sense-pill--privileged' : ''}`;
        const titleAttr = isCompanion
            ? `Used with &quot;${escapeCardText(item.value)}&quot;`
            : `${family}: ${fullLabel}`;
        const ariaLabel = isCompanion
            ? `Used with ${escapeCardText(item.value)}`
            : fullLabel;
        const labelHTML = isCompanion
            ? `<span class="sense-pill-label"><span class="sense-pill-prefix">with</span> <span class="sense-pill-token">${escapeCardText(item.value)}</span></span>`
            : `<span class="sense-pill-label">${shortLabel}</span>`;
        return `<span class="${pillClass}" data-family="${family}" title="${titleAttr}" aria-label="${ariaLabel}">${labelHTML}</span>`;
    }).join('');

    const primary = items.filter(item => (
        ['construction', 'companion', 'register', 'domain', 'functional'].includes(item.family)
    ));
    // Grammar that changes which sense applies is a navigation cue. Routine
    // inflectional detail is still available, but does not compete with the
    // gloss and example until the learner asks for it.
    const grammar = items.filter(item => item.family === 'grammar');
    const visibleKeys = new Set(items.map(metadataItemKey));
    const baseSupporting = active ? senseMetadataItems(meaning).filter(item =>
        item.family === 'grammar' && !isSenseDefiningGrammar(item)
        && !visibleKeys.has(metadataItemKey(item))
        && !grammarIsAlreadyInGloss(item, options.gloss || meaning?.meaning || meaning?.translation || '')
        && !(options.peerMeanings || []).some(peer => senseMetadataItems(peer).some(p => metadataItemKey(p) === metadataItemKey(item)))
    ) : [];

    let displayPrimary = primary;
    let supporting = baseSupporting;

    if (!active && options.allowInactivePrimary) {
        if (!displayPrimary.length && !grammar.length) return '';
        const densityClass = isVeryDense ? ' is-dense is-very-dense' : (isDense ? ' is-dense' : '');
        const primaryHTML = displayPrimary.length
            ? `<span class="sense-metadata-tier sense-metadata-tier--primary">${renderItems(displayPrimary, true)}</span>`
            : '';
        const grammarHTML = grammar.length
            ? `<span class="sense-metadata-tier sense-metadata-tier--grammar">${renderItems(grammar, false)}</span>`
            : '';
        return `<span class="sense-metadata-list${densityClass}" aria-label="Sense details">${primaryHTML}${grammarHTML}</span>`;
    }

    if (!displayPrimary.length && !grammar.length && !supporting.length) return '';
    const densityClass = isVeryDense ? ' is-dense is-very-dense' : (isDense ? ' is-dense' : '');
    const primaryHTML = displayPrimary.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--primary">${renderItems(displayPrimary, true)}</span>`
        : '';
    const grammarHTML = grammar.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--grammar">${renderItems(grammar, false)}</span>`
        : '';
    const supportingHTML = supporting.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--details${supporting.length === 1 ? ' is-single' : ''}" hidden>${renderItems(supporting, false)}</span>`
        : '';
    const more = supporting.length > 0
        ? `<button type="button" class="sense-metadata-more" aria-expanded="false" onclick="toggleSenseMetadataOverflow(event, this)" data-count="${supporting.length}" aria-label="Show ${supporting.length} supporting details"><span class="sense-metadata-more-label">More details</span><span class="sense-metadata-more-count">${supporting.length}</span></button>`
        : '';
    return `<span class="sense-metadata-list${densityClass}" aria-label="Sense details">${primaryHTML}${grammarHTML}${more}${supportingHTML}</span>`;
}

export function contextWithoutSenseMetadata(meaning, active, options = {}) {
    const context = String(meaning?.context || '').trim();
    if (!context) return context;
    const items = compactLearnerSenseMetadata(senseMetadataItems(meaning), meaning, options);
    const gloss = options.gloss || meaning?.meaning || meaning?.translation || '';
    const sourceItems = senseMetadataItems(meaning);
    const represented = items.flatMap(item => [item, ...(item.components || [])]);
    // Grammatical facts already expressed by the English cue need not be
    // repeated as raw prose after being deliberately removed from metadata.
    const redundant = sourceItems.filter(item =>
        grammarIsAlreadyInGloss(item, gloss)
        && !(item.value.startsWith('definiteness=') && options.peerMeanings?.length)
        || (isInflectionalPersonNumber(item) && /^(?:his|her|its|their|my|our|me|us)$/i.test(gloss))
        || (item.family === 'construction' && /^(?:intransitive|transitive|ditransitive)$/.test(item.value)
            && items.some(visible => visible.family === 'companion' || visible.kind === 'required_case'))
    );
    const clauses = splitSenseMetadataClauses(context);
    const residual = clauses.filter(clause => ![...represented, ...redundant].some(item => {
        const display = senseMetadataDisplay(item, options);
        // Exact source spans only. The presence of an unrelated canonical
        // tag does not establish that any of this prose is represented.
        return [item.value, item.sourceText, display.short, display.full]
            .some(value => foldMetadataComparable(value) === foldMetadataComparable(clause));
    }));
    return residual.length === clauses.length ? context : residual.join('; ');
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

export function scoreSenseMetadata(item) {
    if (!item) return 0;
    const family = item.family;
    const kind = item.kind;
    const val = String(item.value || '').toLowerCase();

    // Tier 1 (Score 100): Semantic Qualifier / Context
    if (family === 'context' || kind === 'qualifier' || (family === 'source' && kind === 'qualifier')) {
        return 100;
    }
    // Tier 2 (Score 80): Syntax / Grammatical Construction Frame, Functional Relations & Privileged Companions
    if (family === 'companion') {
        return 80;
    }
    if (family === 'functional') {
        return 80;
    }
    if (family === 'construction') {
        if (['reflexive', 'refl.', 'pronominal', 'impersonal', 'copulative'].includes(val)
            || item.kind === 'complement_form'
            || item.kind === 'argument_type'
            || item.kind === 'clause_context'
            || item.kind === 'object_role') {
            return 80;
        }
        // Plain transitive / intransitive tags alone are less informative when the gloss is identical,
        // but still qualify as differentiators when no higher-tier cue exists.
        if (['transitive', 'intransitive', 'ditransitive'].includes(val)) {
            return 60;
        }
        return 80;
    }
    // Tier 3 (Score 60): Domain and Register
    if (family === 'domain') {
        return 60;
    }
    if (family === 'register') {
        if (SUPPORTING_REGISTER_VALUES.has(val)) return 20;
        return 60;
    }
    // Sense defining grammar (e.g. reflexive=true, personal-infinitive, plural-only)
    if (family === 'grammar' && isSenseDefiningGrammar(item)) {
        return 60;
    }
    // Tier 4 (Score 10): Low-level inflection, technical grammar, routine source notes
    return 10;
}

export function resolveMeaningDifferentiator(meaning, peerMeanings, gloss = '', cleanContextFn = null) {
    if (!meaning) return null;
    const rawContext = meaning.context || '';
    const cleanedContext = cleanContextFn ? cleanContextFn(meaning, gloss) : rawContext;

    // Check if cleaned context differs from all peers
    const peerCleanedContexts = (peerMeanings || [])
        .filter(p => p !== meaning)
        .map(p => (cleanContextFn ? cleanContextFn(p, gloss) : (p.context || '')).trim().toLowerCase());

    const myCtxNorm = cleanedContext.trim().toLowerCase();
    if (myCtxNorm && !peerCleanedContexts.includes(myCtxNorm)) {
        return {
            score: 100,
            type: 'context',
            label: cleanedContext,
        };
    }

    // Check metadata items
    const items = senseMetadataItems(meaning);
    const peerItems = (peerMeanings || [])
        .filter(p => p !== meaning)
        .flatMap(p => senseMetadataItems(p).map(it => `${it.family}\u0000${String(it.value || '').toLowerCase()}`));
    const peerItemsSet = new Set(peerItems);

    let bestDiff = null;
    for (const item of items) {
        const key = `${item.family}\u0000${String(item.value || '').toLowerCase()}`;
        if (peerItemsSet.has(key)) continue; // Not unique to this meaning
        const score = scoreSenseMetadata(item);
        if (!bestDiff || score > bestDiff.score) {
            const display = senseMetadataDisplay(item);
            bestDiff = {
                score,
                type: item.family,
                label: display.short,
                item,
            };
        }
    }
    return bestDiff;
}

// Window attachments for inline HTML onclick handlers
if (typeof window !== 'undefined') {
    window.toggleSenseMetadataChip = toggleSenseMetadataChip;
    window.toggleSenseMetadataOverflow = toggleSenseMetadataOverflow;
    window.scoreSenseMetadata = scoreSenseMetadata;
    window.resolveMeaningDifferentiator = resolveMeaningDifferentiator;
    window.compactLearnerSenseMetadata = compactLearnerSenseMetadata;
    window.metadataTextIsRedundant = metadataTextIsRedundant;
}
