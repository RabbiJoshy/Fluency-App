# Decision 0029 — Dictionary order confirms the gloss but cannot veto it (speech v21)

Measured 2026-09-28/29 on the live Speech runs (es/pt/cs v15-mend, fi
v12-wsd-r2), first 2,000 cards. Profiles `config/wsd/models/{es,pt,cs,fi}-v21-1.json`;
runs and candidates from `scripts/v21_runs.py`.

**Numbering.** Speech and lyrics profiles share one version sequence from here.
Speech had reached v15 and lyrics v20 (`es-lyrics-v20-1`), so this is v21.
Draft runs made under the name v16 on 2026-09-29 are superseded and were never
published.

## What was wrong

`rank_agreement` (v9 on) publishes a sentence's sense only when the gloss winner
and the menu's **first-listed** leaf agree; since v13 a disagreement between
different analyses (headword or part of speech) abstains. First-listed is a
fair prior *inside* one dictionary entry. Between entries it is noise:

- Wiktionary (kaikki adapter) sorts analyses by `(headword, pos)`: ten before
  ty, být before sem, `name` before `noun` before `pron`.
- SpanishDict keeps page order: ser before saber on sé, NOUN "east" before
  PRON "this" on este.

So the order vetoed the gloss. cs ty: gloss chose "you" in 26 of 30 lines, all
26 abstained, and the card shipped only ten "the, this, that". The veto caused
99.7% of cs, 75% of pt and 63% of es abstentions. Where every line abstained,
the card was labelled with the first-listed sense: cs smrt, strach and nevím
read "a male surname", já read "ego", es este read "east".

It is a regression from v13: the v12 decks showed ty "you", já "I", smrt
"death", este "this". It went unnoticed because v13 never shipped alone (v14
added phrases at the same time), audits sample published senses rather than
missing ones, and the "0 empty meanings" check passes a card labelled by the
fallback.

Separately, the POS and lemma gates removed readings spelled like the surface:
UD tags fi missä as PRON of mikä, Wiktionary files "where" as adv, and both
gates deleted "where" before scoring. pt obrigado lost "thanks" the same way.

## Decision

1. **Commit** (`commit.cross_analysis`): dictionary order can no longer veto
   the gloss between analyses, but it still confirms it.
   - Any line the v15 rule would publish is published exactly as v15 would.
   - For the rest, order votes only inside the gloss winner's analysis, and the
     raw gloss (no menu prior) must beat every other analysis by **0.02**; a
     rival inside the margin with the same English commits at glosskey (vy/ty
     "you"); anything else abstains.

   So v21 changes only lines v15 abstained on, for both providers (SpanishDict
   order fails too: sé, este). Drafts that applied the margin more widely made
   es more cautious, not less: que CCONJ/PRON and querer/quererse are split
   entries of one word that order used to settle, and 3,255 es lines v15
   published through a shared English gloss met a third entry in the margin.
2. **Gates** (`constrain.keep_self_reading_pos`): an analysis whose headword is
   the surface and whose POS is adv, intj, particle, pron or det survives the
   tagger's POS and lemma gates as a candidate. It still has to win the commit.
   Not conj: fi et ("you don't") won "and" in 37% of its lines. Not SpanishDict
   PHRASE rows (the `está` → "he's" reason in `languages/spanish.py`).
3. **A contested line abstains in every language** (`contested_outcome`).
   Finnish otherwise keeps fi-v12-1's publishing of unresolved lines: its
   dictionary-POS guard fires on correct menus (entä conj tagged ADV), and
   abstaining there cost 40 cards their right sense.
4. **Wiktionary bridge**: the tagger's ADP matches `postp`. Finnish
   postpositions (kanssa, jälkeen, takia) all failed the gate without it.
5. **Fallback label** (`release/app_compat.py`): an all-abstain card is never
   labelled with a proper-name sense.

## How the margin was chosen

The module notes in `wsd/commit.py` record that a tuple-margin threshold was
non-monotonic in the older repository, so 0.02 was not taken on the margin's
word. Fifteen vetoed lines per band per language were read by hand with their
sentences: the gloss winner was right in nearly all Czech lines at every band;
Spanish and Portuguese were about 30% wrong below 0.02 (revisto→revistar,
devido→dever, impuesto→"duty") and 5-10% wrong at 0.02 and above. Every one of
these lines abstained under v15.

The restored self-readings were judged the same way on the draft candidates:
fi and pt adv/pron/particle/det nearly all right (tässä "here", mihin "where
to", a gente "we", o/a "him/her"); intj mostly right (obrigado "thanks", apua
"help!", huomenta "good morning", tchau "bye"), misses fi miehet "gentlemen" and
naiset "ladies"; conj mostly wrong.

## Rejected

- **Reorder the menus** (self-headword first, names last). Any fixed order is a
  guess between entries; it moves the veto rather than removing it, and a
  stage-02 change re-keys every menu.
- **Gloss alone between analyses.** Below 0.02 it picks rare entries
  (sexo→sexar, iria→irisar) about a third of the time in es/pt.
- **The tagger's lemma as the second vote.** cs has no tagger; for fi the
  lemma votes against missä "where"; for este both remaining entries share
  the lemma.
- **A margin on every line.** See decision 1.
- **Patching Merge Lemmas** (decision 0028 left this to WSD).

## Not addressed

- Lines v15 published wrongly stay wrong: sé "Sé que es verdadero" goes to ser
  because gloss and order agree. Re-examining published lines costs more good
  lines than it saves (see decision 1).
- Proper-name entries still win a few lines by clear margins (cs muž "a male
  surname" at 1-6% of lines); cs hele and och have only name entries on the
  menu.
- fi miehet "gentlemen" and naiset "ladies" win about a third of their lines.

- pt tagger noise: `tu` tagged AUX/VERB matches no menu entry and abstains
  (`dictionary_has_no_matching_part_of_speech`), unchanged from v15.
- SpanishDict PHRASE rows are still on 247 es menus (106 with nothing else);
  WSD gates them, the menu keeps them.

## Results

Inactive candidates `es/pt/cs-speech-v21-10000x10` and `fi-speech-v21-2000x10`,
built from new runs on the same pre-WSD freezes (stages 01-03 carried
byte-for-byte). No Gemini spend: every gloss vector was cached.

Whole deck, abstained lines: es 9,637 → 6,859; pt 11,585 → 5,709; cs 18,067 →
3,304; fi 0 → 238 (contested lines only).

First 2,000 cards:

| | abstained (share of scored) | all-abstain cards | surname labels |
|---|---|---|---|
| es | 2.7% → 1.9% | 9 → 7 | 1 → 1 |
| pt | 5.3% → 2.9% | 34 → 6 | 6 → 3 |
| cs | 8.8% → 2.0% | 84 → 0 | 46 → 14 |
| fi | 0.0% → 0.4% | 0 → 0 | 5 → 5 |

Lines v15 published and v21 left unchanged: es 286,236 of 286,906 (670 moved
because a restored self-reading competed); pt 284,384 of 285,995 (1,607
self-reading, 2 phrase fallbacks no longer needed, 2 sense-level ties);
cs 284,401 of 284,402 (1 phrase fallback).

Cards: cs ty "you", tu "here", sem "hither", jednou "once", já "I", smrt
"death", nevím "to know", ona "she"; es sé saber "to know", este "this";
pt obrigado "thanks", tu "you", pessoa "person", mar "sea", dois "two";
fi missä "where", tässä "here", huomenta "good morning", älä "don't!",
kanssa "with", entä "what about" (kept).
