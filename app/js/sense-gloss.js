// Wiktionary often files several senses under one umbrella gloss — fazer has
// five "to make" senses whose real meanings ("to do; to perform", "to cook")
// sit in the sub-gloss the release calls `context`. When two or more meanings
// on a card share a translation, show a short sub-gloss as the translation
// and keep the umbrella as the context. Long or explanatory sub-glosses
// ("used in forming the perfect aspect") stay notes. Measured on Portuguese:
// 94/99 against hand judgement on the tuning sample, 44/50 on a fresh one.
//
// Display only: the original text is kept (original_translation,
// original_context) so progress keys built from it never change.

const EXPLANATION = /^(used|use|indicates?|denotes?|expresses|forms?|forming|introduces?|see|refers?|relating|pertaining|of|by|for|having|said|in|as|with|when|one who|someone|something|somebody|any|anything|that|which|person|thing|act|state)\b/i;
const ARTICLE = /^(a|an|the)\s+/i;

export function cleanSubgloss(text) {
    let value = String(text || '').replace(/\[[^\]]*\]/g, '');
    for (;;) {
        const next = value.replace(/^\s*\([^()]*\)\s*/, '');
        if (next === value) break;
        value = next;
    }
    return value.replace(/\s*\([^()]*\)\s*$/, '').replace(/^[\s;,.:]+|[\s;,.:]+$/g, '');
}

// Tags, topics and features the sense already carries ("firearms", "music",
// "colloquial", "in the plural"): a context made only of these is a label.
function senseLabels(meaning) {
    const provider = meaning?.metadata?.sense_provider_metadata || {};
    const features = (meaning?.metadata?.sense_metadata?.features || []).map(feature => feature?.value);
    const labels = new Set();
    for (const value of [...(provider.tags || []), ...(provider.topics || []), ...(provider.regions || []), ...features]) {
        const text = String(value || '').toLocaleLowerCase('en').trim();
        if (!text) continue;
        labels.add(text);
        labels.add(text.replace(/-/g, ' '));
    }
    return labels;
}

export function subglossTranslation(umbrella, context, meaning = null) {
    const sub = cleanSubgloss(context);
    if (!sub || EXPLANATION.test(sub)) return null;
    const labels = senseLabels(meaning);
    if (sub.split(/[;,]/).map(part => part.trim().toLocaleLowerCase('en')).filter(Boolean)
        .every(part => labels.has(part))) return null;
    // "to have (to be related to…)" cleans to "to have": nothing to promote,
    // and the note is the only thing telling the senses apart.
    if (sub.toLocaleLowerCase('en') === cleanSubgloss(umbrella).toLocaleLowerCase('en')) return null;
    const parts = sub.split(/[;,]/).map(part => part.trim()).filter(Boolean);
    if (!parts.length || parts.length > 4) return null;
    if (cleanSubgloss(umbrella).startsWith('to ') && !parts[0].startsWith('to ')) return null;
    for (const part of parts) {
        const core = part.replace(ARTICLE, '').replace(/^to\s+/, '');
        if (core.split(/\s+/).length > 3) return null;
    }
    return sub;
}

export function promoteSubglossTranslations(meanings) {
    if (!Array.isArray(meanings)) return meanings;
    const groups = new Map();
    for (const meaning of meanings) {
        if (meaning?.source !== 'wiktionary' || meaning.original_translation != null) continue;
        const key = String(meaning.translation || '').trim().toLocaleLowerCase('en');
        if (!key) continue;
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(meaning);
    }
    for (const group of groups.values()) {
        if (group.length < 2) continue;
        for (const meaning of group) {
            if (!meaning.context) continue;
            const promoted = subglossTranslation(meaning.translation, meaning.context, meaning);
            if (!promoted) continue;
            meaning.original_translation = meaning.translation;
            meaning.original_context = meaning.context;
            meaning.translation = promoted;
            meaning.context = cleanSubgloss(meaning.original_translation);
        }
    }
    return meanings;
}
