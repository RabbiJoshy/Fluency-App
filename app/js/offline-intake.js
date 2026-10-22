// Recognition only: preserve surfaces and locations; never assign a sense,
// merge a clitic, fetch a wiki page, or invent a dictionary definition.
export const OFFLINE_INTAKE_VERSION = 'recognition-v1';
const assetFiles = { es: 'turbo_assets.json', pt: 'pt_turbo_assets.json',
    fr: 'fr_turbo_assets.json', nl: 'nl_turbo_assets.json', fi: 'fi_turbo_assets.json' };
const languageCodes = { spanish: 'es', portuguese: 'pt', french: 'fr', dutch: 'nl', finnish: 'fi' };
const assetPromises = new Map();
const norm = value => String(value || '').normalize('NFC').toLowerCase().replace(/’/g, "'");

export async function loadOfflineIntakeAssets(language) {
    const code = languageCodes[language] || language;
    if (!assetFiles[code]) return null;
    if (!assetPromises.has(code)) {
        const root = new URL('../turbo/', import.meta.url);
        const pending = Promise.all([assetFiles[code], `${code}_50k_data.json`].map(async name => {
            const response = await fetch(new URL(name, root));
            if (!response.ok) throw new Error(`Offline recognition asset HTTP ${response.status}`);
            return response.json();
        })).then(([assets, extra50k]) => ({ assets, extra50k }))
            .catch(error => { assetPromises.delete(code); throw error; });
        assetPromises.set(code, pending);
    }
    return assetPromises.get(code);
}

export function recognizeOfflineRecords({ records = [], speechSurfaces = new Set(), assets = {}, extra50k = {} }) {
    const words = new Map(), entities = new Map();
    const dictionary = assets.dictionary || {}, ranks = extra50k.ranks || {}, lemmas = extra50k.lemmas || {};
    const entityStarts = new Map();
    for (const [alias, entity] of Object.entries(assets.curatedEntities || {})) {
        const parts = norm(alias).split(/\s+/);
        const choices = entityStarts.get(parts[0]) || [];
        choices.push({ parts, entity });
        entityStarts.set(parts[0], choices);
    }
    for (const choices of entityStarts.values()) choices.sort((a, b) => b.parts.length - a.parts.length);
    let tokenCount = 0;
    records.forEach((record, recordIndex) => {
        if (!record || ['miss', 'instrumental', 'error'].includes(record.status)) return;
        const lines = Array.isArray(record.dialogueLines) ? record.dialogueLines
            : String(record.plainLyrics || record.syncedLyrics || '').split(/\r?\n/).map(text => ({ text }));
        lines.forEach((line, lineIndex) => {
            const text = String(line.text || line.spanish || '');
            // Match the shared live tokenizer while preserving character offsets.
            const tokens = [...text.matchAll(/[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*/gu)]
                .map(match => ({ surface: match[0], key: norm(match[0]), start: match.index, end: match.index + match[0].length }));
            tokenCount += tokens.length;
            for (let i = 0; i < tokens.length; i++) {
                const token = tokens[i], key = token.key;
                let word = words.get(key);
                if (!word) {
                    const lemmaHint = Object.hasOwn(lemmas, key) && typeof lemmas[key] === 'string' ? lemmas[key] : null;
                    const frequencyRank = Object.hasOwn(ranks, key) && Number.isFinite(ranks[key]) && ranks[key] > 0 ? ranks[key] : null;
                    word = { surface: key, count: 0, inStudyInventory: speechSurfaces.has(key),
                        inDictionary: Object.hasOwn(dictionary, key), frequencyRank,
                        lemmaHint, lemmaInDictionary: Boolean(lemmaHint && Object.hasOwn(dictionary, lemmaHint)),
                        unassigned: true, examples: [] };
                    words.set(key, word);
                }
                word.count++;
                const location = { recordIndex, lineIndex, start: token.start, end: token.end,
                    surface: token.surface, text, song: record.title || record.episode || '', artist: record.artist || '' };
                if (word.examples.length < 3) word.examples.push(location);
                for (const { parts, entity } of entityStarts.get(key) || []) {
                    if (!parts.every((part, offset) => tokens[i + offset]?.key === part
                        && (!offset || /^\s+$/.test(text.slice(tokens[i + offset - 1].end, tokens[i + offset].start))))) continue;
                    const title = entity.canonicalTitle || parts.join(' ');
                    const candidate = entities.get(title) || { ...entity, canonicalTitle: title, count: 0,
                        assignment: 'candidate', examples: [] };
                    candidate.count++;
                    if (candidate.examples.length < 3) candidate.examples.push({ ...location,
                        end: tokens[i + parts.length - 1].end,
                        surface: text.slice(token.start, tokens[i + parts.length - 1].end) });
                    entities.set(title, candidate);
                    break;
                }
            }
        });
    });
    const surfaces = Object.fromEntries(words);
    return { version: OFFLINE_INTAKE_VERSION, mode: 'no-wsd', grouping: 'original-surface',
        entityCoverage: 'curated-registry-only',
        summary: { tokenCount, distinctSurfaces: words.size,
            studySurfaces: [...words.values()].filter(w => w.inStudyInventory).length,
            frequencyRecognized: [...words.values()].filter(w => w.frequencyRank).length,
            additionalFrequencySurfaces: [...words.values()].filter(w => w.frequencyRank && !w.inStudyInventory).length,
            unrecognizedSurfaces: [...words.values()].filter(w => !w.frequencyRank && !w.inDictionary && !w.lemmaInDictionary && !w.inStudyInventory).length,
            lemmaCandidates: [...words.values()].filter(w => w.lemmaInDictionary).length,
            entityCandidates: entities.size },
        surfaces, entityCandidates: [...entities.values()] };
}

export async function enrichOfflineDeck(deck, records, speechSurfaces = new Set(Object.keys(deck.surfaces || {}))) {
    if (deck.intake?.version === OFFLINE_INTAKE_VERSION) return deck;
    const loaded = await loadOfflineIntakeAssets(deck.language);
    if (loaded) deck.intake = recognizeOfflineRecords({ records, speechSurfaces, ...loaded });
    return deck;
}
