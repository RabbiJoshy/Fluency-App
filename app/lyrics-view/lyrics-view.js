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
let currentFilter = 'all';

// Flat list of all tokens in current song for modal next/previous stepping
let songTokensFlatList = [];
let currentModalTokenIndex = -1;

// DOM Elements
const topbarSongTitle = document.getElementById('topbarSongTitle');
const topbarSongArtist = document.getElementById('topbarSongArtist');
const songSelectorBtn = document.getElementById('songSelectorBtn');
const prevSongBtn = document.getElementById('prevSongBtn');
const nextSongBtn = document.getElementById('nextSongBtn');
const songsCountPill = document.getElementById('songsCountPill');

const mainSongTitle = document.getElementById('mainSongTitle');
const mainSongArtist = document.getElementById('mainSongArtist');
const loadingBox = document.getElementById('loadingBox');
const lyricsFlow = document.getElementById('lyricsFlow');

const entitiesCountBadge = document.getElementById('entitiesCountBadge');
const mwesCountBadge = document.getElementById('mwesCountBadge');
const interjectionsCountBadge = document.getElementById('interjectionsCountBadge');
const totalLinesText = document.getElementById('totalLinesText');
const totalTokensText = document.getElementById('totalTokensText');

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
    // Read initial song from query param if provided
    const urlParams = new URLSearchParams(window.location.search);
    const paramSong = urlParams.get('song');

    // 1. Load engine assets
    engine = await TurboEngine.create('../turbo/turbo_assets.json');

    // 2. Load offline songs playlist
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

    songsCountPill.textContent = `${probeSongs.length} songs`;
    renderSongPickerItems(probeSongs);

    // 3. Render current song
    await selectSong(currentSongIndex);
  } catch (err) {
    console.error('Failed to init Lyrics View:', err);
    loadingBox.innerHTML = `
      <p style="color: #f43f5e; font-weight: 600;">Failed to load lyrics data: ${err.message}</p>
      <p style="font-size: 13px; margin-top: 8px;">Check that assets exist under app/turbo/.</p>
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
  topbarSongTitle.textContent = `${index + 1}. ${song.title}`;
  topbarSongArtist.textContent = song.artist;
  mainSongTitle.textContent = song.title;
  mainSongArtist.textContent = `${song.artist} · Spanish`;

  prevSongBtn.disabled = (index === 0);
  nextSongBtn.disabled = (index === probeSongs.length - 1);

  // Sync URL query without reloading
  const newUrl = new URL(window.location.href);
  newUrl.searchParams.set('song', index);
  window.history.replaceState({}, '', newUrl.toString());

  // Show loading while analyzing if not cached
  lyricsFlow.style.display = 'none';
  loadingBox.style.display = 'block';

  let annotatedSong = annotatedCache.get(index);
  if (!annotatedSong) {
    // Process this song through TurboEngine
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
 * Enhances TurboEngine token classification:
 * - Detects interjections / ad-libs
 * - Detects entities
 * - Classifies elisions
 */
function postProcessAnnotatedSong(song) {
  for (const line of song.lines) {
    for (const token of line.tokens) {
      const lowerRaw = token.raw.toLowerCase().replace(/^[¿¡"'(]+|[.,;:!?"')]+$/g, '');
      const lowerNorm = (token.word || '').toLowerCase();

      // Check if this token is an interjection / ad-lib
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

// ───────────────────────────────────────────────
// Render Lyrics View
// ───────────────────────────────────────────────
function renderLyrics(song) {
  lyricsFlow.innerHTML = '';
  songTokensFlatList = [];

  let countEntities = 0;
  let countMwes = 0;
  let countInterjections = 0;
  let countTokens = 0;

  song.lines.forEach((line, lineIdx) => {
    const lineItem = document.createElement('div');
    lineItem.className = 'lyric-line-item';
    lineItem.dataset.lineIndex = lineIdx;

    // Line number or audio timestamp
    const lineNum = document.createElement('span');
    lineNum.className = 'lyric-line-number';
    if (line.isSynced && line.timestamp_ms != null) {
      const totalSec = Math.floor(line.timestamp_ms / 1000);
      const m = Math.floor(totalSec / 60);
      const s = totalSec % 60;
      lineNum.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
      lineNum.title = `Synced line [${line.timestamp_ms}ms]`;
    } else {
      lineNum.textContent = (lineIdx + 1 < 10 ? '0' : '') + (lineIdx + 1);
    }
    lineItem.appendChild(lineNum);

    // Line text container
    const lineText = document.createElement('div');
    lineText.className = 'lyric-line-text';

    // Auto-breakdown chips for this line
    const autoBreakdownList = [];

    line.tokens.forEach((token, tokenIdx) => {
      countTokens++;
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

      // Styling based on classification
      if (token.type === 'entity') {
        span.classList.add('token-entity');
        countEntities++;
        span.title = `🌸 Entity: ${token.word} (${token.translation || 'Cultural referent'})`;
        autoBreakdownList.push({
          type: 'entity',
          label: `🌸 ${token.raw}`,
          sub: token.translation,
          token
        });
      } else if (token.type === 'mwe') {
        span.classList.add('token-mwe');
        countMwes++;
        span.title = `🟣 Idiom: ${token.word} (${token.translation})`;
        autoBreakdownList.push({
          type: 'mwe',
          label: `🟣 ${token.raw}`,
          sub: token.translation,
          token
        });
      } else if (token.type === 'interjection') {
        span.classList.add('token-interjection');
        countInterjections++;
        span.title = `⚡ Ad-lib / Interjection: ${token.translation || token.raw}`;
        autoBreakdownList.push({
          type: 'interjection',
          label: `⚡ ${token.raw}`,
          sub: token.translation,
          token
        });
      } else {
        span.classList.add('token-word');
        if (token.isElision) {
          span.classList.add('token-elision');
          span.title = `Elision: ${token.raw} → ${token.word} (${token.translation})`;
          autoBreakdownList.push({
            type: 'elision',
            label: `→ ${token.raw} (${token.word})`,
            sub: token.translation,
            token
          });
        } else {
          span.title = `${token.word}: ${token.translation || 'Word'}`;
        }
      }

      // Filter dimming
      if (currentFilter !== 'all' && currentFilter !== token.type) {
        span.classList.add('is-dimmed');
      }

      span.addEventListener('click', (e) => {
        e.stopPropagation();
        openTokenModal(token);
      });

      lineText.appendChild(span);
    });

    lineItem.appendChild(lineText);

    // If this line has auto items (entities, idioms, interjections, elisions), show breakdown row
    if (autoBreakdownList.length > 0) {
      const autoRow = document.createElement('div');
      autoRow.className = 'line-auto-breakdown';

      autoBreakdownList.forEach(item => {
        const chip = document.createElement('span');
        chip.className = `auto-chip auto-chip-${item.type}`;
        chip.innerHTML = `<strong>${item.label}</strong> ${item.sub ? `<small style="opacity:0.8;">· ${item.sub}</small>` : ''}`;
        chip.addEventListener('click', (e) => {
          e.stopPropagation();
          openTokenModal(item.token);
        });
        autoRow.appendChild(chip);
      });

      lineItem.appendChild(autoRow);
    }

    lyricsFlow.appendChild(lineItem);
  });

  // Update metrics badges
  entitiesCountBadge.textContent = countEntities;
  mwesCountBadge.textContent = countMwes;
  interjectionsCountBadge.textContent = countInterjections;
  totalLinesText.textContent = `${song.lines.length} lines`;
  totalTokensText.textContent = `${countTokens} tokens`;
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
    tokenModalElisionHint.textContent = `Contraction → ${token.word}`;
    tokenModalElisionHint.style.display = 'inline-block';
  } else {
    tokenModalElisionHint.style.display = 'none';
  }

  // Badges
  tokenModalBadges.innerHTML = '';
  const typeBadge = document.createElement('span');
  typeBadge.className = 'token-type-badge';

  if (token.type === 'entity') {
    typeBadge.classList.add('badge-entity');
    const entType = token.card?.entity?.entityType || 'Cultural Entity';
    typeBadge.textContent = `🌸 ${entType}`;
  } else if (token.type === 'mwe') {
    typeBadge.classList.add('badge-mwe');
    typeBadge.textContent = `🟣 Idiom / MWE`;
  } else if (token.type === 'interjection') {
    typeBadge.classList.add('badge-interjection');
    typeBadge.textContent = `⚡ Interjection / Ad-lib`;
  } else {
    typeBadge.classList.add('badge-word');
    typeBadge.textContent = `🔷 ${token.pos || 'Vocabulary'}`;
  }
  tokenModalBadges.appendChild(typeBadge);

  if (token.rank) {
    const rankBadge = document.createElement('span');
    rankBadge.className = 'token-type-badge badge-rank';
    rankBadge.textContent = `#${token.rank} in frequency`;
    tokenModalBadges.appendChild(rankBadge);
  }

  // Meaning Callout Styling & Text
  modalMeaningCallout.className = 'meaning-callout';
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

  // Entity Details Box
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
  const highlighted = lineText.replace(regex, `<span style="color: var(--accent-cyan); font-weight: 700; text-decoration: underline;">$1</span>`);
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
        <div class="song-picker-details">
          <div class="song-picker-name">${s.title}</div>
          <div class="song-picker-artist">${s.artist}</div>
        </div>
      </div>
      <span class="song-picker-lines-badge">${(s.lyrics || '').split('\n').length} lines</span>
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

// Keyboard controls (Esc to close, Arrow keys to navigate)
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

// Filter pill buttons
document.querySelectorAll('.filter-pill[data-filter]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-pill[data-filter]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;

    // Apply dimming to tokens
    document.querySelectorAll('.lyric-token').forEach(tokenEl => {
      const type = tokenEl.dataset.type;
      if (currentFilter === 'all' || currentFilter === type) {
        tokenEl.classList.remove('is-dimmed');
      } else {
        tokenEl.classList.add('is-dimmed');
      }
    });
  });
});

// Boot
init();
