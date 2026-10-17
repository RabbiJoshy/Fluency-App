"""Reproduce a frozen, previously unreviewed development-sample check.
Not an independent holdout evaluation; never modifies rules, decks or previews.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from syntax_bridge import OUT, ROOT, decide, sha


def select(rows, excluded):
    groups = defaultdict(list)
    for row in rows:
        if row['example_id'] not in excluded and row['parser_available']:
            groups[row['language'], row['word'], row['status']].append(row)
    return [r for key, group in sorted(groups.items()) for r in sorted(
        group, key=lambda r: hashlib.sha256(('fresh-review-v1|' + r['example_id']).encode()).hexdigest())[:2]]


def main():
    inputs = [OUT/'syntax-findings.json', OUT/'findings.json', OUT/'parse-evidence.json',
              OUT/'sample-review.json', OUT/'syntax-review.json',
              ROOT/'docs/audits/function-word-pilot/source-selections.json',
              ROOT/'research/function_word_audit/syntax_bridge.py']
    originals = json.loads(inputs[1].read_text())['rows']
    selections = json.loads(inputs[5].read_text())['selections']
    excluded = {r['example_id'] for r in selections}
    for path in inputs[3:5]:
        excluded.update(r['example_id'] for r in json.loads(path.read_text()))
    # Exclude repeated sentence texts as well as IDs, even across word cards.
    seen = {r['sentence'] for r in originals if r['example_id'] in excluded}
    excluded.update(r['example_id'] for r in originals if r['sentence'] in seen)
    chosen = select(json.loads(inputs[0].read_text())['rows'], excluded)
    predictions = OUT/'fresh-sample-predictions.json'
    assert chosen == json.loads(predictions.read_text()), 'Frozen sample changed; do not silently resample.'
    pins_path = OUT/'fresh-check-pins.json'
    pins = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    if pins_path.exists():
        assert pins == json.loads(pins_path.read_text()), 'Frozen input changed.'
    else:
        pins_path.write_text(json.dumps(pins, indent=2)+'\n')
    cache = json.loads(inputs[2].read_text())['rows']
    original = {r['example_id']: r for r in originals}
    review = json.loads((OUT/'fresh-review.json').read_text())
    assert {r['example_id'] for r in review} == {r['example_id'] for r in chosen}
    judged = {r['example_id']: r for r in review}
    for r in chosen:
        key = r['language']+'|'+r['word']+'|'+r['example_id']
        actual = decide(original[r['example_id']], cache.get(key))
        for field in ('status','pattern','chunks'):
            assert actual.get(field) == r.get(field), (key, field)
    candidates = [r for r in chosen if r['status']=='candidate']
    counts = {field: dict(Counter(judged[r['example_id']][field] for r in candidates))
              for field in ('pattern_fit','highlight_fit','teaching_ready')}
    abstentions = Counter(judged[r['example_id']]['abstention'] for r in chosen if r['status']=='abstain')
    result = dict(sample_size=len(chosen), candidates=len(candidates), candidate_review=counts,
                  abstention_review=dict(abstentions), rows=[dict(**r, judgment=judged[r['example_id']]) for r in chosen])
    (OUT/'fresh-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    lines = ['# Frozen-rule fresh-review check', '',
             f'{len(chosen)} previously unreviewed examples: {len(candidates)} assignments and {len(chosen)-len(candidates)} abstentions.', '',
             'This is a deterministic, status-stratified editorial sample from the existing development pool, not new corpus data or an independent accuracy estimate. Up to two examples per language/word/status were selected by a fixed hash before individual review. Prior reviewed examples, card selections and repeated sentence texts were excluded. The assistant reviewed predictions visibly; this is not blinded or native-speaker validation. The rules were frozen and replayed without modification. No holdout/gold files were opened.', '',
             '## Results', '', f'Candidate judgments: `{counts}`', '', f'Abstentions: `{dict(abstentions)}`', '',
             'No Spanish nos or Portuguese naquele examples remain eligible in this cached pool. Portuguese que has no eligible assignments. These gaps and deliberately balanced status sampling prevent extrapolation to all cards or corpus precision/recall.', '',
             '## Priority fixes', '',
             '1. Extract complete verb constructions: Spanish “se ha echado para atrás” currently highlights only “se” and “echado”, omitting the auxiliary and idiomatic continuation.',
             '2. Match the actual scope of the displayed rule: “número de minas” and “capital de riesgo” are noun-attached de constructions, but neither is clearly explained by the current ownership/contents/material/purpose wording. Broaden the teaching explanation deliberately or abstain; do not silently approve them.',
             '3. Include relevant noun-phrase modifiers: “mais pessoas como você” is currently shortened to “mais pessoas”.',
             '4. Recover missed clear cases: al autobús; creo que debes…; nos impediu / Nos dê; se possa mover. Keep passive, phrase and pronoun-substitution abstentions.',
             '5. Keep example quality separate from syntax: fragments, regional Portuguese and questionable translation/register need editorial checks even with a plausible label.', '',
             'The uncertain acordar-se wake-up example remains unapproved. Brazilian dictionary evidence distinguishes ordinary wake-up uses from other senses: [Aulete](https://www.aulete.com.br/acordar); [Michaelis](https://michaelis.uol.com.br/moderno-portugues/busca/portugues-brasileiro/acordar). This check does not assert that every pronominal use is impossible.', '',
             '## Individual review', '']
    for r in chosen:
        j=judged[r['example_id']]
        lines += [f'### {r["language"]} / {r["word"]} / {r["example_id"]}', r['sentence'], r['translation'],
                  f'Prediction: {r["status"]}, pattern {r.get("pattern", "—")}.',
                  'Chunks: '+str([(c['slot'], c['text']) for c in r.get('chunks',[])]), j['reason'], '']
    (OUT/'fresh-check.md').write_text('\n\n'.join(lines).rstrip()+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
