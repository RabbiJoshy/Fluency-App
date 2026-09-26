# Candidate: Language Completion Gaps

Status: candidate audit, 2026-09-26.

This document lists the observed work still needed to finish Spanish, French,
Dutch, Italian and Finnish. It compares the repository with the adjacent
`Fluency-Workspace`. A file being present counts as **present**, not necessarily
as audited or production-ready. Internal WSD and classifier design is out of
scope, but an invalid, copied or blocked execution profile is still listed as a
release blocker.

## Status key

- **Ready**: source, policy, output and product wiring are present.
- **Partial**: useful work exists, but it is not finish-ready.
- **Missing**: no usable object was found.
- **Optional**: not required for the first Speech release.

## Summary

| Area | Spanish | French | Dutch | Italian | Finnish |
|---|---|---|---|---|---|
| Language/surface adapter | Ready | Ready | Ready | Ready | Missing |
| App language entry | Ready | Ready | Partial | Partial | Missing |
| Speech pipeline profile | Ready | Partial | Partial | Missing | Missing |
| Frequency source and policy | Ready | Ready | Ready | Missing | Missing |
| Dictionary/menu source | Ready | Ready | Ready | Missing | Missing |
| Menu metadata policy | Ready | Ready | Partial | Scaffold only | Missing |
| Tatoeba snapshot | Ready | Ready | Ready | Missing | Missing |
| OpenSubtitles snapshot | Ready | Ready | Ready | Missing | Missing |
| Surface ledger | Ready | Missing | Missing | Missing | Missing |
| English cognate policy/output | Ready | Partial: app file missing | Ready but unwired | Missing | Missing |
| Conjugations | Ready | Ready | Missing | Missing | Missing |
| Lexical relations | Ready | Ready | Missing | Missing | Missing |
| Production Speech release | Ready | Partial/older release | Missing | Missing | Missing |
| Fresh Artist pipeline | Ready | Missing | Missing | Missing | Missing |

## Cross-language completion rule

A language is considered finished only when all of the following are true:

- [ ] Its external snapshots are pinned with source, licence, attribution and hashes.
- [ ] Its language policies are audited rather than copied or left as scaffolds.
- [ ] Its inventory, menu, examples and declarations have been folded into a surface ledger.
- [ ] Every top-3,000 surface has a recorded human verdict; no review queue remains open.
- [ ] Function words and deterministic declared entries have curated menus and are not
  treated as ordinary lexical sense-selection cases.
- [ ] A full target-size Speech run has produced and validated an immutable release.
- [ ] The app entry points at that release and declares only capabilities actually shipped.
- [ ] Its English cognate layer is generated, calibrated, copied into the app and enabled.
- [ ] Optional layers are either shipped or explicitly declared absent.
- [ ] Artist mode is enabled only after a native Lyrics adapter and real artist corpus exist.

## Mandatory manual gate

For each language, a reviewer must read the first 3,000 surfaces in rank order and
inspect examples wherever the classification is unclear. The pass must explicitly find:

- English or other foreign-language leakage, names, credits and tokenization damage.
- Interjections, fillers, onomatopoeia, abbreviations, slang and genuine loanwords.
- Incorrect headwords, parts of speech, translations, duplicated senses and menu gaps.
- Common grammatical/function words whose raw dictionary menu is not a useful learner
  choice. These receive a small hand-curated menu, as Spanish `el` and `la` do.

Each item must end as keep, exclude, class tag, headword override, expansion, entity,
hand-written one-sense menu, hand-written function-word menu, or an approved provider
menu. Decisions must be versioned declarations or ledger adjudications with provenance.
A candidate release is blocked until the top-3,000 audit and all flagged-tail items are
closed. A second spot-check is required on the assembled release.

## Cognates: completion contract

For the first release, this document treats target-language-to-English cognates
as the required pair. Supporting another known language is separate work and
requires another pair policy and, outside English, that language's dictionary
extract.

Every finished English cognate layer needs:

- [ ] Target-language Kaikki/Wiktionary extract with English glosses.
- [ ] Target frequency list bounding the surfaces to score.
- [ ] English word list for safe gloss-token filtering.
- [ ] `config/cognates/<target>-en.json` with ordered spelling correspondences.
- [ ] Meaning/form thresholds and an explicit default cutoff.
- [ ] Calibration list containing true cognates, near misses and false friends.
- [ ] Full provenance layer at `Fluency-Workspace/cognates/<target>/cognates.layer.json`.
- [ ] App file at `cognates/<target>/cognates.json`.
- [ ] App `cognateFilter` capability and `cognatesPath` wiring.
- [ ] Coverage measurement against the final release, not only the source dictionary.
- [ ] Optional CogNet merge reviewed as supplemental evidence.

