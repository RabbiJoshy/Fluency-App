# Occurrence-level syntax trial



334 examples; 274 cached development parses; 115 structural candidates; 219 abstentions.



No gold/holdout input was read. This reuses cached development parses, not a new parser run. Candidate rules were developed after inspecting the previous 24-example editorial sample, so agreement on that sample is a regression check, not independent accuracy. All outputs remain diagnostic; no production classifier or data is changed.



Each candidate includes focus offsets, head/governor, parser identity and automatically extracted spans. Candidates are not automatically approved teaching examples. Existing editorial chunk strings are never used to generate spans.



## Abstentions



- 60: No matching development parse; not fetched from another split.

- 38: No supported structural rule in this first pass.

- 27: Generic de label does not establish either displayed attachment.

- 23: Need destination versus personal-a/recipient evidence; no forced assignment.

- 12: Article/object evidence does not fit the displayed formula.

- 12: Parser split or merged the focus token; do not guess the contraction/pronoun reading.

- 11: Se needs agreement, valency and reflexive/passive checks; parser-label conflict is unresolved.

- 7: Multiple focus occurrences: occurrence selection is not established.

- 6: Conditional clause structure is not established.

- 5: Conjunction label lacks a matching complement-clause attachment.

- 4: Intervening verb-complex material requires a complete verb-phrase span.

- 3: Clause governor is outside the thought/speech pattern scope.

- 3: Embedded whether clause, not the displayed condition/result.

- 3: Time/rate noun: generic al label is not destination evidence.

- 1: Relative label has no confirmed noun antecedent.

- 1: Word order does not match the displayed de formula.

- 1: First-person plural verb: reflexive/reciprocal interpretation needs a separate check.

- 1: Frame label and parsed governor disagree.

- 1: No syntactic head available.



## Previous reviewed cases (development regression only)



### pt que: É isso que podem fazer!

Prior review: reject. Syntax result: abstain; pattern —.

Relative label has no confirmed noun antecedent.

[]



### pt que: Porque achas que eu te trouxe comigo?

Prior review: accept. Syntax result: candidate; pattern 0.

Complement clause attached to a licensed thought/speech verb.

[{'slot': 'v', 'start': 7, 'end': 12, 'text': 'achas'}, {'slot': 'connector', 'start': 13, 'end': 16, 'text': 'que'}, {'slot': 'c', 'start': 17, 'end': 36, 'text': 'eu te trouxe comigo'}]



### pt o: O caso está a correr muito bem.

Prior review: accept. Syntax result: candidate; pattern 0.

Article attached to noun.

[{'slot': 'connector', 'start': 0, 'end': 1, 'text': 'O'}, {'slot': 'c', 'start': 2, 'end': 6, 'text': 'caso'}]



### pt o: Você escolheu o melhor.

Prior review: reject. Syntax result: abstain; pattern —.

Article/object evidence does not fit the displayed formula.

[]



### pt de: A minha esposa é de Boston.

Prior review: reject. Syntax result: abstain; pattern —.

Generic de label does not establish either displayed attachment.

[]



### pt de: Tenho de admitir que estou curioso.

Prior review: accept. Syntax result: candidate; pattern 0.

Governed de frame and dependency agree.

[{'slot': 'v', 'start': 0, 'end': 5, 'text': 'Tenho'}, {'slot': 'connector', 'start': 6, 'end': 8, 'text': 'de'}, {'slot': 'c', 'start': 9, 'end': 16, 'text': 'admitir'}]



### pt se: Não sei se tenho tempo.

Prior review: reject. Syntax result: abstain; pattern —.

Embedded whether clause, not the displayed condition/result.

[]



### pt se: Faça o seu melhor e não se preocupe.

Prior review: accept. Syntax result: candidate; pattern 1.

Pronominal label and dependency agree.

[{'slot': 'connector', 'start': 24, 'end': 26, 'text': 'se'}, {'slot': 'v', 'start': 27, 'end': 35, 'text': 'preocupe'}]



