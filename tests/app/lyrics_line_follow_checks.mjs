import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const load = async name => {
  const source = await readFile(new URL(`../../app/lyrics-view/${name}`, import.meta.url), 'utf8');
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
};
const follow = await load('line-follow.js');
const playback = await load('line-playback.js');
const { activeLineIndex, lineProgress, tokenFills, playbackPositionMs, timingMatches, adjacentLineStart, repeatEndMs, lineWindowMs } = follow;

const line = (start, end, text = 'una noche mas') => ({ timestamp_ms: start, end_timestamp_ms: end, isSynced: true, text });
const lines = [line(1000, 4000), line(4000, 8000), line(8000, 12000)];

// Active line: before the first, on each boundary, inside, and after the last.
assert.equal(activeLineIndex(lines, 0), -1);
assert.equal(activeLineIndex(lines, 999), -1);
assert.equal(activeLineIndex(lines, 1000), 0);
assert.equal(activeLineIndex(lines, 3999), 0);
assert.equal(activeLineIndex(lines, 4000), 1);
assert.equal(activeLineIndex(lines, 11999), 2);
assert.equal(activeLineIndex(lines, 600000), 2);
assert.equal(activeLineIndex([], 5000), -1);
assert.equal(activeLineIndex(lines, NaN), -1);
// Untimed lines: no timing, no active line.
assert.equal(activeLineIndex([{ isSynced: false, timestamp_ms: null }], 5000), -1);
// A single untimed line inside a timed song does not break the search.
const mixed = [line(1000, 4000), { isSynced: false, timestamp_ms: null, text: 'x' }, line(8000, 12000)];
assert.equal(activeLineIndex(mixed, 9000), 2);
assert.equal(activeLineIndex(mixed, 2000), 0);

// Progress: across the gap, clamped, and capped for a long instrumental gap.
assert.equal(lineProgress(line(0, 4000), 0), 0);
assert.equal(lineProgress(line(0, 4000), 2000), 0.5);
assert.equal(lineProgress(line(0, 4000), 9000), 1);
assert.equal(lineProgress(line(5000, 9000), 1000), 0);
const longGap = line(0, 60000, 'una noche mas y copas de mas'); // 28 chars
const finishedAt = 28 * 85;
assert.ok(lineProgress(longGap, 6000) === 1, 'a line before a 60 s break finishes within the cap');
assert.ok(lineProgress(longGap, 1500) < 1 && lineProgress(longGap, finishedAt) >= 0.99);
assert.equal(lineProgress({ isSynced: false }, 5000), 0);

// Tokens: monotonic, endpoints, and weighted by length.
const texts = ['yo', 'quiero', 'bailar'];
assert.deepEqual(tokenFills(texts, 0), [0, 0, 0]);
assert.deepEqual(tokenFills(texts, 1), [1, 1, 1]);
const half = tokenFills(texts, 0.5);
for (let i = 1; i < half.length; i++) assert.ok(half[i] <= half[i - 1], 'earlier words fill first');
assert.equal(half[0], 1);
assert.ok(half[2] === 0, 'last word has not begun at half way');
const total = 2 + 6 + 6;
assert.ok(Math.abs(tokenFills(texts, 2 / total)[0] - 1) < 1e-9, 'first word is done at its character share');
assert.deepEqual(tokenFills([], 0.5), []);
assert.equal(tokenFills(['', 'a'], 1).length, 2);

// Position: interpolates while playing, holds while paused, never passes the end.
const state = { positionMs: 10000, durationMs: 200000, paused: false, at: 5000 };
assert.equal(playbackPositionMs(state, 5000), 10000);
assert.equal(playbackPositionMs(state, 6500), 11500);
assert.equal(playbackPositionMs({ ...state, paused: true }, 9000), 10000);
assert.equal(playbackPositionMs({ ...state, positionMs: 199000 }, 9000), 200000);
assert.equal(playbackPositionMs({ ...state, at: 9000 }, 5000), 10000, 'a clock earlier than the report does not run backwards');
assert.equal(playbackPositionMs(null, 0), null);

// Same recording or not.
assert.equal(timingMatches(189000, 189400), true);
assert.equal(timingMatches(189000, 198000), false);
assert.equal(timingMatches(undefined, 198000), null);
assert.equal(timingMatches(189000, undefined), null);

// Previous / next line, as a player does it.
assert.equal(adjacentLineStart(lines, 5000, 1), 8000, 'next from inside line 2');
assert.equal(adjacentLineStart(lines, 9000, 1), null, 'no line after the last');
assert.equal(adjacentLineStart(lines, 0, 1), 1000, 'next before the first line is the first');
assert.equal(adjacentLineStart(lines, 6500, -1), 4000, 'previous restarts a line that is well under way');
assert.equal(adjacentLineStart(lines, 4400, -1), 1000, 'previous goes back a line just after it began');
assert.equal(adjacentLineStart(lines, 1200, -1), 1000, 'previous on the first line restarts it');
assert.equal(adjacentLineStart(lines, 0, -1), 1000);
assert.equal(adjacentLineStart([], 0, 1), null);
// Looping a line jumps back at the end of its window, not after a long gap.
assert.equal(repeatEndMs(line(4000, 8000)), 8000);
assert.equal(repeatEndMs(line(0, 60000, 'una noche mas')), lineWindowMs(line(0, 60000, 'una noche mas')));
assert.ok(repeatEndMs(line(0, 60000, 'una noche mas')) <= 6000);
assert.equal(repeatEndMs({ isSynced: false }), null);

// Whether a song offers playback at all.
const track = '1234567890123456789012';
assert.equal(playback.songHasPlayback({ spotifyId: track }, lines), true);
assert.equal(playback.songHasPlayback({}, lines), false, 'no track: no buttons');
assert.equal(playback.songHasPlayback({ spotifyId: track }, [{ isSynced: false, timestamp_ms: null }]), false, 'no timing: no buttons');
assert.equal(playback.songHasPlayback({ spotifyId: 'short' }, lines), false);
assert.equal(playback.songTrackId({ spotifyTrackId: track }), track);
assert.equal(playback.songTrackId({ spotifyId: 'short' }), null);

console.log('Lyrics follow checks passed: active line, progress and cap, word fills, position, duration guard, playback gate.');
