export function songTrackId(song) {
  const trackId = song?.spotifyId || song?.spotifyTrackId || song?.spotify_track_id;
  return typeof trackId === 'string' && /^[A-Za-z0-9]{22}$/.test(trackId) ? trackId : null;
}

// A song offers playback at all only with a real track and at least one timed
// line. Otherwise the reader shows no buttons and no explanation: there is
// nothing the reader could do about it.
export function songHasPlayback(song, lines) {
  return Boolean(songTrackId(song)) && Array.isArray(lines)
    && lines.some(line => line?.isSynced && Number.isFinite(line.timestamp_ms));
}

// Playback is only offered when a real track and an exact synced position exist.
export function linePlaybackTarget(song, line) {
  const trackId = songTrackId(song);
  if (!trackId) {
    return { available: false, reason: 'Load this song from a Spotify link to enable line playback.' };
  }
  const positionMs = line?.timestamp_ms;
  if (!line?.isSynced || typeof positionMs !== 'number' || !Number.isFinite(positionMs) || positionMs < 0) {
    return { available: false, reason: 'This line has no synced timing, so Spotify cannot start from it.' };
  }
  return { available: true, trackId, positionMs };
}

export async function restartLyricLine(target, playTrack) {
  if (!target.available) return false;
  // Repeated taps replay the line rather than toggling pause/resume.
  return playTrack(target.trackId, target.positionMs, { forceStart: true });
}
