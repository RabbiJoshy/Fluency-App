"""The ``fluency enrichment`` command group."""

from __future__ import annotations

from fluency.cli.shared import *  # noqa: F401,F403
from fluency.cli.shared import (  # noqa: F401
    Path, argparse, json, json_bytes, os, re,
    _workspace_path,  # private names are not re-exported by the star import
)

NAME = "enrichment"


def register(subparsers) -> None:
    enrichment = subparsers.add_parser(
        "enrichment", help="build independently selectable optional product layers"
    )
    enrichment_actions = enrichment.add_subparsers(
        dest="enrichment_command", required=True
    )
    conjugations = enrichment_actions.add_parser(
        "build-conjugations",
        help="build a bounded conjugation layer for one exact sense menu",
    )
    conjugations.add_argument(
        "--workspace", default=os.environ.get("FLUENCY_WORKSPACE")
    )
    conjugations.add_argument("--sense-menu", type=Path, required=True)
    conjugations.add_argument("--source-snapshot", type=Path, required=True)
    conjugations.add_argument("--locale", default=None)
    cognates = enrichment_actions.add_parser(
        "build-cognates",
        help="score how transparent a deck's surfaces are to languages the learner reads",
    )
    cognates.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    cognates.add_argument("--language", required=True)
    cognates.add_argument(
        "--release-index",
        type=Path,
        help="deck to take target surfaces from; omit when --target-extract is given",
    )
    cognates.add_argument(
        "--target-extract",
        type=Path,
        help="the target language's own dictionary — scores every surface it "
             "lists rather than only the ones a deck happens to contain",
    )
    cognates.add_argument(
        "--english-wordlist",
        type=Path,
        help="an English word list deciding which gloss tokens count as English; "
             "without it a gloss token can be the target word itself",
    )
    cognates.add_argument(
        "--surface-universe",
        type=Path,
        help="a 'surface count' frequency list bounding which surfaces to score",
    )
    cognates.add_argument(
        "--release-id",
        required=True,
        help="recorded as provenance; the mapping is keyed by language, not by release",
    )
    cognates.add_argument("--config-root", type=Path, default=Path("config"))
    cognates.add_argument(
        "--out",
        type=Path,
        help="app-facing cognates.json (default: <workspace>/cognates/<language>/cognates.json)",
    )
    cognates.add_argument("--layer-out", type=Path, help="full layer, with match provenance")
    # One flag per known language: "en" needs no extract because the deck's
    # glosses are already English; any other language takes its dictionary.
    cognates.add_argument(
        "--known",
        action="append",
        required=True,
        metavar="CODE[=EXTRACT]",
        help="known language, e.g. --known en --known pl=/path/kaikki-Polish.jsonl",
    )
    titles = enrichment_actions.add_parser(
        "build-source-titles",
        help="resolve OpenSubtitles IMDb ids to human film and series names",
    )
    titles.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    titles.add_argument(
        "--ids",
        action="append",
        type=Path,
        default=[],
        help="OpenSubtitles .ids file; repeat for each language corpus",
    )
    titles.add_argument(
        "--release",
        action="append",
        default=[],
        metavar="LANG/MODE/RELEASE_ID",
        help="also collect title ids cited by an existing speech release",
    )
    titles.add_argument(
        "--imdb-dir",
        type=Path,
        help="directory containing title.basics.tsv.gz and title.episode.tsv.gz",
    )
    titles.add_argument(
        "--out",
        type=Path,
        required=True,
        help="JSON snapshot path; must be inside workspace/raw",
    )
    attach = enrichment_actions.add_parser(
        "attach-source-titles",
        help="publish a successor release with human film names on OpenSubtitles examples",
    )
    attach.add_argument("--workspace", default=os.environ.get("FLUENCY_WORKSPACE"))
    attach.add_argument("--language", required=True)
    attach.add_argument("--mode", default="speech")
    attach.add_argument("--source-release", required=True)
    attach.add_argument("--target-release", required=True)
    attach.add_argument("--source-titles", type=Path, required=True)


