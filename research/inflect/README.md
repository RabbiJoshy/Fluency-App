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
  --conjugations $W/conjugations.json --baseline /tmp/baseline.mjs --examples 8
```

Measure the release the app serves (`app/config/config.json`, `indexPath` and
`conjugationsPath`), not the workspace's `active.json`. Rows are run without an
example sentence; on a card the example can also pick I vs he/she and show a
command, so the card can read better than this report.

Readings on 2026-10-11 (after INFLECT, `96375c29`):

| Release | Card/verb pairs inflected | Error classes |
|---|---|---|
| es `es-speech-v24-headway-r4-10000x30-slim` | 4,446 of 5,397 | all 0 |
| pt `pt-speech-v24-headway-r3-10000x30-slim` | 3,255 of 3,386 | all 0 |
| cs `cs-speech-v22-10000x30-slim` (table from `cs-speech-v12-4000x10-conj`) | 1,356 of 3,035 | 0, but some inflected rows are wrong in ways these classes do not test: see INFLECT-CS |

Most of the Spanish remainder is attached pronouns (*hacerlo*, *verte*), left to
the companion-card work.
