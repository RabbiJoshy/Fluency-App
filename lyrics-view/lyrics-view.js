import { preferredAi } from '../js/ai-preference.js?v=8d2b084a';
import { linePlaybackTarget, restartLyricLine, songHasPlayback, songTrackId } from './line-playback.js?v=8d2b084a';
import { playbackPositionMs, activeLineIndex, lineProgress, tokenFills, timingMatches, adjacentLineStart, repeatEndMs } from './line-follow.js?v=8d2b084a';
import { TurboEngine } from '../turbo/turbo-engine.js?v=8d2b084a';

let currentLanguage = 'es';

// Common Spanish & Portuguese ad-libs, interjections, and exclamations
const SPANISH_INTERJECTIONS = new Set([
  'brr', 'wuh', 'ey', 'eh', 'ay', 'oh', 'ah', 'ja', 'jaja', 'yah', 'uh',
  'shh', 'prr', 'rra', 'amén', 'dale', 'oye', 'mera', 'woh', 'uah', 'pla',
  'pew', 'okey', 'bye', 'epa', 'uf', 'chao', 'hola', 'adiós', 'puñeta',
  'carajo', 'dios', 'mami'
]);

const PORTUGUESE_INTERJECTIONS = new Set([
  'opa', 'olha', 'ué', 'eita', 'nossa', 'oxe', 'valeu', 'falou', 'ai', 'ah',
  'oh', 'eh', 'né', 'oba', 'uau', 'vixi', 'xi', 'ô', 'hein', 'aff', 'hum',
  'psiu', 'tomara', 'amém', 'olá', 'tchau', 'beleza', 'cara', 'massa'
]);

const FRENCH_INTERJECTIONS = new Set([
  'ouais', 'bah', 'hein', 'hop', 'bof', 'ah', 'oh', 'eh', 'ouh', 'zou', 'chut', 'zut', 'youpi', 'hélas', 'voilà'
]);

const DUTCH_INTERJECTIONS = new Set([
  'hè', 'nou', 'hoor', 'joh', 'tja', 'zeg', 'ach', 'toch', 'poeh', 'oef', 'tsjonge', 'goh', 'hallo', 'doei'
]);

const FINNISH_INTERJECTIONS = new Set([
  'noh', 'hei', 'oho', 'joo', 'no', 'voi', 'huh', 'ai', 'aha', 'vau', 'kappas', 'apua', 'huraa'
]);

const INTERJECTIONS_SET = new Set([
  ...SPANISH_INTERJECTIONS,
  ...PORTUGUESE_INTERJECTIONS,
  ...FRENCH_INTERJECTIONS,
  ...DUTCH_INTERJECTIONS,
  ...FINNISH_INTERJECTIONS
]);

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeRegExp(str) {
  if (!str) return '';
  return String(str).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Formats an elided word displaying the elided letter(s) in brackets in blue, e.g.:
 * sabemo' -> sabemo<span class="elision-bracket">(</span><span class="elision-letter">s</span><span class="elision-bracket">)</span>
 * 'tás -> <span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>tás
 * estudia'o -> estudia<span class="elision-bracket">(</span><span class="elision-letter">d</span><span class="elision-bracket">)</span>o
 */
function formatElisionToken(raw, fullWord) {
  if (!raw) return '';
  if (!fullWord) return escapeHtml(raw);

  const normRaw = raw.replace(/[’]/g, "'");
  // Separate leading and trailing punctuation (excluding apostrophes which belong to the word)
  const match = normRaw.match(/^([¿¡\"(]*)(.*?)([\"?!.,:;)]*)$/);
  if (!match) return escapeHtml(raw);
  const lead = match[1];
  const core = match[2];
  const trail = match[3];
  if (!core) return escapeHtml(raw);

  const cleanFull = fullWord.trim().toLowerCase();
  const cleanCore = core.toLowerCase();

  if (cleanCore === cleanFull) {
    return escapeHtml(raw);
  }

  // Irregular / common fixed contractions (Spanish & Portuguese)
  if (cleanCore === "pa'") return `${escapeHtml(lead)}pa<span class="elision-bracket">(</span><span class="elision-letter">ra</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "to'") return `${escapeHtml(lead)}to<span class="elision-bracket">(</span><span class="elision-letter">do</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "na'") return `${escapeHtml(lead)}na<span class="elision-bracket">(</span><span class="elision-letter">da</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "e'") return `${escapeHtml(lead)}e<span class="elision-bracket">(</span><span class="elision-letter">s</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "'e") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "toa'" || cleanCore === "toa") return `${escapeHtml(lead)}to<span class="elision-bracket">(</span><span class="elision-letter">d</span><span class="elision-bracket">)</span>a${escapeHtml(trail)}`;
  if (cleanCore === "'tamo" || cleanCore === "tamo") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>tamo<span class="elision-bracket">(</span><span class="elision-letter">s</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "'tamos" || cleanCore === "tamos") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>tamos${escapeHtml(trail)}`;
  if (cleanCore === "'toy" || cleanCore === "toy") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>toy${escapeHtml(trail)}`;
  if (cleanCore === "'tá" || cleanCore === "ta'" || cleanCore === "ta") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>tá${escapeHtml(trail)}`;
  if (cleanCore === "'tás" || cleanCore === "tas'" || cleanCore === "tas") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>tás${escapeHtml(trail)}`;
  if (cleanCore === "'tan" || cleanCore === "tan'") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>tán${escapeHtml(trail)}`;
  if (cleanCore === "'taba" || cleanCore === "taba") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>taba${escapeHtml(trail)}`;

  // Portuguese contractions
  if (cleanCore === "pra") return `${escapeHtml(lead)}p<span class="elision-bracket">(</span><span class="elision-letter">a</span><span class="elision-bracket">)</span>ra${escapeHtml(trail)}`;
  if (cleanCore === "pras") return `${escapeHtml(lead)}p<span class="elision-bracket">(</span><span class="elision-letter">a</span><span class="elision-bracket">)</span>ra<span class="elision-bracket">(</span><span class="elision-letter"> as</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "pro") return `${escapeHtml(lead)}p<span class="elision-bracket">(</span><span class="elision-letter">a</span><span class="elision-bracket">)</span>r<span class="elision-bracket">(</span><span class="elision-letter">a </span><span class="elision-bracket">)</span>o${escapeHtml(trail)}`;
  if (cleanCore === "pros") return `${escapeHtml(lead)}p<span class="elision-bracket">(</span><span class="elision-letter">a</span><span class="elision-bracket">)</span>r<span class="elision-bracket">(</span><span class="elision-letter">a </span><span class="elision-bracket">)</span>os${escapeHtml(trail)}`;
  if (cleanCore === "tô" || cleanCore === "'tô") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>tou${escapeHtml(trail)}`;
  if (cleanCore === "tava" || cleanCore === "'tava") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">es</span><span class="elision-bracket">)</span>tava${escapeHtml(trail)}`;
  if (cleanCore === "né") return `${escapeHtml(lead)}n<span class="elision-bracket">(</span><span class="elision-letter">ão </span><span class="elision-bracket">)</span>é${escapeHtml(trail)}`;
  if (cleanCore === "cê" || cleanCore === "'cê") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">vo</span><span class="elision-bracket">)</span>cê${escapeHtml(trail)}`;
  if (cleanCore === "cês" || cleanCore === "'cês") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">vo</span><span class="elision-bracket">)</span>cês${escapeHtml(trail)}`;
  if (cleanCore === "dum") return `${escapeHtml(lead)}d<span class="elision-bracket">(</span><span class="elision-letter">e </span><span class="elision-bracket">)</span>um${escapeHtml(trail)}`;
  if (cleanCore === "duma") return `${escapeHtml(lead)}d<span class="elision-bracket">(</span><span class="elision-letter">e </span><span class="elision-bracket">)</span>uma${escapeHtml(trail)}`;
  if (cleanCore === "num") return `${escapeHtml(lead)}n<span class="elision-bracket">(</span><span class="elision-letter">em </span><span class="elision-bracket">)</span>um${escapeHtml(trail)}`;
  if (cleanCore === "numa") return `${escapeHtml(lead)}n<span class="elision-bracket">(</span><span class="elision-letter">em </span><span class="elision-bracket">)</span>uma${escapeHtml(trail)}`;

  // French clitics & contractions
  if (cleanCore === "c'") return `${escapeHtml(lead)}c<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "j'") return `${escapeHtml(lead)}j<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "d'") return `${escapeHtml(lead)}d<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "l'") return `${escapeHtml(lead)}l<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "qu'") return `${escapeHtml(lead)}qu<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "m'") return `${escapeHtml(lead)}m<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "t'") return `${escapeHtml(lead)}t<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "s'") return `${escapeHtml(lead)}s<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "n'") return `${escapeHtml(lead)}n<span class="elision-bracket">(</span><span class="elision-letter">e</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "t'as") return `${escapeHtml(lead)}t<span class="elision-bracket">(</span><span class="elision-letter">u </span><span class="elision-bracket">)</span>as${escapeHtml(trail)}`;
  if (cleanCore === "t'es") return `${escapeHtml(lead)}t<span class="elision-bracket">(</span><span class="elision-letter">u </span><span class="elision-bracket">)</span>es${escapeHtml(trail)}`;

  // Dutch clitics & contractions
  if (cleanCore === "'t") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">he</span><span class="elision-bracket">)</span>t${escapeHtml(trail)}`;
  if (cleanCore === "'k") return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">i</span><span class="elision-bracket">)</span>k${escapeHtml(trail)}`;
  if (cleanCore === "m'n") return `${escapeHtml(lead)}m<span class="elision-bracket">(</span><span class="elision-letter">ij</span><span class="elision-bracket">)</span>n${escapeHtml(trail)}`;
  if (cleanCore === "z'n") return `${escapeHtml(lead)}z<span class="elision-bracket">(</span><span class="elision-letter">ij</span><span class="elision-bracket">)</span>n${escapeHtml(trail)}`;
  if (cleanCore === "zo'n") return `${escapeHtml(lead)}zo<span class="elision-bracket">(</span><span class="elision-letter"> een</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;

  // Finnish spoken contractions
  if (cleanCore === "mä") return `${escapeHtml(lead)}m<span class="elision-bracket">(</span><span class="elision-letter">inä</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "sä") return `${escapeHtml(lead)}s<span class="elision-bracket">(</span><span class="elision-letter">inä</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
  if (cleanCore === "oot") return `${escapeHtml(lead)}o<span class="elision-bracket">(</span><span class="elision-letter">le</span><span class="elision-bracket">)</span>t${escapeHtml(trail)}`;
  if (cleanCore === "oon") return `${escapeHtml(lead)}o<span class="elision-bracket">(</span><span class="elision-letter">le</span><span class="elision-bracket">)</span>n${escapeHtml(trail)}`;

  // Case 1: Trailing apostrophe (sabemo' -> sabemos, ere' -> eres, ojo' -> ojos)
  if (cleanCore.endsWith("'")) {
    const stem = core.slice(0, -1);
    if (cleanFull.startsWith(stem.toLowerCase())) {
      const elided = fullWord.slice(stem.length);
      if (elided.length > 0) {
        return `${escapeHtml(lead)}${escapeHtml(stem)}<span class="elision-bracket">(</span><span class="elision-letter">${escapeHtml(elided)}</span><span class="elision-bracket">)</span>${escapeHtml(trail)}`;
      }
    }
    // Stray apostrophe or no extra letters (e.g. quitaba'): tint the apostrophe blue without empty brackets
    return `${escapeHtml(lead)}${escapeHtml(stem)}<span class="apostrophe-tint">'</span>${escapeHtml(trail)}`;
  }

  // Case 2: Leading apostrophe ('tás -> estás, 'toy -> estoy)
  if (cleanCore.startsWith("'")) {
    const stem = core.slice(1);
    if (cleanFull.endsWith(stem.toLowerCase())) {
      const elided = fullWord.slice(0, fullWord.length - stem.length);
      if (elided.length > 0) {
        return `${escapeHtml(lead)}<span class="elision-bracket">(</span><span class="elision-letter">${escapeHtml(elided)}</span><span class="elision-bracket">)</span>${escapeHtml(stem)}${escapeHtml(trail)}`;
      }
    }
    return `${escapeHtml(lead)}<span class="apostrophe-tint">'</span>${escapeHtml(stem)}${escapeHtml(trail)}`;
  }

  // Case 3: Medial apostrophe (estudia'o -> estudiado, cansa'o -> cansado)
  if (core.includes("'")) {
    const parts = core.split("'");
    if (parts.length === 2) {
      const p1 = parts[0];
      const p2 = parts[1];
      if (cleanFull.startsWith(p1.toLowerCase()) && cleanFull.endsWith(p2.toLowerCase())) {
        const elided = fullWord.slice(p1.length, fullWord.length - p2.length);
        if (elided.length > 0) {
          return `${escapeHtml(lead)}${escapeHtml(p1)}<span class="elision-bracket">(</span><span class="elision-letter">${escapeHtml(elided)}</span><span class="elision-bracket">)</span>${escapeHtml(p2)}${escapeHtml(trail)}`;
        }
      }
      return `${escapeHtml(lead)}${escapeHtml(p1)}<span class="apostrophe-tint">'</span>${escapeHtml(p2)}${escapeHtml(trail)}`;
    }
  }

  return escapeHtml(raw);
}

