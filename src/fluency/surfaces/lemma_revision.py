"""Complete source-analysis revisions supersede legacy title-only observations.

History remains append-only. Once a surface has a reviewed analysis set, a
rerun of an old observer cannot resurrect a phrase or form-only headword.
"""
from __future__ import annotations

REVISION_PROVIDER = 'source-lemma-analyses/v1'


def active_lemma_events(events):
    manual = [e for e in events if e.get('reason_code') in {'lemma_resolved', 'lemma_is_headword'}
              and e.get('evidence', {}).get('provider') == 'hand-written']
    if manual:
        return [e for e in events if e.get('reason_code') not in {'lemma_resolved', 'lemma_is_headword'}] + [manual[-1]]
    revisions = [e for e in events if e.get('evidence', {}).get('provider') == REVISION_PROVIDER]
    if not revisions:
        return events
    latest = revisions[-1]
    return [e for e in events if e.get('reason_code') not in {'lemma_resolved', 'lemma_is_headword'}] + [latest]


def project_revision(row, evidence):
    """Project reviewed lemmas and explicit POS; preserve identity and supply."""
    analyses = evidence['analyses']
    lemmas = list(dict.fromkeys(a['lemma'] for a in analyses if a.get('trust') != 'unverified'))
    primary = evidence.get('primary')
    if primary not in lemmas:
        primary = None
    alternates = list(dict.fromkeys(a['lemma'] for a in analyses if a['lemma'] != primary))
    pos_override = ({'part_of_speech': evidence['approved_pos']} if 'approved_pos' in evidence else {})
    return {**row, **pos_override, 'lemma': primary, 'lemmas': lemmas,
            'lemma_provenance': evidence['provider'] if primary else None,
            'lemma_alternates': [{'lemma': l, 'provenance': evidence['provider'],
                                 **({'trust': 'unverified'} if l not in lemmas else {})}
                                 for l in alternates],
            'lemma_analyses': analyses,
            'lemma_revision': {k: v for k, v in evidence.items() if k != 'analyses'}}


def stale_carried_analyses(card, row):
    """Identify carried source keys a reviewed ledger correction superseded."""
    revision = row.get('lemma_revision', {})
    removed = set(revision.get('removed_lemmas', ()))
    moved_verb = any(a.get('lemma') != card.get('surface_form') and
                     (a.get('corrections') or a.get('provenance') == 'wiktionary-row-form-of')
                     for a in row.get('lemma_analyses', ()))
    return [a for a in card.get('analyses', ()) if a.get('source_adapter') not in
            {'declared-gloss/v1', 'declared-entity/v1'} and (a.get('headword') in removed or
            (moved_verb and a.get('headword') == card.get('surface_form')
             and str(a.get('part_of_speech', '')).lower() == 'verb'))]


def compatible_reviewed_pos(events, lemmas):
    """Use reviewed POS only for the current lemma set, respecting manual POS."""
    manual = [e['evidence'] for e in events
              if e.get('reason_code') in {'lemma_resolved', 'lemma_is_headword'}
              and e.get('evidence', {}).get('provider') == 'hand-written']
    if manual and manual[-1].get('pos'):
        return manual[-1]['pos']
    for event in reversed(events):
        evidence = event.get('evidence', {})
        if 'approved_pos' in evidence and set(evidence.get('lemmas', [])) == set(lemmas):
            return evidence['approved_pos']
    return None
