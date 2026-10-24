# Features and the NLP behind them — draft 5

Working draft for the About page, replacing "What's under the hood" in
`app/content/about.md`. Not wired into the app yet.

Plain words, no app vocabulary. Feature first, then one line of how.

---

## What makes it different

### Skips words you already know

Words that look and mean the same in a language you speak, like *información /
information*, are left out, so your time goes to words that actually need it.
No complete cognate list exists for every language pair; existing databases
cover some pairs only partly. So the app builds its own: it compares spellings
the way languages really drift (*-ción* becomes *-tion*), uses translations
as a bridge between languages, and cross-checks with the existing cognate data
where there is any. False friends like *sensible* aren't skipped. Adding a new
pair needs a small config file, not new code.

### One flashcard per word, not per form

*Estaba*, *estamos* and *estar* are one word. Different forms are merged into a
single flashcard, with the forms listed on it, so you don't study the same word
five times. Each language handles this differently (contractions like Portuguese
*no* or French *au* must stay separate), and no standard list of these exists,
so the exceptions are generated per language.

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

**Built for any language.** The pipeline is multilingual by design. It works
for any language that has a Wiktionary, such as French, Portuguese, Czech,
Finnish or Dutch. Adding a language means adding files for it, not rewriting
the engine.

**Dictionaries.** Meanings come from real dictionaries, but there is no single
standard. SpanishDict covers Spanish; Wiktionary covers the rest. Their
structures differ, so each is converted into one common format, and everything
downstream works the same regardless of source.

**Cleaning and normalising.** Sentences are tokenised and tagged for
part-of-speech with spaCy and Stanza, Unicode-normalised, and filtered with
rules for form, length and difficulty. Translation pairs are checked for
alignment with LaBSE.

**Choosing the meaning.** Each example is matched to a dictionary definition in
two tiers:

- **Bi-encoder for the easy cases.** A bi-encoder turns the sentence and each
  definition into numbers and picks the closest meaning. This handles the
  majority of words quickly and cheaply.
- **Jev for the hard cases.** When the bi-encoder isn't confident, the sentence
  goes to Jev, a new kind of decision model. Instead of writing text, it picks
  from a fixed list of options and says how sure it is, which is exactly what
  choosing a dictionary meaning needs. *(Experimental, still being tested.)*

When neither is sure, the flashcard shows a broader meaning rather than a wrong
one.

---

## And more

Support for further languages is on the way, including ones that have no
dedicated tools of their own yet.

---

## Open questions

1. **Jev.** Web search shows Jev is TypeSafe AI's decision model (a product
   name, not an acronym), so I've written "Jev", not "JEV". Fine, or do you
   want the company named?
2. **Merged forms and artist vocabulary.** I wrote these from the repo's
   descriptions. Check the merged-forms example and the artist-slang line are
   how you'd say it.
3. **Tools.** I listed spaCy, Stanza and LaBSE. Anything else you'd name?
