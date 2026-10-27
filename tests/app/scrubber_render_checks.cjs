// Exercise the updateCard ruler pass with a large deck and mutable study state.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const source = fs.readFileSync('app/js/flashcards.js', 'utf8');
const start = source.indexOf('        const pairOf = i => {');
const end = source.indexOf('        const currentSegment = progressSegments.children[scrubIndex];', start);
assert.ok(start > 0 && end > start);
const render = new Function('progressSegments', 'flashcards', 'scrubIndex', 'segmentCount', 'stats', 'onPhraseCard', source.slice(start, end));
let writes = 0;
const changed = new Set();
const touch = i => { writes++; changed.add(i); };
const segments = Array.from({ length: 1000 }, (_, i) => {
    const classes = new Set();
    return {
        classes,
        classList: { toggle(name, value) { touch(i); value ? classes.add(name) : classes.delete(name); } },
        dataset: new Proxy({}, {
            set(target, key, value) { touch(i); target[key] = value; return true; },
            deleteProperty(target, key) { touch(i); delete target[key]; return true; }
        }),
        attributes: {},
        setAttribute(key, value) { touch(i); this.attributes[key] = value; }
    };
});
const progress = { children: segments };
const cards = segments.map(() => ({}));
cards[10].splitInfo = { index: 1, total: 2 };
cards[11].splitInfo = { index: 2, total: 2 };
const stats = { studied: new Set([10]), cardStats: {} };
const run = (index = 10, phrase = false, count = cards.length) => {
    writes = 0; changed.clear();
    render(progress, cards, index, count, stats, phrase);
    return writes;
};
const initialWrites = run();
assert.equal(changed.size, 1000);
assert.equal(segments[10].attributes['aria-current'], 'step');
assert.ok(segments[11].classes.has('is-pair-active'));
assert.equal(segments[11].dataset.pairPos, 'end');
assert.equal(run(), 0, 'Unchanged example/sense rerenders must perform zero segment writes');
stats.cardStats[10] = { correct: 1 };
run();
assert.deepEqual([...changed], [10], 'Only the graded segment needs DOM writes');
assert.ok(segments[10].classes.has('is-result-correct'));
stats.cardStats[10].incorrect = 1;
run();
assert.equal(segments[10].dataset.result, 'mixed');
assert.ok(segments[10].classes.has('is-result-mixed'));
run(11);
assert.ok(changed.size < 12, 'One-card navigation should only rewrite nearby ruler segments');
assert.equal(segments[10].attributes['aria-current'], 'false');
assert.equal(segments[11].attributes['aria-current'], 'step');
run(11, true);
assert.deepEqual([...changed], [11]);
assert.ok(segments[11].classes.has('is-phrases'));
assert.match(segments[11].attributes['aria-label'], /phrases/);
stats.cardStats = {};
stats.studied.clear();
run(11);
assert.equal(segments[10].dataset.result, 'unanswered');
assert.ok(!segments[10].classes.has('is-visited'));
assert.ok(!segments[11].classes.has('is-phrases'));
delete cards[10].splitInfo;
delete cards[11].splitInfo;
run(11);
assert.equal(segments[10].dataset.pair, undefined);
assert.ok(!segments[11].classes.has('is-pair-active'));
run(11, false, cards.length - 1);
assert.equal(changed.size, 1000, 'Deck count changes must refresh accessible labels');
assert.match(segments[11].attributes['aria-label'], /of 999/);
console.log(`Scrubber rendering checks passed: ${initialWrites} initial DOM operations, 0 on unchanged rerender.`);
