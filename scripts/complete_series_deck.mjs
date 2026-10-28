import fs from 'node:fs';
import { completeSeriesVocabulary } from '../app/js/series-vocabulary.js';
const root = new URL('../', import.meta.url);
const deck = JSON.parse(fs.readFileSync(0, 'utf8'));
const assets = JSON.parse(fs.readFileSync(new URL('app/turbo/turbo_assets.json', root), 'utf8'));
const extra50k = JSON.parse(fs.readFileSync(new URL('app/turbo/es_50k_data.json', root), 'utf8'));
const lexicon = JSON.parse(fs.readFileSync(process.argv[2] || new URL('app/data/series/spanish-lexicon.json', root), 'utf8'));
process.stdout.write(JSON.stringify(completeSeriesVocabulary(deck, { assets, extra50k, lexicon })));
