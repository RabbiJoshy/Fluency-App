import { flagImgHTML, regionFlagCode } from './flags.js?v=c931a393';

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
    const display = (remaining || text).replace(/^syncopic form of\s+/i, 'informal form of ');
    return {
        display,
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
        .map((item, index) => item.family === 'grammar' && item.kind !== 'surface_mark'
            && /^(?:person|number|mood|tense)=/.test(item.value) ? index : -1)
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

function grammarNavigationCue(item) {
    if (item?.family !== 'grammar') return false;
    const value = String(item.value || '').toLowerCase();
    return item.kind === 'combined_sense_mark'
        || /(?:first|second|third|1st|2nd|3rd)[ -]person/.test(value)
        || /\bformal\b.*\b(?:singular|plural)\b/.test(value)
        || /\b(?:singular|plural)\b.*\b(?:personal )?pronoun\b/.test(value);
}

export function compactLearnerSenseMetadata(items, meaning, options = {}) {
    const gloss = String(options.gloss || meaning?.meaning || meaning?.translation || '');
    const peers = Array.isArray(options.peerMeanings) ? options.peerMeanings.filter(p => p !== meaning) : [];
    const peerKeys = peers.map(peer => new Set(senseMetadataItems(peer).map(metadataItemKey)));
    const differs = item => peerKeys.length > 0 && peerKeys.some(keys => !keys.has(metadataItemKey(item)));
    const hasCompanion = items.some(item => item.family === 'companion' || item.kind === 'required_case');
    const kept = (items || []).filter(item => {
        if (options.excludeCompanion && (item.family === 'companion' || (item.family === 'construction' && item.kind === 'optional_companion'))) return false;
        if (item.family === 'grammar' && item.kind === 'surface_mark') return false;
        const display = senseMetadataDisplay(item, { gloss });
        if (item.family === 'register' && SUPPORTING_REGISTER_VALUES.has(item.value.toLowerCase())) return false;
        if (options.sharedContext && [item.value, item.sourceText, display.short, display.full].some(value => metadataTextIsRedundant(value, options.sharedContext))) return false;
        if (grammarIsAlreadyInGloss(item, gloss)) return false;
        if (item.family === 'register' && item.value.toLowerCase() === 'colloquial'
            && /^informal form of\b/i.test(gloss)) return false;
        if (gloss && [display.short, display.full, item.value].some(value => metadataTextIsRedundant(value, gloss))) return false;
        if (item.family === 'functional' && functionalAlreadyInGloss(item, gloss)) return false;
        if (isInflectionalPersonNumber(item) && !differs(item) && !/\byour\b/i.test(gloss)) return false;
        if (item.family === 'construction' && /^(?:intransitive|transitive|ditransitive)$/.test(item.value)
            && !differs(item) && (hasCompanion || (peers.length && meaning?.context))) return false;
        if (usefulRegister(item)) return true;
        // A routine grammatical mark may be useful in details, but is not a
        // substitute for the semantic context that distinguishes these rows.
        if (item.family === 'grammar' && !isSenseDefiningGrammar(item) && !grammarNavigationCue(item)
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
    return ((/possibility|doubt/.test(value)) && /\b(?:perhaps|maybe|possibly)\b/.test(text))
        || (value === 'purpose' && /\b(?:in order to|so that)\b/.test(text))
        || (value === 'destination' && /\b(?:towards|in the direction of|homewards)\b/.test(text));
}

export function readableSenseNote(value) {
    const clauses = String(value || '').trim().split(/;\s*/);
    const seen = new Set();
    const text = clauses.filter(clause => {
        const key = clause.trim().toLowerCase();
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    }).join('; ');
    const match = /^(?:used to indicate|indicating|indicates) (place|time|mode|material|characteristics|content)$/i.exec(text);
    if (match) return ({place: 'place', time: 'time', mode: 'manner', material: 'material', characteristics: 'characteristics', content: 'contents'})[match[1].toLowerCase()];
    return text
        // Dictionary frame notation becomes prose after the semantic cue.
        .replace(/^\[(.+?)\]\s*\|\s*(.+)$/u, '$2 ($1)')
        .replace(/^used to indicate\s+/i, 'indicates ')
        .replace(/^used to express\s+/i, 'expresses ')
        .replace(/^used to talk about\s+/i, 'about ')
        .replace(/^used in forming\s+/i, 'forms ')
        .replace(/^used to (elicit|give|make|call)\b/i, (_, verb) => ({elicit:'elicits', give:'gives', make:'makes', call:'calls'}[verb.toLowerCase()]))
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
        if (item.kind === 'combined_frame') return { short: item.value, full: item.value };
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
        if (item.kind === 'surface_summary') return { short: item.value, full: item.value };
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
        const learnerPhrase = String(item.value || '').toLowerCase();
        if (/^personal (?:second|2nd)[ -]person plural$/.test(learnerPhrase)) {
            return { short: 'plural', full: item.sourceText || item.value };
        }
        if (/(?:second|2nd)[ -]person plural/.test(learnerPhrase)) {
            return { short: 'addressing several people', full: item.sourceText || item.value };
        }
        if (/formal.*(?:second|2nd)[ -]person singular|(?:second|2nd)[ -]person singular.*formal/.test(learnerPhrase)) {
            return { short: 'formal singular', full: item.sourceText || item.value };
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
        || item.kind === 'surface_summary'
        || grammarNavigationCue(item)
        || /^(?:countability|definiteness|formation|function|mood|noun-class|number|person|polarity|position|pronoun-class|pronoun-use|tense|verb-class|voice|word-class)=/u.test(item.value)
        || new Set([
            'reflexive=true',
            'form=personal-infinitive',
            'number=plural-only',
            'number=no-plural',
            'number=singular-only',
        ]).has(item.value);
}

function metadataPresentationRole(item) {
    if (!item) return 'supporting';
    if (item.family === 'companion'
        || (item.family === 'construction' && [
            'required_case', 'combined_frame', 'complement_form', 'argument_type',
            'clause_context', 'object_role', 'polarity_context',
        ].includes(item.kind))) return 'production';
    if (item.family === 'register' || item.family === 'domain') return 'usage';
    if (grammarNavigationCue(item) || item.kind === 'surface_summary') return 'navigation';
    return 'supporting';
}

function metadataItemsDiffer(item, peers) {
    if (!peers.length) return false;
    const key = metadataItemKey(item);
    return peers.some(peer => !senseMetadataItems(peer).some(candidate => metadataItemKey(candidate) === key));
}

function requiredCaseVaries(item, relatedMeanings) {
    if (item.kind !== 'required_case' || !relatedMeanings.length) return false;
    const cases = new Set();
    for (const related of relatedMeanings) {
        for (const candidate of senseMetadataItems(related)) {
            if (candidate.kind === 'required_case') cases.add(String(candidate.value || '').toLowerCase());
        }
    }
    return cases.size > 1;
}

function surfaceGrammarSummary(items) {
    const values = new Map();
    for (const item of items) {
        if (item.family !== 'grammar' || item.kind !== 'surface_mark') continue;
        const match = /^(case|gender|number)=(.+)$/u.exec(item.value);
        if (!match) continue;
        if (!values.has(match[1])) values.set(match[1], []);
        values.get(match[1]).push(match[2]);
    }
    const gender = [...new Set(values.get('gender') || [])]
        .filter(value => !['feminine', 'masculine'].every(candidate => values.get('gender')?.includes(candidate)));
    const number = [...new Set(values.get('number') || [])];
    const caseOrder = ['nominative', 'accusative', 'genitive', 'dative', 'instrumental', 'locative', 'vocative'];
    let cases = [...new Set(values.get('case') || [])]
        .sort((left, right) => caseOrder.indexOf(left) - caseOrder.indexOf(right));
    if (cases.length > 1) cases = cases.filter(value => value !== 'vocative');
    const caseLabels = {
        nominative: 'nom.', accusative: 'acc.', genitive: 'gen.', dative: 'dat.',
        instrumental: 'inst.', locative: 'loc.', vocative: 'voc.',
    };
    const labels = [
        ...gender.map(value => value.replace(/-/g, ' ')),
        ...number.map(value => value.replace(/-/g, ' ')),
        cases.map(value => caseLabels[value] || value.replace(/-/g, ' ')).join('/'),
    ].filter(Boolean);
    if (!labels.length) return null;
    return {
        family: 'grammar',
        kind: 'surface_summary',
        value: labels.join(' · '),
        components: items.filter(item => item.family === 'grammar' && item.kind === 'surface_mark'),
        sourceIndex: Number.MAX_SAFE_INTEGER,
    };
}

function senseSurfaceGrammarItems(meaning) {
    const metadata = meaning?.metadata || {};
    const canonical = metadata.sense_metadata || {};
    const features = [
        ...(Array.isArray(canonical.features) ? canonical.features : []),
        ...(Array.isArray(meaning?.specialist_features) ? meaning.specialist_features : []),
        ...(Array.isArray(metadata.specialist_features) ? metadata.specialist_features : []),
    ];
    const seen = new Set();
    return features.filter(feature => {
        if (feature?.family !== 'grammar' || feature.kind !== 'surface_mark' || !feature.value) return false;
        const key = String(feature.value).toLowerCase();
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    }).map((feature, sourceIndex) => ({
        family: 'grammar',
        kind: 'surface_mark',
        value: String(feature.value),
        sourceText: String(feature.embedding_text || ''),
        sourceIndex,
    }));
}

function combineLearnerMetadata(items, meaning, options = {}) {
    const combined = [...items];
    const frameIndex = combined.findIndex(item => item.family === 'construction'
        && /^(?:reflexive|pronominal) with\s+([^\s;,.]+)/iu.test(item.value));
    const companionIndex = combined.findIndex(item => item.family === 'companion');
    if (frameIndex >= 0 && companionIndex >= 0) {
        const reflexive = /^(?:reflexive|pronominal) with\s+([^\s;,.]+)/iu.exec(combined[frameIndex].value)?.[1];
        const companion = String(combined[companionIndex].value || '').trim();
        const headword = String(meaning?.headword || options.targetWord || '').trim();
        if (reflexive && companion) {
            const components = [combined[frameIndex], combined[companionIndex]];
            combined.splice(Math.max(frameIndex, companionIndex), 1);
            combined.splice(Math.min(frameIndex, companionIndex), 1);
            combined.unshift({
                family: 'construction',
                kind: 'combined_frame',
                value: `${headword ? `${headword} ` : ''}${reflexive} ${companion}…`,
                sourceText: components.map(item => item.sourceText || item.value).join('; '),
                components,
                sourceIndex: Math.min(...components.map(item => item.sourceIndex ?? 0)),
            });
        }
    }
    return combined.filter((item, index, values) => {
        const components = values.flatMap(value => value.components || []);
        if (components.some(component => metadataItemKey(component) === metadataItemKey(item))) return false;
        const label = senseMetadataDisplay(item, options).short.toLocaleLowerCase('en');
        if (values.some((candidate, candidateIndex) => candidateIndex !== index
            && candidate.family === item.family
            && senseMetadataDisplay(candidate, options).short.length > label.length
            && metadataTextIsRedundant(label, senseMetadataDisplay(candidate, options).short))) return false;
        return values.findIndex(candidate => senseMetadataDisplay(candidate, options).short.toLocaleLowerCase('en') === label) === index;
    });
}

function contextAfterMetadataPolicy(meaning, represented, options = {}) {
    const context = String(meaning?.context || '').trim();
    if (!context) return context;
    const gloss = options.gloss || meaning?.meaning || meaning?.translation || '';
    const sourceItems = senseMetadataItems(meaning);
    const redundant = sourceItems.filter(item =>
        grammarIsAlreadyInGloss(item, gloss)
        || (isInflectionalPersonNumber(item) && /^(?:his|her|its|their|my|our|me|us)$/i.test(gloss))
        || (item.family === 'construction' && /^(?:intransitive|transitive|ditransitive)$/i.test(item.value)
            && represented.some(visible => visible.family === 'companion'
                || visible.kind === 'required_case' || visible.kind === 'combined_frame'))
    );
    const comparable = [...represented, ...redundant].flatMap(item => [item, ...(item.components || [])]);
    const clauses = splitSenseMetadataClauses(context);
    const residual = clauses.filter(clause => {
        if (/^informal form of\b/i.test(gloss) && /^colloquial$/i.test(clause)) return false;
        return !comparable.some(item => {
            const display = senseMetadataDisplay(item, options);
            return [item.value, item.sourceText, display.short, display.full]
                .some(value => foldMetadataComparable(value) === foldMetadataComparable(clause));
        });
    });
    return residual.length === clauses.length ? context : residual.join('; ');
}

function splitLearnerContextClauses(value) {
    const text = String(value || '').trim();
    const clauses = [];
    let depth = 0;
    let start = 0;
    for (let index = 0; index < text.length; index++) {
        const character = text[index];
        if ('([{'.includes(character)) depth++;
        else if (')]}'.includes(character) && depth) depth--;
        else if ((character === ';' || character === '|') && depth === 0) {
            const clause = text.slice(start, index).trim();
            if (clause) clauses.push(clause);
            start = index + 1;
        }
    }
    const final = text.slice(start).trim();
    if (final) clauses.push(final);
    return clauses;
}

function compactLearnerContextClause(value) {
    return readableSenseNote(value)
        .replace(/^\.\.\.because\s+/i, '')
        .replace(/^it has already been mentioned$/i, 'already mentioned')
        .replace(/^it is presumed to be definitely known in context or from shared knowledge$/i, 'known from context/shared knowledge')
        .replace(/^is to be completely specified in the same sentence$/i, 'specified in this sentence')
        .replace(/^or very shortly thereafter$/i, 'or shortly afterwards')
        .replace(/^indicates that what follows is exceptional$/i, '')
        .trim();
}

function learnerContextByRule(value, gloss = '') {
    const visible = [];
    const detail = [];
    const seenVisible = new Set();
    const seenDetail = new Set();
    const glossIsVerb = /^to\s/i.test(String(gloss).trim());
    for (const source of splitLearnerContextClauses(value)) {
        const readable = readableSenseNote(source).trim();
        const readableKey = foldMetadataComparable(readable);
        if (readable && readableKey && !seenDetail.has(readableKey)) {
            seenDetail.add(readableKey);
            detail.push(readable);
        }
        const compact = compactLearnerContextClause(source);
        const key = foldMetadataComparable(compact);
        if (!compact || !key || seenVisible.has(key)) continue;
        // "to own; to possess" under "to have" is a synonym list, not a cue.
        const synonym = glossIsVerb && /^to\s/i.test(compact);
        if (synonym || !isLabelLikeText(compact)) continue;
        seenVisible.add(key);
        visible.push(compact);
    }
    const visibleContext = visible.join('; ');
    const fullDetail = detail.join('; ');
    return {
        visibleContext,
        detailContext: foldMetadataComparable(visibleContext) === foldMetadataComparable(fullDetail) ? '' : fullDetail,
    };
}

function learnerContextBudget(value, active, senseCount, roomForInlineDetails = false) {
    const sourceClauses = splitLearnerContextClauses(value);
    const sourceSeen = new Set();
    const sourceForDetails = [];
    const seen = new Set();
    const clauses = [];
    for (const source of sourceClauses) {
        const readable = readableSenseNote(source).trim();
        const sourceKey = foldMetadataComparable(readable);
        if (readable && sourceKey && !sourceSeen.has(sourceKey)) {
            sourceSeen.add(sourceKey);
            sourceForDetails.push(readable);
        }
        const compact = compactLearnerContextClause(source);
        const key = foldMetadataComparable(compact);
        if (!compact || !key || seen.has(key)) continue;
        seen.add(key);
        clauses.push(compact);
    }
    const full = clauses.join('; ');
    const fullDetail = sourceForDetails.join('; ');
    if (!full) return { visibleContext: '', detailContext: '' };

    const count = Math.max(1, Number(senseCount) || 1);
    const budget = roomForInlineDetails ? 104 : (count === 1 ? 120 : (active ? 72 : 52));
    if (full.length <= budget) {
        return {
            visibleContext: full,
            detailContext: foldMetadataComparable(full) === foldMetadataComparable(fullDetail) ? '' : fullDetail,
        };
    }

    // Prefer short, concrete alternatives over a dictionary's explanatory
    // preamble: “indicates that …; quite a; quite the” becomes the useful
    // learner cue “quite a; quite the”. Source order is otherwise preserved.
    const concise = clauses.filter(clause => clause.length <= 36
        && !/^(?:indicates?|expresses?|refers?|used to|where\b)/i.test(clause));
    const candidates = concise.length ? concise : clauses;
    const chosen = [];
    for (const clause of candidates) {
        const next = [...chosen, clause].join('; ');
        if (next.length > budget) break;
        chosen.push(clause);
        if (chosen.length === 2) break;
    }
    let visible = chosen.join('; ');
    if (!visible) {
        // Do not leave the learner with an arbitrary half-sentence. If no
        // complete detachable clause fits, keep the explanation in the note.
        return { visibleContext: '', detailContext: fullDetail };
    }
    return {
        visibleContext: visible,
        detailContext: foldMetadataComparable(visible) === foldMetadataComparable(fullDetail)
            ? '' : fullDetail,
    };
}

function glossParentheticalParts(value) {
    const text = String(value || '').trim();
    if (!text.endsWith(')')) return null;
    let depth = 0;
    for (let index = text.length - 1; index >= 0; index--) {
        if (text[index] === ')') depth++;
        else if (text[index] === '(') {
            depth--;
            if (depth === 0 && index > 0) {
                return {
                    before: text.slice(0, index).trim(),
                    inside: text.slice(index + 1, -1).trim(),
                };
            }
        }
    }
    return null;
}

function compactGlossClause(value, budget) {
    let text = String(value || '').trim();
    if (text.length <= budget) return text;

    // Dictionary glosses often place an editorial explanation after a useful
    // first clause. Keep the source wording, but move the explanation to the
    // optional note instead of making it the learner's primary translation.
    let depth = 0;
    for (let index = 0; index < text.length; index++) {
        const character = text[index];
        if ('([{'.includes(character)) depth++;
        else if (')]}'.includes(character) && depth) depth--;
        else if (character === ',' && depth === 0) {
            const suffix = text.slice(index + 1).trim();
            if (/^(?:especially|contrasting|which|where|when|usually|chiefly|literally|figuratively|used\b)/i.test(suffix)) {
                const prefix = text.slice(0, index).trim();
                if (prefix.length >= 3 && prefix.length <= budget) return prefix;
            }
        }
    }

    const parenthetical = glossParentheticalParts(text);
    if (parenthetical && parenthetical.before && parenthetical.inside.length > 36) {
        const firstQualifier = splitLearnerContextClauses(parenthetical.inside)[0] || '';
        const withQualifier = firstQualifier && firstQualifier.length <= 28
            && !/^(?:used|indicates?|expresses?|refers?)\b/i.test(firstQualifier)
            ? `${parenthetical.before} (${firstQualifier})`
            : parenthetical.before;
        text = withQualifier.length <= budget ? withQualifier : parenthetical.before;
    }
    return text;
}

function glossProjectionKey(value) {
    return foldMetadataComparable(String(value || '').replace(/…$/u, ''));
}

function compactGlossDistinction(value) {
    const text = readableSenseNote(value);
    if (!text) return '';
    if (text.length <= 44) return text;

    // Keep a short source phrase when the dictionary has supplied a useful
    // semantic key inside a much longer editorial parenthetical. This gives
    // repeated learner glosses (for example two readings of “because”) a
    // natural second line without manufacturing a new label.
    const semanticPrefix = text.match(
        /^(introduces?\s+(?:(?:an?|the)\s+)?(?:explanation|reason|cause|condition|contrast|result|purpose|question|alternative|comparison|consequence))\b/i
    );
    if (semanticPrefix) return semanticPrefix[1];

    const firstClause = splitLearnerContextClauses(text)[0] || '';
    return firstClause.length <= 44 ? firstClause : '';
}

function glossDistinctionKey(source, visibleGloss) {
    const parenthetical = glossParentheticalParts(source);
    if (!parenthetical || !parenthetical.before || !parenthetical.inside) return '';
    if (glossProjectionKey(parenthetical.before) !== glossProjectionKey(visibleGloss)) return '';
    return compactGlossDistinction(parenthetical.inside);
}

// Wiktionary-derived glosses append the English word's own definition in
// brackets: "king (male monarch)", "to wake up (to stop being sleepy)". The
// translation already says it; the definition belongs in the information
// note. It stays on the row only where it does work:
//   - another sense on this card has the same translation, so the brackets
//     are what tells the two apart ("to leave (to refrain from taking)");
//   - the translation is a bare function word ("in (wearing)", "of (in
//     relation to)") or ends on a preposition ("offended by (a comment)");
//   - it restricts use rather than defining ("said of weather", "especially").
// Argument slots such as "(something)" or "(someone)" are never touched.
// "to" counts only before a person or thing ("(to someone)"), never before a
// verb: "(to cause to die)" is a definition.
const GLOSS_SLOT_PARENTHETICAL = /^(?:some(?:one|thing|body|where)|oneself|one's|its|their|his|her|with|of|from|for|at|on|in|by|about|to (?:some(?:one|thing|body|where)|oneself|one's|a|an|the|him|her|them|me|us))\b/i;
const GLOSS_RESTRICTING_PARENTHETICAL = /^(?:said of|of (?:a|an|the)\b|in (?:a|an|the)\b|when\b|especially\b|usually\b|chiefly\b|often\b|figuratively\b|informal|colloquial|slang|vulgar|dated|archaic|obsolete)/i;
const FUNCTION_WORD_POS = /^(?:adp|prep|preposition|postp|det|determiner|article|pron|pronoun|part|particle|conj|cconj|sconj|conjunction)$/i;

function splitDefinitionParenthetical(text) {
    // The first top-level bracket that is not an argument slot, followed by
    // nothing or by a comma/full stop continuing the explanation.
    let depth = 0;
    let open = -1;
    for (let index = 0; index < text.length; index++) {
        const character = text[index];
        if (character === '(') {
            if (depth === 0) open = index;
            depth++;
        } else if (character === ')' && depth) {
            depth--;
            if (depth !== 0 || open <= 0) continue;
            const inside = text.slice(open + 1, index).trim();
            const rest = text.slice(index + 1).trim();
            // An earlier bracket followed by more text ("yours (singular)
            // (that or those…)", "to be still (doing something) (to not…)")
            // is part of the translation; the definition is the next one.
            if (rest && !/^[,.;]/.test(rest)) continue;
            return { before: text.slice(0, open).trim().replace(/[,;:]$/, '').trim(), inside, rest };
        }
    }
    return null;
}

function glossBase(meaning) {
    const display = projectWiktionaryGloss(meaning, meaning?.meaning || meaning?.translation || '').display;
    const split = splitDefinitionParenthetical(String(display || '').trim());
    return split ? split.before : String(display || '').trim();
}

// A row shows labels, not definitions. A label names a sense or a use in a
// few words ("to depart", "when stressed", "already mentioned"); a
// definition is a sentence ("to be related in some way to…", "…because it is
// presumed to be definitely known…"). Definitions, and synonym lists, belong
// in the information note. The test is what the text is, not how much room
// is left on the row.
const DEFINITION_MARKERS = /^(?:\.\.\.|…)|\b(?:that|which|who|whom|whose|because|whether|rather than|such as|e\.g\.|i\.e\.|eg:|instead of|as opposed to|in order to|so that)\b|:/i;
const DEFINITION_OPENERS = /^(?:used|indicates?|introduces?|describes?|signif(?:y|ies)|expresses?|refers?|denotes?|connects?|forms?|serves?|shows?|asks?|negates?|modifies?|makes?|gives?|is|are|was|has|having|being|any|one|someone|something|anything)\b/i;
const LABEL_MAX_WORDS = 4;

export function isLabelLikeText(value) {
    const text = String(value || '').trim();
    if (!text) return false;
    if (DEFINITION_MARKERS.test(text) || DEFINITION_OPENERS.test(text)) return false;
    // "or shortly afterwards" continues the previous clause; it is not a label.
    if (/^(?:or|and|but|nor)\b/i.test(text)) return false;
    return text.split(/\s+/).length <= LABEL_MAX_WORDS;
}

// A gloss clause that describes the word instead of translating it
// ("second-person singular personal pronoun, formal or informal in Brazil").
function isDescriptiveGlossClause(value) {
    const text = String(value || '').trim();
    return DEFINITION_MARKERS.test(text) || DEFINITION_OPENERS.test(text)
        || /\b(?:pronoun|article|determiner|conjunction|preposition|particle|suffix|prefix|possessive|spelling|form of)\b/i.test(text);
}

const EDITORIAL_SUFFIX = /,\s*(?:especially|contrasting|which|where|when|usually|chiefly|literally|figuratively|as opposed|rather than|used|indicates?|introduces?|describes?|expresses?|refers?|denotes?|forms?|serves?|makes?)\b.*$/i;
// "first-person plural nominative personal pronoun: we" → "we".
const PRONOUN_DESCRIPTION = /^(?:[\w-]+\s+){1,6}?pronoun\b:?\s+(?:used in all positions\s+)?(?!,)(.+)$/i;

// "because (introduces a reason for …)" → "introduces a reason": a named
// semantic role the source itself states, usable as a label.
function semanticRoleLabel(value) {
    const match = String(value || '').match(
        /^(introduces?\s+(?:(?:an?|the)\s+)?(?:explanation|reason|cause|condition|contrast|result|purpose|question|alternative|comparison|consequence))\b/i
    );
    return match ? match[1] : '';
}

function senseSharesTranslation(meaning, before, options) {
    const clauses = new Set(splitLearnerContextClauses(before).map(foldMetadataComparable).filter(Boolean));
    return (options.cardMeanings || []).some(peer => {
        if (!peer || peer === meaning) return false;
        return splitLearnerContextClauses(glossBase(peer))
            .some(clause => clauses.has(foldMetadataComparable(clause)));
    });
}

// The grammatical head of a definition: what it says before its first
// qualifying clause. "to be an example or type of, or the same as" → "to be
// an example or type of"; "connects two clauses indicating that…" →
// "connects two clauses".
function definitionHead(value) {
    const text = readableSenseNote(value).trim().replace(/^(?:\.\.\.|…)\s*/, '');
    const cut = text.search(/,|;|\s(?:that|which|who|whom|because|whether|rather than|such as|indicating|especially|with the|in order)\b/i);
    return (cut > 0 ? text.slice(0, cut) : text).trim();
}

// Returns the row's gloss and optional key when the rules change the source,
// or null when the source already reads as a translation.
function ruleBasedGloss(meaning, source, options) {
    const partOfSpeech = String(meaning?.pos || meaning?.part_of_speech || '');
    let key = '';
    const removed = [];
    const rewritten = splitLearnerContextClauses(source).map(clause => {
        let text = clause.replace(EDITORIAL_SUFFIX, '').trim() || clause;
        const described = text.match(PRONOUN_DESCRIPTION);
        if (described && !isDescriptiveGlossClause(described[1])) text = described[1].trim();
        const split = splitDefinitionParenthetical(text);
        if (!split || !split.before || split.before.length < 2) return text;
        const { before, inside } = split;
        // Argument slots and usage restrictions are part of the translation.
        if (GLOSS_SLOT_PARENTHETICAL.test(inside) && inside.split(/\s+/).length <= LABEL_MAX_WORDS) return text;
        if (GLOSS_RESTRICTING_PARENTHETICAL.test(inside) && isLabelLikeText(inside)) return text;
        if (/\b(?:by|of|to|with|for|on|in|at|from|about|into|than|as)$/i.test(before) && isLabelLikeText(inside)) return text;
        // A label in brackets stays where it is needed to read the row: to
        // tell two senses with the same translation apart, or to give a bare
        // grammar word ("in (wearing)") its sense.
        const needed = senseSharesTranslation(meaning, before, options)
            || FUNCTION_WORD_POS.test(partOfSpeech)
            || (!/\s/.test(before) && before.length <= 3);
        if (needed && isLabelLikeText(inside)) return `${before} (${inside})`;
        if (needed && !key) key = semanticRoleLabel(inside);
        removed.push(inside);
        return before;
    });
    // Describing clauses give way when the gloss also has a real translation:
    // "second-person singular personal pronoun, …; you" → "you".
    // When every clause describes, the first one says it; the rest are notes.
    const translations = rewritten.filter(clause => !isDescriptiveGlossClause(clause));
    const kept = translations.length ? translations : rewritten.slice(0, 1);
    removed.push(...rewritten.filter(clause => !kept.includes(clause)));
    const visibleGloss = kept.join('; ');
    // Two senses must never read alike. If this gloss now matches another
    // sense on the card, the row carries one distinguishing label: the head
    // of whatever the source says about this sense and not the other.
    // Only a gloss with nothing of its own collides: "to be; to cost" is
    // already told apart by "to cost".
    const ownClauses = splitLearnerContextClauses(visibleGloss);
    // A region or register cue ("Brazil", "colloquial") already tells the row
    // apart.
    const hasOwnLabel = senseMetadataItems(meaning).some(item => item.family === 'register'
        && !SUPPORTING_REGISTER_VALUES.has(String(item.value || '').toLocaleLowerCase('en')));
    const collides = !hasOwnLabel && ownClauses.length > 0
        && ownClauses.every(clause => senseSharesTranslation(meaning, clause, options));
    if (!key && collides) {
        const glossKey = foldMetadataComparable(visibleGloss);
        const cueValues = new Set(senseMetadataItems(meaning)
            .flatMap(item => [item.value, item.sourceText]).map(foldMetadataComparable).filter(Boolean));
        const candidates = [...removed, ...splitLearnerContextClauses(meaning?.context || '')]
            .map(text => {
                // "to have (to be related in some way to…)" repeats the gloss.
                const inner = splitDefinitionParenthetical(String(text));
                return inner && foldMetadataComparable(inner.before) === glossKey ? inner.inside : text;
            })
            .map(definitionHead)
            .filter(text => text && foldMetadataComparable(text) !== glossKey
                && !cueValues.has(foldMetadataComparable(text))
                && !/^(?:transitive|intransitive|copulative|impersonal|pronominal|auxiliary|reflexive)\b/i.test(text));
        const labels = candidates.filter(isLabelLikeText);
        key = (labels[0] || candidates[0] || '');
    }
    if (foldMetadataComparable(visibleGloss) === foldMetadataComparable(source) && !key) return null;
    return { visibleGloss, visibleKey: key };
}

// Source-preserving projection for the bold learner-facing meaning. It never
// rewrites a definition: it selects complete source clauses where possible,
// and keeps the full projected gloss for the optional sense note.
export function learnerGlossPresentation(meaning, active, options = {}) {
    const source = String(options.gloss
        ?? projectWiktionaryGloss(meaning, meaning?.meaning || meaning?.translation || '').display
        ?? '').trim();
    if (!source) return { visibleGloss: '', visibleKey: '', noteGloss: '' };
    const ruled = options.keepDefinitionParenthetical ? null : ruleBasedGloss(meaning, source, options);
    if (ruled) {
        const unchanged = foldMetadataComparable(ruled.visibleGloss) === foldMetadataComparable(source);
        return { ...ruled, noteGloss: unchanged ? '' : source };
    }
    if (options.ignoreBudget) return { visibleGloss: source, visibleKey: '', noteGloss: '' };

    const senseCount = Math.max(1, Number(options.senseCount) || 1);
    const budget = senseCount === 1 ? 84 : (active ? 64 : 48);
    if (source.length <= budget) return { visibleGloss: source, visibleKey: '', noteGloss: '' };

    const clauses = splitLearnerContextClauses(source);
    const conciseClauses = clauses.filter(clause => clause.length <= 32
        && !/^(?:indicates?|expresses?|modifies?|refers?|used to|where\b)/i.test(clause));
    const candidates = clauses[0]?.length > budget && conciseClauses.length
        ? conciseClauses
        : clauses;
    const clauseLimit = senseCount === 1 ? 3 : 2;
    const chosen = [];
    for (const clause of candidates) {
        const compact = compactGlossClause(clause, budget);
        if (!compact) continue;
        const next = [...chosen, compact].join('; ');
        if (next.length > budget) break;
        chosen.push(compact);
        if (chosen.length >= clauseLimit) break;
    }
    let visibleGloss = chosen.join('; ')
        || compactGlossClause(candidates[0] || clauses[0] || source, budget);

    // If shortening would make this row visually collide with a peer whose
    // complete meaning is different, retain more of this row's first clause.
    const peers = Array.isArray(options.peerMeanings) ? options.peerMeanings : [];
    const visibleProjectionKey = glossProjectionKey(visibleGloss);
    const collision = options.preservePeerGlossDistinction !== false && peers.some(peer => {
        const peerSource = projectWiktionaryGloss(
            peer,
            peer?.meaning || peer?.translation || ''
        ).display;
        if (!peerSource || foldMetadataComparable(peerSource) === foldMetadataComparable(source)) return false;
        return glossProjectionKey(compactGlossClause(splitLearnerContextClauses(peerSource)[0] || peerSource, budget)) === visibleProjectionKey;
    });
    if (collision) {
        visibleGloss = clauses[0] || source;
    }

    const noteGloss = foldMetadataComparable(visibleGloss) === foldMetadataComparable(source)
        ? ''
        : source;
    const visibleKey = noteGloss ? glossDistinctionKey(source, visibleGloss) : '';
    return { visibleGloss, visibleKey, noteGloss };
}

// One policy surface for every dictionary adapter. Extraction stays faithful
// to the release contract; this selector decides what earns space on a card.
export function learnerSensePresentation(meaning, active, options = {}) {
    const sourceItems = senseMetadataItems(meaning);
    const compact = compactLearnerSenseMetadata(sourceItems, meaning, options);
    let candidates = combineLearnerMetadata(compact, meaning, options);
    const senseCount = Math.max(1, Number(options.senseCount) || 1);
    const partOfSpeech = String(meaning?.pos || meaning?.part_of_speech || '').toLowerCase();
    if (senseCount === 1 && /^(?:pron|pronoun|det|determiner|article)$/.test(partOfSpeech)) {
        const surfaceSummary = surfaceGrammarSummary(senseSurfaceGrammarItems(meaning));
        if (surfaceSummary) candidates.push(surfaceSummary);
    }

    const peers = Array.isArray(options.peerMeanings) ? options.peerMeanings.filter(peer => peer !== meaning) : [];
    const related = (options.cardMeanings || []).filter(peer => peer !== meaning
        && (peer.headword || '') === (meaning?.headword || '')
        && (peer.pos || peer.part_of_speech || '') === (meaning?.pos || meaning?.part_of_speech || ''));
    const ranked = candidates.map(item => {
        const role = metadataPresentationRole(item);
        const distinguishing = metadataItemsDiffer(item, peers) || requiredCaseVaries(item, related);
        const roleScore = ({ production: 400, usage: 300, navigation: 250, supporting: 100 })[role];
        return { item, role, distinguishing, score: (distinguishing ? 1000 : 0) + roleScore + scoreSenseMetadata(item) };
    }).sort((left, right) => right.score - left.score || (left.item.sourceIndex ?? 0) - (right.item.sourceIndex ?? 0));

    let visible = [];
    if (options.ignoreBudget) {
        // Importance, not selection or spare space, determines visible cues.
        visible = ranked.filter(entry => entry.role !== 'supporting'
            || ['semantic_relation', 'temporal_relation', 'discourse_function'].includes(entry.item.kind)
            || isSenseDefiningGrammar(entry.item))
            .map(entry => entry.item);
    } else if (!active && !options.allowInactivePrimary) {
        visible = [];
    } else if (senseCount === 1) {
        visible = ranked.filter(entry => entry.role !== 'supporting').slice(0, 2).map(entry => entry.item);
    } else if (!active) {
        visible = ranked.filter(entry => entry.distinguishing || entry.role === 'navigation')
            .slice(0, 1).map(entry => entry.item);
    } else {
        const differentiator = ranked.find(entry => entry.distinguishing);
        if (differentiator) visible.push(differentiator.item);
        const useful = ranked.find(entry => !visible.includes(entry.item)
            && ['production', 'usage', 'navigation'].includes(entry.role));
        if (useful) visible.push(useful.item);
        visible = visible.slice(0, 2);
    }

    // A semantic context is already the more natural navigation label. Do not
    // append technical metadata to an inactive row unless it is a construction
    // the learner must actually produce (for example a companion or case).
    const semanticContext = contextAfterMetadataPolicy(meaning, candidates, options);
    if (!options.ignoreBudget && !active && semanticContext) {
        visible = visible.filter(item => metadataPresentationRole(item) === 'production');
    }

    const visibleKeys = new Set(visible.map(metadataItemKey));
    const hardDetails = sourceItems.filter(item => {
        if (item.family === 'source' || item.kind === 'surface_mark') return false;
        if (item.family === 'grammar' && /^(?:gender|number|person)=/.test(item.value)) return false;
        if (visible.some(shown => shown.kind === 'combined_frame')
            && ((item.family === 'grammar' && item.value === 'reflexive=true')
                || (item.family === 'construction' && /^(?:reflexive|pronominal)$/i.test(item.value)))) return false;
        if (options.excludeCompanion && item.family === 'companion') return false;
        if (item.family === 'register' && SUPPORTING_REGISTER_VALUES.has(item.value.toLowerCase())) return false;
        const gloss = options.gloss || meaning?.meaning || meaning?.translation || '';
        if (grammarIsAlreadyInGloss(item, gloss)) return false;
        if (item.family === 'functional' && functionalAlreadyInGloss(item, gloss)) return false;
        if (item.family === 'register' && item.value.toLowerCase() === 'colloquial'
            && /^informal form of\b/i.test(gloss)) return false;
        return !visibleKeys.has(metadataItemKey(item));
    });
    const allDetails = combineLearnerMetadata([
        ...candidates.filter(item => !visibleKeys.has(metadataItemKey(item))),
        ...hardDetails,
    ], meaning, options).filter(item => {
                if (item.family === 'grammar' && item.value === 'degree=not-comparable') return false;
                if (visible.some(shown => shown.kind === 'combined_frame')
                    && ((item.family === 'grammar' && item.value === 'reflexive=true')
                        || (item.family === 'construction' && /^(?:reflexive|pronominal)$/i.test(item.value)))) return false;
                return !visible.some(shown => metadataTextIsRedundant(
                    senseMetadataDisplay(item, options).short,
                    senseMetadataDisplay(shown, options).short
                ));
            });
    const details = active ? allDetails : [];
    const represented = combineLearnerMetadata([...visible, ...details, ...candidates], meaning, options);
    const residualContext = contextAfterMetadataPolicy(meaning, represented, options);
    // Rows keep the context's labels ("when stressed", "already mentioned")
    // and send its definitions and synonym lists to the note.
    const contextPresentation = options.ignoreBudget
        ? learnerContextByRule(residualContext, options.gloss || meaning?.meaning || meaning?.translation || '')
        : learnerContextBudget(
        residualContext,
        active,
        senseCount,
        Boolean(options.roomForInlineDetails)
    );
    const glossPresentation = learnerGlossPresentation(meaning, active, {
        ...options,
        senseCount,
        peerMeanings: peers,
    });
    const rankedByKey = new Map(ranked.map(entry => [metadataItemKey(entry.item), entry]));
    const individuallyNoteworthy = item => {
        const entry = rankedByKey.get(metadataItemKey(item));
        if (item.family === 'companion' || item.family === 'domain') return true;
        if (item.family === 'register') {
            return !SUPPORTING_REGISTER_VALUES.has(String(item.value || '').toLocaleLowerCase('en'));
        }
        if (item.family === 'construction') {
            return ['required_case', 'complement_form', 'argument_type', 'clause_context',
                'object_role', 'context_phrase', 'gloss_phrase', 'combined_frame'].includes(item.kind)
                || /^(?:with|takes?|only in|only with|connecting|followed by)\b/i.test(item.value);
        }
        return Boolean(entry?.distinguishing
            && item.family === 'grammar' && isSenseDefiningGrammar(item));
    };
    const visibleContextKeys = new Set(splitLearnerContextClauses(contextPresentation.visibleContext)
        .map(foldMetadataComparable).filter(Boolean));
    const contextRemainder = splitLearnerContextClauses(contextPresentation.detailContext)
        .filter(clause => !visibleContextKeys.has(foldMetadataComparable(clause)));
    const contextOnlyExplainsVisible = Boolean(contextPresentation.visibleContext && contextRemainder.length)
        && contextRemainder.every(clause => /^(?:indicates?|expresses?|refers?|used to)\b/i.test(clause));
    const noteContext = contextOnlyExplainsVisible ? '' : contextPresentation.detailContext;
    const noteworthyItems = allDetails.filter(individuallyNoteworthy);
    const shortConstruction = noteworthyItems.find(item => item.family === 'construction'
        && /^(?:connecting|only in|only with|followed by)\b/i.test(
            senseMetadataDisplay(item, options).short
        )
        && senseMetadataDisplay(item, options).short.length <= 28)
        || allDetails.find(item => senseMetadataDisplay(item, options).short === 'interrogative');
    const inlineAdditions = options.ignoreBudget
        ? noteworthyItems.filter(item => metadataPresentationRole(item) === 'production')
        : options.roomForInlineDetails
        ? noteworthyItems.slice(0, 1)
        : (shortConstruction ? [shortConstruction] : []);
    const inlineKeys = new Set(inlineAdditions.map(metadataItemKey));
    const visibleWithRoom = combineLearnerMetadata([...visible, ...inlineAdditions], meaning, options);
    const remainingNoteworthyItems = noteworthyItems.filter(item => !inlineKeys.has(metadataItemKey(item)));
    const supportingItems = options.ignoreBudget ? [] : allDetails.filter(item => !noteworthyItems.includes(item));
    const noteItems = [
        ...remainingNoteworthyItems,
        ...((glossPresentation.noteGloss || noteContext || supportingItems.length >= 2)
            ? supportingItems : []),
    ];
    const hasSenseNote = Boolean(glossPresentation.noteGloss || noteContext || noteItems.length);
    // Canonical learner-facing contract. Dictionary/provider fields are input;
    // every language leaves this selector as exactly three presentation tiers:
    // a required gloss, an optional compact key, and an optional curated note.
    // The flat fields below remain as compatibility aliases while renderers
    // migrate to these named slots.
    const gloss = glossPresentation.visibleGloss;
    const key = {
        text: contextPresentation.visibleContext || glossPresentation.visibleKey || '',
        items: visibleWithRoom,
    };
    const note = {
        gloss: glossPresentation.noteGloss,
        context: noteContext,
        items: noteItems,
        available: hasSenseNote,
    };
    return {
        gloss,
        key,
        note,
        grammar: { items: visibleWithRoom.filter(isGrammarCue) },
        visibleItems: visibleWithRoom,
        detailItems: details,
        residualContext,
        visibleContext: contextPresentation.visibleContext,
        detailContext: contextPresentation.detailContext,
        visibleGloss: glossPresentation.visibleGloss,
        visibleKey: glossPresentation.visibleKey,
        noteGloss: glossPresentation.noteGloss,
        noteContext,
        noteItems,
        hasSenseNote,
    };
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

function senseNoteSectionHTML(title, values, className) {
    const seen = new Set();
    const clean = [];
    for (const value of values) {
        const text = String(value || '').trim();
        const key = foldMetadataComparable(text);
        if (!text || !key || seen.has(key)) continue;
        seen.add(key);
        clean.push(text);
    }
    if (!clean.length) return '';
    return `<section class="sense-note-section sense-note-section--${className}"><h3>${title}</h3>${clean.map(value => `<p>${escapeCardText(value)}</p>`).join('')}</section>`;
}

export function senseNoteHTML(presentation, options = {}) {
    const note = presentation.note || {
        gloss: presentation.noteGloss,
        context: presentation.noteContext,
        items: presentation.noteItems || [],
        available: presentation.hasSenseNote,
    };
    if (!note.available) return '';
    const usage = [];
    const production = [];
    if (note.context) usage.push(note.context);
    for (const item of note.items) {
        const label = senseMetadataDisplay(item, options).full;
        if (!label) continue;
        if (['companion', 'construction', 'grammar'].includes(item.family)) production.push(label);
        else usage.push(label);
    }
    const body = [
        senseNoteSectionHTML('Meaning', [note.gloss], 'meaning'),
        senseNoteSectionHTML('Usage', usage, 'usage'),
        senseNoteSectionHTML('How it is used', production, 'production'),
    ].join('');
    if (!body) return '';
    const title = presentation.gloss || presentation.visibleGloss || options.gloss || 'This meaning';
    return `<button type="button" class="sense-note-trigger" aria-haspopup="dialog" onclick="openSenseNote(event, this)" aria-label="Information about this meaning" title="Information about this meaning"><span aria-hidden="true">i</span></button><template class="sense-note-template"><div class="sense-note-copy" data-sense-note-title="${escapeCardText(title)}">${body}</div></template>`;
}

export function grammarCueCategory(item) {
    if (item.family === 'companion' || (item.family === 'construction'
        && !SENSE_CONSTRUCTION_TAGS.has(item.value))) return 'construction';
    if (item.family === 'grammar' && /^(?:person|number|gender|tense|mood|aspect|degree|case)=/.test(item.value)
        || item.kind === 'surface_summary') return 'form';
    return 'function';
}

export function isGrammarCue(item) {
    return ['grammar', 'construction', 'companion'].includes(item.family);
}

export function senseMetadataHTML(meaning, active, options = {}) {
    options = { ignoreBudget: true, ...options };
    if (!active && !options.allowInactivePrimary) return '';
    const presentation = learnerSensePresentation(meaning, active, options);
    const senseCount = Number(options?.senseCount) || 1;
    const isDense = senseCount >= 3;
    const isVeryDense = senseCount >= 5;

    const privilegedRegions = new Set((options.privilegedRegions || [])
        .map(region => regionFlagCode(region)).filter(Boolean));
    const renderItems = (values, isPillTier = true) => values.map((item) => {
        const display = senseMetadataDisplay(item, options);
        // A country reads as its flag alone; the name stays in the tooltip
        // and for screen readers. A language's privileged variety (Brazil,
        // for Portuguese) leads the row beside the information button.
        const flagCode = item.family === 'register' && item.kind === 'region' ? regionFlagCode(item.value) : '';
        if (flagCode) {
            const leading = privilegedRegions.has(flagCode) ? ' sense-region-flag--leading' : '';
            return `<span class="sense-metadata-detail sense-region-flag${leading}" data-family="register" role="img" title="${escapeCardText(item.value)}" aria-label="${escapeCardText(item.value)}">${flagImgHTML(flagCode)}</span>`;
        }
        const family = escapeCardText(item.family);
        const category = isGrammarCue(item) ? ` data-grammar-category="${grammarCueCategory(item)}"` : '';
        const shortLabel = escapeCardText(display.short);
        const fullLabel = escapeCardText(display.full);
        if (!isPillTier || display.short.length > 28 || item.family === 'functional') {
            return `<span class="sense-metadata-detail" data-family="${family}"${category} title="${family}: ${fullLabel}" aria-label="${fullLabel}">${shortLabel}</span>`;
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

    const keyItems = presentation.key?.items || presentation.visibleItems;
    const displayPrimary = options.hideVisibleItems
        ? []
        : keyItems.filter(item => !isGrammarCue(item));
    const grammar = options.hideVisibleItems
        ? []
        : keyItems.filter(isGrammarCue);
    const noteHTML = senseNoteHTML(presentation, options);

    if (!active && options.allowInactivePrimary) {
        if (!displayPrimary.length && !grammar.length && !noteHTML) return '';
        const densityClass = isVeryDense ? ' is-dense is-very-dense' : (isDense ? ' is-dense' : '');
        const primaryHTML = displayPrimary.length
            ? `<span class="sense-metadata-tier sense-metadata-tier--primary">${renderItems(displayPrimary, true)}</span>`
            : '';
        const grammarHTML = grammar.length
            ? `<span class="sense-metadata-tier sense-metadata-tier--grammar sense-grammar-cue">${renderItems(grammar, false)}</span>`
            : '';
        return `<span class="sense-metadata-list${densityClass}" aria-label="Sense information">${primaryHTML}${grammarHTML}${noteHTML}</span>`;
    }

    if (!displayPrimary.length && !grammar.length && !noteHTML) return '';
    const densityClass = isVeryDense ? ' is-dense is-very-dense' : (isDense ? ' is-dense' : '');
    const primaryHTML = displayPrimary.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--primary">${renderItems(displayPrimary, true)}</span>`
        : '';
    const grammarHTML = grammar.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--grammar sense-grammar-cue">${renderItems(grammar, false)}</span>`
        : '';
    return `<span class="sense-metadata-list${densityClass}" aria-label="Sense information">${primaryHTML}${grammarHTML}${noteHTML}</span>`;
}

export function contextWithoutSenseMetadata(meaning, active, options = {}) {
    return learnerSensePresentation(meaning, active, options).residualContext;
}

export function toggleSenseMetadataChip(event, chip) {
    event?.preventDefault?.();
    event?.stopPropagation?.();
    if (!chip) return;
    const expanded = chip.getAttribute('aria-expanded') === 'true';
    chip.textContent = decodeURIComponent(expanded ? chip.dataset.short : chip.dataset.full);
    chip.setAttribute('aria-expanded', String(!expanded));
}

export function openSenseNote(event, control) {
    event?.preventDefault?.();
    event?.stopPropagation?.();
    if (!control || typeof document === 'undefined') return;
    const template = control.parentElement?.querySelector?.('.sense-note-template');
    const source = template?.content?.querySelector?.('.sense-note-copy');
    if (!source) return;

    document.querySelector('.sense-note-overlay')?.remove();
    const title = source.dataset.senseNoteTitle || 'This meaning';
    const overlay = document.createElement('div');
    overlay.className = 'sense-note-overlay';
    overlay.innerHTML = `<div class="sense-note-dialog" role="dialog" aria-modal="true" aria-labelledby="senseNoteTitle" tabindex="-1"><button type="button" class="sense-note-close" aria-label="Close sense note">×</button><div class="sense-note-eyebrow">About this meaning</div><h2 id="senseNoteTitle">${escapeCardText(title)}</h2><div class="sense-note-body"></div></div>`;
    overlay.querySelector('.sense-note-body').append(...source.cloneNode(true).children);
    document.body.appendChild(overlay);

    const dialog = overlay.querySelector('.sense-note-dialog');
    const closeButton = overlay.querySelector('.sense-note-close');
    const close = () => {
        document.removeEventListener('keydown', onKey);
        overlay.remove();
        control.focus?.({ preventScroll: true });
    };
    const onKey = keyEvent => {
        if (keyEvent.key === 'Escape') close();
        else if (keyEvent.key === 'Tab') {
            keyEvent.preventDefault();
            closeButton.focus();
        }
    };
    overlay.addEventListener('click', clickEvent => {
        if (clickEvent.target === overlay) close();
    });
    dialog.addEventListener('click', clickEvent => clickEvent.stopPropagation());
    closeButton.addEventListener('click', close);
    document.addEventListener('keydown', onKey);
    dialog.focus({ preventScroll: true });
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

export function extractSenseCompanion(meaning) {
    if (!meaning) return null;
    const items = senseMetadataItems(meaning);
    const companionItem = items.find(i => i.family === 'companion');
    const optCompanionItem = items.find(i => i.family === 'construction' && i.kind === 'optional_companion');

    let qualifier = null;
    let terms = [];
    let isOptional = false;

    if (companionItem) {
        terms.push(String(companionItem.value || '').replace(/["“”]/g, '').trim());
    } else if (optCompanionItem) {
        isOptional = true;
        const val = String(optCompanionItem.value || '').trim();
        const m = /\b(often|frequently|sometimes)\s+used with\s+["“]?([^"”]+)["”]?/iu.exec(val);
        if (m) {
            qualifier = m[1].toLowerCase();
            terms.push(m[2].replace(/["“”]/g, '').trim());
        } else {
            qualifier = 'often';
            terms.push(val.replace(/^(?:often|frequently|sometimes)\s+used with\s+/iu, '').replace(/["“”]/g, '').trim());
        }
    } else if (typeof meaning.context === 'string') {
        const match = /\b(?:(often|frequently|sometimes)\s+)?used with\s+(.+)$/iu.exec(meaning.context);
        if (match) {
            qualifier = (match[1] || '').toLowerCase() || null;
            isOptional = Boolean(qualifier);
            const rawTail = match[2].trim().replace(/[.;]+$/u, '');
            const quoted = [...rawTail.matchAll(/["“]([^"”]+)["”]/gu)].map(m => m[1].trim());
            if (quoted.length) {
                terms.push(...quoted);
            } else {
                const clean = rawTail.replace(/^an?\s+/iu, '').trim();
                terms.push(clean);
            }
        }
    }

    terms = [...new Set(terms.map(t => t.trim()).filter(Boolean))];
    if (!terms.length) return null;

    return {
        terms,
        qualifier,
        isOptional,
    };
}

export function senseCollocationHTML(meaning, card = null) {
    const comp = extractSenseCompanion(meaning);
    if (!comp) return '';
    const baseWord = card?.targetWord || card?.word || meaning?.headword || '';
    const lemma = card?.citationForm || card?.lemma || meaning?.headword || baseWord;
    const target = escapeCardText(lemma || baseWord);
    if (!target) return '';
    const particle = escapeCardText(comp.terms.join(' / '));
    const isOptional = comp.isOptional;
    const qualifier = comp.qualifier ? escapeCardText(comp.qualifier) : '';
    const titleAttr = isOptional
        ? (qualifier ? `${qualifier} used with: ${target} + ${particle}` : `Used with: ${target} + ${particle}`)
        : `Used with: ${target} ${particle}`;

    // The partner word is a privileged cue, not a sub-meaning: a compact
    // "+de" that the row places at its leading edge beside the information
    // button. The lemma is already the card's headword, so only the partner
    // is printed; the full "precisar de" stays in the tooltip.
    const qualifierTag = qualifier ? `<span class="sense-collocation-qualifier">${qualifier}</span> ` : '';
    return `<span class="sense-target-collocation sense-companion-lead${isOptional ? ' is-optional' : ''}" title="${titleAttr}" aria-label="${titleAttr}">${qualifierTag}<span class="sense-collocation-particle">+${particle}</span></span>`;
}

// Window attachments for inline HTML onclick handlers
if (typeof window !== 'undefined') {
    window.toggleSenseMetadataChip = toggleSenseMetadataChip;
    window.openSenseNote = openSenseNote;
    window.scoreSenseMetadata = scoreSenseMetadata;
    window.resolveMeaningDifferentiator = resolveMeaningDifferentiator;
    window.compactLearnerSenseMetadata = compactLearnerSenseMetadata;
    window.metadataTextIsRedundant = metadataTextIsRedundant;
    window.extractSenseCompanion = extractSenseCompanion;
    window.senseCollocationHTML = senseCollocationHTML;
}
