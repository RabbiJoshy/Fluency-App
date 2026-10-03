"""Cross-language regressions: source spans, identity, and provider parity."""
import pytest
from fluency.lyrics.languages import load_lyrics_adapter
from fluency.wsd.pos_bridge import compatible
from fluency.lyrics.lexical import build_provider_menu
from pathlib import Path
import json


def test_french_elisions_preserve_ambiguous_article():
    adapter = load_lyrics_adapter('fr')
    text = "J’aime l’amour qu’il dit d’elle."
    tokens = adapter.tokenize(text)
    forms = [u.surface_key for u in tokens.units if u.eligible]
    assert forms == ['j’', 'aime', 'l’', 'amour', 'qu’', 'il', 'dit', 'd’', 'elle']
    assert adapter.lookup_forms('l’') == ('le', 'la')
    for u in tokens.units:
        assert tokens.canonical_text[u.start:u.end] == u.observed_text


def test_french_dash_does_not_crash():
    result = load_lyrics_adapter('fr').tokenize('Oui -- non, aime-')
    assert any(u.surface_key == 'oui' for u in result.units)
    assert any(u.rejection_reason == 'empty_hyphen_component' for u in result.units)


def test_portuguese_clitics_are_lookup_metadata_not_new_cards():
    adapter = load_lyrics_adapter('pt')
    result = adapter.tokenize('Ele disse-me para fazê-lo numa casa do bairro, bem-vindo!')
    forms = [u.surface_key for u in result.units]
    assert 'disse-me' in forms and 'fazê-lo' in forms
    assert 'numa' in forms and 'do' in forms and 'bem-vindo' in forms
    assert 'me' not in forms and 'lo' not in forms
    assert adapter.lookup_forms('disse-me') == ('disse',)
    assert adapter.lookup_forms('fazê-lo') == ('fazer',)
    assert adapter.lookup_forms('pô-lo') == ('pôr',)
    assert adapter.lookup_forms('fi-lo') == ()
    assert adapter.lookup_forms('bem-vindo') == ()
    for u in result.units: assert result.canonical_text[u.start:u.end] == u.observed_text


@pytest.mark.parametrize('tag,pos', [('ADP','contraction'),('DET','contraction'),('AUX','verb'),('PRON','pron')])
def test_wiktionary_pos_parity(tag, pos):
    assert compatible('wiktionary', tag, pos)


def test_generic_lyrics_builder_uses_supported_kaikki_edition(tmp_path):
    snapshot=tmp_path/'dictionary.jsonl'
    snapshot.write_text(json.dumps({'word':'amour','lang_code':'fr','lang':'French','pos':'noun','senses':[{'glosses':['love']}]}))
    menu, report, policy = build_provider_menu(Path(__file__).resolve().parents[2],language='fr',dictionary_snapshot=snapshot,
                                            snapshot_id='test',language_policy_id='fr-v1',lookup_forms={'amour'})
    assert menu['cards'][0]['analyses']

@pytest.mark.parametrize('language,text,expected', [
    ('fr', "J'aime l'amour", ['j’','aime','l’','amour']),
    ('pt', 'disse-me para fazê-lo numa casa', ['disse-me','para','fazê-lo','numa','casa']),
])
def test_immutable_processing_stage_supports_dictionary_languages(tmp_path, language, text, expected):
    from fluency.core.workspace import Workspace
    from fluency.lyrics.process import process_lyrics_run
    from fluency.core.hashing import file_content_id
    ws=Workspace.initialize(tmp_path/'workspace')
    run=ws.root/'runs'/language/'lyrics'/'fixture'
    source=run/'stages/01_source_ingest/output'; source.mkdir(parents=True)
    (run/'manifest.json').write_text(json.dumps({'run_id':'fixture','language':language,'mode':'lyrics'}))
    (source/'song.json').write_text('{}')
    (source/'lines.jsonl').write_text(json.dumps({'line_id':'line-1','text':text,'source_span':[0,len(text)]})+'\n')
    (source/'manifest.json').write_text(json.dumps({'outputs':{'lines.jsonl':file_content_id(source/'lines.jsonl')}}))
    routing=tmp_path/'routing.json'; routing.write_text(json.dumps({'schema_version':2}))
    output=process_lyrics_run(ws,run_id='fixture',language=language,routing_snapshot=routing)
    units=[json.loads(row) for row in (output/'analysis-units.jsonl').read_text().splitlines()]
    assert [u['normalized_form'] for u in units] == expected
    occurrences=[json.loads(row) for row in (output/'occurrences.jsonl').read_text().splitlines()]
    assert all(text[o['span'][0]:o['span'][1]] == o['surface'] for o in occurrences)
    with pytest.raises(ValueError, match='already exists'):
        process_lyrics_run(ws,run_id='fixture',language=language,routing_snapshot=routing)


