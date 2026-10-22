# Comparing attested-set and visible-back merging

22 October 2026. Read-only experiment against the current configured Spanish and
Portuguese Speech releases (10,000 surfaces each). No app rule, release, saved
progress, or deployment was changed.

## Recommendation

Between the two exact rules, prefer equality of the visible lexical sense sets
for these decks. Withdraw the earlier recommendation that every attested sense
should veto merging: published assignments include errors and the rare tail is
too sensitive to sparse sampling. This is a practical preference from a small
qualitative review, not a measured accuracy win against independent gold labels.

The more faithful longer-term rule is equality of reliably evidenced teaching
senses, independent of incidental display thresholds. That third rule was not
implemented or measured here. Explicit form/construction restrictions should
continue to protect a form even when the sample is small.

Neither observed-set rule establishes linguistic interchangeability, and neither
repairs wrong WSD assignments. In particular, the original havia example includes
incorrect sense assignments, not just an overly broad merge.

## Method

1. Read the release indexes identified by `app/config/config.json` and the matching
   shipped merge-exception overlays. Require matching release IDs.
2. Preserve current exclusions: ambiguous headwords, contractions, frozen
   expressions, and noun-menu protections. Only subdivide currently eligible
   lemma groups; never merge across headwords or re-admit an excluded surface.
3. **All attested:** positive-frequency lexical senses with positive published WSD
   counts, excluding unassigned senses. “Attested” here means assigned by the
   pipeline, not independently confirmed by a human. Unused dictionary senses
   and dictionary illustration sentences do not establish attestation.
4. **Visible back:** take the subset retained by the app's actual
   `finishCardMeanings` routine, including its low-share pooling, fallback and
   promotion rules. Compare standalone surface cards before sibling pooling.
5. Compare senses by `source_reference`, not surface-specific `sense_id`, English
   inflection or gloss spelling. All compared lexical senses had source references.
6. Within each existing group, partition forms by identical nonempty sets under
   each rule. Never merge empty evidence sets. Percentages need not match.

This isolates the lexical sense-selection layer. It is not a full browser replay:
it does not apply grammar-word overlays, final gloss rendering/grouping, cognate
filters, existing learner progress or companion-card expansion. Expressions are
separate teaching items and are excluded from the compared lexical sets; the
existing frozen-expression protections remain in force. Counts below are
hypothetical surface-card representatives, not promised live study-session totals.

The experiment uses the app's code directly, extracted from its marked pure
helper blocks. Release and display-code hashes are recorded in summary.json.
Full per-form records and pairwise disagreements are saved outside Git in
`../Fluency-Workspace/audits/attested-merge-comparison/2026-10-22/comparison.json`.
Reproduce from repository root with:

```sh
node scripts/audit_attested_merge_rules.cjs --original-eligibility
```

## Counts

| Rule | Portuguese representatives | Spanish representatives |
|---|---:|---:|
| Existing eligible-headword grouping | 6,871 | 7,729 |
| Equal visible lexical sense sets | 7,715 | 8,763 |
| Equal all-attested lexical sense sets | 7,922 | 9,043 |

The two rules are not nested. Full sets can match while visible sets differ,
because different usage shares move the same sense above/below the display bar.

| Pairwise comparison within existing eligible groups | Portuguese | Spanish |
|---|---:|---:|
| Pairs matching visible sets but not all-attested sets | 2,596 | 1,326 |
| Above pairs whose every distinguishing sense has just 1–2 assignments | 2,450 (94.4%) | 1,243 (93.7%) |
| Pairs matching all-attested sets but not visible sets | 1,557 | 544 |

Pairs are not independent observations: a large verb paradigm contributes many
pairs. “1–2 assignments” is evidence of fragility, not proof of a mistake.

If the intended policy instead vetoes the *whole original lemma group* whenever
any member differs, without retaining equal subsets, the all-attested / visible
totals are 8,935 / 8,826 for Portuguese and 9,674 / 9,571 for Spanish. That stricter
interpretation loses much more grouping. The recommendation concerns keeping
identical subsets together, rather than requiring an entire paradigm to match.

## Inspecting disagreements

Thirteen pairs were selected to illustrate both directions of disagreement,
frequent verbs, and the original haver case. This is a purposive sample, not a
random accuracy evaluation. Source rows, counts, contexts and up to two corpus
examples per sense are in reviewed-examples.json.

