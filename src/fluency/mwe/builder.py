"""Builder and overlay tools for MWE inventory snapshots.

Produces reproducible snapshots under `Fluency-Workspace/raw/mwe/` adhering to
the `mwe-merged/v1` contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Sequence

from fluency.mwe.policy import classify_mwe


_PROSE_FILTER = re.compile(
    r"^(used other than figuratively|alternative form|inflection of|plural of|see also|"
    r"used to (indicate|express|show|refer))",
    re.I,
)


def _clean_gloss(gloss: str, expression: str = "") -> str | None:
    text = re.sub(r"\(.*?\)", "", gloss or "").strip()
    if not text or _PROSE_FILTER.search(text):
        return None
    if expression:
        parts = [
            p.strip() for p in re.split(r"[;]", text)
            if p.strip() and p.strip().casefold() != expression.strip().casefold()
        ]
        text = "; ".join(parts)
    return text.strip() or None


def build_spanish_overlay(
    input_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Tag existing Spanish merged snapshot with the non-decomposition policy."""

    data = json.loads(input_path.read_text(encoding="utf-8"))
    raw_mwes = data.get("mwes", {})

    tagged_mwes: dict[str, Any] = {}
    sources_breakdown: dict[str, int] = {}
    total_candidates = len(raw_mwes)
    attested = 0
    unattested = 0
    kept = 0
    excluded_comp = 0

    for expr, row in raw_mwes.items():
        translations = list(row.get("translations", []))
        freq = int(row.get("corpus_freq", 0) or 0)
        sources = list(row.get("sources", []))

        src_key = "+".join(sorted(sources))
        sources_breakdown[src_key] = sources_breakdown.get(src_key, 0) + 1

        if freq > 0:
            attested += 1
        else:
            unattested += 1

        disposition = classify_mwe(
            expression=expr,
            translations=translations,
            language="es",
            corpus_freq=freq,
            sources=sources,
        )

        if disposition.verdict == "keep":
            kept += 1
        elif disposition.reason == "compositional":
            excluded_comp += 1

        entry = dict(row)
        entry["id"] = str(row.get("id") or f"mwe:{expr}")
        entry["verdict"] = disposition.verdict
        entry["reason"] = disposition.reason
        entry["status"] = disposition.status
        entry["non_compositional"] = disposition.non_compositional
        tagged_mwes[expr] = entry

    meta = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "language": "es",
        "contract": "mwe-merged/v1",
        "parent_snapshot": input_path.parent.name,
        "filter_policy": "v14_non_decomposition",
        "candidates": total_candidates,
        "attested": attested,
        "unattested": unattested,
        "kept_non_compositional": kept,
        "excluded_compositional": excluded_comp,
        "sources_breakdown": sources_breakdown,
        "note": (
            "tier 1 = corpus_freq > 0, can carry an example and be sense-assigned. "
            "tier 2 = corpus_freq 0, teachable content with no sentence to attach. "
            "Do not collapse them."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "mwes": tagged_mwes}
    output_path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    return meta


