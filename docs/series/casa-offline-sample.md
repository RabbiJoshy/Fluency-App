# Casa de Papel offline sample

The preset uses real Spanish subtitle files already downloaded locally. Building
it makes no network, translation, or WSD calls. It replaces the previous
317-line illustrative dataset.

Coverage: 30 original-numbered episodes: S01E01–09, S02E01–06, S03E01–07,
S04E01–08. Missing: S03E08 and all ten season 5 episodes. The original first
two seasons were recut into 22 Netflix episodes; these credits use the original
9+6 numbering. This sample is not a complete-show transcript collection.

The generated assets contain 22,755 cleaned dialogue cues and 6,102 vocabulary
inventory matches, giving 62 study levels of up to 100 cards. Word occurrences
retain repetitions; example text is deduplicated and spread across available
seasons. Definitions still use canonical Speech ranks. Dialogue examples remain
unassigned. The v3 preset includes conservative English matches from Seasons 3–4:
4,036 full bilingual groups supply 9,080 selected word examples across 3,754 cards.
Translations are preferred when selecting examples. Original Spanish cues alone
supply occurrence counts; expanding an example to its complete bilingual group
never adds occurrences. Cards without a matching English passage retain Spanish
examples and their existing English dictionary definitions.

Seasons 1–2 remain in all Spanish counts but have no sentence translations: an
alternative original-length English pack repeated problems found in the first
pack, including literal idiom translations. The initial Season 4 English US dub
caption track was rejected and replaced with the translated Hitchcock ION10
track. One known numeric mistranslation in Season 3 is excluded by source cue
span; seven historical exclusions remain tied to the rejected track hash. This
prioritises correct pairing and permits missing translations.

The shared offline importer now annotates every observed form with Turbo's local
50k rank, exact dictionary membership, lemma suggestion, and any curated entity
candidate. The Casa build runs the same JavaScript recognizer through a local
Node adapter. It recognises 10,335 forms on the frequency list, including 4,233
outside the current study inventory, and finds 13 curated entity candidates.
All 12,706 observed forms remain in `deck.intake.surfaces`, including unknowns;
each retains a count and up to three examples with original character offsets.

This is recognition, not a new source of definitions or a grouping policy.
Lemma hints do not merge forms, especially attached clitics/pronominal verbs.
The 6,102-card study inventory is unchanged while the separate clitic work is
in progress. Missing definitions never become blank study cards. Entity tagging
uses Turbo's local curated registry only; it makes no Wikipedia requests and
does not claim ambiguous names are sense-resolved. Older cached playlists must
be rebuilt from their original lyrics to recover words filtered out previously.
Unsupported languages or unavailable local recognition assets leave existing
study imports usable; a later build retries failed asset loading.

The matching policy is `precision-timing-v1`: both outer boundaries within
150 ms, up to three cues per language, at most 12 seconds, no internal silence
longer than 1.2 seconds, strong episode timing support and independent neighbouring
matches. This establishes timing acceptance, not a guarantee of semantic accuracy.
A reproducible six-pair sample per translated episode (90 total) was read by the
assistant; no wrong-passage matches were observed. This is not an independent
human accuracy benchmark. Known wording/meaning errors were blocked before build.

Source URLs, local filenames, archive members, and SHA-256 hashes are recorded
in `app/data/series/casa-de-papel-sources.json`. Raw sources remain outside Git. English sources are under `english-20261025/` in the same raw root; their episode mapping and exclusions are in the manifest.
Seasons 1, 2, and 4 came from SubDL packs; season 3 came from WatchSoMuch.
These files are separate from the original local OPUS v2018 bilingual store,
whose full 61,434,251-row Spanish/English ID file had no Casa series/episode ID
matches when checked on 2026-10-21.

Rebuild from the repository root, with Node.js and the local raw sources available:

```sh
python3 scripts/build_casa_de_papel.py \
  --manifest app/data/series/casa-de-papel-sources.json \
  --raw-root /path/to/raw/series/la-casa-de-papel \
  --allow-partial
```

Checksums, duplicate episode IDs, and implausibly short/forced-only subtitle
files fail the build. Partial coverage requires the explicit flag and is
recorded in both generated assets. A future dataset revision must also update
`CASA_PRESET_REVISION` in `app/js/playlist-live.js` to refresh browser caches.

Both the bundled preset and its browser fallback preserve full Spanish/English groups. The preset revision is `offline-30-episodes-v3-translations`, so reopening refreshes older caches while failed refreshes retain usable decks. No source matching or WSD calls are made when opening the preset.
