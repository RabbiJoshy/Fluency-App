# Decision 0031 — Merge only matching visible lexical sense sets

**Superseded for study grouping by [0033](0033-form-privilege-merging.md) (26 October 2026).**

22 October 2026. Adds a study-equivalence condition to decisions 0028 and 0029;
their ambiguity, contraction, frozen-expression and complete noun-menu
protections remain necessary.

## Rule

Two eligible forms of the same headword share a study card only when their
visible lexical source-sense sets are identical. The comparison uses the app's
`finishCardMeanings` routine, including low-share pooling and promotion. Hidden
rarer senses and unattested dictionary-menu senses do not veto an otherwise
equal pair. Empty sets do not establish equivalence. Equal subsets within a
paradigm may merge even when other forms of that headword remain separate.

Senses are identified by `source_reference`, with the existing
POS/translation/context signature fallback. Per-surface sense IDs and inflected
English glosses do not establish a different lexical sense. Percentages can
differ if they retain the same visible set. Expressions are separate teaching
items; the existing frozen-expression veto still applies.

This compares the lexical display-selection layer before final gloss rendering,
grammar-word presentation, or sibling example pooling. It is not a claim that
all contexts or conjugations are interchangeable. In particular, it does not
repair erroneous assignments such as the five existential havia examples
published as “ago” in the current Portuguese release.

## Why

[The paired experiment](../audits/attested-merge-comparison/README.md) compared
the full-attested and visible-set rules on the configured es/pt releases.
About 94% of pairs equal on the visible set but unequal on the full set differed
only through senses with one or two assignments. Inspected examples included
misassignments caused by English translation wording. Counting every such
assignment as a mandatory exception over-separates ordinary verb forms.
The visible-set rule can also over-separate valid senses which cross the
display threshold; it is a pragmatic rule, not an independently measured
reconstruction of true sense distributions.

## Implementation and identity

- `lemmaGroupKey` retains its existing meaning: eligible headword, or empty.
  It remains suitable for printed citation forms and dictionary lookup.
- `lemmaStudyGroupKey` combines that headword with the visible-sense signature.
  Deck election, seen-state inheritance, cognate-group exclusion, sibling
  example/frequency pooling, Extras and placement estimation use this key.
- These are transient metadata. Surface card IDs, full IDs and recorded learner
  progress are unchanged. A differently populated back no longer inherits
  seen-state solely through the shared headword.
- Pool examples by dictionary source sense; an unmatched rare sense must never
  fall back to the first meaning on its host.

## Precomputation and loading

`visible-senses/v1` signatures travel in the existing release-bound merge
overlay as `visible_sense_rule` and `visible_sense_keys`. The rule supplements
the eligibility keys; it does not replace the noun proof or change release
content. Configured overlays and placement pools use new cache-safe URLs.

`scripts/build_visible_sense_merges.cjs` evaluates the marked pure app helpers,
so the display threshold policy has one implementation. The Python
`build_merge_exceptions.py` calls this helper when building release keys and
therefore requires Node for that step. The configured-refresh command preserves
existing contraction lists, noun verdicts and their provenance. Source-code
hashes identify the generating display code. A change to display-selection
semantics must bump the visible-sense rule and regenerate the overlays/pools.

Cold rows without current visible evidence stay separate. Hydration preserves
the overlay; changing releases clears it. A Speech signature can only be
applied to its matching index URL, never to an artist index inheriting the
Speech manifest. Loaded artist data derives its own signatures.

Supplement refresh also withdraws older eligibility approvals when the current
release's full row exposes another headword. It retains existing explicit
exclusions, including after hydration. This repaired five stale Portuguese
approvals without admitting previously excluded forms.

## Validation

Regression checks cover equal visible sets with different rare tails, additional
visible meanings, threshold crossings with identical full repertoires, order and
duplicate rows, stable source references across inflected glosses, existing
eligibility vetoes, cold/loaded parity, release switches, study-state keys and
source-sense example pooling. Shipped metadata checks require a visible decision
for every eligible surface in each configured Speech overlay.
