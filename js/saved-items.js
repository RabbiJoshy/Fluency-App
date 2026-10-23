// Keep the original storage key and word shape so existing saves survive.
// Saved is a personal collection; it never writes to card or review progress.
export const SAVED_ITEMS_KEY = 'fluency_saved_words_v1';
export const escapeSavedText = value => String(value ?? '').replace(/[&<>"']/g,
    char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

export function loadSavedItems(storage = globalThis.localStorage) {
    try {
        const items = JSON.parse(storage.getItem(SAVED_ITEMS_KEY) || '[]');
        return Array.isArray(items) ? items.filter(item => item && typeof item.surface === 'string') : [];
    } catch (_) { return []; }
}

export function savedItemKey(item) {
    return [item.type === 'phrase' ? 'phrase' : 'word', item.language || '', item.surface || '', item.sentence || ''].join('\0');
}

export function isItemSaved(entry) {
    return loadSavedItems().some(item => savedItemKey(item) === savedItemKey(entry));
}

export function toggleSavedItem(entry, storage = globalThis.localStorage) {
    if (!String(entry.surface || '').trim()) throw new Error('Choose a word or phrase to save.');
    const items = loadSavedItems(storage);
    const index = items.findIndex(item => savedItemKey(item) === savedItemKey(entry));
    if (index >= 0) items.splice(index, 1);
    else items.unshift({ ...entry, type: entry.type === 'phrase' ? 'phrase' : 'word', savedAt: new Date().toISOString() });
    // Only report success after storage accepts the write.
    storage.setItem(SAVED_ITEMS_KEY, JSON.stringify(items));
    return index < 0;
}

export function removeSavedItem(key, storage = globalThis.localStorage) {
    storage.setItem(SAVED_ITEMS_KEY, JSON.stringify(loadSavedItems(storage).filter(item => savedItemKey(item) !== key)));
}

// Highlight evidenced spellings only. Inflections come from supplied variants
// or matched_surface; a phrase absent from its example stays unmarked.
export function phraseHighlightRanges(sentence, forms) {
    const text = String(sentence || '');
    for (const form of forms.filter(value => typeof value === 'string' && value.trim())) {
        const tokens = form.trim().split(/\s+/u);
        const pattern = tokens.map((token, index) => (index ? (/['’]$/u.test(tokens[index - 1]) ? '\\s*' : '\\s+') : '') + (/^\[pron\]$/iu.test(token)
            ? '(?:me|te|se|le|les|nos|lo|la|los|las)'
            : token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/['’]/gu, "['’]"))).join('');
        const matches = [...text.matchAll(new RegExp(`(?<![\\p{L}\\p{N}])${pattern}(?![\\p{L}\\p{N}])`, 'giu'))];
        if (matches.length) return matches.map(match => ({ start: match.index, end: match.index + match[0].length }));
    }
    return [];
}

export function highlightSavedSentence(sentence, ranges = []) {
    const text = String(sentence || '');
    let cursor = 0, html = '';
    for (const range of [...ranges].sort((a, b) => a.start - b.start)) {
        if (!Number.isInteger(range.start) || !Number.isInteger(range.end)
            || range.start < cursor || range.end <= range.start || range.end > text.length) continue;
        html += escapeSavedText(text.slice(cursor, range.start))
            + `<span class="saved-phrase-hit">${escapeSavedText(text.slice(range.start, range.end))}</span>`;
        cursor = range.end;
    }
    return html + escapeSavedText(text.slice(cursor));
}

export function savedPhraseEntry(item, language, example = (item.examples || item.allExamples || [])[0]) {
    const sentence = typeof example === 'string' ? example : example?.target || example?.text || example?.targetSentence
        || example?.spanish || example?.portuguese || example?.french || example?.czech || example?.swedish
        || example?.dutch || example?.finnish || example?.italian || example?.polish || '';
    const variants = Array.isArray(item.variants) ? item.variants : Object.keys(item.variants || {});
    const surface = item.expression || item.headword || '';
    return {
        type: 'phrase', language, surface,
        gloss: item.translation || item.meaning || '', context: item.context || '',
        sentence, english: example?.english || example?.translation || example?.englishSentence || '',
        highlightRanges: phraseHighlightRanges(sentence, [example?.matched_surface, example?.matched_variant, surface, ...variants]),
    };
}

export const SAVE_STAR_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.8 5.7 6.3.9-4.5 4.4 1.1 6.2-5.7-3-5.7 3 1.1-6.2L3.2 9.6l6.3-.9L12 3Z"/></svg>';

export function saveItemButtonHTML(entry) {
    if (!entry.surface) return '';
    const saved = isItemSaved(entry);
    return `<button type="button" class="save-item-btn${saved ? ' is-saved' : ''}" data-save-item="${escapeSavedText(JSON.stringify(entry))}"
        aria-pressed="${saved}" aria-haspopup="dialog" aria-label="${saved ? 'Remove' : 'Add'} ${escapeSavedText(entry.surface)}${saved ? ' from Saved' : ' to Saved'}"
        title="${saved ? 'Remove from Saved' : 'Add to Saved'}">${SAVE_STAR_ICON}</button>`;
}

export function renderSavedItems() {
    const items = loadSavedItems();
    const section = document.getElementById('savedItemsSection');
    if (section) section.hidden = items.length === 0;
    const body = document.getElementById('savedWordsBody');
    if (body) {
        body.hidden = items.length === 0;
        body.style.display = '';
        body.innerHTML = items.map(item => {
            const ranges = item.highlightRanges || phraseHighlightRanges(item.sentence || '', [item.surface]);
            return `<article class="saved-item">
                <div class="saved-item-heading"><div><span class="saved-item-kind">${item.type === 'phrase' ? 'Phrase' : 'Word'} · ${escapeSavedText(item.language)}</span>
                <h4>${escapeSavedText(item.surface)}</h4></div>
                <button type="button" class="saved-item-remove" data-remove-saved="${escapeSavedText(JSON.stringify(savedItemKey(item)))}"
                    aria-label="Remove ${escapeSavedText(item.surface)} from Saved">Remove</button></div>
                ${item.gloss ? `<p class="saved-item-meaning">${escapeSavedText(item.gloss)}</p>` : ''}
                ${item.context ? `<p class="saved-item-context">${escapeSavedText(item.context)}</p>` : ''}
                ${item.sentence ? `<p class="saved-item-example">${highlightSavedSentence(item.sentence, ranges)}</p>` : ''}
                ${item.english ? `<p class="saved-item-translation">${escapeSavedText(item.english)}</p>` : ''}
            </article>`;
        }).join('');
    }
    const download = document.getElementById('downloadSavedWordsBtn');
    if (download) download.hidden = !items.length;
    const shortcut = document.getElementById('progressSavedBtn');
    if (shortcut) { shortcut.hidden = !items.length; shortcut.textContent = `Saved (${items.length}) ›`; }
    document.querySelectorAll('[data-save-item]').forEach(button => {
        try {
            const entry = JSON.parse(button.dataset.saveItem);
            const saved = items.some(item => savedItemKey(item) === savedItemKey(entry));
            button.classList.toggle('is-saved', saved);
            button.setAttribute('aria-pressed', String(saved));
            button.setAttribute('aria-label', `${saved ? 'Remove' : 'Add'} ${entry.surface}${saved ? ' from Saved' : ' to Saved'}`);
            button.title = saved ? 'Remove from Saved' : 'Add to Saved';
            button.innerHTML = SAVE_STAR_ICON;
            const actionLabel = button.nextElementSibling?.classList.contains('expression-save-action-label') ? button.nextElementSibling : null;
            if (actionLabel) {
                actionLabel.textContent = saved ? 'Saved' : 'Save expression';
            }
            const cardItem = button.closest('.expression-card-item');
            const indicator = cardItem?.querySelector('.expression-saved-indicator');
            if (indicator) {
                indicator.hidden = !saved;
                indicator.classList.toggle('is-visible', saved);
                indicator.title = saved ? 'Saved in your collection' : '';
            }
        } catch (_) { /* Ignore an unrelated malformed control. */ }
    });
}

export function openSavedItems() {
    document.getElementById('savedItemsToast')?.setAttribute('hidden', '');
    window.hideTotalStatsModal?.();
    window.showSettingsModalWithTab?.('vocabulary');
    renderSavedItems();
    const section = document.getElementById('savedItemsSection');
    section?.scrollIntoView({ block: 'start' });
    document.getElementById('savedWordsTitle')?.focus({ preventScroll: true });
}

let toastTimer;
function notifySaved(message, canView = false) {
    let toast = document.getElementById('savedItemsToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'savedItemsToast';
        toast.setAttribute('role', 'status');
        toast.innerHTML = '<span></span><button type="button">View Saved</button>';
        toast.querySelector('button').addEventListener('click', openSavedItems);
        document.body.appendChild(toast);
    }
    toast.querySelector('span').textContent = message;
    toast.querySelector('button').hidden = !canView;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 5000);
}

export function toggleAndRenderSavedItem(entry) {
    try {
        const saved = toggleSavedItem(entry);
        renderSavedItems();
        notifySaved(saved ? 'Saved for later.' : 'Removed from Saved.', saved);
        return saved;
    } catch (_) {
        notifySaved('Could not save on this device. Please try again.');
        return false;
    }
}

export function downloadSavedItems() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(loadSavedItems(), null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'fluency-saved.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function confirmSavedItem(entry) {
    let dialog = document.getElementById('savedItemConfirmation');
    if (!dialog) {
        dialog = document.createElement('dialog');
        dialog.id = 'savedItemConfirmation';
        dialog.className = 'saved-confirm-dialog';
        dialog.setAttribute('aria-labelledby', 'savedConfirmationTitle');
        dialog.setAttribute('aria-describedby', 'savedConfirmationPhrase');
        dialog.innerHTML = `<h2 id="savedConfirmationTitle"></h2><p id="savedConfirmationPhrase"></p>
            <div class="saved-confirm-actions"><button type="button" data-save-cancel>Cancel</button>
            <button type="button" data-save-confirm></button></div>`;
        dialog.querySelector('[data-save-cancel]').addEventListener('click', () => dialog.close());
        dialog.addEventListener('keydown', event => event.stopPropagation());
        document.body.appendChild(dialog);
    }
    const wasSaved = isItemSaved(entry);
    document.getElementById('savedConfirmationTitle').textContent = wasSaved ? 'Remove from Saved?' : 'Add to Saved?';
    document.getElementById('savedConfirmationPhrase').textContent = entry.surface;
    const confirm = dialog.querySelector('[data-save-confirm]');
    confirm.textContent = wasSaved ? 'Remove' : 'Add to Saved';
    confirm.onclick = () => {
        dialog.close();
        // A save in another tab must not turn an Add confirmation into removal.
        if (isItemSaved(entry) === wasSaved) toggleAndRenderSavedItem(entry);
        else renderSavedItems();
    };
    if (!dialog.open) dialog.showModal();
    dialog.querySelector('[data-save-cancel]').focus();
}

if (typeof document !== 'undefined') {
    document.addEventListener('click', event => {
        const save = event.target.closest('[data-save-item]');
        if (save) {
            event.preventDefault(); event.stopPropagation();
            try { confirmSavedItem(JSON.parse(save.dataset.saveItem)); } catch (_) {}
        }
        const remove = event.target.closest('[data-remove-saved]');
        if (remove) {
            const index = [...document.querySelectorAll('[data-remove-saved]')].indexOf(remove);
            try {
                removeSavedItem(JSON.parse(remove.dataset.removeSaved));
                renderSavedItems();
                const remaining = [...document.querySelectorAll('[data-remove-saved]')];
                (remaining[Math.min(index, remaining.length - 1)] || document.querySelector('.settings-pane-tab[data-settings-pane="words"]'))?.focus();
                notifySaved('Removed from Saved.');
            } catch (_) { notifySaved('Could not remove this item. Please try again.'); }
        }
    }, true);
    window.addEventListener('storage', event => { if (event.key === SAVED_ITEMS_KEY || event.key === null) renderSavedItems(); });
}
globalThis.renderSavedWords = renderSavedItems;
globalThis.openSavedWords = openSavedItems;
