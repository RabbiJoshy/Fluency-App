"""Lyrics WSD adapter retiring the duplicate scoring loop in scripts/plant_artist_v20.py.

Runs ClosedMenuWSDRunner under the unified fluency.wsd engine, using profiles that
extend the speech baseline (es-v23-1) with lyrics lookup scope and margin confidence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import datetime, UTC
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import numpy as np

from fluency.nlp.embeddings import load_cache
from fluency.nlp.models import pin
from fluency.nlp.pos import load_pinned
from fluency.speech.wsd_execute import (
    ExactTextGlossScorer,
    SpanishV5CandidatePolicy,
    model_profile,
    build_analyses,
)
from fluency.wsd.candidate_policy import CandidatePolicy
import hashlib
from fluency.core.identity import build_card_id
from fluency.wsd.contracts import _CARD_ID, WSDAssignment
from fluency.wsd.languages.spanish import SpanishWSDAdapter
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.wsd.multiword import MultiwordEntry, index_multiword_senses
from fluency.wsd.runner import (
    ClosedMenuWSDRunner,
    WSDComponents,
    WSDExecutionProfile,
    WSDRequest,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE = REPO_ROOT.parent / "Fluency-Workspace"


class LyricsWSDAdapter:
    """Adapts ClosedMenuWSDRunner to the lyrics data model and contract."""

    def __init__(
        self,
        profile_id: str = "es-lyrics-v23-1",
        *,
        workspace: Path = WORKSPACE,
        vectors: dict[str, Any] | None = None,
        nlp: Any | None = None,
    ) -> None:
        self.profile_id = profile_id
        self.workspace = workspace
        self.profile_config = model_profile(profile_id)
        if not self.profile_config:
            raise ValueError(f"unknown or empty WSD profile: {profile_id}")

        self.wsd_cfg = self.profile_config.get("wsd") or self.profile_config

        # 1. POS Tagger
        occ_pos = self.wsd_cfg.get("occurrence_pos")
        pos_pin = None
        if isinstance(occ_pos, dict):
            pos_pin = occ_pos.get("model_revision")
        elif isinstance(occ_pos, str):
            if "@" in occ_pos:
                pos_pin = occ_pos
            else:
                pos_pin = pin(occ_pos)
        if not pos_pin:
            pos_pin = pin("occurrence-pos")
        self.nlp = nlp or load_pinned(pos_pin)

        # 2. Embedding vectors
        cache_rel = self.wsd_cfg.get("embedding_cache", "embeddings/es/exact-text-gemini-embedding-001.npz")
        cache_path = self.workspace / cache_rel
        if vectors is not None:
            self.vectors = vectors
        elif cache_path.is_file():
            self.vectors = load_cache(cache_path)
        else:
            self.vectors = {}

        # 3. Multiword index
        mw_cfg = self.profile_config.get("multiword") or {}
        self.multiword_index = None
        self.multiword_content_id = None
        if mw_cfg.get("enabled"):
            snapshot_rel = mw_cfg.get("snapshot_path")
            if snapshot_rel:
                snap_path = REPO_ROOT / snapshot_rel
                if not snap_path.is_file():
                    snap_path = self.workspace / snapshot_rel
                if snap_path.is_file():
                    try:
                        mw_data = json.loads(snap_path.read_text(encoding="utf-8"))
                        self.multiword_index, self.multiword_content_id = index_multiword_senses(mw_data)
                    except Exception:
                        pass

        # 4. Shared runner components
        language_adapter = SpanishWSDAdapter()
        prior_cfg = self.profile_config.get("provider_prior") or {}
        menu_prior = float(prior_cfg.get("weight", 0.02)) if prior_cfg.get("enabled", True) else 0.0
        menu_prior_decay = float(prior_cfg.get("decay", 0.5))

        self.components = WSDComponents(
            language=language_adapter,
            gloss=ExactTextGlossScorer(self.vectors, target_locale=""),
            candidate_policy=SpanishV5CandidatePolicy(
                language="es",
                constraint_mode="filter",
                menu_prior=menu_prior,
                menu_prior_decay=menu_prior_decay,
                clitic_gate=True,
                pronominal_gate=True,
                domain_penalty=0.04,
            ),
            multiword_index=self.multiword_index,
            multiword_inventory_content_id=self.multiword_content_id,
        )

        commit_cfg = self.profile_config.get("commit") or {}
        from fluency.wsd.commit import CommitPolicy
        commit_strategy = commit_cfg.get("strategy", "margin")
        if commit_strategy not in {"margin", "rank_agreement"}:
            commit_strategy = "margin"
        commit_policy = CommitPolicy(
            strategy=commit_strategy,
            unresolved_outcome=commit_cfg.get("unresolved_outcome", "abstain"),
            phrase_winner_skips_provider_order=commit_cfg.get("phrase_winner_skips_provider_order", True),
            unresolved_falls_back_to_phrase=commit_cfg.get("unresolved_falls_back_to_phrase", True),
        )

        from fluency.wsd.disposition import DispositionPolicy
        self.execution_profile = WSDExecutionProfile(
            token_tuple_vote=False,
            tuple_vote_minimum_margin=0.0,
            calibration=False,
            alignment=False,
            generative_escalation=False,
            disposition=DispositionPolicy(minimum_confidence=0.0, weak="abstain"),
            candidate_preparation=True,
            multiword_candidates=bool(self.multiword_index),
            commit=commit_policy,
            active_projection=mw_cfg.get("active_projection", "mwe_augmented"),
        )
        self.runner = ClosedMenuWSDRunner(self.execution_profile, self.components)

    def _convert_card_senses_to_analyses(
        self,
        card_id: str,
        surface: str,
        senses: list[dict[str, Any]],
    ) -> tuple[MenuAnalysis, ...]:
        """Convert flat list of lyrics senses into structured MenuAnalysis records."""
        by_headword_pos: dict[tuple[str, str], list[dict[str, Any]]] = {}
        order: list[tuple[str, str]] = []
        for s in senses:
            key = (s.get("headword", surface), str(s.get("pos", "NOUN")).upper())
            if key not in by_headword_pos:
                order.append(key)
                by_headword_pos[key] = []
            by_headword_pos[key].append(s)

        analyses: list[MenuAnalysis] = []
        for headword, pos in order:
            sense_list = by_headword_pos[(headword, pos)]
            source_adapter = sense_list[0].get("source") or "spanishdict"
            analysis_id = build_analysis_id(
                card_id=card_id,
                source_adapter=source_adapter,
                source_analysis_key=f"{headword}_{pos}",
            )
            leaves = tuple(
                SenseLeaf(
                    sense_id=s["sense_id"],
                    translation=s.get("translation") or "",
                    definition=s.get("context") or "",
                    source_reference=s.get("source") or "spanishdict",
                    provider_metadata={
                        "headword": headword,
                        "pos": pos,
                        "gloss_base": s.get("gloss_base") or s.get("translation") or "",
                    },
                )
                for s in sense_list
            )
            analyses.append(
                MenuAnalysis(
                    menu_analysis_id=analysis_id,
                    card_id=card_id,
                    surface_form=surface,
                    headword=headword,
                    part_of_speech=pos,
                    source_adapter=source_adapter,
                    source_analysis_key=f"{headword}_{pos}",
                    senses=leaves,
                    provider_metadata={},
                )
            )
        return tuple(analyses)

    def assign_examples_for_card(
        self,
        card: dict[str, Any],
        senses: list[dict[str, Any]],
        examples: list[dict[str, Any]],
        *,
        doc_cache: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Disambiguate examples for a single resolved lyrics card."""
        cid = card.get("card_id") or card.get("id") or ""
        word = card.get("word") or card.get("display_form") or ""
        if not cid or _CARD_ID.fullmatch(cid) is None:
            cid = build_card_id("es", word.strip() or "palabra")
        doc_cache = doc_cache if doc_cache is not None else {}
        run_ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")

        sense_buckets: list[list[dict[str, Any]]] = [[] for _ in senses]
        sense_confidences: list[list[float]] = [[] for _ in senses]
        card_decisions: list[dict[str, Any]] = []
        stats: Counter[str] = Counter()

        if len(senses) == 1:
            sense = senses[0]
            for ex_idx, ex in enumerate(examples):
                sense_buckets[0].append({
                    **ex,
                    "assignment_method": self.profile_id,
                    "prompt_id": "lyrics-v23-monosemous-deterministic",
                    "run_ts": run_ts,
                    "confidence": 1.0,
                    "band": "high",
                })
                sense_confidences[0].append(1.0)
                card_decisions.append({
                    "decision_id": f"decision_{cid}_{ex_idx}",
                    "forced_selection": {
                        "selected_tuple": {"headword": sense["headword"], "part_of_speech": sense["pos"]},
                        "sense_id": sense["sense_id"],
                    },
                    "provenance": {
                        "assignment_method": self.profile_id,
                        "prompt_id": "lyrics-v23-monosemous-deterministic",
                        "run_ts": run_ts,
                    },
                    "subject": {"bucket_index": 0, "example_index": ex_idx, "kind": "materialized_example"},
                })
            return {
                "sense_buckets": sense_buckets,
                "sense_confidences": sense_confidences,
                "card_decisions": card_decisions,
                "stats": stats,
            }

        analyses = self._convert_card_senses_to_analyses(cid, word, senses)
        sense_id_to_index = {s["sense_id"]: idx for idx, s in enumerate(senses)}

        for ex_idx, ex in enumerate(examples):
            stext = ex.get("spanish", "").strip()
            if not stext:
                continue
            if stext not in doc_cache:
                doc_cache[stext] = self.nlp(stext)
            doc = doc_cache[stext]

            # Locate observed POS for target word
            observed_pos = None
            observed_grammar = {}
            target_span = None
            target_observed_form = None
            w_bare = word.casefold().replace("'", "").strip()
            for tok in doc:
                t_bare = tok.text.casefold().replace("'", "").strip()
                if t_bare == w_bare or (len(t_bare) > 2 and len(w_bare) > 2 and t_bare.rstrip("s") == w_bare.rstrip("s")):
                    observed_pos = tok.pos_
                    if tok.morph:
                        observed_grammar = tok.morph.to_dict()
                    target_span = (tok.idx, tok.idx + len(tok.text))
                    target_observed_form = tok.text
                    break

            stats["pos_observed"] += observed_pos is not None

            sid_hash = hashlib.sha256(f"{cid}:{ex_idx}:{stext}".encode("utf-8")).hexdigest()[:32]
            sentence_id = f"sentence_{sid_hash}"
            req = WSDRequest(
                card_id=cid,
                surface_form=word,
                sentence_id=sentence_id,
                sentence=stext,
                target_span=target_span,
                target_observed_form=target_observed_form,
                translation=ex.get("english", ""),
                sense_menu_content_id="sha256:" + "0" * 64,
                analyses=analyses,
                observed_pos=observed_pos,
                observed_pos_evidence={"observed_grammar": observed_grammar} if observed_grammar else None,
            )

            assignment = self.runner.assign(req)
            selected_sense_id = assignment.selected_sense_id

            best_idx = sense_id_to_index.get(selected_sense_id, 0)
            conf = assignment.confidence if assignment.confidence is not None else 0.85
            margin = (assignment.evidence.get("commit", {}).get("raw_axis_margins", {}).get("leaf", 0.05))

            band = "high" if margin >= 0.02 else ("medium" if margin >= 0.01 else "low")
            chosen = senses[best_idx]
            provenance = {
                "assignment_method": self.profile_id,
                "prompt_id": "lyrics-v23-unified-runner",
                "run_ts": run_ts,
                "margin": margin,
                "features_scored": assignment.evidence.get("features_scored", []),
                "features_abstained": assignment.evidence.get("features_abstained", []),
                "translation_state": assignment.evidence.get("translation_state", "absent"),
            }

            sense_buckets[best_idx].append({
                **ex,
                "assignment_method": self.profile_id,
                "prompt_id": "lyrics-v23-unified-runner",
                "run_ts": run_ts,
                "confidence": conf,
                "band": band,
                "margin": margin,
            })
            sense_confidences[best_idx].append(conf)

            card_decisions.append({
                "decision_id": f"decision_{cid}_{ex_idx}",
                "forced_selection": {
                    "selected_tuple": {"headword": chosen["headword"], "part_of_speech": chosen["pos"]},
                    "sense_id": chosen["sense_id"],
                },
                "provenance": provenance,
                "subject": {
                    "bucket_index": best_idx,
                    "example_index": len(sense_buckets[best_idx]) - 1,
                    "kind": "materialized_example",
                },
            })

        return {
            "sense_buckets": sense_buckets,
            "sense_confidences": sense_confidences,
            "card_decisions": card_decisions,
            "stats": stats,
        }
