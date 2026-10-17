# Additional structural-candidate review



Assistant editorial review, not a blinded accuracy evaluation. Examples are outside the previous 24-example review. No hand-written highlight spans are used for accepted examples.



## pt / o — accept

Nunca pensei que o veria lá.

I never thought I'd see him there.

[('connector', 'o'), ('v', 'veria')]

Object o before veria; correct target and translation; generated spans fit.



## pt / de — accept

O que você gostaria de fazer agora?

What would you like to do now?

[('v', 'gostaria'), ('connector', 'de'), ('c', 'fazer')]

Governed gostar de plus infinitive; generated spans match the verb frame.



## pt / nos — accept

Se você tiver tempo na semana que vem, por favor, nos avise.

If you have time next week, please let us know.

[('connector', 'nos'), ('v', 'avise')]

Object nos before avise; longer context retained, but the local pattern is clear.



## es / de — accept

Ella acaba de perder su trabajo.

She has just lost her job.

[('v', 'acaba'), ('connector', 'de'), ('c', 'perder')]

Acabar de plus infinitive fits the governed frame. Translation preserves recent completion.



## es / al — accept

En Japón, la gente se quita los zapatos al entrar en una casa.

In Japan people take off their shoes when they enter a house.

[('connector', 'al'), ('v', 'entrar')]

Al plus infinitive is temporal; generated highlight is correct. Longer example is useful for this construction.



## es / se — accept

¿Pero por qué se va?

But why do you leave?

[('connector', 'se'), ('v', 'va')]

Irse fits the pronominal row. English you is a possible usted reading; not evidence of impersonal se.



## pt / o — reject

Ele mente para você o tempo todo.

He lies to you all the time.

[('connector', 'o'), ('c', 'tempo todo')]

Article structure is real, but o tempo todo is a fixed expression; poor generic article exemplar.



## pt / o — reject

Eu quero que o senhor vá com ele.

I want you to go with him.

[('connector', 'o'), ('c', 'senhor')]

O senhor is polite address here; a bare noun-slot highlight hides its learner-relevant function.



## pt / de — reject

Não temos medo de pessoas como você.

We aren't scared of people like you.

[('v', 'medo'), ('connector', 'de'), ('c', 'pessoas')]

Medo de is structurally noun-attached, but the row describes ownership/contents/material/purpose; semantic scope mismatch.



## es / que — reject

No creo que jamás he visto antes.

I don't think I've ever seen it before.

[('v', 'creo'), ('connector', 'que'), ('c', 'jamás he visto antes')]

Parser match does not fix the awkward Spanish sentence; do not recommend it as a teaching example.



## es / de — reject

No el... horrible goulash de tu madre.

Not your... slut mother's goulash.

[('v', 'goulash'), ('connector', 'de'), ('c', 'tu madre')]

Fragment and mismatched translation make the example unsuitable despite a noun + de attachment.



## es / lo — reject

Lo hiciste muy bien en allí.

You did great in there.

[('connector', 'Lo'), ('v', 'hiciste')]

Lo + verb span is sound but en allí is awkward; reject the sentence as teaching copy.
