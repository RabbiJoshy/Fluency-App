"""Join frozen predictions to independent review; route, never publish examples."""
import json
from collections import Counter
from independent_sample import ROOT,OUT,digest

def assess(row, review):
    p=row['result'];supported=review['pattern_indices']
    if p['status']!='candidate':
        return dict(route='unassigned',pattern_fit='missed' if supported else 'appropriate_abstention',spans='not_applicable',reasons=[p['reason']])
    fit=p['pattern'] in supported
    actual=[(c['slot'],c['text']) for c in p['chunks']]
    expected=[(c['slot'],c['text']) for c in review.get('expected_chunks',[])]
    same=actual==expected
    reasons=[]
    if not fit:reasons.append('Assigned pattern is not supported by blind review.')
    if not same:reasons.append('Generated chunks differ from blind reviewer chunks; needs adjudication, not assumed incorrect.')
    for field in ('naturalness','translation','standalone_teaching'):
        if review[field]!='pass':reasons.append(field+': '+review[field])
    return dict(route='reviewed_ready' if not reasons else 'review_required',pattern_fit='supported' if fit else 'unsupported',spans='exact_agreement' if same else 'review_required',reasons=reasons)

def main():
    sample=json.loads((OUT/'sample.json').read_text());pred=json.loads((OUT/'predictions.json').read_text())
    assert pred['sample_sha256']==digest(OUT/'sample.json')
    for name,expected in sample['input_hashes'].items():
        if 'syntax_bridge' in name or 'trouble-words' in name:assert digest(__import__('pathlib').Path(name))==expected,'Frozen rule changed'
    reviews=[r for l in ('pt','es') for r in json.loads((OUT/f'{l}-review.json').read_text())]
    byid={r['example_id']:r for r in reviews}
    assert len(byid)==len(reviews)==len(sample['rows'])==len(pred['rows'])
    assert set(byid)=={r['example_id'] for r in pred['rows']}
    results=[]
    for row in pred['rows']:
        j=byid[row['example_id']]
        assert all(j[f] in ('pass','hold','fail') for f in ('naturalness','translation','standalone_teaching'))
        for c in j.get('expected_chunks',[]):assert c['text'] in row['sentence']
        results.append(dict(**row,review=j,assessment=assess(row,j)))
    metrics={l:{field:dict(Counter(r['assessment'][field] for r in results if r['language']==l)) for field in ('route','pattern_fit','spans')} for l in ('pt','es')}
    files=['sample.json','predictions.json','pt-review.json','es-review.json']
    (OUT/'evaluation.json').write_text(json.dumps(dict(input_hashes={f:digest(OUT/f) for f in files},metrics=metrics,rows=results),ensure_ascii=False,indent=2)+'\n')
    (OUT/'review-queue.json').write_text(json.dumps({route:[r for r in results if r['assessment']['route']==route] for route in ('reviewed_ready','review_required','unassigned')},ensure_ascii=False,indent=2)+'\n')
    assigned=[r for r in results if r['result']['status']=='candidate']
    lines=['# Separate-source function-word check','',
      f'48 unseen harvest sentences, 24 per language, four per pilot word. {len(assigned)} assignments; {48-len(assigned)} abstentions. {sum(r["assessment"]["pattern_fit"]=="supported" for r in assigned)} assigned patterns agree with the blind reviews. {sum(r["assessment"]["spans"]=="exact_agreement" for r in assigned)} assignments have exact chunk agreement.', '',
      '## What is independent','',
      'All previously selected sentence IDs and their normalized source text were excluded across every card in the pinned selection files. This excludes the old holdout pool without opening its file. Prior audit/source-pool/suite text was also excluded. The new sample uses the same underlying harvest corpora, not a new corpus or external validation source. Four sentences per word were selected by deterministic hash ranking before parsing/review, with one focus occurrence and 4–18 whitespace tokens. This small, balanced sample does not estimate overall corpus accuracy.', '',
      'Portuguese and Spanish Sol reviewers saw only sentences, translations and teaching patterns. They did not see predictions or matcher code. Reviews are AI editorial judgments, not human/native-speaker gold. The matcher and upstream labeller code were hashed at sampling and held fixed throughout evaluation. Fresh parsers and current dictionary labellers were run; unlike the earlier retained-label trial, no historical reflexive-decision cache was supplied. Results describe this combined fresh pipeline.', '',
      '## Routing','',
      'reviewed_ready means agreement on pattern and exact chunks plus passing naturalness, translation and standalone suitability. It requires independent review, not merely parser confidence. review_required retains any disagreement or quality hold. unassigned preserves matcher abstentions, including missed supported constructions. No row is inserted into a deck or published.', '',
      'Exact chunk disagreement is a review signal: a reviewer may prefer a wider span than the teaching formula requires. It is not automatically counted as a grammar error.', '',
      '## Results by language','',json.dumps(metrics,ensure_ascii=False,indent=2),'',
      '## Findings and next priorities','',
      '- Pattern matching alone is not example quality. Subtitle translations can add, omit or change meaning, and valid dialogue may be a poor standalone teaching sentence.',
      '- Investigate full complement boundaries: depende de lo que recuerdes currently highlights only recuerdes after de.',
      '- Adjudicate minimal versus full chunks for relative antecedents, reported-speech verb chains and al + infinitive objects before changing extraction rules.',
      '- Coverage is limited. Review missed supported uses, especially contractions and parser-disputed clitics, before extending the matcher to all function words.',
      '- Do not tune against this sample and continue calling it independent. Any subsequent fixes need another untouched sample.','',
      '## Source attribution','',
      'Every record retains source identifiers, licence and attribution. Subtitle data comes from [OpenSubtitles.org](http://www.opensubtitles.org/) via OPUS; Tatoeba records retain sentence links and CC BY attribution. No source sentence or translation was rewritten.','']
    for row in results:
        a=row['assessment'];j=row['review']
        lines += [f'### {row["language"]} / {row["word"]} — {a["route"]}',row['sentence'],row['translation'],f'Pattern: {row["result"].get("pattern","unassigned")}; review: {j["pattern_indices"]}.',j['reason'],j.get('standalone_reason',''),'Reasons: '+'; '.join(a['reasons']),'']
    (OUT/'report.md').write_text('\n\n'.join(lines).rstrip()+'\n')
    print(json.dumps(metrics))
if __name__=='__main__':main()
