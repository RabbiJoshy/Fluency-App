// Dictionary reference cards are opened only by explicit "See …" links.
// They are not deck entries, occurrence evidence, or progress identities.
const referenceLoads = new Map();
const fold = value => String(value || '').normalize('NFC').toLocaleLowerCase().replace(/\s+/gu, ' ').trim();
const escape = value => String(value || '').replace(/[&<>"']/g, char => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
}[char]));

export function isSeeExpressionReference(target, relation) {
    return relation === 'see' && /\s/u.test(String(target || '').trim());
}

export async function resolveSeeExpression(target, langConfig, vocabulary = []) {
    const key = fold(target);
    // Existing attached definitions are usable without downloading new data.
    const senses = vocabulary.flatMap(row => (row.meanings || [])
        .filter(m => fold(m.headword || m.expression) === key && m.translation && !/^see\s/iu.test(m.translation))
        .map(m => ({translation:m.translation, context:m.context || '',
            canonical_example:m.canonical_example || null})));
    const path = langConfig?.seeReferencesPath;
    if (path) {
        if (!referenceLoads.has(path)) {
            referenceLoads.set(path, fetch(path, {cache:'no-cache'}).then(async response => {
                if (!response.ok) throw new Error('Expression reference data unavailable');
                const payload = await response.json();
                if (payload.schema !== 'see-expression-references/v1') throw new Error('Unsupported expression reference data');
                return payload;
            }).catch(error => { referenceLoads.delete(path); throw error; }));
        }
        let payload;
        try { payload = await referenceLoads.get(path); }
        catch (error) {
            if (senses.length) return {expression:target, senses};
            throw error;
        }
        if (payload.scope !== 'see_links_only' || (langConfig.routeCode && payload.language !== langConfig.routeCode))
            throw new Error('Expression reference language or scope mismatch');
        const entry = payload.entries?.[key];
        if (entry?.senses?.length) return entry;
    }
    return senses.length ? {expression:target, senses} : null;
}

export function seeExpressionCardHTML(entry, target, unavailable = false) {
    const title = entry?.expression || target;
    const unique = new Set();
    const senses = (entry?.senses || []).filter(sense => {
        const key = `${sense.translation}\u0000${sense.context || ''}`;
        if (!sense.translation || unique.has(key)) return false;
        unique.add(key); return true;
    });
    const definitions = senses.map(sense => {
        const example = sense.canonical_example;
        return `<li><p class="see-expression-definition">${escape(sense.translation)}</p>`
            + (sense.context ? `<p class="see-expression-context">${escape(sense.context)}</p>` : '')
            + (example?.text ? `<blockquote><p>${escape(example.text)}</p>`
                + (example.translation ? `<p class="see-expression-context">${escape(example.translation)}</p>` : '') + '</blockquote>' : '') + '</li>';
    }).join('');
    // Source URLs are optional and restricted to HTTPS; dictionary text is escaped.
    const url = /^https:\/\//u.test(entry?.source_url || '') ? entry.source_url : '';
    return `<article class="see-expression-card"><header><p class="see-expression-kind">Expression</p>`
        + `<h2 id="seeExpressionTitle" tabindex="-1">${escape(title)}</h2></header>`
        + (definitions ? `<ul class="see-expression-senses">${definitions}</ul>`
            : `<p role="status">${unavailable ? 'Could not load this expression. Close and try the link again.' : 'A definition for this expression is not available yet.'}</p>`)
        + (url ? `<a class="see-expression-source" href="${escape(url)}" target="_blank" rel="noopener noreferrer">Dictionary source ↗</a>` : '')
        + '<button type="button" class="see-expression-close">Back to word</button></article>';
}

export function showSeeExpressionCard(entry, target, trigger, unavailable = false) {
    document.getElementById('seeExpressionDialog')?.close();
    const dialog = document.createElement('dialog');
    dialog.id = 'seeExpressionDialog';
    dialog.className = 'see-expression-dialog';
    dialog.setAttribute('aria-labelledby', 'seeExpressionTitle');
    dialog.innerHTML = seeExpressionCardHTML(entry, target, unavailable);
    dialog.addEventListener('keydown', event => event.stopPropagation());
    dialog.addEventListener('click', event => {
        event.stopPropagation();
        if (event.target === dialog || event.target.closest('.see-expression-close')) dialog.close();
    });
    dialog.addEventListener('close', () => {
        dialog.remove();
        if (trigger?.isConnected) trigger.focus();
    }, {once:true});
    document.body.appendChild(dialog);
    dialog.showModal();
    dialog.querySelector('h2')?.focus({preventScroll:true});
    dialog.scrollTop = 0;
}
