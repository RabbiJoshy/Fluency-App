// Measure the English the app writes on conjugated verb rows, across a whole deck.
//
// Every VERB/AUX sense row of every card is run through englishProductionCue
// (app/js/reverse-cues.js) with the release's own conjugations.json, the way
// the card back does, without an example sentence. Each row gets a status
// (why it is or is not inflected) and the inflected ones are checked for the
// error classes INFLECT fixed. With --baseline, a second copy of
// reverse-cues.js (e.g. from `git show <sha>:app/js/reverse-cues.js`) is run
// too and the rows that changed, gained or lost English are counted.
//
//   node research/inflect/measure.mjs \
//     --index <release>/app/vocabulary.index.json \
//     --conjugations <release>/app/conjugations.json \
//     [--sentences <release>/app/vocabulary.examples.shards] \
//     [--baseline /path/to/old-reverse-cues.mjs] [--out rows.jsonl] [--examples 8]
//
// --sentences attaches each card's example sentences, as the app does once a
// set is loaded; whether a form also shows as a command is decided from them.
//
// Writes nothing unless --out is given; outputs belong in the scratchpad or
// the workspace, not in git.

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, all) => {
    if (value.startsWith('--')) pairs.push([value.slice(2), all[index + 1]]);
    return pairs;
}, []));
if (!args.index || !args.conjugations) {
    console.error('usage: measure.mjs --index <vocabulary.index.json> --conjugations <conjugations.json> [--baseline <reverse-cues.js>] [--out <rows.jsonl>]');
    process.exit(2);
}

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const current = await import(pathToFileURL(path.join(repoRoot, 'app', 'js', 'reverse-cues.js')).href);
const baseline = args.baseline ? await import(pathToFileURL(path.resolve(args.baseline)).href) : null;
const exampleCount = Number(args.examples ?? 8);

const rows = JSON.parse(fs.readFileSync(args.index, 'utf8'));
const conjugations = JSON.parse(fs.readFileSync(args.conjugations, 'utf8'));
const fold = value => String(value || '').normalize('NFC').toLocaleLowerCase().trim();
const tables = new Map(Object.entries(conjugations).map(([lemma, entry]) => [fold(lemma), entry]));
const sentencesByCard = new Map();
if (args.sentences) {
    for (const name of fs.readdirSync(args.sentences).filter(file => file.endsWith('.json'))) {
        const shard = JSON.parse(fs.readFileSync(path.join(args.sentences, name), 'utf8'));
        for (const [id, record] of Object.entries(shard)) sentencesByCard.set(id, record?.m || []);
    }
}

function statusOf(row, meaning, cue) {
    if (fold(row.word) === fold(meaning.headword)) return 'dictionary_form_card';
    if (cue) return 'inflected';
    const entry = tables.get(fold(meaning.headword));
    if (!entry) return 'verb_missing_from_table';
    if (!String(meaning.translation || '').trim().startsWith('to ')) return 'gloss_not_infinitive';
    const cells = Object.values(entry.tenses || {}).flat();
    const matches = cells.some(form => current.conjugationCellMatches?.(form, row.word) ?? fold(form) === fold(row.word))
        || [entry.gerund, entry.past_participle].some(form => fold(form) === fold(row.word));
    return matches ? 'other' : 'word_not_in_table';
}

// The error classes INFLECT removed; a non-zero count is a regression.
const ERROR_CLASSES = {
    // Allowed when the card's sentences use the command (--sentences); without
    // them it must be 0.
    command_listed_with_statement: cue => cue.includes('!') && cue.includes(' / '),
    stative_progressive: cue => /\b(?:was|were) (?:being|having|knowing|wanting|needing|liking|loving|believing|seeming|meaning|wishing)\b/u.test(cue),
    broken_brackets: cue => (cue.match(/\(/gu) || []).length !== (cue.match(/\)/gu) || []).length,
    regular_ending_on_irregular: cue => /\b(?:meaned|lended|beated|hurted|hited|runing|planed|stoped|upseted|foretelled|doed|maked|goed|thinked|bringed|catched|teached|buyed|feeled|keeped|leaved|payed|sayed|sended|spended|builded|knowed|throwed|growed|drived|rided|writed|winned|forgeted|choosed|breaked|speaked|stealed|weared|sleeped|begining)\b/u.test(cue),
    gloss_note_kept: cue => /;\s*(?:forms? the|formula|introduces|usually|especially)\b/u.test(cue),
};

