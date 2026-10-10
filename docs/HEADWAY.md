# HEADWAY — Spanish/Portuguese source lemma audit, 2026-10-10

Source/import fixes, previewed ledger corrections and targeted WSD are complete.
Final candidate decks are built, validated, published and reviewed in staging. Production remains unchanged.
App merging, kept-apart cards and titles remain SEAM's responsibility.

## Evidence and preview

Full evidence is under `../Fluency-Workspace/raw/surfaces/headway/`:

- `es-preview.json` and `es-preview.tsv`: the original before/after preview.
- `es-confirmed-preview.json` and `es-confirmed-preview.tsv`: the amended preview; unverified residual candidates
  do not become lookup lemmas. Both previews were written before their respective
  ledger revisions. The first observations remain in the append-only history.
- `pt-preview.json` and `pt-preview.tsv`: the Portuguese before/after preview.
- `*-ledger-before.json`: original ledgers, including every supply field.
- `fresh-menu-sample.json`: nine real cards regenerated in memory from the pinned
  dictionaries; hay/hacerlo, vamos/és, conta/contar, ser/ir and the phrase/case
  boundaries passed. These are audit outputs, not candidate decks.
- `verification-and-impact.json`: exact affected card/analysis/sense IDs, assignment
  counts, source hashes and affected release row-shard paths.

The first preview corrected 105 Spanish and 4,521 Portuguese surfaces. Subsequent
Spanish previews and the final totals are recorded below. The initial preview unresolved
queue had **51 distinct Spanish surfaces (60 issue records)** and **134 Portuguese
surfaces**; final counts are recorded below. A surface can receive a supported phrase removal while another part
of its analysis remains unresolved. Retained unverified candidates are explicitly
marked and cannot populate `lemmas` or the primary lookup lemma.

Examples:

| Surface / analysis | Before | Corrected analysis / preserved distinction |
|---|---|---|
| es hay, verb | self headword hay | haber; original hay definitions and IDs retained |
| es hacerlo, verb | self headword hacerlo | hacer; original meanings, IDs and attached lo retained |
| es pentágono | alternate el Pentágono | phrase excluded from word lemma set; original provider evidence retained |
| pt vamos, verb | self headword vamos | ir, retaining the specialised auxiliary definition; vamos interjections remain independent |
| pt és | primary é plus ser and self és | primary ser; noun plural of é also retained; unsupported self removed |
| pt conta | contar plus conta | both retained; noun conta and verb contar remain different |
| pt foi / fui | multiple real analyses | ser and ir retained; interjection row retained, no sentence-level choice invented |

`buenas`, `obstante` and several self-titled enclitic entries do not get a guessed
primary after phrase removal. Missing relations and alternative-form chains stay
in the unresolved queue. Spanish `porfavor` / `por favor` remains unresolved;
written-apart spelling equivalents are not silently stripped by the Spanish adapter.

## What was wrong and why earlier cleanup appeared to regress

1. `observe_lemmas.py` read every SpanishDict `dictionary_analyses.headword` as a
   lemma, ignoring explicit `possible_results` morphology. Its Spanish snapshot
   was hardcoded to September v3, while v23's profile pins September v7. Both
   snapshots contain the hay/hacerlo self titles, so updating the snapshot alone
   would not fix these examples.
2. Wiktionary observation counted every dump entry as a headword, including entries
   whose senses consist entirely of form-of links. It also created lowercased
   aliases of uppercase entries. Thus a correct form-of lemma coexisted with a
   spurious independent surface lemma.
3. Follow-up verification found a specific stale-materialisation gap: the saved
   pre-HEADWAY ledger declares 32,727 observations. The original log has 32,889;
   its final 162 events are exactly the earlier Spanish clitic-dephrased batch,
   at zero-based indices 32,727–32,888. None of that batch was folded into this
   saved ledger; only 6 of its 162 primary values happen to agree through other
   observations. This establishes an incomplete rollout in the current artifact,
   not a reverted correction rule. Whether another ledger version incorporated
   the batch earlier is unverified. See `earlier-cleanup-rollout-gap.json`.
   The old script also covered only single-token clitic entries whose senses
   were all PHRASE, not VERB-labelled hay/hacerlo or general Wiktionary forms.
   Materialisation additionally accumulated old/new lemma claims without
   superseding bad analyses, leaving unsafe alternates. The unrolled 162-entry
   batch needs its own supported/ambiguous preview; do not blindly replay its
   old single-candidate choices or overwrite frozen artifacts.
