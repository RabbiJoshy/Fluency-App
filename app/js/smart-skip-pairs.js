// Pair relevance is curated independently of mapping availability or a profile.
export function relevantSources(policy, target) {
    const key = String(target || '').split('-')[0];
    return [...new Set(policy?.targets?.[key] || [])].filter(code => code !== key);
}
export function pairChoices(policy, target, known, available) {
    const selected = new Set(known);
    const ready = new Set(available);
    return relevantSources(policy, target).filter(code => selected.has(code))
        .map(code => ({code, ready: ready.has(code)}));
}
function targetCode() {
    return globalThis.config?.languages?.[globalThis.selectedLanguage]?.routeCode || '';
}
window.relevantSmartSkipLanguages = () => relevantSources(globalThis.config?.smartSkipPairs, targetCode());
window.smartSkipLanguageChoices = (known, available) => pairChoices(globalThis.config?.smartSkipPairs, targetCode(), known, available);
