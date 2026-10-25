# Casa grouped subtitle alignment experiment

Checked 2026-10-25 using the English downloads recorded in
[casa-bilingual-source-check.md](casa-bilingual-source-check.md). This is an
alignment feasibility experiment; published app assets and decks are unchanged.

## Results

| Measurement | Original strict individual-cue match | Individual cues at 500 ms tolerance | Groups plus supported local timing corrections |
| --- | ---: | ---: | ---: |
| Spanish dialogue cues | 16,102 / 22,755 (70.8%) | 18,560 / 22,755 (81.6%) | 21,839 / 22,755 (96.0%) |
| Currently selected deck examples | 12,772 / 18,415 (69.4%) | 14,912 / 18,415 (81.0%) | 17,805 / 18,415 (96.7%) |

6,048 of 6,102 cards (99.1%) have at least one selected example with a timing
candidate. Looking through all matched dialogue rather than only the current
example selection increases that to 6,049 cards. There are still 53 vocabulary
surfaces with no matched occurrence anywhere in these candidates.

3,451 selected examples require expanding the Spanish fragment to its complete
aligned group. Attaching the group's full English text to the unchanged Spanish
fragment would misrepresent what was translated. An eventual integration must
carry both full-language groups and preserve the original target-word occurrence.

| Episode set / provider | Original strict timing coverage | Grouped timing coverage |
| --- | ---: | ---: |
| Original Season 1 / SubDL | 67.7% | 95.6% |
| Original Season 2 / SubDL | 68.8% | 94.2% |
| Season 3 / WatchSoMuch | 87.7% | 97.7% |
| Season 4 / SubDL | 63.2% | 96.7% |

This is not a controlled comparison of providers: seasons, releases and English
subtitle tracks differ. Grouping closes most of the apparent coverage gap.
The lowest final episode coverage is S02E01 at 83.8%, followed by S01E09 at 84.1%.
All other episodes exceed 93%.

## Method and safeguards

`scripts/audit_casa_bilingual_alignment.py` retains each episode's previously
established global timing offset and searches for monotonic, disjoint groups of
one to four cues on each side. Outer boundaries must be within 500 ms. Groups
cannot span more than 20 seconds or bridge silences over two seconds. English
cues cannot be reused, and missing cues do not shift later matches.

The individual-cue 500 ms control separates looser timing tolerance from the
additional benefit of grouping and local corrections. All results remain timing
candidates, not semantic accuracy measurements.

Small local timing corrections search only within five seconds of the baseline.
A five-minute window requires at least ten supporting tight cue matches, support
from at least 30% of its cues, and a substantial improvement over baseline.
S01E08 had an approximately 950 ms change: its early dialogue needs a 135,050 ms
offset and its later dialogue 134,100 ms. Correction recovers the former outlier.
Only three episodes met the adjustment rules (S01E08, S01E09 and S02E01).

Before running, the script verifies the Spanish dialogue snapshot hash and each
English input hash against the acquisition manifest. It does not fetch, translate,
run WSD, alter canonical card ranks, or write app assets.

## Manual review and remaining quality issue

Reviewed one multi-cue group around the midpoint of each episode (30 groups),
plus three spread-out groups in S01E08, S01E09, S02E01, S03E05 and S04E03 (15 groups).
This was a diagnostic sample, not a random, independently labelled accuracy test.
Most groups contain corresponding dialogue. It also exposed source-quality issues:

- The S1/S2 BluRay English pack contains literal translations of Spanish idioms.
  The S01E08 example using `poner la mano en el fuego` is rendered literally.
- A sampled S01E09 joke is mistranslated, and one S01E02 group contains duplicated
  English wording. Correct timestamps cannot repair those defects.
- Some later-season English dialogue is adapted or expanded relative to the
  Spanish (for example the S04E03 flowers/hammer passage). Timing agreement is
  not evidence of literal lexical equivalence.

Therefore 96.7% is candidate availability, not a claim that 96.7% of examples
have a semantically correct translation. A better English release for S1/S2 and
further review should precede publishing these candidates. No word-to-sense
assignments may be inferred from timing matches alone.

## Reproduction and evidence

From the repository root:

```sh
python3 scripts/audit_casa_bilingual_alignment.py \
  --raw-root /Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/series/la-casa-de-papel/english-20261025 \
  --output-dir /Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/audits/casa-bilingual-grouping-20261025
```

The output directory contains `summary.json`, `episodes.json` (including timing
correction evidence), and `groups.json` (complete paired text and cue indices).

Validation: 12 focused tests passed across grouped alignment and the existing
Casa ingestion checks. They cover one-to-many/many-to-one matching, complete
Spanish context, monotonicity, no English reuse, omissions, silence boundaries,
unsupported offsets, invalid timestamps and evidence-gated local corrections.
