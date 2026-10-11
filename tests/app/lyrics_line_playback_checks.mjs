import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const source = await readFile(new URL('../../app/lyrics-view/line-playback.js', import.meta.url), 'utf8');
const { linePlaybackTarget, restartLyricLine } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const song = { spotifyId: '1234567890123456789012' };
assert.deepEqual(linePlaybackTarget(song, { isSynced: true, timestamp_ms: 0 }), {
  available: true, trackId: song.spotifyId, positionMs: 0
});
for (const timestamp_ms of [null, undefined, -1, NaN, Infinity, '12000']) {
  assert.equal(linePlaybackTarget(song, { isSynced: true, timestamp_ms }).available, false);
}
assert.equal(linePlaybackTarget(song, { isSynced: false, timestamp_ms: 12000 }).available, false);
assert.equal(linePlaybackTarget({}, { isSynced: true, timestamp_ms: 12000 }).available, false);
const requests = [];
const play = async (...args) => { requests.push(args); return true; };
for (const timestamp_ms of [12000, 24000, 12000]) {
  await restartLyricLine(linePlaybackTarget(song, { isSynced: true, timestamp_ms }), play);
}
assert.deepEqual(requests, [12000, 24000, 12000].map(ms => [song.spotifyId, ms, { forceStart: true }]));
assert.equal(await restartLyricLine({ available: false }, play), false);
assert.equal(requests.length, 3);
assert.equal(await restartLyricLine({available: true, trackId: song.spotifyId, positionMs: 0}, async () => false), false);
console.log('Lyrics playback checks passed: timing validation, missing metadata, different lines, repeated restart, and playback failure.');
