# Proposal 0004 — Lyrics mode moves onto the surface ledger

**Status:** Proposal by MEND (2026-09-23) for Joshua to decide; VERSE executes.
Nothing here changes lyrics code. It is the critique and migration asked for in
proposal 0003 §7.

**One line.** Legacy lyrics routing (`src/fluency/lyrics/languages/spanish_routing.py`,
`lyrics/overrides.py`) decides, per run, what each word *is* and hides the
decision in a bucket name. The speech surface ledger records facts once and folds
them into answers at read time. Lyrics should record facts in the ledger's
format, read the same resolver, and keep buckets at most as a view.

---

## 1. What routing does today, in the order it checks

`SpanishRouter.route()` returns the first bucket that matches:

| # | Bucket | Test | What it means |
|---|---|---|---|
| 1 | override's own bucket | typed human override (`lyrics-routing-overrides/v1`) | a person decided |
| 2 | `exclude.noise` | three or more repeated characters | not a word |
| 3 | `exclude.proper_nouns` | Wiktionary lists the form only as a name | a name |
| 4 | `classifier.spoken_particle` | POS is exactly `{intj}` | interjection |
| 5 | `review.proper_noun_candidate` | cap-rate ≥ 0.65, ≥ 3 mid-sentence uses, no or name POS | maybe a name |
| 6 | `exclude.english` | English loanword / English list and not Spanish / fallback | English |
| 7 | `clitic_merge` | imperative, infinitive or gerund host in reverse conjugation; parent = most frequent lemma; reflexive by person | attached clitic |
| 8 | `derivation_map` | diminutive / superlative rules | derived form |
| 9 | `classifier.conjugation` / `normal_vocab` | known form | ordinary word |
| 10 | `classifier.elision` | curated elision skip list | pa', to' |
| 11 | `sense_discovery` | nothing matched | unknown |

## 2. Critique

1. **A verdict and its evidence are the same thing.** A bucket name is both the
   fact ("capitalised 70% of the time") and the policy ("therefore exclude").
   Changing the policy means re-running routing; the fact is not kept. The
   ledger stores the fact as an event and folds policy at read time, which is
   why its reason codes have been inverted at no cost.
2. **First match wins, silently.** A word that is both an interjection and an
   English loan gets whichever test runs first; the other fact is lost. The
   ledger keeps every event and the strictest verdict wins, with reasons.
3. **Exclusion is the only answer for names and English.** `exclude.proper_nouns`
   and `exclude.english` throw away cards an artist deck needs (*Santurce*,
   *Gucci*, English hooks). The resolver has an `entity` strategy and a
   `contamination`/`loanword` class instead: the card stays and explains itself.
4. **`clitic_merge` guesses the parent by frequency.** "The most frequent lemma"
   is exactly the silent choice the speech resolver refuses: `díselo` is
   *decir* or *dar* and the enclitic host rule uses mood (imperative, infinitive,
   gerund) to decide, then abstains if two verbs remain. Routing's reflexive
   check is sound and is kept (the speech rule does the same by person).
   Routing also misses `os` as a clitic, which the speech rule has.
5. **Overrides are typed to routing, not to meaning.** A
   `lyrics-routing-overrides/v1` entry says which *bucket* a word goes in. It
   cannot say what the word means, which dictionary entries its menu comes
   from, or that a name is a brand. The declared-entry format says all of
   that, with the same scoping idea (mode, artist, song) and an explicit trust.
6. **Per-run, not per-language.** Routing recomputes everything per artist run,
   so what one artist taught the system (an elision, an entity) is not
   inherited by the next. The three-store stack (language → artist → live) is
   built for inheritance: a fact written once at the widest true scope serves
   every later artist.

What routing is good for is evidence: its buckets are the list of cases the
ledger model must cover, and it covered them in production.

## 3. Mapping

| Routing | Ledger model (built by MEND) | Status |
|---|---|---|
| typed override | declared entry (`headwords`, `gloss`, `expansion`, `entity`), scoped, curated | **covered** |
| `exclude.noise` | an event (`repeated_characters`) folded to exclude by policy | **add** the observer and reason code |
| `exclude.proper_nouns` | `entity` strategy; entity registry entries; Wikidata fill later (0003 §5) | **covered** (shape); fill later |
| `review.proper_noun_candidate` | `capitalised_in_corpus` event → review | **covered** (speech already has it) |
| `classifier.spoken_particle` | provider headwords (SpanishDict *¡Uy!*) or a declared gloss with class `interjection`/`filler`/`onomatopoeia` | **covered** |
| `exclude.english` | `english_wordlist` + `dictionary_entry_language` events; card kept with class `loanword` or `contamination` | **covered**; policy decides keep vs exclude |
| `clitic_merge` | resolver enclitic host rule (menu from the verb, card keeps its identity) | **covered**; the identity split is decision 0025 |
| `derivation_map` | not yet: a derived-form rule (diminutive → base) as another *derived* headword source | **add** |
| `classifier.conjugation` / `normal_vocab` | provider headwords (page self, declared relation, conjugation table) | **covered** |
| `classifier.elision` | `expansion` entries at lyrics scope (`pa'` → `para`) | **covered** (format); GRAFT fills the list |
| `sense_discovery` | `no_menu` declared with reason, plus the live store's curation queue | **covered** (speech); queue later |

**Drop:** bucket names as stored state; "most frequent lemma" as a clitic
parent; English and proper-noun exclusion as the default; routing-typed
overrides once converted.

**Keep:** the lyrics-specific machinery that is not about what a word is —
elision-restored text for the tagger, Spotify spans, formulaic-line handling —
and routing's reflexive-person check.

## 4. What GRAFT, VERSE and the extra-words UI read instead

- **GRAFT writes** declared entries in `config/declared/<lang>/*.json` (language
  or lyrics scope) and, for one artist, in the artist layer
  (`<workspace>/artists/<lang>/<artist>/declared/`). Kinds: `gloss` (slang,
  fillers, ad-libs; one entry fills an empty menu or competes as an overlay),
  `expansion` (elisions), `entity` (brands, places, people), `headwords`
  (corrections). Every entry carries a `class`.
- **VERSE reads** `fluency.surfaces.resolver.Resolver` with
  `Context(language, mode="lyrics", artist=…, song=…)` over
  `fluency.surfaces.stores.stack(...)`, minimum trust `derived`
  (`config/surfaces/strategy.json`). The resolver gives the headword set and
  the menu is built from it; overlays add competing senses at WSD time
  (`SenseOverlayEntry` converts from a declared gloss).
- **The extra-words UI reads**, per card: `word_class` (the tag), the
  resolution stamp (`strategy`, headword `provenance` and `trust`), the declared
  entry's `class`, and for entities the entity meaning (name, type, one-line
  description). Provisional (heuristic) facts carry `trust: heuristic` so the
  app can mark them (0003 §10.8).

## 5. Migration steps (for VERSE)

1. Convert `lyrics-routing-overrides/v1` entries into declared entries at the
   same scope (a converter script; both kept until VERSE signs off, Invariant 1).
2. Run routing's tests (noise, names, English, particles, clitics, elisions,
   derivations) as observations appended to a lyrics event store in the ledger
   format, instead of as buckets.
3. Add the two missing pieces: the `repeated_characters` observer and a
   derived-form headword source.
4. Build lyrics menus with the resolver (the stage-02 wiring MEND built accepts
   a lyrics profile and scope unchanged).
5. Keep bucket output only as a report view for the audit tooling until it is
   no longer read.
