# Dutch and Finnish 2,000-card release candidates

Status: Dutch remains an inactive candidate. Finnish was activated on 2026-09-27
and packaged in static deployment candidate `finnish-2000-release-20260927`.

## Shared release shape

- 2,000 surface cards in spoken-frequency order.
- Five examples per card through rank 1,000; three through rank 2,000.
- Tatoeba and recent aligned OpenSubtitles example sources.
- Kaikki/English Wiktionary as the production sense-menu base.
- WordNet is comparison evidence, not silently merged into the menu.
- English cognate map beside the release.
- Every example remains explicitly unassigned until the language's WSD benchmark is
  complete and its exact model revisions are pinned.

## Dutch

- Run: `runs/nl/speech/20260926T171858Z-f7b6aa3f`
- Candidate: `releases/nl/speech/nl-speech-v1-2000x5-3-candidate`
- Menus: 1,899 ready; 101 explicit `no_menu` cards.
- Harvest: 88,942 retained candidate assignments.
- Open Dutch WordNet direct overlap: 1,080 cards; only 13 provider gaps overlap.
- Surface ledger: 2,000 cards; 122 currently require review.
- Cognates: 891 cards scored; 248 pairs at 0.75+ are queued for calibration.

## Finnish

- Run: `runs/fi/speech/20260926T171858Z-4e22885d`
- Candidate: `releases/fi/speech/fi-speech-v1-2000x5-3-candidate`
- Active workspace release: **yes** (`releases/fi/speech/active.json`).
- Packaged app: `deployments/finnish-2000-release-20260927/site`.
- Menus: 1,884 ready; 116 explicit `no_menu` cards.
- Harvest: 88,113 retained candidate assignments.
- FinnWordNet direct overlap: 708 cards; only 15 provider gaps overlap.
- Surface ledger: 2,000 cards; 68 currently require review.
- Cognates: 709 cards scored. The 0.85 cutoff is provisional; 22 pairs at 0.70+
  are queued for calibration.

## Manual release gate

For each language, complete every row in:

- `reviews/<language>/<run-id>/manual-review.jsonl`
- `reviews/<language>/<run-id>/cognate-review.jsonl`

The first file contains all 2,000 surfaces, real example samples, provider-menu status
and the WordNet comparison. Record one outcome for every row. Put durable menu
exceptions in `config/declared/<language>/onboarding-review.json`; put exclusions and
keep decisions into the surface observation/adjudication store. Common grammatical
words, interjections and fillers should receive a small curated menu when raw dictionary
senses are not useful learner choices.

After those queues are closed:

1. rebuild the surface ledger;
2. rerun the immutable menu and harvest stages if declarations changed;
3. complete and pin the language-specific WSD benchmark;
4. rebuild and validate the candidate release;
5. run a final spot-check of high-frequency cards, every declaration, every menu gap
   and samples from each rank band;
6. activate and deploy explicitly.

Dutch intentionally remains `hasData: false`. Finnish is now enabled for Speech in
the packaged app; its unresolved review and WSD limitations remain recorded above.
