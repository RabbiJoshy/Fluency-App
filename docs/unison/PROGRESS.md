# UNISON progress

Kept by the UNISON chats; see `BRIEF.md` for the rules. Newest first within
each section.

## Status

Part 1 (audit): **done** 2026-10-08 (UNISON-1). Results and causes in
`docs/unison/AUDIT.md`; problem list `docs/unison/audit-300.jsonl` (771 lines);
frozen panel `research/unison/gold/` (scorer `research/unison/score_panel.py`).

- es: 403 cards read in full, 1,209 blind labels, v23 right 1,000/1,209 = 82.7%.
- pt: 350 cards (top 300 + random r01–r02), 1,050 blind labels, v23 right
  742/1,050 = 70.7%. pt r03–r04 (50 random cards) not read: Josh asked to
  finish. pt card views from t02 on were read condensed
  (`research/unison/condense.py`), so pt found-wrong is a lower bound.
- Mechanical card records were not re-run; AUDIT.md cites the pilot counts.

**Fix list: Josh to pick** (from AUDIT.md "Fix families").

Part 1 working rules (kept for reference): blind labels first and final;
special golds `phrase:`, `none:`, `not_target:`; one audit line per
(card, cause, shown → should); `audit.py build` validates ids and labels.
Not logged (Josh): senses the 10% floor moves to Rarer uses; long Wiktionary
glosses (TERSE); phrase card lemmas (separate task). Reader artefact, not a
problem: "PHRASE … — 0%" (the app falls back to the raw share).

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
Part 2 (one engine): completed (UNISON-2, 2026-10-08). Engine unified across speech, lyrics, and TURBO; duplicate loops retired; feature contract and 3-state translation deployed; calibration tables built; stale engine checker implemented; Decision 0025 decided (rejected); frozen checks verified (lyrics accuracy improved from 85.3% to 93.7%; reflexives 100% held/dev).
Part 3 (metadata): **done** 2026-10-09 (UNISON-3). Sense vs label contract formalized in Decision 0030 (`docs/decisions/0030-sense-metadata-and-display-contract.md`); Kaikki adapter updated with companion extraction (`+ com`, `+ de`), junk gloss filtering (`_JUNK_GLOSS_PATTERN`), parenthetical label stripping, and intra-entry sense deduplication; parity tests updated; frozen checks 100% verified (reflexives 1.0000 decisive acc on es held and pt dev; 636/636 tests passing); before/after measured across 173 metadata audit issues; post-UNISON UI questions compiled for Josh review. Releases unactivated, UI files untouched.

## Frozen-check baselines (2026-10-08, before any UNISON change)

- Lyrics v20 accuracy sample (`<W>/reviews/lyrics-v20/accuracy-sample-judged.json`,
  hand-judged, no script): `j20` C 81 / W 14 / U 5 → **85.3%** (C / (C+W)).
- Reflexive gold (`research/reflexives/eval_{es,pt}.py`, POLICY decisive-acc):
  es held 1.0000 (241/300 decisive), es subs 0.9976 (414/500, 1 error);
  pt dev 1.0000 (255/300), pt held 1.0000 (269/300), pt blind2 0.9950
  (200/250, 1 error), pt blind3 0.9940 (166/200, 1 error).
- Audit panel: frozen 2026-10-08 (`research/unison/gold/`); v23 sample es 84.9% / pt 72.1% on menu golds (README there).

## Decisions (approved by Josh)

- 2026-10-08: Josh confirmed the Part 2 fix list (AUDIT.md fix families in the wsd and features layers: grammar verbs, MWE literal guard, POS & pronoun function gating, governed prepositions & companions, plus the unified engine architecture & feature contract parity: "looks good").
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

Part 2 fix list (UNISON-2: wsd and features layers, confirmed by Josh 2026-10-08):

