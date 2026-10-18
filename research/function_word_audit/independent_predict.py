"""Run the frozen matcher on new parses, without reading reviewer decisions."""
import importlib,json,sys
from pathlib import Path
from independent_sample import OUT, ROOT, digest
from syntax_bridge_v3 import decide,render
sys.path.insert(0,str(ROOT/'research/cascade/trouble-words'))
from occurrence import locate

def serialize(doc):
    return [[dict(text=w.text,lemma=w.lemma,upos=w.upos,feats=w.feats,deprel=w.deprel,id=w.id,head=w.head,token=dict(text=w.parent.text,start_char=w.parent.start_char,end_char=w.parent.end_char)) for w in s.words] for s in doc.sentences]

def main(output=OUT, decider=decide):
    OUT=output
    sample=json.loads((OUT/'sample.json').read_text());results=[];parses={};versions={}
    for name,expected in sample['input_hashes'].items():
        p=Path(name)
        if 'trouble-words' in name or 'syntax_bridge' in name or 'syntax_assignment' in name:assert digest(p)==expected,'Rules changed after sampling: '+name
    for lang in ('pt','es'):
        if lang=='pt':
            import stanza
            parser=stanza.Pipeline('pt',processors='tokenize,mwt,pos,lemma,depparse',download_method=None,use_gpu=False,verbose=False)
            parse=lambda text:parser(text)
            version='stanza-pt-default@'+stanza.__version__
        else:
            from spacy_adapter import Pipeline
            parser=Pipeline();parse=parser;version=parser.version
        labeller=importlib.import_module('labeller_'+lang)
        versions[lang]=dict(parser=version,dictionary_path=labeller.KAIKKI,dictionary_sha256=digest(Path(labeller.KAIKKI)),reflexive_decisions='Not supplied; labeller default only. This differs from cached historical label provenance.')
        for row in sample['rows']:
            if row['language']!=lang:continue
            doc=parse(row['sentence']);hit=locate(doc,row['sentence'],row['word'],row['spans'][0])
            label=labeller.label(hit[0],hit[1],surface=hit[2]) if hit else None
            obs=dict(parser=version,spans=row['spans'],sentences=serialize(doc));parses[row['example_id']]=obs
            result=decider(dict(**row,automatic_label=label or {}),obs)
            if result['status']=='candidate':result['targetHTML']=render(row['sentence'],result['chunks'])
            results.append(dict(**row,automatic_label=label,result=result));print(lang,len(results),result['status'],flush=True)
    (OUT/'parses.json').write_text(json.dumps(dict(versions=versions,rows=parses),ensure_ascii=False,indent=2)+'\n')
    (OUT/'predictions.json').write_text(json.dumps(dict(sample_sha256=digest(OUT/'sample.json'),versions=versions,rows=results),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
