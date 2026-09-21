## The problem with most vocabulary apps

Most vocabulary apps teach by theme (colours, at the airport, in the kitchen) and drill you on lists of words you have no reason to care about yet. You learn *la cuchara* (spoon) and forget it before you ever hear or use it in the wild.

This app takes the opposite approach: it turns speech and song lyrics into flashcards, starts with the words that occur most often, and teaches them through material you already care about.

### Speech

![Speech: a flashcard flipping and cycling through senses](demo://normal)

Learn from subtitle dialogue, ordered by how common each word is across millions of subtitle lines. Every flashcard is paired with real examples from OpenSubtitles and Tatoeba at your current level, so you don't get a rare word hidden inside an even rarer sentence.

Words with more than one meaning are split apart: *banco* is usually a *bank* and occasionally a *bench*, and each meaning gets its own sentence. Starting from frequency also brings small linking words like *que* to the front, where a themed lesson would bury them.

### Lyrics

![Lyrics: a lyric card with the translated line](demo://artist)

Pick an artist (Bad Bunny, say) and the app builds a frequency-ranked vocabulary from their catalogue. Each flashcard shows an actual song lyric containing the word, with the line translated underneath. Tap the lyric and it plays in your own Spotify at that exact moment, so you hear the word in context on the original track.

For words with several meanings, the card shows how the artist actually uses them: in these songs *cielo* is mostly *heaven*, and sometimes the *sky*.

A relatively small number of words make up most lyrics. Learn the most frequent few hundred and you can already recognise much of the catalogue.

## What's under the hood

Behind the cards is a data pipeline that turns raw subtitles, song lyrics and dictionaries into a deck a learner can trust.

- **Words worth learning first**: every word is ranked by how often it is actually said, so early study pays off fastest.
- **Sentences worth learning from**: millions of real lines with their translations, cleaned down to the clear, natural ones that help a learner.
- **Every meaning, not one gloss**: each word's meanings come from a real dictionary (SpanishDict for Spanish, Wiktionary for the other languages).
- **The right meaning in every sentence**: each example is matched to the meaning it actually uses, then double-checked. When the app isn't sure, it leaves the sentence out rather than teach you something wrong.
- **Built to keep improving**: every decision about a word is recorded, so the rules can get better without starting over, and any card can be traced back to where it came from.
- **The same care for lyrics**: an artist's songs go through the same kind of steps, so a Bad Bunny deck is built as carefully as the everyday one.
- **Familiar words**: easy connections like *información* / *information* are flagged and can be skipped, so study time goes to the words that need it.
- **Fast and offline**: plain JavaScript with no framework or build step, and decks are cached so the app works without a connection.
