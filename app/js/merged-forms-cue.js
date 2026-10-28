// Front-side membership disclosure. It never changes card identity or grouping.
export function mergedCardForms(card) {
    if (!card?.mergedLemma || card.isChainChild) return [];
    const raw = card.mergedGroupSurfaces || card.mergedSurfaces || [];
    const forms = new Map();
    for (const value of raw) {
        const text = String(value || '').trim();
        if (text) forms.set(text.normalize('NFC').toLocaleLowerCase(), text);
    }
    return [...forms.values()];
}

let cue;
let panel;
let trigger;

export function closeMergedFormsCue() {
    if (!panel) return;
    panel.hidden = true;
    panel.style.maxHeight = '';
    trigger.setAttribute('aria-expanded', 'false');
}

function positionCue() {
    if (!cue || cue.hidden) return;
    const word = document.getElementById('frontWord');
    const face = cue.parentElement;
    const bounds = face.getBoundingClientRect();
    const wordBounds = word.getBoundingClientRect();
    // Ratios keep coordinates in the card's own space during scaled layouts.
    const scale = bounds.height / face.offsetHeight || 1;
    const topInFace = (wordBounds.bottom - bounds.top) / scale + 10;
    cue.style.top = `${topInFace}px`;
    if (!panel.hidden) {
        const availableHeight = face.offsetHeight - topInFace - 12;
        if (availableHeight > 60) {
            panel.style.maxHeight = `${Math.min(300, Math.floor(availableHeight))}px`;
        }
    }
}

function ensureCue() {
    if (cue?.isConnected) return;
    const face = document.getElementById('frontWord')?.closest('.card-front');
    if (!face) return;
    cue = document.createElement('div');
    cue.id = 'frontMergedForms';
    cue.className = 'front-merged-forms';
    cue.hidden = true;
    // This is a sibling of the flip button: native buttons must not nest.
    trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'merged-forms-trigger';
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', 'mergedFormsTooltip');
    panel = document.createElement('div');
    panel.id = 'mergedFormsTooltip';
    panel.className = 'merged-forms-tooltip';
    panel.hidden = true;
    panel.setAttribute('role', 'region');
    panel.setAttribute('aria-labelledby', 'mergedFormsHeading');
    const heading = document.createElement('div');
    heading.id = 'mergedFormsHeading';
    heading.className = 'merged-forms-heading';
    heading.textContent = 'Merged by Smart Skip';
    const list = document.createElement('div');
    list.className = 'merged-forms-list';
    panel.append(heading, list);
    cue.append(trigger, panel);
    face.append(cue);
    cue.addEventListener('click', event => event.stopPropagation());
    // Keep Enter/Space activation and Tab navigation native while focused here;
    // the study surface otherwise uses those keys to grade or cycle examples.
    cue.addEventListener('keydown', event => event.stopPropagation());
    trigger.addEventListener('click', event => {
        event.preventDefault();
        panel.hidden = !panel.hidden;
        trigger.setAttribute('aria-expanded', String(!panel.hidden));
        positionCue();
    });
    document.addEventListener('click', event => { if (!cue.contains(event.target)) closeMergedFormsCue(); });
    document.addEventListener('keydown', event => {
        if (panel.hidden || event.key !== 'Escape') return;
        event.stopImmediatePropagation();
        event.preventDefault();
        closeMergedFormsCue();
        trigger.focus();
    }, true);
    window.addEventListener('resize', positionCue);
    document.getElementById('flashcard')?.addEventListener('transitionend', positionCue);
    if (typeof ResizeObserver !== 'undefined') {
        const observer = new ResizeObserver(positionCue);
        observer.observe(face);
        observer.observe(document.getElementById('frontWord'));
    }
}

export const MAX_DISPLAYED_MERGED_FORMS = 14;

export function renderMergedFormsCue(card, visible = true) {
    ensureCue();
    if (!cue) return;
    closeMergedFormsCue();
    const forms = mergedCardForms(card);
    const shown = String(card?.displaySurface || card?.targetWord || '').normalize('NFC').toLocaleLowerCase();
    const others = forms.filter(form => form.normalize('NFC').toLocaleLowerCase() !== shown);
    cue.hidden = !visible || !forms.some(form => form.normalize('NFC').toLocaleLowerCase() === shown) || !others.length;
    if (cue.hidden) return;
    trigger.textContent = `+${others.length} other form${others.length === 1 ? '' : 's'}`;
    trigger.setAttribute('aria-label', `${trigger.textContent}. Show forms merged by Smart Skip`);

    // Ensure the currently displayed surface is always included within the capped slice
    let displayedForms = forms;
    let extraCount = 0;
    if (forms.length > MAX_DISPLAYED_MERGED_FORMS) {
        const shownIdx = forms.findIndex(f => f.normalize('NFC').toLocaleLowerCase() === shown);
        if (shownIdx >= MAX_DISPLAYED_MERGED_FORMS) {
            // Swap shown form into the visible window
            displayedForms = [forms[shownIdx], ...forms.slice(0, MAX_DISPLAYED_MERGED_FORMS - 1)];
        } else {
            displayedForms = forms.slice(0, MAX_DISPLAYED_MERGED_FORMS);
        }
        extraCount = forms.length - displayedForms.length;
    }

    const items = displayedForms.map(form => {
        const item = document.createElement('span');
        item.textContent = form;
        if (form.normalize('NFC').toLocaleLowerCase() === shown) item.className = 'is-displayed';
        return item;
    });

    if (extraCount > 0) {
        const moreItem = document.createElement('span');
        moreItem.className = 'merged-forms-more';
        moreItem.textContent = `+ ${extraCount} more`;
        items.push(moreItem);
    }

    panel.querySelector('.merged-forms-list').replaceChildren(...items);
    requestAnimationFrame(positionCue);
    document.fonts?.ready?.then(positionCue);
}
