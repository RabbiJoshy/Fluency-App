"""Fetch a named track list from LRCLIB; retain responses for offline replay."""
import argparse
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from fluency.lyrics.polyglot import write_json


def key(text):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower())


def fetch(config, output):
    if (output/'playlist.json').exists():
        raise FileExistsError('Refusing to replace a source manifest')
    output.mkdir(parents=True,exist_ok=True)
    songs=[]; failures=[]
    for track in config['tracks']:
        artist,title=track['artist'],track['title']
        path=output/(key(artist+' '+title)+'.json')
        try:
            if path.exists():
                rows=json.loads(path.read_text())
            else:
                url='https://lrclib.net/api/search?'+urlencode({'artist_name':artist,'track_name':title})
                with urlopen(Request(url,headers={'User-Agent':'Fluency-POLYGLOT/1.0'}),timeout=30) as response:
                    rows=json.load(response)
                write_json(path,rows)
                time.sleep(.2)
            hits=[r for r in rows if r.get('plainLyrics') and key(r['artistName'])==key(artist)
                  and key(r['trackName']).startswith(key(title))]
            if not hits: raise ValueError('no matching lyric-bearing recording')
            row=sorted(hits,key=lambda r:(key(r['trackName'])!=key(title),len(r['trackName']),r['id']))[0]
            songs.append({'id':str(row['id']),'artist':row['artistName'],'title':row['trackName'],
                          'text':row['plainLyrics'],'source':'lrclib',
                          'source_url':f"https://lrclib.net/api/get/{row['id']}",'raw_file':str(path)})
            print(artist, title, 'resolved',flush=True)
        except Exception as error:
            failures.append({'artist':artist,'title':title,'error':str(error)})
    write_json(output/'playlist.json',{'language':config['language'],'slug':config['slug'],'songs':songs,'failures':failures})
    if not 15 <= len(songs) <= 20:
        raise ValueError(f'Expected 15–20 resolved songs, got {len(songs)}; inspect failures')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();fetch(json.loads(args.config.read_text()),args.output)
