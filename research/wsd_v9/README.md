# WSD v9 research harness

This directory is deliberately isolated from `src/fluency`. Nothing here is
active in the production WSD runner, release builder, or deck pipeline.

The first experiment compares four source-only views of a target occurrence
against sense-labelled dictionary examples:

1. unanchored context-word presence;
2. the abstract dependency frame around the target;
3. exact lexical fillers in target-anchored relations;
4. the same relations with static-vector similarity between matching slots.

Candidate menus remain closed. Aligned English is never read. Dictionary
examples are decoded behind provider adapters and become the same
`relation-profile/v1`-style JSON record for SpanishDict and Wiktionary. Missing
examples and failed target alignment remain explicit statuses rather than
silent empty feature vectors.

Run the Spanish hard-panel probe:

```bash
.venv/bin/python -m research.wsd_v9.relation_probe \
  --panel /path/to/hard_200/panel.jsonl \
  --menu /path/to/spanishdict.json \
  --output-dir /tmp/wsd-v9-relation
```

Run the full provider-parity extraction:

```bash
.venv/bin/python -m research.wsd_v9.parity_probe \
  --spanish-menu /path/to/es/sense-menu.json \
  --portuguese-menu /path/to/pt/sense-menu.json \
  --output-dir /tmp/wsd-v9-parity
```

Run the source-only sibling-contrastive probe after the relation probe (the
candidate-predictions input freezes the exact POS-filtered candidate set):

```bash
.venv/bin/python -m research.wsd_v9.contrastive_probe \
  --panel /path/to/hard_200/panel.jsonl \
  --menu /path/to/spanishdict.json \
  --candidate-predictions /tmp/wsd-v9-relation/predictions.jsonl \
  --output-dir /tmp/wsd-v9-contrastive
```

This produces a reusable source-only artifact: frozen BETO meaning prototypes,
plus tiny logistic pair scorers trained with either random negatives or hard
same-surface sibling negatives. The random-negative model is a required
control: if it matches the sibling model, the learner has probably learned
lemma identity rather than sibling-sense distinctions.

The corpus-first WSI probe masks a target, clusters its substitute distribution,
and maps clusters back to the closed menu through dictionary examples. It emits
silhouette, seed-stability, cluster-size, and menu-collision diagnostics; those
are the rejection criteria, not a hand-picked cluster visualization.

```bash
.venv/bin/python -m research.wsd_v9.wsi_probe \
  --language es \
  --menu /path/to/spanishdict.json \
  --corpus /path/to/sentence_bank.jsonl \
  --surfaces por,como,salir,antes,este,clase,parte,tipo,pasado,sobre \
  --panel /path/to/hard_200/panel.jsonl \
  --candidate-predictions /tmp/wsd-v9-relation/predictions.jsonl \
  --span-model es_core_news_lg \
  --encoder dccuchile/bert-base-spanish-wwm-cased \
  --output-dir /tmp/wsd-v9-wsi
```

Use `--surfaces @panel` to run every surface in the supplied panel.

The evidence/prior coefficient in the scored probe is selected with grouped
five-fold cross-validation. Every occurrence of a surface stays in one fold.
That makes the result useful for falsification, but it does not create a clean
v9 acceptance set: a technique chosen because of this panel still needs a new
held-out sibling-sense set before promotion.
