# Chat roadmap

Repo `Fluency-Next`. Workspace `../Fluency-Workspace`. Old `../Fluency` is read-only.

This file is the **switchboard**: what is open, which chat owns it, and the
rules every chat follows. It is not a diary. The campaign history (NEEDLE →
MIRROR, every card, brief and paste) is archived at
`docs/archive/chat-roadmap-2026-10-04.md`. Read it only when a task names an
old codename.

**Every named chat opens with:**

> This chat is **`<CODENAME>`**. Read `CHAT_ROADMAP.md`, then only your row.
> (UNISON chats are `UNISON-1`, `-2`, `-3`; their row points to their brief.)
> Do not do another chat's job.

A chat that is not named here (UI polish, a bug) does not need a row. It must
not start a harvest, WSD run or release from a settings tweak.

After editing, copy this file to `../Fluency-Workspace/raw/surfaces/DECK_CHAT_ROADMAP.md`.

## Open

Everything open is listed here. If it is not in this table, it is either
done (below) or an eventual direction (`LATER.md`). Do not start work from
anywhere else.

| Codename | Job | Status | Read |
|---|---|---|---|
| **TURBO** | Live Spanish pipeline for a user-uploaded Spotify playlist: clean, normalise, tag and run fast WSD in the client/worker, then build a study deck immediately. Must not block the UI thread or break card progress. | **In progress** (`app/turbo/`). The last big piece of the app. Powered by the unified WSD decision logic and asset profile `config/wsd/models/es-turbo-v1.json`. Playlist ingest, worker and UI work continue. | `docs/runbooks/live-playlist.md` (SETLIST, which it builds on) |
| **MIRROR-CS** | Extend the reflexive/pronominal tagger (`src/fluency/reflexive/`) to Czech: 999 of 10,000 cs cards have both a plain and a *se*/*si* meaning. A research chat, not a port: Czech *se*/*si* are second-position clitics with one form for every person, so the person-agreement method behind ~99% in es/pt does not carry over. Needs a Czech parser (Stanza or UDPipe; **ask Josh before downloading**) and new hand-labelled Czech gold sets. No other language is worth extending to (fr deck too small, no pl deck, nl unpublished). | Not started. | `research/reflexives/FINDINGS.md`; reuse the eval harness in `research/reflexives/` |
| **TERSE-2** | Shorten over-long sense contexts and glosses on the card back. Portuguese (and every Wiktionary-provider language) shows Kaikki definitions word for word; e.g. pt *não*: "isn't · used to ask whether a person agrees with the proposition, rather than to ask for an unknown fact". There is no hand-written menu layer for pt. Decide the approach (length policy in the sense-menu adapter, a curated override file, or a model-shortened field with provenance) — provider-agnostic, and labelled per invariant 1 so the original text is kept. | Not started. Raised by Josh 2026-10-05. Versioned as TERSE-2 to prevent history confusion. | `config/sense_menu/providers/wiktionary-v1.json`; `docs/NOMENCLATURE.md` (provider, context) |
| **ACCORDION** | Design pass on whether to show rarer uses & nuances inline via an accordion on the mobile card back vs keeping them off-card in the existing modal (`#rareUsesModal`). Core motivation: hiding rare senses prevents learner confusion, avoids cluttering the card with unimportant meanings, and shields against inaccurate rare WSD assignments. Mobile space is heavily constrained by the active example sentence and Anki grading bar. A pure-UI scale wireframe mockup was produced comparing both: [rarer_uses_accordion_mockup.html](file:///Users/joshuathomasamar/.gemini/antigravity/brain/13564ff2-f373-41a9-881a-9d7c5bfb8bcf/rarer_uses_accordion_mockup.html). Dedicated follow-up chat to decide and implement if approved. | Not started. Wireframe drafted 2026-10-09. | `app/js/flashcards.js` (`renderSections`, `#rareUsesModal`); `app/css/style.css` (`.meanings-scroll`, `.meaning-row`); [Mockup](file:///Users/joshuathomasamar/.gemini/antigravity/brain/13564ff2-f373-41a9-881a-9d7c5bfb8bcf/rarer_uses_accordion_mockup.html) |
| **DUTCH** | Ship the Dutch 2,000-card speech release: review the 122 ledger surfaces, finish the readiness checklist, activate. | Not started. Candidate `nl-speech-v1-2000x5-3-candidate` exists, inactive. | `docs/NL_FI_2000_RELEASE.md` → Dutch; `docs/LANGUAGE_COMPLETION_CANDIDATE.md` |

## Live today (2026-10-04)

| Mode | Release |
|---|---|
| Speech es, pt | `*-speech-v23-10000x30-slim` (reflexive-aware WSD, Wiktionary conjugations) |
| Speech cs | `cs-speech-v21-10000x30-slim` |
| Speech fi | `fi-speech-v21-2000x30-slim` |
| Speech fr | `fr-speech-v7-dual-metadata-v5-20260918` |
| Lyrics es | v20 (Bad Bunny, test playlist); Rosalía and Young Miko carried from v18 |
| Artist fr, pt | Polyglot test releases |

Conjugations come wholly from Wiktionary in every language (verbecc and Jehle
removed, 2026-10-04).

## Done

Treated as finished. Each could be improved; reopening one means giving it a
new row above, not editing this list.

| Codename | What it delivered |
|---|---|
| UNISON | Three-part unification campaign (UNISON-1 audit of 300 es/pt cards, UNISON-2 unified engine & profiles across speech/lyrics/TURBO, UNISON-3 metadata contract decision 0030, Kaikki parity & deployed speech releases). |
| NEEDLE, FUSE, SIEVE, MILL, SWEEP | v13–v15 speech WSD algorithm and the MWE overlay |
| QUARRY, CHISEL 1–2, KILN 1–2, GLASS | 10k supply, MWE curation, 10k speech decks |
| MEND | The word-database structure: surface facts, scopes, trust tiers, shared resolver |
| GRAFT, VERSE, CHORUS | Lyrics overlays and lyrics WSD v16–v18. Lyrics v20 builds its menus through the shared resolver (proposal 0004's menu step) |
| POLYGLOT | Artist mode across languages; French and Portuguese test releases |
| SETLIST | Spotify playlist → LRCLIB → naive study deck |
| GLEAN | MWE re-harvest for Merge Lemmas (decision 0028) |
| KINDRED | Cognates for any language pair; `learner-align/v1` scorer (decision 0027) |
| DRAWER | Conjugation tables and their English glosses |
| INFLECT | Conjugated verb rows read as natural English (pass 1 `46ef386b`, pass 2 `e0b5c1c2`): no spurious commands, imperfect as simple past, English spelling, bracket-aware clauses; Spanish *-se* rows and agreeing participles inflect; the conjugation table finds *-se* forms. Attached object pronouns (*verte* → "to see you") were left to the companion-card work |
| MIRROR | Speech v23 (es, pt): reflexive tagging as a WSD filter; Wiktionary-only conjugations. Keep `research/reflexives/` (eval harness + gold sets): it is how any change to the tagger is re-checked |
| — | Function words (*lo*, *de*, *que*): curated sense grouping in the app, not WSD |
| — | Smaller levels and sets (100-card levels, 25-card sets) |
| — | Release hosting split per language (decision 0026); the old combined `Fluency-Releases` repo was pruned to a README and archived on 2026-10-04 |

## Rules for every pipeline chat

These exist because of **SCAR**: the v12 production run rewrote the 10k ledgers,
re-harvested when pools existed, and did not pin the artifacts that chose its
sentences. Full account in the archive.

| If you are… | You must… |
|---|---|
| Materialising a deck smaller than the language inventory | `--supply-only` |
| Starting a production run | `--run-id` on an **existing named pool** (`fluency pools list`) |
| Auditing WSD quality | Read **that run's** `stages/04_wsd_assignments/` and its frozen `prewsd/<run-id>/`, not the live app or a ledger another session touched |
| Unsure whether to harvest | **Do not harvest.** Use the freeze already on disk. |

- `--language` defaults to `fr` in the CLI. Pass it every time.
- Audits grow a sample and sign off a **new** version file; plant chats run that
  version. Do not overwrite a previous profile; old profiles are release provenance.
- Provider ≠ language. Parity means SpanishDict **and** Wiktionary.
- Absence is declared. A run does not record what it did not verify.
- `git status` before committing; stage only your paths.
- Long briefs live beside the data (`../Fluency-Workspace/raw/surfaces/…`). This file only points.
