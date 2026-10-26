# Élite: second-show, single-provider precision-first check

Checked 2026-10-25. The experiment obtained Spanish and English subtitle packs
for all eight episodes of Season 1 from SubDL alone. It does not measure other
seasons, representative coverage of the full show, or most-show availability.
No app preset, menu, source rankings or live deck was changed.

## Acquisition

- Spanish: `Elite-Season01`, uploader smiling. The ZIP has eight MZABI
  Spanish (Spain) Addic7ed files.
  [Source page](https://subdl.com/s/info/2bZxKAX00z/elite).
  Download: `https://dl.subdl.com/subtitle/2457152-2243025.zip`.
- Primary English: `Elite - s01.MZABI.English.C.orig.Addic7ed.com`, uploader
  Habib_Kzh. Eight matching-release English files.
  Download: `https://dl.subdl.com/subtitle/2457146-1857077.zip`.
- Comparison English: `Elite.S01.SPANiSH.WEBRip.x264-ION10`, uploader hitchcock.
  Eight English files for another release.
  Download: `https://dl.subdl.com/subtitle/2457109-1916616.zip`.
  [English listings](https://subdl.com/subtitle/sd1300491/elite/first-season/english).

All three ZIPs were downloaded in one batch taking 0.392 seconds in the observed
run. Local parsing, counting and testing both packs took 1.472 seconds.
This excludes manual source discovery, is not an authenticated API test, and
is not a first-request or ongoing latency guarantee. Source URLs, ZIP member names,
byte sizes and SHA-256 hashes are retained in the local acquisition manifest.

## Spanish occurrence counts

Counting uses all 5,856 cleaned Spanish dialogue cues, regardless of translation
availability. It found 35,791 token occurrences, 4,482 distinct surface forms,
and 3,006 forms in the current 10k study inventory (31 levels at 100 cards).
Forms remain separate; there is no new WSD or clitic merging.

## Precision-first match acceptance

This experiment uses a stricter policy than the earlier Casa coverage experiment:

1. Fit the episode offset/scale using repeated start AND end boundary evidence.
   Require at least 30 tight boundary matches and support from 35% of the smaller
   cue set before accepting any examples from an episode.
2. Use disjoint monotonic groups of at most three cues per language, outer
   boundaries within 150 ms, maximum duration 12 seconds, and no silence over
   1.2 seconds within a group. Reuse the evidence-gated small local timing corrections.
3. Require independent neighbouring matched groups on both sides within 15 seconds.
4. Keep informative examples: at least four Spanish tokens and three English tokens.
   Show the complete Spanish group with the complete English group.
5. Reject the rest. Do not change the Spanish frequency counts to follow acceptance.

The primary MZABI release was chosen by release compatibility before measuring
coverage. No rule thresholds were changed after viewing the review sample.
All eight primary episodes fit time scale 1 and global offsets of 0–100 ms.

| English release | Episodes | Accepted example groups | Spanish cues represented | Study surfaces with an example |
| --- | ---: | ---: | ---: | ---: |
| MZABI (primary, same release family) | 8 | 2,508 | 3,756 / 5,856 (64.1%) | 2,655 / 3,006 (88.3%) |
| ION10 (comparison) | 8 | 2,012 | 3,266 / 5,856 (55.8%) | 2,460 / 3,006 (81.8%) |

These are automatic acceptance counts, not exhaustively verified translations.
The lower retained cue coverage is intentional; informative translated examples
are selected independently of the much larger set used for counting.

## Review of correct-passage matching

A reproducible sample of 12 informative groups per episode (96 total) was selected
from the primary MZABI pack using fixed per-episode random seeds. The assistant
read all 96 Spanish/English pairs. This was not a separate human-labelled benchmark.

- Wrong-passage matches observed: **0 / 96**.
- One reviewed example should be rejected for translation quality: in S01E08 the
  Spanish says the phone was thrown away, while the English says the listener
  has the phone. The English belongs to the same passage but mistranslates it.
- Other notes include a literal idiom and minor changes in address terms or
  referents. Those were separated from wrong-line pairing errors.

The sample supports the approach for this season but does not prove near-100%
precision over all 2,508 accepted groups. Review decisions are retained separately
from machine output so rerunning the audit cannot silently erase them.

## Reproduction and saved evidence

```sh
python3 scripts/audit_series_subtitle_sample.py \
  --raw-root /Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/series/elite/20261025 \
  --output-dir /Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/audits/elite-bilingual-20261025
```

Raw ZIPs and provenance: `Fluency-Workspace/raw/series/elite/20261025/`.
Audit outputs: `Fluency-Workspace/audits/elite-bilingual-20261025/`.
Files include per-episode results, full accepted groups, vocabulary occurrence
counts, original review sample, annotated review sample and reviewed summary.

Validation: 17 focused tests passed across the new precision policy, grouped
alignment and existing Casa ingestion. These include correct offset fitting,
start/end evidence, weak-episode rejection, isolated coincidence rejection,
short-reply exclusion, no cue reuse, omissions and timing-jump safeguards.
No translation service, embedding, external LLM or WSD request is made by the audit.

## App integration (2026-10-26)

The Season 1 sample is now a selectable TV Series preset. All 4,482 observed
forms receive cards (45 study levels), including words outside the 10k inventory.
English examples are available on 3,817 cards; the reviewed bad phone passage
is excluded. No WSD assignments are added. See
[Complete series decks](complete-series-decks.md) for the build and limitations.
