"""Compare existing inventories and configured release decks; never add cards."""
import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import unicodedata
from check import ROOT

TABLES = {'ARTICLE','PREP_GLOSS','PRON_GLOSS','CONJ_GLOSS','CONTRACTION'}
CLOSED = {'article','det','pron','prep','conj','particle','postp','contraction','adp','cconj','sconj','pronoun','determiner','preposition','conjunction'}
SUPPLEMENTAL = {'es': {'no','nunca','tampoco','también','solo','sólo','aun','aún'},
                'pt': {'não','nunca','também','só','ainda','àquelas','àquilo','nuns','numas','duns','dumas','pra','pro','pras','pros'}}
CONNECTORS = {'es': {'aunque','mientras','sino','ni','pues','o','e','u','así que','ya que','puesto que','a pesar de','sin embargo','por lo tanto','en cuanto','antes de','después de','para que','hasta que'},
              'pt': {'ou','nem','pois','embora','enquanto','porém','senão','caso','assim que','já que','apesar de','no entanto','por isso','para que','antes de','depois de','até que'}}


def normalise(s):
    # Preserve meaningful accents: Spanish el/él and Portuguese nos/nós are different.
    return ' '.join(unicodedata.normalize('NFC', s).casefold().split())


def inventory(path):
    found=defaultdict(set)
    # Read literals, do not import a labeller or execute its dictionary-loading code.
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in TABLES:
                    for word in ast.literal_eval(node.value):
                        found[normalise(word)].add(f'{path.relative_to(ROOT)}:{node.lineno} ({target.id})')
    return found


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,default=ROOT.parent/'Fluency-Workspace')
    parser.add_argument('--out',type=Path,default=ROOT/'docs/audits/function-word-pilot')
    args=parser.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    config_path=ROOT/'app/config/config.json'; config=json.loads(config_path.read_text())
    pins=[dict(path=str(config_path),sha256=digest(config_path))]
    candidates=[]; represented=[]; expressions=[]
    for lang,name in [('es','spanish'),('pt','portuguese')]:
        suite_path=ROOT/f'app/data/grammar-words/{lang}.json'
        suite=json.loads(suite_path.read_text()); existing={normalise(w) for w in suite}
        inv_path=ROOT/f'research/cascade/trouble-words/labeller_{lang}.py'
        known=inventory(inv_path)
        for word in SUPPLEMENTAL[lang]:
            known[word].add('editorial probe: negation/focus or contraction-family gap; verify usage and register')
        manifest_path=args.workspace/config['languages'][name]['releaseManifestPath']
        deck_path=manifest_path.parent/'deck.json'
        for path in [suite_path,inv_path,manifest_path,deck_path]: pins.append(dict(path=str(path.resolve()),sha256=digest(path)))
        cards=json.loads(deck_path.read_text())['cards']
        by_word=defaultdict(list); units=defaultdict(list)
        for card in cards:
            word=normalise(card['display_form']); by_word[word].append(card)
            pos={m.get('part_of_speech','').lower() for m in card.get('meanings',[])} & CLOSED
            if pos: known[word].add('configured release deck: dictionary POS '+', '.join(sorted(pos)))
            for pattern in card.get('function_word',{}).get('patterns',[]):
                unit=normalise(pattern['value'])
                if unit in CONNECTORS[lang] and ' ' in unit:
                    units[unit].append(dict(card_id=card['card_id'],word=word,count=pattern['count'],gloss=pattern.get('gloss','')))
        for word,sources in known.items():
            matches=by_word.get(word,[])
            evidence=[dict(card_id=c['card_id'],rank=c.get('rank'),shown_examples=len(c.get('examples',[])),
                           closed_parts_of_speech=sorted({m.get('part_of_speech','').lower() for m in c.get('meanings',[])} & CLOSED)) for c in matches]
            if word in existing:
                represented.append(dict(language=lang,word=word,reason='Exact normalised suite key already present.'))
                continue
            rank=min((c['rank'] for c in matches if c.get('rank') is not None),default=None)
            priority='P1' if rank is not None and rank<=500 else 'P2' if matches else 'P3'
            category='connector' if word in CONNECTORS[lang] or any('CONJ_GLOSS' in s for s in sources) else 'contraction / reduced form' if lang=='pt' and word in {'àquelas','àquilo','nuns','numas','duns','dumas','pra','pro','pras','pros'} else 'contraction' if any('CONTRACTION' in s for s in sources) else 'other closed-class candidate'
            candidates.append(dict(language=lang,word=word,priority=priority,category=category,rank=rank,
                membership='in release deck; absent from curated suite' if matches else 'inventory/probe only; absent as exact release card',
                evidence=evidence,inventory_sources=sorted(sources),
                duplicate_check='No exact suite key after NFC/case/whitespace normalisation; accent and inflection variants deliberately kept separate.',
                caveat='Dictionary POS and draft inventories nominate candidates, not proof that every usage is closed-class. Review homographs and family grouping before adding.'))
        for word,ev in units.items():
            expressions.append(dict(language=lang,word=word,evidence=ev,
                status='Already labelled inside existing cards; consider a pattern, not automatically a new card.',
                exact_suite_key=word in existing,exact_release_card=word in by_word))
        del cards,by_word
    candidates.sort(key=lambda r:(r['priority'],r['rank'] if r['rank'] is not None else 999999,r['language'],r['word']))
    result=dict(candidates=candidates,already_represented=represented,connector_expressions=expressions,input_pins=pins)
    (args.out/'missing-words.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=['# Second task: remaining-word candidates','',
      '“Missing” means absent from the curated function-word suite, not necessarily absent from the learning deck. No cards were added.', '',
      'Compared both configured 10,000-card release decks with curated suite keys, literal closed-class tables in the existing draft labellers, and closed-class dictionary POS in release meanings. Draft labellers were read, never executed.', '',
      'P1: existing release card ranked 1–500. P2: other existing release cards. P3: inventory entry or editorial probe with no exact release card. Rank is a prioritisation signal, not proof of teaching value.', '',
      'Deduplication preserves accents and inflections: el/él and nos/nós stay distinct. Multiple inventory mentions merge into one language/word candidate. Existing suite words are excluded; their missing uses require a separate usage review.', '',
      'This is bounded discovery, not an exhaustive linguistic census. Explicit editorial probes supplement the inventories for negation/focus words and Portuguese contraction-family gaps; these are labelled separately in the evidence. Connector phrases below come from a small explicit shortlist intersected with existing release labels. No new sentence annotation or assignment research was performed.', '',
      '## Highest-ranked candidates', '', '| Language | Word | Priority | Rank | Kind | Release examples |', '|---|---|---|---|---|---|']
    for lang in ['es','pt']:
        for r in [r for r in candidates if r['language']==lang][:20]:
            lines.append(f"| {lang} | {r['word']} | {r['priority']} | {r['rank'] or '—'} | {r['category']} | {sum(c['shown_examples'] for c in r['evidence'])} |")
    lines+=['','## Contraction candidates','', '| Language | Word | Priority | Rank |', '|---|---|---|---|']
    for r in candidates:
        if r['category'].startswith('contraction'): lines.append(f"| {r['language']} | {r['word']} | {r['priority']} | {r['rank'] or '—'} |")
    lines+=['','## Connector phrases already represented inside cards','']
    for r in expressions:
        lines.append(f"- **{r['language']} · {r['word']}**: {sum(e['count'] for e in r['evidence'])} labelled occurrences across {len(r['evidence'])} parent cards. {r['status']}")
    lines+=['','## Full candidate list','', '| Language | Word | Priority | Rank | Evidence |', '|---|---|---|---|---|']
    for r in candidates:
        lines.append(f"| {r['language']} | {r['word']} | {r['priority']} | {r['rank'] or '—'} | {'; '.join(r['inventory_sources'])} |")
    lines+=['',f"{len(candidates)} candidates; {len(represented)} existing suite words excluded by exact match. Card IDs, source paths, SHA-256 input hashes and duplicate decisions are in missing-words.json.",'']
    (args.out/'missing-words.md').write_text('\n'.join(lines))
    print(f'{len(candidates)} candidates, {len(expressions)} connector expressions; report written.')


if __name__=='__main__': main()
