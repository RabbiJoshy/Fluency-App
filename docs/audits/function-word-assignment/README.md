# Automatic function-word assignment: close-out

The reusable batch assigner now labels Portuguese and Spanish occurrences and produces coloured spans against the existing card patterns. It uses parser structure, agreement and explicit lexical licences where necessary. Translations and editorial suitability do not gate syntax assignment. The approved UI and base example suites are unchanged.

## What shipped

- Language adapters for the pilot words, plus registered articles, possessives and subject pronouns. Coverage is explicit, not universal.
- Complete verb groups, noun phrases and contraction spans; occurrence-specific processing for repeated words; conservative abstention for ambiguous or unsupported uses.
- A batch command accepting raw sentences or cached parses. It records assignments and abstentions and exports a supplemental overlay with original provenance. Fresh parsing uses local Portuguese Stanza and Spanish spaCy models.
- Eight newly assigned examples added to the staging-only syntax trial, alongside the eight existing reviewed examples. Enable `?fwSyntaxTrial=1` on staging. Production ignores this switch. No examples were newly written for this batch.

## Evidence and limits

The earlier 48-sentence sample and the first 40 sentences here are development material. The final separate sample contains 20 harvested sentences, excluding previous selections. Syntax expectations were recorded before predictions; this is a small internal check, not an externally adjudicated benchmark.

Frozen v1 results: 11 supported uses, 8 assigned, all 8 correct patterns. Seven of the eight highlights were clean. One noun highlight included a trailing aside. Version v1.1 removes that aside and has a regression test; its revised result is not a new independent validation. Original final-check predictions remain frozen.

Three supported uses were missed: Portuguese `chapéu de basebol`, Portuguese `se armar em galo`, and Spanish `asegurarnos de que`. They remain unassigned rather than broadening rules without supporting evidence. Unsupported constructions, parser mistakes and unlicensed idioms still limit coverage. This is a working offline assignment pipeline, not live on-device NLP or universal coverage of every card.

Translations are retained verbatim and were not reviewed. Source suitability for curated/offline packs is a separate concern. Original OpenSubtitles attribution is retained in each record; source: [OpenSubtitles.org](http://www.opensubtitles.org/), via OPUS.

## Repeat the cached batch

```sh
python3 scripts/assign_function_word_examples.py \
  --input docs/audits/function-word-assignment/final-check/predictions.json \
  --parses docs/audits/function-word-assignment/final-check/parses.json \
  --output /tmp/fw-assignments.json --overlay /tmp/fw-overlay.json
```

For fresh sentences, omit `--parses` and use `.venv/bin/python`. Supply a JSON list (or `rows` object) containing `language`, `word`, `example_id`, `sentence`, optional `spans`, `translation`, `sentence_id` and `source`. Source metadata with `name` and `source_record_id` is required for export, but not for classification. Keep identifiers unique per sentence. The fresh parser cache is keyed by language, word and example ID so the same sentence can be classified for multiple words.

Each occurrence produces a candidate or abstention with a reason. Candidates include a stable pattern ID, matcher version and source-preserving HTML. The overlay is supplemental: it never edits the base suites or promotes itself into production. Rebuild the browser bundle after changing the trial overlay with `python3 scripts/sync_function_word_card_js.py`.

Validation: assignment unit/regression tests, app suite, and a fresh-parser smoke run in both languages. See `evaluation.json` for bounded final-sample counts and `assignments.json` for the v1.1 replay.
