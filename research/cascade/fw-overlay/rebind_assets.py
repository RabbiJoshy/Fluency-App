#!/usr/bin/env python3
"""Bind the app's release-tied side files to a function-word overlay release.

The overlay release differs from the live one only by the `function_word` field on
some cards (checked here first: same cards, same rows otherwise, same examples).
So the side files' content stays valid and only their binding moves:

- cognates are rebound by scripts/rebind_cognates.py (it adds scores only for new pairs);
- merge exceptions, BRIDGE, speech frequency, estimation pool and dictionary examples are copied with the
  binding fields pointed at the new release and a `rebound_from` note saying why.

Writes app files named <live file>-fw1 and prints the config paths to use.

    rebind_assets.py --language pt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
APP = REPO / "app"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import overlay  # noqa: E402

NAME = {"pt": "portuguese", "es": "spanish", "cs": "czech"}
EXTRACT_UNUSED = {"pt": "raw/wiktionary/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl",
           "cs": "raw/wiktionary/enwiktionary-2026-09-06/kaikki.org-dictionary-Czech.jsonl"}


KNOWN_EXTRACT = {"es": "raw/wiktionary/enwiktionary-2026-09-13/kaikki.org-dictionary-Spanish.jsonl",
                 "pl": "raw/wiktionary/enwiktionary-2026-09-09/kaikki.org-dictionary-Polish.jsonl"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def live_path(rel: str) -> str:
    """The live file a config path was rebound from (config may already name an -fwN copy)."""
    stem, ext = rel.rsplit(".", 1)
    return f"{re.sub(r'-fw[0-9]+$', '', stem)}.{ext}"


def suffixed(rel: str) -> str:
    stem, ext = rel.rsplit(".", 1)
    return f"{stem}-{overlay.TAG}.{ext}"


def check_identity(old: Path, new: Path) -> None:
    a = json.loads((old / "app/vocabulary.index.json").read_text())
    b = json.loads((new / "app/vocabulary.index.json").read_text())
    key = lambda c: c.get("id") or c.get("card_id") or c.get("word")
    A, B = {key(c): c for c in a}, {key(c): {k: v for k, v in c.items() if k != "function_word"} for c in b}
    if A != B:
        raise SystemExit("overlay index differs from the live one beyond function_word; rebuild, do not rebind")
    ea = json.loads((old / "app/vocabulary.examples.json").read_text())
    eb = json.loads((new / "app/vocabulary.examples.json").read_text())
    strip = lambda ex: {k: v for k, v in ex.items() if k != "metadata"} | {
        "metadata": {k: v for k, v in (ex.get("metadata") or {}).items() if k != "function_word"}}
    for cid, card in ea.items():
        other = eb.get(cid) or {}
        if [[strip(x) for x in g] for g in card.get("m") or []] != [[strip(x) for x in g] for g in other.get("m") or []]:
            raise SystemExit(f"examples differ for {cid} beyond function_word labels")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--language", required=True, choices=sorted(NAME))
    ap.add_argument("--workspace", type=Path, default=REPO.parent / "Fluency-Workspace")
    args = ap.parse_args()
    ws, lang = args.workspace.resolve(), args.language
    cfg = json.loads((APP / "config/config.json").read_text())["languages"][NAME[lang]]
    old_rel = "releases/" + overlay.LIVE_RELEASE[lang]  # the live release, whatever config points at now
    old_id = old_rel.rsplit("/", 1)[1]
    new_id = overlay.release_id(lang)
    new_rel = old_rel.rsplit("/", 1)[0] + "/" + new_id
    old_dir, new_dir = ws / old_rel, ws / new_rel
    check_identity(old_dir, new_dir)
    new_index = new_dir / "app/vocabulary.index.json"
    note = {"from_release": old_id, "why": "function-word overlay: cards, senses and examples identical; "
                                           "only function_word labels added (research/cascade/fw-overlay)"}
    paths = {}

    def rebind(field, update):
        src = cfg.get(field)
        if not src:
            return
        src = live_path(src)
        data = json.loads((APP / src).read_text())
        update(data)
        data["rebound_from"] = note
        dest = suffixed(src)
        (APP / dest).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
        paths[field] = dest

    rebind("frequencyPath", lambda d: d.update(indexPath=f"{new_rel}/app/vocabulary.index.json", indexSha256=sha(new_index)))
    rebind("estimationPoolPath", lambda d: d.update(release=f"{new_rel}/app/vocabulary.index.json"))
    rebind("dictionaryExamplesPath", lambda d: d.update(release_id=new_id, index_sha256=sha(new_index)))
    rebind("bridgePath", lambda d: d.update(built_from_release_id=new_id))

    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    # Merge exceptions are copied, not rebuilt: the live list was built from a separate fresh
    # menu (SEAM), so a rebuild from the run menu would change 1,611 pt keys. Cards are identical.
    sys.path.insert(0, str(REPO / "src"))
    from fluency.core.hashing import file_content_id
    rebind("mergeExceptionsPath", lambda d: d.update(release_id=new_id, release_index_content_id=file_content_id(new_index)))
    own = old_dir / "app/merge-exceptions.json"  # the release's own copy, rebound the same way
    if own.exists():
        data = json.loads(own.read_text())
        data.update(release_id=new_id, release_index_content_id=file_content_id(new_index), rebound_from=note)
        (new_dir / "app/merge-exceptions.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")

    cog_src = live_path(cfg["cognatesPath"])
    cog = json.loads((APP / cog_src).read_text())
    cog_out = suffixed(cog_src)
    cmd = [sys.executable, str(REPO / "scripts/rebind_cognates.py"), "--language", lang,
           "--committed", str(APP / cog_src),
           "--previous-index", str(ws / "releases" / lang / "speech" / cog["built_from_release_id"] / "app/vocabulary.index.json"),
           "--release-index", str(new_index), "--release-id", new_id, "--out", str(APP / cog_out)]
    for known in cog.get("known_languages") or ["en"]:
        cmd += ["--known", known if known == "en" else f"{known}={ws / KNOWN_EXTRACT[known]}"]
    subprocess.run(cmd, check=True, env=env)
    paths["cognatesPath"] = cog_out

    for field in ("indexPath", "examplesPath", "studyStructurePath", "releaseManifestPath",
                  "releaseCompositionPath", "conjugationsPath"):
        if cfg.get(field, "").startswith(old_rel + "/") or cfg.get(field, "").startswith(new_rel + "/"):
            paths[field] = cfg[field].replace(old_rel + "/", new_rel + "/")
    print(json.dumps({NAME[lang]: paths}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
