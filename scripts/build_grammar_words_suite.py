#!/usr/bin/env python3
"""Build and validate the Portuguese and Spanish function word suites.

Outputs:
  - app/data/grammar-words/pt.json
  - app/data/grammar-words/es.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "app/data/grammar-words"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def build_portuguese_suite():
    # Load existing 16 curated words
    existing_file = DATA_DIR / "pt.json"
    suite = {}
    if existing_file.exists():
        with open(existing_file) as f:
            suite = json.load(f)

    # Expanded Portuguese words
    additions = {
        "a": {
            "word": "a",
            "role": "Preposition & Article",
            "rank": 2,
            "frequency": 35946,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Destination</span>",
                    "rule": "Directional link: points to a target destination or recipient.",
                    "targetHTML": "Vou <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Lisboa</span> amanhã.",
                    "translation": "I go to Lisbon tomorrow."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                    "rule": "Definite feminine article: specifies a singular feminine entity.",
                    "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>casa</span> é bonita.",
                    "translation": "The house is pretty."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span>",
                    "rule": "Direct object pronoun: replaces a singular 3rd-person feminine noun.",
                    "targetHTML": "Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>conheço</span> bem.",
                    "translation": "I know her well."
                }
            ]
        },
        "e": {
            "word": "e",
            "role": "Connector",
            "rank": 5,
            "frequency": 17238,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Item / Clause</span> + <span class=\"fw-token-connector\">e</span> + <span class=\"fw-token-c\">Addition</span>",
                    "rule": "Copulative coordinator: links equal grammatical items or consecutive actions.",
                    "targetHTML": "Comprei pão <span class='fw-token-connector'>e</span> <span class='fw-token-c'>queijo</span>.",
                    "translation": "I bought bread and cheese."
                }
            ]
        },
        "eu": {
            "word": "eu",
            "role": "Subject Pronoun",
            "rank": 8,
            "frequency": 10606,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Eu</span> + <span class=\"fw-token-v\">Verb (1st Sing)</span>",
                    "rule": "Subject pronoun: emphasizes or clarifies the first-person singular actor.",
                    "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>moro</span> aqui.",
                    "translation": "I live here."
                }
            ]
        },
        "ele": {
            "word": "ele",
            "role": "Subject & Object Pronoun",
            "rank": 15,
            "frequency": 6225,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Ele</span> + <span class=\"fw-token-v\">Verb (3rd Sing)</span>",
                    "rule": "Subject pronoun: marks a 3rd-person masculine singular actor ('he / it').",
                    "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>trabalha</span> muito.",
                    "translation": "He works a lot."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Preposition</span> + <span class=\"fw-token-connector\">ele</span>",
                    "rule": "Prepositional object: follows prepositions like 'com ele' or 'para ele'.",
                    "targetHTML": "Falei com <span class='fw-token-connector'>ele</span> ontem.",
                    "translation": "I spoke with him yesterday."
                }
            ]
        },
        "ela": {
            "word": "ela",
            "role": "Subject & Object Pronoun",
            "rank": 27,
            "frequency": 3530,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Ela</span> + <span class=\"fw-token-v\">Verb (3rd Sing)</span>",
                    "rule": "Subject pronoun: marks a 3rd-person feminine singular actor ('she / it').",
                    "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sabe</span> a resposta.",
                    "translation": "She knows the answer."
                }
            ]
        },
        "um": {
            "word": "um",
            "role": "Article & Number",
            "rank": 6,
            "frequency": 12840,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                    "rule": "Indefinite article: introduces an unspecific singular masculine noun.",
                    "targetHTML": "Tenho <span class='fw-token-connector'>um</span> <span class='fw-token-c'>irmão</span>.",
                    "translation": "I have a brother."
                }
            ]
        },
        "uma": {
            "word": "uma",
            "role": "Article & Number",
            "rank": 9,
            "frequency": 9531,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                    "rule": "Indefinite article: introduces an unspecific singular feminine noun.",
                    "targetHTML": "Vi <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>fotografia</span>.",
                    "translation": "I saw a photograph."
                }
            ]
        },
        "os": {
            "word": "os",
            "role": "Article & Pronoun",
            "rank": 14,
            "frequency": 6233,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">os</span> + <span class=\"fw-token-c\">Plural Masculine Noun</span>",
                    "rule": "Definite article: introduces specific masculine plural nouns.",
                    "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>livros</span> estão na mesa.",
                    "translation": "The books are on the table."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">os</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Direct object pronoun: replaces 3rd-person masculine plural objects ('them').",
                    "targetHTML": "Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>vi</span> no cinema.",
                    "translation": "I saw them at the movies."
                }
            ]
        },
        "as": {
            "word": "as",
            "role": "Article & Pronoun",
            "rank": 21,
            "frequency": 4513,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">as</span> + <span class=\"fw-token-c\">Plural Feminine Noun</span>",
                    "rule": "Definite article: introduces specific feminine plural nouns.",
                    "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>portas</span> estão abertas.",
                    "translation": "The doors are open."
                }
            ]
        },
        "me": {
            "word": "me",
            "role": "Object Pronoun",
            "rank": 25,
            "frequency": 3763,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">me</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Object pronoun: represents 'me / to me' receiving direct or indirect action.",
                    "targetHTML": "Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ajudou</span> hoje.",
                    "translation": "He helped me today."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">-me</span>",
                    "rule": "Reflexive clitic: action reflects back onto the speaker ('myself').",
                    "targetHTML": "<span class='fw-token-v'>Lembro</span><span class='fw-token-connector'>-me</span> de tudo.",
                    "translation": "I remember everything."
                }
            ]
        },
        "te": {
            "word": "te",
            "role": "Object Pronoun",
            "rank": 33,
            "frequency": 2675,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">te</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Object pronoun: represents 2nd-person 'you / to you' (informal).",
                    "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>amo</span>.",
                    "translation": "I love you."
                }
            ]
        },
        "lhe": {
            "word": "lhe",
            "role": "Indirect Pronoun",
            "rank": 48,
            "frequency": 1490,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">lhe</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Indirect object pronoun: represents 'to him / to her / to you'.",
                    "targetHTML": "Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>dei</span> o livro.",
                    "translation": "I gave him the book."
                }
            ]
        },
        "ao": {
            "word": "ao",
            "role": "Contraction",
            "rank": 32,
            "frequency": 2773,
            "parts": ["a", "o"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">a + o</span> + <span class=\"fw-token-c\">Masculine Destination / Time</span>",
                    "rule": "Contraction of 'a + o' (to the / at the) before masculine singular nouns.",
                    "targetHTML": "Vou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>mercado</span>.",
                    "translation": "I am going to the market."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">ao</span> + <span class=\"fw-token-v\">Infinitive</span>",
                    "rule": "Temporal nexus: expresses 'upon doing' or 'at the moment of'.",
                    "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>chegar</span>, avise-me.",
                    "translation": "Upon arriving, let me know."
                }
            ]
        },
        "à": {
            "word": "à",
            "role": "Contraction",
            "rank": 29,
            "frequency": 2819,
            "parts": ["a", "a"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">a + a</span> + <span class=\"fw-token-c\">Feminine Destination / Time</span>",
                    "rule": "Crasis contraction of 'a + a' (to the / at the) before feminine singular nouns.",
                    "targetHTML": "Chegamos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>noite</span>.",
                    "translation": "We arrived at night."
                }
            ]
        },
        "pelo": {
            "word": "pelo",
            "role": "Contraction",
            "rank": 36,
            "frequency": 2420,
            "parts": ["por", "o"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">por + o</span> + <span class=\"fw-token-c\">Masculine Path / Reason</span>",
                    "rule": "Contraction of 'por + o' (through the / by the / for the).",
                    "targetHTML": "Caminhei <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>parque</span>.",
                    "translation": "I walked through the park."
                }
            ]
        },
        "pela": {
            "word": "pela",
            "role": "Contraction",
            "rank": 37,
            "frequency": 2350,
            "parts": ["por", "a"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">por + a</span> + <span class=\"fw-token-c\">Feminine Path / Reason</span>",
                    "rule": "Contraction of 'por + a' (through the / by the / for the).",
                    "targetHTML": "Obrigado <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>ajuda</span>.",
                    "translation": "Thank you for the help."
                }
            ]
        },
        "num": {
            "word": "num",
            "role": "Contraction",
            "rank": 40,
            "frequency": 1940,
            "parts": ["em", "um"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">em + um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                    "rule": "Contraction of 'em + um' (in a / on a).",
                    "targetHTML": "Moro <span class='fw-token-connector'>num</span> <span class='fw-token-c'>apartamento</span>.",
                    "translation": "I live in an apartment."
                }
            ]
        },
        "numa": {
            "word": "numa",
            "role": "Contraction",
            "rank": 41,
            "frequency": 1820,
            "parts": ["em", "uma"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">em + uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                    "rule": "Contraction of 'em + uma' (in a / on a).",
                    "targetHTML": "Entrei <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>loja</span>.",
                    "translation": "I entered a shop."
                }
            ]
        },
        "dele": {
            "word": "dele",
            "role": "Contraction",
            "rank": 42,
            "frequency": 1780,
            "parts": ["de", "ele"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dele</span>",
                    "rule": "Possessive contraction of 'de + ele' (his / of him).",
                    "targetHTML": "Conheço o amigo <span class='fw-token-connector'>dele</span>.",
                    "translation": "I know his friend."
                }
            ]
        },
        "dela": {
            "word": "dela",
            "role": "Contraction",
            "rank": 43,
            "frequency": 1690,
            "parts": ["de", "ela"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dela</span>",
                    "rule": "Possessive contraction of 'de + ela' (her / of her).",
                    "targetHTML": "A casa <span class='fw-token-connector'>dela</span> é grande.",
                    "translation": "Her house is big."
                }
            ]
        },
        "sem": {
            "word": "sem",
            "role": "Preposition",
            "rank": 45,
            "frequency": 1550,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb / Noun</span> + <span class=\"fw-token-connector\">sem</span> + <span class=\"fw-token-c\">Missing Element</span>",
                    "rule": "Privative preposition: marks absence, exclusion, or lack.",
                    "targetHTML": "Café <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>açúcar</span>, por favor.",
                    "translation": "Coffee without sugar, please."
                }
            ]
        },
        "sobre": {
            "word": "sobre",
            "role": "Preposition",
            "rank": 46,
            "frequency": 1520,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Discussion / Thought</span> + <span class=\"fw-token-connector\">sobre</span> + <span class=\"fw-token-c\">Topic</span>",
                    "rule": "Thematic marker: introduces the subject matter or topic.",
                    "targetHTML": "Falamos <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o projeto</span>.",
                    "translation": "We talked about the project."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Position</span> + <span class=\"fw-token-connector\">sobre</span> + <span class=\"fw-token-c\">Surface</span>",
                    "rule": "Spatial relation: located on top of a surface ('upon / above').",
                    "targetHTML": "O papel está <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a mesa</span>.",
                    "translation": "The paper is on the table."
                }
            ]
        },
        "até": {
            "word": "até",
            "role": "Preposition & Focus Particle",
            "rank": 47,
            "frequency": 1510,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Movement / Time</span> + <span class=\"fw-token-connector\">até</span> + <span class=\"fw-token-c\">Limit / Endpoint</span>",
                    "rule": "Terminal boundary: points to the spatial or temporal stopping point.",
                    "targetHTML": "Vou caminhar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a esquina</span>.",
                    "translation": "I will walk as far as the corner."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Até</span> + <span class=\"fw-token-c\">Surprising Subject</span>",
                    "rule": "Scalar focus particle: emphasizes an extreme case ('even').",
                    "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>as crianças</span> entenderam.",
                    "translation": "Even the children understood."
                }
            ]
        },
        "porque": {
            "word": "porque",
            "role": "Connector",
            "rank": 34,
            "frequency": 2642,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Result</span> + <span class=\"fw-token-connector\">porque</span> + <span class=\"fw-token-c\">Cause</span>",
                    "rule": "Causal conjunction: explains the reason or motive behind an action.",
                    "targetHTML": "Fiquei em casa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>choveu</span>.",
                    "translation": "I stayed home because it rained."
                }
            ]
        },
        "quando": {
            "word": "quando",
            "role": "Connector",
            "rank": 35,
            "frequency": 2510,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Quando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Clause</span>",
                    "rule": "Temporal subordinator: anchors the action to a specific time or event.",
                    "targetHTML": "<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>cheguei</span>, <span class='fw-token-c'>todos aplaudiram</span>.",
                    "translation": "When I arrived, everyone applauded."
                }
            ]
        },
        "isso": {
            "word": "isso",
            "role": "Demonstrative Pronoun",
            "rank": 18,
            "frequency": 5751,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">isso</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Neutral demonstrative: refers to a stated fact, concept, or object near the listener.",
                    "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>é</span> verdade.",
                    "translation": "That is true."
                }
            ]
        },
        "isto": {
            "word": "isto",
            "role": "Demonstrative Pronoun",
            "rank": 28,
            "frequency": 3266,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">isto</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Neutral demonstrative: refers to an immediate object or idea near the speaker.",
                    "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>é</span> para você.",
                    "translation": "This is for you."
                }
            ]
        },
        "tudo": {
            "word": "tudo",
            "role": "Indefinite Pronoun",
            "rank": 32,
            "frequency": 2687,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">tudo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                    "rule": "Universal pronoun: represents the totality of things ('everything / all').",
                    "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>está</span> bem.",
                    "translation": "Everything is fine."
                }
            ]
        }
    }

    suite.update(additions)
    with open(DATA_DIR / "pt.json", "w") as f:
        json.dump(suite, f, ensure_ascii=False, indent=2)
    print(f"Updated Portuguese suite: {len(suite)} words.")
    return suite


def build_spanish_suite():
    es_suite = {
        "de": {
            "word": "de",
            "role": "Preposition",
            "rank": 2,
            "frequency": 32926,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Complement</span>",
                    "rule": "Required link: preceding verb governs 'de' before its object or action.",
                    "targetHTML": "<span class='fw-token-v'>Me acuerdo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ti</span>.",
                    "translation": "I remember you."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                    "rule": "Nominal binding: marks possession, origin, content, or material.",
                    "targetHTML": "Quiero un <span class='fw-token-v'>vaso</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>agua</span>.",
                    "translation": "I want a glass of water."
                }
            ]
        },
        "que": {
            "word": "que",
            "role": "Connector",
            "rank": 1,
            "frequency": 33170,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Thought / Speech</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Clause</span>",
                    "rule": "Subordination: bridges what someone thinks, says, or knows to the statement.",
                    "targetHTML": "<span class='fw-token-v'>Creo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>va a llover</span>.",
                    "translation": "I think it’s going to rain."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                    "rule": "Relativization: refers back to a noun while introducing descriptive detail.",
                    "targetHTML": "Es el <span class='fw-token-v'>libro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estoy leyendo</span>.",
                    "translation": "It is the book that I am reading."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                    "rule": "Comparison: connects the two sides of a degree or quality contrast.",
                    "targetHTML": "Ella es <span class='fw-token-v'>más alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>yo</span>.",
                    "translation": "She is taller than me."
                }
            ]
        },
        "a": {
            "word": "a",
            "role": "Preposition",
            "rank": 3,
            "frequency": 22580,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Destination</span>",
                    "rule": "Directional goal: indicates movement toward a place or terminus.",
                    "targetHTML": "Voy <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Madrid</span>.",
                    "translation": "I am going to Madrid."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Person</span>",
                    "rule": "Personal 'a': marks a specific human or personalized direct object.",
                    "targetHTML": "Veo <span class='fw-token-connector'>a</span> <span class='fw-token-c'>María</span> todos los días.",
                    "translation": "I see María every day."
                }
            ]
        },
        "en": {
            "word": "en",
            "role": "Preposition",
            "rank": 7,
            "frequency": 15660,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">en</span> + <span class=\"fw-token-c\">Location</span>",
                    "rule": "Spatial framing: anchors an action or entity within a place or space.",
                    "targetHTML": "Vivo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>Sevilla</span>.",
                    "translation": "I live in Seville."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">en</span> + <span class=\"fw-token-c\">Time Period</span>",
                    "rule": "Temporal framing: situates an event inside a month, year, or duration.",
                    "targetHTML": "Viajamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>julio</span>.",
                    "translation": "We travel in July."
                }
            ]
        },
        "por": {
            "word": "por",
            "role": "Preposition",
            "rank": 10,
            "frequency": 10320,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">State / Gratitude</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                    "rule": "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                    "targetHTML": "Gracias <span class='fw-token-connector'>por</span> <span class='fw-token-c'>venir</span>.",
                    "translation": "Thank you for coming."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                    "rule": "Trajectory: marks the route, medium, or space through which motion happens.",
                    "targetHTML": "Paseo <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el parque</span>.",
                    "translation": "I stroll through the park."
                }
            ]
        },
        "para": {
            "word": "para",
            "role": "Preposition",
            "rank": 19,
            "frequency": 6488,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Objective</span>",
                    "rule": "Purpose and aim: establishes the intended goal or outcome of an action.",
                    "targetHTML": "Estudio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                    "translation": "I study in order to learn."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Entity</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                    "rule": "Beneficiary / Target: designates the person meant to receive something.",
                    "targetHTML": "Esto es <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ti</span>.",
                    "translation": "This is for you."
                }
            ]
        },
        "con": {
            "word": "con",
            "role": "Preposition",
            "rank": 18,
            "frequency": 7024,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">con</span> + <span class=\"fw-token-c\">Companion</span>",
                    "rule": "Accompaniment: joins an action to the companion sharing it.",
                    "targetHTML": "Ceno <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mis amigos</span>.",
                    "translation": "I have dinner with my friends."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">con</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                    "rule": "Instrument and attitude: describes the tool used or care applied.",
                    "targetHTML": "Escribo <span class='fw-token-connector'>con</span> <span class='fw-token-c'>cuidado</span>.",
                    "translation": "I write with care."
                }
            ]
        },
        "sin": {
            "word": "sin",
            "role": "Preposition",
            "rank": 36,
            "frequency": 2180,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Noun / Action</span> + <span class=\"fw-token-connector\">sin</span> + <span class=\"fw-token-c\">Missing Element</span>",
                    "rule": "Privative preposition: marks absence, lack, or omission.",
                    "targetHTML": "Café <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>azúcar</span>, por favor.",
                    "translation": "Coffee without sugar, please."
                }
            ]
        },
        "se": {
            "word": "se",
            "role": "Pronoun Clitic",
            "rank": 17,
            "frequency": 7410,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                    "rule": "Reflexive clitic: action turns back upon the person doing it.",
                    "targetHTML": "Él <span class='fw-token-connector'>se</span> <span class='fw-token-v'>lava</span> la cara.",
                    "translation": "He washes his face."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb (Passive/Impersonal)</span>",
                    "rule": "Impersonal / Passive marker: signals general or collective truth ('one does').",
                    "targetHTML": "Aquí <span class='fw-token-connector'>se</span> <span class='fw-token-v'>habla</span> español.",
                    "translation": "Spanish is spoken here."
                }
            ]
        },
        "me": {
            "word": "me",
            "role": "Object Pronoun",
            "rank": 11,
            "frequency": 9642,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">me</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Object pronoun: represents 1st-person 'me / to me' receiving the verb action.",
                    "targetHTML": "Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>llamó</span> por teléfono.",
                    "translation": "She called me on the phone."
                }
            ]
        },
        "te": {
            "word": "te",
            "role": "Object Pronoun",
            "rank": 14,
            "frequency": 7670,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">te</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Object pronoun: represents 2nd-person 'you / to you' (informal).",
                    "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>quiero</span> mucho.",
                    "translation": "I love you very much."
                }
            ]
        },
        "nos": {
            "word": "nos",
            "role": "Object Pronoun",
            "rank": 38,
            "frequency": 2100,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">nos</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Object pronoun: represents 1st-person plural 'us / to us'.",
                    "targetHTML": "El profesor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>enseña</span> bien.",
                    "translation": "The teacher teaches us well."
                }
            ]
        },
        "le": {
            "word": "le",
            "role": "Indirect Pronoun",
            "rank": 30,
            "frequency": 3589,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">le</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Indirect object pronoun: represents 3rd-person singular 'to him / to her / to you'.",
                    "targetHTML": "Yo <span class='fw-token-connector'>le</span> <span class='fw-token-v'>escribí</span> una carta.",
                    "translation": "I wrote him a letter."
                }
            ]
        },
        "al": {
            "word": "al",
            "role": "Contraction",
            "rank": 13,
            "frequency": 7673,
            "parts": ["a", "el"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">a + el</span> + <span class=\"fw-token-c\">Masculine Destination</span>",
                    "rule": "Mandatory contraction of 'a + el' (to the / at the) before masculine nouns.",
                    "targetHTML": "Vamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>cine</span> esta noche.",
                    "translation": "We are going to the cinema tonight."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">al</span> + <span class=\"fw-token-v\">Infinitive</span>",
                    "rule": "Temporal nexus: expresses 'upon doing' or 'when doing'.",
                    "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>llegar</span> a casa, descansé.",
                    "translation": "Upon arriving home, I rested."
                }
            ]
        },
        "del": {
            "word": "del",
            "role": "Contraction",
            "rank": 15,
            "frequency": 7638,
            "parts": ["de", "el"],
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">de + el</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                    "rule": "Mandatory contraction of 'de + el' (of the / from the).",
                    "targetHTML": "La puerta <span class='fw-token-connector'>del</span> <span class='fw-token-c'>hotel</span> está cerrada.",
                    "translation": "The door of the hotel is closed."
                }
            ]
        },
        "el": {
            "word": "el",
            "role": "Definite Article",
            "rank": 5,
            "frequency": 18067,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">el</span> + <span class=\"fw-token-c\">Masculine Singular Noun</span>",
                    "rule": "Definite article: designates a specific masculine singular referent.",
                    "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>sol</span> brilla en el cielo.",
                    "translation": "The sun shines in the sky."
                }
            ]
        },
        "la": {
            "word": "la",
            "role": "Article & Pronoun",
            "rank": 4,
            "frequency": 21524,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">la</span> + <span class=\"fw-token-c\">Feminine Singular Noun</span>",
                    "rule": "Definite article: designates a specific feminine singular referent.",
                    "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>puerta</span> está abierta.",
                    "translation": "The door is open."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">la</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Direct object pronoun: replaces a 3rd-person feminine singular noun ('her / it').",
                    "targetHTML": "Yo <span class='fw-token-connector'>la</span> <span class='fw-token-v'>vi</span> ayer.",
                    "translation": "I saw her yesterday."
                }
            ]
        },
        "los": {
            "word": "los",
            "role": "Article & Pronoun",
            "rank": 16,
            "frequency": 7540,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">los</span> + <span class=\"fw-token-c\">Masculine Plural Noun</span>",
                    "rule": "Definite article: designates specific masculine plural entities.",
                    "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>niños</span> juegan fuera.",
                    "translation": "The children play outside."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">los</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Direct object pronoun: replaces 3rd-person masculine plural objects ('them').",
                    "targetHTML": "Yo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>compré</span> ayer.",
                    "translation": "I bought them yesterday."
                }
            ]
        },
        "las": {
            "word": "las",
            "role": "Article & Pronoun",
            "rank": 24,
            "frequency": 4810,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">las</span> + <span class=\"fw-token-c\">Feminine Plural Noun</span>",
                    "rule": "Definite article: designates specific feminine plural entities.",
                    "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>llaves</span> están en la mesa.",
                    "translation": "The keys are on the table."
                }
            ]
        },
        "lo": {
            "word": "lo",
            "role": "Article & Pronoun",
            "rank": 8,
            "frequency": 14130,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">lo</span> + <span class=\"fw-token-c\">Adjective / Abstract</span>",
                    "rule": "Neuter article: nominalizes an adjective into an abstract quality ('the ... thing').",
                    "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>importante</span> es participar.",
                    "translation": "The important thing is to participate."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">lo</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Direct object pronoun: replaces a masculine singular item or concept ('it / him').",
                    "targetHTML": "Ya <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>sé</span>.",
                    "translation": "I already know it."
                }
            ]
        },
        "un": {
            "word": "un",
            "role": "Indefinite Article",
            "rank": 9,
            "frequency": 13352,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">un</span> + <span class=\"fw-token-c\">Masculine Singular Noun</span>",
                    "rule": "Indefinite article: introduces a single unspecific masculine noun.",
                    "targetHTML": "Tengo <span class='fw-token-connector'>un</span> <span class='fw-token-c'>amigo</span> en Madrid.",
                    "translation": "I have a friend in Madrid."
                }
            ]
        },
        "una": {
            "word": "una",
            "role": "Indefinite Article",
            "rank": 12,
            "frequency": 8937,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">una</span> + <span class=\"fw-token-c\">Feminine Singular Noun</span>",
                    "rule": "Indefinite article: introduces a single unspecific feminine noun.",
                    "targetHTML": "Es <span class='fw-token-connector'>una</span> <span class='fw-token-c'>buena idea</span>.",
                    "translation": "It is a good idea."
                }
            ]
        },
        "y": {
            "word": "y",
            "role": "Connector",
            "rank": 6,
            "frequency": 16518,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Element</span> + <span class=\"fw-token-connector\">y</span> + <span class=\"fw-token-c\">Addition</span>",
                    "rule": "Copulative conjunction: coordinates items, clauses, or thoughts of equal status.",
                    "targetHTML": "Compré pan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>leche</span>.",
                    "translation": "I bought bread and milk."
                }
            ]
        },
        "pero": {
            "word": "pero",
            "role": "Connector",
            "rank": 22,
            "frequency": 5378,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">pero</span> + <span class=\"fw-token-c\">Contrast</span>",
                    "rule": "Adversative bridge: introduces a qualification, limitation, or unexpected contrast.",
                    "targetHTML": "Quería salir, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>llovía</span>.",
                    "translation": "I wanted to go out, but it was raining."
                }
            ]
        },
        "si": {
            "word": "si",
            "role": "Connector",
            "rank": 21,
            "frequency": 5720,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Si</span> + <span class=\"fw-token-v\">Condition</span> , <span class=\"fw-token-c\">Result</span>",
                    "rule": "Conditional marker: establishes a hypothesis preceding its outcome.",
                    "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>tienes tiempo</span>, <span class='fw-token-c'>ven a verme</span>.",
                    "translation": "If you have time, come see me."
                }
            ]
        },
        "como": {
            "word": "como",
            "role": "Connector",
            "rank": 29,
            "frequency": 3832,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Model / Standard</span>",
                    "rule": "Simile and comparison: links an action to a model or manner standard.",
                    "targetHTML": "Canta <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un ángel</span>.",
                    "translation": "She sings like an angel."
                },
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Capacity / Role</span>",
                    "rule": "Capacity marker: defines the role or capacity in which someone acts.",
                    "targetHTML": "Trabaja <span class='fw-token-connector'>como</span> <span class='fw-token-c'>abogado</span>.",
                    "translation": "He works as a lawyer."
                }
            ]
        },
        "mi": {
            "word": "mi",
            "role": "Possessive",
            "rank": 20,
            "frequency": 5724,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">mi</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                    "rule": "Possessive determiner: denotes 1st-person ownership of a singular noun.",
                    "targetHTML": "Este es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>coche</span>.",
                    "translation": "This is my car."
                }
            ]
        },
        "su": {
            "word": "su",
            "role": "Possessive",
            "rank": 25,
            "frequency": 4679,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">su</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                    "rule": "Possessive determiner: denotes 3rd-person ownership ('his / her / their / your').",
                    "targetHTML": "Ella buscaba <span class='fw-token-connector'>su</span> <span class='fw-token-c'>teléfono</span>.",
                    "translation": "She was looking for her phone."
                }
            ]
        },
        "tu": {
            "word": "tu",
            "role": "Possessive",
            "rank": 28,
            "frequency": 3942,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">tu</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                    "rule": "Possessive determiner: denotes 2nd-person informal ownership ('your').",
                    "targetHTML": "¿Dónde está <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>casa</span>?",
                    "translation": "Where is your house?"
                }
            ]
        },
        "yo": {
            "word": "yo",
            "role": "Subject Pronoun",
            "rank": 27,
            "frequency": 4612,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Yo</span> + <span class=\"fw-token-v\">Verb (1st Sing)</span>",
                    "rule": "Subject pronoun: emphasizes the 1st-person singular actor ('I').",
                    "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>vivo</span> en Barcelona.",
                    "translation": "I live in Barcelona."
                }
            ]
        },
        "tú": {
            "word": "tú",
            "role": "Subject Pronoun",
            "rank": 35,
            "frequency": 2215,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Tú</span> + <span class=\"fw-token-v\">Verb (2nd Sing)</span>",
                    "rule": "Subject pronoun: marks the informal 2nd-person actor ('you').",
                    "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>sabes</span> la verdad.",
                    "translation": "You know the truth."
                }
            ]
        },
        "eso": {
            "word": "eso",
            "role": "Demonstrative Pronoun",
            "rank": 26,
            "frequency": 4676,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">eso</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Neuter demonstrative: refers to a stated matter, idea, or object near the listener.",
                    "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>es</span> verdad.",
                    "translation": "That is true."
                }
            ]
        },
        "esto": {
            "word": "esto",
            "role": "Demonstrative Pronoun",
            "rank": 31,
            "frequency": 2988,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">esto</span> + <span class=\"fw-token-v\">Verb</span>",
                    "rule": "Neuter demonstrative: refers to an immediate topic or object near the speaker.",
                    "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>es</span> para ti.",
                    "translation": "This is for you."
                }
            ]
        },
        "todo": {
            "word": "todo",
            "role": "Indefinite Pronoun",
            "rank": 32,
            "frequency": 2979,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">todo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                    "rule": "Universal pronoun: signifies the totality of matters ('everything / all').",
                    "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>está</span> bien.",
                    "translation": "Everything is fine."
                }
            ]
        },
        "algo": {
            "word": "algo",
            "role": "Indefinite Pronoun",
            "rank": 34,
            "frequency": 2452,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">algo</span>",
                    "rule": "Indefinite entity: marks an unspecified thing or amount ('something').",
                    "targetHTML": "Quiero comer <span class='fw-token-connector'>algo</span>.",
                    "translation": "I want to eat something."
                }
            ]
        },
        "porque": {
            "word": "porque",
            "role": "Connector",
            "rank": 40,
            "frequency": 2080,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-v\">Result</span> + <span class=\"fw-token-connector\">porque</span> + <span class=\"fw-token-c\">Cause</span>",
                    "rule": "Causal conjunction: explains the underlying reason or motive.",
                    "targetHTML": "No fui <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estaba cansado</span>.",
                    "translation": "I did not go because I was tired."
                }
            ]
        },
        "cuando": {
            "word": "cuando",
            "role": "Connector",
            "rank": 41,
            "frequency": 2040,
            "relations": [
                {
                    "formulaHTML": "<span class=\"fw-token-connector\">Cuando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Action</span>",
                    "rule": "Temporal connector: situates an event at a point in time.",
                    "targetHTML": "<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>llegué</span>, <span class='fw-token-c'>todos sonrieron</span>.",
                    "translation": "When I arrived, everyone smiled."
                }
            ]
        }
    }

    with open(DATA_DIR / "es.json", "w") as f:
        json.dump(es_suite, f, ensure_ascii=False, indent=2)
    print(f"Created Spanish suite: {len(es_suite)} words.")
    return es_suite


if __name__ == "__main__":
    pt = build_portuguese_suite()
    es = build_spanish_suite()
    print("Done building suites!")