def test_french_pronominal_gate_sees_elisions():
    adapter=load_lyrics_adapter('fr')
    assert adapter.has_clitic("Il s’endort")
    assert adapter.has_clitic("Tu m'aimes")
    assert not adapter.has_clitic('Il chante')
    assert adapter.pronominal_base('se souvenir') == 'souvenir'
    assert adapter.pronominal_base("s'endormir") == 'endormir'
    assert adapter.clitic_evidence('aime', 'Il aime') is None


def test_offline_build_withholds_cache_misses_and_freezes_exact_inputs(tmp_path, monkeypatch):
    from fluency.lyrics import polyglot
    from fluency.surfaces.prewsd import verify
    class Morph:
        def to_dict(self): return {}
        def __str__(self): return ''
    class Token:
        def __init__(self,text,start):
            self.text=text; self.idx=start; self.pos_='NOUN'; self.lemma_=text; self.morph=Morph()
    def nlp(text):
        import re
        return [Token(m.group(),m.start()) for m in re.finditer(r'\w+',text)]
    monkeypatch.setattr(polyglot,'load_pinned',lambda _:nlp)
    monkeypatch.setattr(polyglot,'load_cache',lambda _: {})
    snapshot=tmp_path/'snapshot.jsonl'
    snapshot.write_text('\n'.join(json.dumps({'word':word,'lang_code':'fr','lang':'French','pos':'noun',
                                            'senses':[{'glosses':[g]} for g in glosses]})
                                  for word,glosses in [('amour',['love','beloved']),('salut',['greeting'])]))
    source=tmp_path/'source.json'
    source.write_text(json.dumps({'language':'fr','slug':'fixture','songs':[{'id':'1','title':'Fixture','text':'salut amour'}]}))
    config=tmp_path/'config.json'
    config.write_text(json.dumps({'language':'fr','profile_id':'fixture','dictionary_snapshot':'snapshot.jsonl',
                                 'menu_policy':'fr-v1','clitic_gate':False}))
    output=tmp_path/'run'
    report=polyglot.build(Path(__file__).resolve().parents[2],tmp_path,source,output,config)
    assert report['released_cards']==1
    assert report['status_counts']['not_evaluated_cache_miss']==1
    assert report['paid_calls']==0
    assert verify(output/'prewsd')==[]
    assert json.loads((output/'missing-embeddings.json').read_text())
    with pytest.raises(FileExistsError):
        polyglot.build(Path(__file__).resolve().parents[2],tmp_path,source,output,config)


def test_contextual_morphology_preserves_gerund_and_subject_evidence():
    from fluency.lyrics.morphology import canonical_grammar
    class Morph:
        def to_dict(self): return {'VerbForm':'Ger', 'Number':'Sing', 'Person':'3'}
    class Token:
        morph=Morph(); lemma_='ter'; pos_='VERB'; dep_='nsubj'
    assert canonical_grammar(Token()) == {'person':'3','number':'singular','form':'gerund',
                                         'pronoun_role':'subject','lemma':'ter'}


def test_scoped_expansion_tagging_retains_original_span_mapping():
    from fluency.lyrics.morphology import parsing_text
    class Resolver:
        def expansion_target(self, surface): return {'pra':'para'}.get(surface,'')
    tokens=load_lyrics_adapter('pt').tokenize('Pra ela cantar')
    text, spans=parsing_text(tokens.canonical_text,tokens.units,Resolver())
    assert text == 'para ela cantar'
    for unit in tokens.units:
        start,end=spans[(unit.start,unit.end)]
        assert text[start:end] == ('para' if unit.surface_key=='pra' else unit.observed_text)
        assert tokens.canonical_text[unit.start:unit.end] == unit.observed_text


def test_opt_in_provider_pronoun_constraints_do_not_change_legacy_policy():
    from fluency.features.wiktionary import extract
    from fluency.wsd.grammar_gate import grammar_compatible
    repo=Path(__file__).resolve().parents[2]
    policy=json.loads((repo/'config/sense_menu/languages/pt-lyrics-polyglot-v1.json').read_text())
    sense={'glosses':['first-person singular prepositional pronoun; me']}
    assert grammar_compatible(extract(sense), {'pronoun_role':'subject'})
    assert not grammar_compatible(extract(sense,policy=policy), {'pronoun_role':'subject'})
    assert not grammar_compatible(extract(sense,policy=policy), {'person':'3'})


