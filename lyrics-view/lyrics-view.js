import { TurboEngine } from '../turbo/turbo-engine.js?v=2abbe085';

// Common Spanish & Latin urban ad-libs, interjections, and exclamations
const INTERJECTIONS_SET = new Set([
  'brr', 'wuh', 'ey', 'eh', 'ay', 'oh', 'ah', 'ja', 'jaja', 'yah', 'uh',
  'shh', 'prr', 'rra', 'amén', 'dale', 'oye', 'mera', 'woh', 'uah', 'pla',
  'pew', 'okey', 'bye', 'epa', 'uf', 'chao', 'hola', 'adiós', 'puñeta',
  'carajo', 'dios', 'mami'
]);

let engine = null;
let probeSongs = [];
let customSongs = [];
let allSongs = [];
let annotatedCache = new Map(); // songCacheKey -> annotatedSong
let currentSongIndex = 0;
let showEnglishUnderneath = true;

// Flat list of all tokens in current song for modal next/previous stepping
let songTokensFlatList = [];
let currentModalTokenIndex = -1;

// DOM Elements
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
const tabOfflineBtn = document.getElementById('tabOfflineBtn');
const tabOnlineBtn = document.getElementById('tabOnlineBtn');
const tabOfflinePane = document.getElementById('tabOfflinePane');
const tabOnlinePane = document.getElementById('tabOnlinePane');
const offlineCountBadge = document.getElementById('offlineCountBadge');

// Online TURBO Elements
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

function switchPickerTab(tab) {
  hideTurboError();
  if (tab === 'offline') {
    if (tabOfflineBtn) {
      tabOfflineBtn.classList.add('active');
      tabOfflineBtn.setAttribute('aria-selected', 'true');
    }
    if (tabOnlineBtn) {
      tabOnlineBtn.classList.remove('active');
      tabOnlineBtn.setAttribute('aria-selected', 'false');
    }
    if (tabOfflinePane) tabOfflinePane.style.display = 'block';
    if (tabOnlinePane) tabOnlinePane.style.display = 'none';
    if (songSearchInput) setTimeout(() => songSearchInput.focus(), 50);
  } else {
    if (tabOnlineBtn) {
      tabOnlineBtn.classList.add('active');
      tabOnlineBtn.setAttribute('aria-selected', 'true');
    }
    if (tabOfflineBtn) {
      tabOfflineBtn.classList.remove('active');
      tabOfflineBtn.setAttribute('aria-selected', 'false');
    }
    if (tabOfflinePane) tabOfflinePane.style.display = 'none';
    if (tabOnlinePane) tabOnlinePane.style.display = 'block';
    if (turboTrackInput) setTimeout(() => turboTrackInput.focus(), 50);
  }
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
    const songsUrl = new URL('../turbo/probe_songs.json', import.meta.url).href;

    // Load assets (read-only)
    engine = await TurboEngine.create(assetsUrl);

    // Load 30 offline songs (read-only)
    const songsResp = await fetch(songsUrl);
    if (!songsResp.ok) throw new Error(`HTTP ${songsResp.status} loading offline songs`);
    probeSongs = await songsResp.json();
    probeSongs.forEach((s, idx) => {
      s.id = `offline_${idx}`;
      s.isOffline = true;
    });

    // Load session-generated songs
    customSongs = loadSavedCustomSongs();
    allSongs = [...customSongs, ...probeSongs];

    if (offlineCountBadge) {
      offlineCountBadge.textContent = String(probeSongs.length);
    }

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
    }

    renderSongPickerItems(allSongs);
    await selectSong(currentSongIndex);
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
async function selectSong(index) {
  if (index < 0 || index >= allSongs.length) return;
  currentSongIndex = index;

  const song = allSongs[index];
  if (topbarSongTitle) topbarSongTitle.textContent = song.title || '';
  if (topbarSongArtist) {
    topbarSongArtist.textContent = (song.artist || '') + (song.isOnline ? ' · ⚡ TURBO' : '');
  }

  // Also populate compatibility anchors if present
  const mainSongTitle = document.getElementById('mainSongTitle');
  if (mainSongTitle) mainSongTitle.textContent = song.title || '';
  const mainSongArtist = document.getElementById('mainSongArtist');
  if (mainSongArtist) mainSongArtist.textContent = song.artist || '';

  if (prevSongBtn) prevSongBtn.disabled = (index === 0);
  if (nextSongBtn) nextSongBtn.disabled = (index === allSongs.length - 1);

  // Sync URL query without reloading
  try {
    const newUrl = new URL(window.location.href);
    newUrl.searchParams.set('song', index);
    window.history.replaceState({}, '', newUrl.toString());
  } catch (_) {}

  if (lyricsFlow) lyricsFlow.style.display = 'none';
  if (loadingBox) loadingBox.style.display = 'block';

  const cacheKey = songCacheKey(song);
  let annotatedSong = annotatedCache.get(cacheKey);
  if (!annotatedSong) {
    const result = await engine.processPlaylist([song]);
    annotatedSong = result.annotatedSongs?.[0];
    if (annotatedSong) {
      postProcessAnnotatedSong(annotatedSong);
      annotatedCache.set(cacheKey, annotatedSong);
    }
  }

  if (loadingBox) loadingBox.style.display = 'none';
  if (lyricsFlow) lyricsFlow.style.display = 'flex';

  if (annotatedSong) {
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
          if (!token.translation || token.translation === 'out of 10k supply / noise') {
            token.translation = 'ad-lib / vocal exclamation';
          }
        }
      }
    }
  }
}

