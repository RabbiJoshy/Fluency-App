/* Read-only comparison; does not alter app rules or immutable releases.
 * Run from repository root: node scripts/audit_attested_merge_rules.cjs
 */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const workspace = path.resolve(root, '../Fluency-Workspace');
const output = path.join(root, 'docs/audits/attested-merge-comparison');
const rawOutput = path.join(workspace, 'audits/attested-merge-comparison/2026-10-22');
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const source = fs.readFileSync(path.join(root, 'app/js/vocab.js'), 'utf8');
const block = name => source.slice(source.indexOf(`// ${name}\n`), source.indexOf(`// /${name}`));
const context = {console};
context.globalThis = context; context.window = context;
vm.createContext(context);
vm.runInContext(block('lemma-merge-pure') + '\n' + block('low-share-pure') + `
globalThis.auditHelpers = {finishCardMeanings, lemmaSenseDedupeKey, isShownSense};
globalThis.isExpressionSenseForLemma = isExpressionSenseForLemma;
`, context);
const {finishCardMeanings, lemmaSenseDedupeKey, isShownSense} = context.auditHelpers;
const config = read(path.join(root, 'app/config/config.json'));
const signature = xs => JSON.stringify([...new Set(xs)].sort());
const combinations = n => n * (n - 1) / 2;
const partition = (rows, field) => {
  const groups = new Map();
  for (const row of rows) {
    // Empty evidence never establishes equivalence.
    const key = row[field].length ? signature(row[field]) : `empty:${row.word}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }
  return [...groups.values()];
};
const results = {};
for (const language of ['portuguese', 'spanish']) {
  const cfg = config.languages[language];
  const rows = read(path.join(workspace, cfg.indexPath));
  const overlayPath = process.argv.includes('--original-eligibility')
    ? cfg.mergeExceptionsPath.replace(/-visible-v1\.json$/, '.json') : cfg.mergeExceptionsPath;
  const overlay = read(path.join(root, 'app', overlayPath));
  if (overlay.release_id !== cfg.indexPath.split('/')[3]) throw new Error('Overlay release mismatch');
  const groups = new Map();
  const analysed = rows.map(row => {
    const counts = row.wsd_distribution?.published_leaf_counts;
    const meanings = (row.meanings || []).map(m => ({...m,
      meaning: m.translation, percentage: parseFloat(m.display_frequency ?? m.frequency),
      canonicalExample: m.canonical_example, _key: lemmaSenseDedupeKey(m),
      _count: counts ? Number(counts[m.sense_id] || 0) : null,
    }));
    const attested = meanings.filter(m => !m.unassigned && !m.exampleOnly
      && m.assignment_method !== 'unassigned' && Number(m.percentage) > 0
      && (!counts || m._count > 0) && isShownSense(m, row));
    const finished = finishCardMeanings(row, meanings);
    const visible = finished.meanings.filter(m => attested.some(a => a._key === m._key));
    const record = {word: row.word, rank: row.rank, id: row.id,
      lemma: overlay.keys[row.word] || '',
      verb: attested.some(m => /^(verb|v|vb)$/i.test(m.pos || '')),
      all: [...new Set(attested.map(m => m._key))],
      visible: [...new Set(visible.map(m => m._key))],
      senses: attested.map(m => ({key:m._key, gloss:m.translation, context:m.context || '',
        count:m._count, raw_frequency:Number(m.frequency),
        visible:visible.some(v => v._key === m._key), sense_id:m.sense_id})),
    };
    if (record.lemma) {
      if (!groups.has(record.lemma)) groups.set(record.lemma, []);
      groups.get(record.lemma).push(record);
    }
    return record;
  });
  const eligibleGroups = [...groups.entries()].filter(([, rs]) => rs.length > 1);
  const stats = {surfaces:rows.length, eligible_surfaces:0, baseline_groups:0,
    baseline_cards:rows.length, all_cards:rows.length, visible_cards:rows.length,
    all_pairs:0, visible_pairs:0, visible_only_pairs:0, all_only_pairs:0,
    visible_only_pairs_all_extras_le_2:0, visible_only_pairs_any_extra_ge_3:0,
    all_or_nothing_all_cards:rows.length, all_or_nothing_visible_cards:rows.length};
  const disagreements = [];
  const groupDetails = [];
  for (const [lemma, rs] of eligibleGroups) {
    const a = partition(rs,'all'), v = partition(rs,'visible');
    stats.eligible_surfaces += rs.length; stats.baseline_groups++;
    stats.baseline_cards -= rs.length - 1;
    stats.all_cards -= rs.length - a.length;
    stats.visible_cards -= rs.length - v.length;
    stats.all_pairs += a.reduce((n,g) => n + combinations(g.length),0);
    stats.visible_pairs += v.reduce((n,g) => n + combinations(g.length),0);
    if (a.length === 1) stats.all_or_nothing_all_cards -= rs.length - 1;
    if (v.length === 1) stats.all_or_nothing_visible_cards -= rs.length - 1;
    for (let i=0;i<rs.length;i++) for(let j=i+1;j<rs.length;j++) {
      const x=rs[i], y=rs[j];
      const sameAll=x.all.length>0 && signature(x.all)===signature(y.all);
      const sameVisible=x.visible.length>0 && signature(x.visible)===signature(y.visible);
      if (sameAll===sameVisible) continue;
      const direction=sameVisible?'visible_only':'all_only';
      stats[direction+'_pairs']++;
      const extraX=x.senses.filter(s=>!y.all.includes(s.key));
      const extraY=y.senses.filter(s=>!x.all.includes(s.key));
      const extras=[...extraX,...extraY];
      if(sameVisible && extras.length && extras.every(s=>s.count!==null && s.count<=2))
        stats.visible_only_pairs_all_extras_le_2++;
      if(sameVisible && extras.some(s=>s.count>=3)) stats.visible_only_pairs_any_extra_ge_3++;
      disagreements.push({lemma,direction,rank:Math.max(x.rank,y.rank),
        x,y,extraX,extraY});
    }
    groupDetails.push({lemma,forms:rs.map(r=>r.word),
      all_partitions:a.map(g=>g.map(r=>r.word)),visible_partitions:v.map(g=>g.map(r=>r.word))});
  }
  disagreements.sort((a,b)=>a.rank-b.rank);
  // Identity is per source reference, never the per-surface sense_id.
  if (analysed.some(r => r.senses.some(s => !s.key.startsWith('ref:'))))
    throw new Error('Unexpected lexical sense without source reference');
  results[language]={release:cfg.indexPath,
    release_index_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(workspace,cfg.indexPath))).digest('hex'),
    display_source_sha256:crypto.createHash('sha256').update(source).digest('hex'),
    stats,groups:groupDetails,records:analysed.filter(r=>r.lemma),
    disagreements:disagreements.map(d=>({lemma:d.lemma,direction:d.direction,rank:d.rank,
      x:d.x.word,y:d.y.word,extraX:d.extraX,extraY:d.extraY})),
    haver:analysed.filter(r=>['há','havia','haver','hei','hás','hão','havemos','haverá','haveria','houve'].includes(r.word))};
  console.log(language,JSON.stringify(stats));
}
fs.mkdirSync(output,{recursive:true});
fs.mkdirSync(rawOutput,{recursive:true});
fs.writeFileSync(path.join(rawOutput,'comparison.json'),JSON.stringify(results,null,2)+'\n');
fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify(Object.fromEntries(
  Object.entries(results).map(([language,{records,disagreements,...summary}])=>[language,summary])
),null,2)+'\n');
