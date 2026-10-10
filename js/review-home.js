// Practice: an explanation and browsable view of the language-wide queue.
// The queue and its ordering still belong to progress.js. Opening a group
// only explains the queue; it must never start a study session.

import './state.js?v=699d12c6';

const LIST_PAGE_SIZE = 50;
const DAY_MS = 24 * 60 * 60 * 1000;

const GROUPS = [
    { tier: 'never_right', key: 'neverRight', title: 'Never correct',
        blurb: 'Words you have answered, but have not got right yet.' },
    { tier: 'critical', key: 'critical', title: 'Needs attention',
        blurb: 'Recent mistakes and words that are long overdue another review.' },
    { tier: 'due', key: 'due', title: 'Due now',
        blurb: 'Scheduled words whose practice time has arrived.' }
];

let activeGroup = null;
let visibleWords = LIST_PAGE_SIZE;

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[char]));
}

function contextSnapshot() {
    return globalThis.__reviewHomeContext || null;
}

function queueSummary() {
    const context = contextSnapshot();
    const language = context?.language || globalThis.selectedLanguage;
    return globalThis.getGlobalDueReviewSummary?.(language) || {
        total: 0, neverRight: [], critical: [], due: [], all: []
    };
}

function cardsFor(summary, group) {
    const cards = summary?.[group?.key];
    return Array.isArray(cards) ? cards : [];
}

function relativePast(timestamp, now = Date.now()) {
    const elapsed = Math.max(0, now - Number(timestamp || 0));
    if (elapsed < 60 * 1000) return 'just now';
    if (elapsed < 60 * 60 * 1000) {
        const minutes = Math.max(1, Math.floor(elapsed / (60 * 1000)));
        return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    }
    if (elapsed < DAY_MS) {
        const hours = Math.max(1, Math.floor(elapsed / (60 * 60 * 1000)));
        return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    }
    const days = Math.max(1, Math.floor(elapsed / DAY_MS));
    if (days < 14) return `${days} day${days === 1 ? '' : 's'} ago`;
    if (days < 60) {
        const weeks = Math.floor(days / 7);
        return `${weeks} week${weeks === 1 ? '' : 's'} ago`;
    }
    if (days < 730) {
        const months = Math.floor(days / 30);
        return `${months} month${months === 1 ? '' : 's'} ago`;
    }
    const years = Math.floor(days / 365);
    return `${years} year${years === 1 ? '' : 's'} ago`;
}

function latenessLabel(overdueMs) {
    const elapsed = Math.max(0, Number(overdueMs) || 0);
    if (elapsed < DAY_MS) return 'due today';
    const days = Math.max(1, Math.floor(elapsed / DAY_MS));
    if (days < 14) return `${days} day${days === 1 ? '' : 's'} late`;
    if (days < 60) {
        const weeks = Math.floor(days / 7);
        return `${weeks} week${weeks === 1 ? '' : 's'} late`;
    }
    const months = Math.floor(days / 30);
    return `${months} month${months === 1 ? '' : 's'} late`;
}

function cardStatus(card) {
    const answeredAt = Number(card?.lastAnsweredAt) || 0;
    const outcome = card?.lastOutcome;
    const answer = answeredAt && outcome
        ? `${outcome === 'wrong' ? 'Wrong' : 'Right'} ${relativePast(answeredAt)}`
        : '';
    const late = card?.reviewReason === 'due' ? latenessLabel(card.overdueMs) : '';
    return [answer, late].filter(Boolean).join(' · ') || 'Ready to practise';
}

function groupRow(group, count) {
    return `<button type="button" class="review-home-row" data-action="open-group"
            data-tier="${group.tier}" ${count > 0 ? '' : 'disabled'}>
            <span class="review-home-row-copy">
                <strong>${escapeHtml(group.title)}</strong>
                <small>${escapeHtml(group.blurb)}</small>
            </span>
            <span class="review-home-row-tail">
                <span class="review-home-row-count">${count.toLocaleString()}</span>
                <span class="review-home-row-chevron" aria-hidden="true">›</span>
            </span>
        </button>`;
}

function srsHTML() {
    const srsOn = globalThis.spacedRepetitionEnabled !== false;
    return `<div class="review-home-srs">
            <span class="review-home-srs-copy">
                <strong>Spaced repetition is ${srsOn ? 'on' : 'off'}</strong>
                <small>${srsOn
                    ? 'Known words return when they are likely to need practice.'
                    : 'Only words you get wrong stay in Practice.'}</small>
            </span>
            <button type="button" class="review-home-srs-info" data-action="srs-info" aria-label="How practice is scheduled">
                <span aria-hidden="true">?</span>
            </button>
        </div>`;
}

