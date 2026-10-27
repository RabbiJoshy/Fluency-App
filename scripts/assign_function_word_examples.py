#!/usr/bin/env python3
"""Assign parsed speech/artist sentences to existing function-word patterns.
Writes auditable assignments and an optional app-compatible supplemental overlay.
Never edits base suites, translations, sources or unassigned sentences.
"""
import argparse,json,sys,hashlib,re,importlib
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/function_word_audit'))
from syntax_assignment import assign_occurrences,VERSION

def build(rows,parses,max_per_pattern=5):
    suites={l:json.loads((ROOT/f'app/data/grammar-words/{l}.json').read_text()) for l in ('pt','es')}
    assignments=[];overlay={'pt':{},'es':{}}
    for row in rows:
        lang,word=row['language'],row['word']
        if lang not in suites or word not in suites[lang]:
            assignments.append(dict(language=lang,word=word,example_id=row['example_id'],sentence=row['sentence'],assignment=dict(status='abstain',reason='No curated pattern for this surface.')));continue
        obs=parses.get(f"{lang}|{word}|{row['example_id']}",parses.get(row['example_id']))
        valid=not obs or all(0<=n['token']['start_char']<n['token']['end_char']<=len(row['sentence']) and n['token']['text']==row['sentence'][n['token']['start_char']:n['token']['end_char']] for sent in obs['sentences'] for n in sent)
        results=assign_occurrences(row,obs) if valid else [dict(status='abstain',reason='Parse/source mismatch.')]
        if not results:results=[dict(status='abstain',reason='No focus occurrence supplied.')]
        for result in results:
            assignments.append(dict(language=lang,word=word,example_id=row['example_id'],sentence=row['sentence'],assignment=result))
            if result['status']!='candidate':continue
            pattern=result['pattern'];assert 0<=pattern<len(suites[lang][word]['relations'])
            bucket=overlay[lang].setdefault(word,{}).setdefault(str(pattern),[])
            if len(bucket)>=max_per_pattern:continue
            # Provenance is mandatory for exporting a learner-facing example,
            # but is not used to classify the syntactic occurrence.
            source=row.get('source') or row.get('metadata',{}).get('source')
            if not source or not source.get('source_record_id'):continue
            if any(e['example_id']==row['example_id'] for e in bucket):continue
            metadata=deepcopy(row.get('metadata') or {})
            metadata.update(source=deepcopy(source),sentence_id=row.get('sentence_id'),target={'language':lang,'text':row['sentence']})
            bucket.append(dict(example_id=row['example_id'],targetHTML=result['targetHTML'],translation=row.get('translation',''),source=source['name'],metadata=metadata,automaticSyntax=dict(patternId=result['pattern_id'],matcherVersion=VERSION,focusSpan=result.get('focus_span'),reason=result['reason'])))
    return assignments,overlay

def parse_rows(rows):
    """Fresh local NLP; no remote model calls and no translation inspection."""
    sys.path.insert(0,str(ROOT/'research/cascade/trouble-words'))
    from occurrence import locate
    from independent_predict import serialize
    cache={}
    for lang in sorted({r['language'] for r in rows}):
        lang_rows = [r for r in rows if r['language'] == lang]
        if not lang_rows:
            continue
        if lang=='pt':
            import stanza
            parser=stanza.Pipeline('pt',processors='tokenize,mwt,pos,lemma,depparse',download_method=None,use_gpu=False,verbose=False)
            version='stanza-pt-default@'+stanza.__version__
            docs = parser.bulk_process([stanza.Document([], text=r['sentence']) for r in lang_rows])
        elif lang=='es':
            from spacy_adapter import Pipeline
            parser=Pipeline();version=parser.version
            docs = parser.bulk([r['sentence'] for r in lang_rows])
        else:continue
        labeller=importlib.import_module('labeller_'+lang)
        for row, doc in zip(lang_rows, docs):
            text=row['sentence'];word=row['word']
            spans=row.get('spans') or [[m.start(),m.end()] for m in re.finditer(r"(?<![\w'’])"+re.escape(word)+r"(?![\w'’])",text,re.I)]
            label=None
            if len(spans)==1:
                hit=locate(doc,text,word,spans[0])
                if hit:label=labeller.label(hit[0],hit[1],surface=hit[2])
            row['automatic_label']=label or {}
            cache[f"{lang}|{word}|{row['example_id']}"]=dict(parser=version,sentence=text,spans=spans,sentences=serialize(doc))
    return cache

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',type=Path,required=True,help='JSON list or object with rows; one row per word/sentence.')
    ap.add_argument('--parses',type=Path,help='Cached observations; omit to run installed local parsers.')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--overlay',type=Path,help='Optional supplemental examples in app syntax-trial format.')
    ap.add_argument('--max-per-pattern',type=int,default=5)
    args=ap.parse_args();assert args.max_per_pattern>0
    data=json.loads(args.input.read_text())
    rows=data['rows'] if isinstance(data,dict) else data
    if args.parses:
        cache=json.loads(args.parses.read_text());parses=cache.get('rows',cache)
    else:
        parses=parse_rows(rows)
    assignments,overlay=build(rows,parses,args.max_per_pattern)
    result=dict(schema='function-word-assignments/v1',matcher_version=VERSION,input_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.input,args.parses] if p is not None},rows=assignments)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if args.overlay:
        args.overlay.parent.mkdir(parents=True,exist_ok=True);args.overlay.write_text(json.dumps(overlay,ensure_ascii=False,indent=2)+'\n')
    print(f'{sum(r.get("assignment",{}).get("status")=="candidate" for r in assignments)}/{len(assignments)} occurrences assigned; base suites unchanged.')
if __name__=='__main__':main()
