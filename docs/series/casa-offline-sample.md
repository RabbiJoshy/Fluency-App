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
unassigned, and no sentence translations are invented: the downloaded sources
have Spanish only. Dictionary definitions continue to provide English meanings.

Source URLs, local filenames, archive members, and SHA-256 hashes are recorded
in `app/data/series/casa-de-papel-sources.json`. Raw sources remain outside Git.
Seasons 1, 2, and 4 came from SubDL packs; season 3 came from WatchSoMuch.
These files are separate from the original local OPUS v2018 bilingual store,
whose full 61,434,251-row Spanish/English ID file had no Casa series/episode ID
matches when checked on 2026-10-21.

Rebuild from the repository root, with the local raw sources available:

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
