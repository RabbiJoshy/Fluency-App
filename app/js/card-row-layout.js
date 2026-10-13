// Fit the rendered gloss, rather than guessing from its character count.
// Keep the dictionary data intact; resizing restores the complete markup.
const originals = new WeakMap();

function restoreText(element) {
    const original = originals.get(element);
    if (!original) return;
    element.innerHTML = original.html;
    if (original.title === null) element.removeAttribute('title');
    else element.setAttribute('title', original.title);
    originals.delete(element);
}

function shortenAtWord(element) {
    const fullText = element.textContent;
    const boundaries = [...fullText.matchAll(/\s+/gu)].map(match => match.index);
    if (!boundaries.length) return; // A single long word stays on one line.
    const original = { html: element.innerHTML, title: element.getAttribute('title') };
    const fits = end => {
        element.innerHTML = original.html;
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
        let offset = end;
        while (walker.nextNode()) {
            const node = walker.currentNode;
            if (offset > node.length) { offset -= node.length; continue; }
            const range = document.createRange();
            range.setStart(node, offset);
            range.setEnd(element, element.childNodes.length);
            range.deleteContents();
            node.textContent = node.textContent.replace(/[,;:.\s]+$/u, '');
            element.append('…');
            break;
        }
        return element.scrollWidth <= element.clientWidth + 1;
    };
    let low = 0;
    let high = boundaries.length - 1;
    let best = -1;
    while (low <= high) {
        const middle = Math.floor((low + high) / 2);
        if (fits(boundaries[middle])) { best = middle; low = middle + 1; }
        else high = middle - 1;
    }
    if (best < 0) {
        element.innerHTML = original.html;
        return;
    }
    fits(boundaries[best]);
    originals.set(element, original);
    element.title = fullText;
}

export function fitSenseRowText(root) {
    if (!root) return;
    const elements = [...root.querySelectorAll('.meaning-row-gloss, .group-card-shared')];
    root.querySelectorAll('.sense-row-needs-stack').forEach(row => row.classList.remove('sense-row-needs-stack'));
    for (const element of elements) {
        restoreText(element);
        element.style.removeProperty('font-size');
    }
    for (const element of elements) {
        if (!element.clientWidth || !element.textContent.trim()) continue;
        const style = getComputedStyle(element);
        const size = parseFloat(style.fontSize);
        const lineRatio = parseFloat(style.lineHeight) / size || 1.25;
        const oneLine = style.whiteSpace === 'nowrap';
        const lines = () => Math.ceil((element.scrollHeight - 1) / (parseFloat(getComputedStyle(element).fontSize) * lineRatio));
        const originalLines = lines();
        const fits = () => element.scrollWidth <= element.clientWidth + 1
            && (oneLine || lines() < originalLines);
        // A near miss gets at most 2px of shrinking, in half-pixel steps.
        // Otherwise use another complete line, keeping the text readable.
        if (element.scrollWidth > element.clientWidth + 1 || (!oneLine && originalLines > 1)) {
            let fitted = false;
            for (let next = size - 0.5; next >= Math.max(15, size - 2); next -= 0.5) {
                element.style.fontSize = `${next}px`;
                if (fits()) { fitted = true; break; }
            }
            if (!fitted) element.style.removeProperty('font-size');
        }
        if (!oneLine && element.scrollWidth > element.clientWidth + 1) {
            element.closest('.meaning-row')?.classList.add('sense-row-needs-stack');
        }
        if (oneLine && element.scrollWidth > element.clientWidth + 1) shortenAtWord(element);
    }
}
