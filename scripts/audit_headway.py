#!/usr/bin/env python3
"""Offline es/pt preview; apply only an unchanged, explicit preview.

No stage, pool, frozen artifact or dictionary snapshot is rewritten.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fluency.sense_menu.spanishdict_lemmas import SpanishDictLemmaRule, entry_index, page_lemma_analyses
from fluency.sense_menu.kaikki import _semantic_senses, semantic_headword
from fluency.surfaces.events import append, build_event, read, store_path
from fluency.surfaces.ledger import ledger_path
from fluency.surfaces.lemma_revision import REVISION_PROVIDER, project_revision
from fluency.surfaces.stores import stack
from fluency.surfaces.declared import Context


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def preview(ws, language, snapshot):
    ledger = ledger_path(ws, language)
    data = json.loads(ledger.read_text())
    inputs = [ledger, store_path(ws, language)]
    if language == 'es':
        inputs += [snapshot / n for n in ('surface_cache.json', 'conjugation_reverse.json', 'headword_cache.json')]
        cache, reverse, heads = [json.loads(p.read_text()) for p in inputs[2:]]
        entries = entry_index(cache, heads)
        rule = SpanishDictLemmaRule(reverse, frozenset(entries))
    else:
        inputs.append(snapshot)
        cache = {}
        for line in snapshot.open():
            r = json.loads(line)
            if r.get('lang_code') == language:
                cache.setdefault(r['word'], []).append(r)
    changes, unresolved = [], []
    registry = stack(Path(__file__).resolve().parents[1], language)
    for surface, row in data['surfaces'].items():
        if not row.get('rank'):
            continue
        if row.get('lemma_provenance') == 'manual':
            continue
        if registry.select(surface, 'headwords', Context(language, mode='speech'), 'derived'):
            continue  # Curated sets take precedence; do not replace them with source guesses.
        old = list(dict.fromkeys([*row.get('lemmas', []),
                   *(a['lemma'] for a in row.get('lemma_alternates', []))]))
        phrases = [l for l in old if len(l.split()) > len(surface.split())]
        analyses, evidence = [], {}
        candidate = bool(phrases)
        if language == 'es':
            page = cache.get(surface, {})
            corrected = page_lemma_analyses(surface, page, rule)
            moved = [a for a in corrected if a.get('_lemma_correction')]
            candidate |= bool(moved)
            result = rule.resolve(surface, page or None)
            fallback_clitic = (result.status == 'enclitic' and not result.relation_unknown
                              and bool(page.get('dictionary_analyses')) and
                              all(str(s.get('pos', '')).upper() == 'PHRASE'
                                  for a in page['dictionary_analyses'] for s in a.get('senses', [])))
            candidate |= fallback_clitic
            if not candidate:
                continue
            evidence = result.to_dict()
            evidence['attached_pronouns'] = rule.enclitic_split(surface)
            for item in result.lemmas:
                if len(item.lemma.split()) > len(surface.split()):
                    continue
                own = [a for a in corrected if a.get('headword') == item.lemma]
                if fallback_clitic and not own:
                    own = entries.get(item.lemma, [])
                pos = sorted({str(s.get('pos')) for a in own for s in a.get('senses', [])})
                if item.provenance == 'spanishdict-conjugation-table':
                    pos = ['VERB']
                analyses.append({'lemma': item.lemma, 'pos': pos, 'provenance': item.provenance,
                    'trust': item.trust, 'detail': item.detail,
                    'corrections': [a['_lemma_correction'] for a in own if a.get('_lemma_correction')]})
            # Only direct page declarations are complete enough to replace old
            # analyses. A fallback after an unrelated answer is a review case.
            if result.relation_unknown or (result.rejected_headwords and not phrases and not fallback_clitic):
                unresolved.append({'surface': surface, 'current': old, 'evidence': evidence,
                                   'reason': 'provider relation missing or conflicting'})
                continue
            # Phrase removal must not discard unrelated noun/pronominal
            # analyses from another provider or the retained normalised menu.
            removed = set(phrases)
            if moved:
                removed.add(surface)
                split = evidence.get('attached_pronouns')
                if split and split['lemma'] not in result.lemma_names:
                    evidence['rejected_coincidental_split'] = split
                    evidence['attached_pronouns'] = None
                    rejected = [a['lemma'] for a in row.get('lemma_analyses', [])
                                if a.get('provenance') in {'spanishdict-conjugation-table-enclitic-host',
                                                         'spanishdict-pronominal-headword'}
                                and a['lemma'] not in result.lemma_names]
                    removed.update(rejected)
                    evidence['superseded_coincidental_clitic_lemmas'] = rejected
            if fallback_clitic:
                removed.update(old)  # Rejected substitution titles are not lemmas.
                evidence['rejected_page_preserved'] = page
            supported = {a['lemma'] for a in analyses}
            for lemma in old:
                if lemma not in removed and lemma not in supported:
                    analyses.append({'lemma': lemma, 'pos': [], 'trust': 'unverified',
                                     'provenance': 'retained-existing-analysis'})
            if not moved and not fallback_clitic:
                # This pass removes bad phrase keys; derived clitic/title
                # disagreements remain in the explicit unresolved queue.
                analyses = [a for a in analyses if a['lemma'] in old]
            if surface in old and not moved and rule.enclitic_split(surface):
                unresolved.append({'surface': surface, 'current': old,
                    'reason': 'self-titled enclitic page lacks an explicit verbal relation; retained',
                    'evidence': evidence})
        else:
            rows = cache.get(surface, [])
            targets = {t['word'] for r in rows for s in r.get('senses', [])
                       for t in s.get('form_of', []) if t.get('word')}
            direct = [r for r in rows if _semantic_senses(r) and semantic_headword(r) == surface]
            candidate |= bool(targets and (surface in old and not direct))
            candidate |= any(semantic_headword(r) != surface and _semantic_senses(r) for r in rows)
            candidate |= surface in {'vamos', 'és', 'foi', 'conta', 'é'}
            if not candidate:
                continue
            for r in rows:
                semantic = _semantic_senses(r)
                if semantic:
                    analyses.append({'lemma': semantic_headword(r), 'pos': [r['pos']],
                        'provenance': 'wiktionary-self' if semantic_headword(r) == surface else 'wiktionary-row-form-of',
                        'source_word': surface, 'sense_ids': [s.get('id') for s in semantic],
                        'trust': 'provider'})
                for s in r.get('senses', []):
                    for t in s.get('form_of', []):
                        target = t.get('word')
                        if target and len(target.split()) <= len(surface.split()):
                            analyses.append({'lemma': target, 'pos': [r['pos']],
                                'provenance': 'wiktionary-form-of', 'trust': 'provider',
                                'source_word': surface, 'sense_ids': [s.get('id')],
                                'tags': s.get('tags', [])})
            evidence = {'rows': [{'pos': r['pos'], 'senses': r.get('senses', [])} for r in rows]}
            # Avoid applying partial alt_of chains, which need the adapter's
            # full redirect scan rather than a one-hop lemma import.
            if any(s.get('alt_of') for r in rows for s in r.get('senses', [])):
                unresolved.append({'surface': surface, 'current': old, 'evidence': evidence,
                                   'reason': 'alt_of chain requires full source analysis'})
                continue
        proposed = list(dict.fromkeys(a['lemma'] for a in analyses))
        if not proposed:
            unresolved.append({'surface': surface, 'current': old, 'evidence': evidence,
                               'reason': 'no supported replacement; phrase remains historical evidence'})
            continue
        # Primary is lookup ordering, not WSD. Prefer the unique verb in the
        # named verb-form cases, preserving other POS analyses alongside it.
        verbs = list(dict.fromkeys(a['lemma'] for a in analyses if any('verb' in p.lower() for p in a['pos'])))
        primary = verbs[0] if len(verbs) == 1 else row.get('lemma') if row.get('lemma') in proposed else proposed[0]
        supported_names = {a['lemma'] for a in analyses if a.get('trust') != 'unverified'}
        if primary not in supported_names:
            primary = None
            unresolved.append({'surface': surface, 'current': old, 'evidence': evidence,
                               'reason': 'remaining legacy lemma candidates unverified; primary unresolved'})
        if set(proposed) == set(old) and primary == row.get('lemma') and not any(a.get('corrections') for a in analyses):
            continue
        def semantic_signature(items):
            return [(a['lemma'], a.get('pos', []), a.get('trust'), a.get('provenance')) for a in items]
        if (row.get('lemma_analyses') and semantic_signature(row['lemma_analyses']) == semantic_signature(analyses)
                and primary == row.get('lemma') and set(proposed) == set(old)):
            continue
        approved_pos = (sorted({p for a in analyses if a.get('trust') != 'unverified' for p in a['pos']})
                        if language == 'es' and (fallback_clitic or any(c.get('original_pos') == 'PHRASE'
                            for a in analyses for c in a.get('corrections', ()))) else None)
        changes.append({'surface': surface, 'current': {'lemma': row.get('lemma'), 'lemmas': old,
            'part_of_speech': row.get('part_of_speech', [])},
            'proposed': {'primary': primary, 'lemmas': proposed, 'analyses': analyses,
                         **({'approved_pos': approved_pos} if approved_pos else {})},
            'evidence': evidence, 'excluded_phrase_keys': phrases, 'status': 'supported'})
    return {'version': 'headway-preview/v1', 'language': language,
            'inputs': {str(p.resolve()): digest(p) for p in inputs},
            'changes': changes, 'unresolved': unresolved}


def apply(ws, path):
    report = json.loads(path.read_text())
    for p, h in report['inputs'].items():
        if digest(Path(p)) != h:
            raise ValueError(f'preview input changed: {p}; regenerate and review')
    lang = report['language']
    ledger = ledger_path(ws, lang)
    data = json.loads(ledger.read_text())
    history = read(store_path(ws, lang))
    events = []
    for change in report['changes']:
        surface = change['surface']
        evidence = {'provider': change.get('provider', REVISION_PROVIDER), 'priority': 1,
            **({'approved_pos': change['proposed']['approved_pos']} if 'approved_pos' in change['proposed'] else {}),
            'lemmas': change['proposed']['lemmas'], 'primary': change['proposed']['primary'],
            'analyses': change['proposed']['analyses'], 'source_evidence': change['evidence'],
            'preview_sha256': digest(path), 'input_hashes': report['inputs'],
            'removed_lemmas': sorted(set(data['surfaces'][surface].get('lemma_revision', {}).get('removed_lemmas', ())) |
                                    (set(change['current']['lemmas']) - set(change['proposed']['lemmas']))),
            'excluded_phrase_keys': change['excluded_phrase_keys'],
            'superseded_event_ids': [e['event_id'] for e in history if e['subject']['id'] == surface
                                    and e['reason_code'] in {'lemma_resolved', 'lemma_is_headword'}]}
        event = build_event(surface=surface, language=lang, phase='lemma', reason_code='lemma_resolved',
                            observer=('HEADWAY/manual-override-restoration/v1' if evidence['provider'] == 'hand-written'
                                      else 'HEADWAY/source-analysis/v1'), evidence=evidence)
        events.append(event)
        row = project_revision(data['surfaces'][surface], evidence)
        row['evidence']['lemma_resolved'] = evidence
        row['observations'] += 1
        data['surfaces'][surface] = row
    append(store_path(ws, lang), events)
    data['derived_from']['events'] = len(read(store_path(ws, lang)))
    ledger.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
    print(f'{lang}: applied {len(events)} supported revisions; {len(report["unresolved"])} unresolved; supply preserved')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace', type=Path, required=True)
    ap.add_argument('--language', choices=['es', 'pt'], required=True)
    ap.add_argument('--snapshot', type=Path)
    ap.add_argument('--preview', type=Path)
    ap.add_argument('--apply-preview', type=Path)
    args = ap.parse_args()
    if args.apply_preview:
        report = json.loads(args.apply_preview.read_text())
        if report['language'] != args.language:
            raise ValueError('preview language mismatch')
        apply(args.workspace, args.apply_preview)
    else:
        if not args.snapshot or not args.preview:
            ap.error('--snapshot and --preview are required')
        report = preview(args.workspace, args.language, args.snapshot)
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
        print(f'{args.language}: {len(report["changes"])} supported, {len(report["unresolved"])} unresolved -> {args.preview}')
if __name__ == '__main__':
    main()
