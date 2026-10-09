import { TurboEngine } from '../turbo/turbo-engine.js';

// Common Spanish & Latin urban ad-libs, interjections, and exclamations
const INTERJECTIONS_SET = new Set([
  'brr', 'wuh', 'ey', 'eh', 'ay', 'oh', 'ah', 'ja', 'jaja', 'yah', 'uh',
  'shh', 'prr', 'rra', 'amén', 'dale', 'oye', 'mera', 'woh', 'uah', 'pla',
  'pew', 'okey', 'bye', 'epa', 'uf', 'chao', 'hola', 'adiós', 'puñeta',
  'carajo', 'dios', 'mami'
]);

let engine = null;
let probeSongs = [];
let annotatedCache = new Map(); // songIndex -> annotatedSong
let currentSongIndex = 0;
let showEnglishUnderneath = true;

// Flat list of all tokens in current song for modal next/previous stepping
let songTokensFlatList = [];
let currentModalTokenIndex = -1;

// DOM Elements
const topbarSongTitle = document.getElementById('topbarSongTitle');
const topbarSongArtist = document.getElementById('topbarSongArtist');
const songSelectorBtn = document.getElementById('songSelectorBtn');
const prevSongBtn = document.getElementById('prevSongBtn');
const nextSongBtn = document.getElementById('nextSongBtn');
const toggleEnglishBtn = document.getElementById('toggleEnglishBtn');

const loadingBox = document.getElementById('loadingBox');
const lyricsFlow = document.getElementById('lyricsFlow');

// Modals
const songPickerModal = document.getElementById('songPickerModal');
const closeSongPickerBtn = document.getElementById('closeSongPickerBtn');
const songPickerList = document.getElementById('songPickerList');
const songSearchInput = document.getElementById('songSearchInput');

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
// Initialisation
// ───────────────────────────────────────────────
async function init() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const paramSong = urlParams.get('song');

    // Load assets (read-only)
    engine = await TurboEngine.create('../turbo/turbo_assets.json');

    // Load 30 offline songs (read-only)
    const songsResp = await fetch('../turbo/probe_songs.json');
    probeSongs = await songsResp.json();

    if (paramSong) {
      const parsedIdx = parseInt(paramSong, 10);
      if (!isNaN(parsedIdx) && parsedIdx >= 0 && parsedIdx < probeSongs.length) {
        currentSongIndex = parsedIdx;
      } else {
        const foundIdx = probeSongs.findIndex(s =>
          s.title.toLowerCase().includes(paramSong.toLowerCase()) ||
          s.artist.toLowerCase().includes(paramSong.toLowerCase())
        );
        if (foundIdx >= 0) currentSongIndex = foundIdx;
      }
    }

    renderSongPickerItems(probeSongs);
    await selectSong(currentSongIndex);
  } catch (err) {
    console.error('Failed to init Lyrics View:', err);
    loadingBox.innerHTML = `
      <p style="color: #ff5252; font-weight: 600;">Failed to load lyrics: ${err.message}</p>
      <p style="font-size: 13px; margin-top: 8px;">Ensure files exist under app/turbo/.</p>
    `;
  }
}

