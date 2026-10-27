# Function-Word Pattern Coverage & Shortage Report

**Date:** 2026-10-18  
**Matcher Version:** `syntax-assignment/v1.2`  
**Total Patterns Audited:** 120 (51 Spanish, 64 Portuguese)  
**Pilot Patterns (Vetted & Traceable):** 24 patterns (12 words)  

## Executive Summary

- **Speech Deck Coverage:** 105 / 120 patterns with $\ge 3$ distinct verified speech examples (15 shortages).
- **Artist Deck Coverage:** 42 / 120 patterns with $\ge 3$ distinct verified artist examples (78 shortages).
- **Cross-Deck Unified Coverage:** 103 / 120 patterns with $\ge 3$ fresh verified examples (17 shortages).

## Speech Deck Shortages

Patterns with fewer than 3 verified speech matches from dialogue/subtitles:

| Pattern ID | Tag | Formula | Matches Found | Shortage | Reason |
|---|---|---|---|---|---|
| `es:por:0` | because of, for | `por + reason` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:por:1` | through, around | `por + place` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:para:1` | for | `para + person` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:como:1` | as | `como + role` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:para:0` | to | `para + place` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:para:2` | for | `para + person` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:por:1` | through, around | `por + place` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:a:0` | to | `a + place` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:a:2` | her, it | `verb + a` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:ele:1` | him, it (after a preposition) | `preposition + ele` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:me:1` | myself | `verb + -me` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:ao:1` | when, on (doing) | `ao + verb` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:dele:0` | his | `noun + dele` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:dela:0` | her, hers | `noun + dela` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:sobre:1` | on, above | `sobre + place` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |

## Artist Deck Shortages

Patterns with fewer than 3 verified artist matches from lyrics:

| Pattern ID | Tag | Formula | Matches Found | Shortage | Reason |
|---|---|---|---|---|---|
| `es:de:0` | of, about (after some verbs) | `verb + de` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:de:1` | of, from | `noun + de` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:que:2` | than | `more / less + que` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:en:1` | in, on | `en + time` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:por:0` | because of, for | `por + reason` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:por:1` | through, around | `por + place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:para:1` | for | `para + person` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:con:1` | with, using | `con + thing` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:se:1` | people, one (no one in particular) | `se + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:al:0` | to the | `al + place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:al:1` | when, on (doing) | `al + verb` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:lo:0` | the … thing | `lo + adjective` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:como:1` | as | `como + role` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:todo:1` | all the | `todo + el + noun` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:de:0` | of, about (after some verbs) | `verb + de` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:de:1` | of, from | `noun + de` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:que:0` | that | `think / say + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:que:1` | that, who, which | `noun + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:que:2` | than | `more / less + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:naquele:0` | in that, on that, at that | `naquele + noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:nos:0` | us, to us | `nos + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:nos:1` | in the, on the, at the | `nos + masculine nouns` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:se:0` | if | `se … , …` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:se:1` | himself, herself, themselves | `se + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:o:0` | the | `o + masculine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:o:1` | him, it | `o + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:em:0` | in, at, on | `em + place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:em:1` | in, on | `em + time` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:para:0` | to | `para + place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:para:1` | to, in order to | `para + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:para:2` | for | `para + person` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:com:0` | with | `com + person` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:com:1` | with, using | `com + thing` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:por:0` | because of, for | `por + reason` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:por:1` | through, around | `por + place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:no:0` | in the, on the, at the | `no + masculine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:na:0` | in the, on the, at the | `na + feminine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:do:0` | of the, from the | `do + masculine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:da:0` | of the, from the | `da + feminine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:como:0` | like, the way | `verb + como` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:como:1` | as | `como + role` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:mas:0` | but | `mas …` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:a:0` | to | `a + place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:a:1` | the | `a + feminine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:a:2` | her, it | `verb + a` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:e:0` | and | `… e …` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:eu:0` | I | `eu + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:ele:0` | he, it | `ele + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:ele:1` | him, it (after a preposition) | `preposition + ele` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:ela:0` | she, it | `ela + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:um:0` | a, an | `um + masculine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:uma:0` | a, an | `uma + feminine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:os:0` | the | `os + masculine nouns` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:os:1` | them | `os + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:as:0` | the | `as + feminine nouns` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:me:0` | me, to me | `me + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:me:1` | myself | `verb + -me` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:te:0` | you, to you | `te + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:lhe:0` | to him, to her, to you | `lhe + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:ao:0` | to the, at the | `ao + place / time` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:ao:1` | when, on (doing) | `ao + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:à:0` | to the, at the | `à + place / time` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:pelo:0` | through the, by the, for the | `pelo + route / reason` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:pela:0` | through the, by the, for the | `pela + route / reason` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:num:0` | in a, on a, at a | `num + masculine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:numa:0` | in a, on a, at a | `numa + feminine noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:dele:0` | his | `noun + dele` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:dela:0` | her, hers | `noun + dela` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:sem:0` | without | `sem + thing` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:sobre:0` | about | `sobre + topic` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:sobre:1` | on, above | `sobre + place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:até:0` | until, as far as | `até + endpoint` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:até:1` | even | `até + …` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:porque:0` | because | `porque …` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:quando:0` | when | `quando … , …` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:isso:0` | that | `isso + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:isto:0` | this | `isto + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:tudo:0` | everything | `tudo + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |

