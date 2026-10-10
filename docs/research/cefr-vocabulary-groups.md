# CEFR calibration after merged-form estimation

Audit date: 9 October 2026. No numerical CEFR thresholds are implemented.

## What the estimator now measures

One unit is an eligible merged group, an independent surface that cannot merge, or one reading of a surface that the existing study-card rules split. It is **not a conventional lemma or word-family count**. A group can span several inflections; ambiguous forms and expressions may remain independent; split readings count separately. Multiple translations under one headword do not automatically create multiple items.

Groups are ordered by the sum of their permitted members' source-list frequencies. Each prompt uses the most frequent eligible form. Split prompts show a target-language example associated with that reading, reveal only its meanings, and divide surface frequency between readings according to the published assigned sense-frequency evidence. Missing split examples or missing allocation evidence exclude that reading from the sampling pool. No fallback assigns full surface frequency to both readings.

The estimator keeps the earlier exclusions: untranslated entries, duplicate/noise/interjection/proper-name/English flags, grammar particles, main POS outside NOUN/VERB/ADJ/ADV, and legacy cognate scores of at least 0.83. The single-occurrence preference still applies when a source supplies corpus counts. These exclusions mean this is knowledge of a filtered shipped pool, not the learner's total vocabulary.

Thirty adaptive self-report questions estimate recognised groups within that pool. The displayed range is the existing approximate band-based interval, not a calibrated CEFR confidence interval. The estimator does not test pronunciation, grammar, listening, speaking or complete knowledge of every meaning within an unsplit item.

Placement is a separate quantity: band recognition rates are expanded onto member surfaces (split readings contribute fractions), then converted into the historical Speech source-rank boundary. Existing saved ranks remain ranks. Group counts never become persisted placement ranks directly.

## Actual shipped pools

Measured using the same runtime merge, split, filtering, loading and example-selection helpers; single-occurrence hiding disabled. Source files came from the configured releases in the local Fluency-Workspace. Reproduce with `node scripts/audit_estimation_pools.cjs /path/to/Fluency-Workspace`. Full release paths and measurements are in [the audit snapshot](estimation-pools-2026-10-09.json).

| Language | Released surfaces | Eligible contributing surfaces | Estimated groups | Mergeable groups | Independent surfaces | Split readings |
|---|---:|---:|---:|---:|---:|---:|
| Spanish | 10,000 | 9,009 | 7,585 | 3,958 | 994 | 2,633 |
| Portuguese | 10,000 | 9,570 | 6,007 | 4,723 | 592 | 692 |
| Czech | 10,000 | 9,040 | 4,129 | 3,566 | 426 | 137 |
| Finnish | 2,000 | 1,657 | 856 | 736 | 59 | 61 |
| French | 200 | 131 | 131 | 0 | 131 | 0 |

Spanish uses EsPal subtitle frequencies; Portuguese and Czech use their configured FrequencyWords lists; French uses Lexique 4 FreqOrtho. Finnish now has a release-matched frequency companion derived from its exact FrequencyWords OpenSubtitles 2018 source snapshot. The Finnish conversion uses the listed-token denominator, recorded in the companion, rather than claiming the complete corpus token total.

Portuguese has twelve released surfaces without source-list frequencies. They contribute zero measured frequency (with source rank breaking ordering ties); no frequencies are invented. One Portuguese split reading is excluded for lack of a suitable example. French currently has no mergeable groups in this release, so it remains a surface-based preview despite the shared algorithm. Spanish `hay` is correctly represented by separate `hay` and `haber` reading items; it does not donate membership to a generic haber group.

Swedish, Italian, Dutch, Russian, Polish and Brazilian Portuguese have no currently shipped Speech capability in configuration. They are not measured as zero-vocabulary languages.

Pool sizes are release-specific. They change with vocabulary coverage, assigned senses, grouping decisions and filters. They cannot be used as universal reference maxima or interchangeable measures across languages.

