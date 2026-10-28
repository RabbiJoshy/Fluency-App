# Complete vocabulary decks from the retained TV samples

The Spanish TV Series picker offers La Casa de Papel and Élite. “Complete” here
means every token form observed in the retained sample gets one card. It does
not mean all seasons were obtained or every line has an English translation.

| Sample | Episodes | Dialogue tokens | Cards | Levels | Cards with English examples |
| --- | ---: | ---: | ---: | ---: | ---: |
| Casa | 30, original numbering across Seasons 1–4 | 136,924 | 12,706 | 128 | 7,930 |
| Élite | 24, Seasons 1–3 | 99,442 | 8,378 | 84 | 7,301 |

Admission never depends on a frequency-list or dictionary hit. Names, numbers,
inflections, attached forms, slang and unrecognised tokens are retained. Cards
are ordered by their own occurrences in the Spanish dialogue; translated group
expansion never creates additional occurrences. Spelling is kept as observed
apart from case/typography normalisation. Forms are not merged into lemmas.

Canonical Speech words keep their existing identities, menus and definition
shard ranks. Additional forms use English Wiktionary's Spanish snapshot through
the existing Kaikki menu adapter, with exact published form-of relationships,
provenance and usage/grammar metadata. The snapshot is
`enwiktionary-2026-09-13`; attribution and entry-history links are retained per
sense. The 50k list helps recognise words; it does not itself supply definitions.
The generated compact lexicon is shared across both series and the browser
fallback. Repeated sense menus are stored once; surface grammar stays on the
individual form. All available menu senses remain inspectable, without WSD.

Forms absent from both lists are checked against the shared curated entity
registry and retained results from Turbo's exact-title Wikipedia resolver.
Entity data remains a candidate, with a neutral name gloss where appropriate;
it does not establish whether a name refers to a city or a character. The
separate optional entity acquisition hit provider throttling after 132 queries.
Unresolved entity checks remain pending and do not discard cards. Other unknown
forms are not automatically labelled slang. Casa currently has 676 cards with a
pending definition and Élite has 421. Some are numerals, names, loanwords or
attached forms; no English definition is fabricated for these.

Examples retain the existing conservative full-passage alignment policy. English
examples are preferred, while cards whose occurrences have no confident English
match keep Spanish examples. A dictionary gloss and a sentence translation are
separate. The reviewed Élite S01E08 phone mistranslation is explicitly excluded.

Inline supplementary cards use no Speech shard (`sourceRank: -1`) and preserve
their own study rank through session and preview hydration. The complete union
is used in setup, levels, search and study. Source changes invalidate prepared
vocabulary, and refresh failure retains the usable cached deck. Optional server
saving stays in the background. The Music inventory admission policy is unchanged.

The 2026-10-28 [SubDL API trial](subdl-api-trial.md) refreshes Casa acquisition
provenance and expands Élite to three seasons. Casa retains seven previously
reviewed Season 3 episodes because the API returned no Spanish Season 3 release.
Élite is entirely acquired through API-discovered downloads.

## Rebuild

With the retained raw subtitle files and Spanish Wiktionary dump available:

```sh
PYTHONPATH=src python3 scripts/build_series_presets.py \
  --workspace /path/to/Fluency-Workspace \
  --wiktionary /path/to/kaikki.org-dictionary-Spanish.jsonl
```

This build makes no network, translation-service, WSD, embedding or LLM requests.
Source hashes and episode members are recorded in each series source manifest.
The optional `resolve_series_entities.mjs` acquisition script uses the same Turbo
entity resolver and a retained result cache; it is separate from rebuilding or
opening the presets. Failed/throttled requests cannot drop words.

Checks cover every retained form and occurrence, inline menus and pending cards,
original character offsets, translated examples, canonical and supplementary
preview hydration, all 128 Casa levels, switching presets, rebuild fallbacks,
failed saving, and zero WSD worker starts.

## Earlier missing-English audit (2026-10-26)

Checked against every original cue and selected card example on 2026-10-26.
After upgrading translated repetitions, every form with an accepted bilingual
occurrence has at least one selected English example (guarded by a dataset test).

Casa has 4,776 cards without English examples; 3,646 occur once. Of 2,151 forms
occurring at least six times, 59 have no accepted English. Nine original-numbered
episodes have no attached English: S01E07–09 and S02E01–06. For example, all 21
occurrences of `camerún` are in untranslated S02E03. Accepted bilingual passages
cover 56,315 of 136,924 word occurrences (41.1%).

Élite has 665 cards without English; 602 occur once. Only one of the 633 forms
occurring at least six times lacks English: `subtítulos`, from subtitle credits.
Accepted bilingual passages cover 26,622 of 35,791 word occurrences (74.4%).
These coverage figures reflect retained timing/quality rules and short-line
exclusions, not whether English exists somewhere in the downloaded source files.
