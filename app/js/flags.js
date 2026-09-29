// Rectangular flags instead of emoji. The SVGs are vendored from flag-icons
// (MIT, assets/flags/LICENSE) and named by ISO 3166 code.
//
// Config and older call sites still name a flag by its emoji ("🇧🇷"); that
// stays the data format. installFlagRendering() swaps any emoji flag that
// reaches the page for the matching picture, so every place that prints one
// — language chip, picker, loading mark, reverse button — gets it without its
// own code. A flag we have no file for stays an emoji.

const FLAG_DIR = 'assets/flags/';
const AVAILABLE = new Set([
    'ao', 'ar', 'bo', 'br', 'cl', 'co', 'cr', 'cu', 'cz', 'do', 'es', 'fi', 'fr',
    'gb', 'gt', 'gw', 'hn', 'it', 'mo', 'mx', 'mz', 'ni', 'nl', 'pa', 'pe', 'pl',
    'pr', 'pt', 'py', 'ru', 'se', 'sv', 'us', 'uy', 've',
]);

// Region labels as the sense menus spell them (Wiktionary hyphenates:
// "Guinea-Bissau"). Only whole countries map to a flag; "Latin America",
// "Azores" or "Northeast Brazil" stay words, because a flag would say less.
const REGION_CODES = {
    angola: 'ao', argentina: 'ar', bolivia: 'bo', brazil: 'br', chile: 'cl',
    colombia: 'co', 'costa rica': 'cr', cuba: 'cu', 'czech republic': 'cz', czechia: 'cz',
    'dominican republic': 'do', spain: 'es', finland: 'fi', france: 'fr',
    uk: 'gb', 'united kingdom': 'gb', britain: 'gb', guatemala: 'gt',
    'guinea bissau': 'gw', honduras: 'hn', italy: 'it', macau: 'mo', macao: 'mo',
    mexico: 'mx', mozambique: 'mz', nicaragua: 'ni', netherlands: 'nl', panama: 'pa',
    peru: 'pe', poland: 'pl', 'puerto rico': 'pr', portugal: 'pt', paraguay: 'py',
    russia: 'ru', sweden: 'se', 'el salvador': 'sv', us: 'us', usa: 'us',
    'united states': 'us', uruguay: 'uy', venezuela: 've',
};

const FLAG_EMOJI = /[\u{1F1E6}-\u{1F1FF}]{2}/gu;

function escapeAttr(value) {
    return String(value).replace(/[&"<>]/g, ch => ({ '&': '&amp;', '"': '&quot;', '<': '&lt;', '>': '&gt;' })[ch]);
}

export function flagCodeFromEmoji(emoji) {
    const points = [...String(emoji || '')].map(ch => ch.codePointAt(0));
    if (points.length !== 2 || points.some(p => p < 0x1F1E6 || p > 0x1F1FF)) return '';
    return points.map(p => String.fromCharCode(p - 0x1F1E6 + 97)).join('');
}

export function regionFlagCode(region) {
    const key = String(region || '').trim().toLowerCase().replace(/[-_]+/g, ' ');
    const code = REGION_CODES[key] || '';
    return AVAILABLE.has(code) ? code : '';
}

export function flagImgHTML(code, label = '', className = '') {
    if (!AVAILABLE.has(code)) return '';
    const alt = label ? escapeAttr(label) : '';
    return `<img class="flag-img${className ? ` ${className}` : ''}" src="${FLAG_DIR}${code}.svg" alt="${alt}"${alt ? ` title="${alt}"` : ' aria-hidden="true"'} draggable="false" decoding="async">`;
}

function flagImgElement(code) {
    const img = document.createElement('img');
    img.className = 'flag-img';
    img.src = `${FLAG_DIR}${code}.svg`;
    img.alt = '';
    img.draggable = false;
    img.decoding = 'async';
    img.dataset.flagEmoji = '1';
    return img;
}

const SKIP_PARENTS = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'INPUT', 'OPTION', 'SELECT', 'TITLE', 'TEMPLATE']);

function replaceFlagsInTextNode(node) {
    const text = node.nodeValue;
    if (!text || !FLAG_EMOJI.test(text)) return;
    FLAG_EMOJI.lastIndex = 0;
    const parent = node.parentNode;
    if (!parent || SKIP_PARENTS.has(parent.nodeName) || parent.isContentEditable) return;
    const fragment = document.createDocumentFragment();
    let last = 0;
    let replaced = false;
    for (const match of text.matchAll(FLAG_EMOJI)) {
        const code = flagCodeFromEmoji(match[0]);
        if (!AVAILABLE.has(code)) continue;
        if (match.index > last) fragment.append(text.slice(last, match.index));
        fragment.append(flagImgElement(code));
        last = match.index + match[0].length;
        replaced = true;
    }
    if (!replaced) return;
    if (last < text.length) fragment.append(text.slice(last));
    parent.replaceChild(fragment, node);
}

function replaceFlagsIn(root) {
    if (root.nodeType === Node.TEXT_NODE) {
        replaceFlagsInTextNode(root);
        return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_FRAGMENT_NODE) return;
    if (SKIP_PARENTS.has(root.nodeName)) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) {
        if (FLAG_EMOJI.test(walker.currentNode.nodeValue)) nodes.push(walker.currentNode);
        FLAG_EMOJI.lastIndex = 0;
    }
    nodes.forEach(replaceFlagsInTextNode);
}

export function installFlagRendering(root = document.body) {
    if (typeof document === 'undefined' || !root || root._flagObserver) return;
    replaceFlagsIn(root);
    const observer = new MutationObserver(records => {
        for (const record of records) {
            if (record.type === 'characterData') replaceFlagsIn(record.target);
            else record.addedNodes.forEach(replaceFlagsIn);
        }
    });
    observer.observe(root, { childList: true, subtree: true, characterData: true });
    root._flagObserver = observer;
}
