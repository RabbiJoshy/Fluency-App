# Sense metadata audit — 21 September 2026

## Shipped treatment

Meaning and context text stays visible on inactive as well as selected rows. Short supporting labels use badges; phrases wrap as text. Long groups can stack at narrow widths. Meaning text has a 13px floor and badges a 12px floor, both tied to the card text scale. Additional grammar remains available on selection. Essential region/register restrictions are exempt from the former two-label limit.

| Language / dictionary | Meaning distinctions | Supporting information |
| --- | --- | --- |
| Portuguese / Wiktionary | Preserve “a bit of”, “quite a”, article uses and semantic parentheses. Give “the” priority over the encyclopedic article definition; retain the original in Full definition. | “with de” takes precedence over redundant intransitive. Keep nuanced region/usage wording attached to its sense. |
| Spanish / SpanishDict | Keep place, time and manner within their shared-gloss group. Different source phrases that normalize to one functional value retain their wording when necessary. | Show “with con”, “command”, “addressing several people”, and relevant domains. Translation-locale labels remain separate from Spanish usage. |
| Czech / Wiktionary | Preserve myself/herself/themselves and preposition-specific contexts. | Show “with na” for a companion word and “takes instrumental case” for a construction. Preserve exact aspect terms in details. |

These are shared concept rules, not separate dictionary-specific layouts. Context is removed only when its substance is represented by visible information; unrelated grammar cannot erase it. Peer comparison is limited to the same gloss, headword and part of speech.

## Verification and limits

- Programmatic census: all 10,000 cards in each current pt/cs/es speech-v15-10000x10 release; all six canonical families are represented.
- First 1,000 cards per language: 136 Portuguese, 6 Czech and 487 Spanish shared-gloss groups. No duplicate resulting context/metadata cues within those groups. Three Portuguese generic readings (seus, sinal, jeito) have no additional cue; their original gloss remains the row fallback alongside qualified siblings. No new label or merge was invented.
- Actual production renderer, using 20 compact fixtures extracted from those releases: a/o/não/um/para/uma/lhe/gosto; se/na/v/si/s/čekat; de/en/su/estoy/padre/ven.
- 41 expanded groups checked at both 375px and 1280px: 82 group/width combinations, no measured metadata font-floor or horizontal-overflow failures. Screenshots additionally reviewed representative shared-gloss, long-context and Czech case/reflexive layouts. This is a fixture-based UI audit, not a screenshot audit of 3,000 live cards.
- Behavior regressions cover preserved context, regional restrictions, grammar, cases, escaping and provider parity. Full app test suite passes.

## Source-data handoff

1. Czech case names arrive in some records as companion/required_word (e.g. s/se instrumental). The UI narrowly recognizes grammatical case names and displays a case construction. Correct the upstream classification rather than extending this bridge to arbitrary words.
2. Some Portuguese article records mix contradictory sense/surface gender tags. This audit does not rewrite linguistic source data. Review the adapter/release projection before asserting a gender from those records.
3. The three generic Portuguese readings above deserve source review if stronger distinctions are wanted. Their absence of a context is explicit; UI wording must not fabricate one.

The census checks display preservation and distinction, not dictionary correctness or every corpus assignment.

## Second pass — cleaner disclosure and broader examples

- Details / Hide is inline, without a numeric count bubble; content wraps independently of the control. Expansion remeasures the scroll budget and excludes the bottom toolbar's auto margin, which is free space. Resize and full-definition disclosures also remeasure.
- Section previews are collected from actual emitted rows after display filtering. Their +N counts cannot include omitted inventory.
- Added 20 Portuguese/Spanish release fixtures: eu, ele, ela, tem, ter, pelo, dar, seja, porquê, sexo; yo, él, ser, era, estar, fuera, tener, debería, hubiera, cuyo.
- Shared deterministic rules deduplicate identical semicolon clauses, shorten known grammatical boilerplate without stripping qualifications, and put the semantic explanation before a bracketed construction. Shared transitivity is available in Details rather than repeated beside every sibling context. No per-word overrides or dictionary edits.
- Compared note formatting over the first 1,000 pt/es cards. The shared note formatter changes 38 Portuguese and 58 Spanish contexts; some Spanish boilerplate was already shortened by the separate context renderer, now consolidated into the shared rule.
- Verified 127 app tests; 134 expanded group/width combinations across the 40 fixtures at 375px and 1280px; 12 targeted normal/large-text checks. Sparse pronoun cards expose details without a scrollbar; genuinely dense ter/dar examples retain bounded scrolling. The larger text check uses the existing card text scale hook in an isolated renderer harness.
- Pronoun compression is agreed but remains a separate pending change; this pass does not merge identities or selectable senses.
