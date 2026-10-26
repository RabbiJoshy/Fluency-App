// Subtitle and Series dialogue import for Fluency.
// Parses .srt/.vtt/text, routes through the live no-WSD engine,
// attaching dialogue lines as unassigned examples to speech vocabulary cards.

import './state.js?v=496d34a9';
import { SERIES_PRESETS, validLiveDeck } from './playlist-live.js?v=496d34a9';

const SDH_REGEX = /\[[^\]]*\]|\([^\)]*\)|<[^>]*>/gu;
const TIMESTAMP_REGEX = /^\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}/;
const SEQ_NUM_REGEX = /^\d+$/;

export function cleanDialogueLine(line) {
    if (!line) return '';
    let cleaned = String(line).replace(SDH_REGEX, ' ');
    // Remove speaker prefixes like "PROFESOR:" or leading dashes
    cleaned = cleaned.replace(/^[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+:\s*/u, '');
    cleaned = cleaned.replace(/^[-–—]\s*/u, '');
    return cleaned.replace(/\s+/g, ' ').trim();
}

export function parseSubtitlesToLines(text) {
    if (!text || typeof text !== 'string') return [];
    const rawLines = text.split(/\r?\n/);
    const result = [];
    const seen = new Set();

    for (let raw of rawLines) {
        raw = raw.trim();
        if (!raw) continue;
        if (SEQ_NUM_REGEX.test(raw)) continue;
        if (TIMESTAMP_REGEX.test(raw)) continue;
        if (/^(WEBVTT|NOTE|STYLE|REGION)/i.test(raw)) continue;

        const cleaned = cleanDialogueLine(raw);
        if (!cleaned || cleaned.length < 3) continue;
        // Deduplicate consecutive or identical lines
        if (seen.has(cleaned)) continue;
        seen.add(cleaned);
        result.push(cleaned);
    }
    return result;
}

export async function buildSeriesLiveDeck({
    title = 'La Casa de Papel',
    artist = 'La Casa de Papel',
    episode = 'S01E01 - Efectuar lo acordado',
    lines = [],
    episodes = null,
    language = 'spanish',
    onProgress = null,
    sourceId = 'subtitle-upload',
    coverage = null
} = {}) {
    const normalizeLines = values => (values || []).map(value => {
        const text = typeof value === 'string' ? value.trim() : String(value?.spanish || value?.text || '').trim();
        const translation = typeof value === 'object' && value?.translation?.spanish && value?.translation?.english
            ? value.translation : null;
        return {
            text,
            exampleText: translation ? String(translation.spanish) : text,
            english: translation ? String(translation.english) : (typeof value === 'object' ? String(value?.english || '') : ''),
            translationSource: translation?.source || '',
            translationPolicy: translation?.policy || '',
            start_ms: translation?.start_ms ?? value?.start_ms ?? null,
            end_ms: translation?.end_ms ?? value?.end_ms ?? null
        };
    }).filter(line => line.text);
    const records = (Array.isArray(episodes) && episodes.length
        ? episodes : [{ episode, lines }]).map(ep => {
        const dialogueLines = normalizeLines(Array.isArray(ep.lines)
            ? ep.lines : String(ep.plainLyrics || '').split(/\r?\n/));
        return {
            title: ep.title || ep.episode || 'Episode', artist, dialogueLines,
            plainLyrics: dialogueLines.map(line => line.text).join('\n')
        };
    }).filter(record => record.dialogueLines.length);
    if (!records.length) throw new Error('No dialogue lines to build deck from.');

    const totalLines = records.reduce((sum, r) => sum + r.plainLyrics.split('\n').filter(Boolean).length, 0);
    if (typeof onProgress === 'function') {
        onProgress({ stage: 'intake', message: `Tokenising ${totalLines} dialogue lines across ${records.length} episode${records.length === 1 ? '' : 's'}…` });
    }

    const playlist = {
        id: sourceId,
        name: title
    };

    if (typeof window.buildPlaylistLiveDeck !== 'function') {
        throw new Error('Live deck builder is unavailable.');
    }

    const deck = await window.buildPlaylistLiveDeck({
        playlist,
        language,
        records,
        onProgress,
        skipWsd: true,
        includeAllForms: true
    });

    if (!deck || !deck.matchedCount) {
        throw new Error('None of the words in this dialogue matched the speech inventory.');
    }

    deck.sourceKind = 'series';
    if (coverage) deck.coverage = coverage;
    if (SERIES_PRESETS[sourceId]) deck.presetRevision = SERIES_PRESETS[sourceId].revision;
    await window.cacheLiveDeck(deck);
    saveSeriesInBackground(deck);
    return deck;
}

function saveSeriesInBackground(deck) {
    Promise.resolve().then(() => window.savePlaylistLiveDeckToServer?.(deck))
        .catch(error => console.warn('Could not save live series deck to server:', error));
}

export async function loadCasaDePapelPreset(onProgress = null) {
    return loadSeriesPreset('la-casa-de-papel', onProgress);
}

export async function loadSeriesPreset(seriesId, onProgress = null) {
    const preset = SERIES_PRESETS[seriesId];
    if (!preset) throw new Error('Unknown TV series.');
    onProgress?.({ stage: 'fetching', message: `Loading ${preset.title} dialogue sample…` });
    const appRoot = new URL('../', import.meta.url);
    try {
        const response = await fetch(new URL(`data/series/${preset.file}-deck.json?preset=${preset.revision}`, appRoot));
        const deck = response.ok ? await response.json() : null;
        if (validLiveDeck(deck) && deck.playlistId === seriesId
            && deck.language === 'spanish' && deck.presetRevision === preset.revision) {
            await window.cacheLiveDeck(deck);
            saveSeriesInBackground(deck);
            return deck;
        }
    } catch (_) {}
    try {
        const response = await fetch(new URL(`data/series/${preset.file}.json`, appRoot));
        if (!response.ok) throw new Error(`Dialogue HTTP ${response.status}`);
        const dialogue = await response.json();
        const deck = await buildSeriesLiveDeck({
            title: dialogue.title || preset.title, artist: preset.title,
            episodes: dialogue.episodes, lines: dialogue.lines,
            sourceId: seriesId, language: 'spanish', onProgress,
            coverage: dialogue.coverage
        });
        return deck;
    } catch (error) {
        await window.preparePlaylistLiveSession?.('spanish');
        const cached = window.playlistLiveDeck?.();
        if (validLiveDeck(cached) && cached.playlistId === seriesId) return cached;
        throw new Error(`Could not load the ${preset.title} sample. ${error.message}`);
    }
}

function handoffLiveStudy(language = 'spanish') {
    closeSubtitleImport();
    window.dismissMusicWorkspace?.();
    if (typeof window.activatePlaylistLiveStudy === 'function') {
        window.activatePlaylistLiveStudy(language);
    } else {
        const routeCode = language === 'spanish' ? 'es' : language;
        window.fluencyRoutes?.goToRoute?.({ kind: 'live', language: routeCode });
    }
}

export function openSubtitleImport({ preselect = null, language = 'spanish' } = {}) {
    const modal = document.getElementById('subtitleImportModal');
    const status = document.getElementById('subtitleImportStatus');
    const textArea = document.getElementById('subtitleTextInput');
    const buildBtn = document.getElementById('buildSubtitleDeckBtn');

    if (status) status.textContent = '';
    if (textArea) textArea.value = '';

    if (preselect === 'la-casa-de-papel') {
        window.showAppLoading?.('Loading La Casa de Papel', 'Building study deck from dialogue…');
        if (modal) modal.classList.remove('hidden');
        if (status) status.textContent = 'Loading La Casa de Papel dialogue…';
        if (buildBtn) buildBtn.disabled = true;

        loadCasaDePapelPreset(({ message }) => {
            window.showAppLoading?.('Loading La Casa de Papel', message);
            if (status) status.textContent = message;
        }).then(() => {
            handoffLiveStudy(language);
        }).catch(err => {
            console.error('Failed to load La Casa de Papel:', err);
            window.hideAppLoading?.();
            if (status) status.textContent = err?.message || 'Failed to load La Casa de Papel.';
            if (buildBtn) buildBtn.disabled = false;
            alert(err?.message || 'Failed to load La Casa de Papel dialogue.');
        });
        return;
    }

    if (modal) modal.classList.remove('hidden');
}

export function closeSubtitleImport() {
    const modal = document.getElementById('subtitleImportModal');
    if (modal) modal.classList.add('hidden');
}

export function initSubtitleImport() {
    const modal = document.getElementById('subtitleImportModal');
    const closeBtn = document.getElementById('closeSubtitleImportModal');
    const loadPresetBtn = document.getElementById('loadCasaDePapelPresetBtn');
    const fileInput = document.getElementById('subtitleFileInput');
    const textArea = document.getElementById('subtitleTextInput');
    const buildBtn = document.getElementById('buildSubtitleDeckBtn');
    const status = document.getElementById('subtitleImportStatus');

    closeBtn?.addEventListener('click', () => {
        closeSubtitleImport();
        if (window.musicWorkspaceStage?.() === 'subtitles') {
            window.showMusicChoices?.();
        }
    });

    loadPresetBtn?.addEventListener('click', async () => {
        loadPresetBtn.disabled = true;
        if (buildBtn) buildBtn.disabled = true;
        window.showAppLoading?.('Loading La Casa de Papel', 'Building study deck from dialogue…');
        if (status) status.textContent = 'Building deck from La Casa de Papel dialogue…';
        try {
            await loadCasaDePapelPreset(({ message }) => {
                window.showAppLoading?.('Loading La Casa de Papel', message);
                if (status) status.textContent = message;
            });
            handoffLiveStudy('spanish');
        } catch (err) {
            console.error('Failed to load preset:', err);
            window.hideAppLoading?.();
            if (status) status.textContent = err?.message || 'Failed to load preset.';
            alert(err?.message || 'Failed to load preset.');
        } finally {
            loadPresetBtn.disabled = false;
            if (buildBtn) buildBtn.disabled = false;
        }
    });

    fileInput?.addEventListener('change', event => {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = e => {
            const content = e.target?.result;
            if (typeof content === 'string' && textArea) {
                textArea.value = content;
                if (status) status.textContent = `Loaded file: ${file.name} (${Math.round(file.size / 1024)} KB). Click 'Build deck' to proceed.`;
            }
        };
        reader.readAsText(file);
    });

    buildBtn?.addEventListener('click', async () => {
        const text = textArea?.value || '';
        if (!text.trim()) {
            if (status) status.textContent = 'Please select a file or paste dialogue text.';
            return;
        }

        const lines = parseSubtitlesToLines(text);
        if (!lines.length) {
            if (status) status.textContent = 'Could not find any dialogue lines in the text.';
            return;
        }

        window.showAppLoading?.('Building deck from subtitles', `Parsed ${lines.length} lines. Matching vocabulary…`);
        if (status) status.textContent = `Parsed ${lines.length} lines. Matching vocabulary…`;
        buildBtn.disabled = true;

        try {
            await buildSeriesLiveDeck({
                title: 'Custom Subtitles',
                artist: 'Subtitles',
                episode: 'Uploaded Subtitles',
                lines,
                language: window.selectedLanguage || 'spanish',
                onProgress: ({ message }) => {
                    window.showAppLoading?.('Building deck from subtitles', message);
                    if (status) status.textContent = message;
                }
            });
            handoffLiveStudy(window.selectedLanguage || 'spanish');
        } catch (err) {
            console.error('Failed to build deck from subtitles:', err);
            window.hideAppLoading?.();
            if (status) status.textContent = err?.message || 'Failed to build deck.';
            alert(err?.message || 'Failed to build deck.');
        } finally {
            buildBtn.disabled = false;
        }
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSubtitleImport);
} else {
    initSubtitleImport();
}

window.openSubtitleImport = openSubtitleImport;
window.closeSubtitleImport = closeSubtitleImport;
window.loadCasaDePapelPreset = loadCasaDePapelPreset;
window.loadSeriesPreset = loadSeriesPreset;
window.parseSubtitlesToLines = parseSubtitlesToLines;
