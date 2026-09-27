# Reference Documentation

Measurements, architectural specifications, and pipeline contracts across Fluency modes.

## Organization

The reference directory is organized into two primary operational modes:

```
docs/reference/
├── lyrics/                 # Lyrics Mode pipelines, WSD hierarchy, and artist tooling
│   └── wsd-hierarchy.md    # 5-Tier WSD hierarchy, inflection, and token rules
├── speech/                 # Speech Mode pipelines (MEND, OpenSubtitles, Tatoeba)
│   └── README.md           # Speech reference index
└── shared/                 # Shared metadata architecture and dictionary parity
```

## Shared & Historical WSD References

| File | What it is |
|---|---|
| `metadata_architecture.md` | Canonical metadata families, shared/provider/language adapter ownership, presentation boundary. |
| `spanishdict_metadata.md` | SpanishDict metadata parsing, features, and bridge contracts. |
| `wiktionary-spanishdict-parity.md` | Wiktionary vs SpanishDict calibration and parity benchmarks. |
| `portuguese-v7-baseline.md` | The first Portuguese WSD measurement, POS-bridge, and ladder numbers. |
| `wsd_dead_ends.md` | Experiments implemented, measured, and rejected. |
| `wsd_open_threads.md` | Leads that were partly measured and not ruled out. |
