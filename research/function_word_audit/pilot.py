"""Editorial proposals only; source decks and assignment rules are never written."""
from copy import deepcopy
from html import escape
import json
from check import ROOT, plain, scan, markdown

WORDS = {'pt': 'de que se o nos naquele'.split(), 'es': 'de que se lo nos al'.split()}
OUT = ROOT / 'docs/audits/function-word-pilot'


def span(kind, text):
    return f'<span class="fw-token-{kind}">{escape(text)}</span>'


def formula(*parts):
    return ' + '.join(span(kind, text) for kind, text in parts)


# One row per existing pattern; preserve pattern identities and grammatical scope.
COPY = {
 'pt': {
  'de': [
   ('Verbs with de', [('v','verb'),('connector','de'),('c','noun / verb / pronoun')], 'Some verbs use de to link to what follows. Learn the verb and de together.'),
   ('Adding a detail', [('v','noun'),('connector','de'),('c','detail / action')], 'Adds a detail: whose it is, what it contains, what it is made of, or what it is for.')],
  'que': [
   ('Saying what you think', [('v','think, say, know or hope'),('connector','que'),('c','what happens')], 'Links what someone thinks, says, knows or hopes to a statement.'),
   ('Adding information', [('v','noun'),('connector','que'),('c','description')], 'Adds information about the noun.'),
   ('Comparing', [('v','more, less or better'),('connector','que'),('c','what you compare with')], 'Means “than” when comparing people, things or situations.')],
  'se': [
   ('If', [('connector','se'),('v','a possible situation'),('c','what happens then')], 'Means “if”: gives a possible situation and what happens then.'),
   ('Oneself / part of a verb', [('connector','se'),('v','verb')], 'Can mean “oneself”, or belong with a verb such as sentir-se (feel). It does not always mean “oneself”.')],
  'o': [
   ('The', [('connector','o'),('c','masculine singular noun')], 'Means “the” before a masculine singular noun, such as livro (book).'),
   ('Him / it', [('connector','o'),('v','verb')], 'Refers to “him” or a masculine “it”. These examples place o before the verb; other positions also occur.')],
  'nos': [
   ('Us / to us', [('connector','nos'),('v','verb')], 'Refers to us: someone sees or helps us, or tells us something.'),
   ('In / on / at the', [('connector','nos'),('c','masculine plural noun')], 'Combines em + os: “in”, “on” or “at the”, before a masculine plural noun.')],
  'naquele': [('In / on / at that', [('connector','naquele'),('c','masculine singular noun')], 'Combines em + aquele: “in”, “on” or “at that”. It can refer to places, things or times.')]
 },
 'es': {
  'de': [
   ('Verbs with de', [('v','verb'),('connector','de'),('c','noun / verb / pronoun')], 'Some verbs use de to link to what follows. Learn the verb and de together.'),
   ('Adding a detail', [('v','noun'),('connector','de'),('c','detail / action')], 'Adds a detail: whose it is, what it contains, what it is made of, or what it is for.')],
  'que': [
   ('Saying what you think', [('v','think, say, know or hope'),('connector','que'),('c','what happens')], 'Links what someone thinks, says, knows or hopes to a statement.'),
   ('Adding information', [('v','noun'),('connector','que'),('c','description')], 'Adds information about the noun.'),
   ('Comparing', [('v','more, less or better'),('connector','que'),('c','what you compare with')], 'Means “than” when comparing people, things or situations.')],
  'se': [
   ('Oneself / part of a verb', [('connector','se'),('v','verb')], 'Can mean “oneself”, or belong with a verb such as sentirse (feel). It does not always mean “oneself”.'),
   ('Without saying who', [('connector','se'),('v','verb')], 'Describes what happens without naming who does it. Compare se habla (people speak) and se venden libros (books are sold).')],
  'lo': [
   ('The … thing / part', [('connector','lo'),('c','adjective')], 'With an adjective, means “the … thing” or “the … part”: lo importante = the important thing.'),
   ('Him / it / that', [('connector','lo'),('v','verb')], 'Refers to “him”, a masculine “it”, or an idea: lo sé = I know that.')],
  'nos': [('Us / to us', [('connector','nos'),('v','verb')], 'Refers to us: someone sees or helps us, or tells us something.')],
  'al': [
   ('To / at the', [('connector','al'),('c','destination')], 'Here, a + el becomes al: “to the” or “at the”.'),
   ('When doing something', [('connector','al'),('v','infinitive (dictionary form)')], 'Means “when” doing something: al llegar = when someone arrives.')]
 }
}
# Shorten a rule without forcing away necessary meaning.
for language in COPY.values():
 language['de'][1] = (language['de'][1][0], language['de'][1][1], 'Adds a detail about ownership, contents, material or purpose, including an action: hora de comer = time to eat.' if language is COPY['es'] else 'Adds a detail about ownership, contents, material or purpose, including an action: hora de partir = time to leave.')


