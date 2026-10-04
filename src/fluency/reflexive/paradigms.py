"""Paradigm table from the English-Wiktionary (Kaikki) dump: form -> [(lemma, mood, tense, person, number)].

Mood and tense names are the labels the detectors use. Usage:

    python -m fluency.reflexive.paradigms <es|pt> <kaikki dump.jsonl> <out forms-<lang>.json>

The output goes to the workspace (``fluency.reflexive.paths.PARADIGMS``), never to git.
"""
import json, sys, collections


def build(lang, dump, out):
    L = {
     'es': dict(ger='gerundio', part='participo', pret='pretérito-perfecto-simple', impf='pretérito-imperfecto', fut_ind='futuro', plup='pretérito-pluscuamperfecto', pers_inf=None),
     'pt': dict(ger='gerúndio', part='particípio', pret='pretérito-perfeito', impf='pretérito-imperfeito', fut_ind='futuro-do-presente', plup='pretérito-mais-que-perfeito', pers_inf='infinitivo-pessoal-presente'),
    }[lang]
    SKIP = {'table-tags', 'inflection-template', 'class', 'combined-form', 'misspelling', 'obsolete', 'romanization', 'dialectal', 'pronunciation-spelling', 'negative'}
    def person(tags):
        p = '1' if 'first-person' in tags else '2' if 'second-person' in tags else '3' if 'third-person' in tags else ''
        n = 's' if 'singular' in tags else 'p' if 'plural' in tags else ''
        return p, n
    def analyse(tags):
        t = set(tags)
        if 'infinitive' in t:
            p, n = person(t)
            if p and lang == 'pt' and 'impersonal' not in t: return 'infinitivo', L['pers_inf'], p, n
            if p: return None            # es 'arrepentirme' style rows: combined, handled by the splitter
            return 'infinitivo', 'infinitivo', '', ''
        if 'gerund' in t: return L['ger'], L['ger'], '', ''
        if 'participle' in t: return L['part'], L['part'], '', ''
        p, n = person(t)
        if 'imperative' in t:
            if 'second-person-semantically' in t: p = '3'
            return 'imperativo', 'afirmativo', p, n
        if 'conditional' in t: return 'condicional', ('futuro-do-pretérito' if lang == 'pt' else 'presente'), p, n
        mood = 'subjuntivo' if 'subjunctive' in t else 'indicativo' if 'indicative' in t else None
        if mood is None: return None
        if 'present' in t: tense = 'presente'
        elif 'preterite' in t: tense = L['pret']
        elif 'imperfect' in t: tense = L['impf'] if mood == 'indicativo' else 'pretérito-imperfeito' if lang == 'pt' else 'pretérito-imperfecto'
        elif 'future' in t: tense = 'futuro' if mood == 'subjuntivo' else L['fut_ind']
        elif 'pluperfect' in t: tense = L['plup']
        else: return None
        return mood, tense, p, n
    forms = collections.defaultdict(set); combined = collections.defaultdict(set); lemmas = set()
    for line in open(dump, encoding='utf8'):
        if '"pos": "verb"' not in line or '"forms"' not in line: continue
        e = json.loads(line)
        lemma = e['word'].lower()
        if ' ' in lemma: continue
        if lang == 'es' and lemma.endswith('se') and len(lemma) > 4 and lemma[-4:-2] in ('ar', 'er', 'ir', 'ír'):
            lemma = lemma[:-2]
        got = False
        for f in e.get('forms', []):
            tags = f.get('tags', []); form = (f.get('form') or '').lower().strip()
            if not form or form == '-': continue
            if 'combined-form' in tags:
                combined[form].add(lemma); continue
            if set(tags) & SKIP: continue
            w = form.split()
            if len(w) > 1:
                if lang == 'es' and len(w) == 2 and w[0] in ('me', 'te', 'se', 'nos', 'os'): w = w[1:]
                else: continue
            a = analyse(tags)
            if a is None: continue
            forms[w[0]].add((lemma,) + a); got = True
        if got:
            forms[lemma].add((lemma, 'inf', 'inf', '', '')); lemmas.add(lemma)
    json.dump({k: sorted(v) for k, v in forms.items()}, open(out, 'w'), ensure_ascii=False)
    json.dump({k: sorted(v) for k, v in combined.items()}, open(out.replace('.json', '-combined.json'), 'w'), ensure_ascii=False)
    print(lang, 'lemmas', len(lemmas), 'forms', len(forms), 'combined', len(combined))



if __name__ == '__main__':
    build(*sys.argv[1:4])
