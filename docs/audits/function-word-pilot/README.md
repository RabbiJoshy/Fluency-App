# Function-word pilot — 15 October 2026

Start with [the side-by-side preview](preview.html). Choose a language, word and pattern, then cycle through the examples. This is an editorial proposal, not a deployed change.

## What changed

Reviewed **12 words, 24 patterns and all 121 examples**. Proposed clearer wording for all 24 patterns and revised **39 examples** (including translation-only and highlighting-only changes); retained 82. The whole-suite scan covers **81 words, 115 patterns and 576 examples**.

The highest-value corrections are:

1. **Teach the right pattern.** Portuguese object **o** currently displays `Verb + o`, although its examples use `o + verb`. Spanish **nos alegramos** is not an example of the displayed “us / to us” rule; its replacement fits that rule, and the original remains in the ledger. Both **se** cards now acknowledge that the word can belong with a verb, rather than claiming it always means “oneself”. Spanish impersonal/passive **se** is no longer described as a “general or collective truth”.
2. **Make the coloured chunks truthful.** Six **que** examples include the main sentence inside the relative-description highlight. Spanish **de** highlights “my brother visited us” rather than “my brother”; three **al** examples include unrelated time/manner details in the destination. The proposals tighten those boundaries without changing the sentences.
3. **Reduce effort without losing meaning.** Replace “Verbal Valency”, “Nominal Binding” and “Temporal Nexus” with ordinary explanations. Complete English fragments, remove a dangling English modifier, simplify distracting constructions, and replace the Portuguese idiom *homem de palavra* with a transparent ownership example. Keep meaningful tense differences, and do not claim a short formula covers every usage.

Existing first examples were already useful anchors, so their order stays unchanged. The Portuguese **o** anchor is shortened. New target sentences carry an explicit original-teaching-example label; existing source labels are preserved in the before records. Attribution labels such as “Subtitles” are inherited claims, not verified citations.

## Whole-suite findings and next priorities

The checker found **43 jargon flags across fields**: 23 Portuguese and 20 Spanish. It found no rules over 20 words, examples over 15 words, missing translations, within-word duplicate sentences or structurally invalid highlights. These results do **not** measure naturalness or semantic correctness: the chunk-boundary and usage errors above passed the mechanical checks.

- **First:** resolve the pilot's teaching mismatches and compare its simpler copy in the preview.
- **Next:** review the 11 remaining jargon flags outside the pilot: Portuguese **para, como, me, ao, quando** and Spanish **para, como, cuando**. “Infinitive” may be useful if explained; a flag is not a demand to remove a word.
- **Then:** extend semantic sentence review beyond the pilot. No claim is made that the other 455 examples have received an editorial naturalness review.

The proposed pilot has no checker flags. Rules describing a subset of uses remain scoped to their examples; no new usage groups, classifier rules or live membership changes were made.

## Separate second task: membership discovery

The [candidate report](missing-words.md) and [evidence file](missing-words.json) compare both configured 10,000-card decks with the curated suites, existing inventory tables and dictionary POS. They include **453 broad candidates** (216 Spanish, 237 Portuguese), plus nine connector expressions already labelled inside parent cards. This broad list includes homographs, minor dictionary senses and editorial probes; it is **not** a list of 453 approved additions.

A focused next batch, with release rank in parentheses:

| Language | Strong candidates absent from curated cards |
|---|---|
| Spanish | **no** (3), **qué** (13), **o** (58), **él** (60), **ella** (74), **ni** (127), **nosotros** (143), **les** (152), **mientras** (290), **aunque** (420) |
| Portuguese | **não** (5), **você** (28), **ou** (73), **nós** (75), **dos** (85), **das** (140), **às** (237), **nas** (240), **aos** (265) |

All of those already have release cards; the gap is their curated function-word treatment. Negation was missing from the narrow inventories, so explicit probes were added rather than assuming the inventories were complete. Keep **nos/nós**, **el/él**, **que/qué** and **si/sí** distinct.

Portuguese **pra** (255) deserves a register-aware review beside **para**, not automatic duplication. Family probes **àquelas, àquilo, nuns, numas, duns, dumas** have no exact card in the configured release and no curated entry. Their absence as independent cards does not establish absence from sentences or other grouped representations. Verify dictionary forms, register and grouping before adding them. The main report includes further contraction candidates and explains its bounded search.

## Language references and remaining judgments

- [RAE: se](https://www.rae.es/dpd/se) distinguishes reflexive/pronominal uses from impersonal/passive constructions. The revised rule avoids treating all examples as literal self-action.
- [RAE: alegrar, alegrarse](https://www.rae.es/dpd/alegrar) supports separating *nos alegramos* from the object-pronoun example group. The sentence is preserved for later usage review.
- [RAE: al](https://www.rae.es/dpd/al) provides the contraction reference. The pilot's destination rule describes these examples rather than asserting a universal contraction rule without exceptions.
- [Ciberdúvidas: convidamo-lo / o convidamos](https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/convidamo-lo-vs-o-convidamos/33196) supports the Brazilian before-verb placement used here. The pilot does not teach that this is the only possible position.
- [Priberam: pra search](https://dicionario.priberam.org/pesquisar/pra) and [Michaelis: pra](https://michaelis.uol.com.br/moderno-portugues/busca/portugues-brasileiro/pra) are reference starting points for the reduced-form candidate review, not blanket approval of every family probe.

Naturalness decisions are an editorial first pass, not native-speaker sign-off. Original attribution accuracy, the formal/everyday balance for Portuguese object **o**, and the final grouping of **se** uses remain review considerations. The preview deliberately retains the current number of patterns; splitting self-action from verb-bound uses is outside this pilot.

## Deliverables and verification

- [Review report](review.md): full before/after wording and reasons.
- [Review ledger](review.json): every pattern and example, including retained examples, exact markup and provenance.
- [Portuguese proposals](pt.proposed.json) and [Spanish proposals](es.proposed.json): existing schema, pilot words only.
- [Whole-suite scan](scan.md), [scan JSON](scan.json), and [proposal scan](proposal-scan.json).
- [Remaining-word report](missing-words.md): ranked candidates, contraction list, duplicate handling and release evidence. The JSON includes input hashes and card IDs.

Eight focused automated tests pass: Unicode/HTML word counting, thresholds, missing translations, duplicate identity/scope, invalid markup, complete pilot coverage/provenance, accent-preserving discovery and read-only checker operation. Browser checks cover both languages, contraction parts, changed formulas/translations and example navigation including wraparound. Visual inspection confirms readable side-by-side cards. This audit does not modify the live grammar suites or generated runtime card file. Unrelated concurrent renderer changes are left intact.

To reproduce from the repository root:

```sh
python3 research/function_word_audit/check.py --format markdown
python3 research/function_word_audit/check.py --format json
python3 research/function_word_audit/pilot.py
python3 research/function_word_audit/discover.py --workspace ../Fluency-Workspace
python3 -m unittest discover -s tests/function_word_audit -v
```

The checker writes only to stdout. The pilot and discovery tools write only to this audit output directory. Discovery requires the release artifacts referenced by `app/config/config.json`; missing artifacts cause a visible error rather than an incomplete report. Open `preview.html` directly in a browser; it is self-contained and needs no server or network connection. Existing HINGE assignment work remains parked.
