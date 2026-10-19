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
        onProgress,
        skipWsd: true
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

    // Fast path: load pre-solved series deck immediately
    const appRoot = new URL('../', import.meta.url);
    const resolvedDeckUrl = new URL('data/series/casa-de-papel-deck.json', appRoot).href;
    const resolvedDialogueUrl = new URL('data/series/casa-de-papel.json', appRoot).href;

    const deckPaths = [
        resolvedDeckUrl,
        'data/series/casa-de-papel-deck.json',
        './data/series/casa-de-papel-deck.json',
        'app/data/series/casa-de-papel-deck.json'
    ];
    for (const p of deckPaths) {
        try {
            const resp = await fetch(p);
            if (resp.ok) {
                const deck = await resp.json();
                if (deck?.matchedCount) {
                    if (typeof window.cacheLiveDeck === 'function') {
                        await window.cacheLiveDeck(deck);
                    }
                    try {
                        await window.savePlaylistLiveDeckToServer?.(deck);
                    } catch (_) {}
                    return deck;
                }
            }
        } catch (_) {}
    }

    let dialogueData = null;
    const paths = [
        resolvedDialogueUrl,
        'data/series/casa-de-papel.json',
        './data/series/casa-de-papel.json',
        'app/data/series/casa-de-papel.json'
    ];
    for (const p of paths) {
        try {
            const resp = await fetch(p);
            if (resp.ok) {
                dialogueData = await resp.json();
                break;
            }
        } catch (_) {}
    }

    const lines = dialogueData?.lines && dialogueData.lines.length
        ? dialogueData.lines
        : [
            "Me llamo Tokio.",
            "Pero cuando empezó esta historia no me llamaba así.",
            "Esta era yo. Y este, el amor de mi vida.",
            "La última vez que lo vi lo dejé en un charco de sangre con los ojos abiertos.",
            "Teníamos la costumbre de no mezclar trabajo y amor.",
            "Hicimos quince atracos limpios hasta que un guardia jurado decidió hacerse el héroe.",
            "Un disparo en el cuello de mi novio y todo se fue a la mierda.",
            "Así que pasé de ser ladrona a ser asesina.",
            "Y desde entonces he estado huyendo.",
            "Dicen que el amor te hace ver el mundo de color de rosa.",
            "Pero cuando estás sola y acorralada, el mundo es negro.",
            "Mi madre vivía en un barrio humilde a las afueras de Madrid.",
            "Iba a verla por su cumpleaños, sabiendo que la policía estaría vigilando la casa.",
            "Era un suicidio, pero necesitaba despedirme.",
            "En ese momento apareció un coche rojo.",
            "Un hombre con gafas se bajó y me dijo: Disculpe, ¿tiene un minuto?",
            "Ese hombre era el Profesor.",
            "No tenía antecedentes, ni ficha policial, ni multas de tráfico.",
            "Era un fantasma.",
            "Me dijo que sabía que la policía me estaba esperando en casa de mi madre.",
            "Y me hizo una propuesta: un atraco histórico.",
            "No un banco, ni una joyería, ni un furgón blindado.",
            "La Fábrica Nacional de Moneda y Timbre.",
            "Nos encerraríamos dentro durante días para imprimir nuestro propio dinero.",
            "Dos mil cuatrocientos millones de euros.",
            "El plan requería cinco meses de encierro en una finca de Toledo.",
            "Cinco meses estudiando cada paso, cada detalle, cada posible error.",
            "Éramos ocho personas, elegidas meticulosamente.",
            "Ninguno tenía nada que perder.",
            "Para proteger nuestras identidades, el Profesor nos prohibió usar nombres reales.",
            "Nada de preguntas personales, nada de relaciones.",
            "Elegimos nombres de ciudades.",
            "Berlín, el jefe al mando dentro de la fábrica, narcisista y calculador.",
            "Moscú, el veterano minero capaz de abrir cualquier cerradura.",
            "Denver, su hijo, impulsivo y con un corazón enorme.",
            "Río, el joven genio de la informática y los sistemas de seguridad.",
            "Nairobi, una optimista nata encargada del control de calidad.",
            "Helsinki y Oslo, la fuerza bruta, dos soldados que no hacían preguntas.",
            "Y yo, Tokio.",
            "La regla fundamental era una: ninguna gota de sangre.",
            "Si hay una sola víctima, la opinión pública se pondrá en nuestra contra.",
            "No somos ladrones comunes, somos la resistencia.",
            "El día del golpe llegó en un camión con bobinas de papel de seguridad.",
            "Entramos armados hasta los dientes, vestidos con monos rojos y caretas de Dalí.",
            "En cuestión de minutos tomamos el edificio y sesenta y siete rehenes.",
            "Entre ellos estaba la hija del embajador británico, Alison Parker.",
            "Nuestro cordero de Pascua.",
            "La policía rodeó el edificio de inmediato.",
            "La inspectora Raquel Murillo tomó el mando del operativo.",
            "Pero el Profesor ya había previsto cada uno de sus movimientos en una partida de ajedrez perfecta.",
            "El juego acababa de comenzar.",
            "A ver, señores, mucha atención a lo que voy a decir.",
            "No vamos a robar el dinero de nadie.",
            "Porque vamos a fabricar nuestro propio dinero.",
            "¿Cómo lo veis?",
            "Para la gente seremos unos héroes.",
            "Eso es fundamental: tenemos que tener a la opinión pública de nuestra parte.",
            "No quiero ni una sola gota de sangre derramada.",
            "¿Ha quedado claro?",
            "El día que haya una sola baja, dejamos de ser la resistencia y nos convertimos en monstruos.",
            "Aquí no hay amigos, no hay familia, no hay relaciones sentimentales.",
            "Quiero que os olvidéis de vuestras vidas anteriores.",
            "A partir de ahora sois Berlín, Moscú, Denver, Río, Nairobi, Helsinki, Oslo y Tokio.",
            "¿Por qué Tokio?",
            "Porque me gusta el nombre y porque suena rápido.",
            "Pues a mí me gusta Río, me parece fresco.",
            "A ti lo que te gusta es hablar demasiado, chaval.",
            "El dinero es solo papel pintado con un número.",
            "La verdadera riqueza es el tiempo, la libertad.",
            "Cuando salgamos de aquí con ese dinero seremos libres para siempre.",
            "Pero para eso hay que aguantar once días dentro.",
            "Once días encerrados mientras las máquinas de imprimir no paran de funcionar.",
            "Las rotativas van a trabajar día y noche sin descanso.",
            "Cada hora que pasa imprimimos ocho millones de euros.",
            "Tenemos comida, agua, medicamentos y armamento suficiente.",
            "Los rehenes son nuestra muralla defensiva.",
            "Hay que tratarlos bien, que coman lo mismo que nosotros.",
            "Les pondremos los mismos monos rojos y las mismas caretas.",
            "Así la policía no sabrá quién es rehén y quién es atracador si deciden asaltar.",
            "Es una obra de arte, un poema visual.",
            "Tranquilos todos, nadie se va a hacer daño si hacéis exactamente lo que os digamos.",
            "Colaboren y todo saldrá bien.",
            "Entregad todos los teléfonos móviles en esta bolsa ahora mismo.",
            "No intentéis ser valientes, el heroísmo en estos casos suele acabar mal.",
            "Si alguien intenta escapar o esconder un teléfono, las consecuencias serán desagradables.",
            "Inspectora Murillo al habla, ¿con quién tengo el placer?",
            "Buenas tardes, inspectora. Puede llamarme el Profesor.",
            "¿Qué es lo que quiere exactamente, Profesor?",
            "Quiero tiempo, inspectora. Solo tiempo.",
            "Sabe perfectamente que no van a poder salir de ese edificio con rehenes.",
            "No subestime nuestra paciencia, ni la suya.",
            "Le propongo mantener una línea abierta de comunicación directa.",
            "Cada decisión que tome tendrá un impacto inmediato en la vida de esas personas.",
            "Usted es una mujer inteligente y sabe que podemos llegar a un entendimiento.",
            "No voy a negociar con terroristas.",
            "Nosotros no somos terroristas, inspectora. Somos ladrones.",
            "Y de los buenos, créame.",
            "La negociación será larga, tensa y fascinante.",
            "Espero que esté lista para una partida larga."
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
window.parseSubtitlesToLines = parseSubtitlesToLines;
