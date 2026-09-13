"""Execute the immutable sentence-harvest stage for one planned run."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from fluency.core.canonical_json import canonical_json
from fluency.core.hashing import canonical_content_id, file_content_id
from fluency.core.manifests import StageManifest, build_stage_cache_key
from fluency.core.workspace import Workspace
from fluency.pipeline.budget import (
    display_examples_for_rank,
    execution_cap_per_card,
    wsd_budget_for_rank,
    wsd_budget_per_card,
)
from fluency.harvest.config import load_harvest_policies
from fluency.harvest.inventory import load_frequency_ranks, load_harvest_inventory
from fluency.harvest.matching import (
    detect_variety,
    SurfaceMatcher,
    easiness_metrics,
    example_identity,
    quality_rejection,
)
from fluency.harvest.pooling import (
    DEFAULT_POOL_MULTIPLIER,
    POOLING_POLICY_VERSION,
    SourcePool,
    pool_key,
    deaccented_index,
    quality_penalty,
    phrase_set,
    redundancy_penalty,
    systematic_sample,
    token_set,
)
from fluency.harvest.records import HarvestRecordError, validate_parallel_sentence
from fluency.harvest.sources import (
    CorpusAdapter,
    OpenSubtitlesAdapter,
    RetainedSentenceBankAdapter,
    TatoebaAdapter,
)
from fluency.pipeline.planning import load_pipeline_profile
from fluency.core.io import atomic_write, json_bytes


STAGE_VERSION = "sentence-harvest/v1"
CANDIDATES_VERSION = "harvest-candidates/v1"
REPORT_VERSION = "harvest-report/v1"
STAGE_RELATIVE = Path("stages/03_sentence_harvest")
_HARVEST_OUTPUT_KEYS = {
    "candidates": "candidates.json",
    "report": "report.json",
    "sentence_bank": "sentence-bank.jsonl",
}
_HARVEST_OUTPUT_FILES = tuple(_HARVEST_OUTPUT_KEYS.values())
INVENTORY_RELATIVE = Path("stages/01_inventory/output/inventory.json")
FREQUENCY_RELATIVE = Path("stages/01_inventory/output/frequency-ranks.json")


class HarvestRunError(ValueError):
    """Raised when a run cannot be harvested without ambiguity or fallback."""


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HarvestRunError(f"required run artifact does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise HarvestRunError(f"run artifact is not valid JSON: {path}") from error
    if not isinstance(value, dict):
        raise HarvestRunError(f"run artifact must contain an object: {path}")
    return value


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _implementation_content_id() -> str:
    package = Path(__file__).resolve().parent
    paths = (
        Path(__file__).resolve(),
        package / "matching.py",
        package / "records.py",
        package / "sources" / "opensubtitles.py",
        package / "sources" / "retained.py",
        package / "sources" / "tatoeba.py",
    )
    return canonical_content_id(
        {str(path.relative_to(package)): file_content_id(path) for path in paths}
    )


def _source_quotas(
    available: dict[str, int], card_cap: int, source_share: dict[str, float]
) -> dict[str, int]:
    """How many slots each source may fill on one card.

    Ordering the whole pool by source first meant the preferred source filled
    every budget and the other was trimmed away before selection ever saw it --
    a Czech pool came out 99% Tatoeba. Which source a learner should be shown is
    a selection decision that can be retuned forever; which sources survive the
    harvest is not, because recovering one means harvesting again.
    """

    if not available:
        return {}
    quotas: dict[str, int] = {}
    for source, count in available.items():
        share = source_share.get(source, 1.0 / len(available))
        quotas[source] = min(count, int(card_cap * share))
    # Whatever a thin source could not fill goes to the others, so a reserved
    # share never wastes budget on a source that has nothing to give.
    spare = card_cap - sum(quotas.values())
    while spare > 0:
        grew = False
        for source, count in available.items():
            if spare <= 0:
                break
            if quotas[source] < count:
                quotas[source] += 1
                spare -= 1
                grew = True
        if not grew:
            break
    return quotas


def _sample_without_repeats(
    shortlist: list[tuple[str, dict[str, Any]]], quota: int
) -> list[tuple[str, dict[str, Any]]]:
    """Spread the pick across the shortlist, skipping near-repeats.

    Tatoeba contributors write agreement families on purpose, so a card can
    receive one sentence several times over -- three of `nada`'s five best
    examples were "Yo no tengo nada que ver con esto/eso/en eso". A repeat is
    swapped for the next unused entry rather than rejected outright, so a card
    with nothing else still fills its budget.
    """

    chosen: list[tuple[str, dict[str, Any]]] = []
    signatures: list[frozenset[str]] = []
    phrases: list[frozenset[tuple[str, ...]]] = []
    used: set[str] = set()

    def admit(identity: str, item: dict[str, Any]) -> bool:
        signature = token_set(item["text"])
        phrase = phrase_set(item["text"])
        if redundancy_penalty(
            signature, signatures, subject_phrases=phrase, other_phrases=phrases
        ):
            return False
        chosen.append((identity, item))
        signatures.append(signature)
        phrases.append(phrase)
        return True

    for identity, item in systematic_sample(shortlist, quota):
        used.add(identity)
        admit(identity, item)
    # A card that lost picks to repeats backfills from the rest of its
    # shortlist rather than publishing short.
    for identity, item in shortlist:
        if len(chosen) >= quota:
            break
        if identity in used:
            continue
        used.add(identity)
        admit(identity, item)
    return chosen


def _reusable_harvest(workspace, run_directory: Path, cache_key: str) -> Path | None:
    """A finished harvest elsewhere in the workspace with this exact cache key.

    The key already covers implementation, config and every input content id, so
    an equal key means an equal output -- that is what content addressing is
    for. It was computed and recorded on every stage from the start and then
    never read, which left the pipeline rescanning millions of subtitle lines to
    reproduce a file it already had.
    """

    runs = workspace.root / "runs"
    if not runs.is_dir():
        return None
    for manifest_path in sorted(runs.glob(f"*/*/*/{STAGE_RELATIVE}/output/manifest.json")):
        if manifest_path.is_relative_to(run_directory):
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("status") != "complete" or manifest.get("cache_key") != cache_key:
            continue
        source = manifest_path.parent
        if all((source / name).is_file() for name in _HARVEST_OUTPUT_FILES):
            return source
    return None


def _reuse_harvest_output(
    source: Path,
    *,
    run_id: str,
    output_directory: Path,
    started_at: datetime,
    cache_key: str,
    implementation_content_id: str,
    config_content_id: str,
    inputs: dict[str, str],
) -> Path:
    """Copy a finished harvest into this run, recording that it was reused.

    The manifest says `reused_from` rather than presenting the work as freshly
    done: a run must not record what it did not verify, and it did not scan the
    corpus. The output content ids are recomputed from the copied bytes rather
    than trusted from the source manifest, so a corrupted copy cannot pass
    itself off as the original.
    """

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_directory.with_name(output_directory.name + ".partial")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    for name in _HARVEST_OUTPUT_FILES:
        shutil.copyfile(source / name, temporary / name)
    # candidates.json and report.json name the run that produced them. Copied
    # verbatim they claim the source run, and every later stage that checks the
    # bundle against the run then refuses it -- which is exactly what the WSD
    # importer did. The harvested content is identical; the label is not, so the
    # label is rewritten and the content ids below are recomputed from the copy.
    for name in ("candidates.json", "report.json"):
        target = temporary / name
        payload = json.loads(target.read_text(encoding="utf-8"))
        if payload.get("run_id") is not None:
            payload["run_id"] = run_id
            target.write_bytes(json_bytes(payload))

    outputs = {
        key: file_content_id(temporary / name)
        for key, name in _HARVEST_OUTPUT_KEYS.items()
    }
    stage = StageManifest(
        stage_name="sentence_harvest",
        stage_version=STAGE_VERSION,
        cache_key=cache_key,
        implementation_hash=implementation_content_id,
        config_hash=config_content_id,
        status="complete",
        started_at=_timestamp(started_at),
        inputs=inputs,
        model_revisions={},
        random_seed=0,
        outputs=outputs,
        completed_at=_timestamp(datetime.now(UTC)),
    )
    payload = stage.to_dict()
    payload["reused_from"] = str(source)
    (temporary / "manifest.json").write_bytes(json_bytes(payload))
    temporary.rename(output_directory)
    return output_directory


def _adapter_for(
    source_policy: dict[str, Any],
    path: Path,
    *,
    language: str,
) -> CorpusAdapter:
    adapter = source_policy["adapter"]
    if adapter == "tatoeba-weekly/v1":
        return TatoebaAdapter(path=path, target_language=language, policy=source_policy)
    if adapter == "opensubtitles-aligned/v1":
        return OpenSubtitlesAdapter(
            path=path, target_language=language, policy=source_policy
        )
    if adapter == "retained-sentence-bank/v1":
        return RetainedSentenceBankAdapter(
            path=path, target_language=language, policy=source_policy
        )
    raise HarvestRunError(f"no installed harvesting adapter for {adapter!r}")


def harvest_run_stage(
    repository_root: Path,
    workspace: Workspace,
    *,
    run_id: str,
    language: str,
    mode: str,
    source_snapshots: dict[str, Path],
    started_at: datetime | None = None,
) -> Path:
    """Harvest explicit raw snapshots into a run-owned, content-hashed candidate pool."""

    started_at = datetime.now(UTC) if started_at is None else started_at
    run_directory = workspace.root / "runs" / language / mode / run_id
    manifest_path = run_directory / "manifest.json"
    run_manifest = _load_object(manifest_path)
    if (
        run_manifest.get("run_id") != run_id
        or run_manifest.get("language") != language
        or run_manifest.get("mode") != mode
    ):
        raise HarvestRunError("run identity does not match the requested harvest")
    profile = load_pipeline_profile(run_directory / "profile.json")
    if profile["language"] != language or profile["mode"] != mode:
        raise HarvestRunError("run profile language or mode does not match")

    shared, language_policy, source_policies, config_content_id = load_harvest_policies(
        repository_root, profile
    )
    selected_sources = profile["harvest"]["sources"]
    if set(source_snapshots) != set(selected_sources):
        raise HarvestRunError(
            "source snapshots must exactly match the profile; no fallback or implicit union is allowed"
        )
    raw_root = workspace.root / "raw"
    normalized_snapshots: dict[str, Path] = {}
    for source, path in source_snapshots.items():
        resolved = path.expanduser().resolve()
        if not _inside(resolved, raw_root):
            raise HarvestRunError(
                f"source snapshot must be inside the workspace raw directory: {resolved}"
            )
        normalized_snapshots[source] = resolved

    output_directory = run_directory / STAGE_RELATIVE / "output"
    if output_directory.exists():
        raise HarvestRunError(
            "sentence-harvest output already exists; create a new run instead of overwriting it"
        )
    cards, inventory_content_id = load_harvest_inventory(
        run_directory / INVENTORY_RELATIVE,
        expected_language=language,
        expected_count=profile["scope"]["surface_limit"],
    )
    raw_ranks, frequency_content_id = load_frequency_ranks(
        run_directory / FREQUENCY_RELATIVE
    )
    matcher = SurfaceMatcher(cards, language_policy)
    frequency_ranks: dict[str, int] = {}
    for token, rank in raw_ranks.items():
        normalized = matcher.normalize(token)
        frequency_ranks[normalized] = min(rank, frequency_ranks.get(normalized, rank))

    # The budget may taper by rank, but never below what WSD will actually
    # score: a card with fewer candidates than the execution cap has its sense
    # assigned from thinner evidence, and nothing spare when a later rule
    # rejects one. The display floor is lower still and is enforced separately.
    execution_floor = execution_cap_per_card(profile)
    cap_for = {
        card["card_id"]: max(
            wsd_budget_for_rank(profile["harvest"], card["rank"]), execution_floor
        )
        for card in cards
    }
    cap = wsd_budget_per_card(profile["harvest"])
    # A card samples wider than its budget and lets quality cut it down, so the
    # pool it draws from is neutral on usage and picky about form.
    pool_multiplier = int(
        (shared.get("pooling") or {}).get("pool_multiplier") or DEFAULT_POOL_MULTIPLIER
    )
    quality_weights = (shared.get("pooling") or {}).get("quality_weights") or {}
    pools: dict[str, dict[str, SourcePool]] = {card["card_id"]: {} for card in cards}
    # An example is the same example wherever it turns up. Deduping the stream
    # once, before matching, costs one set lookup and saves the matcher from
    # re-tokenising subtitle lines that recur in hundreds of films.
    seen_identities: set[str] = set()
    sentence_records: dict[str, dict[str, Any]] = {}
    # Every distinct sentence that ever matched a card, counted before the
    # budget trims it. Without this the funnel is unreadable per card: the
    # report only ever showed the number that SURVIVED the cut.
    matched_per_card: Counter[str] = Counter()
    rejections: Counter[str] = Counter()
    matched_records = 0
    accepted_matches = 0
    adapters: list[CorpusAdapter] = []

    policies_by_source = {policy["source"]: policy for policy in source_policies}
    # Open every adapter first so the snapshot content ids -- and therefore this
    # stage's cache key -- are known before anything is scanned. Scanning is the
    # expensive part of a run (79 minutes for 3,000 Portuguese cards, 113 for
    # Czech), and it is entirely determined by the key: same implementation,
    # same config, same inputs, same output. A finished harvest elsewhere in the
    # workspace is that output, already computed.
    for source in selected_sources:
        adapters.append(
            _adapter_for(
                policies_by_source[source],
                normalized_snapshots[source],
                language=language,
            )
        )
    implementation_content_id = _implementation_content_id()
    inputs = {
        "inventory": inventory_content_id,
        "frequency_ranks": frequency_content_id,
        **{
            f"source_{source}": adapter.snapshot_content_id
            for source, adapter in zip(selected_sources, adapters, strict=True)
        },
    }
    cache_key = build_stage_cache_key(
        stage_name="sentence_harvest",
        stage_version=STAGE_VERSION,
        implementation_hash=implementation_content_id,
        config_hash=config_content_id,
        inputs=inputs,
        model_revisions={},
        random_seed=0,
    )
    reused_from = _reusable_harvest(workspace, run_directory, cache_key)
    if reused_from is not None:
        return _reuse_harvest_output(
            reused_from,
            run_id=run_id,
            output_directory=output_directory,
            started_at=started_at,
            cache_key=cache_key,
            implementation_content_id=implementation_content_id,
            config_content_id=config_content_id,
            inputs=inputs,
        )

    # Stop once enough cards have filled their budget. The rarest cards never
    # fill theirs at all, so waiting for every card is a full scan spent on a
    # handful of words; the policy names the fraction that is worth waiting for.
    # A profile may override the shared scan limits. The shared defaults were
    # calibrated when a 9,999-card Spanish scan cost 2,001 seconds, so stopping
    # at 95% of cards bought back most of it. At 64 seconds the trade is no
    # longer obvious: that stop left 68% of the Spanish subtitle corpus unread,
    # and `arzobispo` -- 71 occurrences, an ordinary word -- harvested nothing.
    scan_policy = {**(shared.get("scan") or {}), **(profile["harvest"].get("scan") or {})}
    stop_fraction = scan_policy.get("stop_when_budget_filled_fraction")
    check_every = int(scan_policy.get("check_every_records") or 50_000)
    stop_after = (
        int(len(cards) * float(stop_fraction))
        if isinstance(stop_fraction, (int, float)) and not isinstance(stop_fraction, bool)
        else None
    )
    # An absolute floor on every card is NOT a stopping condition. It reads as
    # prudence and behaves as a hostage: at 3,000 cards a single surface with
    # two matches in the whole corpus blocked the stop and forced a full 1.5M
    # scan -- 9.8 hours, against 27 seconds at 100 cards where no such card
    # existed. A word that cannot fill is rare, which is a fact about the word;
    # shortfall_policy declares those cards rather than chasing them.
    # A ceiling on how much of each corpus is read. The long tail is what makes
    # a harvest slow, and a card that cannot fill within the ceiling has told
    # you the word is rare rather than that the harvest failed.
    max_per_source = scan_policy.get("max_records_per_source")
    scanned_records = 0
    stopped_early = False

    # Under preferred_order the position of a source in the profile's list is
    # its priority: a card takes everything the first source can give before
    # the next one fills the remainder. Tatoeba is human-written and Czech
    # OpenSubtitles is often amateur translation, so preferring the curated
    # source is worth more than any ranking applied afterwards -- but only
    # where it has depth, which for Czech is 87% of cards.
    # What fraction of a card's budget each source may claim. Declared, so the
    # mix a deck is BUILT from stays a selection decision while the mix the pool
    # CONTAINS is fixed once at harvest.
    source_share = profile["harvest"].get("source_share") or {}
    # How many candidates each source should contribute to a card before the
    # harvest moves on. A share is relative to a budget that may change; a
    # minimum is an absolute guarantee that the pool holds enough of each source
    # to re-tune from later without harvesting again. Without it the first
    # source listed fills every budget and the second is barely read at all:
    # Spanish saw 283,535 Tatoeba rows against 16,962 subtitle rows.
    source_minimum = int(profile["harvest"].get("source_minimum_per_card") or 0)
    prefer = profile["harvest"].get("source_policy") == "preferred_order"
    for source_index, (source_name, adapter) in enumerate(
        zip(selected_sources, adapters, strict=True)
    ):
        # Preference rank and position in the list are different things. Under a
        # plain union every source ranks equally, but the LAST one read is still
        # the last one -- and conflating them made the early stop unreachable,
        # so a 100-card Portuguese harvest read the full ceiling and took 59
        # minutes instead of seconds.
        source_rank = source_index if prefer else 0
        is_last_source = source_index == len(adapters) - 1
        if stopped_early:
            break
        source_records = 0
        from_this_source: Counter[str] = Counter()
        for record in adapter.iter_records():
            scanned_records += 1
            source_records += 1
            if isinstance(max_per_source, int) and source_records > max_per_source:
                break
            # Move on from this source once it has given most cards its
            # minimum. Rare words are not chased: the source ceiling and this
            # fraction both bound how long one source may run.
            if (
                source_minimum
                # `>= (stop_after or 0)` made a disabled fraction mean "stop
                # immediately" rather than "never stop", because any count is
                # at least zero. A profile asking to read everything got one
                # checkpoint's worth of corpus.
                and stop_after is not None
                and scanned_records % check_every == 0
                and sum(1 for n in from_this_source.values() if n >= source_minimum)
                >= stop_after
            ):
                break
            if (
                stop_after is not None
                # Never stop while a later source has not been read. Under
                # preferred_order the first source saturates most cards long
                # before the checkpoint -- Tatoeba filled 95 of 100 Portuguese
                # cards in 50,000 rows -- so stopping here left the fallback
                # source with rows_seen: 0. The cards that need the fallback are
                # precisely the ones the fraction rule is willing to abandon.
                and is_last_source
                and scanned_records % check_every == 0
                and sum(
                    1
                    for cid, by_source in pools.items()
                    if sum(len(pool.held) for pool in by_source.values()) >= cap_for[cid]
                )
                >= stop_after
            ):
                stopped_early = True
                break
            try:
                validate_parallel_sentence(
                    record,
                    target_language=language,
                    provenance_policy=shared["provenance"],
                )
            except HarvestRecordError as error:
                rejections[f"invalid_provenance:{error}"] += 1
                continue
            record_identity = example_identity(record["target"]["text"])
            if record_identity in seen_identities:
                rejections["duplicate_example"] += 1
                continue
            matched_cards = matcher.find_cards(record["target"]["text"])
            if not matched_cards:
                rejections["no_inventory_surface"] += 1
                continue
            matched_records += 1
            reason = quality_rejection(
                record["target"]["text"],
                record["translation"]["text"],
                matcher=matcher,
                shared_policy=shared,
            )
            if reason is not None:
                rejections[reason] += 1
                continue
            variety = detect_variety(record["target"]["text"], language_policy)
            if variety is not None:
                record["target"]["variety"] = variety
            seen_identities.add(record_identity)
            admitted_here = False
            for card in matched_cards:
                card_id = card["card_id"]
                matched_per_card[card_id] += 1
                from_this_source[card_id] += 1
                accepted_matches += 1
                by_source = pools[card_id]
                pool = by_source.get(source_name)
                if pool is None:
                    pool = SourcePool(capacity=cap_for[card_id] * pool_multiplier)
                    by_source[source_name] = pool

                def build(card=card, card_id=card_id) -> dict[str, Any]:
                    # Only a match that actually enters the pool is scored.
                    # `que` scored 209,468 sentences to keep 80, and the top
                    # 100 cards were 55% of all scoring in a 9,999-card run.
                    return {
                        "sentence_id": record["sentence_id"],
                        "metrics": easiness_metrics(
                            record["target"]["text"],
                            card,
                            matcher=matcher,
                            frequency_ranks=frequency_ranks,
                            shared_policy=shared,
                        ),
                        "source": source_name,
                        "source_rank": source_rank,
                        "text": record["target"]["text"],
                    }

                if pool.offer(pool_key(card_id, record_identity), record_identity, build):
                    admitted_here = True
            if admitted_here:
                sentence_records[record["sentence_id"]] = record

    # Cut each card's uniform sample down to budget: worst third discarded on
    # form, then spread evenly across what is left. Taking the head of the
    # quality ranking instead would hand back the concentrating power that
    # sampling removed -- whatever residual correlation quality has with usage
    # would apply at full strength to the head and not at all to the rest.
    deck_size = len(cards)
    deaccented = deaccented_index(frequency_ranks)
    candidates: dict[str, dict[str, dict[str, Any]]] = {}
    for card in cards:
        card_id = card["card_id"]
        by_source = pools[card_id]
        card_cap = cap_for[card_id]
        quotas = _source_quotas(
            {name: len(pool.held) for name, pool in by_source.items()},
            card_cap,
            source_share,
        )
        kept: dict[str, dict[str, Any]] = {}
        for source_name, pool in by_source.items():
            quota = quotas.get(source_name, 0)
            if quota <= 0:
                continue
            scored = sorted(
                pool.held.items(),
                key=lambda entry: (
                    quality_penalty(
                        entry[1]["text"],
                        frequency_ranks=frequency_ranks,
                        deck_size=deck_size,
                        weights=quality_weights,
                        deaccented=deaccented,
                    ),
                    entry[1]["metrics"]["score"],
                    entry[1]["sentence_id"],
                ),
            )
            shortlist = scored[: max(quota, int(len(scored) * 2 / 3))]
            for identity, item in _sample_without_repeats(shortlist, quota):
                kept[identity] = item
        candidates[card_id] = kept
    live_sentence_ids = {
        item["sentence_id"]
        for by_identity in candidates.values()
        for item in by_identity.values()
    }
    sentence_records = {
        sentence_id: sentence_records[sentence_id]
        for sentence_id in sorted(live_sentence_ids)
    }
    candidate_cards: list[dict[str, Any]] = []
    per_surface: list[dict[str, Any]] = []
    scope = profile["scope"]
    for card in cards:
        final_target = display_examples_for_rank(scope, card["rank"])
        retained = [
            # The text rode along so quality could be scored without a second
            # pass over the bank; it lives in the sentence bank, not here.
            {key: value for key, value in item.items() if key != "text"}
            for item in sorted(
                candidates[card["card_id"]].values(),
                key=lambda item: (
                    item.get("source_rank", 0),
                    item["metrics"]["score"],
                    item["sentence_id"],
                ),
            )
        ]
        candidate_cards.append(
            {
                "card_id": card["card_id"],
                "surface_key": card["surface_key"],
                "display_form": card["display_form"],
                "rank": card["rank"],
                "candidates": retained,
            }
        )
        matched_before_budget = matched_per_card[card["card_id"]]
        per_surface.append(
            {
                "card_id": card["card_id"],
                "surface_key": card["surface_key"],
                "candidate_count": len(retained),
                "shortfall": max(0, final_target - len(retained)),
                # Funnel: how many sentences matched this card, how many the
                # per-card WSD budget discarded, and the rule that discarded them.
                "matched_before_budget": matched_before_budget,
                "discarded_by_budget": max(0, matched_before_budget - len(retained)),
                "budget_rule": f"wsd_budget_per_card={cap_for[card['card_id']]}",
                "display_rule": f"display_examples_per_card={final_target}",
            }
        )

    source_reports = [adapter.report() for adapter in adapters]
    candidate_payload = {
        "candidates_version": CANDIDATES_VERSION,
        "run_id": run_id,
        "language": language,
        "mode": mode,
        "source_policy": profile["harvest"]["source_policy"],
        "sources": selected_sources,
        "candidate_cap_per_surface": cap,
        "cards": candidate_cards,
    }
    report_payload = {
        "report_version": REPORT_VERSION,
        "run_id": run_id,
        "language": language,
        "source_policy": profile["harvest"]["source_policy"],
        "fallbacks": [],
        "sources": source_reports,
        "records_scanned": sum(report["rows_seen"] for report in source_reports),
        "records_with_inventory_match": matched_records,
        "accepted_matches_before_cap": accepted_matches,
        "retained_candidate_matches": sum(item["candidate_count"] for item in per_surface),
        "retained_sentences": len(sentence_records),
        "rejections": dict(sorted(rejections.items())),
        # A run must be able to say how much of the corpus it actually read.
        # Without this, an early stop and an exhausted corpus look identical in
        # the report, and a thin pool looks like a rare word rather than a
        # deliberate cut.
        "scan": {
            "stopped_early": stopped_early,
            "max_records_per_source": max_per_source,
            "source_minimum_per_card": source_minimum,
            "records_examined": scanned_records,
            "stop_when_budget_filled_fraction": stop_fraction,
            "cards_at_budget": sum(
                1 for item in per_surface if item["candidate_count"] >= cap_for[item["card_id"]]
            ),
        },
        "pooling": {
            "policy_version": POOLING_POLICY_VERSION,
            "pool_multiplier": pool_multiplier,
            "selection": "uniform_hash_sample_then_quality_shortlist_then_spread",
            "quality_weights": quality_weights,
            "note": (
                "Usage is sampled, form is judged. Ranking the pool by easiness "
                "kept four copies of `de vez en cuando` for `vez` and scored "
                "209,468 sentences for `que` to keep 80."
            ),
        },
        "surfaces_with_shortfall": sum(item["shortfall"] > 0 for item in per_surface),
        "release_blocked_by_shortfall": any(item["shortfall"] > 0 for item in per_surface),
        "per_surface": per_surface,
    }

    temporary_root = workspace.root / ".fluency" / "temporary"
    temporary = Path(tempfile.mkdtemp(prefix="sentence-harvest-", dir=temporary_root))
    try:
        (temporary / "candidates.json").write_bytes(json_bytes(candidate_payload))
        (temporary / "report.json").write_bytes(json_bytes(report_payload))
        with (temporary / "sentence-bank.jsonl").open("w", encoding="utf-8") as stream:
            for record in sentence_records.values():
                stream.write(canonical_json(record))
                stream.write("\n")

        inputs = {
            "inventory": inventory_content_id,
            "frequency_ranks": frequency_content_id,
            **{
                f"source_{source}": adapter.snapshot_content_id
                for source, adapter in zip(selected_sources, adapters, strict=True)
            },
        }
        implementation_content_id = _implementation_content_id()
        stage = StageManifest(
            stage_name="sentence_harvest",
            stage_version=STAGE_VERSION,
            cache_key=build_stage_cache_key(
                stage_name="sentence_harvest",
                stage_version=STAGE_VERSION,
                implementation_hash=implementation_content_id,
                config_hash=config_content_id,
                inputs=inputs,
                model_revisions={},
                random_seed=0,
            ),
            implementation_hash=implementation_content_id,
            config_hash=config_content_id,
            status="running",
            started_at=_timestamp(started_at),
            inputs=inputs,
            model_revisions={},
            random_seed=0,
            outputs={},
        ).complete(
            {
                "candidates": file_content_id(temporary / "candidates.json"),
                "report": file_content_id(temporary / "report.json"),
                "sentence_bank": file_content_id(temporary / "sentence-bank.jsonl"),
            }
        )
        stage_manifest = stage.to_dict()
        (temporary / "manifest.json").write_bytes(json_bytes(stage_manifest))
        output_directory.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temporary, output_directory)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    contract_path = run_directory / STAGE_RELATIVE / "contract.json"
    contract = _load_object(contract_path)
    contract["status"] = "complete"
    contract["completed_at"] = stage_manifest["completed_at"]
    contract["output_directory"] = "output"
    contract["manifest_content_id"] = file_content_id(output_directory / "manifest.json")
    atomic_write(contract_path, contract, temporary_root)

    run_manifest["status"] = "running"
    run_manifest["inputs"] = {
        **run_manifest.get("inputs", {}),
        **stage_manifest["inputs"],
    }
    atomic_write(manifest_path, run_manifest, temporary_root)
    return output_directory