// ───────────────────────────────────────────────
// Song Processing & Selection
// ───────────────────────────────────────────────
async function selectSong(index) {
  if (index < 0 || index >= probeSongs.length) return;
  currentSongIndex = index;

  const song = probeSongs[index];
  topbarSongTitle.textContent = song.title;
  topbarSongArtist.textContent = song.artist;

  prevSongBtn.disabled = (index === 0);
  nextSongBtn.disabled = (index === probeSongs.length - 1);

  // Sync URL query without reloading
  const newUrl = new URL(window.location.href);
  newUrl.searchParams.set('song', index);
  window.history.replaceState({}, '', newUrl.toString());

  lyricsFlow.style.display = 'none';
  loadingBox.style.display = 'block';

  let annotatedSong = annotatedCache.get(index);
  if (!annotatedSong) {
    const result = await engine.processPlaylist([song]);
    annotatedSong = result.annotatedSongs?.[0];
    if (annotatedSong) {
      postProcessAnnotatedSong(annotatedSong);
      annotatedCache.set(index, annotatedSong);
    }
  }

  loadingBox.style.display = 'none';
  lyricsFlow.style.display = 'flex';

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
  tokenModalWord.textContent = token.raw;
  if (token.isElision && token.word && token.word !== token.raw.toLowerCase()) {
    tokenModalElisionHint.textContent = `Contraction of: ${token.word}`;
    tokenModalElisionHint.style.display = 'inline-block';
  } else {
    tokenModalElisionHint.style.display = 'none';
  }

  // Badges
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

  // Meaning Callout
  modalMeaningCallout.className = 'meaning-card';
  if (token.type === 'entity') {
    modalMeaningCallout.classList.add('is-entity');
    modalMeaningLabel.textContent = 'Entity Sense';
  } else if (token.type === 'mwe') {
    modalMeaningCallout.classList.add('is-mwe');
    modalMeaningLabel.textContent = 'Idiomatic Sense';
  } else if (token.type === 'interjection') {
    modalMeaningCallout.classList.add('is-interjection');
    modalMeaningLabel.textContent = 'Ad-lib & Usage';
  } else {
    modalMeaningLabel.textContent = 'Sense Assignment';
  }

  modalMeaningPrimary.textContent = token.translation || token.word;
  modalMeaningContext.textContent = token.card?.meanings?.[0]?.context
    ? `Context: ${token.card.meanings[0].context}`
    : (token.pos ? `Part of speech: ${token.pos}` : '');

  // Entity Details
  if (token.type === 'entity' && token.card?.entity) {
    modalEntityBox.style.display = 'block';
    modalEntityTitle.textContent = token.card.entity.canonicalTitle || token.word;
    modalEntityDesc.textContent = token.card.entity.description || 'Cultural figure, urban artist, brand, or location referenced in Spanish music.';
  } else {
    modalEntityBox.style.display = 'none';
  }

  // Polysemous Breakdown Box
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

  // Context Quote
  modalContextQuoteText.innerHTML = highlightTokenInLine(token.lineText || '', token.raw);
  modalContextQuoteMeta.textContent = `Line ${(token.lineIndex || 0) + 1} · ${token.songTitle || ''} (${token.songArtist || ''})`;

  // Navigation button states
  tokenPrevBtn.disabled = (currentModalTokenIndex <= 0);
  tokenNextBtn.disabled = (currentModalTokenIndex >= songTokensFlatList.length - 1);

  tokenQuickViewModal.classList.add('open');
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
// Song Picker Modal
// ───────────────────────────────────────────────
function renderSongPickerItems(songs) {
  songPickerList.innerHTML = '';
  songs.forEach((s, idx) => {
    const item = document.createElement('div');
    item.className = `song-picker-item ${idx === currentSongIndex ? 'active' : ''}`;
    item.dataset.index = idx;
    item.innerHTML = `
      <div class="song-picker-item-left">
        <span class="song-picker-num">${idx + 1}</span>
        <div>
          <div class="song-picker-name">${s.title}</div>
          <div class="song-picker-artist">${s.artist}</div>
        </div>
      </div>
      <span class="song-picker-lines">${(s.lyrics || '').split('\n').length} lines</span>
    `;

    item.addEventListener('click', () => {
      closeSongPicker();
      selectSong(idx);
    });

    songPickerList.appendChild(item);
  });
}

function openSongPicker() {
  songSearchInput.value = '';
  renderSongPickerItems(probeSongs);
  songPickerModal.classList.add('open');
  setTimeout(() => songSearchInput.focus(), 50);
}

function closeSongPicker() {
  songPickerModal.classList.remove('open');
}

// ───────────────────────────────────────────────
// Event Listeners
// ───────────────────────────────────────────────
songSelectorBtn.addEventListener('click', openSongPicker);
closeSongPickerBtn.addEventListener('click', closeSongPicker);
songPickerModal.addEventListener('click', (e) => {
  if (e.target === songPickerModal) closeSongPicker();
});

prevSongBtn.addEventListener('click', () => {
  if (currentSongIndex > 0) selectSong(currentSongIndex - 1);
});

nextSongBtn.addEventListener('click', () => {
  if (currentSongIndex < probeSongs.length - 1) selectSong(currentSongIndex + 1);
});

toggleEnglishBtn.addEventListener('click', () => {
  showEnglishUnderneath = !showEnglishUnderneath;
  toggleEnglishBtn.classList.toggle('active', showEnglishUnderneath);
  document.querySelectorAll('.lyric-line-english').forEach(el => {
    el.classList.toggle('is-hidden', !showEnglishUnderneath);
  });
});

songSearchInput.addEventListener('input', (e) => {
  const q = e.target.value.toLowerCase().trim();
  if (!q) {
    renderSongPickerItems(probeSongs);
    return;
  }
  const filtered = probeSongs.filter(s =>
    s.title.toLowerCase().includes(q) ||
    s.artist.toLowerCase().includes(q) ||
    (s.lyrics || '').toLowerCase().includes(q)
  );
  renderSongPickerItems(filtered);
});

closeTokenModalBtn.addEventListener('click', closeTokenModal);
tokenQuickViewModal.addEventListener('click', (e) => {
  if (e.target === tokenQuickViewModal) closeTokenModal();
});

tokenPrevBtn.addEventListener('click', () => {
  if (currentModalTokenIndex > 0) {
    openTokenModal(songTokensFlatList[currentModalTokenIndex - 1]);
  }
});

tokenNextBtn.addEventListener('click', () => {
  if (currentModalTokenIndex < songTokensFlatList.length - 1) {
    openTokenModal(songTokensFlatList[currentModalTokenIndex + 1]);
  }
});

// Keyboard controls
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeTokenModal();
    closeSongPicker();
  } else if (tokenQuickViewModal.classList.contains('open')) {
    if (e.key === 'ArrowLeft' && currentModalTokenIndex > 0) {
      openTokenModal(songTokensFlatList[currentModalTokenIndex - 1]);
    } else if (e.key === 'ArrowRight' && currentModalTokenIndex < songTokensFlatList.length - 1) {
      openTokenModal(songTokensFlatList[currentModalTokenIndex + 1]);
    }
  }
});

// Boot
init();
