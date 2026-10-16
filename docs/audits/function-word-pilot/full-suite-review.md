# Full-suite copy and slot review

115 patterns. All existing suite members are included; no missing-word candidates were added.

Explicit slotTypes control colour, independently of display wording. Verb phrases can use the verb colour as a whole. Mixed slots and clauses retain side colours. This is display metadata, not an automatic sentence classifier.

Twelve pilot cards retain their reviewed source examples. Other sentence wording, translations and source labels remain unchanged; reviewed slot highlights are updated. These examples are marked as awaiting source review; this extension is not a claim of full sentence calibration.

## pt · de · 0

Before: Verbal Valency — Verb + de + Complement
Required link: the preceding verb governs 'de' before its object or action.

After: Verbs with de — verb + de + noun / verb / pronoun
Some verbs use de to link to what follows. Learn the verb and de together.

Slots: {'v': 'verb', 'c': 'mixed'}. Examples: source-reviewed.



## pt · de · 1

Before: Noun Attribution — Noun + de + Noun / Origin
Nominal binding: connects a head noun to its owner, origin, or material.

After: Adding a detail — noun + de + detail / action
Adds a detail about ownership, contents, material or purpose, including an action: hora de partir = time to leave.

Slots: {'v': 'noun', 'c': 'mixed'}. Examples: source-reviewed.



## pt · que · 0

Before: Clausal Link — Thought / Speech + que + Clause
Subordination: bridges what someone thinks, says, or knows to the statement.

After: Saying what you think — think, say, know or hope + que + what happens
Links what someone thinks, says, knows or hopes to a statement.

Slots: {'v': 'verb', 'c': 'clause'}. Examples: source-reviewed.



## pt · que · 1

Before: Relative Pronoun — Noun + que + Description
Relativization: refers back to a noun while connecting more information.

After: Adding information — noun + que + description
Adds information about the noun.

Slots: {'v': 'noun', 'c': 'clause'}. Examples: source-reviewed.



## pt · que · 2

Before: Comparison — Degree + que + Standard
Comparison: connects the two sides of a degree or quality difference.

After: Comparing — more, less or better + que + what you compare with
Means “than” when comparing people, things or situations.

Slots: {'v': 'phrase', 'c': 'phrase'}. Examples: source-reviewed.



## pt · naquele · 0

Before: Deictic Location — em + aquele + Place / Time
Contraction formula pointing to a distant place or past moment.

After: In / on / at that — naquele + masculine singular noun
Combines em + aquele: “in”, “on” or “at that”. It can refer to places, things or times.

Slots: {'c': 'noun'}. Examples: source-reviewed.



## pt · nos · 0

Before: Object Pronoun — nos + Verb
Pronominal argument: represents 'us / to us' receiving the action of a verb.

After: Us / to us — nos + verb
Refers to us: someone sees or helps us, or tells us something.

Slots: {'v': 'verb'}. Examples: source-reviewed.



## pt · nos · 1

Before: Contraction — em + os + Plural Noun
Contraction of 'em + os' (in / on / at the) before a masculine plural noun.

After: In / on / at the — nos + masculine plural noun
Combines em + os: “in”, “on” or “at the”, before a masculine plural noun.

Slots: {'c': 'noun'}. Examples: source-reviewed.



## pt · se · 0

Before: Condition — Se + Condition , Result
Conditional marker: introduces a hypothetical situation before its consequence.

After: If — se + a possible situation + what happens then
Means “if”: gives a possible situation and what happens then.

Slots: {'v': 'clause', 'c': 'clause'}. Examples: source-reviewed.



## pt · se · 1

Before: Reflexive Clitic — se + Verb of self-action
Reflexive clitic: action reflects back onto the person doing it.

After: Oneself / part of a verb — se + verb
Can mean “oneself”, or belong with a verb such as sentir-se (feel). It does not always mean “oneself”.

Slots: {'v': 'verb'}. Examples: source-reviewed.



## pt · o · 0

Before: Definite Article — o + Masculine Noun
Definite determiner: points to a specific masculine singular noun.

After: The — o + masculine singular noun
Means “the” before a masculine singular noun, such as livro (book).

Slots: {'c': 'noun'}. Examples: source-reviewed.



## pt · o · 1

Before: Object Clitic — Verb + o
Direct object pronoun: replaces a 3rd-person masculine singular object ('him / it').