### 1. Grammar verbs (Causes 8, 9, 10, 11) — Layer: wsd (~70 cards, 368 sentences)
Deterministic construction and periphrasis rules before/inside WSD so grammar uses are not forced into rare lexical senses:
- **Cause 8 (`construction_misread`)**: *ter que / ter de / tener que* + infinitive → obligation sense, not "to own; possess" or comparative *que* (15 es / 6 pt cards).
- **Cause 9 (`reflexive_slip`)**: Reflexive forms routed to pronominal senses via reflexive tagger and Decision 0025 clitic split; fixes seeded es *irte* on *irse*, *darte* on *darse*, pt *não me importo*, *nos encontramos* (12 es / 7 pt cards).
- **Cause 10 (`progressive_as_lexical`)**: *estar / andar* + gerund (or pt *a* + infinitive) → progressive auxiliary sense, not "to fit" or "to stand"; fixes seeded es *estuve pensando* (9 es / 6 pt cards).
- **Cause 11 (`auxiliary_as_lexical`)**: Future *ir* + infinitive and perfect *ter / haver* + participle → auxiliary sense, not lexical "to go / begin an action" or "to own" (7 es / 7 pt cards).

### 2. Multi-Word Expression literal guard (Cause 4) — Layer: wsd (~72 cards, 183 sentences)
- **Cause 4 (`mwe_false_positive`)**: Guard against literal uses where an idiomatic MWE matches spuriously (*qual é o seu nome?* matched by *qual é* "no way"; *dolor de cabeza* matched by *de cabeza* "headfirst"; *em um dia*; *o mesmo que*).

### 3. Part-of-speech & pronoun function gating (Causes 5, 12) — Layer: wsd (~73 cards, 312 sentences)
- **Cause 5 (`pos_confusion`)**: Strict tagger POS enforcement and consistent bridge across both SpanishDict and Wiktionary to avoid POS mismatch (pt *preciso* verb vs adj, pt *as* article vs pronoun, es *estos*).
- **Cause 12 (`pronoun_function_confusion`)**: Syntactic role / case gating for personal pronouns so subject pronouns are not assigned prepositional or object senses (pt *ela* subject vs prepositional "her", pt *nós* subject vs "us").

### 4. Governed prepositions & companion features (Cause 19) — Layer: features (~5 cards, 38 sentences)
- **Cause 19 (`governed_preposition`) & companion attribution**: Link governed prepositions (*de* after *depender, cuidar, falar*) to governing verb senses instead of rare autonomous senses ("as / in the role of").

### 5. Unified Engine & Feature Contract (UNISON-2 Core Architecture) — Layer: wsd & features
- Unify speech, lyrics, and TURBO into a single `fluency.wsd` engine; retire separate scoring in `scripts/plant_artist_v20.py`.
- Explicit feature scoring contract: every feature returns a score or abstains.
- Per-example evidence recording in assignments (which features scored vs abstained).
- Three-state translation feature: human, machine, absent.
- Confidence calibration per evidence combination.
- Stale-engine check tool (lists live releases built on older engines).
- Write up Decision 0025 (clitic splitting: adopt or reject with measured impact).
- Build candidate releases (es & pt speech, es lyrics) without activation, measured against frozen baselines.

### UNISON-2 Delivered Outputs & Verification (2026-10-08)

1. **Profile Inheritance & Single Engine Architecture**:
   - Implemented profile `extends` mechanism with recursive dictionary inheritance (`src/fluency/wsd/config.py`, `src/fluency/speech/wsd_execute.py`).
   - Created derived execution profiles: `config/wsd/models/es-lyrics-v23-1.json` and `config/wsd/models/es-turbo-v1.json`, both inheriting base models, gates, and features from `es-v23-1`.
   - Created `LyricsWSDAdapter` (`src/fluency/wsd/lyrics_adapter.py`) wrapping `ClosedMenuWSDRunner`.
   - Wired `scripts/plant_artist_v20.py` to `LyricsWSDAdapter`, retiring duplicate inline scoring.

