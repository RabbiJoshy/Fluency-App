# What's under the hood — draft 1

Working draft for the About page's "What's under the hood" section. Replaces the
current bullet list in `app/content/about.md`. Not wired into the app yet.

Audience: a curious learner or a recruiter. No frontend talk. Each block is a
feature a learner can feel, then the NLP that makes it work.

Open questions for Josh are at the bottom.

---

## What's under the hood

The app looks simple: a card, a word, an example. Most of the work happens
before you ever see the card, in a pipeline that reads millions of lines of
subtitles, lyrics and dictionary entries and decides what is worth showing you.

### Smart Skip: don't teach what you already know

Skip the words you can already guess. If you speak English, *información*
doesn't need a flashcard. Smart Skip finds those words and sets them aside, and
you can still browse them, with the reason shown.

Three ideas make it work:

- **Look-alike scoring.** A word pair like *capitán / captain* is scored on how
  similar the two spellings are, using rules for how languages really drift:
  *-ción* becomes *-tion*, *b* sneaks in between *m* and *r* (*número / number*),
  letters swap places. Short words are held to a stricter standard so that
  *este* does not count as *east*.
- **Both words must be real relatives.** Looking alike is not enough. The pair
  also has to be a known cognate (a word with the same ancestor) or a direct
  translation. That filter is what keeps *sensible* (sensitive) from being
  skipped as if it meant *sensible*.
- **Every meaning has to pass.** A card is skipped only if *all* the meanings it
  shows are easy. *Banco* is *bank*, which you know, and also *bench*, which you
  might not, so it stays.

It also works across languages you already speak. Know Spanish, learning
Portuguese? Words you've already learned in Spanish are skipped in Portuguese.

### The right meaning in every example: sentence embeddings (bi-encoders)

*Banco* is a bank in one sentence and a bench in the next. To give each meaning
its own examples, the pipeline turns text into numbers.

A **bi-encoder** reads two pieces of text separately and gives each a position
in a shared meaning-space; the closer two positions are, the closer the
meanings. Because each text is encoded once and stored, comparing millions of
pairs is cheap. It runs here in two places:

1. **Picking the meaning.** Each example sentence is compared against each
   dictionary definition of the word, one definition at a time (never a whole
   entry blended together, which turns into vague topic noise). The closest
   definition wins, with a small nudge towards the dictionary's first meaning,
   since real speech favours it more than 80% of the time. Grammar comes first:
   a verb in the sentence rules out noun definitions before anything is scored.
2. **Catching bad translations.** Subtitle files drift out of sync, so a
   Portuguese line can end up paired with an unrelated English one ("Porque este
   bebe está a bater à porta" next to "Is the Sarah parade over?"). A
   multilingual bi-encoder (LaBSE) scores how well the two sides match. Only
   pairs below 0.30, where every one read by hand was genuinely misaligned, are
   dropped. That removes about 0.55% of candidates and leaves natural, idiomatic
   subtitles alone.

### Knowing when not to answer

When the two ways of picking a meaning disagree, the card doesn't guess. It
falls back to a broader, safer description (the exact meaning, then the shared
English gloss, then just the headword) and keeps the full answer on file.
Better a slightly vaguer card than a confidently wrong one.

### JEV

*(placeholder: see questions below)*

### Every decision is recorded

Each choice about a word (kept, merged, rejected, and why) is stored as a plain
fact in an append-only log. The verdict is worked out from those facts when
needed. So when a rule changes, nothing is rebuilt from scratch, and any card
can be traced back to the sentence, dictionary and corpus it came from.

---

## Open questions

1. **JEV.** I couldn't find it anywhere in the repo, docs or code. What does it
   stand for, and which part of the pipeline is it? I left a placeholder. If it
   is something not yet written down, tell me in a line or two and I'll draft it.
2. **Gemini embeddings.** The meaning-picker uses a Gemini embedding model
   (per `docs/WSD_ARCHITECTURE.md`), and LaBSE does the translation check. Both
   are bi-encoders. Do you want the page to name the models, or keep it generic?
3. **Depth.** This is about 600 words. Shorter (three punchy blocks), or more
   technical, with the measured numbers up front?
4. **Lyrics.** Not covered yet. Is there NLP in the lyrics path (alignment of
   translated lines to Spotify timestamps, idiom detection) worth its own block?
