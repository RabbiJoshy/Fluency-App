// Review home: the sheet behind the setup screen's "Review home" button.
//
// It composes; it does not compute. Every figure here comes from a function that
// already owned it — getGlobalDueReviewSummary() for the queue, the level totals
// that renderRangeSelector() publishes on window.__reviewHomeContext, and
// getCurrentCoverageSnapshot() for progress. Adding a second copy of the review
// maths here is exactly how the two surfaces would start disagreeing.
//
// Categories with a zero count still render, stating the zero. Absence is
// declared, never inferred — a hidden row reads as "no such thing", not "none
// right now".

import './state.js?v=20260921x';

const TIERS = [
    {
        tier: 'never_right',
        key: 'neverRight',
        title: 'Never got right',
        blurb: 'Cards you have answered, but never correctly.'
    },
    {
        tier: 'critical',
        key: 'critical',
        title: 'Recent mistakes',
        blurb: 'Missed lately, or long past the date they were due.'
    },
    {
        tier: 'due',
        key: 'due',
        title: 'Due today',
        blurb: 'The spaced-repetition schedule says these are ready.'
    }
];

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function contextSnapshot() {
    return globalThis.__reviewHomeContext || null;
}

function tierRow({ tier, title, blurb, count }) {
    const disabled = count > 0 ? '' : 'disabled';
    return `<button type="button" class="review-home-row" data-tier="${tier}" ${disabled}>
            <span class="review-home-row-copy">
                <strong>${escapeHtml(title)}</strong>
                <small>${escapeHtml(blurb)}</small>
            </span>
            <span class="review-home-row-count">${count}</span>
        </button>`;
}

function renderReviewHome() {
    const body = document.getElementById('reviewHomeBody');
    if (!body) return;

    const context = contextSnapshot();
    const language = context?.language || globalThis.selectedLanguage;
    const summary = globalThis.getGlobalDueReviewSummary?.(language) || null;
    const total = Number(summary?.total) || 0;

    const tiersHTML = TIERS
        .map(entry => tierRow({ ...entry, count: Number(summary?.[entry.key]) || 0 }))
        .join('');

    const levelReview = Number(context?.levelReviewCount) || 0;
    const levelLabel = escapeHtml(context?.levelLabel || 'This level');
    const levelBlurb = context
        ? `${Number(context.levelDueCount) || 0} due · ${Number(context.levelUnfinishedCount) || 0} unfinished`
        : 'Pick a level to see its review queue.';
    const levelHTML = `<button type="button" class="review-home-row" data-scope="level" ${levelReview > 0 ? '' : 'disabled'}>
            <span class="review-home-row-copy">
                <strong>${levelLabel}</strong>
                <small>${escapeHtml(levelBlurb)}</small>
            </span>
            <span class="review-home-row-count">${levelReview}</span>
        </button>`;

    // Same numbers as the all-time progress sheet, read rather than recomputed.
    const snapshot = globalThis.getCurrentCoverageSnapshot?.() || null;
    const coveragePct = Number(snapshot?.percentage) || 0;
    const covered = Number(snapshot?.coveredCount) || 0;
    const totalWords = Number(snapshot?.totalCount) || 0;
    const progressHTML = `<div class="review-home-progress">
            <div class="review-home-progress-head">
                <strong>${coveragePct.toFixed(1)}%</strong>
                <span>${covered.toLocaleString()} of ${totalWords.toLocaleString()} cards seen</span>
            </div>
            <div class="review-home-progress-track"><i id="reviewHomeProgressFill"></i></div>
            <button type="button" class="review-home-link" data-action="total-stats">All-time progress ›</button>
        </div>`;

    // How reviews are timed decides every count below it, so it states itself
    // first rather than as a footnote under the numbers it explains.
    const srsOn = globalThis.spacedRepetitionEnabled !== false;
    const srsHTML = `<div class="review-home-srs">
            <span class="review-home-srs-copy">
                <strong>Spaced repetition is ${srsOn ? 'on' : 'off'}</strong>
                <small>${srsOn
                    ? 'Words come back just before you would forget them.'
                    : 'Nothing returns on a schedule — only words you got wrong.'}</small>
            </span>
            <button type="button" class="review-home-srs-info" data-action="srs-info" aria-label="How reviews are timed">
                <span aria-hidden="true">?</span>
            </button>
        </div>`;

    body.innerHTML = `
        <p class="review-home-lead">${total > 0
            ? `${total} card${total === 1 ? '' : 's'} waiting across this language.`
            : 'Nothing is waiting for review right now.'}</p>
        ${srsHTML}
        <section class="review-home-section" data-section="queue">
            <h4>By urgency</h4>
            ${tiersHTML}
        </section>
        <section class="review-home-section" data-section="level">
            <h4>By level</h4>
            ${levelHTML}
        </section>
        <section class="review-home-section" data-section="progress">
            <h4>Progress</h4>
            ${progressHTML}
        </section>`;

    // Same double-rAF fill the setup screen's coverage bar uses, so the two bars
    // animate identically.
    const fill = document.getElementById('reviewHomeProgressFill');
    if (fill) {
        fill.style.transition = 'none';
        fill.style.width = '0%';
        requestAnimationFrame(() => requestAnimationFrame(() => {
            fill.style.transition = 'width 1s ease-out';
            fill.style.width = `${Math.min(100, Math.max(0, coveragePct))}%`;
        }));
    }
}

