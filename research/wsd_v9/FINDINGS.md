# Spanish/Portuguese WSD v9 research findings — 2026-09-01

## Decision

There is no promotable v9 method yet. None of the three tested techniques beats
the recorded v7 result on the 199-answer hard panel, and the corpus-first WSI
result becomes sharply negative when expanded beyond a favorable ten-word
pilot. Production WSD, release configuration, decks, and Rosalía were not
changed.

The experiments use no aligned English at runtime or during artifact training.
The `english` field in the hard panel is never read. Candidate inventories stay
closed. Dictionary examples and source-language subtitle sentences are the only
semantic inputs.

## Results

| experiment | hard-panel result | paired result vs prior+POS | disposition |
|---|---:|---:|---|
| prior + bridged POS | 148/199 (74.4%) | — | control |
| presence profile | 148/199 (74.4%) | 0 fixes / 0 breaks after CV | reject |
| abstract frame, selective | 153/199 (76.9%) | 10 fixes / 5 breaks | retain as a lead only |
| exact lexical relations | 148/199 (74.4%) | ignored in every fold | reject |
| semantic relation slots | 148/199 (74.4%) | ignored in every fold | reject |
| BETO dictionary prototype | 151/199 (75.9%) | 12 fixes / 9 breaks | below v7 |
| random-negative pair scorer | 145/199 (72.9%) | 1 fix / 4 breaks | reject |
| sibling-negative pair scorer | 148/199 (74.4%) | ignored in every fold | reject at current depth |
| recorded v7 shipped stack | 156/199 (78.4%) | exact predictions unavailable | acceptance bar |

The selective frame threshold was `0.35` in every fold. Its +2.5 percentage
point paired delta has a bootstrap 95% interval of roughly −1.0 to +6.5 points,
and the method remains three items below v7. Most of its visible wins are
grammatical distinctions such as `este` and `por`, not the difficult lexical
sibling residue. A post-hoc frame/BETO agreement rule made four fixes and no
breaks, but reached only 152/199 and was not a predeclared method.

The sibling scorer is a particularly clear negative result. It reaches 99.7%
training accuracy on 1,248 positive and 4,992 hard-negative source-example
pairs, yet grouped held-out subtitle evaluation chooses to ignore it in all five
folds. This is dictionary-example overfit, not a deployable sense verifier.

## Substitution WSI

The initial ten-surface pilot looked promising: WSI mapped 19/31 items correctly,
versus 13/31 for prior+POS and 16/31 for a one-cluster mapping. The broad run
falsified that lead:

| broad Spanish run (122 surfaces with enough corpus support) | correct |
|---|---:|
| prior+POS on the 184 covered panel items | 135/184 (73.4%) |
| direct masked-substitute profile | 94/184 (51.1%) |
| one cluster per surface | 97/184 (52.7%) |
| selected WSI clusters | 97/184 (52.7%) |

The clustering itself is not behaving like a natural sense inventory. Of 122
Spanish surfaces, 90 select the imposed maximum of six clusters. Clusters map to
only 58.2% as many unique meanings as clusters, the median mapping margin is
0.053, and 48.5% of mappings have margin below 0.05. The pilot gain was slice
selection, not a reusable mechanism.

Portuguese reproduces the diagnosis with Wiktionary and mBERT. Seven of ten
surfaces select the six-cluster ceiling; mean seed-stability ARI is 0.64; average
mapping uniqueness is 0.58; and half the mappings have margin below 0.05.
`claro` cannot map any cluster because its Wiktionary senses have no source
examples. This is a concrete provider-parity failure mode, not a hypothetical
one.

## Provider parity

The relation-profile concept has a real shared contract: both providers emit
the same `presence`, `frame`, `relation`, and typed relation-slot families. Only
source-example decoding and Wiktionary target offsets are provider-specific.
Missing support is explicit.

| full 2,000-card menu | senses | usable sense profiles | coverage | dominant failure |
|---|---:|---:|---:|---|
| SpanishDict | 23,746 | 21,504 | 90.6% | 2,537 target-location failures |
| Wiktionary (Portuguese) | 12,389 | 7,797 | 62.9% | 4,559 senses with no example |

Wiktionary offsets make target location reliable when an example exists, but
example absence makes an example-profile method unsuitable as the shared
primary engine. An explicit backoff would be mandatory.

## What remains worth doing

The evidence points back to depth, not a more elaborate ranker. The next honest
experiment is a new title-held, deduplicated sibling-sense dataset with more than
12 source occurrences behind each sense, labelled offline by a better
source-only teacher and manually audited. The current hard panel is now a
development set and cannot be the final acceptance set for a method chosen from
these results. Any paid teacher run must first print projected units and cost.

Until that data exists:

- do not promote the selective frame gate;
- do not grow the sibling classifier;
- do not pursue substitution-based WSI;
- do not build a v9 deck or touch Rosalía.

## Artifacts

Generated reports remain local under `research/wsd_v9/results/` and are ignored
by Git because the full provider profiles are tens of megabytes. Each result
directory contains `report.json`; scored experiments also contain per-item
predictions or cluster audits. The contrastive directory contains its reusable
source-only prototype and pair-model artifacts.
