// Local loading surfaces keep their measured space and surrounding controls.
// A newer request owns the region, so an older completion cannot clear it.
const owners = new WeakMap();

export function beginRegionLoading(region, { label = 'Loading…', shape = 'rows', preserve = false, onCancel } = {}) {
    if (!region) return () => {};
    owners.get(region)?.();
    const previousBusy = region.getAttribute('aria-busy');
    const previousMinHeight = region.style.minHeight;
    // offsetHeight is layout geometry. A dialog's entrance transform scales
    // getBoundingClientRect(), which would reserve a smaller box and move the
    // input when the skeleton finishes.
    let height = region.offsetHeight || 0;
    if (height > 0) {
        const style = region.ownerDocument.defaultView.getComputedStyle(region);
        if (style.boxSizing !== 'border-box') {
            height -= ['paddingTop', 'paddingBottom', 'borderTopWidth', 'borderBottomWidth']
                .reduce((sum, key) => sum + (parseFloat(style[key]) || 0), 0);
        }
        region.style.minHeight = `${Math.max(0, height)}px`;
    }
    region.setAttribute('aria-busy', 'true');
    let placeholder;
    if (!preserve) {
        region.classList.add('region-loading');
        placeholder = document.createElement('div');
        placeholder.className = `region-loading-placeholder region-loading-${shape}`;
        placeholder.setAttribute('role', 'status');
        const status = document.createElement('span');
        status.className = 'visually-hidden'; status.textContent = label;
        placeholder.appendChild(status);
        for (let i = 0; i < 3; i++) {
            const line = document.createElement('span');
            line.className = 'region-loading-line'; line.setAttribute('aria-hidden', 'true');
            placeholder.appendChild(line);
        }
        region.appendChild(placeholder);
    }
    let cancel;
    if (onCancel) {
        cancel = document.createElement('button');
        cancel.type = 'button'; cancel.className = 'region-loading-cancel conj-close-btn';
        cancel.setAttribute('aria-label', 'Close'); cancel.textContent = '×';
        cancel.onclick = () => { onCancel(); finish(); };
        region.appendChild(cancel);
    }
    const finish = () => {
        if (owners.get(region) !== finish) return;
        placeholder?.remove();
        cancel?.remove();
        region.classList.remove('region-loading');
        region.style.minHeight = previousMinHeight;
        if (previousBusy === null) region.removeAttribute('aria-busy');
        else region.setAttribute('aria-busy', previousBusy);
        owners.delete(region);
    };
    owners.set(region, finish);
    return finish;
}

export function showRegionError(region, message, retry) {
    if (!region) return;
    owners.get(region)?.();
    const box = document.createElement('div');
    box.className = 'region-load-error';
    const text = document.createElement('p'); text.setAttribute('role', 'alert'); text.textContent = message;
    box.appendChild(text);
    if (retry) {
        const button = document.createElement('button');
        button.type = 'button'; button.className = 'region-retry'; button.textContent = 'Try again';
        button.onclick = () => { button.disabled = true; retry(); };
        box.appendChild(button);
    }
    region.replaceChildren(box);
}

// Unlike AbortSignal alone this also bounds transports that stall acquiring a
// token or reading a body. Callers must ignore results from superseded requests.
export function boundedLoad(promise, timeoutMs = 15000) {
    let timer;
    return Promise.race([promise, new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('Loading took too long. Please try again.')), timeoutMs);
    })]).finally(() => clearTimeout(timer));
}
