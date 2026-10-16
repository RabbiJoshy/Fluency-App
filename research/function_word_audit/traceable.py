"""Reviewed, source-preserving example assignments for the twelve-word pilot only."""
from copy import deepcopy
from html import escape
import json
import hashlib
import re
from check import ROOT, plain

OUT=ROOT/'docs/audits/function-word-pilot'


def highlighted(text,chunks):
    cursor=0;html=[];spans=[]
    for kind,chunk in chunks:
        matches=list(re.finditer(r'(?<!\w)'+re.escape(chunk)+r'(?!\w)',text[cursor:]))
        if not matches:raise ValueError(f'Chunk {chunk!r} not found after offset {cursor} in {text!r}')
        start=cursor+matches[0].start();end=cursor+matches[0].end()
        html += [escape(text[cursor:start]),f'<span class="fw-token-{kind}">{escape(text[start:end])}</span>']
        spans.append(dict(slot=kind,start=start,end=end,text=chunk));cursor=end
    html.append(escape(text[cursor:]));result=''.join(html)
    assert plain(result)==text
    return result,spans


def attach(proposals):
    selection=json.loads((OUT/'source-selections.json').read_text())
    for filename,digest in selection['snapshot_hashes'].items():
        if hashlib.sha256((OUT/filename).read_bytes()).hexdigest()!=digest:
            raise ValueError('Source snapshot changed; re-review selections before rebuilding: '+filename)
    candidates=json.loads((OUT/'source-candidates.json').read_text())
    gaps=json.loads((OUT/'source-gap-candidates.json').read_text())
    titles=json.loads((ROOT/'app/data/source_titles.json').read_text())
    proposals=deepcopy(proposals);review=[]
    for words in proposals.values():
        for entry in words.values():
            for relation in entry['relations']:relation['examples']=[]
    for chosen in selection['selections']:
        lang,word,p,pool,key,i,chunks=(chosen[k] for k in ('language','word','pattern','pool','key','index','chunks'))
        if pool=='deck':
            source_card=candidates['decks'][lang][key];raw=source_card['examples'][i];cid=source_card['card_id']
        else:
            row=gaps[lang][key][i];raw=row['example'];cid=row['card_id']
        assert raw['example_id']==chosen['example_id'] and raw['metadata']['sentence_id']==chosen['sentence_id']
        text=raw.get('target') or raw.get('text') or raw['metadata']['target']['text']
        html,spans=highlighted(text,chunks)
        metadata=deepcopy(raw['metadata']);source=metadata['source']
        assert source['name'] in ('tatoeba','opensubtitles')
        assert source.get('source_record_id') and metadata.get('sentence_id') and source.get('attribution') and source.get('license')
        if source['name']=='tatoeba':assert source.get('url','').startswith('https://tatoeba.org/')
        if source['name']=='opensubtitles':assert source.get('document',{}).get('title_id')
        example=dict(targetHTML=html,translation=raw['english'],source=source['name'],metadata=metadata,
                     example_id=raw['example_id'],source_card_id=cid)
        tid=source.get('document',{}).get('title_id');title=titles.get(str(tid))
        if title:example['source_title']=title
        proposals[lang][word]['relations'][p]['examples'].append(example)
        review.append(dict(language=lang,word=word,pattern=p,example_id=raw['example_id'],sentence_id=metadata['sentence_id'],
             source_card_id=cid,candidate_pool=pool,candidate_key=key,candidate_index=i,
             sentence=text,translation=raw['english'],chunks=spans,source=source,
             decision='Reviewed: fits the displayed usage; retain source sentence and translation verbatim.',
             register_note='Tu-form retained for recognition; the first example uses você.' if (lang,word,p,pool,i)==('pt','que',2,'gap',0) else ''))
    for words in proposals.values():
        for entry in words.values():
            for relation in entry['relations']:
                assert len(relation['examples'])>=2
                relation['targetHTML']=relation['examples'][0]['targetHTML']
                relation['translation']=relation['examples'][0]['translation']
    return proposals,review


def write_report(review):
    (OUT/'traceable-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    lines=['# Traceable pilot examples','',f'{len(review)} reviewed source examples across all 24 patterns and 12 cards. Sentence wording and English translations are unchanged; only highlight spans are added. No new classification rules are deployed.','',
      'Examples come from the configured release decks. Some are borrowed from other parent cards when the focus card does not cover the required usage. Record IDs, complete attribution/licence evidence, parent card IDs and highlight offsets are retained in traceable-review.json.','',
      'Sources: [Tatoeba](https://tatoeba.org/) ([CC BY 2.0 FR](https://creativecommons.org/licenses/by/2.0/fr/)) and [OpenSubtitles.org](http://www.opensubtitles.org/) via OPUS. This review validates the retained release records; it does not re-fetch or independently authenticate upstream pages.','',
      'Selection rejected ambiguous pattern matches (e.g. “a menos que” is not a comparison), misaligned translations, and unrelated uses such as “o que”, “tener que” and reciprocal nos. No external benchmark/holdout data was used.','']
    for r in review:
        source=r['source'];url=source['url'] if source['name']=='tatoeba' else 'https://www.imdb.com/title/tt'+str(source['document']['title_id']).zfill(7)+'/'
        lines += [f"## {r['language']} · {r['word']} · pattern {r['pattern']}",'',r['sentence'],'',r['translation'],'',f"[{source['name']}]({url}) — {source['attribution']}",'',r['register_note'],'']
    (OUT/'traceable-review.md').write_text('\n'.join(lines))
