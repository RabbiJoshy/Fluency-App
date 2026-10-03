# Polyglot Artist scaling

Date: 2026-10-03. Scope: POLYGLOT, following SCAR, VERSE and CHORUS.

**Status: French and Portuguese test releases published, activated in the live Artist catalog, and interactively verified.** These are conservative test decks with native WSD evidence. Targeted semantic regressions pass; this is not a certification of perfect sense accuracy or complete vocabulary coverage.

## Releases and measured coverage

Workspace: `/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace`.

| Measure | French | Portuguese |
| --- | ---: | ---: |
| Source songs | 64 | 19 |
| Retained lyric lines | 2,762 | 1,000 |
| Eligible observed occurrences | 19,648 | 5,541 |
| Distinct eligible surfaces | 2,391 | 930 |
| Sampled WSD requests | 6,574 | 2,647 |
| Assigned/published examples | 5,903 | 2,491 |
| Abstained requests | 373 | 110 |
| Requests with no menu | 298 | 46 |
| Released cards | **2,097** | **869** |
| Withheld surfaces | 294 | 61 |
| Required exact-text vectors | 6,449 | 3,613 |
| Remaining vector misses | **0** | **0** |
| Split app contract violations | **0** | **0** |
| Pre-WSD verification errors | **0** | **0** |
| Signed lyric-attested phrases | 46 | 33 |

Final runs: `runs/fr/lyrics/polyglot-review-20261003-v5` and `runs/pt/lyrics/polyglot-review-20261003-v4`. Final releases: `releases/lyrics/lyrics-french-test-playlist-polyglot-v5` and `releases/lyrics/lyrics-portuguese-test-playlist-polyglot-v6`. Earlier candidates and partial rehearsals are superseded and retained unchanged.

Catalog language keys are `french` and `portuguese`; card/asset identity uses `fr` and `pt`. New catalog slugs are `french-test-playlist` and `portuguese-test-playlist`. The older French `testplaylist` remains available. Existing Spanish catalog entries and generated releases are preserved.

## Source provenance

The historical French vocabulary index contained 1,455 cards; its catalog's `maxLevel: 4000` was not a measured card count. The reviewed source imports all 64 original French dumps from read-only `/Users/joshuathomasamar/PycharmProjects/Fluency/Artists/french/TestPlaylist/lyrics/french`.

Final French source: `raw/playlists/polyglot-followup-20261003/french-clean-v4.json`. The importer records 89 cleaning events, including contributor/title headers, anchored Embed footers, explicit Read More introductions, embedded format characters, and five reviewed editorial/section prefixes. Removed text and original file hashes remain in the source manifest. `config/lyrics/fr-reviewed-editorial-prefixes.json` pins the exact reviewed prefixes and refuses source drift. English/code-switched lyric lines remain observed source; absent French dictionary menus are not invented.

Portuguese source: `raw/playlists/polyglot-20261003/portuguese-test-playlist.json`. Twenty requested songs are listed in `config/lyrics/portuguese-test-playlist.json`; 19 resolved through LRCLIB with retained search responses, recording IDs, source URLs and authentic plain lyrics. Marília Mendonça's *Todo Mundo Vai Sofrer* failed with HTTP 503 and was excluded. Artists include Caetano Veloso, Marília Mendonça, Anitta, Gilberto Gil, Djavan, Tim Maia, Chico Buarque, Elis Regina, Jorge Ben Jor, Alceu Valença, Maria Gadú and Tribalistas. This fixture exercises Brazilian Portuguese; European Portuguese quality is not certified. LRCLIB recording IDs are not Spotify track IDs, and no Spotify playlist is required.

## Cross-language architecture

