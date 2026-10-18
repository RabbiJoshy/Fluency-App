# Function-Word Pattern Coverage & Shortage Report

**Date:** 2026-10-18  
**Matcher Version:** `syntax-assignment/v1.1`  
**Total Patterns Audited:** 115 (51 Spanish, 64 Portuguese)  
**Pilot Patterns (Vetted & Traceable):** 24 patterns (12 words)  

## Executive Summary

- **Speech Deck Coverage:** 69 / 115 patterns with $\ge 3$ distinct verified speech examples (46 shortages).
- **Artist Deck Coverage:** 47 / 115 patterns with $\ge 3$ distinct verified artist examples (68 shortages).
- **Cross-Deck Unified Coverage:** 74 / 115 patterns with $\ge 3$ fresh verified examples (41 shortages).

## Speech Deck Shortages

Patterns with fewer than 3 verified speech matches from dialogue/subtitles:

| Pattern ID | Tag | Formula | Matches Found | Shortage | Reason |
|---|---|---|---|---|---|
| `es:de:0` | Verbs with de | `verb + de` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:de:1` | Adding a detail | `noun + de` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:que:2` | Comparing | `more, less or better + que` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:a:0` | Where to | `a + a place` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:en:1` | When | `en + a time / period` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:por:0` | Why | `por + a reason` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:por:1` | Through / along | `por + a place` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:para:1` | Who for | `para + a person` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:con:0` | Who with | `con + a person` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:con:1` | How / with what | `con + a tool / way of doing it` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:se:0` | Oneself / part of a verb | `se + verb` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:se:1` | Without saying who | `se + verb` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:al:0` | To / at the | `al + destination` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:al:1` | When doing something | `al + infinitive (dictionary form)` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:la:1` | Her / it | `la + verb` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:los:1` | Them | `los + verb` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:lo:0` | The … thing / part | `lo + adjective` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:como:1` | As / in a role | `como + a role / job` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `es:esto:0` | This | `esto + verb` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:de:1` | Adding a detail | `noun + de` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:que:1` | Adding information | `noun + que` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:nos:0` | Us / to us | `nos + verb` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:se:0` | If | `se + a possible situation + what happens then` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:se:1` | Oneself / part of a verb | `se + verb` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:o:1` | Him / it | `o + verb` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:em:0` | Where | `em + a place` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:em:1` | When | `em + a time / period` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:para:0` | Where to | `para + a place` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:para:2` | Who for | `para + a person` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:com:1` | How / with what | `com + a tool / way of doing it` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:por:0` | Why | `por + a reason` | 2 | -1 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:por:1` | Through / along | `por + a place` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:como:0` | Like / in the same way | `verb + como` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:como:1` | As / in a role | `como + a role / job` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:a:0` | Where to | `a + a place` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:a:2` | Her / it | `verb + a` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:ele:1` | After a preposition | `preposition + ele` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:os:1` | Them | `os + verb` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:me:1` | Myself / part of a verb | `verb + -me` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:ao:1` | When doing something | `ao + infinitive (dictionary form)` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:dele:0` | His / of him | `noun + dele` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:dela:0` | Hers / of her | `noun + dela` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:sobre:1` | On / above | `sobre + a place` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:até:0` | Until / as far as | `até + an endpoint` | 1 | -2 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:até:1` | Even | `Até + an unexpected example` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |
| `pt:isso:0` | That | `isso + verb` | 0 | -3 | Corpus scarcity in dialogue/speech material or strict grammatical licensing criteria. |

## Artist Deck Shortages

Patterns with fewer than 3 verified artist matches from lyrics:

| Pattern ID | Tag | Formula | Matches Found | Shortage | Reason |
|---|---|---|---|---|---|
| `es:de:0` | Verbs with de | `verb + de` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:de:1` | Adding a detail | `noun + de` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:que:0` | Saying what you think | `think / say / know / hope + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:que:1` | Adding information | `noun + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:que:2` | Comparing | `more, less or better + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:a:0` | Where to | `a + a place` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:a:1` | Before a person | `a + a person` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:en:0` | Where | `en + a place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:en:1` | When | `en + a time / period` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:por:0` | Why | `por + a reason` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:por:1` | Through / along | `por + a place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:para:0` | What for | `para + infinitive (dictionary form)` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:para:1` | Who for | `para + a person` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:con:0` | Who with | `con + a person` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:con:1` | How / with what | `con + a tool / way of doing it` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:se:0` | Oneself / part of a verb | `se + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:se:1` | Without saying who | `se + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:al:0` | To / at the | `al + destination` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:al:1` | When doing something | `al + infinitive (dictionary form)` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:la:1` | Her / it | `la + verb` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:los:1` | Them | `los + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:lo:0` | The … thing / part | `lo + adjective` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:lo:1` | Him / it / that | `lo + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:como:1` | As / in a role | `como + a role / job` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:tú:0` | you | `Tú + verb` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:esto:0` | This | `esto + verb` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `es:todo:0` | Everything | `todo + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:de:0` | Verbs with de | `verb + de` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:de:1` | Adding a detail | `noun + de` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:que:0` | Saying what you think | `think / say / know / hope + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:que:1` | Adding information | `noun + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:que:2` | Comparing | `more, less or better + que` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:naquele:0` | In / on / at that | `naquele + masculine singular noun` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:nos:0` | Us / to us | `nos + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:nos:1` | In / on / at the | `nos + masculine plural noun` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:se:0` | If | `se + a possible situation + what happens then` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:se:1` | Oneself / part of a verb | `se + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:o:0` | The | `o + masculine singular noun` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:o:1` | Him / it | `o + verb` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:em:0` | Where | `em + a place` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:em:1` | When | `em + a time / period` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:para:0` | Where to | `para + a place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:para:1` | What for | `para + infinitive (dictionary form)` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:para:2` | Who for | `para + a person` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:com:1` | How / with what | `com + a tool / way of doing it` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:por:0` | Why | `por + a reason` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:por:1` | Through / along | `por + a place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:como:1` | As / in a role | `como + a role / job` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:a:0` | Where to | `a + a place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:a:2` | Her / it | `verb + a` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:ele:1` | After a preposition | `preposition + ele` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:ela:0` | she / it | `Ela + verb` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:os:1` | Them | `os + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:me:1` | Myself / part of a verb | `verb + -me` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:ao:1` | When doing something | `ao + infinitive (dictionary form)` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:pelo:0` | Through / by / for the | `por + o + a route / reason` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:numa:0` | In / on / at a | `em + uma + feminine noun` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:dele:0` | His / of him | `noun + dele` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:dela:0` | Hers / of her | `noun + dela` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:sobre:0` | About | `sobre + a topic` | 1 | -2 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:sobre:1` | On / above | `sobre + a place` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:até:0` | Until / as far as | `até + an endpoint` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:até:1` | Even | `Até + an unexpected example` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:porque:0` | Because | `porque + a reason` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:quando:0` | When | `Quando + a situation , what happens` | 2 | -1 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:isso:0` | That | `isso + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:isto:0` | This | `isto + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |
| `pt:tudo:0` | Everything | `tudo + verb` | 0 | -3 | Corpus scarcity in artist lyrics material or strict grammatical licensing criteria. |

