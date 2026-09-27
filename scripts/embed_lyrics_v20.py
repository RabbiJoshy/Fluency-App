"""Spend-gated embedding run for lyrics v20: lyric lines and uninflected glosses.

Proposal 0004, "WSD embedding coverage": v19 scored almost every sense pair by
word overlap because the lines were never embedded and the glosses it looked
up were inflected strings nothing had embedded. v20 scores the uninflected
gloss, so this embeds exactly the strings v20's WSD will look up -- every
selected line of a card with more than one sense, and every gloss scored by
embedding -- for all four artists, through the shared resumable store
(``fluency.nlp.embeddings``).

Without ``--spend`` it prints the projected units and calls nothing. With it,
``--confirm`` must repeat the projected string count, so a spend is always
the one that was shown. The test playlist's per-artist delta (3,997 vectors
already paid for) is merged into the shared store first and then no longer
read by anything.

    PYTHONPATH=src python scripts/embed_lyrics_v20.py                 # projection only
    PYTHONPATH=src python scripts/embed_lyrics_v20.py --spend --confirm N
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plant_artist_v20 as v20  # noqa: E402
from fluency.lyrics.wsd_execute import dotenv_value  # noqa: E402
from fluency.nlp.embeddings import BATCH_SIZE, EMBED_MODEL, ensure_embeddings, load_cache, merge_delta  # noqa: E402

LEGACY_DELTAS = ("spanish-test-playlist-delta.npz",)


def legacy_vectors(workspace: Path) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for name in LEGACY_DELTAS:
        path = workspace / "raw/cache/embeddings" / name
        if path.is_file():
            blob = np.load(path, allow_pickle=True)
            out.update({str(k): v for k, v in zip(blob["keys"], blob["vectors"])})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--spend", action="store_true")
    parser.add_argument("--confirm", type=int, default=None, help="the projected string count, repeated")
    parser.add_argument("--polysemous-fallback", default=None, choices=("heuristic", "embedding"))
    args = parser.parse_args()
    profile = v20.load_profile()
    fallback = args.polysemous_fallback or profile["wsd"]["polysemous_fallback_default"]
    workspace = v20.WORKSPACE
    cache_path = workspace / profile["wsd"]["embedding_cache"]

    per_artist: dict[str, dict[str, set[str]]] = {}
    for artist in v20.ARTISTS:
        plan = v20.plan_artist(artist, workspace=workspace, polysemous_fallback=fallback, profile=profile)
        per_artist[artist] = {}
        for mode in ("heuristic", "embedding"):
            lines, glosses = v20.scored_strings(plan["senses"], plan["selection"]["selected"], mode)
            per_artist[artist][f"{mode}:lines"], per_artist[artist][f"{mode}:glosses"] = lines, glosses

    store = load_cache(cache_path)
    legacy = legacy_vectors(workspace)
    report: dict[str, dict] = {}
    for mode in ("heuristic", "embedding"):
        lines = set().union(*(a[f"{mode}:lines"] for a in per_artist.values()))
        glosses = set().union(*(a[f"{mode}:glosses"] for a in per_artist.values()))
        needed = lines | glosses
        missing = sorted(t for t in needed if t not in store and t not in legacy)
        report[mode] = {
            "lines": len(lines), "glosses": len(glosses),
            "in_store": sum(t in store for t in needed),
            "from_legacy_delta": sum(t in legacy and t not in store for t in needed),
            "to_embed": len(missing),
            "to_embed_lines": sum(t in lines for t in missing),
            "to_embed_glosses": sum(t in glosses and t not in lines for t in missing),
            "characters": sum(len(t) for t in missing),
            "batches": -(-len(missing) // BATCH_SIZE),
            "per_artist_lines": {a: len(v[f"{mode}:lines"]) for a, v in per_artist.items()},
        }
        report[mode]["_missing"] = missing

    print(f"\nEmbedding model {EMBED_MODEL}; store {cache_path.name} holds {len(store):,} vectors; "
          f"legacy delta {len(legacy):,}.")
    for mode, r in report.items():
        marker = "  <- this run" if mode == fallback else ""
        print(f"\nWiktionary senses scored by {mode}{marker}:")
        print(f"  needed: {r['lines']:,} lines + {r['glosses']:,} glosses; in store {r['in_store']:,}; "
              f"from legacy delta {r['from_legacy_delta']:,}")
        print(f"  PROJECTED: {r['to_embed']:,} strings to embed ({r['to_embed_lines']:,} lines, "
              f"{r['to_embed_glosses']:,} glosses), {r['characters']:,} characters "
              f"(~{r['characters'] // 4:,} tokens), {r['batches']:,} requests of {BATCH_SIZE}")
    out = workspace / "reviews/lyrics-v20/embedding-projection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({m: {k: v for k, v in r.items() if k != "_missing"} for m, r in report.items()}
                              | {"fallback": fallback, "model": EMBED_MODEL}, indent=1), encoding="utf-8")

    chosen = report[fallback]
    if not args.spend:
        print(f"\nNo model called. To spend: --spend --confirm {chosen['to_embed']}"
              + (f" --polysemous-fallback {fallback}" if args.polysemous_fallback else ""))
        return
    if args.confirm != chosen["to_embed"]:
        raise SystemExit(f"--confirm {args.confirm} does not match the projection ({chosen['to_embed']}); nothing spent")
    if legacy:
        merged = {**legacy, **store}
        merge_delta(cache_path, merged)
        print(f"Merged {len(merged) - len(store):,} legacy delta vectors into {cache_path.name}.")
    key = os.environ.get("GEMINI_API_KEY") or dotenv_value(v20.REPO_ROOT / ".env", "GEMINI_API_KEY")
    needed = set().union(*(a[f"{fallback}:lines"] | a[f"{fallback}:glosses"] for a in per_artist.values()))
    ensure_embeddings(cache_path, sorted(needed), api_key=key)
    print("Done.")


if __name__ == "__main__":
    main()