let engine = null;
let probeSongs = [];       // the curated 30, full text in one file
let extraSongs = [];       // the rest of the catalogue: index only, lyrics fetched when opened
let catalogueSongs = [];   // curated first, then the rest by artist
let customSongs = [];
let allSongs = [];
let annotatedCache = new Map(); // songCacheKey -> annotatedSong
let currentSongIndex = 0;
let currentAnnotatedSong = null;
let showEnglishUnderneath = (() => {
  try { return localStorage.getItem('fluency_lyrics_show_english') !== '0'; } catch (_) { return true; }
})();

// Flat list of all tokens in current song for modal next/previous stepping
let songTokensFlatList = [];
let currentModalTokenIndex = -1;

// DOM Elements
const backToLibraryBtn = document.getElementById('backToLibraryBtn');
const topbarSongTitle = document.getElementById('topbarSongTitle');
const topbarSongArtist = document.getElementById('topbarSongArtist');
const toggleEnglishBtn = document.getElementById('toggleEnglishBtn');

const loadingBox = document.getElementById('loadingBox');
const lyricsFlow = document.getElementById('lyricsFlow');

// Modals & Picker Elements
const songPickerModal = document.getElementById('songPickerModal');
const closeSongPickerBtn = document.getElementById('closeSongPickerBtn');
const songPickerList = document.getElementById('songPickerList');
const songSearchInput = document.getElementById('songSearchInput');
const songSearchClearBtn = document.getElementById('songSearchClearBtn');
const catalogEmptyGuidance = document.getElementById('catalogEmptyGuidance');
const openManualPasteBtn = document.getElementById('openManualPasteBtn');
const goWithoutLyricsBtn = document.getElementById('goWithoutLyricsBtn');
const openSpotifyInputBtn = document.getElementById('openSpotifyInputBtn');
const spotifyInputTray = document.getElementById('spotifyInputTray');
const recentSongShelf = document.getElementById('recentSongShelf');
const recentSongCard = document.getElementById('recentSongCard');

// Track Intake Elements
const turboTrackInput = document.getElementById('turboTrackInput');
const turboClearInputBtn = document.getElementById('turboClearInputBtn');
const turboManualDetails = document.getElementById('turboManualDetails');
const turboManualTitle = document.getElementById('turboManualTitle');
const turboManualArtist = document.getElementById('turboManualArtist');
const turboManualLyrics = document.getElementById('turboManualLyrics');
const turboAlertBox = document.getElementById('turboAlertBox');
const turboAlertText = document.getElementById('turboAlertText');
const turboStatusCard = document.getElementById('turboStatusCard');
const turboStatusTitle = document.getElementById('turboStatusTitle');
const turboStatusSub = document.getElementById('turboStatusSub');
const runTurboBtn = document.getElementById('runTurboBtn');

const tokenQuickViewModal = document.getElementById('tokenQuickViewModal');
const closeTokenModalBtn = document.getElementById('closeTokenModalBtn');
const tokenModalWord = document.getElementById('tokenModalWord');
const tokenModalElisionHint = document.getElementById('tokenModalElisionHint');
const tokenModalBadges = document.getElementById('tokenModalBadges');
const modalMeaningCallout = document.getElementById('modalMeaningCallout');
const modalMeaningLabel = document.getElementById('modalMeaningLabel');
const modalMeaningPrimary = document.getElementById('modalMeaningPrimary');
const modalMeaningContext = document.getElementById('modalMeaningContext');
const modalEntityBox = document.getElementById('modalEntityBox');
const modalEntityTitle = document.getElementById('modalEntityTitle');
const modalEntityDesc = document.getElementById('modalEntityDesc');
const modalPolySensesBox = document.getElementById('modalPolySensesBox');
const modalPolySensesList = document.getElementById('modalPolySensesList');
const modalSongOccurrencesBox = document.getElementById('modalSongOccurrencesBox');
const modalSongOccurrencesList = document.getElementById('modalSongOccurrencesList');
const modalContextQuoteText = document.getElementById('modalContextQuoteText');
const modalContextQuoteMeta = document.getElementById('modalContextQuoteMeta');
const tokenPrevBtn = document.getElementById('tokenPrevBtn');
const tokenNextBtn = document.getElementById('tokenNextBtn');



// ───────────────────────────────────────────────
// Helpers & Tab Switching
// ───────────────────────────────────────────────
function lineTextKey(text) {
  return String(text || '').toLowerCase().normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
}

// A human translation for a line, by its text: the same line, or a near-copy
// differing in an ad-lib or a punctuation mark ("debo" / "debo, oye"). Short
// lines match only exactly, so "no sé" never borrows another line's meaning.
function englishForLine(pairs, text) {
  const key = lineTextKey(text);
  const exact = pairs.find(p => p.key === key);
  if (exact) return exact.english;
  const words = new Set(key.split(' '));
  if (words.size < 4) return null;
  let best = null;
  let bestScore = 0;
  let runnerUp = 0;
  for (const p of pairs) {
    let shared = 0;
    words.forEach(w => { if (p.words.has(w)) shared++; });
    const score = shared / (words.size + p.words.size - shared);
    if (score > bestScore) { runnerUp = bestScore; bestScore = score; best = p; }
    else if (score > runnerUp) runnerUp = score;
  }
  return best && bestScore >= 0.75 && bestScore > runnerUp ? best.english : null;
}

function songCacheKey(song) {
  if (!song) return '';
  if (song.id) return song.id;
  return `${song.title || ''}:::${song.artist || ''}`;
}

