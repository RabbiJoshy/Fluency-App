# Automatic-label bridge: twelve-word first pass



334 retained release examples: 95 unmapped, 207 candidate, 32 ambiguous.



These are adapter routing counts, not accuracy, coverage of the language, or dominance. Releases cap/select examples. The retained labels were not recomputed with today’s draft labeller. No parked HINGE gold/holdout was read or changed.



The trial adds only explicitly accepted examples absent from the original 71-example selection. Existing examples remain available. Sampling is editorial and deliberately includes counterexamples, not a blinded or representative evaluation. Chunk spans are editorially reviewed by the assistant; the automatic labels alone do not supply them.



## Pattern mapping and gaps



- pt / de / 0 (Verbs with de): 26 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- pt / de / 1 (Adding a detail): 13 candidate routes; 0 accepted fresh examples. Not approved for automatic assignment.

- pt / naquele / 0 (In / on / at that): 30 candidate routes; 2 accepted fresh examples. Not approved for automatic assignment.

- pt / nos / 0 (Us / to us): 15 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- pt / nos / 1 (In / on / at the): 0 candidate routes; 0 accepted fresh examples. No retained example reaches this pattern; expand the input pool before judging the matcher.

- pt / o / 0 (The): 10 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- pt / o / 1 (Him / it): 4 candidate routes; 0 accepted fresh examples. Not approved for automatic assignment.

- pt / que / 0 (Saying what you think): 6 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- pt / que / 1 (Adding information): 2 candidate routes; 0 accepted fresh examples. Not approved for automatic assignment.

- pt / que / 2 (Comparing): 0 candidate routes; 0 accepted fresh examples. No retained example reaches this pattern; expand the input pool before judging the matcher.

- pt / se / 0 (If): 11 candidate routes; 0 accepted fresh examples. Not approved for automatic assignment.

- pt / se / 1 (Oneself / part of a verb): 14 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- es / al / 0 (To / at the): 21 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- es / al / 1 (When doing something): 0 candidate routes; 0 accepted fresh examples. No retained example reaches this pattern; expand the input pool before judging the matcher.

- es / de / 0 (Verbs with de): 23 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- es / de / 1 (Adding a detail): 19 candidate routes; 0 accepted fresh examples. Not approved for automatic assignment.

- es / lo / 0 (The … thing / part): 0 candidate routes; 0 accepted fresh examples. No retained example reaches this pattern; expand the input pool before judging the matcher.

- es / lo / 1 (Him / it / that): 22 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- es / nos / 0 (Us / to us): 12 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- es / que / 0 (Saying what you think): 14 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- es / que / 1 (Adding information): 0 candidate routes; 0 accepted fresh examples. No retained example reaches this pattern; expand the input pool before judging the matcher.

- es / que / 2 (Comparing): 0 candidate routes; 0 accepted fresh examples. No retained example reaches this pattern; expand the input pool before judging the matcher.

- es / se / 0 (Oneself / part of a verb): 25 candidate routes; 1 accepted fresh examples. Not approved for automatic assignment.

- es / se / 1 (Without saying who): 4 candidate routes; 0 accepted fresh examples. Not approved for automatic assignment.



## Reviewed fresh examples



### pt / que: reject

É isso que podem fazer!

That's what you can do!

Label: {'gloss': 'that / which / who', 'kind': 'role', 'rule': 'role', 'value': 'relative'}

Candidates: [1]. Relative label is plausible, but antecedent isso is a pronoun, not the displayed noun slot.



### pt / que: accept

Porque achas que eu te trouxe comigo?

Why do you think I brought you with me?

Label: {'gloss': 'that', 'kind': 'role', 'rule': 'role', 'value': 'conj_that'}

Candidates: [0]. Thought verb plus statement fits. Tu-form retained for recognition; not a default Brazilian anchor.



### pt / o: accept

O caso está a correr muito bem.

The case is going very well.

Label: {'gloss': 'the', 'kind': 'role', 'rule': 'role', 'value': 'article'}

Candidates: [0]. Article before masculine singular noun. European progressive appears outside the teaching chunk.



### pt / o: reject

Você escolheu o melhor.

You have chosen the best.

Label: {'gloss': 'the', 'kind': 'role', 'rule': 'role', 'value': 'article'}

Candidates: [0]. O melhor is a nominalised adjective; does not demonstrate the displayed noun formula.



### pt / de: reject

A minha esposa é de Boston.

My wife is from Boston.

Label: {'gloss': 'of / from', 'kind': 'role', 'rule': 'role', 'value': 'prep'}

Candidates: [0, 1]. Origin predicate é de Boston is not a noun + de detail, nor a governed lexical verb frame.



### pt / de: accept

Tenho de admitir que estou curioso.

I have to admit I'm curious.

Label: {'gloss': 'to have to (indicates obligation)', 'kind': 'unit', 'rule': 'verb_frame', 'value': 'ter de'}

Candidates: [0]. Retained governed frame ter de matches verb + de + verb.



### pt / se: reject

Não sei se tenho tempo.

I don't know if I have the time.

Label: {'gloss': 'if / whether', 'kind': 'role', 'rule': 'role', 'value': 'conj_if'}

Candidates: [0]. Embedded whether, not a conditional situation and result.



### pt / se: accept

Faça o seu melhor e não se preocupe.

Do your best and don't worry.

Label: {'gloss': 'to worry', 'kind': 'unit', 'rule': 'pronominal_verb', 'value': 'preocupar-se'}

Candidates: [1]. Pronominal preocupar-se fits the explicitly broad part-of-a-verb row.



