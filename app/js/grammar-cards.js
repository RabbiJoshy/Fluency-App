// Display-only sibling-sense collapse for a keep-list of function words.
// Does not re-score WSD. Merges published leaves and slash-joins their glosses.

const LANGUAGE_ALIASES = {
    spanish: 'es',
    portuguese: 'pt',
    czech: 'cs',
    french: 'fr',
    es: 'es',
    pt: 'pt',
    cs: 'cs',
    fr: 'fr',
};

export const GRAMMAR_CARDS = {
    es: {
        que: {
            note: 'than / to are the comparison use',
            groups: [
                { pos: 'CCONJ', translations: ['than', 'to'], contextIncludes: 'comparison' },
            ],
        },
        de: {
            note: 'of / from / in / with sit on one preposition',
            groups: [
                { pos: 'ADP' },
            ],
        },
        a: {
            note: 'to / at sit on one preposition',
            groups: [
                {
                    pos: 'ADP',
                    translations: ['to', 'at'],
                    contextExcludes: 'personal',
                },
            ],
        },
        lo: {
            note: 'it / him / you are one Spanish form here',
            groups: [
                { pos: 'PRON', translations: ['it', 'him', 'you'], contextIncludes: 'direct object' },
            ],
        },
        un: {
            note: 'a and an are one Spanish article',
            groups: [
                { pos: 'DET', translations: ['a', 'an'] },
            ],
        },
        una: {
            note: 'a and an are one Spanish article',
            groups: [
                { pos: 'DET', translations: ['a', 'an'] },
            ],
        },
        al: {
            note: 'a + el',
            pairs: [
                { surface: 'a', label: 'a' },
                { surface: 'el', label: 'el' },
            ],
            groups: [
                { pos: 'CONTRACTION' },
                { pos: 'ADP' },
            ],
        },
        le: {
            note: 'him / her / you are one dative form',
            groups: [
                { pos: 'PRON', translations: ['him', 'her', 'you'], contextIncludes: 'indirect object' },
            ],
        },
        del: {
            note: 'de + el',
            pairs: [
                { surface: 'de', label: 'de' },
                { surface: 'el', label: 'el' },
            ],
            groups: [
                { pos: 'CONTRACTION' },
            ],
        },
        se: {
            note: 'himself / herself / itself / themselves are one form',
            groups: [
                { pos: 'PRON', contextIncludes: 'reflexive' },
            ],
        },
    },
};

export function grammarLanguageKey(language) {
    const raw = String(language || '').toLowerCase();
    return LANGUAGE_ALIASES[raw] || raw;
}

export function grammarCardSpec(language, surface) {
    const lang = grammarLanguageKey(language);
    const word = String(surface || '').normalize('NFC').toLocaleLowerCase();
    return GRAMMAR_CARDS[lang]?.[word] || null;
}

function glossOf(meaning) {
    return String(meaning?.translation || meaning?.meaning || '').trim();
}

function matchesGroup(meaning, group) {
    if (!meaning || !group) return false;
    if (group.pos && meaning.pos !== group.pos) return false;
    if (group.translations?.length) {
        const gloss = glossOf(meaning).toLowerCase();
        if (!group.translations.some(t => t.toLowerCase() === gloss)) return false;
    }
    const context = String(meaning.context || '').toLowerCase();
    if (group.contextIncludes && !context.includes(String(group.contextIncludes).toLowerCase())) {
        return false;
    }
    if (group.contextExcludes && context.includes(String(group.contextExcludes).toLowerCase())) {
        return false;
    }
    return true;
}

function uniqueJoin(values, sep = ' / ') {
    const seen = new Set();
    const out = [];
    for (const value of values) {
        const text = String(value || '').trim();
        if (!text) continue;
        const key = text.toLowerCase();
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(text);
    }
    return out.join(sep);
}

function cloneMeaning(meaning) {
    return {
        ...meaning,
        examples: (meaning.examples || []).map(example => ({ ...example })),
        regions: Array.isArray(meaning.regions) ? [...meaning.regions] : meaning.regions,
        allExamples: Array.isArray(meaning.allExamples)
            ? meaning.allExamples.map(example => ({ ...example }))
            : meaning.allExamples,
    };
}

function exampleKey(example) {
    return String(example?.target || example?.text || example?.spanish || example?.example_spanish || '').trim();
}

export function mergeGrammarMeanings(meanings, groups) {
    if (!Array.isArray(meanings) || !meanings.length || !Array.isArray(groups) || !groups.length) {
        return meanings || [];
    }
    const assigned = new Set();
    const merged = [];
    for (const group of groups) {
        const members = [];
        meanings.forEach((meaning, index) => {
            if (assigned.has(index)) return;
            if (!matchesGroup(meaning, group)) return;
            assigned.add(index);
            members.push(meaning);
        });
        if (!members.length) continue;
        if (members.length === 1) {
            merged.push(members[0]);
            continue;
        }
        const joinedGloss = uniqueJoin(members.map(glossOf));
        const contexts = [...new Set(members.map(m => String(m.context || '').trim()).filter(Boolean))];
        const examples = [];
        const seenExamples = new Set();
        for (const member of members) {
            for (const example of (member.examples || [])) {
                const key = exampleKey(example);
                if (key && seenExamples.has(key)) continue;
                if (key) seenExamples.add(key);
                examples.push({ ...example });
            }
        }
        const frequency = members.reduce((sum, member) => (
            sum + (Number.parseFloat(member.display_frequency ?? member.frequency) || 0)
        ), 0);
        const first = members[0];
        merged.push({
            ...cloneMeaning(first),
            translation: joinedGloss,
            meaning: joinedGloss,
            context: contexts.length === 1 ? contexts[0] : '',
            examples,
            frequency: String(frequency),
            display_frequency: String(frequency),
            _grammarMerged: true,
            _mergedSenseIds: members.map(m => m.sense_id || m.senseId || m.id).filter(Boolean),
        });
    }
    meanings.forEach((meaning, index) => {
        if (!assigned.has(index)) merged.push(meaning);
    });
    return merged;
}

export function applyGrammarCardOverlay(item, language) {
    if (!item) return null;
    if (Array.isArray(item._grammarSourceMeanings)) {
        item.meanings = item._grammarSourceMeanings.map(cloneMeaning);
    }
    const spec = grammarCardSpec(language, item.word || item.targetWord || item.displaySurface);
    if (!spec) {
        delete item._grammarCard;
        return null;
    }
    const source = Array.isArray(item.meanings) ? item.meanings : [];
    item._grammarSourceMeanings = source.map(cloneMeaning);
    item.meanings = mergeGrammarMeanings(source, spec.groups || []);
    item._grammarCard = {
        note: spec.note || '',
        pairs: spec.pairs || [],
    };
    return spec;
}

export function grammarCardChrome(itemOrCard) {
    return itemOrCard?._grammarCard
        || (itemOrCard?.grammarNote || itemOrCard?.grammarPairs
            ? { note: itemOrCard.grammarNote || '', pairs: itemOrCard.grammarPairs || [] }
            : null);
}
