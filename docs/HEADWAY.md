# HEADWAY — Spanish/Portuguese source lemma audit, 2026-10-10

Source/import fixes, previewed ledger corrections and targeted WSD are complete.
New candidate decks are being validated for staging. Production remains unchanged.
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
Spanish previews and the final totals are recorded below. The unresolved
queue has **51 distinct Spanish surfaces (60 issue records)** and **134 Portuguese
surfaces**. A surface can receive a supported phrase removal while another part
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
`final-unresolved.json` preserves 79 Spanish / 134 Portuguese surfaces with
remaining unresolved issues, including partial readings on otherwise corrected
surfaces. This is not a claim that every PHRASE label is wrong or eliminated.

New immutable candidates use the existing named es-10k-speech/pt-10k-speech
pools and September -v2 freezes. Only **174 Spanish / 59 Portuguese menus**
change; 9,826 / 9,941 menus carry verbatim. Every changed card receives fresh
WSD on its existing frozen occurrences. Unchanged assignments carry with explicit
source-run provenance; no guessed ID mapping masquerades as new WSD.

| Language | Candidate run | Candidate release |
|---|---|---|
| es | 20261010T153100Z-7f63c198 | es-speech-v24-headway-r4-10000x30-slim |
| pt | 20261010T143757Z-d76750c7 | pt-speech-v24-headway-10000x30-slim |

Intermediate Spanish r1/r2/r3 runs remain immutable audit candidates, superseded
by r4. Only the final pair is intended for staging review. Conjugation display
continues to use Wiktionary alone. SpanishDict tables only establish source lemmas.

Fresh WSD: es 4,810 assigned / 7 abstained / 79 no-menu / 2,996 capped;
pt 1,688 assigned / 70 abstained / 940 capped. These are processing statuses,
not accuracy scores. No-menu Spanish cases buenas/obstante remain explicit review
limitations; their removed phrase keys are not silently reinstated as lemmas.
The MWE inventories and overlays remain in the existing MWE path.
454 missing embeddings were created (290 es / 164 pt, 18,884 input UTF-8 bytes);
the final r4 pass reused all 4,333 vectors. Expected published-rate embedding
charge is below US$0.01; exact invoiced cost is not available locally.

Verification: 467 Python tests plus 80 subtests, and 233 app tests passed.
`final-ledger-verification.json` verifies preserved supply/identity and pinned
input hashes; `final-history-verification.json` verifies the original event bytes
remain an unchanged prefix and reviewed lemma sets replay correctly. Menu previews, embedding previews, fresh bundles and splice reports
in the HEADWAY evidence folder identify exact affected cards and assignments.

SEAM owns final merging, kept-apart cards and display. Existing merging policy is
unchanged. Each candidate gets its own Merge Lemmas file generated by the existing
builder, and staging candidate selection loads it alongside the same candidate's
study structure. Review ser/ir, saber/ser, conta/contar, noun homographs,
interjections, specialised commands and genuine expressions. All 10,000 Portuguese surface/card IDs and ranks match v23; Spanish is checked
when its candidate is complete. No SEAM chat was found in the available chat list;
this document is the concrete handoff. SEAM should not compensate for unresolved source cases by
changing merging policy.

Staging publication/review status: pending final artifact checks and deployment.
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
