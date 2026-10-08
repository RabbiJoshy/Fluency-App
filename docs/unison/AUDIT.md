# UNISON part 1 — audit of es and pt speech v23

Read 2026-10-08 by UNISON-1, as a learner sees the cards (app display rules
applied). Nothing was fixed. Josh picks the fix list from this page.

## TL;DR

- v23 picks the right sense 83% of the time in Spanish and 71% in Portuguese
  (blind sample).
- Five fix families cover most errors: **phrases** (~190 cards), **context and
  pills** (~125), **grammar verbs** (~70, a WSD fix), **Portuguese menu gaps**
  (~40), **junk cards** (surface ledger).
- A frozen panel (`research/unison/gold/`) scores any future run.

## What was read

| | Spanish (`es-speech-v23-10000x30-slim`) | Portuguese (`pt-speech-v23-10000x30-slim`) |
|---|---|---|
| Cards read in full | 403: top 300, 100 random from ranks 301–10,000 (seed `unison-1`), 3 seeded (*darte* 701, *irte* 725, *estuve* 742) | 350: top 300 and the first 50 of the 100 random cards (r01–r02) |
| Blind labels (sentence + full menu, v23's choice hidden, never revised) | 1,209 | 1,050 |
| v23 picks the right sense | **1,000 / 1,209 = 82.7%** | **742 / 1,050 = 70.7%** (top 300: 630/900 = 70.0%) |
| v23 at least shows the right English gloss | 90.3% | 73.7% |
| Problem lines (`audit-300.jsonl`) | 442 | 329 |

Portuguese r03–r04 (the other 50 random cards) were not read; Josh asked to
finish. From t02 on, Portuguese card views were read condensed (each row's first
two and two lowest-margin examples; `research/unison/condense.py`), so the
Portuguese "found wrong" set is less complete than the Spanish one. Blind
labels were done in full throughout.

How to read the numbers: "right" means v23's sense is the hand label or a listed
equally-right sense. Phrases the menu lacks, `none:` (the menu has no right
sense) and `not_target:` (proper names, wrong language) count as wrong unless a
listed alternative matches.

## Causes, ranked by cards affected

Counts are cards (sentences in brackets) over both languages. Fix cost is a
rough guess: **S** = a rule or data patch, hours; **M** = a feature or menu
change with a re-run, a day or two; **L** = redesign.

| # | Cause | Cards es / pt (sentences) | Layer | Two examples | Fix cost |
|---|---|---|---|---|---|
| 1 | **Wrong sense** (plainly different meaning) | 104 / 105 (785) | wsd | pt *cara* "guy" shown as "face" (68%) and "resemblance" (#220); pt *embora* (*ir embora* = leave) shown as "although" on 93% (#238) | L (the classifier; partly fixed by the families below) |
| 2 | **Right gloss, wrong context or pill** — the English is right; the context (the grey text under a meaning) or a pill shown with it is not | 55 / 58 (592) | wsd + menu | pt *ser* "to be ⟨indicates a point in time⟩" on *a culpa não foi minha*, *não foi muito divertido* (#37, also *era*, *somos*, *sido*); pt *em* "in" with the pill "indicates a language, script" on *na nossa casa* (#31, *num*, *numa*, *nas*) | M (merge senses with one gloss, or hide unreliable contexts) |
| 3 | **Phrase missing from the menu** | 46 / 32 (218) | menu | es *a veces* not on the *vez* menu (17 of 18 examples); pt *ter certeza* "to be sure" shown as "are you sure?" (95% of *certeza*, #211) and under "to own" on *tenho/tens/ter* | M (add phrases; pt Wiktionary phrase coverage is thin) |
| 4 | **Phrase matched where it is literal** | 24 / 48 (183) | wsd | pt *qual é* "no way" on 94% of *qual* (*qual é o seu nome?*, #185); es *de cabeza* "headfirst" on *dolor de cabeza* | S–M (literal-use guard on the MWE matcher) |
| 5 | **Wrong part of speech** | 19 / 27 (229) | wsd | pt *preciso* (I need) shown as adj "necessary" 80% (#162); pt *as* article shown as "them" (#29); es *estos* as PRON | M |
| 6 | **Phrase gloss wrong for this use** | 18 / 24 (142) | menu | pt *há quanto tempo* glossed "long time no see" on every *how long…?* (#60, #104, #212); pt *tudo bem* glossed "how are you?" on *está tudo bem* (#50) | S (rewrite a few dozen glosses) |
| 7 | **Sense missing from the menu** | 13 / 14 (161) | menu | pt clitic *nos* / *lhe* absent, so *nos rastrear* shows "in" and "the" (#44, #77); pt contractions *dele, dela, disso, daqui, dali* have only *de* senses (#148, #215, #186, #203); es *oye* has no "hey" | M (contraction and clitic entries for pt) |
| 8 | **Construction read as a lexical verb** (*ter que*, *ir a* + inf, *voltar a* + inf) | 15 / 6 (153) | wsd | pt *temos que / tens de* under "to own; possess" (#97, #118); es *tener que* under comparative *que* | S–M (deterministic construction rule) |
| 9 | **Reflexive slip** | 12 / 7 (51) | wsd | seeded es *irte* shows *ir* "to go" on *irse*; pt *não me importo* (I don't care) shown as "to matter" 70% (#1732), *nos encontramos* (we met) as "to be located" (#969) | M (decision 0025 clitic split; reflexive tagger already exists) |
| 10 | **Progressive read as a lexical verb** | 9 / 6 (92) | wsd | seeded es *estuve pensando* shown as "to fit"; pt *estás a fazer* / *estamos te dando* shown as "to stand" (#61, #110) | S (gerund / *a* + infinitive rule) |
| 11 | **Auxiliary read as a lexical verb** (future *ir*, perfect *ter*) | 7 / 7 (72) | wsd | pt *vou / vai / vais / vão* + infinitive under "to go (to begin an action)" 40–53% (#41, #54, #165, #183); pt *ter sido*, *tenha visto* under "to own" (#67, #290) | S (same rule family as #10) |
| 12 | **Pronoun function confused** (subject vs object vs prepositional) | 7 / 4 (83) | wsd | pt *ela* subject shown as "her (prepositional)" 90% (#38); pt *nós* subject as "us" (#75) | S |
| 13 | **Junk gloss** (a spelling note or cross-reference shown as the meaning) | 4 / 12 (22) | menu | pt *seu* possessive senses glossed "Second-person singular possessive determiner." so "you ⟨epithets⟩" wins on 70–100% of *seu/sua/seus/suas* (#63, #68, #190, #273); pt *espectáculo* glossed "pre-reform spelling … of espetáculo" (#1575) | S (gloss rewrite; TERSE owns long glosses, these are wrong ones) |
| 14 | **Same meaning split into several rows** | 2 / 9 (38) | menu | pt *quero* four "to want" rows (#76); pt *falar* two "to talk" rows split by *com* / *de* (#109, the roadmap's part 3 example) | M (part 3 metadata pass) |
| 15 | Bad example (proper names, broken pairs) | 7 / 0 (38) | harvest | es names *Marina, Mina, Norma* as senses | S |
| 16 | Proper noun taken as a word | 0 / 5 (14) | harvest | pt *cal* "lime" on the name Cal (100%, #4006); pt *una* "a municipality of Bahia" (#121) | S |
| 17 | Wrong-language card | 1 / 2 (10) | inventory | pt *mi* "musical note" on Spanish *mi casa* (#161); pt *una* | S (inventory filter) |
| 18 | Same sense under two headwords | 4 / 2 (13) | menu | es *dígales* carries the *dígale* menu; pt *si* examples under *se* senses (#119) | M |
| 19 | Governed preposition | 1 / 4 (37) | features | pt *de* after *depender, cuidar, falar* shown as "as (in the role of)" (#85) | M |
| 20 | Display: split labels, empty rows, bucket drift, dropped expressions | 8 / 3 | display, selection | es *entre* shows the *entre nosotros* sentences under *entre semana*; es *van* card 2 repeats the whole *ir* card | S each |

Smaller: untranslated senses (es 4), folded headwords (pt 4), duplicated
contexts (pt 1), topic chips (pt 1), companion misattributed (es 1).

## Fix families (where one change clears several causes)

Terms as in `docs/NOMENCLATURE.md`: **context** is the grey text under a meaning
on the card (the menu's `context` field); **pills** are the small inline labels.

1. **Phrases** — causes 3, 4, 6 (≈190 cards). Add the missing phrases, guard
   literal uses (*qual é o problema*, *em um dia*, *o mesmo que*), match through
   contractions (*depois do*, *fora da*, *por volta das* are missed today), and
   fix the phrase glosses.
2. **Context and pills** — causes 2, 14 (≈125 cards). The English is right but
   the context or pill shown with it is wrong. Many Wiktionary senses share a
   gloss and differ only in a context the classifier cannot see (*de* "of"
   with the context "introduces the name of a place following its hypernym";
   *ser* "to be" with "indicates a point in time"; *em* "in" with the pill
   "indicates a language, script"). Merge those senses or stop showing those
   contexts. Owner: part 3 (metadata).
3. **Grammar verbs** — causes 8–11 (≈70 cards). A **WSD** error, not a display
   one: the right sense is on the menu and WSD picks another (*vou fazer* gets
   "to go (to begin an action)" although "will; to be going to" is offered;
   *estou a fazer* gets "to stand" although "to be; forms the progressive" is
   offered; *tenho que* gets "to own"). Fix with deterministic construction
   rules before or inside WSD: *ir* + infinitive → future, *estar/andar* +
   gerund or *a* + infinitive → progressive, *ter/haver* + participle →
   perfect, *ter que/de* → obligation, *ser* + participle → passive, and
   reflexive forms. Covers the seeded *irte*, *darte*, *estuve*. Josh
   (2026-10-08): a worthwhile step for the next WSD pass.
4. **Portuguese menu gaps** — causes 7, 13 (≈40 cards). Three kinds of fix:
   - *by hand* (~10 frequent words): clitics *nos*, *lhe*; formal "you" *o
     senhor*, *a senhora*, *si*; *melhor*; *oh*;
   - *one rule*: contractions (*dele, dela, disso, daqui, dali, num*) are a
     preposition plus a word, so a small table ("de + ele = his / of him")
     covers the set;
   - *one Wiktionary adapter fix*: the *seu* senses are glossed "Second-person
     singular possessive determiner." while the English ("your") sits in the
     context; read the gloss from there. Fixes *seu, sua, seus, suas*, so "you"
     stops winning on them.
5. **Junk cards** — causes 15–17. Names and foreign words. Owner: the surface
   ledger, at two levels:
   - *card verdict* (reason code proper name / foreign word) where the whole
     card is junk: *Cal* (always the name, shown as "lime"), Spanish *mi*;
   - *sentence rejects* where the word is real but some sentences are not:
     *Nora* (name / daughter-in-law), *una* (Spanish / subjunctive of *unir*),
     *mortal* (the title "Taça Mortal").

Portuguese is 12 points behind Spanish on the blind sample, and families 1, 3
and 4 account for most of the gap. A large share of pt "wrong sense" lines are
function words, where the Wiktionary menu offers ten near-identical senses.

**Separate, not logged:** the English is always the dictionary form ("to go")
and never matches the form on the card ("I go", "I'm going to"). That is a
display question for later, outside WSD; it affects every verb card, so it was
not logged as a problem.

## Seeded problems (from CHAT_ROADMAP)

| Seed | Rank | Found |
|---|---|---|
| es *irte* shows *ir* "to go" on *irse* sentences | 725 | yes (reflexive_slip) |
| es *darte* shows *darse* "to grow" on *darte razones* | 701 | yes (reflexive_slip) |
| es *estuve* "to fit" from *estuve pensando* | 742 | yes (progressive_as_lexical) |
| pt *tu* glossed "you; thou" | 46 | yes (junk_gloss: "thou" plus archaic/literary pills; also on *ti* #134) |

## Not logged (Josh, 2026-10-08)

Real senses moved to Rarer uses by the 10% floor; over-long Wiktionary glosses
(TERSE); phrase card lemmas such as *pelo menos* on *pelo* (separate task). The
reader's "PHRASE … — 0%" is an artefact, not a learner problem.

Mechanical whole-release counts (pilot, all 803 cards): split card repeating
the whole card on 19 es / 7 pt cards; empty expression rows on 8 es / 8 pt;
240 untranslated es menu senses on 125 cards; pt duplicated contexts on 16
cards. Not re-run as card records.

## The panel (accuracy check for parts 2 and 3)

`research/unison/gold/{es,pt}-panel.jsonl`, frozen 2026-10-08; format and
counts in `research/unison/gold/README.md`. Score any run with
`python research/unison/score_panel.py score --language es --assignments <run>/stages/04_wsd_assignments/output/assignments.jsonl`.

## Files

- `docs/unison/audit-300.jsonl` — 771 problem lines (card, cause, layer, shows, should, sentence ids, gold).
- `research/unison/labels/` — hand labels and audit lines as written.
- `research/unison/cards.py`, `display.mjs` — the card reader (runs the app's own display code).
- `research/unison/compare_blind.py`, `audit.py`, `condense.py`, `score_panel.py`.
