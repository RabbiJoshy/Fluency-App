# GRAFT Audit of MEND

**Auditor:** GRAFT  
**Date:** 2026-09-24  
**Branch:** `claude/blissful-mayer-yojm2v`  
**Reference Design:** `docs/proposals/0003-surface-exceptions-and-menu-fallback.md` (§§1–10, §2a, §10 decisions)  
**Reference Invariants:** `docs/INVARIANTS.md`

---

## 1. Executive Summary

MEND established the foundational structure for the surface database: the offline resolver, the 4-kind declared format (`headwords`, `gloss`, `expansion`, `entity`), the 3-tier scoped store architecture (`language` → `artist` → `live`), the 4-level trust hierarchy (`curated`, `provider`, `derived`, `heuristic`), provider parity (SpanishDict and Kaikki/Wiktionary), and per-card validation.

This audit verified MEND's implementation against its specification and data. All structural foundations, precedence rules, offline guarantees, and test suites hold. In our inspection of hand-written entries, we discovered that MEND's Czech and Portuguese declared glosses had uniformly set `class: "vocabulary"` on inflected forms (conjugated verbs, noun cases, plurals); we fixed 112 Czech and 4 Portuguese entries in place to `class: "inflection"`. We also audited all 44 Czech contamination entries and verified their linguistic accuracy.

---

## 2. Point-by-Point Audit of MEND

