// Read-only transfer of verified source meaning knowledge. No target progress is written.
import { readFastTrack, saveFastTrack } from './fast-track-preferences.js?v=7f0d8f06';
import { mergeProgressRecords } from './progress-identity.js?v=7f0d8f06';

let bundle = null;
let revision = 0;
let cacheEpoch = '';
const verdictCache = new Map();
const downloads = new Map();
const normalize = value => String(value || '').normalize('NFC').trim().toLocaleLowerCase();

async function load(langConfig) {
    bundle = null;
    revision++;
    const request = revision;
    const path = langConfig?.bridgePath;
    if (!path) { refresh(); return; }
    try {
        if (!downloads.has(path)) downloads.set(path, fetch(path, {cache: 'no-store'}).then(async response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        }).catch(error => {downloads.delete(path); throw error;}));
        const value = await downloads.get(path);
        const matchesRelease = String(langConfig.indexPath || '').includes(`/${value.built_from_release_id}/`);
        if (value.schema !== 'bridge/v1' || !matchesRelease || value.language !== langConfig.routeCode) {
            throw new Error('BRIDGE mapping does not describe this release');
        }
        if (request === revision) bundle = value;
    } catch (error) { console.warn('BRIDGE unavailable; keeping cards:', error); }
    if (request === revision) refresh();
}
function enabled() {
    const preference = readFastTrack(selectedLanguage);
    return Boolean(bundle && window.bridgeSourceLanguages().length && preference.enabled && preference.bridge);
}
function compatible(source, requirement, targetMeaning) {
    const [code, word, pivot] = requirement;
    if (Boolean(targetMeaning?.verb) !== Boolean(source.verb)) return false;
    if (targetMeaning?.verb && !(targetMeaning.formSignatures || []).some(a =>
        (source.formSignatures || []).some(b => JSON.stringify(a) === JSON.stringify(b)))) return false;
    return source.language && (bundle.sources[code]?.[word] || []).includes(source)
        && (globalThis.cognateSenseAlternatives?.(source.meanings[0].translation || source.meanings[0].meaning) || new Set()).has(pivot);
}
function sourceKnown(card) {
    if (card.progressEligible === false) return false;
    const code = card.fullId.slice(0, 2);
    const sourceRelease = bundle.source_releases[code];
    if (!sourceRelease || !String(globalThis.config?.languages?.[card.language]?.indexPath || '').includes(`/${sourceRelease}/`)) return false;
    const allRecords = window.getProgressRecordsForCard?.(card.fullId, card.targetWord, card.language) || [];
    const records = allRecords.filter(row => !row.id.includes('::split::'));
    const parent = mergeProgressRecords(records);
    const items = window.getCardKnowledgeItems?.(card) || [];
    if (!items.length) return false;
    return items.every(item => {
        const splitKey = `${normalize(item.headword).replace(/\s+/g, '_')}_${item.pos}`;
        const splitRecords = allRecords.filter(row => row.id.split('::split::')[1] === splitKey);
        const aliases = new Set(item.legacyItemIds || []);
        for (const row of [...records, ...splitRecords]) {
            for (const id of [item.itemId, ...(item.legacyItemIds || [])]) {
                const suffix = id.slice(id.indexOf('~'));
                aliases.add(row.id + suffix);
            }
        }
        const specific = window.getSpecificItemProgress?.({...item, language: card.language, legacyItemIds: [...aliases]});
        const split = mergeProgressRecords(splitRecords);
        const baseline = window.mergeKnowledgeProgress?.(parent, split);
        const state = window.getProgressState?.(window.mergeKnowledgeProgress?.(baseline, specific));
        return state?.known === true;
    });
}
function verdict(item, {useProfile = false, forceProgress = false} = {}) {
    if (!bundle || bundle.targetLanguage !== selectedLanguage) return null;
    const word = normalize(item?.word || item?.targetWord);
    const target = bundle.targets[word];
    if (!target) return null;
    // The precomputed requirements cover the exact release. Artist cards or
    // merged/loaded cards may add meanings: keep them unless all their senses
    // occur in the audited requirement set.
    const meanings = (item?.meanings || []).flatMap(m => m.pos === 'SENSE_CYCLE' && m.allSenses?.length ? m.allSenses : [m]);
    if (meanings.some(m => !target.meanings.some(t =>
        normalize(t.translation || t.meaning) === normalize(m.translation || m.meaning)
        && normalize(t.headword) === normalize(m.headword)))) return null;
    const profile = useProfile ? new Set(globalThis.activeKnownLanguages?.() || []) : new Set();
    const useProgress = forceProgress || enabled();
    if (!profile.size && !useProgress) return null;
    const preference = readFastTrack(selectedLanguage);
    const epoch = [revision, window.__progressEpoch || 0, preference.updatedAt,
        window.readLanguageProfile?.().updatedAt || 0, (window.relevantSmartSkipLanguages?.() || Object.keys(bundle.sources)).join(','), useProfile, forceProgress].join('|');
    if (cacheEpoch !== epoch) {cacheEpoch = epoch; verdictCache.clear();}
    if (verdictCache.has(word)) return verdictCache.get(word);
    const evidence = [];
    for (const [index, requirement] of target.requirements.entries()) {
        let match = null;
        for (const candidate of requirement) {
            const [code, sourceWord, pivot] = candidate;
            if (window.relevantSmartSkipLanguages && !window.relevantSmartSkipLanguages().includes(code)) continue;
            if (profile.has(code) && (!target.meanings[index]?.verb || bundle.verb_compatible?.[word]?.[code] === true)) {
                match = {code, word: sourceWord, pivot, basis: 'profile'};
                break;
            }
            const sources = bundle.sources[code]?.[sourceWord] || [];
            for (const source of sources) {
                if (!compatible(source, candidate, target.meanings[index])) continue;
                if (profile.has(code) || (useProgress && sourceKnown(source))) {
                    match = {code, word: source.targetWord, pivot, basis: profile.has(code) ? 'profile' : 'progress'};
                    break;
                }
            }
            if (match) break;
        }
        if (!match) {verdictCache.set(word, null); return null;}
        evidence.push(match);
    }
    const result = evidence.length ? {evidence, code: evidence[0].code, word: evidence[0].word, basis: evidence[0].basis} : null;
    verdictCache.set(word, result);
    return result;
}
function refresh() {
    window.forgetSmartSkipExtras?.();
    const container = document.getElementById('bridgeToggleContainer');
    if (container) container.hidden = !bundle || window.bridgeSourceLanguages().length === 0;
    const toggle = document.getElementById('bridgeToggle');
    if (toggle) toggle.setAttribute('aria-checked', String(enabled()));
    const text = document.getElementById('bridgeSourcesSummary');
    if (text) text.textContent = bundle ? `Uses your saved ${window.bridgeSourceLanguages()
        .map(code => window.knownLanguageLabel?.(code) || code.toUpperCase()).join(' and ')} progress. Only matching meanings you know are used.` : '';
    const settingsSummary = document.getElementById('settingsKnownLanguagesSummary');
    if (settingsSummary) settingsSummary.textContent = (window.readKnownLanguages?.() || [])
        .map(code => window.knownLanguageLabel?.(code) || code.toUpperCase()).join(', ') || 'None selected';
}
function init() {
    document.getElementById('bridgeToggle')?.addEventListener('click', async () => {
        const previous = readFastTrack(selectedLanguage);
        const on = !enabled();
        saveFastTrack(selectedLanguage, {bridge: on, enabled: on || previous.merge || previous.skip || previous.skipGrammar || previous.skipSlang || previous.skipEntities});
        window.applyGlobalStudyDefaults?.();
        window.invalidatePreparedSetupVocabulary?.();
        await window.updateExclusionBars?.();
        await window.updateLevelSelector?.();
        window.refreshFastMode?.();
        window.renderSkippedWords?.('cognate', {force: true});
        refresh();
    });
    document.getElementById('settingsKnownLanguagesBtn')?.addEventListener('click', () => window.openKnownLanguagesSettings?.());
    window.addEventListener('language-profile-change', () => {
        cacheEpoch = '';
        window.invalidatePreparedSetupVocabulary?.();
        window.renderKnownLanguagePicker?.();
        window.updateKnownLanguageCopy?.();
        window.updateExclusionBars?.();
        window.updateLevelSelector?.();
        refresh();
    });
    window.addEventListener('fast-track-preference-change', refresh);
    refresh();
}
window.loadBridge = load;
window.bridgeVerdict = verdict;
window.isBridgeEnabled = enabled;
window.bridgeSourceLanguages = () => {
    const codes = Object.keys(bundle?.sources || {});
    const relevant = window.relevantSmartSkipLanguages?.();
    return relevant ? codes.filter(code => relevant.includes(code)) : codes;
};
window.refreshBridge = refresh;
window.bridgeVerbCompatible = (item, code) => {
    const word = normalize(item?.word || item?.targetWord);
    const declared = bundle?.verb_compatible?.[word];
    const verb = (item?.meanings || []).some(m => ['VERB', 'AUX'].includes(String(m.pos || '').toUpperCase()));
    if (!declared && !verb) return true;
    return declared?.[code] === true;
};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
