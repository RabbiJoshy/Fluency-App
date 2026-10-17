# Frozen-rule fresh-review check



35 previously unreviewed examples: 15 assignments and 20 abstentions.



This is a deterministic, status-stratified editorial sample from the existing development pool, not new corpus data or an independent accuracy estimate. Up to two examples per language/word/status were selected by a fixed hash before individual review. Prior reviewed examples, card selections and repeated sentence texts were excluded. The assistant reviewed predictions visibly; this is not blinded or native-speaker validation. The rules were frozen and replayed without modification. No holdout/gold files were opened.



## Results



Candidate judgments: `{'pattern_fit': {'fail': 1, 'uncertain': 2, 'pass': 12}, 'highlight_fit': {'pass': 12, 'fail': 2, 'uncertain': 1}, 'teaching_ready': {'no': 5, 'yes': 8, 'regional_review': 2}}`



Abstentions: `{'appropriate': 15, 'missed_match': 5}`



No Spanish nos or Portuguese naquele examples remain eligible in this cached pool. Portuguese que has no eligible assignments. These gaps and deliberately balanced status sampling prevent extrapolation to all cards or corpus precision/recall.



## Priority fixes



1. Extract complete verb constructions: Spanish “se ha echado para atrás” currently highlights only “se” and “echado”, omitting the auxiliary and idiomatic continuation.

2. Match the actual scope of the displayed rule: “número de minas” and “capital de riesgo” are noun-attached de constructions, but neither is clearly explained by the current ownership/contents/material/purpose wording. Broaden the teaching explanation deliberately or abstain; do not silently approve them.

3. Include relevant noun-phrase modifiers: “mais pessoas como você” is currently shortened to “mais pessoas”.

4. Recover missed clear cases: al autobús; creo que debes…; nos impediu / Nos dê; se possa mover. Keep passive, phrase and pronoun-substitution abstentions.

5. Keep example quality separate from syntax: fragments, regional Portuguese and questionable translation/register need editorial checks even with a plausible label.