function loadSavedCustomSongs() {
  try {
    const key = `fluency_turbo_custom_songs_${currentLanguage}`;
    const raw = sessionStorage.getItem(key) || sessionStorage.getItem('fluency_turbo_custom_songs');
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (_) {}
  return [];
}



// ───────────────────────────────────────────────
// Initialisation
// ───────────────────────────────────────────────
async function init() {
  try {
    // Use the same Spotify account, player, and callback as vocabulary mode.
    try {
      const response = await fetch(new URL('../config/config.json', import.meta.url));
      if (!response.ok) throw new Error('Spotify configuration unavailable');
      const config = await response.json();
      window._spotifyClientId = config.publicServices?.spotifyClientId || '';
      window._spotifyRedirectUris = { ...config.publicServices?.spotifyRedirectUris };
      // The fallback must resolve from the app root, not this nested mode.
      window._spotifyRedirectUris[window.location.origin] ||= new URL('../callback.html', import.meta.url).href;
    } catch (error) {
      console.warn('Could not initialize Spotify configuration:', error);
    }
    await import('../js/spotify.js?v=8d2b084a');

    const urlParams = new URLSearchParams(window.location.search);
    const paramSong = urlParams.get('song');
    const paramLang = (urlParams.get('lang') || urlParams.get('language') || '').toLowerCase();
    const langMap = {
      'pt': 'pt', 'portuguese': 'pt',
      'fr': 'fr', 'french': 'fr',
      'nl': 'nl', 'dutch': 'nl',
      'fi': 'fi', 'finnish': 'fi',
      'es': 'es', 'spanish': 'es'
    };
    currentLanguage = langMap[paramLang] || 'es';

    document.documentElement.lang = currentLanguage;
    const isEs = currentLanguage === 'es';

    // Update back links to retain language in Fluency hash
    const backToStudyLink = document.getElementById('backToStudy');
    if (backToStudyLink && !isEs) {
      backToStudyLink.href = `../#${currentLanguage}`;
    }
    const topbarBackLink = document.querySelector('.topbar a.header-icon');
    if (topbarBackLink && !isEs) {
      topbarBackLink.href = `../#${currentLanguage}`;
    }

    const assetsFile = isEs ? 'turbo_assets.json' : `${currentLanguage}_turbo_assets.json`;
    const extra50kFile = isEs ? 'es_50k_data.json' : `${currentLanguage}_50k_data.json`;
    const songsFile = isEs ? 'probe_songs.json' : `${currentLanguage}_probe_songs.json`;

    // Robust asset paths relative to this module
    const assetsUrl = new URL(`../turbo/${assetsFile}?v=20261015all`, import.meta.url).href;
    const extra50kUrl = new URL(`../turbo/${extra50kFile}?v=20261015all`, import.meta.url).href;
    const songsUrl = new URL(`../turbo/${songsFile}?v=20261015all`, import.meta.url).href;

    // Load assets (read-only)
    engine = await TurboEngine.create(assetsUrl, extra50kUrl);

    // Load offline songs (read-only)
    const songsResp = await fetch(songsUrl);
    if (!songsResp.ok) throw new Error(`HTTP ${songsResp.status} loading offline songs`);
    probeSongs = await songsResp.json();
    probeSongs.forEach((s, idx) => {
      // The Spotify track is the song's identity in links; the position is not.
      s.id = s.spotifyId || `offline_${idx}`;
      s.isOffline = true;
    });

    if (isEs) {
      // The wider catalogue: an index of title, artist and track. A song's
      // timed lyrics are fetched when it is opened.
      try {
        const indexResp = await fetch(new URL('../turbo/catalogue/index.json?v=20261009M', import.meta.url));
        if (indexResp.ok) {
          extraSongs = (await indexResp.json()).map(entry => ({
            ...entry, spotifyId: entry.id, isCatalogue: true, needsDetail: true
          }));
        }
      } catch (_) { /* the curated 30 still work */ }
    }
    catalogueSongs = [...probeSongs, ...extraSongs];

    if (isEs) {
      // Human English translations for curated songs, matched to their timed
      // lines by text (the timed lines are LRCLIB's, not the translator's).
      try {
        const trResp = await fetch(new URL('../turbo/probe_translations.json?v=20261009M', import.meta.url));
        if (trResp.ok) {
          const { songs = {} } = await trResp.json();
          probeSongs.forEach(song => {
            const entry = songs[song.spotifyId];
            if (!entry) return;
            song.englishByText = entry.lines.map(l => ({
              key: lineTextKey(l.text), words: new Set(lineTextKey(l.text).split(' ')), english: l.english
            }));
            song.translationSource = entry.source;
          });
        }
      } catch (_) {}
    }

    // Load session-generated songs
    customSongs = loadSavedCustomSongs();
    allSongs = [...customSongs, ...catalogueSongs];

    renderSongPickerItems(allSongs);

    // If a specific song was requested in URL query, load it; otherwise open the library modal
    if (paramSong) {
      // A song's id first; then the old numeric links (a position in the
      // curated list); then a title or artist fragment.
      const byId = allSongs.findIndex(s => s.id === paramSong);
      const legacy = /^\d+$/.test(paramSong) ? probeSongs[parseInt(paramSong, 10)] : null;
      if (byId >= 0) {
        currentSongIndex = byId;
        await selectSong(currentSongIndex);
      } else if (legacy) {
        currentSongIndex = allSongs.indexOf(legacy);
        await selectSong(currentSongIndex);
      } else {
        const foundIdx = allSongs.findIndex(s =>
          (s.title || '').toLowerCase().includes(paramSong.toLowerCase()) ||
          (s.artist || '').toLowerCase().includes(paramSong.toLowerCase())
        );
        if (foundIdx >= 0) {
          currentSongIndex = foundIdx;
          await selectSong(currentSongIndex);
        } else if (paramSong.includes('spotify') || /^[A-Za-z0-9]{22}$/.test(paramSong)) {
          await handleRunTurbo({ input: paramSong });
        } else {
          await selectSong(0);
        }
      }
    } else {
      // Default initial view: Open the Song Library menu so user can choose a track
      await selectSong(0, false); // select song 0 in background without forcing URL param
      openSongPicker();
    }
  } catch (err) {
    console.error('Failed to init Lyrics View:', err);
    if (loadingBox) {
      loadingBox.innerHTML = `
        <p style="color: #ff5252; font-weight: 600;">Failed to load lyrics: ${err.message}</p>
        <p style="font-size: 13px; margin-top: 8px;">Ensure files exist under app/turbo/.</p>
      `;
    }
  }
}

// ───────────────────────────────────────────────
// Song Processing & Selection
// ───────────────────────────────────────────────
async function selectSong(index, syncUrl = true) {
  if (index < 0 || index >= allSongs.length) return;
  currentSongIndex = index;

  const song = allSongs[index];
  if (topbarSongTitle) topbarSongTitle.textContent = song.title || '';
  if (topbarSongArtist) {
    topbarSongArtist.textContent = (song.artist || '') + (song.isOnline ? ' · Online' : '');
  }


  // Sync URL query without reloading (if requested)
  if (syncUrl) {
    try {
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.set('song', song.id || index);
      window.history.replaceState({}, '', newUrl.toString());
    } catch (_) {}
  }

  if (lyricsFlow) lyricsFlow.style.display = 'none';
  if (loadingBox) {
    loadingBox.style.display = 'block';
    loadingBox.querySelector('p').textContent = 'Loading lyrics…';
  }

  if (song.needsDetail) {
    try {
      const detailResp = await fetch(new URL(`../turbo/catalogue/songs/${song.id}.json?v=20261009M`, import.meta.url));
      if (!detailResp.ok) throw new Error(`HTTP ${detailResp.status}`);
      Object.assign(song, await detailResp.json(), { needsDetail: false });
    } catch (error) {
      console.warn('Could not load song lyrics:', error);
      if (loadingBox) loadingBox.querySelector('p').textContent = 'Could not load this song. Check your connection and try again.';
      return;
    }
  }

  const cacheKey = songCacheKey(song);
  let annotatedSong = annotatedCache.get(cacheKey);
  if (!annotatedSong) {
    // If song has known English translation lines attached, pass them through
    const result = await engine.processPlaylist([song]);
    annotatedSong = result.annotatedSongs?.[0];
    if (annotatedSong) {
      if (song.englishLines && Array.isArray(song.englishLines)) {
        annotatedSong.lines.forEach((l, idx) => {
          if (idx < song.englishLines.length && !l.english) {
            l.english = song.englishLines[idx];
          }
        });
      }
      if (song.englishByText) {
        annotatedSong.lines.forEach(l => {
          if (!l.english) l.english = englishForLine(song.englishByText, l.text);
        });
      }
      postProcessAnnotatedSong(annotatedSong);
      annotatedCache.set(cacheKey, annotatedSong);
    }
  }

  if (loadingBox) loadingBox.style.display = 'none';
  if (lyricsFlow) lyricsFlow.style.display = 'flex';

  if (annotatedSong) {
    currentAnnotatedSong = annotatedSong;
    renderLyrics(annotatedSong);
  }
}

/**
 * Enhances token classification:
 * - Detects interjections / ad-libs
 * - Classifies elisions
 */
function postProcessAnnotatedSong(song) {
  for (const line of song.lines) {
    for (const token of line.tokens) {
      const lowerRaw = token.raw.toLowerCase().replace(/^[¿¡"'(]+|[.,;:!?"')]+$/g, '');
      const lowerNorm = (token.word || '').toLowerCase();

      const isPosIntj = token.pos === 'INTJ' || token.pos === 'interjection';
      const hasIntjMeaning = token.card?.meanings && token.card.meanings.some(m => m.pos === 'INTJ' || m.pos === 'interjection');
      const isAdLibPhrase = (token.translation || '').toLowerCase().includes('ad-lib') || (token.translation || '').toLowerCase().includes('interjection');
      const isInAdlibSet = INTERJECTIONS_SET.has(lowerRaw) || INTERJECTIONS_SET.has(lowerNorm);

      if (token.type !== 'entity' && token.type !== 'mwe') {
        if (isPosIntj || hasIntjMeaning || isAdLibPhrase || isInAdlibSet) {
          token.type = 'interjection';
          if (!token.translation || token.translation === 'out of 10k supply / noise' || token.translation === 'Uncatalogued lyric') {
            token.translation = 'ad-lib / vocal exclamation';
          }
        } else if (token.type === 'unmatched' && engine && typeof engine.resolveWordInfo === 'function') {
          // Rescue tokens that exist in the engine 50k ranks or dictionary
          const resolved = engine.resolveWordInfo(lowerNorm || lowerRaw);
          if (resolved) {
            token.type = 'word';
            token.word = resolved.word;
            token.rank = resolved.rank;
            token.speechRank = resolved.speechRank;
            if (resolved.dictEntry) {
              token.translation = resolved.translation;
              token.pos = resolved.pos;
              token.card = { ...resolved.dictEntry, word: resolved.word, translation: resolved.translation };
            } else if (resolved.rank) {
              const langLabel = LANG_NAME_LABELS[currentLanguage] || 'Spanish';
              token.translation = `Top ${Math.ceil(resolved.rank / 1000) * 1000} ${langLabel} word`;
            }
          }
        }
      }
    }
  }
}

const LANG_NAME_LABELS = {
  pt: 'Portuguese',
  fr: 'French',
  nl: 'Dutch',
  fi: 'Finnish',
  es: 'Spanish'
};

// Official brand SVGs
const CLAUDE_SVG = `<svg class="ai-icon" viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><title>Claude</title><path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>`;

const CHATGPT_SVG = `<svg class="ai-icon" viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><title>ChatGPT</title><path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1683a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4947zm-9.66-4.1354a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1402-1.6564zm-1.6704-9.3364a4.4755 4.4755 0 0 1 2.3418-1.9729v5.6725a.7901.7901 0 0 0 .388.6813l5.8428 3.3685-2.02 1.1683a.071.071 0 0 1-.071 0l-4.8303-2.7913a4.4944 4.4944 0 0 1-1.6513-6.1264zM16.598 12.012l-5.8428-3.3685 2.02-1.1683a.071.071 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1 1.6513 6.1264 4.4755 4.4755 0 0 1-2.3418 1.9729v-5.6725a.7901.7901 0 0 0-.388-.6813zm4.6568-1.6366l-.142-.0852-4.783-2.7582a.7712.7712 0 0 0-.7806 0l-5.8428 3.3685v-2.3324a.0804.0804 0 0 1 .0332-.0615L14.26 4.0498a4.4992 4.4992 0 0 1 6.1402 1.6564 4.4708 4.4708 0 0 1 .5346 3.0137zm-9.518-2.6186a.7948.7948 0 0 0-.3927.6813v6.7369l-2.02-1.1683a.071.071 0 0 1-.038-.052V9.0498a4.504 4.504 0 0 1 4.4945-4.4947 4.4755 4.4755 0 0 1 2.8764 1.0408l-.1419.0804zm-1.2588 5.795l2.7677-1.5979 2.7677 1.5979v3.1957l-2.7677 1.5979-2.7677-1.5979z"/></svg>`;

const OUTBOUND_ARROW_SVG = `<svg class="lyric-ai-leave-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`;

function buildAiPromptText(lineText, songTitle, songArtist) {
  const cleanLine = (lineText || '').trim();
  const artistInfo = songArtist ? ` by ${songArtist}` : '';
  const trackInfo = songTitle ? ` from the song "${songTitle}"${artistInfo}` : (artistInfo ? ` by ${songArtist}` : '');
  const langLabel = LANG_NAME_LABELS[currentLanguage] || 'Spanish';
  return `Please translate this ${langLabel} lyric line into English, break down any slang, idioms, or cultural nuances, and tell me anything essential one needs to know about the artist or context behind it:\n\n"${cleanLine}"${trackInfo ? ` (${trackInfo})` : ''}`;
}

async function copyPromptToClipboard(promptText) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(promptText);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = promptText;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
  } catch (err) {
    console.warn('Clipboard write failed:', err);
  }
}

function disarmAllAiChips(exceptChip = null) {
  document.querySelectorAll('.lyric-ai-sheet-chip.is-armed-outbound').forEach(chip => {
    if (chip === exceptChip) return;
    chip.classList.remove('is-armed-outbound');
    const pill = chip.querySelector('.lyric-ai-leave-pill');
    if (pill) pill.hidden = true;
  });
}

function closeAllAiSheets(exceptWrap = null) {
  document.querySelectorAll('.lyric-ai-wrap').forEach(wrap => {
    if (wrap === exceptWrap) return;
    wrap.classList.remove('is-open');
    const sheet = wrap.querySelector('.lyric-ai-sheet');
    if (sheet) sheet.hidden = true;
  });
  disarmAllAiChips();
}

/**
 * Handles tap on Claude / ChatGPT chip in the pull-up sheet.
 * Tap 1: Copies prompt to clipboard and arms outbound leave warning pill.
 * Tap 2: Executes outbound navigation directly to the AI app.
 */
async function armLyricAiLink(event, platform, lineText, songTitle, songArtist, chipEl) {
  event.stopPropagation();
  const promptText = buildAiPromptText(lineText, songTitle, songArtist);
  const encodedPrompt = encodeURIComponent(promptText);
  const targetUrl = platform === 'claude'
    ? `https://claude.ai/new?q=${encodedPrompt}`
    : `https://chatgpt.com/?q=${encodedPrompt}`;

  const leavePill = chipEl.querySelector('.lyric-ai-leave-pill');
  if (!leavePill) return;

  const isArmed = chipEl.classList.contains('is-armed-outbound');

  if (isArmed) {
    // Second tap: Leave the app immediately
    window.open(targetUrl, '_blank', 'noopener,noreferrer');
    disarmAllAiChips();
    closeAllAiSheets();
    return;
  }

  // First tap: Disarm other chips, copy prompt, arm this chip
  disarmAllAiChips(chipEl);
  await copyPromptToClipboard(promptText);

  chipEl.classList.add('is-armed-outbound');
  leavePill.hidden = false;
  showAiToast(`Prompt copied! Tap again to open ${platform === 'claude' ? 'Claude' : 'ChatGPT'}`);
}

function toggleLyricAiSheet(event, wrapEl) {
  event.stopPropagation();
  const sheet = wrapEl.querySelector('.lyric-ai-sheet');
  if (!sheet) return;

  const isHidden = sheet.hidden;
  closeAllAiSheets(isHidden ? wrapEl : null);

  sheet.hidden = !isHidden;
  wrapEl.classList.toggle('is-open', isHidden);
}

let aiToastTimeout = null;
function showAiToast(message) {
  let toast = document.getElementById('aiPromptToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'aiPromptToast';
    toast.className = 'ai-prompt-toast';
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.classList.add('visible');

  if (aiToastTimeout) clearTimeout(aiToastTimeout);
  aiToastTimeout = setTimeout(() => {
    toast.classList.remove('visible');
  }, 2400);
}

/**
 * Generates a clean, natural English gloss line for a lyric row.
 * Prefers human English translation attached to the line; otherwise
 * synthesizes a readable gloss from token translations.
 */
function buildLineEnglishGloss(line) {
  if (!line) return '';
  if (line.english && typeof line.english === 'string' && line.english.trim()) {
    return line.english.trim();
  }
  if (!line.tokens || !Array.isArray(line.tokens)) return '';

  const parts = [];
  for (const t of line.tokens) {
    if (t.type === 'unmatched') {
      parts.push(t.raw);
      continue;
    }
    if (t.type === 'entity') {
      parts.push(t.word || t.raw);
      continue;
    }
    let tr = t.translation || t.word || '';
    if (t.type === 'mwe') {
      tr = tr.split(';')[0].split(',')[0].trim();
      tr = tr.replace(/^Used for explanations:\s*/i, '');
      parts.push(tr);
      continue;
    }
    // Clean dictionary clutter
    tr = tr.replace(/\(inflection of[^)]*\)/gi, '').trim();
    tr = tr.replace(/\([^)]*\)/g, '').trim();
    if (tr.includes(';')) tr = tr.split(';')[0].trim();
    if (tr.includes(',')) tr = tr.split(',')[0].trim();
    // Drop leading infinitive "to " unless it's a stand-alone dictionary cue
    tr = tr.replace(/^to\s+/i, '').trim();
    if (tr) parts.push(tr);
  }

  let text = parts.join(' ').trim();
  if (text.length > 0) {
    text = text.charAt(0).toUpperCase() + text.slice(1);
  }
  return text;
}