1. **Surface identity and spans.** Discovered language adapters produce canonical typography, eligible units, exact offsets and surface keys. Dictionary lemmas are lookup metadata, never new cards. Every final occurrence is verified against its source substring.
2. **Language adapters.** French reuses shared tokenization and elision configuration: `j’`, `l’`, `d’`, `qu’` remain observed surfaces, with ambiguous expansions retained. Empty hyphen components reject safely. Portuguese preserves `do`, `numa`, `disse-me`, `fazê-lo` and lexical compounds; productive enclitic hosts are lookup alternatives (`disse`, `fazer`, `pôr`). Ambiguous deleted consonants and mesoclisis require dictionary evidence and remain conservative omissions.
3. **Morphology and evidence.** Scoped curated expansions affect a separate tagging string with reversible span mapping. Original cards/lyrics remain unchanged. Pinned models are `fr_core_news_lg@3.8.0` and `pt_core_news_lg@3.8.0`. POS, lemma, raw morphology, grammatical axes and adapter corrections are recorded. Closed-class French pronoun person corrects noisy model agreement tags. French `on`'s singular verb agreement does not constrain its semantic number. Portuguese `você` has semantic person 2 despite third-person verb agreement. Adapter hints are recorded separately from original model values.
4. **Provider menus.** Generic Kaikki integration uses the supported `enwiktionary` edition, pinned French 2026-08-05 and Portuguese 2026-08-20 snapshots. Existing provider POS bridges reconcile AUX/VERB, ADP/DET contractions and PRON/pron. Isolated `fr-lyrics-polyglot-v2` and `pt-lyrics-polyglot-v2` menu policies extract explicit grammatical prose. Tagger lemmas rescue absent menus only; they do not widen existing authoritative surface menus. Scoped reviewed declarations repair clipping, spelling/Unicode and specific adlibs while preserving the original menu artifact.
5. **Freeze and sampling.** The shared lyrics rank/sense-count budget and sentence sieve select requests. Exact requests and a verified pre-WSD freeze precede WSD. Portuguese verifies and pins the existing `raw/surfaces/pt/prewsd/20260914T222723Z-e43a0469-v2`; neither its speech freeze nor its ledger is rewritten. New, signed fixed-expression inventories are lyric-attested against pinned Kaikki rows: 46 French and 33 Portuguese expressions compete in shared MWE WSD. Unreviewed candidates are recorded as excluded; no inferred inflections or template gaps are enabled. The older Portuguese speech MWE inventory remains unchanged.
6. **Shared WSD.** `DictionaryCandidatePolicy` requires language-specific callbacks and reuses the historical engine. Strict grammar and scoped surface POS checks run before scoring; an empty evidence-compatible set abstains rather than restoring a known-wrong name or person. Person evidence requirements apply to semantic pronoun marks, avoiding article rejection from inherited surface redirects. French `c’` cannot select European Community, ordinary negative `pas` cannot select its rhetorical intensifier, and `est-ce` receives explicit auxiliary evidence. Common grammatical readings exclude case-colliding proper names. Existing Spanish policy defaults are preserved.
7. **Publication.** Assigned examples publish the existing forced-leaf split contract. Abstentions, absent menus and missing cache vectors are explicitly withheld. The Artist bridge preserves each native decision's active projection and assignment method; mixed provider/MWE cards are labelled `mixed`. Every published example has native evidence. Method composition is derived from actual occurrence evidence and explicitly names the language profile; it does not assume `native-v7` is the only native method. Song catalogs carry complete card membership derived from full frozen occurrences, independently of sampled examples. A live single-song check caught missing membership in earlier packages; those packages are superseded by the final IDs. App catalog entries bind to their own release IDs, so adding languages does not replace the Spanish catalog.

Generic lyrics processing and corpus stages now accept installed dictionary-language adapters and pinned routing snapshots without Spanish elision/conjugation dependencies. These offline profiles are not the TURBO live client/worker pipeline.

## Review evidence and coverage limits

`raw/playlists/polyglot-followup-20261003/validation-final-v3.json` verifies exact spans, native coverage, freezes, cache completion and release contracts. `coverage-and-semantic-audit.json` accounts for **all 348 previously withheld forms**: French 40 recovered, 12 removed as source contamination, 158 still without menus and 54 still without publishable assignments; Portuguese 27 recovered, 22 still without menus and 35 still without assignments. Additional surfaces are now withheld by stricter quality gates, giving final totals of 294 French and 61 Portuguese. The report retains surface/POS counts, example IDs, song titles and recovery glosses; this is exhaustive outcome accounting, not a semantic certification of every unsupported spelling.

Targeted semantic regressions pass for French `tu`, `on`, `l’`, `c’`, `pas`, `est` and Portuguese `eu`, `você`, `se`, `tê`, `mó`, `nê`, `chamá`. In particular, `tu` publishes “you,” `on` publishes pronoun readings rather than a Belgian village, and clipped Portuguese syllables do not publish letter-name or millstone readings. Broad embedding-dependent lexical ambiguity remains; no overall accuracy percentage is claimed.

English sentence translations remain explicitly unavailable (`english: ""`, `translation_source: unavailable`); English sense glosses are present. A free local Marian translation experiment was cached outside Git, but incorrect idioms and clipped lyrics failed review and are **not included in releases**. No complete translation quality sign-off is claimed. Examples retain the historical `spanish` wire field plus language-neutral `source_text`/`source_language` for app compatibility.

