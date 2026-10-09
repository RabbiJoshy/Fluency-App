import { TurboEngine } from '../turbo/turbo-engine.js?v=96375c29';

// Common Spanish & Latin urban ad-libs, interjections, and exclamations
const INTERJECTIONS_SET = new Set([
  'brr', 'wuh', 'ey', 'eh', 'ay', 'oh', 'ah', 'ja', 'jaja', 'yah', 'uh',
  'shh', 'prr', 'rra', 'amén', 'dale', 'oye', 'mera', 'woh', 'uah', 'pla',
  'pew', 'okey', 'bye', 'epa', 'uf', 'chao', 'hola', 'adiós', 'puñeta',
  'carajo', 'dios', 'mami'
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

  // Irregular / common fixed contractions
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
let probeSongs = [];
let customSongs = [];
let allSongs = [];
let annotatedCache = new Map(); // songCacheKey -> annotatedSong
let currentSongIndex = 0;
let currentAnnotatedSong = null;
let showEnglishUnderneath = true;

// Flat list of all tokens in current song for modal next/previous stepping
let songTokensFlatList = [];
let currentModalTokenIndex = -1;

// DOM Elements
const backToLibraryBtn = document.getElementById('backToLibraryBtn');
const topbarSongTitle = document.getElementById('topbarSongTitle');
const topbarSongArtist = document.getElementById('topbarSongArtist');
const songSelectorBtn = document.getElementById('songSelectorBtn');
const topbarTurboBtn = document.getElementById('topbarTurboBtn');
const prevSongBtn = document.getElementById('prevSongBtn');
const nextSongBtn = document.getElementById('nextSongBtn');
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
function songCacheKey(song) {
  if (!song) return '';
  if (song.id) return song.id;
  return `${song.title || ''}:::${song.artist || ''}`;
}

function loadSavedCustomSongs() {
  try {
    const raw = sessionStorage.getItem('fluency_turbo_custom_songs');
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
    const urlParams = new URLSearchParams(window.location.search);
    const paramSong = urlParams.get('song');

    // Robust asset paths relative to this module
    const assetsUrl = new URL('../turbo/turbo_assets.json', import.meta.url).href;
    const extra50kUrl = new URL('../turbo/es_50k_data.json', import.meta.url).href;
    const songsUrl = new URL('../turbo/probe_songs.json', import.meta.url).href;

    // Load assets (read-only)
    engine = await TurboEngine.create(assetsUrl, extra50kUrl);

    // Load 30 offline songs (read-only)
    const songsResp = await fetch(songsUrl);
    if (!songsResp.ok) throw new Error(`HTTP ${songsResp.status} loading offline songs`);
    probeSongs = await songsResp.json();
    probeSongs.forEach((s, idx) => {
      s.id = `offline_${idx}`;
      s.isOffline = true;
    });

    // Hydrate offline curated songs with verified human English translations from the local audit catalog
    try {
      const yonResp = await fetch('../lyrics-audit/data/yonaguni.json');
      if (yonResp.ok) {
        const yonData = await yonResp.json();
        const yLines = yonData.song?.lines || [];
        const yonProbe = probeSongs.find(s => (s.title || '').toLowerCase() === 'yonaguni');
        if (yonProbe && yLines.length > 0) {
          yonProbe.englishLines = yLines.map(l => l.translation?.english || null);
          yonProbe.translationSource = 'genius';
        }
      }
    } catch (_) {}

    // Load session-generated songs
    customSongs = loadSavedCustomSongs();
    allSongs = [...customSongs, ...probeSongs];

    if (offlineCountBadge) {
      offlineCountBadge.textContent = String(probeSongs.length);
    }

    renderSongPickerItems(allSongs);

    // If a specific song was requested in URL query, load it; otherwise open the library modal
    if (paramSong) {
      const parsedIdx = parseInt(paramSong, 10);
      if (!isNaN(parsedIdx) && parsedIdx >= 0 && parsedIdx < allSongs.length) {
        currentSongIndex = parsedIdx;
      } else {
        const foundIdx = allSongs.findIndex(s =>
          (s.title || '').toLowerCase().includes(paramSong.toLowerCase()) ||
          (s.artist || '').toLowerCase().includes(paramSong.toLowerCase())
        );
        if (foundIdx >= 0) currentSongIndex = foundIdx;
      }
      await selectSong(currentSongIndex);
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

  // Also populate compatibility anchors if present
  const mainSongTitle = document.getElementById('mainSongTitle');
  if (mainSongTitle) mainSongTitle.textContent = song.title || '';
  const mainSongArtist = document.getElementById('mainSongArtist');
  if (mainSongArtist) mainSongArtist.textContent = song.artist || '';

  if (prevSongBtn) prevSongBtn.disabled = (index === 0);
  if (nextSongBtn) nextSongBtn.disabled = (index === allSongs.length - 1);

  // Sync URL query without reloading (if requested)
  if (syncUrl) {
    try {
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.set('song', index);
      window.history.replaceState({}, '', newUrl.toString());
    } catch (_) {}
  }

  if (lyricsFlow) lyricsFlow.style.display = 'none';
  if (loadingBox) loadingBox.style.display = 'block';

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
              token.translation = `Top ${Math.ceil(resolved.rank / 1000) * 1000} Spanish word`;
            }
          }
        }
      }
    }
  }
}

/**
 * Returns genuine, hand-translated English line if available; otherwise null.
 * Never constructs synthetic word-by-word gloss strings.
 */
