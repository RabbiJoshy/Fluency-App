# SubDL API trial: Casa and Élite

Run on 2026-10-28 using an ignored local `SUBDL_API_KEY`. The key is never saved
in catalogues, manifests, reports or app assets. No page scraping, translation
service, embeddings, LLM or WSD calls were used.

## Observed acquisition performance

- 26 season/language searches across Casa Seasons 1–5 and Élite Seasons 1–8:
  8.081 seconds total request time; median request 0.280 seconds; zero failures.
- One extra full-season-pack search for Casa Season 1 English: 0.198 seconds.
  This avoids newer individual uploads crowding older packs out of the first
  30 results. It is not a claim of exhaustive pagination.
- Eleven selected ZIP downloads: 1,790,501 bytes, 4.698 seconds including local
  archive validation in the final acquisition run. Additional alternative-track
  comparison downloads and earlier repeated downloads are excluded from that
  selected-pack figure.

These are local observations, not phone benchmarks, an API uptime guarantee,
or end-to-end deck generation times. Dictionary snapshot processing and review
are separate. There is no controlled page-scraping timing baseline, so the
evidence supports practical structured acquisition rather than a speedup ratio.

## Resulting presets

| Preset | Episodes | Forms/cards | Occurrences | Levels | Cards with English |
| --- | ---: | ---: | ---: | ---: | ---: |
| Casa | 30 | 12,706 | 136,924 | 128 | 7,930 (62.4%) |
| Élite | 24 | 8,378 | 99,442 | 84 | 7,301 (87.1%) |

The API returned Spanish Casa original-cut Seasons 1 and 2, plus Netflix Season 4;
23 episodes in total. The refreshed archive hashes match the existing sources.
The previous seven reviewed Season 3 episodes remain explicit retained fallbacks;
no Spanish Season 3 or 5 release was returned. The existing eight-episode Spanish
Netflix recut bridge also remains retained; its English pack was refreshed from
the API. Casa's count and translation coverage are unchanged. API access does
not by itself supply a better corpus or solve cut incompatibilities.

Élite has Spanish packs for Seasons 1–3, eight episodes each. Later Spanish
seasons returned no releases. All 24 included episodes use API-discovered files.
Season 1 retains the previously reviewed MZABI pair. Season 2 uses bontoutou's
Netflix WEB-DL Spanish/English translated tracks. Season 3 uses bontoutou's
Spanish track with hitchcock's BRiNK English pack, selected after comparing the
English US alternative. The source manifest records exact archive hashes and
members. API `hi` flags are not sufficient to distinguish older forced, SDH and
regular releases: filenames, contents and completeness checks remain necessary.

## Alignment and validation

All Spanish dialogue supplies counts. Only the existing precision timing rules
supply bilingual full-passage examples; missing English cannot remove a card.
The additional Élite episodes have dialogue through 44–53 minutes, and each
passes the full-dialogue cue/duration checks. The original Season 1 phone
translation exclusion remains intact. Season 3 episode 2 cue 55 is excluded
because its English passage adds “Thanks anyway” absent from the Spanish cue.

Assistant review inspected 64 spread-out Season 2 passages, 64 passages from
the initially considered Season 3 English track and 64 from the selected Season
3 alternative. The selected-track sample showed corresponding dialogue. This
is a spot review, not an independent estimate of semantic accuracy. Translation
paraphrases, omissions and unknown errors remain possible.

The API corrupts an accented Élite archive member name to U+FFFD. Acquisition
resolves this against unique whole filenames in the downloaded ZIP and rejects
absent/ambiguous matches; it never maps episodes by archive order. The episode
validator now uses each series' expected counts rather than Casa's numbering.

Both preset revisions change so existing local caches refresh. Offline fallback,
canonical ranks, all-form admission, translated-example preference and no-WSD
behaviour remain covered by the app tests. Assets stay below 25 MiB each.

## Reproduce

```sh
python3 scripts/probe_subdl_series.py --output-dir /external/audit/subdl-api
python3 scripts/refresh_series_from_subdl.py \
  --catalogues /external/audit/subdl-api \
  --workspace /external/Fluency-Workspace \
  --output-dir /external/audit/subdl-api/candidates
PYTHONPATH=src python3 scripts/build_series_presets.py \
  --workspace /external/Fluency-Workspace \
  --wiktionary /external/kaikki.org-dictionary-Spanish.jsonl \
  --sources-dir /external/audit/subdl-api/candidates \
  --output-dir /external/audit/subdl-api/candidates
```

The acquisition script uses the reviewed exact release IDs; it is an offline
trial tool, not a finished arbitrary-show online selector. Candidate output is
separate from app assets until validated and copied. Existing reviewed Casa
fallback files must be present in the external workspace. Raw evidence for this
run is under `Fluency-Workspace/audits/subdl-api-20261028/`, including redacted
API responses, acquisition manifests, episode metrics, review samples and
`result.json`. Rebuilding the presets after acquisition needs no network calls.
