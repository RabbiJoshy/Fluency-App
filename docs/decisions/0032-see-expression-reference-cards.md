# Decision 0032 — Readable links and See-only expression reference cards

22 October 2026. User scope: generate expression reference cards only when an
existing card links to a multiword target with a `see` relation. No additional
expression discovery, deck entries, search entries or grading is introduced.

## Behaviour

Meaning links inherit ordinary meaning text size and have at least 44px touch
targets. The row fitter wraps linked content instead of shrinking it or
truncating a button's markup. Synonym labels, textual source controls and
card-reference tool labels also use normal readable text sizes.

An explicit multiword See target opens a native modal reference card with the
dictionary definition, usage distinctions, available dictionary examples and a
source link. Back or Escape returns focus to the original word link. Keyboard
events inside the modal cannot operate the underlying study card. No deck
array, surface identity, saved progress or study statistics are changed.

Other reference relations retain ordinary word-card navigation. A missing
expression definition gets an explicit empty/error state, never an unrelated
first-word fallback. No MWE entry points elsewhere are added by this feature.

## Data

`app/js/sense-reference-cards.js` loads `seeReferencesPath` on demand. The
language-scoped asset uses `see-expression-references/v1`, declares
`scope: see_links_only`, and contains only explicit multiword See targets from
the source deck. Existing attached expression definitions can provide a local
fallback. Dictionary text is escaped; source links must use HTTPS.

Build the Portuguese supplemental file from its pinned provider extract:

```sh
python scripts/build_see_reference_cards.py --language portuguese \
  --dictionary ../Fluency-Workspace/raw/wiktionary/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl
```

The builder reads the configured immutable index, records source/index hashes,
declares unresolved targets, and supplements app data without rewriting any
release. It includes zero-corpus-frequency dictionary entries. It never turns
corpus frequency into a condition for reference lookup. Only explicitly typed
dictionary examples are included; quotations, raw corpus matches, redirects and
misparsed example-as-definition rows are not promoted into teaching evidence.

The current Portuguese targets are acabar de, haver de, ter de and ter que.

## Why haver de was missing

The MWE inventory explicitly recognises haver de as non-compositional. Its
`corpus_freq: 0` and `reason: zero_freq` place it in the existing reference-only
tier, so it was not offered to occurrence WSD or published as an expression
sense. That distinction is deliberate in `src/fluency/wsd/multiword.py`.

The snapshot counter in `src/fluency/mwe/builder.py` counts literal adjacent
word n-grams. It does not aggregate conjugated or hyphenated variants such as
hei de, havia de or hei-de under haver de. Published examples do contain those
constructions, so the literal zero does not establish absence of the verbal
construction. This change supplies reference access without changing the
counter, admitting zero-evidence occurrence assignments or inventing examples.

## Verification

Python tests check See-only extraction, source filtering and all four shipped
targets. Browser checks at 320px, 390px and 1000px exercise the actual reference
link renderer, shared CSS, row fitter and dictionary asset; they verify normal
text size, 44px targets, the correct destination, no progress/deck mutation,
keyboard isolation, focus return, missing-target feedback and no non-See entry
point. `tests/app/see_reference_cards_checks.mjs` is the browser integration
check; the mobile preview is in `docs/audits/see-reference-cards/mobile.png`.
