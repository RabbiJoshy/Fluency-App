# Findings — reflexive / pronominal tagging (2026-10-04)

## The problem in the live decks

On cards whose menu carries both a pronominal and a non-pronominal reading,
v22 assigns the wrong family to roughly one example in ten. Measured on
hand-labelled stratified samples of the live Stage 04 assignments:

| language | v22 chose | clitic near target | wrong family |
|---|---|---|---|
| es | `X` | yes | 59/191 (31%), held-out 27/107 (25%) |
| es | `Xse` | no | 60/60, held-out 40/40 |
| es | `Xse` | yes | 12/100, held-out 6/60 |
| es | `X` | no | 0/120, held-out 0/64 |
| pt | non-pronominal sense | yes | 51/110 (46%), held-out 45/110 (41%) |
| pt | pronominal sense | no | 45/59 (76%), held-out 55/59 |

Typical errors: *¿No vas a sentarte?* → `sentar`; *No te molestes* →
`molestar`; *Le puse algo de leche* → `ponerse`; *ele virou-se* →
non-pronominal *virar*; *Se chover, iremos* → pronominal sense (the *se* is
"if"). The shipped gate (`se_reflexive_evidence`) only sees a `se` directly
left of the target and abstains on *me/te/nos*: on the blind Spanish set it
finds 51% of pronominal uses.

## Method

Rules over a spaCy parse, with person/number and lemma from Wiktionary
paradigm tables. In order:

1. Locate the clitics that belong to this verb: proclitics; enclitics
   (*siéntate*, *virou-se*, mesoclisis *far-se-á*) validated against the
   paradigm table; clitic climbing through restructuring verbs (*me voy a
   duchar*, *te estás a portar*, *devia ter-me matado*); Brazilian
   aux + clitic + infinitive (*vou me deitar*).
2. Portuguese only: decide whether a *se* is the conjunction "if": agreement
   (a 1st/2nd-person verb cannot take reflexive *se*), mood (conjunction *se*
   never takes the present subjunctive), participles (*se condenado*), a
   subordinator already opening the clause (*Se esse cenário se confirmar*).
3. `me/te/nos/os/vos` are reflexive iff they agree with the verb's controller:
   the finite verb, the restructuring governor, the object of an
   object-control verb (*déjame sentarme*), an imperative's addressee, or a
   small-clause subject (*pessoas me tocando*). Forms ambiguous between 1sg
   and 3sg are resolved by an explicit subject or imperative position, else
   left `BOTH`.
4. 3rd-person *se* is `SE_FIRM` only with positive evidence: imperative,
   animate or preverbal subject outside relative clauses, or a per-lemma prior
   from treebank train splits (≥95% pronominal, n≥5). Otherwise `BOTH`.

spaCy alone is not enough in either language. In Spanish it misses
imperative + *se* and marks almost every merged enclitic as reflexive; in
both languages its morphology on sentence-initial verbs is unreliable
(*Deberías* tagged 1st plural). The paradigm table owns person, number and
lemma.

## Results: precision when it commits

"Errors" are commits that would hard-filter the wrong family. `BOTH` is
never an error: it keeps today's behaviour.

| set | commits | errors | precision | `BOTH` |
|---|---|---|---|---|
| es subtitles, dev (500, tuned on) | 414 | 1 | 99.8% | 8.6% |
| **es subtitles, blind (300)** | 241 | **0** | 100% | 8.7% |
| es AnCora test+dev, expert gold (11,700) | 10,782 | 30 | 99.7% | 7.6% |
| pt subtitles, dev (300, tuned on) | 255 | 0 | 100% | 10.0% |
| pt held-out (300) | 269 | 0 | 100% | 5.7% |
| pt blind 2 (250) | 200 | 1 | 99.5% | 16.4% |
| pt blind 3 (200) | 166 | 1 | 99.4% | 13.0% |
| pt UD test/dev, 4 treebanks (25,542) | 24,113 | 92 | 99.6% | 5.6% |

Honest caveat for Portuguese: held-out, blind 2 and blind 3 were each scored
once on first contact (3/265, 5/196 and 5/168 errors: 98.9%, 97.4%, 97.0%)
and the code was then fixed using what they showed. The fixes were
generalisations, not item patches, but the true first-contact rate for
Portuguese is probably ~98.5–99%, not 100%. Spanish's blind set was never
used for tuning.