// ───────────────────────────────────────────────
// Render Spotify-Style Lyrics View
// ───────────────────────────────────────────────
function renderLyrics(song) {
  lyricsFlow.innerHTML = '';
  songTokensFlatList = [];

  const hasAnyEnglish = song.lines.some(l => l.english && typeof l.english === 'string' && l.english.trim());
  if (toggleEnglishBtn) {
    toggleEnglishBtn.style.display = hasAnyEnglish ? 'flex' : 'none';
    toggleEnglishBtn.setAttribute('aria-pressed', String(showEnglishUnderneath));
  }

  const sourceSong = allSongs[currentSongIndex];
  const playbackStatus = document.getElementById('linePlaybackStatus');
  // No track or no timed line: no buttons and no banner. There is nothing to fix.
  const hasPlayback = songHasPlayback(sourceSong, song.lines);
  const unavailable = hasPlayback
    ? song.lines.map(line => linePlaybackTarget(sourceSong, line)).find(target => !target.available)
    : null;
  playbackStatus.textContent = unavailable ? unavailable.reason : '';
  playbackStatus.hidden = !unavailable;
  resetFollow();
  if (playBar) {
    playBar.hidden = !hasPlayback;
    document.body.classList.toggle('has-play-bar', hasPlayback);
    syncPlayBar();
  }

  song.lines.forEach((line, lineIdx) => {
    const lineItem = document.createElement('div');
    lineItem.className = 'lyric-line-item';
    lineItem.dataset.lineIndex = lineIdx;

    const englishGloss = buildLineEnglishGloss(line);
    const hasLineTranslation = Boolean(englishGloss);

    // Spotify replaces the time label; timing stays in the playback request.
    const gutter = document.createElement('div');
    gutter.className = 'lyric-line-gutter';
    const target = linePlaybackTarget(sourceSong, line);
    const listenButton = document.createElement('button');
    listenButton.hidden = !hasPlayback;
    listenButton.type = 'button';
    listenButton.className = 'lyric-listen-btn';
    listenButton.disabled = !target.available;
    listenButton.title = target.available ? 'Play from this line on Spotify' : target.reason;
    listenButton.setAttribute('aria-label', target.available
      ? `Play from line ${lineIdx + 1} on Spotify: ${line.text}`
      : `Line ${lineIdx + 1} playback unavailable. ${target.reason}`);
    listenButton.innerHTML = `<svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" aria-hidden="true"><path d="M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24Zm5.5 17.3a.75.75 0 0 1-1.03.25c-2.82-1.72-6.37-2.11-10.55-1.16a.75.75 0 1 1-.33-1.46c4.57-1.04 8.5-.59 11.66 1.34.35.22.46.68.25 1.03Zm1.47-3.27a.94.94 0 0 1-1.29.3c-3.23-1.99-8.16-2.57-11.98-1.41a.94.94 0 1 1-.54-1.8c4.36-1.32 9.8-.67 13.5 1.62.45.27.59.85.31 1.29Zm.13-3.41C15.23 8.32 8.85 8.11 5.16 9.23a1.13 1.13 0 0 1-.65-2.16c4.23-1.28 11.28-1.03 15.74 1.62a1.13 1.13 0 0 1-1.15 1.93Z"/></svg>`;
    const playLine = async () => {
      if (listenButton.disabled) return;
      listenButton.disabled = true;
      followPausedUntil = 0; // playing a line brings the view back to it
      if (repeatMode) setRepeatLine(lineIdx);
      listenButton.setAttribute('aria-busy', 'true');
      listenButton.classList.add('is-loading');
      playbackStatus.hidden = false;
      playbackStatus.textContent = 'Connecting to Spotify…';
      try {
        const started = await restartLyricLine(target, window.spotifyPlayTrack);
        if (listenButton.isConnected) {
          playbackStatus.textContent = started ? '' : 'Playback did not start. Connect Spotify Premium and try again.';
          playbackStatus.hidden = Boolean(started);
        }
      } catch (error) {
        if (listenButton.isConnected) playbackStatus.textContent = 'Could not start Spotify. Please try again.';
        console.warn('Line playback failed:', error);
      } finally {
        listenButton.disabled = false;
        listenButton.removeAttribute('aria-busy');
        listenButton.classList.remove('is-loading');
      }
    };
    listenButton.addEventListener('click', event => { event.stopPropagation(); playLine(); });
    // The whole line plays too; its words (word card), the gutter and a text
    // selection keep their own meaning.
    if (hasPlayback && target.available) {
      lineItem.classList.add('is-playable');
      lineItem.addEventListener('click', event => {
        if (event.target.closest('.lyric-token, .lyric-line-gutter, button, a')) return;
        if (String(window.getSelection?.() || '').length) return;
        playLine();
      });
    }
    gutter.appendChild(listenButton);

    // AI Look up Action: Single circular "AI" button
    // Pressing it pulls up Claude & ChatGPT icons in a sheet directly above it (exact flashcard lookup pattern).
    // Tapping an icon arms it ("Visit Claude ↗"), and tapping again leaves the app.
    const aiWrap = document.createElement('div');
    aiWrap.className = 'lyric-ai-wrap';

    const aiCircleBtn = document.createElement('button');
    aiCircleBtn.type = 'button';
    aiCircleBtn.className = 'lyric-ai-circle-btn';
    aiCircleBtn.title = 'Look up with AI';
    aiCircleBtn.setAttribute('aria-label', 'Look up with AI');
    const provider = preferredAi();
    aiCircleBtn.innerHTML = provider === 'claude' ? CLAUDE_SVG : CHATGPT_SVG;
    aiCircleBtn.title = `Explain with ${provider === 'claude' ? 'Claude' : 'ChatGPT'}`;
    aiCircleBtn.setAttribute('aria-label', aiCircleBtn.title);
    aiCircleBtn.addEventListener('click', (e) => {
      toggleLyricAiSheet(e, aiWrap);
    });

    // Sheet holding the two circular brand icons
    const aiSheet = document.createElement('div');
    aiSheet.className = 'lyric-ai-sheet';
    aiSheet.hidden = true;

    // Claude Chip
    const claudeChip = document.createElement('span');
    claudeChip.className = 'lyric-ai-sheet-chip is-claude';
    claudeChip.role = 'button';
    claudeChip.tabIndex = 0;
    claudeChip.title = 'Claude';
    claudeChip.setAttribute('aria-label', 'Look up with Claude');
    claudeChip.innerHTML = `
      ${CLAUDE_SVG}
      <span class="lyric-ai-leave-pill" hidden aria-label="Visit Claude">
        <span>Visit Claude</span>
        ${OUTBOUND_ARROW_SVG}
      </span>
    `;
    claudeChip.addEventListener('click', (e) => {
      armLyricAiLink(e, 'claude', line.text, song.title, song.artist, claudeChip);
    });
    claudeChip.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        armLyricAiLink(e, 'claude', line.text, song.title, song.artist, claudeChip);
      }
    });

    // ChatGPT Chip
    const gptChip = document.createElement('span');
    gptChip.className = 'lyric-ai-sheet-chip is-chatgpt';
    gptChip.role = 'button';
    gptChip.tabIndex = 0;
    gptChip.title = 'ChatGPT';
    gptChip.setAttribute('aria-label', 'Look up with ChatGPT');
    gptChip.innerHTML = `
      ${CHATGPT_SVG}
      <span class="lyric-ai-leave-pill" hidden aria-label="Visit ChatGPT">
        <span>Visit ChatGPT</span>
        ${OUTBOUND_ARROW_SVG}
      </span>
    `;
    gptChip.addEventListener('click', (e) => {
      armLyricAiLink(e, 'chatgpt', line.text, song.title, song.artist, gptChip);
    });
    gptChip.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        armLyricAiLink(e, 'chatgpt', line.text, song.title, song.artist, gptChip);
      }
    });

    aiSheet.appendChild(provider === 'claude' ? claudeChip : gptChip);
    aiSheet.appendChild(provider === 'claude' ? gptChip : claudeChip);

    aiWrap.appendChild(aiCircleBtn);
    aiWrap.appendChild(aiSheet);

    gutter.appendChild(aiWrap);
    lineItem.appendChild(gutter);

    // 2. Main Body Column (Target Spanish + English underneath perfectly aligned)
    const lineBody = document.createElement('div');
    lineBody.className = 'lyric-line-body';

    // Target Spanish Line (Large, bold)
    const targetLine = document.createElement('div');
    targetLine.className = 'lyric-line-target';
    const tokenEls = [];
    followLines.push({ item: lineItem, tokenEls });

    // Auto entities / idioms / ad-libs found in this line
    const lineAutoBadges = [];

    line.tokens.forEach(token => {
      const flatIndex = songTokensFlatList.length;
      token.flatIndex = flatIndex;
      token.lineText = line.text;
      token.lineIndex = lineIdx;
      token.songTitle = song.title;
      token.songArtist = song.artist;
      songTokensFlatList.push(token);

      const span = document.createElement('span');
      span.className = 'lyric-token';
      span.dataset.flatIndex = flatIndex;
      span.dataset.type = token.type;

      if (token.type === 'entity') {
        span.classList.add('token-entity');
        span.title = `Entity: ${token.word} (${token.translation || 'Cultural referent'})`;
        span.dataset.fillText = token.raw;
        span.innerHTML = `<span class="entity-wiktionary-icon" aria-hidden="true" title="Wiktionary / Cultural Entity">W</span>${escapeHtml(token.raw)}`;
      } else if (token.type === 'mwe') {
        span.classList.add('token-mwe');
        span.title = `Idiom: ${token.word} (${token.translation || 'Idiom'})`;
        span.textContent = token.raw;
      } else if (token.type === 'interjection') {
        span.classList.add('token-interjection');
        span.title = `Ad-lib: ${token.translation || token.raw}`;
        span.textContent = token.raw;
      } else {
        span.classList.add('token-word');
        if (token.isElision) {
          span.classList.add('token-elision');
          span.title = `Elision: ${token.raw} → ${token.word}`;
          span.innerHTML = formatElisionToken(token.raw, token.word);
        } else {
          span.title = `${token.word}: ${token.translation || 'Word'}`;
          span.textContent = token.raw;
        }
      }

      span.addEventListener('click', (e) => {
        e.stopPropagation();
        openTokenModal(token);
      });

      targetLine.appendChild(span);
      tokenEls.push(span);
    });

    lineBody.appendChild(targetLine);

    // English Line Underneath (Only if genuine hand-translated line exists)
    if (englishGloss) {
      const englishLine = document.createElement('div');
      englishLine.className = `lyric-line-english${showEnglishUnderneath ? '' : ' is-hidden'}`;

      const textSpan = document.createElement('span');
      textSpan.textContent = englishGloss;
      englishLine.appendChild(textSpan);

      lineBody.appendChild(englishLine);
    }

    lineItem.appendChild(lineBody);

    lyricsFlow.appendChild(lineItem);
  });
  // A song already playing when this view opens starts following at once.
  if (hasPlayback) startFollow();
}

