// Use the app's display code for release-bound cold/loaded merge equivalence.
// stdin: full release rows; stdout: {surface: visible-sense signature}.
// --refresh-configured [language ...]: supplement configured immutable decks.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const ROOT = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(ROOT, 'app/js/vocab.js'), 'utf8');
const context = {console};
context.globalThis = context; context.window = context;
vm.createContext(context);
for (const name of ['lemma-merge-pure', 'low-share-pure']) {
    const start = source.indexOf(`// ${name}\n`), end = source.indexOf(`// /${name}`);
    if (start < 0 || end < start) throw new Error(`Missing app helper block: ${name}`);
    vm.runInContext(source.slice(start, end), context);
}

function signatures(rows) {
    return Object.fromEntries(rows.filter(row => row.word).map(row => [
        context.normalizeLemmaToken(row.word), context.visibleSenseMergeSignature(row)
    ]));
}

if (require.main === module) {
    if (process.argv[2] === '--refresh-configured') {
        const configPath = path.join(ROOT, 'app/config/config.json');
        let configText = fs.readFileSync(configPath, 'utf8');
        const config = JSON.parse(configText);
        const wanted = new Set(process.argv.slice(3));
        for (const [language, cfg] of Object.entries(config.languages)) {
            if ((wanted.size && !wanted.has(language)) || !cfg.indexPath || !cfg.mergeExceptionsPath) continue;
            const index = path.resolve(ROOT, '../Fluency-Workspace', cfg.indexPath);
            const payload = JSON.parse(fs.readFileSync(path.join(ROOT, 'app', cfg.mergeExceptionsPath), 'utf8'));
            if (!payload.release_id || !cfg.indexPath.includes(`/${payload.release_id}/`))
                throw new Error(`${language}: merge metadata must match the configured release`);
            const rows = JSON.parse(fs.readFileSync(index, 'utf8'));
            const contractions = new Set(payload.contractions || []);
            // Retain prior exclusions, and withdraw obsolete approvals when
            // the current release exposes an additional dictionary headword.
            for (const row of rows) {
                const word = context.normalizeLemmaToken(row.word);
                const eligible = context.lemmaGroupKey({...row,
                    noun_merge:payload.noun_verdicts?.[word] || row.noun_merge,
                    is_contraction:contractions.has(word) || row.is_contraction});
                if (payload.keys?.[word] && payload.keys[word] !== eligible) payload.keys[word] = '';
            }
            const all = signatures(rows);
            payload.visible_sense_rule = 'visible-senses/v1';
            payload.visible_sense_keys = Object.fromEntries(Object.entries(all).filter(([word]) => payload.keys?.[word]));
            payload.visible_sense_source_sha256 = crypto.createHash('sha256').update(source).digest('hex');
            const oldMergePath = cfg.mergeExceptionsPath;
            cfg.mergeExceptionsPath = oldMergePath.replace(/(?:-visible-v1)?\.json$/, '-visible-v1.json');
            configText = configText.replace(JSON.stringify(oldMergePath), JSON.stringify(cfg.mergeExceptionsPath));
            fs.writeFileSync(path.join(ROOT, 'app', cfg.mergeExceptionsPath), JSON.stringify(payload) + '\n');
            if (cfg.estimationPoolPath) {
                const oldPoolPath = cfg.estimationPoolPath;
                cfg.estimationPoolPath = cfg.estimationPoolPath.replace(/(?:-visible-v1)?\.json$/, '-visible-v1.json');
                configText = configText.replace(JSON.stringify(oldPoolPath), JSON.stringify(cfg.estimationPoolPath));
            }
            console.log(`${language}: ${Object.keys(payload.visible_sense_keys).length} visible sense signatures`);
        }
        fs.writeFileSync(configPath, configText);
    } else {
        process.stdout.write(JSON.stringify(signatures(JSON.parse(fs.readFileSync(0, 'utf8')))));
    }
}
module.exports = {signatures};
