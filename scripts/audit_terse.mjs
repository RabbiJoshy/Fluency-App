// Run from the repository root. Outputs JSON; does not alter release data.
// node scripts/audit_terse.mjs [workspace] [baseline-ref]
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import * as current from '../app/js/card-metadata-pills.js';
import { englishProductionCue } from '../app/js/reverse-cues.js';

const workspace = process.argv[2] || '../Fluency-Workspace';
const baselineRef = process.argv[3] || 'a31031c0';
const baselineCode = execFileSync('git', ['show', `${baselineRef}:app/js/card-metadata-pills.js`], { encoding: 'utf8' })
    .replace('./flags.js?v=20260929flags', pathToFileURL(path.resolve('app/js/flags.js')).href);
const baseline = await import(`data:text/javascript;base64,${Buffer.from(baselineCode).toString('base64')}`);
const releases = { pt: 'pt-speech-v24-headway-r3-10000x30-slim', es: 'es-speech-v24-headway-r5-10000x30-slim' };
const words = text => String(text).trim().split(/\s+/u).filter(Boolean).length;
function distribution(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const percentile = p => sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * p))] || 0;
    return { count: values.length, p50: percentile(.5), p90: percentile(.9), p95: percentile(.95), p99: percentile(.99), max: sorted.at(-1) || 0, over84: values.filter(n => n > 84).length };
}
function balanced(text) {
    const stack = [];
    for (const c of text) {
        if ('([{'.includes(c)) stack.push(c);
        else if (')]}'.includes(c) && stack.pop() !== ({ ')': '(', ']': '[', '}': '{' })[c]) return false;
    }
    return stack.length === 0;
}
function show(ui, card, meaning, cue) {
    const gloss = ui.projectWiktionaryGloss(meaning, cue || meaning.translation).display;
    const p = ui.learnerSensePresentation(meaning, true, {
        gloss, ignoreBudget: true, allowInactivePrimary: true,
        cardMeanings: card.meanings, peerMeanings: ui.senseMetadataPeers(meaning, card.meanings, gloss),
        senseCount: card.meanings.length,
    });
    return { gloss: p.gloss, key: p.key.text, note: p.note.available,
        originalRecoverable: Boolean(p.note.original && p.note.original.originalGloss === meaning.translation
            && p.note.original.originalContext === (meaning.context || '')) };

}
const report = { baselineRef, method: 'All released sense rows; canonical example for command reading. Final gloss includes production cues using release conjugation tables. Group layout and renderer redundancy cleanup are assessed separately in browser.', releases: {} };
for (const [language, release] of Object.entries(releases)) {
    const directory = path.join(workspace, 'releases', language, 'speech', release, 'app');
    const cards = JSON.parse(fs.readFileSync(path.join(directory, 'vocabulary.index.json')));
    const conjugationData = JSON.parse(fs.readFileSync(path.join(directory, 'conjugations.json')));
    const rows = [];
    for (const card of cards) for (const meaning of card.meanings || []) {
        const cue = englishProductionCue(card, meaning, null, { conjugationData, activeExample: meaning.canonical_example });
        rows.push({ word: card.word, headword: meaning.headword, source: meaning.source,
            gloss: meaning.translation, context: meaning.context || '',
            projected: current.projectWiktionaryGloss(meaning, meaning.translation).display,
            before: show(baseline, card, meaning), after: show(current, card, meaning),
            finalBefore: show(baseline, card, meaning, cue), finalAfter: show(current, card, meaning, cue) });
    }
    const fields = { storedGloss: r => r.gloss, storedContext: r => r.context, projectedGloss: r => r.projected,
        beforeGloss: r => r.before.gloss, afterGloss: r => r.after.gloss, beforeKey: r => r.before.key, afterKey: r => r.after.key,
        finalBeforeGloss: r => r.finalBefore.gloss, finalAfterGloss: r => r.finalAfter.gloss };
    const metrics = Object.fromEntries(Object.entries(fields).map(([name, select]) => [name, {
        characters: distribution(rows.map(r => select(r).length)), words: distribution(rows.map(r => words(select(r)))) } ]));
    const longest = field => [...new Map(rows.map(r => [r[field], r])).values()]
        .sort((a, b) => b[field].length - a[field].length || a[field].localeCompare(b[field], 'en')).slice(0, 30)
        .map(r => ({ ...r, outcome: !balanced(r.gloss) ? 'malformed upstream' : r.after.gloss !== r.gloss || r.after.key !== r.context ? 'projected' : 'retained' }));
    report.releases[language] = { release, cards: cards.length, senseRows: rows.length, metrics,
        providers: Object.fromEntries([...new Set(rows.map(r => r.source))].map(source => [source, rows.filter(r => r.source === source).length])),
        newlyUnbalancedGlosses: rows.filter(r => balanced(r.gloss) && !balanced(r.after.gloss)),
        longestGlosses: longest('gloss'), longestContexts: longest('context') };
}
console.log(JSON.stringify(report, null, 2));
