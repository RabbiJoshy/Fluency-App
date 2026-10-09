# Decision 0030 — Sense Metadata, Grouping, and Display Contract

**Date:** 2026-10-09  
**Status:** Decided  
**Context:** UNISON campaign (Part 3: Metadata Pass).  
**Applies to:** Sense adapters (`SpanishDictSenseMenuAdapter`, `KaikkiSenseMenuAdapter`), WSD feature extraction (`fluency.features`, `fluency.wsd`), card compilation and presentation (`research/unison/cards.py`, `display.mjs`, and app consumers).

---

## 1. Context & Motivation

During the UNISON Part 1 audit (`docs/unison/AUDIT.md`, `docs/unison/audit-300.jsonl`), 167 of the 771 logged issues originated in the dictionary menu, metadata, and display layers:
1. **`same_gloss_wrong_context` (120 lines; es: 59, pt: 61)**: Senses with shared translations were misattributed or displayed identical contexts, confusing learners and WSD priors.
2. **`junk_gloss` (16 lines; es: 4, pt: 12)**: Dictionary structural descriptions (e.g. *seu* `Second-person singular possessive determiner.`) were treated as English translations, polluting cards and misleading WSD into matching "you" instead of "your".
3. **`sense_split_across_translations` (11 lines; es: 2, pt: 9)**: Complementary syntactic requirements (such as *falar* "to talk" with *com* vs. with *de*) collapsed into identical rows `to talk ⟨intransitive⟩`, masking the preposition distinction on the card front/back.
4. **`duplicate_sense_across_headwords` (6 lines; es: 4, pt: 2)**: Redundant identical senses across headwords (*hay* / *haber*).
5. **`topic_chip_noise` & `duplicated_context`**: Domain topic chains (e.g., Wiktionary `finance, business` on *e*) leaked into the grey context line, and labels were repeated across sibling rows.

The root cause was the lack of an explicit, unified contract defining what constitutes a **Sense** (a distinct semantic meaning unit that groups rows and drives lexical choice) versus a **Label** (a grammatical, syntactic, regional, or register constraint that annotates a sense).

Under Decision 0020, Wiktionary's `_context` derivation indiscriminately stuffed leading parentheticals (such as `(transitive)` or `(intransitive)`), topic tags (`finance, business`), and register qualifiers (`archaic`) into the `context` field. Because card display formats rows as `translation ⟨context⟩` and groups rows by `(translation, context)`, pure labels were promoted into sense discriminators, creating duplicate rows, noisy chips, and semantic confusion.

---

## 2. Decision: The Sense vs. Label Contract

Every piece of metadata extracted from a dictionary provider belongs either to the **Sense** category or the **Label** category:

- **Sense**: Defines or differentiates a distinct semantic concept.
  - **Groups rows?** **Yes**. Senses with differing translations or semantic contexts form separate rows on flashcards.
  - **WSD reads it?** **Yes**. Scored via gloss embeddings, translation alignment, exact gloss matches, and sense priors.
  - **Card displays it?** **Yes**. Rendered as the primary row text (`translation`) and semantic disambiguation cue (`⟨context⟩`).

- **Label**: Annotates a sense with grammatical, syntactic, regional, register, or domain constraints.
  - **Groups rows?** **NO**. Senses that differ *only* by labels must never be split into confusing twin rows.
  - **WSD reads it?** **Yes**, but strictly as symbolic feature gates or specialist scorers (e.g. `ConstructionGate`, reflexive tagger, register prior), never as gloss embeddings.
  - **Card displays it?** **Selective**. Rendered only as distinct secondary pills/badges, or suppressed when redundant or non-contrastive. Labels **never** occupy the primary grey `⟨context⟩` slot.

### Special Case: Syntactic Companions
When two senses share the same translation (e.g. *falar* "to talk"), a governed syntactic argument requirement (e.g., `+ com` "to speak with/to" vs. `+ de` "to talk about") functions as the **differentiating sense cue**. In this case, the companion is exposed as the disambiguating context cue (`+ com`), allowing both WSD and card display to agree on the distinction.

---

## 3. Metadata Field & Feature Family Specification