function renderOverview(body, summary) {
    const groupsHTML = GROUPS
        .map(group => groupRow(group, cardsFor(summary, group).length))
        .join('');

    // Quick practice lives on the setup screen; this sheet explains the queue.
    body.innerHTML = `
        ${srsHTML()}
        <section class="review-home-section" data-section="queue">
            <h4>Practice order</h4>
            ${groupsHTML}
        </section>`;
}

function renderGroupDetail(body, summary, group) {
    const cards = cardsFor(summary, group);
    const shown = cards.slice(0, visibleWords);
    const rows = shown.map(card => `<li class="review-home-word-row">
            <strong>${escapeHtml(card.word)}</strong>
            <span>${escapeHtml(cardStatus(card))}</span>
        </li>`).join('');
    const remaining = Math.max(0, cards.length - shown.length);

    body.innerHTML = `
        <div class="review-home-detail-head">
            <button type="button" class="review-home-back" data-action="back-to-groups">‹ Back</button>
            <span>${cards.length.toLocaleString()} card${cards.length === 1 ? '' : 's'}</span>
        </div>
        <div class="review-home-detail-title">
            <h4>${escapeHtml(group.title)}</h4>
            <p>${escapeHtml(group.blurb)}</p>
        </div>
        <ol class="review-home-word-list">${rows}</ol>
        ${remaining > 0 ? `<button type="button" class="secondary-btn review-home-more" data-action="show-more">
            Show ${Math.min(LIST_PAGE_SIZE, remaining)} more
        </button>` : ''}`;
}

function renderReviewHome() {
    const body = document.getElementById('reviewHomeBody');
    if (!body) return;
    const summary = queueSummary();
    const group = GROUPS.find(entry => entry.tier === activeGroup);
    if (group) renderGroupDetail(body, summary, group);
    else renderOverview(body, summary);
}

// From Settings it sits over the settings page, and its own link to the
// setting would only lead back to where you already are.
function openSpacedRepetitionInfo({ fromSettings = false } = {}) {
    const modal = document.getElementById('spacedRepetitionInfoModal');
    if (!modal) return;
    modal.classList.toggle('is-over-settings', fromSettings);
    const settingsLink = document.getElementById('spacedRepetitionSettingsBtn');
    if (settingsLink) settingsLink.hidden = fromSettings;
    modal.classList.remove('hidden');
}

function closeSpacedRepetitionInfo() {
    document.getElementById('spacedRepetitionInfoModal')?.classList.add('hidden');
}

function openReviewHome() {
    activeGroup = null;
    visibleWords = LIST_PAGE_SIZE;
    renderReviewHome();
    document.getElementById('reviewHomeModal')?.classList.remove('hidden');
}

function closeReviewHome() {
    document.getElementById('reviewHomeModal')?.classList.add('hidden');
    activeGroup = null;
}

function initReviewHome() {
    document.getElementById('closeReviewHomeModal')?.addEventListener('click', closeReviewHome);
    document.getElementById('reviewHomeModal')?.addEventListener('click', event => {
        if (event.target?.id === 'reviewHomeModal') closeReviewHome();
    });
    document.getElementById('reviewHomeBody')?.addEventListener('click', async event => {
        const action = event.target.closest('[data-action]')?.dataset.action;
        if (!action) return;
        if (action === 'open-group') {
            activeGroup = event.target.closest('[data-tier]')?.dataset.tier || null;
            visibleWords = LIST_PAGE_SIZE;
            renderReviewHome();
            document.querySelector('#reviewHomeBody .review-home-back')?.focus();
        } else if (action === 'back-to-groups') {
            activeGroup = null;
            renderReviewHome();
            document.querySelector('#reviewHomeBody [data-action="open-group"]:not([disabled])')?.focus();
        } else if (action === 'show-more') {
            visibleWords += LIST_PAGE_SIZE;
            renderReviewHome();
        } else if (action === 'srs-info') {
            openSpacedRepetitionInfo();
        }
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
        if (event.key !== 'Escape') return;
        const info = document.getElementById('spacedRepetitionInfoModal');
        if (info && !info.classList.contains('hidden')) {
            closeSpacedRepetitionInfo();
        } else if (activeGroup) {
            activeGroup = null;
            renderReviewHome();
        } else {
            closeReviewHome();
        }
    });
}

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