// ───────────────────────────────────────────────
// Follow playback (karaoke fill)
// ───────────────────────────────────────────────
// Lines are timed by LRCLIB; word timing is estimated from each word's share
// of its line. Classes only: .is-active / .is-past on lines, .is-sung on words.
let followLines = [];          // [{ item, tokenEls }] for the rendered song
let followState = null;        // last 'fluency:spotify-state' detail
let followRaf = 0;
let followActive = -1;
let followSung = 0;
let followPausedUntil = 0;     // the reader scrolled; leave the view alone until then
const FOLLOW_SCROLL_PAUSE_MS = 4000;
let repeatMode = false;        // loop one line
let repeatLineIndex = -1;      // which; -1 until a line is playing or tapped
let repeatSeekAt = 0;

const playBar = document.getElementById('playBar');
const playBarToggle = document.getElementById('playBarToggle');
const playBarPrev = document.getElementById('playBarPrev');
const playBarNext = document.getElementById('playBarNext');
const playBarRepeat = document.getElementById('playBarRepeat');

function openTrackId() { return songTrackId(allSongs[currentSongIndex]); }

// Spotify is on this song, so a seek or pause acts on it rather than starting it.
function trackIsLoaded() {
  const trackId = openTrackId();
  return Boolean(trackId && followState && (followState.trackId === trackId || followState.linkedFromId === trackId));
}

function syncPlayBar() {
  if (!playBar) return;
  const playing = trackIsLoaded() && !followState.paused;
  playBar.classList.toggle('is-playing', playing);
  if (playBarToggle) {
    const label = playing ? 'Pause' : (trackIsLoaded() ? 'Resume' : 'Play from the start');
    playBarToggle.setAttribute('aria-label', label);
    playBarToggle.title = label;
  }
}

function setRepeatLine(index) {
  repeatLineIndex = index;
  followLines.forEach(({ item }, i) => item.classList.toggle('is-looping', repeatMode && i === index));
}

async function seekTo(positionMs) {
  followPausedUntil = 0;
  let ok = false;
  if (trackIsLoaded() && window.spotifyTransport) ok = await window.spotifyTransport.seek(positionMs);
  if (ok) {
    // The player will confirm in a moment; do not let the clock run on past it.
    followState = { ...followState, positionMs, at: performance.now() };
    startFollow();
    return true;
  }
  const trackId = openTrackId();
  if (!trackId || !window.spotifyPlayTrack) return false;
  return restartLyricLine({ available: true, trackId, positionMs }, window.spotifyPlayTrack);
}

async function togglePlayBar() {
  const trackId = openTrackId();
  if (!trackId) return;
  if (trackIsLoaded() && window.spotifyTransport && await window.spotifyTransport.toggle()) return;
  // Nothing of this song is playing: start it from the top.
  if (window.spotifyPlayTrack) await restartLyricLine({ available: true, trackId, positionMs: 0 }, window.spotifyPlayTrack);
}

function stepLine(direction) {
  const song = currentAnnotatedSong;
  if (!song) return;
  const position = trackIsLoaded() ? playbackPositionMs(followState, performance.now()) : -1;
  const target = adjacentLineStart(song.lines, position, direction);
  if (target === null) return;
  const index = song.lines.findIndex(l => l.isSynced && l.timestamp_ms === target);
  if (repeatMode && index >= 0) setRepeatLine(index);
  seekTo(target);
}

if (playBar) {
  playBarToggle.addEventListener('click', togglePlayBar);
  playBarPrev.addEventListener('click', () => stepLine(-1));
  playBarNext.addEventListener('click', () => stepLine(1));
  playBarRepeat.addEventListener('click', () => {
    repeatMode = !repeatMode;
    playBarRepeat.setAttribute('aria-pressed', String(repeatMode));
    playBar.classList.toggle('is-repeating', repeatMode);
    // Loop the line being sung; with nothing playing, the next line played.
    setRepeatLine(repeatMode ? followActive : -1);
  });
}

function resetFollow() {
  if (followRaf) cancelAnimationFrame(followRaf);
  followRaf = 0;
  followLines = [];
  followActive = -1;
  followSung = 0;
  repeatLineIndex = -1;
  window.fluencySpotifyFollow = true; // lets spotify.js poll Connect playback for us
}

function clearFollowClasses() {
  followLines.forEach(({ item, tokenEls }) => {
    item.classList.remove('is-active', 'is-past');
    tokenEls.forEach(el => el.classList.remove('is-sung'));
  });
  followActive = -1;
  followSung = 0;
}

