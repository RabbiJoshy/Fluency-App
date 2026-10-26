# Decision 0033 — A form shares its word's card unless it is privileged

26 October 2026. Replaces decision 0031's visible-sense groups for study
grouping. Decisions 0028 (contractions) and 0029 (noun number needs a proof)
still apply. Card identity is unchanged: a card is still its surface form.

## Why 0031 had to go

0031 merged two forms only when the meanings left on their card backs were
identical. Until WSD is close to perfect, which sense survives on a form is
partly noise, so one verb split into many groups with no visible reason. On
the live DECIDE-1 Portuguese deck, 505 verbs with several forms made 1,203
groups: *ter* 18, *dar* 17, *matar* 3 (matei/mataram…, matou/matado…,
matar/mataria). Wiktionary also gives every form of a verb the whole lemma
menu (all 16 meanings of *ter* on all 43 forms), so the menu itself rarely
says which forms are special.

## Rule

Every form of a word shares one card. A form keeps its own card only when it
is **privileged**: a meaning that is not the plain word carries real usage on
it, at least 3 published examples and 10% of the form's examples (10% of its
frequency when counts are absent), the same bar as the *-se* companion rule.
A meaning counts as not the plain word when it is:

1. **Another word** spelled the same, judged over all that word's senses
   together: *fui*/*foi* (ir and ser), *mato* "bush", *tá* "OK", *fue*.
2. **Another part of speech** of the same headword: *feito* adjective,
   *poder*/*poderes* noun, *obrigado* interjection.
3. **Restricted by the dictionary to some forms**: a sense tagged impersonal
   or third-person counts only on a third-person form, an imperative sense
   only on an imperative form. It counts only when the word's other forms
   rarely use it (under 10%), so *haver* "there is", the main use of every
   form, privileges none. Portuguese: *há*, *tem*, *faz*, *dá*, *dava*.
4. **Filed on the form's own dictionary page** and not merely the base word
   re-glossed for that form. SpanishDict gives *hay* its own page ("there
   is"); *pensé* also has one, but every sense carries tense and person marks
   ("I thought; preterite indicative; first person singular"), and *dime*'s
   glosses an attached pronoun ("tell me"), so neither counts.
5. **Concentrated on this form**: at least 5 examples, 30% of the form, and
   under 5% across the word's other forms (*vamos* "let's", *viene* "next",
   *hacía* "ago"). This is the test most exposed to WSD noise; it does not
   apply to reflexive senses (the *-se* companion rule decides those) or to
   nouns (0029's proof decides number).

The reasons Wiktionary does not tag, politeness and mood forms (*queria*,
*podría*), discourse words (*sabe?*, *digamos*) and imperative interjections,
reach a card only through test 5.

**Not privileges.** Expressions are their own study items: *há quanto tempo*,
*está bem*, *no sé* no longer keep *há*, *está*, *sé* apart, which retires the
frozen-form veto for grouping. Auxiliary uses (*vou* + verb, *tenho que*)
stay sub-rows of the shared card. Reflexive headwords are the base word
(*irse* is *ir*, *matar-se* is *matar*); an unhyphenated *-se* is stripped
only when the base headword is on the same menu.

## Provider parity

The rule reads fields both providers fill: headword, part of speech,
published counts, and `sense_metadata` features. Wiktionary supplies
`grammar_tag` (impersonal, third-person, imperative) and the form's
`surface_mark`s; SpanishDict supplies `sense_mark`s and own-page references
(`spanishdict-menu:<page>:<id>`). SpanishDict shortens one sense's id
differently on different forms (*tener* "to have" is 9b652 on *tiene*, 9b6529
on *tengo*), so ids on one page match when one is a prefix of the other;
senses read from a form's own page have no sibling to compare with and stay
out of test 5.

## Result on the live decks

| | Portuguese DECIDE-1 | Spanish r6 |
|---|---|---|
| Cards with more than one form | 1,262 | 993 |
| Estimation groups (was) | 6,220 (7,393) | 7,027 (8,948) |
| Kept apart: other word / part of speech | 289 / 195 | 339 / 394 |
| Kept apart: restricted / own page / concentrated | 5 / – / 107 | 7 / 2 / 274 |

*ter*, *matar*, *fazer* are now one card each. 2,125 Portuguese and 3,155
Spanish forms stay apart for the old reasons (unproven noun pairs,
contractions). Known data fault: the Portuguese contraction list includes
*deu*, which keeps it off the *dar* card.

## Implementation

One implementation, in the app: `formPrivilegeVerdicts` in `app/js/vocab.js`
(`lemma-merge-pure`). `scripts/build_form_privilege_merges.cjs` runs it over a
release and writes `form_privilege_rule`, `form_privilege_keys` (surface → word,
or empty) and `form_privilege_reasons` into a new `-fp1` merge overlay, and
repoints config; rebuild the estimation pool afterwards. A release-bound
verdict decides both `lemmaGroupKey` and `lemmaStudyGroupKey`. Decks without
an `-fp1` overlay (artist decks, other releases) keep 0031's behaviour until
built. Thresholds are constants beside the rule; changing one is a rule
version bump and an overlay rebuild.
