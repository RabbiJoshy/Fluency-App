# UNISON brief

UNISON is three parts, each its own chat: **UNISON-1** (audit), **UNISON-2**
(one engine), **UNISON-3** (metadata). Each chat opens with:

> This chat is **`UNISON-<n>`**. Read `CHAT_ROADMAP.md` (UNISON row),
> `docs/unison/BRIEF.md` and `docs/unison/PROGRESS.md`. Do only part <n>.

## Rules for every UNISON chat

- **`PROGRESS.md` is the memory, not the conversation.** Update it after every
  unit of work: what was done, decisions Josh approved (date, his words), what is
  next, and what was found but deferred. A new chat resumes from it.
- **The audit sets the scope.** Parts 2 and 3 fix only causes on the fix list in
  `PROGRESS.md`. Anything else found is added to "Found, not on the list" with a
  count and an example, and not worked on.
- **Measure before changing.** The frozen checks (below) run before the first
  change and after every change. A change that lowers any of them is reverted or
  brought to Josh.
- **Stop and report** at the end of each part, and before any harvest, WSD run,
  release build or activation, paid model call, corpus or flag change, or UI
  change. UI changes wait until UNISON is done.
- **Drift check.** For any piece of work, the chat must be able to say which
  audit cause it serves and that the cause is on the fix list.

Frozen checks: lyrics v20 accuracy sample (85.3%), the reflexive gold sets in
`research/reflexives/`, and the audit panel from part 1.

## Part 1: audit (UNISON-1)

The first 300 cards (by rank) of live `es-speech-v23-10000x30-slim` and
`pt-speech-v23-10000x30-slim`, read as a learner sees them. List problems; fix
nothing.

Outputs:

1. `docs/unison/audit-300.jsonl`: one line per problem, with `language`, `rank`,
   `word`, `card_id`, `shows` (the row or example as displayed), `should`,
   `cause` (a short code, e.g. `reflexive_slip`, `progressive_as_lexical`,
   `archaic_gloss`), `layer` (`menu`, `features`, `wsd`, `selection`,
   `display`), and the sentence ids involved.
2. `docs/unison/AUDIT.md`: causes ranked by cards affected, each with its layer,
   two named examples (the card, what it shows, what it should), and a rough
   fix cost. The problems already known are seeded in the roadmap row.
3. The audit panel: every audited example sentence with its correct sense,
   labelled by the chat, frozen under `research/unison/gold/`. This is the
   accuracy check for parts 2 and 3.
4. Stop. Josh picks the fix list; it is recorded in `PROGRESS.md`.

## Part 2: one engine (UNISON-2)

Speech, lyrics and TURBO run one `fluency.wsd`; SpanishDict and Wiktionary feed
it through one feature contract. Scope as in the roadmap row (abstaining
features, three translation states, per-combination calibration, stale-engine
check, decision 0025), plus the fix-list causes in the `wsd` and `features`
layers.

Outputs:

1. Lyrics and TURBO profiles that `extend` the speech profile; the scoring copy
   in `scripts/plant_artist_v20.py` retired behind an adapter.
2. Per-example evidence: each assigned example records which features scored
   and which abstained.
3. A calibration table per evidence combination.
4. The stale-engine check: a command listing live releases built on an older
   engine than the current profile.
5. Decision 0025 written up (adopt or reject), with its measured effect.
6. Candidate releases (es and pt speech, es lyrics) built, **not activated**,
   with before/after on the frozen checks and on the named audit cards.
7. Stop. Josh decides activation.

## Part 3: metadata (UNISON-3)

How sense metadata is grouped, tagged and used, per provider, and the
fix-list causes in the `menu` and `display` layers.

Outputs:

1. A decision record (`docs/decisions/`): a table of every metadata field and
   feature family per provider, saying whether it is a sense or a label, whether
   it may group rows, whether WSD reads it, and whether the card shows it.
   Example: a SpanishDict context is a sense and groups; a Wiktionary
   "intransitive" or topic is a label and never groups.
2. Adapter and feature changes so the card and WSD read the same contract and
   agree on what tells two senses apart (*falar* "to talk" + *com* / + *de*).
3. Before/after on the 300 audited cards for each metadata cause.
4. A list of UI questions handed back to Josh for after UNISON.
5. Stop.
