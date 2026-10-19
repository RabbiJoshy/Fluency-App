// SETWISE-2: how long a study session runs, and when practice comes back.
//
// Learners choose a session as a length of time; the app builds it as a card
// count from a fixed assumed pace. Nothing about a learner's own speed is
// measured or stored (Josh, 2026-10-12): the pace is a rough guide only.

const SESSION_LENGTH_KEY = 'fluencySessionLengthV1';
const DEFAULT_SESSION_LENGTH = '5';
const SESSION_LENGTHS = [
    { id: '5', minutes: 5, label: '5 min', spoken: '5 minutes' },
    { id: '10', minutes: 10, label: '10 min', spoken: '10 minutes' },
    { id: 'all', minutes: null, label: 'All', spoken: 'no time limit' }
];
// Assumed seconds per card. A new card is read, flipped and explored; a
// practice card is usually recognised faster.
const ASSUMED_SECONDS_PER_CARD = { new: 15, practice: 10 };
// "No limit" still needs a number for the deck builder; no level or queue
// comes close to it.
const NO_LIMIT_CARDS = 10000;
const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;

let memoryLength = null;

function findLength(id) {
    return SESSION_LENGTHS.find(length => length.id === String(id)) || null;
}

function getSessionLength() {
    if (memoryLength) return memoryLength;
    try {
        const saved = globalThis.localStorage?.getItem(SESSION_LENGTH_KEY);
        if (findLength(saved)) return saved;
    } catch (error) { /* storage unavailable: use the default */ }
    return DEFAULT_SESSION_LENGTH;
}

function setSessionLength(id) {
    if (!findLength(id)) return getSessionLength();
    memoryLength = String(id);
    try { globalThis.localStorage?.setItem(SESSION_LENGTH_KEY, memoryLength); } catch (error) { /* per-tab only */ }
    globalThis.dispatchEvent?.(new CustomEvent('fluency:session-length', { detail: { id: memoryLength } }));
    return memoryLength;
}

function cycleSessionLength() {
    const index = SESSION_LENGTHS.findIndex(length => length.id === getSessionLength());
    return setSessionLength(SESSION_LENGTHS[(index + 1) % SESSION_LENGTHS.length].id);
}

function sessionLengthInfo(id = getSessionLength()) {
    return findLength(id) || findLength(DEFAULT_SESSION_LENGTH);
}

// Cards to build for a session of the chosen length.
// 5 min → 20 new or 30 practice; 10 min → 40 new or 60 practice.
function sessionCardLimit(kind = 'new', id = getSessionLength()) {
    const length = sessionLengthInfo(id);
    if (!length.minutes) return NO_LIMIT_CARDS;
    const seconds = ASSUMED_SECONDS_PER_CARD[kind] || ASSUMED_SECONDS_PER_CARD.new;
    return Math.max(1, Math.round(length.minutes * 60 / seconds));
}

function startOfDay(timestamp) {
    const date = new Date(timestamp);
    date.setHours(0, 0, 0, 0);
    return date.getTime();
}

// Rough, readable return times: a due time is only "last correct answer plus
// N days", so a clock time would look more precise than it is.
function formatReturnTime(timestamp, now = Date.now()) {
    const at = Number(timestamp) || 0;
    const delta = at - now;
    if (delta <= HOUR_MS) return 'within the hour';
    const dayGap = Math.round((startOfDay(at) - startOfDay(now)) / DAY_MS);
    if (dayGap === 0) {
        const hours = Math.max(1, Math.round(delta / HOUR_MS));
        return `in ${hours} hour${hours === 1 ? '' : 's'}`;
    }
    if (dayGap === 1) return 'tomorrow';
    if (dayGap < 7) return `on ${new Date(at).toLocaleDateString('en-GB', { weekday: 'long' })}`;
    if (dayGap < 14) return 'next week';
    if (dayGap < 60) return `in ${Math.round(dayGap / 7)} weeks`;
    const months = Math.max(2, Math.round(dayGap / 30));
    return `in ${months} months`;
}

// Group future review times into the next batch and the rest of the week.
function summariseUpcoming(times, now = Date.now()) {
    const future = (times || []).map(Number).filter(time => time > now).sort((a, b) => a - b);
    if (future.length === 0) return { total: 0, nextCount: 0, nextLabel: '', laterThisWeek: 0, firstAt: 0 };
    const nextLabel = formatReturnTime(future[0], now);
    const nextCount = future.filter(time => formatReturnTime(time, now) === nextLabel).length;
    const weekEnd = now + 7 * DAY_MS;
    const laterThisWeek = future.slice(nextCount).filter(time => time <= weekEnd).length;
    return { total: future.length, nextCount, nextLabel, laterThisWeek, firstAt: future[0] };
}

function wordCount(count) {
    return `${count.toLocaleString()} word${count === 1 ? '' : 's'}`;
}

// "12 words come back tomorrow, 30 more this week." Empty when nothing is scheduled.
function describeUpcoming(summary) {
    if (!summary?.nextCount) return '';
    const verb = summary.nextCount === 1 ? 'comes' : 'come';
    const more = summary.laterThisWeek > 0 ? `, ${summary.laterThisWeek.toLocaleString()} more this week` : '';
    return `${wordCount(summary.nextCount)} ${verb} back ${summary.nextLabel}${more}.`;
}

const api = {
    SESSION_LENGTHS, ASSUMED_SECONDS_PER_CARD, NO_LIMIT_CARDS,
    getSessionLength, setSessionLength, cycleSessionLength, sessionLengthInfo,
    sessionCardLimit, formatReturnTime, summariseUpcoming, describeUpcoming
};
globalThis.SessionPlan = api;

export {
    SESSION_LENGTHS, ASSUMED_SECONDS_PER_CARD, NO_LIMIT_CARDS,
    getSessionLength, setSessionLength, cycleSessionLength, sessionLengthInfo,
    sessionCardLimit, formatReturnTime, summariseUpcoming, describeUpcoming
};
