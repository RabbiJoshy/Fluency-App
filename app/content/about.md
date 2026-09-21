## The problem with most vocabulary apps

Most vocabulary apps teach by theme (colours, at the airport, in the kitchen) and drill you on lists of words you have no reason to care about yet. You learn *la cuchara* (spoon) and forget it before you ever hear or use it in the wild.

This app takes the opposite approach: it turns speech and song lyrics into flashcards, starts with the words that occur most often, and teaches them through material you already care about.

[See a card, annotated](example://walkthrough)

That brings small linking words to the front instead of burying them behind themed vocabulary. Words like *que* are essential for following how ideas fit together, but are easy to overlook in a lesson about food or travel. The app separates its uses (*that*, *than*, *which*), shows how common each one is, and pairs each with a real sentence where that meaning fits.

### Speech

![Speech: a flashcard flipping and cycling through senses](demo://normal)

Learn from subtitle dialogue, ordered by how common each word is across millions of subtitle lines. Every flashcard is paired with real examples from OpenSubtitles and Tatoeba at your current level, so you don't get a rare word hidden inside an even rarer sentence.

### Lyrics

![Lyrics: a lyric card with the translated line](demo://artist)

Pick an artist (Bad Bunny, say) and the app builds a frequency-ranked vocabulary from their catalogue. Each flashcard shows an actual song lyric containing the word, with the line translated underneath. Tap the lyric and it plays in your own Spotify at that exact moment, so you hear the word in context on the original track.

For words with several meanings, the card shows how the artist actually uses them: in these songs *cielo* is mostly *heaven*, and sometimes the *sky*.

A relatively small number of words make up most lyrics. Learn the most frequent few hundred and you can already recognise much of the catalogue.

## What's under the hood

The app is the front end of a data pipeline. Each step writes a versioned file that is checked against a schema, so every card can be traced back to the sentences and dictionary entries it came from.

1. **Choose the words.** Every word is ranked by how often it is actually said in film and TV subtitles. A card is the form you hear (*tem*, "has"), not its dictionary headword (*ter*, "to have"), because that is what you need to recognise.
2. **Collect real sentences.** Tens of millions of subtitle lines, each paired with its English translation (OpenSubtitles and Tatoeba). Every pair is scored on how well the two sides line up. Weak pairs are tagged rather than deleted, so a rule can be loosened later without scanning the corpus again.
3. **Look up the meanings.** Each word gets its menu of senses from a dictionary: SpanishDict for Spanish, Wiktionary for Portuguese, French and Czech. One engine handles both sources.
4. **Keep a ledger.** Every judgement about a word, such as "duplicate once accents are stripped" or "missing from the dictionary", is recorded as an event and never overwritten. Whether a word makes the deck is worked out from those events by a table of rules, so changing a rule means re-running it, not rewriting the history.
5. **Pick the meaning in each sentence.** Each sentence and each dictionary definition is turned into an embedding, and the closest definition is the starting guess. Then small, precise checks can overrule it: does the grammar agree (person, number, mood)? Is a word the meaning depends on actually present? Which English word does it line up with in the translation? When the evidence is weak, the sentence is left unassigned rather than guessed.
6. **Build the deck.** The clearest sentences for each meaning, with a translated, confidently matched line first, are published as a static release the app loads and caches offline.

- **Lyrics**: song lyrics come from Genius. Section tags and ad-libs are stripped, and a full conjugation table links the different forms of a verb.
- **Familiar words**: easy connections like *información* / *information* are flagged and can be excluded, so your study time goes to words that actually need memorising.
- **Frontend**: vanilla JS, no framework, no build step. Data loads as static JSON and a service worker caches it for offline use as a PWA.
