# Separate-source function-word check



48 unseen harvest sentences, 24 per language, four per pilot word. 10 assignments; 38 abstentions. 10 assigned patterns agree with the blind reviews. 6 assignments have exact chunk agreement.



## What is independent



All previously selected sentence IDs and their normalized source text were excluded across every card in the pinned selection files. This excludes the old holdout pool without opening its file. Prior audit/source-pool/suite text was also excluded. The new sample uses the same underlying harvest corpora, not a new corpus or external validation source. Four sentences per word were selected by deterministic hash ranking before parsing/review, with one focus occurrence and 4–18 whitespace tokens. This small, balanced sample does not estimate overall corpus accuracy.



Portuguese and Spanish Sol reviewers saw only sentences, translations and teaching patterns. They did not see predictions or matcher code. Reviews are AI editorial judgments, not human/native-speaker gold. The matcher and upstream labeller code were hashed at sampling and held fixed throughout evaluation. Fresh parsers and current dictionary labellers were run; unlike the earlier retained-label trial, no historical reflexive-decision cache was supplied. Results describe this combined fresh pipeline.



## Routing



reviewed_ready means agreement on pattern and exact chunks plus passing naturalness, translation and standalone suitability. It requires independent review, not merely parser confidence. review_required retains any disagreement or quality hold. unassigned preserves matcher abstentions, including missed supported constructions. No row is inserted into a deck or published.



Exact chunk disagreement is a review signal: a reviewer may prefer a wider span than the teaching formula requires. It is not automatically counted as a grammar error.



## Results by language



{
  "pt": {
    "route": {
      "unassigned": 20,
      "review_required": 4
    },
    "pattern_fit": {
      "appropriate_abstention": 10,
      "missed": 10,
      "supported": 4
    },
    "spans": {
      "not_applicable": 20,
      "review_required": 2,
      "exact_agreement": 2
    }
  },
  "es": {
    "route": {
      "unassigned": 18,
      "review_required": 6
    },
    "pattern_fit": {
      "appropriate_abstention": 9,
      "supported": 6,
      "missed": 9
    },
    "spans": {
      "not_applicable": 18,
      "review_required": 2,
      "exact_agreement": 4
    }
  }
}



## Findings and next priorities



- Pattern matching alone is not example quality. Subtitle translations can add, omit or change meaning, and valid dialogue may be a poor standalone teaching sentence.

- Investigate full complement boundaries: depende de lo que recuerdes currently highlights only recuerdes after de.

- Adjudicate minimal versus full chunks for relative antecedents, reported-speech verb chains and al + infinitive objects before changing extraction rules.

- Coverage is limited. Review missed supported uses, especially contractions and parser-disputed clitics, before extending the matcher to all function words.

- Do not tune against this sample and continue calling it independent. Any subsequent fixes need another untouched sample.



## Source attribution



