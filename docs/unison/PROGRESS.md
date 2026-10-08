# UNISON progress

Kept by the UNISON chats; see `BRIEF.md` for the rules. Newest first within
each section.

## Status

Part 1 (audit): in progress (UNISON-1). Pilot reviewed by Josh 2026-10-08.

**Done:** es complete (t01–t12, r01–r04, s01: 403 cards, 1,209 blind labels;
v23 1000/1209 = 82.7% strict, 90.3% same gloss; 442 problem lines). pt t01.

**Resume here:** pt t02 → t12, then pt r01 → r04. Report pt to Josh, then the
write-up (below). Per chunk, in this order:
1. Read `<W>/reviews/unison/pt-speech-v23-10000x30-slim/blind-<chunk>.txt`;
   append one line per item to `research/unison/labels/pt-blind.jsonl`:
   `{"id":"pt-t02-0001","gold":"m4","alt":[],"conf":"sure","note":""}`.
   Special golds: `phrase:<mwe>`, `none:<meaning>`, `not_target:<why>`
   (proper names, wrong language, broken pair). Blind labels are final.
2. `.venv/bin/python research/unison/compare_blind.py --language pt --chunk t02 --show`.
3. Read `view-<chunk>.txt` (~1,000 lines; read 400–450 lines at a time).
4. Append problems to `research/unison/labels/pt-audit.jsonl`, one per
   (card, cause, shown → should): `{"rank":26,"cause":"…","layer":"wsd",
   "scope":"example|row|card","shows":"…","should":"…","ids":["8-hex",…],
   "gold":"m3" | {"id":"m3",…},"alt":[…],"note":"…"}`; then
   `.venv/bin/python research/unison/audit.py build` (validates ids and labels).
5. Update the line above.

Cause codes in use: wsd_wrong_sense, same_gloss_wrong_context (same English
gloss, wrong context), missing_phrase, missing_sense, mwe_false_positive,
phrase_gloss_wrong_use, construction_misread (ir a + inf, tener que…),
pos_confusion, pronoun_function_confusion, reflexive_slip,
progressive_as_lexical, auxiliary_as_lexical, governed_preposition,
companion_misattributed, duplicate_sense_across_headwords,
sense_split_across_translations, untranslated_sense, junk_gloss,
wrong_language_entry, proper_noun_sense, topic_chip_noise, duplicated_context,
bad_example (harvest: proper-name or broken sentences), empty_row,
split_label_mismatch, split_drops_expressions, example_bucket_drift.
Layers: menu, features, wsd, selection, display, inventory, harvest.
Not logged (Josh): senses moved to Rarer uses by the floor; long Wiktionary
glosses (TERSE); phrase card lemmas (separate task). Reader artefact, not a
problem: "PHRASE … — 0%" (the app falls back to the raw share).

**Write-up after pt:** (1) mechanical card records, deduped against hand
records: split card repeating the whole card, rows with share but no example,
untranslated senses, non-standard POS labels ('transitive verb', 'pronominal
verb', 'intransitive verb phrase', lowercase 'noun'/'adverb'; seen on es
reunirme, pedírselo, dársela, salirte, aparcamiento, emocionalmente);
(2) `research/unison/gold/{es,pt}-panel.jsonl` (strata sample / found_wrong /
seeded = es s01) + `gold/README.md`; (3) `research/unison/score_panel.py`
(scores a run's assignments or a release's shards against the panel, by
stratum, language and cause; v23 must reproduce the blind numbers);
(4) `docs/unison/AUDIT.md` (causes ranked by cards, layer, two named examples,
rough fix cost, seeded items with ranks); (5) PROGRESS: Part 1 done, "Fix
list: Josh to pick"; (6) commit only `docs/unison/` and `research/unison/`;
stop for Josh.

Cause codes added after the pilot: `auxiliary_as_lexical`,
`duplicate_sense_across_headwords`, `companion_misattributed`,
`pronoun_function_confusion` (renamed from clitic_function_confusion), and
later `example_bucket_drift` (display; entre).

### Pilot results (2026-10-08)

- Blind sample (75 per language, labelled before v23 was opened): es 61/75
  right (81.3%), same gloss shown 63/75 (84.0%); pt 56/75 (74.7%), same gloss
  59/75 (78.7%). `python research/unison/compare_blind.py --language es`.
- Problems: 115 lines over 50 cards (`docs/unison/audit-300.jsonl`, built from
  `research/unison/labels/<lang>-audit.jsonl` by `research/unison/audit.py
  build`; `audit.py summary` ranks causes).
