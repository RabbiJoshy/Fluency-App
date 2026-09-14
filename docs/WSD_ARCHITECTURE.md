# WSD Architecture & Engine Reference

This document is the authoritative engineering specification for Word Sense Disambiguation (WSD) in Fluency-Next. It codifies the active **v10** engine architecture, core product invariants, and execution boundaries.

---

## 1. Core Architectural Invariants

These invariants constrain all WSD passes and outlive specific model configurations:

### Invariant 1: Surface-Form Card Identity
A flashcard's identity is strictly the observed surface form:
$$\text{card\_id} = f(\text{language}, \text{surface\_key})$$
Lemmas, roots, and parts of speech are lookup metadata, never card identity. Inflected forms, clitics, and contractions (`dame`, `deixa-me`, `pa'`) retain their own progress cards. A learner's review history must never be broken by dictionary reorganization or lemma re-routing.

### Invariant 2: The 4-Decision Seam
Every disambiguation run keeps four independent decisions separate:
1. **Candidate Universe:** `provider_only` (default) vs. `mwe_augmented` (counterfactual, scored in the same pass).
2. **Forced Selection:** The classifier's single best leaf choice (`forced_selection`), retained for all occurrences.
3. **Emitted Specificity Level:** The level of detail safe to show on the card (`leaf`, `glosskey`, `tuple`, or `unresolved`).
4. **Release View Projection:** Decided at release build time (`--wsd-selection-projection` and `--wsd-publication-projection`). Switching projections requires zero model re-runs.

### Invariant 3: Sense-to-Sense Comparison (No Sense Bags)
Semantic comparisons hold between **individual senses**, never between whole words or dictionary "sense bags." Lumping multiple definitions into a single text block dilutes cosine vectors into general topical noise. The single highest-scoring 1-on-1 sense pair carries the decision.

### Invariant 4: Competing, Non-Vetoing MWEs
Multi-word expressions (e.g. `de nuevo`, `a menos que`) compete as regular candidates attached to the cards of their component surface forms. They never act as hard vetoes, preventing false positives from erasing valid literal meanings. Only phrases with corpus evidence (`corpus_freq > 0`) compete; zero-frequency dictionary idioms are excluded from candidate pools.

### Invariant 5: Diamond Pipeline & Resumable Caches
The pipeline is a diamond, not a linear chain:
```
01 inventory ──┬──> 02 sense_menu ──┐
               └──> 03 harvest    ──┴──> 04 wsd ────> 05 selection ────> 06 release
```
`sense_menu` and `harvest` are independent siblings reading only the surface inventory. Exact-text embedding caches (`exact-text-gemini-embedding-001.npz`) are stored per-language, outliving individual runs to ensure amortized zero-cost regeneration.

---

## 2. The Three Execution Roles

The legacy 7-stage chain is organized into three distinct functional roles:

```
[Harvested Sentence + Closed Menu Candidates]
                      │
                      ▼
               1. CONSTRAIN
    (Prune impossible candidates via POS & grammar)
                      │
                      ▼
                  2. RANK
   (Score survivors: Gloss Cosine + Dictionary Prior)
                      │
                      ▼
                  3. COMMIT
   (Compare choices: Decide specificity level for display)
```

### Role 1: CONSTRAIN
* **Purpose:** Remove candidates that are structurally or grammatically impossible before scoring.
* **Mechanism:**
  - Map tagger Universal Dependencies tags to dictionary categories via language POS bridges (e.g. mapping `AUX` $\to$ `VERB`).
  - Apply vetted morphological rules (e.g. Spanish `se` clitic gate).
* **Safety Fallback:** If a constraint would eliminate all candidates (e.g. tagger error or missing dictionary category), it falls back to the complete candidate menu. Absence of evidence never deletes a word's senses.

### Role 2: RANK
* **Purpose:** Score surviving candidates in authentic sentence context.
* **Mechanism:**
  - **Gloss Embeddings:** Dense cosine similarity between the full sentence and candidate English glosses.
  - **Dictionary Prior:** A small decaying prior based on dictionary entry order ($+0.02 \times 0.5^{\text{rank}}$). Because real conversation heavily favors dominant senses (>80% on sense 1), this prior stabilizes decisions without overwhelming sentence context.

### Role 3: COMMIT
* **Purpose:** Decide *how specific* an answer to display on the card, turning uncertainty into a broader, safer card rather than an incorrect guess.
* **Mechanism (Rank Agreement):**
  - Compare the dictionary-order winner against the raw gloss-cosine winner:
    - Same exact leaf $\to$ `leaf`
    - Different leaves, identical English gloss $\to$ `glosskey`
    - Different glosses, same headword + POS $\to$ `tuple`
    - Conflicting headword/POS $\to$ `unresolved`
* **Card Display:** If specificity falls below `leaf`, the card displays the broader category or glosskey. The exact forced leaf is preserved in the underlying assignment data for future audit.

---

## 3. Specialist Features & Diagnostic Boundary

Normalized feature families (`grammar`, `companion`, `construction`, `domain`, `register`) are extracted by dictionary adapters (SpanishDict and Kaikki/Wiktionary).

* **Status:** **Evidence-Only.**
* **Boundary:** Features are stored in the assignment record as inspectable diagnostic evidence. Hard filtering gates on these features remain disabled because empirical spot-checks revealed that hard leaf gates broke more cards than they fixed.
* **Requirement for Activation:** Any future specialist gate must demonstrate positive net deltas on a cross-provider, frequency-stratified benchmark before being promoted.

---

## 4. Runtime Cost Boundary & Escalation Policy

* **Current Baseline:** **Strictly Zero Runtime API Cost.** All embedding vectors are reused from local resumable caches. Zero calls are made to external LLM endpoints during production deck generation.
* **Model Disagreement Diagnostic:** When candidate agreement falls below `leaf`, the engine records `gemini_recommendation.recommended = true`, but sets `gemini_called = false`.
* **Future Escalation Hook:** A frontier LLM escalation hook is preserved for difficult, low-confidence cases where candidate agreement fails and sentence redrawing is impossible (e.g. fixed user corpora in lyrics mode), to be enabled once harvesting and heuristics fully stabilize.

---

## 5. Model Profiles & Configuration Pointers

Active production profiles implementing the v10 specification:
- **Spanish Speech:** [`config/wsd/models/es-v10-1.json`](../config/wsd/models/es-v10-1.json)
- **Portuguese Speech:** [`config/wsd/models/pt-v10-1.json`](../config/wsd/models/pt-v10-1.json)
- **Czech Speech:** [`config/wsd/models/cs-v10-1.json`](../config/wsd/models/cs-v10-1.json)

Execution code:
- Main CLI executor: [`src/fluency/speech/wsd_execute.py`](../src/fluency/speech/wsd_execute.py)
- Commit and specificity policy: [`src/fluency/wsd/commit.py`](../src/fluency/wsd/commit.py)
- Projections and release contracts: [`src/fluency/wsd/projection.py`](../src/fluency/wsd/projection.py)
