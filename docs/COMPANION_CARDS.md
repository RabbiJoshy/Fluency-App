# Companion cards

Implemented in `app/js/vocab.js` and mirrored in
`src/fluency/enrichments/card_rules.py`. The rule uses WSD-attributed lexical
senses, including assigned senses shown under Rarer uses. Unused dictionary
senses, unassigned rows, example-only rows and multiword-expression senses
cannot trigger a split or defeat an exception. Published WSD counts determine
usage shares; legacy rows fall back to their assigned frequencies.

## Different lemmas (polysemy)

- At least four distinct represented lexical sense rows in total.
- At least two distinct base-headword groups, each with at least 10% of the
  represented lexical assignments.
- Pronominal verb headwords are folded into the base verb for this test.
- Each qualifying lemma gets a companion. Three qualifying lemmas produce
  three cards, rather than putting the third major reading on the wrong card.
- Minor lemma groups remain on the primary companion. No represented sense
  is discarded. Existing main-card/rarer-use presentation is retained.

This rule runs first. A polysemy companion retains its lemma's ordinary and
pronominal readings together; it is not recursively split again.

Headword identity is exact after case/Unicode/space normalization and the
language's pronominal suffix handling. The former arbitrary `osae` suffix
stripping is removed: shared trailing letters do not establish a shared lemma.
Provider aliases and false headwords (`hay/haber`, `hacerlo/hacer`, etc.) are
the separate HEADWAY task in `CHAT_ROADMAP.md`.

## Ordinary versus pronominal (Spanish and Portuguese)

For a surface with one base-headword group, create separate companions when
both ordinary and exclusively pronominal senses are represented. There is no
four-sense minimum and no minimum usage share for this rule.

- Verb headwords such as Spanish `irse` or Portuguese `lembrar-se` establish
  a pronominal reading. Portuguese legacy unhyphenated verb headwords are
  also accepted.
- Wiktionary and provider-neutral construction metadata can identify a
  pronominal reading under the same headword: `pronominal`, `reflexive`, or
  the normalized grammar mark `reflexive=true`.
- Passive and impersonal construction marks do not establish a lexical
  pronominal reading. A non-verb ending in `se` is not a pronominal verb.
- A single definition explicitly marked both reflexive/pronominal and
  transitive/ambitransitive/ditransitive is shared, not an exclusive
  pronominal definition; it stays with the ordinary reading.

Keep one combined card if every represented exclusive pronominal definition
matches a represented ordinary definition. Match the complete gloss after
case, punctuation and whitespace normalization. If both rows have semantic
context, that context must match too; grammatical labels alone do not count
as a semantic difference. Any unmatched represented pronominal definition
defeats the exception. This is a deliberately simple heuristic, not a claim
of complete semantic equivalence.

One represented family stays on one card. Unused dictionary rows cannot
supply the missing family. Pronominal companions in additional languages
require a language-specific rule for their citation forms.

## Presentation and verification

Sense identity controls ownership. Metadata/headword matching is the fallback
for rows without identity or unused menu rows. Each companion gets its own
assigned senses, examples, unused menu and Rarer uses. If a companion's only
assigned senses had been hidden by the combined card's rarity threshold,
those senses are promoted so the companion has a usable main meaning.

Study sets, search, word links and vocabulary estimation share the builder.
Multiple companions display their own card numbers and can be visited in
sequence; search can start on the companion containing the focused sense.
Estimation allocates surface frequency by assigned usage on each companion.

Regression coverage: `tests/app/test_companion_rules.py`,
`tests/app/test_card_rules_parity.py`, and `tests/app/test_split_cards.py`.
The live v23 Spanish and Portuguese rows were also checked for Python/app
parity and exactly-once ownership of every represented lexical sense.