function startFollow() {
  if (!followRaf && followLines.length) followRaf = requestAnimationFrame(followTick);
}

function followNote(text) {
  const status = document.getElementById('linePlaybackStatus');
  if (!status) return;
  status.textContent = text;
  status.hidden = !text;
}

function followTick() {
  followRaf = 0;
  const song = currentAnnotatedSong;
  const source = allSongs[currentSongIndex];
  const state = followState;
  const trackId = songTrackId(source);
  if (!song || !state || !trackId || (state.trackId !== trackId && state.linkedFromId !== trackId)) {
    clearFollowClasses();
    return;
  }
  if (timingMatches(source.lrclibDurationMs, state.durationMs) === false) {
    clearFollowClasses();
    followNote('Spotify is playing a different cut of this song, so the highlight is off.');
    return;
  }

  const position = playbackPositionMs(state, performance.now());
  const index = activeLineIndex(song.lines, position);
  syncPlayBar();
  if (repeatMode && !state.paused) {
    if (repeatLineIndex < 0 && index >= 0) setRepeatLine(index);
    const loopLine = song.lines[repeatLineIndex];
    const loopEnd = repeatEndMs(loopLine);
    if (loopEnd !== null && position >= loopEnd && performance.now() - repeatSeekAt > 800) {
      repeatSeekAt = performance.now();
      seekTo(loopLine.timestamp_ms);
    }
  }
  if (index !== followActive) {
    followLines.forEach(({ item, tokenEls }, i) => {
      item.classList.toggle('is-active', i === index);
      item.classList.toggle('is-past', index >= 0 && i < index);
      if (i !== index) tokenEls.forEach(el => el.classList.remove('is-sung'));
    });
    followActive = index;
    followSung = 0;
    if (index >= 0 && performance.now() >= followPausedUntil) {
      const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
      followLines[index].item.scrollIntoView({ block: 'center', behavior: reduce ? 'auto' : 'smooth' });
    }
  }
  if (index >= 0) {
    const { tokenEls } = followLines[index];
    const fills = tokenFills(tokenEls.map(el => el.dataset.fillText ?? el.textContent), lineProgress(song.lines[index], position));
    const sung = fills.filter(f => f > 0).length;
    if (sung !== followSung) {
      tokenEls.forEach((el, i) => el.classList.toggle('is-sung', i < sung));
      followSung = sung;
    }
  }
  if (!state.paused) followRaf = requestAnimationFrame(followTick);
}

window.addEventListener('fluency:spotify-state', event => {
  followState = event.detail;
  syncPlayBar();
  startFollow();
});

// A reader who scrolls is reading, not following; give the view back after a pause.
['wheel', 'touchmove', 'keydown', 'pointerdown'].forEach(type => {
  window.addEventListener(type, () => {
    followPausedUntil = performance.now() + FOLLOW_SCROLL_PAUSE_MS;
  }, { passive: true });
});

// ───────────────────────────────────────────────
// Quick-View Token Modal
// ───────────────────────────────────────────────
function openTokenModal(token) {
  if (!token) return;
  currentModalTokenIndex = token.flatIndex;

  // Title & Elision
  if (tokenModalWord) tokenModalWord.textContent = token.raw;
  if (tokenModalElisionHint) {
    if (token.isElision && token.word && token.word !== token.raw.toLowerCase()) {
      tokenModalElisionHint.textContent = `Contraction of: ${token.word}`;
      tokenModalElisionHint.style.display = 'inline-block';
    } else {
      tokenModalElisionHint.style.display = 'none';
    }
  }

  // Disambiguate context meaning for polysemous words using engine's unified WSD logic
  const cardMeanings = token.card?.meanings || [];
  let chosenMeaning = cardMeanings[0] || null;
  let chosenIdx = 0;

  if (cardMeanings.length > 1 && engine && typeof engine.disambiguateWord === 'function') {
    const dictEntry = (token.word && engine.dictionary?.[token.word.toLowerCase()]) || token.card;
    if (dictEntry) {
      chosenIdx = engine.disambiguateWord(token.word || token.raw, dictEntry, token.lineText || '');
      if (cardMeanings[chosenIdx]) {
        chosenMeaning = cardMeanings[chosenIdx];
      }
    }
  }

  // Badges
  if (tokenModalBadges) {
    tokenModalBadges.innerHTML = '';
    const typeBadge = document.createElement('span');
    typeBadge.className = 'token-type-pill';

    if (token.type === 'entity') {
      typeBadge.classList.add('pill-entity-style');
      const entType = token.card?.entity?.entityType || 'Cultural Entity';
      typeBadge.textContent = entType;
    } else if (token.type === 'mwe') {
      typeBadge.classList.add('pill-mwe-style');
      typeBadge.textContent = 'Idiom';
    } else if (token.type === 'interjection') {
      typeBadge.classList.add('pill-intj-style');
      typeBadge.textContent = 'Ad-lib / Interjection';
    } else {
      typeBadge.classList.add('pill-word-style');
      // Reflect the specific disambiguated sense's POS if available
      typeBadge.textContent = chosenMeaning?.pos || token.pos || 'Vocabulary';
    }
    tokenModalBadges.appendChild(typeBadge);

    // Authentic Frequency in Spanish (Corpus 50k / Speech mode)
    const authenticRank = token.rank || token.speechRank || token.card?.speechRank || null;
    const rankBadge = document.createElement('span');
    rankBadge.className = 'token-type-pill pill-rank-style';
    if (token.type === 'entity') {
      rankBadge.textContent = 'Named Entity';
      tokenModalBadges.appendChild(rankBadge);
    } else if (token.type === 'mwe') {
      rankBadge.textContent = 'Multi-Word Expression';
      tokenModalBadges.appendChild(rankBadge);
    } else if (authenticRank && authenticRank > 0 && authenticRank <= 50000) {
      rankBadge.textContent = `#${Number(authenticRank).toLocaleString()} in Spanish frequency`;
      tokenModalBadges.appendChild(rankBadge);
    } else {
      rankBadge.textContent = '50,000+ Spanish frequency';
      tokenModalBadges.appendChild(rankBadge);
    }
  }

  // Meaning Callout
  if (modalMeaningCallout) {
    modalMeaningCallout.className = 'meaning-card';
    if (token.type === 'entity') modalMeaningCallout.classList.add('is-entity');
    else if (token.type === 'mwe') modalMeaningCallout.classList.add('is-mwe');
    else if (token.type === 'interjection') modalMeaningCallout.classList.add('is-interjection');
  }

  if (modalMeaningLabel) {
    if (token.type === 'entity') modalMeaningLabel.textContent = 'Entity in this instance';
    else if (token.type === 'mwe') modalMeaningLabel.textContent = 'Idiom in this instance';
    else if (token.type === 'interjection') modalMeaningLabel.textContent = 'Ad-lib in this instance';
    else modalMeaningLabel.textContent = 'Sense in this instance';
  }

  if (modalMeaningPrimary) modalMeaningPrimary.textContent = chosenMeaning?.translation || token.translation || token.word;
  if (modalMeaningContext) {
    const posStr = chosenMeaning?.pos || token.pos || '';
    modalMeaningContext.textContent = chosenMeaning?.context
      ? `Context: ${chosenMeaning.context}${posStr ? ` (${posStr})` : ''}`
      : (posStr ? `Part of speech: ${posStr}` : '');
  }

  // Entity Details
  if (modalEntityBox) {
    if (token.type === 'entity' && token.card?.entity) {
      modalEntityBox.style.display = 'block';
      if (modalEntityTitle) modalEntityTitle.textContent = token.card.entity.canonicalTitle || token.word;
      if (modalEntityDesc) modalEntityDesc.textContent = token.card.entity.description || 'Cultural figure, urban artist, brand, or location referenced in Spanish music.';
    } else {
      modalEntityBox.style.display = 'none';
    }
  }

  // Polysemous Breakdown Box (Show all other alternative senses cleanly one-by-one with click-to-expand)
  if (modalPolySensesBox && modalPolySensesList) {
    const otherMeanings = cardMeanings.filter((_, idx) => idx !== chosenIdx);
    if (otherMeanings.length > 0) {
      modalPolySensesBox.style.display = 'block';
      modalPolySensesList.innerHTML = '';
      otherMeanings.forEach(m => {
        const item = document.createElement('div');
        item.className = 'sense-item';
        item.innerHTML = `
          <div class="sense-row">
            <span class="sense-trans">${escapeHtml(m.translation)}</span>
            <div style="display: flex; align-items: center; gap: 4px;">
              <span class="sense-meta">${escapeHtml(m.pos || '')}</span>
              <span class="sense-chevron" aria-hidden="true">›</span>
            </div>
          </div>
          <div class="sense-details-drawer">
            <div><strong>Context / Usage:</strong> ${escapeHtml(m.context || 'Standard general usage')}</div>
          </div>
        `;
        item.addEventListener('click', () => {
          item.classList.toggle('is-expanded');
        });
        modalPolySensesList.appendChild(item);
      });
    } else {
      modalPolySensesBox.style.display = 'none';
    }
  }

  // Other occurrences of the word in the same song (excluding the exact current lyric line and duplicate copies)
  if (modalSongOccurrencesBox && modalSongOccurrencesList) {
    const songToSearch = currentAnnotatedSong || (currentSongIndex >= 0 ? allSongs[currentSongIndex] : null);
    const targetWord = (token.word || token.raw || '').toLowerCase();
    const targetRaw = (token.raw || '').toLowerCase();
    const currentLineIdx = token.lineIndex;
    const currentCleanLine = (token.lineText || '').trim().toLowerCase();

    const occurrences = [];
    const seenLineTexts = new Set();
    if (currentCleanLine) seenLineTexts.add(currentCleanLine); // Never show duplicates of the current line

    if (songToSearch && Array.isArray(songToSearch.lines)) {
      songToSearch.lines.forEach((lineObj, idx) => {
        if (idx === currentLineIdx) return; // Skip current lyric line
        const lineText = (lineObj.text || '').trim();
        const cleanText = lineText.toLowerCase();
        if (!lineText || seenLineTexts.has(cleanText)) return; // Deduplicate copies

        const lineTokens = lineObj.tokens || [];
        
        // Check if line contains this word
        let matched = false;
        if (lineTokens.length > 0) {
          matched = lineTokens.some(t => {
            const w = (t.word || '').toLowerCase();
            const r = (t.raw || '').toLowerCase();
            return (w && w === targetWord) || (r && r === targetRaw);
          });
        } else {
          // Fallback string search
          const regex = new RegExp(`\\b${escapeRegExp(targetWord)}\\b`, 'i');
          matched = regex.test(lineText);
        }

        if (matched) {
          seenLineTexts.add(cleanText);
          occurrences.push({
            lineIndex: idx,
            text: lineText,
            timestamp_ms: lineObj.timestamp_ms
          });
        }
      });
    }

    if (occurrences.length > 0) {
      modalSongOccurrencesBox.style.display = 'block';
      modalSongOccurrencesList.innerHTML = '';
      occurrences.forEach(occ => {
        const occItem = document.createElement('div');
        occItem.className = 'occurrence-item';
        const highlightedText = highlightTokenInLine(occ.text, token.raw || token.word);
        occItem.innerHTML = `
          <div class="occurrence-text">${highlightedText}</div>
          <div class="occurrence-meta">Line ${occ.lineIndex + 1}</div>
        `;
        modalSongOccurrencesList.appendChild(occItem);
      });
    } else {
      modalSongOccurrencesBox.style.display = 'none';
    }
  }

  // Navigation button states
  if (tokenPrevBtn) tokenPrevBtn.disabled = (currentModalTokenIndex <= 0);
  if (tokenNextBtn) tokenNextBtn.disabled = (currentModalTokenIndex >= songTokensFlatList.length - 1);

  if (tokenQuickViewModal) tokenQuickViewModal.classList.add('open');
}