Every record retains source identifiers, licence and attribution. Subtitle data comes from [OpenSubtitles.org](http://www.opensubtitles.org/) via OPUS; Tatoeba records retain sentence links and CC BY attribution. No source sentence or translation was rewritten.



### pt / de — unassigned

Três dos meus amigos, além de mim, foram autorizados para entrar no bar.

Three of my friends, besides me, were admitted to the bar.

Pattern: unassigned; review: [].

The targeted de belongs to the fixed expression além de, not either taught pattern. Autorizados a entrar is more idiomatic than autorizados para entrar in everyday Brazilian Portuguese.

Besides me presupposes context, and autorizados para entrar is less idiomatic than autorizados a entrar in Brazilian Portuguese.

Reasons: Generic de label does not establish either displayed attachment.



### pt / de — unassigned

Talvez tivesse enviado estas como cópias de segurança.

Fuck. Maybe she sent these as backup.

Pattern: unassigned; review: [1].

De segurança specifies the purpose/type of cópias. The omitted subject and estas require context; tivesse enviado sounds more literary or European than everyday Brazilian talvez tenha enviado. The English adds an unsupported expletive and specifies she.

Estas and the omitted sender have unresolved referents; the verb form also needs a clearer conversational Brazilian setting.

Reasons: Noun attachment alone cannot establish the ownership/contents/material/purpose scope of this card.



### pt / de — unassigned

Vi muita coisa de realidade virtual e penso sempre ser interessante.

I've seen a lot of VR stuff, and it's always, like, "Oh, wow! This is so interesting,"

Pattern: unassigned; review: [1].

The noun modifier identifies the subject/type of coisa, within the broad adding-a-detail pattern. Penso sempre ser interessante is stiff and unclear in everyday Brazilian Portuguese; the English expands it into a vivid quoted reaction.

The final clause is stiff and unclear, distracting from an otherwise usable noun modifier.

Reasons: Noun attachment alone cannot establish the ownership/contents/material/purpose scope of this card.



### pt / de — unassigned

Ele salta para cima de outra e obriga-a a ajudar.

He'll just slide another girl on his dick, make her help out.

Pattern: unassigned; review: [].

De is part of the spatial expression para cima de, not verb-selected de or an ordinary noun-detail construction. Outra needs a contextual referent; obriga-a is formal/European in conversational register. The English introduces explicit sexual content and describes a materially different action.

Outra has no explicit referent; the construction and clitic placement are a poor fit for an everyday Brazilian card.

Reasons: Generic de label does not establish either displayed attachment.



### pt / que — unassigned

O que uma comunista teria em comum com dois pilotos?

Not sure what a red-ragger would have in common with a couple of RAAF pilots, Sir.

Pattern: unassigned; review: [].

O que is interrogative what, outside all three que patterns. The Portuguese is natural; the English adds uncertainty, RAAF and Sir, requiring wider subtitle context.

The unexplained pairing of a communist and two pilots presupposes a narrative setting.

Reasons: No supported structural rule in this first pass.



### pt / que — review_required

Sim, quero encontrar um africano que me leve, pelo interior, à minha aldeia.

Yes, I want to find an African to take me inland to my village.

Pattern: 1; review: [1].

Que introduces a relative clause modifying africano. Grammatically natural, though aldeia and the setting depend on narrative context; commas around pelo interior are optional.

The African journey and minha aldeia require a specific narrative setting; parenthetical commas add complexity.

Reasons: Generated chunks differ from blind reviewer chunks; needs adjudication, not assumed incorrect.; standalone_teaching: hold



### pt / que — review_required

Quero fazer fortuna no ramo das peles e ouvi dizer que é o homem certo.

I want to make my fortune in the fur trade and I hear you're the man to help me do it.

Pattern: 0; review: [0].

Ouvi dizer que introduces reported information. É can address você with the subject omitted; the English help-me-do-it expansion is a reasonable contextual rendering of homem certo.

The fur-trade setting and omitted addressee of é o homem certo make this a narrative-heavy example.

Reasons: Generated chunks differ from blind reviewer chunks; needs adjudication, not assumed incorrect.; standalone_teaching: hold



### pt / que — unassigned

Que faria você se perdesse o seu emprego?

What would you do if you lost your job?

Pattern: unassigned; review: [].

Initial Que is interrogative what, not a statement linker, relative or comparison. Que faria você is grammatical but literary/formal; everyday Brazilian Portuguese favors O que você faria.

The inverted Que faria você is literary compared with everyday Brazilian O que você faria.

Reasons: Conjunction label lacks a matching complement-clause attachment.



### pt / se — unassigned

- Se ele cooperar e falar, podemos seguir essa pista até ao topo.

If we can get them to talk, we could follow that lead all the way up to the top.

Pattern: unassigned; review: [0].

Clear conditional with both condition and consequence. Até ao topo is characteristically European; Brazilian usage usually até o topo. English changes the condition to getting them to talk and shifts can to could.

Essa pista and topo are figurative references needing context; até ao also departs from default Brazilian usage.

Reasons: Conditional clause structure is not established.



### pt / se — unassigned

Estou à espera da confirmação dele para saber se o carregamento chega hoje à tarde.

I just spoke with Reynaldo in Colombia. I'm waiting for his confirmation to see if the shipment is arriving later today.

Pattern: unassigned; review: [].

Se means whether in an embedded question after saber, not conditional if or a reflexive/lexical pronoun. The Portuguese is acceptable in Brazil, though estou esperando is more conversational. English adds an entire unsupported sentence about Reynaldo and Colombia.

Dele and the expected shipment presume prior context; a shorter explicit subject would teach more cleanly.

Reasons: Embedded whether clause, not the displayed condition/result.



### pt / se — unassigned

Negra como o ás de espadas, como se costuma dizer.

Black as the ace of spades, as they say.

Pattern: unassigned; review: [].

Se in como se costuma dizer marks an impersonal/generalized construction, not a reflexive or lexically pronominal verb. The fragment is conventional but needs an antecedent; negra can describe a feminine noun, and a person-directed reading warrants contextual editorial review.

A fragment with no referent for negra; the simile may distract or become inappropriate depending on its referent.

Reasons: Se needs agreement, valency and reflexive/passive checks; parser-label conflict is unresolved.



### pt / se — unassigned

Não uma ocupação para a qual se penda naturalmente, imagino eu.

Not an occupation one drifts into, I imagine, undertaking.

Pattern: unassigned; review: [].

Se is an impersonal subject marker with pender, outside the taught patterns. The Portuguese lacks an expected copula and uses an awkward literary formulation; one would expect Não é uma ocupação.... English undertaking may name the occupation but that information is absent from this isolated Portuguese fragment.

The missing copula, literary wording and unspecified occupation make the isolated fragment unsuitable.

Reasons: Se needs agreement, valency and reflexive/passive checks; parser-label conflict is unresolved.



### pt / o — unassigned

E o que fizemos aqui foi especial.

And what we did here was specia l.

Pattern: unassigned; review: [].

O que means what/that which as a nominal relative construction; o is neither a masculine noun article nor an object clitic here. Portuguese is natural; English specia l contains a visible spacing error.

O que fizemos aqui depends on an unspecified shared event and location.

Reasons: Article/object evidence does not fit the displayed formula.



### pt / o — review_required

Quando coloquei o anúncio, achei que ficaria feliz por achar algo.

When I bought that ad, I was so sure I'd be glad to find anything.

Pattern: 0; review: [0].

O is the masculine singular article before anúncio. Brazilian Portuguese is natural. English bought that ad adds a purchase and strong certainty absent from coloquei o anúncio, achei.

The advertisement and the unspecified something sought require context, while the two subordinate clauses add unnecessary load.

Reasons: translation: hold; standalone_teaching: hold



### pt / o — unassigned

Vais fazer o que quiseres, quando quiseres.

Owie, you can now. You're gonna do what you want when you want.

Pattern: unassigned; review: [].

O que is a nominal relative meaning what, outside the two o patterns. Vais and quiseres are standard European and some regional Brazilian tu usage, not the default everyday Brazilian register. English adds a separate utterance and name absent from Portuguese.

Default Brazilian register mismatch from vais/quiseres; also begins from an unstated situation granting freedom.

Reasons: Article/object evidence does not fit the displayed formula.



### pt / o — unassigned

Ele correu o mais rápido que seus membros podiam carregá-lo.

He ran as fast as his limbs could carry him.

Pattern: unassigned; review: [].

Targeted o belongs to the degree expression o mais rápido, not an article before a noun or an object clitic; carregá-lo is a separate token. O mais rápido que seus membros podiam carregá-lo is an awkward calque; Brazilian Portuguese would normally use tão rápido quanto... or o mais rápido que podia.

The degree construction is a malformed, distracting calque and unsuitable as a model sentence.

Reasons: Article/object evidence does not fit the displayed formula.



### pt / nos — unassigned

É uma grande oportunidade para nos conhecermos melhor.

Oh, this is a great opportunity for us to get to know each other.

Pattern: unassigned; review: [0].

Nos is a first-person plural object pronoun, here reciprocal each other. It fits the broad us/object pattern, though the teaching rule should explicitly mention the reciprocal reading. Natural Brazilian Portuguese.



Reasons: Nos contraction/object interpretation not established.



### pt / nos — unassigned

Andou a passear fora da nossa janela todos os dias nos últimos 2 meses.

She's been hanging around outside our window every day for the last couple of months.

Pattern: unassigned; review: [1].

Nos is em + os before a masculine plural time expression; include últimos 2 in the noun phrase. Andou a passear is European; Brazilian speech favors ficou andando/passeando. Passear implies strolling whereas hanging around may merely mean lingering.

European andou a passear and an unspecified subject make this unsuitable for default Brazilian teaching.

Reasons: Parser split or merged the focus token; do not guess the contraction/pronoun reading.



### pt / nos — review_required

O espectáculo de domingo não nos dará o estatuto real.

Sunday's show won't give us the real estate.

Pattern: 0; review: [0].

Nos is the indirect object to us. Espectáculo and estatuto are European spelling/lexical choices; estatuto real needs context even there. Real estate means property, not estatuto real, so the translation exposes a substantive mistranslation.

European spelling and opaque estatuto real obscure the intended meaning; the aligned translation is substantively wrong.

Reasons: naturalness: hold; translation: fail; standalone_teaching: fail



### pt / nos — unassigned

Entretanto, cabe-nos decidir o que fazer.

In the meantime, it is up to us to decide what to do.

Pattern: unassigned; review: [0].

Enclitic nos means to us with caber; include the actual verb-before-clitic order despite the displayed formula. Cabe-nos is correct but formal for everyday Brazilian speech; cabe a nós or a gente decide is more conversational.

Cabe-nos is formal for everyday Brazilian usage, and entretanto assumes a preceding contrast.

Reasons: Parser split or merged the focus token; do not guess the contraction/pronoun reading.



### pt / naquele — unassigned

Estás naquele momento em que tudo está perfeitamente calmo... Mesmo antes de começares prestes a cair.

You're in that moment where everything is perfectly still... right before you're about to fall.

Pattern: unassigned; review: [0].

Naquele momento clearly fits the time use. Estás/começares are European or regional tu forms, and antes de começares prestes a cair is malformed: antes de estares prestes a cair would be grammatical. English conveys the apparent intent but cannot validate the malformed ending.

Malformed final clause and European/regional tu forms make the sentence unsuitable as a Brazilian model.

Reasons: Parser split or merged the focus token; do not guess the contraction/pronoun reading.



### pt / naquele — unassigned

A Inteligência Artificial aprende determinado idioma lendo incontáveis exemplos diferentes de frases bem construídas naquele idioma.

Artificial Intelligence learns a given language by reading countless different examples of well-constructed sentences in that language.

Pattern: unassigned; review: [0].

Naquele combines em + aquele before masculine singular idioma. Natural expository Brazilian Portuguese; capitalization of Inteligência Artificial is stylistic.

Grammatical but long and conceptually dense for a simple connector card; a shorter example would isolate naquele idioma.

Reasons: Parser split or merged the focus token; do not guess the contraction/pronoun reading.



### pt / naquele — unassigned

Eles souberam naquele momento.

They knew right away.

Pattern: unassigned; review: [0].

Clear temporal naquele momento. Souberam naturally means found out/came to know; knew right away can fit a narrative context but adds immediacy beyond at that moment.

What they learned and which moment are both unstated, so the isolated example conveys little.

Reasons: Parser split or merged the focus token; do not guess the contraction/pronoun reading.



### pt / naquele — unassigned

Vire à esquerda naquele corredor.

Head left down that corridor.

Pattern: unassigned; review: [0].

Clear place reference with em + aquele. Natural Brazilian direction; English head left down gives a slightly freer but acceptable directional rendering.



Reasons: Parser split or merged the focus token; do not guess the contraction/pronoun reading.



### es / de — unassigned

Eso fue cuando sus padres tenían algo de dinero.

This was back when her parents had a little money.

Pattern: unassigned; review: [].

Natural and broadly understandable. Algo de is a quantity expression (some/a little), not either taught de pattern; her is one possible contextual reading of sus.

Eso and sus require narrative reference; the target quantity use also falls outside the supplied patterns.

Reasons: Generic de label does not establish either displayed attachment.



### es / de — unassigned

Ja ja ja, de verdad que eres malo para guardar secretos.

A-hahaha, you really are bad at keeping secrets.

Pattern: unassigned; review: [].

Natural colloquial Spanish. De verdad is an adverbial expression meaning really, not verb + de or noun + de.



Reasons: Generic de label does not establish either displayed attachment.



### es / de — review_required

Todo depende de lo que recuerdes.

All depends on how much you can remember.

Pattern: 0; review: [0].

Depender de clearly supports the verb pattern. The Spanish means what you remember; the English shifts this to how much you can remember and is slightly awkward without It.



Reasons: Generated chunks differ from blind reviewer chunks; needs adjudication, not assumed incorrect.; translation: hold



### es / de — unassigned

El que sigue es el hombre elegido para ser el oponente de Ares.

Next, the presentation fighter to the next point Arès.

Pattern: unassigned; review: [1].

Natural announcement in context. Oponente de Ares adds a relational detail to a noun. The English is garbled and does not convey the selected opponent.

The selected man, next participant and named Ares rely on a narrative setting; the supplied translation is unusable.

Reasons: Noun attachment alone cannot establish the ownership/contents/material/purpose scope of this card.



### es / que — unassigned

No te estás metiendo en mi camino. Es solo que... Es mi responsabilidad.

Just more cheap beer and pizza than usual.

Pattern: unassigned; review: [].

Natural interrupted dialogue; es solo que introduces an explanation and is outside the three taught que uses. The English is unrelated.

Interrupted explanation, ellipsis and narrative references make a poor standalone card; the supplied translation is unrelated.

Reasons: No supported structural rule in this first pass.



### es / que — review_required

Espero que no queden dudas.

I hope that is unquestionable.

Pattern: 0; review: [0].

Clear hope + que clause, natural throughout the Spanish-speaking world. The English roughly conveys certainty but changes I hope no doubts remain into a claim being unquestionable.



Reasons: translation: hold



### es / que — unassigned

- No olvidemos que su candidato perdió.

Let's just not forget, his candidate lost.

Pattern: unassigned; review: [0].

Natural negative exhortation. Olvidar + que is a cognitive statement complement, within the thinking/knowing family; su needs context for his, her, their or your.

Su candidato has an unresolved possessor, and the exhortation presupposes an ongoing political discussion.

Reasons: Clause governor is outside the thought/speech pattern scope.



### es / que — unassigned

Ahí tomamos un barco que nos lleve a Quito.

From there, we get on a boat and we go down to Quito.

Pattern: unassigned; review: [1].

Clear relative clause modifying barco; the subjunctive naturally describes the boat needed for the plan. English flattens that intended destination into an actual journey and adds down. A boat reaching inland Quito requires special narrative context.

Ahí and the journey plan need context, while reaching Quito by boat is geographically distracting.

Reasons: Relative label has no confirmed noun antecedent.



### es / se — unassigned

Jesse se lleva bien con todas.

Jesse gets along with everybody.

Pattern: unassigned; review: [0].

Llevarse bien con is a pronominal construction, so the full expression matters. Todas refers to an understood feminine group; everybody is acceptable in that context.

Todas requires an understood feminine group; Jesse alone does not supply that reference.

Reasons: Se needs agreement, valency and reflexive/passive checks; parser-label conflict is unresolved.



### es / se — unassigned

Me temo que se equivoca.

I'm afraid you're mistaken.

Pattern: unassigned; review: [0].

Equivocarse is pronominal. Natural polite/formal address if the subject is usted; he or she is also possible from context.



Reasons: Se needs agreement, valency and reflexive/passive checks; parser-label conflict is unresolved.



### es / se — review_required

Tírala un poco así se empareja

Pull it along a bit and get it sort of squared up.

Pattern: 0; review: [0].

Pronominal change of state: it becomes even/aligned. Colloquial Latin American emparejarse and tirar for pull are understandable; a comma before así and final punctuation would improve presentation. This is not impersonal se.

The object of tírala is unresolved, así depends on a demonstrated action, and punctuation is incomplete.

Reasons: standalone_teaching: hold



### es / se — unassigned

Cielo, en lo que al matrimonio se refiere, estáis vosotros solos.

Oh, honey, when it comes to marriage, you're really kind of on your own.

Pattern: unassigned; review: [0].

Referirse a occurs in the fixed topic expression en lo que a ... se refiere. The pronominal verb supports pattern 0, not impersonal se. Estáis/vosotros signals Spain; natural with a couple being addressed.

The couple addressed is unresolved, and the topic idiom plus vosotros adds distracting complexity for a basic se card.

Reasons: Se needs agreement, valency and reflexive/passive checks; parser-label conflict is unresolved.



### es / lo — review_required

"¿Por qué no lo hacemos y tratamos de crear estas cosas?

"You know, why don't we go ahead and try and make one of these things?

Pattern: 1; review: [1].

Lo refers to an understood action/idea. Natural speech despite an unmatched opening quotation mark. English one of these things narrows Spanish these things, though the overall proposal is similar.

Lo has no standalone antecedent, estas cosas is unspecified, and the opening quotation mark is unmatched.

Reasons: translation: hold; standalone_teaching: fail



### es / lo — unassigned

Creen que Marina Mills no era su nombre real. ¿Estás seguro que lo es?

'They don't even think that Marina mills was her real name.' uh, are you serious?

Pattern: unassigned; review: [1].

Lo substitutes for the predicate su nombre real, an anaphoric idea covered by that. Colloquial seguro que is broadly understandable, with seguro de que preferable in careful prose. English are you serious is not the same question as are you sure it is, so context is needed.

The two-sentence identity exchange and anaphoric predicate lo add complexity, alongside the held translation and informal seguro que.

Reasons: Article/object evidence does not fit the displayed formula.



### es / lo — unassigned

¿Cuántas veces os lo tengo que explicar?

How many times do I have to explain it to you?

Pattern: unassigned; review: [1].

Lo is the thing/idea explained and climbs before the full tener que explicar construction. Os is informal plural address in Spain; natural and accurately translated.

Lo has no antecedent identifying what must be explained; the sentence clearly needs a prior discussion.

Reasons: Intervening verb-complex material requires a complete verb-phrase span.



### es / lo — unassigned

Todo lo que tenemos que hacer es cuidar que su fondo de guerra permanece vacío.

All we have to do is see to it that his war chest remains empty.

Pattern: unassigned; review: [].

Lo que is a nominal relative construction, outside lo + adjective and object-pronoun lo + verb. The intended meaning matches the English, but cuidar que ... permanece is poor Spanish here: cuidar de que/asegurarse de que ... permanezca is needed; fondo de guerra also sounds literal.

The awkward mood and verb construction need repair, su is unresolved, and nominal-relative lo is outside the supplied patterns.

Reasons: Article/object evidence does not fit the displayed formula.



### es / nos — unassigned

Entrenador, nos vemos en la concentración.

Coach, I guess I'll be seeing you at mini-camp.

Pattern: unassigned; review: [].

Natural reciprocal nos vemos means see each other/see you, rather than the taught object us/to us construction. Concentración is a sports training gathering; mini-camp is context-specific but plausible.

The sports gathering is assumed context, and reciprocal nos falls outside the supplied us/to us pattern.

Reasons: Nos contraction/object interpretation not established.



### es / nos — unassigned

Supongo que sintió que nos estábamos acercando.

My guess, he sensed we were closing in.

Pattern: unassigned; review: [].

Nos belongs to pronominal acercarse (we were approaching), not an object meaning us/to us. Natural wording and an accurate contextual English rendering.

The inferred subject of sintió and the situation being approached are unresolved; embedded clauses add complexity.

Reasons: Nos contraction/object interpretation not established.



### es / nos — review_required

Razón por la que debemos continuar con la única pista que nos dio Nassar.

Which is why we need to press on with the only lead Nassar gave us.

Pattern: 0; review: [0].

Nos is the indirect object to us in Nassar gave us a lead. Natural continuation fragment in dialogue; the English preserves that discourse structure.

Razón por la que is a discourse continuation fragment with an unspecified lead and narrative named character.

Reasons: standalone_teaching: hold



### es / nos — unassigned

Nos tenemos el uno al otro, ¿vale?

We got each other, okay?

Pattern: unassigned; review: [].

Nos is reciprocal, explicitly reinforced by el uno al otro, rather than the taught us/to us object use. Natural supportive dialogue; vale is especially associated with Spain.

Who the reciprocal pair are is unstated, and the supported construction is outside the supplied us/to us pattern.

Reasons: Nos contraction/object interpretation not established.



### es / al — unassigned

No se lo digas al jefe.

Don't tell the boss.

Pattern: unassigned; review: [0].

Al is a + el marking the recipient to the boss, so the to/at the rule applies even though the formula calls the slot a destination. Natural and accurate.

Lo refers to unspecified information, and se lo introduces an additional pronoun construction alongside al.

Reasons: Need destination versus personal-a/recipient evidence; no forced assignment.



### es / al — unassigned

Solo el rey puede llamar al Guardián.

Only the King summons the Guardian.

Pattern: unassigned; review: [].

Al contracts the personal a plus el before the animate direct object of llamar. Here it does not mean to/at the and is not a destination; neither taught pattern explains this use. English summons is a natural contextual translation, though puede adds can/authority.

The king and capitalized Guardian assume a fictional setting; personal a also falls outside the supplied to/at the pattern.

Reasons: Need destination versus personal-a/recipient evidence; no forced assignment.



### es / al — unassigned

Comemos tres veces al día.

We eat a meal three times a day.

Pattern: unassigned; review: [].

Al día is a frequency expression meaning per day/a day. It is neither to/at a destination nor al + infinitive. Natural Spanish and English.



Reasons: Time/rate noun: generic al label is not destination evidence.



### es / al — review_required

Al beber un purgante, es mejor mantenerse en casa.

When drinking a laxative, it's best to stay home.

Pattern: 1; review: [1].

Clear temporal al + infinitive construction, with its object included. Broadly understandable; tomar un purgante and quedarse en casa would be more usual choices in some regions, but the given wording is acceptable.



Reasons: Generated chunks differ from blind reviewer chunks; needs adjudication, not assumed incorrect.
