# Decision 0023 — Tutorial, walkthrough and About are three things

## Decision

Three features, three audiences, and one shared card:

| | For | Shape | Opened from | Code |
|---|---|---|---|---|
| **Tutorial** | learners using the app | guided, one element at a time; starts from the setup screen; owns the flip; a slide explains Lyrics mode before showing one. Desktop and phone equal. | "?" button, first run, Settings → How to Study, the in-study prompt | `app/js/tutorial.js` |
| **Walkthrough** | visitors (employers, anyone being shown the app) | two screens (three on a phone); a whole face labelled at once, so a five-second look still lands; no setup, no instructions | **only** About, layered over it | `app/js/walkthrough.js` |
| **About** | visitors | what the app is and how it was built; desktop-first, comfortable on a phone | landing page, `?about=1`, Settings | `app/content/about.md`, `auth.js` |

The card both features show is `app/js/card-replica.js`: real demo entries in
the live card's own markup, with no knowledge of steps, notes or audiences.

About **links** the walkthrough. It never contains or opens the tutorial.

## Context

One module, `about-example.js`, served all of it. It began as the walkthrough
(About → "See Example", header comment: "the main audience for it" is a
visitor on `?about=1`). Two changes turned it into the learner tutorial
without renaming it:

- `4993397` *Show the card walkthrough once on first entry* pointed first run
  at it.
- `2ea7cda` *Make tutorial a guided Speech to Lyrics flow* renamed About's link
  from "See Example" to "Start tutorial" and made it **close About** and open
  the learner tutorial's intro instead.

So an employer clicking the link in About was ejected into a two-minute
learner course that asks them to pick a language and a study set, and learners
met a module, CSS prefix and localStorage key all named for About. The
requirements that produced this mixed desktop/mobile layout choices with
audience choices; the split here is by audience, and each feature handles both
layouts itself.

## What the walkthrough does differently, and why

A visitor may look for five seconds. The tutorial's unit of a step (one ringed
element and its note) makes the first screen say almost nothing, so the
walkthrough's unit is a **whole face with every label on it**:

- Where two cards fit side by side (≥ ~800px of stage), screen 1 shows the
  front and back together; screen 2 is a Lyrics card. One click sees it all.
- On a phone the card turns over in place instead: three screens.
- Labels are callouts in the gutter with leader lines when there is room, and
  short tags pinned onto the card when there is not. Choice is by measured
  room, not device name.
- The card stays live — tap a meaning and the example changes, Spotify plays
  the real line — because that is worth showing off.

## Found on the way

About was invisible to logged-out visitors. `#authModal` (the landing card)
sits at `z-index: 30001` since `6f2820e`, and About opened at the generic modal
z-index beneath it, so a recruiter sent `?about=1` saw only a login card. About
is now 30002 and the walkthrough 30003. A test pins all three.

## Kept on purpose

- localStorage keys `fluencyCardWalkthroughSeenV1` / `…PromptV1` keep their
  names: renaming them would re-show the tutorial to everyone who has seen it.
- The About entry button keeps its `.about-see-example-*` classes; it opens
  the walkthrough, which is what the name always meant.

## Consequences

- A learner-facing string that says "walkthrough", or an About link that opens
  the tutorial, is a bug. `docs/NOMENCLATURE.md` pins the words;
  `tests/app/test_product_shell.py` pins the wiring.
- Adding a language to the tutorial is still one adapter entry and one demo
  card. The walkthrough is Spanish only: it is a showcase, not a course.