## Spanish (`es`)

Spanish is the reference implementation and is closest to finished.

### Present

- Surface normalization and language package.
- Frequency inventory, SpanishDict menu, Tatoeba and OpenSubtitles sources.
- Audited inventory, menu, harvest and tokenization policies.
- Surface ledger and declared slang, filler, elision, entity and mend overlays.
- Full Speech releases, conjugations, lexical relations, MWEs and coverage output.
- English cognate pair policy, generated app map and provenance layer.
- Fresh Artist corpus, processing profile, artist releases and Lyrics adapter.

### Still to finish or verify

- [ ] Freeze one final Speech release as the canonical production release rather than
  leaving several v15/mend candidates in circulation.
- [ ] Verify the deployed release contains the current cognate map and that its coverage
  is measured against the final 10,000-card index.
- [ ] Decide whether the supplemental CogNet merge is part of the canonical cognate
  build; a Spanish merge exists, but this should be an explicit release policy.
- [ ] Record optional layers that are intentionally absent instead of relying on missing
  files.
- [ ] Run the final app acceptance pass across both Speech and all four Spanish artists.

## French (`fr`)

French has nearly all external Speech sources, but the current scaled path is
not a finished fresh release.

### Present

- French surface, contraction, lookup and tokenization adapters.
- Lexique 4 frequency snapshot and adapter.
- Audited Wiktionary menu policy and pinned French Kaikki extract.
- Tatoeba and aligned OpenSubtitles snapshots.
- English cognate policy, generated workspace map and provenance layer.
- Verbecc conjugation source and generated conjugation release.
- Kaikki lexical-relations source.
- Existing Speech releases and app wiring.

### Missing or incomplete

- [ ] Build the French observation events and materialized surface ledger.
- [ ] Run and review the full 3,000-card profile; its current execution status is
  `blocked_pending_benchmark` and its model revisions are empty.
- [ ] Produce a successor release from the current ledger-based pipeline rather than
  treating the older migrated release as final.
- [ ] Generate and wire French coverage output.
- [ ] Recheck the English cognate cutoff against the final release. The existing map was
  calibrated against the dictionary/frequency universe while the deck was only a preview.
- [ ] Copy the generated French `cognates.json` into the app/deployment input. The app
  config names the path, but the file is not present under `app/cognates/fr`.
- [ ] Decide whether to build the available `eng-fra` CogNet supplement and document the
  merge policy.
- [ ] Audit dictionary gaps and add French declared entries only where the ledger shows
  unresolved contractions, colloquialisms or headwords.
- [ ] Decide whether French needs an MWE layer; none is currently present.

### Artist mode

- [ ] Implement a French Lyrics normalization adapter.
- [ ] Implement French live routing resources and rules.
- [ ] Create a French artist corpus plan with pinned lyrics and aligned English lines.
- [ ] Replace or formally migrate the legacy French test-playlist assets.
- [ ] Add French artist declarations for elisions, slang, entities and dialect where needed.
- [ ] Build, validate and activate a French Lyrics release before setting `lyrics: true`.

## Dutch (`nl`)

Dutch has the core source snapshots and cognate work, but its current profile
contains copied placeholders and no workspace Speech release was found.

### Present

- Dutch surface normalizer.
- OpenSubtitles-derived 50,000-surface frequency list and inventory policy.
- Pinned Dutch Kaikki/English-Wiktionary extract.
- Tatoeba and aligned OpenSubtitles snapshots.
- Partial Wiktionary metadata policy.
- English cognate pair policy, generated app map and provenance layer.
- A real 3,000-surface inventory, menu and sentence harvest. The later stage
  directories contain planning contracts only, not completed outputs.
- Basic app display entry with Dutch name, flag and speech locale.

### Missing or incorrect

- [ ] Correct the scale profile locale from `cs-CZ` to `nl-NL`.
- [ ] Add a proper source manifest for the Dutch FrequencyWords snapshot. Its content
  hash and snapshot ID are recorded by runs, but the raw directory contains only the
  two-column text file and does not retain licence/source metadata.
- [ ] Replace the copied Portuguese execution profile, model profile and revision pins
  with a Dutch-valid profile before another run is trusted.
- [ ] Remove the copied Czech source note and write a Dutch corpus note based on Dutch
  measurements.
- [ ] Build and compare the Dutch hybrid menu. Use Kaikki for broad coverage and
  grammatical/conversational forms, and Open Dutch WordNet for its cleaner lexical
  synsets and stable links to English WordNet definitions. Open Dutch WordNet is not a
  standalone replacement: direct lemma overlap is 1,591/3,000 (53.0%), while the
  current Kaikki run supplies 2,784/3,000 menus (92.8%).
