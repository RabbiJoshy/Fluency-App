# Function-Word Pattern Coverage & Shortage Report

**Date:** 2026-10-18  
**Matcher Version:** `syntax-assignment/v1.1`  
**Total Patterns Audited:** 115 (51 Spanish, 64 Portuguese)  
**Pilot Patterns (Vetted & Traceable):** 24 patterns (12 words)  
**Patterns with >= 3 Fresh Verified Examples:** 90  
**Patterns with Reported Shortages (< 3 fresh examples):** 25  

## Shortage Inventory

The following patterns have fewer than 3 verified fresh matches in the source speech and artist corpora.
To ensure card rendering and flip-cycling remain operational in the app, existing placeholder examples
are retained as secondary fallbacks (`is_legacy_fallback: true`), while the shortages are documented below.

| Pattern ID | Tag | Formula | Fresh Found | Shortage | Speech Matches | Artist Matches | Reason |
|---|---|---|---|---|---|---|---|
| `es:en:1` | When | `en + a time / period` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:por:0` | Why | `por + a reason` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:por:1` | Through / along | `por + a place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:para:1` | Who for | `para + a person` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:con:0` | Who with | `con + a person` | 2 | -1 | 2 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:con:1` | How / with what | `con + a tool / way of doing it` | 1 | -2 | 1 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `es:como:1` | As / in a role | `como + a role / job` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:em:1` | When | `em + a time / period` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:para:0` | Where to | `para + a place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:para:2` | Who for | `para + a person` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:com:1` | How / with what | `com + a tool / way of doing it` | 2 | -1 | 1 | 1 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:por:0` | Why | `por + a reason` | 1 | -2 | 1 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:por:1` | Through / along | `por + a place` | 2 | -1 | 2 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:a:0` | Where to | `a + a place` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:a:2` | Her / it | `verb + a` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:ele:1` | After a preposition | `preposition + ele` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:os:1` | Them | `os + verb` | 1 | -2 | 1 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:me:1` | Myself / part of a verb | `verb + -me` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:ao:1` | When doing something | `ao + infinitive (dictionary form)` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:dele:0` | His / of him | `noun + dele` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:dela:0` | Hers / of her | `noun + dela` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:sobre:1` | On / above | `sobre + a place` | 2 | -1 | 2 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:até:0` | Until / as far as | `até + an endpoint` | 1 | -2 | 1 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:até:1` | Even | `Até + an unexpected example` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |
| `pt:isso:0` | That | `isso + verb` | 0 | -3 | 0 | 0 | Corpus scarcity or strict grammatical licensing criteria under UD dependency parsing. |

## Complete Pattern Breakdown