def build_wiktionary_inventory(
    language: str,
    wiktionary_path: Path,
    ledger_path: Path,
    prewsd_examples_path: Path,
    output_path: Path,
    *,
    max_examples_per_mwe: int = 6,
) -> dict[str, Any]:
    """Build a Wiktionary-route MWE snapshot for pt or cs."""

    lang = language.lower()
    ledger_data = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger_surfaces = set(ledger_data.get("surfaces", {}).keys())

    # 1. Collect candidates from Wiktionary
    raw_candidates: dict[str, dict[str, Any]] = {}

    with wiktionary_path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            word = row.get("word", "").strip()
            pos = row.get("pos", "")

            # Multiword headwords
            if " " in word and pos in {"phrase", "prep_phrase", "adv", "conj", "prep", "intj", "noun", "adj", "particle"}:
                tokens = word.split()
                if 2 <= len(tokens) <= 5:
                    cleaned_glosses: list[str] = []
                    for s in row.get("senses", []):
                        for g in s.get("glosses", []):
                            cleaned = _clean_gloss(g, word)
                            if cleaned and cleaned not in cleaned_glosses:
                                cleaned_glosses.append(cleaned)
                    if cleaned_glosses:
                        attach = [t.lower() for t in tokens if t.lower() in ledger_surfaces]
                        if attach:
                            raw_candidates[word.lower()] = {
                                "translations": cleaned_glosses[:3],
                                "sources": ["wiktionary"],
                                "attach_words": sorted(list(set(attach))),
                                "pos": pos,
                            }

            # Derived terms
            for d in row.get("derived", []):
                dw = d.get("word", "").strip()
                if " " in dw:
                    tokens = dw.split()
                    if 2 <= len(tokens) <= 5:
                        trans = _clean_gloss(d.get("english") or d.get("translation") or "", dw)
                        parent = word.lower()
                        attach = [parent] if parent in ledger_surfaces else []
                        attach += [t.lower() for t in tokens if t.lower() in ledger_surfaces and t.lower() not in attach]
                        if attach and (trans or dw.lower() in raw_candidates):
                            existing = raw_candidates.get(dw.lower(), {})
                            translations = list(existing.get("translations", []))
                            if trans and trans not in translations:
                                translations.append(trans)
                            raw_candidates[dw.lower()] = {
                                "translations": translations,
                                "sources": ["wiktionary"],
                                "attach_words": sorted(list(set(existing.get("attach_words", []) + attach))),
                                "pos": existing.get("pos", "derived"),
                            }

    # 2. Count frequency and collect examples from prewsd frozen examples
    examples_data = json.loads(prewsd_examples_path.read_text(encoding="utf-8"))
    targets = examples_data["columns"]["target"]
    translations = examples_data["columns"]["translation"]

    counts: dict[str, int] = {k: 0 for k in raw_candidates}
    examples: dict[str, list[dict[str, Any]]] = {k: [] for k in raw_candidates}

    word_re = re.compile(r"\b[\w'-]+\b")
    for i, target_text in enumerate(targets):
        tokens = word_re.findall(target_text.lower())
        num_toks = len(tokens)
        seen_in_sentence: set[str] = set()
        for n in (2, 3, 4, 5):
            for j in range(num_toks - n + 1):
                ngram = " ".join(tokens[j:j+n])
                if ngram in raw_candidates and ngram not in seen_in_sentence:
                    seen_in_sentence.add(ngram)
                    counts[ngram] += 1
                    if len(examples[ngram]) < max_examples_per_mwe:
                        examples[ngram].append({
                            lang: target_text,
                            "en": translations[i],
                            "line": i,
                        })

    # 3. Classify with non-decomposition policy
    tagged_mwes: dict[str, Any] = {}
    attested = 0
    unattested = 0
    kept = 0
    excluded_comp = 0

    for expr, cand in raw_candidates.items():
        trans_list = cand["translations"]
        if not trans_list:
            continue
        freq = counts.get(expr, 0)
        if freq > 0:
            attested += 1
        else:
            unattested += 1

        disposition = classify_mwe(
            expression=expr,
            translations=trans_list,
            language=lang,
            corpus_freq=freq,
            sources=["wiktionary"],
        )

        if disposition.verdict == "keep":
            kept += 1
        elif disposition.reason == "compositional":
            excluded_comp += 1

        tagged_mwes[expr] = {
            "id": f"mwe:{expr}",
            "expression": expr,
            "translations": trans_list,
            "sources": ["wiktionary"],
            "attach_words": cand["attach_words"],
            "corpus_freq": freq,
            "verdict": disposition.verdict,
            "reason": disposition.reason,
            "status": disposition.status,
            "non_compositional": disposition.non_compositional,
            "examples": examples.get(expr, []),
        }

    meta = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "language": lang,
        "contract": "mwe-merged/v1",
        "wiktionary_snapshot": wiktionary_path.parent.name,
        "prewsd_freeze": prewsd_examples_path.parent.name,
        "filter_policy": "v14_non_decomposition",
        "candidates": len(tagged_mwes),
        "attested": attested,
        "unattested": unattested,
        "kept_non_compositional": kept,
        "excluded_compositional": excluded_comp,
        "sources_breakdown": {"wiktionary": len(tagged_mwes)},
        "note": (
            "tier 1 = corpus_freq > 0, can carry an example and be sense-assigned. "
            "tier 2 = corpus_freq 0, teachable content with no sentence to attach. "
            "Do not collapse them."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "mwes": tagged_mwes}
    output_path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    return meta


