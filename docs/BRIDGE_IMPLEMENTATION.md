# BRIDGE — implementation and verification

2026-10-12. Implements the cross-language skipping requested in the BRIDGE
roadmap, together with the shared language profile. Production promotion remains
separate from staging review.

## Learner behaviour

- Onboarding asks once which languages the learner can comfortably read, offering
  14 choices including Polish. A confirmed empty answer is valid.
- Settings → App → Languages you know edits one account-scoped, synced profile.
  Guest choices are local and can seed a new account without replacing an
  existing account's profile. Old browser preferences migrate once.
- Smart Skip's profile-language buttons restrict filtering for the current target;
  they no longer overwrite the shared profile or another target's preferences.
- The separate **Use words I've learned in other languages** switch is opt-in
  per target. The master Smart Skip switch disables it without forgetting it.
- BRIDGE skips a card only when every mapped target meaning has a qualifying
  source meaning. Additional meanings on loaded or merged cards keep the card
  unless they occur in the verified target requirements. Expressions remain
  protected by the existing v4 rules.
- Skipped cards remain browsable in the existing Smart Skip list, with a reason
  such as “From your learned Spanish: años”. Target answers, SRS stages and
  recorded coverage are never written by BRIDGE.

## Curated pairs and full language profiles

2026-10-12 follow-up: `app/config/smart-skip-pairs.json` explicitly declares
useful source languages for each target. Josh confirmed the initial Romance,
Czech/Polish/Slovak and close Germanic direction, retaining existing English
mappings. Finnish/Estonian and Russian/Ukrainian/Belarusian are also declared
close-pair candidates. A listed pair does not promise that its mapping exists.

Both runtime filtering and the offline builder honour this list. Adding a
policy file alone cannot generate an unapproved cross-combination. Existing
bundles already fit the approved list, so this change does not add mapping data.

Smart Skip shows only relevant profile languages; unmapped relevant choices are
disabled and marked **Coming soon**. Its Languages you know editor shows the
curated target list, preserves unrelated saved languages, and links to the full
profile in Settings. Following Josh’s picker refinement, onboarding and general
Settings offer only the fixed catalogue; there is no free-text Add language action.
Languages without an app study deck are labelled **Coming soon** in the full
profile, but remain selectable as known languages. English remains the app’s
translation language. Existing saved custom labels remain readable and preserved,
but are not offered as new picker choices.

The language picker uses a header X that discards unsaved edits and a centred
Save button. Dismissing first-run onboarding confirms the existing choices rather
than saving a draft. Song selection, playlist import, dictionary-leaving confirmation
and the word-saving popup also use an X without a duplicate Cancel action.

## Knowledge evidence

Use the existing `getProgressState(...).known` contract: at least one correct
answer and no unresolved newer mistake. A merely seen word does not qualify.
A due source word retains recorded knowledge; being due is not an explicit
incorrect answer.

Reuse `mergeKnowledgeProgress` for parent/sense precedence. An explicit sense
mistake cannot be erased by a subsequent general whole-card yes. A newer whole-
card no still reaches inherited senses. Source split-card evidence is restricted
by headword and POS. Cross-mode and historical surface IDs are resolved by the
same progress identity engine, with the source language passed explicitly.

Only represented source meanings inherit card-level progress: explicitly
unassigned or zero-frequency unused dictionary senses are ineligible. A recorded
whole-card correct is the app's existing baseline for its represented meanings;
explicit per-meaning answers refine that baseline. No additional claims of
full-language fluency are inferred.

Source progress epochs invalidate the setup vocabulary signature and verdict
cache. The next prepared set and setup counts therefore reflect updated source
knowledge. BRIDGE does not rewrite an in-progress set.

## Mapping and form safeguards

`scripts/build_bridge.py` reuses `build_app_cognates_by_sense`, its English gloss
pivot, CogNet checks, source-primary-reading safeguards and existing pair scorer.
New pair policies are files, not branches of a second matching engine. Initial
new-pair cutoffs are conservative 0.80, without claiming a comprehensive manual
calibration.