def test_artist_bridge_preserves_per_occurrence_projection_and_method():
    from fluency.artist.wsd_bridge import overlay_native_assignments
    master={'card':{'word':'que','lemma':'que','senses':[{'sense_id':'sense','translation':'that'}]}}
    records=[]
    for i, projection in enumerate(['provider_only','mwe_augmented']):
        records.append({'surface':'que','occurrence_id':str(i), 'selection_projection':projection,
                        'assignment_method':'pt-lyrics-polyglot-v1',
                        'assignment':{'selection_projections':{projection:{'selected_sense_id':'sense',
                        'selected_tuple':{'headword':'que','part_of_speech':'conj'},'emitted_level':'leaf'}}}})
    index,evidence=overlay_native_assignments([{'id':'card'}],None,master,records)
    assert index[0]['wsd_distribution']['selection_projection']=='mixed'
    assert evidence['selection_projection']=='mixed'
    decisions=evidence['cards']['card']['decisions']
    assert [d['selection_projection'] for d in decisions]==['provider_only','mwe_augmented']
    assert all(d['provenance']['assignment_method']=='pt-lyrics-polyglot-v1' for d in decisions)


def test_dictionary_candidate_profile_filters_grammar_before_scoring():
    from fluency.wsd.dictionary_candidates import DictionaryCandidatePolicy
    from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
    from fluency.features import SpecialistFeature
    adapter=load_lyrics_adapter('pt')
    policy=DictionaryCandidatePolicy(language='pt',sense_compatible=lambda *_:True,
        pos_is_orthogonal=lambda _:False,clitic_evidence=adapter.clitic_evidence,
        pronominal_base=adapter.pronominal_base,has_clitic=adapter.has_clitic)
    standard=SenseLeaf('subject','I','','ref:subject',{})
    marked=SenseLeaf('prepositional','me','','ref:prep',{}, specialist_features=(
        SpecialistFeature('grammar','gloss_mark','pronoun_role=prepositional','prepositional pronoun'),))
    analysis=MenuAnalysis(build_analysis_id(card_id='card',source_adapter='wiktionary',source_analysis_key='eu:pron'),
                          'card','eu','eu','pron','wiktionary','eu:pron',(standard,marked),{})
    prepared=policy.prepare(sentence='Eu canto',surface_form='eu',observed_pos='PRON',
        observed_grammar={'pronoun_role':'subject','lemma':'eu'},analyses=(analysis,))
    assert [s.sense_id for s in prepared.analyses[0].senses] == ['subject']
    assert prepared.evidence['normalized_leaf_gate_policy']=='filter'


def test_review_profile_withholds_person_specific_leaf_without_person_evidence():
    from fluency.wsd.dictionary_candidates import DictionaryCandidatePolicy
    from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
    from fluency.features import SpecialistFeature
    adapter=load_lyrics_adapter('pt')
    policy=DictionaryCandidatePolicy(language='pt',sense_compatible=lambda *_:True,
        pos_is_orthogonal=lambda _:False,clitic_evidence=adapter.clitic_evidence,
        pronominal_base=adapter.pronominal_base,has_clitic=adapter.has_clitic,
        required_grammar_axes=('person',))
    leaf=SenseLeaf('first','myself','','ref',{},specialist_features=(
        SpecialistFeature('grammar','sense_mark','person=1','first person'),))
    analysis=MenuAnalysis(build_analysis_id(card_id='card',source_adapter='wiktionary',source_analysis_key='se'),
                          'card','se','se','pron','wiktionary','se',(leaf,),{})
    result=policy.prepare(sentence='se canta',surface_form='se',observed_pos='PRON',analyses=(analysis,))
    assert not result.analyses
    assert result.evidence['strict_rejected_leaf_refs'][0]['reason']=='missing_required_grammar'


def test_french_elision_pos_constraint_never_restores_proper_name_on_empty_set():
    from fluency.wsd.dictionary_candidates import DictionaryCandidatePolicy
    from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
    adapter=load_lyrics_adapter('fr')
    policy=DictionaryCandidatePolicy(language='fr',sense_compatible=lambda *_:True,
        pos_is_orthogonal=lambda _:False,clitic_evidence=adapter.clitic_evidence,
        pronominal_base=adapter.pronominal_base,has_clitic=adapter.has_clitic,
        surface_pos_constraints={'c’':['pron','det']})
    analysis=MenuAnalysis(build_analysis_id(card_id='card',source_adapter='wiktionary',source_analysis_key='ce'),
        'card','c’','ce','name','wiktionary','ce',(SenseLeaf('EC','European Community','','ref',{}),),{})
    assert not policy.prepare(sentence='c’est beau',surface_form='c’',observed_pos='PRON',analyses=(analysis,)).analyses


