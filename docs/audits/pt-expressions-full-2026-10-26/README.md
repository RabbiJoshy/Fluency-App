# Inflected expressions: full Portuguese WSD pass (2026-10-26)

DECIDE-1 sentences that contain an expression the inflecting matcher (decision 0034) now finds,
re-asked with that expression added to the card's menu. Inventory: the recount
`raw/mwe/mwe-pt-20261026-v15-inflected` (86 `zero_freq` exclusions readmitted, e.g. *dar-se conta*).
Skipped: expressions whose meaning the menu already has (`expression_already_on_menu`; *acabar de*,
*ter que*, *prestar atenção*). 338 cards, 857 sentences counted against the model that answered each
card in DECIDE-1 (mercury-decide for the top 1,077, Jev for the rest). The DECIDE request file holds
every polysemous card, so 225 Jev cards were also sent to mercury-decide; those answers are unused.
Cost $0.065.

Outcomes (release NONE rule: NONE only at P >= 0.8):

| Outcome | n |
|---|---|
| Meaning corrected (verb sense → expression) | 519 |
| Was NONE (unpublished), now the expression | 107 |
| Relabel of a meaning already on the menu | 16 |
| Expression offered, not chosen | 192 |
| Answer changed without choosing it (run-to-run noise) | 23 |

An earlier count (523 / 519 / 15 …) compared mercury's DECIDE-1 answers for cards Jev had answered,
treating missing ones as NONE; superseded.

Release: `pt-speech-v25-decide-1-expr-10000-slim` (`scripts/build_decide1_expressions_release.py`);
`check_release.py`: untouched cards identical to DECIDE-1, published examples 139,859 → 139,957.

Most taken: *tomar conta* 54, *valer a pena* 49, *fazer ideia* 39, *dar cabo* 26, *querer dizer* 25, *dar-se bem* 20, *fazer parte* 20, *bater à porta* 13.
Answers: `reviews/pt-expressions-inflected-20261026/`.
