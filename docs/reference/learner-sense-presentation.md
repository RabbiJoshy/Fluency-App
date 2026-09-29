# Learner sense presentation: schema and handover

Updated 2026-09-29. This is the high-level product agreement and handover for
vocabulary-card backs. Read it alongside [metadata_architecture.md](metadata_architecture.md),
which documents the underlying canonical feature contract. They describe
separate layers: what the source information means, and what learners see.

## Status and scope

The user approved a simple first pass for visual evaluation. Shared grammar
cues and the no-budget experiment shipped in `20db82de`; the shared shaded
cue-area layout shipped in `39829ee9`. This is not a finished metadata policy
or a completed multilingual audit. Subsequent work should start from live
cards and the user's feedback, not assume every currently visible label has
already earned its place.

Keep this system deterministic, provider-neutral and shared across languages.
SpanishDict and Wiktionary equivalent information must receive equivalent
presentation. Provider fields are inputs, never automatic display entitlements.

## Two axes: content category versus presentation destination

These conceptual content categories are a product vocabulary, not a replacement
for the canonical data schema:

| Content category | Subcategories / purpose |
|---|---|
| Meaning | The shortest clear learner meaning |
| Sense context | Semantic scope or a distinction between neighbouring meanings |
| Grammar | Form (person, number, tense, etc.); construction (required words, cases, complements); function (grammatical role) |
| Usage | Register, region, domain and other meaningful restrictions |
| Evidence and uncertainty | Examples, attribution, assignment confidence and possible meanings |

The stored canonical feature families remain `companion`, `construction`,
`domain`, `functional`, `grammar`, and `register`. In particular, canonical
`functional` and the UI grammar subtype `function` are not interchangeable.
The conceptual grammar category can draw from multiple canonical families.
No schema, adapter or release changes were authorized by the presentation work.

## Three destinations for sense information

| Destination | Contract | Visual treatment |
|---|---|---|
| Gloss / level 1 | Required: shortest clear learner meaning | Main area, centered within its allocated space |
| Key / level 2 | Optional: information worth seeing immediately to distinguish or correctly use the meaning | Subtly shaded cue area; context and grammar can coexist |
| Note | Optional: worthwhile additional meaning, construction or usage explanation | Information button at the left edge of the whole sense row |

Grammar is a content category, not a fourth display tier. Do not leave loose
sense labels outside these destinations. Do not put everything rejected from
levels 1 and 2 into the note: redundant and technical source metadata can be
omitted from the learner view without deleting it from storage.

Headword, pronunciation/audio, examples, source attribution, commonness and
learning controls serve separate card functions and keep their own areas.
Uncertainty must qualify the relevant claim (for example a possible-meanings
heading); it must not be silently presented as an established assignment.

## Deterministic selection: implemented foundation, not final policy

`learnerSensePresentation()` in `app/js/card-metadata-pills.js` returns:

- `gloss`: learner-facing meaning text;
- `key: { text, items }`: residual context and selected metadata cues;
- `note: { gloss, context, items, available }`: curated additional information;
- `grammar: { items }`: the grammar subset of key items, not another destination.

Compatibility aliases also remain. Provider inputs pass through normalization,
compaction, combination and redundancy filtering before selection. Rules use
feature families/kinds/values, comparisons with peer senses and existing gloss
content; they do not invoke a model at render time.

In the current `ignoreBudget` experiment, selected cues include production
requirements (companions, required cases, complement frames), register/domain
cues, navigation grammar, designated semantic/temporal/discourse features and
sense-defining grammar. Peer distinctions affect ranking. Residual context is
shown without budget truncation. Grammar is styled consistently and classified
as form, construction or function by `grammarCueCategory()`.

This is a broad first-pass selector. It does **not** prove that every admitted
register, domain, grammar label or residual context is useful. Refine importance
and redundancy from recurring real examples, not per-word overrides. The ideal
"shortest clear gloss" is also not guaranteed merely by the current projection.

## Budget experiment and layout

Stored budget policies remain, but the current card presentation ignores text
and six/eight-row budgets. Useful keys remain visible on inactive rows; selection
changes emphasis, not eligibility merely because of spare space. Rows wrap and
the meanings area scrolls when needed. Never add content just to fill space.

The shared layout is: left information control, main gloss, optional shaded
cue area, right commonness control. Both edge controls have reserved space.
The cue area fits content up to 48% of the body width. At a row content width
of 340px or less it stacks beneath the gloss and can use the full body width.
Text is centered within each area. Note-only singleton rows leave no empty
shaded area after the disclosure button is moved out.

Matching-gloss groups retain a shared gloss and individually selectable cue
cells. Context-only grouping is disabled in this experiment: a shared grammar
or context label must not collapse different meanings. Grouped notes are pooled
under one whole-row information button, with labels where multiple notes exist.
Grouping and pooled-example honesty remain audit questions, not settled merely
by having the shared layout.

## Implementation map

- `app/js/card-metadata-pills.js`: normalization, cue importance, redundancy,
  gloss/key/note selection, grammar classification and note rendering.
- `app/js/flashcards.js`: `learnerRowPresentation`, grouping, row rendering,
  `placeRowInformationButtons`, `arrangeSenseCueAreas`, scrolling and layout.
- `app/css/style.css`: final "Shared learner cues" and "One provider-neutral
  layout" sections, alongside older card styles.
- `tests/app/test_sense_metadata_behavior.py`: selection and provider-regression
  tests; fixtures in `tests/app/fixtures/`.
- Both `app/config/dev_changelog.json` and `config/dev_changelog.json`: shipped
  change records. Follow `CLAUDE.md` for validation and deployment.

The last pass ran all 178 app tests and visually checked Portuguese `que` and
Spanish `tener` at phone and desktop widths, including grouped cue selection.
That limited check must not be reported as the originally requested full audit.

## Open work and boundaries for the next chat

1. Get visual feedback on the new shared cue areas. Check dense, long, grouped,
   monosemous, selected/inactive and possible-meaning cases across languages.
2. Review which grammar and usage subclasses actually deserve level 2. Check
   duplicated construction cues, residual prose and inconsistent pill styling.
3. Verify essential information is not hidden, note icons earn opening, and
   matching glosses do not conceal distinct senses or misleading pooled examples.
4. Evaluate the no-budget experiment for readability and access to examples and
   controls. Do not silently restore budgets or assume the experiment is final.
5. Retain gloss–key–note unless a recurring class of real cards cannot fit it
   naturally. More content categories alone do not justify another display tier.

The original full audit remains outstanding: first 300 Portuguese, 150 Czech,
100 Spanish and 50 of every other actually shipped language, each at 390×844
and 1440×900. Record default session settings/order, coverage and evidence;
separate measured recurrence from inference. Confirm languages in the live
chooser rather than equating repository scaffolds with shipped availability.

Do not change source data, definitions, release JSON, WSD, sense ordering,
dictionary adapters, public APIs or manual overrides to disguise presentation
problems. Record suspected data/WSD faults separately. Do not touch unrelated
Finnish pipeline/WSD work or the pre-existing study-set CSS relocation.
