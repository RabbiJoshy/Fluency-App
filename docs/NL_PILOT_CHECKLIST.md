# Dutch pilot checklist (ROLLCALL-1)

Status of Dutch against every item in `docs/LANGUAGE_ONBOARDING.md`, audited
2026-10-11 with no runs or spend. Dutch is the CASCADE-WSD pilot language and its
menu is locked to English Wiktionary (Kaikki). Pilot size: 3,000–4,000 surfaces.

Legend: **done** · **partial** · **missing**. *Pilot?* says whether the item blocks
the CASCADE-WSD pilot (yes) or only a public Dutch release (release).

## 1. Shared language setup

| Item | Status | Evidence / gap | Pilot? | Size |
|---|---|---|---|---|
| Language identity (code, name, locale, flag, speech locale) | done | `app/config/config.json` `dutch`: `nl-NL`, flag, route `nl` | – | – |
| App presentation (theme, links, capabilities, release paths) | partial | reference links present; `hasData: false`, no release/study/capability paths | release | S |
| Surface adapter (Unicode, case, apostrophe, hyphen, diacritics) | done | `src/fluency/languages/dutch/surfaces.py`: NFC, apostrophe/hyphen kept inside words, diacritics preserved | – | – |
| Token/boundary rules | **partial** | `config/harvest/languages/nl-v1.json` token pattern keeps `auto's`, `z'n`, but cannot start with an apostrophe, so `'t`, `'n`, `'s` never form a token. See Dutch-specific issue A | yes | M |
| Pipeline profile | partial | `config/pipelines/nl/speech/v1-2000x5-3.json` (2,000) and `scale-3000.json`; no profile at the 3–4k pilot size with current settings | yes | S |

## 2. Speech inputs

| Item | Status | Evidence / gap | Pilot? | Size |
|---|---|---|---|---|
| Frequency list snapshot + adapter | **partial** | FrequencyWords OpenSubtitles 2018 nl 50k. **The list has had every apostrophe removed** (0 lines contain one), producing fake cards. See issue A. SUBTLEX-NL (in `../Fluency`, unused) may not have this defect; unchecked | yes | M |
| Inventory policy (names, abbreviations, noise, leakage) | **partial** | `config/inventory/languages/nl-v1.json` excludes only `n t s m mr`. Still kept: `z` (132), `lk` (416, subtitle OCR for `ik`), `r` (1118), `d` (1272), English `i`/`a`/`to`/`he` | yes | S–M |
| Dictionary snapshot | done | `enwiktionary-2026-09-09-nl`; 1,899/2,000 menus, 6,825 senses | – | – |
| Surface→headword route, explicit `no_menu` | done | 101 cards explicit `no_menu` | – | – |
| Menu metadata policy (region, register, grammar, construction, domain, redirects) | partial | `config/sense_menu/languages/nl-v1.json` `audit_status: partial` | release | M |
| Tatoeba + OpenSubtitles snapshots | done | `raw/tatoeba`, `raw/opensubtitles/opensubtitles-v2018-en-nl-2016plus` | – | – |
| Harvest policy | done | `nl-v1`: apostrophes and hyphens never rejected | – | – |
| Sentence bank | done (2k) | run `20260926T171858Z-f7b6aa3f`: 78,194 sentences, 0 shortfalls. Needs a new run at pilot size | yes | S (minutes, $0) |
| Sentence pools | missing | no `pools/nl`; the run's bank is sufficient | no | – |
| Model pins (POS/parser) | **missing** | no Dutch entry in `config/nlp/models.json`; no Dutch spaCy package installed | yes | S |
| WSD language profile | **missing** | profile names `nl-v1`, but `config/wsd/languages/nl-v1.json` and `config/wsd/closed-class/nl.json` do not exist | yes | part of CASCADE-WSD |

## 3. Mandatory human audit

