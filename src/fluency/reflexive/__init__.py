"""Pronominal / reflexive tagging of one verb occurrence.

``policy(doc, span)`` in each language module answers whether the verb at
``span`` (character offsets) in a parsed sentence is used pronominally:

``NO_SE``    no reflexive clitic belongs to the verb: the pronominal family can go
``SE_FIRM``  a reflexive clitic belongs to it and agrees with its controller:
             the non-pronominal family can go
``BOTH``     undecidable (3rd-person *se* that may be passive or impersonal, or no
             controller recovered): keep both, WSD decides
``Z``        not a verb

Provider parity: SpanishDict files pronominal uses as separate headwords
(``hacer`` / ``hacerse``); Wiktionary files them as senses tagged
``pronominal`` or ``reflexive=true``. The tag is provider-neutral; the WSD
candidate policy applies it as a headword or a sense filter.

Precision when committing (NO_SE / SE_FIRM) is 99.4-100% on hand-labelled
subtitle sets and 99.6-99.7% on UD treebanks; the measurements and the
evaluation harness are in ``research/reflexives/``.

A language is added by creating ``fluency/reflexive/<name>.py`` with a
``policy`` function and listing its parser in ``PARSERS``.
"""

from __future__ import annotations

import importlib
from types import ModuleType

LABELS = ("NO_SE", "SE_FIRM", "BOTH", "Z")

# The parser each detector was measured with. A faster Spanish parser
# (es_core_news_lg) made 7 commit errors on the subtitle sets against 1.
PARSERS = {"es": "es_dep_news_trf", "pt": "pt_core_news_lg"}

_MODULES = {"es": "spanish", "pt": "portuguese"}


def detector(language: str) -> ModuleType:
    """The language's detector module. Importing it loads its paradigm table."""
    try:
        name = _MODULES[language]
    except KeyError:
        raise ValueError(f"no reflexive detector for {language!r}") from None
    return importlib.import_module(f"fluency.reflexive.{name}")
