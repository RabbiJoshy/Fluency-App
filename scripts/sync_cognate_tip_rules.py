#!/usr/bin/env python3
"""Copy each pair's memory-tip rules into the cognate maps the app ships.

The rules live in ``config/cognates/<target>-<known>.json`` beside the scorer's
own settings, and a fresh build writes them into the map. A rule edit should
not need a rescore, so this rewrites only the ``tip_rules`` key of every map
that ``app/config/config.json`` points a language at, leaving the scores alone.

    python scripts/sync_cognate_tip_rules.py          # write
    python scripts/sync_cognate_tip_rules.py --check  # exit 1 if any map is stale
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
POLICIES = ROOT / "config" / "cognates"


def shipped_maps() -> list[Path]:
    config = json.loads((APP / "config" / "config.json").read_text(encoding="utf-8"))
    paths = {
        APP / language["cognatesPath"]
        for language in config["languages"].values()
        if language.get("cognatesPath")
    }
    return sorted(paths)


def tip_rules_for(payload: dict) -> dict[str, list]:
    out = {}
    for code in payload.get("known_languages") or []:
        policy = POLICIES / f"{payload['language']}-{code}.json"
        if not policy.exists():
            continue
        rules = json.loads(policy.read_text(encoding="utf-8")).get("tip_rules") or []
        if rules:
            out[code] = rules
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report stale maps without writing")
    args = parser.parse_args()
    stale = []
    for path in shipped_maps():
        payload = json.loads(path.read_text(encoding="utf-8"))
        rules = tip_rules_for(payload)
        if payload.get("tip_rules", {}) == rules:
            continue
        stale.append(path.relative_to(ROOT))
        if args.check:
            continue
        if rules:
            payload["tip_rules"] = rules
        else:
            payload.pop("tip_rules", None)
        # The maps are written compact with sorted keys; matching that keeps
        # the diff to the one key that changed.
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        path.write_text(text + "\n", encoding="utf-8")
    for path in stale:
        print(f"{'stale' if args.check else 'updated'}: {path}")
    return 1 if args.check and stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
