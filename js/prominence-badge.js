// The meaning-frequency badge: three bars, with a tooltip naming the level
// (Dominant / Common / Uncommon / Rare). Its own module so pages without the
// study engine (the standalone About page and its walkthrough) draw the same
// bars as the live card. flashcards.js imports it; inline handlers in the
// badge markup call the window.* functions set at the bottom.

import { escapeCardText } from './card-metadata-pills.js?v=7a369b8a';

export const PROMINENCE_BLURBS = {
    dominant: 'means this most often',
    common: 'means this often',
    uncommon: 'means this sometimes',
    rare: 'means this rarely',
};

export function prominenceMeterHTML(key) {
    // Three bars; Rare is all three empty rather than a fourth, lowest step.
    const filled = key === 'dominant' ? 3 : key === 'common' ? 2 : key === 'uncommon' ? 1 : 0;
    return `<span class="sense-prominence-meter" aria-hidden="true">${[1, 2, 3].map(i => `<i${i <= filled ? ' class="is-on"' : ''}></i>`).join('')}</span>`;
}

export function prominenceBadgeHTML(promInfo, extraStyle = '') {
    if (!promInfo) return '';
    const key = promInfo.key || 'rare';
    const label = promInfo.label || 'Rare';
    const blurb = PROMINENCE_BLURBS[key] || PROMINENCE_BLURBS.rare;
    const style = extraStyle ? ` style="${extraStyle}"` : '';
    return `<span class="sense-prominence-badge prominence-${escapeCardText(key)}"${style} role="button" tabindex="0" aria-expanded="false" aria-label="${escapeCardText(label)}. Tap to explain." onpointerenter="if (event.pointerType !== 'touch') showProminenceTooltip(this)" onpointerleave="hideProminenceTooltip(this)" onfocus="showProminenceTooltip(this)" onblur="hideProminenceTooltip()" onclick="toggleProminenceBadge(event, this)" onkeydown="if (event.key === 'Enter' || event.key === ' ') toggleProminenceBadge(event, this)">${prominenceMeterHTML(key)}<span class="sense-prominence-detail"><span class="sense-prominence-detail-heading">${prominenceMeterHTML(key)}<strong>${escapeCardText(label)}</strong></span><span class="sense-prominence-detail-description">${escapeCardText(blurb)}</span></span></span>`;
}

let prominenceTooltip = null;
let prominenceTooltipSource = null;

export function hideProminenceTooltip(button = null) {
    if (button && (button !== prominenceTooltipSource
        || button.getAttribute('aria-expanded') === 'true')) return;
    prominenceTooltipSource?.setAttribute('aria-expanded', 'false');
    prominenceTooltipSource?.removeAttribute('aria-describedby');
    prominenceTooltipSource = null;
    if (!prominenceTooltip) return;
    if (prominenceTooltip.hasAttribute('popover')
        && prominenceTooltip.matches(':popover-open')) prominenceTooltip.hidePopover();
    prominenceTooltip.hidden = true;
}

export function showProminenceTooltip(button) {
    const detail = button?.querySelector('.sense-prominence-detail');
    if (!detail || !button.isConnected) return;
    if (prominenceTooltipSource !== button) hideProminenceTooltip();
    if (!prominenceTooltip) {
        prominenceTooltip = document.createElement('div');
        prominenceTooltip.id = 'commonnessTooltip';
        prominenceTooltip.className = 'sense-prominence-detail sense-prominence-popup';
        prominenceTooltip.setAttribute('role', 'tooltip');
        // The browser's top layer escapes scrolling and transformed card
        // ancestors. Older browsers still get a fixed overlay on the body.
        if (typeof prominenceTooltip.showPopover === 'function') {
            prominenceTooltip.setAttribute('popover', 'manual');
        }
        document.body.append(prominenceTooltip);
    }
    prominenceTooltipSource = button;
    button.setAttribute('aria-describedby', 'commonnessTooltip');
    prominenceTooltip.innerHTML = detail.innerHTML;
    prominenceTooltip.hidden = false;
    if (prominenceTooltip.hasAttribute('popover')
        && !prominenceTooltip.matches(':popover-open')) prominenceTooltip.showPopover();

    const anchor = button.getBoundingClientRect();
    const box = prominenceTooltip.getBoundingClientRect();
    const inset = 8;
    const viewportWidth = document.documentElement.clientWidth;
    const viewportHeight = window.innerHeight;
    let left = anchor.left - box.width - inset;
    if (left < inset) left = anchor.right + inset;
    left = Math.max(inset, Math.min(left, viewportWidth - box.width - inset));
    const top = Math.max(inset, Math.min(anchor.top + (anchor.height - box.height) / 2,
        viewportHeight - box.height - inset));
    // Account for the app's larger-text page zoom when positioning in
    // viewport coordinates; the tooltip keeps the learner's text size.
    const scale = box.width / prominenceTooltip.offsetWidth || 1;
    prominenceTooltip.style.left = `${left / scale}px`;
    prominenceTooltip.style.top = `${top / scale}px`;
}

export function toggleProminenceBadge(event, button) {
    event?.stopPropagation?.();
    event?.preventDefault?.();
    if (!button) return;
    if (button.getAttribute('aria-expanded') === 'true') {
        hideProminenceTooltip();
    } else {
        showProminenceTooltip(button);
        button.setAttribute('aria-expanded', 'true');
    }
}

document.addEventListener('pointerdown', event => {
    if (!event.target.closest('.sense-prominence-badge')) hideProminenceTooltip();
}, true);
document.addEventListener('keydown', event => {
    if (event.key === 'Escape') hideProminenceTooltip();
});
document.addEventListener('scroll', () => hideProminenceTooltip(), true);
window.addEventListener?.('resize', () => hideProminenceTooltip());
window.prominenceBadgeHTML = prominenceBadgeHTML;
window.toggleProminenceBadge = toggleProminenceBadge;
window.showProminenceTooltip = showProminenceTooltip;
window.hideProminenceTooltip = hideProminenceTooltip;
