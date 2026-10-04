# SIGN_OFF: GLEAN — MWE Re-Harvest & Curation for Merge Lemmas

**Date**: 2026-10-03  
**Status**: Signed off  
**Target Languages**: Spanish (`es`), Portuguese (`pt`), Czech (`cs`)  
**Scope**: Merge Lemmas (Decision 0028, Rule 3 & Lemma senses)

---

## 1. Executive Summary

Merge Lemmas keeps an inflected form on its own card when the card shows an expression frozen on that exact non-citation form (Decision 0028, Rule 3). Prior to this curation, the phrase inventories were uneven:
- **Weak phrases kept forms apart unnecessarily**: Phrases like Spanish *"qué tiene"* (on *tiene*) and *"aquí estamos"* (on *estamos*) were treated as freezing the verb form, keeping frequent verb conjugations from merging into their lemma cards.
- **Genuine frozen expressions were missing or misclassified**: Idiomatic frozen expressions like *"ya voy"* (on *voy*), *"mám za to"* (on *mám*), and *"co je ti?"* (on *ti*) were missing from explicit inventory or marked compositional.
- **Lemma constructions lacked clear structural separation**: Multiword constructions headed by the lemma (e.g., *dejar de*, *tener que*, *ir a*, *ter de*, *mít rád*, *dát se do*, *jít o*) existed only as raw gloss text or scattered collocations. Because they are compositional across inflections and argue for no specific form, they must live as senses on the merged lemma card (to be consumed by WSD/overlays in subsequent plant steps) and must **never** trigger Rule 3.

