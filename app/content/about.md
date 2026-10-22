## The problem with most vocabulary apps

Most vocabulary apps teach by theme (colours, at the airport, in the kitchen) and drill you on lists of words you have no reason to care about yet. You learn *la cuchara* (spoon) and forget it before you ever hear or use it in real life.

This app takes the opposite approach: it starts with the words that occur most often, and teaches them through things you already watch and listen to. Learn from everyday speech, from a playlist of songs you love, or from the series you are watching right now.

Choose a series and its dialogue becomes your vocabulary. In *La Casa de Papel*, *rehenes* (hostages) is the 120th most common word, where everyday Spanish puts it around 4,300th; *atraco* (heist) is 193rd, against nearly 9,000th. Music works the same way: on Bad Bunny's *YHLQMDLG*, *perreo* (reggaeton dancing) is among the 70 most common words, though it is rare in everyday Spanish.

### Speech

![Speech: a flashcard flipping and cycling through senses](demo://normal)

Learn Spanish as people actually speak it, with every word ranked by how often it comes up across millions of conversations in films and TV shows. Each card comes with real examples, lines from film and TV alongside professionally translated sentences, chosen to suit your level, so you never meet a rare word hidden inside an even rarer sentence.

Words with more than one meaning are split apart: *banco* is usually a *bank* and occasionally a *bench*, and each meaning gets its own sentence. Starting from frequency also brings everyday essentials like *mañana* (tomorrow) and *todavía* (still) to the front, where a themed lesson would bury them.

### Music

![Lyrics: a lyric card with the translated line](demo://artist)

Bring a playlist, your own from Spotify or one of the ready-made ones, and the app turns it into a vocabulary of the words those songs actually use, most frequent first. Each flashcard shows a real lyric containing the word, with the line translated underneath. Tap the Spotify button and the line plays at that exact moment, so you hear the word on the original track.

For words with several meanings, the card shows how your songs actually use them: in these songs *cielo* is mostly *heaven*, and sometimes the *sky*.

A relatively small number of words make up most lyrics. Learn the most frequent few hundred and you can already follow much of the playlist.

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