- [ ] Define a deterministic merge order and preserve the source of every sense; do not
  silently combine similarly worded senses from the two providers.
- [ ] Finish the resulting menu metadata audit; the current Kaikki-only policy is marked
  `partial`.
- [ ] Resolve or explicitly declare the 216 of 3,000 surfaces that currently have no
  usable menu.
- [ ] Manually audit all 3,000 ranked surfaces and examples, including English leakage,
  subtitle names/credits, interjections, fillers, loanwords and function words that need
  small curated menus rather than ordinary sense selection.
- [ ] Build Dutch observation events and the materialized surface ledger.
- [ ] Audit inventory noise beyond the five already declared apostrophe/tokenizer cases.
- [ ] Produce and validate an immutable Dutch Speech release; none exists under
  `Fluency-Workspace/releases/nl/speech`.
- [ ] Change the app from `hasData: false` and add release, capability and study paths.
- [ ] Copy/wire the existing cognate output into the app and enable `cognateFilter`.
- [ ] Measure cognate coverage and recalibrate the cutoff against the final deck.
- [ ] Decide whether to build the available `eng-nld` CogNet supplement.
- [ ] Generate Dutch coverage output.

### Optional Speech quality layers

- [ ] Choose and pin a Dutch conjugation source. Verbecc is explicitly unsupported;
  the generic Kaikki conjugation path is the current candidate and needs validation.
- [ ] Build Dutch lexical relations from the Kaikki extract.
- [ ] Audit and add Dutch declared contractions, colloquialisms and dictionary gaps.
- [ ] Decide whether Dutch needs an MWE layer.

### Artist mode

- [ ] Add a Dutch Lyrics normalization adapter and live router.
- [ ] Create all Dutch routing datasets: elisions, expansions, known forms, frequency,
  lexeme register, capitalization statistics and overrides.
- [ ] Pin at least one Dutch artist corpus with aligned English translations.
- [ ] Add artist metadata/assets and build the first Dutch Lyrics release.

## Italian (`it`)

Italian currently has a language package, app shell and a scaffold menu policy;
the actual Speech supply chain has not been onboarded.

### Present

- Italian surface normalizer and discoverable language package.
- App display shell with name, flag, speech locale and CEFR copy.
- Registered Wiktionary menu policy marked `scaffold`.
- Raw CogNet includes an `eng-ita` pair that may be used as supplemental evidence.

### Required Speech work

- [ ] Select, download and pin a spoken Italian surface-frequency list.
- [ ] Add `config/inventory/languages/it-v1.json` and audit its exclusions.
- [ ] Download and pin a current Italian Kaikki/Wiktionary JSONL extract.
- [ ] Audit the Italian menu policy: redirects, POS mappings, region, register,
  construction, domain, grammar, contextual grammar and ignored tags.
- [ ] Promote the menu policy from `scaffold` to `audited` only after metadata accounting.
- [ ] Add Italian to the Tatoeba source policy (`ita`) and pin an Italian-English snapshot.
- [ ] Pin an aligned English-Italian OpenSubtitles snapshot with provenance metadata.
- [ ] Add `config/harvest/languages/it-v1.json`, including apostrophe/elision and regional rules.
- [ ] Add an Italian Speech pipeline profile with `it-IT` locale.
- [ ] Build inventory, menu and harvest stages; audit their shortfalls and source quality.
- [ ] Build Italian observation events and the materialized surface ledger.
- [ ] Add declared entries for contractions, clitics, conversational fillers and menu gaps
  discovered by the ledger.
- [ ] Produce, validate and activate the first immutable Italian Speech release.
- [ ] Replace `hasData: false` with release paths and explicit app capabilities.
- [ ] Add Italian app data routing/CEFR entries wherever the app still uses explicit maps.

### Cognates

- [ ] Create and calibrate `config/cognates/it-en.json`.
- [ ] Use the Italian dictionary extract, final surface universe and English word list to
  build the provenance layer and app map.
- [ ] Review common Italian-English false friends before choosing the shipped cutoff.
- [ ] Optionally merge the existing `eng-ita` CogNet pair and audit what it adds.
- [ ] Wire `cognatesPath`, `cognateFilter` and final-deck coverage into the app.

### Optional Speech quality layers

- [ ] Pin and validate an Italian conjugation source. The generic Kaikki path is the
  current code-compatible candidate; Italian has no default locale in the layer builder,
  so `it-IT` must be supplied or added.
