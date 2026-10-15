// Function-word presentation & ambient lighting for Fluency.
//
// Function words -- articles, prepositions, particles, clitics, contractions -- are
// taught by their structural role and deterministic content-word variation,
// rather than dictionary sense assignments.
//
// Supported deterministic closed-class focus suites: Portuguese (pt), Spanish (es).

export const FW_SIGNATURE_GLOW_RGB = '212, 218, 245'; // Periwinkle Moonstone Off-White

// Curated deterministic relational definitions for Portuguese closed-class focus words.
export const PORTUGUESE_GRAMMAR_WORDS = {
    "de": {
        "word": "de",
        "role": "Preposition",
        "rank": 4,
        "frequency": 25447,
        "relations": [
            {
                "tag": "Verbal Valency",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Complement</span>",
                "rule": "Required link: the preceding verb governs 'de' before its object or action.",
                "targetHTML": "<span class='fw-token-v'>Gosto</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>música</span>.",
                "translation": "I like music."
            },
            {
                "tag": "Noun Attribution",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                "rule": "Nominal binding: connects a head noun to its owner, origin, or content.",
                "targetHTML": "Quero um <span class='fw-token-v'>copo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>água</span>.",
                "translation": "I want a glass of water."
            }
        ],
        "uses": [
            {
                "tag": "Verbal Valency",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Complement</span>",
                "rule": "Required link: the preceding verb governs 'de' before its object or action.",
                "targetHTML": "<span class='fw-token-v'>Gosto</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>música</span>.",
                "translation": "I like music."
            },
            {
                "tag": "Noun Attribution",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                "rule": "Nominal binding: connects a head noun to its owner, origin, or content.",
                "targetHTML": "Quero um <span class='fw-token-v'>copo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>água</span>.",
                "translation": "I want a glass of water."
            }
        ]
    },
    "que": {
        "word": "que",
        "role": "Connector",
        "rank": 1,
        "frequency": 38240,
        "relations": [
            {
                "tag": "Clausal Link",
                "formulaHTML": "<span class=\"fw-token-v\">Thought / Speech</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Clause</span>",
                "rule": "Subordination: bridges what someone thinks, says, or knows to the statement.",
                "targetHTML": "<span class='fw-token-v'>Acho</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vai chover</span>.",
                "translation": "I think it’s going to rain."
            },
            {
                "tag": "Relative Pronoun",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                "rule": "Relativization: refers back to a noun while connecting more information.",
                "targetHTML": "Este é o <span class='fw-token-v'>livro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estou lendo</span>.",
                "translation": "This is the book that I’m reading."
            },
            {
                "tag": "Comparison",
                "formulaHTML": "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                "rule": "Comparison: connects the two sides of a degree or quality difference.",
                "targetHTML": "Ela é <span class='fw-token-v'>mais alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>eu</span>.",
                "translation": "She is taller than me."
            }
        ],
        "uses": [
            {
                "tag": "Clausal Link",
                "formulaHTML": "<span class=\"fw-token-v\">Thought / Speech</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Clause</span>",
                "rule": "Subordination: bridges what someone thinks, says, or knows to the statement.",
                "targetHTML": "<span class='fw-token-v'>Acho</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vai chover</span>.",
                "translation": "I think it’s going to rain."
            },
            {
                "tag": "Relative Pronoun",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                "rule": "Relativization: refers back to a noun while connecting more information.",
                "targetHTML": "Este é o <span class='fw-token-v'>livro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estou lendo</span>.",
                "translation": "This is the book that I’m reading."
            },
            {
                "tag": "Comparison",
                "formulaHTML": "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                "rule": "Comparison: connects the two sides of a degree or quality difference.",
                "targetHTML": "Ela é <span class='fw-token-v'>mais alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>eu</span>.",
                "translation": "She is taller than me."
            }
        ]
    },
    "naquele": {
        "word": "naquele",
        "role": "Contraction",
        "rank": 1104,
        "frequency": 88,
        "parts": [
            "em",
            "aquele"
        ],
        "relations": [
            {
                "tag": "Deictic Location",
                "formulaHTML": "<span class=\"fw-token-connector\">em + aquele</span> + <span class=\"fw-token-c\">Place / Time</span>",
                "rule": "Contraction formula pointing to a distant place or past moment.",
                "targetHTML": "Eu estava <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>lugar</span>.",
                "translation": "I was in that place."
            }
        ],
        "uses": [
            {
                "tag": "Deictic Location",
                "formulaHTML": "<span class=\"fw-token-connector\">em + aquele</span> + <span class=\"fw-token-c\">Place / Time</span>",
                "rule": "Contraction formula pointing to a distant place or past moment.",
                "targetHTML": "Eu estava <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>lugar</span>.",
                "translation": "I was in that place."
            }
        ]
    },
    "nos": {
        "word": "nos",
        "role": "Pronoun & Contraction",
        "rank": 44,
        "frequency": 1581,
        "relations": [
            {
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">nos</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Pronominal argument: represents 'us / to us' receiving the action of a verb.",
                "targetHTML": "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>chamou</span> para jantar.",
                "translation": "She called us for dinner."
            },
            {
                "tag": "Contraction",
                "formulaHTML": "<span class=\"fw-token-connector\">em + os</span> + <span class=\"fw-token-c\">Plural Noun</span>",
                "parts": [
                    "em",
                    "os"
                ],
                "rule": "Contraction of 'em + os' (in / on / at the) before a masculine plural noun.",
                "targetHTML": "Está <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>livros</span>.",
                "translation": "It’s in the books."
            }
        ],
        "uses": [
            {
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">nos</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Pronominal argument: represents 'us / to us' receiving the action of a verb.",
                "targetHTML": "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>chamou</span> para jantar.",
                "translation": "She called us for dinner."
            },
            {
                "tag": "Contraction",
                "formulaHTML": "<span class=\"fw-token-connector\">em + os</span> + <span class=\"fw-token-c\">Plural Noun</span>",
                "parts": [
                    "em",
                    "os"
                ],
                "rule": "Contraction of 'em + os' (in / on / at the) before a masculine plural noun.",
                "targetHTML": "Está <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>livros</span>.",
                "translation": "It’s in the books."
            }
        ]
    },
    "se": {
        "word": "se",
        "role": "Conjunction & Clitic",
        "rank": 11,
        "frequency": 7806,
        "relations": [
            {
                "tag": "Condition",
                "formulaHTML": "<span class=\"fw-token-connector\">Se</span> + <span class=\"fw-token-v\">Condition</span> , <span class=\"fw-token-c\">Result</span>",
                "rule": "Conditional marker: introduces a hypothetical situation before its consequence.",
                "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>chover</span>, <span class='fw-token-c'>fico em casa</span>.",
                "translation": "If it rains, I’ll stay home."
            },
            {
                "tag": "Reflexive Clitic",
                "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                "rule": "Reflexive clitic: action reflects back onto the person doing it.",
                "targetHTML": "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>olhou</span> no espelho.",
                "translation": "She looked at herself in the mirror."
            }
        ],
        "uses": [
            {
                "tag": "Condition",
                "formulaHTML": "<span class=\"fw-token-connector\">Se</span> + <span class=\"fw-token-v\">Condition</span> , <span class=\"fw-token-c\">Result</span>",
                "rule": "Conditional marker: introduces a hypothetical situation before its consequence.",
                "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>chover</span>, <span class='fw-token-c'>fico em casa</span>.",
                "translation": "If it rains, I’ll stay home."
            },
            {
                "tag": "Reflexive Clitic",
                "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                "rule": "Reflexive clitic: action reflects back onto the person doing it.",
                "targetHTML": "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>olhou</span> no espelho.",
                "translation": "She looked at herself in the mirror."
            }
        ]
    },
    "o": {
        "word": "o",
        "role": "Article & Clitic",
        "rank": 3,
        "frequency": 34538,
        "relations": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">o</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                "rule": "Definite determiner: points to a specific masculine singular noun.",
                "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>livro</span> está na mesa.",
                "translation": "The book is on the table."
            },
            {
                "tag": "Object Clitic",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">o</span>",
                "rule": "Direct object pronoun: replaces a 3rd-person masculine singular object.",
                "targetHTML": "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>vi</span> ontem no parque.",
                "translation": "I saw him yesterday in the park."
            }
        ],
        "uses": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">o</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                "rule": "Definite determiner: points to a specific masculine singular noun.",
                "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>livro</span> está na mesa.",
                "translation": "The book is on the table."
            },
            {
                "tag": "Object Clitic",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">o</span>",
                "rule": "Direct object pronoun: replaces a 3rd-person masculine singular object.",
                "targetHTML": "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>vi</span> ontem no parque.",
                "translation": "I saw him yesterday in the park."
            }
        ]
    },
    "em": {
        "word": "em",
        "role": "Preposition",
        "rank": 21,
        "frequency": 6025,
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Place</span>",
                "rule": "Spatial location: anchors an action or state to an enclosed place, city, or space.",
                "targetHTML": "<span class='fw-token-v'>Moro</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>Lisboa</span>.",
                "translation": "I live in Lisbon."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Time Period</span>",
                "rule": "Temporal framing: situates an event within a month, year, or duration.",
                "targetHTML": "<span class='fw-token-v'>Viajo</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>maio</span>.",
                "translation": "I travel in May."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Place</span>",
                "rule": "Spatial location: anchors an action or state to an enclosed place, city, or space.",
                "targetHTML": "<span class='fw-token-v'>Moro</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>Lisboa</span>.",
                "translation": "I live in Lisbon."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Time Period</span>",
                "rule": "Temporal framing: situates an event within a month, year, or duration.",
                "targetHTML": "<span class='fw-token-v'>Viajo</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>maio</span>.",
                "translation": "I travel in May."
            }
        ]
    },
    "para": {
        "word": "para",
        "role": "Preposition",
        "rank": 9,
        "frequency": 11850,
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Destination</span>",
                "rule": "Direction and destination: points toward a final physical goal or place of arrival.",
                "targetHTML": "<span class='fw-token-v'>Vou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>casa</span>.",
                "translation": "I am going home."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Goal</span>",
                "rule": "Purpose and objective: links an intentional action to what it aims to achieve.",
                "targetHTML": "<span class='fw-token-v'>Estudo</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                "translation": "I study in order to learn."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Object</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                "rule": "Beneficiary: marks who receives or benefits from something.",
                "targetHTML": "Isto é <span class='fw-token-v'>um presente</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>você</span>.",
                "translation": "This is a gift for you."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Destination</span>",
                "rule": "Direction and destination: points toward a final physical goal or place of arrival.",
                "targetHTML": "<span class='fw-token-v'>Vou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>casa</span>.",
                "translation": "I am going home."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Goal</span>",
                "rule": "Purpose and objective: links an intentional action to what it aims to achieve.",
                "targetHTML": "<span class='fw-token-v'>Estudo</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                "translation": "I study in order to learn."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Object</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                "rule": "Beneficiary: marks who receives or benefits from something.",
                "targetHTML": "Isto é <span class='fw-token-v'>um presente</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>você</span>.",
                "translation": "This is a gift for you."
            }
        ]
    },
    "com": {
        "word": "com",
        "role": "Preposition",
        "rank": 17,
        "frequency": 7842,
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Companion</span>",
                "rule": "Accompaniment: joins an action to the person or entity sharing it.",
                "targetHTML": "<span class='fw-token-v'>Falo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>você</span> amanhã.",
                "translation": "I speak with you tomorrow."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                "rule": "Instrument and manner: describes the means used or attitude applied.",
                "targetHTML": "<span class='fw-token-v'>Escrevo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>cuidado</span>.",
                "translation": "I write with care."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Companion</span>",
                "rule": "Accompaniment: joins an action to the person or entity sharing it.",
                "targetHTML": "<span class='fw-token-v'>Falo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>você</span> amanhã.",
                "translation": "I speak with you tomorrow."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                "rule": "Instrument and manner: describes the means used or attitude applied.",
                "targetHTML": "<span class='fw-token-v'>Escrevo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>cuidado</span>.",
                "translation": "I write with care."
            }
        ]
    },
    "por": {
        "word": "por",
        "role": "Preposition",
        "rank": 16,
        "frequency": 6938,
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                "rule": "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                "targetHTML": "<span class='fw-token-v'>Obrigado</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>ajudar</span>.",
                "translation": "Thank you for helping."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                "rule": "Trajectory: marks the path, medium, or space through which motion occurs.",
                "targetHTML": "<span class='fw-token-v'>Caminho</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aqui</span>.",
                "translation": "I walk around here."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                "rule": "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                "targetHTML": "<span class='fw-token-v'>Obrigado</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>ajudar</span>.",
                "translation": "Thank you for helping."
            },
            {
                "formulaHTML": "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                "rule": "Trajectory: marks the path, medium, or space through which motion occurs.",
                "targetHTML": "<span class='fw-token-v'>Caminho</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aqui</span>.",
                "translation": "I walk around here."
            }
        ]
    },
    "no": {
        "word": "no",
        "role": "Contraction",
        "rank": 13,
        "frequency": 4450,
        "parts": [
            "em",
            "o"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">em + o</span> + <span class=\"fw-token-c\">Masculine Noun / Place</span>",
                "rule": "Contraction of 'em + o' (in the / at the) before a specific masculine noun.",
                "targetHTML": "O livro está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>quarto</span>.",
                "translation": "The book is in the room."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">em + o</span> + <span class=\"fw-token-c\">Masculine Noun / Place</span>",
                "rule": "Contraction of 'em + o' (in the / at the) before a specific masculine noun.",
                "targetHTML": "O livro está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>quarto</span>.",
                "translation": "The book is in the room."
            }
        ]
    },
    "na": {
        "word": "na",
        "role": "Contraction",
        "rank": 31,
        "frequency": 4170,
        "parts": [
            "em",
            "a"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">em + a</span> + <span class=\"fw-token-c\">Feminine Noun / Place</span>",
                "rule": "Contraction of 'em + a' (in the / at the) before a specific feminine noun.",
                "targetHTML": "Ela está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>praia</span>.",
                "translation": "She is at the beach."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">em + a</span> + <span class=\"fw-token-c\">Feminine Noun / Place</span>",
                "rule": "Contraction of 'em + a' (in the / at the) before a specific feminine noun.",
                "targetHTML": "Ela está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>praia</span>.",
                "translation": "She is at the beach."
            }
        ]
    },
    "do": {
        "word": "do",
        "role": "Contraction",
        "rank": 19,
        "frequency": 7403,
        "parts": [
            "de",
            "o"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">de + o</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                "rule": "Contraction of 'de + o' (of the / from the) denoting possession, origin, or attribute.",
                "targetHTML": "Este é o carro <span class='fw-token-connector'>do</span> <span class='fw-token-c'>meu pai</span>.",
                "translation": "This is my father's car."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">de + o</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                "rule": "Contraction of 'de + o' (of the / from the) denoting possession, origin, or attribute.",
                "targetHTML": "Este é o carro <span class='fw-token-connector'>do</span> <span class='fw-token-c'>meu pai</span>.",
                "translation": "This is my father's car."
            }
        ]
    },
    "da": {
        "word": "da",
        "role": "Contraction",
        "rank": 27,
        "frequency": 5714,
        "parts": [
            "de",
            "a"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">de + a</span> + <span class=\"fw-token-c\">Feminine Noun / Origin</span>",
                "rule": "Contraction of 'de + a' (of the / from the) denoting possession, origin, or attribute.",
                "targetHTML": "Esta é a chave <span class='fw-token-connector'>da</span> <span class='fw-token-c'>casa</span>.",
                "translation": "This is the key to the house."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">de + a</span> + <span class=\"fw-token-c\">Feminine Noun / Origin</span>",
                "rule": "Contraction of 'de + a' (of the / from the) denoting possession, origin, or attribute.",
                "targetHTML": "Esta é a chave <span class='fw-token-connector'>da</span> <span class='fw-token-c'>casa</span>.",
                "translation": "This is the key to the house."
            }
        ]
    },
    "como": {
        "word": "como",
        "role": "Connector",
        "rank": 23,
        "frequency": 5447,
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Model / Standard</span>",
                "rule": "Simile and manner: compares the style or way an action is performed to an archetype.",
                "targetHTML": "Ela <span class='fw-token-v'>canta</span> <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um pássaro</span>.",
                "translation": "She sings like a bird."
            },
            {
                "formulaHTML": "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Role / Capacity</span>",
                "rule": "Capacity and function: specifies the role, profession, or capacity someone acts in.",
                "targetHTML": "Trabalho <span class='fw-token-connector'>como</span> <span class='fw-token-c'>engenheiro</span>.",
                "translation": "I work as an engineer."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Model / Standard</span>",
                "rule": "Simile and manner: compares the style or way an action is performed to an archetype.",
                "targetHTML": "Ela <span class='fw-token-v'>canta</span> <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um pássaro</span>.",
                "translation": "She sings like a bird."
            },
            {
                "formulaHTML": "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Role / Capacity</span>",
                "rule": "Capacity and function: specifies the role, profession, or capacity someone acts in.",
                "targetHTML": "Trabalho <span class='fw-token-connector'>como</span> <span class='fw-token-c'>engenheiro</span>.",
                "translation": "I work as an engineer."
            }
        ]
    },
    "mas": {
        "word": "mas",
        "role": "Connector",
        "rank": 26,
        "frequency": 6058,
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">mas</span> + <span class=\"fw-token-c\">Counterpoint</span>",
                "rule": "Adversative bridge: introduces a contrast, restriction, or unexpected limitation.",
                "targetHTML": "<span class='fw-token-v'>Tentei</span>, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>não consegui</span>.",
                "translation": "I tried, but I could not."
            }
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">mas</span> + <span class=\"fw-token-c\">Counterpoint</span>",
                "rule": "Adversative bridge: introduces a contrast, restriction, or unexpected limitation.",
                "targetHTML": "<span class='fw-token-v'>Tentei</span>, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>não consegui</span>.",
                "translation": "I tried, but I could not."
            }
        ]
    },
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        "parts": [
            "a",
            "o"
        ],
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
        ],
        "uses": [
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
        "parts": [
            "a",
            "a"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">a + a</span> + <span class=\"fw-token-c\">Feminine Destination / Time</span>",
                "rule": "Crasis contraction of 'a + a' (to the / at the) before feminine singular nouns.",
                "targetHTML": "Chegamos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>noite</span>.",
                "translation": "We arrived at night."
            }
        ],
        "uses": [
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
        "parts": [
            "por",
            "o"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">por + o</span> + <span class=\"fw-token-c\">Masculine Path / Reason</span>",
                "rule": "Contraction of 'por + o' (through the / by the / for the).",
                "targetHTML": "Caminhei <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>parque</span>.",
                "translation": "I walked through the park."
            }
        ],
        "uses": [
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
        "parts": [
            "por",
            "a"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">por + a</span> + <span class=\"fw-token-c\">Feminine Path / Reason</span>",
                "rule": "Contraction of 'por + a' (through the / by the / for the).",
                "targetHTML": "Obrigado <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>ajuda</span>.",
                "translation": "Thank you for the help."
            }
        ],
        "uses": [
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
        "parts": [
            "em",
            "um"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">em + um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                "rule": "Contraction of 'em + um' (in a / on a).",
                "targetHTML": "Moro <span class='fw-token-connector'>num</span> <span class='fw-token-c'>apartamento</span>.",
                "translation": "I live in an apartment."
            }
        ],
        "uses": [
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
        "parts": [
            "em",
            "uma"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">em + uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                "rule": "Contraction of 'em + uma' (in a / on a).",
                "targetHTML": "Entrei <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>loja</span>.",
                "translation": "I entered a shop."
            }
        ],
        "uses": [
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
        "parts": [
            "de",
            "ele"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dele</span>",
                "rule": "Possessive contraction of 'de + ele' (his / of him).",
                "targetHTML": "Conheço o amigo <span class='fw-token-connector'>dele</span>.",
                "translation": "I know his friend."
            }
        ],
        "uses": [
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
        "parts": [
            "de",
            "ela"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dela</span>",
                "rule": "Possessive contraction of 'de + ela' (her / of her).",
                "targetHTML": "A casa <span class='fw-token-connector'>dela</span> é grande.",
                "translation": "Her house is big."
            }
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">tudo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                "rule": "Universal pronoun: represents the totality of things ('everything / all').",
                "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>está</span> bem.",
                "translation": "Everything is fine."
            }
        ]
    }
};

