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
| Cognates | wired 2026-10-19: `app/cognates/nl/cognates.json` rebuilt for `nl-speech-cascade-proto2-6000x10`, memory tips on; 0.80 cutoff not recalibrated for this deck |
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

**Pilot run: `runs/nl/speech/20261012T175838Z-76d34ee3`** (profile
`config/pipelines/nl/speech/pilot-6000.json`). Earlier runs carry a
`SUPERSEDED.txt` and are not to be used.

| | Value |
|---|---|
| Word list | SUBTLEX-NL (`raw/frequency/subtlex-nl-cd2`; licence and URL unrecorded, labelled), adapter `subtlex-surface-frequency/v1`, policy `nl-v2` |
| Ledger | **complete**: 5,997 cards keep, 0 review; 719 surfaces excluded in total |
| Usable cards | 5,997 of 6,000 (`evan`, `rio`, `l` excluded in the last pass) |
| Menus | every kept card has one (5,998/6,000; the two without are excluded) |
| Lemmas | 98.8%, Wiktionary `enwiktionary-2026-09-09` |
| Declared entries | 80 in `config/declared/nl/onboarding-review.json`, applied by the profile's resolver |
| Sentences | 244,967 candidates; 203,689 eligible after LaBSE cleaning (floor 0.3, shared default); 0 shortfalls; 4 cards under 10 eligible |
| POS model | `stanza-nl-default@1.14.0` pinned (installed, 303 MB) |

How the surface ledger was used to settle all 6,000 words:

1. **Word list.** FrequencyWords had removed every apostrophe; SUBTLEX-NL keeps
   them (`'t` 58, `m'n` 79, `'n` 81, `z'n` 125). The adapter splits `_` units back
   into words, joins full-stop tokens, repairs apostrophe stand-ins.
2. **Exclusions (721), all recorded as ledger events with a reason and a
   `category` (proper_name 550, english 92, foreign_place 38, ocr_damage 16,
   letter 9, abbreviation 7, foreign_word 6, subtitle_credit 2,
   tokenization_damage 1). Review keeps carry one too (country_or_nationality,
   exonym, religious, interjection, vocabulary). Kinds: personal names,
   English and foreign words, foreign place names, isolated letters, OCR damage
   (capital I read as l: `lk ls ln lets ledereen lemand ltalië lrak lerse ...`),
   tokenization damage (`datje`), subtitle credits. Rule as fi/es/pt: keep countries,
   nationality and language words, Dutch exonyms, religious words, interjections.
3. **Lookup fixes in code (provider-level):** title-case Wiktionary entries read only
   where the ledger licenses them (`amerikaanse` -> "American"); pronominal adverbs
   keep their own gloss (`ermee` "with it"); `m'n` reaches `mijn` (menu policy
   `nl-v2`); a declared headword is no longer narrowed by the dictionary's own
   redirect (`anderen` -> `ander` "other"); matcher no longer finds `'s` inside `auto's`.
4. **Per-word declarations (80)** for the 141 cards that still had no menu:
   inflections Wiktionary lists only in its tables (`schitterende` -> schitterend,
   `persoonlijks` -> persoonlijk, `misdaan` -> misdoen); stress spellings (`eén`,
   `zó`, `écht`) as expansions; solid spellings of phrases (`dankjewel` "thank you
   very much", `hoelang` "how long"); phrase fragments (`ziens` in *tot ziens*, `se`
   in *per se*); colloquial words and loanwords with hand-written glosses
   (`da's` "that's", `goddank`, `gin`); `ok`/`okay`/`okee` -> `oké`.
5. **Never-run steps** for Dutch (`observe_lemmas.py`, `condition_pools.py`) now run.
6. **Ledger completeness** now counts only ranked cards; rows left from the
   FrequencyWords list (`sms`) are not cards.

## Open, in order (none blocks starting CASCADE-WSD)

1. **What CASCADE-WSD has to answer (Josh, 2026-10-12).** Not "what to do about
   function words" but, in this order:
   - **Do cheap embeddings work** for the middle tier?
   - **When to raise to an LLM**: what signal says a sentence is too hard for them?
   - **Which words systematically cause WSD trouble.** Found from the data (per-word
     error and escalation rates on the benchmark), not assumed. Likely, but not
     necessarily, function words and clitics.
   - **For those words, a presentation decision:** (a) a new kind of card
     presentation instead of WSD, so no LLM at all; or (b) a new presentation, with
     the LLM kept only for the hardest cases. Two older ideas feed in and are not
     adopted: the onboarding doc's small curated menus (Spanish `el`/`la`), and the
     declared function-word class in the CHAT_ROADMAP TURBO-STREAM row.
   - Why it matters: offline the per-card cap makes these words small (33 common
     Dutch function words x 10 = 330 of 60,000 WSD units); in Turbo every
     occurrence counts, and those 33 words are 37% of running tokens in SUBTLEX-NL.
2. **Hand-labelled benchmark**: a few hundred real sentences with the correct menu
   sense marked by hand, used only to score the cascade. Built so per-word trouble is
   measurable: enough sentences per suspected word, and keep the suspected words in
   rather than removing them first. Deliberately include hard cases: separable verbs (B) and er-splits (C). Stanza already separates them:
   `ik bel je op` gives `op` `compound:prt`; `op de tafel` gives `op` `case`.
3. **Glosses written by hand** (about 30 in the declarations) are Claude's, labelled
   `author: Claude`; review them with the cards.
4. **Stale alternates:** pre-fix `ermee -> met` observations survive only as labelled
   alternates the menu does not follow.
5. **Licence of SUBTLEX-NL** before any public release.
6. Release-only items in the tables above (manual review queue, cognates, app wiring).
