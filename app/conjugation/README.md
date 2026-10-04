# Conjugation mode

A Conjugato-shaped drill built on the existing `conjugation-layer/v1`
enrichment. It is a **separate page** under `app/conjugation/`, sharing no
HTML, CSS or JS with the study app. It is entered three ways: the *Verb
drills* row in the pop-up behind the top-left language button (shown for
languages whose config entry names a `conjugationDrill` deck), the *Drill this verb in conjugation mode*
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

Two tabs, **Set up** and **Practise** (internally `setup` and `drill`). The learner-facing copy says *pattern*,
never *lesson*.

- **Set up** — verb type, how common, tenses, persons, stem hints, and an
  Advanced group (prompt). *Patterns*, *Repetition* and *Where this data comes
  from* are still built but carry `hidden` in `index.html`; remove it to bring
  one back. Hidden settings keep their defaults (all patterns, every form).
  The button that starts is just **Start**.
- **Stem hints** (was *Easy mode*) — colours the prompt by what this card does
  and names the verb's family.
- **Practise** — space or tap reveals; then **Got it** (space/enter) or
  **Missed it** (`x`) grades and moves to the next unanswered card. `←` goes
  back (re-grading replaces the first answer), swipe skips without grading,
  `t` or *see the table* opens that verb's table, and *see sentences* (only on
  a form with examples) lists up to three sentences using it. Answering the
  last card shows the round summary with *Drill the missed ones*.
- **Progress** (Set up section) — order: weakest first (default), only what
  needs work, or random; the summary bar shows known / learning / missed / new.
- **Table** — no tab of its own: reached from a card or a `?view=table` link,
  with its own back button (to the same card, or to Set up when no drill runs).

## Progress

`progress.js` keeps three things in `localStorage`, each under its own key:

| key | holds |
| --- | --- |
| `conj_progress_v2_<account>_<lang>` | one record per form, keyed `verb\|tenseId\|person` |
| `conj_session_v2_<account>_<lang>` | the round in flight, so a closed tab offers *Resume* |
| `conj_settings_v2_<lang>` | the Set up choices (a one-verb deep link never overwrites them) |

`<account>` is the study app's signed-in initials, else `guest`. Each form
climbs a Leitner ladder (waits 10 min, 1 d, 3 d, 7 d, 21 d, 60 d); a miss drops
it to the bottom and makes it due at once. *Known* means box 3 or above. A form
with no record is declared *new*. Pattern-level progress is folded from form
records at read time, never stored. The table view marks practised forms with
a dot.

Progress is device-local: it does not go through the study app's sync queue
or the Google Sheets backend. Syncing it would need a new backend sheet.

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

Every deck is built from a Wiktionary (Kaikki) layer; Fred Jehle and verbecc
were dropped on 2026-10-04. `data/es.js` is `sha256:c9210195…` from
`enwiktionary-2026-09-13`: 1,783 verbs, 18 tenses, 1,427 lessons, ranks from
run `20261004T160042Z-fe49e477`. The eight compound tenses are built from
*haber* + participle, and the 625 `-se` verbs Wiktionary files only under
their base verb are that verb's table with the reflexive pronoun and its
listed attached imperatives (*acuéstate*); both are labelled `derived` in
the layer. `data/pt.js` is `sha256:ed493d47…` from `enwiktionary-2026-08-20`:
1,420 verbs, 11 tenses (the pluperfect is new), 1,030 lessons, ranks from
`20261004T160042Z-b4bc9acd`. Against the old decks, shared cells agree
99.4% (es) and 98.6% (pt); the Portuguese differences are verbecc's broken
*nós* preterites (*dan* for *dançámos*). `data/cs.js` is the kaikki layer
(`sha256:b683bd1d…`, 404 verbs, present + imperative only, 162 lessons) with
ranks from `20260919T122021Z-0606a927`.
Czech tables stay present + imperative; that is the layer, not a drill
omission. French still has no deck file, so it stays off
`CONJ_DRILL_DECKS` in `app/js/flashcards-conj.js`.

## Example sentences

`data/<lang>-examples.json` gives each form up to three example sentences
taken from a harvest pool: no corpus rescan, only sentences already harvested
for the vocabulary. The drill fetches it the first time a revealed card could
use it. How many a form gets follows its verb's rank (three for the top 50,
two to 200, then one); a form the pool never saw has no entry and its card
offers none. Homographs are accepted (*fue* is *ir* or *ser*, *limpia* may be
the adjective). Each sentence's pool `sentence_id` is in the unloaded sidecar
`data/<lang>-examples.ids.json`. The script's docstring has the cleaning rules.

```bash
python scripts/build_conjugation_examples.py --language es \
  --pool <workspace>/pools/es/es-10k-speech
```

Built from `es-10k-speech` (17,039 of 188,854 forms, 18,986 sentences),
`pt-10k-speech` (11,019 of 90,464; European only, so mostly subtitles) and
`cs-10k-speech` (2,255 of 3,403).

## Two things that are derived, not supplied

**Commonness** is the rank of the **infinitive** in the speech inventory, not
the best rank across inflected forms — those collide with homographic function
words and rank `parar` at 22 because `para` is a preposition. 955 of 1,783
Spanish verbs have a rank; the rest are declared unranked and only appear when
the slider reaches the end.

**Enclitic imperatives** (`lávate`, `lavémonos`) carry their pronoun glued on,
so the model cannot see the ending underneath. Those forms are declared
unclassified rather than called irregular, and unclassified never raises a
verb's type on its own.

## Where it would have to connect

A conjugation cell is not an observed surface form, so it cannot take a
`card_id = f(language, surface_key)`. The progress store above runs parallel
to the vocabulary system rather than inside it.
