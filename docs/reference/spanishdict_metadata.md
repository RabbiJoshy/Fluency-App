# SpanishDict metadata projection

SpanishDict's sense `context` is a mixed field. It contains both semantic
clarification (`to possess`) and metadata (`imperative; second person
singular`, `used with "de"`, `anatomy`). The Spanish adapter partitions the
field clause by clause; it does not classify the entire field from one match.

The provider-neutral output uses the same six feature families as Wiktionary:

- `companion`: a required Spanish word, including quoted `"a"`;
- `construction`: syntactic frames and optional companions;
- `domain`: an explicit subject label such as `anatomy` or `aviation`;
- `functional`: metalinguistic notes beginning `used to ...`;
- `grammar`: person, number, mood, tense, form, voice and grammatical role;
- `register`: regional and usage labels.

Canonical values are normalized at the adapter boundary where the providers use
different surface labels for the same concept (`legal` → `law`, `religious` →
`religion`). SpanishDict's mixed `regions` field is allowlisted: Spanish usage
regions become `register/region`, known English-gloss locales are explicitly
ignored, and a new unknown label becomes `unclassified` for policy review.

Unmatched clauses remain ordinary sense clarification. Dictionary examples and
the original provider fields remain in `source_metadata`, and unknown future
fields enter `unclassified`. A metadata upgrade reprojects from that preserved
source, so improving these rules does not retain stale older classifications.

Argument structure is normalized rather than merely placed in the right broad
family. SpanishDict's `direct object` now matches Wiktionary's
`construction/object_role`; complement prose such as `used with an infinitive`
becomes `construction/complement_form=infinitive`; and `before adjective`
becomes `construction/position=before adjective`. The original wording remains
as embedding evidence. Unmistakable functional labels written as participles
(`indicating time`, `expressing surprise`) join `used to ...` notes, while
ordinary meanings such as `to express` remain semantic text.

Recurring closed frames are atomic too: progressive and compound-tense
auxiliaries, verb substitution, argument types (`with dates`, `with pronouns`),
polarity contexts, comparisons and question contexts no longer survive as an
opaque `usage_note`. Narrow exact mappings keep looser phrases such as `used in
games` from being assigned syntactic meaning without enough evidence.

Functional prose has two layers. A stable machine purpose groups established
aliases across providers (`used to express obligation` and `used to indicate an
obligation` become `functional/modality=obligation`), while `embedding_text`
retains the provider's complete wording. The card deliberately displays that
original wording. Unmapped functions remain typed `usage_note` values rather
than being forced into a broad or misleading bucket.
The current Spanish projection canonicalizes 1,218 of 1,578 functional feature
occurrences (77%) across modality, temporal and semantic relations, discourse
functions, speech acts and emotions; the other 360 retain provider prose.

## Shipped Spanish audit

Across the repeated sense appearances in the 2,000-card projection, the current
release carries 7,384 typed feature occurrences: 1,657 companions, 637
constructions, 1,056 domains, 1,578 functional notes, 1,166 grammar marks and
1,290 regions/registers. The construction total includes 202 normalized frame
occurrences (116 complement forms, 54 positions and 32 object roles). The
grammar and region boundaries are deliberate quality corrections:
family-member senses such as `abuela — relative` are not relative-pronoun
grammar, and `United States` / `United Kingdom` labels describe the English
gloss chosen by SpanishDict rather than a variety of Spanish. Those gloss-locale
labels remain preserved and explicitly accounted for as ignored. The remaining
context is intentionally semantic text rather than uncategorised metadata.

The language policy also records a non-operative future-WSD role for each
family. It does not change v10 scoring. It preserves the distinction between
potential compatibility constraints (grammar), attachment-dependent strong
evidence (companions/constructions), and softer contextual evidence
(domain/register/functional) for a later v11 design.

On the card, source spans represented by typed metadata are removed from the
inline context while semantic remainders stay beside the gloss. This also
applies to inactive subsense rows, which retain a useful clarification but do
not repeat their person, tense, region or construction prose. Sense-defining
grammar is always visible and its WSD-friendly atomic features are recombined
for learners (`mood` + `tense`, `person` + `number`). One supporting detail
appears directly, and larger supporting groups use the `More details`
disclosure.
Canonical releases are rendered only from canonical features. Raw provider
fields remain a legacy-release fallback and cannot reintroduce a region or tag
that the adapter deliberately ignored.
