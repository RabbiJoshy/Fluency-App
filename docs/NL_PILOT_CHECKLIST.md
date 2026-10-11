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

## Pilot-blocking order and progress (2026-10-11)

Pilot run: `runs/nl/speech/20261011T225109Z-9d9612c4`, profile
`config/pipelines/nl/speech/pilot-4000.json`.

1. **Word list → SUBTLEX-NL. Done.** Snapshot `raw/frequency/subtlex-nl-cd2`
   (licence and download URL unrecorded, labelled in `snapshot.json`); adapter
   `src/fluency/inventory/subtlex.py` splits `_` units back into words (they had
   removed `orde` to a sixth of its share), joins 4,916 full-stop tokens (`ben.`) and
   repairs 209 apostrophe stand-ins. Policy `nl-v2`. `'t` 58, `m'n` 79, `'n` 81,
   `z'n` 125 are now cards; `z` fell from 136 to 4,516.
2. **Apostrophe matching. Done.** Matcher no longer finds `'s` inside `auto's`;
   harvest policy `nl-v2` scores `'t 'n 's 'm 'k` as words.
3. **Menus. Done at 91%** (3,641/4,000, snapshot `enwiktionary-2026-09-09-nl`,
   unchanged). Open: `m'n` has no menu (needs a declared entry); er/daar/hier/waar +
   preposition words (`ermee`, `daarmee`, `ervoor`, `daarna`) have none; and
   **capitalized Dutch vocabulary has none** (`amerikaanse`, `franse`, `engeland`,
   `londen`, about 40 cards) because the menu join requires case to match and
   Wiktionary files these capitalized.
4. **Harvest. Done.** 157,142 sentences, 186,061 candidate matches; 6 shortfalls,
   all OCR junk.
5. **OCR damage (capital I read as l).** `lk ls ln lets ledereen lemand fbl cla ltalië
   lsland lndia` excluded (`lk` by policy, the rest by ledger adjudication). Only 35
   of 157,142 harvested sentences contain such a token; the list, not the corpus, is
   the problem.
6. **Ledger lemmas. Cause found and fixed:** `observe_lemmas.py` had never been run
   for Dutch. Now 3,662/4,000 (91.5%) resolved.
7. **Review queue. Adjudicated:** 338 capitalized surfaces: 56 keep (countries,
   nationalities, `god`, interjections), 246 personal names + 46 English fragments
   and foreign place names excluded, same rule as fi/es/pt.
8. **Eligible sentences. Cause found:** the cleaning stage
   (`scripts/condition_pools.py`, local LaBSE alignment) had never run for Dutch.
9. **Still open before the pilot:** pin and install a Dutch POS model (download
   needs Josh's approval); re-run the inventory so exclusions free their ranks;
   curated function-word menus; a hand-labelled benchmark including separable verbs
   (B) and er-splits (C).