4. MEND's resolver was rolled out only to explicit surface lists. v23's Spanish
   profile carries menus from `20260914T223348Z-c35194bc`; Portuguese carries from
   `20260914T222723Z-e43a0469`. hay, hacerlo, vamos and és are outside those resolver
   lists. Consequently most menus remained unchanged despite newer adapter code.
5. `11276edc` fixed the release index's lemma column, and `d3992be5` fixed the app's
   citation selection. These are later presentation safeguards, not repairs to
   the ledger or immutable menus. The app config still points to the v23 decks
   built on October 4. There is no evidence here of a browser-cache regression
   or of either later presentation fix being reverted.

## Underlying fixes and verification

SpanishDict now reparents VERB senses only when the page declares one unambiguous
verbal relation. Original titles, sense IDs, source references, inflection text
and attached pronouns remain evidence. Noun homographs and ambiguous relations
are preserved. This applies both to retained normalised menus and resolver-built
menus; source entry availability uses the same corrected page analyses.

Wiktionary imports distinguish semantic senses from form/alternative links even
when tags are incomplete. A specialised verb sense on a form page follows the
unique same-row verb lemma; other POS rows remain distinct. Exact original entry
spelling prevents uppercase name entries becoming lowercase surface headwords.
Phrase headwords are excluded from word menus/declarations; MWE inventories,
overlays and raw provider snapshots remain intact. Explanatory pseudo-headwords
such as “verb combined with …” are excluded word keys, not newly invented MWEs.

The observer now uses semantic headwords and the shared SpanishDict rule. Spanish
observation requires an explicit pinned snapshot, Portuguese an explicit pinned
dump. Reviewed complete analysis sets supersede title-only observations at read
time, retaining all original events. A later legacy import cannot resurrect a
superseded analysis. A carried-menu build fails with the exact surfaces to include
in its new profile if it would reuse superseded source analyses; curated declared
entries remain protected.

Initial verification: **193 tests passed, 34 subtests passed** across sense-menu, surface and index-shard
checks, including ten HEADWAY regressions. All 4,626 changed surfaces were checked
for unchanged supply, verdict, rank, reason codes and tags; all untouched rows were
byte-equivalent as parsed records. Original event bytes remain an unchanged prefix.
Pinned dictionary hashes match. Replaying the latest revisions produces the same
lemma fields. No frozen run or existing release was rewritten.

## Targeted rollout and SEAM handoff

Josh authorised completion through staging, including necessary targeted WSD,
and approved a combined embedding spend of up to US$1. Production promotion
remains unapproved. No harvests or broad multilingual rebuilds were started.

The final ledgers differ on **293 Spanish / 4,521 Portuguese surfaces**. Spanish
POS changed only on 195 explicitly reviewed source-backed verbal cases. Rank,
identity, verdict, tags and every sentence-supply field remain unchanged.
Existing manual headword sets for atrevo, bares and fantasías were restored;
manual observations now take precedence over later source imports.

A final conflict preview (`es-conflict-reviewed-preview.json`) corrects comete
→ cometer and piense → pensar. Explicit source verb relationships take precedence
over coincidental accent-stripped clitic splits; the rejected pronoun parsing is
retained as rejected evidence and removed from active morphology metadata.

