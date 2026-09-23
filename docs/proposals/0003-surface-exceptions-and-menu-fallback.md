# Proposal 0003 — Surface exceptions and the menu-fallback layer

**Status:** Settled with Joshua (2026-09-23). This is **MEND**'s design; its
prompt is in `CHAT_ROADMAP.md` under *MEND*. §10 records the decisions MEND
works to. Changes from here go through Joshua.

**One-line summary.** Some surfaces reach a release with no sense menu.
Today that is a dead end: the card ships empty and the app drops it. This
proposal makes it a routed case. A fact about the surface (from the ledger, or
from lyrics routing) picks a *strategy* that supplies meanings
deterministically, from local data, without waiting on a scrape. Hand work is
reduced to a few small declared lists, and those lists are scoped so a new
artist can borrow what earlier artists already paid for.

---

## 1. What prompted this

The live release `es-speech-v15-10000x10` has **105 cards whose `meanings` is
empty** and whose WSD status is `no_menu` on every example (`ud`: 80/80).
WSD is not at fault. It only chooses among menu senses (stage 02), and these
menus are empty. The app counted those cards as "new" on the setup page, the
deck builder dropped them, and Learn New bounced between sets. That is patched
in the app, but the data should not ship this way.

GLASS reported "0 empty study sets". That was true and still missed this: a set
with 19 good cards and 1 empty one is not empty. **Acceptance for this work is
per card, not per set.**

### The 105, by what is actually wrong

| Class | Count | Examples (rank) | Likely cause | Evidence so far |
|---|---:|---|---|---|
| Attached clitics | ~70 | decírtelo (1163), cógelo (4280), dígaselo (5342), vayámonos (6594), quédatelo (6096), concéntrate (3099) | SpanishDict files the verb, not each enclitic bundle, so the exact surface has no page | `resolve_clitic_lemmas.py` already writes lemmas to the ledger (72 surfaces). But the SpanishDict menu adapter never reads ledger lemmas (`BUILD_STATUS.md`, "Known and open": *external_lemmas is wired into the Kaikki adapter only*). 55/70 resolve with the app's 434-verb drill table alone; the rest are verbs outside it. |
| Ordinary words | 23 | suponiendo (9995), conduces (9958), comprendí (9945), veían (9992), castigar (9985), bares (7583), fantasías (7739) | Not SpanishDict. 16 of the 23 sit at ranks 9,870–10,000. | The refetch ran (3,319 surfaces, **97.5% answered** → ~83 unanswered). The fetch script treats an empty response as a blip to retry, and runs in rank order. **Hypothesis:** the empties are the end of that run (rate limiting), and nobody reran it. Check the refetch JSONL. `bares` and `fantasías` may instead be the plural-conflict filter. |
| Abbreviations | 4 | ud (323), sra (427), srta (564), uds (985) | `_abbreviation_mismatch` in `sense_menu/spanishdict.py` drops any headword containing "." when the surface has none. SpanishDict likely answers `Ud.`, `Sra.` | Not yet confirmed against the pinned snapshot. |
| Interjections / sounds | 6 | uh (864), je (3980), uy, bum, aló, tai | Mixed. **The GRAFT dossier found sampled `je` lines are French and `uh` is English subtitle filler.** So some are source contamination, not Spanish words. | uy, aló, bum look like genuine Spanish. tai is unknown; read its lines. |
| Proper nouns / foreign | 2 | ferrari (9954), off (9932) | No dictionary entry expected | "off" is used in Spanish (*voz en off*). |

The counts come from the release rows plus a quick analyser run in this chat.
They are a starting table for MEND to verify, not a measurement to cite.

---

## 2. The core idea: facts → class → strategy

The ledger already folds **facts** (append-only events) into **verdicts**
(keep / review / exclude) at read time (`surfaces/policy.py`). This adds a
second, parallel fold. For a surface whose provider menu is empty, the facts
pick a **menu strategy**.

```
facts (events.jsonl)  ──fold──►  verdict   (keep / review / exclude)     exists today
                      ──fold──►  strategy  (how a missing menu is filled)  new
```

