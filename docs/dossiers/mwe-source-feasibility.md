# MWE Source Feasibility Dossier: Portuguese & Spanish

**Status:** Completed Feasibility Audit  
**Date:** 2026-10-03  
**Target Languages:** Portuguese (`pt` - primary), Spanish (`es` - secondary)  
**Deliverable:** Feasibility assessment of external multiword expression (MWE) sources vs. Kaikki Wiktionary for WSD disambiguation menus and learner card curation.

---

## 1. Executive Summary & Core Finding

### The Core Finding
**Kaikki Wiktionary is genuinely our only viable, structured, legally unencumbered, and parseable source for non-compositional MWEs in Portuguese (and secondary Spanish).**

Crucially, **the perceived gap in Portuguese MWE coverage was NOT caused by a limitation of Wiktionary itself**, but rather by a configuration choice in our ingestion filter:
- In `src/fluency/mwe/builder.py`, `build_wiktionary_inventory` previously restricted multiword headwords to:
  ```python
  pos in {"phrase", "prep_phrase", "adv", "conj", "prep", "intj", "noun", "adj", "particle"}
  ```
- **`pos == "verb"` was excluded from multiword ingestion!**
- Because of this POS filter omission, **869 Portuguese multiword verbs** present in our pinned Kaikki dump (`kaikki.org-dictionary-Portuguese.jsonl`) were skipped during the candidate harvest.
- This directly explains why benchmark verbal idioms and periphrases such as:
  - *ter a ver* ("to have to do with; to be related to")
  - *dar um jeito* ("to find a way of; to solve or eliminate")
  - *ter que* / *ter de* ("to have to")
  - *dar conta* ("to give notice; to realize; to be able to handle")
  - *valer a pena* ("to be worthwhile")
  - *abrir mão* ("to give up; to renounce")
  - *bater papo* ("to chat; to talk")
  - *dar bronca* ("to scold; to reprove")
  - *passar mal* ("to feel sick; to feel unwell")
  - *tomar conta* ("to mind; to look after; to take care")
  - *prestar atenção* ("to pay attention")
  were completely absent from `Fluency-Workspace/raw/mwe/mwe-pt-10k-sieve/mwe_merged.json` (which had only 8 verbal expressions, compared to 2,149 multiword verbs in Spanish).

All of these benchmark idioms exist right now with high-quality English glosses, sub-senses, and usage tags (`colloquial`, `idiomatic`) in our local Kaikki Portuguese dump.

No external paid API or legally fraught scraping pipeline is necessary. Fixing the candidate ingestion set to admit multiword verbal headwords instantly unlocks Portuguese parity.

---

## 2. External Candidate Source Audit

We systematically investigated the four candidate external sources identified for Portuguese:

| Source | Access / Format | License | Idiom vs. Collocation Distinction | Viability Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **OpenWN-PT** (Open WordNet-PT) | RDF / WordNet XML / Python NLTK / OMW | CC-BY 4.0 / CC-BY-SA 3.0 | **Poor**. MWE coverage is heavily skewed toward nominal multiword entities and synset mappings projected from Princeton WordNet. High-frequency verbal idioms and conversational pragmatic formulas are sparse and difficult to disambiguate from compositional compounds. Glosses are often circular or direct translations of English WordNet synsets. | **Not Recommended**. High noise, complex alignment, low idiomatic precision for language learners. |
| **PARSEME PT** (Shared Task v1.1 / 1.2) | `.cupt` (CoNLL-U format with MWE column) on GitLab | CC-BY / Open Academic | **High (Linguistic)**. High precision for verbal MWEs (LVCs, ID - idioms, IRV - reflexive verbs, VPC - particle verbs). However, it is an **annotated corpus sample**, not a dictionary inventory. It contains token-level spans across ~20,000 sentences without clean English learner glosses or dictionary definitions. | **Not Suitable for WSD Menus**. Excellent for training token extractors, but unusable as a plug-and-play sense menu overlay because it lacks bilingual translations/glosses. |
| **CETEMPúblico Idioms** (Linguateca AC/DC) | Web search interface / concordances / research papers | Academic research use only. Monolingual Portuguese newspaper corpus (Público, 180M tokens). | **Mixed**. Journalistic corpus containing empirical occurrences of idioms (e.g. *bater na tecla*), but exists as raw occurrences and academic research extracts, not an extractable, structured bilingual dictionary with English translations. | **Not Viable**. No machine-readable bilingual glosses; requires heavy NLP post-processing and manual translation. |
| **Priberam / Infopédia** | Commercial proprietary web dictionaries (Porto Editora / Priberam Informática) | **Strictly Proprietary & Commercial**. Terms of Service forbid scraping and automated extraction. Commercial NLP APIs require enterprise contracts. | **High (Lexicographical)**. High-quality human lexicography, but legally blocked and commercially gated. Direct extraction violates ToS and risks legal liability. | **Disqualified**. Licensing and ToS barriers prohibit automated scraping or ingestion. |

