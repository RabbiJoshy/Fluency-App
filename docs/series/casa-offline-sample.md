# Casa de Papel offline sample

The preset uses real Spanish subtitle files already downloaded locally. Building
it makes no network, translation, or WSD calls. It replaces the previous
317-line illustrative dataset.

Coverage: 30 original-numbered episodes: S01E01–09, S02E01–06, S03E01–07,
S04E01–08. Missing: S03E08 and all ten season 5 episodes. The original first
two seasons were recut into 22 Netflix episodes; these credits use the original
9+6 numbering. This sample is not a complete-show transcript collection.

The generated assets contain 22,755 cleaned dialogue cues and 12,706 observed word forms, giving 128 study
levels of up to 100 cards. All forms are admitted, including the 6,102 matches
in the original Speech inventory and forms absent from both frequency lists. Word occurrences
retain repetitions; example text is deduplicated and spread across available
seasons. Definitions still use canonical Speech ranks. Dialogue examples remain
unassigned. The v6 preset includes conservative English matches in 21 original-numbered
episodes across Seasons 1, 3 and 4: 5,495 full bilingual groups supply selected translated examples across 7,930
cards when all observed forms are included.
Translations are preferred when selecting examples. Original Spanish cues alone
supply occurrence counts; expanding an example to its complete bilingual group
never adds occurrences. Cards without a matching English passage retain Spanish
examples and their existing English dictionary definitions.

Early-season English examples use a separate Netflix-cut bilingual source.
The 13+9 Netflix episodes cannot be aligned by timestamps against the original
9+6 episode cut. Instead, Spanish and English are first paired within the Netflix
cut using the same precision timing rules. A passage is then attached to an
original episode only if its complete Spanish word sequence matches exactly one
whole-cue span across the original first two seasons. Matches require at least
six words and at most six original cues; punctuation, case and wrapping may
vary, but words, accents and negation cannot. Ambiguous, partial and fuzzy text
matches are rejected. This bridge does not change the Spanish count inputs or
episode numbering. Provenance retains both the original timing and Netflix
source episode/timing (`unique-exact-span-v1`). The current download contains
Netflix S01E01–08, supplying 1,459 added groups across original S01E01–06. The
provider throttled further acquisition even after backoff, so this is explicitly
a partial sample. Original S01E07–09 and S02 still have no English examples; no
claim is made that those episodes lack usable translations elsewhere.

The first original-length English packs contained literal idiom translations,
a mistranslated joke and duplicated wording. That diagnostic spot-check did not
establish that every line was unusable. We prefer the separately checked Netflix
pairs and reject known meaning errors individually; awkward but faithful English
is acceptable. The initial Season 4 English US dub caption track was replaced
with the translated Hitchcock ION10 track. One known numeric mistranslation in
Season 3 is excluded; seven historical exclusions remain tied to the rejected
Season 4 track hash.

The shared offline importer now annotates every observed form with Turbo's local
50k rank, exact dictionary membership, lemma suggestion, and any curated entity
candidate. The Casa build runs the same JavaScript recognizer through a local
Node adapter. It recognises 10,335 forms on the frequency list, including 4,233
outside the current study inventory, and finds 13 curated entity candidates.
All 12,706 observed forms remain in `deck.intake.surfaces`, including unknowns;
each retains a count and up to three examples with original character offsets.
Repeated line text is stored once in `intake.exampleLines`; card projection
expands the line references without losing the original offsets.

Recognition and admission are separate. Lemma hints do not merge forms, especially
attached clitics/pronominal verbs. The separate clitic work and canonical Speech
inventory remain unchanged. Every observed form now gets a series card; missing
definitions are explicitly pending instead of excluding the word. Additional
forms receive local Wiktionary menus where published entries or form-of paths
exist; the 50k rank is recognition metadata, not a claim that a definition exists. Entity tagging uses the shared Turbo curated registry plus retained build-time
Wikipedia candidates. The optional separate entity acquisition was throttled
after 132 queries, so remaining uncurated entity lookups are pending. Opening
the preset makes no Wikipedia requests and never claims a name is sense-resolved. Older cached playlists must
be rebuilt from their original lyrics to recover words filtered out previously.
Unsupported languages or unavailable local recognition assets leave existing
study imports usable; a later build retries failed asset loading.

The matching policy is `precision-timing-v1`: both outer boundaries within
150 ms, up to three cues per language, at most 12 seconds, no internal silence
longer than 1.2 seconds, strong episode timing support and independent neighbouring
matches. This establishes timing acceptance, not a guarantee of semantic accuracy.
A reproducible six-pair sample from each of the 15 later-season source episodes
(90 total) was read by the assistant; no wrong-passage matches were observed. This is not an independent
human accuracy benchmark. Known wording/meaning errors were blocked before build.
A further reproducible
four-passage sample from each of the eight Netflix source episodes (32 total)
was read by the assistant with no wrong-passage matches observed. Targeted
checks of numbers and idiomatic wording found one subject-changing English
error, which was blocked individually. This remains a spot-check, not an
exhaustive semantic review or an independent accuracy benchmark.

Source URLs, local filenames, archive members, and SHA-256 hashes are recorded
in `app/data/series/casa-de-papel-sources.json`. Raw sources remain outside Git. Later-season English sources are under `english-20261025/`; Netflix-cut sources
are under `netflix-20261025/` in the same raw root. Their episode mapping and
exclusions are in the manifest.
The original Spanish Seasons 1, 2, and 4 came from SubDL packs; Season 3 came
from WatchSoMuch. The added Netflix Spanish tracks came from WatchSoMuch and
their English tracks from SubDL’s Mooi1990-labelled season pack.
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

Both the bundled preset and its browser fallback preserve full Spanish/English groups. The preset revision is `offline-30-episodes-v6-example-reuse`, so reopening refreshes older caches while failed refreshes retain usable decks. No source matching or WSD calls are made when opening the preset.

The Netflix bridge diagnostic sample and unchanged-count comparison are saved
locally under `Fluency-Workspace/audits/casa-netflix-bridge-20261026/`.

See [Complete series decks](complete-series-decks.md) for the shared build,
Wiktionary source, entity limitations and Élite preset.