The remaining Portuguese errors are a European-Portuguese misspelling
(*arranjas-te* for *arranjaste*) and a middle-voice borderline (*o pedido se
justifica*). A large share of the UD "errors" are annotation conventions, not
mistakes: AnCora and Porttinari tag *se trata de* as impersonal, but both
SpanishDict and Wiktionary file "to be about" under the pronominal entry or
sense; GSD and CINTIL leave *tornou-se*, *mostrou-se*, *ele se acidentou*
without a pronominal label.

## Impact on live v22

| language | examples on pair cards | a hard filter would change | → pronominal | → non-pronominal |
|---|---|---|---|---|
| es | 15,000 (random sample of ~115k) | 1,142 (7.6%) | 1,053 | 89 |
| pt | 28,669 (all) | 1,913 (6.7%) | 1,348 | 565 |

A random 30 of the Spanish changes were all correct; 29 of 30 Portuguese
changes were correct and the one miss (*Vais portar-te*) is fixed.

## What a wrong commit looks like

Usually harmless, because the two menus overlap: a missed *quedarme* lands
on `quedar`, which has "to stay"; *la esperanza se mantiene* forced to
`mantenerse` gets "to remain", which is right anyway. The visible failures
are newswire passives promoted by a prior (*se despidieron dos
seleccionadores* "were sacked" → `despedirse` "to say goodbye"), which is why
the 3rd-person *se* promotion is conservative and relative clauses and
*poder/dever + se* always stay `BOTH`.

## Recommendation for integration

- Hard-filter `NO_SE` and `SE_FIRM`; keep both families for `BOTH`.
- Safety valve: if the surviving family has no plausible sense, fall back to
  the full menu. Some `Xse` entries are thin (`venderse`: only "to sell
  out").
- Spanish filters headwords; Portuguese filters senses by the `pronominal` /
  `reflexive=true` tags. Wiktionary's tags are inconsistent (*tratar* lists
  "to be about" both tagged and untagged), which is harmless for filtering
  but means a tag is not a complete inventory.
- Next languages with the same structure: Czech *se/si*, Polish *się*,
  French *se/s'*, Dutch *zich*.

## Integrated: v23 (2026-10-04)

The tagger is now `src/fluency/reflexive/` and runs as a WSD candidate filter
from the `{es,pt}-v23-1` profiles. Tags are precomputed per freeze by
`scripts/build_reflexive_tags.py` (Spanish parses at ~300 sentences/s on
this machine, not the ~10/s first assumed); `scripts/v23_runs.py` re-scores
only the pair cards and carries every other row from v22.

What the filter does, as shipped:

- Only `NO_SE` and `SE_FIRM` act. `BOTH` and `Z` keep v21's own se-only
  evidence. A first version let `BOTH` clear that evidence; it moved 2,772
  Spanish lines, many wrongly (*que se pruebe los guantes* lost *probarse*).
- Spanish (SpanishDict headwords): the tag keeps `X` or `Xse`.
- Portuguese (Wiktionary senses): `NO_SE` drops senses tagged pronominal;
  `SE_FIRM` drops only senses tagged transitive. Keeping only the tagged
  pronominal senses was worse: Wiktionary leaves many pronominal readings
  untagged (*recusar-se a* "to refuse", *virar-se* "to turn around").

Live effect against a same-inventory baseline (the 10k MWE sieve v21 used was
rebuilt in place on 2026-10-03, so v22 -> baseline is the inventory, baseline
-> v23 the filter):

| | pair-card lines | changed by the filter | by tag |
|---|---|---|---|
| es | 119,431 | 9,369 (7.8%) | SE_FIRM 8,540, NO_SE 829 |
| pt | 40,952 | 1,338 (3.3%) | SE_FIRM 743, NO_SE 595 |

Hand-read: Spanish, 49 of 50 family flips right (the miss: *con seguirte*,
object *te*). Portuguese, of 60 changed lines about 30 better and 10 worse
than v22, the rest neutral; the worse ones are the gloss picking a wrong sense
inside the right family (*se tornar realidade* -> "to return"), which the
family filter cannot fix.