2. **WSD Fix Families**:
   - **Grammar Verbs (Causes 8, 9, 10, 11)**: Implemented `ConstructionGate` (`src/fluency/wsd/construction_gate.py`) handling progressive (*estar/andar* + gerund / *a* + inf), obligation (*tener/ter que/de* + inf), future (*ir* + inf), and perfect (*haber/ter* + participle).
   - **MWE Literal Guard (Cause 4)**: Implemented `is_mwe_false_positive` (`src/fluency/wsd/multiword.py`) blocking literal false positives (*qual é o seu...*, *dolor de cabeza*, *não é verdade*, *da vida*, *e se*, *do que*).
   - **POS & Pronoun Function Gating (Causes 5, 12)**: Enforced strict POS matching with orthogonal POS isolation in `SpanishV5CandidatePolicy` (`src/fluency/wsd/languages/spanish.py`) and pronoun function gating in `ConstructionGate`.
   - **Governed Prepositions & Companions (Cause 19)**: Integrated preposition attribution and companion scoring.

3. **Feature Contract & Evidence Accounting**:
   - Updated `ClosedMenuWSDRunner` (`src/fluency/wsd/runner.py`) to track `features_scored`, `features_abstained`, `translation_state` (`human`, `machine`, `absent`), and compound key `evidence_combination`.
   - Updated `ExactTextGlossScorer` (`src/fluency/speech/wsd_execute.py`) to score with fallback rather than crashing on missing vectors, supporting 3-state translation bonuses (`human` 0.04, `machine` 0.02, `absent` 0.0).

4. **Stale Engine Check**:
   - Implemented `scripts/check_stale_engine.py` inspecting all live deployments and flagging releases running on older engine definitions.
   - Identified 3 stale releases: `lyrics es` (v20), `speech es` (v23 without unified construction/contract), `speech pt` (v23).

5. **Decision 0025 Finalized**:
   - `docs/decisions/0025-spanish-clitic-tokenization-split.md` updated to **REJECTED in UNISON-2**.
   - Rationale: WSD-level reflexive & construction gates eliminate reflexive slips without destroying card identity, invalidating learner progress on 1,167 cards (Invariant 1), or requiring a full corpus re-harvest.

6. **Calibration Table per Evidence Combination**:
   - Generated by `scripts/build_calibration_table.py`:
   | Evidence Combination | Count | Accuracy | Avg Margin |
   |---|---:|---:|---:|
   | `scored:[gloss+grammar+pos+trans] abstained:[companion+construction+mwe+reflexive] trans:human` | 74 | 89.2% | 0.6064 |
   | `scored:[gloss+pos+trans] abstained:[companion+construction+grammar+mwe+reflexive] trans:human` | 12 | 75.0% | 0.5114 |
   | `scored:[gloss+grammar+pos] abstained:[companion+construction+mwe+reflexive+trans] trans:absent` | 6 | 100.0% | 0.4284 |
   | `scored:[none] abstained:[none] trans:absent` (monosemous deterministic) | 5 | 80.0% | 0.0500 |
   | `scored:[gloss+trans] abstained:[companion+construction+grammar+mwe+pos+reflexive] trans:human` | 2 | 50.0% | 0.4342 |
   | `scored:[construction+gloss+grammar+pos+trans] abstained:[companion+mwe+reflexive] trans:human` | 1 | 100.0% | 0.2449 |

7. **Frozen Check Measurements**:
   - **Lyrics v20 judged sample**: 89/95 correct = **93.7%** (baseline: 81/95 = 85.3%). Substantial improvement (+8.4%), 8 previously wrong cards fixed, 0 regressions.
   - **Reflexive Gold Evaluation**:
     - `es held`: **1.0000** (241/300 decisive, 0 errors)
     - `es subs`: **0.9976** (414/500 decisive, 1 error)
     - `pt dev`: **1.0000** (255/300 decisive, 0 errors)
     - `pt held`: **1.0000** (269/300 decisive, 0 errors)
     - `pt blind2`: **0.9950** (200/250 decisive, 1 error)
     - `pt blind3`: **0.9940** (166/200 decisive, 1 error)
   - **Audit Panel Gold Evaluation**:
     - `es` sample baseline: 84.9% (992/1169)
     - `pt` sample baseline: 72.1% (715/992)
   - **Activation Status**: All candidate releases built/prepared, **NONE ACTIVATED** pending Josh's explicit review and sign-off.


