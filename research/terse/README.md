# TERSE-2 — conservative card-back trimming

Implemented 2026-10-11. Policy: `learner-card-trimming/v1`.

## Policy and provenance

Trimming belongs in the shared client presentation selector. Kaikki’s first English gloss supplies the translation; its adapter projects recognized grammar notes and extracts contexts from raw glosses, companion frames and short sub-glosses. The shipped Portuguese data also carries long explanatory contexts and repeated clauses. Spanish r5 uses SpanishDict, including release-composed multiword definitions. Length alone does not identify an explanation or a safe cut.

Release artifacts, source metadata, sense IDs, menu IDs and WSD inputs are unchanged. Reverse cues still receive original meanings before the presentation selector runs. The optional `transformation` field declares the policy, applied rules, original gloss and original context; `note.original` carries that same record into the existing information dialog. All prior presentation fields remain available.

Rules select whole clauses, respect brackets, retain argument slots and usage restrictions, preserve spelling targets, and keep complete translations containing words such as “that”. A known colon frame can introduce a translation; it is never used as a generic delimiter. Commas detach recognized editorial explanations only outside brackets and after a standalone head. Contrast and conditional tails remain intact. If shortened siblings cannot be distinguished, the full gloss stays. 84 characters is an audit threshold, not a display cap. The existing context and metadata rules remain in place, with original context recoverable even when it was reduced to a label or metadata.

No pipeline, provider policy, release schema or English conjugation rules were changed. UI transformations are explicitly labelled rather than presented as new native dictionary data.

## Repeatable audit

From the repository root:

```sh
node scripts/audit_terse.mjs ../Fluency-Workspace a31031c0 > /tmp/terse-audit.json
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/app -t .
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/research/terse/preview.html` for the renderer preview. `audit.json` records character and whitespace-word distributions for stored gloss/context, dictionary projections, sense cues and final production glosses, plus the 30 longest distinct glosses and contexts in each deck. Counts are sense-row weighted; longest lists deduplicate exact source text. Final production glosses use each release’s conjugation table and canonical example. This measures the shared presentation selector, not every group-layout or redundancy-cleanup step in flashcards.js.

## Results

| Metric | pt r3 before → after | es r5 before → after |
|---|---:|---:|
| Presented glosses over 84 chars | 146 → 102 | 5 → 5 |
| Final production glosses over 84 chars | 140 → 94 | 5 → 5 |
| Introduced unmatched brackets | 0 | 0 |

Portuguese’s final rows over the review threshold fall by about one third. Its maximum grows from 170 to 195 characters because restrictions and otherwise indistinguishable meanings are now retained. Spanish’s length distribution is essentially unchanged; the change restores complete alternatives on a few rows. No shortened item in the longest-case review lacks its verbatim original-text fallback.

## Longest-gloss review

Reviewed the 30 distinct longest source glosses per deck against their projected gloss, cue, and original text. “Existing projection” means the previously compact display is retained with a full-text fallback. Long synonym lists stay whole; pre-truncated source definitions are flagged without inventing repairs.

### pt — pt-speech-v24-headway-r3-10000x30-slim

| Word | Display gloss | Outcome |
|---|---|---|
| planta | plant | Existing projection; original recoverable |
| galáxia | galaxy | Safe complete translation / relationship |
| rios | river | Existing projection; original recoverable |
| antibióticos | antibiotic | Existing projection; original recoverable |
| federais | federal | Existing projection; original recoverable |
| sopa | soup | Existing projection; original recoverable |
| fosse | even; only | Safe complete translation / relationship |
| certidão | certificate | Safe complete translation / relationship |
| dom | Sir | Existing projection; original recoverable |
| correctamente | pre-reform spelling of corretamente | Safe complete translation / relationship |
| electricidade | pre-reform spelling of eletricidade | Safe complete translation / relationship |
| directamente | pre-reform spelling of diretamente | Safe complete translation / relationship |
| espectacular | pre-reform spelling of espetacular | Safe complete translation / relationship |
| actualmente | pre-reform spelling of atualmente | Safe complete translation / relationship |
| exactamente | pre-reform spelling of exatamente | Safe complete translation / relationship |
| actividades | pre-reform spelling of atividade | Safe complete translation / relationship |
| distracção | pre-reform spelling of distração | Safe complete translation / relationship |
| correcção | pre-reform spelling of correção | Safe complete translation / relationship |
| detectives | pre-reform spelling of detetive | Safe complete translation / relationship |
| inspecção | pre-reform spelling of inspeção | Safe complete translation / relationship |
| inspector | pre-reform spelling of inspetor | Safe complete translation / relationship |
| objectivos | pre-reform spelling of objetivo | Safe complete translation / relationship |
| optimista | pre-reform spelling of otimista | Safe complete translation / relationship |
| protecção | pre-reform spelling of proteção | Safe complete translation / relationship |
| protector | pre-reform spelling of protetor | Safe complete translation / relationship |
| activado | pre-reform spelling of ativado | Safe complete translation / relationship |
| actuação | pre-reform spelling of atuação | Safe complete translation / relationship |
| colecção | pre-reform spelling of coleção | Safe complete translation / relationship |
| correcta | pre-reform spelling of correto | Safe complete translation / relationship |
| direcção | pre-reform spelling of direção | Safe complete translation / relationship |
### es — es-speech-v24-headway-r5-10000x30-slim

