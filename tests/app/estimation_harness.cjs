const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ROOT = path.resolve(__dirname, '../..');
function createHarness(overrides = {}) {
    const elements = new Map();
    const buttons = [1, 101, 201].map((start, index) => ({
        dataset: { startRank: String(start), endRank: String(start + 100) },
        click() { context.clickedLevel = index + 1; }
    }));
    const context = {
        console, URL, URLSearchParams, setTimeout, clearTimeout, addEventListener() {},
        localStorage: { getItem() { return null; }, setItem() {} },
        selectedLanguage: 'spanish', activeArtist: null, hideSingleOccurrence: false,
        config: { languages: { spanish: {} } }, levelEstimates: {},
        estimationState: null, currentUser: null,
        releaseUrl: value => value, validateVocabularyIndex: () => {}, trackDataFreshness: () => {},
        saveLevelEstimateToSheet: rank => { context.savedRank = rank; },
        alert: message => { context.lastAlert = message; },
        document: {
            addEventListener() {}, querySelectorAll: () => buttons,
            querySelector: () => buttons[0],
            getElementById(id) {
                if (!elements.has(id)) elements.set(id, { textContent: '', hidden: false, style: {},
                    classList: { add() {}, remove() {}, contains: () => false } });
                return elements.get(id);
            }
        },
        ...overrides
    };
    context.window = context;
    vm.createContext(context);
    context.loadModule = file => {
        let source = fs.readFileSync(path.join(ROOT, 'app/js', file), 'utf8');
        source = source.replace(/^import .*;\s*$/gm, '').replace(/export \{[\s\S]*?\};/g, '');
        if (file === 'ui.js') source = source.replace(/^applyGlobalStudyDefaults\(\);$/m, '');
        vm.runInContext(source, context, { filename: file });
    };
    for (const file of ['vocab.js', 'estimation.js']) context.loadModule(file);
    context.elements = elements;
    context.run = code => vm.runInContext(code, context);
    return context;
}
module.exports = { createHarness, ROOT };