| Field / Feature Family | Provider Source | Category | Groups Rows? | WSD Reads It? | Card Displays It? | Behavior & Normalization Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`translation` (`display_gloss`)** | SpanishDict `translation`<br>Wiktionary `glosses[0]` | **Sense** | **Yes** | Yes (Primary gloss embedding & exact match) | Yes (Main text) | Strips dictionary meta-descriptions (e.g. skips `Second-person singular possessive determiner.` for `your`). Projections remove bracketed cross-references. |
| **`context` (Semantic)** | SpanishDict `context`<br>Wiktionary semantic parenthetical / sub-gloss | **Sense** | **Yes** | Yes (Context embed bonus + definition prior) | Yes (Grey `⟨context⟩` cue) | Disambiguating semantic domain or usage cue (e.g. `⟨place⟩`, `⟨time⟩`, `⟨used in double negatives⟩`). Wiktionary strips all pure labels (transitive, register, region). |
| **`companion`** | SpanishDict context / examples<br>Wiktionary `info_templates` (`+obj`), `[with ...]` | **Sense / Cue** | **Yes** (when disambiguating shared translation) | Yes (`GovernedPrepositionFeature`, `CompanionFeature`) | Yes (`+ <prep>` in context slot or pill) | Extracts argument prepositions (e.g. `+ com`, `+ de`, `+ a`). Differentiates otherwise identical verb rows. |
| **`construction`** | SpanishDict `part_of_speech`<br>Wiktionary `(transitive)`, `(intransitive)`, tags | **Label** | **No** | Yes (`ConstructionGate`, transitive/intransitive gating) | No (Suppressed from context line; optional badge if contrastive) | Stripped from Wiktionary `_context`. Mapped to `SpecialistFeature("construction", tag)`. Never creates duplicate card rows. |
| **`register`** | SpanishDict `register`<br>Wiktionary `qualifier`, tags (`colloquial`, `slang`, `archaic`) | **Label** | **No** | Yes (`RegisterFeature` prior) | Yes (Badge/chip on sense back if contrastive) | Stripped from Wiktionary `_context`. Mapped to `SpecialistFeature("register", tag)`. |
| **`regions`** | SpanishDict `regions`<br>Wiktionary policy `region_tags` in tags/gloss | **Label** | **No** | Yes (Dialect/region prior) | Yes (Regional flag/chip) | Stored in `provider_metadata["regions"]`. Normalized per language policy (e.g. `Brazil`, `Portugal`). Never groups rows. |
| **`domain` / `topics`** | SpanishDict category<br>Wiktionary `topics` (`finance`, `business`) | **Label** | **No** | Yes (`DomainScorer`) | No / Badge (Only if distinguishing sibling rows) | Stripped from Wiktionary `_context`. Stored in `provider_metadata["topics"]`. Eliminates `topic_chip_noise`. |
| **`grammar`** | SpanishDict inflections<br>Wiktionary `form_of`, `_surface_grammar` | **Label** | **No** | Yes (`KeepSelfReadingPos`, `SurfaceGrammarFeature`) | Card front/back info (Not a sense row) | Surface-level grammatical facts (person, number, tense, gender). Attached to analysis, not leaf. |
| **`functional`** | SpanishDict POS (`PRON`, `DET`, `CONJ`)<br>Wiktionary POS & syntactic tags | **Label** | **No** | Yes (`PronounFunctionGate`, `SpanishV5CandidatePolicy`) | Gating (Filters candidate senses) | Distinguishes syntactic roles (subject vs object vs prepositional pronoun). |

---

## 4. Implementation Details

1. **Kaikki Adapter (`src/fluency/sense_menu/kaikki.py`)**:
   - `_JUNK_GLOSS_PATTERN`: Skips structural POS definitions (e.g. `Second-person singular possessive determiner.`), projecting clean translation glosses (`your`).
   - `_context()`:
     - Prioritizes companion requirements (`info_templates` `+obj` and `[with ...]` brackets) to emit `+ <prep>`.
     - Parses leading parentheticals with `leading_parenthetical` and `split_top_level_commas`, stripping composite construction, register, regional, and grammatical label tokens.
     - Preserves true semantic parentheticals (e.g. `(said of people (especially children))`) and clean explanatory sub-glosses (e.g. `used in double negatives`).
     - Suppresses raw topic lists and register qualifiers from leaking into `context`.
   - `build_analyses()`: Deduplicates identical raw senses within `(headword, pos)` sharing `(translation, definition, specialist_features)` to eliminate redundant split rows.

2. **WSD Alignment (`src/fluency/wsd/`)**:
   - `ConstructionGate` and `ExactTextGlossScorer` operate over canonical `(translation, definition)` signatures.
   - Senses distinguished by companion prepositions (`+ com` vs `+ de`) receive matching companion feature bonuses and align directly with user-facing card rows.

---

## 5. Verification & Safety Guarantees

- **Test Suite**: 636/636 tests pass across `tests/features/`, `tests/sense_menu/`, and `tests/wsd/`.
- **Reflexive Gold Evaluation**:
  - `eval_es.py held`: 1.0000 decisive accuracy (0 errors).
  - `eval_pt.py dev`: 1.0000 decisive accuracy (0 errors).
- **Freezes**: No card releases activated. No UI files in `app/**` modified.