function closeTokenModal() {
  tokenQuickViewModal.classList.remove('open');
}

function highlightTokenInLine(lineText, rawToken) {
  if (!lineText || !rawToken) return `"${lineText}"`;
  const escaped = rawToken.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'gi');
  const highlighted = lineText.replace(regex, `<span style="color: var(--accent-blue); font-weight: 700; text-decoration: underline;">$1</span>`);
  return `"${highlighted}"`;
}

// ───────────────────────────────────────────────
// Song Picker Modal & List Rendering
// ───────────────────────────────────────────────
function renderRecentSongShelf() {
  if (!recentSongShelf || !recentSongCard) return;
  // If user previously loaded an online/custom track, offer the most recent one
  const lastLoaded = (customSongs && customSongs.length > 0) ? customSongs[0] : null;
  if (!lastLoaded) {
    recentSongShelf.style.display = 'none';
    return;
  }

  recentSongShelf.style.display = 'block';
  recentSongCard.innerHTML = `
    <div class="recent-card-left">
      <span class="recent-badge-pill">Recent</span>
      <div>
        <div class="recent-card-title">${escapeHtml(lastLoaded.title)}</div>
        <div class="recent-card-artist">${escapeHtml(lastLoaded.artist)}</div>
      </div>
    </div>
    <span class="recent-resume-btn">Open Song ‹</span>
  `;

  recentSongCard.onclick = () => {
    closeSongPicker();
    const origIdx = allSongs.indexOf(lastLoaded);
    if (origIdx >= 0) selectSong(origIdx);
  };
}

function renderSongPickerItems(songs) {
  if (!songPickerList) return;
  songPickerList.innerHTML = '';

  renderRecentSongShelf();

  if (songs.length === 0) {
    // Show guided fallback pane
    songPickerList.style.display = 'none';
    if (catalogEmptyGuidance) {
      catalogEmptyGuidance.style.display = 'block';
      const curQuery = (songSearchInput ? songSearchInput.value.trim() : '');
      if (curQuery && turboTrackInput && !turboTrackInput.value) {
        turboTrackInput.value = curQuery;
        if (turboClearInputBtn) turboClearInputBtn.style.display = 'block';
      }
    }
    return;
  }

  // Catalogue matches exist: Show list, hide guidance
  songPickerList.style.display = 'flex';
  if (catalogEmptyGuidance) catalogEmptyGuidance.style.display = 'none';

  songs.forEach((s) => {
    const originalIndex = allSongs.indexOf(s);
    const item = document.createElement('div');
    item.className = `song-picker-item ${originalIndex === currentSongIndex ? 'active' : ''} ${s.isOnline ? 'is-online' : ''}`;
    item.dataset.index = originalIndex;

    // Song and artist only: the number, line count and badges were noise.
    item.innerHTML = `
      <div class="song-picker-item-left">
        <div>
          <div class="song-picker-name">${escapeHtml(s.title)}</div>
          <div class="song-picker-artist">${escapeHtml(s.artist)}</div>
        </div>
      </div>
    `;

    item.addEventListener('click', () => {
      closeSongPicker();
      selectSong(originalIndex);
    });

    songPickerList.appendChild(item);
  });
}

function openSongPicker(initialQuery = '') {
  hideTurboStatus();
  hideTurboError();
  if (catalogEmptyGuidance) catalogEmptyGuidance.style.display = 'none';
  if (turboManualDetails) turboManualDetails.style.display = 'none';

  if (songSearchInput) {
    songSearchInput.value = initialQuery;
    if (songSearchClearBtn) songSearchClearBtn.style.display = initialQuery ? 'block' : 'none';
  }

  // Hide Spotify intake tray by default when opening
  if (spotifyInputTray) spotifyInputTray.style.display = 'none';

  if (initialQuery) {
    filterCatalog(initialQuery);
  } else {
    // Catalogue only, without the old session imports
    renderSongPickerItems(catalogueSongs);
  }

  if (songPickerModal) songPickerModal.classList.add('open');
  if (songSearchInput) setTimeout(() => songSearchInput.focus(), 60);
}

function closeSongPicker() {
  if (songPickerModal) songPickerModal.classList.remove('open');
  hideTurboStatus();
  hideTurboError();
}

function filterCatalog(query) {
  const q = (query || '').trim();
  if (songSearchClearBtn) songSearchClearBtn.style.display = q ? 'block' : 'none';

  if (!q) {
    renderSongPickerItems(catalogueSongs);
    return;
  }

  if (q.startsWith('http') || q.startsWith('spotify:')) {
    // Show Spotify tray, fill input, and focus
    if (spotifyInputTray) spotifyInputTray.style.display = 'flex';
    if (turboTrackInput) {
      turboTrackInput.value = q;
      turboTrackInput.focus();
    }
    if (turboClearInputBtn) turboClearInputBtn.style.display = 'block';
    renderSongPickerItems([]); // Triggers guidance pane
    return;
  }

  const lower = q.toLowerCase();
  const filtered = catalogueSongs.filter(s =>
    (s.title || '').toLowerCase().includes(lower) ||
    (s.artist || '').toLowerCase().includes(lower) ||
    (s.lyrics || '').toLowerCase().includes(lower)
  );

  renderSongPickerItems(filtered);
}

// ───────────────────────────────────────────────
// Online TURBO Intake Logic
// ───────────────────────────────────────────────
function setTurboStatus(title, sub = '') {
  if (turboStatusCard) turboStatusCard.style.display = 'flex';
  if (turboStatusTitle) turboStatusTitle.textContent = title;
  if (turboStatusSub) turboStatusSub.textContent = sub;
}

function hideTurboStatus() {
  if (turboStatusCard) turboStatusCard.style.display = 'none';
}

function showTurboError(msg) {
  if (turboAlertBox) turboAlertBox.style.display = 'flex';
  if (turboAlertText) turboAlertText.textContent = msg;
}

function hideTurboError() {
  if (turboAlertBox) turboAlertBox.style.display = 'none';
}

function pickLyricsRecord(records) {
  if (!Array.isArray(records) || records.length === 0) return null;
  const usable = records.filter(r => !r.instrumental || (r.plainLyrics || '').trim() || (r.syncedLyrics || '').trim());
  if (usable.length === 0) return records[0] || null;
  // Prefer syncedLyrics first, else plainLyrics
  return usable.find(r => (r.syncedLyrics || '').trim()) ||
         usable.find(r => (r.plainLyrics || '').trim()) ||
         usable[0];
}

