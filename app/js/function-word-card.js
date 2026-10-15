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
                "allowed_lemmas": [
                    "gostar",
                    "precisar",
                    "lembrar",
                    "depender",
                    "esquecer",
                    "tratar",
                    "falar",
                    "desistir"
                ],
                "targetHTML": "<span class='fw-token-v'>Gosto</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>música</span>.",
                "translation": "I like music.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Gosto</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>música</span>.",
                        "translation": "I like music.",
                        "source": "Ainda Bem · Marisa Monte"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Gostamos</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>passear por aí</span>.",
                        "translation": "We like to stroll around.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ele <span class='fw-token-v'>precisa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ajuda agora</span>.",
                        "translation": "He needs help now.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Lembro-me</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>tudo perfeitamente</span>.",
                        "translation": "I remember everything perfectly.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Isso <span class='fw-token-v'>depende</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>muitas coisas</span>.",
                        "translation": "That depends on many things.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Não podemos <span class='fw-token-v'>desistir</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>lutar</span>.",
                        "translation": "We cannot give up fighting.",
                        "source": "Film dialogue"
                    }
                ]
            },
            {
                "tag": "Noun Attribution",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                "rule": "Nominal binding: connects a head noun to its owner, origin, or material.",
                "allowed_lemmas": [
                    "copo",
                    "casa",
                    "carro",
                    "hora",
                    "mesa",
                    "dia",
                    "homem",
                    "tempo"
                ],
                "targetHTML": "Quero um <span class='fw-token-v'>copo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>água</span>.",
                "translation": "I want a glass of water.",
                "examples": [
                    {
                        "targetHTML": "Quero um <span class='fw-token-v'>copo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>água</span>.",
                        "translation": "I want a glass of water.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Uma <span class='fw-token-v'>mesa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>madeira maciça</span>.",
                        "translation": "A solid wood table.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "É <span class='fw-token-v'>hora</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>partir</span>.",
                        "translation": "It is time to leave.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Um <span class='fw-token-v'>dia</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>sol</span> na praia.",
                        "translation": "A sunny day at the beach.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ele é um <span class='fw-token-v'>homem</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>palavra</span>.",
                        "translation": "He is a man of his word.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Verbal Valency",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Complement</span>",
                "rule": "Required link: the preceding verb governs 'de' before its object or action.",
                "allowed_lemmas": [
                    "gostar",
                    "precisar",
                    "lembrar",
                    "depender",
                    "esquecer",
                    "tratar",
                    "falar",
                    "desistir"
                ],
                "targetHTML": "<span class='fw-token-v'>Gosto</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>música</span>.",
                "translation": "I like music.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Gosto</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>música</span>.",
                        "translation": "I like music.",
                        "source": "Ainda Bem · Marisa Monte"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Gostamos</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>passear por aí</span>.",
                        "translation": "We like to stroll around.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ele <span class='fw-token-v'>precisa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ajuda agora</span>.",
                        "translation": "He needs help now.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Lembro-me</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>tudo perfeitamente</span>.",
                        "translation": "I remember everything perfectly.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Isso <span class='fw-token-v'>depende</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>muitas coisas</span>.",
                        "translation": "That depends on many things.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Não podemos <span class='fw-token-v'>desistir</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>lutar</span>.",
                        "translation": "We cannot give up fighting.",
                        "source": "Film dialogue"
                    }
                ]
            },
            {
                "tag": "Noun Attribution",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                "rule": "Nominal binding: connects a head noun to its owner, origin, or material.",
                "allowed_lemmas": [
                    "copo",
                    "casa",
                    "carro",
                    "hora",
                    "mesa",
                    "dia",
                    "homem",
                    "tempo"
                ],
                "targetHTML": "Quero um <span class='fw-token-v'>copo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>água</span>.",
                "translation": "I want a glass of water.",
                "examples": [
                    {
                        "targetHTML": "Quero um <span class='fw-token-v'>copo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>água</span>.",
                        "translation": "I want a glass of water.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Uma <span class='fw-token-v'>mesa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>madeira maciça</span>.",
                        "translation": "A solid wood table.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "É <span class='fw-token-v'>hora</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>partir</span>.",
                        "translation": "It is time to leave.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Um <span class='fw-token-v'>dia</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>sol</span> na praia.",
                        "translation": "A sunny day at the beach.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ele é um <span class='fw-token-v'>homem</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>palavra</span>.",
                        "translation": "He is a man of his word.",
                        "source": "Literature"
                    }
                ]
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
                "allowed_lemmas": [
                    "achar",
                    "pensar",
                    "saber",
                    "dizer",
                    "esperar",
                    "ver",
                    "sentir"
                ],
                "targetHTML": "<span class='fw-token-v'>Acho</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vai chover</span>.",
                "translation": "I think it’s going to rain.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Acho</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vai chover</span>.",
                        "translation": "I think it’s going to rain.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>disse</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>viria hoje</span>.",
                        "translation": "She said she would come today.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Sei</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>você tem razão</span>.",
                        "translation": "I know you are right.",
                        "source": "Contemporary speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Espero</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>tudo corra bem</span>.",
                        "translation": "I hope everything goes well.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ele <span class='fw-token-v'>pensou</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estava sozinho</span>.",
                        "translation": "He thought he was alone.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Relative Pronoun",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                "rule": "Relativization: refers back to a noun while connecting more information.",
                "allowed_lemmas": [
                    "livro",
                    "pessoa",
                    "filme",
                    "lugar",
                    "coisa",
                    "carro",
                    "casa"
                ],
                "targetHTML": "Este é o <span class='fw-token-v'>livro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estou lendo</span>.",
                "translation": "This is the book that I’m reading.",
                "examples": [
                    {
                        "targetHTML": "Este é o <span class='fw-token-v'>livro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estou lendo</span>.",
                        "translation": "This is the book that I’m reading.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "A <span class='fw-token-v'>pessoa</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>me ligou não falou nada</span>.",
                        "translation": "The person who called me said nothing.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O <span class='fw-token-v'>filme</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vimos ontem foi ótimo</span>.",
                        "translation": "The movie we saw yesterday was great.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O <span class='fw-token-v'>lugar</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>visitamos era lindo</span>.",
                        "translation": "The place we visited was beautiful.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "São <span class='fw-token-v'>coisas</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>acontecem na vida</span>.",
                        "translation": "These are things that happen in life.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Comparison",
                "formulaHTML": "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                "rule": "Comparison: connects the two sides of a degree or quality difference.",
                "allowed_lemmas": [
                    "mais",
                    "menos",
                    "melhor",
                    "pior",
                    "maior",
                    "menor"
                ],
                "targetHTML": "Ela é <span class='fw-token-v'>mais alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>eu</span>.",
                "translation": "She is taller than me.",
                "examples": [
                    {
                        "targetHTML": "Ela é <span class='fw-token-v'>mais alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>eu</span>.",
                        "translation": "She is taller than me.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Isto é <span class='fw-token-v'>melhor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>o esperado</span>.",
                        "translation": "This is better than expected.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Gastamos <span class='fw-token-v'>menos tempo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>ontem</span>.",
                        "translation": "We spent less time than yesterday.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "A casa é <span class='fw-token-v'>maior</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>o apartamento</span>.",
                        "translation": "The house is bigger than the apartment.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Hoje está <span class='fw-token-v'>mais frio</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>semana passada</span>.",
                        "translation": "Today is colder than last week.",
                        "source": "Contemporary speech"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Clausal Link",
                "formulaHTML": "<span class=\"fw-token-v\">Thought / Speech</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Clause</span>",
                "rule": "Subordination: bridges what someone thinks, says, or knows to the statement.",
                "allowed_lemmas": [
                    "achar",
                    "pensar",
                    "saber",
                    "dizer",
                    "esperar",
                    "ver",
                    "sentir"
                ],
                "targetHTML": "<span class='fw-token-v'>Acho</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vai chover</span>.",
                "translation": "I think it’s going to rain.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Acho</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vai chover</span>.",
                        "translation": "I think it’s going to rain.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>disse</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>viria hoje</span>.",
                        "translation": "She said she would come today.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Sei</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>você tem razão</span>.",
                        "translation": "I know you are right.",
                        "source": "Contemporary speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Espero</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>tudo corra bem</span>.",
                        "translation": "I hope everything goes well.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ele <span class='fw-token-v'>pensou</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estava sozinho</span>.",
                        "translation": "He thought he was alone.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Relative Pronoun",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                "rule": "Relativization: refers back to a noun while connecting more information.",
                "allowed_lemmas": [
                    "livro",
                    "pessoa",
                    "filme",
                    "lugar",
                    "coisa",
                    "carro",
                    "casa"
                ],
                "targetHTML": "Este é o <span class='fw-token-v'>livro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estou lendo</span>.",
                "translation": "This is the book that I’m reading.",
                "examples": [
                    {
                        "targetHTML": "Este é o <span class='fw-token-v'>livro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estou lendo</span>.",
                        "translation": "This is the book that I’m reading.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "A <span class='fw-token-v'>pessoa</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>me ligou não falou nada</span>.",
                        "translation": "The person who called me said nothing.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O <span class='fw-token-v'>filme</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vimos ontem foi ótimo</span>.",
                        "translation": "The movie we saw yesterday was great.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O <span class='fw-token-v'>lugar</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>visitamos era lindo</span>.",
                        "translation": "The place we visited was beautiful.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "São <span class='fw-token-v'>coisas</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>acontecem na vida</span>.",
                        "translation": "These are things that happen in life.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Comparison",
                "formulaHTML": "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                "rule": "Comparison: connects the two sides of a degree or quality difference.",
                "allowed_lemmas": [
                    "mais",
                    "menos",
                    "melhor",
                    "pior",
                    "maior",
                    "menor"
                ],
                "targetHTML": "Ela é <span class='fw-token-v'>mais alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>eu</span>.",
                "translation": "She is taller than me.",
                "examples": [
                    {
                        "targetHTML": "Ela é <span class='fw-token-v'>mais alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>eu</span>.",
                        "translation": "She is taller than me.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Isto é <span class='fw-token-v'>melhor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>o esperado</span>.",
                        "translation": "This is better than expected.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Gastamos <span class='fw-token-v'>menos tempo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>ontem</span>.",
                        "translation": "We spent less time than yesterday.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "A casa é <span class='fw-token-v'>maior</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>o apartamento</span>.",
                        "translation": "The house is bigger than the apartment.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Hoje está <span class='fw-token-v'>mais frio</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>semana passada</span>.",
                        "translation": "Today is colder than last week.",
                        "source": "Contemporary speech"
                    }
                ]
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
                "allowed_lemmas": [
                    "lugar",
                    "momento",
                    "dia",
                    "ano",
                    "tempo",
                    "canto"
                ],
                "targetHTML": "Eu estava <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>lugar</span>.",
                "translation": "I was in that place.",
                "examples": [
                    {
                        "targetHTML": "Eu estava <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>lugar</span>.",
                        "translation": "I was in that place.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Naquele</span> <span class='fw-token-c'>momento</span>, tudo mudou.",
                        "translation": "At that moment, everything changed.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Nos conhecemos <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>ano inesquecível</span>.",
                        "translation": "We met in that unforgettable year.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Deixei as chaves <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>quarto</span>.",
                        "translation": "I left the keys in that room.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Naquele</span> <span class='fw-token-c'>dia</span> choveu sem parar.",
                        "translation": "On that day it rained without stopping.",
                        "source": "Subtitles"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Deictic Location",
                "formulaHTML": "<span class=\"fw-token-connector\">em + aquele</span> + <span class=\"fw-token-c\">Place / Time</span>",
                "rule": "Contraction formula pointing to a distant place or past moment.",
                "allowed_lemmas": [
                    "lugar",
                    "momento",
                    "dia",
                    "ano",
                    "tempo",
                    "canto"
                ],
                "targetHTML": "Eu estava <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>lugar</span>.",
                "translation": "I was in that place.",
                "examples": [
                    {
                        "targetHTML": "Eu estava <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>lugar</span>.",
                        "translation": "I was in that place.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Naquele</span> <span class='fw-token-c'>momento</span>, tudo mudou.",
                        "translation": "At that moment, everything changed.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Nos conhecemos <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>ano inesquecível</span>.",
                        "translation": "We met in that unforgettable year.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Deixei as chaves <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>quarto</span>.",
                        "translation": "I left the keys in that room.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Naquele</span> <span class='fw-token-c'>dia</span> choveu sem parar.",
                        "translation": "On that day it rained without stopping.",
                        "source": "Subtitles"
                    }
                ]
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
                "allowed_lemmas": [
                    "chamar",
                    "ver",
                    "ajudar",
                    "ouvir",
                    "contar",
                    "encontrar"
                ],
                "targetHTML": "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>chamou</span> para jantar.",
                "translation": "She called us for dinner.",
                "examples": [
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>chamou</span> para jantar.",
                        "translation": "She called us for dinner.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "O professor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ensinou</span> muito.",
                        "translation": "The teacher taught us a lot.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Eles <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>viram</span> no centro.",
                        "translation": "They saw us downtown.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Alguém <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ajudou</span> a tempo.",
                        "translation": "Someone helped us in time.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>contou</span> a verdade.",
                        "translation": "She told us the truth.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Contraction",
                "formulaHTML": "<span class=\"fw-token-connector\">em + os</span> + <span class=\"fw-token-c\">Plural Noun</span>",
                "rule": "Contraction of 'em + os' (in / on / at the) before a masculine plural noun.",
                "allowed_lemmas": [
                    "livro",
                    "olho",
                    "braço",
                    "dia",
                    "parque",
                    "ombro"
                ],
                "targetHTML": "Está <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>livros</span>.",
                "translation": "It’s in the books.",
                "examples": [
                    {
                        "targetHTML": "Está <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>livros</span>.",
                        "translation": "It’s in the books.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Vi a tristeza <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>olhos dele</span>.",
                        "translation": "I saw sadness in his eyes.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Passeamos <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>parques da cidade</span>.",
                        "translation": "We strolled in the city parks.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Nos</span> <span class='fw-token-c'>dias de festa</span>, a vila enche-se.",
                        "translation": "On festival days, the village fills up.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "O peso caiu <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>nossos ombros</span>.",
                        "translation": "The weight fell on our shoulders.",
                        "source": "Everyday speech"
                    }
                ],
                "parts": [
                    "em",
                    "os"
                ]
            }
        ],
        "uses": [
            {
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">nos</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Pronominal argument: represents 'us / to us' receiving the action of a verb.",
                "allowed_lemmas": [
                    "chamar",
                    "ver",
                    "ajudar",
                    "ouvir",
                    "contar",
                    "encontrar"
                ],
                "targetHTML": "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>chamou</span> para jantar.",
                "translation": "She called us for dinner.",
                "examples": [
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>chamou</span> para jantar.",
                        "translation": "She called us for dinner.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "O professor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ensinou</span> muito.",
                        "translation": "The teacher taught us a lot.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Eles <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>viram</span> no centro.",
                        "translation": "They saw us downtown.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Alguém <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ajudou</span> a tempo.",
                        "translation": "Someone helped us in time.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>contou</span> a verdade.",
                        "translation": "She told us the truth.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Contraction",
                "formulaHTML": "<span class=\"fw-token-connector\">em + os</span> + <span class=\"fw-token-c\">Plural Noun</span>",
                "rule": "Contraction of 'em + os' (in / on / at the) before a masculine plural noun.",
                "allowed_lemmas": [
                    "livro",
                    "olho",
                    "braço",
                    "dia",
                    "parque",
                    "ombro"
                ],
                "targetHTML": "Está <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>livros</span>.",
                "translation": "It’s in the books.",
                "examples": [
                    {
                        "targetHTML": "Está <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>livros</span>.",
                        "translation": "It’s in the books.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Vi a tristeza <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>olhos dele</span>.",
                        "translation": "I saw sadness in his eyes.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Passeamos <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>parques da cidade</span>.",
                        "translation": "We strolled in the city parks.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Nos</span> <span class='fw-token-c'>dias de festa</span>, a vila enche-se.",
                        "translation": "On festival days, the village fills up.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "O peso caiu <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>nossos ombros</span>.",
                        "translation": "The weight fell on our shoulders.",
                        "source": "Everyday speech"
                    }
                ],
                "parts": [
                    "em",
                    "os"
                ]
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
                "allowed_lemmas": [
                    "chover",
                    "quiser",
                    "puder",
                    "souber",
                    "tiver",
                    "precisar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>chover</span>, <span class='fw-token-c'>fico em casa</span>.",
                "translation": "If it rains, I’ll stay home.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>chover</span>, <span class='fw-token-c'>fico em casa</span>.",
                        "translation": "If it rains, I’ll stay home.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> você <span class='fw-token-v'>quiser</span>, <span class='fw-token-c'>podemos ir juntos</span>.",
                        "translation": "If you want, we can go together.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> eu <span class='fw-token-v'>souber</span> de algo, <span class='fw-token-c'>aviso</span>.",
                        "translation": "If I know anything, I'll let you know.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>tiver tempo</span>, <span class='fw-token-c'>leia este artigo</span>.",
                        "translation": "If you have time, read this article.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>precisares</span>, <span class='fw-token-c'>estou aqui</span>.",
                        "translation": "If you need, I am here.",
                        "source": "Contemporary dialogue"
                    }
                ]
            },
            {
                "tag": "Reflexive Clitic",
                "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                "rule": "Reflexive clitic: action reflects back onto the person doing it.",
                "allowed_lemmas": [
                    "olhar",
                    "sentir",
                    "lembrar",
                    "vestir",
                    "lavar",
                    "sentar"
                ],
                "targetHTML": "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>olhou</span> no espelho.",
                "translation": "She looked at herself in the mirror.",
                "examples": [
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>olhou</span> no espelho.",
                        "translation": "She looked at herself in the mirror.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Ele <span class='fw-token-connector'>se</span> <span class='fw-token-v'>sente</span> muito melhor hoje.",
                        "translation": "He feels much better today.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Eles <span class='fw-token-connector'>se</span> <span class='fw-token-v'>levantaram</span> cedo.",
                        "translation": "They got up early.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "O menino <span class='fw-token-connector'>se</span> <span class='fw-token-v'>vestiu</span> rapidamente.",
                        "translation": "The boy got dressed quickly.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>sentou</span> junto à janela.",
                        "translation": "She sat down by the window.",
                        "source": "Dialogue"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Condition",
                "formulaHTML": "<span class=\"fw-token-connector\">Se</span> + <span class=\"fw-token-v\">Condition</span> , <span class=\"fw-token-c\">Result</span>",
                "rule": "Conditional marker: introduces a hypothetical situation before its consequence.",
                "allowed_lemmas": [
                    "chover",
                    "quiser",
                    "puder",
                    "souber",
                    "tiver",
                    "precisar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>chover</span>, <span class='fw-token-c'>fico em casa</span>.",
                "translation": "If it rains, I’ll stay home.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>chover</span>, <span class='fw-token-c'>fico em casa</span>.",
                        "translation": "If it rains, I’ll stay home.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> você <span class='fw-token-v'>quiser</span>, <span class='fw-token-c'>podemos ir juntos</span>.",
                        "translation": "If you want, we can go together.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> eu <span class='fw-token-v'>souber</span> de algo, <span class='fw-token-c'>aviso</span>.",
                        "translation": "If I know anything, I'll let you know.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>tiver tempo</span>, <span class='fw-token-c'>leia este artigo</span>.",
                        "translation": "If you have time, read this article.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>precisares</span>, <span class='fw-token-c'>estou aqui</span>.",
                        "translation": "If you need, I am here.",
                        "source": "Contemporary dialogue"
                    }
                ]
            },
            {
                "tag": "Reflexive Clitic",
                "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                "rule": "Reflexive clitic: action reflects back onto the person doing it.",
                "allowed_lemmas": [
                    "olhar",
                    "sentir",
                    "lembrar",
                    "vestir",
                    "lavar",
                    "sentar"
                ],
                "targetHTML": "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>olhou</span> no espelho.",
                "translation": "She looked at herself in the mirror.",
                "examples": [
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>olhou</span> no espelho.",
                        "translation": "She looked at herself in the mirror.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Ele <span class='fw-token-connector'>se</span> <span class='fw-token-v'>sente</span> muito melhor hoje.",
                        "translation": "He feels much better today.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Eles <span class='fw-token-connector'>se</span> <span class='fw-token-v'>levantaram</span> cedo.",
                        "translation": "They got up early.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "O menino <span class='fw-token-connector'>se</span> <span class='fw-token-v'>vestiu</span> rapidamente.",
                        "translation": "The boy got dressed quickly.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>sentou</span> junto à janela.",
                        "translation": "She sat down by the window.",
                        "source": "Dialogue"
                    }
                ]
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
                "allowed_lemmas": [
                    "livro",
                    "carro",
                    "dia",
                    "tempo",
                    "trabalho",
                    "sol"
                ],
                "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>livro</span> está na mesa.",
                "translation": "The book is on the table.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>livro</span> está na mesa.",
                        "translation": "The book is on the table.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>carro</span> novo funciona bem.",
                        "translation": "The new car works well.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>dia</span> começou ensolarado.",
                        "translation": "The day began sunny.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>trabalho</span> foi concluído com sucesso.",
                        "translation": "The work was completed successfully.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>sol</span> brilha forte lá fora.",
                        "translation": "The sun shines brightly outside.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Object Clitic",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">o</span>",
                "rule": "Direct object pronoun: replaces a 3rd-person masculine singular object ('him / it').",
                "allowed_lemmas": [
                    "ver",
                    "encontrar",
                    "conhecer",
                    "ouvir",
                    "deixar",
                    "levar"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>vi</span> ontem no parque.",
                "translation": "I saw him yesterday in the park.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>vi</span> ontem no parque.",
                        "translation": "I saw him yesterday in the park.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Não <span class='fw-token-connector'>o</span> <span class='fw-token-v'>encontrei</span> em lugar nenhum.",
                        "translation": "I didn't find it anywhere.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Todos <span class='fw-token-connector'>o</span> <span class='fw-token-v'>conhecem</span> na cidade.",
                        "translation": "Everyone knows him in town.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>deixei</span> sobre a bancada.",
                        "translation": "I left it on the counter.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "O guarda <span class='fw-token-connector'>o</span> <span class='fw-token-v'>ouviu</span> gritar.",
                        "translation": "The guard heard him yell.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">o</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                "rule": "Definite determiner: points to a specific masculine singular noun.",
                "allowed_lemmas": [
                    "livro",
                    "carro",
                    "dia",
                    "tempo",
                    "trabalho",
                    "sol"
                ],
                "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>livro</span> está na mesa.",
                "translation": "The book is on the table.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>livro</span> está na mesa.",
                        "translation": "The book is on the table.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>carro</span> novo funciona bem.",
                        "translation": "The new car works well.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>dia</span> começou ensolarado.",
                        "translation": "The day began sunny.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>trabalho</span> foi concluído com sucesso.",
                        "translation": "The work was completed successfully.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>sol</span> brilha forte lá fora.",
                        "translation": "The sun shines brightly outside.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Object Clitic",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">o</span>",
                "rule": "Direct object pronoun: replaces a 3rd-person masculine singular object ('him / it').",
                "allowed_lemmas": [
                    "ver",
                    "encontrar",
                    "conhecer",
                    "ouvir",
                    "deixar",
                    "levar"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>vi</span> ontem no parque.",
                "translation": "I saw him yesterday in the park.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>vi</span> ontem no parque.",
                        "translation": "I saw him yesterday in the park.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Não <span class='fw-token-connector'>o</span> <span class='fw-token-v'>encontrei</span> em lugar nenhum.",
                        "translation": "I didn't find it anywhere.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Todos <span class='fw-token-connector'>o</span> <span class='fw-token-v'>conhecem</span> na cidade.",
                        "translation": "Everyone knows him in town.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>deixei</span> sobre a bancada.",
                        "translation": "I left it on the counter.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "O guarda <span class='fw-token-connector'>o</span> <span class='fw-token-v'>ouviu</span> gritar.",
                        "translation": "The guard heard him yell.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Spatial Location",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Place</span>",
                "rule": "Spatial location: anchors an action or state to an enclosed place, city, or space.",
                "allowed_lemmas": [
                    "morar",
                    "viver",
                    "entrar",
                    "ficar",
                    "estar",
                    "trabalhar"
                ],
                "targetHTML": "<span class='fw-token-v'>Moro</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>Lisboa</span>.",
                "translation": "I live in Lisbon.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Moro</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>Lisboa</span>.",
                        "translation": "I live in Lisbon.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Eles <span class='fw-token-v'>ficaram</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>casa</span> hoje.",
                        "translation": "They stayed at home today.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Trabalho</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>um hospital</span>.",
                        "translation": "I work in a hospital.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Nós <span class='fw-token-v'>entramos</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>uma sala ampla</span>.",
                        "translation": "We entered a large room.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O café <span class='fw-token-v'>fica</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>frente à estação</span>.",
                        "translation": "The cafe is in front of the station.",
                        "source": "Contemporary speech"
                    }
                ]
            },
            {
                "tag": "Temporal Framing",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Time Period</span>",
                "rule": "Temporal framing: situates an event within a month, year, or duration.",
                "allowed_lemmas": [
                    "viajar",
                    "nascer",
                    "terminar",
                    "voltar",
                    "chegar",
                    "começar"
                ],
                "targetHTML": "<span class='fw-token-v'>Viajo</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>maio</span>.",
                "translation": "I travel in May.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Viajo</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>maio</span>.",
                        "translation": "I travel in May.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>nasceu</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>1995</span>.",
                        "translation": "She was born in 1995.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Terminaremos <span class='fw-token-connector'>em</span> <span class='fw-token-c'>duas semanas</span>.",
                        "translation": "We will finish in two weeks.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O curso <span class='fw-token-v'>começa</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>setembro</span>.",
                        "translation": "The course starts in September.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Eles voltam <span class='fw-token-connector'>em</span> <span class='fw-token-c'>poucos dias</span>.",
                        "translation": "They return in a few days.",
                        "source": "Contemporary dialogue"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Spatial Location",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Place</span>",
                "rule": "Spatial location: anchors an action or state to an enclosed place, city, or space.",
                "allowed_lemmas": [
                    "morar",
                    "viver",
                    "entrar",
                    "ficar",
                    "estar",
                    "trabalhar"
                ],
                "targetHTML": "<span class='fw-token-v'>Moro</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>Lisboa</span>.",
                "translation": "I live in Lisbon.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Moro</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>Lisboa</span>.",
                        "translation": "I live in Lisbon.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Eles <span class='fw-token-v'>ficaram</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>casa</span> hoje.",
                        "translation": "They stayed at home today.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Trabalho</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>um hospital</span>.",
                        "translation": "I work in a hospital.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Nós <span class='fw-token-v'>entramos</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>uma sala ampla</span>.",
                        "translation": "We entered a large room.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O café <span class='fw-token-v'>fica</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>frente à estação</span>.",
                        "translation": "The cafe is in front of the station.",
                        "source": "Contemporary speech"
                    }
                ]
            },
            {
                "tag": "Temporal Framing",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Time Period</span>",
                "rule": "Temporal framing: situates an event within a month, year, or duration.",
                "allowed_lemmas": [
                    "viajar",
                    "nascer",
                    "terminar",
                    "voltar",
                    "chegar",
                    "começar"
                ],
                "targetHTML": "<span class='fw-token-v'>Viajo</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>maio</span>.",
                "translation": "I travel in May.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Viajo</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>maio</span>.",
                        "translation": "I travel in May.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>nasceu</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>1995</span>.",
                        "translation": "She was born in 1995.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Terminaremos <span class='fw-token-connector'>em</span> <span class='fw-token-c'>duas semanas</span>.",
                        "translation": "We will finish in two weeks.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O curso <span class='fw-token-v'>começa</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>setembro</span>.",
                        "translation": "The course starts in September.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Eles voltam <span class='fw-token-connector'>em</span> <span class='fw-token-c'>poucos dias</span>.",
                        "translation": "They return in a few days.",
                        "source": "Contemporary dialogue"
                    }
                ]
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
                "tag": "Destination",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Destination</span>",
                "rule": "Direction and destination: points toward a final physical goal or place of arrival.",
                "allowed_lemmas": [
                    "ir",
                    "viajar",
                    "voltar",
                    "caminhar",
                    "partir",
                    "olhar"
                ],
                "targetHTML": "<span class='fw-token-v'>Vou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>casa</span>.",
                "translation": "I am going home.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Vou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>casa</span>.",
                        "translation": "I am going home.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Eles <span class='fw-token-v'>viajam</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o Brasil</span>.",
                        "translation": "They travel to Brazil.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>olhou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o céu</span>.",
                        "translation": "She looked toward the sky.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Vamos <span class='fw-token-v'>voltar</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o hotel</span>.",
                        "translation": "We are returning to the hotel.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O comboio <span class='fw-token-v'>parte</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o Porto</span>.",
                        "translation": "The train departs for Porto.",
                        "source": "Contemporary speech"
                    }
                ]
            },
            {
                "tag": "Purpose",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Goal</span>",
                "rule": "Purpose and objective: links an intentional action to what it aims to achieve.",
                "allowed_lemmas": [
                    "estudar",
                    "trabalhar",
                    "sair",
                    "parar",
                    "correr",
                    "ligar"
                ],
                "targetHTML": "<span class='fw-token-v'>Estudo</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                "translation": "I study in order to learn.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Estudo</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                        "translation": "I study in order to learn.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Trabalho <span class='fw-token-connector'>para</span> <span class='fw-token-c'>sustentar minha família</span>.",
                        "translation": "I work in order to support my family.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ligou <span class='fw-token-connector'>para</span> <span class='fw-token-c'>saber notícias</span>.",
                        "translation": "Called in order to get news.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Paramos <span class='fw-token-connector'>para</span> <span class='fw-token-c'>descansar um pouco</span>.",
                        "translation": "We stopped in order to rest a bit.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Correu <span class='fw-token-connector'>para</span> <span class='fw-token-c'>não perder o autocarro</span>.",
                        "translation": "Ran in order not to miss the bus.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Recipient",
                "formulaHTML": "<span class=\"fw-token-v\">Object</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                "rule": "Beneficiary: marks who receives or benefits from something.",
                "allowed_lemmas": [
                    "presente",
                    "carta",
                    "comida",
                    "mensagem",
                    "dinheiro",
                    "espaço"
                ],
                "targetHTML": "Isto é <span class='fw-token-v'>um presente</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>você</span>.",
                "translation": "This is a gift for you.",
                "examples": [
                    {
                        "targetHTML": "Isto é <span class='fw-token-v'>um presente</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>você</span>.",
                        "translation": "This is a gift for you.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Escrevi <span class='fw-token-v'>uma carta</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>meus pais</span>.",
                        "translation": "I wrote a letter to my parents.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Cozinhei <span class='fw-token-v'>jantar</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>todos nós</span>.",
                        "translation": "I cooked dinner for all of us.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Há lugar <span class='fw-token-connector'>para</span> <span class='fw-token-c'>mais uma pessoa</span>?",
                        "translation": "Is there room for one more person?",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Deixei <span class='fw-token-v'>um bilhete</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ela</span>.",
                        "translation": "I left a note for her.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Destination",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Destination</span>",
                "rule": "Direction and destination: points toward a final physical goal or place of arrival.",
                "allowed_lemmas": [
                    "ir",
                    "viajar",
                    "voltar",
                    "caminhar",
                    "partir",
                    "olhar"
                ],
                "targetHTML": "<span class='fw-token-v'>Vou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>casa</span>.",
                "translation": "I am going home.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Vou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>casa</span>.",
                        "translation": "I am going home.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Eles <span class='fw-token-v'>viajam</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o Brasil</span>.",
                        "translation": "They travel to Brazil.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>olhou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o céu</span>.",
                        "translation": "She looked toward the sky.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Vamos <span class='fw-token-v'>voltar</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o hotel</span>.",
                        "translation": "We are returning to the hotel.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O comboio <span class='fw-token-v'>parte</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o Porto</span>.",
                        "translation": "The train departs for Porto.",
                        "source": "Contemporary speech"
                    }
                ]
            },
            {
                "tag": "Purpose",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Goal</span>",
                "rule": "Purpose and objective: links an intentional action to what it aims to achieve.",
                "allowed_lemmas": [
                    "estudar",
                    "trabalhar",
                    "sair",
                    "parar",
                    "correr",
                    "ligar"
                ],
                "targetHTML": "<span class='fw-token-v'>Estudo</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                "translation": "I study in order to learn.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Estudo</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                        "translation": "I study in order to learn.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Trabalho <span class='fw-token-connector'>para</span> <span class='fw-token-c'>sustentar minha família</span>.",
                        "translation": "I work in order to support my family.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ligou <span class='fw-token-connector'>para</span> <span class='fw-token-c'>saber notícias</span>.",
                        "translation": "Called in order to get news.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Paramos <span class='fw-token-connector'>para</span> <span class='fw-token-c'>descansar um pouco</span>.",
                        "translation": "We stopped in order to rest a bit.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Correu <span class='fw-token-connector'>para</span> <span class='fw-token-c'>não perder o autocarro</span>.",
                        "translation": "Ran in order not to miss the bus.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Recipient",
                "formulaHTML": "<span class=\"fw-token-v\">Object</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                "rule": "Beneficiary: marks who receives or benefits from something.",
                "allowed_lemmas": [
                    "presente",
                    "carta",
                    "comida",
                    "mensagem",
                    "dinheiro",
                    "espaço"
                ],
                "targetHTML": "Isto é <span class='fw-token-v'>um presente</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>você</span>.",
                "translation": "This is a gift for you.",
                "examples": [
                    {
                        "targetHTML": "Isto é <span class='fw-token-v'>um presente</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>você</span>.",
                        "translation": "This is a gift for you.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Escrevi <span class='fw-token-v'>uma carta</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>meus pais</span>.",
                        "translation": "I wrote a letter to my parents.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Cozinhei <span class='fw-token-v'>jantar</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>todos nós</span>.",
                        "translation": "I cooked dinner for all of us.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Há lugar <span class='fw-token-connector'>para</span> <span class='fw-token-c'>mais uma pessoa</span>?",
                        "translation": "Is there room for one more person?",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Deixei <span class='fw-token-v'>um bilhete</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ela</span>.",
                        "translation": "I left a note for her.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Accompaniment",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Companion</span>",
                "rule": "Accompaniment: joins an action to the person or entity sharing it.",
                "allowed_lemmas": [
                    "falar",
                    "sair",
                    "viajar",
                    "almoçar",
                    "viver",
                    "trabalhar"
                ],
                "targetHTML": "<span class='fw-token-v'>Falo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>você</span> amanhã.",
                "translation": "I speak with you tomorrow.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Falo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>você</span> amanhã.",
                        "translation": "I speak with you tomorrow.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Fui ao cinema <span class='fw-token-connector'>com</span> <span class='fw-token-c'>meus amigos</span>.",
                        "translation": "I went to the cinema with my friends.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>mora</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>a irmã</span>.",
                        "translation": "She lives with her sister.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Quero <span class='fw-token-v'>conversar</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>o gerente</span>.",
                        "translation": "I want to speak with the manager.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Nós <span class='fw-token-v'>trabalhamos</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>profissionais excelentes</span>.",
                        "translation": "We work with excellent professionals.",
                        "source": "Contemporary speech"
                    }
                ]
            },
            {
                "tag": "Instrument and Manner",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                "rule": "Instrument and manner: describes the means used or attitude applied.",
                "allowed_lemmas": [
                    "escrever",
                    "cortar",
                    "fazer",
                    "ouvir",
                    "olhar",
                    "tratar"
                ],
                "targetHTML": "<span class='fw-token-v'>Escrevo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>cuidado</span>.",
                "translation": "I write with care.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Escrevo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>cuidado</span>.",
                        "translation": "I write with care.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ele abriu a porta <span class='fw-token-connector'>com</span> <span class='fw-token-c'>a chave reserva</span>.",
                        "translation": "He opened the door with the spare key.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ouvimos tudo <span class='fw-token-connector'>com</span> <span class='fw-token-c'>muita atenção</span>.",
                        "translation": "We listened to everything with great attention.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Cortei o papel <span class='fw-token-connector'>com</span> <span class='fw-token-c'>uma tesoura</span>.",
                        "translation": "I cut the paper with scissors.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Tratou os convidados <span class='fw-token-connector'>com</span> <span class='fw-token-c'>extrema simpatia</span>.",
                        "translation": "Treated the guests with extreme warmth.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Accompaniment",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Companion</span>",
                "rule": "Accompaniment: joins an action to the person or entity sharing it.",
                "allowed_lemmas": [
                    "falar",
                    "sair",
                    "viajar",
                    "almoçar",
                    "viver",
                    "trabalhar"
                ],
                "targetHTML": "<span class='fw-token-v'>Falo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>você</span> amanhã.",
                "translation": "I speak with you tomorrow.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Falo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>você</span> amanhã.",
                        "translation": "I speak with you tomorrow.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Fui ao cinema <span class='fw-token-connector'>com</span> <span class='fw-token-c'>meus amigos</span>.",
                        "translation": "I went to the cinema with my friends.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>mora</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>a irmã</span>.",
                        "translation": "She lives with her sister.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Quero <span class='fw-token-v'>conversar</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>o gerente</span>.",
                        "translation": "I want to speak with the manager.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Nós <span class='fw-token-v'>trabalhamos</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>profissionais excelentes</span>.",
                        "translation": "We work with excellent professionals.",
                        "source": "Contemporary speech"
                    }
                ]
            },
            {
                "tag": "Instrument and Manner",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                "rule": "Instrument and manner: describes the means used or attitude applied.",
                "allowed_lemmas": [
                    "escrever",
                    "cortar",
                    "fazer",
                    "ouvir",
                    "olhar",
                    "tratar"
                ],
                "targetHTML": "<span class='fw-token-v'>Escrevo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>cuidado</span>.",
                "translation": "I write with care.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Escrevo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>cuidado</span>.",
                        "translation": "I write with care.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ele abriu a porta <span class='fw-token-connector'>com</span> <span class='fw-token-c'>a chave reserva</span>.",
                        "translation": "He opened the door with the spare key.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ouvimos tudo <span class='fw-token-connector'>com</span> <span class='fw-token-c'>muita atenção</span>.",
                        "translation": "We listened to everything with great attention.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Cortei o papel <span class='fw-token-connector'>com</span> <span class='fw-token-c'>uma tesoura</span>.",
                        "translation": "I cut the paper with scissors.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Tratou os convidados <span class='fw-token-connector'>com</span> <span class='fw-token-c'>extrema simpatia</span>.",
                        "translation": "Treated the guests with extreme warmth.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Cause / Motive",
                "formulaHTML": "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                "rule": "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                "allowed_lemmas": [
                    "obrigado",
                    "esperar",
                    "lutar",
                    "chorar",
                    "pagar",
                    "agradecer"
                ],
                "targetHTML": "<span class='fw-token-v'>Obrigado</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>ajudar</span>.",
                "translation": "Thank you for helping.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Obrigado</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>ajudar</span>.",
                        "translation": "Thank you for helping.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Espero <span class='fw-token-connector'>por</span> <span class='fw-token-c'>notícias suas</span>.",
                        "translation": "I wait for news from you.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ele foi elogiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>sua coragem</span>.",
                        "translation": "He was praised for his courage.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Pagou vinte euros <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aquele livro</span>.",
                        "translation": "Paid twenty euros for that book.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Agradeço <span class='fw-token-connector'>por</span> <span class='fw-token-c'>toda a paciência</span>.",
                        "translation": "I thank you for all the patience.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Trajectory",
                "formulaHTML": "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                "rule": "Trajectory: marks the path, medium, or space through which motion occurs.",
                "allowed_lemmas": [
                    "caminhar",
                    "passar",
                    "andar",
                    "viajar",
                    "olhar",
                    "entrar"
                ],
                "targetHTML": "<span class='fw-token-v'>Caminho</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aqui</span>.",
                "translation": "I walk around here.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Caminho</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aqui</span>.",
                        "translation": "I walk around here.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Passamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>uma ponte antiga</span>.",
                        "translation": "We passed through an old bridge.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Olhou <span class='fw-token-connector'>por</span> <span class='fw-token-c'>entre as grades</span>.",
                        "translation": "Looked through between the railings.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "O gato entrou <span class='fw-token-connector'>por</span> <span class='fw-token-c'>uma brecha na janela</span>.",
                        "translation": "The cat entered through a gap in the window.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Viajamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>estradas desertas</span>.",
                        "translation": "We traveled through deserted roads.",
                        "source": "Contemporary speech"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Cause / Motive",
                "formulaHTML": "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                "rule": "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                "allowed_lemmas": [
                    "obrigado",
                    "esperar",
                    "lutar",
                    "chorar",
                    "pagar",
                    "agradecer"
                ],
                "targetHTML": "<span class='fw-token-v'>Obrigado</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>ajudar</span>.",
                "translation": "Thank you for helping.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Obrigado</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>ajudar</span>.",
                        "translation": "Thank you for helping.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Espero <span class='fw-token-connector'>por</span> <span class='fw-token-c'>notícias suas</span>.",
                        "translation": "I wait for news from you.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ele foi elogiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>sua coragem</span>.",
                        "translation": "He was praised for his courage.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Pagou vinte euros <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aquele livro</span>.",
                        "translation": "Paid twenty euros for that book.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Agradeço <span class='fw-token-connector'>por</span> <span class='fw-token-c'>toda a paciência</span>.",
                        "translation": "I thank you for all the patience.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Trajectory",
                "formulaHTML": "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                "rule": "Trajectory: marks the path, medium, or space through which motion occurs.",
                "allowed_lemmas": [
                    "caminhar",
                    "passar",
                    "andar",
                    "viajar",
                    "olhar",
                    "entrar"
                ],
                "targetHTML": "<span class='fw-token-v'>Caminho</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aqui</span>.",
                "translation": "I walk around here.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Caminho</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aqui</span>.",
                        "translation": "I walk around here.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Passamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>uma ponte antiga</span>.",
                        "translation": "We passed through an old bridge.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Olhou <span class='fw-token-connector'>por</span> <span class='fw-token-c'>entre as grades</span>.",
                        "translation": "Looked through between the railings.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "O gato entrou <span class='fw-token-connector'>por</span> <span class='fw-token-c'>uma brecha na janela</span>.",
                        "translation": "The cat entered through a gap in the window.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Viajamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>estradas desertas</span>.",
                        "translation": "We traveled through deserted roads.",
                        "source": "Contemporary speech"
                    }
                ]
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
                "tag": "Spatial / Temporal Location",
                "formulaHTML": "<span class=\"fw-token-connector\">em + o</span> + <span class=\"fw-token-c\">Masculine Noun / Place</span>",
                "rule": "Contraction of 'em + o' (in the / at the) before a specific masculine noun.",
                "allowed_lemmas": [
                    "quarto",
                    "trabalho",
                    "carro",
                    "mundo",
                    "cinema",
                    "hospital"
                ],
                "targetHTML": "O livro está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>quarto</span>.",
                "translation": "The book is in the room.",
                "examples": [
                    {
                        "targetHTML": "O livro está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>quarto</span>.",
                        "translation": "The book is in the room.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ele ainda está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>trabalho</span>.",
                        "translation": "He is still at work.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Nos encontramos <span class='fw-token-connector'>no</span> <span class='fw-token-c'>cinema às oito</span>.",
                        "translation": "We met at the cinema at eight.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Não há ninguém como ele <span class='fw-token-connector'>no</span> <span class='fw-token-c'>mundo</span>.",
                        "translation": "There is no one like him in the world.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Esqueci a carteira <span class='fw-token-connector'>no</span> <span class='fw-token-c'>carro</span>.",
                        "translation": "I forgot my wallet in the car.",
                        "source": "Dialogue"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Spatial / Temporal Location",
                "formulaHTML": "<span class=\"fw-token-connector\">em + o</span> + <span class=\"fw-token-c\">Masculine Noun / Place</span>",
                "rule": "Contraction of 'em + o' (in the / at the) before a specific masculine noun.",
                "allowed_lemmas": [
                    "quarto",
                    "trabalho",
                    "carro",
                    "mundo",
                    "cinema",
                    "hospital"
                ],
                "targetHTML": "O livro está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>quarto</span>.",
                "translation": "The book is in the room.",
                "examples": [
                    {
                        "targetHTML": "O livro está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>quarto</span>.",
                        "translation": "The book is in the room.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ele ainda está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>trabalho</span>.",
                        "translation": "He is still at work.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Nos encontramos <span class='fw-token-connector'>no</span> <span class='fw-token-c'>cinema às oito</span>.",
                        "translation": "We met at the cinema at eight.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Não há ninguém como ele <span class='fw-token-connector'>no</span> <span class='fw-token-c'>mundo</span>.",
                        "translation": "There is no one like him in the world.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Esqueci a carteira <span class='fw-token-connector'>no</span> <span class='fw-token-c'>carro</span>.",
                        "translation": "I forgot my wallet in the car.",
                        "source": "Dialogue"
                    }
                ]
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
                "tag": "Spatial / Temporal Location",
                "formulaHTML": "<span class=\"fw-token-connector\">em + a</span> + <span class=\"fw-token-c\">Feminine Noun / Place</span>",
                "rule": "Contraction of 'em + a' (in the / at the) before a specific feminine noun.",
                "allowed_lemmas": [
                    "praia",
                    "mesa",
                    "rua",
                    "cidade",
                    "escola",
                    "cozinha"
                ],
                "targetHTML": "Ela está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>praia</span>.",
                "translation": "She is at the beach.",
                "examples": [
                    {
                        "targetHTML": "Ela está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>praia</span>.",
                        "translation": "She is at the beach.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "A carta está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>mesa da sala</span>.",
                        "translation": "The letter is on the living room table.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Vi muitas pessoas <span class='fw-token-connector'>na</span> <span class='fw-token-c'>rua principal</span>.",
                        "translation": "I saw many people on the main street.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "As crianças estão <span class='fw-token-connector'>na</span> <span class='fw-token-c'>escola agora</span>.",
                        "translation": "The children are at school now.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ela cozinha <span class='fw-token-connector'>na</span> <span class='fw-token-c'>cozinha espaçosa</span>.",
                        "translation": "She cooks in the spacious kitchen.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Spatial / Temporal Location",
                "formulaHTML": "<span class=\"fw-token-connector\">em + a</span> + <span class=\"fw-token-c\">Feminine Noun / Place</span>",
                "rule": "Contraction of 'em + a' (in the / at the) before a specific feminine noun.",
                "allowed_lemmas": [
                    "praia",
                    "mesa",
                    "rua",
                    "cidade",
                    "escola",
                    "cozinha"
                ],
                "targetHTML": "Ela está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>praia</span>.",
                "translation": "She is at the beach.",
                "examples": [
                    {
                        "targetHTML": "Ela está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>praia</span>.",
                        "translation": "She is at the beach.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "A carta está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>mesa da sala</span>.",
                        "translation": "The letter is on the living room table.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Vi muitas pessoas <span class='fw-token-connector'>na</span> <span class='fw-token-c'>rua principal</span>.",
                        "translation": "I saw many people on the main street.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "As crianças estão <span class='fw-token-connector'>na</span> <span class='fw-token-c'>escola agora</span>.",
                        "translation": "The children are at school now.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ela cozinha <span class='fw-token-connector'>na</span> <span class='fw-token-c'>cozinha espaçosa</span>.",
                        "translation": "She cooks in the spacious kitchen.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Possession / Origin",
                "formulaHTML": "<span class=\"fw-token-connector\">de + o</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                "rule": "Contraction of 'de + o' (of the / from the) denoting possession, origin, or attribute.",
                "allowed_lemmas": [
                    "pai",
                    "hotel",
                    "filme",
                    "livro",
                    "Brasil",
                    "governo"
                ],
                "targetHTML": "Este é o carro <span class='fw-token-connector'>do</span> <span class='fw-token-c'>meu pai</span>.",
                "translation": "This is my father's car.",
                "examples": [
                    {
                        "targetHTML": "Este é o carro <span class='fw-token-connector'>do</span> <span class='fw-token-c'>meu pai</span>.",
                        "translation": "This is my father's car.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "A porta <span class='fw-token-connector'>do</span> <span class='fw-token-c'>hotel</span> estava fechada.",
                        "translation": "The hotel door was closed.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Gostei muito <span class='fw-token-connector'>do</span> <span class='fw-token-c'>final do filme</span>.",
                        "translation": "I liked the end of the movie a lot.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ele veio direto <span class='fw-token-connector'>do</span> <span class='fw-token-c'>aeroporto</span>.",
                        "translation": "He came straight from the airport.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "A decisão <span class='fw-token-connector'>do</span> <span class='fw-token-c'>juiz foi definitiva</span>.",
                        "translation": "The judge's decision was final.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Possession / Origin",
                "formulaHTML": "<span class=\"fw-token-connector\">de + o</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                "rule": "Contraction of 'de + o' (of the / from the) denoting possession, origin, or attribute.",
                "allowed_lemmas": [
                    "pai",
                    "hotel",
                    "filme",
                    "livro",
                    "Brasil",
                    "governo"
                ],
                "targetHTML": "Este é o carro <span class='fw-token-connector'>do</span> <span class='fw-token-c'>meu pai</span>.",
                "translation": "This is my father's car.",
                "examples": [
                    {
                        "targetHTML": "Este é o carro <span class='fw-token-connector'>do</span> <span class='fw-token-c'>meu pai</span>.",
                        "translation": "This is my father's car.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "A porta <span class='fw-token-connector'>do</span> <span class='fw-token-c'>hotel</span> estava fechada.",
                        "translation": "The hotel door was closed.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Gostei muito <span class='fw-token-connector'>do</span> <span class='fw-token-c'>final do filme</span>.",
                        "translation": "I liked the end of the movie a lot.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ele veio direto <span class='fw-token-connector'>do</span> <span class='fw-token-c'>aeroporto</span>.",
                        "translation": "He came straight from the airport.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "A decisão <span class='fw-token-connector'>do</span> <span class='fw-token-c'>juiz foi definitiva</span>.",
                        "translation": "The judge's decision was final.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Possession / Origin",
                "formulaHTML": "<span class=\"fw-token-connector\">de + a</span> + <span class=\"fw-token-c\">Feminine Noun / Origin</span>",
                "rule": "Contraction of 'de + a' (of the / from the) denoting possession, origin, or attribute.",
                "allowed_lemmas": [
                    "casa",
                    "mãe",
                    "cidade",
                    "vida",
                    "janela",
                    "música"
                ],
                "targetHTML": "Esta é a chave <span class='fw-token-connector'>da</span> <span class='fw-token-c'>casa</span>.",
                "translation": "This is the key to the house.",
                "examples": [
                    {
                        "targetHTML": "Esta é a chave <span class='fw-token-connector'>da</span> <span class='fw-token-c'>casa</span>.",
                        "translation": "This is the key to the house.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O sorriso <span class='fw-token-connector'>da</span> <span class='fw-token-c'>mãe acalmou a todos</span>.",
                        "translation": "The mother's smile calmed everyone.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "A vista <span class='fw-token-connector'>da</span> <span class='fw-token-c'>janela é deslumbrante</span>.",
                        "translation": "The view from the window is breathtaking.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Conhecemos os cantos <span class='fw-token-connector'>da</span> <span class='fw-token-c'>cidade antiga</span>.",
                        "translation": "We know the corners of the old city.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O ritmo <span class='fw-token-connector'>da</span> <span class='fw-token-c'>música empolgou a sala</span>.",
                        "translation": "The rhythm of the music excited the room.",
                        "source": "Everyday speech"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Possession / Origin",
                "formulaHTML": "<span class=\"fw-token-connector\">de + a</span> + <span class=\"fw-token-c\">Feminine Noun / Origin</span>",
                "rule": "Contraction of 'de + a' (of the / from the) denoting possession, origin, or attribute.",
                "allowed_lemmas": [
                    "casa",
                    "mãe",
                    "cidade",
                    "vida",
                    "janela",
                    "música"
                ],
                "targetHTML": "Esta é a chave <span class='fw-token-connector'>da</span> <span class='fw-token-c'>casa</span>.",
                "translation": "This is the key to the house.",
                "examples": [
                    {
                        "targetHTML": "Esta é a chave <span class='fw-token-connector'>da</span> <span class='fw-token-c'>casa</span>.",
                        "translation": "This is the key to the house.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O sorriso <span class='fw-token-connector'>da</span> <span class='fw-token-c'>mãe acalmou a todos</span>.",
                        "translation": "The mother's smile calmed everyone.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "A vista <span class='fw-token-connector'>da</span> <span class='fw-token-c'>janela é deslumbrante</span>.",
                        "translation": "The view from the window is breathtaking.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Conhecemos os cantos <span class='fw-token-connector'>da</span> <span class='fw-token-c'>cidade antiga</span>.",
                        "translation": "We know the corners of the old city.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O ritmo <span class='fw-token-connector'>da</span> <span class='fw-token-c'>música empolgou a sala</span>.",
                        "translation": "The rhythm of the music excited the room.",
                        "source": "Everyday speech"
                    }
                ]
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
                "tag": "Manner / Simile",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Model / Standard</span>",
                "rule": "Simile and manner: compares the style or way an action is performed to an archetype.",
                "allowed_lemmas": [
                    "cantar",
                    "agir",
                    "falar",
                    "brilhar",
                    "correr",
                    "tratar"
                ],
                "targetHTML": "Ela <span class='fw-token-v'>canta</span> <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um pássaro</span>.",
                "translation": "She sings like a bird.",
                "examples": [
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>canta</span> <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um pássaro</span>.",
                        "translation": "She sings like a bird.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ele agiu <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um verdadeiro herói</span>.",
                        "translation": "He acted like a true hero.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Seus olhos brilham <span class='fw-token-connector'>como</span> <span class='fw-token-c'>estrelas</span>.",
                        "translation": "Her eyes shine like stars.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Faz as coisas <span class='fw-token-connector'>como</span> <span class='fw-token-c'>sempre fez</span>.",
                        "translation": "Does things like he always did.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Correu rápido <span class='fw-token-connector'>como</span> <span class='fw-token-c'>o vento</span>.",
                        "translation": "Ran fast like the wind.",
                        "source": "Dialogue"
                    }
                ]
            },
            {
                "tag": "Capacity / Role",
                "formulaHTML": "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Role / Capacity</span>",
                "rule": "Capacity and function: specifies the role, profession, or capacity someone acts in.",
                "allowed_lemmas": [
                    "engenheiro",
                    "médico",
                    "professor",
                    "voluntário",
                    "testemunha"
                ],
                "targetHTML": "Trabalho <span class='fw-token-connector'>como</span> <span class='fw-token-c'>engenheiro</span>.",
                "translation": "I work as an engineer.",
                "examples": [
                    {
                        "targetHTML": "Trabalho <span class='fw-token-connector'>como</span> <span class='fw-token-c'>engenheiro</span>.",
                        "translation": "I work as an engineer.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ele atuou <span class='fw-token-connector'>como</span> <span class='fw-token-c'>porta-voz do grupo</span>.",
                        "translation": "He acted as spokesperson for the group.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ela participou <span class='fw-token-connector'>como</span> <span class='fw-token-c'>voluntária no projeto</span>.",
                        "translation": "She took part as a volunteer in the project.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Falo <span class='fw-token-connector'>como</span> <span class='fw-token-c'>amigo preocupado</span>.",
                        "translation": "I speak as a concerned friend.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Foi chamado <span class='fw-token-connector'>como</span> <span class='fw-token-c'>testemunha principal</span>.",
                        "translation": "Was called as chief witness.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Manner / Simile",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Model / Standard</span>",
                "rule": "Simile and manner: compares the style or way an action is performed to an archetype.",
                "allowed_lemmas": [
                    "cantar",
                    "agir",
                    "falar",
                    "brilhar",
                    "correr",
                    "tratar"
                ],
                "targetHTML": "Ela <span class='fw-token-v'>canta</span> <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um pássaro</span>.",
                "translation": "She sings like a bird.",
                "examples": [
                    {
                        "targetHTML": "Ela <span class='fw-token-v'>canta</span> <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um pássaro</span>.",
                        "translation": "She sings like a bird.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ele agiu <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um verdadeiro herói</span>.",
                        "translation": "He acted like a true hero.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Seus olhos brilham <span class='fw-token-connector'>como</span> <span class='fw-token-c'>estrelas</span>.",
                        "translation": "Her eyes shine like stars.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Faz as coisas <span class='fw-token-connector'>como</span> <span class='fw-token-c'>sempre fez</span>.",
                        "translation": "Does things like he always did.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Correu rápido <span class='fw-token-connector'>como</span> <span class='fw-token-c'>o vento</span>.",
                        "translation": "Ran fast like the wind.",
                        "source": "Dialogue"
                    }
                ]
            },
            {
                "tag": "Capacity / Role",
                "formulaHTML": "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Role / Capacity</span>",
                "rule": "Capacity and function: specifies the role, profession, or capacity someone acts in.",
                "allowed_lemmas": [
                    "engenheiro",
                    "médico",
                    "professor",
                    "voluntário",
                    "testemunha"
                ],
                "targetHTML": "Trabalho <span class='fw-token-connector'>como</span> <span class='fw-token-c'>engenheiro</span>.",
                "translation": "I work as an engineer.",
                "examples": [
                    {
                        "targetHTML": "Trabalho <span class='fw-token-connector'>como</span> <span class='fw-token-c'>engenheiro</span>.",
                        "translation": "I work as an engineer.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ele atuou <span class='fw-token-connector'>como</span> <span class='fw-token-c'>porta-voz do grupo</span>.",
                        "translation": "He acted as spokesperson for the group.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ela participou <span class='fw-token-connector'>como</span> <span class='fw-token-c'>voluntária no projeto</span>.",
                        "translation": "She took part as a volunteer in the project.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Falo <span class='fw-token-connector'>como</span> <span class='fw-token-c'>amigo preocupado</span>.",
                        "translation": "I speak as a concerned friend.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Foi chamado <span class='fw-token-connector'>como</span> <span class='fw-token-c'>testemunha principal</span>.",
                        "translation": "Was called as chief witness.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Contrast",
                "formulaHTML": "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">mas</span> + <span class=\"fw-token-c\">Counterpoint</span>",
                "rule": "Adversative bridge: introduces a contrast, restriction, or unexpected limitation.",
                "allowed_lemmas": [
                    "tentar",
                    "querer",
                    "procurar",
                    "saber",
                    "chamar"
                ],
                "targetHTML": "<span class='fw-token-v'>Tentei</span>, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>não consegui</span>.",
                "translation": "I tried, but I could not.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Tentei</span>, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>não consegui</span>.",
                        "translation": "I tried, but I could not.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Queria sair, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>estava a chover forte</span>.",
                        "translation": "I wanted to go out, but it was raining hard.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ele sabia a resposta, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>ficou calado</span>.",
                        "translation": "He knew the answer, but stayed silent.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Procurei por todo o lado, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>nada encontrei</span>.",
                        "translation": "I searched everywhere, but found nothing.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "O plano era bom, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>faltou tempo</span>.",
                        "translation": "The plan was good, but time ran short.",
                        "source": "Everyday speech"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Contrast",
                "formulaHTML": "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">mas</span> + <span class=\"fw-token-c\">Counterpoint</span>",
                "rule": "Adversative bridge: introduces a contrast, restriction, or unexpected limitation.",
                "allowed_lemmas": [
                    "tentar",
                    "querer",
                    "procurar",
                    "saber",
                    "chamar"
                ],
                "targetHTML": "<span class='fw-token-v'>Tentei</span>, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>não consegui</span>.",
                "translation": "I tried, but I could not.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Tentei</span>, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>não consegui</span>.",
                        "translation": "I tried, but I could not.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Queria sair, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>estava a chover forte</span>.",
                        "translation": "I wanted to go out, but it was raining hard.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ele sabia a resposta, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>ficou calado</span>.",
                        "translation": "He knew the answer, but stayed silent.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Procurei por todo o lado, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>nada encontrei</span>.",
                        "translation": "I searched everywhere, but found nothing.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "O plano era bom, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>faltou tempo</span>.",
                        "translation": "The plan was good, but time ran short.",
                        "source": "Everyday speech"
                    }
                ]
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
                "tag": "Directional Link",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Destination</span>",
                "rule": "Directional link: points to a target destination or recipient.",
                "allowed_lemmas": [
                    "ir",
                    "chegar",
                    "voltar",
                    "escrever",
                    "entregar",
                    "levar"
                ],
                "targetHTML": "Vou <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Lisboa</span> amanhã.",
                "translation": "I go to Lisbon tomorrow.",
                "examples": [
                    {
                        "targetHTML": "Vou <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Lisboa</span> amanhã.",
                        "translation": "I go to Lisbon tomorrow.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Chegamos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>casa são e salvos</span>.",
                        "translation": "We arrived home safe and sound.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Entregou o documento <span class='fw-token-connector'>a</span> <span class='fw-token-c'>ele</span>.",
                        "translation": "Delivered the document to him.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Escreveu uma nota <span class='fw-token-connector'>a</span> <span class='fw-token-c'>um amigo</span>.",
                        "translation": "Wrote a note to a friend.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Eles voltaram <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Porto Alegre</span>.",
                        "translation": "They returned to Porto Alegre.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                "rule": "Definite feminine article: specifies a singular feminine entity.",
                "allowed_lemmas": [
                    "casa",
                    "porta",
                    "cidade",
                    "noite",
                    "vida",
                    "viagem"
                ],
                "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>casa</span> é bonita.",
                "translation": "The house is pretty.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>casa</span> é bonita.",
                        "translation": "The house is pretty.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>porta</span> principal estava trancada.",
                        "translation": "The main door was locked.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>cidade</span> acorda cedo.",
                        "translation": "The city wakes up early.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>noite</span> estava fresca e calma.",
                        "translation": "The night was cool and quiet.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>viagem</span> correu muito bem.",
                        "translation": "The trip went very well.",
                        "source": "Conversation"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span>",
                "rule": "Direct object pronoun: replaces a singular 3rd-person feminine noun ('her / it').",
                "allowed_lemmas": [
                    "conhecer",
                    "ver",
                    "ouvir",
                    "ajudar",
                    "chamar"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>conheço</span> bem.",
                "translation": "I know her well.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>conheço</span> bem.",
                        "translation": "I know her well.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>vi</span> ontem à tarde.",
                        "translation": "I saw her yesterday afternoon.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Todos <span class='fw-token-connector'>a</span> <span class='fw-token-v'>respeitam</span> pelo trabalho sério.",
                        "translation": "Everyone respects her for her earnest work.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Nunca mais <span class='fw-token-connector'>a</span> <span class='fw-token-v'>encontrei</span> depois disso.",
                        "translation": "I never met her again after that.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "O médico <span class='fw-token-connector'>a</span> <span class='fw-token-v'>examinou</span> com cuidado.",
                        "translation": "The doctor examined her carefully.",
                        "source": "Everyday speech"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Directional Link",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Destination</span>",
                "rule": "Directional link: points to a target destination or recipient.",
                "allowed_lemmas": [
                    "ir",
                    "chegar",
                    "voltar",
                    "escrever",
                    "entregar",
                    "levar"
                ],
                "targetHTML": "Vou <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Lisboa</span> amanhã.",
                "translation": "I go to Lisbon tomorrow.",
                "examples": [
                    {
                        "targetHTML": "Vou <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Lisboa</span> amanhã.",
                        "translation": "I go to Lisbon tomorrow.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Chegamos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>casa são e salvos</span>.",
                        "translation": "We arrived home safe and sound.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Entregou o documento <span class='fw-token-connector'>a</span> <span class='fw-token-c'>ele</span>.",
                        "translation": "Delivered the document to him.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Escreveu uma nota <span class='fw-token-connector'>a</span> <span class='fw-token-c'>um amigo</span>.",
                        "translation": "Wrote a note to a friend.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Eles voltaram <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Porto Alegre</span>.",
                        "translation": "They returned to Porto Alegre.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                "rule": "Definite feminine article: specifies a singular feminine entity.",
                "allowed_lemmas": [
                    "casa",
                    "porta",
                    "cidade",
                    "noite",
                    "vida",
                    "viagem"
                ],
                "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>casa</span> é bonita.",
                "translation": "The house is pretty.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>casa</span> é bonita.",
                        "translation": "The house is pretty.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>porta</span> principal estava trancada.",
                        "translation": "The main door was locked.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>cidade</span> acorda cedo.",
                        "translation": "The city wakes up early.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>noite</span> estava fresca e calma.",
                        "translation": "The night was cool and quiet.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>A</span> <span class='fw-token-c'>viagem</span> correu muito bem.",
                        "translation": "The trip went very well.",
                        "source": "Conversation"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span>",
                "rule": "Direct object pronoun: replaces a singular 3rd-person feminine noun ('her / it').",
                "allowed_lemmas": [
                    "conhecer",
                    "ver",
                    "ouvir",
                    "ajudar",
                    "chamar"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>conheço</span> bem.",
                "translation": "I know her well.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>conheço</span> bem.",
                        "translation": "I know her well.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>vi</span> ontem à tarde.",
                        "translation": "I saw her yesterday afternoon.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Todos <span class='fw-token-connector'>a</span> <span class='fw-token-v'>respeitam</span> pelo trabalho sério.",
                        "translation": "Everyone respects her for her earnest work.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Nunca mais <span class='fw-token-connector'>a</span> <span class='fw-token-v'>encontrei</span> depois disso.",
                        "translation": "I never met her again after that.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "O médico <span class='fw-token-connector'>a</span> <span class='fw-token-v'>examinou</span> com cuidado.",
                        "translation": "The doctor examined her carefully.",
                        "source": "Everyday speech"
                    }
                ]
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
                "tag": "Addition",
                "formulaHTML": "<span class=\"fw-token-v\">Item / Clause</span> + <span class=\"fw-token-connector\">e</span> + <span class=\"fw-token-c\">Addition</span>",
                "rule": "Copulative coordinator: links equal grammatical items or consecutive actions.",
                "allowed_lemmas": [
                    "pão",
                    "água",
                    "dia",
                    "entrar",
                    "falar",
                    "sorrir"
                ],
                "targetHTML": "Comprei pão <span class='fw-token-connector'>e</span> <span class='fw-token-c'>queijo</span>.",
                "translation": "I bought bread and cheese.",
                "examples": [
                    {
                        "targetHTML": "Comprei pão <span class='fw-token-connector'>e</span> <span class='fw-token-c'>queijo</span>.",
                        "translation": "I bought bread and cheese.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ele levantou-se <span class='fw-token-connector'>e</span> <span class='fw-token-c'>abriu a janela</span>.",
                        "translation": "He stood up and opened the window.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Trabalho de dia <span class='fw-token-connector'>e</span> <span class='fw-token-c'>estudo à noite</span>.",
                        "translation": "I work during the day and study at night.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela sorriu <span class='fw-token-connector'>e</span> <span class='fw-token-c'>agradeceu a ajuda</span>.",
                        "translation": "She smiled and thanked for the help.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Comemos fruta <span class='fw-token-connector'>e</span> <span class='fw-token-c'>bebemos sumo fresco</span>.",
                        "translation": "We ate fruit and drank fresh juice.",
                        "source": "Subtitles"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Addition",
                "formulaHTML": "<span class=\"fw-token-v\">Item / Clause</span> + <span class=\"fw-token-connector\">e</span> + <span class=\"fw-token-c\">Addition</span>",
                "rule": "Copulative coordinator: links equal grammatical items or consecutive actions.",
                "allowed_lemmas": [
                    "pão",
                    "água",
                    "dia",
                    "entrar",
                    "falar",
                    "sorrir"
                ],
                "targetHTML": "Comprei pão <span class='fw-token-connector'>e</span> <span class='fw-token-c'>queijo</span>.",
                "translation": "I bought bread and cheese.",
                "examples": [
                    {
                        "targetHTML": "Comprei pão <span class='fw-token-connector'>e</span> <span class='fw-token-c'>queijo</span>.",
                        "translation": "I bought bread and cheese.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ele levantou-se <span class='fw-token-connector'>e</span> <span class='fw-token-c'>abriu a janela</span>.",
                        "translation": "He stood up and opened the window.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Trabalho de dia <span class='fw-token-connector'>e</span> <span class='fw-token-c'>estudo à noite</span>.",
                        "translation": "I work during the day and study at night.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela sorriu <span class='fw-token-connector'>e</span> <span class='fw-token-c'>agradeceu a ajuda</span>.",
                        "translation": "She smiled and thanked for the help.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Comemos fruta <span class='fw-token-connector'>e</span> <span class='fw-token-c'>bebemos sumo fresco</span>.",
                        "translation": "We ate fruit and drank fresh juice.",
                        "source": "Subtitles"
                    }
                ]
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
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Eu</span> + <span class=\"fw-token-v\">Verb (1st Sing)</span>",
                "rule": "Subject pronoun: emphasizes or clarifies the first-person singular actor.",
                "allowed_lemmas": [
                    "morar",
                    "saber",
                    "querer",
                    "pensar",
                    "estar",
                    "fazer"
                ],
                "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>moro</span> aqui.",
                "translation": "I live here.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>moro</span> aqui.",
                        "translation": "I live here.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>sei</span> exatamente o que fazer.",
                        "translation": "I know exactly what to do.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>quero</span> falar com você.",
                        "translation": "I want to talk with you.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>estou</span> pronto para começar.",
                        "translation": "I am ready to start.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>fiz</span> o melhor que pude.",
                        "translation": "I did the best that I could.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Eu</span> + <span class=\"fw-token-v\">Verb (1st Sing)</span>",
                "rule": "Subject pronoun: emphasizes or clarifies the first-person singular actor.",
                "allowed_lemmas": [
                    "morar",
                    "saber",
                    "querer",
                    "pensar",
                    "estar",
                    "fazer"
                ],
                "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>moro</span> aqui.",
                "translation": "I live here.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>moro</span> aqui.",
                        "translation": "I live here.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>sei</span> exatamente o que fazer.",
                        "translation": "I know exactly what to do.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>quero</span> falar com você.",
                        "translation": "I want to talk with you.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>estou</span> pronto para começar.",
                        "translation": "I am ready to start.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>fiz</span> o melhor que pude.",
                        "translation": "I did the best that I could.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Ele</span> + <span class=\"fw-token-v\">Verb (3rd Sing)</span>",
                "rule": "Subject pronoun: marks a 3rd-person masculine singular actor ('he / it').",
                "allowed_lemmas": [
                    "trabalhar",
                    "chegar",
                    "dizer",
                    "saber",
                    "viver"
                ],
                "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>trabalha</span> muito.",
                "translation": "He works a lot.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>trabalha</span> muito.",
                        "translation": "He works a lot.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>chegou</span> na hora combinada.",
                        "translation": "He arrived at the agreed time.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>sabe</span> o caminho de volta.",
                        "translation": "He knows the way back.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>disse</span> que viria cedo.",
                        "translation": "He said he would come early.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>vive</span> num mundo próprio.",
                        "translation": "He lives in a world of his own.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Prepositional Object",
                "formulaHTML": "<span class=\"fw-token-v\">Preposition</span> + <span class=\"fw-token-connector\">ele</span>",
                "rule": "Prepositional object: follows prepositions like 'com ele' or 'para ele'.",
                "allowed_lemmas": [
                    "com",
                    "para",
                    "sem",
                    "sobre",
                    "por",
                    "até"
                ],
                "targetHTML": "Falei com <span class='fw-token-connector'>ele</span> ontem.",
                "translation": "I spoke with him yesterday.",
                "examples": [
                    {
                        "targetHTML": "Falei com <span class='fw-token-connector'>ele</span> ontem.",
                        "translation": "I spoke with him yesterday.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Isto é para <span class='fw-token-connector'>ele</span>.",
                        "translation": "This is for him.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Não podemos decidir sem <span class='fw-token-connector'>ele</span>.",
                        "translation": "We cannot decide without him.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Todos perguntaram por <span class='fw-token-connector'>ele</span>.",
                        "translation": "Everyone asked for him.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Escreveram uma matéria sobre <span class='fw-token-connector'>ele</span>.",
                        "translation": "They wrote an article about him.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Ele</span> + <span class=\"fw-token-v\">Verb (3rd Sing)</span>",
                "rule": "Subject pronoun: marks a 3rd-person masculine singular actor ('he / it').",
                "allowed_lemmas": [
                    "trabalhar",
                    "chegar",
                    "dizer",
                    "saber",
                    "viver"
                ],
                "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>trabalha</span> muito.",
                "translation": "He works a lot.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>trabalha</span> muito.",
                        "translation": "He works a lot.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>chegou</span> na hora combinada.",
                        "translation": "He arrived at the agreed time.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>sabe</span> o caminho de volta.",
                        "translation": "He knows the way back.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>disse</span> que viria cedo.",
                        "translation": "He said he would come early.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>vive</span> num mundo próprio.",
                        "translation": "He lives in a world of his own.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Prepositional Object",
                "formulaHTML": "<span class=\"fw-token-v\">Preposition</span> + <span class=\"fw-token-connector\">ele</span>",
                "rule": "Prepositional object: follows prepositions like 'com ele' or 'para ele'.",
                "allowed_lemmas": [
                    "com",
                    "para",
                    "sem",
                    "sobre",
                    "por",
                    "até"
                ],
                "targetHTML": "Falei com <span class='fw-token-connector'>ele</span> ontem.",
                "translation": "I spoke with him yesterday.",
                "examples": [
                    {
                        "targetHTML": "Falei com <span class='fw-token-connector'>ele</span> ontem.",
                        "translation": "I spoke with him yesterday.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Isto é para <span class='fw-token-connector'>ele</span>.",
                        "translation": "This is for him.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Não podemos decidir sem <span class='fw-token-connector'>ele</span>.",
                        "translation": "We cannot decide without him.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Todos perguntaram por <span class='fw-token-connector'>ele</span>.",
                        "translation": "Everyone asked for him.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Escreveram uma matéria sobre <span class='fw-token-connector'>ele</span>.",
                        "translation": "They wrote an article about him.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Ela</span> + <span class=\"fw-token-v\">Verb (3rd Sing)</span>",
                "rule": "Subject pronoun: marks a 3rd-person feminine singular actor ('she / it').",
                "allowed_lemmas": [
                    "saber",
                    "falar",
                    "sorrir",
                    "estudar",
                    "voltar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sabe</span> a resposta.",
                "translation": "She knows the answer.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sabe</span> a resposta.",
                        "translation": "She knows the answer.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>fala</span> três línguas fluentemente.",
                        "translation": "She speaks three languages fluently.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sorriu</span> calorosamente para nós.",
                        "translation": "She smiled warmly at us.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>estuda</span> medicina na capital.",
                        "translation": "She studies medicine in the capital.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>voltou</span> de viagem ontem.",
                        "translation": "She returned from her trip yesterday.",
                        "source": "Subtitles"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Ela</span> + <span class=\"fw-token-v\">Verb (3rd Sing)</span>",
                "rule": "Subject pronoun: marks a 3rd-person feminine singular actor ('she / it').",
                "allowed_lemmas": [
                    "saber",
                    "falar",
                    "sorrir",
                    "estudar",
                    "voltar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sabe</span> a resposta.",
                "translation": "She knows the answer.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sabe</span> a resposta.",
                        "translation": "She knows the answer.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>fala</span> três línguas fluentemente.",
                        "translation": "She speaks three languages fluently.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sorriu</span> calorosamente para nós.",
                        "translation": "She smiled warmly at us.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>estuda</span> medicina na capital.",
                        "translation": "She studies medicine in the capital.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>voltou</span> de viagem ontem.",
                        "translation": "She returned from her trip yesterday.",
                        "source": "Subtitles"
                    }
                ]
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
                "tag": "Indefinite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                "rule": "Indefinite article: introduces an unspecific singular masculine noun.",
                "allowed_lemmas": [
                    "irmão",
                    "amigo",
                    "dia",
                    "livro",
                    "café",
                    "lugar"
                ],
                "targetHTML": "Tenho <span class='fw-token-connector'>um</span> <span class='fw-token-c'>irmão</span>.",
                "translation": "I have a brother.",
                "examples": [
                    {
                        "targetHTML": "Tenho <span class='fw-token-connector'>um</span> <span class='fw-token-c'>irmão</span>.",
                        "translation": "I have a brother.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Conheci <span class='fw-token-connector'>um</span> <span class='fw-token-c'>amigo legal</span>.",
                        "translation": "I met a cool friend.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Tomamos <span class='fw-token-connector'>um</span> <span class='fw-token-c'>café juntos</span>.",
                        "translation": "We had a coffee together.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Li <span class='fw-token-connector'>um</span> <span class='fw-token-c'>livro fantástico</span>.",
                        "translation": "I read a fantastic book.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Procuramos <span class='fw-token-connector'>um</span> <span class='fw-token-c'>lugar tranquilo</span>.",
                        "translation": "We looked for a quiet place.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Indefinite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                "rule": "Indefinite article: introduces an unspecific singular masculine noun.",
                "allowed_lemmas": [
                    "irmão",
                    "amigo",
                    "dia",
                    "livro",
                    "café",
                    "lugar"
                ],
                "targetHTML": "Tenho <span class='fw-token-connector'>um</span> <span class='fw-token-c'>irmão</span>.",
                "translation": "I have a brother.",
                "examples": [
                    {
                        "targetHTML": "Tenho <span class='fw-token-connector'>um</span> <span class='fw-token-c'>irmão</span>.",
                        "translation": "I have a brother.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Conheci <span class='fw-token-connector'>um</span> <span class='fw-token-c'>amigo legal</span>.",
                        "translation": "I met a cool friend.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Tomamos <span class='fw-token-connector'>um</span> <span class='fw-token-c'>café juntos</span>.",
                        "translation": "We had a coffee together.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Li <span class='fw-token-connector'>um</span> <span class='fw-token-c'>livro fantástico</span>.",
                        "translation": "I read a fantastic book.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Procuramos <span class='fw-token-connector'>um</span> <span class='fw-token-c'>lugar tranquilo</span>.",
                        "translation": "We looked for a quiet place.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Indefinite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                "rule": "Indefinite article: introduces an unspecific singular feminine noun.",
                "allowed_lemmas": [
                    "fotografia",
                    "ideia",
                    "semana",
                    "casa",
                    "pergunta",
                    "história"
                ],
                "targetHTML": "Vi <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>fotografia</span>.",
                "translation": "I saw a photograph.",
                "examples": [
                    {
                        "targetHTML": "Vi <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>fotografia</span>.",
                        "translation": "I saw a photograph.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela teve <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>ideia brilhante</span>.",
                        "translation": "She had a brilliant idea.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ficarei aqui por <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>semana</span>.",
                        "translation": "I will stay here for a week.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Quero fazer <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>pergunta simples</span>.",
                        "translation": "I want to ask a simple question.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Contou-nos <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>história engraçada</span>.",
                        "translation": "Told us a funny story.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Indefinite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                "rule": "Indefinite article: introduces an unspecific singular feminine noun.",
                "allowed_lemmas": [
                    "fotografia",
                    "ideia",
                    "semana",
                    "casa",
                    "pergunta",
                    "história"
                ],
                "targetHTML": "Vi <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>fotografia</span>.",
                "translation": "I saw a photograph.",
                "examples": [
                    {
                        "targetHTML": "Vi <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>fotografia</span>.",
                        "translation": "I saw a photograph.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ela teve <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>ideia brilhante</span>.",
                        "translation": "She had a brilliant idea.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ficarei aqui por <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>semana</span>.",
                        "translation": "I will stay here for a week.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Quero fazer <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>pergunta simples</span>.",
                        "translation": "I want to ask a simple question.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Contou-nos <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>história engraçada</span>.",
                        "translation": "Told us a funny story.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">os</span> + <span class=\"fw-token-c\">Plural Masculine Noun</span>",
                "rule": "Definite article: introduces specific masculine plural nouns.",
                "allowed_lemmas": [
                    "livros",
                    "dias",
                    "olhos",
                    "amigos",
                    "homens",
                    "carros"
                ],
                "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>livros</span> estão na mesa.",
                "translation": "The books are on the table.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>livros</span> estão na mesa.",
                        "translation": "The books are on the table.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>dias</span> passam voando.",
                        "translation": "The days fly by.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>meus amigos</span> chegam logo.",
                        "translation": "My friends arrive soon.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>olhos dela</span> brilhavam.",
                        "translation": "Her eyes were shining.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>carros</span> pararam no sinal.",
                        "translation": "The cars stopped at the light.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">os</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Direct object pronoun: replaces 3rd-person masculine plural objects ('them').",
                "allowed_lemmas": [
                    "ver",
                    "comprar",
                    "conhecer",
                    "ouvir",
                    "deixar"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>vi</span> no cinema.",
                "translation": "I saw them at the movies.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>vi</span> no cinema.",
                        "translation": "I saw them at the movies.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Não <span class='fw-token-connector'>os</span> <span class='fw-token-v'>encontrei</span> em casa.",
                        "translation": "I did not find them at home.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>comprei</span> na feira de manhã.",
                        "translation": "I bought them at the morning market.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "O professor <span class='fw-token-connector'>os</span> <span class='fw-token-v'>chamou</span> para conversar.",
                        "translation": "The teacher called them to talk.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Guardei<span class='fw-token-connector'>-os</span> com cuidado.",
                        "translation": "I stored them carefully.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">os</span> + <span class=\"fw-token-c\">Plural Masculine Noun</span>",
                "rule": "Definite article: introduces specific masculine plural nouns.",
                "allowed_lemmas": [
                    "livros",
                    "dias",
                    "olhos",
                    "amigos",
                    "homens",
                    "carros"
                ],
                "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>livros</span> estão na mesa.",
                "translation": "The books are on the table.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>livros</span> estão na mesa.",
                        "translation": "The books are on the table.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>dias</span> passam voando.",
                        "translation": "The days fly by.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>meus amigos</span> chegam logo.",
                        "translation": "My friends arrive soon.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>olhos dela</span> brilhavam.",
                        "translation": "Her eyes were shining.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>carros</span> pararam no sinal.",
                        "translation": "The cars stopped at the light.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">os</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Direct object pronoun: replaces 3rd-person masculine plural objects ('them').",
                "allowed_lemmas": [
                    "ver",
                    "comprar",
                    "conhecer",
                    "ouvir",
                    "deixar"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>vi</span> no cinema.",
                "translation": "I saw them at the movies.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>vi</span> no cinema.",
                        "translation": "I saw them at the movies.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Não <span class='fw-token-connector'>os</span> <span class='fw-token-v'>encontrei</span> em casa.",
                        "translation": "I did not find them at home.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>comprei</span> na feira de manhã.",
                        "translation": "I bought them at the morning market.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "O professor <span class='fw-token-connector'>os</span> <span class='fw-token-v'>chamou</span> para conversar.",
                        "translation": "The teacher called them to talk.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Guardei<span class='fw-token-connector'>-os</span> com cuidado.",
                        "translation": "I stored them carefully.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">as</span> + <span class=\"fw-token-c\">Plural Feminine Noun</span>",
                "rule": "Definite article: introduces specific feminine plural nouns.",
                "allowed_lemmas": [
                    "portas",
                    "flores",
                    "coisas",
                    "horas",
                    "pessoas",
                    "ruas"
                ],
                "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>portas</span> estão abertas.",
                "translation": "The doors are open.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>portas</span> estão abertas.",
                        "translation": "The doors are open.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>flores</span> do jardim desabrocharam.",
                        "translation": "The garden flowers blossomed.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>pessoas</span> aplaudiram de pé.",
                        "translation": "The people gave a standing ovation.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>ruas</span> estavam iluminadas.",
                        "translation": "The streets were illuminated.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Entendo bem <span class='fw-token-connector'>as</span> <span class='fw-token-c'>tuas dúvidas</span>.",
                        "translation": "I understand your questions well.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">as</span> + <span class=\"fw-token-c\">Plural Feminine Noun</span>",
                "rule": "Definite article: introduces specific feminine plural nouns.",
                "allowed_lemmas": [
                    "portas",
                    "flores",
                    "coisas",
                    "horas",
                    "pessoas",
                    "ruas"
                ],
                "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>portas</span> estão abertas.",
                "translation": "The doors are open.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>portas</span> estão abertas.",
                        "translation": "The doors are open.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>flores</span> do jardim desabrocharam.",
                        "translation": "The garden flowers blossomed.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>pessoas</span> aplaudiram de pé.",
                        "translation": "The people gave a standing ovation.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>As</span> <span class='fw-token-c'>ruas</span> estavam iluminadas.",
                        "translation": "The streets were illuminated.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Entendo bem <span class='fw-token-connector'>as</span> <span class='fw-token-c'>tuas dúvidas</span>.",
                        "translation": "I understand your questions well.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">me</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 'me / to me' receiving direct or indirect action.",
                "allowed_lemmas": [
                    "ajudar",
                    "chamar",
                    "ouvir",
                    "dar",
                    "dizer",
                    "avisar"
                ],
                "targetHTML": "Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ajudou</span> hoje.",
                "translation": "He helped me today.",
                "examples": [
                    {
                        "targetHTML": "Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ajudou</span> hoje.",
                        "translation": "He helped me today.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>me</span> <span class='fw-token-v'>chamou</span> para jantar.",
                        "translation": "She invited me for dinner.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Você <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ouviu</span> bem?",
                        "translation": "Did you hear me well?",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>deu</span> um bom conselho.",
                        "translation": "He gave me good advice.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>avisa</span> quando chegar.",
                        "translation": "Let me know when you arrive.",
                        "source": "Contemporary speech"
                    }
                ]
            },
            {
                "tag": "Reflexive Clitic",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">-me</span>",
                "rule": "Reflexive clitic: action reflects back onto the speaker ('myself').",
                "allowed_lemmas": [
                    "lembrar",
                    "sentir",
                    "sentar",
                    "levantar",
                    "esquecer"
                ],
                "targetHTML": "<span class='fw-token-v'>Lembro</span><span class='fw-token-connector'>-me</span> de tudo.",
                "translation": "I remember everything.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Lembro</span><span class='fw-token-connector'>-me</span> de tudo.",
                        "translation": "I remember everything.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Sinto</span><span class='fw-token-connector'>-me</span> ótimo depois do descanso.",
                        "translation": "I feel great after resting.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Sentei</span><span class='fw-token-connector'>-me</span> no banco da praça.",
                        "translation": "I sat down on the square bench.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Esqueci</span><span class='fw-token-connector'>-me</span> da carteira em casa.",
                        "translation": "I forgot my wallet at home.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Levantei</span><span class='fw-token-connector'>-me</span> ao amanhecer.",
                        "translation": "I got up at daybreak.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">me</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 'me / to me' receiving direct or indirect action.",
                "allowed_lemmas": [
                    "ajudar",
                    "chamar",
                    "ouvir",
                    "dar",
                    "dizer",
                    "avisar"
                ],
                "targetHTML": "Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ajudou</span> hoje.",
                "translation": "He helped me today.",
                "examples": [
                    {
                        "targetHTML": "Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ajudou</span> hoje.",
                        "translation": "He helped me today.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>me</span> <span class='fw-token-v'>chamou</span> para jantar.",
                        "translation": "She invited me for dinner.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Você <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ouviu</span> bem?",
                        "translation": "Did you hear me well?",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>deu</span> um bom conselho.",
                        "translation": "He gave me good advice.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>avisa</span> quando chegar.",
                        "translation": "Let me know when you arrive.",
                        "source": "Contemporary speech"
                    }
                ]
            },
            {
                "tag": "Reflexive Clitic",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">-me</span>",
                "rule": "Reflexive clitic: action reflects back onto the speaker ('myself').",
                "allowed_lemmas": [
                    "lembrar",
                    "sentir",
                    "sentar",
                    "levantar",
                    "esquecer"
                ],
                "targetHTML": "<span class='fw-token-v'>Lembro</span><span class='fw-token-connector'>-me</span> de tudo.",
                "translation": "I remember everything.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Lembro</span><span class='fw-token-connector'>-me</span> de tudo.",
                        "translation": "I remember everything.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Sinto</span><span class='fw-token-connector'>-me</span> ótimo depois do descanso.",
                        "translation": "I feel great after resting.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Sentei</span><span class='fw-token-connector'>-me</span> no banco da praça.",
                        "translation": "I sat down on the square bench.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Esqueci</span><span class='fw-token-connector'>-me</span> da carteira em casa.",
                        "translation": "I forgot my wallet at home.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Levantei</span><span class='fw-token-connector'>-me</span> ao amanhecer.",
                        "translation": "I got up at daybreak.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">te</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 2nd-person 'you / to you' (informal).",
                "allowed_lemmas": [
                    "amar",
                    "ver",
                    "ligar",
                    "dizer",
                    "ouvir",
                    "esperar"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>amo</span>.",
                "translation": "I love you.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>amo</span>.",
                        "translation": "I love you.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>vi</span> ontem à tarde.",
                        "translation": "I saw you yesterday afternoon.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>ligo</span> mais tarde.",
                        "translation": "I will call you later.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Vou <span class='fw-token-connector'>te</span> <span class='fw-token-v'>contar</span> uma novidade.",
                        "translation": "I will tell you some news.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Nós <span class='fw-token-connector'>te</span> <span class='fw-token-v'>esperamos</span> no saguão.",
                        "translation": "We wait for you in the lobby.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">te</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 2nd-person 'you / to you' (informal).",
                "allowed_lemmas": [
                    "amar",
                    "ver",
                    "ligar",
                    "dizer",
                    "ouvir",
                    "esperar"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>amo</span>.",
                "translation": "I love you.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>amo</span>.",
                        "translation": "I love you.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>vi</span> ontem à tarde.",
                        "translation": "I saw you yesterday afternoon.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>ligo</span> mais tarde.",
                        "translation": "I will call you later.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Vou <span class='fw-token-connector'>te</span> <span class='fw-token-v'>contar</span> uma novidade.",
                        "translation": "I will tell you some news.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Nós <span class='fw-token-connector'>te</span> <span class='fw-token-v'>esperamos</span> no saguão.",
                        "translation": "We wait for you in the lobby.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Indirect Object",
                "formulaHTML": "<span class=\"fw-token-connector\">lhe</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Indirect object pronoun: represents 'to him / to her / to you'.",
                "allowed_lemmas": [
                    "dar",
                    "dizer",
                    "entregar",
                    "perguntar",
                    "enviar",
                    "pedir"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>dei</span> o livro.",
                "translation": "I gave him the book.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>dei</span> o livro.",
                        "translation": "I gave him the book.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>disse</span> a verdade.",
                        "translation": "She told him the truth.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "O carteiro <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>entregou</span> a encomenda.",
                        "translation": "The mail carrier delivered the package to her.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>enviei</span> uma mensagem ontem.",
                        "translation": "I sent him a message yesterday.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lhe</span> <span class='fw-token-v'>desejo</span> toda a sorte do mundo.",
                        "translation": "I wish you all the luck in the world.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Indirect Object",
                "formulaHTML": "<span class=\"fw-token-connector\">lhe</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Indirect object pronoun: represents 'to him / to her / to you'.",
                "allowed_lemmas": [
                    "dar",
                    "dizer",
                    "entregar",
                    "perguntar",
                    "enviar",
                    "pedir"
                ],
                "targetHTML": "Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>dei</span> o livro.",
                "translation": "I gave him the book.",
                "examples": [
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>dei</span> o livro.",
                        "translation": "I gave him the book.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ela <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>disse</span> a verdade.",
                        "translation": "She told him the truth.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "O carteiro <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>entregou</span> a encomenda.",
                        "translation": "The mail carrier delivered the package to her.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>enviei</span> uma mensagem ontem.",
                        "translation": "I sent him a message yesterday.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lhe</span> <span class='fw-token-v'>desejo</span> toda a sorte do mundo.",
                        "translation": "I wish you all the luck in the world.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Direction / Destination",
                "formulaHTML": "<span class=\"fw-token-connector\">a + o</span> + <span class=\"fw-token-c\">Masculine Destination / Time</span>",
                "rule": "Contraction of 'a + o' (to the / at the) before masculine singular nouns.",
                "allowed_lemmas": [
                    "mercado",
                    "cinema",
                    "trabalho",
                    "fim",
                    "redor"
                ],
                "targetHTML": "Vou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>mercado</span>.",
                "translation": "I am going to the market.",
                "examples": [
                    {
                        "targetHTML": "Vou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>mercado</span>.",
                        "translation": "I am going to the market.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Fomos <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>cinema</span> ver a estreia.",
                        "translation": "We went to the cinema to see the premiere.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Voltou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>trabalho na segunda-feira</span>.",
                        "translation": "Returned to work on Monday.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Chegamos <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>fim da jornada</span>.",
                        "translation": "We reached the end of the journey.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Olhou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>redor com curiosidade</span>.",
                        "translation": "Looked around with curiosity.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Temporal Nexus",
                "formulaHTML": "<span class=\"fw-token-connector\">ao</span> + <span class=\"fw-token-v\">Infinitive</span>",
                "rule": "Temporal nexus: expresses 'upon doing' or 'at the moment of'.",
                "allowed_lemmas": [
                    "chegar",
                    "ouvir",
                    "entrar",
                    "abrir",
                    "sair"
                ],
                "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>chegar</span>, avise-me.",
                "translation": "Upon arriving, let me know.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>chegar</span>, avise-me.",
                        "translation": "Upon arriving, let me know.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>ouvir</span> o sinal, todos saíram.",
                        "translation": "Upon hearing the signal, everyone left.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>abrir</span> a porta, sentiu o vento frio.",
                        "translation": "Upon opening the door, felt the cold wind.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Sorriu <span class='fw-token-connector'>ao</span> <span class='fw-token-v'>ver</span> os velhos amigos.",
                        "translation": "Smiled upon seeing the old friends.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>entrar</span> na sala, percebeu o silêncio.",
                        "translation": "Upon entering the room, noticed the silence.",
                        "source": "Conversation"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Direction / Destination",
                "formulaHTML": "<span class=\"fw-token-connector\">a + o</span> + <span class=\"fw-token-c\">Masculine Destination / Time</span>",
                "rule": "Contraction of 'a + o' (to the / at the) before masculine singular nouns.",
                "allowed_lemmas": [
                    "mercado",
                    "cinema",
                    "trabalho",
                    "fim",
                    "redor"
                ],
                "targetHTML": "Vou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>mercado</span>.",
                "translation": "I am going to the market.",
                "examples": [
                    {
                        "targetHTML": "Vou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>mercado</span>.",
                        "translation": "I am going to the market.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Fomos <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>cinema</span> ver a estreia.",
                        "translation": "We went to the cinema to see the premiere.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Voltou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>trabalho na segunda-feira</span>.",
                        "translation": "Returned to work on Monday.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Chegamos <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>fim da jornada</span>.",
                        "translation": "We reached the end of the journey.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Olhou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>redor com curiosidade</span>.",
                        "translation": "Looked around with curiosity.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Temporal Nexus",
                "formulaHTML": "<span class=\"fw-token-connector\">ao</span> + <span class=\"fw-token-v\">Infinitive</span>",
                "rule": "Temporal nexus: expresses 'upon doing' or 'at the moment of'.",
                "allowed_lemmas": [
                    "chegar",
                    "ouvir",
                    "entrar",
                    "abrir",
                    "sair"
                ],
                "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>chegar</span>, avise-me.",
                "translation": "Upon arriving, let me know.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>chegar</span>, avise-me.",
                        "translation": "Upon arriving, let me know.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>ouvir</span> o sinal, todos saíram.",
                        "translation": "Upon hearing the signal, everyone left.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>abrir</span> a porta, sentiu o vento frio.",
                        "translation": "Upon opening the door, felt the cold wind.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Sorriu <span class='fw-token-connector'>ao</span> <span class='fw-token-v'>ver</span> os velhos amigos.",
                        "translation": "Smiled upon seeing the old friends.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>entrar</span> na sala, percebeu o silêncio.",
                        "translation": "Upon entering the room, noticed the silence.",
                        "source": "Conversation"
                    }
                ]
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
                "tag": "Destination / Time",
                "formulaHTML": "<span class=\"fw-token-connector\">a + a</span> + <span class=\"fw-token-c\">Feminine Destination / Time</span>",
                "rule": "Crasis contraction of 'a + a' (to the / at the) before feminine singular nouns.",
                "allowed_lemmas": [
                    "noite",
                    "praia",
                    "escola",
                    "hora",
                    "tarde"
                ],
                "targetHTML": "Chegamos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>noite</span>.",
                "translation": "We arrived at night.",
                "examples": [
                    {
                        "targetHTML": "Chegamos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>noite</span>.",
                        "translation": "We arrived at night.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Fomos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>praia tomar sol</span>.",
                        "translation": "We went to the beach to sunbathe.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "As crianças foram <span class='fw-token-connector'>à</span> <span class='fw-token-c'>escola de manhã</span>.",
                        "translation": "The kids went to school in the morning.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "O filme começa <span class='fw-token-connector'>à</span> <span class='fw-token-c'>uma da tarde</span>.",
                        "translation": "The film begins at one in the afternoon.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Voltaremos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>nossa rotina habitual</span>.",
                        "translation": "We will return to our usual routine.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Destination / Time",
                "formulaHTML": "<span class=\"fw-token-connector\">a + a</span> + <span class=\"fw-token-c\">Feminine Destination / Time</span>",
                "rule": "Crasis contraction of 'a + a' (to the / at the) before feminine singular nouns.",
                "allowed_lemmas": [
                    "noite",
                    "praia",
                    "escola",
                    "hora",
                    "tarde"
                ],
                "targetHTML": "Chegamos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>noite</span>.",
                "translation": "We arrived at night.",
                "examples": [
                    {
                        "targetHTML": "Chegamos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>noite</span>.",
                        "translation": "We arrived at night.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Fomos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>praia tomar sol</span>.",
                        "translation": "We went to the beach to sunbathe.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "As crianças foram <span class='fw-token-connector'>à</span> <span class='fw-token-c'>escola de manhã</span>.",
                        "translation": "The kids went to school in the morning.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "O filme começa <span class='fw-token-connector'>à</span> <span class='fw-token-c'>uma da tarde</span>.",
                        "translation": "The film begins at one in the afternoon.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Voltaremos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>nossa rotina habitual</span>.",
                        "translation": "We will return to our usual routine.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Path / Motive",
                "formulaHTML": "<span class=\"fw-token-connector\">por + o</span> + <span class=\"fw-token-c\">Masculine Path / Reason</span>",
                "rule": "Contraction of 'por + o' (through the / by the / for the).",
                "allowed_lemmas": [
                    "parque",
                    "caminho",
                    "trabalho",
                    "apoio",
                    "mundo"
                ],
                "targetHTML": "Caminhei <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>parque</span>.",
                "translation": "I walked through the park.",
                "examples": [
                    {
                        "targetHTML": "Caminhei <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>parque</span>.",
                        "translation": "I walked through the park.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Obrigado <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>apoio constante</span>.",
                        "translation": "Thank you for the constant support.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Passamos <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>caminho mais curto</span>.",
                        "translation": "We passed through the shortest path.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Foi reconhecido <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>bom trabalho</span>.",
                        "translation": "Was recognized for the good work.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Viajou <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>mundo todo</span>.",
                        "translation": "Traveled throughout the whole world.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Path / Motive",
                "formulaHTML": "<span class=\"fw-token-connector\">por + o</span> + <span class=\"fw-token-c\">Masculine Path / Reason</span>",
                "rule": "Contraction of 'por + o' (through the / by the / for the).",
                "allowed_lemmas": [
                    "parque",
                    "caminho",
                    "trabalho",
                    "apoio",
                    "mundo"
                ],
                "targetHTML": "Caminhei <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>parque</span>.",
                "translation": "I walked through the park.",
                "examples": [
                    {
                        "targetHTML": "Caminhei <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>parque</span>.",
                        "translation": "I walked through the park.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Obrigado <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>apoio constante</span>.",
                        "translation": "Thank you for the constant support.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Passamos <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>caminho mais curto</span>.",
                        "translation": "We passed through the shortest path.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Foi reconhecido <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>bom trabalho</span>.",
                        "translation": "Was recognized for the good work.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Viajou <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>mundo todo</span>.",
                        "translation": "Traveled throughout the whole world.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Path / Motive",
                "formulaHTML": "<span class=\"fw-token-connector\">por + a</span> + <span class=\"fw-token-c\">Feminine Path / Reason</span>",
                "rule": "Contraction of 'por + a' (through the / by the / for the).",
                "allowed_lemmas": [
                    "ajuda",
                    "cidade",
                    "janela",
                    "manhã",
                    "vida"
                ],
                "targetHTML": "Obrigado <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>ajuda</span>.",
                "translation": "Thank you for the help.",
                "examples": [
                    {
                        "targetHTML": "Obrigado <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>ajuda</span>.",
                        "translation": "Thank you for the help.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Passeamos <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>cidade antiga</span>.",
                        "translation": "We strolled through the old city.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Olhou <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>janela do quarto</span>.",
                        "translation": "Looked through the bedroom window.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Caminha <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>manhã bem cedo</span>.",
                        "translation": "Walks in the very early morning.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Lutou <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>justiça com determinação</span>.",
                        "translation": "Fought for justice with determination.",
                        "source": "Dialogue"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Path / Motive",
                "formulaHTML": "<span class=\"fw-token-connector\">por + a</span> + <span class=\"fw-token-c\">Feminine Path / Reason</span>",
                "rule": "Contraction of 'por + a' (through the / by the / for the).",
                "allowed_lemmas": [
                    "ajuda",
                    "cidade",
                    "janela",
                    "manhã",
                    "vida"
                ],
                "targetHTML": "Obrigado <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>ajuda</span>.",
                "translation": "Thank you for the help.",
                "examples": [
                    {
                        "targetHTML": "Obrigado <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>ajuda</span>.",
                        "translation": "Thank you for the help.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Passeamos <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>cidade antiga</span>.",
                        "translation": "We strolled through the old city.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Olhou <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>janela do quarto</span>.",
                        "translation": "Looked through the bedroom window.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Caminha <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>manhã bem cedo</span>.",
                        "translation": "Walks in the very early morning.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Lutou <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>justiça com determinação</span>.",
                        "translation": "Fought for justice with determination.",
                        "source": "Dialogue"
                    }
                ]
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
                "tag": "Location / State",
                "formulaHTML": "<span class=\"fw-token-connector\">em + um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                "rule": "Contraction of 'em + um' (in a / on a).",
                "allowed_lemmas": [
                    "apartamento",
                    "dia",
                    "segundo",
                    "lugar",
                    "momento"
                ],
                "targetHTML": "Moro <span class='fw-token-connector'>num</span> <span class='fw-token-c'>apartamento</span>.",
                "translation": "I live in an apartment.",
                "examples": [
                    {
                        "targetHTML": "Moro <span class='fw-token-connector'>num</span> <span class='fw-token-c'>apartamento</span>.",
                        "translation": "I live in an apartment.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Tudo aconteceu <span class='fw-token-connector'>num</span> <span class='fw-token-c'>segundo</span>.",
                        "translation": "Everything happened in a second.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Num</span> <span class='fw-token-c'>dia chuvoso</span>, ficamos lendo.",
                        "translation": "On a rainy day, we stayed reading.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Eles vivem <span class='fw-token-connector'>num</span> <span class='fw-token-c'>lugar tranquilo</span>.",
                        "translation": "They live in a quiet place.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Conhecemo-nos <span class='fw-token-connector'>num</span> <span class='fw-token-c'>evento cultural</span>.",
                        "translation": "We met at a cultural event.",
                        "source": "Dialogue"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Location / State",
                "formulaHTML": "<span class=\"fw-token-connector\">em + um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                "rule": "Contraction of 'em + um' (in a / on a).",
                "allowed_lemmas": [
                    "apartamento",
                    "dia",
                    "segundo",
                    "lugar",
                    "momento"
                ],
                "targetHTML": "Moro <span class='fw-token-connector'>num</span> <span class='fw-token-c'>apartamento</span>.",
                "translation": "I live in an apartment.",
                "examples": [
                    {
                        "targetHTML": "Moro <span class='fw-token-connector'>num</span> <span class='fw-token-c'>apartamento</span>.",
                        "translation": "I live in an apartment.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Tudo aconteceu <span class='fw-token-connector'>num</span> <span class='fw-token-c'>segundo</span>.",
                        "translation": "Everything happened in a second.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Num</span> <span class='fw-token-c'>dia chuvoso</span>, ficamos lendo.",
                        "translation": "On a rainy day, we stayed reading.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Eles vivem <span class='fw-token-connector'>num</span> <span class='fw-token-c'>lugar tranquilo</span>.",
                        "translation": "They live in a quiet place.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Conhecemo-nos <span class='fw-token-connector'>num</span> <span class='fw-token-c'>evento cultural</span>.",
                        "translation": "We met at a cultural event.",
                        "source": "Dialogue"
                    }
                ]
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
                "tag": "Location / State",
                "formulaHTML": "<span class=\"fw-token-connector\">em + uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                "rule": "Contraction of 'em + uma' (in a / on a).",
                "allowed_lemmas": [
                    "loja",
                    "casa",
                    "noite",
                    "viagem",
                    "mesa"
                ],
                "targetHTML": "Entrei <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>loja</span>.",
                "translation": "I entered a shop.",
                "examples": [
                    {
                        "targetHTML": "Entrei <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>loja</span>.",
                        "translation": "I entered a shop.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ficamos hospedados <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>pousada</span>.",
                        "translation": "We stayed hosted at an inn.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Numa</span> <span class='fw-token-c'>noite fria</span>, acendemos a lareira.",
                        "translation": "On a cold night, we lit the fireplace.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Ela trabalha <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>empresa de tecnologia</span>.",
                        "translation": "She works at a technology company.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Sentamo-nos <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>mesa perto da janela</span>.",
                        "translation": "We sat at a table near the window.",
                        "source": "Everyday speech"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Location / State",
                "formulaHTML": "<span class=\"fw-token-connector\">em + uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                "rule": "Contraction of 'em + uma' (in a / on a).",
                "allowed_lemmas": [
                    "loja",
                    "casa",
                    "noite",
                    "viagem",
                    "mesa"
                ],
                "targetHTML": "Entrei <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>loja</span>.",
                "translation": "I entered a shop.",
                "examples": [
                    {
                        "targetHTML": "Entrei <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>loja</span>.",
                        "translation": "I entered a shop.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ficamos hospedados <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>pousada</span>.",
                        "translation": "We stayed hosted at an inn.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Numa</span> <span class='fw-token-c'>noite fria</span>, acendemos a lareira.",
                        "translation": "On a cold night, we lit the fireplace.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Ela trabalha <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>empresa de tecnologia</span>.",
                        "translation": "She works at a technology company.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Sentamo-nos <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>mesa perto da janela</span>.",
                        "translation": "We sat at a table near the window.",
                        "source": "Everyday speech"
                    }
                ]
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
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dele</span>",
                "rule": "Possessive contraction of 'de + ele' (his / of him).",
                "allowed_lemmas": [
                    "amigo",
                    "casa",
                    "carro",
                    "trabalho",
                    "irmão"
                ],
                "targetHTML": "Conheço o amigo <span class='fw-token-connector'>dele</span>.",
                "translation": "I know his friend.",
                "examples": [
                    {
                        "targetHTML": "Conheço o amigo <span class='fw-token-connector'>dele</span>.",
                        "translation": "I know his friend.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "A casa <span class='fw-token-connector'>dele</span> é muito acolhedora.",
                        "translation": "His house is very cozy.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Gostei muito da ideia <span class='fw-token-connector'>dele</span>.",
                        "translation": "I really liked his idea.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O carro <span class='fw-token-connector'>dele</span> está parado ali.",
                        "translation": "His car is parked there.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O trabalho <span class='fw-token-connector'>dele</span> foi elogiado por todos.",
                        "translation": "His work was praised by all.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dele</span>",
                "rule": "Possessive contraction of 'de + ele' (his / of him).",
                "allowed_lemmas": [
                    "amigo",
                    "casa",
                    "carro",
                    "trabalho",
                    "irmão"
                ],
                "targetHTML": "Conheço o amigo <span class='fw-token-connector'>dele</span>.",
                "translation": "I know his friend.",
                "examples": [
                    {
                        "targetHTML": "Conheço o amigo <span class='fw-token-connector'>dele</span>.",
                        "translation": "I know his friend.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "A casa <span class='fw-token-connector'>dele</span> é muito acolhedora.",
                        "translation": "His house is very cozy.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Gostei muito da ideia <span class='fw-token-connector'>dele</span>.",
                        "translation": "I really liked his idea.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O carro <span class='fw-token-connector'>dele</span> está parado ali.",
                        "translation": "His car is parked there.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O trabalho <span class='fw-token-connector'>dele</span> foi elogiado por todos.",
                        "translation": "His work was praised by all.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dela</span>",
                "rule": "Possessive contraction of 'de + ela' (her / of her).",
                "allowed_lemmas": [
                    "casa",
                    "voz",
                    "sorriso",
                    "irmã",
                    "opinião"
                ],
                "targetHTML": "A casa <span class='fw-token-connector'>dela</span> é grande.",
                "translation": "Her house is big.",
                "examples": [
                    {
                        "targetHTML": "A casa <span class='fw-token-connector'>dela</span> é grande.",
                        "translation": "Her house is big.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "A voz <span class='fw-token-connector'>dela</span> é calma e bonita.",
                        "translation": "Her voice is calm and beautiful.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Respeito muito a opinião <span class='fw-token-connector'>dela</span>.",
                        "translation": "I respect her opinion a lot.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "A irmã <span class='fw-token-connector'>dela</span> chega amanhã.",
                        "translation": "Her sister arrives tomorrow.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O sorriso <span class='fw-token-connector'>dela</span> iluminou o ambiente.",
                        "translation": "Her smile lit up the room.",
                        "source": "Subtitles"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dela</span>",
                "rule": "Possessive contraction of 'de + ela' (her / of her).",
                "allowed_lemmas": [
                    "casa",
                    "voz",
                    "sorriso",
                    "irmã",
                    "opinião"
                ],
                "targetHTML": "A casa <span class='fw-token-connector'>dela</span> é grande.",
                "translation": "Her house is big.",
                "examples": [
                    {
                        "targetHTML": "A casa <span class='fw-token-connector'>dela</span> é grande.",
                        "translation": "Her house is big.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "A voz <span class='fw-token-connector'>dela</span> é calma e bonita.",
                        "translation": "Her voice is calm and beautiful.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Respeito muito a opinião <span class='fw-token-connector'>dela</span>.",
                        "translation": "I respect her opinion a lot.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "A irmã <span class='fw-token-connector'>dela</span> chega amanhã.",
                        "translation": "Her sister arrives tomorrow.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "O sorriso <span class='fw-token-connector'>dela</span> iluminou o ambiente.",
                        "translation": "Her smile lit up the room.",
                        "source": "Subtitles"
                    }
                ]
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
                "tag": "Privation / Absence",
                "formulaHTML": "<span class=\"fw-token-v\">Verb / Noun</span> + <span class=\"fw-token-connector\">sem</span> + <span class=\"fw-token-c\">Missing Element</span>",
                "rule": "Privative preposition: marks absence, exclusion, or lack.",
                "allowed_lemmas": [
                    "açúcar",
                    "medo",
                    "pressa",
                    "dúvida",
                    "problema"
                ],
                "targetHTML": "Café <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>açúcar</span>, por favor.",
                "translation": "Coffee without sugar, please.",
                "examples": [
                    {
                        "targetHTML": "Café <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>açúcar</span>, por favor.",
                        "translation": "Coffee without sugar, please.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ele falou <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>qualquer hesitação</span>.",
                        "translation": "He spoke without any hesitation.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Saímos <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>pressa nenhuma</span>.",
                        "translation": "We left without any rush.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Isso é, <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>dúvida</span>, a melhor opção.",
                        "translation": "That is, without doubt, the best option.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Resolvemos a questão <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>problemas</span>.",
                        "translation": "We solved the issue without problems.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Privation / Absence",
                "formulaHTML": "<span class=\"fw-token-v\">Verb / Noun</span> + <span class=\"fw-token-connector\">sem</span> + <span class=\"fw-token-c\">Missing Element</span>",
                "rule": "Privative preposition: marks absence, exclusion, or lack.",
                "allowed_lemmas": [
                    "açúcar",
                    "medo",
                    "pressa",
                    "dúvida",
                    "problema"
                ],
                "targetHTML": "Café <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>açúcar</span>, por favor.",
                "translation": "Coffee without sugar, please.",
                "examples": [
                    {
                        "targetHTML": "Café <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>açúcar</span>, por favor.",
                        "translation": "Coffee without sugar, please.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ele falou <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>qualquer hesitação</span>.",
                        "translation": "He spoke without any hesitation.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Saímos <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>pressa nenhuma</span>.",
                        "translation": "We left without any rush.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Isso é, <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>dúvida</span>, a melhor opção.",
                        "translation": "That is, without doubt, the best option.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Resolvemos a questão <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>problemas</span>.",
                        "translation": "We solved the issue without problems.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Thematic Topic",
                "formulaHTML": "<span class=\"fw-token-v\">Discussion / Thought</span> + <span class=\"fw-token-connector\">sobre</span> + <span class=\"fw-token-c\">Topic</span>",
                "rule": "Thematic marker: introduces the subject matter or topic.",
                "allowed_lemmas": [
                    "falar",
                    "conversar",
                    "escrever",
                    "discutir",
                    "pensar"
                ],
                "targetHTML": "Falamos <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o projeto</span>.",
                "translation": "We talked about the project.",
                "examples": [
                    {
                        "targetHTML": "Falamos <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o projeto</span>.",
                        "translation": "We talked about the project.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Li um livro <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>história europeia</span>.",
                        "translation": "I read a book about European history.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Eles discutiram <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o futuro do trabalho</span>.",
                        "translation": "They discussed about the future of work.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Gostaria de saber mais <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>isso</span>.",
                        "translation": "I would like to know more about that.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Escreveu um ensaio <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a arte moderna</span>.",
                        "translation": "Wrote an essay about modern art.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Spatial Surface",
                "formulaHTML": "<span class=\"fw-token-v\">Position</span> + <span class=\"fw-token-connector\">sobre</span> + <span class=\"fw-token-c\">Surface</span>",
                "rule": "Spatial relation: located on top of a surface ('upon / above').",
                "allowed_lemmas": [
                    "mesa",
                    "cama",
                    "cidade",
                    "rio",
                    "bancada"
                ],
                "targetHTML": "O papel está <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a mesa</span>.",
                "translation": "The paper is on the table.",
                "examples": [
                    {
                        "targetHTML": "O papel está <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a mesa</span>.",
                        "translation": "The paper is on the table.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "A ponte ergue-se <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o grande rio</span>.",
                        "translation": "The bridge rises over the great river.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Deixou o casaco <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a cama</span>.",
                        "translation": "Left the coat upon the bed.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "As chaves ficaram <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o balcão</span>.",
                        "translation": "The keys were left on the counter.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O sol poente brilhava <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a cidade</span>.",
                        "translation": "The setting sun shone over the city.",
                        "source": "Everyday speech"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Thematic Topic",
                "formulaHTML": "<span class=\"fw-token-v\">Discussion / Thought</span> + <span class=\"fw-token-connector\">sobre</span> + <span class=\"fw-token-c\">Topic</span>",
                "rule": "Thematic marker: introduces the subject matter or topic.",
                "allowed_lemmas": [
                    "falar",
                    "conversar",
                    "escrever",
                    "discutir",
                    "pensar"
                ],
                "targetHTML": "Falamos <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o projeto</span>.",
                "translation": "We talked about the project.",
                "examples": [
                    {
                        "targetHTML": "Falamos <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o projeto</span>.",
                        "translation": "We talked about the project.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Li um livro <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>história europeia</span>.",
                        "translation": "I read a book about European history.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Eles discutiram <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o futuro do trabalho</span>.",
                        "translation": "They discussed about the future of work.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Gostaria de saber mais <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>isso</span>.",
                        "translation": "I would like to know more about that.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Escreveu um ensaio <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a arte moderna</span>.",
                        "translation": "Wrote an essay about modern art.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Spatial Surface",
                "formulaHTML": "<span class=\"fw-token-v\">Position</span> + <span class=\"fw-token-connector\">sobre</span> + <span class=\"fw-token-c\">Surface</span>",
                "rule": "Spatial relation: located on top of a surface ('upon / above').",
                "allowed_lemmas": [
                    "mesa",
                    "cama",
                    "cidade",
                    "rio",
                    "bancada"
                ],
                "targetHTML": "O papel está <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a mesa</span>.",
                "translation": "The paper is on the table.",
                "examples": [
                    {
                        "targetHTML": "O papel está <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a mesa</span>.",
                        "translation": "The paper is on the table.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "A ponte ergue-se <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o grande rio</span>.",
                        "translation": "The bridge rises over the great river.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Deixou o casaco <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a cama</span>.",
                        "translation": "Left the coat upon the bed.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "As chaves ficaram <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o balcão</span>.",
                        "translation": "The keys were left on the counter.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "O sol poente brilhava <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a cidade</span>.",
                        "translation": "The setting sun shone over the city.",
                        "source": "Everyday speech"
                    }
                ]
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
                "tag": "Terminal Boundary",
                "formulaHTML": "<span class=\"fw-token-v\">Movement / Time</span> + <span class=\"fw-token-connector\">até</span> + <span class=\"fw-token-c\">Limit / Endpoint</span>",
                "rule": "Terminal boundary: points to the spatial or temporal stopping point.",
                "allowed_lemmas": [
                    "caminhar",
                    "ficar",
                    "esperar",
                    "trabalhar",
                    "ir"
                ],
                "targetHTML": "Vou caminhar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a esquina</span>.",
                "translation": "I will walk as far as the corner.",
                "examples": [
                    {
                        "targetHTML": "Vou caminhar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a esquina</span>.",
                        "translation": "I will walk as far as the corner.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ficamos no evento <span class='fw-token-connector'>até</span> <span class='fw-token-c'>às dez</span>.",
                        "translation": "We stayed at the event until ten.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Espere aqui <span class='fw-token-connector'>até</span> <span class='fw-token-c'>eu voltar</span>.",
                        "translation": "Wait here until I return.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Trabalhou sem parar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>ao anoitecer</span>.",
                        "translation": "Worked non-stop until nightfall.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Dirigiram <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a fronteira</span>.",
                        "translation": "They drove as far as the border.",
                        "source": "Everyday speech"
                    }
                ]
            },
            {
                "tag": "Scalar Focus",
                "formulaHTML": "<span class=\"fw-token-connector\">Até</span> + <span class=\"fw-token-c\">Surprising Subject</span>",
                "rule": "Scalar focus particle: emphasizes an extreme case ('even').",
                "allowed_lemmas": [
                    "criança",
                    "ele",
                    "amigo",
                    "inimigo",
                    "estranho"
                ],
                "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>as crianças</span> entenderam.",
                "translation": "Even the children understood.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>as crianças</span> entenderam.",
                        "translation": "Even the children understood.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>ele</span> ficou surpreso com o resultado.",
                        "translation": "Even he was surprised with the result.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>os especialistas</span> erraram a previsão.",
                        "translation": "Even the experts missed the prediction.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Estava tão frio que <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a água congelou</span>.",
                        "translation": "It was so cold that even the water froze.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>o vento</span> parecia sussurrar segredos.",
                        "translation": "Even the wind seemed to whisper secrets.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Terminal Boundary",
                "formulaHTML": "<span class=\"fw-token-v\">Movement / Time</span> + <span class=\"fw-token-connector\">até</span> + <span class=\"fw-token-c\">Limit / Endpoint</span>",
                "rule": "Terminal boundary: points to the spatial or temporal stopping point.",
                "allowed_lemmas": [
                    "caminhar",
                    "ficar",
                    "esperar",
                    "trabalhar",
                    "ir"
                ],
                "targetHTML": "Vou caminhar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a esquina</span>.",
                "translation": "I will walk as far as the corner.",
                "examples": [
                    {
                        "targetHTML": "Vou caminhar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a esquina</span>.",
                        "translation": "I will walk as far as the corner.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ficamos no evento <span class='fw-token-connector'>até</span> <span class='fw-token-c'>às dez</span>.",
                        "translation": "We stayed at the event until ten.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Espere aqui <span class='fw-token-connector'>até</span> <span class='fw-token-c'>eu voltar</span>.",
                        "translation": "Wait here until I return.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Trabalhou sem parar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>ao anoitecer</span>.",
                        "translation": "Worked non-stop until nightfall.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Dirigiram <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a fronteira</span>.",
                        "translation": "They drove as far as the border.",
                        "source": "Everyday speech"
                    }
                ]
            },
            {
                "tag": "Scalar Focus",
                "formulaHTML": "<span class=\"fw-token-connector\">Até</span> + <span class=\"fw-token-c\">Surprising Subject</span>",
                "rule": "Scalar focus particle: emphasizes an extreme case ('even').",
                "allowed_lemmas": [
                    "criança",
                    "ele",
                    "amigo",
                    "inimigo",
                    "estranho"
                ],
                "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>as crianças</span> entenderam.",
                "translation": "Even the children understood.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>as crianças</span> entenderam.",
                        "translation": "Even the children understood.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>ele</span> ficou surpreso com o resultado.",
                        "translation": "Even he was surprised with the result.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>os especialistas</span> erraram a previsão.",
                        "translation": "Even the experts missed the prediction.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Estava tão frio que <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a água congelou</span>.",
                        "translation": "It was so cold that even the water froze.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>o vento</span> parecia sussurrar segredos.",
                        "translation": "Even the wind seemed to whisper secrets.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Causal Reason",
                "formulaHTML": "<span class=\"fw-token-v\">Result</span> + <span class=\"fw-token-connector\">porque</span> + <span class=\"fw-token-c\">Cause</span>",
                "rule": "Causal conjunction: explains the reason or motive behind an action.",
                "allowed_lemmas": [
                    "chover",
                    "cansar",
                    "gostar",
                    "querer",
                    "precisar"
                ],
                "targetHTML": "Fiquei em casa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>choveu</span>.",
                "translation": "I stayed home because it rained.",
                "examples": [
                    {
                        "targetHTML": "Fiquei em casa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>choveu</span>.",
                        "translation": "I stayed home because it rained.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Não fui à festa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estava muito cansado</span>.",
                        "translation": "I didn't go to the party because I was very tired.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Estudo português <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>amo a cultura</span>.",
                        "translation": "I study Portuguese because I love the culture.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ele sorriu <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>ouviu uma boa notícia</span>.",
                        "translation": "He smiled because he heard good news.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Perguntei <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>queria ter a certeza</span>.",
                        "translation": "I asked because I wanted to be sure.",
                        "source": "Dialogue"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Causal Reason",
                "formulaHTML": "<span class=\"fw-token-v\">Result</span> + <span class=\"fw-token-connector\">porque</span> + <span class=\"fw-token-c\">Cause</span>",
                "rule": "Causal conjunction: explains the reason or motive behind an action.",
                "allowed_lemmas": [
                    "chover",
                    "cansar",
                    "gostar",
                    "querer",
                    "precisar"
                ],
                "targetHTML": "Fiquei em casa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>choveu</span>.",
                "translation": "I stayed home because it rained.",
                "examples": [
                    {
                        "targetHTML": "Fiquei em casa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>choveu</span>.",
                        "translation": "I stayed home because it rained.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Não fui à festa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estava muito cansado</span>.",
                        "translation": "I didn't go to the party because I was very tired.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Estudo português <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>amo a cultura</span>.",
                        "translation": "I study Portuguese because I love the culture.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ele sorriu <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>ouviu uma boa notícia</span>.",
                        "translation": "He smiled because he heard good news.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Perguntei <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>queria ter a certeza</span>.",
                        "translation": "I asked because I wanted to be sure.",
                        "source": "Dialogue"
                    }
                ]
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
                "tag": "Temporal Subordination",
                "formulaHTML": "<span class=\"fw-token-connector\">Quando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Clause</span>",
                "rule": "Temporal subordinator: anchors the action to a specific time or event.",
                "allowed_lemmas": [
                    "chegar",
                    "abrir",
                    "ouvir",
                    "sair",
                    "voltar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>cheguei</span>, <span class='fw-token-c'>todos aplaudiram</span>.",
                "translation": "When I arrived, everyone applauded.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>cheguei</span>, <span class='fw-token-c'>todos aplaudiram</span>.",
                        "translation": "When I arrived, everyone applauded.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> você <span class='fw-token-v'>puder</span>, ligue-me por favor.",
                        "translation": "When you can, please call me.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> o sol <span class='fw-token-v'>nasce</span>, a cidade ganha vida.",
                        "translation": "When the sun rises, the city comes alive.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>terminares</span> o trabalho, avisa.",
                        "translation": "When you finish the work, let me know.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> era jovem, viajava muito.",
                        "translation": "When I was young, I used to travel a lot.",
                        "source": "Subtitles"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Temporal Subordination",
                "formulaHTML": "<span class=\"fw-token-connector\">Quando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Clause</span>",
                "rule": "Temporal subordinator: anchors the action to a specific time or event.",
                "allowed_lemmas": [
                    "chegar",
                    "abrir",
                    "ouvir",
                    "sair",
                    "voltar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>cheguei</span>, <span class='fw-token-c'>todos aplaudiram</span>.",
                "translation": "When I arrived, everyone applauded.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>cheguei</span>, <span class='fw-token-c'>todos aplaudiram</span>.",
                        "translation": "When I arrived, everyone applauded.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> você <span class='fw-token-v'>puder</span>, ligue-me por favor.",
                        "translation": "When you can, please call me.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> o sol <span class='fw-token-v'>nasce</span>, a cidade ganha vida.",
                        "translation": "When the sun rises, the city comes alive.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>terminares</span> o trabalho, avisa.",
                        "translation": "When you finish the work, let me know.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Quando</span> era jovem, viajava muito.",
                        "translation": "When I was young, I used to travel a lot.",
                        "source": "Subtitles"
                    }
                ]
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
                "tag": "Neutral Demonstrative",
                "formulaHTML": "<span class=\"fw-token-connector\">isso</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Neutral demonstrative: refers to a stated fact, concept, or object near the listener.",
                "allowed_lemmas": [
                    "ser",
                    "significar",
                    "acontecer",
                    "ajudar",
                    "mudar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>é</span> verdade.",
                "translation": "That is true.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>é</span> verdade.",
                        "translation": "That is true.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>acontece</span> com frequência.",
                        "translation": "That happens frequently.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isso</span> não <span class='fw-token-v'>faz</span> sentido nenhum.",
                        "translation": "That makes no sense at all.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>mudou</span> toda a situação.",
                        "translation": "That changed the whole situation.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Já sabia <span class='fw-token-connector'>disso</span> antes de falarem.",
                        "translation": "I already knew about that before they spoke.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Neutral Demonstrative",
                "formulaHTML": "<span class=\"fw-token-connector\">isso</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Neutral demonstrative: refers to a stated fact, concept, or object near the listener.",
                "allowed_lemmas": [
                    "ser",
                    "significar",
                    "acontecer",
                    "ajudar",
                    "mudar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>é</span> verdade.",
                "translation": "That is true.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>é</span> verdade.",
                        "translation": "That is true.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>acontece</span> com frequência.",
                        "translation": "That happens frequently.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isso</span> não <span class='fw-token-v'>faz</span> sentido nenhum.",
                        "translation": "That makes no sense at all.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>mudou</span> toda a situação.",
                        "translation": "That changed the whole situation.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Já sabia <span class='fw-token-connector'>disso</span> antes de falarem.",
                        "translation": "I already knew about that before they spoke.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Immediate Demonstrative",
                "formulaHTML": "<span class=\"fw-token-connector\">isto</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Neutral demonstrative: refers to an immediate object or idea near the speaker.",
                "allowed_lemmas": [
                    "ser",
                    "pertencer",
                    "parecer",
                    "bastar",
                    "custar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>é</span> para você.",
                "translation": "This is for you.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>é</span> para você.",
                        "translation": "This is for you.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>parece</span> delicioso.",
                        "translation": "This looks delicious.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>pertence</span> ao meu colega.",
                        "translation": "This belongs to my colleague.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>basta</span> por hoje.",
                        "translation": "This is enough for today.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>custou</span> muito menos do que imaginei.",
                        "translation": "This cost much less than I imagined.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Immediate Demonstrative",
                "formulaHTML": "<span class=\"fw-token-connector\">isto</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Neutral demonstrative: refers to an immediate object or idea near the speaker.",
                "allowed_lemmas": [
                    "ser",
                    "pertencer",
                    "parecer",
                    "bastar",
                    "custar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>é</span> para você.",
                "translation": "This is for you.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>é</span> para você.",
                        "translation": "This is for you.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>parece</span> delicioso.",
                        "translation": "This looks delicious.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>pertence</span> ao meu colega.",
                        "translation": "This belongs to my colleague.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>basta</span> por hoje.",
                        "translation": "This is enough for today.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>custou</span> muito menos do que imaginei.",
                        "translation": "This cost much less than I imagined.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Universal Totality",
                "formulaHTML": "<span class=\"fw-token-connector\">tudo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                "rule": "Universal pronoun: represents the totality of things ('everything / all').",
                "allowed_lemmas": [
                    "estar",
                    "correr",
                    "mudar",
                    "terminar",
                    "ficar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>está</span> bem.",
                "translation": "Everything is fine.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>está</span> bem.",
                        "translation": "Everything is fine.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>correu</span> perfeitamente no evento.",
                        "translation": "Everything went perfectly at the event.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>mudou</span> depois daquele dia.",
                        "translation": "Everything changed after that day.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Entendi <span class='fw-token-connector'>tudo</span> o que explicaste.",
                        "translation": "I understood everything that you explained.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>ficou</span> calmo após a tempestade.",
                        "translation": "Everything became quiet after the storm.",
                        "source": "Subtitles"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Universal Totality",
                "formulaHTML": "<span class=\"fw-token-connector\">tudo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                "rule": "Universal pronoun: represents the totality of things ('everything / all').",
                "allowed_lemmas": [
                    "estar",
                    "correr",
                    "mudar",
                    "terminar",
                    "ficar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>está</span> bem.",
                "translation": "Everything is fine.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>está</span> bem.",
                        "translation": "Everything is fine.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>correu</span> perfeitamente no evento.",
                        "translation": "Everything went perfectly at the event.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>mudou</span> depois daquele dia.",
                        "translation": "Everything changed after that day.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Entendi <span class='fw-token-connector'>tudo</span> o que explicaste.",
                        "translation": "I understood everything that you explained.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>ficou</span> calmo após a tempestade.",
                        "translation": "Everything became quiet after the storm.",
                        "source": "Subtitles"
                    }
                ]
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
                "tag": "Verbal Valency",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Complement</span>",
                "rule": "Required link: preceding verb governs 'de' before its object or action.",
                "allowed_lemmas": [
                    "acordar",
                    "hablar",
                    "tratar",
                    "depender",
                    "olvidar",
                    "darse_cuenta"
                ],
                "targetHTML": "<span class='fw-token-v'>Me acuerdo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ti</span>.",
                "translation": "I remember you.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Me acuerdo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ti</span>.",
                        "translation": "I remember you.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Antonio dice que no <span class='fw-token-v'>se acuerda</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ella</span>.",
                        "translation": "Antonio says he doesn't remember her.",
                        "source": "Dictionary speech"
                    },
                    {
                        "targetHTML": "Se <span class='fw-token-v'>trata</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>un asunto importante</span>.",
                        "translation": "It's about an important matter.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Eso <span class='fw-token-v'>depende</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>muchos factores</span>.",
                        "translation": "That depends on many factors.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "No te <span class='fw-token-v'>olvides</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>cerrar la puerta</span>.",
                        "translation": "Don't forget to close the door.",
                        "source": "Everyday dialogue"
                    }
                ]
            },
            {
                "tag": "Nominal Binding",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                "rule": "Nominal binding: marks possession, origin, content, or material.",
                "allowed_lemmas": [
                    "vaso",
                    "casa",
                    "hora",
                    "madera",
                    "amigo",
                    "días"
                ],
                "targetHTML": "Quiero un <span class='fw-token-v'>vaso</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>agua</span>.",
                "translation": "I want a glass of water.",
                "examples": [
                    {
                        "targetHTML": "Quiero un <span class='fw-token-v'>vaso</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>agua</span>.",
                        "translation": "I want a glass of water.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Una hermosa <span class='fw-token-v'>mesa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>madera</span>.",
                        "translation": "A beautiful wooden table.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Es <span class='fw-token-v'>hora</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>comer</span>.",
                        "translation": "It is time to eat.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Un <span class='fw-token-v'>amigo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>mi hermano nos visitó</span>.",
                        "translation": "A friend of my brother visited us.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Un <span class='fw-token-v'>día</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>descanso muy merecido</span>.",
                        "translation": "A well-deserved day of rest.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Verbal Valency",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Complement</span>",
                "rule": "Required link: preceding verb governs 'de' before its object or action.",
                "allowed_lemmas": [
                    "acordar",
                    "hablar",
                    "tratar",
                    "depender",
                    "olvidar",
                    "darse_cuenta"
                ],
                "targetHTML": "<span class='fw-token-v'>Me acuerdo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ti</span>.",
                "translation": "I remember you.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Me acuerdo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ti</span>.",
                        "translation": "I remember you.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Antonio dice que no <span class='fw-token-v'>se acuerda</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ella</span>.",
                        "translation": "Antonio says he doesn't remember her.",
                        "source": "Dictionary speech"
                    },
                    {
                        "targetHTML": "Se <span class='fw-token-v'>trata</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>un asunto importante</span>.",
                        "translation": "It's about an important matter.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Eso <span class='fw-token-v'>depende</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>muchos factores</span>.",
                        "translation": "That depends on many factors.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "No te <span class='fw-token-v'>olvides</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>cerrar la puerta</span>.",
                        "translation": "Don't forget to close the door.",
                        "source": "Everyday dialogue"
                    }
                ]
            },
            {
                "tag": "Nominal Binding",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                "rule": "Nominal binding: marks possession, origin, content, or material.",
                "allowed_lemmas": [
                    "vaso",
                    "casa",
                    "hora",
                    "madera",
                    "amigo",
                    "días"
                ],
                "targetHTML": "Quiero un <span class='fw-token-v'>vaso</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>agua</span>.",
                "translation": "I want a glass of water.",
                "examples": [
                    {
                        "targetHTML": "Quiero un <span class='fw-token-v'>vaso</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>agua</span>.",
                        "translation": "I want a glass of water.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Una hermosa <span class='fw-token-v'>mesa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>madera</span>.",
                        "translation": "A beautiful wooden table.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Es <span class='fw-token-v'>hora</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>comer</span>.",
                        "translation": "It is time to eat.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Un <span class='fw-token-v'>amigo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>mi hermano nos visitó</span>.",
                        "translation": "A friend of my brother visited us.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Un <span class='fw-token-v'>día</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>descanso muy merecido</span>.",
                        "translation": "A well-deserved day of rest.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Clausal Link",
                "formulaHTML": "<span class=\"fw-token-v\">Thought / Speech</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Clause</span>",
                "rule": "Subordination: bridges what someone thinks, says, or knows to the statement.",
                "allowed_lemmas": [
                    "creer",
                    "pensar",
                    "decir",
                    "saber",
                    "esperar"
                ],
                "targetHTML": "<span class='fw-token-v'>Creo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>va a llover</span>.",
                "translation": "I think it’s going to rain.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Creo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>va a llover</span>.",
                        "translation": "I think it’s going to rain.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ella <span class='fw-token-v'>dijo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vendría temprano</span>.",
                        "translation": "She said she would come early.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Sé</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>tienes toda la razón</span>.",
                        "translation": "I know you are completely right.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Espero</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>todo salga bien</span>.",
                        "translation": "I hope everything turns out well.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Él <span class='fw-token-v'>pensaba</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>era el momento oportuno</span>.",
                        "translation": "He thought it was the right moment.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Relative Pronoun",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                "rule": "Relativization: refers back to a noun while introducing descriptive detail.",
                "allowed_lemmas": [
                    "libro",
                    "persona",
                    "película",
                    "lugar",
                    "cosa"
                ],
                "targetHTML": "Es el <span class='fw-token-v'>libro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estoy leyendo</span>.",
                "translation": "It is the book that I am reading.",
                "examples": [
                    {
                        "targetHTML": "Es el <span class='fw-token-v'>libro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estoy leyendo</span>.",
                        "translation": "It is the book that I am reading.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "La <span class='fw-token-v'>persona</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>llamó no dejó mensaje</span>.",
                        "translation": "The person who called left no message.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "La <span class='fw-token-v'>película</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vimos fue excelente</span>.",
                        "translation": "The movie we saw was excellent.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "El <span class='fw-token-v'>lugar</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>conocimos era precioso</span>.",
                        "translation": "The place we visited was lovely.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Son <span class='fw-token-v'>cosas</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>pasan todos los días</span>.",
                        "translation": "These are things that happen every day.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Comparison",
                "formulaHTML": "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                "rule": "Comparison: connects the two sides of a degree or quality contrast.",
                "allowed_lemmas": [
                    "más",
                    "menos",
                    "mejor",
                    "peor",
                    "mayor"
                ],
                "targetHTML": "Ella es <span class='fw-token-v'>más alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>yo</span>.",
                "translation": "She is taller than me.",
                "examples": [
                    {
                        "targetHTML": "Ella es <span class='fw-token-v'>más alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>yo</span>.",
                        "translation": "She is taller than me.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Esto es <span class='fw-token-v'>mejor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>lo que teníamos</span>.",
                        "translation": "This is better than what we had.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Tardamos <span class='fw-token-v'>menos tiempo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>ayer</span>.",
                        "translation": "We took less time than yesterday.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "La casa es <span class='fw-token-v'>mayor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>el piso anterior</span>.",
                        "translation": "The house is larger than the previous flat.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Hoy hace <span class='fw-token-v'>más calor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>la semana pasada</span>.",
                        "translation": "Today is hotter than last week.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Clausal Link",
                "formulaHTML": "<span class=\"fw-token-v\">Thought / Speech</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Clause</span>",
                "rule": "Subordination: bridges what someone thinks, says, or knows to the statement.",
                "allowed_lemmas": [
                    "creer",
                    "pensar",
                    "decir",
                    "saber",
                    "esperar"
                ],
                "targetHTML": "<span class='fw-token-v'>Creo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>va a llover</span>.",
                "translation": "I think it’s going to rain.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-v'>Creo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>va a llover</span>.",
                        "translation": "I think it’s going to rain.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ella <span class='fw-token-v'>dijo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vendría temprano</span>.",
                        "translation": "She said she would come early.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Sé</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>tienes toda la razón</span>.",
                        "translation": "I know you are completely right.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-v'>Espero</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>todo salga bien</span>.",
                        "translation": "I hope everything turns out well.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Él <span class='fw-token-v'>pensaba</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>era el momento oportuno</span>.",
                        "translation": "He thought it was the right moment.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Relative Pronoun",
                "formulaHTML": "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                "rule": "Relativization: refers back to a noun while introducing descriptive detail.",
                "allowed_lemmas": [
                    "libro",
                    "persona",
                    "película",
                    "lugar",
                    "cosa"
                ],
                "targetHTML": "Es el <span class='fw-token-v'>libro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estoy leyendo</span>.",
                "translation": "It is the book that I am reading.",
                "examples": [
                    {
                        "targetHTML": "Es el <span class='fw-token-v'>libro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estoy leyendo</span>.",
                        "translation": "It is the book that I am reading.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "La <span class='fw-token-v'>persona</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>llamó no dejó mensaje</span>.",
                        "translation": "The person who called left no message.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "La <span class='fw-token-v'>película</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vimos fue excelente</span>.",
                        "translation": "The movie we saw was excellent.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "El <span class='fw-token-v'>lugar</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>conocimos era precioso</span>.",
                        "translation": "The place we visited was lovely.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Son <span class='fw-token-v'>cosas</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>pasan todos los días</span>.",
                        "translation": "These are things that happen every day.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Comparison",
                "formulaHTML": "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                "rule": "Comparison: connects the two sides of a degree or quality contrast.",
                "allowed_lemmas": [
                    "más",
                    "menos",
                    "mejor",
                    "peor",
                    "mayor"
                ],
                "targetHTML": "Ella es <span class='fw-token-v'>más alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>yo</span>.",
                "translation": "She is taller than me.",
                "examples": [
                    {
                        "targetHTML": "Ella es <span class='fw-token-v'>más alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>yo</span>.",
                        "translation": "She is taller than me.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Esto es <span class='fw-token-v'>mejor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>lo que teníamos</span>.",
                        "translation": "This is better than what we had.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Tardamos <span class='fw-token-v'>menos tiempo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>ayer</span>.",
                        "translation": "We took less time than yesterday.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "La casa es <span class='fw-token-v'>mayor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>el piso anterior</span>.",
                        "translation": "The house is larger than the previous flat.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Hoy hace <span class='fw-token-v'>más calor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>la semana pasada</span>.",
                        "translation": "Today is hotter than last week.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Directional Goal",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Destination</span>",
                "rule": "Directional goal: indicates movement toward a place or terminus.",
                "allowed_lemmas": [
                    "ir",
                    "viajar",
                    "llegar",
                    "volver",
                    "entrar"
                ],
                "targetHTML": "Voy <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Madrid</span>.",
                "translation": "I am going to Madrid.",
                "examples": [
                    {
                        "targetHTML": "Voy <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Madrid</span>.",
                        "translation": "I am going to Madrid.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Llegamos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>casa sanos y salvos</span>.",
                        "translation": "We arrived home safe and sound.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Regresaron <span class='fw-token-connector'>a</span> <span class='fw-token-c'>España el mes pasado</span>.",
                        "translation": "They returned to Spain last month.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Fuimos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>la plaza mayor</span>.",
                        "translation": "We went to the main square.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "El tren viaja <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Valencia</span>.",
                        "translation": "The train travels to Valencia.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Personal 'a'",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Person</span>",
                "rule": "Personal 'a': marks a specific human or personalized direct object.",
                "allowed_lemmas": [
                    "ver",
                    "conocer",
                    "llamar",
                    "esperar",
                    "cuidar"
                ],
                "targetHTML": "Veo <span class='fw-token-connector'>a</span> <span class='fw-token-c'>María</span> todos los días.",
                "translation": "I see María every day.",
                "examples": [
                    {
                        "targetHTML": "Veo <span class='fw-token-connector'>a</span> <span class='fw-token-c'>María</span> todos los días.",
                        "translation": "I see María every day.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Conocí <span class='fw-token-connector'>a</span> <span class='fw-token-c'>tu hermano en la fiesta</span>.",
                        "translation": "I met your brother at the party.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Llamé <span class='fw-token-connector'>a</span> <span class='fw-token-c'>mis padres anoche</span>.",
                        "translation": "I called my parents last night.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Estamos esperando <span class='fw-token-connector'>a</span> <span class='fw-token-c'>los demás invitados</span>.",
                        "translation": "We are waiting for the rest of the guests.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Cuida mucho <span class='fw-token-connector'>a</span> <span class='fw-token-c'>sus abuelos</span>.",
                        "translation": "Takes great care of his grandparents.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Directional Goal",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Destination</span>",
                "rule": "Directional goal: indicates movement toward a place or terminus.",
                "allowed_lemmas": [
                    "ir",
                    "viajar",
                    "llegar",
                    "volver",
                    "entrar"
                ],
                "targetHTML": "Voy <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Madrid</span>.",
                "translation": "I am going to Madrid.",
                "examples": [
                    {
                        "targetHTML": "Voy <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Madrid</span>.",
                        "translation": "I am going to Madrid.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Llegamos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>casa sanos y salvos</span>.",
                        "translation": "We arrived home safe and sound.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Regresaron <span class='fw-token-connector'>a</span> <span class='fw-token-c'>España el mes pasado</span>.",
                        "translation": "They returned to Spain last month.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Fuimos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>la plaza mayor</span>.",
                        "translation": "We went to the main square.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "El tren viaja <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Valencia</span>.",
                        "translation": "The train travels to Valencia.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Personal 'a'",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Person</span>",
                "rule": "Personal 'a': marks a specific human or personalized direct object.",
                "allowed_lemmas": [
                    "ver",
                    "conocer",
                    "llamar",
                    "esperar",
                    "cuidar"
                ],
                "targetHTML": "Veo <span class='fw-token-connector'>a</span> <span class='fw-token-c'>María</span> todos los días.",
                "translation": "I see María every day.",
                "examples": [
                    {
                        "targetHTML": "Veo <span class='fw-token-connector'>a</span> <span class='fw-token-c'>María</span> todos los días.",
                        "translation": "I see María every day.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Conocí <span class='fw-token-connector'>a</span> <span class='fw-token-c'>tu hermano en la fiesta</span>.",
                        "translation": "I met your brother at the party.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Llamé <span class='fw-token-connector'>a</span> <span class='fw-token-c'>mis padres anoche</span>.",
                        "translation": "I called my parents last night.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Estamos esperando <span class='fw-token-connector'>a</span> <span class='fw-token-c'>los demás invitados</span>.",
                        "translation": "We are waiting for the rest of the guests.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Cuida mucho <span class='fw-token-connector'>a</span> <span class='fw-token-c'>sus abuelos</span>.",
                        "translation": "Takes great care of his grandparents.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Spatial Framing",
                "formulaHTML": "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">en</span> + <span class=\"fw-token-c\">Location</span>",
                "rule": "Spatial framing: anchors an action or entity within a place or space.",
                "allowed_lemmas": [
                    "vivir",
                    "estar",
                    "trabajar",
                    "quedarse",
                    "entrar"
                ],
                "targetHTML": "Vivo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>Sevilla</span>.",
                "translation": "I live in Seville.",
                "examples": [
                    {
                        "targetHTML": "Vivo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>Sevilla</span>.",
                        "translation": "I live in Seville.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Estamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>el centro de la ciudad</span>.",
                        "translation": "We are in the city center.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Trabaja <span class='fw-token-connector'>en</span> <span class='fw-token-c'>un restaurante cerca</span>.",
                        "translation": "Works at a restaurant nearby.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Nos quedamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>casa descansando</span>.",
                        "translation": "We stayed at home resting.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "El libro está guardado <span class='fw-token-connector'>en</span> <span class='fw-token-c'>la biblioteca</span>.",
                        "translation": "The book is kept in the library.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Temporal Framing",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">en</span> + <span class=\"fw-token-c\">Time Period</span>",
                "rule": "Temporal framing: situates an event inside a month, year, or duration.",
                "allowed_lemmas": [
                    "viajar",
                    "llegar",
                    "terminar",
                    "volver",
                    "nacer"
                ],
                "targetHTML": "Viajamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>julio</span>.",
                "translation": "We travel in July.",
                "examples": [
                    {
                        "targetHTML": "Viajamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>julio</span>.",
                        "translation": "We travel in July.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Nació <span class='fw-token-connector'>en</span> <span class='fw-token-c'>1998</span>.",
                        "translation": "Was born in 1998.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Estará listo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>cinco minutos</span>.",
                        "translation": "It will be ready in five minutes.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Las clases comienzan <span class='fw-token-connector'>en</span> <span class='fw-token-c'>septiembre</span>.",
                        "translation": "Classes begin in September.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Volveremos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>pocas horas</span>.",
                        "translation": "We will return in a few hours.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Spatial Framing",
                "formulaHTML": "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">en</span> + <span class=\"fw-token-c\">Location</span>",
                "rule": "Spatial framing: anchors an action or entity within a place or space.",
                "allowed_lemmas": [
                    "vivir",
                    "estar",
                    "trabajar",
                    "quedarse",
                    "entrar"
                ],
                "targetHTML": "Vivo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>Sevilla</span>.",
                "translation": "I live in Seville.",
                "examples": [
                    {
                        "targetHTML": "Vivo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>Sevilla</span>.",
                        "translation": "I live in Seville.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Estamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>el centro de la ciudad</span>.",
                        "translation": "We are in the city center.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Trabaja <span class='fw-token-connector'>en</span> <span class='fw-token-c'>un restaurante cerca</span>.",
                        "translation": "Works at a restaurant nearby.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Nos quedamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>casa descansando</span>.",
                        "translation": "We stayed at home resting.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "El libro está guardado <span class='fw-token-connector'>en</span> <span class='fw-token-c'>la biblioteca</span>.",
                        "translation": "The book is kept in the library.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Temporal Framing",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">en</span> + <span class=\"fw-token-c\">Time Period</span>",
                "rule": "Temporal framing: situates an event inside a month, year, or duration.",
                "allowed_lemmas": [
                    "viajar",
                    "llegar",
                    "terminar",
                    "volver",
                    "nacer"
                ],
                "targetHTML": "Viajamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>julio</span>.",
                "translation": "We travel in July.",
                "examples": [
                    {
                        "targetHTML": "Viajamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>julio</span>.",
                        "translation": "We travel in July.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Nació <span class='fw-token-connector'>en</span> <span class='fw-token-c'>1998</span>.",
                        "translation": "Was born in 1998.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Estará listo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>cinco minutos</span>.",
                        "translation": "It will be ready in five minutes.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Las clases comienzan <span class='fw-token-connector'>en</span> <span class='fw-token-c'>septiembre</span>.",
                        "translation": "Classes begin in September.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Volveremos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>pocas horas</span>.",
                        "translation": "We will return in a few hours.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Cause / Motive",
                "formulaHTML": "<span class=\"fw-token-v\">State / Gratitude</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                "rule": "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                "allowed_lemmas": [
                    "gracias",
                    "preocuparse",
                    "luchar",
                    "esperar",
                    "pagar"
                ],
                "targetHTML": "Gracias <span class='fw-token-connector'>por</span> <span class='fw-token-c'>venir</span>.",
                "translation": "Thank you for coming.",
                "examples": [
                    {
                        "targetHTML": "Gracias <span class='fw-token-connector'>por</span> <span class='fw-token-c'>venir</span>.",
                        "translation": "Thank you for coming.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Te preocupas demasiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>eso</span>.",
                        "translation": "You worry too much about that.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Lucharon <span class='fw-token-connector'>por</span> <span class='fw-token-c'>sus derechos</span>.",
                        "translation": "They fought for their rights.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Pagó diez euros <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el billete</span>.",
                        "translation": "Paid ten euros for the ticket.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Fue premiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>su gran esfuerzo</span>.",
                        "translation": "Was awarded for his great effort.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Trajectory",
                "formulaHTML": "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                "rule": "Trajectory: marks the route, medium, or space through which motion happens.",
                "allowed_lemmas": [
                    "pasear",
                    "caminar",
                    "andar",
                    "mirar",
                    "viajar"
                ],
                "targetHTML": "Paseo <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el parque</span>.",
                "translation": "I stroll through the park.",
                "examples": [
                    {
                        "targetHTML": "Paseo <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el parque</span>.",
                        "translation": "I stroll through the park.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Caminamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>las calles del centro</span>.",
                        "translation": "We walked through downtown streets.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Miró <span class='fw-token-connector'>por</span> <span class='fw-token-c'>la ventana del tren</span>.",
                        "translation": "Looked through the train window.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "El gato entró <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el balcón</span>.",
                        "translation": "The cat entered through the balcony.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Viajamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>toda Andalucía</span>.",
                        "translation": "We traveled throughout Andalusia.",
                        "source": "Everyday speech"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Cause / Motive",
                "formulaHTML": "<span class=\"fw-token-v\">State / Gratitude</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                "rule": "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                "allowed_lemmas": [
                    "gracias",
                    "preocuparse",
                    "luchar",
                    "esperar",
                    "pagar"
                ],
                "targetHTML": "Gracias <span class='fw-token-connector'>por</span> <span class='fw-token-c'>venir</span>.",
                "translation": "Thank you for coming.",
                "examples": [
                    {
                        "targetHTML": "Gracias <span class='fw-token-connector'>por</span> <span class='fw-token-c'>venir</span>.",
                        "translation": "Thank you for coming.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Te preocupas demasiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>eso</span>.",
                        "translation": "You worry too much about that.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Lucharon <span class='fw-token-connector'>por</span> <span class='fw-token-c'>sus derechos</span>.",
                        "translation": "They fought for their rights.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Pagó diez euros <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el billete</span>.",
                        "translation": "Paid ten euros for the ticket.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Fue premiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>su gran esfuerzo</span>.",
                        "translation": "Was awarded for his great effort.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Trajectory",
                "formulaHTML": "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                "rule": "Trajectory: marks the route, medium, or space through which motion happens.",
                "allowed_lemmas": [
                    "pasear",
                    "caminar",
                    "andar",
                    "mirar",
                    "viajar"
                ],
                "targetHTML": "Paseo <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el parque</span>.",
                "translation": "I stroll through the park.",
                "examples": [
                    {
                        "targetHTML": "Paseo <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el parque</span>.",
                        "translation": "I stroll through the park.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Caminamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>las calles del centro</span>.",
                        "translation": "We walked through downtown streets.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Miró <span class='fw-token-connector'>por</span> <span class='fw-token-c'>la ventana del tren</span>.",
                        "translation": "Looked through the train window.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "El gato entró <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el balcón</span>.",
                        "translation": "The cat entered through the balcony.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Viajamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>toda Andalucía</span>.",
                        "translation": "We traveled throughout Andalusia.",
                        "source": "Everyday speech"
                    }
                ]
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
                "tag": "Purpose",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Objective</span>",
                "rule": "Purpose and aim: establishes the intended goal or outcome of an action.",
                "allowed_lemmas": [
                    "estudiar",
                    "trabajar",
                    "ahorrar",
                    "salir",
                    "llamar"
                ],
                "targetHTML": "Estudio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                "translation": "I study in order to learn.",
                "examples": [
                    {
                        "targetHTML": "Estudio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                        "translation": "I study in order to learn.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ahorro dinero <span class='fw-token-connector'>para</span> <span class='fw-token-c'>viajar en verano</span>.",
                        "translation": "I save money in order to travel in summer.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Llamé <span class='fw-token-connector'>para</span> <span class='fw-token-c'>confirmar la cita</span>.",
                        "translation": "I called to confirm the appointment.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Nos detuvimos <span class='fw-token-connector'>para</span> <span class='fw-token-c'>descansar</span>.",
                        "translation": "We stopped to rest.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Trabajan duro <span class='fw-token-connector'>para</span> <span class='fw-token-c'>construir un buen futuro</span>.",
                        "translation": "They work hard to build a good future.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Beneficiary / Target",
                "formulaHTML": "<span class=\"fw-token-v\">Entity</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                "rule": "Beneficiary / Target: designates the person meant to receive something.",
                "allowed_lemmas": [
                    "regalo",
                    "carta",
                    "comida",
                    "mensaje",
                    "tiempo"
                ],
                "targetHTML": "Esto es <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ti</span>.",
                "translation": "This is for you.",
                "examples": [
                    {
                        "targetHTML": "Esto es <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ti</span>.",
                        "translation": "This is for you.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Compré un libro <span class='fw-token-connector'>para</span> <span class='fw-token-c'>mi madre</span>.",
                        "translation": "I bought a book for my mother.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Hay espacio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>dos personas más</span>.",
                        "translation": "There is room for two more people.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Preparé la cena <span class='fw-token-connector'>para</span> <span class='fw-token-c'>la familia</span>.",
                        "translation": "I prepared dinner for the family.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Un mensaje especial <span class='fw-token-connector'>para</span> <span class='fw-token-c'>los graduados</span>.",
                        "translation": "A special message for the graduates.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Purpose",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Objective</span>",
                "rule": "Purpose and aim: establishes the intended goal or outcome of an action.",
                "allowed_lemmas": [
                    "estudiar",
                    "trabajar",
                    "ahorrar",
                    "salir",
                    "llamar"
                ],
                "targetHTML": "Estudio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                "translation": "I study in order to learn.",
                "examples": [
                    {
                        "targetHTML": "Estudio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                        "translation": "I study in order to learn.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Ahorro dinero <span class='fw-token-connector'>para</span> <span class='fw-token-c'>viajar en verano</span>.",
                        "translation": "I save money in order to travel in summer.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Llamé <span class='fw-token-connector'>para</span> <span class='fw-token-c'>confirmar la cita</span>.",
                        "translation": "I called to confirm the appointment.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Nos detuvimos <span class='fw-token-connector'>para</span> <span class='fw-token-c'>descansar</span>.",
                        "translation": "We stopped to rest.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Trabajan duro <span class='fw-token-connector'>para</span> <span class='fw-token-c'>construir un buen futuro</span>.",
                        "translation": "They work hard to build a good future.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Beneficiary / Target",
                "formulaHTML": "<span class=\"fw-token-v\">Entity</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                "rule": "Beneficiary / Target: designates the person meant to receive something.",
                "allowed_lemmas": [
                    "regalo",
                    "carta",
                    "comida",
                    "mensaje",
                    "tiempo"
                ],
                "targetHTML": "Esto es <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ti</span>.",
                "translation": "This is for you.",
                "examples": [
                    {
                        "targetHTML": "Esto es <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ti</span>.",
                        "translation": "This is for you.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Compré un libro <span class='fw-token-connector'>para</span> <span class='fw-token-c'>mi madre</span>.",
                        "translation": "I bought a book for my mother.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Hay espacio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>dos personas más</span>.",
                        "translation": "There is room for two more people.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Preparé la cena <span class='fw-token-connector'>para</span> <span class='fw-token-c'>la familia</span>.",
                        "translation": "I prepared dinner for the family.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Un mensaje especial <span class='fw-token-connector'>para</span> <span class='fw-token-c'>los graduados</span>.",
                        "translation": "A special message for the graduates.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Accompaniment",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">con</span> + <span class=\"fw-token-c\">Companion</span>",
                "rule": "Accompaniment: joins an action to the companion sharing it.",
                "allowed_lemmas": [
                    "cenar",
                    "hablar",
                    "salir",
                    "vivir",
                    "trabajar"
                ],
                "targetHTML": "Ceno <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mis amigos</span>.",
                "translation": "I have dinner with my friends.",
                "examples": [
                    {
                        "targetHTML": "Ceno <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mis amigos</span>.",
                        "translation": "I have dinner with my friends.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Hablé <span class='fw-token-connector'>con</span> <span class='fw-token-c'>el médico esta mañana</span>.",
                        "translation": "I spoke with the doctor this morning.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Vive <span class='fw-token-connector'>con</span> <span class='fw-token-c'>su familia en Granada</span>.",
                        "translation": "Lives with her family in Granada.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Salimos <span class='fw-token-connector'>con</span> <span class='fw-token-c'>los compañeros de clase</span>.",
                        "translation": "We went out with classmates.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Trabajo a diario <span class='fw-token-connector'>con</span> <span class='fw-token-c'>un equipo excelente</span>.",
                        "translation": "I work daily with an excellent team.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Instrument and Manner",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">con</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                "rule": "Instrument and attitude: describes the tool used or care applied.",
                "allowed_lemmas": [
                    "escribir",
                    "abrir",
                    "escuchar",
                    "cortar",
                    "tratar"
                ],
                "targetHTML": "Escribo <span class='fw-token-connector'>con</span> <span class='fw-token-c'>cuidado</span>.",
                "translation": "I write with care.",
                "examples": [
                    {
                        "targetHTML": "Escribo <span class='fw-token-connector'>con</span> <span class='fw-token-c'>cuidado</span>.",
                        "translation": "I write with care.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Abrió la caja <span class='fw-token-connector'>con</span> <span class='fw-token-c'>unas tijeras</span>.",
                        "translation": "Opened the box with scissors.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Escuchó la noticia <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mucha sorpresa</span>.",
                        "translation": "Listened to the news with great surprise.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Cortó el pan <span class='fw-token-connector'>con</span> <span class='fw-token-c'>un cuchillo afilado</span>.",
                        "translation": "Cut the bread with a sharp knife.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Trató el tema <span class='fw-token-connector'>con</span> <span class='fw-token-c'>máxima seriedad</span>.",
                        "translation": "Treated the subject with utmost seriousness.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Accompaniment",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">con</span> + <span class=\"fw-token-c\">Companion</span>",
                "rule": "Accompaniment: joins an action to the companion sharing it.",
                "allowed_lemmas": [
                    "cenar",
                    "hablar",
                    "salir",
                    "vivir",
                    "trabajar"
                ],
                "targetHTML": "Ceno <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mis amigos</span>.",
                "translation": "I have dinner with my friends.",
                "examples": [
                    {
                        "targetHTML": "Ceno <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mis amigos</span>.",
                        "translation": "I have dinner with my friends.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Hablé <span class='fw-token-connector'>con</span> <span class='fw-token-c'>el médico esta mañana</span>.",
                        "translation": "I spoke with the doctor this morning.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Vive <span class='fw-token-connector'>con</span> <span class='fw-token-c'>su familia en Granada</span>.",
                        "translation": "Lives with her family in Granada.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Salimos <span class='fw-token-connector'>con</span> <span class='fw-token-c'>los compañeros de clase</span>.",
                        "translation": "We went out with classmates.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Trabajo a diario <span class='fw-token-connector'>con</span> <span class='fw-token-c'>un equipo excelente</span>.",
                        "translation": "I work daily with an excellent team.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Instrument and Manner",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">con</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                "rule": "Instrument and attitude: describes the tool used or care applied.",
                "allowed_lemmas": [
                    "escribir",
                    "abrir",
                    "escuchar",
                    "cortar",
                    "tratar"
                ],
                "targetHTML": "Escribo <span class='fw-token-connector'>con</span> <span class='fw-token-c'>cuidado</span>.",
                "translation": "I write with care.",
                "examples": [
                    {
                        "targetHTML": "Escribo <span class='fw-token-connector'>con</span> <span class='fw-token-c'>cuidado</span>.",
                        "translation": "I write with care.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Abrió la caja <span class='fw-token-connector'>con</span> <span class='fw-token-c'>unas tijeras</span>.",
                        "translation": "Opened the box with scissors.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Escuchó la noticia <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mucha sorpresa</span>.",
                        "translation": "Listened to the news with great surprise.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Cortó el pan <span class='fw-token-connector'>con</span> <span class='fw-token-c'>un cuchillo afilado</span>.",
                        "translation": "Cut the bread with a sharp knife.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Trató el tema <span class='fw-token-connector'>con</span> <span class='fw-token-c'>máxima seriedad</span>.",
                        "translation": "Treated the subject with utmost seriousness.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Absence / Omission",
                "formulaHTML": "<span class=\"fw-token-v\">Noun / Action</span> + <span class=\"fw-token-connector\">sin</span> + <span class=\"fw-token-c\">Missing Element</span>",
                "rule": "Privative preposition: marks absence, lack, or omission.",
                "allowed_lemmas": [
                    "azúcar",
                    "duda",
                    "miedo",
                    "prisa",
                    "problema"
                ],
                "targetHTML": "Café <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>azúcar</span>, por favor.",
                "translation": "Coffee without sugar, please.",
                "examples": [
                    {
                        "targetHTML": "Café <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>azúcar</span>, por favor.",
                        "translation": "Coffee without sugar, please.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Es, <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>duda</span>, la mejor elección.",
                        "translation": "It is, without doubt, the best choice.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Actuó <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>miedo ante el peligro</span>.",
                        "translation": "Acted without fear before danger.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Caminamos <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>prisa por el paseo</span>.",
                        "translation": "We walked without rush along the promenade.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Resolvieron el conflicto <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>ningún problema</span>.",
                        "translation": "They resolved the conflict without any problem.",
                        "source": "Dialogue"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Absence / Omission",
                "formulaHTML": "<span class=\"fw-token-v\">Noun / Action</span> + <span class=\"fw-token-connector\">sin</span> + <span class=\"fw-token-c\">Missing Element</span>",
                "rule": "Privative preposition: marks absence, lack, or omission.",
                "allowed_lemmas": [
                    "azúcar",
                    "duda",
                    "miedo",
                    "prisa",
                    "problema"
                ],
                "targetHTML": "Café <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>azúcar</span>, por favor.",
                "translation": "Coffee without sugar, please.",
                "examples": [
                    {
                        "targetHTML": "Café <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>azúcar</span>, por favor.",
                        "translation": "Coffee without sugar, please.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Es, <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>duda</span>, la mejor elección.",
                        "translation": "It is, without doubt, the best choice.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Actuó <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>miedo ante el peligro</span>.",
                        "translation": "Acted without fear before danger.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Caminamos <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>prisa por el paseo</span>.",
                        "translation": "We walked without rush along the promenade.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Resolvieron el conflicto <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>ningún problema</span>.",
                        "translation": "They resolved the conflict without any problem.",
                        "source": "Dialogue"
                    }
                ]
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
                "tag": "Reflexive Clitic",
                "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                "rule": "Reflexive clitic: action turns back upon the person doing it.",
                "allowed_lemmas": [
                    "lavar",
                    "mirar",
                    "sentir",
                    "levantar",
                    "vestir"
                ],
                "targetHTML": "Él <span class='fw-token-connector'>se</span> <span class='fw-token-v'>lava</span> la cara.",
                "translation": "He washes his face.",
                "examples": [
                    {
                        "targetHTML": "Él <span class='fw-token-connector'>se</span> <span class='fw-token-v'>lava</span> la cara.",
                        "translation": "He washes his face.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ella <span class='fw-token-connector'>se</span> <span class='fw-token-v'>miró</span> en el espejo.",
                        "translation": "She looked at herself in the mirror.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>siente</span> mucho más tranquilo ahora.",
                        "translation": "Feels much calmer now.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Los niños <span class='fw-token-connector'>se</span> <span class='fw-token-v'>levantaron</span> temprano.",
                        "translation": "The children got up early.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "El actor <span class='fw-token-connector'>se</span> <span class='fw-token-v'>vistió</span> con elegancia.",
                        "translation": "The actor dressed with elegance.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Impersonal / Passive",
                "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb (Passive/Impersonal)</span>",
                "rule": "Impersonal / Passive marker: signals general or collective truth ('one does').",
                "allowed_lemmas": [
                    "hablar",
                    "vender",
                    "comer",
                    "vivir",
                    "esperar"
                ],
                "targetHTML": "Aquí <span class='fw-token-connector'>se</span> <span class='fw-token-v'>habla</span> español.",
                "translation": "Spanish is spoken here.",
                "examples": [
                    {
                        "targetHTML": "Aquí <span class='fw-token-connector'>se</span> <span class='fw-token-v'>habla</span> español.",
                        "translation": "Spanish is spoken here.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>venden</span> libros antiguos.",
                        "translation": "Old books are sold here.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>come</span> muy bien en este restaurante.",
                        "translation": "One eats very well in this restaurant.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>vive</span> con tranquilidad en este pueblo.",
                        "translation": "One lives peacefully in this village.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>espera</span> una gran multitud hoy.",
                        "translation": "A large crowd is expected today.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Reflexive Clitic",
                "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                "rule": "Reflexive clitic: action turns back upon the person doing it.",
                "allowed_lemmas": [
                    "lavar",
                    "mirar",
                    "sentir",
                    "levantar",
                    "vestir"
                ],
                "targetHTML": "Él <span class='fw-token-connector'>se</span> <span class='fw-token-v'>lava</span> la cara.",
                "translation": "He washes his face.",
                "examples": [
                    {
                        "targetHTML": "Él <span class='fw-token-connector'>se</span> <span class='fw-token-v'>lava</span> la cara.",
                        "translation": "He washes his face.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Ella <span class='fw-token-connector'>se</span> <span class='fw-token-v'>miró</span> en el espejo.",
                        "translation": "She looked at herself in the mirror.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>siente</span> mucho más tranquilo ahora.",
                        "translation": "Feels much calmer now.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Los niños <span class='fw-token-connector'>se</span> <span class='fw-token-v'>levantaron</span> temprano.",
                        "translation": "The children got up early.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "El actor <span class='fw-token-connector'>se</span> <span class='fw-token-v'>vistió</span> con elegancia.",
                        "translation": "The actor dressed with elegance.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Impersonal / Passive",
                "formulaHTML": "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb (Passive/Impersonal)</span>",
                "rule": "Impersonal / Passive marker: signals general or collective truth ('one does').",
                "allowed_lemmas": [
                    "hablar",
                    "vender",
                    "comer",
                    "vivir",
                    "esperar"
                ],
                "targetHTML": "Aquí <span class='fw-token-connector'>se</span> <span class='fw-token-v'>habla</span> español.",
                "translation": "Spanish is spoken here.",
                "examples": [
                    {
                        "targetHTML": "Aquí <span class='fw-token-connector'>se</span> <span class='fw-token-v'>habla</span> español.",
                        "translation": "Spanish is spoken here.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>venden</span> libros antiguos.",
                        "translation": "Old books are sold here.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>come</span> muy bien en este restaurante.",
                        "translation": "One eats very well in this restaurant.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>vive</span> con tranquilidad en este pueblo.",
                        "translation": "One lives peacefully in this village.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>espera</span> una gran multitud hoy.",
                        "translation": "A large crowd is expected today.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">me</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 1st-person 'me / to me' receiving the verb action.",
                "allowed_lemmas": [
                    "llamar",
                    "ayudar",
                    "dar",
                    "decir",
                    "gustar"
                ],
                "targetHTML": "Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>llamó</span> por teléfono.",
                "translation": "She called me on the phone.",
                "examples": [
                    {
                        "targetHTML": "Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>llamó</span> por teléfono.",
                        "translation": "She called me on the phone.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "¿<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>puedes ayudar</span> un segundo?",
                        "translation": "Can you help me for a second?",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Él <span class='fw-token-connector'>me</span> <span class='fw-token-v'>dio</span> una excelente noticia.",
                        "translation": "He gave me great news.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>gusta</span> mucho este lugar.",
                        "translation": "I like this place very much.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>dijo</span> la verdad completa.",
                        "translation": "She told me the whole truth.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">me</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 1st-person 'me / to me' receiving the verb action.",
                "allowed_lemmas": [
                    "llamar",
                    "ayudar",
                    "dar",
                    "decir",
                    "gustar"
                ],
                "targetHTML": "Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>llamó</span> por teléfono.",
                "translation": "She called me on the phone.",
                "examples": [
                    {
                        "targetHTML": "Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>llamó</span> por teléfono.",
                        "translation": "She called me on the phone.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "¿<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>puedes ayudar</span> un segundo?",
                        "translation": "Can you help me for a second?",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Él <span class='fw-token-connector'>me</span> <span class='fw-token-v'>dio</span> una excelente noticia.",
                        "translation": "He gave me great news.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>gusta</span> mucho este lugar.",
                        "translation": "I like this place very much.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>dijo</span> la verdad completa.",
                        "translation": "She told me the whole truth.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">te</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 2nd-person 'you / to you' (informal).",
                "allowed_lemmas": [
                    "querer",
                    "ver",
                    "llamar",
                    "esperar",
                    "decir"
                ],
                "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>quiero</span> mucho.",
                "translation": "I love you very much.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>quiero</span> mucho.",
                        "translation": "I love you very much.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>vi</span> ayer en la plaza.",
                        "translation": "I saw you yesterday in the square.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>llamo</span> en cuanto llegue a casa.",
                        "translation": "I will call you as soon as I arrive home.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>esperamos</span> en la entrada del teatro.",
                        "translation": "We wait for you at the theatre entrance.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>deseo</span> lo mejor en tu examen.",
                        "translation": "I wish you the best in your exam.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">te</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 2nd-person 'you / to you' (informal).",
                "allowed_lemmas": [
                    "querer",
                    "ver",
                    "llamar",
                    "esperar",
                    "decir"
                ],
                "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>quiero</span> mucho.",
                "translation": "I love you very much.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>quiero</span> mucho.",
                        "translation": "I love you very much.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>vi</span> ayer en la plaza.",
                        "translation": "I saw you yesterday in the square.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>llamo</span> en cuanto llegue a casa.",
                        "translation": "I will call you as soon as I arrive home.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>esperamos</span> en la entrada del teatro.",
                        "translation": "We wait for you at the theatre entrance.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>deseo</span> lo mejor en tu examen.",
                        "translation": "I wish you the best in your exam.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">nos</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 1st-person plural 'us / to us'.",
                "allowed_lemmas": [
                    "enseñar",
                    "ver",
                    "invitar",
                    "esperar",
                    "ayudar"
                ],
                "targetHTML": "El profesor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>enseña</span> bien.",
                "translation": "The teacher teaches us well.",
                "examples": [
                    {
                        "targetHTML": "El profesor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>enseña</span> bien.",
                        "translation": "The teacher teaches us well.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ellos <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>invitaron</span> a cenar.",
                        "translation": "They invited us for dinner.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "El guía <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>mostró</span> la ciudad vieja.",
                        "translation": "The guide showed us the old city.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Un vecino <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ayudó</span> con el coche.",
                        "translation": "A neighbour helped us with the car.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Nos</span> <span class='fw-token-v'>alegramos</span> mucho de verte.",
                        "translation": "We are very glad to see you.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">nos</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Object pronoun: represents 1st-person plural 'us / to us'.",
                "allowed_lemmas": [
                    "enseñar",
                    "ver",
                    "invitar",
                    "esperar",
                    "ayudar"
                ],
                "targetHTML": "El profesor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>enseña</span> bien.",
                "translation": "The teacher teaches us well.",
                "examples": [
                    {
                        "targetHTML": "El profesor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>enseña</span> bien.",
                        "translation": "The teacher teaches us well.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Ellos <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>invitaron</span> a cenar.",
                        "translation": "They invited us for dinner.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "El guía <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>mostró</span> la ciudad vieja.",
                        "translation": "The guide showed us the old city.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Un vecino <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ayudó</span> con el coche.",
                        "translation": "A neighbour helped us with the car.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Nos</span> <span class='fw-token-v'>alegramos</span> mucho de verte.",
                        "translation": "We are very glad to see you.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Indirect Object",
                "formulaHTML": "<span class=\"fw-token-connector\">le</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Indirect object pronoun: represents 3rd-person singular 'to him / to her / to you'.",
                "allowed_lemmas": [
                    "escribir",
                    "dar",
                    "preguntar",
                    "decir",
                    "entregar"
                ],
                "targetHTML": "Yo <span class='fw-token-connector'>le</span> <span class='fw-token-v'>escribí</span> una carta.",
                "translation": "I wrote him a letter.",
                "examples": [
                    {
                        "targetHTML": "Yo <span class='fw-token-connector'>le</span> <span class='fw-token-v'>escribí</span> una carta.",
                        "translation": "I wrote him a letter.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Le</span> <span class='fw-token-v'>entregué</span> las llaves a la recepcionista.",
                        "translation": "I handed the keys to the receptionist.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "El médico <span class='fw-token-connector'>le</span> <span class='fw-token-v'>recetó</span> descanso.",
                        "translation": "The doctor prescribed him rest.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Le</span> <span class='fw-token-v'>pregunté</span> la hora amablemente.",
                        "translation": "I asked her the time politely.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Nadie <span class='fw-token-connector'>le</span> <span class='fw-token-v'>dijo</span> nada sobre el cambio.",
                        "translation": "Nobody told him anything about the change.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Indirect Object",
                "formulaHTML": "<span class=\"fw-token-connector\">le</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Indirect object pronoun: represents 3rd-person singular 'to him / to her / to you'.",
                "allowed_lemmas": [
                    "escribir",
                    "dar",
                    "preguntar",
                    "decir",
                    "entregar"
                ],
                "targetHTML": "Yo <span class='fw-token-connector'>le</span> <span class='fw-token-v'>escribí</span> una carta.",
                "translation": "I wrote him a letter.",
                "examples": [
                    {
                        "targetHTML": "Yo <span class='fw-token-connector'>le</span> <span class='fw-token-v'>escribí</span> una carta.",
                        "translation": "I wrote him a letter.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Le</span> <span class='fw-token-v'>entregué</span> las llaves a la recepcionista.",
                        "translation": "I handed the keys to the receptionist.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "El médico <span class='fw-token-connector'>le</span> <span class='fw-token-v'>recetó</span> descanso.",
                        "translation": "The doctor prescribed him rest.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Le</span> <span class='fw-token-v'>pregunté</span> la hora amablemente.",
                        "translation": "I asked her the time politely.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Nadie <span class='fw-token-connector'>le</span> <span class='fw-token-v'>dijo</span> nada sobre el cambio.",
                        "translation": "Nobody told him anything about the change.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Direction / Goal",
                "formulaHTML": "<span class=\"fw-token-connector\">a + el</span> + <span class=\"fw-token-c\">Masculine Destination</span>",
                "rule": "Mandatory contraction of 'a + el' (to the / at the) before masculine nouns.",
                "allowed_lemmas": [
                    "cine",
                    "parque",
                    "médico",
                    "trabajo",
                    "aeropuerto"
                ],
                "targetHTML": "Vamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>cine</span> esta noche.",
                "translation": "We are going to the cinema tonight.",
                "examples": [
                    {
                        "targetHTML": "Vamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>cine</span> esta noche.",
                        "translation": "We are going to the cinema tonight.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Llegamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>parque al atardecer</span>.",
                        "translation": "We arrived at the park at sunset.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Tuve que ir <span class='fw-token-connector'>al</span> <span class='fw-token-c'>médico por la mañana</span>.",
                        "translation": "I had to go to the doctor in the morning.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Acompañó a su abuelo <span class='fw-token-connector'>al</span> <span class='fw-token-c'>aeropuerto</span>.",
                        "translation": "Accompanied his grandfather to the airport.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Volvieron <span class='fw-token-connector'>al</span> <span class='fw-token-c'>trabajo con energía</span>.",
                        "translation": "They returned to work with energy.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Temporal Nexus",
                "formulaHTML": "<span class=\"fw-token-connector\">al</span> + <span class=\"fw-token-v\">Infinitive</span>",
                "rule": "Temporal nexus: expresses 'upon doing' or 'when doing'.",
                "allowed_lemmas": [
                    "llegar",
                    "salir",
                    "abrir",
                    "oír",
                    "ver"
                ],
                "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>llegar</span> a casa, descansé.",
                "translation": "Upon arriving home, I rested.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>llegar</span> a casa, descansé.",
                        "translation": "Upon arriving home, I rested.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>oír</span> la campana, salieron todos.",
                        "translation": "Upon hearing the bell, everyone left.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Sonrió <span class='fw-token-connector'>al</span> <span class='fw-token-v'>ver</span> la sorpresa preparada.",
                        "translation": "Smiled upon seeing the surprise prepared.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>abrir</span> la ventana entró aire fresco.",
                        "translation": "Upon opening the window, fresh air entered.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>terminar</span> el discurso, todos aplaudieron.",
                        "translation": "Upon finishing the speech, everyone applauded.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Direction / Goal",
                "formulaHTML": "<span class=\"fw-token-connector\">a + el</span> + <span class=\"fw-token-c\">Masculine Destination</span>",
                "rule": "Mandatory contraction of 'a + el' (to the / at the) before masculine nouns.",
                "allowed_lemmas": [
                    "cine",
                    "parque",
                    "médico",
                    "trabajo",
                    "aeropuerto"
                ],
                "targetHTML": "Vamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>cine</span> esta noche.",
                "translation": "We are going to the cinema tonight.",
                "examples": [
                    {
                        "targetHTML": "Vamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>cine</span> esta noche.",
                        "translation": "We are going to the cinema tonight.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Llegamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>parque al atardecer</span>.",
                        "translation": "We arrived at the park at sunset.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Tuve que ir <span class='fw-token-connector'>al</span> <span class='fw-token-c'>médico por la mañana</span>.",
                        "translation": "I had to go to the doctor in the morning.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Acompañó a su abuelo <span class='fw-token-connector'>al</span> <span class='fw-token-c'>aeropuerto</span>.",
                        "translation": "Accompanied his grandfather to the airport.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Volvieron <span class='fw-token-connector'>al</span> <span class='fw-token-c'>trabajo con energía</span>.",
                        "translation": "They returned to work with energy.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Temporal Nexus",
                "formulaHTML": "<span class=\"fw-token-connector\">al</span> + <span class=\"fw-token-v\">Infinitive</span>",
                "rule": "Temporal nexus: expresses 'upon doing' or 'when doing'.",
                "allowed_lemmas": [
                    "llegar",
                    "salir",
                    "abrir",
                    "oír",
                    "ver"
                ],
                "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>llegar</span> a casa, descansé.",
                "translation": "Upon arriving home, I rested.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>llegar</span> a casa, descansé.",
                        "translation": "Upon arriving home, I rested.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>oír</span> la campana, salieron todos.",
                        "translation": "Upon hearing the bell, everyone left.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Sonrió <span class='fw-token-connector'>al</span> <span class='fw-token-v'>ver</span> la sorpresa preparada.",
                        "translation": "Smiled upon seeing the surprise prepared.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>abrir</span> la ventana entró aire fresco.",
                        "translation": "Upon opening the window, fresh air entered.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>terminar</span> el discurso, todos aplaudieron.",
                        "translation": "Upon finishing the speech, everyone applauded.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Origin / Attribute",
                "formulaHTML": "<span class=\"fw-token-connector\">de + el</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                "rule": "Mandatory contraction of 'de + el' (of the / from the).",
                "allowed_lemmas": [
                    "hotel",
                    "libro",
                    "mundo",
                    "edificio",
                    "río"
                ],
                "targetHTML": "La puerta <span class='fw-token-connector'>del</span> <span class='fw-token-c'>hotel</span> está cerrada.",
                "translation": "The door of the hotel is closed.",
                "examples": [
                    {
                        "targetHTML": "La puerta <span class='fw-token-connector'>del</span> <span class='fw-token-c'>hotel</span> está cerrada.",
                        "translation": "The door of the hotel is closed.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "El final <span class='fw-token-connector'>del</span> <span class='fw-token-c'>libro fue emocionante</span>.",
                        "translation": "The end of the book was exciting.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Viene <span class='fw-token-connector'>del</span> <span class='fw-token-c'>centro en bicicleta</span>.",
                        "translation": "Comes from downtown by bicycle.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Es una de las maravillas <span class='fw-token-connector'>del</span> <span class='fw-token-c'>mundo</span>.",
                        "translation": "It is one of the wonders of the world.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "La vista <span class='fw-token-connector'>del</span> <span class='fw-token-c'>valle nos impresionó</span>.",
                        "translation": "The view of the valley impressed us.",
                        "source": "Dialogue"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Origin / Attribute",
                "formulaHTML": "<span class=\"fw-token-connector\">de + el</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                "rule": "Mandatory contraction of 'de + el' (of the / from the).",
                "allowed_lemmas": [
                    "hotel",
                    "libro",
                    "mundo",
                    "edificio",
                    "río"
                ],
                "targetHTML": "La puerta <span class='fw-token-connector'>del</span> <span class='fw-token-c'>hotel</span> está cerrada.",
                "translation": "The door of the hotel is closed.",
                "examples": [
                    {
                        "targetHTML": "La puerta <span class='fw-token-connector'>del</span> <span class='fw-token-c'>hotel</span> está cerrada.",
                        "translation": "The door of the hotel is closed.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "El final <span class='fw-token-connector'>del</span> <span class='fw-token-c'>libro fue emocionante</span>.",
                        "translation": "The end of the book was exciting.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Viene <span class='fw-token-connector'>del</span> <span class='fw-token-c'>centro en bicicleta</span>.",
                        "translation": "Comes from downtown by bicycle.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Es una de las maravillas <span class='fw-token-connector'>del</span> <span class='fw-token-c'>mundo</span>.",
                        "translation": "It is one of the wonders of the world.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "La vista <span class='fw-token-connector'>del</span> <span class='fw-token-c'>valle nos impresionó</span>.",
                        "translation": "The view of the valley impressed us.",
                        "source": "Dialogue"
                    }
                ]
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
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">el</span> + <span class=\"fw-token-c\">Masculine Singular Noun</span>",
                "rule": "Definite article: designates a specific masculine singular referent.",
                "allowed_lemmas": [
                    "sol",
                    "coche",
                    "día",
                    "tren",
                    "tiempo"
                ],
                "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>sol</span> brilla en el cielo.",
                "translation": "The sun shines in the sky.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>sol</span> brilla en el cielo.",
                        "translation": "The sun shines in the sky.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>coche nuevo</span> consume poca gasolina.",
                        "translation": "The new car consumes little petrol.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>tren de las ocho</span> ya partió.",
                        "translation": "The eight o'clock train already left.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>tiempo</span> pasa muy rápido aquí.",
                        "translation": "Time passes very quickly here.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>viento</span> soplaba suavemente entre los árboles.",
                        "translation": "The wind blew gently among the trees.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">el</span> + <span class=\"fw-token-c\">Masculine Singular Noun</span>",
                "rule": "Definite article: designates a specific masculine singular referent.",
                "allowed_lemmas": [
                    "sol",
                    "coche",
                    "día",
                    "tren",
                    "tiempo"
                ],
                "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>sol</span> brilla en el cielo.",
                "translation": "The sun shines in the sky.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>sol</span> brilla en el cielo.",
                        "translation": "The sun shines in the sky.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>coche nuevo</span> consume poca gasolina.",
                        "translation": "The new car consumes little petrol.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>tren de las ocho</span> ya partió.",
                        "translation": "The eight o'clock train already left.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>tiempo</span> pasa muy rápido aquí.",
                        "translation": "Time passes very quickly here.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>El</span> <span class='fw-token-c'>viento</span> soplaba suavemente entre los árboles.",
                        "translation": "The wind blew gently among the trees.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">la</span> + <span class=\"fw-token-c\">Feminine Singular Noun</span>",
                "rule": "Definite article: designates a specific feminine singular referent.",
                "allowed_lemmas": [
                    "puerta",
                    "casa",
                    "ciudad",
                    "noche",
                    "vida"
                ],
                "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>puerta</span> está abierta.",
                "translation": "The door is open.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>puerta</span> está abierta.",
                        "translation": "The door is open.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>casa de campo</span> tiene un gran jardín.",
                        "translation": "The country house has a large garden.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>ciudad</span> duerme bajo las estrellas.",
                        "translation": "The city sleeps under the stars.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>noche</span> era serena y estrellada.",
                        "translation": "The night was serene and starry.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>música</span> llenaba todo el salón.",
                        "translation": "The music filled the entire hall.",
                        "source": "Dialogue"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">la</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Direct object pronoun: replaces a 3rd-person feminine singular noun ('her / it').",
                "allowed_lemmas": [
                    "ver",
                    "conocer",
                    "esperar",
                    "llamar",
                    "escuchar"
                ],
                "targetHTML": "Yo <span class='fw-token-connector'>la</span> <span class='fw-token-v'>vi</span> ayer en el mercado.",
                "translation": "I saw her yesterday at the market.",
                "examples": [
                    {
                        "targetHTML": "Yo <span class='fw-token-connector'>la</span> <span class='fw-token-v'>vi</span> ayer en el mercado.",
                        "translation": "I saw her yesterday at the market.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "No <span class='fw-token-connector'>la</span> <span class='fw-token-v'>conozco</span> en persona todavía.",
                        "translation": "I don't know her in person yet.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-v'>llamé</span> para avisarle del retraso.",
                        "translation": "I called her to notify her of the delay.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Todos <span class='fw-token-connector'>la</span> <span class='fw-token-v'>escucharon</span> con respeto.",
                        "translation": "Everyone listened to her with respect.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "La llave estaba perdida, pero por fin <span class='fw-token-connector'>la</span> <span class='fw-token-v'>encontré</span>.",
                        "translation": "The key was lost, but at last I found it.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">la</span> + <span class=\"fw-token-c\">Feminine Singular Noun</span>",
                "rule": "Definite article: designates a specific feminine singular referent.",
                "allowed_lemmas": [
                    "puerta",
                    "casa",
                    "ciudad",
                    "noche",
                    "vida"
                ],
                "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>puerta</span> está abierta.",
                "translation": "The door is open.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>puerta</span> está abierta.",
                        "translation": "The door is open.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>casa de campo</span> tiene un gran jardín.",
                        "translation": "The country house has a large garden.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>ciudad</span> duerme bajo las estrellas.",
                        "translation": "The city sleeps under the stars.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>noche</span> era serena y estrellada.",
                        "translation": "The night was serene and starry.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-c'>música</span> llenaba todo el salón.",
                        "translation": "The music filled the entire hall.",
                        "source": "Dialogue"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">la</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Direct object pronoun: replaces a 3rd-person feminine singular noun ('her / it').",
                "allowed_lemmas": [
                    "ver",
                    "conocer",
                    "esperar",
                    "llamar",
                    "escuchar"
                ],
                "targetHTML": "Yo <span class='fw-token-connector'>la</span> <span class='fw-token-v'>vi</span> ayer en el mercado.",
                "translation": "I saw her yesterday at the market.",
                "examples": [
                    {
                        "targetHTML": "Yo <span class='fw-token-connector'>la</span> <span class='fw-token-v'>vi</span> ayer en el mercado.",
                        "translation": "I saw her yesterday at the market.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "No <span class='fw-token-connector'>la</span> <span class='fw-token-v'>conozco</span> en persona todavía.",
                        "translation": "I don't know her in person yet.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>La</span> <span class='fw-token-v'>llamé</span> para avisarle del retraso.",
                        "translation": "I called her to notify her of the delay.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Todos <span class='fw-token-connector'>la</span> <span class='fw-token-v'>escucharon</span> con respeto.",
                        "translation": "Everyone listened to her with respect.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "La llave estaba perdida, pero por fin <span class='fw-token-connector'>la</span> <span class='fw-token-v'>encontré</span>.",
                        "translation": "The key was lost, but at last I found it.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">los</span> + <span class=\"fw-token-c\">Masculine Plural Noun</span>",
                "rule": "Definite article: designates specific masculine plural entities.",
                "allowed_lemmas": [
                    "niños",
                    "libros",
                    "días",
                    "amigos",
                    "árboles"
                ],
                "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>niños</span> juegan fuera.",
                "translation": "The children play outside.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>niños</span> juegan fuera.",
                        "translation": "The children play outside.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>libros</span> estaban colocados en orden.",
                        "translation": "The books were arranged in order.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>días soleados</span> son mis favoritos.",
                        "translation": "Sunny days are my favorites.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>amigos</span> se reunieron para celebrar.",
                        "translation": "The friends met to celebrate.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>pájaros</span> cantaban al amanecer.",
                        "translation": "The birds sang at dawn.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">los</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Direct object pronoun: replaces 3rd-person masculine plural objects ('them').",
                "allowed_lemmas": [
                    "comprar",
                    "ver",
                    "conocer",
                    "recoger",
                    "dejar"
                ],
                "targetHTML": "Yo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>compré</span> ayer en la tienda.",
                "translation": "I bought them yesterday at the shop.",
                "examples": [
                    {
                        "targetHTML": "Yo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>compré</span> ayer en la tienda.",
                        "translation": "I bought them yesterday at the shop.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "No <span class='fw-token-connector'>los</span> <span class='fw-token-v'>he visto</span> en toda la semana.",
                        "translation": "I haven't seen them all week.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-v'>recogí</span> de la estación a tiempo.",
                        "translation": "I picked them up from the station in time.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Si encuentras los papeles, <span class='fw-token-connector'>los</span> <span class='fw-token-v'>dejas</span> aquí.",
                        "translation": "If you find the papers, leave them here.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "El abuelo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>abrazó</span> con emoción.",
                        "translation": "The grandfather hugged them with emotion.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">los</span> + <span class=\"fw-token-c\">Masculine Plural Noun</span>",
                "rule": "Definite article: designates specific masculine plural entities.",
                "allowed_lemmas": [
                    "niños",
                    "libros",
                    "días",
                    "amigos",
                    "árboles"
                ],
                "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>niños</span> juegan fuera.",
                "translation": "The children play outside.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>niños</span> juegan fuera.",
                        "translation": "The children play outside.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>libros</span> estaban colocados en orden.",
                        "translation": "The books were arranged in order.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>días soleados</span> son mis favoritos.",
                        "translation": "Sunny days are my favorites.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>amigos</span> se reunieron para celebrar.",
                        "translation": "The friends met to celebrate.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>pájaros</span> cantaban al amanecer.",
                        "translation": "The birds sang at dawn.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">los</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Direct object pronoun: replaces 3rd-person masculine plural objects ('them').",
                "allowed_lemmas": [
                    "comprar",
                    "ver",
                    "conocer",
                    "recoger",
                    "dejar"
                ],
                "targetHTML": "Yo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>compré</span> ayer en la tienda.",
                "translation": "I bought them yesterday at the shop.",
                "examples": [
                    {
                        "targetHTML": "Yo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>compré</span> ayer en la tienda.",
                        "translation": "I bought them yesterday at the shop.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "No <span class='fw-token-connector'>los</span> <span class='fw-token-v'>he visto</span> en toda la semana.",
                        "translation": "I haven't seen them all week.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Los</span> <span class='fw-token-v'>recogí</span> de la estación a tiempo.",
                        "translation": "I picked them up from the station in time.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Si encuentras los papeles, <span class='fw-token-connector'>los</span> <span class='fw-token-v'>dejas</span> aquí.",
                        "translation": "If you find the papers, leave them here.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "El abuelo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>abrazó</span> con emoción.",
                        "translation": "The grandfather hugged them with emotion.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">las</span> + <span class=\"fw-token-c\">Feminine Plural Noun</span>",
                "rule": "Definite article: designates specific feminine plural entities.",
                "allowed_lemmas": [
                    "llaves",
                    "flores",
                    "cosas",
                    "personas",
                    "calles"
                ],
                "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>llaves</span> están en la mesa.",
                "translation": "The keys are on the table.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>llaves</span> están en la mesa.",
                        "translation": "The keys are on the table.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>flores del patio</span> huelen de maravilla.",
                        "translation": "The courtyard flowers smell wonderful.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>calles</span> estaban llenas de luces navideñas.",
                        "translation": "The streets were full of Christmas lights.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>personas</span> escuchaban con atención.",
                        "translation": "The people listened with attention.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Hay que poner <span class='fw-token-connector'>las</span> <span class='fw-token-c'>cosas</span> en su sitio.",
                        "translation": "One must put things in their place.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Definite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">las</span> + <span class=\"fw-token-c\">Feminine Plural Noun</span>",
                "rule": "Definite article: designates specific feminine plural entities.",
                "allowed_lemmas": [
                    "llaves",
                    "flores",
                    "cosas",
                    "personas",
                    "calles"
                ],
                "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>llaves</span> están en la mesa.",
                "translation": "The keys are on the table.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>llaves</span> están en la mesa.",
                        "translation": "The keys are on the table.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>flores del patio</span> huelen de maravilla.",
                        "translation": "The courtyard flowers smell wonderful.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>calles</span> estaban llenas de luces navideñas.",
                        "translation": "The streets were full of Christmas lights.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>personas</span> escuchaban con atención.",
                        "translation": "The people listened with attention.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Hay que poner <span class='fw-token-connector'>las</span> <span class='fw-token-c'>cosas</span> en su sitio.",
                        "translation": "One must put things in their place.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Neuter Article",
                "formulaHTML": "<span class=\"fw-token-connector\">lo</span> + <span class=\"fw-token-c\">Adjective / Abstract</span>",
                "rule": "Neuter article: nominalizes an adjective into an abstract quality ('the ... thing').",
                "allowed_lemmas": [
                    "importante",
                    "bueno",
                    "malo",
                    "mejor",
                    "difícil"
                ],
                "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>importante</span> es participar.",
                "translation": "The important thing is to participate.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>importante</span> es participar.",
                        "translation": "The important thing is to participate.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>bueno</span> es que tenemos tiempo de sobra.",
                        "translation": "The good thing is that we have plenty of time.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>difícil</span> ya ha pasado.",
                        "translation": "The difficult part has already passed.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Hizo <span class='fw-token-connector'>lo</span> <span class='fw-token-c'>mejor</span> que pudo dadas las circunstancias.",
                        "translation": "Did the best that he could given the circumstances.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>curioso</span> es que nadie notó la diferencia.",
                        "translation": "The curious thing is that nobody noticed the difference.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">lo</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Direct object pronoun: replaces a masculine singular item or concept ('it / him').",
                "allowed_lemmas": [
                    "saber",
                    "ver",
                    "hacer",
                    "tener",
                    "entender"
                ],
                "targetHTML": "Ya <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>sé</span>.",
                "translation": "I already know it.",
                "examples": [
                    {
                        "targetHTML": "Ya <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>sé</span>.",
                        "translation": "I already know it.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "No <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>entiendo</span> con claridad.",
                        "translation": "I do not understand it clearly.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "¿<span class='fw-token-connector'>Lo</span> <span class='fw-token-v'>has visto</span> por aquí?",
                        "translation": "Have you seen him around here?",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-v'>hice</span> exactamente como me pediste.",
                        "translation": "I did it exactly as you asked me.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Si tienes el informe, <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>leo</span> esta noche.",
                        "translation": "If you have the report, I'll read it tonight.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Neuter Article",
                "formulaHTML": "<span class=\"fw-token-connector\">lo</span> + <span class=\"fw-token-c\">Adjective / Abstract</span>",
                "rule": "Neuter article: nominalizes an adjective into an abstract quality ('the ... thing').",
                "allowed_lemmas": [
                    "importante",
                    "bueno",
                    "malo",
                    "mejor",
                    "difícil"
                ],
                "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>importante</span> es participar.",
                "translation": "The important thing is to participate.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>importante</span> es participar.",
                        "translation": "The important thing is to participate.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>bueno</span> es que tenemos tiempo de sobra.",
                        "translation": "The good thing is that we have plenty of time.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>difícil</span> ya ha pasado.",
                        "translation": "The difficult part has already passed.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Hizo <span class='fw-token-connector'>lo</span> <span class='fw-token-c'>mejor</span> que pudo dadas las circunstancias.",
                        "translation": "Did the best that he could given the circumstances.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>curioso</span> es que nadie notó la diferencia.",
                        "translation": "The curious thing is that nobody noticed the difference.",
                        "source": "Literature"
                    }
                ]
            },
            {
                "tag": "Direct Object Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">lo</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Direct object pronoun: replaces a masculine singular item or concept ('it / him').",
                "allowed_lemmas": [
                    "saber",
                    "ver",
                    "hacer",
                    "tener",
                    "entender"
                ],
                "targetHTML": "Ya <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>sé</span>.",
                "translation": "I already know it.",
                "examples": [
                    {
                        "targetHTML": "Ya <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>sé</span>.",
                        "translation": "I already know it.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "No <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>entiendo</span> con claridad.",
                        "translation": "I do not understand it clearly.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "¿<span class='fw-token-connector'>Lo</span> <span class='fw-token-v'>has visto</span> por aquí?",
                        "translation": "Have you seen him around here?",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Lo</span> <span class='fw-token-v'>hice</span> exactamente como me pediste.",
                        "translation": "I did it exactly as you asked me.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Si tienes el informe, <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>leo</span> esta noche.",
                        "translation": "If you have the report, I'll read it tonight.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Indefinite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">un</span> + <span class=\"fw-token-c\">Masculine Singular Noun</span>",
                "rule": "Indefinite article: introduces a single unspecific masculine noun.",
                "allowed_lemmas": [
                    "amigo",
                    "día",
                    "libro",
                    "café",
                    "coche"
                ],
                "targetHTML": "Tengo <span class='fw-token-connector'>un</span> <span class='fw-token-c'>amigo</span> en Madrid.",
                "translation": "I have a friend in Madrid.",
                "examples": [
                    {
                        "targetHTML": "Tengo <span class='fw-token-connector'>un</span> <span class='fw-token-c'>amigo</span> en Madrid.",
                        "translation": "I have a friend in Madrid.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Tomemos <span class='fw-token-connector'>un</span> <span class='fw-token-c'>café caliente juntos</span>.",
                        "translation": "Let's have a warm coffee together.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Compré <span class='fw-token-connector'>un</span> <span class='fw-token-c'>libro muy interesante</span>.",
                        "translation": "I bought a very interesting book.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Fue <span class='fw-token-connector'>un</span> <span class='fw-token-c'>día inolvidable para todos</span>.",
                        "translation": "It was an unforgettable day for everyone.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Buscamos <span class='fw-token-connector'>un</span> <span class='fw-token-c'>lugar tranquilo para charlar</span>.",
                        "translation": "We are looking for a quiet place to chat.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Indefinite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">un</span> + <span class=\"fw-token-c\">Masculine Singular Noun</span>",
                "rule": "Indefinite article: introduces a single unspecific masculine noun.",
                "allowed_lemmas": [
                    "amigo",
                    "día",
                    "libro",
                    "café",
                    "coche"
                ],
                "targetHTML": "Tengo <span class='fw-token-connector'>un</span> <span class='fw-token-c'>amigo</span> en Madrid.",
                "translation": "I have a friend in Madrid.",
                "examples": [
                    {
                        "targetHTML": "Tengo <span class='fw-token-connector'>un</span> <span class='fw-token-c'>amigo</span> en Madrid.",
                        "translation": "I have a friend in Madrid.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Tomemos <span class='fw-token-connector'>un</span> <span class='fw-token-c'>café caliente juntos</span>.",
                        "translation": "Let's have a warm coffee together.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Compré <span class='fw-token-connector'>un</span> <span class='fw-token-c'>libro muy interesante</span>.",
                        "translation": "I bought a very interesting book.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Fue <span class='fw-token-connector'>un</span> <span class='fw-token-c'>día inolvidable para todos</span>.",
                        "translation": "It was an unforgettable day for everyone.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Buscamos <span class='fw-token-connector'>un</span> <span class='fw-token-c'>lugar tranquilo para charlar</span>.",
                        "translation": "We are looking for a quiet place to chat.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Indefinite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">una</span> + <span class=\"fw-token-c\">Feminine Singular Noun</span>",
                "rule": "Indefinite article: introduces a single unspecific feminine noun.",
                "allowed_lemmas": [
                    "idea",
                    "casa",
                    "pregunta",
                    "semana",
                    "historia"
                ],
                "targetHTML": "Es <span class='fw-token-connector'>una</span> <span class='fw-token-c'>buena idea</span>.",
                "translation": "It is a good idea.",
                "examples": [
                    {
                        "targetHTML": "Es <span class='fw-token-connector'>una</span> <span class='fw-token-c'>buena idea</span>.",
                        "translation": "It is a good idea.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Alquilamos <span class='fw-token-connector'>una</span> <span class='fw-token-c'>casa cerca de la playa</span>.",
                        "translation": "We rented a house near the beach.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Quiero hacer <span class='fw-token-connector'>una</span> <span class='fw-token-c'>pregunta rápida</span>.",
                        "translation": "I want to ask a quick question.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Contó <span class='fw-token-connector'>una</span> <span class='fw-token-c'>historia emocionante</span>.",
                        "translation": "Told an exciting story.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Esperamos durante <span class='fw-token-connector'>una</span> <span class='fw-token-c'>semana entera</span>.",
                        "translation": "We waited for a whole week.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Indefinite Article",
                "formulaHTML": "<span class=\"fw-token-connector\">una</span> + <span class=\"fw-token-c\">Feminine Singular Noun</span>",
                "rule": "Indefinite article: introduces a single unspecific feminine noun.",
                "allowed_lemmas": [
                    "idea",
                    "casa",
                    "pregunta",
                    "semana",
                    "historia"
                ],
                "targetHTML": "Es <span class='fw-token-connector'>una</span> <span class='fw-token-c'>buena idea</span>.",
                "translation": "It is a good idea.",
                "examples": [
                    {
                        "targetHTML": "Es <span class='fw-token-connector'>una</span> <span class='fw-token-c'>buena idea</span>.",
                        "translation": "It is a good idea.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Alquilamos <span class='fw-token-connector'>una</span> <span class='fw-token-c'>casa cerca de la playa</span>.",
                        "translation": "We rented a house near the beach.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Quiero hacer <span class='fw-token-connector'>una</span> <span class='fw-token-c'>pregunta rápida</span>.",
                        "translation": "I want to ask a quick question.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Contó <span class='fw-token-connector'>una</span> <span class='fw-token-c'>historia emocionante</span>.",
                        "translation": "Told an exciting story.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Esperamos durante <span class='fw-token-connector'>una</span> <span class='fw-token-c'>semana entera</span>.",
                        "translation": "We waited for a whole week.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Addition",
                "formulaHTML": "<span class=\"fw-token-v\">Element</span> + <span class=\"fw-token-connector\">y</span> + <span class=\"fw-token-c\">Addition</span>",
                "rule": "Copulative conjunction: coordinates items, clauses, or thoughts of equal status.",
                "allowed_lemmas": [
                    "pan",
                    "leche",
                    "entrar",
                    "abrir",
                    "cantar",
                    "bailar"
                ],
                "targetHTML": "Compré pan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>leche</span>.",
                "translation": "I bought bread and milk.",
                "examples": [
                    {
                        "targetHTML": "Compré pan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>leche</span>.",
                        "translation": "I bought bread and milk.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Se levantó temprano <span class='fw-token-connector'>y</span> <span class='fw-token-c'>salió a correr</span>.",
                        "translation": "Got up early and went out to run.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Cantan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>bailan con alegría</span>.",
                        "translation": "They sing and dance with joy.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "El día era fresco <span class='fw-token-connector'>y</span> <span class='fw-token-c'>despejado</span>.",
                        "translation": "The day was cool and clear.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Escuchó la pregunta <span class='fw-token-connector'>y</span> <span class='fw-token-c'>asintió en silencio</span>.",
                        "translation": "Heard the question and nodded in silence.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Addition",
                "formulaHTML": "<span class=\"fw-token-v\">Element</span> + <span class=\"fw-token-connector\">y</span> + <span class=\"fw-token-c\">Addition</span>",
                "rule": "Copulative conjunction: coordinates items, clauses, or thoughts of equal status.",
                "allowed_lemmas": [
                    "pan",
                    "leche",
                    "entrar",
                    "abrir",
                    "cantar",
                    "bailar"
                ],
                "targetHTML": "Compré pan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>leche</span>.",
                "translation": "I bought bread and milk.",
                "examples": [
                    {
                        "targetHTML": "Compré pan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>leche</span>.",
                        "translation": "I bought bread and milk.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Se levantó temprano <span class='fw-token-connector'>y</span> <span class='fw-token-c'>salió a correr</span>.",
                        "translation": "Got up early and went out to run.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Cantan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>bailan con alegría</span>.",
                        "translation": "They sing and dance with joy.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "El día era fresco <span class='fw-token-connector'>y</span> <span class='fw-token-c'>despejado</span>.",
                        "translation": "The day was cool and clear.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Escuchó la pregunta <span class='fw-token-connector'>y</span> <span class='fw-token-c'>asintió en silencio</span>.",
                        "translation": "Heard the question and nodded in silence.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Contrast",
                "formulaHTML": "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">pero</span> + <span class=\"fw-token-c\">Contrast</span>",
                "rule": "Adversative bridge: introduces a qualification, limitation, or unexpected contrast.",
                "allowed_lemmas": [
                    "salir",
                    "querer",
                    "intentar",
                    "saber",
                    "buscar"
                ],
                "targetHTML": "Quería salir, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>llovía</span>.",
                "translation": "I wanted to go out, but it was raining.",
                "examples": [
                    {
                        "targetHTML": "Quería salir, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>llovía</span>.",
                        "translation": "I wanted to go out, but it was raining.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Lo intenté con todas mis fuerzas, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>no pude</span>.",
                        "translation": "I tried with all my might, but couldn't.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Sabía la lección, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>se puso nervioso</span>.",
                        "translation": "Knew the lesson, but got nervous.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Es caro, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>vale la pena</span>.",
                        "translation": "It is expensive, but worth it.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Buscó por doquier, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>la carta había desaparecido</span>.",
                        "translation": "Searched everywhere, but the letter had vanished.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Contrast",
                "formulaHTML": "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">pero</span> + <span class=\"fw-token-c\">Contrast</span>",
                "rule": "Adversative bridge: introduces a qualification, limitation, or unexpected contrast.",
                "allowed_lemmas": [
                    "salir",
                    "querer",
                    "intentar",
                    "saber",
                    "buscar"
                ],
                "targetHTML": "Quería salir, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>llovía</span>.",
                "translation": "I wanted to go out, but it was raining.",
                "examples": [
                    {
                        "targetHTML": "Quería salir, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>llovía</span>.",
                        "translation": "I wanted to go out, but it was raining.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Lo intenté con todas mis fuerzas, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>no pude</span>.",
                        "translation": "I tried with all my might, but couldn't.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Sabía la lección, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>se puso nervioso</span>.",
                        "translation": "Knew the lesson, but got nervous.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Es caro, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>vale la pena</span>.",
                        "translation": "It is expensive, but worth it.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Buscó por doquier, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>la carta había desaparecido</span>.",
                        "translation": "Searched everywhere, but the letter had vanished.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Condition",
                "formulaHTML": "<span class=\"fw-token-connector\">Si</span> + <span class=\"fw-token-v\">Condition</span> , <span class=\"fw-token-c\">Result</span>",
                "rule": "Conditional marker: establishes a hypothesis preceding its outcome.",
                "allowed_lemmas": [
                    "tener",
                    "querer",
                    "llover",
                    "poder",
                    "saber"
                ],
                "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>tienes tiempo</span>, <span class='fw-token-c'>ven a verme</span>.",
                "translation": "If you have time, come see me.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>tienes tiempo</span>, <span class='fw-token-c'>ven a verme</span>.",
                        "translation": "If you have time, come see me.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>llueve mañana</span>, <span class='fw-token-c'>nos quedaremos en casa</span>.",
                        "translation": "If it rains tomorrow, we will stay at home.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>quieres</span>, <span class='fw-token-c'>podemos almorzar juntos</span>.",
                        "translation": "If you want, we can have lunch together.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>puedes ayudarme</span>, <span class='fw-token-c'>te lo agradezco</span>.",
                        "translation": "If you can help me, I appreciate it.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>sabes algo nuevo</span>, <span class='fw-token-c'>avísame enseguida</span>.",
                        "translation": "If you know anything new, let me know right away.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Condition",
                "formulaHTML": "<span class=\"fw-token-connector\">Si</span> + <span class=\"fw-token-v\">Condition</span> , <span class=\"fw-token-c\">Result</span>",
                "rule": "Conditional marker: establishes a hypothesis preceding its outcome.",
                "allowed_lemmas": [
                    "tener",
                    "querer",
                    "llover",
                    "poder",
                    "saber"
                ],
                "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>tienes tiempo</span>, <span class='fw-token-c'>ven a verme</span>.",
                "translation": "If you have time, come see me.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>tienes tiempo</span>, <span class='fw-token-c'>ven a verme</span>.",
                        "translation": "If you have time, come see me.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>llueve mañana</span>, <span class='fw-token-c'>nos quedaremos en casa</span>.",
                        "translation": "If it rains tomorrow, we will stay at home.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>quieres</span>, <span class='fw-token-c'>podemos almorzar juntos</span>.",
                        "translation": "If you want, we can have lunch together.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>puedes ayudarme</span>, <span class='fw-token-c'>te lo agradezco</span>.",
                        "translation": "If you can help me, I appreciate it.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>sabes algo nuevo</span>, <span class='fw-token-c'>avísame enseguida</span>.",
                        "translation": "If you know anything new, let me know right away.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Manner / Simile",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Standard</span>",
                "rule": "Simile and manner: compares action execution against an exemplar.",
                "allowed_lemmas": [
                    "cantar",
                    "correr",
                    "brillar",
                    "hablar",
                    "actuar"
                ],
                "targetHTML": "Canta <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un pájaro</span>.",
                "translation": "Sings like a bird.",
                "examples": [
                    {
                        "targetHTML": "Canta <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un pájaro</span>.",
                        "translation": "Sings like a bird.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Corre rápido <span class='fw-token-connector'>como</span> <span class='fw-token-c'>el viento</span>.",
                        "translation": "Runs fast like the wind.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Brilla <span class='fw-token-connector'>como</span> <span class='fw-token-c'>el oro puro bajo el sol</span>.",
                        "translation": "Shines like pure gold under the sun.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Actuó <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un verdadero profesional</span>.",
                        "translation": "Acted like a true professional.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Habla español tan claro <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un nativo</span>.",
                        "translation": "Speaks Spanish as clearly as a native.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Capacity / Role",
                "formulaHTML": "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Capacity / Profession</span>",
                "rule": "Capacity and role: designates the status or function held.",
                "allowed_lemmas": [
                    "médico",
                    "profesor",
                    "voluntario",
                    "guía",
                    "testigo"
                ],
                "targetHTML": "Trabaja <span class='fw-token-connector'>como</span> <span class='fw-token-c'>médico en el hospital central</span>.",
                "translation": "Works as a doctor in the central hospital.",
                "examples": [
                    {
                        "targetHTML": "Trabaja <span class='fw-token-connector'>como</span> <span class='fw-token-c'>médico en el hospital central</span>.",
                        "translation": "Works as a doctor in the central hospital.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Actuó <span class='fw-token-connector'>como</span> <span class='fw-token-c'>representante oficial</span>.",
                        "translation": "Acted as official representative.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Participa <span class='fw-token-connector'>como</span> <span class='fw-token-c'>voluntaria en la biblioteca</span>.",
                        "translation": "Participates as a volunteer in the library.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Te hablo <span class='fw-token-connector'>como</span> <span class='fw-token-c'>amigo sincero</span>.",
                        "translation": "I speak to you as a sincere friend.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Declaró <span class='fw-token-connector'>como</span> <span class='fw-token-c'>testigo del suceso</span>.",
                        "translation": "Testified as a witness of the event.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Manner / Simile",
                "formulaHTML": "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Standard</span>",
                "rule": "Simile and manner: compares action execution against an exemplar.",
                "allowed_lemmas": [
                    "cantar",
                    "correr",
                    "brillar",
                    "hablar",
                    "actuar"
                ],
                "targetHTML": "Canta <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un pájaro</span>.",
                "translation": "Sings like a bird.",
                "examples": [
                    {
                        "targetHTML": "Canta <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un pájaro</span>.",
                        "translation": "Sings like a bird.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Corre rápido <span class='fw-token-connector'>como</span> <span class='fw-token-c'>el viento</span>.",
                        "translation": "Runs fast like the wind.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Brilla <span class='fw-token-connector'>como</span> <span class='fw-token-c'>el oro puro bajo el sol</span>.",
                        "translation": "Shines like pure gold under the sun.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "Actuó <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un verdadero profesional</span>.",
                        "translation": "Acted like a true professional.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Habla español tan claro <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un nativo</span>.",
                        "translation": "Speaks Spanish as clearly as a native.",
                        "source": "Subtitles"
                    }
                ]
            },
            {
                "tag": "Capacity / Role",
                "formulaHTML": "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Capacity / Profession</span>",
                "rule": "Capacity and role: designates the status or function held.",
                "allowed_lemmas": [
                    "médico",
                    "profesor",
                    "voluntario",
                    "guía",
                    "testigo"
                ],
                "targetHTML": "Trabaja <span class='fw-token-connector'>como</span> <span class='fw-token-c'>médico en el hospital central</span>.",
                "translation": "Works as a doctor in the central hospital.",
                "examples": [
                    {
                        "targetHTML": "Trabaja <span class='fw-token-connector'>como</span> <span class='fw-token-c'>médico en el hospital central</span>.",
                        "translation": "Works as a doctor in the central hospital.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Actuó <span class='fw-token-connector'>como</span> <span class='fw-token-c'>representante oficial</span>.",
                        "translation": "Acted as official representative.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Participa <span class='fw-token-connector'>como</span> <span class='fw-token-c'>voluntaria en la biblioteca</span>.",
                        "translation": "Participates as a volunteer in the library.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Te hablo <span class='fw-token-connector'>como</span> <span class='fw-token-c'>amigo sincero</span>.",
                        "translation": "I speak to you as a sincere friend.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "Declaró <span class='fw-token-connector'>como</span> <span class='fw-token-c'>testigo del suceso</span>.",
                        "translation": "Testified as a witness of the event.",
                        "source": "Literature"
                    }
                ]
            }
        ]
    },
    "mi": {
        "word": "mi",
        "role": "Possessive Determiner",
        "rank": 20,
        "frequency": 6120,
        "relations": [
            {
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-connector\">mi</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                "rule": "1st-person singular possessive: introduces something belonging to the speaker.",
                "allowed_lemmas": [
                    "casa",
                    "vida",
                    "amigo",
                    "hermano",
                    "coche"
                ],
                "targetHTML": "Esta es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>casa</span>.",
                "translation": "This is my house.",
                "examples": [
                    {
                        "targetHTML": "Esta es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>casa</span>.",
                        "translation": "This is my house.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>mejor amigo desde la infancia</span>.",
                        "translation": "He is my best friend since childhood.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Mi</span> <span class='fw-token-c'>hermano mayor</span> vive en Barcelona.",
                        "translation": "My older brother lives in Barcelona.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "He dedicado toda <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>vida</span> a este trabajo.",
                        "translation": "I have dedicated my whole life to this work.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Mi</span> <span class='fw-token-c'>coche</span> está aparcado enfrente.",
                        "translation": "My car is parked in front.",
                        "source": "Subtitles"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-connector\">mi</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                "rule": "1st-person singular possessive: introduces something belonging to the speaker.",
                "allowed_lemmas": [
                    "casa",
                    "vida",
                    "amigo",
                    "hermano",
                    "coche"
                ],
                "targetHTML": "Esta es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>casa</span>.",
                "translation": "This is my house.",
                "examples": [
                    {
                        "targetHTML": "Esta es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>casa</span>.",
                        "translation": "This is my house.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>mejor amigo desde la infancia</span>.",
                        "translation": "He is my best friend since childhood.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Mi</span> <span class='fw-token-c'>hermano mayor</span> vive en Barcelona.",
                        "translation": "My older brother lives in Barcelona.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "He dedicado toda <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>vida</span> a este trabajo.",
                        "translation": "I have dedicated my whole life to this work.",
                        "source": "Literature"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Mi</span> <span class='fw-token-c'>coche</span> está aparcado enfrente.",
                        "translation": "My car is parked in front.",
                        "source": "Subtitles"
                    }
                ]
            }
        ]
    },
    "su": {
        "word": "su",
        "role": "Possessive Determiner",
        "rank": 10,
        "frequency": 11240,
        "relations": [
            {
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-connector\">su</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                "rule": "3rd-person possessive: denotes something belonging to him, her, them, or formal 'you'.",
                "allowed_lemmas": [
                    "nombre",
                    "casa",
                    "familia",
                    "trabajo",
                    "opinión"
                ],
                "targetHTML": "¿Cuál es <span class='fw-token-connector'>su</span> <span class='fw-token-c'>nombre</span>?",
                "translation": "What is your (formal) / his / her name?",
                "examples": [
                    {
                        "targetHTML": "¿Cuál es <span class='fw-token-connector'>su</span> <span class='fw-token-c'>nombre</span>?",
                        "translation": "What is your (formal) / his / her name?",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Su</span> <span class='fw-token-c'>familia</span> es muy amable y acogedora.",
                        "translation": "His family is very kind and welcoming.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Admiro mucho <span class='fw-token-connector'>su</span> <span class='fw-token-c'>trabajo profesional</span>.",
                        "translation": "I admire his professional work very much.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Su</span> <span class='fw-token-c'>opinión</span> es fundamental para nosotros.",
                        "translation": "Your (formal) opinion is essential for us.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Visité <span class='fw-token-connector'>su</span> <span class='fw-token-c'>casa de campo el fin de semana</span>.",
                        "translation": "I visited his country house on the weekend.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-connector\">su</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                "rule": "3rd-person possessive: denotes something belonging to him, her, them, or formal 'you'.",
                "allowed_lemmas": [
                    "nombre",
                    "casa",
                    "familia",
                    "trabajo",
                    "opinión"
                ],
                "targetHTML": "¿Cuál es <span class='fw-token-connector'>su</span> <span class='fw-token-c'>nombre</span>?",
                "translation": "What is your (formal) / his / her name?",
                "examples": [
                    {
                        "targetHTML": "¿Cuál es <span class='fw-token-connector'>su</span> <span class='fw-token-c'>nombre</span>?",
                        "translation": "What is your (formal) / his / her name?",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Su</span> <span class='fw-token-c'>familia</span> es muy amable y acogedora.",
                        "translation": "His family is very kind and welcoming.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Admiro mucho <span class='fw-token-connector'>su</span> <span class='fw-token-c'>trabajo profesional</span>.",
                        "translation": "I admire his professional work very much.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Su</span> <span class='fw-token-c'>opinión</span> es fundamental para nosotros.",
                        "translation": "Your (formal) opinion is essential for us.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Visité <span class='fw-token-connector'>su</span> <span class='fw-token-c'>casa de campo el fin de semana</span>.",
                        "translation": "I visited his country house on the weekend.",
                        "source": "Literature"
                    }
                ]
            }
        ]
    },
    "tu": {
        "word": "tu",
        "role": "Possessive Determiner",
        "rank": 23,
        "frequency": 5100,
        "relations": [
            {
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-connector\">tu</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                "rule": "2nd-person informal possessive: introduces something belonging to the listener.",
                "allowed_lemmas": [
                    "casa",
                    "amigo",
                    "trabajo",
                    "idea",
                    "familia"
                ],
                "targetHTML": "<span class='fw-token-connector'>Tu</span> <span class='fw-token-c'>casa</span> es preciosa.",
                "translation": "Your house is lovely.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tu</span> <span class='fw-token-c'>casa</span> es preciosa.",
                        "translation": "Your house is lovely.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Me gusta mucho <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>idea para el proyecto</span>.",
                        "translation": "I like your idea for the project a lot.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "¿Cómo está <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>familia</span>?",
                        "translation": "How is your family?",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ayer conocí a <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>amigo Carlos</span>.",
                        "translation": "Yesterday I met your friend Carlos.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Felicidades por <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>nuevo trabajo</span>.",
                        "translation": "Congratulations on your new job.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Possession",
                "formulaHTML": "<span class=\"fw-token-connector\">tu</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                "rule": "2nd-person informal possessive: introduces something belonging to the listener.",
                "allowed_lemmas": [
                    "casa",
                    "amigo",
                    "trabajo",
                    "idea",
                    "familia"
                ],
                "targetHTML": "<span class='fw-token-connector'>Tu</span> <span class='fw-token-c'>casa</span> es preciosa.",
                "translation": "Your house is lovely.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tu</span> <span class='fw-token-c'>casa</span> es preciosa.",
                        "translation": "Your house is lovely.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Me gusta mucho <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>idea para el proyecto</span>.",
                        "translation": "I like your idea for the project a lot.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "¿Cómo está <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>familia</span>?",
                        "translation": "How is your family?",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Ayer conocí a <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>amigo Carlos</span>.",
                        "translation": "Yesterday I met your friend Carlos.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Felicidades por <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>nuevo trabajo</span>.",
                        "translation": "Congratulations on your new job.",
                        "source": "Literature"
                    }
                ]
            }
        ]
    },
    "yo": {
        "word": "yo",
        "role": "Subject Pronoun",
        "rank": 25,
        "frequency": 4200,
        "relations": [
            {
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Yo</span> + <span class=\"fw-token-v\">Verb (1st Sing)</span>",
                "rule": "Subject pronoun: explicitly emphasizes or contrasts the 1st-person actor.",
                "allowed_lemmas": [
                    "saber",
                    "pensar",
                    "creer",
                    "querer",
                    "estar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>sé</span> la verdad.",
                "translation": "I know the truth.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>sé</span> la verdad.",
                        "translation": "I know the truth.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>pienso</span> que deberíamos intentarlo.",
                        "translation": "I think that we should try it.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> no <span class='fw-token-v'>tengo</span> ninguna duda al respecto.",
                        "translation": "I have no doubt about it.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>quiero</span> acompañarte al centro.",
                        "translation": "I want to accompany you downtown.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>estoy</span> listo cuando tú digas.",
                        "translation": "I am ready whenever you say.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Yo</span> + <span class=\"fw-token-v\">Verb (1st Sing)</span>",
                "rule": "Subject pronoun: explicitly emphasizes or contrasts the 1st-person actor.",
                "allowed_lemmas": [
                    "saber",
                    "pensar",
                    "creer",
                    "querer",
                    "estar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>sé</span> la verdad.",
                "translation": "I know the truth.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>sé</span> la verdad.",
                        "translation": "I know the truth.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>pienso</span> que deberíamos intentarlo.",
                        "translation": "I think that we should try it.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> no <span class='fw-token-v'>tengo</span> ninguna duda al respecto.",
                        "translation": "I have no doubt about it.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>quiero</span> acompañarte al centro.",
                        "translation": "I want to accompany you downtown.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>estoy</span> listo cuando tú digas.",
                        "translation": "I am ready whenever you say.",
                        "source": "Literature"
                    }
                ]
            }
        ]
    },
    "tú": {
        "word": "tú",
        "role": "Subject Pronoun",
        "rank": 26,
        "frequency": 4100,
        "relations": [
            {
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Tú</span> + <span class=\"fw-token-v\">Verb (2nd Sing)</span>",
                "rule": "Subject pronoun: explicitly clarifies or contrasts the 2nd-person actor.",
                "allowed_lemmas": [
                    "saber",
                    "tener",
                    "poder",
                    "querer",
                    "entender"
                ],
                "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>sabes</span> lo que quiero decir.",
                "translation": "You know what I mean.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>sabes</span> lo que quiero decir.",
                        "translation": "You know what I mean.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>tienes</span> toda la razón en esto.",
                        "translation": "You are completely right on this.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Si <span class='fw-token-connector'>tú</span> <span class='fw-token-v'>puedes</span> venir, será genial.",
                        "translation": "If you can come, it will be great.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>entiendes</span> mejor que nadie la situación.",
                        "translation": "You understand the situation better than anyone.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>decides</span> qué camino tomar.",
                        "translation": "You decide which path to take.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Subject Pronoun",
                "formulaHTML": "<span class=\"fw-token-connector\">Tú</span> + <span class=\"fw-token-v\">Verb (2nd Sing)</span>",
                "rule": "Subject pronoun: explicitly clarifies or contrasts the 2nd-person actor.",
                "allowed_lemmas": [
                    "saber",
                    "tener",
                    "poder",
                    "querer",
                    "entender"
                ],
                "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>sabes</span> lo que quiero decir.",
                "translation": "You know what I mean.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>sabes</span> lo que quiero decir.",
                        "translation": "You know what I mean.",
                        "source": "Everyday speech"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>tienes</span> toda la razón en esto.",
                        "translation": "You are completely right on this.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Si <span class='fw-token-connector'>tú</span> <span class='fw-token-v'>puedes</span> venir, será genial.",
                        "translation": "If you can come, it will be great.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>entiendes</span> mejor que nadie la situación.",
                        "translation": "You understand the situation better than anyone.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>decides</span> qué camino tomar.",
                        "translation": "You decide which path to take.",
                        "source": "Literature"
                    }
                ]
            }
        ]
    },
    "eso": {
        "word": "eso",
        "role": "Demonstrative Pronoun",
        "rank": 27,
        "frequency": 3900,
        "relations": [
            {
                "tag": "Neuter Demonstrative",
                "formulaHTML": "<span class=\"fw-token-connector\">eso</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Neuter demonstrative: refers to a stated matter, idea, or object near the listener.",
                "allowed_lemmas": [
                    "ser",
                    "parecer",
                    "cambiar",
                    "pasar",
                    "significar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>es</span> verdad.",
                "translation": "That is true.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>es</span> verdad.",
                        "translation": "That is true.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>parece</span> una magnífica solución.",
                        "translation": "That looks like a magnificent solution.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>cambia</span> las cosas por completo.",
                        "translation": "That changes things completely.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eso</span> no <span class='fw-token-v'>significa</span> que sea fácil.",
                        "translation": "That does not mean that it is easy.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Precisamente por <span class='fw-token-connector'>eso</span> vine a hablar contigo.",
                        "translation": "Precisely because of that I came to talk to you.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Neuter Demonstrative",
                "formulaHTML": "<span class=\"fw-token-connector\">eso</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Neuter demonstrative: refers to a stated matter, idea, or object near the listener.",
                "allowed_lemmas": [
                    "ser",
                    "parecer",
                    "cambiar",
                    "pasar",
                    "significar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>es</span> verdad.",
                "translation": "That is true.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>es</span> verdad.",
                        "translation": "That is true.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>parece</span> una magnífica solución.",
                        "translation": "That looks like a magnificent solution.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>cambia</span> las cosas por completo.",
                        "translation": "That changes things completely.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Eso</span> no <span class='fw-token-v'>significa</span> que sea fácil.",
                        "translation": "That does not mean that it is easy.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Precisamente por <span class='fw-token-connector'>eso</span> vine a hablar contigo.",
                        "translation": "Precisely because of that I came to talk to you.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Immediate Demonstrative",
                "formulaHTML": "<span class=\"fw-token-connector\">esto</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Neuter demonstrative: refers to an immediate topic or object near the speaker.",
                "allowed_lemmas": [
                    "ser",
                    "parecer",
                    "funcionar",
                    "gustar",
                    "acabar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>es</span> para ti.",
                "translation": "This is for you.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>es</span> para ti.",
                        "translation": "This is for you.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>funciona</span> a la perfección.",
                        "translation": "This works to perfection.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>parece</span> muy interesante.",
                        "translation": "This looks very interesting.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> me <span class='fw-token-v'>gusta</span> cada día más.",
                        "translation": "I like this more every day.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> apenas <span class='fw-token-v'>comienza</span>.",
                        "translation": "This is only just beginning.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Immediate Demonstrative",
                "formulaHTML": "<span class=\"fw-token-connector\">esto</span> + <span class=\"fw-token-v\">Verb</span>",
                "rule": "Neuter demonstrative: refers to an immediate topic or object near the speaker.",
                "allowed_lemmas": [
                    "ser",
                    "parecer",
                    "funcionar",
                    "gustar",
                    "acabar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>es</span> para ti.",
                "translation": "This is for you.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>es</span> para ti.",
                        "translation": "This is for you.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>funciona</span> a la perfección.",
                        "translation": "This works to perfection.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>parece</span> muy interesante.",
                        "translation": "This looks very interesting.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> me <span class='fw-token-v'>gusta</span> cada día más.",
                        "translation": "I like this more every day.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Esto</span> apenas <span class='fw-token-v'>comienza</span>.",
                        "translation": "This is only just beginning.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Universal Totality",
                "formulaHTML": "<span class=\"fw-token-connector\">todo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                "rule": "Universal pronoun: signifies the totality of matters ('everything / all').",
                "allowed_lemmas": [
                    "estar",
                    "salir",
                    "cambiar",
                    "pasar",
                    "terminar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>está</span> bien.",
                "translation": "Everything is fine.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>está</span> bien.",
                        "translation": "Everything is fine.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>salió</span> según lo planeado.",
                        "translation": "Everything turned out as planned.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>cambió</span> de un momento a otro.",
                        "translation": "Everything changed from one moment to the next.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Entendí <span class='fw-token-connector'>todo</span> sin ninguna dificultad.",
                        "translation": "I understood everything without any difficulty.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>quedó</span> en calma tras la lluvia.",
                        "translation": "Everything remained calm after the rain.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Universal Totality",
                "formulaHTML": "<span class=\"fw-token-connector\">todo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                "rule": "Universal pronoun: signifies the totality of matters ('everything / all').",
                "allowed_lemmas": [
                    "estar",
                    "salir",
                    "cambiar",
                    "pasar",
                    "terminar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>está</span> bien.",
                "translation": "Everything is fine.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>está</span> bien.",
                        "translation": "Everything is fine.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>salió</span> según lo planeado.",
                        "translation": "Everything turned out as planned.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>cambió</span> de un momento a otro.",
                        "translation": "Everything changed from one moment to the next.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Entendí <span class='fw-token-connector'>todo</span> sin ninguna dificultad.",
                        "translation": "I understood everything without any difficulty.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>quedó</span> en calma tras la lluvia.",
                        "translation": "Everything remained calm after the rain.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Indefinite Entity",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">algo</span>",
                "rule": "Indefinite entity: marks an unspecified thing or amount ('something').",
                "allowed_lemmas": [
                    "comer",
                    "decir",
                    "pasar",
                    "saber",
                    "traer"
                ],
                "targetHTML": "Quiero comer <span class='fw-token-connector'>algo</span>.",
                "translation": "I want to eat something.",
                "examples": [
                    {
                        "targetHTML": "Quiero comer <span class='fw-token-connector'>algo</span>.",
                        "translation": "I want to eat something.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Tiene <span class='fw-token-connector'>algo</span> importante que contarnos.",
                        "translation": "Has something important to tell us.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "¿Ha pasado <span class='fw-token-connector'>algo</span> mientras estaba fuera?",
                        "translation": "Did something happen while I was away?",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Sé <span class='fw-token-connector'>algo</span> sobre este tema histórico.",
                        "translation": "I know something about this historical topic.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Te traje <span class='fw-token-connector'>algo</span> del viaje que te gustará.",
                        "translation": "I brought you something from the trip you will like.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Indefinite Entity",
                "formulaHTML": "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">algo</span>",
                "rule": "Indefinite entity: marks an unspecified thing or amount ('something').",
                "allowed_lemmas": [
                    "comer",
                    "decir",
                    "pasar",
                    "saber",
                    "traer"
                ],
                "targetHTML": "Quiero comer <span class='fw-token-connector'>algo</span>.",
                "translation": "I want to eat something.",
                "examples": [
                    {
                        "targetHTML": "Quiero comer <span class='fw-token-connector'>algo</span>.",
                        "translation": "I want to eat something.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Tiene <span class='fw-token-connector'>algo</span> importante que contarnos.",
                        "translation": "Has something important to tell us.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "¿Ha pasado <span class='fw-token-connector'>algo</span> mientras estaba fuera?",
                        "translation": "Did something happen while I was away?",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Sé <span class='fw-token-connector'>algo</span> sobre este tema histórico.",
                        "translation": "I know something about this historical topic.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Te traje <span class='fw-token-connector'>algo</span> del viaje que te gustará.",
                        "translation": "I brought you something from the trip you will like.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Causal Reason",
                "formulaHTML": "<span class=\"fw-token-v\">Result</span> + <span class=\"fw-token-connector\">porque</span> + <span class=\"fw-token-c\">Cause</span>",
                "rule": "Causal conjunction: explains the underlying reason or motive.",
                "allowed_lemmas": [
                    "cansar",
                    "llover",
                    "gustar",
                    "querer",
                    "importar"
                ],
                "targetHTML": "No fui <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estaba cansado</span>.",
                "translation": "I did not go because I was tired.",
                "examples": [
                    {
                        "targetHTML": "No fui <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estaba cansado</span>.",
                        "translation": "I did not go because I was tired.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Nos quedamos <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>empezó a llover</span>.",
                        "translation": "We stayed because it started raining.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Estudio español <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>me encanta viajar</span>.",
                        "translation": "I study Spanish because I love traveling.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Sonrió <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>recibió buenas noticias</span>.",
                        "translation": "Smiled because he received good news.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Te pregunto <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>me importa tu opinión</span>.",
                        "translation": "I ask you because your opinion matters to me.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Causal Reason",
                "formulaHTML": "<span class=\"fw-token-v\">Result</span> + <span class=\"fw-token-connector\">porque</span> + <span class=\"fw-token-c\">Cause</span>",
                "rule": "Causal conjunction: explains the underlying reason or motive.",
                "allowed_lemmas": [
                    "cansar",
                    "llover",
                    "gustar",
                    "querer",
                    "importar"
                ],
                "targetHTML": "No fui <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estaba cansado</span>.",
                "translation": "I did not go because I was tired.",
                "examples": [
                    {
                        "targetHTML": "No fui <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estaba cansado</span>.",
                        "translation": "I did not go because I was tired.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "Nos quedamos <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>empezó a llover</span>.",
                        "translation": "We stayed because it started raining.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "Estudio español <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>me encanta viajar</span>.",
                        "translation": "I study Spanish because I love traveling.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "Sonrió <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>recibió buenas noticias</span>.",
                        "translation": "Smiled because he received good news.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "Te pregunto <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>me importa tu opinión</span>.",
                        "translation": "I ask you because your opinion matters to me.",
                        "source": "Literature"
                    }
                ]
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
                "tag": "Temporal Nexus",
                "formulaHTML": "<span class=\"fw-token-connector\">Cuando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Action</span>",
                "rule": "Temporal connector: situates an event at a point in time.",
                "allowed_lemmas": [
                    "llegar",
                    "salir",
                    "ver",
                    "poder",
                    "despertar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>llegué</span>, <span class='fw-token-c'>todos sonrieron</span>.",
                "translation": "When I arrived, everyone smiled.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>llegué</span>, <span class='fw-token-c'>todos sonrieron</span>.",
                        "translation": "When I arrived, everyone smiled.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>puedas</span>, pásate por mi oficina.",
                        "translation": "When you can, drop by my office.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> sale el sol, la plaza se llena de gente.",
                        "translation": "When the sun rises, the square fills with people.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> era niño, vivía cerca del mar.",
                        "translation": "When I was a boy, I lived near the sea.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> despertó, el tren ya había llegado.",
                        "translation": "When he woke up, the train had already arrived.",
                        "source": "Literature"
                    }
                ]
            }
        ],
        "uses": [
            {
                "tag": "Temporal Nexus",
                "formulaHTML": "<span class=\"fw-token-connector\">Cuando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Action</span>",
                "rule": "Temporal connector: situates an event at a point in time.",
                "allowed_lemmas": [
                    "llegar",
                    "salir",
                    "ver",
                    "poder",
                    "despertar"
                ],
                "targetHTML": "<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>llegué</span>, <span class='fw-token-c'>todos sonrieron</span>.",
                "translation": "When I arrived, everyone smiled.",
                "examples": [
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>llegué</span>, <span class='fw-token-c'>todos sonrieron</span>.",
                        "translation": "When I arrived, everyone smiled.",
                        "source": "Everyday dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>puedas</span>, pásate por mi oficina.",
                        "translation": "When you can, drop by my office.",
                        "source": "Conversation"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> sale el sol, la plaza se llena de gente.",
                        "translation": "When the sun rises, the square fills with people.",
                        "source": "Dialogue"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> era niño, vivía cerca del mar.",
                        "translation": "When I was a boy, I lived near the sea.",
                        "source": "Subtitles"
                    },
                    {
                        "targetHTML": "<span class='fw-token-connector'>Cuando</span> despertó, el tren ya había llegado.",
                        "translation": "When he woke up, the train had already arrived.",
                        "source": "Literature"
                    }
                ]
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
    direct_obj: 'direct object',
    indirect_obj: 'indirect object',
    reflexive: 'reflexive',
    rel_pron: 'relative',
    coord_conj: 'coordination',
    subord_conj: 'subordination',
    adverbial: 'adverbial',
    adv_connector: 'connector',
    possessive: 'possessive',
    demonstrative: 'demonstrative',
    indefinite: 'indefinite',
    quantifier: 'quantifier',
    negation: 'negation',
    focus_particle: 'focus particle',
    interrogative: 'question',
    comparative: 'comparison',
    contraction: 'contraction',
    clitic: 'clitic'
};

function esc(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function shortGloss(raw) {
    const s = String(raw || '').trim();
    if (!s) return '';
    return s.split(/[,;/]/)[0].trim().toLowerCase();
}

function meaningOf(obj) {
    if (!obj) return '';
    if (typeof obj === 'string') return obj;
    return obj.gloss || obj.meaning || obj.translation || obj.definition || '';
}

/** Lookup a deterministic grammar-word definition for a card in the given language. */
export function getGrammarWordDefinition(cardOrWord, lang) {
    if (!cardOrWord) return null;
    const wordKey = typeof cardOrWord === 'string'
        ? cardOrWord.trim().toLowerCase()
        : (cardOrWord.targetWord || cardOrWord.word || '').trim().toLowerCase();
    if (!wordKey) return null;

    const langKey = String(lang || 'pt').toLowerCase();
    const suite = GRAMMAR_WORDS[langKey] || PORTUGUESE_GRAMMAR_WORDS;
    return suite[wordKey] || null;
}

// Backward-compatibility alias:
export function getPortugueseGrammarDefinition(cardOrWord, lang) {
    return getGrammarWordDefinition(cardOrWord, lang || 'pt');
}

/** Determine if a card is a function word. */
export function isFunctionWordCard(card, lang) {
    if (!card) return false;
    if (card.partOfSpeech === 'FW' || card.pos === 'FW' || card.functionWord) return true;
    return Boolean(getGrammarWordDefinition(card, lang));
}

export function isPortugueseGrammarWord(card, lang) {
    if (!card) return false;
    const isPt = !lang || lang === 'portuguese' || lang === 'pt' || lang === 'portuguese_brazilian';
    if (!isPt) return false;
    const wordKey = String(card.targetWord || card.word || card.lemma || '').trim().toLowerCase();
    return Boolean(PORTUGUESE_GRAMMAR_WORDS[wordKey]);
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

// Computes ambient glow CSS for any flashcard based on POS rules & FW signature glow
export function getCardAmbientGlow(card, lang, activePos, isSplitCard, getPosAccentRgbFn) {
    const getRgb = getPosAccentRgbFn || (typeof window !== 'undefined' ? window.getPosAccentRgb : null) || (() => '148, 163, 184');

    // 1. Function words get the dedicated Periwinkle Moonstone Off-White halo
    if (isFunctionWordCard(card, lang)) {
        return `radial-gradient(circle at 50% 20%, rgba(${FW_SIGNATURE_GLOW_RGB}, 0.18), transparent 70%)`;
    }

    // 2. Companion card ("Card 1 of 2"): single POS color matching active companion card
    if (isSplitCard && card?.splitInfo) {
        const splitPos = card.splitInfo.pos || card.partOfSpeech || activePos;
        const rgb = getRgb(splitPos);
        return `radial-gradient(circle at 50% 20%, rgba(${rgb}, 0.18), transparent 70%)`;
    }

    // 3. Merged lemmas: merged cards represent a single unified lexeme (verb).
    // Always emits a single centered radial glow in the verb color (green).
    if (card?.mergedLemma) {
        const mergedPos = (card.partOfSpeech && !/verb|aux/i.test(card.partOfSpeech))
            ? card.partOfSpeech
            : (activePos || card.partOfSpeech || 'VERB');
        const rgb = getRgb(mergedPos);
        return `radial-gradient(circle at 50% 20%, rgba(${rgb}, 0.18), transparent 70%)`;
    }

    const NON_LEXICAL_POS = new Set(['MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY', 'PHRASE']);

    const isRareMeaning = m => {
        if (!m) return true;
        if (m.isRareSense || m.lowShare || m.rare || m.unassigned || m.exampleOnly) return true;
        if (m.assignment_method === 'unassigned') return true;
        const prom = String(m.prominenceLabel || '').trim().toLowerCase();
        if (prom === 'rare') return true;
        if (typeof window !== 'undefined' && typeof window.getSenseProminenceInfo === 'function') {
            try {
                if (window.getSenseProminenceInfo(m)?.key === 'rare') return true;
            } catch (_) {}
        }
        const share = Number(m.shownShare ?? m.percentage);
        const hasExplicitShare = (m.shownShare != null || m.percentage != null) && !isNaN(share);
        const hasExamples = Boolean(
            m.targetSentence ||
            (Array.isArray(m.allExamples) && m.allExamples.length > 0) ||
            (Array.isArray(m.examples) && m.examples.length > 0)
        );
        if (hasExplicitShare && share <= 0) return true;
        if (!hasExamples && hasExplicitShare && share < 0.10) return true;
        return false;
    };

    const cardMeanings = (card?.meanings || []).filter(m => {
        if (!m) return false;
        const pos = m.pos === 'SENSE_CYCLE' ? (m.cycle_pos || '') : (m.pos || '');
        if (!pos || NON_LEXICAL_POS.has(String(pos).toUpperCase())) return false;
        if (typeof window !== 'undefined' && typeof window.isHiddenExpressionOnParent === 'function' && window.isHiddenExpressionOnParent(card, m)) return false;
        return true;
    });

    const nonRareMeanings = cardMeanings.filter(m => !isRareMeaning(m));
    const candidateMeanings = nonRareMeanings.length > 0 ? nonRareMeanings : cardMeanings;

    const totalWeight = candidateMeanings.reduce(
        (sum, m) => sum + (Number(m.shownShare ?? m.percentage) || 0),
        0
    );

    const rgbWeights = new Map();
    const rgbOrder = [];

    for (const m of candidateMeanings) {
        const pos = m.pos === 'SENSE_CYCLE' ? (m.cycle_pos || '') : (m.pos || '');
        const rgb = getRgb(pos);
        if (!rgb) continue;
        const weight = Number(m.shownShare ?? m.percentage) || 0;
        if (!rgbWeights.has(rgb)) {
            rgbWeights.set(rgb, 0);
            rgbOrder.push(rgb);
        }
        rgbWeights.set(rgb, rgbWeights.get(rgb) + weight);
    }

    let distinctRgb = rgbOrder;
    if (totalWeight > 0 && rgbOrder.length > 1) {
        const significant = rgbOrder.filter(rgb => (rgbWeights.get(rgb) / totalWeight) >= 0.10);
        if (significant.length > 0) {
            distinctRgb = significant;
        }
    }

    if (distinctRgb.length === 0) {
        const fallbackPos = card?.partOfSpeech || activePos;
        distinctRgb = [getRgb(fallbackPos)];
    }

    const activeRgb = activePos ? getRgb(activePos) : null;
    if (activeRgb && distinctRgb.includes(activeRgb) && distinctRgb[0] !== activeRgb) {
        distinctRgb = [activeRgb, ...distinctRgb.filter(c => c !== activeRgb)];
    }

    // Single POS color: single centered radial glow
    if (distinctRgb.length <= 1) {
        return `radial-gradient(circle at 50% 20%, rgba(${distinctRgb[0]}, 0.18), transparent 70%)`;
    }

    // 2 POS colors: multi-corner glow
    if (distinctRgb.length === 2) {
        return `radial-gradient(circle at 22% 16%, rgba(${distinctRgb[0]}, 0.17), transparent 58%), radial-gradient(circle at 78% 16%, rgba(${distinctRgb[1]}, 0.17), transparent 58%)`;
    }

    // 3 or more POS colors
    return `radial-gradient(circle at 18% 16%, rgba(${distinctRgb[0]}, 0.15), transparent 50%), radial-gradient(circle at 50% 12%, rgba(${distinctRgb[1]}, 0.15), transparent 50%), radial-gradient(circle at 82% 16%, rgba(${distinctRgb[2]}, 0.15), transparent 50%)`;
}

// Active state for deterministic card back navigation
let _activeWordKey = null;
let _activeRelIndex = 0;
let _activeExampleIndex = 0;

export function selectFunctionWordRelation(relIdx) {
    _activeRelIndex = Number(relIdx) || 0;
    _activeExampleIndex = 0;
    refreshFunctionWordCardBack();
}

// Backward compatibility alias:
export function selectFunctionWordUse(useIdx) {
    selectFunctionWordRelation(useIdx);
}

export function cycleFunctionWordExample() {
    const container = document.querySelector('.fw-deterministic-card');
    if (!container) return;
    const cardWord = container.dataset.word;
    const lang = container.dataset.lang || 'pt';
    const data = getGrammarWordDefinition(cardWord, lang);
    if (!data) return;

    const relations = data.relations || data.uses || [];
    if (_activeRelIndex >= relations.length) _activeRelIndex = 0;
    const currentRel = relations[_activeRelIndex];
    const examples = currentRel?.examples || (currentRel?.targetHTML ? [currentRel] : []);
    if (examples.length <= 1) {
        const plain = (currentRel?.targetHTML || currentRel?.target || '').replace(/<[^>]+>/g, '');
        window.speakTargetSentence?.() || window.speakText?.(plain);
        return;
    }

    _activeExampleIndex = (_activeExampleIndex + 1) % examples.length;
    refreshFunctionWordCardBack();

    const curEx = examples[_activeExampleIndex];
    if (curEx) {
        const plain = (curEx.targetHTML || curEx.target || '').replace(/<[^>]+>/g, '');
        window.speakText?.(plain);
    }
}

function renderFwTicks(total, current) {
    if (total < 2) return '';
    const ticks = Array.from({ length: total }, (_, i) =>
        `<span class="example-tick${i === current ? ' is-current' : ''}"></span>`
    ).join('');
    return `<div class="example-ticks" role="img" aria-label="Example ${current + 1} of ${total}">${ticks}</div>`;
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

    // Get current example from examples array
    const examples = currentRel?.examples || (currentRel?.targetHTML ? [currentRel] : []);
    if (_activeExampleIndex >= examples.length) _activeExampleIndex = 0;
    const currentEx = examples[_activeExampleIndex] || currentRel;

    // Update sentence target and translation
    const sentenceEl = container.querySelector('.fw-sentence-target');
    if (sentenceEl && currentEx) {
        sentenceEl.innerHTML = currentEx.targetHTML || currentEx.target || '';
    }

    const transEl = container.querySelector('.fw-sentence-translation');
    if (transEl && currentEx) {
        transEl.textContent = currentEx.translation || '';
    }

    const creditStartEl = container.querySelector('.fw-credit-start');
    if (creditStartEl) {
        creditStartEl.textContent = currentEx?.source || '';
    }

    const ticksContainer = container.querySelector('.fw-sentence-ticks-container');
    if (ticksContainer) {
        ticksContainer.innerHTML = renderFwTicks(examples.length, _activeExampleIndex);
    }
}

// Make functions available globally for onclick handlers
if (typeof window !== 'undefined') {
    window.selectFunctionWordRelation = selectFunctionWordRelation;
    window.selectFunctionWordUse = selectFunctionWordUse;
    window.cycleFunctionWordExample = cycleFunctionWordExample;
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
            _activeExampleIndex = 0;
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

        const examples = currentRel?.examples || (currentRel?.targetHTML ? [currentRel] : []);
        if (_activeExampleIndex >= examples.length) _activeExampleIndex = 0;
        const currentEx = examples[_activeExampleIndex] || currentRel;

        const targetHTML = currentEx?.targetHTML || currentRel?.targetHTML || esc(currentRel?.target || '');
        const plainTargetText = targetHTML.replace(/<[^>]+>/g, '');
        const sourceText = currentEx?.source || '';
        const ticksHTML = renderFwTicks(examples.length, _activeExampleIndex);

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
                <div class="fw-sentence-panel" onclick="event.stopPropagation(); window.cycleFunctionWordExample();">
                    <div class="fw-sentence-target">${targetHTML}</div>
                    <div class="fw-sentence-translation">${esc(currentEx?.translation || currentRel?.translation || '')}</div>
                    <div class="fw-example-credit-row">
                        <span class="fw-credit-start">${esc(sourceText)}</span>
                        <div class="fw-sentence-ticks-container">${ticksHTML}</div>
                    </div>
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