The earlier 162-event batch was re-adjudicated against saved source evidence,
not blindly replayed: 150 are fully supported and corrected; 12 retain unresolved readings. Later previews cover clitic-host corrections, rejected
neighbour-page fallbacks and person/mood-labelled grammatical entries. See
`es-clitic-preview.json`, `es-fallback-clitic-preview.json` and
`es-person-reviewed-preview.json`. All were written before applying their data.
`es-final-preview.json` is idempotent: zero additional supported changes.
`final-unresolved.json` preserves 79 Spanish / 142 Portuguese surfaces with
remaining unresolved issues, including partial readings on otherwise corrected
surfaces. This is not a claim that every PHRASE label is wrong or eliminated.

New immutable candidates use the existing named es-10k-speech/pt-10k-speech
pools and September -v2 freezes. Only **174 Spanish / 977 Portuguese menus**
change; 9,826 / 9,023 menus carry verbatim. Every changed card receives fresh
WSD on its existing frozen occurrences. Unchanged assignments carry with explicit
source-run provenance; no guessed ID mapping masquerades as new WSD.

| Language | Candidate run | Candidate release |
|---|---|---|
| es | 20261010T153100Z-7f63c198 | es-speech-v24-headway-r4-10000x30-slim |
| pt | 20261010T161908Z-63f07fe8 | pt-speech-v24-headway-r2-10000x30-slim |

Intermediate Spanish r1/r2/r3 runs remain immutable audit candidates, superseded
by r4; Portuguese r1 is superseded by r2. Only the final pair is intended for staging review. Conjugation display
continues to use Wiktionary alone. SpanishDict tables only establish source lemmas.

Fresh WSD: es 4,810 assigned / 7 abstained / 79 no-menu / 2,996 capped;
pt 27,985 assigned / 903 abstained / 349 no-menu / 17,726 capped. These are processing statuses,
not accuracy scores. No-menu Spanish cases buenas/obstante remain explicit review
limitations; their removed phrase keys are not silently reinstated as lemmas.
The MWE inventories and overlays remain in the existing MWE path.
1,222 missing embeddings were created (290 es / 932 pt, 49,964 input UTF-8 bytes);
the final r4 pass reused all 4,333 vectors. Expected published-rate embedding
charge is below US$0.01; exact invoiced cost is not available locally.

Verification: 549 Python tests plus 177 subtests passed; the app deployment suite passed.
`final-ledger-verification.json` verifies preserved supply/identity and pinned
input hashes; `final-history-verification.json` verifies the original event bytes
remain an unchanged prefix and reviewed lemma sets replay correctly. Menu previews, embedding previews, fresh bundles and splice reports
in the HEADWAY evidence folder identify exact affected cards and assignments.

SEAM owns final merging, kept-apart cards and display. Existing merging policy is
unchanged. Each candidate gets its own Merge Lemmas file generated by the existing
builder, and staging candidate selection loads it alongside the same candidate's
study structure. Review ser/ir, saber/ser, conta/contar, noun homographs,
interjections, specialised commands and genuine expressions. Both candidates retain all 10,000 surface/card IDs and ranks from v23. No SEAM chat was found in the available chat list;
this document is the concrete handoff. SEAM should not compensate for unresolved source cases by
changing merging policy.

Staging publication/review status: Spanish r4 is published and browser-reviewed on
staging app commit f51cb60e. Portuguese r2 is published (release-site commit
69a565b6) and browser-reviewed on the newer staging app 04321919. Its normal
study route shows verb és → ser (“you are”) and separately noun és → é, with
the unsupported noun ser removed. `staging-pt-r2-es.png` is the final screenshot;
old r1 screenshots are historical evidence only. Hosted columns, study structure,
Merge Lemmas and selected card shards match validated local bytes.
The newer staging app already supports candidate selection; HEADWAY did not
redeploy or replace other chats’ staging changes. Review the final pair at
https://fluency-staging.pages.dev/?esRelease=es-speech-v24-headway-r4-10000x30-slim&ptRelease=pt-speech-v24-headway-r2-10000x30-slim .
Default staging and production deck choices have not been activated.
Production pointers, production storage and active releases remain unchanged.
Other-language findings (Czech navěky and older cs/fi/fr rollout gaps) are recorded
in the roadmap for later CONVOY work; no parity work was performed.

## Local resource use