Like verdicts, strategies are policy, not history. Changing how a class is
handled edits a table and re-materialises; it never rewrites events. And like
the verdict fold, it is one engine used by every provider (Invariant 4): the
SpanishDict and Kaikki adapters both call the same resolver.

### Surface classes and their strategies

| Class | Detected by (fact / route) | Strategy | WSD? | Hand work |
|---|---|---|---|---|
| **Ordinary** | provider menu present | provider menu | yes | none |
| **Inflection** (conduces, suponiendo) | conjugation_reverse / `lemma_resolved` | `lemma_hop`: the lemma's menu | yes, among senses already embedded for the lemma's own card | none |
| **Attached clitic** (decírtelo) | clitic resolver, verified against conjugation tables | `lemma_hop` to the verb. When the clitic is reflexive (te + tú imperative, nos + nosotros, se + infinitive/usted), **also** the pronominal headword (quedarse, llevarse) | yes; WSD picks quedar vs quedarse per sentence | abstentions only (díselo → decir \| dar) |
| **Abbreviation / elision** (ud, sra; lyrics: pa', to', e') | `abbreviation_form` fact; lyrics elision routing | `expand`: a declared expansion (ud → usted, pa' → para), then look that up | only if the expansion is polysemous | the expansion list (small, shared) |
| **Interjection / filler** (uy, aló, bum; lyrics: yeh, brr) | `lexical_interjection` / `classifier.spoken_particle` | `declared_gloss`: a hand-written single sense | **no**: one declared sense needs no choice | the gloss list |
| **Source contamination** (je as French, uh as English) | foreign-line evidence (`foreign_frequency_list`, `english_wordlist`, line language) | exclude, or fix at source quality | no | none (policy) |
| **Proper noun / entity** (ferrari, Gucci, Santurce) | `wiktionary_name_only`, `capitalised_in_corpus`, `review.proper_noun_candidate` | `entity` (§5): speech defaults to exclude, artist defaults to an entity card | no | optional; borrowable (§5) |
| **Loanword** (off) | `english_loanword` + evidence of Spanish use | `declared_gloss` or exclude, per scope | no | a few entries |
| **Slang / regional sense** (guagua, corillo) | GRAFT evidence | overlay: an **extra** sense that competes in WSD (§6) | yes | GRAFT's lists |
| **Unresolved** | none of the above | declared `no_menu` (Invariant 2) | no | queue for review |

Precedence is fixed, never implicit (an idea worth keeping from `lyrics/overrides.py`):
1. a scoped human override;
2. the provider menu for the exact surface;
3. the class strategy;
4. declared `no_menu`.

Every resolved sense records the strategy that produced it.

**Cheaper, not just more complete.** `declared_gloss` and `entity` skip WSD
entirely. `lemma_hop` reuses glosses that are already embedded for the
lemma's own card, so it adds no gloss spend; only the new sentences are scored.
The honest limit: an attached clitic still goes through WSD when its verb has
several senses. What disappears is the dead end, not the choice.

---

## 3. Coverage: menu / absent / unfetched

Invariant 2 says absence is declared, never inferred. "We never asked" and
"we asked and there is nothing" are different facts, even when the fallback
treats them the same.

| State | Meaning | Source of the fact |
|---|---|---|
| `menu` | the provider gave senses | snapshot |
| `absent` | queried; the provider has no entry | refetch row that is empty after retries, or `spelling_substitution` / `entry_lang_not_spanish` flags |
| `unfetched` | never queried, or only blips | surface missing from the snapshot and the refetch logs |

- **Coverage is a declared property of each provider.** Kaikki is a complete
  dump: not in the dump means `absent` for that edition. SpanishDict is a
  fetched cache: not in the cache means `unfetched`.
- **The fallback runs identically for `absent` and `unfetched`.** An
  `unfetched` surface also joins a fetch queue. When a later fetch returns a
  real menu, the provider menu wins on the next build, and the strategy stamp
  makes the swap traceable.
