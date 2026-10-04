# Reflexive / pronominal tagger (es, pt)

Decides, for one verb occurrence in one sentence, whether the verb is used
pronominally (*me hice rico* → `hacerse`; *virou-se* → pronominal sense of
`virar`) or not (*me hace falta* → `hacer`; *se ele virar* → "if"). Results
are in [FINDINGS.md](FINDINGS.md).

The tagger itself now lives in `src/fluency/reflexive/` and is wired into WSD
from v23 (`config/wsd/models/{es,pt}-v23-1.json`; tags per freeze from
`scripts/build_reflexive_tags.py`, runs from `scripts/v23_runs.py`). This
folder keeps the evaluation harness and the hand-labelled gold sets; rerun the
blind sets after any change to the package.

## Output

`policy(doc, span)` returns one of:

| label | meaning | menu action it licenses |
|---|---|---|
| `NO_SE` | no reflexive clitic belongs to this verb | drop the pronominal family |
| `SE_FIRM` | a reflexive clitic belongs to it and agrees with its subject | drop the non-pronominal family |
| `BOTH` | 3rd-person *se* that may be passive/impersonal, or no recoverable controller | keep both, WSD decides |
| `Z` | not a verb | none (POS gate's job) |

Provider parity: SpanishDict files pronominal uses as separate headwords
(`hacer` / `hacerse`); Wiktionary files them as senses tagged `pronominal` or
`reflexive=true` under one headword. The tagger answers the same question for
both; only the consumer differs (headword filter vs sense filter).

## Dependencies

- spaCy `es_dep_news_trf` (Spanish) and `pt_core_news_lg` (Portuguese) for
  POS, dependencies and, in Spanish, the clitic labels as a tie-breaker.
- Paradigm tables built **only from Wiktionary (Kaikki)**: form → (lemma,
  mood, tense, person, number). No verbecc, no Jehle.

## Files

| file | does |
|---|---|
| `src/fluency/reflexive/paradigms.py` | builds `forms-<lang>.json` from a Kaikki dump |
| `src/fluency/reflexive/spanish_base.py`, `spanish.py` | Spanish detector (`spanish.policy`) |
| `src/fluency/reflexive/portuguese.py` | Portuguese detector (`portuguese.policy`) |
| `src/fluency/reflexive/data/se-prior-es.json` | per-lemma pronominal vs passive *se*, AnCora **train** only |
| `src/fluency/reflexive/data/se-prior-pt.json` | the same from PetroGold **train** only |
| `src/fluency/reflexive/data/pt-pronominal-capable.json` | pt verbs with a Wiktionary pronominal/reflexive sense |
| `paths.py` | gold and results locations for the harness |
| `data/gold/*.json` | hand-labelled in-domain sets (R / P / N / Z per item) |
| `gold_ud_es.py`, `gold_ud_pt.py` | token-level gold from UD treebanks |
| `parse.py` | caches spaCy parses as DocBin |
| `eval_es.py`, `eval_pt.py`, `eval_ud_pt.py` | scoring (`REFL_PARSER=lg` scores Spanish with the fast parser) |
| `impact.py` | what a hard filter would change in live v22 assignments |

## Reproduce

```bash
W=../Fluency-Workspace/raw/wiktionary
PY=.venv/bin/python; R=research/reflexives
mkdir -p ../Fluency-Workspace/cache/reflexives
PYTHONPATH=src $PY -m fluency.reflexive.paradigms es $W/enwiktionary-2026-09-13/kaikki.org-dictionary-Spanish.jsonl ../Fluency-Workspace/cache/reflexives/forms-es.json
PYTHONPATH=src $PY -m fluency.reflexive.paradigms pt $W/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl ../Fluency-Workspace/cache/reflexives/forms-pt.json
# UD treebanks into results/ud (git clone --depth 1 https://github.com/UniversalDependencies/UD_Spanish-AnCora etc.)
$PY $R/gold_ud_es.py es $R/results/gold-ancora.json $R/results/ud/UD_Spanish-AnCora/es_ancora-ud-{test,dev}.conllu
$PY $R/parse.py es_dep_news_trf $R/results/gold-ancora.json $R/results/ancora-trf.spacy
$PY $R/parse.py es_dep_news_trf $R/data/gold/subs-es.json $R/results/subs-es-trf.spacy   # likewise held-es
$PY $R/parse.py pt_core_news_lg $R/data/gold/dev-pt.json $R/results/dev-pt-sp.spacy      # likewise held, blind2, blind3
$PY $R/eval_es.py held            # subs | held | ancora
$PY $R/eval_pt.py blind3 show     # dev | held | blind2 | blind3
$PY $R/eval_ud_pt.py              # needs results/gold-ud-pt.json from gold_ud_pt.py + its parse
```

Parsing runs at about 300 sentences/s for the Spanish transformer and 1,400/s
for the Portuguese CNN on this machine. The fast Spanish parser
(`es_core_news_lg`) is not good enough: 7 commit errors on the subtitle sets
against 1.
