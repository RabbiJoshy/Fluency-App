const fs=require('fs'),path=require('path');
const {build}=require('/Users/joshuathomasamar/PycharmProjects/Fluency-Next/scripts/build_form_privilege_merges.cjs');
const ROOT='/Users/joshuathomasamar/PycharmProjects/Fluency-Next';
const lang=process.argv[2];
const cfg=JSON.parse(fs.readFileSync(ROOT+'/app/config/config.json','utf8')).languages[lang];
const cur=JSON.parse(fs.readFileSync(ROOT+'/app/'+cfg.mergeExceptionsPath,'utf8')).form_privilege_keys;
const payload=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const rows=JSON.parse(fs.readFileSync(path.resolve(ROOT,'../Fluency-Workspace',cfg.indexPath),'utf8'));
const rank=Object.fromEntries(rows.map(r=>[r.word.toLowerCase(),r.rank]));
const v=build(rows,payload); const now=Object.fromEntries(Object.entries(v).map(([w,x])=>[w,x.lemma]));
const joined={}, left=[];
for (const w of Object.keys(now)) { if (now[w]===cur[w]) continue; if (now[w]) (joined[now[w]] ||= []).push(w); else left.push(`${w}(was ${cur[w]})`); }
const groups=Object.entries(joined).sort((a,b)=>Math.min(...a[1].map(w=>rank[w]))-Math.min(...b[1].map(w=>rank[w])));
const members=k=>Object.keys(now).filter(w=>now[w]===k).sort((a,b)=>rank[a]-rank[b]);
console.log(`${lang}: forms newly sharing a card ${Object.values(joined).flat().length}, in ${groups.length} cards; forms newly split ${left.length}`);
for (const [k,ws] of groups.slice(0,40)) console.log(`  ${k}: +${ws.sort((a,b)=>rank[a]-rank[b]).join(', +')}  => now ${members(k).join(' / ')}`);
if (left.length) console.log('  split:', left.slice(0,20).join(', '));
fs.writeFileSync(process.argv[3]+'.groups.json', JSON.stringify({groups: groups.map(([k,ws])=>({lemma:k, added:ws, now:members(k)})), left}, null, 1));