| Item | Status | Evidence / gap | Pilot? | Size |
|---|---|---|---|---|
| Surface ledger | partial | 2,000 rows, 1,878 keep / 122 review (all `capitalised_in_corpus`: `god`, `john`, `dr`, `new`) | yes | S |
| Ledger lemmas | **missing** | all 1,878 keep rows have `lemma: null`; examples document has 0 rows. Cause unknown | yes | S–M |
| Per-surface review queue | missing | `reviews/nl/20260926T171858Z-f7b6aa3f/manual-review.jsonl`: 0/2,000 decided | release | L (1–2 days) |
| Curated function-word menus | **missing** | `config/declared/nl/onboarding-review.json` has 0 entries. Candidates: `de het een er te om op aan zich` | yes | M |
| Cognate calibration | missing | `cognate-review.jsonl`: 0/248 decided | release | S–M |

## 4. Selection and publication policy

Recorded in the profile (source shares 60/40 Tatoeba/subtitles, WSD budget 60/30,
display 5/3). WSD scoring and commit rule are `blocked_pending_benchmark`, which is
exactly what CASCADE-WSD replaces. Benchmark labels: **missing**, a few hundred
hand-labelled items (M, about a day). Pilot: yes.

## 5. Optional quality layers

| Item | Status |
|---|---|
| Declared entries (contractions, slang, fillers) | missing (0 entries) |
| Conjugations | missing; no `raw/conjugations/nl`; Kaikki path is the candidate |
| Cognates | partial: `config/cognates/nl-en.json`, `app/cognates/nl` present; calibration open |
| MWE overlay | missing; no `config/mwe/nl-*` |
| Lexical relations | missing; no `raw/lexical-relations/nl` |
| Reflexive tagger (`zich`) | missing; es/pt only |

None of these block the pilot.

## 6–7. Artist mode

Out of scope: no Dutch Lyrics adapter, corpus or routing exists.

## Dutch-specific issues (the counterparts of French elision)

**A. Apostrophe words are missing or broken.** Spoken Dutch is full of them: `'t`
(het), `'n` (een), `'s` (des / 's morgens), `z'n` (zijn), `m'n` (mijn), `d'r` (haar),
`zo'n`, plurals like `auto's`. The frequency list removed every apostrophe, so
`z'n` was counted as `z` + `n`, and `zo'n` inflated `zo` (rank 38). The result is junk
cards (`z`, `r`, `d`) and no cards for the real forms. Fix: expand or redirect them
in a Dutch contraction table (French has `languages/french/contractions.py`),
recount from a list that keeps apostrophes, and let the harvest token pattern start a
word with an apostrophe. Size M. Blocks the pilot because these words are among the
most frequent.

**B. Separable verbs.** `ik bel je morgen op` (opbellen): `op` is a verb particle,
not the preposition. `op` (18), `aan` (32), `uit` (59), `mee` (104), `af` (142) are
top-150 cards whose sentences mix both uses. This is a closed-class routing problem
like LITERAL-GROUND's prepositions, and the cascade's router needs to handle it. Size
M, inside CASCADE-WSD.

**C. Split `er`/`daar` + preposition.** `ik heb er niet aan gedacht`. Same family as B;
`er` is rank 20. Inside CASCADE-WSD.

**D. Subtitle OCR damage.** `lk` for `ik` (rank 416). Probably more l/I swaps; sweep
the inventory once. Size S.

## State handed to CASCADE-WSD (2026-10-12)

**Pilot run: `runs/nl/speech/20261012T135827Z-bbb7d8cb`** (profile
`config/pipelines/nl/speech/pilot-6000.json`). Superseded and not to be used:
`20261011T225109Z-9d9612c4` (4,000), `20261012T082613Z-a8c7ba30` (adjudication pass),
`20261012T135749Z-d4921938` (duplicate inventory; see its `SUPERSEDED.txt`).

| | Value |
|---|---|
| Word list | SUBTLEX-NL (`raw/frequency/subtlex-nl-cd2`; licence and URL unrecorded, labelled), adapter `subtlex-surface-frequency/v1`, policy `nl-v2` |
| Ledger | 6,637 rows: 5,958 keep / 679 exclude / **0 review**; supply complete |
| Usable cards in the run | 5,952 of 6,000 (48 excluded in the last review pass; a next run refills them) |
| Lemmas | 5,955 (97.8%), Wiktionary `enwiktionary-2026-09-09`, 72 via title-case licence |
| Menus | 5,859/6,000 (97.7%), policy `nl-v2` |
| Sentences | 244,864 candidates; 203,859 distinct eligible after LaBSE cleaning (floor 0.3, shared default); 7 cards under 10 eligible |
| POS model | `stanza-nl-default@1.14.0` pinned in `config/nlp/models.json` (installed, 303 MB) |

What was fixed on the way:

1. **Word list.** FrequencyWords had removed every apostrophe (`z'n` counted as
   `z` + `n`). SUBTLEX-NL keeps them: `'t` 58, `m'n` 79, `'n` 81, `z'n` 125. The
   adapter splits SUBTLEX's `_` units back into words (they had taken `orde` to a
   sixth of its share), joins full-stop tokens (`ben.`), repairs apostrophe stand-ins.
