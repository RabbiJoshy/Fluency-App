#!/usr/bin/env python3
"""Rebuild one artist's lyric deck from Jev's per-line sense decisions.

Everything before WSD is the v20 plan (menus with the per-headword cap lifted,
and the lines chosen for them), run by docs/audits/bad-bunny-jev-2026-11-01/run_jev.py.
Only cards with several senses change; one-sense cards are copied from the base
release byte for byte.

- NONE stands whenever it is Jev's choice. DECIDE's floor of P(NONE) >= 0.8 is not
  used: on a sample of the 1,511 lines below it, the forced sense was mostly wrong
  (te va a gustar -> "to look", a través de -> "traverse").
- A NONE line leaves its card, and stays in wsd-evidence.json.
- A card with every line NONE keeps its lines and withholds a meaning, in the
  same form as a card with no dictionary entry (menu_status "no_menu").
- Runner-up senses at >= 0.5 x the top sense are recorded as ties.
- A sense the base release already shows keeps its base release gloss.

    python scripts/plant_artist_jev.py --review <run dir> --release-id lyrics-bad-bunny-v21-jev-1
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT.parent / "Fluency-Workspace"
sys.path.insert(0, str(REPO_ROOT / "src"))

from fluency.artist.release import LYRICS_COMPOSITION_VERSION, LYRICS_MANIFEST_VERSION, validate_lyrics_release  # noqa: E402
from fluency.core.hashing import file_content_id  # noqa: E402
from fluency.lyrics.assemble import _validate_split  # noqa: E402

LYRICS = WORKSPACE / "releases" / "lyrics"
BASE_RELEASE = "lyrics-all-artists-v20-1"
MODEL = "jev-1.14.0"
RUN_TS = "2026-11-01T22:00Z"
GARBLED = re.compile(r"yoursel(f|ves)|you!$|^(he/she|they|I|you|we) .*(oneself|himself)")
TIE_RATIO = 0.5


def band(p: float) -> str:
    return "high" if p >= 0.70 else ("medium" if p >= 0.50 else "low")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def line_decisions(run: Path) -> dict[str, dict[str, dict]]:
    """card id -> Spanish line -> {sense_id or None, p, p_none, margin, ties}."""
    out: dict[str, dict[str, dict]] = {}
    for req in read(run / "requests.json"):
        state = req["body"]["state"]
        answers = read(run / "responses" / f"{req['request_id']}.json")["answers"]
        for sid, text in state["sentences"].items():
            probs = answers[sid].get("probabilities") or {}
            choice, p_none = answers[sid].get("choice"), probs.get("NONE", 0.0)
            senses = sorted(((p, k) for k, p in probs.items() if k != "NONE"), reverse=True)
            none = choice in (None, "NONE")
            top = senses[0] if none and senses else (probs.get(choice, 0.0), choice) if not none else (0.0, "1")
            rest = [s for s in senses if s[1] != top[1]]
            out.setdefault(req["card_id"], {})[text.replace("<<", "").replace(">>", "")] = {
                "sense_id": None if none else state["menu"][top[1]]["sense_id"],
                "p": round(top[0], 4), "p_none": round(p_none, 4),
                "margin": round(top[0] - rest[0][0], 4) if rest else None,
                "ties": [state["menu"][k]["sense_id"] for p, k in rest if p >= TIE_RATIO * top[0]],
            }
    return out


def plant(run: Path, release_id: str, slug: str) -> None:
    base = LYRICS / BASE_RELEASE / "app" / "Artists" / "es" / slug
    plan = read(run.parent / "plan.json")
    live_master, live_examples = read(base / "vocabulary_master.json"), read(base / "examples.json")
    live_index, live_evidence = read(base / "index.json"), read(base / "wsd-evidence.json")
    decisions = line_decisions(run)
    master, examples, index, stats = {}, {}, [], Counter()
    glosses_new = []
    for item in live_index:
        cid = item["id"]
        card, live = plan[cid], live_master[cid]
        if cid not in decisions:
            master[cid], examples[cid] = live, live_examples[cid]
            index.append(item)
            continue
        shown = {s["sense_id"]: s for s in live["senses"]}
        # The plan re-inflects from today's code, which garbles clitic forms the
        # base release shows plainly (paraos "he/she stops yourselves"). Where the
        # two disagree on a card, its new senses take the plain dictionary gloss.
        garbled = any(s["sense_id"] in shown and s["translation"] != shown[s["sense_id"]]["translation"]
                      for s in card["senses"])
        menu = [shown.get(s["sense_id"]) or ({**s, "translation": s["gloss_base"]}
                                             if s.get("gloss_base") and (garbled or GARBLED.search(s["translation"])) else s)
                for s in card["senses"]]
        buckets = {s["sense_id"]: [] for s in menu}
        kept_lines, dropped = [], []
        for ex in card["examples"]:
            d = decisions[cid][ex["spanish"]]
            line = {**ex, "assignment_method": MODEL, "prompt_id": MODEL, "run_ts": RUN_TS,
                    "confidence": d["p"], "band": band(d["p"]), "margin": d["margin"]}
            if d["sense_id"] is None:
                dropped.append(line)
            else:
                buckets[d["sense_id"]].append(line)
                kept_lines.append(line)
        stats["lines_assigned"] += len(kept_lines)
        stats["lines_none"] += len(dropped)
        entry = {k: v for k, v in item.items() if k not in ("sense_methods", "sense_model_proposed")}
        if kept_lines:
            active = [s for s in menu if buckets[s["sense_id"]]]
            parts = [buckets[s["sense_id"]] for s in active]
            chosen = Counter()
            for s, b in zip(active, parts):
                if s["source"] in ("spanishdict", "wiktionary") and s["headword"] in live.get("headwords", ()):
                    chosen[s["headword"]] += len(b)
            lemma = chosen.most_common(1)[0][0] if chosen else live.get("lemma")
            master[cid] = {**live, "lemma": lemma, "senses": active}
            for s in active:
                if s["sense_id"] not in shown and s["translation"] != s.get("gloss_base"):
                    glosses_new.append((card["surface"], s["translation"], s.get("gloss_base")))
        else:
            # Every line NONE: declared absence, not a forced sense (invariant 2).
            stats["cards_withheld"] += 1
            active = [{"headword": card["surface"], "pos": "X", "translation": "", "gloss_base": "",
                       "context": "no listed meaning fits these lines", "source": "no_menu",
                       "sense_id": f"no_menu:{card['surface']}"}]
            parts = [dropped]
            master[cid] = {**live, "lemma": card["surface"], "senses": active, "menu_status": "no_menu",
                           "resolution": {**(live.get("resolution") or {}), "reason": "jev_none_all_lines"}}
        tot = sum(len(b) for b in parts)
        conf = [round(sum(x["confidence"] for x in b) / len(b), 4) for b in parts]
        counts = {s["sense_id"][:4]: len(b) for s, b in zip(active, parts)}
        entry.update({
            "sense_frequencies": [round(len(b) / tot, 4) for b in parts],
            "sense_confidence": conf, "sense_band": [band(c) for c in conf],
            "sense_prompt_ids": [MODEL] * len(active), "sense_run_ts": [RUN_TS] * len(active),
            "wsd_distribution": {**item["wsd_distribution"], "denominator": tot, "forced_leaf_counts": counts,
                                 "known_leaf_mass": tot, "published_leaf_counts": counts,
                                 "status_counts": {"assigned": tot}, "supported_unavailable_mass": tot},
        })
        index.append(entry)
        examples[cid] = {"m": parts, "w": live_examples[cid].get("w", [])}
    evidence = {**live_evidence, "source_kind": f"lyrics_wsd_{MODEL}", "profile_id": MODEL, 
                "tie_ratio": TIE_RATIO, "base_release": BASE_RELEASE}
    evidence["cards"] = dict(live_evidence["cards"])
    by_id = {r["id"]: r for r in index}
    for cid, lines in decisions.items():
        rows = []
        for b, (sense, bucket) in enumerate(zip(master[cid]["senses"], examples[cid]["m"])):
            for e, ex in enumerate(bucket):
                d = lines[ex["spanish"]]
                rows.append({"decision_id": f"decision_{cid}_{b}_{e}",
                             "forced_selection": {"selected_tuple": {"headword": sense["headword"], "part_of_speech": sense["pos"]},
                                                  "sense_id": sense["sense_id"]},
                             "provenance": {"assignment_method": MODEL, "run_ts": RUN_TS, "probability": d["p"],
                                            "none_probability": d["p_none"], "margin": d["margin"], "ties": d["ties"]},
                             "subject": {"bucket_index": b, "example_index": e, "kind": "materialized_example"}})
        evidence["cards"][cid] = {**live_evidence["cards"][cid], "decisions": rows, "distribution": by_id[cid]["wsd_distribution"],
                                  "lemma": master[cid].get("lemma", ""),
                                  "none_lines": [{"spanish": k, **v} for k, v in lines.items() if v["sense_id"] is None]}
    evidence["decision_count"] = sum(len(c["decisions"]) for c in evidence["cards"].values())
    _validate_split(index, examples, master)
    package(release_id, slug, base, {"index.json": index, "examples.json": examples,
                                     "vocabulary_master.json": master, "wsd-evidence.json": evidence})
    print(dict(stats), "new inflected glosses:", len(glosses_new))
    (run / "new-inflected-glosses.json").write_text(json.dumps(glosses_new, ensure_ascii=False, indent=0), encoding="utf-8")


def package(release_id: str, slug: str, base: Path, docs: dict) -> None:
    root = LYRICS / release_id
    if root.exists():
        raise SystemExit(f"{root} already exists; releases are immutable, use a new id")
    deck = root / "app" / "Artists" / "es" / slug
    deck.mkdir(parents=True)
    for name, doc in docs.items():
        (deck / name).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(base / "songs.json", deck / "songs.json")
    shutil.copy2(base / "albums.json", deck / "albums.json")
    shutil.copytree(base / "Images", deck / "Images")
    app = root / "app"
    shutil.copy2(base.parents[1] / "spotify_tracks.json", app / "Artists" / "spotify_tracks.json")
    catalog = read(REPO_ROOT / "app/config/artists.json")
    (app / "config").mkdir()
    (app / "config/artists.json").write_text(
        json.dumps({slug: {**catalog[slug], "releaseId": release_id}}, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat()
    ids = {k: file_content_id(deck / f) for k, f in (("index", "index.json"), ("examples", "examples.json"),
                                                     ("master", "vocabulary_master.json"), ("wsd_evidence", "wsd-evidence.json"))}
    source_id = f"{MODEL}_{slug}_{RUN_TS[:10]}"
    composition = {
        "artists": [{"assignment_bridge_status": "forced_leaf_preserved_supported_specificity_not_recorded",
                     "card_count": len(docs["index.json"]), "example_card_count": len(docs["index.json"]),
                     "examples_content_id": ids["examples"], "index_content_id": ids["index"], "language": "es",
                     "master_content_id": ids["master"], "migration_status": "lyrics_v21_jev_decisions",
                     "name": catalog[slug].get("name", slug), "slug": slug,
                     "song_count": len(read(deck / "songs.json").get("songs", [])), "source_id": source_id,
                     "wsd_evidence_content_id": ids["wsd_evidence"]}],
        "composition_version": LYRICS_COMPOSITION_VERSION, "conflict_policy": "error", "created_at": now,
        "fallback_policy": "none", "layers": {f"artist:{slug}": {"artifact_ids": ids, "requires": {}, "source_id": source_id,
                                                                 "source_type": "lyrics_jev_plant"}},
        "mode": "lyrics", "omitted_layers": [], "publication_status": "candidate_release", "release_id": release_id,
        "wsd_profile": MODEL,
    }
    (root / "composition.json").write_text(json.dumps(composition, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "artist_count": 1, "assignment_status": "lyrics_jev_per_line", "card_count": len(docs["index.json"]),
        "catalog_content_id": file_content_id(app / "config/artists.json"), "catalog_path": "app/config/artists.json",
        "composition_content_id": file_content_id(root / "composition.json"), "composition_path": "composition.json",
        "created_at": now, "languages": ["es"], "manifest_version": LYRICS_MANIFEST_VERSION, "mode": "lyrics",
        "files": [{"path": f"app/{p.relative_to(app).as_posix()}", "bytes": p.stat().st_size, "content_id": file_content_id(p)}
                  for p in sorted(app.rglob("*")) if p.is_file() and not p.name.startswith(".")],
        "publication_status": "candidate_release", "release_id": release_id,
        "supported_specificity_status": "not_recorded_in_materialized_sources",
    }
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    m, _ = validate_lyrics_release(root)
    print(f"[VALIDATED] {release_id}: {m['card_count']:,} cards, {len(m['files'])} files")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--review", type=Path, required=True, help="run dir holding requests.json and responses/")
    ap.add_argument("--release-id", required=True)
    ap.add_argument("--artist", default="bad-bunny")
    args = ap.parse_args()
    plant(args.review, args.release_id, args.artist)


if __name__ == "__main__":
    main()
