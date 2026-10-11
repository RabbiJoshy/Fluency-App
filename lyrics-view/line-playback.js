// Playback is only offered when a real track and an exact synced position exist.
export function linePlaybackTarget(song, line) {
  const trackId = song?.spotifyId || song?.spotifyTrackId || song?.spotify_track_id;
  if (typeof trackId !== 'string' || !/^[A-Za-z0-9]{22}$/.test(trackId)) {
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