## What external research can and cannot supply

**Milton / Alexiou's multilingual X-Lex work** uses a common method for English, French and Greek: recognition within a restricted 5,000-lemma frequency pool. Their CEFR associations differ by language, and learners at different levels overlap. Those numbers are useful reference evidence, but neither total vocabulary estimates nor Fluency lexical-group thresholds. [Original paper, Tables 2 and 4](https://www.enl.auth.gr/gala/14th/Papers/English%20papers/Milton%26Alexiou.pdf).

**Gesa's recent English study** tested 311 Catalan/Spanish-speaking learners against Oxford Placement Test levels and a 14,000-word-family vocabulary test. Vocabulary increased with level, but individual scores overlapped and A2/B1 differences were not statistically significant. The authors discuss cognate-related inflation. This supports a probabilistic calibration rather than fixed universal cutoffs; it does not establish thresholds for learners of Spanish. [Full study](https://onlinelibrary.wiley.com/doi/full/10.1111/ijal.70313).

**Finlayson, Marsden and Hawkes** review early vocabulary-size evidence in developing lists for French, German and Spanish. Broad A1–B1 associations support frequency-based vocabulary learning, but their counting units and learner populations differ from Fluency's pool. Their review cannot validate A1–C2 group thresholds for this app. [Publisher record](https://journals.sagepub.com/doi/abs/10.1177/13621688241288877).

