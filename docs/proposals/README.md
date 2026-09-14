# WSD Proposals & Iteration History

This directory documents the evolution of Word Sense Disambiguation (WSD) in Fluency-Next. All historical proposals and status documents are preserved in place to maintain commit lineage, test references, and data provenance.

For the definitive technical specification of the current engine, see [`docs/WSD_ARCHITECTURE.md`](../WSD_ARCHITECTURE.md).

---

## Evolution & Status Matrix

| Version / Document | Status | Key Innovations | Lessons & Dead Ends Exposed |
|---|---|---|---|
| **[Proposal 0001](0001-wsd-port-architecture.md)**<br>`0001-wsd-port-architecture.md` | **Historical Foundation** | • Closed-menu candidate scoring.<br>• Immutable run artifacts (Stage 04).<br>• Surface-form card identity.<br>• Disallowed mutable method merges. | • Silently falling down to weaker variants when assets are missing is dangerous: component profiles must fail-closed. |
| **v6**<br>`spanish-wsd-v6-implementation-map.md`<br>`spanish-wsd-v6-status.md` | **Structural Frame** | • Reorganized 7 stages into 3 roles: `CONSTRAIN`, `RANK`, `COMMIT`.<br>• Multi-word expressions (MWEs) compete as regular candidates attached to surface cards (no hard vetoes).<br>• Fixed the silent `AUX` tagger bridge bug. | • Dropped BETO prototypes (needed 13+ examples; deck median was 4).<br>• Dropped confidence calibrator (trained on uniform dictionary gold).<br>• Rejection curves show leaf accuracy is flat: do not reject to buy leaf accuracy. |
| **v7**<br>`spanish-wsd-v7-status.md` | **Core Contract** | • Separated 4 independent decisions: Candidate Universe, Forced Selection, Emitted Level, Release Projection.<br>• Persisted occurrence spans across elisions (`pa' -> para`).<br>• Portuguese v7 baseline proving POS bridge is mandatory for contractions (`do, da, ao`). | • Menu prior (`0.02 * 0.5^rank`) strongly favored early leaves on Rosalía: raw whole-sentence cosine has weak separating power for close synonyms.<br>• Rediscovering spans in raw text breaks elisions. |
| **v8**<br>`spanish-wsd-v8-status.md` | **Grounding & Specialist** | • Wired reverse-conjugation lookup (`conjugation_reverse.json`), recovering 166 `no_menu` cards without network.<br>• Pinned SimAlign English word alignment as a high-precision sparse corrector (95% precision). | • Hard leaf gates for companion/grammar features broke more cards than they fixed (5 better, 9 worse in spot-checks); kept as audit evidence only. |
| **v9**<br>`spanish-wsd-v9-status.md`<br>`research/wsd_v9/` | **Falsification & Agreement** | • Display support determined by agreement between dictionary order and raw embedding cosine (`leaf`, `glosskey`, `tuple`, `unresolved`).<br>• `gemini_recommendation` records model disagreement without calling external APIs.<br>• Zero-spend 2,000-card production runs. | • Substitution WSI and dictionary-example pair scorers overfit to dictionary style and failed on subtitles.<br>• Wiktionary lacks example sentences on >37% of Portuguese senses, blocking example-based WSI from parity. |
| **v10**<br>`config/wsd/models/*-v10-1.json` | **Active Production Baseline** | • Provider-neutral pedagogy publication guards across Spanish (`es-v10-1`), Portuguese (`pt-v10-1`), and Czech (`cs-v10-1`).<br>• Single-leaf menus still pass through publication guards.<br>• Languages without reliable token taggers (e.g. Czech) use prior + gloss alone without artificial filters. | • Never invent an unvalidated POS filter just because a tagger is missing: subtraction without evidence erases correct senses. |

---

## Key References
- Active model configurations: [`config/wsd/models/`](../../config/wsd/models/)
- Empirical dead ends log: [`docs/reference/wsd_dead_ends.md`](../reference/wsd_dead_ends.md)
- Open research threads: [`docs/reference/wsd_open_threads.md`](../reference/wsd_open_threads.md)
- Research probe findings: [`research/wsd_v9/FINDINGS.md`](../../research/wsd_v9/FINDINGS.md)
