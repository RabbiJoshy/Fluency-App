// The app's own display rules, applied to release cards for the UNISON audit.
//
// Runs the same code the app runs, sliced from its files rather than copied:
// the empty-translation filter and positional example attachment (vocab.js),
// the es function-word overlay (grammar-cards.js), the 10% floor and shown
// shares (vocab.js `// low-share-pure`), and the expression-child split
// (flashcards.js). Row grouping and fold-together are not reproduced here;
// cards.py approximates them and the audit confirms display findings live.
//
// stdin:  {"language": "es", "items": [{card_id, word, meanings, ex_m, unused_menu_senses}]}
// stdout: [{card_id, dropped, drift, main: [...], rare: [...]}]
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const { applyGrammarCardOverlay } = await import(pathToFileURL(path.join(ROOT, 'app/js/grammar-cards.js')));

function slice(file, start, end) {
    const text = fs.readFileSync(path.join(ROOT, file), 'utf8');
    const a = text.indexOf(start);
    const b = a < 0 ? -1 : text.indexOf(end, a);
    if (a < 0 || b < 0) throw new Error(`display marker missing in ${file}: ${start} .. ${end}`);
    return text.slice(a, b);
}

vm.runInThisContext([
    slice('app/js/vocab.js', 'function normalizeLemmaToken', 'function lemmaHeadwordsOf'),
    'globalThis.isExpressionSenseForLemma = isExpressionSenseForLemma;',
    slice('app/js/vocab.js', 'function cleanHeadwordToken', '// /lemma-merge-pure'),
    slice('app/js/vocab.js', '// low-share-pure', '// /low-share-pure'),
    slice('app/js/flashcards.js', 'function meaningSourceAdapter', 'function cardHasOnlyInvariantMwes'),
    'globalThis.__unison = { finishCardMeanings, isExpressionChildMeaning, cardHasOnlyExpressionMeanings, detectSplitCardTuples };',
].join('\n'));
const { finishCardMeanings, isExpressionChildMeaning, cardHasOnlyExpressionMeanings, detectSplitCardTuples } = globalThis.__unison;

const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const exampleIds = m => (m.allExamples || m.examples || []).map(e => e.i).filter(Boolean);

const out = input.items.map(item => {
    // vocab.js drops meanings without a translation, then attaches example
    // buckets by the *filtered* position. Record both, so a shift is visible.
    const raw = item.meanings || [];
    const kept = [];
    raw.forEach((m, rawIndex) => { if (m.translation && String(m.translation).trim()) kept.push({ ...m, _rawIndex: rawIndex }); });
    const dropped = raw.length - kept.length;
    const drift = kept.some((m, i) => m._rawIndex !== i);
    kept.forEach((m, i) => { m.examples = (item.ex_m || [])[i] || []; });

    const card = { word: item.word, meanings: kept, unused_menu_senses: item.unused_menu_senses || [] };
    if (input.language === 'es') applyGrammarCardOverlay(card, 'es');
    // A split surface is studied as two cards (vaya -> ir | interjection).
    const tuples = detectSplitCardTuples(card, input.language);
    const split = tuples ? {
        kind: tuples.kind,
        cards: [tuples.tuple1, tuples.tuple2].map(t => ({
            label: t.label,
            refs: t.meanings.map(m => m.source_reference),
        })),
    } : null;

    const meanings = card.meanings.map(m => ({
        pos: m.pos,
        meaning: m.translation,
        percentage: parseFloat(m.display_frequency ?? m.frequency),
        source: m.source,
        senseId: m.sense_id,
        context: m.context,
        headword: m.headword,
        metadata: m.metadata,
        allExamples: m.examples || [],
        _ref: m.source_reference,
        _rawIndex: m._rawIndex,
        _merged: m._mergedSenseIds || null,
    }));
    const done = finishCardMeanings(card, meanings);
    const shown = { word: item.word, targetWord: item.word, displaySurface: item.word, meanings: done.meanings };
    const onlyExpressions = cardHasOnlyExpressionMeanings(shown);
    const pack = m => ({
        ref: m._ref || null,
        raw_index: m._rawIndex ?? null,
        merged_sense_ids: m._merged,
        sense_id: m.senseId || null,
        pos: m.pos,
        headword: m.headword || '',
        translation: m.meaning || '',
        context: m.context || '',
        source: m.source || '',
        percentage: m.percentage,
        shown_share: m.shownShare ?? null,
        low_share: Boolean(m.lowShare),
        unassigned: Boolean(m.unassigned),
        expression_child: isExpressionChildMeaning(m, shown) && !onlyExpressions,
        example_ids: exampleIds(m),
    });
    return {
        card_id: item.card_id,
        dropped,
        drift,
        grammar_card: Boolean(card._grammarCard),
        split,
        main: done.meanings.map(pack),
        rare: done.unusedMenuSenses.map(pack),
    };
});
process.stdout.write(JSON.stringify(out));