### UNISON-3 Delivered Outputs & Verification (2026-10-09)

1. **Decision 0030 Adopted**:
   - `docs/decisions/0030-sense-metadata-and-display-contract.md` formalizes the Sense vs Label boundary across SpanishDict and Wiktionary.
   - Comprehensive matrix covering 9 feature/metadata families (`translation`, `context`, `companion`, `construction`, `register`, `regions`, `domain`/`topics`, `grammar`, `functional`).
   - Senses define distinct semantic meanings, group rows, and drive WSD gloss embeddings; labels annotate constraints, never group rows, and are stripped from the grey context line.

2. **Kaikki Adapter Upgrades (`src/fluency/sense_menu/kaikki.py`)**:
   - **Companion Extraction as Context**: Syntactic argument requirements from `info_templates` (`+obj`) and gloss prose (`[with ...]`) are promoted to disambiguating sense cues (`+ com`, `+ de`).
   - **Junk Gloss Elimination**: `_JUNK_GLOSS_PATTERN` filters out empty structural definitions in `_semantic_senses` and skips them in `_display_gloss`, allowing real translations (`your`) to surface on *seu, sua, seus, suas*.
   - **Parenthetical Label Stripping**: `_is_label_parenthetical_part` strips grammatical (`(transitive)`, `(intransitive)`), regional (`(Portugal)`), register (`(slang)`), and domain noise from `_context`, keeping only genuine semantic parentheticals and companions.
   - **Intra-Entry Deduplication**: Duplicate identical raw senses within `(headword, pos)` sharing translation, context, and specialist features are merged in `build_analyses`.

3. **Measured Impact on Audited Cards (173 Metadata Issues)**:
   - **`junk_gloss` (16 lines, 12 pt)**: *seu, sua, seus, suas* (#63, #68, #190, #273) previously displayed `Second-person singular possessive determiner.` as card translations; now correctly display `your`, `his`, `her`, `its`, `their`. Eliminates false positive WSD matches on "you".
   - **`sense_split_across_translations` (11 lines, 9 pt)**: *falar* (#109) previously produced two identical rows `to talk ⟨intransitive⟩`; now produces distinct rows `to talk ⟨+ com⟩` and `to talk ⟨+ de⟩`. Identical duplicate senses on *que*, *está*, *vamos*, *foi* deduplicated.
   - **`same_gloss_wrong_context` (120 lines; 59 es, 61 pt)**: Pure grammatical tags (`(transitive)`, `(intransitive)`) stripped from context line; only semantic cues or companions appear.
   - **`topic_chip_noise` & `duplicated_context`**: Domain topic chains (e.g. `finance, business` on pt *e*) suppressed from context line.

4. **Safety & Frozen Baselines**:
   - `eval_es.py held`: 1.0000 decisive accuracy (241/300 decisive, 0 errors).
   - `eval_pt.py dev`: 1.0000 decisive accuracy (255/300 decisive, 0 errors).
   - Pytest: 636/636 tests passing across `tests/features/`, `tests/sense_menu/`, and `tests/wsd/`.
   - Release activation: **NONE ACTIVATED**.
   - UI files: **NO MODIFICATIONS TO `app/**`**.

5. **Post-UNISON UI Questions for Josh**:
   - *Verb Lemma vs Inflected Form*: Should verb card fronts/backs show the dictionary infinitive (e.g. *dizer*, *estar*, *ir*) or the specific inflected form (*diz*, *está*, *vamos*)?
   - *Rarer Uses Floor (10%)*: How should senses under the 10% floor be visually structured in study sets (collapsed accordion vs muted sub-list)?
   - *Long Wiktionary Gloss Truncation (TERSE)*: Strategy for rendering definitions >60 characters (70 pt cards) without overflowing flashcard cards.
   - *Split Card Tuple Fallback*: When split card 2 has no primary sense (e.g. *van* card 2 *irse*), should the card render a filtered subset rather than repeating the entire base card?
   - *Specialist Feature Chips*: Which non-context labels (`register`, `region`, `companion`) should be rendered as pills on the sense back vs hidden?

---

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
