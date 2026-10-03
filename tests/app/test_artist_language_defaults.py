"""Artist releases without bespoke colours must inherit language defaults."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

APP=Path(__file__).resolve().parents[2]/'app'


@unittest.skipUnless(shutil.which('node'),'Node.js is needed for app execution checks')
class ArtistLanguageDefaultsTests(unittest.TestCase):
    def test_empty_artist_theme_loads_french_and_portuguese(self):
        script=r'''
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(process.argv[2],'utf8').replace(/^import .*;$/gm,'');
(async()=>{
 const result=[];
 for(const language of ['french','portuguese']) {
  for(const theme of [{},{primary:'#abcdef'}]) {
   const base={primary:'#046A38',secondary:'#DA291C'};
   const context={URLSearchParams,console,window:{location:{search:''}},document:{},
    activeArtist:{language,name:'Test',colorTheme:theme},releaseUrl:x=>x,
    fetch:async(url)=>({json:async()=>url.startsWith('config/config.json')?{languages:{[language]:{colorTheme:base}}}:{}}),
    alert:message=>{throw new Error(message);}};
   vm.runInNewContext(source,context);await context.window.loadConfig();
   result.push({language,theme:context.activeArtist.colorTheme,normal:context.window._normalModeLangConfigs[language].colorTheme});
  }
 }
 console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exit(1);});
'''
        done=subprocess.run(['node','-',str(APP/'js/config.js')],input=script,text=True,capture_output=True)
        self.assertEqual(done.returncode,0,done.stderr)
        result=json.loads(done.stdout)
        for index,row in enumerate(result):
            self.assertEqual(row['theme']['secondary'],'#DA291C')
            self.assertEqual(row['theme']['primary'],'#046A38' if index%2==0 else '#abcdef')
            self.assertEqual(row['normal']['primary'],'#046A38')