async function resolveOnlineTrack({ input, manualTitle, manualArtist, manualLyrics, allowEmptyLyrics = false }) {
  // Check manual lyrics first
  if (manualLyrics && manualLyrics.trim().length > 0) {
    return {
      title: (manualTitle || '').trim() || 'Custom Track',
      artist: (manualArtist || '').trim() || 'User Lyrics',
      lyrics: manualLyrics.trim(),
      syncedLyrics: '',
      isOnline: true
    };
  }

  const query = (input || '').trim();
  if (!query && !manualTitle) {
    throw new Error('Please enter a Spotify URL, track ID, song title & artist, or paste lyrics.');
  }

  // Detect Spotify ID or URL
  let spotifyTrackId = null;
  const urlMatch = query.match(/spotify\.com\/track\/([A-Za-z0-9]{22})/i);
  const uriMatch = query.match(/spotify:track:([A-Za-z0-9]{22})/i);
  const idMatch = query.match(/^([A-Za-z0-9]{22})$/);

  if (urlMatch) spotifyTrackId = urlMatch[1];
  else if (uriMatch) spotifyTrackId = uriMatch[1];
  else if (idMatch) spotifyTrackId = idMatch[1];

  let resolvedTitle = (manualTitle || '').trim();
  let resolvedArtist = (manualArtist || '').trim();

  if (spotifyTrackId) {
    setTurboStatus('Resolving Spotify track...', `Track ID: ${spotifyTrackId}`);
    const token = localStorage.getItem('spotify_access_token');
    if (token) {
      try {
        const resp = await fetch(`https://api.spotify.com/v1/tracks/${spotifyTrackId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (resp.ok) {
          const trackData = await resp.json();
          resolvedTitle = trackData.name || resolvedTitle;
          resolvedArtist = trackData.artists?.map(a => a.name).join(', ') || resolvedArtist;
        }
      } catch (e) {
        console.warn('Spotify API track query failed:', e);
      }
    }

    // Try Spotify oEmbed (public CORS)
    if (!resolvedTitle) {
      try {
        const oembedUrl = `https://open.spotify.com/oembed?url=https://open.spotify.com/track/${spotifyTrackId}`;
        const resp = await fetch(oembedUrl);
        if (resp.ok) {
          const data = await resp.json();
          if (data.title) resolvedTitle = data.title;
        }
      } catch (e) {
        console.warn('Spotify oEmbed query failed:', e);
      }
    }
  }

  // Search LRCLIB
  setTurboStatus('Searching LRCLIB for lyrics...', resolvedTitle ? `"${resolvedTitle}"` : query);
  let lrclibRecord = null;

  if (resolvedTitle && resolvedArtist) {
    try {
      const primaryArtist = resolvedArtist.split(',')[0].trim();
      const params = new URLSearchParams({ track_name: resolvedTitle, artist_name: primaryArtist });
      const resp = await fetch(`https://lrclib.net/api/search?${params}`, {
        headers: { 'Lrclib-Client': 'Fluency/0.1 (https://github.com/JoshuaThomasAmar/Fluency-Next)' }
      });
      if (resp.ok) {
        const list = await resp.json();
        lrclibRecord = pickLyricsRecord(list);
      }
    } catch (e) {
      console.warn('LRCLIB specific search failed:', e);
    }
  }

  if (!lrclibRecord) {
    const searchQuery = resolvedTitle ? (resolvedArtist ? `${resolvedTitle} ${resolvedArtist}` : resolvedTitle) : query;
    try {
      const resp = await fetch(`https://lrclib.net/api/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: { 'Lrclib-Client': 'Fluency/0.1 (https://github.com/JoshuaThomasAmar/Fluency-Next)' }
      });
      if (resp.ok) {
        const list = await resp.json();
        lrclibRecord = pickLyricsRecord(list);
      }
    } catch (e) {
      console.warn('LRCLIB search failed:', e);
    }
  }

  const hasLyrics = lrclibRecord && ((lrclibRecord.plainLyrics || '').trim() || (lrclibRecord.syncedLyrics || '').trim());

  if (!hasLyrics) {
    if (allowEmptyLyrics) {
      return {
        title: resolvedTitle || query || 'Unknown Track',
        artist: resolvedArtist || 'Unknown Artist',
        lyrics: '(Instrumental / No lyrics available)',
        syncedLyrics: '',
        spotifyId: spotifyTrackId || null,
        isOnline: true
      };
    }
    // Remember resolved title & artist for manual paste or go-without options
    if (turboManualTitle && resolvedTitle && !turboManualTitle.value) turboManualTitle.value = resolvedTitle;
    if (turboManualArtist && resolvedArtist && !turboManualArtist.value) turboManualArtist.value = resolvedArtist;

    throw new Error('Lyrics not found for this track.');
  }

  return {
    title: lrclibRecord.name || lrclibRecord.trackName || resolvedTitle || query,
    artist: lrclibRecord.artistName || resolvedArtist || 'Unknown Artist',
    lyrics: (lrclibRecord.plainLyrics || '').trim(),
    syncedLyrics: (lrclibRecord.syncedLyrics || '').trim(),
    spotifyId: spotifyTrackId || null,
    isOnline: true
  };
}

async function handleRunTurbo(options = {}) {
  hideTurboError();
  const input = (options.input !== undefined ? options.input : (turboTrackInput ? turboTrackInput.value.trim() : (songSearchInput ? songSearchInput.value.trim() : ''))).trim();
  if (turboTrackInput && options.input) {
    turboTrackInput.value = options.input;
  }
  const manualTitle = turboManualTitle ? turboManualTitle.value.trim() : '';
  const manualArtist = turboManualArtist ? turboManualArtist.value.trim() : '';
  const manualLyrics = turboManualLyrics ? turboManualLyrics.value.trim() : '';
  const allowEmpty = Boolean(options.allowEmptyLyrics);

  if (!input && !manualLyrics && !manualTitle) {
    showTurboError('Please enter a Spotify URL, track ID, song search, or paste lyrics.');
    if (turboTrackInput) turboTrackInput.focus();
    return;
  }

  if (runTurboBtn) runTurboBtn.disabled = true;

  try {
    const songData = await resolveOnlineTrack({
      input,
      manualTitle,
      manualArtist,
      manualLyrics,
      allowEmptyLyrics: allowEmpty
    });

    setTurboStatus('Searching Genius for verified English translation...', `"${songData.title}" by ${songData.artist}`);

    // Check Cloudflare Worker proxy for authentic Genius human English translation
    try {
      const gResp = await fetch('https://fluency-api.rabbijoshy.workers.dev', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'getGeniusTranslation',
          title: songData.title,
          artist: songData.artist
        })
      });
      if (gResp.ok) {
        const gData = await gResp.json();
        if (gData.success && gData.data?.found && Array.isArray(gData.data?.lines) && gData.data.lines.length > 0) {
          songData.englishLines = gData.data.lines;
          songData.translationSource = 'genius';
          songData.translationTitle = gData.data.translationTitle || '';
        }
      }
    } catch (gErr) {
      console.warn('Genius translation lookup failed, continuing with Spanish only:', gErr);
    }

    setTurboStatus('Running intake engine...', 'Tokenizing and analyzing vocabulary...');

    const result = await engine.processPlaylist([songData]);
    const annotatedSong = result.annotatedSongs?.[0];
    if (!annotatedSong || !annotatedSong.lines || annotatedSong.lines.length === 0) {
      throw new Error('Processed 0 lines for this track.');
    }

    // Attach verified English translation lines if available
    if (songData.englishLines && songData.englishLines.length > 0) {
      annotatedSong.lines.forEach((l, idx) => {
        if (idx < songData.englishLines.length) {
          l.english = songData.englishLines[idx];
        }
      });
    }

    postProcessAnnotatedSong(annotatedSong);

    songData.id = 'online_' + Date.now();
    customSongs.unshift(songData);
    try {
      sessionStorage.setItem(`fluency_turbo_custom_songs_${currentLanguage}`, JSON.stringify(customSongs));
    } catch (_) {}

    allSongs = [...customSongs, ...catalogueSongs];
    annotatedCache.set(songCacheKey(songData), annotatedSong);

    hideTurboStatus();
    if (runTurboBtn) runTurboBtn.disabled = false;

    // Reset input fields
    if (turboTrackInput) turboTrackInput.value = '';
    if (turboManualLyrics) turboManualLyrics.value = '';
    if (turboManualTitle) turboManualTitle.value = '';
    if (turboManualArtist) turboManualArtist.value = '';
    if (turboClearInputBtn) turboClearInputBtn.style.display = 'none';

    renderSongPickerItems(allSongs);
    closeSongPicker();
    await selectSong(0); // Select the newly generated song
  } catch (err) {
    console.error('Intake error:', err);
    hideTurboStatus();
    if (runTurboBtn) runTurboBtn.disabled = false;
    showTurboError(err.message || 'Lyrics not found for this track.');
  }
}

// ───────────────────────────────────────────────
// Event Listeners
// ───────────────────────────────────────────────
if (backToLibraryBtn) backToLibraryBtn.addEventListener('click', () => openSongPicker());
if (closeSongPickerBtn) closeSongPickerBtn.addEventListener('click', closeSongPicker);

if (openManualPasteBtn) {
  openManualPasteBtn.addEventListener('click', () => {
    if (turboManualDetails) {
      turboManualDetails.style.display = 'flex';
      if (turboManualLyrics) turboManualLyrics.focus();
    }
  });
}

if (goWithoutLyricsBtn) {
  goWithoutLyricsBtn.addEventListener('click', () => {
    handleRunTurbo({ allowEmptyLyrics: true });
  });
}

if (runTurboBtn) runTurboBtn.addEventListener('click', () => handleRunTurbo());
if (turboTrackInput) {
  turboTrackInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleRunTurbo();
  });
  turboTrackInput.addEventListener('input', () => {
    if (turboClearInputBtn) {
      turboClearInputBtn.style.display = turboTrackInput.value ? 'block' : 'none';
    }
  });
}
if (turboClearInputBtn) {
  turboClearInputBtn.addEventListener('click', () => {
    if (turboTrackInput) {
      turboTrackInput.value = '';
      turboTrackInput.focus();
    }
    turboClearInputBtn.style.display = 'none';
  });
}

if (songPickerModal) {
  songPickerModal.addEventListener('click', (e) => {
    if (e.target === songPickerModal) closeSongPicker();
  });
}

if (toggleEnglishBtn) {
  toggleEnglishBtn.addEventListener('click', () => {
    showEnglishUnderneath = !showEnglishUnderneath;
    toggleEnglishBtn.setAttribute('aria-pressed', String(showEnglishUnderneath));
    try { localStorage.setItem('fluency_lyrics_show_english', showEnglishUnderneath ? '1' : '0'); } catch (_) {}
    document.querySelectorAll('.lyric-line-english').forEach(el => {
      el.classList.toggle('is-hidden', !showEnglishUnderneath);
    });
  });
}

if (songSearchInput) {
  songSearchInput.addEventListener('input', (e) => {
    filterCatalog(e.target.value);
  });
  songSearchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const q = e.target.value.trim();
      if (q.startsWith('http') || q.startsWith('spotify:')) {
        handleRunTurbo();
      }
    }
  });
}

if (songSearchClearBtn) {
  songSearchClearBtn.addEventListener('click', () => {
    if (songSearchInput) {
      songSearchInput.value = '';
      filterCatalog('');
      songSearchInput.focus();
    }
    songSearchClearBtn.style.display = 'none';
  });
}

if (closeTokenModalBtn) closeTokenModalBtn.addEventListener('click', closeTokenModal);
if (tokenQuickViewModal) {
  tokenQuickViewModal.addEventListener('click', (e) => {
    if (e.target === tokenQuickViewModal) closeTokenModal();
  });
}

if (tokenPrevBtn) {
  tokenPrevBtn.addEventListener('click', () => {
    if (currentModalTokenIndex > 0) {
      openTokenModal(songTokensFlatList[currentModalTokenIndex - 1]);
    }
  });
}

if (tokenNextBtn) {
  tokenNextBtn.addEventListener('click', () => {
    if (currentModalTokenIndex < songTokensFlatList.length - 1) {
      openTokenModal(songTokensFlatList[currentModalTokenIndex + 1]);
    }
  });
}

if (openSpotifyInputBtn) {
  openSpotifyInputBtn.addEventListener('click', () => {
    if (spotifyInputTray) {
      const isVisible = spotifyInputTray.style.display === 'flex';
      spotifyInputTray.style.display = isVisible ? 'none' : 'flex';
      if (!isVisible && turboTrackInput) {
        turboTrackInput.focus();
      }
    }
  });
}

// Global click outside to dismiss any open lyric AI sheet and disarm chips
document.addEventListener('click', (e) => {
  if (!e.target.closest('.lyric-ai-wrap')) {
    closeAllAiSheets();
  }
});

// Keyboard controls
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeTokenModal();
    closeSongPicker();
    closeAllAiSheets();
  } else if (tokenQuickViewModal && tokenQuickViewModal.classList.contains('open')) {
    if (e.key === 'ArrowLeft' && currentModalTokenIndex > 0) {
      openTokenModal(songTokensFlatList[currentModalTokenIndex - 1]);
    } else if (e.key === 'ArrowRight' && currentModalTokenIndex < songTokensFlatList.length - 1) {
      openTokenModal(songTokensFlatList[currentModalTokenIndex + 1]);
    }
  }
});

// Boot
init();

