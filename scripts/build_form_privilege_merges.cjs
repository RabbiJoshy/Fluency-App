// Decision 0033: precompute which forms share a word's card, with the app's
// own rule (vocab.js formPrivilegeVerdicts), into each configured Speech
// merge overlay. Writes a new overlay file (-fp<rule version>) and repoints config; the
// estimation pool must then be rebuilt (scripts/build_estimation_pools.cjs).
//
// Usage: node scripts/build_form_privilege_merges.cjs [language ...]
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
const RULE = vm.runInContext('FORM_PRIVILEGE_RULE', context);
const verdictsFor = vm.runInContext('formPrivilegeVerdicts', context);

function build(rows, payload) {
    const contractions = new Set(payload.contractions || []);
    for (const row of rows) {
        const word = context.normalizeLemmaToken(row.word);
        if (payload.noun_verdicts?.[word]) row.noun_merge = payload.noun_verdicts[word];
        row.is_contraction = contractions.has(word) || row.is_contraction;
    }
    return verdictsFor(rows);
}

if (require.main === module) {
    const configPath = path.join(ROOT, 'app/config/config.json');
    let configText = fs.readFileSync(configPath, 'utf8');
    const config = JSON.parse(configText);
    const wanted = new Set(process.argv.slice(2));
    for (const [language, cfg] of Object.entries(config.languages)) {
        if ((wanted.size && !wanted.has(language)) || !cfg.indexPath || !cfg.mergeExceptionsPath) continue;
        const payload = JSON.parse(fs.readFileSync(path.join(ROOT, 'app', cfg.mergeExceptionsPath), 'utf8'));
        if (!payload.release_id || !cfg.indexPath.includes(`/${payload.release_id}/`))
            throw new Error(`${language}: merge metadata must match the configured release`);
        const rows = JSON.parse(fs.readFileSync(path.resolve(ROOT, '../Fluency-Workspace', cfg.indexPath), 'utf8'));
        const verdicts = build(rows, payload);
        payload.form_privilege_rule = RULE;
        payload.form_privilege_keys = Object.fromEntries(Object.entries(verdicts).map(([w, v]) => [w, v.lemma]));
        payload.form_privilege_reasons = Object.fromEntries(Object.entries(verdicts)
            .filter(([, v]) => !v.lemma).map(([w, v]) => [w, v.reasons]));
        payload.form_privilege_source_sha256 = crypto.createHash('sha256').update(source).digest('hex');
        // Cold rows read the same verdict through their merge key.
        payload.keys = {...payload.keys, ...payload.form_privilege_keys};
        const swap = (key, from) => {
            const next = from.replace(/(?:-fp\d+)?\.json$/, `-fp${RULE.split('/v')[1]}.json`);
            configText = configText.replace(JSON.stringify(from), JSON.stringify(next));
            cfg[key] = next;
            return next;
        };
        const out = swap('mergeExceptionsPath', cfg.mergeExceptionsPath);
        fs.writeFileSync(path.join(ROOT, 'app', out), JSON.stringify(payload) + '\n');
        if (cfg.estimationPoolPath) swap('estimationPoolPath', cfg.estimationPoolPath);
        const shared = Object.values(verdicts).filter(v => v.lemma).length;
        console.log(`${language}: ${shared} forms share a card, ${rows.length - shared} keep their own -> ${out}`);
    }
    fs.writeFileSync(configPath, configText);
}
module.exports = {build};