### Cases favouring visible-set equality

**Portuguese estou / estás.** The visible sets match. The full rule separates
them because estou has one assignment to “to look, to appear”. Its sentence is
“Eu estou ansioso para trabalhar com você” (“I look forward to working with
you”). The English translation contains “look”, but estou itself is copular
“am”. This is a likely sense-assignment error, not a form-exclusive meaning.

**Spanish necesito / necesita.** The main “to need; to require” sense has 30
and 29 assignments respectively. Necesita additionally has one assignment to
“to need; to be necessary”: “Ahora nos necesita más que nunca.” In context this
is the ordinary transitive “needs us”, not persuasive evidence of a distinct use
exclusive to necesita. The full rule splits an apparently duplicate teaching card.

**Spanish hacer / haciendo.** Visible lexical sets match. Haciendo has several
one-off senses, including “to take [time]” assigned to “Nada termina, sólo
estamos haciendo una pausa.” Here haciendo is “taking/making [a pause]”; this
does not substantiate the dictionary's time-duration sense. Another one-off,
“to be [weather]”, is attached to “Los días se están haciendo más largos”,
which is a change-of-state use. The full rule splits all 36 currently eligible
hacer forms into separate sets; visible equality retains some shared subsets.

### Cases showing that visible equality also has costs

**Portuguese sabe / sabia.** Both attest exactly the same three dictionary
senses: knowing how, being aware, and knowing a piece of information. Counts
are 6/17/7 versus 1/27/2. The latter back retains only the dominant sense, so
visible equality separates them. The stored example explicitly says “At five years old
he already knew how to ski.” There is positive evidence for the same use.

**Spanish creo / cree.** Both attest “believe” and “think”, but the counts are
1/29 and 18/12. The one believe example on creo is “No creo en el aborto.” It
does instantiate that belief use. The visible rule separates cards despite the
same underlying attested repertoire; the full rule merges them.

**Portuguese posso / podemos.** Posso alone has one assignment to “may/might”,
from “Posso ver a vista?” This is a permission question, overlapping the
separate permission sense rather than clearly instantiating epistemic
possibility. Rare distinctions can reflect overlapping dictionary categories
as well as outright errors. Neither counting every label nor trusting gloss
text alone resolves that issue.

### The original havia case

All five examples published as havia = “ago” were inspected:

| Sentence | What havia contributes |
|---|---|
| Eu sabia o que havia na outra sala. | what there was in the other room |
| Havia uma ponte aqui há muito tempo. | there was a bridge; separate há marks elapsed time |
| Há muitos anos, havia um castelo aqui. | there was a castle; separate há marks elapsed time |
| Não havia isto o ano passado. | this was not there last year |
| Não havia clientes, então fechamos cedo a loja. | there were no customers |

None of these five attests elapsed-time havia. This does not mean havia cannot
express elapsed time; it means these particular assignments do not prove it.

The all-attested rule actually groups havia with havemos: both have the same
four published lexical sense labels. Havemos has a single “ago” assignment on
“É uma pena, pois nunca havemos saber”, which does not express elapsed time.
Their visible sets differ, so the visible rule separates them.

Hei has two “ago” examples beginning “Hei” meaning “Hey”, and six existential
assignments also including interjection uses. These source/assignment errors
can exceed the rare-sense threshold too. Neither proposed rule alone ensures
correct cards.

## Practical decision

Use visible-set equality if choosing between these two now, while retaining
existing explicit exception protections. Do not claim that it discovers the
true meaning distribution or eliminates all duplicate cards. Avoid treating
one additional low-confidence assignment as a mandatory separation. A future
evidence-qualified rule should address both one-off false senses and valid
senses hidden by the display threshold; it needs a separate measured comparison.

Implementation follow-up: decision 0031 adopts the visible-set comparison.
The original eligibility overlays remain available for reproducing this audit.
Implementation validation also withdrew five stale Portuguese approvals, so its
final Portuguese grouping count is 7,719 rather than this experiment's 7,715.

Corpus examples are from the local releases, sourced from
[Tatoeba](https://tatoeba.org/) and [OpenSubtitles](http://www.opensubtitles.org/)
via OPUS. Individual Tatoeba URLs, when available, are retained in
reviewed-examples.json; original release files retain full provenance.
