"""Build an opt-in staging overlay from explicit editorial approvals only."""
import json
from collections import Counter
from copy import deepcopy
from syntax_bridge_v2 import OUT, ROOT, sha, decide, render


def build():
    predictions=json.loads((OUT/'syntax-v2-findings.json').read_text())['rows']
    byid={r['example_id']:r for r in predictions}
    sample=json.loads((OUT/'v2-fresh-predictions.json').read_text())
    reviews=json.loads((OUT/'v2-fresh-review.json').read_text())
    assert {r['example_id'] for r in sample}=={r['example_id'] for r in reviews}
    for r in sample:
        assert r==byid[r['example_id']], 'Frozen fresh prediction changed.'
    accepted=[r for r in reviews if r['decision']=='accept']
    accepted += [dict(example_id=i,decision='accept',reason=reason) for i,reason in [
        ('example_2e2657447b9656ac568c0b748a0630ae','Reviewed regression: al autobús is a clear destination.'),
        ('example_1334fd62d539abfc920dc94f1e21f5b7','Reviewed regression: full ha echado para atrás now retained.')]]
    originals=json.loads((OUT/'findings.json').read_text())['rows']
    cache=json.loads((OUT/'parse-evidence.json').read_text())['rows']
    raw=json.loads((ROOT/'docs/audits/function-word-pilot/source-candidates.json').read_text())['decks']
    overlay={'pt':{},'es':{}}
    for approval in accepted:
        row=byid[approval['example_id']]; lang,word,pattern=row['language'],row['word'],row['pattern']
        original=next(r for r in originals if r['example_id']==row['example_id'])
        actual=decide(original,cache[lang+'|'+word+'|'+row['example_id']])
        assert actual['status']=='candidate' and actual['pattern']==pattern
        assert render(row['sentence'],actual['chunks'])==row['targetHTML']
        card=raw[lang][word];source=next(e for e in card['examples'] if e['example_id']==row['example_id'])
        ex=dict(targetHTML=row['targetHTML'],translation=row['translation'],source=source['metadata']['source']['name'],metadata=deepcopy(source['metadata']),example_id=row['example_id'],syntax_trial_review=approval['reason'])
        overlay[lang].setdefault(word,{}).setdefault(str(pattern),[]).append(ex)
    out=ROOT/'app/data/grammar-words/syntax-trial.json'
    out.write_text(json.dumps(overlay,ensure_ascii=False,indent=2)+'\n')
    pins={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'syntax-v2-findings.json',OUT/'v2-fresh-predictions.json',OUT/'v2-fresh-review.json',ROOT/'research/function_word_audit/syntax_bridge_v2.py']}
    (OUT/'v2-staging-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
    counts=Counter(r['decision'] for r in reviews)
    lines=['# Second matching pass and staging trial','',
           'Rules are a separate v2; the v1 bridge and its frozen evaluation remain unchanged. No gold or holdout inputs were read. No production assignment process is enabled.','',
           '## Changes','',
           '- Verb chunks retain auxiliaries, intervening modal governors and licensed direction particles.',
           '- Noun chunks retain dependency-linked modifiers. A trailing comparison with contradictory attachment causes abstention rather than truncation.',
           '- Noun-attached de now abstains until the semantic relation is established; noun attachment alone cannot prove the displayed explanation.',
           '- Recover finite modal complements after que and a bounded set of motion-verb/destination-noun al constructions.',
           '- Preserve abstention for split nos tokens; no speculative parser correction.','',
           '## Further sentence review','',
           f'24 previously unreviewed development sentences: 12 candidates and 12 abstentions. Decisions: {dict(counts)}.',
           'Sample fixed by SHA-256 of v2-review plus example ID: six per language/status, excluding all prior reviewed IDs, source selections and matching texts. This is an assistant editorial check with predictions visible, not independent corpus accuracy or native-speaker validation. Rules were not revised after this sample was inspected. Six candidates are ready for this bounded trial; six remain on editorial hold. Four abstentions miss suitable constructions.', '',
           '## Staging behaviour','',
           f'{len(accepted)} reviewed additions: six from the further review and two corrected regression cases. Generated highlights are used verbatim and source metadata retained. Existing examples remain in the cycle. No pattern copy or deck membership changes.',
           'Enable with ?fwSyntaxTrial=1 on staging. Remove that query parameter or set it to 0 to return to the normal examples. Production ignores the parameter. Affected cards display “Reviewed example trial”.', '',
           '## Still unresolved','',
           'Split-token nos; semantic noun-de classification; broader destination nouns; regional Portuguese and context-dependent examples; independent evaluation outside this development pool. These do not silently enter the staged overlay.','']
    for r,j in zip(sample,reviews):
        assert r['example_id']==j['example_id']
        lines += [f'### {r["language"]} / {r["word"]}: {j["decision"]}',r['sentence'],r['translation'],j['reason'],'']
    (OUT/'v2-staging-report.md').write_text('\n\n'.join(lines).rstrip()+'\n')
    print(f'{len(accepted)} reviewed additions; fresh review: {dict(counts)}')
    return overlay

if __name__=='__main__':build()
