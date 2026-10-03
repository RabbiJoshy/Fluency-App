"""Freeze lyric-bearing legacy batches without changing the reference repository."""
import argparse
import json
from pathlib import Path
import re
from fluency.core.hashing import file_content_id
from fluency.lyrics.polyglot import write_json


def clean_genius_text(text):
    """Remove explicit transport headers, leaving lyric text and section labels."""
    removed=[]
    marker=text.find('Lyrics')
    if marker >= 0 and ('Contributor' in text[:marker] or 'Translations' in text[:marker]):
        end=marker+len('Lyrics')
        removed.append({'reason':'genius_title_header','text':text[:end]})
        text=text[end:]
        read_more=text.find('Read More')
        # Introductions captured by Genius end at this explicit marker.
        if read_more >= 0:
            removed.append({'reason':'genius_editorial_introduction','text':text[:read_more+len('Read More')]})
            text=text[read_more+len('Read More'):]
    match=re.search(r'(?:\d+)?Embed\s*$',text)
    if match:
        removed.append({'reason':'genius_embed_footer','text':match.group()})
        text=text[:match.start()]
    # Latin lyric dumps sometimes insert a zero-width joiner inside words.
    # Preserve the repair evidence instead of creating stray f / ilm cards.
    for marker in ('\u200c', '\u200d', '\ufeff'):
        if marker in text:
            removed.append({'reason':'embedded_format_character','codepoint':hex(ord(marker)),
                            'positions':[i for i,c in enumerate(text) if c==marker]})
            text=text.replace(marker,'')
    return text.strip(),removed


def freeze(directory, output, language, slug, reviewed_prefixes=None):
    if output.exists(): raise FileExistsError(output)
    songs=[]; ids=set(); inputs={}; cleaning=[]
    for path in sorted(directory.glob('*.json')):
        raw=json.loads(path.read_text())
        if not isinstance(raw,list): raise ValueError('expected legacy song batch: '+str(path))
        inputs[str(path.resolve())]=file_content_id(path)
        for row in raw:
            if not row.get('lyrics'): continue
            song_id=str(row['id'])
            if song_id in ids: raise ValueError('duplicate song identity: '+song_id)
            ids.add(song_id)
            text,removed=clean_genius_text(row['lyrics'])
            prefix=(reviewed_prefixes or {}).get(row['title'])
            if prefix:
                if not text.startswith(prefix): raise ValueError('reviewed source prefix drift: '+row['title'])
                removed.append({'reason':'reviewed_editorial_or_section_prefix','text':prefix})
                text=text[len(prefix):].strip()
            if not text: raise ValueError('cleaning erased a song: '+song_id)
            songs.append({'id':song_id,'title':row['title'],'artist':row['artist'],'text':text,
                          'source':'legacy_genius_batch','source_url':row.get('url'),
                          'raw_file':str(path.resolve())})
            cleaning.extend(dict(item,song_id=song_id) for item in removed)
    write_json(output,{'language':language,'slug':slug,'songs':songs,'source_files':inputs,'cleaning':cleaning})
    print(json.dumps({'songs':len(songs),'header_or_footer_regions_removed':len(cleaning)},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--language',required=True);p.add_argument('--slug',required=True)
    p.add_argument('--reviewed-prefixes',type=Path)
    args=p.parse_args();freeze(args.directory,args.output,args.language,args.slug,
        json.loads(args.reviewed_prefixes.read_text()) if args.reviewed_prefixes else None)
