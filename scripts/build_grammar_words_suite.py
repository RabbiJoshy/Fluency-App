#!/usr/bin/env python3
"""Build and validate the Portuguese and Spanish function word suites.

Each relation defines:
  - tag: Human-readable relation tag
  - formulaHTML: Constituent formula with semantic classes (fw-token-v, fw-token-connector, fw-token-c)
  - rule: Intuitive grammatical explanation
  - allowed_lemmas: Characteristic licensing lemmas/words participating in this pattern
  - examples: 5-6 vetted examples with targetHTML, translation, and source provenance
  - targetHTML & translation: top-level baseline for backwards compatibility

Outputs:
  - app/data/grammar-words/pt.json
  - app/data/grammar-words/es.json
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "app/data/grammar-words"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def rel(
    tag: str,
    formula: str,
    rule: str,
    allowed_lemmas: list[str],
    examples: list[dict[str, str]],
    parts: list[str] | None = None
) -> dict:
    """Construct a validated relation dictionary."""
    if len(examples) < 2:
        raise ValueError(f"Relation '{tag}' must have at least 2 examples, got {len(examples)}")
    d = {
        "tag": tag,
        "formulaHTML": formula,
        "rule": rule,
        "allowed_lemmas": allowed_lemmas,
        "targetHTML": examples[0]["targetHTML"],
        "translation": examples[0]["translation"],
        "examples": examples
    }
    if parts:
        d["parts"] = parts
    return d


def ex(targetHTML: str, translation: str, source: str = "Contemporary dialogue") -> dict[str, str]:
    """Helper to return an example object."""
    return {
        "targetHTML": targetHTML,
        "translation": translation,
        "source": source
    }


def build_portuguese():
    return {
        "de": {
            "word": "de", "role": "Preposition", "rank": 4, "frequency": 25447,
            "relations": [
                rel(
                    "Verbal Valency",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Complement</span>",
                    "Required link: the preceding verb governs 'de' before its object or action.",
                    ["gostar", "precisar", "lembrar", "depender", "esquecer", "tratar", "falar", "desistir"],
                    [
                        ex("<span class='fw-token-v'>Gosto</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>música</span>.", "I like music.", "Ainda Bem · Marisa Monte"),
                        ex("<span class='fw-token-v'>Gostamos</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>passear por aí</span>.", "We like to stroll around.", "Subtitles"),
                        ex("Ele <span class='fw-token-v'>precisa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ajuda agora</span>.", "He needs help now.", "Dialogue"),
                        ex("<span class='fw-token-v'>Lembro-me</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>tudo perfeitamente</span>.", "I remember everything perfectly.", "Conversation"),
                        ex("Isso <span class='fw-token-v'>depende</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>muitas coisas</span>.", "That depends on many things.", "Everyday speech"),
                        ex("Não podemos <span class='fw-token-v'>desistir</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>lutar</span>.", "We cannot give up fighting.", "Film dialogue")
                    ]
                ),
                rel(
                    "Noun Attribution",
                    "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                    "Nominal binding: connects a head noun to its owner, origin, or material.",
                    ["copo", "casa", "carro", "hora", "mesa", "dia", "homem", "tempo"],
                    [
                        ex("Quero um <span class='fw-token-v'>copo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>água</span>.", "I want a glass of water.", "Everyday speech"),
                        ex("Uma <span class='fw-token-v'>mesa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>madeira maciça</span>.", "A solid wood table.", "Conversation"),
                        ex("É <span class='fw-token-v'>hora</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>partir</span>.", "It is time to leave.", "Dialogue"),
                        ex("Um <span class='fw-token-v'>dia</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>sol</span> na praia.", "A sunny day at the beach.", "Subtitles"),
                        ex("Ele é um <span class='fw-token-v'>homem</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>palavra</span>.", "He is a man of his word.", "Literature")
                    ]
                )
            ]
        },
        "que": {
            "word": "que", "role": "Connector", "rank": 1, "frequency": 38240,
            "relations": [
                rel(
                    "Clausal Link",
                    "<span class=\"fw-token-v\">Thought / Speech</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Clause</span>",
                    "Subordination: bridges what someone thinks, says, or knows to the statement.",
                    ["achar", "pensar", "saber", "dizer", "esperar", "ver", "sentir"],
                    [
                        ex("<span class='fw-token-v'>Acho</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vai chover</span>.", "I think it’s going to rain.", "Dialogue"),
                        ex("Ela <span class='fw-token-v'>disse</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>viria hoje</span>.", "She said she would come today.", "Conversation"),
                        ex("<span class='fw-token-v'>Sei</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>você tem razão</span>.", "I know you are right.", "Contemporary speech"),
                        ex("<span class='fw-token-v'>Espero</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>tudo corra bem</span>.", "I hope everything goes well.", "Everyday dialogue"),
                        ex("Ele <span class='fw-token-v'>pensou</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estava sozinho</span>.", "He thought he was alone.", "Subtitles")
                    ]
                ),
                rel(
                    "Relative Pronoun",
                    "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                    "Relativization: refers back to a noun while connecting more information.",
                    ["livro", "pessoa", "filme", "lugar", "coisa", "carro", "casa"],
                    [
                        ex("Este é o <span class='fw-token-v'>livro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estou lendo</span>.", "This is the book that I’m reading.", "Conversation"),
                        ex("A <span class='fw-token-v'>pessoa</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>me ligou não falou nada</span>.", "The person who called me said nothing.", "Dialogue"),
                        ex("O <span class='fw-token-v'>filme</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vimos ontem foi ótimo</span>.", "The movie we saw yesterday was great.", "Subtitles"),
                        ex("O <span class='fw-token-v'>lugar</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>visitamos era lindo</span>.", "The place we visited was beautiful.", "Everyday speech"),
                        ex("São <span class='fw-token-v'>coisas</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>acontecem na vida</span>.", "These are things that happen in life.", "Literature")
                    ]
                ),
                rel(
                    "Comparison",
                    "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                    "Comparison: connects the two sides of a degree or quality difference.",
                    ["mais", "menos", "melhor", "pior", "maior", "menor"],
                    [
                        ex("Ela é <span class='fw-token-v'>mais alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>eu</span>.", "She is taller than me.", "Everyday dialogue"),
                        ex("Isto é <span class='fw-token-v'>melhor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>o esperado</span>.", "This is better than expected.", "Conversation"),
                        ex("Gastamos <span class='fw-token-v'>menos tempo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>ontem</span>.", "We spent less time than yesterday.", "Dialogue"),
                        ex("A casa é <span class='fw-token-v'>maior</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>o apartamento</span>.", "The house is bigger than the apartment.", "Subtitles"),
                        ex("Hoje está <span class='fw-token-v'>mais frio</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>semana passada</span>.", "Today is colder than last week.", "Contemporary speech")
                    ]
                )
            ]
        },
        "naquele": {
            "word": "naquele", "role": "Contraction", "rank": 1104, "frequency": 88,
            "parts": ["em", "aquele"],
            "relations": [
                rel(
                    "Deictic Location",
                    "<span class=\"fw-token-connector\">em + aquele</span> + <span class=\"fw-token-c\">Place / Time</span>",
                    "Contraction formula pointing to a distant place or past moment.",
                    ["lugar", "momento", "dia", "ano", "tempo", "canto"],
                    [
                        ex("Eu estava <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>lugar</span>.", "I was in that place.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Naquele</span> <span class='fw-token-c'>momento</span>, tudo mudou.", "At that moment, everything changed.", "Literature"),
                        ex("Nos conhecemos <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>ano inesquecível</span>.", "We met in that unforgettable year.", "Conversation"),
                        ex("Deixei as chaves <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>quarto</span>.", "I left the keys in that room.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Naquele</span> <span class='fw-token-c'>dia</span> choveu sem parar.", "On that day it rained without stopping.", "Subtitles")
                    ]
                )
            ]
        },
        "nos": {
            "word": "nos", "role": "Pronoun & Contraction", "rank": 44, "frequency": 1581,
            "relations": [
                rel(
                    "Object Pronoun",
                    "<span class=\"fw-token-connector\">nos</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Pronominal argument: represents 'us / to us' receiving the action of a verb.",
                    ["chamar", "ver", "ajudar", "ouvir", "contar", "encontrar"],
                    [
                        ex("Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>chamou</span> para jantar.", "She called us for dinner.", "Conversation"),
                        ex("O professor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ensinou</span> muito.", "The teacher taught us a lot.", "Dialogue"),
                        ex("Eles <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>viram</span> no centro.", "They saw us downtown.", "Subtitles"),
                        ex("Alguém <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ajudou</span> a tempo.", "Someone helped us in time.", "Everyday speech"),
                        ex("Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>contou</span> a verdade.", "She told us the truth.", "Literature")
                    ]
                ),
                rel(
                    "Contraction",
                    "<span class=\"fw-token-connector\">em + os</span> + <span class=\"fw-token-c\">Plural Noun</span>",
                    "Contraction of 'em + os' (in / on / at the) before a masculine plural noun.",
                    ["livro", "olho", "braço", "dia", "parque", "ombro"],
                    [
                        ex("Está <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>livros</span>.", "It’s in the books.", "Dialogue"),
                        ex("Vi a tristeza <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>olhos dele</span>.", "I saw sadness in his eyes.", "Literature"),
                        ex("Passeamos <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>parques da cidade</span>.", "We strolled in the city parks.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Nos</span> <span class='fw-token-c'>dias de festa</span>, a vila enche-se.", "On festival days, the village fills up.", "Conversation"),
                        ex("O peso caiu <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>nossos ombros</span>.", "The weight fell on our shoulders.", "Everyday speech")
                    ],
                    parts=["em", "os"]
                )
            ]
        },
        "se": {
            "word": "se", "role": "Conjunction & Clitic", "rank": 11, "frequency": 7806,
            "relations": [
                rel(
                    "Condition",
                    "<span class=\"fw-token-connector\">Se</span> + <span class=\"fw-token-v\">Condition</span> , <span class=\"fw-token-c\">Result</span>",
                    "Conditional marker: introduces a hypothetical situation before its consequence.",
                    ["chover", "quiser", "puder", "souber", "tiver", "precisar"],
                    [
                        ex("<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>chover</span>, <span class='fw-token-c'>fico em casa</span>.", "If it rains, I’ll stay home.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Se</span> você <span class='fw-token-v'>quiser</span>, <span class='fw-token-c'>podemos ir juntos</span>.", "If you want, we can go together.", "Conversation"),
                        ex("<span class='fw-token-connector'>Se</span> eu <span class='fw-token-v'>souber</span> de algo, <span class='fw-token-c'>aviso</span>.", "If I know anything, I'll let you know.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>tiver tempo</span>, <span class='fw-token-c'>leia este artigo</span>.", "If you have time, read this article.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>precisares</span>, <span class='fw-token-c'>estou aqui</span>.", "If you need, I am here.", "Contemporary dialogue")
                    ]
                ),
                rel(
                    "Reflexive Clitic",
                    "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                    "Reflexive clitic: action reflects back onto the person doing it.",
                    ["olhar", "sentir", "lembrar", "vestir", "lavar", "sentar"],
                    [
                        ex("Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>olhou</span> no espelho.", "She looked at herself in the mirror.", "Literature"),
                        ex("Ele <span class='fw-token-connector'>se</span> <span class='fw-token-v'>sente</span> muito melhor hoje.", "He feels much better today.", "Everyday dialogue"),
                        ex("Eles <span class='fw-token-connector'>se</span> <span class='fw-token-v'>levantaram</span> cedo.", "They got up early.", "Conversation"),
                        ex("O menino <span class='fw-token-connector'>se</span> <span class='fw-token-v'>vestiu</span> rapidamente.", "The boy got dressed quickly.", "Subtitles"),
                        ex("Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>sentou</span> junto à janela.", "She sat down by the window.", "Dialogue")
                    ]
                )
            ]
        },
        "o": {
            "word": "o", "role": "Article & Clitic", "rank": 3, "frequency": 34538,
            "relations": [
                rel(
                    "Definite Article",
                    "<span class=\"fw-token-connector\">o</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                    "Definite determiner: points to a specific masculine singular noun.",
                    ["livro", "carro", "dia", "tempo", "trabalho", "sol"],
                    [
                        ex("<span class='fw-token-connector'>O</span> <span class='fw-token-c'>livro</span> está na mesa.", "The book is on the table.", "Dialogue"),
                        ex("<span class='fw-token-connector'>O</span> <span class='fw-token-c'>carro</span> novo funciona bem.", "The new car works well.", "Conversation"),
                        ex("<span class='fw-token-connector'>O</span> <span class='fw-token-c'>dia</span> começou ensolarado.", "The day began sunny.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>O</span> <span class='fw-token-c'>trabalho</span> foi concluído com sucesso.", "The work was completed successfully.", "Subtitles"),
                        ex("<span class='fw-token-connector'>O</span> <span class='fw-token-c'>sol</span> brilha forte lá fora.", "The sun shines brightly outside.", "Literature")
                    ]
                ),
                rel(
                    "Object Clitic",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">o</span>",
                    "Direct object pronoun: replaces a 3rd-person masculine singular object ('him / it').",
                    ["ver", "encontrar", "conhecer", "ouvir", "deixar", "levar"],
                    [
                        ex("Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>vi</span> ontem no parque.", "I saw him yesterday in the park.", "Conversation"),
                        ex("Não <span class='fw-token-connector'>o</span> <span class='fw-token-v'>encontrei</span> em lugar nenhum.", "I didn't find it anywhere.", "Dialogue"),
                        ex("Todos <span class='fw-token-connector'>o</span> <span class='fw-token-v'>conhecem</span> na cidade.", "Everyone knows him in town.", "Subtitles"),
                        ex("Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>deixei</span> sobre a bancada.", "I left it on the counter.", "Everyday speech"),
                        ex("O guarda <span class='fw-token-connector'>o</span> <span class='fw-token-v'>ouviu</span> gritar.", "The guard heard him yell.", "Literature")
                    ]
                )
            ]
        },
        "em": {
            "word": "em", "role": "Preposition", "rank": 21, "frequency": 6025,
            "relations": [
                rel(
                    "Spatial Location",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Place</span>",
                    "Spatial location: anchors an action or state to an enclosed place, city, or space.",
                    ["morar", "viver", "entrar", "ficar", "estar", "trabalhar"],
                    [
                        ex("<span class='fw-token-v'>Moro</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>Lisboa</span>.", "I live in Lisbon.", "Everyday dialogue"),
                        ex("Eles <span class='fw-token-v'>ficaram</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>casa</span> hoje.", "They stayed at home today.", "Conversation"),
                        ex("<span class='fw-token-v'>Trabalho</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>um hospital</span>.", "I work in a hospital.", "Dialogue"),
                        ex("Nós <span class='fw-token-v'>entramos</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>uma sala ampla</span>.", "We entered a large room.", "Subtitles"),
                        ex("O café <span class='fw-token-v'>fica</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>frente à estação</span>.", "The cafe is in front of the station.", "Contemporary speech")
                    ]
                ),
                rel(
                    "Temporal Framing",
                    "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">em</span> + <span class=\"fw-token-c\">Time Period</span>",
                    "Temporal framing: situates an event within a month, year, or duration.",
                    ["viajar", "nascer", "terminar", "voltar", "chegar", "começar"],
                    [
                        ex("<span class='fw-token-v'>Viajo</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>maio</span>.", "I travel in May.", "Conversation"),
                        ex("Ela <span class='fw-token-v'>nasceu</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>1995</span>.", "She was born in 1995.", "Everyday speech"),
                        ex("Terminaremos <span class='fw-token-connector'>em</span> <span class='fw-token-c'>duas semanas</span>.", "We will finish in two weeks.", "Dialogue"),
                        ex("O curso <span class='fw-token-v'>começa</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>setembro</span>.", "The course starts in September.", "Subtitles"),
                        ex("Eles voltam <span class='fw-token-connector'>em</span> <span class='fw-token-c'>poucos dias</span>.", "They return in a few days.", "Contemporary dialogue")
                    ]
                )
            ]
        },
        "para": {
            "word": "para", "role": "Preposition", "rank": 9, "frequency": 11850,
            "relations": [
                rel(
                    "Destination",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Destination</span>",
                    "Direction and destination: points toward a final physical goal or place of arrival.",
                    ["ir", "viajar", "voltar", "caminhar", "partir", "olhar"],
                    [
                        ex("<span class='fw-token-v'>Vou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>casa</span>.", "I am going home.", "Everyday speech"),
                        ex("Eles <span class='fw-token-v'>viajam</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o Brasil</span>.", "They travel to Brazil.", "Conversation"),
                        ex("Ela <span class='fw-token-v'>olhou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o céu</span>.", "She looked toward the sky.", "Subtitles"),
                        ex("Vamos <span class='fw-token-v'>voltar</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o hotel</span>.", "We are returning to the hotel.", "Dialogue"),
                        ex("O comboio <span class='fw-token-v'>parte</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>o Porto</span>.", "The train departs for Porto.", "Contemporary speech")
                    ]
                ),
                rel(
                    "Purpose",
                    "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Goal</span>",
                    "Purpose and objective: links an intentional action to what it aims to achieve.",
                    ["estudar", "trabalhar", "sair", "parar", "correr", "ligar"],
                    [
                        ex("<span class='fw-token-v'>Estudo</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.", "I study in order to learn.", "Conversation"),
                        ex("Trabalho <span class='fw-token-connector'>para</span> <span class='fw-token-c'>sustentar minha família</span>.", "I work in order to support my family.", "Everyday speech"),
                        ex("Ligou <span class='fw-token-connector'>para</span> <span class='fw-token-c'>saber notícias</span>.", "Called in order to get news.", "Dialogue"),
                        ex("Paramos <span class='fw-token-connector'>para</span> <span class='fw-token-c'>descansar um pouco</span>.", "We stopped in order to rest a bit.", "Subtitles"),
                        ex("Correu <span class='fw-token-connector'>para</span> <span class='fw-token-c'>não perder o autocarro</span>.", "Ran in order not to miss the bus.", "Literature")
                    ]
                ),
                rel(
                    "Recipient",
                    "<span class=\"fw-token-v\">Object</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                    "Beneficiary: marks who receives or benefits from something.",
                    ["presente", "carta", "comida", "mensagem", "dinheiro", "espaço"],
                    [
                        ex("Isto é <span class='fw-token-v'>um presente</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>você</span>.", "This is a gift for you.", "Conversation"),
                        ex("Escrevi <span class='fw-token-v'>uma carta</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>meus pais</span>.", "I wrote a letter to my parents.", "Dialogue"),
                        ex("Cozinhei <span class='fw-token-v'>jantar</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>todos nós</span>.", "I cooked dinner for all of us.", "Everyday speech"),
                        ex("Há lugar <span class='fw-token-connector'>para</span> <span class='fw-token-c'>mais uma pessoa</span>?", "Is there room for one more person?", "Subtitles"),
                        ex("Deixei <span class='fw-token-v'>um bilhete</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ela</span>.", "I left a note for her.", "Literature")
                    ]
                )
            ]
        },
        "com": {
            "word": "com", "role": "Preposition", "rank": 17, "frequency": 7842,
            "relations": [
                rel(
                    "Accompaniment",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Companion</span>",
                    "Accompaniment: joins an action to the person or entity sharing it.",
                    ["falar", "sair", "viajar", "almoçar", "viver", "trabalhar"],
                    [
                        ex("<span class='fw-token-v'>Falo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>você</span> amanhã.", "I speak with you tomorrow.", "Everyday dialogue"),
                        ex("Fui ao cinema <span class='fw-token-connector'>com</span> <span class='fw-token-c'>meus amigos</span>.", "I went to the cinema with my friends.", "Conversation"),
                        ex("Ela <span class='fw-token-v'>mora</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>a irmã</span>.", "She lives with her sister.", "Dialogue"),
                        ex("Quero <span class='fw-token-v'>conversar</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>o gerente</span>.", "I want to speak with the manager.", "Subtitles"),
                        ex("Nós <span class='fw-token-v'>trabalhamos</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>profissionais excelentes</span>.", "We work with excellent professionals.", "Contemporary speech")
                    ]
                ),
                rel(
                    "Instrument and Manner",
                    "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">com</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                    "Instrument and manner: describes the means used or attitude applied.",
                    ["escrever", "cortar", "fazer", "ouvir", "olhar", "tratar"],
                    [
                        ex("<span class='fw-token-v'>Escrevo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>cuidado</span>.", "I write with care.", "Dialogue"),
                        ex("Ele abriu a porta <span class='fw-token-connector'>com</span> <span class='fw-token-c'>a chave reserva</span>.", "He opened the door with the spare key.", "Conversation"),
                        ex("Ouvimos tudo <span class='fw-token-connector'>com</span> <span class='fw-token-c'>muita atenção</span>.", "We listened to everything with great attention.", "Subtitles"),
                        ex("Cortei o papel <span class='fw-token-connector'>com</span> <span class='fw-token-c'>uma tesoura</span>.", "I cut the paper with scissors.", "Everyday speech"),
                        ex("Tratou os convidados <span class='fw-token-connector'>com</span> <span class='fw-token-c'>extrema simpatia</span>.", "Treated the guests with extreme warmth.", "Literature")
                    ]
                )
            ]
        },
        "por": {
            "word": "por", "role": "Preposition", "rank": 16, "frequency": 6938,
            "relations": [
                rel(
                    "Cause / Motive",
                    "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                    "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                    ["obrigado", "esperar", "lutar", "chorar", "pagar", "agradecer"],
                    [
                        ex("<span class='fw-token-v'>Obrigado</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>ajudar</span>.", "Thank you for helping.", "Everyday speech"),
                        ex("Espero <span class='fw-token-connector'>por</span> <span class='fw-token-c'>notícias suas</span>.", "I wait for news from you.", "Dialogue"),
                        ex("Ele foi elogiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>sua coragem</span>.", "He was praised for his courage.", "Literature"),
                        ex("Pagou vinte euros <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aquele livro</span>.", "Paid twenty euros for that book.", "Conversation"),
                        ex("Agradeço <span class='fw-token-connector'>por</span> <span class='fw-token-c'>toda a paciência</span>.", "I thank you for all the patience.", "Subtitles")
                    ]
                ),
                rel(
                    "Trajectory",
                    "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                    "Trajectory: marks the path, medium, or space through which motion occurs.",
                    ["caminhar", "passar", "andar", "viajar", "olhar", "entrar"],
                    [
                        ex("<span class='fw-token-v'>Caminho</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aqui</span>.", "I walk around here.", "Dialogue"),
                        ex("Passamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>uma ponte antiga</span>.", "We passed through an old bridge.", "Conversation"),
                        ex("Olhou <span class='fw-token-connector'>por</span> <span class='fw-token-c'>entre as grades</span>.", "Looked through between the railings.", "Literature"),
                        ex("O gato entrou <span class='fw-token-connector'>por</span> <span class='fw-token-c'>uma brecha na janela</span>.", "The cat entered through a gap in the window.", "Subtitles"),
                        ex("Viajamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>estradas desertas</span>.", "We traveled through deserted roads.", "Contemporary speech")
                    ]
                )
            ]
        },
        "no": {
            "word": "no", "role": "Contraction", "rank": 13, "frequency": 4450,
            "parts": ["em", "o"],
            "relations": [
                rel(
                    "Spatial / Temporal Location",
                    "<span class=\"fw-token-connector\">em + o</span> + <span class=\"fw-token-c\">Masculine Noun / Place</span>",
                    "Contraction of 'em + o' (in the / at the) before a specific masculine noun.",
                    ["quarto", "trabalho", "carro", "mundo", "cinema", "hospital"],
                    [
                        ex("O livro está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>quarto</span>.", "The book is in the room.", "Everyday dialogue"),
                        ex("Ele ainda está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>trabalho</span>.", "He is still at work.", "Conversation"),
                        ex("Nos encontramos <span class='fw-token-connector'>no</span> <span class='fw-token-c'>cinema às oito</span>.", "We met at the cinema at eight.", "Subtitles"),
                        ex("Não há ninguém como ele <span class='fw-token-connector'>no</span> <span class='fw-token-c'>mundo</span>.", "There is no one like him in the world.", "Literature"),
                        ex("Esqueci a carteira <span class='fw-token-connector'>no</span> <span class='fw-token-c'>carro</span>.", "I forgot my wallet in the car.", "Dialogue")
                    ]
                )
            ]
        },
        "na": {
            "word": "na", "role": "Contraction", "rank": 31, "frequency": 4170,
            "parts": ["em", "a"],
            "relations": [
                rel(
                    "Spatial / Temporal Location",
                    "<span class=\"fw-token-connector\">em + a</span> + <span class=\"fw-token-c\">Feminine Noun / Place</span>",
                    "Contraction of 'em + a' (in the / at the) before a specific feminine noun.",
                    ["praia", "mesa", "rua", "cidade", "escola", "cozinha"],
                    [
                        ex("Ela está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>praia</span>.", "She is at the beach.", "Conversation"),
                        ex("A carta está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>mesa da sala</span>.", "The letter is on the living room table.", "Dialogue"),
                        ex("Vi muitas pessoas <span class='fw-token-connector'>na</span> <span class='fw-token-c'>rua principal</span>.", "I saw many people on the main street.", "Subtitles"),
                        ex("As crianças estão <span class='fw-token-connector'>na</span> <span class='fw-token-c'>escola agora</span>.", "The children are at school now.", "Everyday speech"),
                        ex("Ela cozinha <span class='fw-token-connector'>na</span> <span class='fw-token-c'>cozinha espaçosa</span>.", "She cooks in the spacious kitchen.", "Literature")
                    ]
                )
            ]
        },
        "do": {
            "word": "do", "role": "Contraction", "rank": 19, "frequency": 7403,
            "parts": ["de", "o"],
            "relations": [
                rel(
                    "Possession / Origin",
                    "<span class=\"fw-token-connector\">de + o</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                    "Contraction of 'de + o' (of the / from the) denoting possession, origin, or attribute.",
                    ["pai", "hotel", "filme", "livro", "Brasil", "governo"],
                    [
                        ex("Este é o carro <span class='fw-token-connector'>do</span> <span class='fw-token-c'>meu pai</span>.", "This is my father's car.", "Conversation"),
                        ex("A porta <span class='fw-token-connector'>do</span> <span class='fw-token-c'>hotel</span> estava fechada.", "The hotel door was closed.", "Dialogue"),
                        ex("Gostei muito <span class='fw-token-connector'>do</span> <span class='fw-token-c'>final do filme</span>.", "I liked the end of the movie a lot.", "Subtitles"),
                        ex("Ele veio direto <span class='fw-token-connector'>do</span> <span class='fw-token-c'>aeroporto</span>.", "He came straight from the airport.", "Everyday speech"),
                        ex("A decisão <span class='fw-token-connector'>do</span> <span class='fw-token-c'>juiz foi definitiva</span>.", "The judge's decision was final.", "Literature")
                    ]
                )
            ]
        },
        "da": {
            "word": "da", "role": "Contraction", "rank": 27, "frequency": 5714,
            "parts": ["de", "a"],
            "relations": [
                rel(
                    "Possession / Origin",
                    "<span class=\"fw-token-connector\">de + a</span> + <span class=\"fw-token-c\">Feminine Noun / Origin</span>",
                    "Contraction of 'de + a' (of the / from the) denoting possession, origin, or attribute.",
                    ["casa", "mãe", "cidade", "vida", "janela", "música"],
                    [
                        ex("Esta é a chave <span class='fw-token-connector'>da</span> <span class='fw-token-c'>casa</span>.", "This is the key to the house.", "Dialogue"),
                        ex("O sorriso <span class='fw-token-connector'>da</span> <span class='fw-token-c'>mãe acalmou a todos</span>.", "The mother's smile calmed everyone.", "Literature"),
                        ex("A vista <span class='fw-token-connector'>da</span> <span class='fw-token-c'>janela é deslumbrante</span>.", "The view from the window is breathtaking.", "Conversation"),
                        ex("Conhecemos os cantos <span class='fw-token-connector'>da</span> <span class='fw-token-c'>cidade antiga</span>.", "We know the corners of the old city.", "Subtitles"),
                        ex("O ritmo <span class='fw-token-connector'>da</span> <span class='fw-token-c'>música empolgou a sala</span>.", "The rhythm of the music excited the room.", "Everyday speech")
                    ]
                )
            ]
        },
        "como": {
            "word": "como", "role": "Connector", "rank": 23, "frequency": 5447,
            "relations": [
                rel(
                    "Manner / Simile",
                    "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Model / Standard</span>",
                    "Simile and manner: compares the style or way an action is performed to an archetype.",
                    ["cantar", "agir", "falar", "brilhar", "correr", "tratar"],
                    [
                        ex("Ela <span class='fw-token-v'>canta</span> <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um pássaro</span>.", "She sings like a bird.", "Everyday dialogue"),
                        ex("Ele agiu <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um verdadeiro herói</span>.", "He acted like a true hero.", "Conversation"),
                        ex("Seus olhos brilham <span class='fw-token-connector'>como</span> <span class='fw-token-c'>estrelas</span>.", "Her eyes shine like stars.", "Literature"),
                        ex("Faz as coisas <span class='fw-token-connector'>como</span> <span class='fw-token-c'>sempre fez</span>.", "Does things like he always did.", "Subtitles"),
                        ex("Correu rápido <span class='fw-token-connector'>como</span> <span class='fw-token-c'>o vento</span>.", "Ran fast like the wind.", "Dialogue")
                    ]
                ),
                rel(
                    "Capacity / Role",
                    "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Role / Capacity</span>",
                    "Capacity and function: specifies the role, profession, or capacity someone acts in.",
                    ["engenheiro", "médico", "professor", "voluntário", "testemunha"],
                    [
                        ex("Trabalho <span class='fw-token-connector'>como</span> <span class='fw-token-c'>engenheiro</span>.", "I work as an engineer.", "Conversation"),
                        ex("Ele atuou <span class='fw-token-connector'>como</span> <span class='fw-token-c'>porta-voz do grupo</span>.", "He acted as spokesperson for the group.", "Dialogue"),
                        ex("Ela participou <span class='fw-token-connector'>como</span> <span class='fw-token-c'>voluntária no projeto</span>.", "She took part as a volunteer in the project.", "Subtitles"),
                        ex("Falo <span class='fw-token-connector'>como</span> <span class='fw-token-c'>amigo preocupado</span>.", "I speak as a concerned friend.", "Everyday speech"),
                        ex("Foi chamado <span class='fw-token-connector'>como</span> <span class='fw-token-c'>testemunha principal</span>.", "Was called as chief witness.", "Literature")
                    ]
                )
            ]
        },
        "mas": {
            "word": "mas", "role": "Connector", "rank": 26, "frequency": 6058,
            "relations": [
                rel(
                    "Contrast",
                    "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">mas</span> + <span class=\"fw-token-c\">Counterpoint</span>",
                    "Adversative bridge: introduces a contrast, restriction, or unexpected limitation.",
                    ["tentar", "querer", "procurar", "saber", "chamar"],
                    [
                        ex("<span class='fw-token-v'>Tentei</span>, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>não consegui</span>.", "I tried, but I could not.", "Dialogue"),
                        ex("Queria sair, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>estava a chover forte</span>.", "I wanted to go out, but it was raining hard.", "Conversation"),
                        ex("Ele sabia a resposta, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>ficou calado</span>.", "He knew the answer, but stayed silent.", "Subtitles"),
                        ex("Procurei por todo o lado, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>nada encontrei</span>.", "I searched everywhere, but found nothing.", "Literature"),
                        ex("O plano era bom, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>faltou tempo</span>.", "The plan was good, but time ran short.", "Everyday speech")
                    ]
                )
            ]
        },
        "a": {
            "word": "a", "role": "Preposition & Article", "rank": 2, "frequency": 35946,
            "relations": [
                rel(
                    "Directional Link",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Destination</span>",
                    "Directional link: points to a target destination or recipient.",
                    ["ir", "chegar", "voltar", "escrever", "entregar", "levar"],
                    [
                        ex("Vou <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Lisboa</span> amanhã.", "I go to Lisbon tomorrow.", "Conversation"),
                        ex("Chegamos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>casa são e salvos</span>.", "We arrived home safe and sound.", "Dialogue"),
                        ex("Entregou o documento <span class='fw-token-connector'>a</span> <span class='fw-token-c'>ele</span>.", "Delivered the document to him.", "Subtitles"),
                        ex("Escreveu uma nota <span class='fw-token-connector'>a</span> <span class='fw-token-c'>um amigo</span>.", "Wrote a note to a friend.", "Everyday speech"),
                        ex("Eles voltaram <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Porto Alegre</span>.", "They returned to Porto Alegre.", "Literature")
                    ]
                ),
                rel(
                    "Definite Article",
                    "<span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                    "Definite feminine article: specifies a singular feminine entity.",
                    ["casa", "porta", "cidade", "noite", "vida", "viagem"],
                    [
                        ex("<span class='fw-token-connector'>A</span> <span class='fw-token-c'>casa</span> é bonita.", "The house is pretty.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>A</span> <span class='fw-token-c'>porta</span> principal estava trancada.", "The main door was locked.", "Dialogue"),
                        ex("<span class='fw-token-connector'>A</span> <span class='fw-token-c'>cidade</span> acorda cedo.", "The city wakes up early.", "Subtitles"),
                        ex("<span class='fw-token-connector'>A</span> <span class='fw-token-c'>noite</span> estava fresca e calma.", "The night was cool and quiet.", "Literature"),
                        ex("<span class='fw-token-connector'>A</span> <span class='fw-token-c'>viagem</span> correu muito bem.", "The trip went very well.", "Conversation")
                    ]
                ),
                rel(
                    "Direct Object Pronoun",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span>",
                    "Direct object pronoun: replaces a singular 3rd-person feminine noun ('her / it').",
                    ["conhecer", "ver", "ouvir", "ajudar", "chamar"],
                    [
                        ex("Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>conheço</span> bem.", "I know her well.", "Conversation"),
                        ex("Eu <span class='fw-token-connector'>a</span> <span class='fw-token-v'>vi</span> ontem à tarde.", "I saw her yesterday afternoon.", "Dialogue"),
                        ex("Todos <span class='fw-token-connector'>a</span> <span class='fw-token-v'>respeitam</span> pelo trabalho sério.", "Everyone respects her for her earnest work.", "Subtitles"),
                        ex("Nunca mais <span class='fw-token-connector'>a</span> <span class='fw-token-v'>encontrei</span> depois disso.", "I never met her again after that.", "Literature"),
                        ex("O médico <span class='fw-token-connector'>a</span> <span class='fw-token-v'>examinou</span> com cuidado.", "The doctor examined her carefully.", "Everyday speech")
                    ]
                )
            ]
        },
        "e": {
            "word": "e", "role": "Connector", "rank": 5, "frequency": 17238,
            "relations": [
                rel(
                    "Addition",
                    "<span class=\"fw-token-v\">Item / Clause</span> + <span class=\"fw-token-connector\">e</span> + <span class=\"fw-token-c\">Addition</span>",
                    "Copulative coordinator: links equal grammatical items or consecutive actions.",
                    ["pão", "água", "dia", "entrar", "falar", "sorrir"],
                    [
                        ex("Comprei pão <span class='fw-token-connector'>e</span> <span class='fw-token-c'>queijo</span>.", "I bought bread and cheese.", "Everyday speech"),
                        ex("Ele levantou-se <span class='fw-token-connector'>e</span> <span class='fw-token-c'>abriu a janela</span>.", "He stood up and opened the window.", "Dialogue"),
                        ex("Trabalho de dia <span class='fw-token-connector'>e</span> <span class='fw-token-c'>estudo à noite</span>.", "I work during the day and study at night.", "Conversation"),
                        ex("Ela sorriu <span class='fw-token-connector'>e</span> <span class='fw-token-c'>agradeceu a ajuda</span>.", "She smiled and thanked for the help.", "Literature"),
                        ex("Comemos fruta <span class='fw-token-connector'>e</span> <span class='fw-token-c'>bebemos sumo fresco</span>.", "We ate fruit and drank fresh juice.", "Subtitles")
                    ]
                )
            ]
        },
        "eu": {
            "word": "eu", "role": "Subject Pronoun", "rank": 8, "frequency": 10606,
            "relations": [
                rel(
                    "Subject Pronoun",
                    "<span class=\"fw-token-connector\">Eu</span> + <span class=\"fw-token-v\">Verb (1st Sing)</span>",
                    "Subject pronoun: emphasizes or clarifies the first-person singular actor.",
                    ["morar", "saber", "querer", "pensar", "estar", "fazer"],
                    [
                        ex("<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>moro</span> aqui.", "I live here.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>sei</span> exatamente o que fazer.", "I know exactly what to do.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>quero</span> falar com você.", "I want to talk with you.", "Conversation"),
                        ex("<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>estou</span> pronto para começar.", "I am ready to start.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Eu</span> <span class='fw-token-v'>fiz</span> o melhor que pude.", "I did the best that I could.", "Literature")
                    ]
                )
            ]
        },
        "ele": {
            "word": "ele", "role": "Subject & Object Pronoun", "rank": 15, "frequency": 6225,
            "relations": [
                rel(
                    "Subject Pronoun",
                    "<span class=\"fw-token-connector\">Ele</span> + <span class=\"fw-token-v\">Verb (3rd Sing)</span>",
                    "Subject pronoun: marks a 3rd-person masculine singular actor ('he / it').",
                    ["trabalhar", "chegar", "dizer", "saber", "viver"],
                    [
                        ex("<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>trabalha</span> muito.", "He works a lot.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>chegou</span> na hora combinada.", "He arrived at the agreed time.", "Conversation"),
                        ex("<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>sabe</span> o caminho de volta.", "He knows the way back.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>disse</span> que viria cedo.", "He said he would come early.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Ele</span> <span class='fw-token-v'>vive</span> num mundo próprio.", "He lives in a world of his own.", "Literature")
                    ]
                ),
                rel(
                    "Prepositional Object",
                    "<span class=\"fw-token-v\">Preposition</span> + <span class=\"fw-token-connector\">ele</span>",
                    "Prepositional object: follows prepositions like 'com ele' or 'para ele'.",
                    ["com", "para", "sem", "sobre", "por", "até"],
                    [
                        ex("Falei com <span class='fw-token-connector'>ele</span> ontem.", "I spoke with him yesterday.", "Conversation"),
                        ex("Isto é para <span class='fw-token-connector'>ele</span>.", "This is for him.", "Dialogue"),
                        ex("Não podemos decidir sem <span class='fw-token-connector'>ele</span>.", "We cannot decide without him.", "Everyday speech"),
                        ex("Todos perguntaram por <span class='fw-token-connector'>ele</span>.", "Everyone asked for him.", "Subtitles"),
                        ex("Escreveram uma matéria sobre <span class='fw-token-connector'>ele</span>.", "They wrote an article about him.", "Literature")
                    ]
                )
            ]
        },
        "ela": {
            "word": "ela", "role": "Subject & Object Pronoun", "rank": 27, "frequency": 3530,
            "relations": [
                rel(
                    "Subject Pronoun",
                    "<span class=\"fw-token-connector\">Ela</span> + <span class=\"fw-token-v\">Verb (3rd Sing)</span>",
                    "Subject pronoun: marks a 3rd-person feminine singular actor ('she / it').",
                    ["saber", "falar", "sorrir", "estudar", "voltar"],
                    [
                        ex("<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sabe</span> a resposta.", "She knows the answer.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>fala</span> três línguas fluentemente.", "She speaks three languages fluently.", "Conversation"),
                        ex("<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>sorriu</span> calorosamente para nós.", "She smiled warmly at us.", "Literature"),
                        ex("<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>estuda</span> medicina na capital.", "She studies medicine in the capital.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Ela</span> <span class='fw-token-v'>voltou</span> de viagem ontem.", "She returned from her trip yesterday.", "Subtitles")
                    ]
                )
            ]
        },
        "um": {
            "word": "um", "role": "Article & Number", "rank": 6, "frequency": 12840,
            "relations": [
                rel(
                    "Indefinite Article",
                    "<span class=\"fw-token-connector\">um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                    "Indefinite article: introduces an unspecific singular masculine noun.",
                    ["irmão", "amigo", "dia", "livro", "café", "lugar"],
                    [
                        ex("Tenho <span class='fw-token-connector'>um</span> <span class='fw-token-c'>irmão</span>.", "I have a brother.", "Everyday dialogue"),
                        ex("Conheci <span class='fw-token-connector'>um</span> <span class='fw-token-c'>amigo legal</span>.", "I met a cool friend.", "Conversation"),
                        ex("Tomamos <span class='fw-token-connector'>um</span> <span class='fw-token-c'>café juntos</span>.", "We had a coffee together.", "Dialogue"),
                        ex("Li <span class='fw-token-connector'>um</span> <span class='fw-token-c'>livro fantástico</span>.", "I read a fantastic book.", "Subtitles"),
                        ex("Procuramos <span class='fw-token-connector'>um</span> <span class='fw-token-c'>lugar tranquilo</span>.", "We looked for a quiet place.", "Literature")
                    ]
                )
            ]
        },
        "uma": {
            "word": "uma", "role": "Article & Number", "rank": 9, "frequency": 9531,
            "relations": [
                rel(
                    "Indefinite Article",
                    "<span class=\"fw-token-connector\">uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                    "Indefinite article: introduces an unspecific singular feminine noun.",
                    ["fotografia", "ideia", "semana", "casa", "pergunta", "história"],
                    [
                        ex("Vi <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>fotografia</span>.", "I saw a photograph.", "Conversation"),
                        ex("Ela teve <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>ideia brilhante</span>.", "She had a brilliant idea.", "Dialogue"),
                        ex("Ficarei aqui por <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>semana</span>.", "I will stay here for a week.", "Everyday speech"),
                        ex("Quero fazer <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>pergunta simples</span>.", "I want to ask a simple question.", "Subtitles"),
                        ex("Contou-nos <span class='fw-token-connector'>uma</span> <span class='fw-token-c'>história engraçada</span>.", "Told us a funny story.", "Literature")
                    ]
                )
            ]
        },
        "os": {
            "word": "os", "role": "Article & Pronoun", "rank": 14, "frequency": 6233,
            "relations": [
                rel(
                    "Definite Article",
                    "<span class=\"fw-token-connector\">os</span> + <span class=\"fw-token-c\">Plural Masculine Noun</span>",
                    "Definite article: introduces specific masculine plural nouns.",
                    ["livros", "dias", "olhos", "amigos", "homens", "carros"],
                    [
                        ex("<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>livros</span> estão na mesa.", "The books are on the table.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>dias</span> passam voando.", "The days fly by.", "Conversation"),
                        ex("<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>meus amigos</span> chegam logo.", "My friends arrive soon.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>olhos dela</span> brilhavam.", "Her eyes were shining.", "Literature"),
                        ex("<span class='fw-token-connector'>Os</span> <span class='fw-token-c'>carros</span> pararam no sinal.", "The cars stopped at the light.", "Subtitles")
                    ]
                ),
                rel(
                    "Direct Object Pronoun",
                    "<span class=\"fw-token-connector\">os</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Direct object pronoun: replaces 3rd-person masculine plural objects ('them').",
                    ["ver", "comprar", "conhecer", "ouvir", "deixar"],
                    [
                        ex("Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>vi</span> no cinema.", "I saw them at the movies.", "Conversation"),
                        ex("Não <span class='fw-token-connector'>os</span> <span class='fw-token-v'>encontrei</span> em casa.", "I did not find them at home.", "Dialogue"),
                        ex("Eu <span class='fw-token-connector'>os</span> <span class='fw-token-v'>comprei</span> na feira de manhã.", "I bought them at the morning market.", "Everyday speech"),
                        ex("O professor <span class='fw-token-connector'>os</span> <span class='fw-token-v'>chamou</span> para conversar.", "The teacher called them to talk.", "Subtitles"),
                        ex("Guardei<span class='fw-token-connector'>-os</span> com cuidado.", "I stored them carefully.", "Literature")
                    ]
                )
            ]
        },
        "as": {
            "word": "as", "role": "Article & Pronoun", "rank": 21, "frequency": 4513,
            "relations": [
                rel(
                    "Definite Article",
                    "<span class=\"fw-token-connector\">as</span> + <span class=\"fw-token-c\">Plural Feminine Noun</span>",
                    "Definite article: introduces specific feminine plural nouns.",
                    ["portas", "flores", "coisas", "horas", "pessoas", "ruas"],
                    [
                        ex("<span class='fw-token-connector'>As</span> <span class='fw-token-c'>portas</span> estão abertas.", "The doors are open.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>As</span> <span class='fw-token-c'>flores</span> do jardim desabrocharam.", "The garden flowers blossomed.", "Conversation"),
                        ex("<span class='fw-token-connector'>As</span> <span class='fw-token-c'>pessoas</span> aplaudiram de pé.", "The people gave a standing ovation.", "Dialogue"),
                        ex("<span class='fw-token-connector'>As</span> <span class='fw-token-c'>ruas</span> estavam iluminadas.", "The streets were illuminated.", "Subtitles"),
                        ex("Entendo bem <span class='fw-token-connector'>as</span> <span class='fw-token-c'>tuas dúvidas</span>.", "I understand your questions well.", "Literature")
                    ]
                )
            ]
        },
        "me": {
            "word": "me", "role": "Object Pronoun", "rank": 25, "frequency": 3763,
            "relations": [
                rel(
                    "Object Pronoun",
                    "<span class=\"fw-token-connector\">me</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Object pronoun: represents 'me / to me' receiving direct or indirect action.",
                    ["ajudar", "chamar", "ouvir", "dar", "dizer", "avisar"],
                    [
                        ex("Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ajudou</span> hoje.", "He helped me today.", "Everyday dialogue"),
                        ex("Ela <span class='fw-token-connector'>me</span> <span class='fw-token-v'>chamou</span> para jantar.", "She invited me for dinner.", "Conversation"),
                        ex("Você <span class='fw-token-connector'>me</span> <span class='fw-token-v'>ouviu</span> bem?", "Did you hear me well?", "Dialogue"),
                        ex("Ele <span class='fw-token-connector'>me</span> <span class='fw-token-v'>deu</span> um bom conselho.", "He gave me good advice.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>avisa</span> quando chegar.", "Let me know when you arrive.", "Contemporary speech")
                    ]
                ),
                rel(
                    "Reflexive Clitic",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">-me</span>",
                    "Reflexive clitic: action reflects back onto the speaker ('myself').",
                    ["lembrar", "sentir", "sentar", "levantar", "esquecer"],
                    [
                        ex("<span class='fw-token-v'>Lembro</span><span class='fw-token-connector'>-me</span> de tudo.", "I remember everything.", "Dialogue"),
                        ex("<span class='fw-token-v'>Sinto</span><span class='fw-token-connector'>-me</span> ótimo depois do descanso.", "I feel great after resting.", "Conversation"),
                        ex("<span class='fw-token-v'>Sentei</span><span class='fw-token-connector'>-me</span> no banco da praça.", "I sat down on the square bench.", "Subtitles"),
                        ex("<span class='fw-token-v'>Esqueci</span><span class='fw-token-connector'>-me</span> da carteira em casa.", "I forgot my wallet at home.", "Everyday speech"),
                        ex("<span class='fw-token-v'>Levantei</span><span class='fw-token-connector'>-me</span> ao amanhecer.", "I got up at daybreak.", "Literature")
                    ]
                )
            ]
        },
        "te": {
            "word": "te", "role": "Object Pronoun", "rank": 33, "frequency": 2675,
            "relations": [
                rel(
                    "Object Pronoun",
                    "<span class=\"fw-token-connector\">te</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Object pronoun: represents 2nd-person 'you / to you' (informal).",
                    ["amar", "ver", "ligar", "dizer", "ouvir", "esperar"],
                    [
                        ex("Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>amo</span>.", "I love you.", "Everyday dialogue"),
                        ex("Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>vi</span> ontem à tarde.", "I saw you yesterday afternoon.", "Conversation"),
                        ex("Eu <span class='fw-token-connector'>te</span> <span class='fw-token-v'>ligo</span> mais tarde.", "I will call you later.", "Dialogue"),
                        ex("Vou <span class='fw-token-connector'>te</span> <span class='fw-token-v'>contar</span> uma novidade.", "I will tell you some news.", "Subtitles"),
                        ex("Nós <span class='fw-token-connector'>te</span> <span class='fw-token-v'>esperamos</span> no saguão.", "We wait for you in the lobby.", "Literature")
                    ]
                )
            ]
        },
        "lhe": {
            "word": "lhe", "role": "Indirect Pronoun", "rank": 48, "frequency": 1490,
            "relations": [
                rel(
                    "Indirect Object",
                    "<span class=\"fw-token-connector\">lhe</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Indirect object pronoun: represents 'to him / to her / to you'.",
                    ["dar", "dizer", "entregar", "perguntar", "enviar", "pedir"],
                    [
                        ex("Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>dei</span> o livro.", "I gave him the book.", "Dialogue"),
                        ex("Ela <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>disse</span> a verdade.", "She told him the truth.", "Conversation"),
                        ex("O carteiro <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>entregou</span> a encomenda.", "The mail carrier delivered the package to her.", "Subtitles"),
                        ex("Eu <span class='fw-token-connector'>lhe</span> <span class='fw-token-v'>enviei</span> uma mensagem ontem.", "I sent him a message yesterday.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Lhe</span> <span class='fw-token-v'>desejo</span> toda a sorte do mundo.", "I wish you all the luck in the world.", "Literature")
                    ]
                )
            ]
        },
        "ao": {
            "word": "ao", "role": "Contraction", "rank": 32, "frequency": 2773,
            "parts": ["a", "o"],
            "relations": [
                rel(
                    "Direction / Destination",
                    "<span class=\"fw-token-connector\">a + o</span> + <span class=\"fw-token-c\">Masculine Destination / Time</span>",
                    "Contraction of 'a + o' (to the / at the) before masculine singular nouns.",
                    ["mercado", "cinema", "trabalho", "fim", "redor"],
                    [
                        ex("Vou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>mercado</span>.", "I am going to the market.", "Everyday dialogue"),
                        ex("Fomos <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>cinema</span> ver a estreia.", "We went to the cinema to see the premiere.", "Conversation"),
                        ex("Voltou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>trabalho na segunda-feira</span>.", "Returned to work on Monday.", "Dialogue"),
                        ex("Chegamos <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>fim da jornada</span>.", "We reached the end of the journey.", "Literature"),
                        ex("Olhou <span class='fw-token-connector'>ao</span> <span class='fw-token-c'>redor com curiosidade</span>.", "Looked around with curiosity.", "Subtitles")
                    ]
                ),
                rel(
                    "Temporal Nexus",
                    "<span class=\"fw-token-connector\">ao</span> + <span class=\"fw-token-v\">Infinitive</span>",
                    "Temporal nexus: expresses 'upon doing' or 'at the moment of'.",
                    ["chegar", "ouvir", "entrar", "abrir", "sair"],
                    [
                        ex("<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>chegar</span>, avise-me.", "Upon arriving, let me know.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>ouvir</span> o sinal, todos saíram.", "Upon hearing the signal, everyone left.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>abrir</span> a porta, sentiu o vento frio.", "Upon opening the door, felt the cold wind.", "Literature"),
                        ex("Sorriu <span class='fw-token-connector'>ao</span> <span class='fw-token-v'>ver</span> os velhos amigos.", "Smiled upon seeing the old friends.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Ao</span> <span class='fw-token-v'>entrar</span> na sala, percebeu o silêncio.", "Upon entering the room, noticed the silence.", "Conversation")
                    ]
                )
            ]
        },
        "à": {
            "word": "à", "role": "Contraction", "rank": 29, "frequency": 2819,
            "parts": ["a", "a"],
            "relations": [
                rel(
                    "Destination / Time",
                    "<span class=\"fw-token-connector\">a + a</span> + <span class=\"fw-token-c\">Feminine Destination / Time</span>",
                    "Crasis contraction of 'a + a' (to the / at the) before feminine singular nouns.",
                    ["noite", "praia", "escola", "hora", "tarde"],
                    [
                        ex("Chegamos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>noite</span>.", "We arrived at night.", "Dialogue"),
                        ex("Fomos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>praia tomar sol</span>.", "We went to the beach to sunbathe.", "Conversation"),
                        ex("As crianças foram <span class='fw-token-connector'>à</span> <span class='fw-token-c'>escola de manhã</span>.", "The kids went to school in the morning.", "Everyday speech"),
                        ex("O filme começa <span class='fw-token-connector'>à</span> <span class='fw-token-c'>uma da tarde</span>.", "The film begins at one in the afternoon.", "Subtitles"),
                        ex("Voltaremos <span class='fw-token-connector'>à</span> <span class='fw-token-c'>nossa rotina habitual</span>.", "We will return to our usual routine.", "Literature")
                    ]
                )
            ]
        },
        "pelo": {
            "word": "pelo", "role": "Contraction", "rank": 36, "frequency": 2420,
            "parts": ["por", "o"],
            "relations": [
                rel(
                    "Path / Motive",
                    "<span class=\"fw-token-connector\">por + o</span> + <span class=\"fw-token-c\">Masculine Path / Reason</span>",
                    "Contraction of 'por + o' (through the / by the / for the).",
                    ["parque", "caminho", "trabalho", "apoio", "mundo"],
                    [
                        ex("Caminhei <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>parque</span>.", "I walked through the park.", "Everyday speech"),
                        ex("Obrigado <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>apoio constante</span>.", "Thank you for the constant support.", "Dialogue"),
                        ex("Passamos <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>caminho mais curto</span>.", "We passed through the shortest path.", "Conversation"),
                        ex("Foi reconhecido <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>bom trabalho</span>.", "Was recognized for the good work.", "Subtitles"),
                        ex("Viajou <span class='fw-token-connector'>pelo</span> <span class='fw-token-c'>mundo todo</span>.", "Traveled throughout the whole world.", "Literature")
                    ]
                )
            ]
        },
        "pela": {
            "word": "pela", "role": "Contraction", "rank": 37, "frequency": 2350,
            "parts": ["por", "a"],
            "relations": [
                rel(
                    "Path / Motive",
                    "<span class=\"fw-token-connector\">por + a</span> + <span class=\"fw-token-c\">Feminine Path / Reason</span>",
                    "Contraction of 'por + a' (through the / by the / for the).",
                    ["ajuda", "cidade", "janela", "manhã", "vida"],
                    [
                        ex("Obrigado <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>ajuda</span>.", "Thank you for the help.", "Everyday dialogue"),
                        ex("Passeamos <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>cidade antiga</span>.", "We strolled through the old city.", "Conversation"),
                        ex("Olhou <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>janela do quarto</span>.", "Looked through the bedroom window.", "Literature"),
                        ex("Caminha <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>manhã bem cedo</span>.", "Walks in the very early morning.", "Subtitles"),
                        ex("Lutou <span class='fw-token-connector'>pela</span> <span class='fw-token-c'>justiça com determinação</span>.", "Fought for justice with determination.", "Dialogue")
                    ]
                )
            ]
        },
        "num": {
            "word": "num", "role": "Contraction", "rank": 40, "frequency": 1940,
            "parts": ["em", "um"],
            "relations": [
                rel(
                    "Location / State",
                    "<span class=\"fw-token-connector\">em + um</span> + <span class=\"fw-token-c\">Masculine Noun</span>",
                    "Contraction of 'em + um' (in a / on a).",
                    ["apartamento", "dia", "segundo", "lugar", "momento"],
                    [
                        ex("Moro <span class='fw-token-connector'>num</span> <span class='fw-token-c'>apartamento</span>.", "I live in an apartment.", "Everyday dialogue"),
                        ex("Tudo aconteceu <span class='fw-token-connector'>num</span> <span class='fw-token-c'>segundo</span>.", "Everything happened in a second.", "Conversation"),
                        ex("<span class='fw-token-connector'>Num</span> <span class='fw-token-c'>dia chuvoso</span>, ficamos lendo.", "On a rainy day, we stayed reading.", "Literature"),
                        ex("Eles vivem <span class='fw-token-connector'>num</span> <span class='fw-token-c'>lugar tranquilo</span>.", "They live in a quiet place.", "Subtitles"),
                        ex("Conhecemo-nos <span class='fw-token-connector'>num</span> <span class='fw-token-c'>evento cultural</span>.", "We met at a cultural event.", "Dialogue")
                    ]
                )
            ]
        },
        "numa": {
            "word": "numa", "role": "Contraction", "rank": 41, "frequency": 1820,
            "parts": ["em", "uma"],
            "relations": [
                rel(
                    "Location / State",
                    "<span class=\"fw-token-connector\">em + uma</span> + <span class=\"fw-token-c\">Feminine Noun</span>",
                    "Contraction of 'em + uma' (in a / on a).",
                    ["loja", "casa", "noite", "viagem", "mesa"],
                    [
                        ex("Entrei <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>loja</span>.", "I entered a shop.", "Conversation"),
                        ex("Ficamos hospedados <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>pousada</span>.", "We stayed hosted at an inn.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Numa</span> <span class='fw-token-c'>noite fria</span>, acendemos a lareira.", "On a cold night, we lit the fireplace.", "Literature"),
                        ex("Ela trabalha <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>empresa de tecnologia</span>.", "She works at a technology company.", "Subtitles"),
                        ex("Sentamo-nos <span class='fw-token-connector'>numa</span> <span class='fw-token-c'>mesa perto da janela</span>.", "We sat at a table near the window.", "Everyday speech")
                    ]
                )
            ]
        },
        "dele": {
            "word": "dele", "role": "Contraction", "rank": 42, "frequency": 1780,
            "parts": ["de", "ele"],
            "relations": [
                rel(
                    "Possession",
                    "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dele</span>",
                    "Possessive contraction of 'de + ele' (his / of him).",
                    ["amigo", "casa", "carro", "trabalho", "irmão"],
                    [
                        ex("Conheço o amigo <span class='fw-token-connector'>dele</span>.", "I know his friend.", "Everyday dialogue"),
                        ex("A casa <span class='fw-token-connector'>dele</span> é muito acolhedora.", "His house is very cozy.", "Conversation"),
                        ex("Gostei muito da ideia <span class='fw-token-connector'>dele</span>.", "I really liked his idea.", "Dialogue"),
                        ex("O carro <span class='fw-token-connector'>dele</span> está parado ali.", "His car is parked there.", "Subtitles"),
                        ex("O trabalho <span class='fw-token-connector'>dele</span> foi elogiado por todos.", "His work was praised by all.", "Literature")
                    ]
                )
            ]
        },
        "dela": {
            "word": "dela", "role": "Contraction", "rank": 43, "frequency": 1690,
            "parts": ["de", "ela"],
            "relations": [
                rel(
                    "Possession",
                    "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">dela</span>",
                    "Possessive contraction of 'de + ela' (her / of her).",
                    ["casa", "voz", "sorriso", "irmã", "opinião"],
                    [
                        ex("A casa <span class='fw-token-connector'>dela</span> é grande.", "Her house is big.", "Everyday speech"),
                        ex("A voz <span class='fw-token-connector'>dela</span> é calma e bonita.", "Her voice is calm and beautiful.", "Literature"),
                        ex("Respeito muito a opinião <span class='fw-token-connector'>dela</span>.", "I respect her opinion a lot.", "Conversation"),
                        ex("A irmã <span class='fw-token-connector'>dela</span> chega amanhã.", "Her sister arrives tomorrow.", "Dialogue"),
                        ex("O sorriso <span class='fw-token-connector'>dela</span> iluminou o ambiente.", "Her smile lit up the room.", "Subtitles")
                    ]
                )
            ]
        },
        "sem": {
            "word": "sem", "role": "Preposition", "rank": 45, "frequency": 1550,
            "relations": [
                rel(
                    "Privation / Absence",
                    "<span class=\"fw-token-v\">Verb / Noun</span> + <span class=\"fw-token-connector\">sem</span> + <span class=\"fw-token-c\">Missing Element</span>",
                    "Privative preposition: marks absence, exclusion, or lack.",
                    ["açúcar", "medo", "pressa", "dúvida", "problema"],
                    [
                        ex("Café <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>açúcar</span>, por favor.", "Coffee without sugar, please.", "Everyday dialogue"),
                        ex("Ele falou <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>qualquer hesitação</span>.", "He spoke without any hesitation.", "Dialogue"),
                        ex("Saímos <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>pressa nenhuma</span>.", "We left without any rush.", "Conversation"),
                        ex("Isso é, <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>dúvida</span>, a melhor opção.", "That is, without doubt, the best option.", "Subtitles"),
                        ex("Resolvemos a questão <span class='fw-token-connector'>sem</span> <span class='fw-token-c'>problemas</span>.", "We solved the issue without problems.", "Literature")
                    ]
                )
            ]
        },
        "sobre": {
            "word": "sobre", "role": "Preposition", "rank": 46, "frequency": 1520,
            "relations": [
                rel(
                    "Thematic Topic",
                    "<span class=\"fw-token-v\">Discussion / Thought</span> + <span class=\"fw-token-connector\">sobre</span> + <span class=\"fw-token-c\">Topic</span>",
                    "Thematic marker: introduces the subject matter or topic.",
                    ["falar", "conversar", "escrever", "discutir", "pensar"],
                    [
                        ex("Falamos <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o projeto</span>.", "We talked about the project.", "Dialogue"),
                        ex("Li um livro <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>história europeia</span>.", "I read a book about European history.", "Conversation"),
                        ex("Eles discutiram <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o futuro do trabalho</span>.", "They discussed about the future of work.", "Subtitles"),
                        ex("Gostaria de saber mais <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>isso</span>.", "I would like to know more about that.", "Everyday speech"),
                        ex("Escreveu um ensaio <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a arte moderna</span>.", "Wrote an essay about modern art.", "Literature")
                    ]
                ),
                rel(
                    "Spatial Surface",
                    "<span class=\"fw-token-v\">Position</span> + <span class=\"fw-token-connector\">sobre</span> + <span class=\"fw-token-c\">Surface</span>",
                    "Spatial relation: located on top of a surface ('upon / above').",
                    ["mesa", "cama", "cidade", "rio", "bancada"],
                    [
                        ex("O papel está <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a mesa</span>.", "The paper is on the table.", "Dialogue"),
                        ex("A ponte ergue-se <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o grande rio</span>.", "The bridge rises over the great river.", "Literature"),
                        ex("Deixou o casaco <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a cama</span>.", "Left the coat upon the bed.", "Conversation"),
                        ex("As chaves ficaram <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>o balcão</span>.", "The keys were left on the counter.", "Subtitles"),
                        ex("O sol poente brilhava <span class='fw-token-connector'>sobre</span> <span class='fw-token-c'>a cidade</span>.", "The setting sun shone over the city.", "Everyday speech")
                    ]
                )
            ]
        },
        "até": {
            "word": "até", "role": "Preposition & Focus Particle", "rank": 47, "frequency": 1510,
            "relations": [
                rel(
                    "Terminal Boundary",
                    "<span class=\"fw-token-v\">Movement / Time</span> + <span class=\"fw-token-connector\">até</span> + <span class=\"fw-token-c\">Limit / Endpoint</span>",
                    "Terminal boundary: points to the spatial or temporal stopping point.",
                    ["caminhar", "ficar", "esperar", "trabalhar", "ir"],
                    [
                        ex("Vou caminhar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a esquina</span>.", "I will walk as far as the corner.", "Dialogue"),
                        ex("Ficamos no evento <span class='fw-token-connector'>até</span> <span class='fw-token-c'>às dez</span>.", "We stayed at the event until ten.", "Conversation"),
                        ex("Espere aqui <span class='fw-token-connector'>até</span> <span class='fw-token-c'>eu voltar</span>.", "Wait here until I return.", "Subtitles"),
                        ex("Trabalhou sem parar <span class='fw-token-connector'>até</span> <span class='fw-token-c'>ao anoitecer</span>.", "Worked non-stop until nightfall.", "Literature"),
                        ex("Dirigiram <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a fronteira</span>.", "They drove as far as the border.", "Everyday speech")
                    ]
                ),
                rel(
                    "Scalar Focus",
                    "<span class=\"fw-token-connector\">Até</span> + <span class=\"fw-token-c\">Surprising Subject</span>",
                    "Scalar focus particle: emphasizes an extreme case ('even').",
                    ["criança", "ele", "amigo", "inimigo", "estranho"],
                    [
                        ex("<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>as crianças</span> entenderam.", "Even the children understood.", "Conversation"),
                        ex("<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>ele</span> ficou surpreso com o resultado.", "Even he was surprised with the result.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>os especialistas</span> erraram a previsão.", "Even the experts missed the prediction.", "Subtitles"),
                        ex("Estava tão frio que <span class='fw-token-connector'>até</span> <span class='fw-token-c'>a água congelou</span>.", "It was so cold that even the water froze.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Até</span> <span class='fw-token-c'>o vento</span> parecia sussurrar segredos.", "Even the wind seemed to whisper secrets.", "Literature")
                    ]
                )
            ]
        },
        "porque": {
            "word": "porque", "role": "Connector", "rank": 34, "frequency": 2642,
            "relations": [
                rel(
                    "Causal Reason",
                    "<span class=\"fw-token-v\">Result</span> + <span class=\"fw-token-connector\">porque</span> + <span class=\"fw-token-c\">Cause</span>",
                    "Causal conjunction: explains the reason or motive behind an action.",
                    ["chover", "cansar", "gostar", "querer", "precisar"],
                    [
                        ex("Fiquei em casa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>choveu</span>.", "I stayed home because it rained.", "Everyday dialogue"),
                        ex("Não fui à festa <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estava muito cansado</span>.", "I didn't go to the party because I was very tired.", "Conversation"),
                        ex("Estudo português <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>amo a cultura</span>.", "I study Portuguese because I love the culture.", "Subtitles"),
                        ex("Ele sorriu <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>ouviu uma boa notícia</span>.", "He smiled because he heard good news.", "Literature"),
                        ex("Perguntei <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>queria ter a certeza</span>.", "I asked because I wanted to be sure.", "Dialogue")
                    ]
                )
            ]
        },
        "quando": {
            "word": "quando", "role": "Connector", "rank": 35, "frequency": 2510,
            "relations": [
                rel(
                    "Temporal Subordination",
                    "<span class=\"fw-token-connector\">Quando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Clause</span>",
                    "Temporal subordinator: anchors the action to a specific time or event.",
                    ["chegar", "abrir", "ouvir", "sair", "voltar"],
                    [
                        ex("<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>cheguei</span>, <span class='fw-token-c'>todos aplaudiram</span>.", "When I arrived, everyone applauded.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Quando</span> você <span class='fw-token-v'>puder</span>, ligue-me por favor.", "When you can, please call me.", "Conversation"),
                        ex("<span class='fw-token-connector'>Quando</span> o sol <span class='fw-token-v'>nasce</span>, a cidade ganha vida.", "When the sun rises, the city comes alive.", "Literature"),
                        ex("<span class='fw-token-connector'>Quando</span> <span class='fw-token-v'>terminares</span> o trabalho, avisa.", "When you finish the work, let me know.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Quando</span> era jovem, viajava muito.", "When I was young, I used to travel a lot.", "Subtitles")
                    ]
                )
            ]
        },
        "isso": {
            "word": "isso", "role": "Demonstrative Pronoun", "rank": 18, "frequency": 5751,
            "relations": [
                rel(
                    "Neutral Demonstrative",
                    "<span class=\"fw-token-connector\">isso</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Neutral demonstrative: refers to a stated fact, concept, or object near the listener.",
                    ["ser", "significar", "acontecer", "ajudar", "mudar"],
                    [
                        ex("<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>é</span> verdade.", "That is true.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>acontece</span> com frequência.", "That happens frequently.", "Conversation"),
                        ex("<span class='fw-token-connector'>Isso</span> não <span class='fw-token-v'>faz</span> sentido nenhum.", "That makes no sense at all.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Isso</span> <span class='fw-token-v'>mudou</span> toda a situação.", "That changed the whole situation.", "Subtitles"),
                        ex("Já sabia <span class='fw-token-connector'>disso</span> antes de falarem.", "I already knew about that before they spoke.", "Literature")
                    ]
                )
            ]
        },
        "isto": {
            "word": "isto", "role": "Demonstrative Pronoun", "rank": 28, "frequency": 3266,
            "relations": [
                rel(
                    "Immediate Demonstrative",
                    "<span class=\"fw-token-connector\">isto</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Neutral demonstrative: refers to an immediate object or idea near the speaker.",
                    ["ser", "pertencer", "parecer", "bastar", "custar"],
                    [
                        ex("<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>é</span> para você.", "This is for you.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>parece</span> delicioso.", "This looks delicious.", "Conversation"),
                        ex("<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>pertence</span> ao meu colega.", "This belongs to my colleague.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>basta</span> por hoje.", "This is enough for today.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Isto</span> <span class='fw-token-v'>custou</span> muito menos do que imaginei.", "This cost much less than I imagined.", "Literature")
                    ]
                )
            ]
        },
        "tudo": {
            "word": "tudo", "role": "Indefinite Pronoun", "rank": 32, "frequency": 2687,
            "relations": [
                rel(
                    "Universal Totality",
                    "<span class=\"fw-token-connector\">tudo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                    "Universal pronoun: represents the totality of things ('everything / all').",
                    ["estar", "correr", "mudar", "terminar", "ficar"],
                    [
                        ex("<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>está</span> bem.", "Everything is fine.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>correu</span> perfeitamente no evento.", "Everything went perfectly at the event.", "Conversation"),
                        ex("<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>mudou</span> depois daquele dia.", "Everything changed after that day.", "Literature"),
                        ex("Entendi <span class='fw-token-connector'>tudo</span> o que explicaste.", "I understood everything that you explained.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Tudo</span> <span class='fw-token-v'>ficou</span> calmo após a tempestade.", "Everything became quiet after the storm.", "Subtitles")
                    ]
                )
            ]
        }
    }


def build_spanish():
    return {
        "de": {
            "word": "de", "role": "Preposition", "rank": 2, "frequency": 32926,
            "relations": [
                rel(
                    "Verbal Valency",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Complement</span>",
                    "Required link: preceding verb governs 'de' before its object or action.",
                    ["acordar", "hablar", "tratar", "depender", "olvidar", "darse_cuenta"],
                    [
                        ex("<span class='fw-token-v'>Me acuerdo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ti</span>.", "I remember you.", "Dialogue"),
                        ex("Antonio dice que no <span class='fw-token-v'>se acuerda</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>ella</span>.", "Antonio says he doesn't remember her.", "Dictionary speech"),
                        ex("Se <span class='fw-token-v'>trata</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>un asunto importante</span>.", "It's about an important matter.", "Conversation"),
                        ex("Eso <span class='fw-token-v'>depende</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>muchos factores</span>.", "That depends on many factors.", "Subtitles"),
                        ex("No te <span class='fw-token-v'>olvides</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>cerrar la puerta</span>.", "Don't forget to close the door.", "Everyday dialogue")
                    ]
                ),
                rel(
                    "Nominal Binding",
                    "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">de</span> + <span class=\"fw-token-c\">Noun / Origin</span>",
                    "Nominal binding: marks possession, origin, content, or material.",
                    ["vaso", "casa", "hora", "madera", "amigo", "días"],
                    [
                        ex("Quiero un <span class='fw-token-v'>vaso</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>agua</span>.", "I want a glass of water.", "Everyday dialogue"),
                        ex("Una hermosa <span class='fw-token-v'>mesa</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>madera</span>.", "A beautiful wooden table.", "Conversation"),
                        ex("Es <span class='fw-token-v'>hora</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>comer</span>.", "It is time to eat.", "Dialogue"),
                        ex("Un <span class='fw-token-v'>amigo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>mi hermano nos visitó</span>.", "A friend of my brother visited us.", "Subtitles"),
                        ex("Un <span class='fw-token-v'>día</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>descanso muy merecido</span>.", "A well-deserved day of rest.", "Literature")
                    ]
                )
            ]
        },
        "que": {
            "word": "que", "role": "Connector", "rank": 1, "frequency": 33170,
            "relations": [
                rel(
                    "Clausal Link",
                    "<span class=\"fw-token-v\">Thought / Speech</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Clause</span>",
                    "Subordination: bridges what someone thinks, says, or knows to the statement.",
                    ["creer", "pensar", "decir", "saber", "esperar"],
                    [
                        ex("<span class='fw-token-v'>Creo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>va a llover</span>.", "I think it’s going to rain.", "Dialogue"),
                        ex("Ella <span class='fw-token-v'>dijo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vendría temprano</span>.", "She said she would come early.", "Conversation"),
                        ex("<span class='fw-token-v'>Sé</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>tienes toda la razón</span>.", "I know you are completely right.", "Everyday speech"),
                        ex("<span class='fw-token-v'>Espero</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>todo salga bien</span>.", "I hope everything turns out well.", "Subtitles"),
                        ex("Él <span class='fw-token-v'>pensaba</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>era el momento oportuno</span>.", "He thought it was the right moment.", "Literature")
                    ]
                ),
                rel(
                    "Relative Pronoun",
                    "<span class=\"fw-token-v\">Noun</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Description</span>",
                    "Relativization: refers back to a noun while introducing descriptive detail.",
                    ["libro", "persona", "película", "lugar", "cosa"],
                    [
                        ex("Es el <span class='fw-token-v'>libro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estoy leyendo</span>.", "It is the book that I am reading.", "Everyday dialogue"),
                        ex("La <span class='fw-token-v'>persona</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>llamó no dejó mensaje</span>.", "The person who called left no message.", "Conversation"),
                        ex("La <span class='fw-token-v'>película</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vimos fue excelente</span>.", "The movie we saw was excellent.", "Subtitles"),
                        ex("El <span class='fw-token-v'>lugar</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>conocimos era precioso</span>.", "The place we visited was lovely.", "Dialogue"),
                        ex("Son <span class='fw-token-v'>cosas</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>pasan todos los días</span>.", "These are things that happen every day.", "Literature")
                    ]
                ),
                rel(
                    "Comparison",
                    "<span class=\"fw-token-v\">Degree</span> + <span class=\"fw-token-connector\">que</span> + <span class=\"fw-token-c\">Standard</span>",
                    "Comparison: connects the two sides of a degree or quality contrast.",
                    ["más", "menos", "mejor", "peor", "mayor"],
                    [
                        ex("Ella es <span class='fw-token-v'>más alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>yo</span>.", "She is taller than me.", "Everyday dialogue"),
                        ex("Esto es <span class='fw-token-v'>mejor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>lo que teníamos</span>.", "This is better than what we had.", "Conversation"),
                        ex("Tardamos <span class='fw-token-v'>menos tiempo</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>ayer</span>.", "We took less time than yesterday.", "Subtitles"),
                        ex("La casa es <span class='fw-token-v'>mayor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>el piso anterior</span>.", "The house is larger than the previous flat.", "Dialogue"),
                        ex("Hoy hace <span class='fw-token-v'>más calor</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>la semana pasada</span>.", "Today is hotter than last week.", "Literature")
                    ]
                )
            ]
        },
        "a": {
            "word": "a", "role": "Preposition", "rank": 3, "frequency": 22580,
            "relations": [
                rel(
                    "Directional Goal",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Destination</span>",
                    "Directional goal: indicates movement toward a place or terminus.",
                    ["ir", "viajar", "llegar", "volver", "entrar"],
                    [
                        ex("Voy <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Madrid</span>.", "I am going to Madrid.", "Everyday dialogue"),
                        ex("Llegamos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>casa sanos y salvos</span>.", "We arrived home safe and sound.", "Conversation"),
                        ex("Regresaron <span class='fw-token-connector'>a</span> <span class='fw-token-c'>España el mes pasado</span>.", "They returned to Spain last month.", "Subtitles"),
                        ex("Fuimos <span class='fw-token-connector'>a</span> <span class='fw-token-c'>la plaza mayor</span>.", "We went to the main square.", "Dialogue"),
                        ex("El tren viaja <span class='fw-token-connector'>a</span> <span class='fw-token-c'>Valencia</span>.", "The train travels to Valencia.", "Literature")
                    ]
                ),
                rel(
                    "Personal 'a'",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">a</span> + <span class=\"fw-token-c\">Person</span>",
                    "Personal 'a': marks a specific human or personalized direct object.",
                    ["ver", "conocer", "llamar", "esperar", "cuidar"],
                    [
                        ex("Veo <span class='fw-token-connector'>a</span> <span class='fw-token-c'>María</span> todos los días.", "I see María every day.", "Conversation"),
                        ex("Conocí <span class='fw-token-connector'>a</span> <span class='fw-token-c'>tu hermano en la fiesta</span>.", "I met your brother at the party.", "Dialogue"),
                        ex("Llamé <span class='fw-token-connector'>a</span> <span class='fw-token-c'>mis padres anoche</span>.", "I called my parents last night.", "Everyday speech"),
                        ex("Estamos esperando <span class='fw-token-connector'>a</span> <span class='fw-token-c'>los demás invitados</span>.", "We are waiting for the rest of the guests.", "Subtitles"),
                        ex("Cuida mucho <span class='fw-token-connector'>a</span> <span class='fw-token-c'>sus abuelos</span>.", "Takes great care of his grandparents.", "Literature")
                    ]
                )
            ]
        },
        "en": {
            "word": "en", "role": "Preposition", "rank": 7, "frequency": 15660,
            "relations": [
                rel(
                    "Spatial Framing",
                    "<span class=\"fw-token-v\">Verb / State</span> + <span class=\"fw-token-connector\">en</span> + <span class=\"fw-token-c\">Location</span>",
                    "Spatial framing: anchors an action or entity within a place or space.",
                    ["vivir", "estar", "trabajar", "quedarse", "entrar"],
                    [
                        ex("Vivo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>Sevilla</span>.", "I live in Seville.", "Everyday dialogue"),
                        ex("Estamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>el centro de la ciudad</span>.", "We are in the city center.", "Conversation"),
                        ex("Trabaja <span class='fw-token-connector'>en</span> <span class='fw-token-c'>un restaurante cerca</span>.", "Works at a restaurant nearby.", "Subtitles"),
                        ex("Nos quedamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>casa descansando</span>.", "We stayed at home resting.", "Dialogue"),
                        ex("El libro está guardado <span class='fw-token-connector'>en</span> <span class='fw-token-c'>la biblioteca</span>.", "The book is kept in the library.", "Literature")
                    ]
                ),
                rel(
                    "Temporal Framing",
                    "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">en</span> + <span class=\"fw-token-c\">Time Period</span>",
                    "Temporal framing: situates an event inside a month, year, or duration.",
                    ["viajar", "llegar", "terminar", "volver", "nacer"],
                    [
                        ex("Viajamos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>julio</span>.", "We travel in July.", "Conversation"),
                        ex("Nació <span class='fw-token-connector'>en</span> <span class='fw-token-c'>1998</span>.", "Was born in 1998.", "Dialogue"),
                        ex("Estará listo <span class='fw-token-connector'>en</span> <span class='fw-token-c'>cinco minutos</span>.", "It will be ready in five minutes.", "Everyday speech"),
                        ex("Las clases comienzan <span class='fw-token-connector'>en</span> <span class='fw-token-c'>septiembre</span>.", "Classes begin in September.", "Subtitles"),
                        ex("Volveremos <span class='fw-token-connector'>en</span> <span class='fw-token-c'>pocas horas</span>.", "We will return in a few hours.", "Literature")
                    ]
                )
            ]
        },
        "por": {
            "word": "por", "role": "Preposition", "rank": 10, "frequency": 10320,
            "relations": [
                rel(
                    "Cause / Motive",
                    "<span class=\"fw-token-v\">State / Gratitude</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Motive / Cause</span>",
                    "Causal ground: links an emotion, gratitude, or outcome back to its reason.",
                    ["gracias", "preocuparse", "luchar", "esperar", "pagar"],
                    [
                        ex("Gracias <span class='fw-token-connector'>por</span> <span class='fw-token-c'>venir</span>.", "Thank you for coming.", "Everyday dialogue"),
                        ex("Te preocupas demasiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>eso</span>.", "You worry too much about that.", "Conversation"),
                        ex("Lucharon <span class='fw-token-connector'>por</span> <span class='fw-token-c'>sus derechos</span>.", "They fought for their rights.", "Literature"),
                        ex("Pagó diez euros <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el billete</span>.", "Paid ten euros for the ticket.", "Dialogue"),
                        ex("Fue premiado <span class='fw-token-connector'>por</span> <span class='fw-token-c'>su gran esfuerzo</span>.", "Was awarded for his great effort.", "Subtitles")
                    ]
                ),
                rel(
                    "Trajectory",
                    "<span class=\"fw-token-v\">Movement</span> + <span class=\"fw-token-connector\">por</span> + <span class=\"fw-token-c\">Transit Space</span>",
                    "Trajectory: marks the route, medium, or space through which motion happens.",
                    ["pasear", "caminar", "andar", "mirar", "viajar"],
                    [
                        ex("Paseo <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el parque</span>.", "I stroll through the park.", "Dialogue"),
                        ex("Caminamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>las calles del centro</span>.", "We walked through downtown streets.", "Conversation"),
                        ex("Miró <span class='fw-token-connector'>por</span> <span class='fw-token-c'>la ventana del tren</span>.", "Looked through the train window.", "Literature"),
                        ex("El gato entró <span class='fw-token-connector'>por</span> <span class='fw-token-c'>el balcón</span>.", "The cat entered through the balcony.", "Subtitles"),
                        ex("Viajamos <span class='fw-token-connector'>por</span> <span class='fw-token-c'>toda Andalucía</span>.", "We traveled throughout Andalusia.", "Everyday speech")
                    ]
                )
            ]
        },
        "para": {
            "word": "para", "role": "Preposition", "rank": 19, "frequency": 6488,
            "relations": [
                rel(
                    "Purpose",
                    "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Infinitive Objective</span>",
                    "Purpose and aim: establishes the intended goal or outcome of an action.",
                    ["estudiar", "trabajar", "ahorrar", "salir", "llamar"],
                    [
                        ex("Estudio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.", "I study in order to learn.", "Conversation"),
                        ex("Ahorro dinero <span class='fw-token-connector'>para</span> <span class='fw-token-c'>viajar en verano</span>.", "I save money in order to travel in summer.", "Everyday dialogue"),
                        ex("Llamé <span class='fw-token-connector'>para</span> <span class='fw-token-c'>confirmar la cita</span>.", "I called to confirm the appointment.", "Dialogue"),
                        ex("Nos detuvimos <span class='fw-token-connector'>para</span> <span class='fw-token-c'>descansar</span>.", "We stopped to rest.", "Subtitles"),
                        ex("Trabajan duro <span class='fw-token-connector'>para</span> <span class='fw-token-c'>construir un buen futuro</span>.", "They work hard to build a good future.", "Literature")
                    ]
                ),
                rel(
                    "Beneficiary / Target",
                    "<span class=\"fw-token-v\">Entity</span> + <span class=\"fw-token-connector\">para</span> + <span class=\"fw-token-c\">Recipient</span>",
                    "Beneficiary / Target: designates the person meant to receive something.",
                    ["regalo", "carta", "comida", "mensaje", "tiempo"],
                    [
                        ex("Esto es <span class='fw-token-connector'>para</span> <span class='fw-token-c'>ti</span>.", "This is for you.", "Everyday dialogue"),
                        ex("Compré un libro <span class='fw-token-connector'>para</span> <span class='fw-token-c'>mi madre</span>.", "I bought a book for my mother.", "Conversation"),
                        ex("Hay espacio <span class='fw-token-connector'>para</span> <span class='fw-token-c'>dos personas más</span>.", "There is room for two more people.", "Subtitles"),
                        ex("Preparé la cena <span class='fw-token-connector'>para</span> <span class='fw-token-c'>la familia</span>.", "I prepared dinner for the family.", "Dialogue"),
                        ex("Un mensaje especial <span class='fw-token-connector'>para</span> <span class='fw-token-c'>los graduados</span>.", "A special message for the graduates.", "Literature")
                    ]
                )
            ]
        },
        "con": {
            "word": "con", "role": "Preposition", "rank": 18, "frequency": 7024,
            "relations": [
                rel(
                    "Accompaniment",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">con</span> + <span class=\"fw-token-c\">Companion</span>",
                    "Accompaniment: joins an action to the companion sharing it.",
                    ["cenar", "hablar", "salir", "vivir", "trabajar"],
                    [
                        ex("Ceno <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mis amigos</span>.", "I have dinner with my friends.", "Everyday speech"),
                        ex("Hablé <span class='fw-token-connector'>con</span> <span class='fw-token-c'>el médico esta mañana</span>.", "I spoke with the doctor this morning.", "Conversation"),
                        ex("Vive <span class='fw-token-connector'>con</span> <span class='fw-token-c'>su familia en Granada</span>.", "Lives with her family in Granada.", "Subtitles"),
                        ex("Salimos <span class='fw-token-connector'>con</span> <span class='fw-token-c'>los compañeros de clase</span>.", "We went out with classmates.", "Dialogue"),
                        ex("Trabajo a diario <span class='fw-token-connector'>con</span> <span class='fw-token-c'>un equipo excelente</span>.", "I work daily with an excellent team.", "Literature")
                    ]
                ),
                rel(
                    "Instrument and Manner",
                    "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">con</span> + <span class=\"fw-token-c\">Tool / Manner</span>",
                    "Instrument and attitude: describes the tool used or care applied.",
                    ["escribir", "abrir", "escuchar", "cortar", "tratar"],
                    [
                        ex("Escribo <span class='fw-token-connector'>con</span> <span class='fw-token-c'>cuidado</span>.", "I write with care.", "Dialogue"),
                        ex("Abrió la caja <span class='fw-token-connector'>con</span> <span class='fw-token-c'>unas tijeras</span>.", "Opened the box with scissors.", "Conversation"),
                        ex("Escuchó la noticia <span class='fw-token-connector'>con</span> <span class='fw-token-c'>mucha sorpresa</span>.", "Listened to the news with great surprise.", "Subtitles"),
                        ex("Cortó el pan <span class='fw-token-connector'>con</span> <span class='fw-token-c'>un cuchillo afilado</span>.", "Cut the bread with a sharp knife.", "Everyday speech"),
                        ex("Trató el tema <span class='fw-token-connector'>con</span> <span class='fw-token-c'>máxima seriedad</span>.", "Treated the subject with utmost seriousness.", "Literature")
                    ]
                )
            ]
        },
        "sin": {
            "word": "sin", "role": "Preposition", "rank": 36, "frequency": 2180,
            "relations": [
                rel(
                    "Absence / Omission",
                    "<span class=\"fw-token-v\">Noun / Action</span> + <span class=\"fw-token-connector\">sin</span> + <span class=\"fw-token-c\">Missing Element</span>",
                    "Privative preposition: marks absence, lack, or omission.",
                    ["azúcar", "duda", "miedo", "prisa", "problema"],
                    [
                        ex("Café <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>azúcar</span>, por favor.", "Coffee without sugar, please.", "Everyday dialogue"),
                        ex("Es, <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>duda</span>, la mejor elección.", "It is, without doubt, the best choice.", "Conversation"),
                        ex("Actuó <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>miedo ante el peligro</span>.", "Acted without fear before danger.", "Literature"),
                        ex("Caminamos <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>prisa por el paseo</span>.", "We walked without rush along the promenade.", "Subtitles"),
                        ex("Resolvieron el conflicto <span class='fw-token-connector'>sin</span> <span class='fw-token-c'>ningún problema</span>.", "They resolved the conflict without any problem.", "Dialogue")
                    ]
                )
            ]
        },
        "se": {
            "word": "se", "role": "Pronoun Clitic", "rank": 17, "frequency": 7410,
            "relations": [
                rel(
                    "Reflexive Clitic",
                    "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb of self-action</span>",
                    "Reflexive clitic: action turns back upon the person doing it.",
                    ["lavar", "mirar", "sentir", "levantar", "vestir"],
                    [
                        ex("Él <span class='fw-token-connector'>se</span> <span class='fw-token-v'>lava</span> la cara.", "He washes his face.", "Everyday dialogue"),
                        ex("Ella <span class='fw-token-connector'>se</span> <span class='fw-token-v'>miró</span> en el espejo.", "She looked at herself in the mirror.", "Conversation"),
                        ex("<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>siente</span> mucho más tranquilo ahora.", "Feels much calmer now.", "Dialogue"),
                        ex("Los niños <span class='fw-token-connector'>se</span> <span class='fw-token-v'>levantaron</span> temprano.", "The children got up early.", "Subtitles"),
                        ex("El actor <span class='fw-token-connector'>se</span> <span class='fw-token-v'>vistió</span> con elegancia.", "The actor dressed with elegance.", "Literature")
                    ]
                ),
                rel(
                    "Impersonal / Passive",
                    "<span class=\"fw-token-connector\">se</span> + <span class=\"fw-token-v\">Verb (Passive/Impersonal)</span>",
                    "Impersonal / Passive marker: signals general or collective truth ('one does').",
                    ["hablar", "vender", "comer", "vivir", "esperar"],
                    [
                        ex("Aquí <span class='fw-token-connector'>se</span> <span class='fw-token-v'>habla</span> español.", "Spanish is spoken here.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>venden</span> libros antiguos.", "Old books are sold here.", "Conversation"),
                        ex("<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>come</span> muy bien en este restaurante.", "One eats very well in this restaurant.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>vive</span> con tranquilidad en este pueblo.", "One lives peacefully in this village.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>espera</span> una gran multitud hoy.", "A large crowd is expected today.", "Literature")
                    ]
                )
            ]
        },
        "me": {
            "word": "me", "role": "Object Pronoun", "rank": 11, "frequency": 9642,
            "relations": [
                rel(
                    "Object Pronoun",
                    "<span class=\"fw-token-connector\">me</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Object pronoun: represents 1st-person 'me / to me' receiving the verb action.",
                    ["llamar", "ayudar", "dar", "decir", "gustar"],
                    [
                        ex("Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>llamó</span> por teléfono.", "She called me on the phone.", "Everyday speech"),
                        ex("¿<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>puedes ayudar</span> un segundo?", "Can you help me for a second?", "Conversation"),
                        ex("Él <span class='fw-token-connector'>me</span> <span class='fw-token-v'>dio</span> una excelente noticia.", "He gave me great news.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Me</span> <span class='fw-token-v'>gusta</span> mucho este lugar.", "I like this place very much.", "Subtitles"),
                        ex("Ella <span class='fw-token-connector'>me</span> <span class='fw-token-v'>dijo</span> la verdad completa.", "She told me the whole truth.", "Literature")
                    ]
                )
            ]
        },
        "te": {
            "word": "te", "role": "Object Pronoun", "rank": 14, "frequency": 7670,
            "relations": [
                rel(
                    "Object Pronoun",
                    "<span class=\"fw-token-connector\">te</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Object pronoun: represents 2nd-person 'you / to you' (informal).",
                    ["querer", "ver", "llamar", "esperar", "decir"],
                    [
                        ex("<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>quiero</span> mucho.", "I love you very much.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>vi</span> ayer en la plaza.", "I saw you yesterday in the square.", "Conversation"),
                        ex("<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>llamo</span> en cuanto llegue a casa.", "I will call you as soon as I arrive home.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>esperamos</span> en la entrada del teatro.", "We wait for you at the theatre entrance.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Te</span> <span class='fw-token-v'>deseo</span> lo mejor en tu examen.", "I wish you the best in your exam.", "Literature")
                    ]
                )
            ]
        },
        "nos": {
            "word": "nos", "role": "Object Pronoun", "rank": 38, "frequency": 2100,
            "relations": [
                rel(
                    "Object Pronoun",
                    "<span class=\"fw-token-connector\">nos</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Object pronoun: represents 1st-person plural 'us / to us'.",
                    ["enseñar", "ver", "invitar", "esperar", "ayudar"],
                    [
                        ex("El profesor <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>enseña</span> bien.", "The teacher teaches us well.", "Everyday speech"),
                        ex("Ellos <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>invitaron</span> a cenar.", "They invited us for dinner.", "Conversation"),
                        ex("El guía <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>mostró</span> la ciudad vieja.", "The guide showed us the old city.", "Subtitles"),
                        ex("Un vecino <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>ayudó</span> con el coche.", "A neighbour helped us with the car.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Nos</span> <span class='fw-token-v'>alegramos</span> mucho de verte.", "We are very glad to see you.", "Literature")
                    ]
                )
            ]
        },
        "le": {
            "word": "le", "role": "Indirect Pronoun", "rank": 30, "frequency": 3589,
            "relations": [
                rel(
                    "Indirect Object",
                    "<span class=\"fw-token-connector\">le</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Indirect object pronoun: represents 3rd-person singular 'to him / to her / to you'.",
                    ["escribir", "dar", "preguntar", "decir", "entregar"],
                    [
                        ex("Yo <span class='fw-token-connector'>le</span> <span class='fw-token-v'>escribí</span> una carta.", "I wrote him a letter.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Le</span> <span class='fw-token-v'>entregué</span> las llaves a la recepcionista.", "I handed the keys to the receptionist.", "Conversation"),
                        ex("El médico <span class='fw-token-connector'>le</span> <span class='fw-token-v'>recetó</span> descanso.", "The doctor prescribed him rest.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Le</span> <span class='fw-token-v'>pregunté</span> la hora amablemente.", "I asked her the time politely.", "Everyday speech"),
                        ex("Nadie <span class='fw-token-connector'>le</span> <span class='fw-token-v'>dijo</span> nada sobre el cambio.", "Nobody told him anything about the change.", "Literature")
                    ]
                )
            ]
        },
        "al": {
            "word": "al", "role": "Contraction", "rank": 13, "frequency": 7673,
            "parts": ["a", "el"],
            "relations": [
                rel(
                    "Direction / Goal",
                    "<span class=\"fw-token-connector\">a + el</span> + <span class=\"fw-token-c\">Masculine Destination</span>",
                    "Mandatory contraction of 'a + el' (to the / at the) before masculine nouns.",
                    ["cine", "parque", "médico", "trabajo", "aeropuerto"],
                    [
                        ex("Vamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>cine</span> esta noche.", "We are going to the cinema tonight.", "Everyday dialogue"),
                        ex("Llegamos <span class='fw-token-connector'>al</span> <span class='fw-token-c'>parque al atardecer</span>.", "We arrived at the park at sunset.", "Conversation"),
                        ex("Tuve que ir <span class='fw-token-connector'>al</span> <span class='fw-token-c'>médico por la mañana</span>.", "I had to go to the doctor in the morning.", "Subtitles"),
                        ex("Acompañó a su abuelo <span class='fw-token-connector'>al</span> <span class='fw-token-c'>aeropuerto</span>.", "Accompanied his grandfather to the airport.", "Dialogue"),
                        ex("Volvieron <span class='fw-token-connector'>al</span> <span class='fw-token-c'>trabajo con energía</span>.", "They returned to work with energy.", "Literature")
                    ]
                ),
                rel(
                    "Temporal Nexus",
                    "<span class=\"fw-token-connector\">al</span> + <span class=\"fw-token-v\">Infinitive</span>",
                    "Temporal nexus: expresses 'upon doing' or 'when doing'.",
                    ["llegar", "salir", "abrir", "oír", "ver"],
                    [
                        ex("<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>llegar</span> a casa, descansé.", "Upon arriving home, I rested.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>oír</span> la campana, salieron todos.", "Upon hearing the bell, everyone left.", "Conversation"),
                        ex("Sonrió <span class='fw-token-connector'>al</span> <span class='fw-token-v'>ver</span> la sorpresa preparada.", "Smiled upon seeing the surprise prepared.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>abrir</span> la ventana entró aire fresco.", "Upon opening the window, fresh air entered.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Al</span> <span class='fw-token-v'>terminar</span> el discurso, todos aplaudieron.", "Upon finishing the speech, everyone applauded.", "Literature")
                    ]
                )
            ]
        },
        "del": {
            "word": "del", "role": "Contraction", "rank": 15, "frequency": 7638,
            "parts": ["de", "el"],
            "relations": [
                rel(
                    "Origin / Attribute",
                    "<span class=\"fw-token-connector\">de + el</span> + <span class=\"fw-token-c\">Masculine Noun / Origin</span>",
                    "Mandatory contraction of 'de + el' (of the / from the).",
                    ["hotel", "libro", "mundo", "edificio", "río"],
                    [
                        ex("La puerta <span class='fw-token-connector'>del</span> <span class='fw-token-c'>hotel</span> está cerrada.", "The door of the hotel is closed.", "Everyday dialogue"),
                        ex("El final <span class='fw-token-connector'>del</span> <span class='fw-token-c'>libro fue emocionante</span>.", "The end of the book was exciting.", "Conversation"),
                        ex("Viene <span class='fw-token-connector'>del</span> <span class='fw-token-c'>centro en bicicleta</span>.", "Comes from downtown by bicycle.", "Subtitles"),
                        ex("Es una de las maravillas <span class='fw-token-connector'>del</span> <span class='fw-token-c'>mundo</span>.", "It is one of the wonders of the world.", "Literature"),
                        ex("La vista <span class='fw-token-connector'>del</span> <span class='fw-token-c'>valle nos impresionó</span>.", "The view of the valley impressed us.", "Dialogue")
                    ]
                )
            ]
        },
        "el": {
            "word": "el", "role": "Definite Article", "rank": 5, "frequency": 18067,
            "relations": [
                rel(
                    "Definite Article",
                    "<span class=\"fw-token-connector\">el</span> + <span class=\"fw-token-c\">Masculine Singular Noun</span>",
                    "Definite article: designates a specific masculine singular referent.",
                    ["sol", "coche", "día", "tren", "tiempo"],
                    [
                        ex("<span class='fw-token-connector'>El</span> <span class='fw-token-c'>sol</span> brilla en el cielo.", "The sun shines in the sky.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>El</span> <span class='fw-token-c'>coche nuevo</span> consume poca gasolina.", "The new car consumes little petrol.", "Conversation"),
                        ex("<span class='fw-token-connector'>El</span> <span class='fw-token-c'>tren de las ocho</span> ya partió.", "The eight o'clock train already left.", "Dialogue"),
                        ex("<span class='fw-token-connector'>El</span> <span class='fw-token-c'>tiempo</span> pasa muy rápido aquí.", "Time passes very quickly here.", "Subtitles"),
                        ex("<span class='fw-token-connector'>El</span> <span class='fw-token-c'>viento</span> soplaba suavemente entre los árboles.", "The wind blew gently among the trees.", "Literature")
                    ]
                )
            ]
        },
        "la": {
            "word": "la", "role": "Article & Pronoun", "rank": 4, "frequency": 21524,
            "relations": [
                rel(
                    "Definite Article",
                    "<span class=\"fw-token-connector\">la</span> + <span class=\"fw-token-c\">Feminine Singular Noun</span>",
                    "Definite article: designates a specific feminine singular referent.",
                    ["puerta", "casa", "ciudad", "noche", "vida"],
                    [
                        ex("<span class='fw-token-connector'>La</span> <span class='fw-token-c'>puerta</span> está abierta.", "The door is open.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>La</span> <span class='fw-token-c'>casa de campo</span> tiene un gran jardín.", "The country house has a large garden.", "Conversation"),
                        ex("<span class='fw-token-connector'>La</span> <span class='fw-token-c'>ciudad</span> duerme bajo las estrellas.", "The city sleeps under the stars.", "Literature"),
                        ex("<span class='fw-token-connector'>La</span> <span class='fw-token-c'>noche</span> era serena y estrellada.", "The night was serene and starry.", "Subtitles"),
                        ex("<span class='fw-token-connector'>La</span> <span class='fw-token-c'>música</span> llenaba todo el salón.", "The music filled the entire hall.", "Dialogue")
                    ]
                ),
                rel(
                    "Direct Object Pronoun",
                    "<span class=\"fw-token-connector\">la</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Direct object pronoun: replaces a 3rd-person feminine singular noun ('her / it').",
                    ["ver", "conocer", "esperar", "llamar", "escuchar"],
                    [
                        ex("Yo <span class='fw-token-connector'>la</span> <span class='fw-token-v'>vi</span> ayer en el mercado.", "I saw her yesterday at the market.", "Conversation"),
                        ex("No <span class='fw-token-connector'>la</span> <span class='fw-token-v'>conozco</span> en persona todavía.", "I don't know her in person yet.", "Dialogue"),
                        ex("<span class='fw-token-connector'>La</span> <span class='fw-token-v'>llamé</span> para avisarle del retraso.", "I called her to notify her of the delay.", "Everyday speech"),
                        ex("Todos <span class='fw-token-connector'>la</span> <span class='fw-token-v'>escucharon</span> con respeto.", "Everyone listened to her with respect.", "Subtitles"),
                        ex("La llave estaba perdida, pero por fin <span class='fw-token-connector'>la</span> <span class='fw-token-v'>encontré</span>.", "The key was lost, but at last I found it.", "Literature")
                    ]
                )
            ]
        },
        "los": {
            "word": "los", "role": "Article & Pronoun", "rank": 16, "frequency": 7540,
            "relations": [
                rel(
                    "Definite Article",
                    "<span class=\"fw-token-connector\">los</span> + <span class=\"fw-token-c\">Masculine Plural Noun</span>",
                    "Definite article: designates specific masculine plural entities.",
                    ["niños", "libros", "días", "amigos", "árboles"],
                    [
                        ex("<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>niños</span> juegan fuera.", "The children play outside.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>libros</span> estaban colocados en orden.", "The books were arranged in order.", "Conversation"),
                        ex("<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>días soleados</span> son mis favoritos.", "Sunny days are my favorites.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>amigos</span> se reunieron para celebrar.", "The friends met to celebrate.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Los</span> <span class='fw-token-c'>pájaros</span> cantaban al amanecer.", "The birds sang at dawn.", "Literature")
                    ]
                ),
                rel(
                    "Direct Object Pronoun",
                    "<span class=\"fw-token-connector\">los</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Direct object pronoun: replaces 3rd-person masculine plural objects ('them').",
                    ["comprar", "ver", "conocer", "recoger", "dejar"],
                    [
                        ex("Yo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>compré</span> ayer en la tienda.", "I bought them yesterday at the shop.", "Conversation"),
                        ex("No <span class='fw-token-connector'>los</span> <span class='fw-token-v'>he visto</span> en toda la semana.", "I haven't seen them all week.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Los</span> <span class='fw-token-v'>recogí</span> de la estación a tiempo.", "I picked them up from the station in time.", "Subtitles"),
                        ex("Si encuentras los papeles, <span class='fw-token-connector'>los</span> <span class='fw-token-v'>dejas</span> aquí.", "If you find the papers, leave them here.", "Everyday speech"),
                        ex("El abuelo <span class='fw-token-connector'>los</span> <span class='fw-token-v'>abrazó</span> con emoción.", "The grandfather hugged them with emotion.", "Literature")
                    ]
                )
            ]
        },
        "las": {
            "word": "las", "role": "Article & Pronoun", "rank": 24, "frequency": 4810,
            "relations": [
                rel(
                    "Definite Article",
                    "<span class=\"fw-token-connector\">las</span> + <span class=\"fw-token-c\">Feminine Plural Noun</span>",
                    "Definite article: designates specific feminine plural entities.",
                    ["llaves", "flores", "cosas", "personas", "calles"],
                    [
                        ex("<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>llaves</span> están en la mesa.", "The keys are on the table.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>flores del patio</span> huelen de maravilla.", "The courtyard flowers smell wonderful.", "Conversation"),
                        ex("<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>calles</span> estaban llenas de luces navideñas.", "The streets were full of Christmas lights.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Las</span> <span class='fw-token-c'>personas</span> escuchaban con atención.", "The people listened with attention.", "Dialogue"),
                        ex("Hay que poner <span class='fw-token-connector'>las</span> <span class='fw-token-c'>cosas</span> en su sitio.", "One must put things in their place.", "Literature")
                    ]
                )
            ]
        },
        "lo": {
            "word": "lo", "role": "Article & Pronoun", "rank": 8, "frequency": 14130,
            "relations": [
                rel(
                    "Neuter Article",
                    "<span class=\"fw-token-connector\">lo</span> + <span class=\"fw-token-c\">Adjective / Abstract</span>",
                    "Neuter article: nominalizes an adjective into an abstract quality ('the ... thing').",
                    ["importante", "bueno", "malo", "mejor", "difícil"],
                    [
                        ex("<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>importante</span> es participar.", "The important thing is to participate.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>bueno</span> es que tenemos tiempo de sobra.", "The good thing is that we have plenty of time.", "Conversation"),
                        ex("<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>difícil</span> ya ha pasado.", "The difficult part has already passed.", "Dialogue"),
                        ex("Hizo <span class='fw-token-connector'>lo</span> <span class='fw-token-c'>mejor</span> que pudo dadas las circunstancias.", "Did the best that he could given the circumstances.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Lo</span> <span class='fw-token-c'>curioso</span> es que nadie notó la diferencia.", "The curious thing is that nobody noticed the difference.", "Literature")
                    ]
                ),
                rel(
                    "Direct Object Pronoun",
                    "<span class=\"fw-token-connector\">lo</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Direct object pronoun: replaces a masculine singular item or concept ('it / him').",
                    ["saber", "ver", "hacer", "tener", "entender"],
                    [
                        ex("Ya <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>sé</span>.", "I already know it.", "Everyday dialogue"),
                        ex("No <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>entiendo</span> con claridad.", "I do not understand it clearly.", "Conversation"),
                        ex("¿<span class='fw-token-connector'>Lo</span> <span class='fw-token-v'>has visto</span> por aquí?", "Have you seen him around here?", "Dialogue"),
                        ex("<span class='fw-token-connector'>Lo</span> <span class='fw-token-v'>hice</span> exactamente como me pediste.", "I did it exactly as you asked me.", "Subtitles"),
                        ex("Si tienes el informe, <span class='fw-token-connector'>lo</span> <span class='fw-token-v'>leo</span> esta noche.", "If you have the report, I'll read it tonight.", "Literature")
                    ]
                )
            ]
        },
        "un": {
            "word": "un", "role": "Indefinite Article", "rank": 9, "frequency": 13352,
            "relations": [
                rel(
                    "Indefinite Article",
                    "<span class=\"fw-token-connector\">un</span> + <span class=\"fw-token-c\">Masculine Singular Noun</span>",
                    "Indefinite article: introduces a single unspecific masculine noun.",
                    ["amigo", "día", "libro", "café", "coche"],
                    [
                        ex("Tengo <span class='fw-token-connector'>un</span> <span class='fw-token-c'>amigo</span> en Madrid.", "I have a friend in Madrid.", "Everyday dialogue"),
                        ex("Tomemos <span class='fw-token-connector'>un</span> <span class='fw-token-c'>café caliente juntos</span>.", "Let's have a warm coffee together.", "Conversation"),
                        ex("Compré <span class='fw-token-connector'>un</span> <span class='fw-token-c'>libro muy interesante</span>.", "I bought a very interesting book.", "Dialogue"),
                        ex("Fue <span class='fw-token-connector'>un</span> <span class='fw-token-c'>día inolvidable para todos</span>.", "It was an unforgettable day for everyone.", "Subtitles"),
                        ex("Buscamos <span class='fw-token-connector'>un</span> <span class='fw-token-c'>lugar tranquilo para charlar</span>.", "We are looking for a quiet place to chat.", "Literature")
                    ]
                )
            ]
        },
        "una": {
            "word": "una", "role": "Indefinite Article", "rank": 12, "frequency": 8937,
            "relations": [
                rel(
                    "Indefinite Article",
                    "<span class=\"fw-token-connector\">una</span> + <span class=\"fw-token-c\">Feminine Singular Noun</span>",
                    "Indefinite article: introduces a single unspecific feminine noun.",
                    ["idea", "casa", "pregunta", "semana", "historia"],
                    [
                        ex("Es <span class='fw-token-connector'>una</span> <span class='fw-token-c'>buena idea</span>.", "It is a good idea.", "Everyday speech"),
                        ex("Alquilamos <span class='fw-token-connector'>una</span> <span class='fw-token-c'>casa cerca de la playa</span>.", "We rented a house near the beach.", "Conversation"),
                        ex("Quiero hacer <span class='fw-token-connector'>una</span> <span class='fw-token-c'>pregunta rápida</span>.", "I want to ask a quick question.", "Dialogue"),
                        ex("Contó <span class='fw-token-connector'>una</span> <span class='fw-token-c'>historia emocionante</span>.", "Told an exciting story.", "Subtitles"),
                        ex("Esperamos durante <span class='fw-token-connector'>una</span> <span class='fw-token-c'>semana entera</span>.", "We waited for a whole week.", "Literature")
                    ]
                )
            ]
        },
        "y": {
            "word": "y", "role": "Connector", "rank": 6, "frequency": 16518,
            "relations": [
                rel(
                    "Addition",
                    "<span class=\"fw-token-v\">Element</span> + <span class=\"fw-token-connector\">y</span> + <span class=\"fw-token-c\">Addition</span>",
                    "Copulative conjunction: coordinates items, clauses, or thoughts of equal status.",
                    ["pan", "leche", "entrar", "abrir", "cantar", "bailar"],
                    [
                        ex("Compré pan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>leche</span>.", "I bought bread and milk.", "Everyday speech"),
                        ex("Se levantó temprano <span class='fw-token-connector'>y</span> <span class='fw-token-c'>salió a correr</span>.", "Got up early and went out to run.", "Conversation"),
                        ex("Cantan <span class='fw-token-connector'>y</span> <span class='fw-token-c'>bailan con alegría</span>.", "They sing and dance with joy.", "Subtitles"),
                        ex("El día era fresco <span class='fw-token-connector'>y</span> <span class='fw-token-c'>despejado</span>.", "The day was cool and clear.", "Dialogue"),
                        ex("Escuchó la pregunta <span class='fw-token-connector'>y</span> <span class='fw-token-c'>asintió en silencio</span>.", "Heard the question and nodded in silence.", "Literature")
                    ]
                )
            ]
        },
        "pero": {
            "word": "pero", "role": "Connector", "rank": 22, "frequency": 5378,
            "relations": [
                rel(
                    "Contrast",
                    "<span class=\"fw-token-v\">Statement</span> + <span class=\"fw-token-connector\">pero</span> + <span class=\"fw-token-c\">Contrast</span>",
                    "Adversative bridge: introduces a qualification, limitation, or unexpected contrast.",
                    ["salir", "querer", "intentar", "saber", "buscar"],
                    [
                        ex("Quería salir, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>llovía</span>.", "I wanted to go out, but it was raining.", "Everyday dialogue"),
                        ex("Lo intenté con todas mis fuerzas, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>no pude</span>.", "I tried with all my might, but couldn't.", "Conversation"),
                        ex("Sabía la lección, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>se puso nervioso</span>.", "Knew the lesson, but got nervous.", "Subtitles"),
                        ex("Es caro, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>vale la pena</span>.", "It is expensive, but worth it.", "Dialogue"),
                        ex("Buscó por doquier, <span class='fw-token-connector'>pero</span> <span class='fw-token-c'>la carta había desaparecido</span>.", "Searched everywhere, but the letter had vanished.", "Literature")
                    ]
                )
            ]
        },
        "si": {
            "word": "si", "role": "Connector", "rank": 21, "frequency": 5720,
            "relations": [
                rel(
                    "Condition",
                    "<span class=\"fw-token-connector\">Si</span> + <span class=\"fw-token-v\">Condition</span> , <span class=\"fw-token-c\">Result</span>",
                    "Conditional marker: establishes a hypothesis preceding its outcome.",
                    ["tener", "querer", "llover", "poder", "saber"],
                    [
                        ex("<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>tienes tiempo</span>, <span class='fw-token-c'>ven a verme</span>.", "If you have time, come see me.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>llueve mañana</span>, <span class='fw-token-c'>nos quedaremos en casa</span>.", "If it rains tomorrow, we will stay at home.", "Conversation"),
                        ex("<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>quieres</span>, <span class='fw-token-c'>podemos almorzar juntos</span>.", "If you want, we can have lunch together.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>puedes ayudarme</span>, <span class='fw-token-c'>te lo agradezco</span>.", "If you can help me, I appreciate it.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Si</span> <span class='fw-token-v'>sabes algo nuevo</span>, <span class='fw-token-c'>avísame enseguida</span>.", "If you know anything new, let me know right away.", "Literature")
                    ]
                )
            ]
        },
        "como": {
            "word": "como", "role": "Connector", "rank": 29, "frequency": 3832,
            "relations": [
                rel(
                    "Manner / Simile",
                    "<span class=\"fw-token-v\">Action</span> + <span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Standard</span>",
                    "Simile and manner: compares action execution against an exemplar.",
                    ["cantar", "correr", "brillar", "hablar", "actuar"],
                    [
                        ex("Canta <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un pájaro</span>.", "Sings like a bird.", "Everyday speech"),
                        ex("Corre rápido <span class='fw-token-connector'>como</span> <span class='fw-token-c'>el viento</span>.", "Runs fast like the wind.", "Conversation"),
                        ex("Brilla <span class='fw-token-connector'>como</span> <span class='fw-token-c'>el oro puro bajo el sol</span>.", "Shines like pure gold under the sun.", "Literature"),
                        ex("Actuó <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un verdadero profesional</span>.", "Acted like a true professional.", "Dialogue"),
                        ex("Habla español tan claro <span class='fw-token-connector'>como</span> <span class='fw-token-c'>un nativo</span>.", "Speaks Spanish as clearly as a native.", "Subtitles")
                    ]
                ),
                rel(
                    "Capacity / Role",
                    "<span class=\"fw-token-connector\">como</span> + <span class=\"fw-token-c\">Capacity / Profession</span>",
                    "Capacity and role: designates the status or function held.",
                    ["médico", "profesor", "voluntario", "guía", "testigo"],
                    [
                        ex("Trabaja <span class='fw-token-connector'>como</span> <span class='fw-token-c'>médico en el hospital central</span>.", "Works as a doctor in the central hospital.", "Conversation"),
                        ex("Actuó <span class='fw-token-connector'>como</span> <span class='fw-token-c'>representante oficial</span>.", "Acted as official representative.", "Dialogue"),
                        ex("Participa <span class='fw-token-connector'>como</span> <span class='fw-token-c'>voluntaria en la biblioteca</span>.", "Participates as a volunteer in the library.", "Subtitles"),
                        ex("Te hablo <span class='fw-token-connector'>como</span> <span class='fw-token-c'>amigo sincero</span>.", "I speak to you as a sincere friend.", "Everyday speech"),
                        ex("Declaró <span class='fw-token-connector'>como</span> <span class='fw-token-c'>testigo del suceso</span>.", "Testified as a witness of the event.", "Literature")
                    ]
                )
            ]
        },
        "mi": {
            "word": "mi", "role": "Possessive Determiner", "rank": 20, "frequency": 6120,
            "relations": [
                rel(
                    "Possession",
                    "<span class=\"fw-token-connector\">mi</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                    "1st-person singular possessive: introduces something belonging to the speaker.",
                    ["casa", "vida", "amigo", "hermano", "coche"],
                    [
                        ex("Esta es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>casa</span>.", "This is my house.", "Everyday dialogue"),
                        ex("Es <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>mejor amigo desde la infancia</span>.", "He is my best friend since childhood.", "Conversation"),
                        ex("<span class='fw-token-connector'>Mi</span> <span class='fw-token-c'>hermano mayor</span> vive en Barcelona.", "My older brother lives in Barcelona.", "Dialogue"),
                        ex("He dedicado toda <span class='fw-token-connector'>mi</span> <span class='fw-token-c'>vida</span> a este trabajo.", "I have dedicated my whole life to this work.", "Literature"),
                        ex("<span class='fw-token-connector'>Mi</span> <span class='fw-token-c'>coche</span> está aparcado enfrente.", "My car is parked in front.", "Subtitles")
                    ]
                )
            ]
        },
        "su": {
            "word": "su", "role": "Possessive Determiner", "rank": 10, "frequency": 11240,
            "relations": [
                rel(
                    "Possession",
                    "<span class=\"fw-token-connector\">su</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                    "3rd-person possessive: denotes something belonging to him, her, them, or formal 'you'.",
                    ["nombre", "casa", "familia", "trabajo", "opinión"],
                    [
                        ex("¿Cuál es <span class='fw-token-connector'>su</span> <span class='fw-token-c'>nombre</span>?", "What is your (formal) / his / her name?", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Su</span> <span class='fw-token-c'>familia</span> es muy amable y acogedora.", "His family is very kind and welcoming.", "Conversation"),
                        ex("Admiro mucho <span class='fw-token-connector'>su</span> <span class='fw-token-c'>trabajo profesional</span>.", "I admire his professional work very much.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Su</span> <span class='fw-token-c'>opinión</span> es fundamental para nosotros.", "Your (formal) opinion is essential for us.", "Dialogue"),
                        ex("Visité <span class='fw-token-connector'>su</span> <span class='fw-token-c'>casa de campo el fin de semana</span>.", "I visited his country house on the weekend.", "Literature")
                    ]
                )
            ]
        },
        "tu": {
            "word": "tu", "role": "Possessive Determiner", "rank": 23, "frequency": 5100,
            "relations": [
                rel(
                    "Possession",
                    "<span class=\"fw-token-connector\">tu</span> + <span class=\"fw-token-c\">Singular Noun</span>",
                    "2nd-person informal possessive: introduces something belonging to the listener.",
                    ["casa", "amigo", "trabajo", "idea", "familia"],
                    [
                        ex("<span class='fw-token-connector'>Tu</span> <span class='fw-token-c'>casa</span> es preciosa.", "Your house is lovely.", "Everyday dialogue"),
                        ex("Me gusta mucho <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>idea para el proyecto</span>.", "I like your idea for the project a lot.", "Conversation"),
                        ex("¿Cómo está <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>familia</span>?", "How is your family?", "Dialogue"),
                        ex("Ayer conocí a <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>amigo Carlos</span>.", "Yesterday I met your friend Carlos.", "Subtitles"),
                        ex("Felicidades por <span class='fw-token-connector'>tu</span> <span class='fw-token-c'>nuevo trabajo</span>.", "Congratulations on your new job.", "Literature")
                    ]
                )
            ]
        },
        "yo": {
            "word": "yo", "role": "Subject Pronoun", "rank": 25, "frequency": 4200,
            "relations": [
                rel(
                    "Subject Pronoun",
                    "<span class=\"fw-token-connector\">Yo</span> + <span class=\"fw-token-v\">Verb (1st Sing)</span>",
                    "Subject pronoun: explicitly emphasizes or contrasts the 1st-person actor.",
                    ["saber", "pensar", "creer", "querer", "estar"],
                    [
                        ex("<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>sé</span> la verdad.", "I know the truth.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>pienso</span> que deberíamos intentarlo.", "I think that we should try it.", "Conversation"),
                        ex("<span class='fw-token-connector'>Yo</span> no <span class='fw-token-v'>tengo</span> ninguna duda al respecto.", "I have no doubt about it.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>quiero</span> acompañarte al centro.", "I want to accompany you downtown.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Yo</span> <span class='fw-token-v'>estoy</span> listo cuando tú digas.", "I am ready whenever you say.", "Literature")
                    ]
                )
            ]
        },
        "tú": {
            "word": "tú", "role": "Subject Pronoun", "rank": 26, "frequency": 4100,
            "relations": [
                rel(
                    "Subject Pronoun",
                    "<span class=\"fw-token-connector\">Tú</span> + <span class=\"fw-token-v\">Verb (2nd Sing)</span>",
                    "Subject pronoun: explicitly clarifies or contrasts the 2nd-person actor.",
                    ["saber", "tener", "poder", "querer", "entender"],
                    [
                        ex("<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>sabes</span> lo que quiero decir.", "You know what I mean.", "Everyday speech"),
                        ex("<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>tienes</span> toda la razón en esto.", "You are completely right on this.", "Conversation"),
                        ex("Si <span class='fw-token-connector'>tú</span> <span class='fw-token-v'>puedes</span> venir, será genial.", "If you can come, it will be great.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>entiendes</span> mejor que nadie la situación.", "You understand the situation better than anyone.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Tú</span> <span class='fw-token-v'>decides</span> qué camino tomar.", "You decide which path to take.", "Literature")
                    ]
                )
            ]
        },
        "eso": {
            "word": "eso", "role": "Demonstrative Pronoun", "rank": 27, "frequency": 3900,
            "relations": [
                rel(
                    "Neuter Demonstrative",
                    "<span class=\"fw-token-connector\">eso</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Neuter demonstrative: refers to a stated matter, idea, or object near the listener.",
                    ["ser", "parecer", "cambiar", "pasar", "significar"],
                    [
                        ex("<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>es</span> verdad.", "That is true.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>parece</span> una magnífica solución.", "That looks like a magnificent solution.", "Conversation"),
                        ex("<span class='fw-token-connector'>Eso</span> <span class='fw-token-v'>cambia</span> las cosas por completo.", "That changes things completely.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Eso</span> no <span class='fw-token-v'>significa</span> que sea fácil.", "That does not mean that it is easy.", "Subtitles"),
                        ex("Precisamente por <span class='fw-token-connector'>eso</span> vine a hablar contigo.", "Precisely because of that I came to talk to you.", "Literature")
                    ]
                )
            ]
        },
        "esto": {
            "word": "esto", "role": "Demonstrative Pronoun", "rank": 31, "frequency": 2988,
            "relations": [
                rel(
                    "Immediate Demonstrative",
                    "<span class=\"fw-token-connector\">esto</span> + <span class=\"fw-token-v\">Verb</span>",
                    "Neuter demonstrative: refers to an immediate topic or object near the speaker.",
                    ["ser", "parecer", "funcionar", "gustar", "acabar"],
                    [
                        ex("<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>es</span> para ti.", "This is for you.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>funciona</span> a la perfección.", "This works to perfection.", "Conversation"),
                        ex("<span class='fw-token-connector'>Esto</span> <span class='fw-token-v'>parece</span> muy interesante.", "This looks very interesting.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Esto</span> me <span class='fw-token-v'>gusta</span> cada día más.", "I like this more every day.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Esto</span> apenas <span class='fw-token-v'>comienza</span>.", "This is only just beginning.", "Literature")
                    ]
                )
            ]
        },
        "todo": {
            "word": "todo", "role": "Indefinite Pronoun", "rank": 32, "frequency": 2979,
            "relations": [
                rel(
                    "Universal Totality",
                    "<span class=\"fw-token-connector\">todo</span> + <span class=\"fw-token-v\">State / Verb</span>",
                    "Universal pronoun: signifies the totality of matters ('everything / all').",
                    ["estar", "salir", "cambiar", "pasar", "terminar"],
                    [
                        ex("<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>está</span> bien.", "Everything is fine.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>salió</span> según lo planeado.", "Everything turned out as planned.", "Conversation"),
                        ex("<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>cambió</span> de un momento a otro.", "Everything changed from one moment to the next.", "Dialogue"),
                        ex("Entendí <span class='fw-token-connector'>todo</span> sin ninguna dificultad.", "I understood everything without any difficulty.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Todo</span> <span class='fw-token-v'>quedó</span> en calma tras la lluvia.", "Everything remained calm after the rain.", "Literature")
                    ]
                )
            ]
        },
        "algo": {
            "word": "algo", "role": "Indefinite Pronoun", "rank": 34, "frequency": 2452,
            "relations": [
                rel(
                    "Indefinite Entity",
                    "<span class=\"fw-token-v\">Verb</span> + <span class=\"fw-token-connector\">algo</span>",
                    "Indefinite entity: marks an unspecified thing or amount ('something').",
                    ["comer", "decir", "pasar", "saber", "traer"],
                    [
                        ex("Quiero comer <span class='fw-token-connector'>algo</span>.", "I want to eat something.", "Everyday dialogue"),
                        ex("Tiene <span class='fw-token-connector'>algo</span> importante que contarnos.", "Has something important to tell us.", "Conversation"),
                        ex("¿Ha pasado <span class='fw-token-connector'>algo</span> mientras estaba fuera?", "Did something happen while I was away?", "Dialogue"),
                        ex("Sé <span class='fw-token-connector'>algo</span> sobre este tema histórico.", "I know something about this historical topic.", "Subtitles"),
                        ex("Te traje <span class='fw-token-connector'>algo</span> del viaje que te gustará.", "I brought you something from the trip you will like.", "Literature")
                    ]
                )
            ]
        },
        "porque": {
            "word": "porque", "role": "Connector", "rank": 40, "frequency": 2080,
            "relations": [
                rel(
                    "Causal Reason",
                    "<span class=\"fw-token-v\">Result</span> + <span class=\"fw-token-connector\">porque</span> + <span class=\"fw-token-c\">Cause</span>",
                    "Causal conjunction: explains the underlying reason or motive.",
                    ["cansar", "llover", "gustar", "querer", "importar"],
                    [
                        ex("No fui <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>estaba cansado</span>.", "I did not go because I was tired.", "Everyday dialogue"),
                        ex("Nos quedamos <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>empezó a llover</span>.", "We stayed because it started raining.", "Conversation"),
                        ex("Estudio español <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>me encanta viajar</span>.", "I study Spanish because I love traveling.", "Dialogue"),
                        ex("Sonrió <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>recibió buenas noticias</span>.", "Smiled because he received good news.", "Subtitles"),
                        ex("Te pregunto <span class='fw-token-connector'>porque</span> <span class='fw-token-c'>me importa tu opinión</span>.", "I ask you because your opinion matters to me.", "Literature")
                    ]
                )
            ]
        },
        "cuando": {
            "word": "cuando", "role": "Connector", "rank": 41, "frequency": 2040,
            "relations": [
                rel(
                    "Temporal Nexus",
                    "<span class=\"fw-token-connector\">Cuando</span> + <span class=\"fw-token-v\">Time Condition</span> , <span class=\"fw-token-c\">Main Action</span>",
                    "Temporal connector: situates an event at a point in time.",
                    ["llegar", "salir", "ver", "poder", "despertar"],
                    [
                        ex("<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>llegué</span>, <span class='fw-token-c'>todos sonrieron</span>.", "When I arrived, everyone smiled.", "Everyday dialogue"),
                        ex("<span class='fw-token-connector'>Cuando</span> <span class='fw-token-v'>puedas</span>, pásate por mi oficina.", "When you can, drop by my office.", "Conversation"),
                        ex("<span class='fw-token-connector'>Cuando</span> sale el sol, la plaza se llena de gente.", "When the sun rises, the square fills with people.", "Dialogue"),
                        ex("<span class='fw-token-connector'>Cuando</span> era niño, vivía cerca del mar.", "When I was a boy, I lived near the sea.", "Subtitles"),
                        ex("<span class='fw-token-connector'>Cuando</span> despertó, el tren ya había llegado.", "When he woke up, the train had already arrived.", "Literature")
                    ]
                )
            ]
        }
    }


def validate_suite(suite: dict, lang: str):
    print(f"Validating {lang.upper()} suite ({len(suite)} words)...")
    total_senses = 0
    total_examples = 0
    for word, entry in suite.items():
        assert entry["word"] == word, f"Key mismatch: {word} vs {entry['word']}"
        assert "role" in entry and entry["role"], f"Missing role in {word}"
        assert "rank" in entry and isinstance(entry["rank"], int), f"Missing rank in {word}"
        assert "frequency" in entry, f"Missing frequency in {word}"
        assert "relations" in entry and len(entry["relations"]) > 0, f"No relations in {word}"

        for i, rel_obj in enumerate(entry["relations"]):
            total_senses += 1
            assert "tag" in rel_obj and rel_obj["tag"], f"Missing tag in {word} rel {i}"
            assert "formulaHTML" in rel_obj and rel_obj["formulaHTML"], f"Missing formulaHTML in {word} rel {i}"
            assert "rule" in rel_obj and rel_obj["rule"], f"Missing rule in {word} rel {i}"
            assert "allowed_lemmas" in rel_obj and isinstance(rel_obj["allowed_lemmas"], list) and len(rel_obj["allowed_lemmas"]) >= 3, f"Missing allowed_lemmas in {word} rel {i}"
            assert "examples" in rel_obj and len(rel_obj["examples"]) >= 5, f"Expected >=5 examples in {word} rel {i}, got {len(rel_obj['examples'])}"
            for j, eg in enumerate(rel_obj["examples"]):
                total_examples += 1
                assert "targetHTML" in eg and "<span class='fw-token-connector'>" in eg["targetHTML"], f"Missing connector span in {word} rel {i} ex {j}: {eg['targetHTML']}"
                assert "translation" in eg and eg["translation"], f"Empty translation in {word} rel {i} ex {j}"
                assert "source" in eg and eg["source"], f"Empty source in {word} rel {i} ex {j}"

    print(f"✓ {lang.upper()}: {len(suite)} words, {total_senses} relation senses, {total_examples} examples (avg {total_examples/total_senses:.1f} per sense).")


def main():
    pt = build_portuguese()
    es = build_spanish()

    validate_suite(pt, "pt")
    validate_suite(es, "es")

    pt_file = DATA_DIR / "pt.json"
    es_file = DATA_DIR / "es.json"

    with open(pt_file, "w", encoding="utf-8") as f:
        json.dump(pt, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(pt)} words to {pt_file}")

    with open(es_file, "w", encoding="utf-8") as f:
        json.dump(es, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(es)} words to {es_file}")


if __name__ == "__main__":
    main()
