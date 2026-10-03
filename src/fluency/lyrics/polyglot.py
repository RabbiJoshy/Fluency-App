"""Offline Artist rehearsal over pinned sources and the shared menu/WSD engine.

No transport or paid embedding writer is imported. Cache misses are recorded as
not evaluated, never silently replaced by dictionary order or a zero vector.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import inspect
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
from fluency.sense_menu.declared_menu import declared_gloss_analyses

from fluency.core.hashing import canonical_content_id, file_content_id
from fluency.core.identity import create_card_record
from fluency.lyrics.languages import load_lyrics_adapter
from fluency.lyrics.assemble import _validate_split
from fluency.lyrics.sampling import calculate_lyrics_wsd_budget, select_best_lyrics_occurrences
from fluency.nlp.models import pin
from fluency.nlp.pos import load_pinned
from fluency.nlp.embeddings import load_cache
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.kaikki import KaikkiSenseMenuAdapter, KaikkiHeadwordSource
from fluency.surfaces.resolver import Resolver, ModePolicy
from fluency.surfaces.declared import Context
from fluency.surfaces.stores import stack
from fluency.surfaces.prewsd import verify, build as build_prewsd
from fluency.speech.wsd_execute import build_analyses, ExactTextGlossScorer
from fluency.lyrics.morphology import canonical_grammar, parsing_text
from fluency.wsd.bindings import binding_for, pos_gate_for
from fluency.wsd.runner import ClosedMenuWSDRunner, WSDComponents, WSDExecutionProfile, WSDRequest
from fluency.wsd.commit import CommitPolicy
from fluency.wsd.disposition import DispositionPolicy
from fluency.wsd.dictionary_candidates import DictionaryCandidatePolicy
from fluency.wsd.multiword import index_multiword_senses, multiword_analyses
from fluency.wsd.overlays import InMemoryOverlayRegistry, declared_gloss_to_overlay


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def identity(prefix, value):
    return prefix + '_' + canonical_content_id(value).split(':')[1][:32]


def recovered_french(source):
    """Recover observed lines only; inherited translations are not re-certified."""
    examples = json.loads((source / 'examples.json').read_text())
    songs = {}
    seen = set()
    for entry in examples.values():
        for key in ('m', 'w', 'r'):
            for bucket in entry.get(key, []):
                for example in bucket if isinstance(bucket, list) else [bucket]:
                    text = example.get('spanish', '').strip()
                    song = str(example.get('song', ''))
                    if not text or not song or (song, text) in seen:
                        continue
                    seen.add((song, text))
                    songs.setdefault(song, {'id': song, 'title': example.get('song_name', song),
                                           'artist': None, 'source': 'retained_french_release', 'lines': []})['lines'].append(text)
    return {'language': 'fr', 'slug': 'french-test-playlist', 'source_files': {
        name: file_content_id(source / name) for name in ('index.json', 'examples.json', 'vocabulary_master.json')},
        'songs': [dict(song, text='\n'.join(song.pop('lines'))) for song in songs.values()]}


def build(repo: Path, workspace: Path, source_path: Path, output: Path, config_path: Path):
    if output.exists():
        raise FileExistsError('Create a new run: refusing to overwrite ' + str(output))
    config = json.loads(config_path.read_text())
    source = json.loads(source_path.read_text())
    language = config['language']
    if source['language'] != language:
        raise ValueError('source/config language mismatch')
    adapter = load_lyrics_adapter(language)
    binding = binding_for(language)
    model_pin = pin(binding.pos_model_role)
    nlp = load_pinned(model_pin)
    snapshot = workspace / config['dictionary_snapshot']
    inputs = {'source': file_content_id(source_path), 'config': file_content_id(config_path),
              'dictionary': file_content_id(snapshot)}
    if config.get('reference_prewsd'):
        reference = workspace / config['reference_prewsd']
        bad = verify(reference)
        if bad:
            raise ValueError('corrupt reference pre-WSD: ' + ', '.join(bad))
        inputs['reference_prewsd_manifest'] = file_content_id(reference / 'manifest.json')
    mwe_index = None
    if config.get('mwe_snapshot'):
        mwe_path = workspace / config['mwe_snapshot']
        inputs['mwe'] = file_content_id(mwe_path)
        mwe_index = index_multiword_senses(json.loads(mwe_path.read_text()))
    context = Context(language=language, mode='lyrics', artist=source['slug'])
    registry = stack(repo, language, workspace=workspace, artist=source['slug'])
    resolver = Resolver(KaikkiHeadwordSource(), registry, context,
                        ModePolicy.load(repo / 'config/surfaces/strategy.json', 'lyrics'))
    # New lyrics sentences are a new freeze, never mutations of speech pairs.
    lines = {}; occurrences = defaultdict(list); external = defaultdict(set); counts = Counter()
    rejected = Counter()
    for song in source['songs']:
        for line_number, text in enumerate(song['text'].splitlines()):
            text = text.strip()
            if not text or text.startswith('['):
                continue
            tokens = adapter.tokenize(text)
            line = tokens.canonical_text
            line_id = identity('sentence', [language, song['id'], line_number, line])
            lines[line_id] = {'line_id': line_id, 'text': line, 'song': song['id'], 'song_name': song['title']}
            tagged_text, tagged_spans = parsing_text(line, tokens.units, resolver)
            doc = nlp(tagged_text)
            for unit in tokens.units:
                if not unit.eligible:
                    rejected[unit.rejection_reason] += 1
                    continue
                form = unit.surface_key
                tag_start, tag_end = tagged_spans[(unit.start, unit.end)]
                exact = [t for t in doc if t.idx == tag_start and t.idx + len(t.text) == tag_end]
                pos = exact[0].pos_ if len(exact) == 1 else None
                lemma = exact[0].lemma_.casefold() if len(exact) == 1 else None
                # spaCy lemmas are first-hop hints; Kaikki still validates them.
                if lemma and lemma != form and pos in {'VERB','AUX','NOUN','ADJ','DET'}:
                    external[form].add(lemma)
                for lookup in adapter.lookup_forms(form):
                    external[form].add(lookup)
                    host = nlp(lookup)
                    if len(host) == 1 and host[0].pos_ in {'VERB', 'AUX'}:
                        external[form].add(host[0].lemma_.casefold())
                occurrence = {'occurrence_id': identity('occurrence', [line_id, unit.start, unit.end]),
                              'line_id': line_id, 'surface': form, 'observed_text': unit.observed_text,
                              'start': unit.start, 'end': unit.end, 'occurrence_pos': pos,
                              'occurrence_lemma': lemma, 'morphology': str(exact[0].morph) if exact else None,
                              'observed_grammar': canonical_grammar(exact[0]) if exact else {}}
                if hasattr(adapter, 'occurrence_grammar'):
                    hint = adapter.occurrence_grammar(
                        form, line, (unit.start, unit.end), exact[0] if exact else None)
                    occurrence['adapter_grammar_evidence'] = dict(hint)
                    for field, key in (('_pos', 'occurrence_pos'), ('_lemma', 'occurrence_lemma')):
                        if field in hint:
                            occurrence['model_' + key] = occurrence[key]
                            occurrence[key] = hint.pop(field)
                    occurrence['observed_grammar'].update(hint)
                    occurrence['observed_grammar'] = {k:v for k,v in occurrence['observed_grammar'].items() if v is not None}
                assert line[unit.start:unit.end] == unit.observed_text
                occurrences[form].append(occurrence); counts[form] += 1
    cards = [create_card_record(language, form).to_dict() for form in sorted(counts)]
    policy = load_sense_menu_language_policy(repo, policy_id=config['menu_policy'], language=language)
    dictionary = KaikkiSenseMenuAdapter(snapshot, language_code=language, language_policy=policy,
                                       external_lemmas={})
    inputs['declared_entries'] = canonical_content_id([e.to_dict() for e in registry.entries])
    inputs['strategy_policy'] = file_content_id(repo / 'config/surfaces/strategy.json')
    inputs['menu_policy'] = file_content_id(repo / 'config/sense_menu/languages' / (config['menu_policy'] + '.json'))
    dictionary.resolver = Resolver(KaikkiHeadwordSource(), registry, context,
                                   ModePolicy.load(repo / 'config/surfaces/strategy.json', 'lyrics'))
    overlays = InMemoryOverlayRegistry([declared_gloss_to_overlay(e) for e in registry.entries
                                       if e.kind == 'gloss' and e.applies_to(context)])
    dictionary.resolver_surfaces = frozenset(counts)
    menu, menu_report = dictionary.build(cards, snapshot_id=snapshot.parent.name)
    # Heuristic tagger lemmas may rescue absent entries, never widen an
    # authoritative provider menu that already exists for the observed form.
    absent_cards = [c for c in cards if not next(m for m in menu['cards'] if m['card_id'] == c['card_id'])['analyses']]
    if absent_cards:
        dictionary.external_lemmas = {k: tuple(sorted(v)) for k, v in external.items()}
        rescued, rescue_report = dictionary.build(absent_cards, snapshot_id=snapshot.parent.name)
        replacements = {c['card_id']: c for c in rescued['cards']}
        menu['cards'] = [replacements.get(c['card_id'], c) for c in menu['cards']]
        menu_report['fallback_only_lemma_rescue'] = rescue_report
    original_menu = deepcopy(menu)
    overrides = set(config.get('reviewed_gloss_overrides', ()))
    for card in menu['cards']:
        form = card['surface_form']
        if form not in overrides:
            continue
        entry = registry.select(form, 'gloss', context, 'curated')
        if entry is None:
            raise ValueError('reviewed gloss override lacks scoped curated evidence: ' + form)
        resolution = SimpleNamespace(entry=entry, stamp=lambda e=entry: {
            'strategy': 'declared_gloss', 'entry_id': e.entry_id, 'trust': e.trust,
            'scope': dict(e.scope), 'reason': e.reason, 'reviewed_provider_replacement': True})
        card['analyses'] = [a.to_dict() for a in declared_gloss_analyses(card['card_id'], form, resolution)]
    menu_report['reviewed_gloss_overrides'] = sorted(overrides)
    menu_id = canonical_content_id(menu)
    by_form = {c['surface_form']: c for c in menu['cards']}
    vectors = load_cache(workspace / 'embeddings' / language / 'exact-text-gemini-embedding-001.npz')
    sense_gate, orthogonal = pos_gate_for(language)
    runner = ClosedMenuWSDRunner(
        WSDExecutionProfile(token_tuple_vote=False, tuple_vote_minimum_margin=0, calibration=False,
                            alignment=False, generative_escalation=False, disposition=DispositionPolicy(None, 'abstain'),
                            candidate_preparation=True, multiword_candidates=True,
                            active_projection='mwe_augmented',
                            commit=CommitPolicy(strategy='rank_agreement', unresolved_outcome='abstain',
                                                shared_translation_licenses_glosskey=True,
                                                phrase_winner_skips_provider_order=True, unresolved_falls_back_to_phrase=True)),
        WSDComponents(language=binding.adapter_factory(), gloss=ExactTextGlossScorer(vectors),
                      candidate_policy=DictionaryCandidatePolicy(language=language, sense_compatible=sense_gate,
                                                               pos_is_orthogonal=orthogonal,
                                                               clitic_gate=config['clitic_gate'], pronominal_gate=True,
                                                               surface_pos_constraints=config.get('surface_pos_constraints'),
                                                               required_grammar_axes=config.get('required_grammar_axes', ()),
                                                               contextual_lemma_gate=True, normalized_leaf_gates=True,
                                                               clitic_evidence=adapter.clitic_evidence,
                                                               pronominal_base=adapter.pronominal_base, has_clitic=adapter.has_clitic),
                      multiword_index=mwe_index, multiword_inventory_content_id=inputs.get('mwe'), overlay_provider=overlays,
                      context_model_revisions={'occurrence_pos': model_pin}))
    selected_by_form = {}
    for rank, form in enumerate(sorted(counts, key=lambda f: (-counts[f], f)), 1):
        leaves = sum(len(a['senses']) for a in by_form[form]['analyses'])
        budget = calculate_lyrics_wsd_budget(rank, leaves, len(occurrences[form]))
        selected_by_form[form], _ = select_best_lyrics_occurrences(occurrences[form], lines, {}, budget=budget)
    selected_all = [o for group in selected_by_form.values() for o in group]
    # Freeze the exact sampled requests before the first WSD decision.
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'prewsd-pairs.json', selected_all)
    sentence_rows = list(lines.values())
    positions = {row['line_id']: i for i,row in enumerate(sentence_rows)}
    frozen_surfaces = {}
    for form in counts:
        eligible = [o for o in selected_all if o['surface'] == form]
        frozen_surfaces[form] = {
            'eligible': [positions[o['line_id']] for o in eligible],
            'occurrence_pos': [o['occurrence_pos'] for o in eligible],
        }
    build_prewsd(output/'prewsd', language=language, run_id=output.name,
                 sentences=[{'sentence_id':r['line_id'], 'target':r['text'], 'source':r['song']} for r in sentence_rows],
                 surfaces=frozen_surfaces, occurrence_pos_model=model_pin)
    if verify(output/'prewsd'):
        raise ValueError('new lyrics pre-WSD freeze failed verification')
    index=[]; master={}; examples={}; decisions=[]; missing=set(); required=set(); statuses=Counter(); skipped=[]
    for rank, form in enumerate(sorted(counts, key=lambda f:(-counts[f], f)), 1):
        card = by_form[form]; cid = card['card_id']
        analyses = build_analyses(card, menu_source_adapter=menu['source_adapter'])
        selected = selected_by_form[form]
        grouped=defaultdict(list); sense_records={}
        for occurrence in selected:
            row=lines[occurrence['line_id']]; text=row['text']
            extra = multiword_analyses(card_id=cid, surface_form=form, sentence=text, index=mwe_index) if mwe_index else ()
            extra = tuple(extra) + tuple(overlays.candidates_for_occurrence(
                card_id=cid, surface_form=form, sentence=text,
                occurrence_span=(occurrence['start'], occurrence['end'])))
            all_analyses = analyses + tuple(a for a,_,_ in extra)
            needed = {text} | {s.gloss_text for a in all_analyses for s in a.senses if s.gloss_text.strip()} if sum(len(a.senses) for a in all_analyses)>1 else set()
            required.update(needed); absent=needed-vectors.keys(); missing.update(absent)
            base={'card_id':cid, 'occurrence_id':occurrence['occurrence_id'], 'sentence_id':row['line_id']}
            if absent:
                statuses['not_evaluated_cache_miss']+=1
                decisions.append(dict(base, status='not_evaluated_cache_miss', missing_text_count=len(absent)))
                continue
            prepared = runner.components.candidate_policy.prepare(sentence=text, surface_form=form,
                observed_pos=occurrence['occurrence_pos'], observed_grammar=occurrence['observed_grammar'], analyses=analyses) if analyses else None
            if prepared is not None and not prepared.analyses:
                statuses['abstained'] += 1
                decisions.append(dict(base, status='abstained', evidence=prepared.evidence))
                continue
            assignment = runner.assign(WSDRequest(card_id=cid, surface_form=form, sentence_id=row['line_id'],
                sentence=text, translation='', sense_menu_content_id=menu_id, analyses=analyses,
                target_span=(occurrence['start'],occurrence['end']), target_observed_form=occurrence['observed_text'],
                observed_pos=occurrence['occurrence_pos'],
                observed_pos_evidence={'observed_grammar':occurrence['observed_grammar']}))
            record=assignment.to_dict(); decisions.append(dict(base, assignment=record)); statuses[assignment.status]+=1
            if assignment.status != 'assigned':
                continue
            found=[(a,s) for a in all_analyses for s in a.senses if a.menu_analysis_id==assignment.menu_analysis_id and s.sense_id==assignment.selected_sense_id]
            if not found:
                raise ValueError('assignment is outside exact menu')
            analysis, leaf=found[0]; key=(analysis.menu_analysis_id,leaf.sense_id)
            sense_records[key]={'headword':analysis.headword,'pos':analysis.part_of_speech,'translation':leaf.translation,
                                'source':analysis.source_adapter,'sense_id':leaf.sense_id}
            grouped[key].append({'song':row['song'],'song_name':row['song_name'],'spanish':text,
                                 'source_text':text,'source_language':language,'english':'', 'translation_source':'unavailable',
                                 'assignment_method':config['profile_id'], 'decision_kind':assignment.decision_kind,
                                 'occurrence_id':occurrence['occurrence_id']})
        if not grouped:
            skipped.append({'surface':form,'card_id':cid,'reason':'no_menu' if not analyses else 'no_publishable_assignment'})
            continue
        keys=list(grouped); total=sum(len(grouped[k]) for k in keys)
        master[cid]={'word':form,'lemma':sense_records[keys[0]]['headword'], 'senses':[sense_records[k] for k in keys]}
        examples[cid]={'m':[grouped[k] for k in keys],'w':[]}
        index.append({'id':cid,'corpus_count':counts[form], 'sense_frequencies':[len(grouped[k])/total for k in keys]})
    _validate_split(index,examples,master)
    report={'language':language,'source_songs':len(source['songs']), 'source_lines':len(lines),
            'surface_count':len(counts),'released_cards':len(index),'withheld_cards':len(skipped),
            'raw_occurrences':sum(counts.values()),'selected_occurrences':len(selected_all),
            'status_counts':dict(statuses),'required_embeddings':len(required),'cache_hits':len(required-missing),
            'cache_misses':len(missing),'paid_calls':0,'spend_usd':0,'split_contract_violations':0,
            'rejected_tokens':dict(rejected), 'complete':not missing, 'coverage_complete':not skipped,
            'publication_projection':'forced_leaf',
            'release_status':'offline_partial_candidate' if missing else 'validated_candidate'}
    # Publication happens only after validation. Exclusive creation guards old runs.
    artifacts={'source.json':source,'lines.json':list(lines.values()),'occurrences.json':dict(occurrences),
               'sense-menu.json':menu,'sense-menu-original.json':original_menu,'menu-report.json':menu_report,'prewsd-pairs.json':selected_all,
               'decisions.json':decisions,'withheld.json':skipped,'missing-embeddings.json':sorted(missing),
               'report.json':report, 'index.json':index,'examples.json':examples,'vocabulary_master.json':master,
               'songs.json':[{k:v for k,v in s.items() if k!='text'} for s in source['songs']]}
    for name,value in artifacts.items(): write_json(output/name,value)
    write_json(output/'manifest.json', {'schema':'polyglot-artist-rehearsal/v1','inputs':inputs,
         'occurrence_pos_model':model_pin,'normalizer':adapter.method_id,'language':language,
         'source_path':str(source_path),'config_path':str(config_path),
         'implementation':{str(p.relative_to(repo)):file_content_id(p) for p in [Path(__file__),Path(inspect.getfile(type(adapter))), repo/'src/fluency/lyrics/morphology.py', repo/'src/fluency/wsd/languages/spanish.py', repo/'src/fluency/wsd/runner.py', repo/'src/fluency/wsd/dictionary_candidates.py', repo/'src/fluency/features/wiktionary.py']},
         'outputs':{name:file_content_id(output/name) for name in [*artifacts, 'prewsd/manifest.json', 'prewsd/examples.json', 'prewsd/pairs.json']}})
    print(json.dumps(report,indent=2),flush=True)
    return report
