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

## 3. Speech mode: optional quality inputs

- Declared surface/headword entries for contractions, slang, fillers and dictionary gaps.
- Conjugation dataset and provider adapter.
- Cognate datasets and a policy for each target/known-language pair.
- Multi-word-expression overlay.
- Source-title metadata for subtitle examples.
- Manual redirects, exclusions and corrections.

## 4. Artist mode: additional required inputs

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

## 5. Artist mode: optional quality inputs

- English frequency list and target-language English-loanword list.
- Reverse conjugation lookup.
- Artist capitalization and name statistics.
- Hand-written routing overrides.
- Artist-specific slang, entities, dialect and lyric-elision declarations.
- Song and album metadata, artwork and Spotify IDs.

## Current limitation

The fresh Artist processing path currently has a Spanish-only normalization and routing
implementation. Onboarding another Artist language therefore requires a new Lyrics
language adapter as well as the data listed above.