## Cross-Deck Unified Shortage Inventory

| Pattern ID | Tag | Formula | Fresh Found | Shortage | Speech | Artist | Reason |
|---|---|---|---|---|---|---|---|
| `es:de:1` | of, from | `noun + de` | 1 | -2 | 1 | 0 | Pilot pattern with vetted traceable baseline examples; 1 additional fresh matches harvested. |
| `es:por:1` | through, around | `por + place` | 1 | -2 | 1 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:para:1` | for | `para + person` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:se:1` | people, one (no one in particular) | `se + verb` | 0 | -3 | 0 | 0 | Pilot pattern with vetted traceable baseline examples; 0 additional fresh matches harvested. |
| `es:como:1` | as | `como + role` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:se:1` | himself, herself, themselves | `se + verb` | 0 | -3 | 0 | 0 | Pilot pattern with vetted traceable baseline examples; 0 additional fresh matches harvested. |
| `pt:para:0` | to | `para + place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:para:2` | for | `para + person` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:por:1` | through, around | `por + place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:a:0` | to | `a + place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:a:2` | her, it | `verb + a` | 2 | -1 | 2 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:ele:1` | him, it (after a preposition) | `preposition + ele` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:me:1` | myself | `verb + -me` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:ao:1` | when, on (doing) | `ao + verb` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:dele:0` | his | `noun + dele` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:dela:0` | her, hers | `noun + dela` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:sobre:1` | on, above | `sobre + place` | 2 | -1 | 2 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |

## Complete Pattern Breakdown

