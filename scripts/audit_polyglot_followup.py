"""Record every formerly withheld surface's outcome and targeted semantic regressions."""
import argparse
from collections import Counter
import json
from pathlib import Path
from fluency.lyrics.polyglot import write_json


def audit(old, current):
    previous=json.loads((old/'withheld.json').read_text())
    master=json.loads((current/'vocabulary_master.json').read_text())
    withheld={r['surface']:r for r in json.loads((current/'withheld.json').read_text())}
    occurrences=json.loads((current/'occurrences.json').read_text())
    lines={r['line_id']:r for r in json.loads((current/'lines.json').read_text())}
    released={v['word']:v for v in master.values()}
    rows=[]
    for row in previous:
        surface=row['surface']
        state='recovered' if surface in released else 'removed_from_clean_source' if surface not in occurrences else withheld[surface]['reason']
        observed=occurrences.get(surface,[])
        rows.append({'surface':surface,'outcome':state,'observed_pos_counts':dict(Counter(r['occurrence_pos'] for r in observed)),
            'example_line_ids':[r['line_id'] for r in observed[:3]],
            'song_titles':sorted({lines[r['line_id']]['song_name'] for r in observed}),
            'released_glosses':[s['translation'] for s in released.get(surface,{}).get('senses',[])]})
    return {'old_run':old.name,'reviewed_run':current.name,'prior_withheld_count':len(previous),
            'outcomes':dict(Counter(r['outcome'] for r in rows)), 'rows':rows,
            'remaining_withheld':list(withheld.values()),
            'scope':'Exhaustive outcome/POS/provenance accounting, not a semantic certification of every missing spelling.'}


def semantic_check(run, checks):
    master=json.loads((run/'vocabulary_master.json').read_text())
    words={v['word']:[s['translation'] for s in v['senses']] for v in master.values()}
    result={}
    for word,required,forbidden in checks:
        glosses=words.get(word,[])
        passed=bool(glosses) and all(any(needle.casefold() in g.casefold() for g in glosses) for needle in required) and not any(needle.casefold() in g.casefold() for g in glosses for needle in forbidden)
        result[word]={'passed':passed,'glosses':glosses}
        if not passed: raise ValueError('semantic regression: '+word)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();w=a.workspace
    fr=w/'runs/fr/lyrics/polyglot-review-20261003-v5';pt=w/'runs/pt/lyrics/polyglot-review-20261003-v4'
    result={'fr':audit(w/'runs/fr/lyrics/polyglot-full-20261003-v8',fr),
            'pt':audit(w/'runs/pt/lyrics/polyglot-20261003-v8',pt),
            'semantic_regressions':{'fr':semantic_check(fr,[('tu',['you'],['question marker']),('on',['one','we'],['village']),
                ('l’',['the'],[]),('c’',['this'],['Community']),('pas',['negation'],['rhetorical']),('est',['to be'],['east'])]),
                'pt':semantic_check(pt,[('eu',['I'],[]),('você',['you'],['indefinite']),('se',[],['first-person','second-person']),
                    ('tê',['I have'],['letter']),('mó',['I live'],['millstone']),('nê',['woman'],['letter']),('chamá',['called'],[])])},
            'limitations':['Targeted regression checks do not measure overall sense accuracy.',
                'Uncertain forms remain withheld; complete word coverage and sentence translations are not promised.']}
    write_json(a.output,result)
    print(json.dumps({lang:result[lang]['outcomes'] for lang in ['fr','pt']},indent=2))
