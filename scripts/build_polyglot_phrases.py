"""Freeze reviewed, lyric-attested Wiktionary phrase candidates; never edit speech inventories."""
import argparse
import json
from pathlib import Path
from fluency.core.hashing import file_content_id
from fluency.lyrics.polyglot import write_json

# These are reviewed lexical entries, not automatically accepted n-grams.
REVIEWED = {
 'fr': ['un peu','même si','ce que','tout ça','tout le monde','tant pis','près de','au fond','comme ça',
        'ce qui','si seulement','au plus','à la mode','tu sais','du tout','rien du tout','chacun pour soi',
        'à quoi bon','parce que','tous les deux','avec le temps','bon voyage','faire semblant','de travers',
        'encore une fois','quelque chose','afin de','face à','au hasard','rien que','pas encore','le temps que',
        'à peine','à gogo','pourvu que','perdre la tête','pour que','quelque part','s’il te plaît',
        'tout le temps','après tout','pour de vrai','en fait','de plus','sans doute','quand même'],
 'pt': ['todo mundo','à toa','pois é','assim que','isto é','de jeito maneira','não sei','por favor','às vezes',
        'apesar de','do que','em casa','quem sabe','só que','perto de','de repente','por isso','a pé',
        'graças a deus','graças a','ir embora','onde quer que','com certeza','cadê você','acontece que',
        'será que','por perto','deus lhe pague','a gente','o que','por que','como se','é que'],
}


def build(candidates, source, dictionary, output):
    if output.exists(): raise FileExistsError(output)
    payload=json.loads(candidates.read_text());language=json.loads(source.read_text())['language']
    rows={}
    for expression, entries in payload.items():
        kept=expression in REVIEWED[language]
        translations=[]
        for entry in entries:
            for sense in entry['senses']:
                gloss=sense['glosses'][0]
                if gloss.casefold().startswith(('used other than','for non-idiomatic')):continue
                if gloss not in translations:translations.append(gloss)
        rows[expression]={'id':'mwe:'+expression,'expression':expression,'translations':translations,
            'sources':['wiktionary','polyglot-lyrics-review'], 'source_rows':[e['line'] for e in entries],
            'attach_words':expression.replace('’',' ').split(),'corpus_freq':entries[0]['freq'],
            'verdict':'keep' if kept and translations else 'exclude',
            'reason':'reviewed_lexical_phrase' if kept else 'not_signed_for_lyrics',
            'status':'keep' if kept else 'compositional', 'non_compositional':kept,
            'route':'ambiguous','wsd_routing':'competitive_wsd','flexibility':'frozen',
            'ui_role':'formula' if any(e['pos']=='intj' for e in entries) else 'connector',
            'transparency':'formulaic','template_gap_limit':0,'verbal_idiom':False}
    write_json(output,{'meta':{'language':language,'contract':'mwe-merged/v1',
        'audit':'POLYGLOT targeted lyric-attested Wiktionary review', 'signed_by':'Codex','signed_date':'2026-10-03',
        'source_content_id':file_content_id(source),'dictionary_content_id':file_content_id(dictionary),
        'candidate_content_id':file_content_id(candidates),'kept':sum(r['verdict']=='keep' for r in rows.values()),
        'policy':'fixed exact phrases compete; unreviewed/compositional candidates withheld; no inferred inflection'},'mwes':rows})
    print(language,sum(r['verdict']=='keep' for r in rows.values()),'signed phrases')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['candidates','source','dictionary','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.candidates,a.source,a.dictionary,a.output)