| Word | Display gloss | Outcome |
|---|---|---|
| imperio | Ottoman Empire (a large former Turkish empire centered in modern Turkey that ruled over much of S... | Malformed upstream; retained |
| contrario | on the contrary, conversely, to the contrary, contrariwise, on the other hand, in contrast, instead | Retained whole |
| puerto | Puerto Rico (a commonwealth, island and dependent territory of the United States in the Caribbean | Malformed upstream; retained |
| tiene | Used to downplay a situation | Existing projection; original recoverable |
| aire | Used other than figuratively or idiomatically: see en, el, aire. in the air, up in the air | Retained whole |
| justo | just in time; right on time; right on cue, in the nick of time, right on schedule | Retained whole |
| pasa | what's up?; what’s the matter?; what is the problem?; what is wrong?; what's up? | Retained whole |
| peso | to lose weight, to shed weight, to reduce weight, to cut weight, to drop weight | Retained whole |
| amor | for God's sake, for the love of God, for Christ's sake, for crying out loud | Retained whole |
| si | if only | Existing projection; original recoverable |
| partir | from, as of, starting from, beginning, starting in, beginning in | Retained whole |
| ya | no longer, no more, not anymore, not any more, not any longer | Retained whole |
| es | it's just that, because; it's not that | Safe complete translation / relationship |
| vete | fuck you, fuck off, get fucked, go fuck yourself, go to hell | Retained whole |
| supone | it is supposed, it is assumed; it is supposed to be that way | Complete alternatives restored |
| cago | synonym of me cago en la leche; fuck everything, holy fuck | Retained whole |
| máximo | at most, at the most, maximum, up to, tops, at best, max | Retained whole |
| momento | at the moment, at present, for now, for the time being | Retained whole |
| medida | largely, greatly, to a large extent, to a great extent | Retained whole |
| borde | on the verge of, on the brink of, on the precipice of | Retained whole |
| espalda | to turn one's back; to refuse to help or aid somebody | Retained whole |
| además | as well as; in addition to, besides, along with | Retained whole |
| huevo | forcedly having no choice and with great effort | Retained whole |
| plazo | short-term, in the short term, in the short run | Retained whole |
| hecho | in fact, actually, indeed, as a matter of fact | Retained whole |
| curso | ongoing, under way, underway, current, present | Retained whole |
| hora | per hour, an hour; hourly; on an hourly basis | Retained whole |
| pasó | what's happening?, what's up?; what happened? | Retained whole |
| voluntad | freely; under one's own free will; willingly | Retained whole |
| verdad | it may be true that; it may be the case that | Complete alternatives restored |

## Longest-context review

All 30 distinct longest contexts per deck were checked. Companion frames remain cues, explanatory paragraphs stay in notes, and unchanged legacy cues are recorded rather than treated as new trimming. Original contexts are recoverable verbatim. The existing terse context labels can still read awkwardly (for example “in his; her” and “or of which there is only one at a time”); this change preserves their originals rather than synthesizing new wording.

### pt

| Word | Display cue | Outcome |
|---|---|---|
| o | when stressed | Existing cue; full context in note |
| o | because it has already been mentioned | Existing cue; full context in note |
| pelos | — | Existing cue; full context in note |
| o | or of which there is only one at a time | Existing cue; full context in note |
| análises | qualitative and quantitative examination of certain substances in the body | Existing cue; full context in note |
| darmos | + a / para | Existing cue; full context in note |
| tabaco | — | Existing cue; full context in note |
| porquê | — | Existing cue; full context in note |
| máquinas | person or organisation that seemingly acts like a machine | Existing cue; full context in note |
| sinais | sign | Existing cue; full context in note |
| darmos | + a / para | Existing cue; full context in note |
| sexo | gender | Existing cue; full context in note |
| não | negates the meaning of the verb or adverb | Existing cue; full context in note |
| ovos | — | Existing cue; full context in note |
| tribos | cohesive group of people | Existing cue; full context in note |
| derem | + a / para | Existing cue; full context in note |
| darmos | + em | Existing cue; full context in note |
| monstro | a fictional creature with hideous traits | Existing cue; full context in note |
| sé | a neighborhood of the city of Porto | Existing cue; full context in note |
| pirâmide | — | Existing cue; full context in note |
| tribos | cohesive group of people | Existing cue; full context in note |
| cesta | — | Existing cue; full context in note |
| nos | — | Existing cue; full context in note |
| literatura | a body of written works collectively | Existing cue; full context in note |
| gays | — | Existing cue; full context in note |
| sinais | a visible or otherwise perceivable indication of something | Existing cue; full context in note |
| missões | set of tasks that fulfills a purpose or duty | Existing cue; full context in note |
| darão | + a / para | Existing cue; full context in note |
| braço | sleeve | Existing cue; full context in note |
| tendes | to be related in some way to | Existing cue; full context in note |
### es

| Word | Display cue | Outcome |
|---|---|---|
| hago | I'm producing or creating | Existing cue; full context in note |
| pongámonos | — | Existing cue; full context in note |
| hago | I'm completing | Existing cue; full context in note |
| estan | — | Existing cue; full context in note |
| hago | I produce or create | Existing cue; full context in note |
| ponme | — | Existing cue; full context in note |
| ponme | — | Existing cue; full context in note |
| hago | I complete | Existing cue; full context in note |
| disculpe | — | Existing cue; full context in note |
| contigo | — | Existing cue; full context in note |
| consigo | in his; her | Existing cue; full context in note |
| perdona | asks for something to be repeated | Existing cue; full context in note |
| venían | — | Existing cue; full context in note |
| este | — | Existing cue; full context in note |
| déjale | — | Existing cue; full context in note |
| dándole | handing over; lending | Existing cue; full context in note |
| parece | — | Existing cue; full context in note |
| ponme | — | Existing cue; full context in note |
| déjale | — | Existing cue; full context in note |
| llegaba | — | Existing cue; full context in note |
| tai | — | Existing cue; full context in note |
| muévase | imperative | Existing cue; full context in note |
| off | — | Existing cue; full context in note |
| hágalo | imperative | Existing cue; full context in note |
| sube | — | Existing cue; full context in note |
| consigo | accompanying him or her | Existing cue; full context in note |
| pensé | I reflected | Existing cue; full context in note |
| muévase | imperative | Existing cue; full context in note |
| perdone | — | Existing cue; full context in note |
| háganlo | imperative | Existing cue; full context in note |

## Validation and review

App suite: **261 tests passed** (baseline: 260). Regressions cover nested parentheses, spelling targets, slots, restrictions, contrast/negation, sibling distinctions, explicit translation frames, immutable input, deterministic output and original-text recovery from already projected inputs.

Browser review used the shared renderer preview at 390 × 844, including a grouped-sense example. Confirmed no horizontal page overflow, complete original text in the dialog, focus capture, Tab containment, Escape dismissal and focus restoration. This preview does not reproduce the complete flashcard grouping controller. The app’s existing grouping and production-cue tests also pass.

Staging deployment uses the committed ref through `scripts/deploy_staging.py`. Review the audited releases with the `ptRelease=pt-speech-v24-headway-r3-10000x30-slim` and `esRelease=es-speech-v24-headway-r5-10000x30-slim` query parameters; Staging’s default decks may be newer. Production promotion is separate.
