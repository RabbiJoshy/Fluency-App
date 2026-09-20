# Decision 0022 — 10k Pre-WSD Supply, Sampling Taper, and Clitic De-Phrasing

## Decision

1. **WSD Candidate Cap & Non-Linear Tapering**:
   - **Monosemous cards** (`senses == 1`): Allocated **25 candidates by default** at **$0.00 compute cost** via the `sole_leaf` bypass in WSD execution (single-leaf sense menus skip Gemini embedding calls).
   - **Polysemous cards** (`senses > 1`): Sample cap combines rank boost and polysemy boost with a **logarithmic / non-linear taper**:
     $$\text{cap}(\text{rank}, \text{senses}) = \text{clamp}\Big(10,\, 40,\, \text{round}\big(10 + \text{rank\_boost}(\text{rank}) + \text{polysemy\_boost}(\text{senses})\big)\Big)$$
     - **Front-end prioritization**: Ranks 1–3,000 receive generous candidate caps (up to 40) where nuance, usage dispersion, and polysemy matter most to learners.
     - **Non-linear tail taper**: Rank boost decays logarithmically/non-linearly so tail vocabulary (ranks 5,000–10,000) tapers down lean (~10–14 candidates), where competing polysemy is minimal and learners are advanced.
   - **Storage vs. Execution Boundary**: `materialise_surfaces.py` records **all** eligible candidates in `prewsd/pairs.json` in prioritized order without truncation; the dynamic candidate cap is applied downstream during WSD sampling/execution (in KILN).

2. **Candidate Ordering & Admissibility Philosophy**:
   - Admissibility filter operates strictly as negative gating (<1% rejection on corrupted alignments or extreme length anomalies).
   - Alignment banding (0.05 bins) combined with difficulty (frequency burden + grammar penalty) provides **soft ordering pressure**, not a hard cutoff, preventing short/dominant sentences from choking secondary senses.

3. **SpanishDict Single-Word Clitic De-Phrasing**:
   - Intercept single-token enclitic verbs (e.g. *déjalo*, *hazlo*, *dime*, *cállate*, *ayúdame*) scraped by SpanishDict with POS `"PHRASE"`.
   - Map them to root verb lemmas (*dejar*, *hacer*, *decir*, etc.) and POS `["VERB"]` with provenance `spanishdict clitic de-phrased`, preserving original SpanishDict headwords as alternates.
   - Append durable observation events to `raw/surfaces/es/events.jsonl` and place `spanishdict-clitic-dephrased` at top authority in `AUTHORITY["es"]`.

4. **10k Freeze & Supply-Only Contract (SCAR Defense)**:
   - Enforce `--supply-only` flag on `materialise_surfaces.py` for run-specific materialisation, guaranteeing durable `ledger.json` files are never overwritten or thinned.
   - Added `--dry-run` simulation mode to `materialise_surfaces.py`.
   - Registered named 10k pools: `es-10k-speech`, `pt-10k-speech`, `cs-10k-speech`.
   - Frozen pre-WSD artifact sets stamped with `prewsd-pairs/v2` schema (occurrence POS support).

---

## Context & Rationale

### 1. Why 25 Candidates for Monosemous Cards is Free
In `fluency.speech.wsd_execute`, any card whose sense menu has only one leaf triggers the `sole_leaf` bypass:
```python
if len(leaves) == 1:
    # All candidates trivially assign to the only sense; no embedding or model call
    return trivial_assignment(candidates, leaves[0])
```
Because no vector similarity scoring or model API calls occur, allocating 25 candidates instead of 10 costs zero compute dollars while providing richer sentence variety for downstream flashcard selection.

### 2. Why Logarithmic / Non-Linear Tapering
A linear interpolation between rank 1 and rank 10,000 distributes candidate allowances too evenly across the deck. 
- In the **head** (ranks 1–3,000), words like *hacer*, *quedar*, *pasar*, or *dar* possess dozens of colloquial and idiomatic nuances that require wide candidate coverage (30–40 sentences) to sample secondary senses reliably.
- In the **tail** (ranks 5,000–10,000), words are predominantly domain-specific nouns and monosemous or low-polysemy forms (*descongelar*, *hipótesis*). Advanced learners at rank 8,000 do not benefit from 30 redundant example sentences; 10–14 high-quality candidates suffice.
- A logarithmic curve steepens the falloff after rank 3,000, concentrating token budgets and compute spend where semantic ambiguity is highest.

### 3. Why Clitic De-Phrasing is Essential
SpanishDict's dictionary crawler treated pronominal imperatives (*déjalo*, *hazlo*) and clitic constructions as autonomous dictionary headwords tagged as `"PHRASE"`.
Because SpanishDict headword cache had primary authority in `AUTHORITY["es"]`, these words:
1. Had no Part of Speech (`pos: []`),
2. Used their own clitic string as their lemma (`lemma: "déjalo"`),
3. Failed to find dictionary conjugation menus and could not merge cleanly with their parent verb.

By resolving them to the true base lemma (*dejar*, *hacer*) and tagging POS `["VERB"]` with full provenance, clitics participate in standard verbal sense disambiguation.

---

## Polysemy & Embedding Inventory Across 10k Decks

Audited sense counts and existing embedding cache reuse across all 10,000 cards:

| Language | Base Senses | Kept MWEs | Total Senses | Senses / Card | Existing Cache Reuse |
|---|---|---|---|---|---|
| **Spanish (`es`)** | 96,979 | 1,544 | 98,523 | 9.79 | ~55% |
| **Portuguese (`pt`)** | 48,632 | 937 | 49,569 | 4.94 | ~45% |
| **Czech (`cs`)** | 20,094 | 171 | 20,265 | 2.04 | ~40% |

---

## Artifacts & Deliverables

- **CLI Support**:
  - `src/fluency/cli/__main__.py` enables direct execution via `python3 -m fluency.cli`.
  - `scripts/materialise_surfaces.py` supports `--dry-run` and `--supply-only`.
- **Clitic Resolver**:
  - `scripts/resolve_single_word_clitics.py` (162 durable events appended to `es/events.jsonl`).
- **Registered Named Pools**:
  - `es-10k-speech` (`20260914T223348Z-c35194bc`, 365,813 sentences)
  - `pt-10k-speech` (`20260914T222723Z-e43a0469`, 375,892 sentences)
  - `cs-10k-speech` (`20260914T223828Z-ad405a28`, 369,666 sentences)
- **Frozen Pre-WSD Artifact Sets (`prewsd-pairs/v2`)**:
  - `raw/surfaces/es/prewsd/20260914T223348Z-c35194bc` (364,387 sentences, 10,133 surfaces)
  - `raw/surfaces/pt/prewsd/20260914T222723Z-e43a0469` (373,659 sentences, 10,100 surfaces)
  - `raw/surfaces/cs/prewsd/20260914T223828Z-ad405a28` (367,139 sentences, 10,122 surfaces)
- **Roadmap Sync**:
  - `CHAT_ROADMAP.md` and `Fluency-Workspace/raw/surfaces/DECK_CHAT_ROADMAP.md` updated with QUARRY marked Done.
