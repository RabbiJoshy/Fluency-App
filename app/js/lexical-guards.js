// Shared word/entity identity guards. Recognition is not sense assignment.
const normalizedName = value => String(value || '').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, ' ').trim();

export function entityTitleMatchesQuery(query, title) {
    // A disambiguating suffix is fine; an expanded phrase is another entity.
    // Berlín -> Berlín (personaje) is possible; Berlín -> Muro de Berlín isn't.
    const bareTitle = String(title || '').replace(/\s*\([^)]*\)\s*$/, '');
    const name = normalizedName(query);
    return Boolean(name && name === normalizedName(bareTitle));
}

export function standaloneWordMeanings(word, meanings = [], language = 'es') {
    // The release attached the phrase "muro de Berlín" to the word berlín.
    // Keep a neutral proper-name gloss; do not infer city vs character alias.
    const isSpanish = ['es', 'spanish'].includes(language);
    if (isSpanish && normalizedName(word) === 'berlin'
        && meanings.some(m => normalizedName(m.headword || m.metadata?.multiword_expression) === 'muro de berlin'
            || normalizedName(m.translation) === 'berlin wall')) {
        return [{pos:'PROPN', translation:'Berlin', context:'proper name',
            headword:word, frequency:'1', unassigned:true, assignment_method:'unassigned',
            source:'lexical-correction', source_reference:'standalone-name:berlin-v1'}];
    }
    return meanings;
}

export function guardStandaloneDictionary(dictionary = {}, language = 'es') {
    const guarded = { ...dictionary };
    for (const [word, entry] of Object.entries(dictionary)) {
        const meanings = standaloneWordMeanings(word, entry.meanings || [], language);
        if (meanings === entry.meanings) continue;
        if (!meanings.length) continue;
        guarded[word] = { ...entry, meanings, top_translation:meanings[0].translation,
            top_pos:meanings[0].pos, polysemous:meanings.length > 1, meaning_count:meanings.length };
    }
    return guarded;
}
