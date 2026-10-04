# Conjugation sources for Czech, Portuguese, French, and Dutch

Research measured live menus against pin-able sources. This note records the
chosen adapters, the optional layers that were built, and the languages that
now ship a Conjugate drawer on the live speech compositions that select a
layer (`*-conj` releases). Missing headwords stay listed; Dutch still has no
deck.

App conclusions (English inflection, dummy *it*, come-back list): `docs/open/conjugations.md`.
Come-back row: `OPEN.md`.

## Envelope that stays shared

Pin one snapshot → `conjugation-layer/v1` joined by sense-menu **headword** →
optional `app/conjugations.json`. Card identity remains the observed surface.
Missing headwords are listed, never filled from a fallback. Reverse conjugation
in the SpanishDict adapter is menu resolution, not this layer.

`_requested_headwords` accepts both SpanishDict `VERB`/`AUX` and Wiktionary
`verb`/`aux`.

## Czech — Kaikki

Chosen source: the already-on-disk dump
`raw/wiktionary/enwiktionary-2026-09-06/kaikki.org-dictionary-Czech.jsonl`.
License CC BY-SA + GFDL. Pinned at
`raw/conjugations/cs/kaikki/enwiktionary-2026-09-06` (reference the dump; do
not copy 193 MB).

Live `cs-speech-v12-4000x10` menu
(`runs/cs/speech/20260915T162357Z-ca5c81cd`): **404/414** covered. Layer
`sha256:b683bd1d2f868afeb12d85b1735806ecfd961a315f1fc4d997299a1ecfdcfd50`.
Missing, listed not filled: `dosáhnout`, `odpověz`, `pošlete`, `předstírat`,
`přiznat`, `sklapnout`, `vysílat`, `vyžadovat`, `zabrat`, `zadržet`.

Past is gendered (`byl`/`byla`/`bylo`) and is stored only as a citation
`past_participle`, not as a person×tense paradigm. Aspect pairs stay out of
`conjugation-layer/v1`. The Conjugate drawer stays gated until a composition
selects this layer.

MorfFlex CZ is CC BY-NC-SA 4.0 and is a tag lexicon, not a learner table. It is
not used. verbecc is refused for `cs`.

## Portuguese and French — verbecc XML, ML off

Live Portuguese menu (`pt-speech-v12-6000x10`, run
`20260915T130807Z-4120e951`): **955/1074** covered. Layer
`sha256:4f2abe83c43223cb81e04386279d2a25199f7b3a20c8529e0233b6deb483afd7`.
Pin: `raw/conjugations/pt/verbecc/verbecc-installed`. Machine-learning
prediction stays off. Missing 119, listed not filled:

`abelhar`, `acabaram`, `acessar`, `acharam`, `agendar`, `aliançar`,
`apanharam`, `apareceram`, `arrepender`, `atacaram`, `atendar`, `atrever`,
`aulir`, `avisa`, `baratar`, `bastir`, `bombar`, `bundar`, `cadear`,
`camperar`, `candidatar`, `cartar`, `caíram`, `chamaram`, `chegaram`,
`chinar`, `chipar`, `colar velcro`, `colocaram`, `comandar`, `começaram`,
`complexar`, `conheceram`, `conseguiram`, `decidiram`, `deixaram`, `deram`,
`desapareceram`, `descobriram`, `digamos`, `digitar`, `dignar`, `disseram`,
`domingar`, `dêem`, `encontraram`, `entraram`, `esquerdar`, `estiveram`,
`falaram`, `ficaram`, `fizeram`, `florestar`, `foram`, `frescar`, `fugiram`,
`futurar`, `gatar`, `gestar`, `gregar`, `hei-de`, `há-de`, `identificar`,
`impactar`, `janelar`, `levaram`, `listar`, `logar`, `mandaram`, `mandatar`,
`mataram`, `mestrar`, `militar`, `mitar`, `morreram`, `mudaram`, `objectivo`,
`ouviram`, `passaram`, `pediram`, `pegaram`, `pensaram`, `perderam`,
`pistolar`, `popular`, `porrar`, `puseram`, `pára`, `queixar`, `roubaram`,
`ruar`, `saíram`, `sejar`, `sexar`, `sextar`, `suicidar`, `tacar`, `tankar`,
`telar`, `tentaram`, `tipar`, `tiraram`, `tiveram`, `tornaram`, `trago`,
`trampar`, `tretar`, `trouxeram`, `unar`, `usaram`, `vamos`, `vampirar`,
`vieram`, `viger`, `viram`, `voltaram`, `vêem`, `zerar`, `zonar`.

Workspace-active French is the 200-card audit
`fr-speech-v7-dual-metadata-v3-20260910` (menu from
`20260822T172017Z-651bcd8e`): **29/35** covered. Layer
`sha256:17a4de33b546a86f6fc214d3a3256c2babff39cc7588d26621bb93a49f87cfe8`.
Pin: `raw/conjugations/fr/verbecc/verbecc-installed`. Missing:
`dit`, `falloir`, `soir`, `soit`, `vader`, `voilà`. `falloir` is in the XML
as an impersonal with empty person slots; it is listed missing rather than
published as a hollow 6-cell table. Re-measure before a production French
deck. `config.json` currently points at a v4 path that is not in
Fluency-Workspace.

Kaikki present-6 coverage is also high (PT 1007/1074, FR 30/35). verbecc is the
chosen Romance generator because it ships the bounded simple-tense inventory;
Kaikki remains the provider-native alternative. XML is GPL-2+ (Verbiste/mlconjug).

European Portuguese locale `pt-PT` collapses verbecc's 10 pronoun rows to
eu/tu/ele/nós/vós/eles. French collapses il/elle/on and ils/elles.

## Dutch — no drawer

`hasData: false`, no `releases/nl`, no live sense menu, no default conjugation
locale, no `raw/conjugations/nl` pin. `fluency migration verbecc-conjugation-snapshot
--language nl` raises: Dutch has no live speech menu or release, and verbecc has
no nl language. A Dutch Kaikki dump exists for a future language package; it is
not coverage of a live deck. CELEX-2 NL is not fetched.

## App renderer

`flashcards-conj.js` carries pronoun/tense maps for Spanish, Portuguese, French,
Czech, and Dutch. Empty-state links use each language's `referenceLinks.conjugation`
(Wiktionary/Reverso/Verbix), not a hardcoded SpanishDict URL. Live speech config
now points `conjugationsPath` at the `*-conj` releases. Dutch stays `null`.

## Commands

```bash
PYTHONPATH=src python -m fluency migration kaikki-conjugation-snapshot \
  --language cs --snapshot-id enwiktionary-2026-09-06 \
  --source $WORKSPACE/raw/wiktionary/enwiktionary-2026-09-06/kaikki.org-dictionary-Czech.jsonl

PYTHONPATH=src python -m fluency migration verbecc-conjugation-snapshot \
  --language pt --snapshot-id verbecc-installed
PYTHONPATH=src python -m fluency migration verbecc-conjugation-snapshot \
  --language fr --snapshot-id verbecc-installed

PYTHONPATH=src python -m fluency enrichment build-conjugations \
  --sense-menu <menu.json> --source-snapshot <pin dir> --locale cs-CZ
```

The last command stores an optional layer artifact. It does not compose or
activate a release.
