# GRAFT: Domain & Slang Overlay Source Dossier

**Status:** Collecting ahead of GRAFT; source vetting and snapshot sign-off are incomplete.

This document is the research and source-vetting dossier for **GRAFT** (and downstream **VERSE** lyrics WSD). 
Its purpose is to record evaluated candidate sources, category taxonomies, and mapping strategies for non-standard, colloquial, and lyrics senses *before* generating snapshots.

---

## 1. Candidate Source Inventory

### 1.1 Spanish (Caribbean, Urban / Reggaeton, Colloquial)
- **Source Name**:
  - *Location / URL*:
  - *License / Access*:
  - *Format* (e.g. JSON, dump, scrape, API):
  - *Coverage & Volume*:
  - *Notes & Vetting Assessment*:

### 1.2 Portuguese (Brazilian Slang, Funk / Urban, Colloquial)
- **Source Name**:
  - *Location / URL*:
  - *License / Access*:
  - *Format*:
  - *Coverage & Volume*:
  - *Notes & Vetting Assessment*:

### 1.3 Czech (Obecná čeština, Slang, Discourse Markers)
- **Source Name**:
  - *Location / URL*:
  - *License / Access*:
  - *Format*:
  - *Coverage & Volume*:
  - *Notes & Vetting Assessment*:

---

## 2. Category Taxonomy & Target Expressions

### 2.1 Lyrics Slang & Regionalisms
- *Spanish*: Caribbean/Puerto Rican terms (*guagua*, *vaina*, *corillo*, *chavo*, *acicalao*).
- *Portuguese*: Urban/Rio/SP terms (*mano*, *rolê*, *grana*, *brecha*, *trampo*).
- *Czech*: Common colloquialisms (*kámo*, *prachy*, *hustý*, *fakt*).

### 2.2 Conversational Fillers & Discourse Markers
Pragmatic particles and conversational crutches that standard dictionary menus often miss or misattribute:
- *Spanish*: *o sea*, *bueno*, *en plan*, *a ver*, *tipo*.
- *Portuguese*: *né*, *tipo assim*, *então*, *aí*, *cara*.
- *Czech*: *jako*, *prostě*, *takže*, *vlastně*.

### 2.3 Formulaic Lyric Contractions & Elisions
- *Spanish*: *pa'* (*para*), *'to* (*todo*), *na'* (*nada*), *'tá* (*está*).
- *Portuguese*: *pra* / *pras* (*para a*), *tô* (*estou*), *tá* (*está*), *cê* (*você*).

---

## 3. Overlay Architecture Compatibility

All curated overlays must map cleanly into the `SenseOverlayEntry` interface (`src/fluency/wsd/overlays.py`):

```python
SenseOverlayEntry(
    overlay_id="es:slang:guagua:bus",
    headword="guagua",
    expression="guagua",
    part_of_speech="NOUN",
    translation="bus",
    definition="autobús o vehículo de transporte público (Caribe/Canarias)",
    source_type="slang", # "slang" | "lyrics" | "filler" | "regional"
    canonical_example={"target": "Esperamos la guagua.", "english": "We waited for the bus."},
    target_card_headwords=["guagua"]
)
```

---

## 4. Source Evaluation & Action Plan

- [ ] Vetted Spanish colloquial & lyrics sources identified
- [ ] Vetted Portuguese colloquial sources identified
- [ ] Vetted Czech slang & discourse sources identified
- [ ] Sample entries drafted for integration test
- [ ] Sign-off for snapshot generation under `raw/overlays/`

---

## 5. Spanish Speech Baseline Checkpoint (2026-09-19)

**Working hypothesis, not a coverage measurement:** SpanishDict plus the signed-off v14 MWE inventory probably offers an adequate menu for most OpenSubtitles and Tatoeba Spanish speech sentences. Conversational fillers, rare slang, and non-standard forms will still leave a tail of sentences whose intended meaning is unavailable. The size of that tail has not been measured, and card coverage cannot estimate it.