def test_importer_removes_singular_contributor_header_and_joiner_debris():
    import runpy
    clean_genius_text=runpy.run_path(str(Path(__file__).resolve().parents[2]/"scripts/import_polyglot_lyrics.py"))["clean_genius_text"]
    text, evidence=clean_genius_text('1 ContributorGisèle Lyrics\nUn f\u200cilm\n12Embed')
    assert text=='Un film'
    assert {row['reason'] for row in evidence}=={'genius_title_header','genius_embed_footer','embedded_format_character'}


def test_common_noun_evidence_removes_case_colliding_proper_name():
    from fluency.wsd.dictionary_candidates import DictionaryCandidatePolicy
    from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
    adapter=load_lyrics_adapter('fr')
    policy=DictionaryCandidatePolicy(language='fr',sense_compatible=lambda *_:True,
        pos_is_orthogonal=lambda _:False,clitic_evidence=adapter.clitic_evidence,
        pronominal_base=adapter.pronominal_base,has_clitic=adapter.has_clitic)
    analyses=tuple(MenuAnalysis(build_analysis_id(card_id='card',source_adapter='wiktionary',source_analysis_key=pos),
        'card','amour','amour',pos,'wiktionary',pos,(SenseLeaf(pos,gloss,'','ref',{}),),{})
        for pos,gloss in [('name','Cupid'),('noun','love')])
    prepared=policy.prepare(sentence='cet amour',surface_form='amour',observed_pos='NOUN',analyses=analyses)
    assert [a.part_of_speech for a in prepared.analyses]==['noun']


def test_french_lexical_person_overrides_noisy_tagger_agreement():
    from types import SimpleNamespace
    adapter=load_lyrics_adapter('fr')
    token=SimpleNamespace(pos_='PRON')
    assert adapter.occurrence_grammar('tu','Tu chantes',(0,2),token)['person']=='2'
    assert adapter.occurrence_grammar('on','On chante',(0,2),token)['number'] is None
    assert adapter.occurrence_grammar('est','Est-ce vrai',(0,3),token)['_pos']=='AUX'
    assert adapter.occurrence_grammar('est','Vers l’est',(7,10),token)=={}


def test_portuguese_addressee_person_differs_from_agreement():
    from types import SimpleNamespace
    adapter=load_lyrics_adapter('pt')
    assert adapter.occurrence_grammar('você','Você canta',(0,4),SimpleNamespace(pos_='PRON'))=={'person':'2'}


def test_surface_redirect_person_does_not_require_article_person():
    from fluency.wsd.dictionary_candidates import DictionaryCandidatePolicy
    from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
    from fluency.features import SpecialistFeature
    adapter=load_lyrics_adapter('fr')
    policy=DictionaryCandidatePolicy(language='fr',sense_compatible=lambda *_:True,
        pos_is_orthogonal=lambda _:False,clitic_evidence=adapter.clitic_evidence,
        pronominal_base=adapter.pronominal_base,has_clitic=adapter.has_clitic,
        required_grammar_axes=('person',))
    leaf=SenseLeaf('article','the','','ref',{},specialist_features=(
        SpecialistFeature('grammar','surface_mark','person=3','elided surface redirect'),))
    analysis=MenuAnalysis(build_analysis_id(card_id='card',source_adapter='wiktionary',source_analysis_key='le'),
        'card','l’','le','article','wiktionary','le',(leaf,),{})
    assert policy.prepare(sentence='l’amour',surface_form='l’',observed_pos='DET',analyses=(analysis,)).analyses


def test_method_composition_names_explicit_language_profile():
    from fluency.wsd.provenance import method_composition
    cards=[{'wsd_distribution':{'buckets':[{'provenance':{'assignment_method':'pt-lyrics-polyglot-v3'}}]}}]
    composition=method_composition(cards,native_method='pt-lyrics-polyglot-v3')
    assert composition['decision_count']==composition['native_decisions']==1
    assert composition['fully_native'] and composition['native_share']==1
    assert method_composition(cards)['native_decisions']==0  # legacy default preserved


def test_artist_song_membership_uses_all_occurrences_not_sampled_examples(tmp_path):
    import runpy
    catalog=runpy.run_path(str(Path(__file__).resolve().parents[2]/'scripts/package_polyglot_artist.py'))['song_catalog']
    (tmp_path/'lines.json').write_text(json.dumps([{'line_id':'a','song':'1'},{'line_id':'b','song':'2'}]))
    (tmp_path/'occurrences.json').write_text(json.dumps({'amor':[{'line_id':'a'},{'line_id':'b'}],'eu':[{'line_id':'a'}]}))
    source={'songs':[{'id':'1','title':'First'},{'id':'2','title':'Second'}]}
    master={'love-card':{'word':'amor'},'i-card':{'word':'eu'}}
    songs=catalog(tmp_path,source,master)['songs']
    assert songs[0]['cardIds']==['i-card','love-card']
    assert songs[1]['cardIds']==['love-card']