This audit audited the first 300 cards of `es`, `pt`, and `cs` (`v15-mend` releases) across Wiktionary and SpanishDict multiword extracts, preserved existing merge rules and code contracts, and delivered structured curated inventories in [`config/mwe/`](file:///Users/joshuathomasamar/PycharmProjects/Fluency-Next/config/mwe/).

---

## 2. Audited Inventories Overview

Structured inventories delivered to:
- [`config/mwe/es-curated.json`](file:///Users/joshuathomasamar/PycharmProjects/Fluency-Next/config/mwe/es-curated.json)
- [`config/mwe/pt-curated.json`](file:///Users/joshuathomasamar/PycharmProjects/Fluency-Next/config/mwe/pt-curated.json)
- [`config/mwe/cs-curated.json`](file:///Users/joshuathomasamar/PycharmProjects/Fluency-Next/config/mwe/cs-curated.json)

Each inventory strictly separates:
1. **List (a) — Frozen-form expressions**: Feeds Rule 3 (`hasFrozenFormExpression`). Contains specific non-citation/inflected surface forms (e.g. *sé* in *no sé*, *voy* in *ya voy*, *muchas* in *muchas gracias*, *vezes* in *às vezes*, *není* in *není zač*). Keeps the inflected form on its own card.
2. **List (b) — Lemma constructions**: Headed by the citation lemma. Forms verbal/grammatical periphrases and idioms (*dejar de*, *tener que*, *ir a*, *ter de*, *mít rád*, *jít o*). They become senses on the merged lemma card and **never** keep an inflected form separate.

---

## 3. First 300 Cards Audit & Measurement (v15-mend)

### Spanish (`es`)
- **First 300 cards total**: 300 cards
- **Cards kept separate before**: 52
- **Cards kept specifically by Rule 3 before**: 15 (*está*, *tengo*, *sé*, *estás*, *tiene*, *tienes*, *puede*, *estamos*, *sea*, *sabe*, *días*, *buena*, *importa*, *veo*, *muchas*)
- **Audit Findings**:
  - **Weak phrases identified**:
    - *"qué tiene"* (on *tiene*): Weak conversational deprecation; *tiene* should merge into *tener*.
    - *"aquí estamos"* (on *estamos*): Weak greeting reply; *estamos* should merge into *estar*.
    - *"tengo una pregunta"* (on *tengo*): Literal compositional collocation; *tengo* should merge into *tener*.
  - **Genuine frozen forms kept**:
    - *"no sé"* (keeps *sé* distinct from *saber* / *ser*), *"ya voy"* (keeps *voy* distinct from *ir*), *"muchas gracias"* (keeps *muchas* distinct from *mucho*), *"buenos días"* (keeps *días* distinct from *día*), *"buenas noches"* / *"buenas tardes"* (keeps *buenas* distinct from *bueno*).
  - **Lemma constructions separated**:
    - *tener que*, *dejar de*, *ir a*, *tener cuidado*, *tener en cuenta*, *echar de menos* are cataloged in List (b) and strictly excluded from triggering Rule 3.

### Portuguese (`pt`)
- **First 300 cards total**: 300 cards
- **Cards kept separate before**: 63
- **Cards kept specifically by Rule 3 before**: 21 (*é*, *uma*, *está*, *vamos*, *minha*, *sei*, *há*, *são*, *quer*, *obrigado*, *tua*, *boa*, *diz*, *outra*, *toda*, *seja*, *será*, *vi*, *vezes*, *sinto*, *diga*)
- **Audit Findings**:
  - **Weak phrases identified**:
    - *"eu tenho uma pergunta"* (on *uma*): Compositional sentence; *uma* is already handled by noun/indefinite rules, should not be frozen by this sentence.
    - *"já vi esse filme"* (on *vi*): Phrasal idiom on past tense *vi*; should not prevent normal merge if standard senses apply.
  - **Genuine frozen forms kept**:
    - *"às vezes"* (keeps *vezes* distinct from *vez*), *"não sei"* (keeps *sei* distinct from *saber*), *"muito obrigado"* / *"muito obrigada"* (keeps *obrigado/a* distinct from *obrigar*), *"não é"* & *"é que"* (keeps *é* distinct), *"será que"* (keeps *será* distinct), *"sinto muito"* (keeps *sinto* distinct).
  - **Lemma constructions separated**:
    - *ter de*, *ter que*, *deixar de*, *haver de*, *acabar de*, *estar a* cataloged in List (b).

### Czech (`cs`)
- **First 300 cards total**: 300 cards
- **Cards kept separate before**: 56 (predominantly Rule 1 ambiguity such as clitics/pronouns *mě*, *ti*, *se*, *by*)
- **Cards kept specifically by Rule 3 before**: 4 (*ve*, *máš*, *abych*, *jde*)
- **Audit Findings**:
  - **Genuine frozen forms added/confirmed**:
    - *"není zač"* (keeps *není* distinct from *být*), *"mám za to"* (keeps *mám* distinct from *mít*), *"co je ti?"* & *"děkuji ti"* (keeps *ti* distinct), *"jak se máš"* (keeps *máš* distinct from *mít*), *"děkuji vám"* (keeps *vám* distinct).
  - **Lemma constructions separated**:
    - *mít rád*, *dát se do*, *jít o*, *dávat pozor*, *být rád*, *dávat smysl* cataloged in List (b).

---

## 4. Code & Architecture Verification

Verified [`app/js/vocab.js`](file:///Users/joshuathomasamar/PycharmProjects/Fluency-Next/app/js/vocab.js#L840-L935) and [`src/fluency/enrichments/card_rules.py`](file:///Users/joshuathomasamar/PycharmProjects/Fluency-Next/src/fluency/enrichments/card_rules.py#L31-L97):
1. **Rule parity**: `isExpressionSenseForLemma` and `hasFrozenFormExpression` mirror `is_expression_sense` and `lemma_group_key`. Tests in `tests/app/test_card_rules_parity.py` and `tests/app/test_lemma_merge_key.py` pass 100%.
2. **Structural boundary**:
   - `hasFrozenFormExpression(item, lemma)` checks that `surface !== lemma` and that the surface is contained in the expression tokens.
   - For List (b) constructions, when headed by the lemma (e.g., `tener` for `tener cuidado`), `surface === lemma`, so `hasFrozenFormExpression` returns `false` by contract.
   - When inflected forms appear (e.g., `tiene que` for `tener que`), List (b) entries are marked as verbal head constructions, ensuring they do not populate as frozen surface entries for `tiene`.
3. **No merge rules were reopened**: Decision 0028 rules 1, 2, and 3 remain exactly intact.

---

## 5. Leftovers & Next Steps

1. **GLEAN is complete**: Curated List (a) and List (b) inventories are committed and documented.
2. **Plant Step (Subsequent)**: Full WSD / overlay reruns for List (b) lemma constructions will be executed in the next plant cycle to stamp multiword senses directly onto lemma cards.
3. **KINDRED Hand-off**: GLEAN has cleanly settled the phrase inventories. KINDRED can now proceed to cognate mapping calibration.