### pt / nos: accept

Você quer nos dizer por que estamos aqui?

Do you want to tell us why we're here?

Label: {'gloss': 'us / to us', 'kind': 'role', 'rule': 'role', 'value': 'object_pron'}

Candidates: [0]. Us is the recipient of dizer; not reflexive/reciprocal.



### pt / nos: reject

Com licença, podemos nos sentar aqui?

Excuse me, may we sit here?

Label: {'gloss': 'us / to us', 'kind': 'role', 'rule': 'role', 'value': 'object_pron'}

Candidates: [0]. Nos sentar is pronominal/reflexive, not an us/to-us recipient. Retained object_pron label is insufficient.



### pt / naquele: accept

Eu sabia que estava tudo certo naquele momento.

I knew it was OK at that point.

Label: {'gloss': 'in that', 'kind': 'role', 'rule': 'role', 'value': 'prep'}

Candidates: [0]. Contraction followed by masculine singular noun.



### pt / naquele: accept

Naquele dia, na praia, eu a vi com meus próprios olhos.

That day on the beach I saw her with my own eyes.

Label: {'gloss': 'in that', 'kind': 'role', 'rule': 'role', 'value': 'prep'}

Candidates: [0]. Time use fits the contraction row; noun span stops before the separate place phrase.



### es / que: accept

Supongo que es un secreto.

I guess it's a secret.

Label: {'gloss': 'that', 'kind': 'role', 'rule': 'role', 'value': 'conj_that'}

Candidates: [0]. Supposition is a thought verb introducing a statement.



### es / que: reject

No tengo nada que ver con ella.

I have nothing to do with her.

Label: {'gloss': 'nothing to see here; move along', 'kind': 'unit', 'rule': 'phrase', 'value': 'nada que ver'}

Candidates: []. Tener que ver con is a separate construction; do not force into thought, relative or comparison rows.



### es / de: reject

Hacer eso llevó más tiempo de lo que esperábamos.

Doing that took more time than we expected.

Label: {'gloss': 'of / from (+ verb)', 'kind': 'role', 'rule': 'role', 'value': 'prep'}

Candidates: [0, 1]. Comparative más ... de lo que needs a separate construction; generic prep cannot choose either de row.



### es / de: accept

¿Trataste de repasar las clases de inglés?

Did you try to review the English lessons?

Label: {'gloss': 'to try to', 'kind': 'unit', 'rule': 'verb_frame', 'value': 'tratar de'}

Candidates: [0]. Tratar de governs an infinitive; fits the displayed verb frame.



### es / lo: accept

Nadie lo sabe todo.

Nobody knows everything.

Label: {'gloss': 'him / it', 'kind': 'role', 'rule': 'role', 'value': 'object_pron'}

Candidates: [1]. Object pronoun resumes the content known.



### es / lo: reject

¿Es lo único que vas a decir?

That's all you gonna say?

Label: {'gloss': 'him / it', 'kind': 'role', 'rule': 'role', 'value': 'object_pron'}

Candidates: [1]. Lo único is the adjective construction (pattern 0), but retained object_pron routes to pattern 1: label error.



### es / al: reject

¡12.000 $ al año es una fortuna en Polonia!

$12,000 a year is a fortune in Poland!

Label: {'gloss': 'to the', 'kind': 'role', 'rule': 'role', 'value': 'prep'}

Candidates: [0]. Al año means per year, not a destination; generic prep is too broad.



### es / al: accept

Ahora estoy de camino al trabajo.

I'm on my way to work now.

Label: {'gloss': 'to the', 'kind': 'role', 'rule': 'role', 'value': 'prep'}

Candidates: [0]. Destination with a + el; fits the card scope.



### es / se: accept

La imagen se ve mejor de lejos.

The picture looks better at a distance.

Label: {'gloss': 'to look, to seem', 'kind': 'unit', 'rule': 'pronominal_verb', 'value': 'verse'}

Candidates: [0]. Verse meaning look/seem fits the part-of-a-verb row, not literal self-action.



### es / se: reject

Papá, por favor, no se vaya.

Daddy, please, don't leave.

Label: {'gloss': 'one / (it) is done', 'kind': 'role', 'rule': 'role', 'value': 'impersonal_se'}

Candidates: [1]. No se vaya addresses a person using pronominal irse; not impersonal. Retained label is wrong.



### es / nos: accept

¿Por qué nos pasa esto a nosotros?

Why is this happening to us?

Label: {'gloss': '(to) us', 'kind': 'role', 'rule': 'pron_det', 'value': 'object_pron'}

Candidates: [0]. To us is the affected recipient; fits the object row.



### es / nos: reject

En ese entonces no nos veíamos mucho.

We didn't see each other a lot then.

Label: {'gloss': 'to look, to seem', 'kind': 'unit', 'rule': 'pronominal_verb', 'value': 'verse'}

Candidates: []. Reciprocal seeing each other is not the us/to-us row; unmapped pronominal label should remain unmapped.



## Recommended next implementation



1. Recover occurrence-level parse evidence (focus offsets, governor, dependency relation and complement type) rather than guessing from the label or English gloss.

2. Resolve conditional/whether se, reciprocal nos, nominalised lo/o, and destination/personal/rate al before broad automatic assignment.

3. Map classifier outputs to stable pattern identities; keep unmapped and ambiguous outcomes visible. Expand beyond capped release examples for missing patterns.

4. Validate mapping and automatic chunk extraction on a separately sampled development set; keep the existing holdout untouched. Do not promote the trial as an accuracy result.
