# Second matching pass and staging trial



Rules are a separate v2; the v1 bridge and its frozen evaluation remain unchanged. No gold or holdout inputs were read. No production assignment process is enabled.



## Changes



- Verb chunks retain auxiliaries, intervening modal governors and licensed direction particles.

- Noun chunks retain dependency-linked modifiers. A trailing comparison with contradictory attachment causes abstention rather than truncation.

- Noun-attached de now abstains until the semantic relation is established; noun attachment alone cannot prove the displayed explanation.

- Recover finite modal complements after que and a bounded set of motion-verb/destination-noun al constructions.

- Preserve abstention for split nos tokens; no speculative parser correction.



## Further sentence review



24 previously unreviewed development sentences: 12 candidates and 12 abstentions. Decisions: {'hold': 6, 'accept': 6, 'appropriate_abstention': 8, 'missed_match': 4}.

Sample fixed by SHA-256 of v2-review plus example ID: six per language/status, excluding all prior reviewed IDs, source selections and matching texts. This is an assistant editorial check with predictions visible, not independent corpus accuracy or native-speaker validation. Rules were not revised after this sample was inspected. Six candidates are ready for this bounded trial; six remain on editorial hold. Four abstentions miss suitable constructions.



## Staging behaviour



8 reviewed additions: six from the further review and two corrected regression cases. Generated highlights are used verbatim and source metadata retained. Existing examples remain in the cycle. No pattern copy or deck membership changes.

Enable with ?fwSyntaxTrial=1 on staging. Remove that query parameter or set it to 0 to return to the normal examples. Production ignores the parameter. Affected cards display “Reviewed example trial”.



## Still unresolved



Split-token nos; semantic noun-de classification; broader destination nouns; regional Portuguese and context-dependent examples; independent evaluation outside this development pool. These do not silently enter the staged overlay.



### pt / se: hold

Esse se sente incrível.

That feels amazing.

Referent and English correspondence are unclear without context; do not publish as a standalone example.



### pt / o: hold

O Tom está de férias, não é?

Tom is now on vacation, isn't he?

Article before a name is grammatical but adds little variety; proper-name use needs regional context.



### pt / de: hold

"Precisas de ligar imediatamente."

"You need to call right away."

Precisas de + infinitive is European Portuguese; retain for regional review, not default Brazilian trial.



### pt / o: hold

O Tom é cego.

Tom is blind.

Article before a name is grammatical; avoid adding another Tom example without regional context.



### pt / o: hold

Ele mente para mim o tempo inteiro.

He lies to me all the time.

O tempo inteiro is a fixed time expression; structurally a noun phrase but unsuitable as the simplest article demonstration.



### pt / se: accept

O meu namorado não se importa comigo.

My boyfriend doesn't care about me.

Natural pronominal importar-se example; correct contiguous se + importa and faithful translation.



### pt / que: appropriate_abstention

E porque é que eles continuam a respirar?

Then why are they still breathing?

Interrogative é que construction is outside the displayed patterns.



### pt / de: missed_match

Vou encontrar um jeito de fazer isso.

I'll find a way to do it.

Jeito de fazer is a noun plus action construction fitting the purpose/action explanation; v2 deliberately abstains on noun de semantics.



### pt / de: appropriate_abstention

Não está ligado à reunião de ontem.

It's not related to yesterday's meeting.

Temporal noun detail is not covered clearly by the current de explanation.



### pt / se: appropriate_abstention

Não importa se você vence ou não.

It doesn't matter whether you win or not.

Whether clause, not a condition and result.



### pt / de: missed_match

Não posso te impedir de fazer isso.

I can't stop you from doing that.

Impedir de is a governed verb construction; requires fuller verb frame handling.



### pt / que: appropriate_abstention

Eu queria saber o que iria acontecer.

I wanted to know what would happen.

O que question clause is outside the displayed que patterns.



### es / se: accept

¿A qué se refería con "No hay inocencia"?

What did you mean by "No Innocence"?

Referirse is pronominal; imperfect can refer to usted, matching English you. Correct minimal verbal chunk.



### es / lo: accept

Este libro lo compré ayer.

I bought this book yesterday.

Object lo resumes the topicalised book; natural Spanish and accurate translation.



### es / se: accept

Por fin se ha acabado todo.

It is finally all over.

Se ha acabado contains auxiliary plus participle in one generated verb chunk.



### es / se: accept

Las gemelas se ven exactamente iguales.

The twins look exactly alike.

Verse + adjective describes appearance here; pronominal row and translation fit.



### es / se: accept

Olvidé el nombre de tu hermano, ¿cómo se llama?

I forgot the name of your brother; what's his name?

Llamarse is pronominal; natural sentence and faithful translation.



### es / que: hold

Ya te dije que ella no se encuentra.

I already told you that she isn't here.

Statement construction fits, but ella no se encuentra is context-dependent without a place; retain for editorial review.



### es / al: missed_match

Es mejor que yo vuelva al trabajo.

I'd better get back to work.

Volver al trabajo fits to/at the but trabajo is outside the deliberately narrow destination list.



### es / que: appropriate_abstention

¿Hace cuánto tiempo que tienes esta cuenta secreta?

How long have you had this secret account?

Hace tiempo que temporal construction is outside the three que patterns.



### es / de: appropriate_abstention

Fuera de mi casa ahora.

Out of my house now.

Fuera de is a phrase, not the displayed noun/verb pattern.



### es / de: appropriate_abstention

No cabe la menor duda de que Yanni es inocente.

There is absolutely no doubt that Yanni is innocent.

Duda de que complement is outside the explicitly listed semantic de scope.



### es / se: missed_match

Esta se ve reciente.

This one looks recent.

Se ve describes appearance and fits pronominal se; retained label/parser conflict causes abstention.



### es / que: appropriate_abstention

Piensa lo que quieras.

Think what you want.

Lo que free relative is outside noun-antecedent relative and thought-plus-statement patterns.