---

## 3. Comparative Source Breakdown

### 3.1 OpenWN-PT (Open Multilingual WordNet)
- **Structure**: Graph-based synset network linked to Princeton WordNet 3.0.
- **Deficiencies for WSD Menus**:
  1. *Projection artifacts*: Because synsets were initially projected from English WordNet, many Portuguese MWEs are artificial multiword loan translations rather than natural Brazilian/European Portuguese idioms.
  2. *Glosses*: Glosses in OpenWN-PT are either missing or in formal Portuguese, requiring a secondary translation hop to create English menus for learners.
  3. *Coverage gap*: Conversational spoken locutions (*né*, *tipo assim*, *e aí*, *dar um jeito*) are systematically underrepresented in WordNet taxonomies.

### 3.2 PARSEME Portuguese VMWE Dataset
- **Structure**: CUPT files annotating Verbal Multiword Expressions (VMWEs) into categories: `VID` (Verbal Idiom), `LVC.full` / `LVC.cause` (Light Verb Construction), `IRV` (Inherently Reflexive Verb), `MVC` (Multiword Verb Construction).
- **Strengths**: Highly rigorous linguistic categorization distinguishing idioms from compositional collocations.
- **Fatal Obstacle**: PARSEME is a *corpus annotation benchmark*, not a *lexical resource*. It provides token offsets in sentence trees, not bilingual learner dictionary entries. To use PARSEME, one would have to extract lemmas, cluster contexts, and synthesize English glosses from scratch.

### 3.3 Priberam & Infopédia
- Both represent the gold standard of Portuguese lexicography (Priberam for modern general usage, Infopédia for comprehensive European Portuguese).
- Both strictly forbid automated crawling, reverse engineering of internal APIs, and bulk data extraction under their Terms of Service. Enterprise API licensing is commercial and requires contract negotiation, violating the project constraint of zero paid API calls and unencumbered open architectures.

---

## 4. Kaikki Wiktionary: The Undiscovered Goldmine

### 4.1 What Wiktionary Actually Contains for Portuguese
An audit of our pinned snapshot `Fluency-Workspace/raw/wiktionary/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl` revealed **13,280 multiword headwords**:

```
Multiword POS Distribution in Kaikki Portuguese:
  noun:        7,451
  name:        2,686
  verb:          869
  adv:           645
  adj:           464
  phrase:        370
  proverb:       287
  intj:          217
  prep:           86
  num:            76
  pron:           51
  conj:           49
  prep_phrase:    21
  det / other:     7
```

Non-noun multiword headwords total **2,722 expressions**.

### 4.2 Proof of Extracted Idioms in Kaikki
Direct extraction from `kaikki.org-dictionary-Portuguese.jsonl` proves that English Wiktionary contains high-quality, non-compositional, learner-ready entries for all target Portuguese expressions:

| Target Expression | POS | Kaikki Wiktionary Gloss | Wiktionary Sense Tags |
| :--- | :--- | :--- | :--- |
| **ter a ver** | `verb` | "to have (something) to do with; to be related to or relevant to" | `idiomatic` |
| **dar um jeito** | `verb` | "to find a way of"; "to solve or eliminate" | `idiomatic`, `colloquial` |
| **ter que** | `verb` | "to have to (indicates obligation)" | `auxiliary` |
| **ter de** | `verb` | "to have to (indicates obligation)" | `auxiliary` |
| **dar conta** | `verb` | "to give (someone) notice (of), to give an account"; "to realize, to notice"; "to be sufficient or adequate for, to be able to handle" | `idiomatic` |
| **valer a pena** | `verb` | "to be worthwhile" | `idiomatic` |
| **abrir mão** | `verb` | "to give up; to renounce" | `idiomatic` |
| **bater papo** | `verb` | "to chat; to talk; to engage in a conversation" | `colloquial`, `idiomatic` |
| **dar bronca** | `verb` | "to scold, to reprove" | `colloquial` |
| **passar mal** | `verb` | "to feel sick, to get sick, to feel unwell" | `idiomatic` |
| **tomar conta** | `verb` | "to mind; to look after; to take care"; "to overwhelm" | `idiomatic` |
| **prestar atenção** | `verb` | "to pay attention (to be attentive)" | `idiomatic` |
| **à toa** | `adj` / `adv` | "idle (not doing anything important)"; "despicable, without importance" | `idiomatic` |
| **de repente** | `adv` | "suddenly; unexpectedly" | `idiomatic` |
| **por favor** | `phrase` / `adv`| "please" | `formulaic`, `polite` |