## Cross-Deck Unified Shortage Inventory

| Pattern ID | Tag | Formula | Fresh Found | Shortage | Speech | Artist | Reason |
|---|---|---|---|---|---|---|---|
| `es:de:0` | Verbs with de | `verb + de` | 1 | -2 | 1 | 0 | Pilot pattern with vetted traceable baseline examples; 1 additional fresh matches harvested. |
| `es:de:1` | Adding a detail | `noun + de` | 0 | -3 | 0 | 0 | Pilot pattern with vetted traceable baseline examples; 0 additional fresh matches harvested. |
| `es:que:2` | Comparing | `more, less or better + que` | 2 | -1 | 2 | 0 | Pilot pattern with vetted traceable baseline examples; 2 additional fresh matches harvested. |
| `es:en:1` | When | `en + a time / period` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:por:0` | Why | `por + a reason` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:por:1` | Through / along | `por + a place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:para:1` | Who for | `para + a person` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:con:0` | Who with | `con + a person` | 2 | -1 | 2 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:con:1` | How / with what | `con + a tool / way of doing it` | 1 | -2 | 1 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:se:0` | Oneself / part of a verb | `se + verb` | 1 | -2 | 1 | 0 | Pilot pattern with vetted traceable baseline examples; 1 additional fresh matches harvested. |
| `es:se:1` | Without saying who | `se + verb` | 0 | -3 | 0 | 0 | Pilot pattern with vetted traceable baseline examples; 0 additional fresh matches harvested. |
| `es:al:0` | To / at the | `al + destination` | 0 | -3 | 0 | 0 | Pilot pattern with vetted traceable baseline examples; 0 additional fresh matches harvested. |
| `es:al:1` | When doing something | `al + infinitive (dictionary form)` | 0 | -3 | 0 | 0 | Pilot pattern with vetted traceable baseline examples; 0 additional fresh matches harvested. |
| `es:la:1` | Her / it | `la + verb` | 1 | -2 | 0 | 1 | Pilot pattern with vetted traceable baseline examples; 1 additional fresh matches harvested. |
| `es:los:1` | Them | `los + verb` | 2 | -1 | 2 | 0 | Pilot pattern with vetted traceable baseline examples; 2 additional fresh matches harvested. |
| `es:lo:0` | The … thing / part | `lo + adjective` | 2 | -1 | 2 | 0 | Pilot pattern with vetted traceable baseline examples; 2 additional fresh matches harvested. |
| `es:como:1` | As / in a role | `como + a role / job` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:de:1` | Adding a detail | `noun + de` | 0 | -3 | 0 | 0 | Pilot pattern with vetted traceable baseline examples; 0 additional fresh matches harvested. |
| `pt:que:1` | Adding information | `noun + que` | 2 | -1 | 2 | 0 | Pilot pattern with vetted traceable baseline examples; 2 additional fresh matches harvested. |
| `pt:nos:0` | Us / to us | `nos + verb` | 1 | -2 | 1 | 0 | Pilot pattern with vetted traceable baseline examples; 1 additional fresh matches harvested. |
| `pt:se:0` | If | `se + a possible situation + what happens then` | 1 | -2 | 1 | 0 | Pilot pattern with vetted traceable baseline examples; 1 additional fresh matches harvested. |
| `pt:se:1` | Oneself / part of a verb | `se + verb` | 0 | -3 | 0 | 0 | Pilot pattern with vetted traceable baseline examples; 0 additional fresh matches harvested. |
| `pt:em:1` | When | `em + a time / period` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:para:0` | Where to | `para + a place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:para:2` | Who for | `para + a person` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:com:1` | How / with what | `com + a tool / way of doing it` | 2 | -1 | 1 | 1 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:por:0` | Why | `por + a reason` | 2 | -1 | 2 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:por:1` | Through / along | `por + a place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:como:1` | As / in a role | `como + a role / job` | 1 | -2 | 0 | 1 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:a:0` | Where to | `a + a place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:a:2` | Her / it | `verb + a` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:ele:1` | After a preposition | `preposition + ele` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:os:1` | Them | `os + verb` | 1 | -2 | 1 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:me:1` | Myself / part of a verb | `verb + -me` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:ao:1` | When doing something | `ao + infinitive (dictionary form)` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:dele:0` | His / of him | `noun + dele` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:dela:0` | Hers / of her | `noun + dela` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:sobre:1` | On / above | `sobre + a place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:até:0` | Until / as far as | `até + an endpoint` | 1 | -2 | 1 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:até:1` | Even | `Até + an unexpected example` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:isso:0` | That | `isso + verb` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |

