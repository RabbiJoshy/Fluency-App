"""The ``fluency release`` command group."""

from __future__ import annotations

from fluency.cli.shared import *  # noqa: F401,F403
from fluency.cli.shared import (  # noqa: F401
    Path, argparse, json, os, re,
    _workspace_path,  # private names are not re-exported by the star import
)

NAME = "release"


def register(subparsers) -> None:
    release = subparsers.add_parser("release", help="compose, inspect, validate, and activate exact releases")
    release_actions = release.add_subparsers(dest="release_command", required=True)
    for action in ("list", "catalog"):
        action_parser = release_actions.add_parser(action)
        action_parser.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
        action_parser.add_argument("--language", default="fr")
        action_parser.add_argument("--mode", default="speech")
    validate = release_actions.add_parser("validate")
    validate.add_argument("release_id")
    validate.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    validate.add_argument("--language", default="fr")
    validate.add_argument("--mode", default="speech")
    activate = release_actions.add_parser("activate")
    activate.add_argument("release_id")
    activate.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    activate.add_argument("--language", default="fr")
    activate.add_argument("--mode", default="speech")
    compose = release_actions.add_parser("compose")
    compose.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    compose.add_argument("--composition", type=Path, required=True, help="exact release-composition JSON")
    compose.add_argument("--deck", type=Path, required=True, help="already assembled compact deck JSON")
    shard = release_actions.add_parser(
        "shard-examples",
        help="split vocabulary.examples.json into per-study-set shards for greedy loading",
    )
    shard.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    shard.add_argument("--language", required=True)
    shard.add_argument("--mode", default="speech")
    shard.add_argument("--release-id", required=True)
    index_shard = release_actions.add_parser(
        "shard-index",
        help="split vocabulary.index.json into skinny columns plus per-study-set rows",
    )
    index_shard.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    index_shard.add_argument("--language", required=True)
    index_shard.add_argument("--mode", default="speech")
    index_shard.add_argument("--release-id", required=True)
    payload = release_actions.add_parser(
        "shard-speech-payload",
        help="split both the speech index and examples for greedy set loading",
    )
    payload.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    payload.add_argument("--language", required=True)
    payload.add_argument("--mode", default="speech")
    payload.add_argument("--release-id", required=True)


def handle_release(args: argparse.Namespace) -> int:
    workspace = Workspace.load(_workspace_path(args.workspace))
    if args.release_command == "compose":
        directory = compose_release(workspace, load_json_object(args.composition), load_json_object(args.deck))
        print(f"Composed immutable candidate: {directory}")
        print("Activation unchanged. Validate, then run `fluency release activate ...`.")
        return 0
    if args.release_command == "validate":
        directory = workspace.root / "releases" / args.language / args.mode / args.release_id
        manifest, _, composition = validate_release_bundle(directory)
        print(f"Valid release: {manifest['release_id']}")
        print(f"Layers: {', '.join(sorted(composition['layers']))}")
        return 0
    if args.release_command == "activate":
        path = activate_release(workspace, args.language, args.mode, args.release_id)
        print(f"Activated release: {args.release_id}")
        print(f"Pointer: {path}")
        return 0
    if args.release_command == "catalog":
        path = write_catalog(workspace, args.language, args.mode)
        print(f"Wrote release catalog: {path}")
        return 0
    if args.release_command in {"shard-examples", "shard-index", "shard-speech-payload"}:
        from fluency.release.example_shards import shard_app_examples
        from fluency.release.index_shards import shard_app_index

        app_dir = (
            workspace.root / "releases" / args.language / args.mode / args.release_id / "app"
        )
        if args.release_command in {"shard-index", "shard-speech-payload"}:
            manifest = shard_app_index(app_dir)
            print(f"Wrote {manifest['shard_count']} index row shards under {app_dir}")
            if manifest["missing_cards"]:
                print(f"Missing index cards: {manifest['missing_cards']}")
        if args.release_command in {"shard-examples", "shard-speech-payload"}:
            manifest = shard_app_examples(app_dir)
            print(f"Wrote {manifest['shard_count']} example shards under {app_dir}")
            if manifest["missing_cards"]:
                print(f"Missing example cards: {manifest['missing_cards']}")
        return 0
    if args.release_command == "list":
        catalog = build_catalog(workspace, args.language, args.mode)
        for candidate in catalog["candidates"]:
            marker = "*" if candidate["active"] else " "
            print(f"{marker} {candidate['release_id']}  {candidate['card_count']} cards  WSD={candidate['wsd_status']}  fallbacks={candidate['fallback_layers']}")
        return 0
    raise AssertionError(f"Unhandled release command: {args.release_command}")


def handle(args) -> int:
    return handle_release(args)
