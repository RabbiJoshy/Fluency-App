# Casa: same-provider bilingual source check

Checked 2026-10-25. English subtitle files were downloaded for all 30 episodes
already represented in the Spanish preset. This establishes availability for
Casa, not coverage of most shows or production-ready translation quality.
The published preset is unchanged by this check.

| Existing episode numbering | English provider | Episodes downloaded | Closely timed candidate pairs | Share of Spanish cues |
| --- | --- | ---: | ---: | ---: |
| S01E01–09 | SubDL | 9 | 5,714 | 67.7% |
| S02E01–06 | SubDL | 6 | 3,161 | 68.8% |
| S03E01–07 | WatchSoMuch | 7 | 3,880 | 87.7% |
| S04E01–08 | SubDL | 8 | 3,347 | 63.2% |
| Total | Same provider as each episode's Spanish source | 30 | 16,102 | 70.8% |

## Sources and release selection

- S1/S2 English: SubDL's `La.casa.de.papel.S01.720p.BluRay.FLAC2.0.x264-SbR`
  pack, uploaded by eladir. It contains 15 original-length episodes, numbered
  S01E01–15. The final six correspond to the preset's original S02E01–06.
  [English listings](https://subdl.com/subtitle/sd1300185/money-heist/first-season/english).
  Download: `https://dl.subdl.com/subtitle/2035037-2664436.zip`.
- S4 English: bontoutou's full English US Netflix WEB-DL pack (not the SDH or
  forced-only alternatives), matching the uploader/release family of our Spanish
  source. [Source page](https://subdl.com/s/info/3k4AsKyMHo/money-heist).
  Download: `https://dl.subdl.com/subtitle/1578521-2179767`.
- S3 English: WatchSoMuch's `Money Heist S03 COMPLETE 1080p WEB X264-EDHD`
  entries marked Original. One file per episode.
  [Episode 1 listing](https://watchsomuch.tv/Subs/?e=1&l=en&mid=6468322&s=3).
  Exact download URLs and hashes for all seven are in the saved acquisition manifest.

The downloaded S1 and S4 Spanish packs match the SHA-256 hashes already recorded
in the app's Spanish source manifest. No new Spanish cut was substituted.

One other English upload advertised for the original 15 episodes had visibly
poor English and subtitle sequence numbers translated into the dialogue. It was
rejected by preview inspection. Mere language availability is not a quality check.

## Timing experiment and limitations

The experiment uses the current Spanish cue text/timestamps and the existing SRT
cleaner. It tests three global time scales (1, 25/23.976 and 23.976/25), searches
for offset peaks within ten minutes, and counts one-to-one cues whose starts are
within 250 ms and ends within 350 ms. All selected episode scales were 1.

S1/S2 often need offsets of several minutes. S3/S4 mostly align at zero or a
small offset. Do not pair cues by row number or assume that identical episode
numbers mean identical cuts. The original first two seasons are also different
from the Netflix 13+9 recut.

These are timestamp candidates, not 16,102 independently verified translations.
One longer pair per episode and additional spread-out S1E1/S2E1/S3E1/S4E1 pairs
were inspected. The sample showed corresponding dialogue, but some translations
are stilted, paraphrased, or omit small phrases. Split/merged subtitle boundaries
also leave useful dialogue outside the strict one-to-one matches. Full semantic
accuracy and production alignment acceptance thresholds have not been measured.

The direct SubDL pack downloads took roughly 0.2–0.5 seconds in the observed
requests. WatchSoMuch initially throttled parallel page discovery with "Please
slow down!". Remaining episodes were retrieved after backing off and spacing
requests. These observations are not an end-to-end online latency guarantee or
an API benchmark.

## Saved local evidence

Raw downloads, English checksums/URLs, the audit script, per-episode metrics and
candidate pairs are stored outside Git in:

`/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/series/la-casa-de-papel/english-20261025/`

- `sources.json`: provenance, episode mapping and input dialogue checksum.
- `pairing-report.json`: counts, offsets, scales and English filenames.
- `candidate-pairs.json`: Spanish/English text and original timing evidence.
- `audit_pairing.py`: rerun from the Fluency-Next repository root.

No LLM, translation service, biencoder or WSD call was used. No app assets,
browser caches or deployed decks were changed.

Follow-up: [Grouped alignment experiment](casa-bilingual-grouping-check.md) tests cue groups, small timing corrections and actual deck-example coverage.
