"""The ``fluency lexical-relations`` command group."""

from __future__ import annotations

from fluency.cli.shared import *  # noqa: F401,F403
from fluency.cli.shared import (  # noqa: F401
    Path, argparse, os,
    _workspace_path,
)

NAME = "lexical-relations"


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        "lexical-relations",
        help="build and attach optional synonym/antonym layers",
    )
    actions = parser.add_subparsers(dest="lexical_relations_command", required=True)

    pin_sd = actions.add_parser(
        "pin-spanishdict",
        help="pin the recovered SpanishDict thesaurus fold as reconstructed source",
    )
    pin_sd.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    pin_sd.add_argument("--source", type=Path, required=True)
    pin_sd.add_argument("--snapshot-id", required=True)

    pin_kaikki = actions.add_parser(
        "pin-kaikki",
        help="pin a Kaikki dump as Wiktionary synonym/antonym evidence",
    )
    pin_kaikki.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    pin_kaikki.add_argument("--source", type=Path, required=True)
    pin_kaikki.add_argument("--language", required=True)
    pin_kaikki.add_argument("--snapshot-id", required=True)

    build = actions.add_parser(
        "build",
        help="build a bounded lexical-relations layer for one exact sense menu",
    )
    build.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    build.add_argument("--sense-menu", type=Path, required=True)
    build.add_argument("--source-snapshot", type=Path, required=True)
    build.add_argument("--locale", default=None)

    attach = actions.add_parser(
        "attach",
        help="publish a successor release with synonyms stamped on the app index",
    )
    attach.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    attach.add_argument("--language", required=True)
    attach.add_argument("--mode", default="speech")
    attach.add_argument("--source-release", required=True)
    attach.add_argument("--target-release", required=True)
    attach.add_argument("--artifact-id", required=True)


def handle(args) -> int:
    from fluency.core.workspace import Workspace
    from fluency.enrichments.lexical_relations import (
        build_lexical_relations_layer,
        pin_kaikki_dump,
        pin_spanishdict_fold,
    )
    from fluency.release.lexical_relations import attach_lexical_relations

    workspace = Workspace.load(_workspace_path(args.workspace))
    command = args.lexical_relations_command
    if command == "pin-spanishdict":
        snapshot = pin_spanishdict_fold(
            workspace,
            source=args.source,
            snapshot_id=args.snapshot_id,
        )
        print(f"Pinned SpanishDict thesaurus fold: {snapshot}")
        print("No layer was built and no release was composed.")
        return 0
    if command == "pin-kaikki":
        snapshot = pin_kaikki_dump(
            workspace,
            source=args.source,
            language=args.language,
            snapshot_id=args.snapshot_id,
        )
        print(f"Pinned Kaikki lexical-relation dump: {snapshot}")
        print("No layer was built and no release was composed.")
        return 0
    if command == "build":
        metadata, coverage = build_lexical_relations_layer(
            workspace,
            sense_menu=args.sense_menu,
            source_snapshot=args.source_snapshot,
            locale=args.locale,
        )
        print(f"Built immutable lexical-relations layer: {metadata.artifact_id}")
        print(
            f"Covered {coverage['covered_headwords']} of "
            f"{coverage['requested_headwords']} requested headwords."
        )
        print("No release was composed or activated.")
        return 0
    if command == "attach":
        directory, stats = attach_lexical_relations(
            workspace,
            language=args.language,
            mode=args.mode,
            source_release_id=args.source_release,
            target_release_id=args.target_release,
            artifact_id=args.artifact_id,
        )
        print(f"Built inactive lexical-relations release: {directory}")
        print(f"Relation records: {stats['records']:,}")
        print("Activation unchanged. Validate, then run `fluency release activate ...`.")
        return 0
    raise AssertionError(f"Unhandled lexical-relations command: {command}")
