# GRAFT: Domain & Slang Overlay Source Dossier

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
