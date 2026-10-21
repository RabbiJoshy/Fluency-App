// Offline build adapter for the same recognizer used by browser imports.
import fs from 'node:fs';
const root = new URL('../', import.meta.url);
const source = fs.readFileSync(new URL('app/js/offline-intake.js', root), 'utf8');
const { recognizeOfflineRecords } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const assets = JSON.parse(fs.readFileSync(new URL('app/turbo/turbo_assets.json', root), 'utf8'));
const extra50k = JSON.parse(fs.readFileSync(new URL('app/turbo/es_50k_data.json', root), 'utf8'));
process.stdout.write(JSON.stringify(recognizeOfflineRecords({ records: input.records,
    speechSurfaces: new Set(input.speechSurfaces), assets, extra50k })));