function openSpacedRepetitionInfo() {
    document.getElementById('spacedRepetitionInfoModal')?.classList.remove('hidden');
}

function closeSpacedRepetitionInfo() {
    document.getElementById('spacedRepetitionInfoModal')?.classList.add('hidden');
}

function openReviewHome({ section } = {}) {
    renderReviewHome();
    document.getElementById('reviewHomeModal')?.classList.remove('hidden');
    if (section) {
        document.querySelector(`.review-home-section[data-section="${section}"]`)
            ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function closeReviewHome() {
    document.getElementById('reviewHomeModal')?.classList.add('hidden');
}

async function startTier(tier) {
    const context = contextSnapshot();
    const summary = globalThis.getGlobalDueReviewSummary?.(context?.language || globalThis.selectedLanguage) || null;
    const key = TIERS.find(entry => entry.tier === tier)?.key;
    const available = Number(summary?.[key]) || 0;
    if (available <= 0) return;
    closeReviewHome();
    await globalThis.startDailyReview?.({ limit: Math.min(available, 100), urgencyTier: tier });
}

async function startLevelReview() {
    const context = contextSnapshot();
    if (!context?.range || !(context.levelReviewCount > 0)) return;
    closeReviewHome();
    globalThis.showAppLoading?.('Loading review', 'Collecting the cards that need another look…');
    try {
        await globalThis.loadLevelReviewSet?.(context.range, {
            rankBasis: context.rankBasis,
            levelNumber: context.levelNumber
        });
    } finally {
        globalThis.hideAppLoading?.();
    }
}

function initReviewHome() {
    document.getElementById('closeReviewHomeModal')?.addEventListener('click', closeReviewHome);
    document.getElementById('reviewHomeModal')?.addEventListener('click', event => {
        if (event.target?.id === 'reviewHomeModal') closeReviewHome();
    });
    document.getElementById('reviewHomeBody')?.addEventListener('click', async event => {
        const row = event.target.closest('.review-home-row');
        if (row && !row.disabled) {
            if (row.dataset.scope === 'level') await startLevelReview();
            else if (row.dataset.tier) await startTier(row.dataset.tier);
            return;
        }
        const link = event.target.closest('.review-home-link');
        if (!link) return;
        if (link.dataset.action === 'total-stats') {
            closeReviewHome();
            globalThis.showTotalStatsModal?.();
        }
    });
    document.getElementById('reviewHomeBody')?.addEventListener('click', event => {
        // The explainer stacks over this sheet rather than replacing it: it
        // answers a question about what is on screen, so the screen stays.
        if (event.target.closest('[data-action="srs-info"]')) openSpacedRepetitionInfo();
    });
    document.getElementById('spacedRepetitionSettingsBtn')?.addEventListener('click', () => {
        closeSpacedRepetitionInfo();
        closeReviewHome();
        globalThis.showSettingsModalWithTab?.('review', { singleTab: true });
    });
    document.getElementById('closeSpacedRepetitionInfoModal')
        ?.addEventListener('click', closeSpacedRepetitionInfo);
    document.getElementById('spacedRepetitionInfoModal')?.addEventListener('click', event => {
        if (event.target?.id === 'spacedRepetitionInfoModal') closeSpacedRepetitionInfo();
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            // Topmost first, so one press does not close both sheets.
            const info = document.getElementById('spacedRepetitionInfoModal');
            if (info && !info.classList.contains('hidden')) closeSpacedRepetitionInfo();
            else closeReviewHome();
        }
    });
}

// Self-initialising, the same shape extras.js uses, so no caller has to
// remember to wire it.
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReviewHome);
} else {
    initReviewHome();
}

globalThis.openReviewHome = openReviewHome;
globalThis.openSpacedRepetitionInfo = openSpacedRepetitionInfo;
globalThis.closeReviewHome = closeReviewHome;
globalThis.initReviewHome = initReviewHome;

export { initReviewHome, openReviewHome, closeReviewHome };
