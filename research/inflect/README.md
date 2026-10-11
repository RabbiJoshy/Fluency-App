# Inflect: measuring conjugated-verb English across a deck

`measure.mjs` runs every verb sense row of a release through the same function
the card back uses (`englishProductionCue` in `app/js/reverse-cues.js`, with the
release's own `conjugations.json`) and reports:

- **status per row**: inflected, a dictionary-form card, the card's word not
  found in the verb's table, the verb missing from the table, or a gloss that
  is not "to …" (already English such as "can", or a note);
- **error classes INFLECT removed**, each of which should stay at 0: a command
  listed beside a statement (`seem! / he/she seems`), a state verb made
  progressive (`was being`), broken brackets, a regular ending on an irregular
  verb (`meaned`), a dictionary note left on the row (`; forms the progressive
  aspect`);
- with `--baseline`, how many rows **changed, gained or lost** English against an
  older copy of `reverse-cues.js`, with examples. A change is reviewed by
  reading these, not by its tests alone.

```bash
W=../Fluency-Workspace/releases/es/speech/<release>/app
git show <sha>:app/js/reverse-cues.js > /tmp/baseline.mjs   # optional
node research/inflect/measure.mjs --index $W/vocabulary.index.json \
  --conjugations $W/conjugations.json --sentences $W/vocabulary.examples.shards \
  --baseline /tmp/baseline.mjs --examples 8
```

`--sentences` gives each card its example sentences, as the app has once a set
is loaded. Since 2026-10-11 a form that is both a statement and a command shows
one reading, never both: the statement, unless the card's sentences are
two-thirds commands (*mira* "look!", *esqueça* "don't forget!") or the example
on screen is a command for that row's verb ("¡Espera aquí!": "wait!"; this
report runs without an on-screen example). So `command_listed_with_statement`
stays 0. The person never follows the example: *era* is "I/he/she was" on every
example.

**This report reads the cue string, not the card.** The card back lifts a
trailing definition bracket out of the row and shows it as a sub-row
(production *vou*: "I go" with "to begin an action or process" and "+ para to
move to a destination"; *quero*: "I want to" with "to feel the need to do
something"). A cue such as "he/she went (to move to a destination)" therefore
does not read as a purpose on the card. INFLECT-2 tried dropping those
brackets (2026-10-11, `35f1d319`) and reverted it after seeing the real card:
it only cost sub-rows. Check a change on a staging card before trusting a
count of cue strings.

Measure the release the app serves (`app/config/config.json`, `indexPath` and
`conjugationsPath`), not the workspace's `active.json`. Without `--sentences`
no row shows a command.

Readings on 2026-10-11 (after INFLECT, `96375c29`):

| Release | Card/verb pairs inflected | Error classes |
|---|---|---|
| es `es-speech-v24-headway-r4-10000x30-slim` | 4,446 of 5,397 | all 0 |
| pt `pt-speech-v24-headway-r3-10000x30-slim` | 3,255 of 3,386 | all 0 |
| cs `cs-speech-v22-10000x30-slim` (table from `cs-speech-v12-4000x10-conj`) | 1,356 of 3,035 | 0, but some inflected rows are wrong in ways these classes do not test: see INFLECT-CS |

Most of the Spanish remainder is attached pronouns (*hacerlo*, *verte*), left to
the companion-card work.