The old Stage 04 importer decoded the entire 2.1 GB Spanish assignment bundle
and kept every validated assignment in memory. This was internal validation and
publication of existing WSD results, not a dictionary import or harvest.
The HEADWAY path now streams that same JSON format, spools validated records to
disk and preserves the complete identity, source, projection and coverage checks.
The release builder indexes assignment and sentence offsets, decoding one card's
assignments and caching at most 256 sentences. Completed Portuguese output is
reused. Heavy steps run serially at low process priority.

Final Spanish import completed in 32.08 seconds, with 1,392,852,992 bytes maximum
resident memory and zero swaps reported by macOS. Seven focused regression tests
cover identical assignment/method/report bytes, identical full deck selection,
both provider/MWE projections, malformed input, stale sources, wrong models,
duplicate/missing rows, cache eviction and Unicode sentence boundaries.


## Further source defect found in staging

The r1 Portuguese review showed noun `ser` (“being”) on the verb surface `és`.
Wiktionary’s raw surface rows specify verb → ser and noun → é. The ledger
analysis already preserved that distinction, but the menu adapter seeded ledger
lookup lemmas with unrestricted POS. That seed overrode the narrower dictionary
form-of edge, importing all POS of the base word. This is source/menu ingestion,
not a reason to change app merging policy.

`pt-form-pos-preview.json` records current analyses, proposed exclusions and raw
source evidence for 1,106 analyses on 934 surfaces. Complete graph verification
confirmed those exclusions; no additional indirect POS path licenses them.
The importer now applies existing source POS constraints to ledger lookup hops,
unioning multiple genuine direct or indirect relations and retaining unknown
external first hops without inventing a POS. Carrying a source menu now checks
those same complete graph constraints and refuses an incomplete rollout.
This accounts for the final 977 changed menus, including the earlier corrections.
No additional ledger headword or POS edits were necessary.

Eight surfaces have no supported semantic menu after the exclusions: lha, lho,
ma, mo, mos, pouca, poucas and vários. `pt-r2-no-menu-review.json` records the
349 affected occurrences; they were added to the explicit unresolved queue
(142 Portuguese surfaces). No unrelated POS is imported to fill the gap.

The same seeding path is provider-generic; CONVOY should audit existing cs/fi/fr
menus when that work resumes. No other-language counts or parity fixes are claimed.

The r1 staging review also reported v23 cognate card verdicts being ignored for
new releases, and unavailable coverage JSON. Before promotion, SEAM/release
review must refresh or explicitly omit release-bound `cognates/es/cognates.json`
and `cognates/pt/cognates.json`, and check staging delivery of
`coverage/es/coverage.json` and `coverage/pt/coverage.json`. Source analyses must
not be changed to work around these app-asset issues.

The bounded-memory release path now serializes canonical deck/index/example
JSON in chunks and releases loaded inputs before composition. Regression checks
compare every published byte with the original composition path, including
republication and immutable-release validation.

Final Portuguese r2 import took 89.11 seconds with about 2.1 GB maximum resident
memory; packaging took 205.28 seconds with about 4.4 GB maximum resident memory.
Both reported zero swaps. Final objects and validation still use substantial memory;
these changes reduce the avoidable full-file copies rather than guaranteeing a
small-memory build. All heavy processing is complete.

## Final SEAM review limitations

On staging 04321919, a cold Find a word search for és opens an examples-only
card and omits its meanings. Loading level 2, set 126–150 through normal study
and navigating to card 21 shows the correct verb meaning and noun companion.
The search jump still omits meanings even after set loading. This reproduces an
app loading/display boundary issue; supported meanings are present in the hosted
row shard. `staging-pt-r2-search-missing-meanings.png` and
`final-staging-review.json` record the exact observation. SEAM should verify and
fix search hydration without changing source analyses or merging policy.
The cognate/coverage warnings above remain pre-promotion review items.

Final app checks: 234 tests passed. The source/release code is committed as
1a83f788, locally; no app redeploy or production push was performed for that
checkpoint. Other chats’ uncommitted app edits were left untouched.