- **Design constraint for live and artist use:** every strategy runs offline,
  on local data (conjugation tables, saved lemma menus, declared lists, an
  entity snapshot). No network call sits in the resolution path. Fetching is
  always a background upgrade. A user loading a new playlist never waits on
  SpanishDict. (In the live tier, §4, a fetch result arrives as ordinary
  provider data and replaces heuristic guesses for that word on next load.) Pre-fetching the top ~50k later just shrinks the fallback's
  share.

---

## 4. Three stores, one format, read as a stack

There are three kinds of work, and they need different amounts of certainty:
- **Speech releases** are curated and slow to change.
- **Artists Joshua runs by hand** are curated per artist and inherit speech.
- **Playlists a user uploads live** must answer in seconds, grow quickly, and
  may be wrong.

**These are three stores**, each kept where it belongs and sized for its job:

| Store | Holds | Lives in | Size | Maintained by |
|---|---|---|---|---|
| Language ledger (exists today, one per language) | speech facts and language-wide declarations | `raw/surfaces/<lang>/` in the workspace | bounded, ~10k surfaces | pipeline chats |
| Artist layer | only what differs for that artist | beside the language ledger, per artist | a few hundred entries | Joshua, when running an artist by hand |
| Live store | heuristic facts from users' playlists | a database on SETLIST's server, never a JSON file | unbounded; grows with users | itself; Joshua works only the curation queue |

What they share is **one event format and one resolver**. The resolver reads
them **as a stack**: language, then artist, then live. It filters by scope and
by minimum trust, and the narrowest scope wins. So a new kind of exception
(entities, elisions…) is added once, not three times. Every fact and every
declared entry (expansion, gloss, entity, override) carries two labels.

**Scope: where it applies.** This borrows the scoping idea from
`src/fluency/lyrics/overrides.py`, not its format. An empty
scope means "all", and two matching entries at the same scope are an error,
never a silent precedence.

```
es                                  ud → usted · uy → "oops, ouch" · Gucci → entity
 └ es / lyrics                      pa' → para · to' → todo · yeh → ad-lib
    └ es / lyrics / artist:bad-bunny   Benito → entity (the artist)
       └ … / song                   a one-off reading
 └ es / live / playlist:<id>        whatever a live playlist met first
```

**Trust: how it was established.**

| Trust | Established by | Examples | Where it can appear |
|---|---|---|---|
| `curated` | a person reviewed it (`human_review`, `adjudicated_*`, hand-written entries) | ud → usted; Gucci → brand | everywhere |
| `derived` | a deterministic rule that verified its own answer and abstains on ambiguity | clitic resolver (decírtelo → decir); a gated Wikidata entity fill | everywhere; stamped with the rule and its evidence |
| `heuristic` | a cheap live guess with no verification beyond the rule itself | a capitalised unknown word guessed as a name; an unverified elision expansion; an ungated entity match | live playlists only, shown as provisional in the app |

**Each consumer declares a minimum trust:**

| Consumer | Accepts | Scopes read |
|---|---|---|
| Speech release | curated, derived | language, speech |
| Hand-run artist release | curated, derived | language, lyrics, that artist, its songs |
| Live playlist | curated, derived, **heuristic** | everything above, plus that playlist |

This is how an artist, or a user, inherits from the layers before it. Most
of what a new artist or playlist meets is already answered at a broader scope
and a higher trust. The narrow scopes hold only what is genuinely new.

**Heuristic facts are shared across users, not kept per playlist.** They are
facts about words, not about people, so they hold no user data. If many users'
playlists produce the same heuristic guess (the same unknown entity, the same
unexpanded elision), that count is the signal of which gaps matter.
**Promotion** is the only way a fact moves up a trust level:

```
heuristic ──(recurs across playlists; reaches the curation queue)──► person reviews ──► curated
heuristic ──(a deterministic rule later verifies it)──────────────► derived
```

