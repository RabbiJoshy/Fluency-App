# Decision 0029 — All-or-nothing noun number merging

Noun forms merge only when their complete, uninflected dictionary menus have
the same set of lexical senses. An extra sense on either side keeps the entire
group separate; there are no noun companion cards or partially merged senses.
Whole-word noun merging also requires one dictionary entry, identified by
headword plus part of speech, on both sides. A noun and verb with the same
headword spelling are separate entries: `ser` / `seres` and `poder` / `poderes`
stay separate even when both menus inherit all the same noun and verb senses.
Repeated analyses of the same noun entry across providers are permitted.

## Evidence and comparison

Stage-02 SpanishDict and Wiktionary adapters stamp `noun_merge` verdicts before
WSD, rare-sense filtering, menu caps, or English display inflection. The
comparison includes source adapter, headword, POS, source sense reference,
original definition and translation, and lexical features. Order, duplicate
copies, usage frequency, examples, and surface grammatical marks do not affect
the set. No English singularisation or semantic guessing is used.

Every noun form must have a provider-declared relationship: SpanishDict's
explicit plural inflection result, or Wiktionary's structured form-of relationship
with plural grammar. The singular's complete menu must also be present in the
build. Missing counterparts or relationships keep forms separate.
Explicit gender/singular inflections are outside this number-pair rule and
cannot prevent an otherwise equivalent singular/plural pair from merging.

Sense-level number restrictions block the group even when both forms inherited
the same menu. These include plural-only, singular-only, in-plural,
usually-plural, and no-plural senses. Wiktionary entry-level restrictions are
retained too. SpanishDict's original POS label is preserved separately from
normalised POS, including "plural noun". Older caches lacking that original
label cannot approve noun merges; neither can older Wiktionary menus that did
not preserve entry-level tags. Re-fetch or rebuild the source evidence rather
than interpreting absent metadata as permission to merge.

The provider chain compares combined menus, not separate partial provider
results. Conflicting verdicts across artists keep the combined card separate.
Existing ambiguity, contraction and frozen-expression protections still apply.

## Delivery and compatibility

`noun_merge` contains `rule_version: noun-merge/v2`, `lemma`, `allowed`, and a
diagnostic `reason`; approved verdicts also carry a `sense_set` fingerprint.
It survives clean release assembly, the app compatibility index, skinny index
columns, and artist-master joins. The app and Python merge-key builder use the
same verdict for deck grouping, Smart Skip, examples, Extras and estimation.
Recorded surface progress and displayed inflections are unchanged.

Merge-exceptions v3 carries `noun_merge_rule` and optional `noun_verdicts` beside
the existing per-surface keys. Rebuild keys using `scripts/build_merge_exceptions.py`
with `--release-index` and optionally `--sense-menu` for the matching full
stage-02 menu. The latter provides a supplemental verdict without editing an
immutable release. Matching surface card IDs, spellings, and complete source
sense references are required, including unused and nested senses.
Existing keys from an older rule version are ignored; unloaded cards remain
separate until current keys or full senses are available. Existing noun rows
without a complete-menu verdict remain separate.
Version 2 invalidates version 1 approvals that could merge mixed noun/verb
entries. Loaded-card guards also check unused and nested senses for another entry.

## Refreshing existing Speech releases

`scripts/refresh_noun_merge_metadata.py` copies the release's original stage-02
menu and supplements evidence without changing senses, references or examples.
For Wiktionary, a rebuilt menu must match the complete original references,
definitions, translations and lexical features before entry tags and form
relationships are copied. SpanishDict responses must match the complete original
headword, translation, source context and region sets before original POS labels
and explicit plural relationships are recovered. New plural-only labels are
retained as number restrictions. An extra fresh sense, a rejected response,
missing relationship or mismatched release references keeps the group separate.

Refresh failures are recorded on the supplemental menu and remain blocking when
the merge-exceptions builder recomputes verdicts. Outputs carry content hashes of
the original menu, release index and evidence; the final metadata also identifies
its release and supplemental menu. Published releases and their progress IDs are
not edited.

The 2026-10-10 refresh for es/pt Speech v23 approves 314 Spanish and 335 Portuguese
groups under the full app rules. Spanish evidence covers all 773 candidate
spellings; Portuguese uses the pinned 2026-08-20 Wiktionary dump. The detailed
evidence, rejected groups and pair lists live outside Git under
`Fluency-Workspace/audits/noun-merge/2026-10-10-v2/`.

## Validation

Tests cover equal menus with surface grammar differences, reordered and duplicate
senses, an extra sense on either side, number-specific senses, ambiguous
headwords, missing relationships/counterparts, source-reference collisions,
SpanishDict declarations, Portuguese/Spanish Wiktionary form-of rows, skinny
delivery, assignment filtering, estimates, and Python/JavaScript parity.

These are deterministic correctness checks, not a measured 90–100% dictionary
accuracy claim. Measure both missed exceptions and unnecessary separations on
an independently labelled sample per provider/language before making that claim.
