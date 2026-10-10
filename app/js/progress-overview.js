// A single local snapshot powers the coverage and card counts. No example
// corpus is downloaded, and completed loads cannot reopen a closed dialog.
export function summarizeProgress(cards, { getId, getState, getProgress }) {
    const result = { total: 0, known: 0, practice: 0, new: 0, due: 0, correct: 0, wrong: 0, coverage: 0 };
    const counted = new Set();
    let frequency = 0, covered = 0;
    for (const item of cards || []) {
        const id = getId(item);
        if (!id || counted.has(id)) continue;
        counted.add(id);
        const state = getState(item) || {};
        const record = getProgress(item) || {};
        const weight = Number(item.corpus_count);
        const freq = Number.isFinite(weight) && weight > 0 ? weight : 1;
        frequency += freq;
        result.total++;
        if (state.needsReview) {
            result.practice++;
            if (state.isDue || state.reviewReason === 'due') result.due++;
        } else if (state.seen) {
            result.known++;
        } else {
            result.new++;
        }
        // A scheduled review does not erase vocabulary knowledge. A more
        // recent mistake does, as decided by the shared progress engine.
        if (state.known && !['incorrect', 'partial'].includes(state.reviewReason)) covered += freq;
        result.correct += Math.max(0, Number(record.correct) || 0);
        result.wrong += Math.max(0, Number(record.wrong) || 0);
    }
    result.coverage = frequency ? Math.min(100, covered / frequency * 100) : 0;
    return result;
}

let request = 0;
let returnFocus = null;
let latestOptions = null;
let wiredModal = null;
const byId = id => document.getElementById(id);
const setText = (id, text) => { const el = byId(id); if (el) el.textContent = text; };
const count = value => value.toLocaleString();

export function closeProgressOverview() {
    request++;
    const modal = byId('totalStatsModal');
    modal?.classList.add('hidden');
    modal?.removeAttribute('aria-busy');
    if (returnFocus?.isConnected) returnFocus.focus();
    returnFocus = null;
}

function wireModal(modal) {
    if (wiredModal === modal) return;
    wiredModal = modal;
    byId('closeTotalStatsModal')?.addEventListener('click', closeProgressOverview);
    byId('progressRefreshBtn')?.addEventListener('click', () => openProgressOverview(latestOptions));
    modal.addEventListener('click', event => {
        if (event.target === modal) closeProgressOverview();
    });
    modal.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            event.preventDefault();
            event.stopPropagation();
            closeProgressOverview();
        }
        if (event.key !== 'Tab') return;
        const focusable = [...modal.querySelectorAll('button:not(:disabled), summary, [tabindex="0"]')]
            .filter(el => el.getClientRects().length && !el.closest('[hidden]'));
        const first = focusable[0], last = focusable.at(-1);
        if (!first) return;
        if (event.shiftKey && (document.activeElement === first || !modal.contains(document.activeElement))) {
            event.preventDefault(); last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault(); first.focus();
        }
    });
}

export async function openProgressOverview(options) {
    const modal = byId('totalStatsModal');
    if (!modal || !options) return;
    wireModal(modal);
    const opening = modal.classList.contains('hidden');
    if (opening) returnFocus = document.activeElement;
    latestOptions = options;
    const token = ++request;
    const current = () => token === request && !modal.classList.contains('hidden') && options.isCurrent();
    const content = byId('progressOverviewContent');
    const refresh = byId('progressRefreshBtn');
    content.hidden = true;
    setText('totalStatsLanguage', `${options.source} · ${options.mode}`);
    setText('progressOverviewStatus', 'Loading your progress…');
    setText('progressDataActionStatus', options.guest ? 'Guest mode: progress is not saved to a profile.' : '');
    byId('progressImportKnownBtn').disabled = !options.canImport;
    refresh.disabled = true;
    modal.setAttribute('aria-busy', 'true');
    modal.classList.remove('hidden');
    if (opening) byId('closeTotalStatsModal')?.focus();
    try {
        const cards = await options.loadVocabulary();
        if (!current()) {
            if (token === request && !options.isCurrent()) closeProgressOverview();
            return;
        }
        const data = summarizeProgress(cards, options);
        setText('progressOverviewStatus', data.total ? '' : 'This source has no study cards yet. Choose another source to get started.');
        setText('totalStatsCoverage', `${data.coverage.toFixed(1)}%`);
        setText('totalStatsCoverageLabel', options.coverageLabel);
        setText('progressCoverageDescription', data.total
            ? 'Based on your recorded knowledge in the current study vocabulary.'
            : 'Coverage will appear as you answer cards.');
        byId('progressCoverageRing').style.setProperty('--progress-coverage', `${data.coverage}%`);
        setText('totalStatsWords', `${count(data.total)} cards`);
        for (const [key, id] of [['known', 'progressKnownCount'], ['practice', 'progressPracticeCount'], ['new', 'progressNewCount']]) {
            setText(id, count(data[key]));
        }
        setText('progressPracticeDetail', data.due ? `${count(data.due)} scheduled for review` : 'Mistakes to revisit');
        const track = byId('progressWordTrack');
        track.setAttribute('aria-label', `${data.known} known, ${data.practice} practice, ${data.new} new cards`);
        for (const key of ['known', 'practice', 'new']) {
            track.querySelector(`.is-${key}`).style.width = `${data.total ? data[key] / data.total * 100 : 0}%`;
        }
        setText('progressScopeNote', 'Counts follow your current source and Smart Skip settings. Practice includes mistakes and scheduled reviews; due cards can still contribute to coverage. Level estimates are not counted as recorded knowledge.');
        setText('totalWordsCorrect', count(data.correct));
        setText('totalWordsIncorrect', count(data.wrong));
        setText('progressAttemptCount', `${count(data.correct + data.wrong)} answers`);
        content.hidden = false;
        refresh.textContent = 'Refresh progress';
    } catch (error) {
        if (!current()) {
            if (token === request && !options.isCurrent()) closeProgressOverview();
            return;
        }
        setText('progressOverviewStatus', 'Progress could not be loaded. Your saved progress is unchanged. Try again.');
        refresh.textContent = 'Try again';
        console.warn('Progress overview could not load:', error);
    } finally {
        if (token === request) {
            refresh.disabled = false;
            modal.removeAttribute('aria-busy');
        }
    }
}
