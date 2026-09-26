# Language Onboarding

This is the minimum external-data checklist for taking a new language through
the Fluency pipeline. Speech mode comes first; Artist mode adds the final
section. Internal WSD and classifier design is intentionally out of scope.

## 1. Shared language setup

- Language identity: ISO code, app key, name, locale, flag and speech locale.
- App presentation: colour theme, reference links, capabilities and release paths.
- Surface adapter: Unicode, case, apostrophe, hyphen and diacritic rules.
- Token/boundary rules for matching complete observed surface forms.
- One pipeline profile connecting the language, sources, policies and release scope.

## 2. Speech mode: required inputs

### Frequency list

- A pinned snapshot containing one surface form and a positive count or rank per row.
- An adapter for the source format.
- A language inventory policy for exclusions such as names, abbreviations, noise and
  foreign-language leakage.
- Prefer a large, recent, spoken-language corpus matching the intended regional variety.

### Sense menu / dictionary

- A pinned dictionary snapshot with English glosses.
- For every sense: a stable source sense ID, headword, part of speech, gloss and
  source provenance.
- A surface-to-headword lookup route; the headword remains metadata and never becomes
  the card identity.
- An explicit `no_menu` result for surfaces without a usable entry.
- A provider adapter that converts the source into `sense-menu/v1`.
- A language metadata policy mapping provider data into:
  - region
  - register
  - grammar
  - construction
  - domain
  - redirects and inflected-form lookups
- Prefer provider examples, good sense ordering, usage labels and complete inflection
  redirects.

### Example corpora

- A pinned Tatoeba target-language-to-English snapshot.
- A pinned, line-aligned OpenSubtitles target-language-to-English snapshot.
- Each snapshot must retain source IDs, licence, attribution, source URL and snapshot
  metadata.
- Source adapters for the snapshot formats.
- A language harvest policy covering normalization, word boundaries, forbidden content,
  sentence rules and regional-variety markers.

### Runtime and storage

- Exact external model packages and revisions required by the selected pipeline profile.
- Provider credentials where an external model service is used.
- Stable snapshot names and content hashes for every input.
- A Fluency Workspace for raw corpora, artifacts, runs and generated releases.

## 3. Speech mode: mandatory human audit

The first release must not go directly from downloaded data to automated processing.

- Review every surface in the first 3,000, in frequency order. For larger releases,
  also review every flagged item and samples from each later rank band.
- Check English leakage, names, subtitle credits, tokenization damage, abbreviations,
  dialect forms, loanwords, interjections, fillers, onomatopoeia and slang.
- Review each surface's menu for wrong-language entries, wrong headwords or parts of
  speech, missing common meanings, duplicate meanings and unusable grammatical senses.
- Inspect real example lines when the surface or menu is ambiguous.
- Give every reviewed exception one recorded outcome:
  - keep the provider menu
  - exclude it as contamination
  - assign a word class such as interjection, filler, loanword or entity
  - redirect it to the correct headword or expansion
  - replace it with a hand-written one-sense menu
  - give it a small hand-written menu for grammatical/function-word uses
  - retain the full menu for ordinary contextual sense selection
- Do not send a one-sense declared entry, entity or other deterministic item through
  ordinary sense selection. Record why it is deterministic.
- Treat common function words separately when dictionary senses are not useful learner
  choices. Spanish `el` and `la` are the model: use a small curated menu rather than a
  raw dictionary menu.
- Store all decisions as versioned inventory adjudications or declared entries, with
  reason, author, date and scope. Do not leave decisions in an informal spreadsheet.
- Block release while any top-3,000 surface remains unresolved or any manual review
  queue is open.

Repeat a shorter human pass after the candidate release is assembled: inspect the
highest-frequency cards, every declared or excluded item, every remaining menu gap and
a sample from each rank band.

## 4. Speech mode: optional quality inputs

- Declared surface/headword entries for contractions, slang, fillers and dictionary gaps.
- Conjugation dataset and provider adapter.
- Cognate layer for each language the learner may already know. Each pair needs:
  - a target-language dictionary extract with English glosses
  - a bounded target surface universe, normally the frequency list
  - a known-language dictionary extract for every known language except English
  - an English word list when English gloss-token filtering is required
  - a pair policy defining spelling correspondences, scoring limits and the shipped cutoff
  - a reviewed false-friend set used to calibrate that cutoff
  - an app-facing `cognates.json` and a provenance-rich layer artifact
  - optional CogNet pair data as supplemental evidence, never as the only source
- Multi-word-expression overlay.
- Source-title metadata for subtitle examples.
- Manual redirects, exclusions and corrections.

## 5. Artist mode: additional required inputs

- A pinned lyrics corpus containing song ID, title, artist, raw lyrics, source URL,
  licence and attribution.
- A corpus manifest giving the language, artist slug/name and source-file locations.
- English line translations or alignments. These are optional during ingestion but are
  effectively required for useful learner cards.
- A Lyrics language adapter for token normalization, colloquial forms and elisions.
- Lyrics routing resources:
  - elision mapping
  - multi-word expansions
  - known-word forms
  - target-language frequency snapshot
  - lexeme/headword register
  - routing snapshot or equivalent language rules
- The same dictionary snapshot, menu adapter and metadata policy used by Speech mode.

## 6. Artist mode: optional quality inputs

- English frequency list and target-language English-loanword list.
- Reverse conjugation lookup.
- Artist capitalization and name statistics.
- Hand-written routing overrides.
- Artist-specific slang, entities, dialect and lyric-elision declarations.
- Song and album metadata, artwork and Spotify IDs.

Artist mode also needs a human pass over every unique lyric surface and its example
lines. Explicitly separate target-language vocabulary, valid loanwords/code-switching,
artist or place names, interjections/fillers, elisions and transcription noise.

## Current limitation

The fresh Artist processing path currently has a Spanish-only normalization and routing
implementation. Onboarding another Artist language therefore requires a new Lyrics
language adapter as well as the data listed above.