| Pattern ID | Tag | Total Examples | Fresh Matches | Speech | Artist | Status |
|---|---|---|---|---|---|---|
| `es:a:0` | Where to | 3 | 3 | 2 | 1 | Full verified coverage |
| `es:a:1` | Before a person | 3 | 5 | 4 | 1 | Full verified coverage |
| `es:al:0` | To / at the | 3 | 0 | 0 | 0 | Full verified coverage |
| `es:al:1` | When doing something | 3 | 0 | 0 | 0 | Full verified coverage |
| `es:algo:0` | Something | 3 | 14 | 10 | 4 | Full verified coverage |
| `es:como:0` | Like / in the same way | 3 | 21 | 14 | 7 | Full verified coverage |
| `es:como:1` | As / in a role | 3 | 0 | 0 | 0 | Shortage reported |
| `es:con:0` | Who with | 3 | 2 | 2 | 0 | Shortage reported |
| `es:con:1` | How / with what | 3 | 1 | 1 | 0 | Shortage reported |
| `es:cuando:0` | When | 3 | 18 | 12 | 6 | Full verified coverage |
| `es:de:0` | Verbs with de | 3 | 1 | 1 | 0 | Full verified coverage |
| `es:de:1` | Adding a detail | 3 | 0 | 0 | 0 | Full verified coverage |
| `es:del:0` | Of / from the | 3 | 16 | 11 | 5 | Full verified coverage |
| `es:el:0` | The | 3 | 18 | 13 | 5 | Full verified coverage |
| `es:en:0` | Where | 3 | 21 | 15 | 6 | Full verified coverage |
| `es:en:1` | When | 3 | 0 | 0 | 0 | Shortage reported |
| `es:eso:0` | That | 3 | 7 | 4 | 3 | Full verified coverage |
| `es:esto:0` | This | 3 | 3 | 2 | 1 | Full verified coverage |
| `es:la:0` | The | 3 | 20 | 14 | 6 | Full verified coverage |
| `es:la:1` | Her / it | 3 | 1 | 0 | 1 | Full verified coverage |
| `es:las:0` | The | 3 | 17 | 12 | 5 | Full verified coverage |
| `es:le:0` | To him / her / you | 3 | 21 | 15 | 6 | Full verified coverage |
| `es:lo:0` | The … thing / part | 3 | 2 | 2 | 0 | Full verified coverage |
| `es:lo:1` | Him / it / that | 3 | 6 | 6 | 0 | Full verified coverage |
| `es:los:0` | The | 3 | 20 | 13 | 7 | Full verified coverage |
| `es:los:1` | Them | 3 | 2 | 2 | 0 | Full verified coverage |
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
| `es:que:2` | Comparing | 3 | 2 | 2 | 0 | Full verified coverage |
| `es:se:0` | Oneself / part of a verb | 3 | 1 | 1 | 0 | Full verified coverage |
| `es:se:1` | Without saying who | 3 | 0 | 0 | 0 | Full verified coverage |
| `es:si:0` | If | 3 | 22 | 15 | 7 | Full verified coverage |
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
| `pt:como:0` | Like / in the same way | 3 | 15 | 8 | 7 | Full verified coverage |
| `pt:como:1` | As / in a role | 3 | 5 | 4 | 1 | Full verified coverage |
| `pt:da:0` | Of / from the | 3 | 20 | 14 | 6 | Full verified coverage |
| `pt:de:0` | Verbs with de | 3 | 5 | 4 | 1 | Full verified coverage |
| `pt:de:1` | Adding a detail | 3 | 0 | 0 | 0 | Full verified coverage |
| `pt:dela:0` | Hers / of her | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:dele:0` | His / of him | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:do:0` | Of / from the | 3 | 20 | 15 | 5 | Full verified coverage |
| `pt:e:0` | And | 3 | 21 | 13 | 8 | Full verified coverage |
| `pt:ela:0` | she / it | 3 | 7 | 6 | 1 | Full verified coverage |
| `pt:ele:0` | he / it | 3 | 17 | 12 | 5 | Full verified coverage |
| `pt:ele:1` | After a preposition | 3 | 0 | 0 | 0 | Shortage reported |
| `pt:em:0` | Where | 3 | 18 | 13 | 5 | Full verified coverage |
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
| `pt:nos:0` | Us / to us | 3 | 1 | 1 | 0 | Full verified coverage |
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
| `pt:por:0` | Why | 3 | 1 | 1 | 0 | Shortage reported |
| `pt:por:1` | Through / along | 3 | 2 | 2 | 0 | Shortage reported |
| `pt:porque:0` | Because | 3 | 17 | 15 | 2 | Full verified coverage |
| `pt:quando:0` | When | 3 | 13 | 11 | 2 | Full verified coverage |
| `pt:que:0` | Saying what you think | 3 | 6 | 6 | 0 | Full verified coverage |
| `pt:que:1` | Adding information | 3 | 2 | 2 | 0 | Full verified coverage |
| `pt:que:2` | Comparing | 3 | 5 | 5 | 0 | Full verified coverage |
| `pt:se:0` | If | 3 | 1 | 1 | 0 | Full verified coverage |
| `pt:se:1` | Oneself / part of a verb | 3 | 0 | 0 | 0 | Full verified coverage |
| `pt:sem:0` | Without | 3 | 16 | 13 | 3 | Full verified coverage |
| `pt:sobre:0` | About | 3 | 7 | 6 | 1 | Full verified coverage |
| `pt:sobre:1` | On / above | 3 | 2 | 2 | 0 | Shortage reported |
| `pt:te:0` | You / to you | 3 | 14 | 8 | 6 | Full verified coverage |
| `pt:tudo:0` | Everything | 3 | 3 | 3 | 0 | Full verified coverage |
| `pt:um:0` | A / an | 3 | 20 | 12 | 8 | Full verified coverage |
| `pt:uma:0` | A / an | 3 | 16 | 11 | 5 | Full verified coverage |
| `pt:à:0` | To / at the | 3 | 18 | 15 | 3 | Full verified coverage |