const counts = {};
const errors = Object.fromEntries(Object.keys(ERROR_CLASSES).map(name => [name, []]));
const delta = { changed: [], gained: [], lost: [] };
const out = [];
const bump = key => { counts[key] = (counts[key] || 0) + 1; };

for (const row of rows) {
    const perMeaning = sentencesByCard.get(row.id) || [];
    const meanings = (row.meanings || []).map((meaning, index) => ({
        ...meaning,
        meaning: meaning.translation,
        allExamples: (perMeaning[index] || []).map(sentence => ({ target: sentence.t, english: sentence.e })),
    }));
    for (const meaning of meanings) {
        const pos = String(meaning.pos || '').toUpperCase();
        if (pos !== 'VERB' && pos !== 'AUX') continue;
        const card = {
            targetWord: row.word, word: row.word, displaySurface: row.word, productionAnswer: row.word,
            representativeSurface: row.word, citationForm: meaning.headword, lemma: meaning.headword, meanings,
        };
        const options = { conjugationData: conjugations };
        const cue = current.englishProductionCue(card, meaning, null, options);
        const status = statusOf(row, meaning, cue);
        bump(status);
        const record = { rank: row.rank, word: row.word, headword: meaning.headword, translation: meaning.translation, status, cue };
        if (cue) {
            for (const [name, test] of Object.entries(ERROR_CLASSES)) if (test(cue)) errors[name].push(record);
        }
        if (baseline) {
            const before = baseline.englishProductionCue(card, meaning, null, options);
            record.before = before;
            if (before && !cue) delta.lost.push(record);
            else if (!before && cue) delta.gained.push(record);
            else if (before !== cue) delta.changed.push(record);
        }
        out.push(record);
    }
}

const pairs = records => new Set(records.map(r => `${r.word}\u0000${r.headword}`)).size;
const show = (records, render) => {
    const seen = new Set();
    for (const r of records) {
        const key = `${r.word}\u0000${r.translation}`;
        if (seen.has(key)) continue;
        seen.add(key);
        console.log(`    ${render(r)}`);
        if (seen.size >= exampleCount) break;
    }
};

console.log(`verb rows by status: ${JSON.stringify(counts)}`);
const inflectable = out.filter(r => r.status !== 'dictionary_form_card');
console.log(`card/verb pairs inflected: ${pairs(inflectable.filter(r => r.cue))} of ${pairs(inflectable)}`);
for (const status of ['word_not_in_table', 'verb_missing_from_table', 'gloss_not_infinitive']) {
    const records = out.filter(r => r.status === status);
    if (!records.length) continue;
    console.log(`  ${status}: ${records.length} rows, ${pairs(records)} card/verb pairs`);
    show(records, r => `${r.word} [${r.headword}] "${r.translation}"`);
}
console.log('error classes (should be 0):');
for (const [name, records] of Object.entries(errors)) {
    console.log(`  ${name}: ${records.length}`);
    show(records, r => `${r.word} [${r.headword}] "${r.translation}" -> ${r.cue}`);
}
if (baseline) {
    console.log(`against baseline: changed ${delta.changed.length}, gained ${delta.gained.length}, lost ${delta.lost.length}`);
    for (const [name, records] of Object.entries(delta)) {
        if (!records.length) continue;
        console.log(`  ${name}:`);
        show(records, r => `${r.word} [${r.headword}]: ${r.before ?? `(${r.translation})`} -> ${r.cue ?? `(${r.translation})`}`);
    }
}
if (args.out) fs.writeFileSync(args.out, out.map(record => JSON.stringify(record)).join('\n') + '\n');