Promotion appends a new event at the higher trust level. It never edits the
heuristic one, so the history of what was guessed and what was confirmed
survives (Invariant 3: nothing is recorded as verified until it is). A
promotion can also widen the scope: an entity guessed in one playlist and
confirmed becomes language-scoped, and every later artist and playlist gets it
for free.

**Why trust is a label and not just "which store".** A single store can mix
trust levels. A hand-run artist layer holds both entries Joshua reviewed
(`curated`) and entries a rule derived (`derived`). The label keeps them
distinguishable wherever they sit, and promotion copies a fact up the stack
(live → language) as a new event at the higher trust.

**MEND builds the two labels and the trust gate in the resolver, and nothing
else of the live tier.** Every fact MEND writes is curated or derived. The
live tier's heuristics, storage (SETLIST's worker is the likely home), sharing
and curation queue are later work that plugs into the same fields.

---

## 5. Entities: proper nouns as a strategy, not an exclusion

Speech excludes proper nouns today (`exclude.proper_nouns` via
`wiktionary_name_only` in lyrics routing; policy in speech). For artist mode
that throws away useful cards. Knowing what *Santurce*, *Gucci* or a named
person is often matters for understanding a Bad Bunny line. Proposal: `entity`
becomes a strategy with its own card shape, off by default in speech and on by
default in artist mode.

**What an entity card shows.** The name, a type (brand, place, person, work,
event), and a one-line description ("Italian sports-car maker"; "neighbourhood
of San Juan, Puerto Rico"). No senses, no WSD, no translation. The app renders
it as a reference card; that is a later UI job.

**Where the description comes from, in order:**
1. **Declared entity registry** (hand-written, scoped as in §4). This is the
   borrowable asset. An entity written for one artist is written at language
   scope when it is not artist-specific, so the next artist gets it for free.
2. **Deterministic fill from Wikidata/Wikipedia**, from a pinned offline
   snapshot, never a live call. Accept only when all of these hold:
   - the surface has name evidence (`wiktionary_name_only`, high mid-sentence
     capitalisation, or `review.proper_noun_candidate`);
   - an exact label or alias match in es or en;
   - the candidate's type is on a whitelist (company/brand, human, city,
     country, neighbourhood, musical work, sports team…);
   - one candidate clearly dominates (for example by sitelink count), or the
     artist's scope tags break the tie (a Puerto Rico / music domain prefers the
     PR place or the reggaeton artist).

   Anything that fails a gate goes to review. The Wikidata id is stored with
   the entry, so the fill is reproducible and auditable. A gated fill is
   `derived` trust (§4). In the live tier, a looser match with fewer gates may
   be shown as `heuristic`, marked provisional, and enter the curation queue.
3. Otherwise, exclude, or `review` in artist scope.

**Ambiguity is the real risk.** *Mercedes* (name, car), *Paris* (city, person),
*Santos* (saints, surname, team). The gates prefer abstaining. An entity card
that is wrong is worse than none, the same rule the clitic resolver follows.

**Relationship to SpanishDict.** SpanishDict sometimes has ordinary senses for
a capitalised word (*Mercedes* → "mercy"). When the provider menu exists and
the surface also has entity evidence, the entity can compete in WSD like an
overlay sense (§6) instead of replacing the menu. That is a later refinement;
the first cut handles menu-less entities only.

---

## 6. How MEND and GRAFT fit together

There are two ways declared data reaches a card. Both use the same entry
format and the same scopes.

| | **Fallback** (MEND) | **Overlay** (GRAFT) |
|---|---|---|
| When | the provider menu is **empty** | the provider menu exists but **lacks a sense** |
| Where | sense-menu stage (02) | WSD, after constraints, before scoring (`fluency.wsd.overlays`) |
| Effect | **fills** the menu | **adds** a candidate that competes |
| Examples | uy → "oops", ud → usted, decírtelo → decir's menu | oye → "hey", venga → "come on", guagua → "bus" |

**MEND builds the mechanism; GRAFT supplies most of the content.** MEND
defines:
- the class → strategy table;
- the scope field and precedence;
- the declared-entry format for glosses, expansions and entities (compatible
  with `SenseOverlayEntry`, so one entry can serve as a fallback on an empty
  menu or as an overlay on a full one);