- Confirmed live (study sets, not the word link): *entre* shows the *entre
  nosotros* sentences under *entre semana* (example buckets shift after a
  meaning with no translation is dropped); *van* card 2 "irse (to leave)"
  repeats the whole *ir* card (a split reading with no main sense falls back to
  every sense). Wrong card lemmas (pt *não*, *é* → "não é") are not visible on
  the front.
- Mechanical, all 803 cards: es 240 untranslated menu senses on 125 cards;
  split card repeats the whole card on 19 es / 7 pt cards; empty expression
  rows on 8 es / 8 pt cards; pt duplicated contexts on 16 cards; pt glosses
  over 60 characters on 70 cards (TERSE); pt place-name senses on 20 cards.

### Part 1 working notes

- Card reader: `research/unison/cards.py` + `display.mjs` (runs the app's own
  floor, function-word overlay, split and expression code). Outputs in
  `<W>/reviews/unison/<release_id>/` (not git): `view-<chunk>.txt` (card as
  shown, with v23 choices), `blind-<chunk>.txt` (sample, v23 hidden),
  `blind-key.jsonl`, `v23-choice.jsonl` (open only after labelling),
  `cards.jsonl`, `selection.json`. Chunks t01–t12 = ranks 1–300, r01–r04 =
  100 random from 301–10,000 (seed `unison-1`), s01 = es *darte*, *irte*,
  *estuve*. 403 es + 400 pt cards; 1,209 + 1,200 blind items.
- Fidelity: live study sets es 1-1, es 3-3, pt 1-1 (75 cards) match the reader
  on every main meaning, share, example count and floor move. Row families
  (shared-gloss grouping) are not reproduced; display findings are confirmed
  live.
- Workflow per chunk: label `blind-<chunk>` first into
  `research/unison/labels/<lang>-blind.jsonl` (final, never revised), then read
  `view-<chunk>` and append problems to `docs/unison/audit-300.jsonl`.
Part 2 (one engine): waiting on part 1.
Part 3 (metadata): waiting on part 1.

## Frozen-check baselines (2026-10-08, before any UNISON change)

- Lyrics v20 accuracy sample (`<W>/reviews/lyrics-v20/accuracy-sample-judged.json`,
  hand-judged, no script): `j20` C 81 / W 14 / U 5 → **85.3%** (C / (C+W)).
- Reflexive gold (`research/reflexives/eval_{es,pt}.py`, POLICY decisive-acc):
  es held 1.0000 (241/300 decisive), es subs 0.9976 (414/500, 1 error);
  pt dev 1.0000 (255/300), pt held 1.0000 (269/300), pt blind2 0.9950
  (200/250, 1 error), pt blind3 0.9940 (166/200, 1 error).
- Audit panel: frozen at the end of part 1 (`research/unison/gold/`).

## Decisions (approved by Josh)

- 2026-10-08: the audit panel is 3 random examples per card plus every example
  the audit finds wrong ("3 per card + all wrong").
- 2026-10-08: the 3 random examples are labelled **blind**: sentence and full
  menu only, v23's choice hidden, then compared ("Label the random sample
  without seeing what v23 chose"). Wrong examples found while reading cards
  stay a separate group.
- 2026-10-08 (after the pilot): not logged as audit problems — (a) a real
  sense moved to Rarer uses by the 10% floor ("doesnt affect WSD right, the
  rare option is still in the menu"); (b) over-long Wiktionary glosses
  ("TERSE will act later"); (c) wrong multi-word card lemmas, handed to a
  separate task ("let some subagent finish it or put it on a todo item").
- 2026-10-08: add 100 random cards per language from ranks 301–10,000, with
  the same treatment ("a random 100 cards outside the top 300 … to get
  something more representative").
- 2026-10-08: UNISON covers modes (speech, lyrics, TURBO) and providers
  (SpanishDict, Wiktionary), plus a metadata pass and a 300-card audit of es
  and pt. Audit first. UI changes wait until UNISON is done.

## Fix list

Set by Josh after part 1.

## Done before UNISON (2026-10-08)

- Wiktionary companion notes keep every alternative (`[with de or sobre]`),
  treat form alternatives as no requirement, and read a lone "a" as the
  preposition (`features/wiktionary.py`, 3bcf94ce). Not in any release until
  menus are rebuilt.
- Live display changes: 10% floor per subsense row; SpanishDict senses sharing a
  context group into one row; topic chips only when they distinguish rows.

## Found, not on the list

(Count and one example each.)

- Card lemma is a phrase: 112 es / 132 pt cards (pt *não* → "não é", es *por*
  → "por qué"). Not shown on the card front. Handed to a separate task
  ("Stop phrase headwords becoming card lemmas"), 2026-10-08.
- Over-long Wiktionary glosses (pt rows over 60 characters on 70 of 400
  cards, e.g. *ele* "third-person masculine singular nominative personal
  pronoun; he; it"): owner TERSE.