- [ ] Build Italian lexical relations.
- [ ] Decide whether Italian needs an MWE layer.
- [ ] Build source-title metadata for Italian subtitle examples.

### Artist mode

- [ ] Implement an Italian Lyrics normalization adapter and live router.
- [ ] Create the full Italian routing-resource set.
- [ ] Pin an Italian lyrics corpus and aligned English translations.
- [ ] Add artist-specific elisions, slang, entities and dialect declarations.
- [ ] Add artist/song/album metadata and build the first Italian Lyrics release.

## Finnish (`fi`)

Finnish is a clean-slate onboarding: no Finnish repository or workspace support
was found.

### Required shared setup

- [ ] Add `src/fluency/languages/finnish/` with `LANGUAGE_CODE = "fi"`.
- [ ] Define Finnish NFC, casing, hyphen and apostrophe behavior in `surfaces.py`.
- [ ] Add Finnish app configuration: name, flag, `fi-FI`, colours, reference links,
  route code, CEFR copy and capability defaults.
- [ ] Add Finnish to remaining explicit frontend language/flag maps.
- [ ] Register Finnish in the sense-menu registry.

### Required Speech work

- [ ] Select, download and pin a spoken Finnish surface-frequency list.
- [ ] Add `config/inventory/languages/fi-v1.json` and audit exclusions.
- [ ] Download and pin a Finnish Kaikki/Wiktionary JSONL extract.
- [ ] Compare Finnish Kaikki with FinnWordNet before fixing the menu design. Prefer the
  same explicit hybrid pattern if FinnWordNet improves lexical senses without covering
  the conversational and grammatical surface inventory.
- [ ] Create and fully audit `config/sense_menu/languages/fi-v1.json` for the selected
  provider or hybrid.
- [ ] Add Finnish to the Tatoeba source policy (`fin`) and pin a Finnish-English snapshot.
- [ ] Pin an aligned English-Finnish OpenSubtitles snapshot.
- [ ] Add `config/harvest/languages/fi-v1.json` with Finnish token and compound behavior.
- [ ] Add a Finnish Speech profile with `fi-FI` locale.
- [ ] Build and audit the inventory, menu and example supply.
- [ ] Manually audit all first 3,000 surfaces and examples, then write exclusions,
  classes, overrides, expansions and curated function-word menus for every exception.
- [ ] Build Finnish observation events and the materialized surface ledger.
- [ ] Add declared entries for colloquialisms, contractions and dictionary gaps found by
  the ledger.
- [ ] Produce, validate and activate the first immutable Finnish Speech release.
- [ ] Wire release paths, capabilities and coverage into the app.

### Cognates

- [ ] Choose the intended first known-language pair; this candidate assumes Finnish-English.
- [ ] Create and calibrate `config/cognates/fi-en.json`.
- [ ] Build the provenance layer and app map from the Finnish extract, final surface
  universe and English word list.
- [ ] Create a Finnish-English calibration/false-friend set before fixing the cutoff.
- [ ] Find a supplemental cognate source if desired; the pinned CogNet pair collection
  contains no Finnish data.
- [ ] Wire `cognatesPath`, `cognateFilter` and final-deck coverage into the app.

### Optional Speech quality layers

- [ ] Validate Kaikki conjugation extraction for Finnish morphology and add `fi-FI` as a
  layer locale if the result is useful.
- [ ] Build Finnish lexical relations.
- [ ] Decide how compounds and multi-word expressions should be represented, then build
  an overlay only if the audit supports one.
- [ ] Build source-title metadata for Finnish subtitle examples.

### Artist mode

- [ ] Implement a Finnish Lyrics normalization adapter and live router.
- [ ] Create Finnish routing resources, including colloquial reductions and known forms.
- [ ] Pin a Finnish lyrics corpus with aligned English translations.
- [ ] Add artist-specific slang, entities and dialect declarations.
- [ ] Add artist metadata/assets and build the first Finnish Lyrics release.

## Recommended completion order

1. **Spanish:** freeze and acceptance-test the existing complete stack.
2. **French:** add the ledger, unblock the scaled profile and publish a fresh successor.
3. **Dutch:** repair copied configuration, finish the menu audit, publish, then wire the
   cognate layer that already exists.
4. **Italian:** acquire the four core snapshots—frequency, dictionary, Tatoeba and
   OpenSubtitles—then build Speech end to end.
5. **Finnish:** scaffold the language and app first, then acquire the same four core
   snapshots and build the first audit release.
6. Add Artist support language by language only after each Speech ledger and menu are
   stable; reuse those dictionary and cognate objects rather than creating Artist-only
   equivalents.