- the entity registry shape.

MEND seeds each list only with what the 105 need. GRAFT then fills those same
lists: slang, fillers, elisions, lyrics entities. It does not invent a second
format. GRAFT's dossier already found the first speech overlay candidates
(*oye*, *venga*, the *hostia* family), and they slot straight in as overlay
entries.

Order: **MEND → GRAFT → VERSE.** VERSE inherits the resolver, the lemma hop
and the scopes, and lyrics has far more attached clitics, elisions and entities
than speech.

---

## 7. Artist mode: the speech ledger leads, lyrics routing is legacy

**The speech surface ledger is the mature system. Lyrics routing is not the
model.** `src/fluency/lyrics/languages/spanish_routing.py` and its data
structures date from the first version of the app. They were shaped around the
UI of that time, and Joshua is not attached to them. GRAFT and VERSE are
expected to consume something different from what lyrics mode reads today.
After VERSE, new UI will change how learners meet "extra" words (fillers,
slang, entities, ad-libs). So MEND is a pivotal chat. It designs the layer
lyrics will move onto, and it is **allowed to question the current lyrics
structure** wherever the ledger model does better.

What lyrics routing is still good for: **evidence of which cases exist**, not
a design to inherit. It already had to handle:
- proper nouns: `exclude.proper_nouns`, `review.proper_noun_candidate`;
- interjections: `classifier.spoken_particle`;
- English: `exclude.english`;
- repeated-character noise;
- diminutive/derivation rules;
- clitic merging, guarded to imperative, infinitive and gerund hosts, tracking
  reflexive person (`clitic_merge`);
- typed, scoped human overrides (`lyrics/overrides.py`).

Each of those is a test case the new layer must cover. How lyrics expresses
them (bucket names, route objects, what the UI reads) is open to replacement.

| Piece | Speech today (the base) | Lyrics today (legacy) | Direction |
|---|---|---|---|
| Surface facts | append-only ledger events, folded at read time | routing buckets computed per run | ledger events for both; buckets become at most a view |
| Missing-menu handling | ships empty | `no_menu` for unresolved routes | the strategy table, shared |
| Clitics | own card; no menu when SpanishDict has no page | merged into the parent | speech: lemma hop now; the split is decided on its merits at the next rebuild (§8) |
| Proper nouns | excluded or review | excluded or review | `entity` strategy, scoped |
| Human decisions | `adjudicated_*` events | `lyrics-routing-overrides/v1` | one scoped, trust-labelled format |
| Per-artist data | — | per-song/artist override scope | the artist layer (§4) |

**What MEND delivers for lyrics:** not a mapping that keeps routing alive, but
a short **critique and migration proposal**. It lists:
- which routing behaviours the ledger model already covers;
- which it must add;
- which should be dropped;
- what GRAFT and VERSE should read instead;
- what the post-VERSE "extra words" UI will need from the data (a class, a
  strategy stamp, a trust level, an entity shape).

Joshua decides; VERSE executes.

---

## 8. Attached clitics: fallback now, split later

Joshua's proposal: treat `decírtelo` as `decir te lo`, merging frequency,
examples and menus into the simpler surface.

- **Precedent.** French already does this (Decision 0005 splits imperative
  clitic groups). Legacy lyrics routing does it too (`clitic_merge`), which shows it is workable, not that it is right. Spanish
  speech chose the opposite in Decision 0014 and
  `config/languages/es/tokenization.json` (`preserve_surface`,
  `may_replace_surface_card: false`).
- **Unconditional, not "only when there is no menu".** If the merge depended
  on menu coverage, a card's identity would flip as more of SpanishDict was
  fetched, moving learners' progress. It would also be inconsistent (decírtelo
  merged, decirte not). So: split every verified clitic form, or none.
- **Merge into the bare surface, not the lemma.** cógelo → *coge*, dígaselo →
  *diga*. Folding *coge* into *coger* is the separate lemma merge Fast Track
  already offers.