The new `verb_forms.py` adapter reads dictionary form tags and checks compatible
person, number, tense, mood, aspect and voice. Lexical aspect declared on Czech
or Polish dictionary headwords is carried onto their forms. Ordinary infinitives
can match ordinary infinitives; personal infinitives and undeclared/unsupported
forms are retained. An infinitive match never licenses conjugated forms or
assumes a verb's entire paradigm is regular/known.

These form safeguards apply to BRIDGE and to non-English whole-language cognate
skipping for the bundled targets, including Czech/Polish. Existing English
cognate scoring is preserved; the cross-language transfer switch has no English
study-progress source.

A bundle declares its target release, source releases, extract snapshots,
policies and scoring method. Target-release mismatches fail closed. Source
progress is used only when its current configured release matches the source
snapshot. A release update requires rebuilding these assets; stale mappings must
not silently transfer knowledge to changed meanings.

## Available data, measured rather than assumed

Bundles use the configured 10,000-card Spanish and Portuguese releases, the
200-card French release, and the 10,000-card Czech release. Progress transfer
supports Spanish/French/Portuguese directions for which the existing scorer
produces a safe match. Czech/Polish has whole-language form compatibility, but
Polish has no active source study release and is not offered as a BRIDGE progress
source.

The runtime audit set every represented source card known in an isolated test
harness (not a real user account). Its upper bounds are:

| Target | Cards qualifying in that synthetic upper-bound check | Named check |
| --- | ---: | --- |
| Spanish | 906 | años from Portuguese anos |
| Portuguese | 2,420 | anos from Spanish años |
| French | 1 | jamais from Spanish jamás |

These are not expected skip counts for Josh or other learners. Actual eligibility
requires their own saved source meaning knowledge. French is highly constrained
by its current release and conservative matching; French release completion
remains a CONVOY rollout dependency. The feature does not publish or activate a
new French deck.

## Validation

- `tests/app/bridge_checks.cjs` runs the real progress, item-knowledge, profile and
  BRIDGE code against partial knowledge, historical IDs, explicit mistakes,
  split cards, additional merged meanings, master-off behaviour, mismatched verb
  forms and release changes. It also evaluates the actual generated assets and
  verifies that filtering never changes learning progress.
- Both profile and Fast Track preference writers use the isolated staging sync
  identity, verified by regression checks.
- Profile tests cover empty answers, account isolation, stale remote metadata,
  guest migration and preserving languages independently of a target.
- `tests/features/test_verb_forms.py` covers finite/infinitive compatibility,
  undeclared forms, personal infinitives and Czech/Polish lexical aspect.
- The app suite passes 265 tests. The four new morphology tests also pass.
- Full-app browser checks cover the 14-choice onboarding (including Polish),
  no repeat prompt for another target, Settings editing/cancel, BRIDGE toggling,
  master-off/re-enable, narrow phones, larger text and desktop. External progress
  writes were blocked; account sync was checked through the real metadata queue
  payload and apply-remote logic in the isolated test harness.

Build example (all inputs are local; no paid inference):

```sh
PYTHONPATH=src python3 scripts/build_bridge.py \
  --workspace ../Fluency-Workspace \
  --extract es=../Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-13/kaikki.org-dictionary-Spanish.jsonl \
  --extract fr=../Fluency-Workspace/raw/wiktionary/enwiktionary-2026-08-05/kaikki.org-dictionary-French.jsonl \
  --extract pt=../Fluency-Workspace/raw/wiktionary/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl \
  --extract cs=../Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-06/kaikki.org-dictionary-Czech.jsonl \
  --extract pl=../Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-06/kaikki.org-dictionary-Polish.jsonl
```

Related design: `KNOWN_LANGUAGE_PROFILE_DESIGN.md`; decision 0028; BRIDGE and
CONVOY in `CHAT_ROADMAP.md`.
