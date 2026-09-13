# Sense metadata architecture

Sense metadata is one subsystem with deliberately separate ownership layers.
No provider or language may bypass the canonical contract to add a card pill.

| Responsibility | Source of truth |
|---|---|
| Families and feature envelope | `src/fluency/features/contract.py` |
| Shared construction values | `src/fluency/features/construction.py` |
| Shared functional purposes | `src/fluency/features/functional.py` |
| SpanishDict field adapter | `src/fluency/features/spanishdict.py` |
| Wiktionary fields, tags and templates | `src/fluency/features/wiktionary.py` |
| Wiktionary gloss parentheses | `src/fluency/features/wiktionary_gloss.py` |
| Provider-wide empty defaults | `config/sense_menu/providers/*.json` |
| Language-specific tag adapters | `config/sense_menu/languages/*.json` |
| Language/provider registry | `config/sense_menu/registry.json` |
| Preservation and re-projection | `src/fluency/release/metadata_upgrade.py` |
| Learner-facing rendering and gating | `app/js/card-metadata-pills.js` |
| Cross-language contract tests | `tests/sense_menu/test_metadata_conformance.py` |

The canonical families are `companion`, `construction`, `domain`, `functional`,
`grammar` and `register`. A language does not invent another family. It adapts
its provider representation into one of these families and a shared kind/value,
or leaves the source value explicitly unclassified.

Every Wiktionary language policy has the same adapter slots, including an
explicit `construction_tag_mappings` object. An empty object means the concept
has no currently established tag mapping for that language; it does not mean
that the architecture forgot the category. Shared prose normalization still
applies to every Wiktionary language. Current established tag equivalences are:

- Czech and Portuguese `auxiliary` → `construction/auxiliary_frame=auxiliary`;
- French `direct-object` → `construction/object_role=direct object`;
- provider-wide `with-infinitive`, `with-gerund`, and analogous recognized form
  tags → `construction/complement_form`.

Functional categories do not need duplicated language maps: SpanishDict and
all Wiktionary languages call the same exact-alias adapter. Original wording is
always retained as `embedding_text`. Language-specific mappings should only be
added after an observed snapshot establishes their semantics.

Policy maturity remains explicit in `registry.json`: Czech, French and
Portuguese are audited; Dutch and Polish are partial; Italian, Russian and
Swedish remain scaffolds until source snapshots are audited. The shared slots
and fallbacks work for all of them, but scaffold status must not be mistaken for
empirical coverage.