## Complete Pattern Breakdown

| Pattern ID | Tag | Total Assigned | Fresh Total | Speech Deck | Artist Deck | Unified Status |
|---|---|---|---|---|---|---|
| `es:a:0` | Where to | 3 | 3 | 2 | 1 | Full verified coverage |
| `es:a:1` | Before a person | 3 | 5 | 4 | 1 | Full verified coverage |
| `es:al:0` | To / at the | 3 | 0 | 0 | 0 | Shortage reported |
| `es:al:1` | When doing something | 3 | 0 | 0 | 0 | Shortage reported |
| `es:algo:0` | Something | 3 | 14 | 10 | 4 | Full verified coverage |
| `es:como:0` | Like / in the same way | 3 | 8 | 4 | 4 | Full verified coverage |
| `es:como:1` | As / in a role | 3 | 0 | 0 | 0 | Shortage reported |
| `es:con:0` | Who with | 3 | 2 | 2 | 0 | Shortage reported |
| `es:con:1` | How / with what | 3 | 1 | 1 | 0 | Shortage reported |
| `es:cuando:0` | When | 3 | 18 | 12 | 6 | Full verified coverage |
| `es:de:0` | Verbs with de | 3 | 1 | 1 | 0 | Shortage reported |
| `es:de:1` | Adding a detail | 3 | 0 | 0 | 0 | Shortage reported |
| `es:del:0` | Of / from the | 3 | 16 | 11 | 5 | Full verified coverage |
| `es:el:0` | The | 3 | 18 | 13 | 5 | Full verified coverage |
| `es:en:0` | Where | 3 | 7 | 7 | 0 | Full verified coverage |
| `es:en:1` | When | 3 | 0 | 0 | 0 | Shortage reported |
| `es:eso:0` | That | 3 | 7 | 4 | 3 | Full verified coverage |
| `es:esto:0` | This | 3 | 3 | 2 | 1 | Full verified coverage |
| `es:la:0` | The | 3 | 20 | 14 | 6 | Full verified coverage |
| `es:la:1` | Her / it | 3 | 1 | 0 | 1 | Shortage reported |
| `es:las:0` | The | 3 | 17 | 12 | 5 | Full verified coverage |
| `es:le:0` | To him / her / you | 3 | 21 | 15 | 6 | Full verified coverage |
| `es:lo:0` | The … thing / part | 3 | 2 | 2 | 0 | Shortage reported |
| `es:lo:1` | Him / it / that | 3 | 6 | 6 | 0 | Full verified coverage |
| `es:los:0` | The | 3 | 20 | 13 | 7 | Full verified coverage |
| `es:los:1` | Them | 3 | 2 | 2 | 0 | Shortage reported |
| `es:me:0` | Me / to me | 3 | 18 | 12 | 6 | Full verified coverage |
| `es:mi:0` | My | 3 | 20 | 15 | 5 | Full verified coverage |
| `es:nos:0` | Us / to us | 3 | 20 | 15 | 5 | Full verified coverage |
| `es:para:0` | What for | 3 | 8 | 8 | 0 | Full verified coverage |
| `es:para:1` | Who for | 3 | 0 | 0 | 0 | Shortage reported |
| `es:pero:0` | But | 3 | 22 | 15 | 7 | Full verified coverage |
| `es:por:0` | Why | 3 | 0 | 0 | 0 | Shortage reported |
| `es:por:1` | Through / along | 3 | 0 | 0 | 0 | Shortage reported |
| `es:porque:0` | Because | 3 | 20 | 15 | 5 | Full verified coverage |
| `es:que:0` | Saying what you think | 3 | 4 | 4 | 0 | Full verified coverage |
| `es:que:1` | Adding information | 3 | 3 | 3 | 0 | Full verified coverage |
| `es:que:2` | Comparing | 3 | 2 | 2 | 0 | Shortage reported |
| `es:se:0` | Oneself / part of a verb | 3 | 1 | 1 | 0 | Shortage reported |
| `es:se:1` | Without saying who | 3 | 0 | 0 | 0 | Shortage reported |
| `es:si:0` | If | 3 | 18 | 13 | 5 | Full verified coverage |
| `es:sin:0` | Without | 3 | 16 | 11 | 5 | Full verified coverage |
| `es:su:0` | His / her / their / your (formal) | 3 | 19 | 15 | 4 | Full verified coverage |
| `es:te:0` | You / to you | 3 | 21 | 15 | 6 | Full verified coverage |
| `es:todo:0` | Everything | 3 | 3 | 3 | 0 | Full verified coverage |
| `es:tu:0` | Your (informal) | 3 | 20 | 14 | 6 | Full verified coverage |
| `es:tú:0` | you | 3 | 6 | 4 | 2 | Full verified coverage |
| `es:un:0` | A / an | 3 | 17 | 11 | 6 | Full verified coverage |
| `es:una:0` | A / an | 3 | 21 | 14 | 7 | Full verified coverage |
| `es:y:0` | And | 3 | 14 | 8 | 6 | Full verified coverage |
| `es:yo:0` | I | 3 | 12 | 7 | 5 | Full verified coverage |
| `pt:a:0` | Where to | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:a:1` | The | 3 | 12 | 5 | 7 | Full verified coverage |
| `pt:a:2` | Her / it | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:ao:0` | To / at the | 3 | 16 | 12 | 4 | Full verified coverage |
| `pt:ao:1` | When doing something | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:as:0` | The | 3 | 19 | 14 | 5 | Full verified coverage |
| `pt:até:0` | Until / as far as | 3 | 1 | 1 | 0 | Shortage reported |
| `pt:até:1` | Even | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:com:0` | Who with | 3 | 7 | 4 | 3 | Full verified coverage |
| `pt:com:1` | How / with what | 3 | 2 | 1 | 1 | Shortage reported |
| `pt:como:0` | Like / in the same way | 3 | 7 | 1 | 6 | Full verified coverage |
| `pt:como:1` | As / in a role | 3 | 1 | 0 | 1 | Shortage reported |
| `pt:da:0` | Of / from the | 3 | 20 | 14 | 6 | Full verified coverage |
| `pt:de:0` | Verbs with de | 3 | 5 | 4 | 1 | Full verified coverage |
| `pt:de:1` | Adding a detail | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:dela:0` | Hers / of her | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:dele:0` | His / of him | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:do:0` | Of / from the | 3 | 20 | 15 | 5 | Full verified coverage |
| `pt:e:0` | And | 3 | 21 | 13 | 8 | Full verified coverage |
| `pt:ela:0` | she / it | 3 | 7 | 6 | 1 | Full verified coverage |
| `pt:ele:0` | he / it | 3 | 17 | 12 | 5 | Full verified coverage |
| `pt:ele:1` | After a preposition | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:em:0` | Where | 3 | 3 | 2 | 1 | Full verified coverage |
| `pt:em:1` | When | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:eu:0` | I | 3 | 13 | 6 | 7 | Full verified coverage |
| `pt:isso:0` | That | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:isto:0` | This | 3 | 3 | 3 | 0 | Full verified coverage |
| `pt:lhe:0` | To him / her / you | 3 | 10 | 7 | 3 | Full verified coverage |
| `pt:mas:0` | But | 3 | 18 | 14 | 4 | Full verified coverage |
| `pt:me:0` | Me / to me | 3 | 14 | 6 | 8 | Full verified coverage |
| `pt:me:1` | Myself / part of a verb | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:na:0` | In / on / at the | 3 | 23 | 15 | 8 | Full verified coverage |
| `pt:naquele:0` | In / on / at that | 3 | 15 | 15 | 0 | Full verified coverage |
| `pt:no:0` | In / on / at the | 3 | 22 | 14 | 8 | Full verified coverage |
| `pt:nos:0` | Us / to us | 3 | 1 | 1 | 0 | Shortage reported |
| `pt:nos:1` | In / on / at the | 3 | 7 | 5 | 2 | Full verified coverage |
| `pt:num:0` | In / on / at a | 3 | 17 | 13 | 4 | Full verified coverage |
| `pt:numa:0` | In / on / at a | 3 | 15 | 14 | 1 | Full verified coverage |
| `pt:o:0` | The | 3 | 10 | 8 | 2 | Full verified coverage |
| `pt:o:1` | Him / it | 3 | 3 | 2 | 1 | Full verified coverage |
| `pt:os:0` | The | 3 | 14 | 11 | 3 | Full verified coverage |
| `pt:os:1` | Them | 3 | 1 | 1 | 0 | Shortage reported |
| `pt:para:0` | Where to | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:para:1` | What for | 3 | 12 | 10 | 2 | Full verified coverage |
| `pt:para:2` | Who for | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:pela:0` | Through / by / for the | 3 | 18 | 13 | 5 | Full verified coverage |
| `pt:pelo:0` | Through / by / for the | 3 | 13 | 11 | 2 | Full verified coverage |
| `pt:por:0` | Why | 3 | 2 | 2 | 0 | Shortage reported |
| `pt:por:1` | Through / along | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:porque:0` | Because | 3 | 17 | 15 | 2 | Full verified coverage |
| `pt:quando:0` | When | 3 | 13 | 11 | 2 | Full verified coverage |
| `pt:que:0` | Saying what you think | 3 | 6 | 6 | 0 | Full verified coverage |
| `pt:que:1` | Adding information | 3 | 2 | 2 | 0 | Shortage reported |
| `pt:que:2` | Comparing | 3 | 5 | 5 | 0 | Full verified coverage |
| `pt:se:0` | If | 3 | 1 | 1 | 0 | Shortage reported |
| `pt:se:1` | Oneself / part of a verb | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:sem:0` | Without | 3 | 16 | 13 | 3 | Full verified coverage |
| `pt:sobre:0` | About | 3 | 9 | 8 | 1 | Full verified coverage |
| `pt:sobre:1` | On / above | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:te:0` | You / to you | 3 | 14 | 8 | 6 | Full verified coverage |
| `pt:tudo:0` | Everything | 3 | 3 | 3 | 0 | Full verified coverage |
| `pt:um:0` | A / an | 3 | 20 | 12 | 8 | Full verified coverage |
| `pt:uma:0` | A / an | 3 | 16 | 11 | 5 | Full verified coverage |
| `pt:à:0` | To / at the | 3 | 18 | 15 | 3 | Full verified coverage |