| Pattern ID | Tag | Total Assigned | Fresh Total | Speech Deck | Artist Deck | Unified Status |
|---|---|---|---|---|---|---|
| `es:a:0` | to | 15 | 22 | 17 | 5 | Full verified coverage |
| `es:a:1` | not translated: marks the person | 15 | 48 | 27 | 21 | Full verified coverage |
| `es:al:0` | to the | 6 | 3 | 3 | 0 | Full verified coverage |
| `es:al:1` | when, on (doing) | 14 | 11 | 10 | 1 | Full verified coverage |
| `es:algo:0` | something | 30 | 132 | 109 | 23 | Full verified coverage |
| `es:como:0` | like, the way | 15 | 20 | 17 | 3 | Full verified coverage |
| `es:como:1` | as | 5 | 0 | 0 | 0 | Shortage reported |
| `es:con:0` | with | 15 | 63 | 45 | 18 | Full verified coverage |
| `es:con:1` | with, using | 9 | 4 | 3 | 1 | Full verified coverage |
| `es:cuando:0` | when | 30 | 180 | 141 | 39 | Full verified coverage |
| `es:de:0` | of, about (after some verbs) | 11 | 8 | 8 | 0 | Full verified coverage |
| `es:de:1` | of, from | 4 | 1 | 1 | 0 | Shortage reported |
| `es:del:0` | of the, from the | 30 | 159 | 131 | 28 | Full verified coverage |
| `es:el:0` | the | 30 | 182 | 126 | 56 | Full verified coverage |
| `es:en:0` | in, at, on | 15 | 38 | 35 | 3 | Full verified coverage |
| `es:en:1` | in, on | 12 | 7 | 6 | 1 | Full verified coverage |
| `es:eso:0` | that | 30 | 39 | 32 | 7 | Full verified coverage |
| `es:esto:0` | this | 30 | 38 | 32 | 6 | Full verified coverage |
| `es:la:0` | the | 15 | 184 | 134 | 50 | Full verified coverage |
| `es:la:1` | her, it | 15 | 21 | 5 | 16 | Full verified coverage |
| `es:las:0` | the | 30 | 145 | 127 | 18 | Full verified coverage |
| `es:le:0` | to him, to her, to you | 30 | 194 | 148 | 46 | Full verified coverage |
| `es:lo:0` | the … thing | 12 | 14 | 12 | 2 | Full verified coverage |
| `es:lo:1` | him, it | 12 | 90 | 69 | 21 | Full verified coverage |
| `es:lo:2` | what, the thing that | 12 | 82 | 51 | 31 | Full verified coverage |
| `es:los:0` | the | 15 | 130 | 108 | 22 | Full verified coverage |
| `es:los:1` | them | 15 | 14 | 11 | 3 | Full verified coverage |
| `es:me:0` | me, to me | 15 | 172 | 107 | 65 | Full verified coverage |
| `es:me:1` | myself | 15 | 50 | 37 | 13 | Full verified coverage |
| `es:mi:0` | my | 30 | 185 | 145 | 40 | Full verified coverage |
| `es:nos:0` | us, to us | 15 | 119 | 99 | 20 | Full verified coverage |
| `es:nos:1` | ourselves, each other | 15 | 60 | 51 | 9 | Full verified coverage |
| `es:para:0` | to, in order to | 15 | 75 | 67 | 8 | Full verified coverage |
| `es:para:1` | for | 5 | 0 | 0 | 0 | Shortage reported |
| `es:pero:0` | but | 30 | 194 | 149 | 45 | Full verified coverage |
| `es:por:0` | because of, for | 8 | 3 | 2 | 1 | Full verified coverage |
| `es:por:1` | through, around | 6 | 1 | 1 | 0 | Shortage reported |
| `es:porque:0` | because | 30 | 187 | 148 | 39 | Full verified coverage |
| `es:que:0` | that | 12 | 47 | 38 | 9 | Full verified coverage |
| `es:que:1` | that, who, which | 12 | 40 | 23 | 17 | Full verified coverage |
| `es:que:2` | than | 12 | 17 | 15 | 2 | Full verified coverage |
| `es:se:0` | himself, herself, themselves | 13 | 10 | 7 | 3 | Full verified coverage |
| `es:se:1` | people, one (no one in particular) | 3 | 0 | 0 | 0 | Shortage reported |
| `es:si:0` | if | 30 | 167 | 129 | 38 | Full verified coverage |
| `es:sin:0` | without | 30 | 149 | 123 | 26 | Full verified coverage |
| `es:su:0` | his, her, their, your | 30 | 170 | 143 | 27 | Full verified coverage |
| `es:te:0` | you, to you | 15 | 178 | 109 | 69 | Full verified coverage |
| `es:te:1` | yourself | 15 | 50 | 40 | 10 | Full verified coverage |
| `es:todo:0` | everything | 15 | 23 | 18 | 5 | Full verified coverage |
| `es:todo:1` | all the | 15 | 36 | 35 | 1 | Full verified coverage |
| `es:tu:0` | your | 30 | 186 | 138 | 48 | Full verified coverage |
| `es:tú:0` | you | 30 | 67 | 48 | 19 | Full verified coverage |
| `es:un:0` | a, an | 30 | 167 | 127 | 40 | Full verified coverage |
| `es:una:0` | a, an | 30 | 165 | 136 | 29 | Full verified coverage |
| `es:y:0` | and | 30 | 181 | 115 | 66 | Full verified coverage |
| `es:yo:0` | I | 30 | 120 | 71 | 49 | Full verified coverage |
| `pt:a:0` | to | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:a:1` | the | 12 | 66 | 66 | 0 | Full verified coverage |
| `pt:a:2` | her, it | 7 | 2 | 2 | 0 | Shortage reported |
| `pt:ao:0` | to the, at the | 15 | 133 | 133 | 0 | Full verified coverage |
| `pt:ao:1` | when, on (doing) | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:as:0` | the | 30 | 120 | 120 | 0 | Full verified coverage |
| `pt:até:0` | until, as far as | 15 | 12 | 12 | 0 | Full verified coverage |
| `pt:até:1` | even | 11 | 6 | 6 | 0 | Full verified coverage |
| `pt:com:0` | with | 15 | 51 | 51 | 0 | Full verified coverage |
| `pt:com:1` | with, using | 10 | 5 | 5 | 0 | Full verified coverage |
| `pt:como:0` | like, the way | 10 | 5 | 4 | 1 | Full verified coverage |
| `pt:como:1` | as | 10 | 5 | 5 | 0 | Full verified coverage |
| `pt:da:0` | of the, from the | 30 | 142 | 142 | 0 | Full verified coverage |
| `pt:de:0` | of, about (after some verbs) | 15 | 31 | 31 | 0 | Full verified coverage |
| `pt:de:1` | of, from | 8 | 5 | 5 | 0 | Full verified coverage |
| `pt:dela:0` | her, hers | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:dele:0` | his | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:do:0` | of the, from the | 30 | 120 | 120 | 0 | Full verified coverage |
| `pt:e:0` | and | 30 | 141 | 140 | 1 | Full verified coverage |
| `pt:ela:0` | she, it | 30 | 87 | 87 | 0 | Full verified coverage |
| `pt:ele:0` | he, it | 15 | 100 | 100 | 0 | Full verified coverage |
| `pt:ele:1` | him, it (after a preposition) | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:em:0` | in, at, on | 15 | 17 | 17 | 0 | Full verified coverage |
| `pt:em:1` | in, on | 11 | 6 | 6 | 0 | Full verified coverage |
| `pt:eu:0` | I | 30 | 95 | 95 | 0 | Full verified coverage |
| `pt:isso:0` | that | 30 | 26 | 26 | 0 | Full verified coverage |
| `pt:isto:0` | this | 30 | 32 | 32 | 0 | Full verified coverage |
| `pt:lhe:0` | to him, to her, to you | 30 | 74 | 74 | 0 | Full verified coverage |
| `pt:mas:0` | but | 30 | 142 | 142 | 0 | Full verified coverage |
| `pt:me:0` | me, to me | 15 | 83 | 83 | 0 | Full verified coverage |
| `pt:me:1` | myself | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:na:0` | in the, on the, at the | 30 | 144 | 144 | 0 | Full verified coverage |
| `pt:naquele:0` | in that, on that, at that | 30 | 149 | 149 | 0 | Full verified coverage |
| `pt:no:0` | in the, on the, at the | 30 | 141 | 141 | 0 | Full verified coverage |
| `pt:nos:0` | us, to us | 15 | 14 | 14 | 0 | Full verified coverage |
| `pt:nos:1` | in the, on the, at the | 15 | 39 | 39 | 0 | Full verified coverage |
| `pt:num:0` | in a, on a, at a | 30 | 136 | 136 | 0 | Full verified coverage |
| `pt:numa:0` | in a, on a, at a | 30 | 137 | 137 | 0 | Full verified coverage |
| `pt:o:0` | the | 15 | 95 | 95 | 0 | Full verified coverage |
| `pt:o:1` | him, it | 14 | 11 | 11 | 0 | Full verified coverage |
| `pt:os:0` | the | 15 | 113 | 111 | 2 | Full verified coverage |
| `pt:os:1` | them | 9 | 4 | 4 | 0 | Full verified coverage |
| `pt:para:0` | to | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:para:1` | to, in order to | 12 | 67 | 67 | 0 | Full verified coverage |
| `pt:para:2` | for | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:pela:0` | through the, by the, for the | 30 | 133 | 133 | 0 | Full verified coverage |
| `pt:pelo:0` | through the, by the, for the | 30 | 128 | 128 | 0 | Full verified coverage |
| `pt:por:0` | because of, for | 15 | 35 | 35 | 0 | Full verified coverage |
| `pt:por:1` | through, around | 5 | 0 | 0 | 0 | Shortage reported |
| `pt:porque:0` | because | 30 | 144 | 144 | 0 | Full verified coverage |
| `pt:quando:0` | when | 30 | 100 | 100 | 0 | Full verified coverage |
| `pt:que:0` | that | 12 | 50 | 50 | 0 | Full verified coverage |
| `pt:que:1` | that, who, which | 12 | 16 | 16 | 0 | Full verified coverage |
| `pt:que:2` | than | 12 | 19 | 19 | 0 | Full verified coverage |
| `pt:se:0` | if | 15 | 21 | 21 | 0 | Full verified coverage |
| `pt:se:1` | himself, herself, themselves | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:sem:0` | without | 30 | 135 | 135 | 0 | Full verified coverage |
| `pt:sobre:0` | about | 15 | 58 | 58 | 0 | Full verified coverage |
| `pt:sobre:1` | on, above | 7 | 2 | 2 | 0 | Shortage reported |
| `pt:te:0` | you, to you | 30 | 76 | 76 | 0 | Full verified coverage |
| `pt:tudo:0` | everything | 29 | 24 | 24 | 0 | Full verified coverage |
| `pt:um:0` | a, an | 30 | 114 | 114 | 0 | Full verified coverage |
| `pt:uma:0` | a, an | 30 | 119 | 119 | 0 | Full verified coverage |
| `pt:à:0` | to the, at the | 30 | 146 | 146 | 0 | Full verified coverage |