- The pinned SpanishDict menu reached **98.94% card coverage** over the 10,000-surface Spanish inventory, with **106 explicit `no_menu` cards** after the September 2026 refetch ([build status](../BUILD_STATUS.md#spanish-menu-coverage-restored)). Card coverage only establishes that a card has a menu; it does not establish that the right sense appears in it.
- The v14 SIEVE sign-off kept **1,544 Spanish multiword candidates** for speech WSD ([SIEVE sign-off](../../../Fluency-Workspace/raw/mwe/sieve-2026-09-18/SIGN_OFF.md)). The roadmap still puts the first v14 speech ship after MILL or GLASS; this is a signed-off candidate inventory, not evidence that the live speech deck already presents those meanings ([roadmap](../../CHAT_ROADMAP.md#chat-index)).
- A spot check of SpanishDict's **public pages** found entries for [*guagua* as “bus”](https://www.spanishdict.com/translate/la%20guagua?langFrom=es), [*corillo* as a Puerto Rican group of friends](https://www.spanishdict.com/translate/corillo?langFrom=es), and [*o sea* as a restatement phrase](https://www.spanishdict.com/translate/%C3%B3%20sea). These examples should not be assumed absent from SpanishDict. Public pages do not prove that the same leaves are present in the pinned menu or offered to the right card occurrence.

**Next check:** For each proposed Spanish overlay sense, compare the actual pinned SpanishDict menu and signed-off v14 MWE inventory, then inspect representative speech or lyrics occurrences. Record whether the failure is lookup/normalization, an absent sense, an absent phrase candidate, an elision, or a scoring/commit error. Add an overlay only for an evidenced gap that the existing source path does not cover.

**Provisional workload estimate for Spanish Speech alone:** This looks like a bounded curation pass rather than a new broad lexical build: sample actual speech utterances, group recurring missing fillers/slang/forms, vet those groups, and test a modest overlay against the frozen speech set. Expect a small number of focused research and validation passes, with expansion only if sampling reveals a repeated missing class. This estimate is judgment, not a measured count of expressions or hours; Spanish Artist Mode is a separate, harder part of GRAFT.

---

## 6. Six audit boundaries

The language source work overlaps strongly, but each mode gets its own coverage judgment. A source or overlay candidate discovered in one boundary can be reused in the paired boundary; acceptance must still be checked against that mode's actual utterances and menu.

| Boundary | Corpus and question | Current state |
|---|---|---|
| **1. Spanish Speech** | Do SpanishDict and the signed-off speech MWE inventory offer adequate meanings for almost all selected OpenSubtitles/Tatoeba utterances? | Sampling in this dossier; do not infer sense coverage from card coverage. |
| **2. Spanish Artists** | Which additional slang, lyrics idioms, fillers, and elisions are needed for Spanish Artist Mode? | Shares Spanish source research with 1; separate, harder lyrics audit for VERSE. |
| **3. Portuguese Speech** | Does the Portuguese speech menu plus MWE inventory cover its selected utterances? | Not audited here yet. |
| **4. Portuguese Artists** | What additional menu coverage would Portuguese Artist Mode need? | Future boundary; Artist Mode has not been worked on for Portuguese. |
| **5. Czech Speech** | Does the Czech speech menu plus MWE inventory cover its selected utterances? | Not audited here yet. |
| **6. Czech Lyrics** | What additional menu coverage would Czech lyrics need? | Future boundary; lyrics mode has not been worked on for Czech. |

This dossier gathers evidence ahead of GRAFT. The six rows are audit scopes, not six separate source inventories or permission to run GRAFT or VERSE now.

## 7. Spanish Speech: first targeted sample (2026-09-19)

**Inputs:** Frozen Spanish `prewsd/20260914T223348Z-c35194bc-v2` (364,387 selected sentences, 248,958 OpenSubtitles and 115,429 Tatoeba); pinned `spanishdict-complete-menu-2026-09-15-v3/normalized_menu.json`; signed-off `mwe-es-2026-09-18-v14-sieve/mwe_merged.json`. I searched expressions in the frozen sentences, inspected examples selected for their component cards, and compared the actual pinned menu and MWE entries. This was a targeted probe, not a random sample or a coverage-rate estimate. Sentence mention counts below are not counts of missing meanings.

| Pattern | Observation | Status |
|---|---|---|
| Common single-word fillers already represented | The pinned menu includes discourse senses for *bueno* (“well”), *pues* (“well”), *eh* (“um/uh/huh”), *tipo* (“like/I mean”), *vale* (“okay”), *claro* (“of course”), and *vaya* (“wow/well”). These also occur in the frozen speech sentences. | Do not overlay merely because they appear on a filler list. Check scoring only if a real occurrence is misread. |
| Some phrase fillers have a v14 candidate | *O sea* (139 sentence mentions), *a ver* (666), and *en plan* (36) are all marked `keep` in the signed-off MWE inventory. The pinned word menu alone cannot express every phrase meaning. | Candidate present for v14; test actual selection after the v14 speech run. *A ver* also appears in literal constructions, so occurrence matching matters. |
| Attention-getting *oye* is missing from the word menu | In 905 frozen sentences mentioning *oye*, examples such as “Oye, ¿podemos hablar un momento en privado?” mean “Hey, can we talk ...?” The pinned menu for *oye* contains only *oír/oírse* analyses (“hear/listen”), with no “hey” sense; there is no single-word MWE entry. | Strong candidate for a speech overlay, subject to exact card occurrence and source vetting. |
| Exhortative *venga* is missing from the word menu | In 365 sentences mentioning *venga*, examples include “Venga, que te vea.” (“Come on. Show me.”) and “Venga ya, es patético.” The pinned menu routes to *venir/venirse/vengar/vengarse* and does not offer “come on”; no *venga ya* MWE entry is present. | Strong candidate; distinguish exhortation from literal verb uses. |
| *Hostia* is a lexical and phrase gap in this freeze | The 10k pre-WSD set has 59 sentences mentioning *hostia*, including an exclamation (“Hostia, Toni ...”), an intensifier (*de la hostia*), and speed (*a toda hostia*). The pinned menu has no *hostia* entry, and those three phrases are absent from the signed-off MWE inventory. | Strong candidate family, especially for Spanish colloquial speech; check register and source rights before curation. This card is outside the current 6k menu report, so it is not evidence of a live 6k failure. |
| Raw `no_menu` counts overstate this kind of gap | The v12 6k sense-menu report has 25 `no_menu` cards, mostly clitic forms and abbreviations. *Uh* and *je* appear in the freeze, but sampled *je* lines are French and *uh* is English subtitle filler. | Route these through normalization or source-quality review rather than automatically adding Spanish senses. |

**Occurrence-level confirmation:** In the existing v12 6k stage-04 assignments, both *oye* and *venga* have 30 scored examples and 49–50 further examples stopped by the per-card cap. At least some scored pragmatic uses are forced into literal senses: “Oye, Jordan, ¿has visto eso?” (“Hey, Jordan ...”) was assigned “to hear”; “Venga, levántate ...” (“Come on, get up ...”) was assigned “to come.” Other sampled literal uses, such as “Venga a pescar conmigo” (“Come fishing with me”), show why an overlay must compete on context rather than replace the verb menu. These are observed examples of an unavailable menu option, not an estimated error rate.

**Next sample:** Audit the *hostia* family on the 10k surface scope and test an occurrence-level overlay candidate for *oye* and *venga* against both pragmatic and literal examples. Expand to other frequent pragmatic forms only if the next sample shows the same missing-sense pattern.

**Top-1,000 surface estimate (provisional):** Assuming the signed-off v14 MWE candidates are available, I would expect roughly **5–15** of the first 1,000 Spanish speech surface forms to need at least one additional menu option, with **about 10** as a planning guess. Two are directly evidenced here: *oye* (rank 236) and *venga* (rank 389). The v12 6k report has five `no_menu` forms in ranks 1–1,000 (*ud, sra, srta, uh, uds*), but those are abbreviations or an English filler rather than five demonstrated Spanish slang senses. Many other likely conversational candidates checked in the top 1,000 already have discourse meanings in the pinned menu. This is a judgment from a targeted scan, not a statistical estimate or a completed 1,000-card audit; it excludes needs already met by v14 phrases.
