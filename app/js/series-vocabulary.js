// Series admission is independent of dictionary coverage. Never drop an unknown
// form or merge it with a lemma; definitions and entity candidates are metadata.
import { standaloneWordMeanings } from './lexical-guards.js?v=42901562';

export const SERIES_ADMISSION_POLICY = 'all-forms-v1';
let seriesLexiconPromise;
export async function loadSeriesLexicon() {
    if (!seriesLexiconPromise) {
        seriesLexiconPromise = fetch(new URL('../data/series/spanish-lexicon.json?v=all-forms-v1', import.meta.url))
            .then(response => {
                if (!response.ok) throw new Error(`Series dictionary HTTP ${response.status}`);
                return response.json();
            })
            .catch(error => { seriesLexiconPromise = null; throw error; });
    }
    return seriesLexiconPromise;
}

export function completeSeriesVocabulary(deck, { assets = {}, extra50k = {}, lexicon = {} } = {}) {
    const menus = {}, menuIds = new Map();
    const summary = { cards: 0, dictionaryCards: 0, entityCandidates: 0, pendingDefinitions: 0,
        cardsWithTranslatedExamples: 0 };
    for (const [word, entry] of Object.entries(deck.surfaces || {})) {
        const recognized = deck.intake?.surfaces?.[word];
        const definition = (lexicon.entries || lexicon)[word];
        const curated = assets.dictionary?.[word];
        const entity = definition?.entity || assets.curatedEntities?.[word] || null;
        // A frequency-list entry is not a definition. Published Wiktionary
        // form-of paths may supply a menu, but never change the card's surface.
        const meanings = standaloneWordMeanings(word,
            (definition?.meanings || lexicon.menus?.[definition?.meaningMenu])?.length
                ? (definition.meanings || lexicon.menus[definition.meaningMenu]) : (curated?.meanings || []), deck.language)
            .map(meaning => ({ ...meaning, assignment_method: 'unassigned' }));
        const frequencyRank = recognized?.frequencyRank || extra50k.ranks?.[word] || null;
        if (!meanings.length && entity && !recognized?.inStudyInventory && !frequencyRank
            && ['person', 'place', 'location', 'brand', 'work'].includes(entity.entityType || entity.entity_type)) {
            meanings.push({ pos: 'PROPN', translation: entity.englishTitle || entity.canonicalTitle || word,
                context: 'name · entity candidate', headword: word, source: entity.source || 'curated',
                assignment_method: 'unassigned' });
        }
        const hasDefinition = meanings.length > 0;
        if (recognized?.inStudyInventory && curated) {
            // Existing Speech rows keep their canonical menu and shard rank.
            // Do not bundle a second dictionary copy for these 6k+ cards.
            entry.card = {id: curated.id, word, sourceRank: curated.rank,
                definitionSource: 'speech', _indexRowsPending: true};
        } else {
            const menu = hasDefinition ? meanings : [{ pos: '', translation: '',
                context: 'Definition pending', unassigned: true, assignment_method: 'unassigned' }];
            const key = JSON.stringify(menu);
            if (!menuIds.has(key)) {
                const id = `menu-${menuIds.size + 1}`;
                menuIds.set(key, id);
                menus[id] = menu;
            }
            entry.card = {
                id: curated?.id || definition?.id || `series:es:${word}`, word, lemma: word,
                // Inline-only cards must never request a Speech definition shard at
                // their series study rank. -1 is outside every canonical shard.
                sourceRank: -1, definitionSource: 'inline', _indexRowsPending: false,
                meaningMenu: menuIds.get(key),
                surfaceGrammar: definition?.surfaceGrammar || null,
                definitionStatus: hasDefinition ? 'available' : 'pending', frequencyRank,
                entityCandidate: entity, entityRecognition: definition?.entityRecognition || 'curated-registry-checked'
            };
        }
        summary.cards++;
        if (hasDefinition) summary.dictionaryCards++; else summary.pendingDefinitions++;
        if (entity) summary.entityCandidates++;
        if (entry.lines.some(line => line.english)) summary.cardsWithTranslatedExamples++;
    }
    deck.admissionPolicy = SERIES_ADMISSION_POLICY;
    deck.dictionaryMenus = menus;
    deck.vocabularySummary = summary;
    deck.matchedCount = summary.cards;
    // Keep all recognition locations without repeating the same subtitle text
    // for every word. This also keeps the bundled preset below host file limits.
    if (deck.intake && !deck.intake.exampleLines) {
        const lines = {};
        for (const word of Object.values(deck.intake.surfaces || {})) {
            word.examples = (word.examples || []).map(example => {
                const {recordIndex, lineIndex, text, song, artist, ...location} = example;
                const line = `${recordIndex}:${lineIndex}`;
                lines[line] = {recordIndex, lineIndex, text, song, artist};
                return {...location, line};
            });
        }
        deck.intake.exampleLines = lines;
        deck.intake.exampleEncoding = 'line-refs-v1';
    }
    return deck;
}