// Curated deterministic relational definitions for Spanish closed-class focus words.
export const SPANISH_GRAMMAR_WORDS = {
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        "parts": [
            "a",
            "el"
        ],
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
        ],
        "uses": [
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
        "parts": [
            "de",
            "el"
        ],
        "relations": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">de + el</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                "rule": "Mandatory contraction of 'de + el' (of the / from the).",
                "targetHTML": "La puerta <span class='fw-token-connector'>del</span> <span class='fw-token-c'>hotel</span> está cerrada.",
                "translation": "The door of the hotel is closed."
            }
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
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
        ],
        "uses": [
            {
                "formulaHTML": "<span class=\"fw-token-connector\">Cuando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Action</span>",
                "rule": "Temporal connector: situates an event at a point in time.",
                "targetHTML": "<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>llegué</span>, <span class='fw-token-c'>todos sonrieron</span>.",
                "translation": "When I arrived, everyone smiled."
            }
        ]
    }
};

export const GRAMMAR_WORDS = {
    pt: PORTUGUESE_GRAMMAR_WORDS,
    portuguese: PORTUGUESE_GRAMMAR_WORDS,
    portuguese_brazilian: PORTUGUESE_GRAMMAR_WORDS,
    es: SPANISH_GRAMMAR_WORDS,
    spanish: SPANISH_GRAMMAR_WORDS,
};