def build():
    originals = {l: json.loads((OUT / f'{l}.original.json').read_text()) for l in WORDS}
    proposals = {l: {w: deepcopy(originals[l][w]) for w in words} for l, words in WORDS.items()}
    notes = {}
    def ex(l,w,i,j): return proposals[l][w]['relations'][i]['examples'][j]
    def note(l,w,i,j,reason): notes.setdefault((l,w,i,j), []).append(reason)
    def change(l,w,i,j,target=None,translation=None,reason='Simpler everyday example.'):
        e = ex(l,w,i,j)
        if target is not None:
            if plain(target) != plain(e['targetHTML']):
                e['source'] = 'Original teaching example · Function-word pilot'
            e['targetHTML'] = target
        if translation is not None: e['translation'] = translation
        note(l,w,i,j,reason)
    def boundary(l,w,i,j,old,new):
        e=ex(l,w,i,j)
        assert old in e['targetHTML'], (l,w,i,j,old)
        change(l,w,i,j,target=e['targetHTML'].replace(old,new),reason='Highlight only the phrase described by the formula; keep the rest outside the coloured chunk.')
    for l, words in COPY.items():
        for w, rows in words.items():
            for i, (tag, parts, rule) in enumerate(rows):
                proposals[l][w]['relations'][i].update(tag=tag, formulaHTML=formula(*parts), rule=rule)
    for l, pairs in [('pt', [('me ligou não falou nada','me ligou</span> não falou nada'),('vimos ontem foi ótimo','vimos ontem</span> foi ótimo'),('visitamos era lindo','visitamos</span> era lindo')]),('es',[('llamó no dejó mensaje','llamó</span> no dejó mensaje'),('vimos fue excelente','vimos</span> fue excelente'),('conocimos era precioso','conocimos</span> era precioso')])]:
        for j,(old,new) in enumerate(pairs,1): boundary(l,'que',1,j,old+'</span>',new)
    boundary('es','de',1,3,'mi hermano nos visitó</span>','mi hermano</span> nos visitó')
    boundary('pt','de',0,2,'ajuda agora</span>','ajuda</span> agora')
    for j,old,new in [(1,'parque al atardecer','parque'),(2,'médico por la mañana','médico'),(4,'trabajo con energía','trabajo')]:
        tail=old[len(new):]
        boundary('es','al',0,j,old+'</span>',new+'</span>'+tail)
    boundary('pt','se',0,1,"você <span class='fw-token-v'>quiser</span>","<span class='fw-token-v'>você quiser</span>")
    boundary('pt','se',0,2,"eu <span class='fw-token-v'>souber</span> de algo","<span class='fw-token-v'>eu souber de algo</span>")
    change('pt','de',0,3,span('v','Eu me lembro')+' '+span('connector','de')+' '+span('c','tudo')+'.','I remember everything.','Use a straightforward Brazilian example; original Lembro-me remains preserved in the review.')
    change('pt','de',1,4,'A '+span('v','casa')+' '+span('connector','de')+' '+span('c','Ana')+' é pequena.','Ana’s house is small.','Use a transparent ownership example instead of the idiom homem de palavra.')
    change('pt','se',0,4,span('connector','Se')+' '+span('v','você precisar de ajuda')+', '+span('c','estou aqui')+'.',"If you need help, I’m here.",'Use você consistently in the Brazilian pilot; precisares is valid with tu, not an error.')
    change('pt','o',0,2,translation='The day started out sunny.',reason='Use natural English while preserving the Portuguese.')
    change('pt','o',0,3,span('connector','O')+' '+span('c','trabalho')+' está pronto.','The work is ready.','Remove a passive construction that distracts from learning the article.')
    change('pt','o',1,0,'Eu '+span('connector','o')+' '+span('v','vi')+' ontem.','I saw him yesterday.','Remove an unnecessary location from the first example; retain the pronoun form for recognition.')
    change('pt','nos',1,3,span('connector','Nos')+' '+span('c','dias de festa')+', a vila fica cheia.','On festival days, the village fills up.','Keep the contraction, remove unrelated attached se from the sentence.')
    change('pt','naquele',0,2,'Nós nos conhecemos '+span('connector','naquele')+' '+span('c','ano')+'.','We met that year.','Remove decorative vocabulary and make the subject explicit.')
    change('es','de',0,1,'No '+span('v','se acuerda')+' '+span('connector','de')+' '+span('c','ella')+'.',"He doesn’t remember her.",'Remove the surrounding reported-speech clause; English supplies a possible subject.')
    boundary('es','de',0,2,"Se <span class='fw-token-v'>trata</span>","<span class='fw-token-v'>Se trata</span>")
    boundary('es','de',0,4,"No te <span class='fw-token-v'>olvides</span>","No <span class='fw-token-v'>te olvides</span>")
    change('es','que',2,3,'La casa es '+span('v','más grande')+' '+span('connector','que')+' '+span('c','el piso anterior')+'.','The house is bigger than the previous flat.','Use the more transparent size comparison; preserve piso as valid Spanish vocabulary.')
    change('es','se',0,2,translation='He feels much calmer now.',reason='Complete the English sentence; the Spanish permits an omitted subject.')
    change('es','se',0,4,translation='The actor dressed elegantly.',reason='Use idiomatic English.')
    change('es','se',1,1,translation='Old books are for sale.',reason='Remove “here”, which the Spanish does not specify.')
    change('es','se',1,2,translation='The food is very good at this restaurant.',reason='Use natural English for impersonal se come bien.')
    change('es','se',1,3,translation='Life is peaceful in this village.',reason='Avoid stiff English “one lives”; retain the general meaning.')
    change('es','lo',0,3,'Hizo '+span('connector','lo')+' '+span('c','mejor')+' que pudo.','He did the best he could.','Remove a dispensable circumstance phrase and complete the English subject.')
    change('es','lo',1,0,translation='I already know that.',reason='Make the reference to an idea explicit; lo need not refer to a masculine object.')
    change('es','nos',0,4,'Ella '+span('connector','nos')+' '+span('v','espera')+' aquí.','She is waiting for us here.','Original nos alegramos belongs with alegrarse, not the us/to us pattern. Preserve it in the ledger for a later usage review.')
    change('es','al',0,3,translation='He accompanied his grandfather to the airport.',reason='Complete the English subject; one possible reading of omitted Spanish subject.')
    change('es','al',1,0,translation='When I got home, I rested.',reason='Use everyday English instead of “upon arriving”.')
    change('es','al',1,1,translation='When everyone heard the bell, they left.',reason='Use a natural when-clause.')
    change('es','al',1,2,'Sonrió '+span('connector','al')+' '+span('v','ver')+' el regalo.','She smiled when she saw the gift.','Replace an awkward, context-heavy surprise phrase; English supplies a possible subject.')
    change('es','al',1,3,translation='When the window was opened, fresh air came in.',reason='Avoid a dangling English modifier that makes fresh air appear to open the window.')
    change('es','al',1,4,translation='When the speech ended, everyone applauded.',reason='Make the timing natural without implying everyone delivered the speech.')
    ledger=[]
    for l, words in proposals.items():
        for w, entry in words.items():
            for i,r in enumerate(entry['relations']):
                old=originals[l][w]['relations'][i]
                # Existing first examples are short, representative anchors; retain their order.
                r['targetHTML']=r['examples'][0]['targetHTML']; r['translation']=r['examples'][0]['translation']
                ledger.append(dict(language=l, word=w, pattern=i, example=None, status='revise',
                    before={k:old[k] for k in ('tag','formulaHTML','rule')}, after={k:r[k] for k in ('tag','formulaHTML','rule')},
                    reasons=['Use everyday wording and match the formula to the displayed sentence order. Rules describe this usage, not every use of the word.']))
                for j,e in enumerate(r['examples']):
                    before=old['examples'][j]
                    ledger.append(dict(language=l,word=w,pattern=i,example=j,status='revise' if before!=e else 'retain',
                        before=before,after=e,reasons=notes.get((l,w,i,j),['Reviewed sentence, translation, pattern fit and highlighting; retain.']),
                        provenance='New teaching sentence; original source retained only in before record.' if before['source']!=e['source'] else 'Original attribution retained verbatim; not independently authenticated.'))
    return originals,proposals,ledger


