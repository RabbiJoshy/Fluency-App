# Features and the NLP behind them — draft 7

Working draft for the About page, replacing "What's under the hood" in
`app/content/about.md`. Not wired into the app yet.

Plain words, no app vocabulary. Part 1 is for learners, short. Part 2 is for the
technically curious.

---

## What makes it different

### Skip what you already know

Why spend time on words you can already guess? The app cuts through vocabulary
you effectively know, so study time goes to what's new.

**Words you already know**
*Información* is *information*. Look-alike words are left out, but false friends
like *sensible* (it means "sensitive") are kept.

**One flashcard per word**
Different forms of the same word share a flashcard: *estaba*, *estamos* and
*estar* are one verb, and *gato* and *gatos* are one noun. But only when the
meaning really is the same. Forms stay separate when they differ in meaning or
function:
- *fue* (could be *ser* or *ir*)
- *del* and *al* (contractions)
- *seres* (beings), which isn't just the plural of the verb *ser* (to be)
- *no sé* (a set phrase)

### Examples worth learning from

Real lines from film and TV, cleaned down to clear, natural sentences with
accurate translations, at the right difficulty. Words with several meanings get
separate examples for each: *banco* is a bank in one sentence and a bench in
another.

### Idioms and expressions

Phrases like *de nuevo* and *a menos que* are learned as units, not word by word.

### The slang each artist actually uses

For music, vocabulary comes from the artist's own lyrics. Dictionaries often
don't have the slang, so I built the missing word lists myself, so *perreo*
appears for Bad Bunny and is translated properly.

### Learn what things are, too

People, places, brands and names aren't dictionary words. The app recognises
them and teaches what they are, instead of a bad literal translation.

### Any language

The same pipeline works for any language that has a Wiktionary.

---

## How it works

**Any language.** The pipeline is multilingual by design. It works for any
language with a Wiktionary, such as French, Portuguese, Czech, Finnish or Dutch.
Adding a language means adding files for it, not rewriting the engine.

**Skipping known words.** No complete cognate list exists for every language
pair, and existing databases cover only some pairs, partly. So I built my own.
It compares spellings the way languages really drift (*-ción* becomes *-tion*),
uses translations as a bridge between languages, and cross-checks with existing
cognate data where there is any. A word is skipped only if every one of its
meanings is easy. Words learned in one language can also be skipped in a related
one.

**One flashcard per word.** Verb forms merge under their base verb, and plurals
merge with singulars, but only when the dictionary entries for both forms carry
exactly the same set of meanings. An extra meaning on either side, a noun and
a verb that share a spelling (*ser* / *seres*), a plural-only sense, or a missing
dictionary link keeps them apart. Contractions and frozen phrases are protected
too. Languages differ (Portuguese *no*, French *au*), and no standard list of
exceptions exists, so it is generated for each language.

**Cleaning sentences.** Sentences are tokenised and tagged for part-of-speech
with spaCy and Stanza, Unicode-normalised, and filtered on form, length and
difficulty. Translation pairs are checked for alignment with LaBSE.

**Dictionaries.** There is no single standard. SpanishDict covers Spanish;
Wiktionary covers the rest. Each is converted into one common format, so
everything downstream works the same whatever the source.

**Choosing the meaning.** Each example is matched to a dictionary definition in
two tiers:

- **Bi-encoder for the easy cases.** It turns the sentence and each definition
  into numbers and picks the closest meaning. Fast and cheap, and enough for
  most words.
- **Jev for the hard cases.** When the bi-encoder isn't confident, the sentence
  goes to Jev, a new kind of decision model. Instead of writing text, it picks
  from a fixed list of options and says how sure it is, which is what choosing a
  dictionary meaning needs. *(Experimental, still being tested.)*

When neither is sure, the flashcard shows a broader meaning rather than a wrong
one.

**Expressions and artist vocabulary.** Multi-word expressions compete with
single words as candidate meanings, so *de nuevo* can win without erasing the
literal meaning of its parts. For artists, I assembled slang and regional
vocabulary menus where dictionaries had none.

**Names and things.** Entities are identified using Wikipedia-style sources, so
the app can say what something is.

*(Entity recognition and the slang source are written from your description, not
from the repo. Please correct.)*

---

## And more

Support for further languages is on the way, including ones with no dedicated
tools of their own yet.

---

## Open questions

1. **Entity recognition.** I couldn't find it in the repo. What source do you
   use (Wiktionary, Wikipedia, Wikidata), and what does a learner see?
2. **Artist slang.** Which source(s) did you use for the slang menus, and does
   "built the missing word lists myself" overstate it?
3. **Jev.** Name TypeSafe AI as the maker, or just "Jev"?
4. **Tools.** spaCy, Stanza, LaBSE. Anything else to name?
