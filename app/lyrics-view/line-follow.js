// Follow Spotify playback through a song's lines. Pure functions; the reader
// owns the DOM. Times come from LRCLIB at line level only, so word timing here
// is an estimate: each word's share of its line is its share of the characters.

// An instrumental gap after a line must not stretch its words across the gap.
export const MAX_LINE_WINDOW_MS = 6000;
// Timing from a different cut drifts by seconds; below this it is the same recording.
export const DURATION_TOLERANCE_MS = 3000;

// Position now: the last reported position plus the time since the report,
// unless the player is paused. The SDK reports only on change, never per tick.
export function playbackPositionMs(state, nowMs) {
  if (!state || !Number.isFinite(state.positionMs)) return null;
  const elapsed = state.paused ? 0 : Math.max(0, nowMs - state.at);
  const position = state.positionMs + elapsed;
  return Number.isFinite(state.durationMs) && state.durationMs > 0
    ? Math.min(position, state.durationMs)
    : position;
}

// The last synced line that has started, or -1 before the first line.
export function activeLineIndex(lines, positionMs) {
  if (!Array.isArray(lines) || !Number.isFinite(positionMs)) return -1;
  let low = 0;
  let high = lines.length - 1;
  let found = -1;
  while (low <= high) {
    const mid = (low + high) >> 1;
    const start = lines[mid]?.timestamp_ms;
    if (lines[mid]?.isSynced && Number.isFinite(start)) {
      if (start <= positionMs) { found = mid; low = mid + 1; } else { high = mid - 1; }
    } else {
      // An untimed line breaks the ordering; fall back to a plain scan.
      found = -1;
      for (let i = 0; i < lines.length; i++) {
        const t = lines[i]?.timestamp_ms;
        if (lines[i]?.isSynced && Number.isFinite(t) && t <= positionMs) found = i;
      }
      return found;
    }
  }
  return found;
}

// How far through the line the singer is, 0..1. The window is the gap to the
// next line, or, when that gap is long (an instrumental break), an estimate
// from the line's length, never more than MAX_LINE_WINDOW_MS.
export function lineProgress(line, positionMs) {
  const start = line?.timestamp_ms;
  if (!Number.isFinite(start) || !Number.isFinite(positionMs)) return 0;
  const end = Number.isFinite(line.end_timestamp_ms) ? line.end_timestamp_ms : start + 4000;
  const gap = Math.max(1, end - start);
  const chars = String(line.text || '').length;
  const estimate = Math.min(MAX_LINE_WINDOW_MS, Math.max(1500, chars * 85));
  const window = gap <= MAX_LINE_WINDOW_MS ? gap : estimate;
  return Math.min(1, Math.max(0, (positionMs - start) / window));
}

// Per word, 0..1: how much of it has been sung, weighting by character count.
export function tokenFills(tokenTexts, progress) {
  const weights = tokenTexts.map(text => Math.max(1, String(text || '').trim().length));
  const total = weights.reduce((sum, w) => sum + w, 0);
  const p = Math.min(1, Math.max(0, progress));
  let before = 0;
  return weights.map(weight => {
    const start = before / total;
    before += weight;
    const end = before / total;
    return Math.min(1, Math.max(0, (p - start) / (end - start)));
  });
}

// False when Spotify's cut is a different length from the one the lines were
// timed against. `null` means there is nothing to compare.
export function timingMatches(bakedDurationMs, spotifyDurationMs) {
  if (!Number.isFinite(bakedDurationMs) || !Number.isFinite(spotifyDurationMs)) return null;
  return Math.abs(bakedDurationMs - spotifyDurationMs) <= DURATION_TOLERANCE_MS;
}
