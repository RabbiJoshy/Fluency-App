import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('app/js/main.js','utf8');
const artist = {name:'Test artist',language:'spanish',indexPath:'test-index.json'};
const errors = [];
const context = vm.createContext({
    window:{fluencyRoute:{kind:'artist',artist:'test'}},
    CUSTOM_ARTIST_SLUG:'__custom__', activeArtist:null, allArtistsConfig:null,
    selectedArtistSlugs:[], artistVocabularyScope:'main',
    requestedLyricsRelease:()=>null, artistCatalogUrl:()=> 'test-artists.json',
    validateArtistCatalog:value=>value, bindArtistCatalogToRelease:value=>value,
    fetch:async()=>({ok:true,json:async()=>({test:{...artist}})}),
    releaseUrl:value=>value, console:{warn(){},error:(...args)=>errors.push(args)}
});
vm.runInContext(source.slice(source.indexOf('async function resolveArtist()'),source.indexOf('\nawait resolveArtist();')),context);
await vm.runInContext('resolveArtist()',context);
assert.equal(context.activeArtist.name,'Test artist','A direct artist URL must restore its catalogue entry');
assert.equal(context.window._urlArtistSlug,'test');
assert.deepEqual(errors,[]);
context.allArtistsConfig=null;
context.readJsonWithTimeout=async()=>{throw new Error('Offline')};
vm.runInContext(source.slice(source.indexOf('let artistCatalogFailed = false;'),source.indexOf('// The music source choice is a persistent page')),context);
await vm.runInContext('ensureArtistCatalog()',context);
assert.equal(vm.runInContext('artistCatalogFailed',context),true,'Failed catalogue transport must not look like an empty catalogue');
context.readJsonWithTimeout=async()=>({response:{ok:true},data:{test:{...artist}}});
await vm.runInContext('ensureArtistCatalog()',context);
assert.equal(vm.runInContext('artistCatalogFailed',context),false);
assert.equal(context.allArtistsConfig.test.name,'Test artist','Catalogue loading must recover on retry');
console.log('Direct artist restoration, catalogue failures and retry passed.');