French negative `n’`, unknown hyphenated forms, unsupported code-switching, adlibs, proper names and uncertain assignments can remain withheld. These omissions are explicit and do not block a usable test release. Expanding another language requires its adapter, dictionary/policy, POS bridge, pinned tagger and selected phrase inventory; discovery alone is not linguistic certification.

## Costs and regression guardrails

User approval: **up to $1 total**. Every uncached embedding request printed projected cost before calls. Across initial and follow-up fills, **7,521 exact texts** were requested: projected total **$0.01265925**, conservative planning allowance **$0.03942780**. Estimates use $0.15 per million input tokens (characters/3; one token per UTF-8 byte for conservative planning), not invoice totals. Final runs are offline cache-only with zero paid calls. The helper enforces an invocation allowance; cumulative task cost is accounted separately.

Packaging refuses incomplete cache evaluation, changed pinned output/config artifacts or contract-invalid runs. Existing output directories cannot be overwritten. `spanish-before.json` pins 33 Bad Bunny/Rosalía/Young Miko v18 files; every hash remains unchanged. Existing production v20 catalog entries are retained exactly. `spanish-publication-preservation.json` also compares Git tree objects before/after release publication: all nine pre-existing published release trees (including current Spanish v20 artist trees) are identical.

Focused lyrics/Artist/WSD/sense-menu/provider/French suite: **514 passed, 91 subtests**. App suite with catalog and missing-colour regression check: **184 passed**. Two previously failing SpanishDict tests now pass after canonical accented reverse-lookup repair and applying conjugation/plausibility recovery to retained menus; all eight tests in that module pass. No Spanish release was rebuilt or overwritten.

## Signed release verification

Reviewer: **Codex / POLYGLOT, 2026-10-03**. App deployment [`cf6a5dbb`](https://github.com/RabbiJoshy/Fluency-App/actions/runs/37153088947) and release-site deployment [`ba1e863e`](https://github.com/RabbiJoshy/Fluency-Releases-lyrics/actions/runs/37152884057) completed successfully. `raw/playlists/polyglot-followup-20261003/live-verification.json` records the checks.

| Check | French | Portuguese |
| --- | --- | --- |
| Live complete deck | 2,097 cards / 64 songs | 869 cards / 19 songs |
| Single-song selection | Balance ton quoi: 114 cards | Sozinho: 78 cards |
| Study card flip | Pass | Pass |
| Meaning display | Article readings and multi-meaning menu verified | você → you and source lyric verified |
| Full selection restored | All 64 songs | All 19 songs |
| Exact source spans / freeze / split contract | Pass | Pass |
| Native profile decision coverage | 5,903 / 5,903 | 2,491 / 2,491 |
| Uncached final embeddings | 0 | 0 |

Published catalogs and song membership match packaged artifacts. No knowledge votes were submitted during the interactive checks. Sampled examples can be absent when a card is restricted to a particular song; complete source membership still preserves the correct card, and no substitute lyric is fabricated. Test release sign-off covers these measured contracts and targeted regressions; complete semantic accuracy, full coverage, and sentence translations remain explicitly outside the sign-off.

## Reproduction and publication

From this repository, use `PYTHONPATH=src .venv/bin/python` for pipeline scripts. Source/menus/MWE/cache data reside in the workspace.

- Import French with `scripts/import_polyglot_lyrics.py`, including `--reviewed-prefixes config/lyrics/fr-reviewed-editorial-prefixes.json`.
- Build with `scripts/plant_polyglot_artist.py --workspace ../Fluency-Workspace --config config/lyrics/<fr|pt>-polyglot-v3.json --source <pinned source> --output <new run>`.
- Inspect cache misses. Only approved calls use `scripts/embed_polyglot_artist.py --approved-usd <remaining allowance>`; rebuild under a new ID afterward.
- Package with `scripts/package_polyglot_artist.py --workspace ../Fluency-Workspace --run <complete run> --release-id <new id>`.
- Validate with `scripts/validate_polyglot_artist.py`, using repeated `--candidate LANGUAGE RUN_ID RELEASE_ID` and the Spanish baseline.
- Run `scripts/audit_polyglot_followup.py` for the final review accounting and targeted semantic guards.
- Publish generated data to the lyrics release repository before changing the app catalog. Preserve existing releases; never prune Spanish outputs. Deploy the catalog through the existing app deployment procedure.

Immutable earlier releases remain available for provenance; only the final IDs above should be used for this review.
