# Features and the NLP behind them — draft 3

Working draft for the About page, replacing "What's under the hood" in
`app/content/about.md`. Not wired into the app yet.

Plain words, no app vocabulary. Feature first, then one line of how.

---

## What makes it different

### Skips words you already know

Words that look and mean the same in a language you speak, like *información /
information*, are left out, so your time goes to words that actually need it.
Look-alikes are found by comparing spellings the way languages really drift
(*-ción* becomes *-tion*), and checked against a database of true cognates so
false friends like *sensible* aren't skipped.

### One flashcard per word, not per form

*Estaba*, *estamos* and *estar* are one word. Different forms are merged into a
single flashcard, with the forms listed on it, so you don't study the same word
five times.

### Clean, useful example sentences

Examples come from real film and TV dialogue and professionally translated
sentences, then filtered down to ones that are clear, natural and the right
difficulty. Sentences with misaligned translations, broken text or odd
formatting are removed.

### The right meaning, every time

Most words have several meanings, and each gets examples that really use it.
*Banco* shows a bank in some sentences and a bench in others.

### Idioms and expressions

Multi-word expressions like *de nuevo* or *a menos que* are recognised as units
rather than word by word.

### Language that belongs to each artist

For music, vocabulary and slang are drawn from the artist's own lyrics, so
*perreo* appears for Bad Bunny and not for a general learner.

---

## For the curious: how it works

**Dictionaries.** Meanings come from real dictionaries: SpanishDict for Spanish,
Wiktionary for the other languages.

**Cleaning and normalising.** Sentences are tokenised and tagged for
part-of-speech with spaCy and Stanza, Unicode-normalised, and filtered with
rules for form, length and difficulty. Translation pairs are checked for
alignment with LaBSE.

**Choosing the meaning.** Each example is matched to a dictionary definition in
two tiers:

- **Bi-encoder for the easy cases.** A bi-encoder turns the sentence and each
  definition into numbers and picks the closest meaning. This handles the
  majority of words quickly and cheaply.
- **JEV for the hard cases.** When the bi-encoder isn't confident, the sentence
  goes to JEV, a constrained decision model. Instead of writing text, it picks
  from a fixed list of options. *(Experimental, still in development.)*

When neither is sure, the flashcard shows a broader meaning rather than a wrong
one.

---

## Open questions

1. **JEV.** Is "constrained decision model" the right description, or does the
   name stand for something I should spell out?
2. **Merged forms and artist vocabulary.** I wrote these from the repo's
   descriptions. Check the merged-forms example and the artist-slang line are
   how you'd say it.
3. **Tools.** I listed spaCy, Stanza and LaBSE. Anything else you'd name?
