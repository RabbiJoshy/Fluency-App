## The problem with most vocabulary apps

Most vocabulary apps teach by theme (colours, at the airport, in the kitchen) and drill you on lists of words you have no reason to care about yet. You learn *la cuchara* (spoon) and forget it before you ever hear or use it in real life.

This app takes the opposite approach: it starts with the words that occur most often, and teaches them through things you already watch and listen to. Learn from everyday speech, from an artist or playlist you choose, or from the series you are watching right now.

In everyday speech, common essentials like *mañana* (tomorrow) come first. But choose a series and its dialogue becomes your vocabulary: in *La Casa de Papel*, *rehenes* (hostages) is the 120th most common word, where everyday Spanish puts it around 4,300th; *atraco* (heist) is 193rd, against nearly 9,000th. Music works the same way: on Bad Bunny's *YHLQMDLG*, *perreo* (reggaeton dancing) is among the 70 most common words, though it is rare in everyday Spanish.

### Speech

![Speech: a flashcard flipping and cycling through senses](demo://normal)

Learn Spanish as people actually speak it, ranked across millions of lines of film and TV dialogue.

Each card gives you clean, natural examples suited to your level, with multiple meanings split into their own clear context.

### Music

![Lyrics: a lyric card with the translated line](demo://artist)

Upload a playlist or select an artist to learn the exact words from their music, most frequent first.

Each card pairs a real translated line with a Spotify button that jumps straight to that moment in the track.

## What makes it different

:::feature
### Skip what you already know

Pick the languages you already know, and words you can get from them are skipped. Words you've learned in another language in the app can be skipped too. Look-alikes and repeated forms don't get their own flashcards.

:::compare
#### Skipped
*información* (information)
~ A look-alike you can already guess.
*estaba* (was), *estamos* (we are), *estar* (to be)
~ Forms of one verb share a single flashcard.
#### Kept
*sensible* (sensitive, not "sensible")
~ A false friend.
*seres* (beings)
~ Not a form of *ser* (to be).
:::
:::

:::feature
### Examples worth learning from

Clean, natural lines from film and TV with accurate translations. Words with several meanings get separate examples: *banco* is a bank in one sentence and a bench in another.
:::

:::feature
### Expressions

Phrases made of several words are learned as one unit, not word by word: *de nuevo* (again), *a menos que* (unless).
:::

:::music-group
:::feature
### The slang each artist uses

Word lists built from the artist's own lyrics, so words like *roncar* (to brag, not "to snore") and *perreo* (reggaeton dancing) appear for Bad Bunny and are translated properly.
:::

:::feature
### Learn what things are

People, places and brands in lyrics are recognised and explained.
:::
:::

## How it works (technical details)

**Any language.** The pipeline is multilingual by design. It works for any language with a Wiktionary, such as French, Portuguese, Czech, Finnish or Dutch. Adding a language means adding files for it, not rewriting the engine.

**Skipping known words.** No complete cognate list (words that share an ancestor, like *información* and *information*) exists for every language pair, and existing databases cover only some pairs, partly. So I built my own. It compares spellings the way languages really drift (*-ción* becomes *-tion*), uses translations as a bridge between languages, and cross-checks with existing cognate data where there is any. A word is skipped only if every one of its meanings is easy.

**One flashcard per word.** Verb forms merge under their base verb, and plurals merge with singulars, but only when the dictionary entries for both forms carry exactly the same set of meanings. An extra meaning on either side, a noun and a verb that share a spelling (*ser* / *seres*), a plural-only sense, or a missing dictionary link keeps them apart. Contractions (Portuguese *no*, "in the"; French *au*, "to the") and frozen phrases are protected too. Languages differ, and no standard list of exceptions exists, so it is generated for each language.

**Cleaning sentences.** Sentences are split into words and tagged by part of speech with spaCy and Stanza, Unicode-normalised, and filtered on form, length and difficulty. Each translation pair is checked for alignment with LaBSE.

**Dictionaries.** There is no single standard. SpanishDict covers Spanish; Wiktionary covers the rest. Each is converted into one common format, so everything downstream works the same whatever the source.

**Choosing the meaning.** Each example is matched to a dictionary definition in two tiers:

- **Bi-encoder for the easy cases.** It turns the sentence and each definition into numbers and picks the closest meaning. Fast and cheap, and enough for most words.
- **Jev for the hard cases.** When the bi-encoder isn't confident, the sentence goes to Jev, a new kind of decision model. Instead of writing text, it picks from a fixed list of options and says how sure it is, which is what choosing a dictionary meaning needs.

When neither is sure, the flashcard shows a broader meaning rather than a wrong one.

**Expressions and artist vocabulary.** Multi-word expressions compete with single words as candidate meanings, so *de nuevo* (again) can win without erasing the literal meaning of its parts. For artists, I assembled slang and regional vocabulary lists where dictionaries had none.