function buildLineEnglishGloss(line) {
  if (line.english && typeof line.english === 'string' && line.english.trim().length > 0) {
    return line.english.trim();
  }
  return null;
}

// ───────────────────────────────────────────────
// Render Spotify-Style Lyrics View
// ───────────────────────────────────────────────
function renderLyrics(song) {
  lyricsFlow.innerHTML = '';
  songTokensFlatList = [];

  const hasAnyEnglish = song.lines.some(l => l.english && typeof l.english === 'string' && l.english.trim());
  if (toggleEnglishBtn) {
    toggleEnglishBtn.style.display = hasAnyEnglish ? 'inline-flex' : 'none';
  }

  const songHasTimestamps = song.lines.some(l => l.isSynced && l.timestamp_ms != null);

  song.lines.forEach((line, lineIdx) => {
    const lineItem = document.createElement('div');
    lineItem.className = 'lyric-line-item';
    lineItem.dataset.lineIndex = lineIdx;

    // 1. Optional Left Gutter: Timestamp (only rendered if track has synced timestamps)
    if (songHasTimestamps) {
      if (line.isSynced && line.timestamp_ms != null) {
        const totalSec = Math.floor(line.timestamp_ms / 1000);
        const m = Math.floor(totalSec / 60);
        const s = totalSec % 60;
        const timeSpan = document.createElement('span');
        timeSpan.className = 'lyric-line-timestamp';
        timeSpan.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
        lineItem.appendChild(timeSpan);
      } else {
        const spacer = document.createElement('span');
        spacer.className = 'lyric-line-timestamp-spacer';
        lineItem.appendChild(spacer);
      }
    }

    // 2. Main Body Column (Target Spanish + English underneath perfectly aligned)
    const lineBody = document.createElement('div');
    lineBody.className = 'lyric-line-body';

    // Target Spanish Line (Large, bold)
    const targetLine = document.createElement('div');
    targetLine.className = 'lyric-line-target';

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
        // Enclosing pill with authentic Wiktionary icon (white circle with black W)
        span.innerHTML = `${escapeHtml(token.raw)}<span class="entity-wiktionary-icon" aria-hidden="true" title="Wiktionary / Cultural Entity">W</span>`;
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
    });

    lineBody.appendChild(targetLine);

    // English Line Underneath (Only if genuine hand-translated line exists)
    const englishGloss = buildLineEnglishGloss(line);
    if (englishGloss) {
      const englishLine = document.createElement('div');
      englishLine.className = 'lyric-line-english';

      const textSpan = document.createElement('span');
      textSpan.textContent = englishGloss;
      englishLine.appendChild(textSpan);

      lineBody.appendChild(englishLine);
    }

    lineItem.appendChild(lineBody);

    lyricsFlow.appendChild(lineItem);
  });
}

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
function renderSongPickerItems(songs) {
  if (!songPickerList) return;
  songPickerList.innerHTML = '';

  if (songs.length === 0) {
    // Show guided fallback pane
    songPickerList.style.display = 'none';
    if (catalogEmptyGuidance) {
      catalogEmptyGuidance.style.display = 'block';
      // Auto-populate input with search term if it looks like a query or link
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

    const onlineBadge = s.isOnline ? `<span class="song-picker-online-badge">ONLINE</span>` : '';
    const lineCount = (s.lyrics || s.plainLyrics || '').split('\n').filter(l => l.trim()).length || (s.syncedLyrics ? s.syncedLyrics.split('\n').length : 0);

    item.innerHTML = `
      <div class="song-picker-item-left">
        <span class="song-picker-num">${originalIndex + 1}</span>
        <div>
          <div class="song-picker-name">${s.title}${onlineBadge}</div>
          <div class="song-picker-artist">${s.artist}</div>
        </div>
      </div>
      <span class="song-picker-lines">${lineCount} lines</span>
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

  if (initialQuery) {
    filterCatalog(initialQuery);
  } else {
    renderSongPickerItems(allSongs);
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
    renderSongPickerItems(allSongs);
    return;
  }

  if (q.startsWith('http') || q.startsWith('spotify:')) {
    // Directly guide to paste link
    if (turboTrackInput) turboTrackInput.value = q;
    if (turboClearInputBtn) turboClearInputBtn.style.display = 'block';
    renderSongPickerItems([]); // Triggers guidance pane
    return;
  }

  const lower = q.toLowerCase();
  const filtered = allSongs.filter(s =>
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
  const input = turboTrackInput ? turboTrackInput.value.trim() : (songSearchInput ? songSearchInput.value.trim() : '');
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
      sessionStorage.setItem('fluency_turbo_custom_songs', JSON.stringify(customSongs));
    } catch (_) {}

    allSongs = [...customSongs, ...probeSongs];
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
if (songSelectorBtn) songSelectorBtn.addEventListener('click', () => openSongPicker());
if (topbarTurboBtn) topbarTurboBtn.addEventListener('click', () => openSongPicker());
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

if (prevSongBtn) {
  prevSongBtn.addEventListener('click', () => {
    if (currentSongIndex > 0) selectSong(currentSongIndex - 1);
  });
}

if (nextSongBtn) {
  nextSongBtn.addEventListener('click', () => {
    if (currentSongIndex < allSongs.length - 1) selectSong(currentSongIndex + 1);
  });
}

if (toggleEnglishBtn) {
  toggleEnglishBtn.addEventListener('click', () => {
    showEnglishUnderneath = !showEnglishUnderneath;
    toggleEnglishBtn.classList.toggle('active', showEnglishUnderneath);
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

// Keyboard controls
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeTokenModal();
    closeSongPicker();
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

