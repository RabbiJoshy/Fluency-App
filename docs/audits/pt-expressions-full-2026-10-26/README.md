# Inflected expressions: full Portuguese WSD pass (2026-10-26)

DECIDE-1 sentences that contain an expression the inflecting matcher (decision 0034) now finds,
re-asked with that expression added to the card's menu, by the model that answered the card
(mercury-decide for the top 1,077 cards, Jev for the rest). Inventory: the recount
`raw/mwe/mwe-pt-20261026-v15-inflected` (86 `zero_freq` exclusions readmitted, e.g. *dar-se conta*).
Skipped: expressions whose meaning the menu already has (`expression_already_on_menu`; *acabar de*,
*ter que*, *prestar atenção*). 563 cards, 1,389 sentences, $0.065.

Outcomes (release NONE rule: NONE only at P >= 0.8):

| Outcome | n |
|---|---|
| Meaning corrected (verb sense → expression) | 523 |
| Was NONE (unpublished), now the expression | 519 |
| Relabel of a meaning already on the menu | 15 |
| Expression offered, not chosen | 174 |
| Answer changed without choosing it (run-to-run noise) | 148 |
| Earlier answer from a different menu, skipped | 10 |

Most taken: *tomar conta* 87, *valer a pena* 84, *fazer ideia* 48, *querer dizer* 37, *fazer parte* 34,
*dar cabo* 33, *dar-se bem* 32, *bater à porta* 32. Answers: `reviews/pt-expressions-inflected-20261026/`.
Not yet in a release.
