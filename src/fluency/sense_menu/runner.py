"""Execute the immutable dictionary sense-menu stage for one planned run."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from fluency.core.hashing import canonical_content_id, file_content_id
from fluency.core.manifests import StageManifest, build_stage_cache_key
from fluency.core.workspace import Workspace
from fluency.harvest.inventory import load_harvest_inventory
from fluency.pipeline.planning import load_pipeline_profile
from fluency.surfaces.ledger import ledger_path
from fluency.core.io import atomic_write, json_bytes
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.kaikki import (
    ADAPTER_ID as KAIKKI_ADAPTER_ID,
    KaikkiHeadwordSource,
    KaikkiSenseMenuAdapter,
)
from fluency.sense_menu.spanishdict import (
    ADAPTER_ID as SPANISHDICT_ADAPTER_ID,
    SpanishDictSenseMenuAdapter,
)
from fluency.sense_menu.spanishdict_lemmas import (
    RULE_VERSION as SPANISHDICT_LEMMA_RULE,
    SpanishDictHeadwordSource,
    SpanishDictLemmaRule,
)
from fluency.surfaces.declared import Context, DeclaredRegistry
from fluency.surfaces.stores import stack as declared_stack
from fluency.surfaces.resolver import RESOLVER_VERSION, ModePolicy, Resolver

DECLARED_ROOT = Path("config/declared")
STRATEGY_POLICY = Path("config/surfaces/strategy.json")


STAGE_VERSION = "sense-menu-stage/v1"
STAGE_RELATIVE = Path("stages/02_sense_menu")
INVENTORY_RELATIVE = Path("stages/01_inventory/output/inventory.json")


class SenseMenuRunError(ValueError):
    """Raised when a sense-menu run would be ambiguous, mutable, or implicit."""


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SenseMenuRunError(f"required run artifact does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise SenseMenuRunError(f"run artifact is not valid JSON: {path}") from error
    if not isinstance(value, dict):
        raise SenseMenuRunError(f"run artifact must contain an object: {path}")
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
        package / "config.py",
        package / "kaikki.py",
        package / "spanishdict.py",
        package.parent / "wsd" / "menus.py",
    )
    return canonical_content_id(
        {str(path.relative_to(package.parent)): file_content_id(path) for path in paths}
    )


def _store_lemmas(workspace, language: str) -> dict[str, list[str]]:
    """Surface to lemma, as the observation store records it.

    Only lemmas that were actually resolved are handed over: a surface that is
    merely its own headword adds no hop the builder does not already have, and
    passing it would make every card look externally resolved.
    """
    view = ledger_path(workspace.root, language)
    if not view.exists():
        return {}
    try:
        payload = json.loads(view.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, list[str]] = {}
    for surface, row in (payload.get("surfaces") or {}).items():
        lemmas = [lemma for lemma in (row.get("lemmas") or []) if lemma and lemma != surface]
        if lemmas:
            out[surface] = lemmas
    return out


def _resolver_settings(
    repository_root: Path, profile: dict[str, Any], language: str, mode: str
) -> tuple[frozenset[str], DeclaredRegistry, ModePolicy, dict[str, Any]] | None:
    """The profile's ``sense_menu.resolver`` block, loaded and pinned.

    It names the cards whose headword set comes from the resolver; every
    other card is built exactly as before. The declared lists and the strategy
    policy are pinned by content, so the stage manifest records which
    hand-written facts a menu was built from.
    """
    declared = profile["sense_menu"].get("resolver")
    if not declared:
        return None
    surfaces = declared.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces or not all(isinstance(s, str) and s for s in surfaces):
        raise SenseMenuRunError("sense_menu.resolver.surfaces must list the resolved surfaces explicitly")
    # Speech reads the language store only (proposal 0003 §4).
    registry = declared_stack(repository_root, language)
    policy = ModePolicy.load(repository_root / STRATEGY_POLICY, mode)
    pinned = {
        "resolver_version": RESOLVER_VERSION,
        "surfaces": sorted(set(surfaces)),
        "declared_entries": canonical_content_id(
            sorted((entry.to_dict() for entry in registry.entries), key=lambda e: e["entry_id"])),
        "strategy_policy": file_content_id(repository_root / STRATEGY_POLICY),
        "mode": mode,
        "minimum_trust": policy.minimum_trust,
    }
    return frozenset(surfaces), registry, policy, pinned


def _store_lemma_provenance(workspace, language: str) -> dict[str, str]:
    """Surface -> how the ledger's lemma was established (e.g. "CNK word at a glance")."""
    view = ledger_path(workspace.root, language)
    if not view.exists():
        return {}
    try:
        payload = json.loads(view.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {surface: str(row.get("lemma_provenance"))
            for surface, row in (payload.get("surfaces") or {}).items()
            if row.get("lemma_provenance")}


def _build_and_carry(workspace, adapter, cards, *, snapshot_id, language, mode, resolved, carry_run):
    """Build only the resolved cards; carry every other card's menu verbatim.

    A menu depends on the ledger's lemmas as well as the dictionary, and the
    ledger moves between runs, so rebuilding a card the resolver does not
    touch can change it (measured: 877 Portuguese and 1,114 Czech cards). A run
    that re-resolves a named set of cards must not move the rest, so the rest
    are copied from ``carry_run``'s stage 02 and labelled as carried
    (Invariant 1). The resolved cards are the only ones this stage computed.
    """
    source = workspace.root / "runs" / language / mode / carry_run / STAGE_RELATIVE / "output"
    source_menu = _load_object(source / "sense-menu.json")
    source_report = _load_object(source / "report.json")
    built_cards = [card for card in cards if card.get("surface_key") in resolved]
    menu, report = adapter.build(built_cards, snapshot_id=snapshot_id)
    fresh = {card["card_id"]: card for card in menu["cards"]}
    fresh_rows = {row["card_id"]: row for row in report["per_surface"]}
    old = {card["card_id"]: card for card in source_menu.get("cards", [])}
    old_rows = {row["card_id"]: row for row in source_report.get("per_surface", [])}
    missing = [card["card_id"] for card in cards if card["card_id"] not in fresh and card["card_id"] not in old]
    if missing:
        raise SenseMenuRunError(f"{len(missing)} cards are neither resolved nor in {carry_run}'s menu")
    menu["cards"] = [fresh.get(card["card_id"]) or old[card["card_id"]] for card in cards]
    report["per_surface"] = [fresh_rows.get(card["card_id"]) or old_rows[card["card_id"]] for card in cards]
    carried = {
        "from_run": carry_run,
        "cards": len(cards) - len(fresh),
        "resolved_cards": len(fresh),
        "source_snapshot_id": source_menu.get("snapshot_id"),
        "source_snapshot_content_id": source_menu.get("snapshot_content_id"),
        "source_sense_menu_content_id": file_content_id(source / "sense-menu.json"),
    }
    menu["carried"] = carried
    report["carried"] = carried
    report["inventory_cards"] = len(cards)
    report["cards_ready"] = sum(row["status"] == "ready" for row in report["per_surface"])
    report["cards_without_menu"] = sum(row["status"] == "no_menu" for row in report["per_surface"])
    report["analysis_count"] = sum(len(card.get("analyses") or []) for card in menu["cards"])
    report["sense_count"] = sum(len(a.get("senses") or []) for card in menu["cards"]
                                for a in card.get("analyses") or [])
    return menu, report


def build_sense_menu_stage(
    repository_root: Path,
    workspace: Workspace,
    *,
    run_id: str,
    language: str,
    mode: str,
    dictionary_snapshot: Path,
    snapshot_id: str,
    started_at: datetime | None = None,
) -> Path:
    """Normalize one explicit provider snapshot into a run-owned closed menu."""

    if not snapshot_id.strip():
        raise SenseMenuRunError("snapshot_id must be explicit and non-empty")
    started_at = datetime.now(UTC) if started_at is None else started_at
    run_directory = workspace.root / "runs" / language / mode / run_id
    manifest_path = run_directory / "manifest.json"
    run_manifest = _load_object(manifest_path)
    if (
        run_manifest.get("run_id") != run_id
        or run_manifest.get("language") != language
        or run_manifest.get("mode") != mode
    ):
        raise SenseMenuRunError("run identity does not match the requested sense menu")
    profile = load_pipeline_profile(run_directory / "profile.json")
    if profile["language"] != language or profile["mode"] != mode:
        raise SenseMenuRunError("run profile language or mode does not match")
    source_adapter = profile["sense_menu"]["source_adapter"]
    language_policy = load_sense_menu_language_policy(
        repository_root,
        policy_id=profile["sense_menu"]["language_policy"],
        language=language,
    )

    resolved_snapshot = dictionary_snapshot.expanduser().resolve()
    if not _inside(resolved_snapshot, workspace.root / "raw"):
        raise SenseMenuRunError(
            f"dictionary snapshot must be inside the workspace raw directory: {resolved_snapshot}"
        )
    output_directory = run_directory / STAGE_RELATIVE / "output"
    if output_directory.exists():
        raise SenseMenuRunError(
            "sense-menu output already exists; create a new run instead of overwriting it"
        )
    cards, inventory_content_id = load_harvest_inventory(
        run_directory / INVENTORY_RELATIVE,
        expected_language=language,
        expected_count=profile["scope"]["surface_limit"],
    )
    adapter: KaikkiSenseMenuAdapter | SpanishDictSenseMenuAdapter
    if source_adapter == KAIKKI_ADAPTER_ID:
        adapter = KaikkiSenseMenuAdapter(
            resolved_snapshot,
            language_code=language,
            gloss_language=profile["sense_menu"]["gloss_language"],
            source_edition=profile["sense_menu"]["source_edition"],
            language_policy=language_policy,
            external_lemmas=_store_lemmas(workspace, language),
        )
    elif source_adapter == SPANISHDICT_ADAPTER_ID:
        adapter = SpanishDictSenseMenuAdapter(
            resolved_snapshot,
            language_code=language,
            gloss_language=profile["sense_menu"]["gloss_language"],
            source_edition=profile["sense_menu"]["source_edition"],
            language_policy=language_policy,
        )
    else:
        raise SenseMenuRunError("no installed sense-menu adapter matches the run profile")
    resolver_settings = _resolver_settings(repository_root, profile, language, mode)
    if resolver_settings is not None:
        surfaces, registry, policy, pinned = resolver_settings
        context = Context(language=language, mode=mode)
        if isinstance(adapter, SpanishDictSenseMenuAdapter):
            reverse = json.loads((resolved_snapshot / "conjugation_reverse.json").read_text(encoding="utf-8"))
            source = SpanishDictHeadwordSource(
                SpanishDictLemmaRule(reverse, known_headwords=frozenset(adapter.headword_cache)),
                adapter.surface_cache, adapter.headword_cache)
            pinned["lemma_rule"] = SPANISHDICT_LEMMA_RULE
        else:
            # Kaikki: the dump is read in passes inside build(), which binds the
            # source to its scan. External first hops keep the ledger's label.
            source = KaikkiHeadwordSource(_store_lemma_provenance(workspace, language))
            pinned["lemma_rule"] = "kaikki-redirect-paths/v1"
        adapter.resolver = Resolver(source, registry, context, policy)
        adapter.resolver_surfaces = surfaces
    carried_from = (profile["sense_menu"].get("resolver") or {}).get("carry_from_run")
    if resolver_settings is not None and carried_from:
        menu, report = _build_and_carry(
            workspace, adapter, cards, snapshot_id=snapshot_id, language=language, mode=mode,
            resolved=resolver_settings[0], carry_run=carried_from)
        resolver_settings[3]["carry_from_run"] = carried_from
    else:
        menu, report = adapter.build(cards, snapshot_id=snapshot_id)
    inventory_cards = int(report.get("inventory_cards", 0))
    cards_ready = int(report.get("cards_ready", 0))
    coverage = cards_ready / inventory_cards if inventory_cards else 0.0
    report["card_coverage"] = coverage
    minimum_coverage = profile["sense_menu"].get("minimum_card_coverage")
    if minimum_coverage is not None and coverage < float(minimum_coverage):
        raise SenseMenuRunError(
            "sense-menu coverage is below the profile minimum: "
            f"{cards_ready}/{inventory_cards} ({coverage:.2%}) < {float(minimum_coverage):.2%}"
        )

    config = {
        "source_adapter": source_adapter,
        "language": language,
        "gloss_language": adapter.gloss_language,
        "source_edition": adapter.source_edition,
        "language_policy": language_policy,
        "card_identity": "surface-card/v1",
        "fallback_policy": "none",
    }
    if resolver_settings is not None:
        # The resolver is not a fallback in the old sense: it decides the
        # headword set first, for the named cards only, and says so.
        config["fallback_policy"] = RESOLVER_VERSION
        config["resolver"] = resolver_settings[3]
    if isinstance(adapter, KaikkiSenseMenuAdapter):
        config["max_redirect_hops"] = adapter.max_redirect_hops
    inputs = {
        "inventory": inventory_content_id,
        "dictionary_snapshot": adapter.snapshot_content_id,
    }
    if menu.get("carried"):
        inputs["carried_sense_menu"] = menu["carried"]["source_sense_menu_content_id"]
    implementation_content_id = _implementation_content_id()
    config_content_id = canonical_content_id(config)
    temporary_root = workspace.root / ".fluency" / "temporary"
    temporary = Path(tempfile.mkdtemp(prefix="sense-menu-", dir=temporary_root))
    try:
        (temporary / "sense-menu.json").write_bytes(json_bytes(menu))
        (temporary / "report.json").write_bytes(json_bytes(report))
        stage = StageManifest(
            stage_name="sense_menu",
            stage_version=STAGE_VERSION,
            cache_key=build_stage_cache_key(
                stage_name="sense_menu",
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
                "sense_menu": file_content_id(temporary / "sense-menu.json"),
                "report": file_content_id(temporary / "report.json"),
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
    run_manifest["inputs"] = {**run_manifest.get("inputs", {}), **inputs}
    atomic_write(manifest_path, run_manifest, temporary_root)
    return output_directory
