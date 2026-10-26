# Inflected-expression pilot (2026-10-26)

Does offering expressions found by the inflecting matcher (decision 0034) change Jev's answers?
16 Portuguese inflected verb cards from DECIDE-1, 418 sentences. Jev 1.14 asked twice with the
same prompt: the original menu (baseline) and the menu plus each matched expression, offered only
to the sentences that contain it (as the WSD runner does). Cost $0.026 in all.

| Outcome on the 159 matched sentences | n | Examples |
|---|---|---|
| Meaning corrected | 31 | *vale a pena*: valer "to be worth, valid" → *valer a pena* "worthwhile" (29) |
| Was NONE, now assigned | 20 | *tome cuidado*, *toma conta de*, *fique de olho* |
| Relabel: same meaning, now the expression | 86 | *acabei de* "to have just", *temos que* "to have to", *presta atenção* |
| Expression offered, not chosen | 22 | *tomar uma* (junk entry), some *acabar de* |

Unmatched sentences changed 15 of 259 times between two identical-menu runs: Jev's run-to-run
noise, so changes below ~6% mean nothing.

Reading: real gains are idioms whose meaning the verb's own menu lacks (*valer a pena*, *tomar conta*,
*tomar cuidado*, *ficar de olho*). Where Wiktionary already files the construction as a verb sense
(*acabar* "to have just", *ter* "to have to", *prestar* "to pay"), the expression only duplicates it.

`run_pilot.py` (projected cost first; `--run` calls Jev), `compare.py`, `comparison.json`, `responses/`.
