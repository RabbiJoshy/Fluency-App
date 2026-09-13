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

Unmatched clauses remain ordinary sense clarification. Dictionary examples and
the original provider fields remain in `source_metadata`, and unknown future
fields enter `unclassified`. A metadata upgrade reprojects from that preserved
source, so improving these rules does not retain stale older classifications.

## Shipped Spanish audit

The 2,000-card release contains 3,401 senses and 3,389 non-empty contexts. With
the current projection it yields 837 typed features: 58 companions, 44
constructions, 124 domains, 201 functional notes, 370 grammar marks and 40
regions/registers. The lower grammar and region totals are deliberate quality
corrections: family-member senses such as `abuela — relative` are not relative
pronoun grammar, and `United States` / `United Kingdom` labels describe the
English gloss chosen by SpanishDict rather than a variety of Spanish. Those
gloss-locale labels remain preserved and explicitly accounted for as ignored.
The remaining context is intentionally semantic text rather than uncategorised
metadata.

On the card, source spans represented by typed metadata are removed from the
inline context while semantic remainders stay beside the gloss. This also
applies to inactive subsense rows, which retain a useful clarification but do
not repeat their person, tense, region or construction prose. Sense-defining
grammar is always visible and its WSD-friendly atomic features are recombined
for learners (`mood` + `tense`, `person` + `number`). One supporting detail
appears directly, and larger supporting groups use the `More details`
disclosure.