def handle_enrichment(args: argparse.Namespace) -> int:
    workspace = Workspace.load(_workspace_path(args.workspace))
    if args.enrichment_command == "build-conjugations":
        metadata, coverage = build_conjugation_layer(
            workspace,
            sense_menu=args.sense_menu,
            source_snapshot=args.source_snapshot,
            locale=args.locale,
        )
        print(f"Built immutable conjugation layer: {metadata.artifact_id}")
        print(
            f"Covered {coverage['covered_headwords']} of "
            f"{coverage['requested_headwords']} requested verb headwords."
        )
        if coverage["missing_headwords"]:
            print("Missing headwords: " + ", ".join(coverage["missing_headwords"]))
        print("No release was composed or activated.")
        return 0
    if args.enrichment_command == "build-cognates":
        known: dict[str, Path | None] = {}
        for item in args.known:
            code, _, extract = str(item).partition("=")
            known[code.strip()] = Path(extract) if extract else None
        workspace_root = Workspace.load(_workspace_path(args.workspace)).root
        out = args.out or workspace_root / "cognates" / args.language / "cognates.json"
        universe = None
        if getattr(args, "surface_universe", None):
            from fluency.inventory.coverage import read_frequency_counts
            counts, _total = read_frequency_counts(args.surface_universe)
            universe = set(counts)
        english_words = None
        if getattr(args, "english_wordlist", None):
            from fluency.enrichments.cognates import read_english_wordlist
            english_words = read_english_wordlist(args.english_wordlist)
        layer = build_cognate_layer(
            english_words=english_words,
            target_extract=getattr(args, "target_extract", None),
            surface_universe=universe,
            language=args.language,
            release_index=args.release_index,
            known_extracts=known,
            config_root=args.config_root,
            release_id=args.release_id,
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(json_bytes(build_app_cognates(layer)))
        if args.layer_out:
            args.layer_out.parent.mkdir(parents=True, exist_ok=True)
            args.layer_out.write_bytes(json_bytes(layer))
        for code in layer["known_languages"]:
            report = layer["coverage"][code]
            print(
                f"{args.language}->{code}: scored {report['scored_surfaces']} of "
                f"{report['deck_surfaces']} deck surfaces "
                f"against {report['known_entries']} {code} entries"
            )
        print(f"Wrote {out}")
        print("No release was composed or activated.")
        return 0
    if args.enrichment_command == "build-source-titles":
        from fluency.harvest.source_titles import (
            build_source_titles_snapshot,
            collect_title_ids_from_ids_file,
            collect_title_ids_from_examples,
            iter_deck_examples,
        )

        out_path = args.out.expanduser().resolve()
        try:
            out_path.relative_to((workspace.root / "raw").resolve())
        except ValueError:
            raise SystemExit("source titles snapshot must be inside workspace/raw")
        wanted: set[str] = set()
        for ids_path in args.ids:
            wanted.update(collect_title_ids_from_ids_file(ids_path))
        for spec in args.release:
            language, mode, release_id = spec.split("/", 2)
            deck = json.loads(
                (
                    workspace.root / "releases" / language / mode / release_id / "deck.json"
                ).read_text(encoding="utf-8")
            )
            wanted.update(collect_title_ids_from_examples(iter_deck_examples(deck)))
        if not wanted:
            raise SystemExit("no OpenSubtitles title ids were found")
        imdb_dir = (
            args.imdb_dir.expanduser().resolve()
            if args.imdb_dir
            else workspace.root / "raw/imdb/imdb-retrieved-2026-08-22"
        )
        report = build_source_titles_snapshot(
            wanted,
            basics_path=imdb_dir / "title.basics.tsv.gz",
            episodes_path=imdb_dir / "title.episode.tsv.gz",
            out_path=out_path,
        )
        print(
            f"Resolved {report['resolved']:,} of {report['requested']:,} "
            f"title ids -> {out_path}"
        )
        if report["missing"]:
            print(f"Unresolved: {len(report['missing']):,}")
        print("No release was composed or activated.")
        return 0
    if args.enrichment_command == "attach-source-titles":
        from fluency.release.source_titles import attach_source_titles

        directory, stats = attach_source_titles(
            workspace,
            language=args.language,
            mode=args.mode,
            source_release_id=args.source_release,
            target_release_id=args.target_release,
            source_titles_path=args.source_titles,
        )
        print(f"Built inactive source-title release: {directory}")
        print(
            f"OpenSubtitles examples: {stats['resolved']:,} named, "
            f"{stats['unresolved']:,} still only an IMDb id, "
            f"{stats['opensubtitles']:,} total"
        )
        print("Activation unchanged. Validate, then run `fluency release activate ...`.")
        return 0
    raise AssertionError(f"Unhandled enrichment command: {args.enrichment_command}")


def handle(args) -> int:
    return handle_enrichment(args)