/**
 * Generates a clean, natural English gloss line for a lyric row
 */
function buildLineEnglishGloss(line) {
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
    // Capitalize first letter
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

  song.lines.forEach((line, lineIdx) => {
    const lineItem = document.createElement('div');
    lineItem.className = 'lyric-line-item';
    lineItem.dataset.lineIndex = lineIdx;

    // 1. Target Spanish Line (Large, bold)
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
      span.textContent = token.raw;

      if (token.type === 'entity') {
        span.classList.add('token-entity');
        span.title = `🌸 Entity: ${token.word} (${token.translation || 'Cultural referent'})`;
        lineAutoBadges.push({
          type: 'entity',
          label: `🌸 ${token.raw}`,
          sub: token.card?.entity?.entityType || 'Entity',
          token
        });
      } else if (token.type === 'mwe') {
        span.classList.add('token-mwe');
        span.title = `🟣 Idiom: ${token.word} (${token.translation})`;
        lineAutoBadges.push({
          type: 'mwe',
          label: `🟣 ${token.raw}`,
          sub: token.translation,
          token
        });
      } else if (token.type === 'interjection') {
        span.classList.add('token-interjection');
        span.title = `⚡ Ad-lib: ${token.translation || token.raw}`;
        lineAutoBadges.push({
          type: 'interjection',
          label: `⚡ ${token.raw}`,
          sub: 'ad-lib',
          token
        });
      } else {
        span.classList.add('token-word');
        if (token.isElision) {
          span.classList.add('token-elision');
          span.title = `Elision: ${token.raw} → ${token.word}`;
        } else {
          span.title = `${token.word}: ${token.translation || 'Word'}`;
        }
      }

      span.addEventListener('click', (e) => {
        e.stopPropagation();
        openTokenModal(token);
      });

      targetLine.appendChild(span);
    });

    lineItem.appendChild(targetLine);

    // 2. English Line Underneath (Spotify Subtitle Style)
    const englishGloss = buildLineEnglishGloss(line);
    if (englishGloss) {
      const englishLine = document.createElement('div');
      englishLine.className = `lyric-line-english ${showEnglishUnderneath ? '' : 'is-hidden'}`;

      if (line.isSynced && line.timestamp_ms != null) {
        const totalSec = Math.floor(line.timestamp_ms / 1000);
        const m = Math.floor(totalSec / 60);
        const s = totalSec % 60;
        const timeSpan = document.createElement('span');
        timeSpan.className = 'lyric-line-timestamp';
        timeSpan.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
        englishLine.appendChild(timeSpan);
      }

      const textSpan = document.createElement('span');
      textSpan.textContent = englishGloss;
      englishLine.appendChild(textSpan);

      lineItem.appendChild(englishLine);
    }

    // 3. Subtle inline line badges if line contains entities or idioms
    if (lineAutoBadges.length > 0) {
      const badgesRow = document.createElement('div');
      badgesRow.className = 'line-auto-badges';

      lineAutoBadges.forEach(item => {
        const badge = document.createElement('span');
        badge.className = `line-auto-badge badge-${item.type}`;
        badge.innerHTML = `<strong>${item.label}</strong> <small style="opacity:0.75;">· ${item.sub}</small>`;
        badge.addEventListener('click', (e) => {
          e.stopPropagation();
          openTokenModal(item.token);
        });
        badgesRow.appendChild(badge);
      });

      lineItem.appendChild(badgesRow);
    }

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

  // Badges
  if (tokenModalBadges) {
    tokenModalBadges.innerHTML = '';
    const typeBadge = document.createElement('span');
    typeBadge.className = 'token-type-pill';

    if (token.type === 'entity') {
      typeBadge.classList.add('pill-entity-style');
      const entType = token.card?.entity?.entityType || 'Cultural Entity';
      typeBadge.textContent = `🌸 ${entType}`;
    } else if (token.type === 'mwe') {
      typeBadge.classList.add('pill-mwe-style');
      typeBadge.textContent = `🟣 Idiom / MWE`;
    } else if (token.type === 'interjection') {
      typeBadge.classList.add('pill-intj-style');
      typeBadge.textContent = `⚡ Ad-lib / Interjection`;
    } else {
      typeBadge.classList.add('pill-word-style');
      typeBadge.textContent = `🔷 ${token.pos || 'Vocabulary'}`;
    }
    tokenModalBadges.appendChild(typeBadge);

    if (token.rank) {
      const rankBadge = document.createElement('span');
      rankBadge.className = 'token-type-pill pill-rank-style';
      rankBadge.textContent = `#${token.rank} in frequency`;
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
    if (token.type === 'entity') modalMeaningLabel.textContent = 'Entity Sense';
    else if (token.type === 'mwe') modalMeaningLabel.textContent = 'Idiomatic Sense';
    else if (token.type === 'interjection') modalMeaningLabel.textContent = 'Ad-lib & Usage';
    else modalMeaningLabel.textContent = 'Sense Assignment';
  }

  if (modalMeaningPrimary) modalMeaningPrimary.textContent = token.translation || token.word;
  if (modalMeaningContext) {
    modalMeaningContext.textContent = token.card?.meanings?.[0]?.context
      ? `Context: ${token.card.meanings[0].context}`
      : (token.pos ? `Part of speech: ${token.pos}` : '');
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

  // Polysemous Breakdown Box
  if (modalPolySensesBox && modalPolySensesList) {
    const cardMeanings = token.card?.meanings || [];
    if (cardMeanings.length > 1) {
      modalPolySensesBox.style.display = 'block';
      modalPolySensesList.innerHTML = '';
      cardMeanings.slice(1).forEach(m => {
        const item = document.createElement('div');
        item.className = 'sense-item';
        item.innerHTML = `
          <span class="sense-trans">${m.translation}</span>
          <span class="sense-meta">${m.pos} ${m.context ? `· ${m.context}` : ''}</span>
        `;
        modalPolySensesList.appendChild(item);
      });
    } else {
      modalPolySensesBox.style.display = 'none';
    }
  }

  // Context Quote
  if (modalContextQuoteText) modalContextQuoteText.innerHTML = highlightTokenInLine(token.lineText || '', token.raw);
  if (modalContextQuoteMeta) modalContextQuoteMeta.textContent = `Line ${(token.lineIndex || 0) + 1} · ${token.songTitle || ''} (${token.songArtist || ''})`;

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
  songs.forEach((s) => {
    const originalIndex = allSongs.indexOf(s);
    const item = document.createElement('div');
    item.className = `song-picker-item ${originalIndex === currentSongIndex ? 'active' : ''} ${s.isOnline ? 'is-online' : ''}`;
    item.dataset.index = originalIndex;

    const onlineBadge = s.isOnline ? `<span class="song-picker-online-badge">⚡ ONLINE</span>` : '';
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

function openSongPicker(initialTab = 'offline') {
  if (songSearchInput) songSearchInput.value = '';
  renderSongPickerItems(allSongs);
  switchPickerTab(initialTab);
  if (songPickerModal) songPickerModal.classList.add('open');
}

function closeSongPicker() {
  if (songPickerModal) songPickerModal.classList.remove('open');
  hideTurboStatus();
  hideTurboError();
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

async function resolveOnlineTrack({ input, manualTitle, manualArtist, manualLyrics }) {
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
  if (!query) {
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

  let resolvedTitle = '';
  let resolvedArtist = '';

  if (spotifyTrackId) {
    setTurboStatus('Resolving Spotify track...', `Track ID: ${spotifyTrackId}`);
    // If Spotify access token in localStorage
    const token = localStorage.getItem('spotify_access_token');
    if (token) {
      try {
        const resp = await fetch(`https://api.spotify.com/v1/tracks/${spotifyTrackId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (resp.ok) {
          const trackData = await resp.json();
          resolvedTitle = trackData.name || '';
          resolvedArtist = trackData.artists?.map(a => a.name).join(', ') || '';
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

  if (!lrclibRecord || (!lrclibRecord.plainLyrics && !lrclibRecord.syncedLyrics)) {
    if (resolvedTitle) {
      throw new Error(`Found Spotify track "${resolvedTitle}", but no lyrics were found on LRCLIB. Please paste the lyrics in the section below to run TURBO!`);
    }
    throw new Error('No lyrics found on LRCLIB for this search. Try "Song Title - Artist" or paste lyrics directly.');
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

async function handleRunTurbo() {
  hideTurboError();
  const input = turboTrackInput ? turboTrackInput.value.trim() : '';
  const manualTitle = turboManualTitle ? turboManualTitle.value.trim() : '';
  const manualArtist = turboManualArtist ? turboManualArtist.value.trim() : '';
  const manualLyrics = turboManualLyrics ? turboManualLyrics.value.trim() : '';

  if (!input && !manualLyrics) {
    showTurboError('Please enter a Spotify URL, track ID, song search, or paste lyrics.');
    if (turboTrackInput) turboTrackInput.focus();
    return;
  }

  if (runTurboBtn) runTurboBtn.disabled = true;

  try {
    const songData = await resolveOnlineTrack({ input, manualTitle, manualArtist, manualLyrics });
    setTurboStatus('Running TURBO engine...', 'Tokenizing, analyzing Caribbean elisions, entities & senses...');

    const result = await engine.processPlaylist([songData]);
    const annotatedSong = result.annotatedSongs?.[0];
    if (!annotatedSong || !annotatedSong.lines || annotatedSong.lines.length === 0) {
      throw new Error('TURBO processed 0 lines for this track.');
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
    console.error('TURBO online intake error:', err);
    hideTurboStatus();
    if (runTurboBtn) runTurboBtn.disabled = false;
    showTurboError(err.message || 'Failed to process track with TURBO.');
    // If lyrics missing, open manual details
    if (turboManualDetails && err.message.includes('paste')) {
      turboManualDetails.open = true;
      if (turboManualLyrics) turboManualLyrics.focus();
    }
  }
}

// ───────────────────────────────────────────────
// Event Listeners
// ───────────────────────────────────────────────
if (songSelectorBtn) songSelectorBtn.addEventListener('click', () => openSongPicker('offline'));
if (topbarTurboBtn) topbarTurboBtn.addEventListener('click', () => openSongPicker('online'));
if (closeSongPickerBtn) closeSongPickerBtn.addEventListener('click', closeSongPicker);

if (tabOfflineBtn) tabOfflineBtn.addEventListener('click', () => switchPickerTab('offline'));
if (tabOnlineBtn) tabOnlineBtn.addEventListener('click', () => switchPickerTab('online'));

if (runTurboBtn) runTurboBtn.addEventListener('click', handleRunTurbo);
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
    const q = e.target.value.trim();
    if (q.startsWith('http') || q.startsWith('spotify:')) {
      // User pasted a Spotify URL into search! Switch to online tab automatically!
      if (turboTrackInput) turboTrackInput.value = q;
      if (turboClearInputBtn) turboClearInputBtn.style.display = 'block';
      switchPickerTab('online');
      return;
    }
    const lower = q.toLowerCase();
    if (!lower) {
      renderSongPickerItems(allSongs);
      return;
    }
    const filtered = allSongs.filter(s =>
      (s.title || '').toLowerCase().includes(lower) ||
      (s.artist || '').toLowerCase().includes(lower) ||
      (s.lyrics || '').toLowerCase().includes(lower)
    );
    renderSongPickerItems(filtered);
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