### 2.1 Resolver Precedence and Offline Guarantee (§2, §2a)
- **Code:** `src/fluency/surfaces/resolver.py` (`Resolver.resolve`).
- **Precedence Verified:**
  1. Hand-written `headwords` override (`curated`) — replaces the headword set; strictly validates that the provider has entries for all named headwords (raises `ResolverError` if missing).
  2. Provider-declared headwords (`provider` trust) or rule-derived headwords (`derived` trust), filtered by the consumer's `minimum_trust` floor. Drops any headword missing from local snapshot entries (`available = tuple(h for h in accepted if h.headword not in missing)`).
  3. Empty set fallbacks only:
     - `expansion` (borrows target surface's headword set, e.g. `ud` → `usted`);
     - `declared_gloss` (hand-written single sense);
     - `entity` (name/proper noun card if enabled in `ModePolicy`, else declared `no_menu` with reason `entity_not_in_mode`).
  4. Declared `no_menu` with an explicit reason (`absent`, `unfetched`, `headword_not_in_snapshot`, `below_minimum_trust`).
- **Offline Guarantee:** Holds completely. No HTTP requests or network calls exist in `resolver.py`, `declared.py`, `stores.py`, or `trust.py`. All lookups query local snapshots and local declared files.

### 2.2 SpanishDict Lemma Rule (`spanishdict_lemmas.py`)
- **No Fuzzy Matching (Joshua's Rule):** Strictly verified. `_page` only compares `headword_key(head) == headword_key(surface)` (stripping punctuation `¡!¿?.` and casefolding) or declared relations (`conjugation`, `inflection`). There is zero Levenshtein, phonetic, prefix, or fuzzy distance matching.
- **Enclitic Host Rule on Real Forms:**
  - `díselo`: Host `di` matched against conjugation table. `di` is imperative (2s) of *decir* and preterite indicative (1s) of *dar*. Because `table_has_moods` checks `HOST_MOODS` (`imperativo`, `infinitivo`, `gerundio`), the indicative preterite of *dar* is excluded. Only *decir* remains; resolves uniquely to *decir*.
  - `vete`: Host `ve` is imperative (2s) of both *ir* and *ver*. Because both belong to `HOST_MOODS`, the rule finds two candidate verbs and abstains (`status == "enclitic_ambiguous"`, candidates `("ir", "ver")`).
  - `dele`: Host `de` (accented *dé*) is imperative (3s formal *usted*) of *dar*; resolves uniquely to *dar*.
  - `quédatelo`: Host `queda` is imperative (2s) of *quedar*; clitic `te` is 2s reflexive; resolves to *quedar* and adds pronominal headword *quedarse*.
- **Reflexive Pronoun Rule:** Verified in `_reflexive`:
  - On imperatives: reflexive is checked against the host person (`REFLEXIVE_PERSONS[first] == {row["person"]}`).
  - On infinitives and gerunds: the subject is not encoded in the host, so `me`, `te`, `nos`, `os` cannot be distinguished from indirect objects (e.g. *decírtelo* is "to tell it to you", not *decirse*). Only `se` triggers pronominal headwords on infinitives/gerunds.

### 2.3 Kaikki Parity and CNK Lemma Trust (§10.11)
- **Code:** `src/fluency/sense_menu/kaikki.py` (`KaikkiHeadwordSource.declare`).
- **Provenance & Trust:**
  - Exact headwords: `provenance = "wiktionary-self"`, `trust = provider`.
  - Form-of chains: `provenance = "wiktionary-form-of"`, `trust = provider`.
  - External morphology hops (Czech CNK): `provenance = "external-lemma"`, `detail = self.external_provenance.get(surface, "ledger lemma")`, `trust = provider`.
- Parity holds: published morphological authorities are treated as provider declarations, not our inferences.

### 2.4 Carrying Drifted Menus (877 pt, 1,114 cs)
- **Finding:** Between KILN 2 and MEND, workspace ledgers were updated, causing 877 Portuguese and 1,114 Czech menus to drift outside the affected cards if completely rebuilt from the live ledger.
- **Evaluation:** MEND's decision to carry unaffected cards verbatim from KILN 2 runs (`carry_from_run`) via `_build_and_carry` is **the correct call**. It strictly adheres to:
  - **SCAR:** Never rebuild unaffected release components from drifted ledgers.
  - **Invariant 1:** Migrate the shape, preserve the substance, label both (`menu["carried"]` and `report["carried"]` record the source run id, source menu hash, and card counts).
  - **MEND Brief:** Diff against v15 must show 0 changes outside the affected cards.

### 2.5 WSD Splice and Importer Narrowness
- **Code:** `src/fluency/wsd/splice.py` and `src/fluency/wsd/importer.py`.
- **Carried Row Labeling:** Each carried row has `evidence["carried"]` recording `from_run`, `source_sense_menu_content_id`, `source_method`, and reason.
- **Importer Narrowness:** `_is_declared_default` in `importer.py` strictly restricts model revision exemption to:
  1. `assignment_method == "declared-single-sense/v1"`,
  2. `decision_kind == "deterministic_default"`,
  3. `model_revisions == {}`,
  4. exactly one sense on the card menu (`len(senses) == 1`).
  Any multi-sense card or undeclared method is rejected if model revisions do not match the profile.

### 2.6 MEND's Autonomous Decisions for Joshua (§10)
We reviewed the decisions MEND took on Joshua's behalf:
1. **Decision §10.1' (Entities ON in speech release):**
   - *MEND's choice:* A proper noun with no provider menu becomes an entity card in speech (e.g. `ferrari` in `es-speech-v15-10000x10`).
   - *GRAFT appraisal:* **Agreed.** Without this, `ferrari` would have shipped with an empty meaning, violating the zero-empty-card acceptance requirement.
2. **Decision §10.3' (Interjections vs Contamination):**
   - *MEND's choice:* Every card gets a class tag and translation/explanation. `je` was mapped to SpanishDict's *¡Je!*; `uh` was glossed as a filler; English words in Czech were glossed with class `contamination`. Exclusion is left to ledger policy, not hand deletion.
   - *GRAFT appraisal:* **Agreed.** Provides full auditability and semantic explanation for every card.
3. **Decision §10.13 (Word Class Taxonomy):**
   - *MEND's choice:* 12 classes: `vocabulary`, `inflection`, `enclitic`, `abbreviation`, `interjection`, `onomatopoeia`, `filler`, `loanword`, `slang`, `entity`, `name_fragment`, `contamination`.
   - *GRAFT appraisal:* **Agreed.** Granular enough for UI presentation pills without unbounded fragmentation.

### 2.7 Known Gaps Left Open
MEND documented six known gaps; we confirmed all remain cleanly isolated:
1. Repeated-character observer (for noise like *jaaa*).
2. Derived-form (diminutive/superlative → base) headword source.
3. Wikidata entity offline snapshot fill.
4. Live-store persistent database.
5. Deck-wide ledger lemma cleanup.
6. Clitic tokenization split (Decision 0025, draft proposal only).

---

## 3. Hand-Written Entries Audit & Fixes

### 3.1 Spanish (`config/declared/es/mend-speech-v15.json` — 8 entries)
All 8 entries audited and verified:
- `atrevo` (`headwords`: *atreverse*), `bares` (`headwords`: *bar*), `fantasías` (`headwords`: *fantasía*) — correct overrides for SpanishDict ambiguities.
- `bum` (`onomatopoeia`), `uh` (`filler`), `off` (`loanword`), `tai` (`name_fragment`), `ferrari` (`entity`: brand) — sound translations and classes.

### 3.2 Portuguese (`config/declared/pt/mend-speech-v15.json` — 19 entries)
- Audited all 19 entries.
- **Fixes Applied:** 4 entries (`kilos`, `replicadores`, `infectados`, `habituada`) were labeled with `class: "vocabulary"`. Even though `infectados` and `habituada` resolved via Kaikki headwords, their fallback gloss declarations were updated to `class: "inflection"`.

### 3.3 Czech (`config/declared/cs/mend-speech-v15.json` — 381 entries)
- **Deep Translation & Meaning Check:** All 381 Czech gloss translations were audited for linguistic precision in English and Czech. All translations accurately convey the Czech word's meaning in subtitle context.
- **Contamination Cards (44 entries):** Verified all 44 contamination cards:
  - 38 English functional/grammatical words (`the`, `you`, `that`, `is`, `we`, `your`, `he`, `all`, `for`, `be`, `one`, `what`, `up`, `can`, `with`, `out`, `this`, `know`, `ll`, `get`, `but`, `are`, `there`, `got`, `come`, `have`, `they`, `when`, `was`, `now`, `if`, `right`, `as`, `she`, `how`, `make`).
  - 6 foreign fragments/particles from foreign subtitle dialogue: `sa` (Slovak reflexive), `ma` (Slovak pronoun / mum), `del` (Spanish/Italian preposition), `la` (syllable / article), `ka`, `mo`.
  - None of these are valid standard Czech headwords. Their classification as `contamination` is accurate.
- **Class Misclassifications Fixed (112 entries):**
  - MEND had uniformly stamped `"class": "vocabulary"` across all non-particle glosses.
  - 112 entries were inflected forms whose definitions explicitly state their inflectional role (e.g. *past tense* `povedlo`, `odvedl`, `zaslechl`, `zařídila`, `kontroloval`; *vocative cases* `seržante`, `parťáku`, `lorde`, `výsosti`, `ctihodnosti`, `admirále`; *imperatives* `zmlkni`, `uhni`, `odveďte`, `posluž`; *oblique cases and plurals* `centů`, `historku`, `linii`, `minutách`, `doktorů`, `pojistky`, `e-maily`, `monstra`).
  - **Action taken:** Reclassified all 112 inflected entries from `class: "vocabulary"` to `class: "inflection"`.

---

## 4. Test Verification

- Executed `PYTHONPATH=src python3 -m unittest` on all MEND test suites:
  - `tests/surfaces/test_declared_and_resolver.py`
  - `tests/surfaces/test_stores.py`
  - `tests/sense_menu/test_spanishdict_lemmas.py`
  - `tests/sense_menu/test_resolved_menus.py`
  - `tests/sense_menu/test_kaikki_resolved_menus.py`
  - `tests/wsd/test_splice.py`
  - `tests/release/test_validation.py`
- Result: **All 68 MEND tests pass (OK)**.
- Full repo test suite comparison: Confirmed that repository-wide failures/errors match the documented environmental issues (missing audio/espeak/phonetic packages, missing live workspace files).

---

## 5. Audit Sign-Off

MEND's architecture is sound, verified, and ready to be built upon by GRAFT. With the Czech and Portuguese inflection class fixes committed, we proceed to Part 2.
