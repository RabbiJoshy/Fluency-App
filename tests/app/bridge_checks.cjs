const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = require('node:path').resolve(__dirname, '../..');
function load(context, file) {
    const source = fs.readFileSync(`${root}/${file}`, 'utf8').replace(/^import[\s\S]*?;[ \t]*$/mg, '').replace(/^export /mg, '');
    vm.runInContext(`(()=>{${source}\n})()`, context, {filename: file});
}
function harness() {
    const values = new Map(), events = {}, writes = [];
    const c = {console, Date, Set, Map, Promise, URL, setTimeout, clearTimeout,
        currentUser: {initials: 'ONE'}, selectedLanguage: 'french', activeArtist: null,
        progressData: {}, itemProgressData: {}, spacedRepetitionEnabled: true, __progressEpoch: 0,
        config: {languages: {spanish: {indexPath: 'releases/es/speech/es-test/app/index.json'}}},
        localStorage: {getItem: key => values.get(key) ?? null, setItem: (key,value) => values.set(key,value)},
        document: {readyState: 'loading', addEventListener() {}, getElementById: () => null, querySelector: () => null},
        addEventListener: (name, fn) => (events[name] ||= []).push(fn),
        dispatchEvent: event => (events[event.type] || []).forEach(fn => fn(event)),
        CustomEvent: class {constructor(type, options) {this.type = type; Object.assign(this, options);}},
        getIsolatedSyncUser: user => `stg_${user}`,
        sendOrQueue: async payload => {writes.push(payload);},
    };
    c.window = c; c.globalThis = c;
    vm.createContext(c);
    c.values = values; c.writes = writes;
    return c;
}
(async () => {
    const p = harness();
    p.values.set('fluency_known_languages_v1', JSON.stringify(['en','pl']));
    load(p, 'app/js/language-profile.js');
    assert.deepEqual(Array.from(p.readLanguageProfile().languages), ['en','pl']);
    assert(p.readLanguageProfile().confirmed);
    p.saveLanguageProfile([]);
    assert.equal(p.writes[0].user, 'stg_ONE', 'staging profile writes must be isolated');
    assert(p.readLanguageProfile().confirmed);
    assert.equal(p.readLanguageProfile().languages.length, 0);
    p.currentUser = {initials: 'TWO'};
    assert.equal(p.readLanguageProfile().confirmed, false, 'another account must not inherit ONE');
    p.applyRemoteLanguageProfile([{metaKey:'language-profile',metaId:'profile',value:JSON.stringify({languages:['fr'],confirmed:true,updatedAt:Date.now()})}],{full:true});
    assert.deepEqual(Array.from(p.readLanguageProfile().languages), ['fr']);
    p.saveLanguageProfile(['pl','es']);
    p.applyRemoteLanguageProfile([{metaKey:'language-profile',metaId:'profile',value:JSON.stringify({languages:['en'],confirmed:true,updatedAt:1})}],{full:true});
    assert.deepEqual(Array.from(p.readLanguageProfile().languages), ['pl','es'], 'stale sync cannot erase a new local edit');
    p.currentUser = {isGuest:true}; p.saveLanguageProfile(['pl']);
    p.currentUser = {initials:'THREE'};
    p.applyRemoteLanguageProfile([], {full:true});
    assert.deepEqual(Array.from(p.readLanguageProfile().languages), ['pl'], 'guest profile carries into a new account');

    const f = harness();
    load(f, 'app/js/fast-track-preferences.js');
    vm.runInContext(fs.readFileSync(`${root}/app/js/fast-track-preferences.js`, 'utf8').replace(/^import .*$/mg,'').replace(/^export /mg,''), f);
    f.saveFastTrack('spanish', {enabled:true, bridge:true});
    assert.equal(f.writes[0].user,'stg_ONE','BRIDGE preference writes must use staging identity too');

    const policy = JSON.parse(fs.readFileSync(`${root}/app/config/smart-skip-pairs.json`,'utf8'));
    const pairs = harness();
    vm.runInContext(fs.readFileSync(`${root}/app/js/smart-skip-pairs.js`,'utf8').replace(/^export /mg,''), pairs);
    const sources = pairs.relevantSources(policy, 'es');
    assert(sources.includes('it') && !sources.includes('ja'), 'only predefined useful pairs may appear');
    const choices = pairs.pairChoices(policy,'es',['en','it','ja'],['en','pt','fr']);
    assert.equal(JSON.stringify(choices),JSON.stringify([{code:'en',ready:true},{code:'it',ready:false}]));
    // Older saved custom labels remain readable even though the picker is now fixed.
    const other = {code:'x-legacy',label:'My community language'};
    p.saveLanguageProfile(['ja',other.code],{[other.code]:other.label});
    assert(p.readLanguageProfile().languages.includes('ja'));
    assert.equal(p.readLanguageProfile().labels[other.code],'My community language');

    const h = harness();
    let identity = fs.readFileSync(`${root}/app/js/progress-identity.js`,'utf8').replace(/^export /mg,'');
    vm.runInContext(identity, h);
    load(h, 'app/js/progress.js');
    load(h, 'app/js/knowledge.js');
    h.readFastTrack = () => ({enabled:true, bridge:true, updatedAt:1});
    h.activeKnownLanguages = () => [];
    h.cognateSenseAlternatives = text => new Set(text.toLowerCase().split(/[,;]/).map(x=>x.trim().replace(/^to /,'')));
    const sense = (translation,id='sense-bank') => ({pos:'NOUN',headword:'banco',translation,sense_id:id});
    const bank = {fullId:'es0bank',targetWord:'banco',language:'spanish',verb:false,meanings:[sense('bank')]};
    const bench = {...bank,meanings:[sense('bench','sense-bench')]};
    const bundle = {schema:'bridge/v1',language:'fr',targetLanguage:'french',built_from_release_id:'fr-test',
        source_releases:{es:'es-test'}, sources:{es:{banco:[bank,bench]}},verb_compatible:{},targets:{
            banque:{requirements:[[['es','banco','bank',.9]]],meanings:[{headword:'banque',translation:'bank',verb:false}]},
            banc:{requirements:[[['es','banco','bank',.9]],[['es','banco','bench',.9]]],meanings:[{headword:'banc',translation:'bank',verb:false},{headword:'banc',translation:'bench',verb:false}]}
        }};
    h.fetch = async () => ({ok:true,json:async()=>bundle});
    load(h,'app/js/bridge.js');
    await h.loadBridge({routeCode:'fr',bridgePath:'fr.json',indexPath:'releases/fr/speech/fr-test/app/index.json'});
    const target = {word:'banque',meanings:[]};
    assert.equal(h.bridgeVerdict(target),null,'unseen source does not qualify');
    const bankItem = h.getCardKnowledgeItems(bank)[0];
    h.itemProgressData[bankItem.itemId] = {correct:1,lastCorrect:'2026-10-01T00:00:00Z'};
    h.__progressEpoch++;
    assert(h.bridgeVerdict(target), 'one known matching sense qualifies even if its parent is unseen');
    bank.progressEligible = false; h.__progressEpoch++;
    assert.equal(h.bridgeVerdict(target),null,'unused dictionary senses do not inherit whole-card progress');
    bank.progressEligible = true; h.__progressEpoch++;
    assert.equal(h.bridgeVerdict({word:'banc',meanings:[]}),null,'an unknown second sense keeps the card');
    h.progressData.es1historic = {word:'banco',language:'spanish',correct:2,lastCorrect:'2026-10-02T00:00:00Z'};
    h.__progressEpoch++;
    assert(h.bridgeVerdict({word:'banc',meanings:[]}), 'historical source-language IDs inherit whole-card knowledge');
    const benchItem = h.getCardKnowledgeItems(bench)[0];
    h.itemProgressData[benchItem.itemId] = {wrong:1,lastWrong:'2026-10-03T00:00:00Z'};
    h.__progressEpoch++;
    assert.equal(h.bridgeVerdict({word:'banc',meanings:[]}),null,'explicit sense-level mistakes block transfer');
    h.progressData.es1historic.lastCorrect = '2026-10-04T00:00:00Z'; h.__progressEpoch++;
    assert.equal(h.bridgeVerdict({word:'banc',meanings:[]}),null,'a general yes cannot erase an explicit sense mistake');
    assert.equal(h.bridgeVerdict({...target,meanings:[{headword:'banque',translation:'bank'},{headword:'banque',translation:'school of fish'}]}),null,'additional merged senses must not be lost');
    const before = JSON.stringify([h.progressData,h.itemProgressData]);
    h.bridgeVerdict(target); assert.equal(JSON.stringify([h.progressData,h.itemProgressData]),before);
    // Split-card knowledge never applies to a different headword or POS.
    h.progressData['es0bank::split::banco_NOUN'] = {word:'banco',language:'spanish',wrong:1,lastWrong:'2026-10-05T00:00:00Z'};
    h.__progressEpoch++;
    assert.equal(h.bridgeVerdict(target),null,'a matching split-card mistake overrides general source knowledge');
    delete h.progressData['es0bank::split::banco_NOUN']; h.__progressEpoch++;
    h.readFastTrack = () => ({enabled:false,bridge:true,updatedAt:2});
    assert.equal(h.bridgeVerdict(target),null,'master switch off disables BRIDGE');
    h.activeKnownLanguages = () => ['es'];
    assert(h.bridgeVerdict(target,{useProfile:true}),'whole-language declaration remains a separate evidence source');
    h.activeKnownLanguages = () => [];
    h.readFastTrack = () => ({enabled:true,bridge:true,updatedAt:3});
    const finite = ['finite','first-person','singular','present','indicative','',''];
    const infinitive = ['infinitive'];
    const verb = {fullId:'es0informar',targetWord:'informar',language:'spanish',verb:true,formSignatures:[infinitive],meanings:[{headword:'informar',pos:'VERB',translation:'to inform'}]};
    bundle.sources.es.informar = [verb];
    bundle.targets.informo = {requirements:[[['es','informar','inform',.9]]],meanings:[{headword:'informar',translation:'to inform',verb:true,formSignatures:[finite]}]};
    h.progressData.es0informar = {word:'informar',language:'spanish',correct:1,lastCorrect:'2026-10-06T00:00:00Z'}; h.__progressEpoch++;
    assert.equal(h.bridgeVerdict({word:'informo'}),null,'a known infinitive never licenses a finite target');
    bundle.targets.informo.meanings[0].formSignatures = [infinitive];h.__progressEpoch++;
    assert(h.bridgeVerdict({word:'informo'}),'matching declared verb forms qualify');
    await h.loadBridge({routeCode:'fr',bridgePath:'wrong.json',indexPath:'releases/fr/speech/other-release/app/index.json'});
    assert.equal(h.bridgeVerdict(target),null,'release mismatch must retain cards');
    // Evaluate real shipped assets with synthetic known source progress. This
    // checks the full build/runtime seam, without touching a user's account.
    h.config = JSON.parse(fs.readFileSync(`${root}/app/config/config.json`, 'utf8'));
    for (const [code, language] of [['fr','french'],['es','spanish'],['pt','portuguese']]) {
        const real = JSON.parse(fs.readFileSync(`${root}/app/data/bridge/${code}.json`, 'utf8'));
        assert(Object.keys(real.thresholds).every(source=>policy.targets[code].includes(source)), 'bundles may only contain approved pairs');
        h.selectedLanguage = language;
        h.progressData = {}; h.itemProgressData = {}; h.__progressEpoch++;
        for (const words of Object.values(real.sources)) for (const cards of Object.values(words)) for (const card of cards)
            h.progressData[card.fullId] = {word:card.targetWord,language:card.language,correct:1,lastCorrect:'2026-10-12T10:00:00Z'};
        h.fetch = async () => ({ok:true,json:async()=>real});
        await h.loadBridge(h.config.languages[language]);
        const qualifying = Object.keys(real.targets).filter(word => h.bridgeVerdict({word}));
        assert(qualifying.length > 0, `${language} needs tested source-deck examples`);
        assert(qualifying.includes({fr:'jamais',es:'años',pt:'anos'}[code]), 'named cross-language examples must qualify');
        console.log(code, 'all-source-known upper bound:', qualifying.length, 'examples:', qualifying.slice(0,8).join(', '));
        const progressBefore = JSON.stringify(h.progressData);
        h.bridgeVerdict({word:qualifying[0]});
        assert.equal(JSON.stringify(h.progressData),progressBefore,'target filtering never writes learning progress');
    }
    h.relevantSmartSkipLanguages = () => ['fr'];
    assert.equal(h.bridgeVerdict({word:'anos'}),null,'a removed source pair cannot survive in the verdict cache');
    console.log('BRIDGE profile, per-sense knowledge, mistakes, aliases, switches, morphology and release checks passed');
})();
