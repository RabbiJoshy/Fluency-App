// Subtitle and Series dialogue import for Fluency.
// Parses .srt/.vtt/text, routes through the live no-WSD engine,
// attaching dialogue lines as unassigned examples to speech vocabulary cards.

import './state.js?v=20260825ak';

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
    language = 'spanish',
    onProgress = null
} = {}) {
    if (!lines || !lines.length) {
        throw new Error('No dialogue lines to build deck from.');
    }

    if (typeof onProgress === 'function') {
        onProgress({ stage: 'intake', message: `Tokenising ${lines.length} dialogue lines…` });
    }

    const records = [{
        title: episode,
        artist,
        plainLyrics: lines.join('\n')
    }];

    const playlist = {
        id: 'la-casa-de-papel',
        name: title
    };

    if (typeof window.buildPlaylistLiveDeck !== 'function') {
        throw new Error('Live deck builder is unavailable.');
    }

    const deck = await window.buildPlaylistLiveDeck({
        playlist,
        language,
        records,
        onProgress
    });

    if (!deck || !deck.matchedCount) {
        throw new Error('None of the words in this dialogue matched the speech inventory.');
    }

    try {
        await window.savePlaylistLiveDeckToServer?.(deck);
    } catch (e) {
        console.warn('Could not save live series deck to server:', e);
    }

    return deck;
}

export async function loadCasaDePapelPreset(onProgress = null) {
    if (typeof onProgress === 'function') {
        onProgress({ stage: 'fetching', message: 'Loading La Casa de Papel dialogue…' });
    }

    let dialogueData = null;
    try {
        const resp = await fetch('data/series/casa-de-papel.json');
        if (resp.ok) {
            dialogueData = await resp.json();
        }
    } catch (e) {
        console.warn('Could not load casa-de-papel.json, using fallback lines:', e);
    }

    const lines = dialogueData?.lines && dialogueData.lines.length
        ? dialogueData.lines
        : [
            'Me llamo Tokio.',
            'Pero cuando empezó esta historia no me llamaba así.',
            'Esta era yo. Y este, el amor de mi vida.',
            'La última vez que lo vi lo dejé en un charco de sangre con los ojos abiertos.',
            'Teníamos la costumbre de no mezclar trabajo y amor.',
            'Hicimos quince atracos limpios hasta que un guardia jurado decidió hacerse el héroe.',
            'Ese hombre con gafas era el Profesor.',
            'Nos encerraríamos dentro para imprimir nuestro propio dinero.',
            'Dos mil cuatrocientos millones de euros.',
            'El plan requería cinco meses de encierro en una finca de Toledo.',
            'La regla fundamental era una: ninguna gota de sangre.',
            'No somos ladrones comunes, somos la resistencia.',
            'El dinero es solo papel pintado con un número.',
            'La verdadera riqueza es el tiempo, la libertad.',
            'Inspectora Murillo al habla, ¿con quién tengo el placer?',
            'Buenas tardes, inspectora. Puede llamarme el Profesor.'
        ];

    const deck = await buildSeriesLiveDeck({
        title: 'La Casa de Papel',
        artist: 'La Casa de Papel',
        episode: dialogueData?.episode || 'S01E01 - Efectuar lo acordado',
        lines,
        language: 'spanish',
        onProgress
    });

    return deck;
}

export function openSubtitleImport({ preselect = null, language = 'spanish' } = {}) {
    const modal = document.getElementById('subtitleImportModal');
    const status = document.getElementById('subtitleImportStatus');
    const textArea = document.getElementById('subtitleTextInput');
    const buildBtn = document.getElementById('buildSubtitleDeckBtn');

    if (status) status.textContent = '';
    if (textArea) textArea.value = '';

    if (preselect === 'la-casa-de-papel') {
        if (modal) modal.classList.remove('hidden');
        if (status) status.textContent = 'Loading La Casa de Papel dialogue…';
        if (buildBtn) buildBtn.disabled = true;

        loadCasaDePapelPreset(({ message }) => {
            if (status) status.textContent = message;
        }).then(() => {
            if (modal) modal.classList.add('hidden');
            window.activatePlaylistLiveStudy?.(language);
        }).catch(err => {
            if (status) status.textContent = err?.message || 'Failed to load La Casa de Papel.';
            if (buildBtn) buildBtn.disabled = false;
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

    closeBtn?.addEventListener('click', closeSubtitleImport);

    loadPresetBtn?.addEventListener('click', async () => {
        if (status) status.textContent = 'Building deck from La Casa de Papel dialogue…';
        loadPresetBtn.disabled = true;
        if (buildBtn) buildBtn.disabled = true;
        try {
            await loadCasaDePapelPreset(({ message }) => {
                if (status) status.textContent = message;
            });
            closeSubtitleImport();
            window.activatePlaylistLiveStudy?.('spanish');
        } catch (err) {
            if (status) status.textContent = err?.message || 'Failed to load preset.';
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
                    if (status) status.textContent = message;
                }
            });
            closeSubtitleImport();
            window.activatePlaylistLiveStudy?.(window.selectedLanguage || 'spanish');
        } catch (err) {
            if (status) status.textContent = err?.message || 'Failed to build deck.';
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
window.parseSubtitlesToLines = parseSubtitlesToLines;