### 4.3 Why Were They Missing from `mwe-pt-10k-sieve`?
In `src/fluency/mwe/builder.py` (lines 139-140):
```python
# Multiword headwords
if " " in word and pos in {"phrase", "prep_phrase", "adv", "conj", "prep", "intj", "noun", "adj", "particle"}:
    tokens = word.split()
    ...
```
Because `"verb"` was omitted from this membership set, the builder discarded every multiword verb entry in Kaikki! The only verbal entries that made it into the snapshot were 8 entries tagged with secondary or ambiguous POS categories (e.g., `['phrase', 'verb']` or `['verb', 'intj']` like *cala a boca* and *sei lá*).

---

## 5. Spanish Comparison & Lessons Learned

In Spanish, our initial candidate pool was larger (10,419 raw candidates, yielding 1,544 kept non-compositional MWEs in `mwe-es-10k-sieve`):
- **SpanishDict contribution**: SpanishDict provided 8,280 phrasebook collocations.
- **However**, our non-decomposition policy (`src/fluency/mwe/policy.py`, Rule 1) explicitly enacted:
  > *"Candidate source rule: Multiword expressions must appear in Wiktionary as multiword entries; pure SpanishDict phrasebook collocations without Wiktionary backing are excluded as compositional noise."*
- Out of 8,280 pure SpanishDict phrases, **all 8,280 were excluded as compositional collocations** unless attested in Wiktionary.
- Only the 2,139 expressions with Wiktionary backing (1,697 pure Wiktionary + 442 SpanishDict+Wiktionary overlaps) survived the non-compositional filter.
- Furthermore, Spanish Kaikki contained **2,149 multiword verb headwords** (such as *tener en cuenta*, *echar de menos*, *dar a luz*, *hacer caso*), which gave Spanish a rich verbal idiom inventory.

The Spanish experience demonstrated that external phrasebook scraping yielded vast amounts of compositional noise (*tengo una pregunta*, *aquí estamos*), and **Wiktionary was the sole reliable arbiter of non-compositionality and lexicalization**.

---

## 6. Clear Recommendation & Action Plan

### Recommendation: Sole Reliance on Kaikki Wiktionary
**Do NOT integrate an external source.** Commit fully to Kaikki Wiktionary for Portuguese MWE disambiguation and WSD menus.

### Why this is the optimal engineering decision:
1. **Zero Legal or Financial Risk**: CC-BY-SA 3.0 / Wikimedia license; zero API subscription costs; reproducible offline runs.
2. **True Non-Compositionality**: English Wiktionary editors only create multiword headword pages when a phrase is lexicalized, non-compositional, or culturally established. It naturally filters out arbitrary collocations.
3. **Structured Senses & English Glosses**: Unlike OpenWN-PT or PARSEME, Kaikki entries provide clear, concise English translations ready for learner WSD menus.
4. **Immediate Coverage Expansion**: Ingesting the 869 existing Portuguese multiword verbs from Kaikki will immediately expand the Portuguese kept MWE inventory from **937** to **~1,400+ non-compositional idioms**, matching Spanish parity.

### Next Steps for Implementation (in future harvest/build chat):
1. **Update `src/fluency/mwe/builder.py`**:
   Add `"verb"` to the allowed POS set for multiword headwords:
   ```python
   pos in {"verb", "phrase", "prep_phrase", "adv", "conj", "prep", "intj", "noun", "adj", "particle"}
   ```
2. **Re-run candidate harvest for Portuguese**:
   Extract all ~2,720 non-noun multiword expressions from `enwiktionary-2026-08-20`.
3. **Integrate with Merge Lemma Policy**:
   Feed the resulting verbal idioms into `config/mwe/pt-curated.json` as List (b) Lemma constructions (e.g. *ter a ver*, *dar um jeito*, *abrir mão*, *dar conta* as senses on the verb lemma cards) or List (a) frozen expressions where applicable.
