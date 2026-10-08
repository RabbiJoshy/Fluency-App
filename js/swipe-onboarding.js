// One-time guidance lives outside the card, so the answer face stays clear.
const LEARNED_KEY = 'fluency_swipe_grading_learned_v1';
let learned = false;
try { learned = localStorage.getItem(LEARNED_KEY) === '1'; } catch (_) {}
let revealed = false;

export function showSwipeHint({ realCard = true } = {}) {
    if (learned || !realCard) return;
    revealed = true;
    let hint = document.getElementById('firstSwipeHint');
    if (!hint) {
        hint = document.createElement('div');
        hint.id = 'firstSwipeHint';
        hint.setAttribute('role', 'status');
        hint.textContent = '← Needs practice · Got it →';
        Object.assign(hint.style, {
            position: 'fixed', bottom: 'max(18px, env(safe-area-inset-bottom))',
            left: '50%', transform: 'translateX(-50%)', zIndex: '1100',
            padding: '12px 18px', borderRadius: '24px',
            background: 'var(--bg-secondary, #242330)', color: 'var(--text-primary, #fff)',
            border: '1px solid var(--border-color, #777)', boxShadow: '0 4px 20px #0005',
            fontSize: '14px', whiteSpace: 'nowrap', pointerEvents: 'none'
        });
        document.body.appendChild(hint);
    }
    hint.hidden = false;
}

export function rememberGradingSwipe() {
    if (!revealed) return;
    learned = true;
    try { localStorage.setItem(LEARNED_KEY, '1'); } catch (_) {}
    document.getElementById('firstSwipeHint')?.remove();
}

// Keep the hint through card changes; hide it while setup or a dialog is open.
export function refreshSwipeHint() {
    const hint = document.getElementById('firstSwipeHint');
    if (!hint) return;
    const hidden = Boolean(document.getElementById('appContent')?.classList.contains('hidden')
        || document.querySelector('.modal:not(.hidden), .knowledge-overview-modal:not([hidden])'));
    if (hint.hidden !== hidden) hint.hidden = hidden;
}
if (typeof MutationObserver !== 'undefined') {
    new MutationObserver(refreshSwipeHint).observe(document.body, {
        subtree: true, attributes: true, attributeFilter: ['class', 'hidden'], childList: true
    });
}