def retag_snapshot(
    input_path: Path,
    output_path: Path,
    language: str,
    *,
    filter_policy: str = "v14_wiktionary_source_and_pos",
    audit: str = "sieve",
    wiktionary_dump_path: Path | None = None,
) -> dict[str, Any]:
    """Re-fold verdicts on an existing snapshot. Does not rewrite the parent file."""

    data = json.loads(input_path.read_text(encoding="utf-8"))
    raw_mwes = data.get("mwes", {})
    parent_meta = data.get("meta") or {}
    lang = language.lower()

    # Load Wiktionary headword POS mapping if dump provided
    wikt_heads: dict[str, list[str]] = {}
    if wiktionary_dump_path and wiktionary_dump_path.is_file():
        with wiktionary_dump_path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                w = row.get("word", "").strip().lower()
                if " " in w:
                    pos = row.get("pos")
                    if pos:
                        wikt_heads.setdefault(w, []).append(pos)

    tagged_mwes: dict[str, Any] = {}
    attested = 0
    unattested = 0
    kept = 0
    excluded_comp = 0
    excluded_sd_collocation = 0
    excluded_noun_compound = 0
    flipped_to_exclude = 0
    flipped_to_keep = 0

    for expr, row in raw_mwes.items():
        translations = list(row.get("translations", []))
        freq = int(row.get("corpus_freq", 0) or 0)
        sources = list(row.get("sources", []))
        if freq > 0:
            attested += 1
        else:
            unattested += 1

        in_wikt = ("wiktionary" in sources) or (expr in wikt_heads)
        poses = wikt_heads.get(expr) or row.get("pos")

        disposition = classify_mwe(
            expression=expr,
            translations=translations,
            language=lang,
            corpus_freq=freq,
            sources=sources,
            pos=poses,
            in_wiktionary=in_wikt,
        )
        if disposition.verdict == "keep":
            kept += 1
        elif disposition.reason == "compositional":
            excluded_comp += 1
            if not in_wikt:
                excluded_sd_collocation += 1
            else:
                excluded_noun_compound += 1

        old_verdict = row.get("verdict")
        if old_verdict == "keep" and disposition.verdict == "exclude":
            flipped_to_exclude += 1
        elif old_verdict == "exclude" and disposition.verdict == "keep":
            flipped_to_keep += 1

        entry = dict(row)
        entry["id"] = str(row.get("id") or f"mwe:{expr}")
        if poses:
            entry["pos"] = poses if isinstance(poses, list) else [poses]
        entry["verdict"] = disposition.verdict
        entry["reason"] = disposition.reason
        entry["status"] = disposition.status
        entry["non_compositional"] = disposition.non_compositional
        tagged_mwes[expr] = entry

    meta = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "language": lang,
        "contract": "mwe-merged/v1",
        "parent_snapshot": input_path.parent.name,
        "filter_policy": filter_policy,
        "audit": audit,
        "candidates": len(tagged_mwes),
        "attested": attested,
        "unattested": unattested,
        "kept_non_compositional": kept,
        "excluded_compositional": excluded_comp,
        "excluded_sd_collocation": excluded_sd_collocation,
        "excluded_noun_compound": excluded_noun_compound,
        "flipped_keep_to_exclude": flipped_to_exclude,
        "flipped_exclude_to_keep": flipped_to_keep,
        "sources_breakdown": parent_meta.get("sources_breakdown"),
        "prewsd_freeze": parent_meta.get("prewsd_freeze"),
        "wiktionary_snapshot": (
            wiktionary_dump_path.parent.name if wiktionary_dump_path
            else parent_meta.get("wiktionary_snapshot")
        ),
        "filter_description": (
            "1. Candidate source rule: Multiword expressions must appear in Wiktionary "
            "(SpanishDict collocations without Wiktionary backing are excluded as compositional). "
            "2. Part-of-speech rule: Within Wiktionary, noun compounds (only POS is noun) "
            "are excluded as compositional; non-noun locutions with corpus_freq > 0 are kept."
        ),
        "note": (
            "SIEVE retag of the FUSE snapshot. Keys are unchanged; verdicts are "
            "re-folded. tier 1 = corpus_freq > 0; tier 2 = corpus_freq 0. "
            "Do not collapse them."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "mwes": tagged_mwes}
    output_path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    return meta

