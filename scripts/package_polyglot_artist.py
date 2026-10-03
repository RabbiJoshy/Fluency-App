"""Package an immutable offline rehearsal through the existing Artist contract."""
import argparse
import json
from pathlib import Path
import shutil
from fluency.core.workspace import Workspace
from fluency.core.languages import language_keys
from fluency.core.hashing import file_content_id
from fluency.artist.release import build_lyrics_catalog_release, validate_lyrics_release
from fluency.lyrics.polyglot import write_json


def package(workspace, run, release_id):
    manifest=json.loads((run/'manifest.json').read_text())
    for name,digest in manifest['outputs'].items():
        if file_content_id(run/name) != digest: raise ValueError('changed run artifact: '+name)
    report=json.loads((run/'report.json').read_text())
    if not report['complete'] or report['split_contract_violations']:
        raise ValueError('only completely evaluated, contract-valid candidates may be packaged')
    if file_content_id(Path(manifest['config_path'])) != manifest['inputs']['config']:
        raise ValueError('run config changed; rebuild under a new run id')
    source=json.loads((run/'source.json').read_text())
    slug=source['slug']; language=source['language']
    staging=workspace.root/'raw/playlists'/release_id
    staging.mkdir(parents=True,exist_ok=False)
    base=f'Artists/{language}/{slug}'
    target=staging/base;target.mkdir(parents=True)
    for name in ('index.json','examples.json','vocabulary_master.json'):
        shutil.copy2(run/name,target/name)
    write_json(target/'songs.json',{'schemaVersion':1,'source':'polyglot-pinned-source',
               'songs':[{'id':s['id'],'title':s['title'],'artist':s.get('artist')} for s in source['songs']]})
    (staging/'config').mkdir()
    write_json(staging/'config/artists.json',{slug:{'name':slug.replace('-',' ').title(),
         'language':language_keys()[language],'indexPath':base+'/index.json','examplesPath':base+'/examples.json',
         'masterPath':base+'/vocabulary_master.json','songsPath':base+'/songs.json'}})
    write_json(staging/'Artists/spotify_tracks.json',{})
    config=json.loads(Path(manifest['config_path']).read_text())
    master=json.loads((run/'vocabulary_master.json').read_text())
    native=staging/'native-assignments.jsonl'
    records=[]
    for record in json.loads((run/'decisions.json').read_text()):
        assignment=record.get('assignment') or {}
        if record['card_id'] not in master or assignment.get('status') != 'assigned': continue
        records.append(dict(record, surface=master[record['card_id']]['word'],
                            selection_projection=assignment['active_selection_projection'],
                            assignment_method=config['profile_id']))
    native.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    release=build_lyrics_catalog_release(workspace,source_repository=staging,release_id=release_id,
                                        wsd_assignment_overrides={slug:native})
    checked,_=validate_lyrics_release(release)
    print(json.dumps({'release':str(release),'cards':checked['card_count'],'artists':checked['artist_count'],
                      'status':'validated_inactive_candidate','run':str(run)},indent=2))
    return release


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--release-id',required=True)
    args=p.parse_args();package(Workspace.load(args.workspace),args.run,args.release_id)
