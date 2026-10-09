# UNISON audit panel (frozen 2026-10-08)

The accuracy check for UNISON parts 2 and 3. Built by
`python research/unison/score_panel.py freeze` from the hand labels in
`research/unison/labels/` and `docs/unison/audit-300.jsonl`. Do not edit by
hand; re-freezing from the same labels gives the same files.

## Strata

| | es | pt |
|---|---|---|
| `sample` — 3 examples per card, chosen by a seeded hash of the sentence id, labelled blind (v23's choice hidden, never revised) | 1,200 | 1,050 |
| `seeded` — es chunk s01 (*darte*, *irte*, *estuve*): blind sample and found-wrong items | 35 | — |
| `found_wrong` — every example the audit found wrong and gave a gold, minus causes that are not about the sense pick (gloss text, row layout, display) | 1,516 | 1,332 |

Cards: es top 300 + 100 random from ranks 301–10,000 (seed `unison-1`) + 3
seeded; pt top 300 + the first 50 of the 100 random (r01–r02). pt found-wrong
items come from condensed card views from t02 on, so they are a lower bound.

## Item

`id, language, stratum, chunk, rank, word, card_id` (full surface card id),
`sentence_id` (run id without `sentence_`), `text, translation`,
`gold` (menu sense as text — label, sense_id, menu_analysis_id, headword, pos,
translation, context — or a special string), `alt` (equally-right senses, same
shape), `accept` (sense ids that count as right; a phrase also as
`mwe:<headword>`, which is how stage 04 names it), `v23` (what v23 chose/showed),
and `conf, note` (sample) or `cause, layer, note` (found_wrong).

Special golds: `phrase:<mwe>` (a phrase the menu lacks), `none:<meaning>` (the
menu has no right sense), `not_target:<why>` (proper name, wrong language,
part of a compound). They are scored apart; a run can only get them right
through a listed alternative. After a menu rebuild, map `gold` by its text,
not its label.

## v23 baseline

`score_panel.py score --language <l> --assignments <v23 run>/stages/04_wsd_assignments/output/assignments.jsonl`
gives exactly the same as `--v23` (the frozen choice):

| | es | pt |
|---|---|---|
| sample (menu golds) | 992 / 1,169 = 84.9% | 715 / 992 = 72.1% |
| sample (special golds) | 4 / 31 | 27 / 58 |
| seeded | 5 / 35 | — |
| found_wrong (menu golds) | 11 / 1,184 = 0.9% | 45 / 1,106 = 4.1% |

All blind items together reproduce `compare_blind.py`: pt 742 / 1,050 (70.7%);
es 1,001 / 1,209 against 1,000 there (one phrase gold now also matches its
`mwe:` id). Found-wrong items that score right are mostly
`phrase_gloss_wrong_use` (the phrase was picked; its gloss is what is wrong) and
`missing_sense` items with a listed alternative.

Runs: es `20261004T160042Z-fe49e477`, pt `20261004T160042Z-b4bc9acd`.