// Backward-compatibility: ensure .uses aliases
for (const dict of [PORTUGUESE_GRAMMAR_WORDS, SPANISH_GRAMMAR_WORDS]) {
    for (const entry of Object.values(dict)) {
        if (!entry.uses) entry.uses = entry.relations;
    }
}

const ROLE_NAMES = {
    prep: 'preposition',
    article: 'article',
    subject_pron: 'subject',
    object_pron: 'object',
    reflexive: 'reflexive (-self)',
    interrogative: 'question word',
    indefinite: 'pronoun',
    quantifier: 'amount word',
    conj: 'conjunction',
    conj_that: 'conjunction',
    conj_if: 'conjunction',
    conj_before: 'conjunction',
    infinitive_to: 'to + verb',
    degree_too: 'too + adjective',
    existential_er: 'there is / are',
    locative_er: 'there (place)',
    pronominal_adverb: 'with a preposition',
    partitive_er: 'of them',
    possessive: 'possessive',
    aux_perfect: 'helper verb',
    aux_passive: 'helper verb (passive)',
    copula: 'linking verb',
    be: 'verb',
    adverb: 'adverb',
    demonstrative: 'pointing word',
    relative: 'relative pronoun',
    personal_a: 'personal a',
    impersonal_se: 'impersonal se',
    than: 'comparison',
    conditional: 'conditional',
    negation: 'negation',
};

