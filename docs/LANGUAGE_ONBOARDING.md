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

- For a first release of 3,000 cards or fewer, review every surface in frequency
  order. For larger releases, review at least the first 3,000, every flagged item
  and samples from each later rank band.
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
- Block release while any required surface remains unresolved or any manual review
  queue is open.

Repeat a shorter human pass after the candidate release is assembled: inspect the
highest-frequency cards, every declared or excluded item, every remaining menu gap and
a sample from each rank band.

## 4. Selection and publication policy

These choices are required onboarding inputs. The engine is shared, but the values and
enabled gates may differ by language and mode. Record them in the pipeline, harvest,
WSD-model and mode profiles, together with the measurement or judgement behind each
non-default value.

### What enters the candidate pool

- Per-source harvest quota: for source `s`, reserve
  `q_s = min(available_s, floor(card_cap * source_share_s))`, then redistribute unused
  slots to sources that still have supply. Source share controls what survives harvest;
  it does not directly control what the learner sees.
- Record the rank-banded harvest budget, candidate cap, source shares and every cheap
  rejection rule. These are language/mode choices because recovering discarded rows
  requires another harvest.
- Record cleaning gates such as the language-specific alignment floor, variety rules,
  length rules and contamination rules. Cleaning tags rejected rows; it does not erase
  them.

### What reaches WSD

- Record the execution cap or rank/polysemy budget. Speech normally takes at most the
  configured cap from each eligible, priority-ordered pool. Lyrics uses a separate
  rank-and-polysemy budget, so mode parity does not mean identical numbers.
- Record the exact candidate constraints: POS bridge, contextual lemma rule, grammar,
  companion/clitic rules, multi-word routing and deterministic bypasses. A language may
  disable a gate only by declaring that absence.
- Record the scoring profile: provider-order prior, gloss/context score, translation
  overlap bonus, domain penalty, and any language-specific repair. Do not copy Spanish
  settings to a Wiktionary language without measuring provider parity.
- Record the commit rule: forced leaf, rank agreement, evidence guards, abstain/redraw,
  or escalation. Also record the release projection: `forced_leaf` publishes the chosen
  leaf; `supported_specificity` publishes only leaf-level supported decisions.

### What reaches the learner UI

- Speech computes an audit-only difficulty value from distinct harder words:
  `c_i = log10(rank_i / target_rank)`,
  `burden = first_new_word_discount * max(c_i) + sum(other c_i)`, plus configured
  short/long sentence penalties. The exact weights live in the shared harvest policy.
- Difficulty is a ceiling, not the final order. For a card with more than 12 candidates,
  retain the lower two-thirds of its own difficulty distribution, then rank by formal
  sentence quality, difficulty and stable sentence ID.
- Fill display slots in four passes: unseen senses before repeats, first with strict
  single-sentence/no-placeholder rules and then relaxed; next fill remaining slots with
  the same strict-then-relaxed order. Deduplicate near-identical lines and cap reuse of
  one sentence across cards.
- Record the number of examples shown per rank band and the shortfall policy. These can
  differ by release even when harvesting and WSD are shared.
- Artist/Lyrics mode must separately record its occurrence-budget equation and line
  quality equation, including length, alignment, punctuation and playable-audio terms.

For every candidate release, archive a compact policy summary with the actual values,
not only profile names. This is what lets a later onboarding answer “why did this line
reach WSD?” and “why did this example reach the UI?” without reading implementation code.

## 5. Speech mode: optional quality inputs

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

## 6. Artist mode: additional required inputs

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

## 7. Artist mode: optional quality inputs

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
