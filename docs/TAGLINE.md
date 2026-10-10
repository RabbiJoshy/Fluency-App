# TAGLINE — contextual POS tagging and WSD safeguards

Decide which sentence-level part-of-speech tagger, if any, to use per language.
Portuguese is the immediate priority. Do not assume that a larger or transformer
model is necessarily better, or that every language needs a contextual POS gate.

## Concrete trigger

HEADWAY corrected the es/pt source lemma analyses and already completed targeted
WSD using the existing frozen sentences/tags. Portuguese run
`20261010T161908Z-63f07fe8` uses `pt_core_news_lg@3.8.0` tags frozen in
workspace `raw/surfaces/pt/prewsd/20260914T222723Z-e43a0469-v2/`.
The read-only follow-up audit is workspace
`raw/surfaces/headway/pt-es-wsd-followup-audit.json`.

Of 30 evaluated és occurrences, six were assigned to noun é, the name of the
letter E, despite being ordinary verb uses. Five carried PROPN and one NOUN;
the current POS gate removes the ser verb when those tags match the noun.
Example: “Tu és a mulher que eu amo.” → letter-name noun. These counts describe
this sample, not whole-deck accuracy. Other obviously wrong verb choices include
“Tu és responsável pelo que fazes.” → “to exist”; compare against a manually
labelled expected reading and coordinate English-gloss distinctions with LITERAL.
The noun reading itself is valid dictionary evidence and must not be deleted
merely to conceal a contextual-classification failure.

## Required work

1. Read the roadmap Current direction, then this brief and the relevant profile,
   bindings, contextual tag adapters and POS gate. Verify the actual served run
   and its frozen inputs; profile summaries alone are not evidence of execution.
2. Build a small labelled Portuguese sample covering AUX/VERB confusion,
   noun/name homographs, clitic forms, rare genuine noun readings and ambiguous
   cases. Retain the known és failures as regressions; include unaffected controls.
3. Compare the existing tagger and existing WSD gate, safer confidence/fallback
   behaviour, a no-tagger baseline and promising supported alternatives. Evaluate
   per occurrence and by resulting WSD errors; report speed, RAM, variety coverage
   (European/Brazilian Portuguese), provenance and deployment constraints.
4. Distinguish bad frozen tags from bad target/token alignment and overconfident
   filtering. Choose how much authority a contextual tag should have: an
   uncertain tag must not silently eliminate the correct dictionary analysis.
5. Record a supported tagger/no-tagger decision per language, Portuguese first.
   Establish actual Spanish, Czech, Finnish and French configuration before
   proposing changes. Current Czech profile cs-v21-1 explicitly has no contextual
   POS model; this is a baseline to assess, not an automatic defect. Keep Spanish
   transformer tagging as a comparison, not a universal prescription.
6. Implement justified safeguards with focused regression checks. State exactly
   which new versioned freeze/tag artifact, affected menus or assignment outputs
   need regeneration. Create new immutable runs for approved follow-up; never
   overwrite the old freezes. A bare unchanged WSD rerun is not a fix.

## Boundaries and approval

HEADWAY owns source lemma/POS analyses; TAGLINE owns contextual tags and WSD use
of them. SEAM owns app merging and display. LITERAL owns the targeted translation/
English-gloss audit. Coordinate shared WSD files rather than duplicating work.

Follow existing named pools, freezes, spend and deployment rules. No unrelated
harvests, broad rebuilds, paid calls or model downloads are authorised by this
roadmap entry. Obtain required approval before downloads/spend; the previous
HEADWAY US$1 approval was for its embedding campaign, not this new job. Review
resulting app/deck changes in current staging, preserving other chats’ work;
production promotion requires Josh’s explicit approval. Record other-language
findings for later rather than starting parity runs during the Portuguese pass.