After: Him / it — o + verb
Refers to “him” or a masculine “it”. These examples place o before the verb; other positions also occur.

Slots: {'v': 'verb'}. Examples: source-reviewed.



## pt · em · 0

Before: Spatial Location — Verb + em + Place
Spatial location: anchors an action or state to an enclosed place, city, or space.

After: Where — verb + em + a place
Shows where something happens or is located.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · em · 1

Before: Temporal Framing — Action + em + Time Period
Temporal framing: situates an event within a month, year, or duration.

After: When — verb + em + a time / period
Places an event in a time period, such as a month or year.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · para · 0

Before: Destination — Verb + para + Destination
Direction and destination: points toward a final physical goal or place of arrival.

After: Where to — verb + para + a place
Shows where someone or something is going.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · para · 1

Before: Purpose — Action + para + Infinitive Goal
Purpose and objective: links an intentional action to what it aims to achieve.

After: What for — verb + para + infinitive (dictionary form)
Links an action to its purpose: what someone wants to do or achieve.

Slots: {'v': 'verb', 'c': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · para · 2

Before: Recipient — Object + para + Recipient
Beneficiary: marks who receives or benefits from something.

After: Who for — noun / noun phrase + para + a person
Shows who something is for.

Slots: {'v': 'noun', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · com · 0

Before: Accompaniment — Verb + com + Companion
Accompaniment: joins an action to the person or entity sharing it.

After: Who with — verb + com + a person
Shows who shares an action or is together with someone.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · com · 1

Before: Instrument and Manner — Action + com + Tool / Manner
Instrument and manner: describes the means used or attitude applied.

After: How / with what — verb + com + a tool / way of doing it
Shows the tool used or the way something is done.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · por · 0

Before: Cause / Motive — Verb / State + por + Motive / Cause
Causal ground: links an emotion, gratitude, or outcome back to its reason.

After: Why — verb / expression + por + a reason
Gives the reason for an action, feeling or result.

Slots: {'v': 'mixed', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · por · 1

Before: Trajectory — Movement + por + Transit Space
Trajectory: marks the path, medium, or space through which motion occurs.

After: Through / along — verb + por + a place
Shows the route or place someone or something moves through.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · no · 0

Before: Spatial / Temporal Location — em + o + Masculine Noun / Place
Contraction of 'em + o' (in the / at the) before a specific masculine noun.

After: In / on / at the — em + o + masculine noun
Combines em + o: “in / on / at the”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · na · 0

Before: Spatial / Temporal Location — em + a + Feminine Noun / Place
Contraction of 'em + a' (in the / at the) before a specific feminine noun.

After: In / on / at the — em + a + feminine noun
Combines em + a: “in / on / at the”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · do · 0

Before: Possession / Origin — de + o + Masculine Noun / Origin
Contraction of 'de + o' (of the / from the) denoting possession, origin, or attribute.

After: Of / from the — de + o + masculine noun
Combines de + o: “of / from the”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · da · 0

Before: Possession / Origin — de + a + Feminine Noun / Origin
Contraction of 'de + a' (of the / from the) denoting possession, origin, or attribute.

After: Of / from the — de + a + feminine noun
Combines de + a: “of / from the”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · como · 0

Before: Manner / Simile — Action + como + Model / Standard
Simile and manner: compares the style or way an action is performed to an archetype.

After: Like / in the same way — verb + como + what you compare with
Compares how something is done with another example.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · como · 1

Before: Capacity / Role — como + Role / Capacity
Capacity and function: specifies the role, profession, or capacity someone acts in.

After: As / in a role — como + a role / job
Shows the role or job someone has in a situation.

Slots: {'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · mas · 0

Before: Contrast — Statement + mas + Counterpoint
Adversative bridge: introduces a contrast, restriction, or unexpected limitation.

After: But — what happens + mas + a contrasting idea
Adds a contrasting idea or an unexpected difference.

Slots: {'v': 'clause', 'c': 'clause'}. Examples: copy-reviewed; source review pending.



## pt · a · 0

Before: Directional Link — Verb + a + Destination
Directional link: points to a target destination or recipient.

After: Where to — verb + a + a place
Points to a destination or recipient.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · a · 1

Before: Definite Article — a + Feminine Noun
Definite feminine article: specifies a singular feminine entity.

After: The — a + feminine noun
Means “the”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · a · 2

Before: Direct Object Pronoun — Verb + a
Direct object pronoun: replaces a singular 3rd-person feminine noun ('her / it').

After: Her / it — verb + a
Refers to “her / it”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · e · 0

Before: Addition — Item / Clause + e + Addition
Copulative coordinator: links equal grammatical items or consecutive actions.

After: And — an item / idea + e + an item / idea
Joins items, ideas or actions.

Slots: {'v': 'mixed', 'c': 'mixed'}. Examples: copy-reviewed; source review pending.



## pt · eu · 0

Before: Subject Pronoun — Eu + Verb (1st Sing)
Subject pronoun: emphasizes or clarifies the first-person singular actor.

After: I — Eu + verb
Means “I”. Names who does the action; the pronoun can often be left out.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · ele · 0

Before: Subject Pronoun — Ele + Verb (3rd Sing)
Subject pronoun: marks a 3rd-person masculine singular actor ('he / it').

After: he / it — Ele + verb
Means “he / it”. Names who does the action; the pronoun can often be left out.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · ele · 1

Before: Prepositional Object — Preposition + ele
Prepositional object: follows prepositions like 'com ele' or 'para ele'.

After: After a preposition — preposition + ele
Refers to him after a preposition: com ele (with him), para ele (for him).

Slots: {'v': 'prep'}. Examples: copy-reviewed; source review pending.



## pt · ela · 0

Before: Subject Pronoun — Ela + Verb (3rd Sing)
Subject pronoun: marks a 3rd-person feminine singular actor ('she / it').

After: she / it — Ela + verb
Means “she / it”. Names who does the action; the pronoun can often be left out.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · um · 0

Before: Indefinite Article — um + Masculine Noun
Indefinite article: introduces an unspecific singular masculine noun.

After: A / an — um + masculine noun
Means “a / an”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · uma · 0

Before: Indefinite Article — uma + Feminine Noun
Indefinite article: introduces an unspecific singular feminine noun.

After: A / an — uma + feminine noun
Means “a / an”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · os · 0

Before: Definite Article — os + Plural Masculine Noun
Definite article: introduces specific masculine plural nouns.

After: The — os + plural masculine noun
Means “the”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · os · 1

Before: Direct Object Pronoun — os + Verb
Direct object pronoun: replaces 3rd-person masculine plural objects ('them').

After: Them — os + verb
Refers to “them”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · as · 0

Before: Definite Article — as + Plural Feminine Noun
Definite article: introduces specific feminine plural nouns.

After: The — as + plural feminine noun
Means “the”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · me · 0

Before: Object Pronoun — me + Verb
Object pronoun: represents 'me / to me' receiving direct or indirect action.

After: Me / to me — me + verb
Refers to “me / to me”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · me · 1

Before: Reflexive Clitic — Verb + -me
Reflexive clitic: action reflects back onto the speaker ('myself').

After: Myself / part of a verb — verb + -me
Can mean “myself”, or belong with a verb, such as lembrar-se (remember). These examples use the after-verb form.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · te · 0

Before: Object Pronoun — te + Verb
Object pronoun: represents 2nd-person 'you / to you' (informal).

After: You / to you — te + verb
Refers to “you / to you”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · lhe · 0

Before: Indirect Object — lhe + Verb
Indirect object pronoun: represents 'to him / to her / to you'.

After: To him / her / you — lhe + verb
Refers to “to him / her / you”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · ao · 0

Before: Direction / Destination — a + o + Masculine Destination / Time
Contraction of 'a + o' (to the / at the) before masculine singular nouns.

After: To / at the — a + o + a place / time
Combines a + o: “to / at the”.

Slots: {'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · ao · 1

Before: Temporal Nexus — ao + Infinitive
Temporal nexus: expresses 'upon doing' or 'at the moment of'.

After: When doing something — ao + infinitive (dictionary form)
Means “when” doing something; followed by the infinitive (dictionary form).

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · à · 0

Before: Destination / Time — a + a + Feminine Destination / Time
Crasis contraction of 'a + a' (to the / at the) before feminine singular nouns.

After: To / at the — a + a + a place / time
Combines a + a: “to / at the”.

Slots: {'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · pelo · 0

Before: Path / Motive — por + o + Masculine Path / Reason
Contraction of 'por + o' (through the / by the / for the).

After: Through / by / for the — por + o + a route / reason
Combines por + o: “through / by / for the”.

Slots: {'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · pela · 0

Before: Path / Motive — por + a + Feminine Path / Reason
Contraction of 'por + a' (through the / by the / for the).

After: Through / by / for the — por + a + a route / reason
Combines por + a: “through / by / for the”.

Slots: {'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · num · 0

Before: Location / State — em + um + Masculine Noun
Contraction of 'em + um' (in a / on a).

After: In / on / at a — em + um + masculine noun
Combines em + um: “in / on / at a”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · numa · 0

Before: Location / State — em + uma + Feminine Noun
Contraction of 'em + uma' (in a / on a).

After: In / on / at a — em + uma + feminine noun
Combines em + uma: “in / on / at a”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · dele · 0

Before: Possession — Noun + dele
Possessive contraction of 'de + ele' (his / of him).

After: His / of him — noun + dele
Shows who something belongs to: “his / of him”.

Slots: {'v': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · dela · 0

Before: Possession — Noun + dela
Possessive contraction of 'de + ela' (her / of her).

After: Hers / of her — noun + dela
Shows who something belongs to: “hers / of her”.

Slots: {'v': 'noun'}. Examples: copy-reviewed; source review pending.



## pt · sem · 0

Before: Privation / Absence — Verb / Noun + sem + Missing Element
Privative preposition: marks absence, exclusion, or lack.

After: Without — noun / verb + sem + what is missing
Shows what is missing or absent.

Slots: {'v': 'mixed', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · sobre · 0

Before: Thematic Topic — Discussion / Thought + sobre + Topic
Thematic marker: introduces the subject matter or topic.

After: About — verb / noun phrase + sobre + a topic
Introduces the topic someone talks or thinks about.

Slots: {'v': 'mixed', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · sobre · 1

Before: Spatial Surface — Position + sobre + Surface
Spatial relation: located on top of a surface ('upon / above').

After: On / above — verb + sobre + a place
Shows that something is on or above a surface.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · até · 0

Before: Terminal Boundary — Movement / Time + até + Limit / Endpoint
Terminal boundary: points to the spatial or temporal stopping point.

After: Until / as far as — verb + até + an endpoint
Shows where a movement ends or how long something lasts.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · até · 1

Before: Scalar Focus — Até + Surprising Subject
Scalar focus particle: emphasizes an extreme case ('even').

After: Even — Até + an unexpected example
Includes an example that may be surprising.

Slots: {'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · porque · 0

Before: Causal Reason — Result + porque + Cause
Causal conjunction: explains the reason or motive behind an action.

After: Because — what happens + porque + a reason
Gives the reason why something happens.

Slots: {'v': 'clause', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## pt · quando · 0

Before: Temporal Subordination — Quando + Time Condition , Main Clause
Temporal subordinator: anchors the action to a specific time or event.

After: When — Quando + a situation , what happens
Connects an event to the time or situation when it happens.

Slots: {'v': 'clause', 'c': 'clause'}. Examples: copy-reviewed; source review pending.



## pt · isso · 0

Before: Neutral Demonstrative — isso + Verb
Neutral demonstrative: refers to a stated fact, concept, or object near the listener.

After: That — isso + verb
Refers to an idea, situation or thing already mentioned or near the listener.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · isto · 0

Before: Immediate Demonstrative — isto + Verb
Neutral demonstrative: refers to an immediate object or idea near the speaker.

After: This — isto + verb
Refers to a thing or idea close to the speaker or being introduced now.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## pt · tudo · 0

Before: Universal Totality — tudo + State / Verb
Universal pronoun: represents the totality of things ('everything / all').

After: Everything — tudo + verb
Refers to everything in the situation.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.

Remaining slot issues: [{'example': 3, 'issue': 'The focus word is an object before no following verb here; this example needs a separate word-order pattern.'}]

## es · de · 0

Before: Verbal Valency — Verb + de + Complement
Required link: preceding verb governs 'de' before its object or action.

After: Verbs with de — verb + de + noun / verb / pronoun
Some verbs use de to link to what follows. Learn the verb and de together.

Slots: {'v': 'verb', 'c': 'mixed'}. Examples: source-reviewed.



## es · de · 1

Before: Nominal Binding — Noun + de + Noun / Origin
Nominal binding: marks possession, origin, content, or material.

After: Adding a detail — noun + de + detail / action
Adds a detail about ownership, contents, material or purpose, including an action: hora de comer = time to eat.

Slots: {'v': 'noun', 'c': 'mixed'}. Examples: source-reviewed.



## es · que · 0

Before: Clausal Link — Thought / Speech + que + Clause
Subordination: bridges what someone thinks, says, or knows to the statement.

After: Saying what you think — think, say, know or hope + que + what happens
Links what someone thinks, says, knows or hopes to a statement.

Slots: {'v': 'verb', 'c': 'clause'}. Examples: source-reviewed.



## es · que · 1

Before: Relative Pronoun — Noun + que + Description
Relativization: refers back to a noun while introducing descriptive detail.

After: Adding information — noun + que + description
Adds information about the noun.

Slots: {'v': 'noun', 'c': 'clause'}. Examples: source-reviewed.



## es · que · 2

Before: Comparison — Degree + que + Standard
Comparison: connects the two sides of a degree or quality contrast.

After: Comparing — more, less or better + que + what you compare with
Means “than” when comparing people, things or situations.

Slots: {'v': 'phrase', 'c': 'phrase'}. Examples: source-reviewed.



## es · a · 0

Before: Directional Goal — Verb + a + Destination
Directional goal: indicates movement toward a place or terminus.

After: Where to — verb + a + a place
Shows where someone or something is going.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · a · 1

Before: Personal 'a' — Verb + a + Person
Personal 'a': marks a specific human or personalized direct object.

After: Before a person — verb + a + a person
Used before a specific person receiving the action, as in veo a Ana (I see Ana).

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · en · 0

Before: Spatial Framing — Verb / State + en + Location
Spatial framing: anchors an action or entity within a place or space.

After: Where — verb + en + a place
Shows where something happens or is located.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · en · 1

Before: Temporal Framing — Action + en + Time Period
Temporal framing: situates an event inside a month, year, or duration.

After: When — verb + en + a time / period
Places an event in a time period, such as a month or year.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · por · 0

Before: Cause / Motive — State / Gratitude + por + Motive / Cause
Causal ground: links an emotion, gratitude, or outcome back to its reason.

After: Why — verb / expression + por + a reason
Gives the reason for an action, feeling or result.

Slots: {'v': 'mixed', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · por · 1

Before: Trajectory — Movement + por + Transit Space
Trajectory: marks the route, medium, or space through which motion happens.

After: Through / along — verb + por + a place
Shows the route or place someone or something moves through.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · para · 0

Before: Purpose — Action + para + Infinitive Objective
Purpose and aim: establishes the intended goal or outcome of an action.

After: What for — verb + para + infinitive (dictionary form)
Links an action to its purpose: what someone wants to do or achieve.

Slots: {'v': 'verb', 'c': 'verb'}. Examples: copy-reviewed; source review pending.



## es · para · 1

Before: Beneficiary / Target — Entity + para + Recipient
Beneficiary / Target: designates the person meant to receive something.

After: Who for — an item / idea + para + a person
Shows who something is for.

Slots: {'v': 'mixed', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · con · 0

Before: Accompaniment — Verb + con + Companion
Accompaniment: joins an action to the companion sharing it.

After: Who with — verb + con + a person
Shows who shares an action or is together with someone.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · con · 1

Before: Instrument and Manner — Action + con + Tool / Manner
Instrument and attitude: describes the tool used or care applied.

After: How / with what — verb + con + a tool / way of doing it
Shows the tool used or the way something is done.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · sin · 0

Before: Absence / Omission — Noun / Action + sin + Missing Element
Privative preposition: marks absence, lack, or omission.

After: Without — noun / verb + sin + what is missing
Shows what is missing or left out.

Slots: {'v': 'mixed', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · se · 0

Before: Reflexive Clitic — se + Verb of self-action
Reflexive clitic: action turns back upon the person doing it.

After: Oneself / part of a verb — se + verb
Can mean “oneself”, or belong with a verb such as sentirse (feel). It does not always mean “oneself”.

Slots: {'v': 'verb'}. Examples: source-reviewed.



## es · se · 1

Before: Impersonal / Passive — se + Verb (Passive/Impersonal)
Impersonal / Passive marker: signals general or collective truth ('one does').

After: Without saying who — se + verb
Describes what happens without naming who does it. Compare se habla (people speak) and se venden libros (books are sold).

Slots: {'v': 'verb'}. Examples: source-reviewed.



## es · me · 0

Before: Object Pronoun — me + Verb
Object pronoun: represents 1st-person 'me / to me' receiving the verb action.

After: Me / to me — me + verb
Refers to “me / to me”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · te · 0

Before: Object Pronoun — te + Verb
Object pronoun: represents 2nd-person 'you / to you' (informal).

After: You / to you — te + verb
Refers to “you / to you”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · nos · 0

Before: Object Pronoun — nos + Verb
Object pronoun: represents 1st-person plural 'us / to us'.

After: Us / to us — nos + verb
Refers to us: someone sees or helps us, or tells us something.

Slots: {'v': 'verb'}. Examples: source-reviewed.



## es · le · 0

Before: Indirect Object — le + Verb
Indirect object pronoun: represents 3rd-person singular 'to him / to her / to you'.

After: To him / her / you — le + verb
Refers to “to him / her / you”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · al · 0

Before: Direction / Goal — a + el + Masculine Destination
Mandatory contraction of 'a + el' (to the / at the) before masculine nouns.

After: To / at the — al + destination
Here, a + el becomes al: “to the” or “at the”.

Slots: {'c': 'phrase'}. Examples: source-reviewed.



## es · al · 1

Before: Temporal Nexus — al + Infinitive
Temporal nexus: expresses 'upon doing' or 'when doing'.

After: When doing something — al + infinitive (dictionary form)
Means “when” doing something: al llegar = when someone arrives.

Slots: {'v': 'verb'}. Examples: source-reviewed.



## es · del · 0

Before: Origin / Attribute — de + el + Masculine Noun / Origin
Mandatory contraction of 'de + el' (of the / from the).

After: Of / from the — de + el + masculine noun
Combines de + el: “of / from the”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · el · 0

Before: Definite Article — el + Masculine Singular Noun
Definite article: designates a specific masculine singular referent.

After: The — el + masculine singular noun
Means “the”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · la · 0

Before: Definite Article — la + Feminine Singular Noun
Definite article: designates a specific feminine singular referent.

After: The — la + feminine singular noun
Means “the”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · la · 1

Before: Direct Object Pronoun — la + Verb
Direct object pronoun: replaces a 3rd-person feminine singular noun ('her / it').

After: Her / it — la + verb
Refers to “her / it”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · los · 0

Before: Definite Article — los + Masculine Plural Noun
Definite article: designates specific masculine plural entities.

After: The — los + masculine plural noun
Means “the”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · los · 1

Before: Direct Object Pronoun — los + Verb
Direct object pronoun: replaces 3rd-person masculine plural objects ('them').

After: Them — los + verb
Refers to “them”. The surrounding verb and sentence show who or what is meant.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · las · 0

Before: Definite Article — las + Feminine Plural Noun
Definite article: designates specific feminine plural entities.

After: The — las + feminine plural noun
Means “the”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · lo · 0

Before: Neuter Article — lo + Adjective / Abstract
Neuter article: nominalizes an adjective into an abstract quality ('the ... thing').

After: The … thing / part — lo + adjective
With an adjective, means “the … thing” or “the … part”: lo importante = the important thing.

Slots: {'c': 'adj'}. Examples: source-reviewed.



## es · lo · 1

Before: Direct Object Pronoun — lo + Verb
Direct object pronoun: replaces a masculine singular item or concept ('it / him').

After: Him / it / that — lo + verb
Refers to “him”, a masculine “it”, or an idea: lo sé = I know that.

Slots: {'v': 'verb'}. Examples: source-reviewed.



## es · un · 0

Before: Indefinite Article — un + Masculine Singular Noun
Indefinite article: introduces a single unspecific masculine noun.

After: A / an — un + masculine singular noun
Means “a / an”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · una · 0

Before: Indefinite Article — una + Feminine Singular Noun
Indefinite article: introduces a single unspecific feminine noun.

After: A / an — una + feminine singular noun
Means “a / an”. Use the form that matches the noun’s gender and number.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · y · 0

Before: Addition — Element + y + Addition
Copulative conjunction: coordinates items, clauses, or thoughts of equal status.

After: And — an item / idea + y + an item / idea
Joins items, ideas or actions.

Slots: {'v': 'mixed', 'c': 'mixed'}. Examples: copy-reviewed; source review pending.



## es · pero · 0

Before: Contrast — Statement + pero + Contrast
Adversative bridge: introduces a qualification, limitation, or unexpected contrast.

After: But — what happens + pero + a contrasting idea
Adds a contrasting idea or an unexpected difference.

Slots: {'v': 'clause', 'c': 'clause'}. Examples: copy-reviewed; source review pending.



## es · si · 0

Before: Condition — Si + Condition , Result
Conditional marker: establishes a hypothesis preceding its outcome.

After: If — Si + a situation , what happens
Gives a possible situation and what happens if it is true.

Slots: {'v': 'clause', 'c': 'clause'}. Examples: copy-reviewed; source review pending.



## es · como · 0

Before: Manner / Simile — Action + como + Standard
Simile and manner: compares action execution against an exemplar.

After: Like / in the same way — verb + como + what you compare with
Compares how something is done with another example.

Slots: {'v': 'verb', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · como · 1

Before: Capacity / Role — como + Capacity / Profession
Capacity and role: designates the status or function held.

After: As / in a role — como + a role / job
Shows the role or job someone has in a situation.

Slots: {'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · mi · 0

Before: Possession — mi + Singular Noun
1st-person singular possessive: introduces something belonging to the speaker.

After: My — mi + singular noun
Shows who something belongs to: “my”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · su · 0

Before: Possession — su + Singular Noun
3rd-person possessive: denotes something belonging to him, her, them, or formal 'you'.

After: His / her / their / your (formal) — su + singular noun
Shows who something belongs to: “his / her / their / your (formal)”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · tu · 0

Before: Possession — tu + Singular Noun
2nd-person informal possessive: introduces something belonging to the listener.

After: Your (informal) — tu + singular noun
Shows who something belongs to: “your (informal)”.

Slots: {'c': 'noun'}. Examples: copy-reviewed; source review pending.



## es · yo · 0

Before: Subject Pronoun — Yo + Verb (1st Sing)
Subject pronoun: explicitly emphasizes or contrasts the 1st-person actor.

After: I — Yo + verb
Means “I”. Names who does the action; the pronoun can often be left out.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · tú · 0

Before: Subject Pronoun — Tú + Verb (2nd Sing)
Subject pronoun: explicitly clarifies or contrasts the 2nd-person actor.

After: you — Tú + verb
Means “you”. Names who does the action; the pronoun can often be left out.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · eso · 0

Before: Neuter Demonstrative — eso + Verb
Neuter demonstrative: refers to a stated matter, idea, or object near the listener.

After: That — eso + verb
Refers to an idea, situation or thing already mentioned or near the listener.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · esto · 0

Before: Immediate Demonstrative — esto + Verb
Neuter demonstrative: refers to an immediate topic or object near the speaker.

After: This — esto + verb
Refers to a thing or idea close to the speaker or being introduced now.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · todo · 0

Before: Universal Totality — todo + State / Verb
Universal pronoun: signifies the totality of matters ('everything / all').

After: Everything — todo + verb
Refers to everything in the situation.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.

Remaining slot issues: [{'example': 3, 'issue': 'The focus word is an object before no following verb here; this example needs a separate word-order pattern.'}]

## es · algo · 0

Before: Indefinite Entity — Verb + algo
Indefinite entity: marks an unspecified thing or amount ('something').

After: Something — verb + algo
Refers to an unspecified thing or amount.

Slots: {'v': 'verb'}. Examples: copy-reviewed; source review pending.



## es · porque · 0

Before: Causal Reason — Result + porque + Cause
Causal conjunction: explains the underlying reason or motive.

After: Because — what happens + porque + a reason
Gives the reason why something happens.

Slots: {'v': 'clause', 'c': 'phrase'}. Examples: copy-reviewed; source review pending.



## es · cuando · 0

Before: Temporal Nexus — Cuando + Time Condition , Main Action
Temporal connector: situates an event at a point in time.

After: When — Cuando + a situation , what happens
Connects an event to the time or situation when it happens.

Slots: {'v': 'clause', 'c': 'clause'}. Examples: copy-reviewed; source review pending.