The uncertain acordar-se wake-up example remains unapproved. Brazilian dictionary evidence distinguishes ordinary wake-up uses from other senses: [Aulete](https://www.aulete.com.br/acordar); [Michaelis](https://michaelis.uol.com.br/moderno-portugues/busca/portugues-brasileiro/acordar). This check does not assert that every pronominal use is impossible.



## Individual review



### es / al / example_f94674a1e817a7121a956c9b8b517a07

Lo preguntas al cabo de dos años.

After two years, you ask that.

Prediction: abstain, pattern —.

Chunks: []

Fixed al cabo de expression; neither destination nor temporal infinitive.



### es / al / example_2e2657447b9656ac568c0b748a0630ae

Se apresuró para subir al autobús.

He hurried to get on the bus.

Prediction: abstain, pattern —.

Chunks: []

Al autobús is a clear destination and fits pattern 0; conservative rule misses it.



### es / de / example_263c23c9e3b4d76158f825dfe5cee7dc

Este es un reloj a prueba de agua.

This is a waterproof watch.

Prediction: abstain, pattern —.

Chunks: []

A prueba de is a fixed phrase outside these two de explanations.



### es / de / example_51ee7e1b3db07e9769623a5e67d5f6ed

Nunca he estado más seguro de algo en mi vida.

Never been more sure of anything in my life.

Prediction: abstain, pattern —.

Chunks: []

Seguro de is adjective-governed, not the displayed verb or noun pattern.



### es / de / example_98ef0d0031e53721d9d2635be38fde84

El número de minas navales no coincide.

The number of naval mines doesn't match up.

Prediction: candidate, pattern 1.

Chunks: [('v', 'número'), ('connector', 'de'), ('c', 'minas navales')]

Noun attachment is correct, but number/quantity is not covered by the displayed ownership/contents/material/purpose explanation.



### es / de / example_e60573f8f1d476dab70ed3bb615e3fc1

El capital de riesgo.

Risk capital.

Prediction: candidate, pattern 1.

Chunks: [('v', 'capital'), ('connector', 'de'), ('c', 'riesgo')]

Risk capital is a lexical noun compound; relation to the listed semantic categories is unclear. Fragment also adds little teaching value.



### es / lo / example_c42f53ae703fd2b46835d2cc86c8a789

Ya te dije todo lo que sé.

I already told you everything I know.

Prediction: abstain, pattern —.

Chunks: []

Todo lo que is outside lo + adjective / object lo.



### es / lo / example_08c4a4c3e99bd137e6ff3d2811ebc6f1

Un equipo es lo que me gusta ver.

A team is what I like to see.

Prediction: abstain, pattern —.

Chunks: []

Lo que relative construction is outside the displayed two patterns.



### es / lo / example_28cefab21855a9c391dba48cb4a01375

Mi padre sí que juega al golf, pero no lo hace bien.

My father does play golf, but not well.

Prediction: candidate, pattern 1.

Chunks: [('connector', 'lo'), ('v', 'hace')]

Object lo before hace; translation conveys the meaning through English ellipsis.



### es / lo / example_8bf2bd6a2117211786705719c40b6a77

No lo dejes abierto.

Don't leave it open.

Prediction: candidate, pattern 1.

Chunks: [('connector', 'lo'), ('v', 'dejes')]

Object lo before dejes; clear natural example.



### es / que / example_413d8183c04320452c994aefe0c23f2c

Así que él fué.

So he came over.

Prediction: abstain, pattern —.

Chunks: []

Así que is a connector phrase; source also has obsolete accent fué and a loose translation.



### es / que / example_1d7f172d6e0e04caf1b92c56ce5cf159

Bueno, creo que debes ir a por ello.

Well, i think you should go for it.

Prediction: abstain, pattern —.

Chunks: []

Creo que debes… clearly fits thought verb plus statement; current gate misses it.



### es / que / example_1a65b342314029e01213192325108d3b

No creo que ella sepa hablar francés.

I don't think she can speak French.

Prediction: candidate, pattern 0.

Chunks: [('v', 'creo'), ('connector', 'que'), ('c', 'ella sepa hablar francés')]

Thought verb plus complete subordinate statement; negative main clause is preserved.



### es / que / example_1e1800f311c889a05217bc22fb3a8e28

Creo que eran muy apreciados allí.

I believe they were much appreciated there.

Prediction: candidate, pattern 0.

Chunks: [('v', 'Creo'), ('connector', 'que'), ('c', 'eran muy apreciados allí')]

Thought verb and full subordinate statement are correctly separated.



### es / se / example_677cc0a626c4baf81f75f3e95e1f2d07

La fecha y el lugar de nuestro próximo concierto todavía no se ha fijado.

The date and venue for our next concert haven't been set yet.

Prediction: abstain, pattern —.

Chunks: []

Conservative abstention is justified; passive-like use also has subject/verb number mismatch, so do not add this sentence.



### es / se / example_5e88dbabf2547271110542e1d051cf44

Eres el único al que se lo he contado.

You're the only one I've ever told.

Prediction: abstain, pattern —.

Chunks: []

Se substitutes for le before lo, outside current reflexive/pronominal row.



### es / se / example_1334fd62d539abfc920dc94f1e21f5b7

Jamás se ha echado para atrás en situaciones difíciles.

He's never backed down in difficult situations.

Prediction: candidate, pattern 0.

Chunks: [('connector', 'se'), ('v', 'echado')]

Pronominal reading fits, but highlight omits ha and para atrás from se ha echado para atrás; coloured construction is incomplete.



### es / se / example_9502d08ea89c6ba73439e2a47bacab8b

Nos interesan los demás cuando se interesan por nosotros.

We are interested in others, when they are interested in us.

Prediction: candidate, pattern 0.

Chunks: [('connector', 'se'), ('v', 'interesan')]

Se interesan is pronominal and correctly highlighted; repeated interesar is natural here.



### pt / de / example_8743fa9d9379d21a750d6a76557782da

Eu era a favor de ir e eles eram a favor de ficar.

I was in favor of going and they were in favor of staying.

Prediction: abstain, pattern —.

Chunks: []

Repeated de occurrences and fixed a favor de phrase justify abstention.



### pt / de / example_4120c8db365b262a19404749353feaed

Você não deveria precisar fazer isso de novo.

You shouldn't need to do that again.

Prediction: abstain, pattern —.

Chunks: []

De novo is a fixed adverbial phrase, outside current patterns.



### pt / de / example_07217055d94377551840dfc270e9e1d8

Você deve estar morrendo de fome.

You must be starving.

Prediction: candidate, pattern 0.

Chunks: [('v', 'morrendo'), ('connector', 'de'), ('c', 'fome')]

Morrer de fome is a natural verb-with-de expression and translation preserves idiomatic meaning.



### pt / de / example_399c9c3d39e291440fc5f7495b118300

Nós precisamos de mais pessoas como você.

We need more people like you.

Prediction: candidate, pattern 0.

Chunks: [('v', 'precisamos'), ('connector', 'de'), ('c', 'mais pessoas')]

Verb-with-de reading is correct; noun chunk should retain como você as part of mais pessoas como você.



### pt / nos / example_dfbc0dd96353c76910dc5b3bb8f86e62

O mau tempo nos impediu de sair.

The bad weather prevented us from leaving.

Prediction: abstain, pattern —.

Chunks: []

Nos impediu is a clear object us before verb, pattern 0.



### pt / nos / example_117fe697d7b7d267c46b063f583a554f

Nos dê algumas horas.

Give us a couple of hours.

Prediction: abstain, pattern —.

Chunks: []

Nos dê is natural everyday Brazilian imperative with object us; matches pattern 0.



### pt / nos / example_10bf876147a204bca1322a3dab35bf1b

Eu não gostaria que nos vissem juntas.

I wouldn't like us to be seen together.

Prediction: candidate, pattern 0.

Chunks: [('connector', 'nos'), ('v', 'vissem')]

Nos is the object of third-person plural vissem; English passive preserves the meaning.



### pt / o / example_fbc1bf2de407091f9db394921586b8f4

Eu quero saber o que é.

I want to know what it is.

Prediction: abstain, pattern —.

Chunks: []

O que interrogative is not article + noun or object o.



### pt / o / example_375a4edb23bd4c34001233d031099ba0

O que é que parece?

What does it look like?

Prediction: abstain, pattern —.

Chunks: []

O que interrogative is outside current two patterns.



### pt / o / example_7959719a810f78e5c5ca7c58040a2cca

Sabias que o Quincannon ia lá estar?

Did you know Quincannon was gonna be there?

Prediction: candidate, pattern 0.

Chunks: [('connector', 'o'), ('c', 'Quincannon')]

Article before a personal name fits the grammatical pattern, but sabias and ia lá estar require a European Portuguese label rather than default Brazilian copy.



### pt / o / example_0dcdb7b5bbfec62b9b2e3b6f6005853d

Diz-me do que falava o teu filho.

Tell me what your son was talking about.

Prediction: candidate, pattern 0.

Chunks: [('connector', 'o'), ('c', 'teu filho')]

Article plus noun phrase teu filho is highlighted correctly; enclitic imperative Diz-me needs regional handling.



### pt / que / example_2422e404f33c58a5a40eef2fd38ff9d3

Por que estamos rindo?

Why are we laughing?

Prediction: abstain, pattern —.

Chunks: []

Por que question phrase is outside current que patterns.



### pt / que / example_8ece1c806bd0d03ca274f1c55ad41a02

E que tal jogarmos uma partida?

How about we play a match?

Prediction: abstain, pattern —.

Chunks: []

Que tal suggestion phrase is outside current que patterns.



### pt / se / example_f6cd80c3c81cdb55ed4b7d9d3b796d7d

Encontra alguém que se possa mover no mundo dele.

Find someone who can move in his world.

Prediction: abstain, pattern —.

Chunks: []

Pronominal mover-se fits the second Portuguese se pattern; needs whole verb-complex handling for se possa mover.



### pt / se / example_d5161219cb80f5c237bafe1fbb2e9494

Suspeita-se que ela seja uma espiã.

She is suspected of being a spy.

Prediction: abstain, pattern —.

Chunks: []

Passive/impersonal suspeita-se is outside the two Portuguese se patterns.



### pt / se / example_3796c686d2f2182d74b77f0c99103a9b

Você deveria ter se acordado mais cedo.

You should've gotten up earlier.

Prediction: candidate, pattern 1.

Chunks: [('connector', 'se'), ('v', 'acordado')]

Se acordado with wake-up meaning is unsuitable for automatic approval in default Brazilian Portuguese; dictionary/register review required. English gotten up also differs from waking up.



### pt / se / example_4b6353c4bae6347a837952f2eaaf1883

Eles me disseram que vão se juntar a nós mais tarde.

They told me that they'll join us later.

Prediction: candidate, pattern 1.

Chunks: [('connector', 'se'), ('v', 'juntar')]

Se juntar is a natural pronominal infinitive and the future meaning is retained in translation.
