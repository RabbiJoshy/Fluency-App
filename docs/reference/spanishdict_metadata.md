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
the current projection it yields 885 typed features: 57 companions, 42
constructions, 124 domains, 201 functional notes, 387 grammar marks and 74
regions/registers. The remaining context is intentionally semantic text rather
than uncategorised metadata.

On the card, source spans represented by typed metadata are removed from the
inline context while semantic remainders stay beside the gloss. Sense-defining
grammar is always visible; one supporting detail appears directly, and larger
supporting groups use the `More details` disclosure.