**DIALANG** offers a shared CEFR-based assessment approach across fourteen languages, including Spanish, Portuguese, Finnish and French. Its vocabulary placement component is one part of a diagnostic system; this is not a reusable word-count-to-CEFR lookup. Czech is not among those fourteen languages. [Council of Europe documentation](https://rm.coe.int/16806a6d13).

The Council of Europe specifies communicative descriptors and language-specific reference descriptions rather than a universal numerical vocabulary requirement. [Reference level descriptions](https://www.coe.int/en/web/common-european-framework-reference-languages/reference-level-descriptions).

## Recommended calibration and presentation by language

| Language | Proposed calibration range | Evidence and practical limit |
|---|---|---|
| Spanish | Initially investigate A1–B2; add C1/C2 only if validated | Large pool, but split readings materially increase its count. Match app scores to independent Spanish CEFR results rather than English numbers. |
| Portuguese | Initially investigate A1–B2; extend only if validated | Large pool with different merging and sense-source behaviour. DIALANG can provide an external receptive-skill comparison; full proficiency claims need fuller assessment. |
| Czech | Initially investigate A1–B2; extend only if validated | Many forms collapse into fewer groups. Use an independent Czech CEFR assessment; neither Spanish boundaries nor DIALANG support a direct conversion. |
| Finnish | Investigate A1–A2 first | Only 856 eligible groups in a 2,000-surface pool. Ceiling effects prevent assuming a full six-level scale. Even low-level CEFR labels require learner validation. |
| French | Keep vocabulary/placement output only for now | A 131-item surface preview cannot support broad vocabulary-size calibration. Expand and resolve lemma metadata before fitting a CEFR scale. |

These are **ranges to investigate**, not claims that the pools establish these levels or numerical boundaries.

Use the same estimator implementation but separate calibration for each language and material pool revision. A first calibration study should collect independent, recent CEFR evidence, the app's release/grouping version, group count and interval, band answer counts and knowledge rates, native/known languages, and whether the result reached the pool ceiling. Prefer externally assessed levels; self-reported CEFR can be exploratory data but should not define production thresholds. No learner data collection is implemented by this change.

As a practical recruitment target, aim for roughly 30 learners per level being calibrated, plus a separate validation group. This is a study-design proposal, not a statistical guarantee. Include different first-language backgrounds and repeat a subset of checks to quantify short-test instability.

Fit an ordered CEFR prediction from the vocabulary-group score and frequency-band profile for each language. Evaluate adjacent-level confusion and repeatability on held-out learners; compare against a count-only model. If vocabulary cannot distinguish neighbouring levels, present an adjacent-band range such as “Vocabulary estimate: around B1–B2,” or withhold the label. Do not convert the current group-count interval mechanically into a CEFR confidence interval; model uncertainty and external-assessment uncertainty also matter.

A high score in a restricted pool means “you recognise most of this pool.” It must not automatically mean C2. Do not scale CEFR thresholds by a language's total pool size: 50% of 131 French surfaces and 50% of 7,585 Spanish groups measure different vocabulary coverage.

**Decision:** keep the implemented group estimate and practical placement, withhold legacy CEFR labels, and derive language-specific CEFR ranges from external learner validation. The literature supplies useful methodology and comparison points, but no defensible off-the-shelf numerical thresholds for these exact groups.


## Quick provisional cutoffs requested after implementation

These are product heuristics proposed on 9 October 2026, not fitted or validated thresholds. No numerical thresholds have been added to the app. Each number is the minimum estimated vocabulary-group count for that provisional label; below A1 is “Getting started”. Do not compare them with saved Speech ranks.

| Language | A1 | A2 | B1 | B2 | C1 | C2 |
|---|---:|---:|---:|---:|---:|---:|
| Spanish | 500 | 1,200 | 2,200 | 3,600 | 5,000 | 6,500 |
| Portuguese | 500 | 1,000 | 1,800 | 3,000 | 4,200 | 5,400 |
| Czech | 400 | 900 | 1,600 | 2,500 | 3,500 | 4,800 |
| Finnish | 500 | 1,100 | 2,000 | 3,200 | 4,500 | 6,000 |
| French | 500 | 1,000 | 1,800 | 2,800 | 4,000 | 5,200 |
| Swedish, Italian, Dutch, Polish, Russian, Brazilian Portuguese (future starting set) | 500 | 1,000 | 2,000 | 3,500 | 5,000 | 6,500 |

**How these were chosen.** Finlayson et al.'s review suggests typical A1 knowledge near 1,000 lemmas, A2 near 1,000–2,000, and B1 near 2,000–3,000. Those are broad observed associations, not lower boundaries. The suggested entry cutoffs are lower than typical within-level scores, and allow for Fluency's content-word and cognate exclusions. Milton/Alexiou's French results use a restricted 5,000-lemma test and show considerable adjacent-level overlap, so their scores are a scale check rather than values to copy. Spanish's greater reading splitting raises its proposed thresholds relative to Portuguese; Czech's pool collapses many inflections. These adjustments are judgement, not measured conversion factors. The higher-level widening is a deliberately conservative product choice, not a research finding.

There is no direct benchmark for Fluency groups in Finnish or Czech, and no resolved group pool for the future languages. Their numbers are especially tentative. Russian lexical minima are defined for a different examination vocabulary; do not silently substitute those requirements for this recognition measure. The shared future set avoids pretending that unmeasured language differences have been quantified.

**Ceiling and uncertainty rules.** If the point estimate or upper interval reaches 90% of the available pool, prefer “Near the top of this vocabulary check; level may be higher” over a precise CEFR label. This 90% guard is a heuristic. At present Finnish cannot reach the proposed A2 boundary, French cannot reach A1, and Czech cannot reach C2. Do not compress the boundaries to make every language display all six labels. Label French as a short vocabulary preview; a capped Finnish score needs a larger pool to distinguish A2 and above. When the existing group interval crosses a boundary, display the adjacent vocabulary bands rather than a precise level; broad uncertainty may require withholding the label. Wording should be “Rough vocabulary level”, not an overall proficiency assessment.

**Current recommendation:** use these as the next reviewable starting set if a rough label is desired, retaining the ceiling rules and the ability to swap calibration later. This supersedes the earlier recommendation to wait for learner validation only for the purpose of a visibly provisional product estimate; it does not establish empirical accuracy.