### pt nos: Você quer nos dizer por que estamos aqui?

Prior review: accept. Syntax result: abstain; pattern —.

Parser split or merged the focus token; do not guess the contraction/pronoun reading.

[]



### pt nos: Com licença, podemos nos sentar aqui?

Prior review: reject. Syntax result: abstain; pattern —.

Parser split or merged the focus token; do not guess the contraction/pronoun reading.

[]



### pt naquele: Eu sabia que estava tudo certo naquele momento.

Prior review: accept. Syntax result: abstain; pattern —.

No matching development parse; not fetched from another split.

[]



### pt naquele: Naquele dia, na praia, eu a vi com meus próprios olhos.

Prior review: accept. Syntax result: abstain; pattern —.

No matching development parse; not fetched from another split.

[]



### es que: Supongo que es un secreto.

Prior review: accept. Syntax result: candidate; pattern 0.

Complement clause attached to a licensed thought/speech verb.

[{'slot': 'v', 'start': 0, 'end': 7, 'text': 'Supongo'}, {'slot': 'connector', 'start': 8, 'end': 11, 'text': 'que'}, {'slot': 'c', 'start': 12, 'end': 25, 'text': 'es un secreto'}]



### es que: No tengo nada que ver con ella.

Prior review: reject. Syntax result: abstain; pattern —.

No supported structural rule in this first pass.

[]



### es de: Hacer eso llevó más tiempo de lo que esperábamos.

Prior review: reject. Syntax result: abstain; pattern —.

Generic de label does not establish either displayed attachment.

[]



### es de: ¿Trataste de repasar las clases de inglés?

Prior review: accept. Syntax result: abstain; pattern —.

Multiple focus occurrences: occurrence selection is not established.

[]



### es lo: Nadie lo sabe todo.

Prior review: accept. Syntax result: candidate; pattern 1.

Object dependency and before-verb placement agree.

[{'slot': 'connector', 'start': 6, 'end': 8, 'text': 'lo'}, {'slot': 'v', 'start': 9, 'end': 13, 'text': 'sabe'}]



### es lo: ¿Es lo único que vas a decir?

Prior review: reject. Syntax result: candidate; pattern 0.

Determiner plus adjective; overrides stale object label.

[{'slot': 'connector', 'start': 4, 'end': 6, 'text': 'lo'}, {'slot': 'c', 'start': 7, 'end': 12, 'text': 'único'}]



### es al: ¡12.000 $ al año es una fortuna en Polonia!

Prior review: reject. Syntax result: abstain; pattern —.

Time/rate noun: generic al label is not destination evidence.

[]



### es al: Ahora estoy de camino al trabajo.

Prior review: accept. Syntax result: abstain; pattern —.

Need destination versus personal-a/recipient evidence; no forced assignment.

[]



### es se: La imagen se ve mejor de lejos.

Prior review: accept. Syntax result: abstain; pattern —.

Se needs agreement, valency and reflexive/passive checks; parser-label conflict is unresolved.

[]



### es se: Papá, por favor, no se vaya.

Prior review: reject. Syntax result: candidate; pattern 0.

Pronominal dependency contradicts retained impersonal label; diagnostic correction requires review.

[{'slot': 'connector', 'start': 20, 'end': 22, 'text': 'se'}, {'slot': 'v', 'start': 23, 'end': 27, 'text': 'vaya'}]



### es nos: ¿Por qué nos pasa esto a nosotros?

Prior review: accept. Syntax result: abstain; pattern —.

No matching development parse; not fetched from another split.

[]



### es nos: En ese entonces no nos veíamos mucho.

Prior review: reject. Syntax result: abstain; pattern —.

No matching development parse; not fetched from another split.

[]



## Next validation



Inspect fresh structural candidates for semantic fit and chunk boundaries before enabling them in the learner preview. Parser coverage and abstention are not precision. In particular, first-plural filtering alone does not prove non-reciprocal nos; al destination inference and passive se remain deliberately unsupported.
