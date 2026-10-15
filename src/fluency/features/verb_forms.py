"""Conservative dictionary-evidenced verb-form compatibility for cognates."""
from itertools import product

DIMENSIONS = {
    'person': {'first-person', 'second-person', 'third-person'},
    'number': {'singular', 'plural'},
    'tense': {'present', 'past', 'preterite', 'imperfect', 'future', 'pluperfect'},
    'mood': {'indicative', 'subjunctive', 'conditional', 'imperative'},
    'aspect': {'perfective', 'imperfective'},
    'voice': {'passive', 'middle'},
    'gender': {'masculine', 'feminine', 'neuter'},
}


def signatures(tags):
    tags = set(tags)
    if 'past-historic' in tags:
        tags.add('preterite')
    # Slavic past l-forms are tagged as active past participles with gender.
    # Distinguish these finite 3rd-person past tense forms from adjectival/passive participles.
    if 'participle' in tags and 'past' in tags and (tags & {'masculine', 'feminine', 'neuter'}) and not (tags & {'passive'}):
        tags.discard('participle')
        tags.add('third-person')
        tags.add('past')
    if tags & {'combined-form', 'multiword-construction', 'participle', 'gerund'}:
        return set()
    if 'infinitive' in tags:
        # Portuguese personal infinitives are not ordinary infinitives.
        if tags & (DIMENSIONS['person'] | DIMENSIONS['number']):
            return set()
        return {('infinitive',)}
    if not all(tags & DIMENSIONS[key] for key in ('person', 'number', 'tense')):
        return set()
    if not (tags & DIMENSIONS['mood']):
        tags.add('indicative')
    choices = [sorted(tags & values) or [''] for values in DIMENSIONS.values()]
    return {('finite', *values) for values in product(*choices)}


def read_verb_forms(entries):
    result = {}
    lexical_aspects = {}
    for entry in entries:
        if entry.get('pos') != 'verb':
            continue
        word = str(entry.get('word') or '').strip().lower()
        for sense in entry.get('senses', []):
            if not sense.get('form_of'):
                lexical_aspects.setdefault(word, set()).update(set(sense.get('tags', [])) & DIMENSIONS['aspect'])
            refs = sense.get('form_of') or []
            if not refs:
                continue
            for ref in refs:
                lemma = str(ref.get('word') or '').strip().lower()
                result.setdefault(word, {}).setdefault(lemma, set()).update(signatures(sense.get('tags', [])))
        for form in entry.get('forms', []):
            surface = str(form.get('form') or '').strip().lower()
            if not surface or ' ' in surface:
                continue
            result.setdefault(surface, {}).setdefault(word, set()).update(signatures(form.get('tags', [])))
    # Aspect can be stated on the dictionary headword rather than repeated on
    # every inflected form (particularly Czech and Polish).
    for lemmas in result.values():
        for lemma, values in lemmas.items():
            aspects = lexical_aspects.get(lemma, set())
            if not aspects:
                continue
            enriched = set()
            for value in values:
                if value[0] == 'infinitive':
                    enriched.update((value[0], aspect) for aspect in aspects)
                elif not value[5]:
                    enriched.update((*value[:5], aspect, *value[6:]) for aspect in aspects)
                else:
                    enriched.add(value)
            lemmas[lemma] = enriched
    return result


def compatible_forms(target_forms, source_forms, target, target_headword, source, source_headword):
    a = target_forms.get(target, {}).get(target_headword, set())
    b = source_forms.get(source, {}).get(source_headword, set())
    # Unknown forms are never licensed by spelling or a shared lemma.
    return bool(a and b and a & b)
