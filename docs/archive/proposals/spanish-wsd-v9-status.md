# Spanish speech WSD v9: forced leaf, display support, and Gemini recommendation

v9 keeps three decisions separate for every evaluated occurrence:

1. `forced_selection` always contains the classifier's best leaf.
2. `emitted_level` controls whether the optional supported view may show that
   leaf, only its gloss, only its headword/POS, or nothing.
3. `gemini_recommendation` says whether the cheap leaf choices disagree. It is
   recorded whether or not Gemini escalation is enabled. v9 never calls Gemini.

## Forced-leaf classifier

The forced leaf uses the strongest source-only stack that survived the v7/v8
work:

- the recovered SpanishDict menu lookup, including conjugated surfaces;
- the provider POS bridge and the Spanish `se` constraint;
- SpanishDict ordering plus exact sentence/gloss ranking;
- the existing renderable-leaf and required-companion repair;
- no supplied-English alignment and no frontier model.

Two full-deck audit failures were fixed before the final bundle:

- SpanishDict `CONTRACTION` analyses now survive an observed `ADP` tag, so `al
  acuario` no longer gets forced onto the special `al + infinitive` leaves;
- the fused-`se` check now examines the accented spelling before folding it, so
  `pensé` is no longer mistaken for a reflexive form and forced to `pensarse`.

Normalized grammar and companion features remain recorded for both providers.
Their newer hard gates remain off because the real-deck review found more breaks
than fixes. The older measured Spanish companion repair remains in the forced
classifier.

## Display support and Gemini recommendation

The dictionary-order choice and the raw sentence/gloss choice are computed
independently. Their deepest shared level controls display support:

- same leaf: `leaf`;
- different leaves with the same gloss: `glosskey`;
- different glosses with the same headword/POS: `tuple`;
- different headword/POS: `unresolved`.

Any result below `leaf` records `gemini_recommendation.recommended = true`.
This never changes or removes the forced leaf. The recommendation also records
`gemini_called = false`, so recommendation and execution cannot be confused.

## Complete Spanish run

- run: `20260901T180346Z-d6e4f0dc`
- WSD profile: `es-v9-1`
- final release: `es-speech-v9-20260901-r2`
- cards: 2,000
- selected examples: 5,994
- assigned examples in the release: 5,943
- unassigned examples in the release: 51
- fallbacks: 0
- Gemini calls: 0
- embedding cache: 13,934 required texts, all reused locally, 0 created

Across all 5,959 assigned occurrences in the imported WSD stage:

- forced leaf present: 5,959
- leaf supported: 2,795
- gloss only supported: 1,085
- headword/POS only supported: 1,700
- unresolved: 379
- Gemini recommended: 3,164
- Gemini not recommended: 2,795

The release validates. Activation was deliberately not performed because the
live-pointer change requires separate explicit approval; the rejected v8 preview
therefore remains active at the time of this note.

## Provider parity

The same `pt-v9-1` profile ran offline over the existing cached 200-card
Portuguese/Wiktionary input:

- 600 forced leaves;
- 177 leaf, 42 glosskey, 312 tuple, 69 unresolved;
- 423 Gemini recommendations;
- 0 Gemini calls and 0 missing forced leaves.

A fresh Portuguese menu exposed 59 uncached gloss texts. Offline-only execution
correctly stopped instead of transmitting them. The cached parity run proves the
shared v9 engine and output shape; it makes no claim about Portuguese meaning
quality.

## Verification

- 138 WSD tests pass.
- 39 provider-feature tests pass.
- 28 release tests pass.
- Full repository run: 488 pass, 3 unrelated existing app-shell assertions fail
  because they still expect an older service-worker version and Google Apps
  Script URL.