def main():
    from preview import render
    originals,proposals,ledger=build()
    from traceable import attach, write_report
    proposals, source_review = attach(proposals)
    write_report(source_review)
    from expand import expand, write_report as write_full_report
    proposals, full_review = expand(originals, proposals)
    write_full_report(OUT, full_review)
    OUT.mkdir(parents=True,exist_ok=True)
    for l,data in proposals.items(): (OUT/f'{l}.proposed.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (OUT/'review.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
    findings=scan(originals)
    (OUT/'scan.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2)+'\n')
    (OUT/'scan.md').write_text(markdown(findings))
    (OUT/'proposal-scan.json').write_text(json.dumps(scan(proposals),ensure_ascii=False,indent=2)+'\n')
    lines=['# Twelve-word editorial review','', 'Historical editorial pass: all existing pilot examples were reviewed. The current preview uses the separate traceable-review.md source selections. Indexes are zero-based. No live data was changed.', '',
           'First examples remain in their existing order: they already provide short, representative anchors. Revised sentences are original teaching examples, not quotations from the old sources.', '',
           'The JSON ledger preserves complete original and proposed markup and source labels. Original attributions have not been independently authenticated.', '']
    for row in ledger:
        label=f"{row['language']} · {row['word']} · pattern {row['pattern']}"
        if row['example'] is not None: label+=f" · example {row['example']}"
        lines += [f"## {label} — {row['status']}", '']
        for side in ('before','after'):
            d=row[side]
            if row['example'] is None:
                lines += [f"**{side.title()}:** {d['tag']} · {plain(d['formulaHTML'])}", '', d['rule'], '']
            else:
                lines += [f"**{side.title()}:** {plain(d['targetHTML'])} → {d['translation']}", '', f"Source label: {d['source']}", '']
        lines += [' '.join(row['reasons']), '']
    (OUT/'review.md').write_text('\n'.join(lines))
    (OUT/'preview.html').write_text(render(originals,proposals,ledger))
    print(f'Wrote proposals and review to {OUT}; {len(ledger)} reviewed records.')


if __name__=='__main__': main()