function esc(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function shortGloss(gloss) {
    return String(gloss || '').split(/\s*[(;,]/)[0].trim();
}

const NOT_A_MEANING = /^used other than|\b(?:form|spelling) of\b|^synonym of\b/i;

function meaningOf(gloss) {
    return NOT_A_MEANING.test(String(gloss || '')) ? '' : gloss;
}

export function getGrammarWordDefinition(cardOrWord, lang) {
    const langKey = String(lang || 'pt').toLowerCase();
    const dict = GRAMMAR_WORDS[langKey] || (langKey.startsWith('es') ? SPANISH_GRAMMAR_WORDS : PORTUGUESE_GRAMMAR_WORDS);
    if (!dict) return null;
    const wordKey = typeof cardOrWord === 'string'
        ? cardOrWord.trim().toLowerCase()
        : String(cardOrWord?.targetWord || cardOrWord?.word || cardOrWord?.lemma || '').trim().toLowerCase();
    return dict[wordKey] || null;
}

export function isPortugueseGrammarWord(card, lang) {
    if (!card) return false;
    const isPt = !lang || lang === 'portuguese' || lang === 'pt' || lang === 'portuguese_brazilian';
    if (!isPt) return false;
    const wordKey = String(card.targetWord || card.word || card.lemma || '').trim().toLowerCase();
    return Boolean(PORTUGUESE_GRAMMAR_WORDS[wordKey]);
}

export function getPortugueseGrammarDefinition(card, lang) {
    return getGrammarWordDefinition(card, lang || 'pt');
}

export function isSpanishGrammarWord(card, lang) {
    if (!card) return false;
    const isEs = lang === 'spanish' || lang === 'es';
    if (!isEs) return false;
    const wordKey = String(card.targetWord || card.word || card.lemma || '').trim().toLowerCase();
    return Boolean(SPANISH_GRAMMAR_WORDS[wordKey]);
}

export function getSpanishGrammarDefinition(card, lang) {
    return getGrammarWordDefinition(card, lang || 'es');
}

export function isFunctionWordCard(card, lang) {
    return Boolean(card?.functionWord || getGrammarWordDefinition(card, lang));
}

// Computes ambient glow CSS for any flashcard based on POS rules & FW signature glow
export function getCardAmbientGlow(card, lang, activePos, isSplitCard, getPosAccentRgbFn) {
    const getRgb = getPosAccentRgbFn || (typeof window !== 'undefined' ? window.getPosAccentRgb : null) || (() => '148, 163, 184');

    // 1. Function words get the dedicated Periwinkle Moonstone Off-White halo
    if (isFunctionWordCard(card, lang)) {
        return `radial-gradient(circle at 50% 20%, rgba(${FW_SIGNATURE_GLOW_RGB}, 0.18), transparent 70%)`;
    }

    // 2. Non-function words
    // Companion card ("Card 1 of 2"): single POS color matching active companion card
    if (isSplitCard && card?.splitInfo) {
        const splitPos = card.splitInfo.pos || card.partOfSpeech || activePos;
        const rgb = getRgb(splitPos);
        return `radial-gradient(circle at 50% 20%, rgba(${rgb}, 0.18), transparent 70%)`;
    }

    // Collect distinct POS realized on this card (prioritize active/non-rare meanings)
    const nonRareMeanings = (card?.meanings || []).filter(m =>
        m && !m.isRareSense && m.prominenceLabel !== 'Rare' && !m.exampleOnly && !m.unassigned
    );
    const candidateMeanings = nonRareMeanings.length > 0 ? nonRareMeanings : (card?.meanings || []);

    const distinctPos = [...new Set(
        candidateMeanings
            .map(m => m?.pos)
            .filter(p => p && !['MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY'].includes(p))
    )];
    if (distinctPos.length === 0 && (card?.partOfSpeech || activePos)) {
        distinctPos.push(card.partOfSpeech || activePos);
    }

    // Single POS: single centered radial glow
    if (distinctPos.length <= 1) {
        const rgb = getRgb(distinctPos[0] || activePos);
        return `radial-gradient(circle at 50% 20%, rgba(${rgb}, 0.18), transparent 70%)`;
    }

    // Multi-POS Unified: multi-corner glow
    if (distinctPos.length === 2) {
        const rgb1 = getRgb(distinctPos[0]);
        const rgb2 = getRgb(distinctPos[1]);
        return `radial-gradient(circle at 22% 16%, rgba(${rgb1}, 0.17), transparent 58%), radial-gradient(circle at 78% 16%, rgba(${rgb2}, 0.17), transparent 58%)`;
    }

    // 3 or more POS
    const rgb1 = getRgb(distinctPos[0]);
    const rgb2 = getRgb(distinctPos[1]);
    const rgb3 = getRgb(distinctPos[2]);
    return `radial-gradient(circle at 18% 16%, rgba(${rgb1}, 0.15), transparent 50%), radial-gradient(circle at 50% 12%, rgba(${rgb2}, 0.15), transparent 50%), radial-gradient(circle at 82% 16%, rgba(${rgb3}, 0.15), transparent 50%)`;
}

// Active state for deterministic card back navigation
let _activeWordKey = null;
let _activeRelIndex = 0;

export function selectFunctionWordRelation(relIdx) {
    _activeRelIndex = Number(relIdx) || 0;
    refreshFunctionWordCardBack();
}

// Backward compatibility alias:
export function selectFunctionWordUse(useIdx) {
    selectFunctionWordRelation(useIdx);
}

function refreshFunctionWordCardBack() {
    const container = document.querySelector('.fw-deterministic-card');
    if (!container) return;
    const cardWord = container.dataset.word;
    const lang = container.dataset.lang || 'pt';
    const data = getGrammarWordDefinition(cardWord, lang);
    if (!data) return;

    const relations = data.relations || data.uses || [];
    if (_activeRelIndex >= relations.length) _activeRelIndex = 0;
    const currentRel = relations[_activeRelIndex];

    // Update relations selection
    container.querySelectorAll('.fw-relation-box').forEach((btn, i) => {
        const isSelected = i === _activeRelIndex;
        btn.setAttribute('aria-pressed', String(isSelected));
        btn.classList.toggle('is-selected', isSelected);
    });

    // Update contextual parts box (e.g. for hybrid nos)
    const dynamicPartsBox = container.querySelector('.fw-dynamic-parts-box');
    if (dynamicPartsBox) {
        if (currentRel?.parts && currentRel.parts.length === 2) {
            dynamicPartsBox.innerHTML = `<span class="fw-part-pill">${esc(currentRel.parts[0])}</span> <span class="fw-part-plus">+</span> <span class="fw-part-pill">${esc(currentRel.parts[1])}</span>`;
            dynamicPartsBox.style.display = 'inline-flex';
        } else {
            dynamicPartsBox.style.display = 'none';
        }
    }

    // Update sentence target and translation
    const sentenceEl = container.querySelector('.fw-sentence-target');
    if (sentenceEl && currentRel) {
        sentenceEl.innerHTML = currentRel.targetHTML || currentRel.target || '';
    }

    const transEl = container.querySelector('.fw-sentence-translation');
    if (transEl && currentRel) {
        transEl.textContent = currentRel.translation || '';
    }
}

// Make functions available globally for onclick handlers
if (typeof window !== 'undefined') {
    window.selectFunctionWordRelation = selectFunctionWordRelation;
    window.selectFunctionWordUse = selectFunctionWordUse;
    window.getCardAmbientGlow = getCardAmbientGlow;
    window.FW_SIGNATURE_GLOW_RGB = FW_SIGNATURE_GLOW_RGB;
}

export function functionWordLabelText(label) {
    if (!label || !label.value) return '';
    if (label.kind === 'unit') {
        const gloss = shortGloss(meaningOf(label.gloss));
        return gloss ? `${label.value} · ${gloss}` : label.value;
    }
    const name = ROLE_NAMES[label.value] || label.value.replace(/_/g, ' ');
    const gloss = label.value === 'prep' ? String(label.gloss || '').replace(/\s*\(\+ verb\)$/, '') : label.gloss;
    return gloss && gloss !== name ? `${name} · ${gloss}` : name;
}

/** Card-back block replacing the sense list: what the word does, and its constructions. */
export function functionWordBlockHTML(card, lang) {
    const fwData = getGrammarWordDefinition(card, lang) || (card?.functionWord?.uses ? card.functionWord : null);

    // 1. Deterministic layout for Portuguese and Spanish focus grammar words
    if (fwData && (fwData.relations || fwData.uses)) {
        const wordKey = fwData.word || card.targetWord || card.word;
        if (_activeWordKey !== wordKey) {
            _activeWordKey = wordKey;
            _activeRelIndex = 0;
        }

        const relations = fwData.relations || fwData.uses || [];
        if (_activeRelIndex >= relations.length) _activeRelIndex = 0;
        const currentRel = relations[_activeRelIndex];

        // Permanent contraction formula box (e.g. naquele = em + aquele)
        let partsBoxHTML = '';
        if (fwData.parts && fwData.parts.length === 2) {
            partsBoxHTML = `
                <div class="fw-parts-box">
                    <span class="fw-part-pill">${esc(fwData.parts[0])}</span>
                    <span class="fw-part-plus">+</span>
                    <span class="fw-part-pill">${esc(fwData.parts[1])}</span>
                </div>`;
        }

        // Contextual formula box for hybrid words (e.g. nos = em + os when contraction relation is active)
        let dynamicPartsHTML = '';
        if (!fwData.parts) {
            const hasParts = currentRel?.parts && currentRel.parts.length === 2;
            dynamicPartsHTML = `
                <div class="fw-parts-box fw-dynamic-parts-box" style="${hasParts ? 'display: inline-flex;' : 'display: none;'}">
                    ${hasParts ? `<span class="fw-part-pill">${esc(currentRel.parts[0])}</span> <span class="fw-part-plus">+</span> <span class="fw-part-pill">${esc(currentRel.parts[1])}</span>` : ''}
                </div>`;
        }

        // Relations tiles (no square brackets, color alone establishes constituents)
        const relationsHTML = relations.map((rel, i) => {
            const isSelected = i === _activeRelIndex;
            return `
                <button type="button" class="fw-relation-box${isSelected ? ' is-selected' : ''}" aria-pressed="${isSelected}" onclick="event.stopPropagation(); window.selectFunctionWordRelation(${i})">
                    <div class="fw-relation-formula">${rel.formulaHTML || esc(rel.formula || '')}</div>
                    <p class="fw-relation-rule">${esc(rel.rule || rel.description || '')}</p>
                </button>`;
        }).join('');

        const targetHTML = currentRel?.targetHTML || esc(currentRel?.target || '');
        const plainTargetText = targetHTML.replace(/<[^>]+>/g, '');

        return `
            <div class="fw-deterministic-card" data-word="${esc(wordKey)}" data-lang="${esc(lang || 'pt')}">
                <div class="fw-header">
                    <h2 class="fw-heading">${esc(wordKey)}</h2>
                    <div class="fw-section-header">Function Word · Example Patterns</div>
                </div>
                ${partsBoxHTML}
                ${dynamicPartsHTML}
                <div class="fw-relations-list">
                    ${relationsHTML}
                </div>
                <div class="fw-sentence-panel" onclick="event.stopPropagation(); (window.speakTargetSentence?.() || window.speakText?.('${esc(plainTargetText)}'))">
                    <div class="fw-sentence-target">${targetHTML}</div>
                    <div class="fw-sentence-translation">${esc(currentRel?.translation || '')}</div>
                </div>
            </div>`;
    }

    // 2. Fallback to existing prototype for other languages/words
    const summary = card?.functionWord;
    if (!summary) return '';
    const distinct = texts => [...new Set(texts.filter(Boolean))];
    const roleTexts = distinct((summary.roles || []).map(r => functionWordLabelText({ kind: 'role', ...r }))).slice(0, 3);
    const patternTexts = distinct((summary.patterns || []).filter(p => p.count >= 2 && meaningOf(p.gloss))
        .map(p => functionWordLabelText({ kind: 'unit', ...p }))).slice(0, 3);
    const roleChips = roleTexts.map(t => `<span class="fw-chip fw-chip-role">${esc(t)}</span>`).join('');
    const patternChips = patternTexts.map(t => `<span class="fw-chip fw-chip-pattern">${esc(t)}</span>`).join('');

    return `
        <div class="fw-block">
            <div class="fw-row"><span class="fw-badge">Grammar word</span>${roleChips}</div>
            ${patternChips ? `<div class="fw-row"><span class="fw-row-label">Patterns</span>${patternChips}</div>` : ''}
        </div>`;
}

/** The label under one example's translation; empty when the rules gave none. */
export function functionWordExampleHTML(example) {
    const label = example?.metadata?.function_word;
    const text = functionWordLabelText(label);
    if (!text) return '';
    const kind = label.kind === 'unit' ? 'fw-chip-pattern' : 'fw-chip-role';
    return `<div class="fw-example-label"><span class="fw-chip ${kind}">${esc(text)}</span></div>`;
}
