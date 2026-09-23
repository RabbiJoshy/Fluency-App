# Conjugation mode

A Conjugato-shaped drill built on the existing `conjugation-layer/v1`
enrichment. It is a **separate page** under `app/conjugation/`, sharing no
HTML, CSS or JS with the study app. It is entered three ways: the *Verb
conjugation* option on the main page (shown for languages whose config entry
names a `conjugationDrill` deck), the *Drill this verb in conjugation mode*
link in the conjugate drawer on the back of a card (`app/js/flashcards-conj.js`),
and the shareable routes `#/es/conjugate` and `#/es/conjugate/<verb>`, which
the app redirects here.

## The primitive: a lesson signature

Everything here rests on five fields per form:

    (class, tense, person, ending, stem_delta)

`ending` is the commonest ending observed for verbs of that class in that
tense and person. `stem_delta` is the minimal edit from the infinitive's stem
to the stem actually realised once that ending is removed — `pens` → `piens`
is `e>ie`, `busc` → `busqu` is `c>qu`, `ten` → `teng` is `0>g`.

**Two forms teach the same thing exactly when those five fields match.** That
is the whole similarity relation: exact tuple equality, no score, no
threshold. For Spanish it turns 45,790 forms into **1,353 lessons** over
**44 distinct alternations**, 285 of them singletons — the genuine one-offs.

Nothing is hand-tagged, and nothing depends on which source supplied the
forms: the builder reads only the infinitive and the paradigm, so it runs
identically on Portuguese, French and Czech.

The familiar verb types are read off the delta rather than stored separately:

| code | meaning | rule |
| --- | --- | --- |
| 0 | regular | delta is empty |
| 1 | spelling change | the realised stem folds back to the citation stem |
| 2 | stem change | any other delta |
| 3 | irregular | the ending itself does not match (delta `*`) |
| 4 | unclassified | no model available |

## Screens

- **Choose** — eight collapsed sections, each stating its own selection so the
  whole menu is legible at phone width without opening anything: tenses, verb
  type, patterns, repetition, how common, persons, prompt, provenance.
- **Patterns** — one row per alternation, with example verbs. *Only the odd
  ones* drops the no-change pattern and leaves the verbs that actually differ.
- **Repetition** — *every form*, or *one per lesson*, which shows each lesson
  once by a verb picked at random from the verbs that share it. The Choose
  screen reports both numbers so the trade is visible before you start.
- **Drill** — no buttons. Space or tap reveals, space again advances, `←` goes
  back, swipe left/right moves, `t` opens the full table on the tense you just
  missed. The answer names the pattern and the verbs that share it.
- **Tables** — type a verb, pick one tense or all, read the paradigm coloured
  by form type.

Nothing is scored, stored or scheduled. A progress model is a later decision.

## Deep links

    conjugation/?lang=es&verb=tener              drill that verb, every tense
    conjugation/?lang=es&verb=tener&view=table   open its paradigm instead

An unknown verb lands on Tables with the search box pre-filled rather than
failing. The page keeps its own address in this form as you move around, so
the address bar is always a link to the verb on screen.

## Rebuilding a deck

```bash
python scripts/build_conjugation_drill.py \
  --layer <workspace>/objects/sha256/<aa>/<rest>/conjugations.json \
  --language es \
  --ranks <workspace>/runs/es/speech/<run-id>/stages/01_inventory/output/frequency-ranks.json
```

`data/es.js` was built from the `fred-jehle` layer (`sha256:c1c66373…`,
434 verbs, 18 paradigms) with ranks from run `20260919T122017Z-c088090a`.
`data/pt.js` is the verbecc layer (`sha256:4f2abe83…`, 955 verbs, 10 tenses,
485 lessons) with ranks from `20260919T122019Z-a3c6945d`.
`data/cs.js` is the kaikki layer (`sha256:b683bd1d…`, 404 verbs, present +
imperative only, 162 lessons) with ranks from `20260919T122021Z-0606a927`.
Czech tables stay present + imperative; that is the layer, not a drill
omission. French still has no deck file, so it stays off
`CONJ_DRILL_DECKS` in `app/js/flashcards-conj.js`.

## Two things that are derived, not supplied

**Commonness** is the rank of the **infinitive** in the speech inventory, not
the best rank across inflected forms — those collide with homographic function
words and rank `parar` at 22 because `para` is a preposition. 386 of 434
Spanish verbs have a rank; the rest are declared unranked and only appear when
the slider reaches the end.

**Enclitic imperatives** (`lávate`, `lavémonos`) carry their pronoun glued on,
so the model cannot see the ending underneath. Those forms are declared
unclassified rather than called irregular, and unclassified never raises a
verb's type on its own.

## Where it would have to connect

A conjugation cell is not an observed surface form, so it cannot take a
`card_id = f(language, surface_key)`. A progress store would key on the lesson
signature, parallel to the vocabulary system rather than inside it.
