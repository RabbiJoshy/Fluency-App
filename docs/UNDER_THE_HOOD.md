# What's under the hood — draft 2

Working draft for the About page's "What's under the hood" section. Replaces the
current bullet list in `app/content/about.md`. Not wired into the app yet.

Audience: anyone curious. Plain words, no app vocabulary, no frontend talk. Each block is a
feature a learner can feel, then the NLP that makes it work.

Open questions for Josh are at the bottom.

---

## What's under the hood

### Smart Skip: don't teach what you already know

Smart Skip leaves out words you can already guess. If you speak English,
*información* doesn't need a flashcard. Skipped words aren't deleted: you can
still browse them, with the reason shown.

- **Spelling similarity.** Each word is compared with its English counterpart
  using rules for how languages really drift: *-ción* becomes *-tion*, a *b*
  sneaks in between *m* and *r* (*número / number*), letters swap places
  (*capitán / captain*). Short words are held to a stricter standard, so *este*
  isn't treated as *east*.
- **Shared ancestry.** Looking alike isn't enough. The two words must also be
  known relatives or direct translations, which keeps false friends like
  *sensible* (it means "sensitive") from being skipped.
- **Every meaning must be easy.** A word is skipped only if all of its meanings
  are easy. *Banco* means *bank*, which you know, but also *bench*, which you may
  not, so it stays.
- **Other languages you speak.** Know Spanish and learning Portuguese? Words you
  already learned in Spanish can be skipped in Portuguese.

### Matching each example to the right meaning: bi-encoders

*Banco* is a bank in one sentence and a bench in the next. To give each meaning
its own examples, the pipeline turns text into numbers.

A **bi-encoder** reads two pieces of text separately and places each one in a
shared "meaning space". The closer two positions are, the closer the meanings.
Each text is encoded once and stored, so comparing millions of pairs is cheap.
It is used in two places:

1. **Choosing the meaning.** Each example sentence is compared with each
   dictionary definition of the word, one definition at a time. Blending all
   definitions together would wash the signal out into general topic noise. The
   closest definition wins, with a small nudge towards the dictionary's first
   definition, since real speech picks it more than 80% of the time. Grammar is
   checked first: if the word is a verb in the sentence, noun definitions are
   ruled out before anything is scored.
2. **Catching bad translations.** Subtitle files drift out of sync, so a
   Portuguese line can end up next to an unrelated English one ("Porque este
   bebe está a bater à porta" paired with "Is the Sarah parade over?"). A
   multilingual bi-encoder (LaBSE) scores how well the two sides match. Only
   pairs below 0.30, where every pair checked by hand was genuinely misaligned,
   are dropped. That removes about 0.55% of candidates and leaves idiomatic
   subtitle translations alone.

### Knowing when not to answer

When the two ways of choosing a meaning disagree, the system doesn't guess. It
shows a broader, safer description instead: the exact meaning if both agree,
otherwise the shared English translation, otherwise just the word. The full
answer stays on file. A slightly vaguer answer beats a confident wrong one.

### JEV

*(placeholder: see questions below)*

### Every decision is recorded

Each choice about a word (kept, merged, rejected, and why) is stored as a plain
fact in an append-only log. Conclusions are worked out from those facts when
needed, so when a rule changes nothing is rebuilt from scratch, and any
flashcard can be traced back to the sentence and dictionary it came from.

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