- **Why not now.** It changes stage 01 (tokenization → frequencies → ranks),
  which needs a re-harvest (a SCAR-level decision), full WSD and a progress
  migration for ~900 speech cards (Invariant 1: preserve the substance, label
  both). That is a full-rebuild job.
- **Plan.** MEND's lemma hop fixes the empty cards now without touching
  identity. The split becomes a decision record proposed for the next full
  Spanish rebuild. VERSE already works this way. The fallback must not assume
  the split, so it still catches whatever the split leaves.

---

## 9. Invariant check

| Invariant | How this respects it |
|---|---|
| 1. Migrate the shape, preserve the substance, label both | No card identity changes in MEND. The later clitic split needs an explicit progress migration. |
| 2. Absence is declared | `absent` vs `unfetched`; declared `no_menu` for leftovers; every filled sense stamped with its strategy. |
| 3. A run must not record what it did not verify | Every fact carries a trust level. Releases accept only curated and derived facts. Heuristic guesses stay labelled heuristic until promotion appends a verified event. The resolver and entity fill abstain on ambiguity. |
| 4. Adapters absorb irregularity; the engine exists once | One resolver for both providers. Lyrics buckets map onto the same classes, not a second engine. |
| 5. Added by creating files | A new class is a fact plus a table row plus declared data files, never code lists. |

---

## 10. Decisions MEND works to

Settled 2026-09-23 by adopting the proposed defaults. Joshua can overturn any
of them; MEND flags anything the evidence argues against rather than quietly
deviating.

| # | Question | Decision | Needed by |
|---|---|---|---|
| 1 | Entity cards in speech? | Excluded by default in speech; `entity` is on by default for artist scope | MEND (speech default only) |
| 2 | Wikidata source | A pinned, filtered offline subset; type whitelist settled when artist entities are built | later |
| 3 | Interjections in speech | Genuine Spanish ones (uy, aló, bum, if confirmed) get a `declared_gloss` in all modes. Contamination (je, uh) is excluded. | MEND |
| 4 | Where the strategy table lives | A second fold beside the verdict fold in `surfaces/policy.py` (or a sibling module if that file would sprawl) | MEND |
| 5 | Lyrics routing | Legacy, not the model. MEND writes a critique and migration proposal (§7): what the ledger covers, what to add, what to drop, what GRAFT, VERSE and the post-VERSE extra-words UI should read. Joshua decides; VERSE executes. | MEND (proposal only) |
| 6 | Clitic split | A next-rebuild decision, argued on its merits (legacy `clitic_merge` is evidence, not the model). MEND drafts the decision record only | MEND (draft only) |
| 7 | Live store and sharing | SETLIST's server; word-level facts shared across users; curation threshold set when built | later |
| 8 | Provisional meanings in the app | A subtle marker on the card | later (UI) |
| 9 | Home of declared entries | Small hand-written lists in `config/` (in git, reviewed); large generated snapshots (Wikidata subset) in the workspace | MEND |

---

## 11. MEND at a glance

- **Deliverable:** the fallback layer (§2–§3), the scope and trust labels
  with a minimum-trust gate in the resolver (§4), the entity strategy shape (§5),
  the declared-entry format shared with GRAFT (§6), proved on the 105.
- **Code:** a shared resolver; `external_lemmas` for SpanishDict (parity); the
  reflexive headword rule; the abbreviation filter fix; coverage states per
  provider.
- **Data:** diagnose the refetch empties and rerun the tail; seed the declared
  lists with only what the 105 need.
- **Release:** new sense-menu run; WSD for affected cards only (reusing
  QUARRY's prewsd v2 and KILN 2's Stage 04); a candidate release; per-card
  acceptance (0 empty meanings); a diff against v15 limited to the affected
  cards. No activation without Joshua.
- **Not in MEND:** the clitic tokenization split (drafted as a decision
  proposal only); attaching clitic forms to verb cards (`clitic_memberships`);
  any artist's actual layer; the live tier's heuristics, storage, sharing and
  curation queue; GRAFT's content.
