"""Extract provider-neutral features from SpanishDict senses.

The companion note is the reason this exists. SpanishDict records it as prose
inside ``context`` -- ``to remove; used with "de"`` -- while Wiktionary records
the same fact as a structured ``+obj`` template. Same concept, two encodings, so
it belongs behind an adapter rather than being read as a feature of either
provider.

Measured: 587 SpanishDict senses carry one (de 149, con 132, a 127, en 72,
por 40), against 632 in Portuguese Wiktionary (de 126, em 119, com 91, a 87).
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from fluency.features.contract import GRAMMATICAL_FORMS, SpecialistFeature


# SpanishDict's ``context`` is deliberately overloaded: it may be a semantic
# gloss (``to possess``), a domain, a grammatical mark, or a usage frame.  The
# adapter partitions those cases rather than pretending every context is one
# kind of metadata.
USED_WITH = re.compile(
    r"\b(?P<soft>can be|commonly|frequently|generally|may be|normally|often|"
    r"sometimes|typically|usually)?\s*used with\s+(?P<tail>.+)$",
    re.IGNORECASE,
)
QUOTED_TERM = re.compile(r'["“](?P<term>[^"”]+)["”]')
FUNCTIONAL = re.compile(r"^used to\b", re.IGNORECASE)
CONSTRUCTION = re.compile(
    r"^(?:followed by|takes?|used after|used before|used in|used with)\b",
    re.IGNORECASE,
)
GRAMMATICAL_WITH = re.compile(
    r"^with\s+(?:an?\s+|the\s+)?(?:adjectives?|clauses?|conditional clauses|"
    r"dates?|direct objects?|gerunds?|indirect objects?|indirect questions|"
    r"infinitives?|negatives?|nouns?|numbers?|participles?|passive voice|"
    r"plural|pronouns?|quantities|singular|subjunctive|verbs?)\b",
    re.IGNORECASE,
)
DOMAIN_LABELS = frozenset(
    {
        "anatomy", "architecture", "art", "aviation", "biology", "botany",
        "business", "chemistry", "computing", "culinary", "economics",
        "education", "finance", "football", "geography", "grammar", "law",
        "legal", "linguistics", "medicine", "military", "music", "nautical",
        "physics", "politics", "religion", "religious", "science", "sports",
        "technology", "theater", "zoology",
    }
)
REGISTER_LABELS = frozenset(
    {
        "archaic", "colloquial", "dated", "euphemistic", "formal", "informal",
        "obsolete", "offensive", "poetic", "slang", "vulgar",
    }
)
GRAMMAR_PATTERNS = (
    (re.compile(r"\bfirst person\b", re.I), "person=1"),
    (re.compile(r"\bsecond person\b", re.I), "person=2"),
    (re.compile(r"\bthird person\b", re.I), "person=3"),
    (re.compile(r"\bsingular\b", re.I), "number=singular"),
    (re.compile(r"\bplural\b", re.I), "number=plural"),
    (re.compile(r"\bimperative\b", re.I), "mood=imperative"),
    (re.compile(r"\bindicative\b", re.I), "mood=indicative"),
    (re.compile(r"\bsubjunctive\b", re.I), "mood=subjunctive"),
    (re.compile(r"\bconditional\b", re.I), "mood=conditional"),
    (re.compile(r"\bpreterite\b", re.I), "tense=preterite"),
    (re.compile(r"\bimperfect\b", re.I), "tense=imperfect"),
    (re.compile(r"\bfuture\b", re.I), "tense=future"),
    (re.compile(r"\bpast participle\b", re.I), "form=participle"),
    (re.compile(r"\bgerund\b", re.I), "form=gerund"),
    (re.compile(r"\binfinitive\b", re.I), "form=infinitive"),
    (re.compile(r"\breflexive\b", re.I), "reflexive=true"),
    (re.compile(r"\bpassive voice\b", re.I), "voice=passive"),
    (re.compile(r"\bdirect object\b", re.I), "function=direct-object"),
    (re.compile(r"\bindirect object\b", re.I), "function=indirect-object"),
)
EXACT_GRAMMAR = {
    "demonstrative": "function=demonstrative",
    "feminine demonstrative": "function=demonstrative",
    "indeterminate": "definiteness=indefinite",
    "interrogative": "function=interrogative",
    "personal": "pronoun-class=personal",
    "possessive": "possessive=true",
    "relative": "function=relative",
    "subject": "function=subject",
}


def _clauses(context: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in re.split(r"[;|]", context) if part.strip())


def _grammar_features(clause: str) -> tuple[SpecialistFeature, ...]:
    lowered = clause.casefold().strip(" .;:()[]")
    features: list[SpecialistFeature] = []
    exact = EXACT_GRAMMAR.get(lowered)
    if exact:
        features.append(SpecialistFeature("grammar", "sense_mark", exact, clause))
    # These two labels carry gender as well as demonstrative function.
    if lowered == "feminine demonstrative":
        features.append(SpecialistFeature("grammar", "sense_mark", "gender=feminine", clause))
    for pattern, value in GRAMMAR_PATTERNS:
        if pattern.search(clause):
            features.append(SpecialistFeature("grammar", "sense_mark", value, clause))
    return tuple(dict.fromkeys(features))



def extract(sense: Mapping[str, Any]) -> tuple[SpecialistFeature, ...]:
    """Return typed features for one SpanishDict sense."""

    features: list[SpecialistFeature] = []
    context = sense.get("context")
    if isinstance(context, str) and context.strip():
        for clause in _clauses(context):
            lowered = clause.casefold().strip(" .;:()[]")
            if lowered in DOMAIN_LABELS:
                features.append(SpecialistFeature("domain", "domain_label", lowered, clause))
                continue
            if lowered in REGISTER_LABELS:
                features.append(SpecialistFeature("register", "usage_label", lowered, clause))
                continue

            used_with = USED_WITH.search(clause)
            if used_with:
                usage_text = used_with.group(0).strip()
                if used_with.group("soft"):
                    features.append(
                        SpecialistFeature("construction", "optional_companion", usage_text, usage_text)
                    )
                    continue
                quoted = [
                    match.group("term").strip().casefold()
                    for match in QUOTED_TERM.finditer(used_with.group("tail"))
                    if match.group("term").strip()
                ]
                # Quotation is provider evidence that ``a`` is the Spanish
                # preposition, not the English article in "an infinitive".
                if quoted and all(" " not in value for value in quoted):
                    features.extend(
                        SpecialistFeature("companion", "required_word", value, usage_text)
                        for value in quoted
                    )
                    continue
                unquoted = used_with.group("tail").strip(' .,:[]()"“”').split()[0].casefold()
                if unquoted and unquoted not in GRAMMATICAL_FORMS:
                    features.append(
                        SpecialistFeature("companion", "required_word", unquoted, usage_text)
                    )
                else:
                    features.append(
                        SpecialistFeature("construction", "companion_form", usage_text, usage_text)
                    )
                continue

            if FUNCTIONAL.match(clause):
                features.append(SpecialistFeature("functional", "usage_note", clause, clause))
                continue
            grammar = _grammar_features(clause)
            if grammar:
                features.extend(grammar)
                continue
            if lowered == "impersonal use":
                features.append(SpecialistFeature("construction", "grammar_tag", "impersonal", clause))
                continue
            if CONSTRUCTION.match(clause) or GRAMMATICAL_WITH.match(clause):
                features.append(SpecialistFeature("construction", "usage_note", clause, clause))

    for region in sense.get("regions", []) or []:
        if isinstance(region, Mapping):
            region = region.get("name") or region.get("label") or region.get("region")
        if isinstance(region, str) and region.strip():
            features.append(
                SpecialistFeature("register", "region", region.strip(), region.strip())
            )
    return tuple(dict.fromkeys(features))