2. **Matcher.** `'s` was found inside `auto's`, `'n` inside `z'n`; fixed for every
   language.
3. **Capitalized vocabulary.** Exact-case matching stays the rule; the ledger
   licenses a title-case Wiktionary entry per word where no exact entry exists
   (`amerikaanse` -> "American", "a female American"; `engeland`, `londen`).
4. **Pronominal adverbs** keep their own gloss (`ermee` "with it", `daarna`
   "afterwards") instead of redirecting to the preposition.
5. **`m'n`** reaches `mijn` "my" (menu policy `nl-v2`: pronoun may redirect to
   determiner).
6. **OCR damage** (capital I read as l): `lk ls ln lets ledereen lemand fbl cla
   ltalië lsland lndia ltaliaanse ltaliaans lrak lerse` excluded. Only 35 of 157,142
   harvested sentences carried such a token in the 4,000 run: the list, not the
   corpus, was damaged.
7. **Review.** 759 capitalized surfaces adjudicated by the fi/es/pt rule: keep
   countries, nationality and language words, Dutch exonyms, religious words,
   interjections; exclude personal names, English fragments, foreign place names,
   letters. Events carry observer `dutch-pilot-review/2026-10-1x`.
8. **Never-run steps.** `observe_lemmas.py` and `condition_pools.py` had never run
   for Dutch; that was the "no lemmas, empty examples" gap.

## Open, in order (none blocks starting CASCADE-WSD design)

1. **141 no-menu cards:** about 40 English/foreign (`ok`, `hey`, `sir`) and 30 tail
   names already excluded by review; about 28 inflected forms whose redirect fails
   (`anderen`, `meeste`, `schitterende`, partitive `persoonlijks`), likely the same
   part-of-speech mismatch as `m'n`; 5 stress-accent spellings (`eén`, `zó`, `vóór`,
   `écht`) that should redirect; about 30 colloquial words needing declared entries
   (`da's`, `ofzo`, `dankjewel`, `asjeblieft`).
2. **Curated function-word menus** (Spanish `el`/`la` model) for about 10-20 words:
   `de het een er te om op aan`.
3. **Hand-labelled benchmark**, a few hundred sentences, deliberately including
   separable verbs (B) and er-splits (C). Stanza already separates them:
   `ik bel je op` gives `op` `compound:prt`; `op de tafel` gives `op` `case`.
4. **Stale alternates:** the event log still holds the pre-fix `ermee -> met`
   observations; they survive only as labelled alternates the menu does not follow.
5. **Licence of SUBTLEX-NL** before any public release.
6. Release-only items in the tables above (manual review queue, cognates, app wiring).
