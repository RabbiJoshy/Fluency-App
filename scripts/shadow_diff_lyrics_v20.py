"""Shadow diff of lyrics v19 against v20 menus, per card, before any v20 release.

v19's menus are v19's own: its ``plant_artist`` runs unmodified and is stopped
at its first budgeting call, after the tier chain has built every card's
menu; the menus are read from its frame. Its inflector is wrapped so each
sense keeps the gloss it had before inflection. v20's menus come from
``plant_artist_v20.plan_artist``. Senses are compared on (headword,
uninflected gloss), so a display inflection is not counted as a change.

Writes, under ``<workspace>/reviews/lyrics-v20/shadow-diff/``:
  ``<artist>.jsonl``   one row per card that changed
  ``unresolved-<artist>.json``  surfaces the resolver could not answer
  ``summary.json``     counts by reason, samples of each

    PYTHONPATH=src python scripts/shadow_diff_lyrics_v20.py --artist all
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = REPO_ROOT.parent / "Fluency-Workspace"
OUT = WORKSPACE / "reviews/lyrics-v20/shadow-diff"
FORM_OF = re.compile(
    r"\b(?:form|plural|inflection|conjugation|participle|gerund|feminine|masculine|diminutive|"
    r"augmentative|superlative|spelling|abbreviation|contraction)\s+(?:form\s+)?of\b"
    r"|\b(?:first|second|third)-person\b.*\bof\b",
    re.IGNORECASE)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Stop(Exception):
    pass


def v19_menus(v19, artist: str) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """Run v19's plant up to its menus; return (cards, senses) as v19 built them."""
    real = v19.inflect_card_senses

    def keep_base(surface, lemma, senses, conj_rev, is_plural=False):
        out = real(surface, lemma, senses, conj_rev, is_plural=is_plural)
        for before, after in zip(senses, out):
            after["_base"] = before.get("translation") or before.get("gloss") or ""
        return out

    def stop(*_args, **_kwargs):
        raise _Stop

    v19.inflect_card_senses = keep_base
    v19.calculate_target_occurrence_budget = stop
    src = v19_source(artist)
    try:
        v19.plant_artist(artist, src, OUT / "unused", WORKSPACE, REPO_ROOT)
    except _Stop as captured:
        tb = captured.__traceback__
        while tb is not None:
            if tb.tb_frame.f_code.co_name == "plant_artist":
                frame = tb.tb_frame.f_locals
                return frame["resolved_cards"], frame["resolved_senses_by_card"]
            tb = tb.tb_next
    raise RuntimeError("v19 plant_artist finished without reaching its budgeting step")


def v19_source(artist: str) -> Path:
    import plant_artist_v20 as v20
    return v20.source_dir(WORKSPACE, artist)


def v19_route(senses: list[dict]) -> str:
    if not senses:
        return "v19:empty"
    s = senses[0]
    src, sid = str(s.get("source", "")), str(s.get("sense_id", ""))
    if sid.startswith("override:"):
        return "v19:hardcoded_override"
    if src == "overlay:elision":
        return "v19:declared_elision"
    if src == "overlay:entity/v1":
        return "v19:declared_entity"
    if src.startswith("overlay:"):
        return "v19:declared_gloss"
    if src == "entity:wikipedia":
        return "v19:wikipedia_entity"
    if src == "spanishdict":
        return "v19:spanishdict_page"
    if src == "spanishdict:headword_borrow":
        return "v19:spanishdict_headword_borrow"
    if src == "wiktionary":
        return "v19:wiktionary_glosses"
    if src.startswith("retained_fallback"):
        return "v19:" + src.replace(":", "_")
    return "v19:" + src


def v20_route(card: dict, menu) -> str:
    r = menu.resolution
    if card.get("menu_status") == "no_menu":
        return f"v20:no_menu({card['resolution']['reason']})"
    if r.strategy in ("headwords", "expansion"):
        relations = "+".join(sorted({h.relation for h in r.headwords}))
        named = r.notes.get("named_by")
        crossed = f",named_by={named}" if named and named != menu.provider else ""
        return f"v20:{r.strategy}:{menu.provider}[{relations}{crossed}]"
    return f"v20:{r.strategy}"


def _declared(src: str) -> bool:
    return src.startswith(("overlay:", "curated:", "declared:", "entity:", "retained_fallback", "no_menu"))


def sense_key(s: dict, base_field: str) -> tuple[str, str]:
    head = "<declared>" if _declared(str(s.get("source", ""))) else str(s.get("headword", "")).casefold()
    return head, str(s.get(base_field) or s.get("translation") or "").strip().casefold()


def headword_set(senses: list[dict]) -> set[str]:
    return {str(s.get("headword", "")).casefold() for s in senses if not _declared(str(s.get("source", "")))}


def diff_artist(v19, v20, artist: str) -> dict[str, Any]:
    old_cards, old_senses = v19_menus(v19, artist)
    plan = v20.plan_artist(artist, workspace=WORKSPACE)
    rank = {item["id"]: i for i, item in enumerate(plan["source"]["index"], start=1)}
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    sense_totals = Counter()
    for cid, new in plan["senses"].items():
        resolved = plan["resolved"]["cards"][cid]
        menu = resolved["menu"]
        old = old_senses.get(cid, [])
        old_keys = {sense_key(s, "_base"): s for s in old}
        new_keys = {sense_key(s, "gloss_base"): s for s in new if s["source"] != "no_menu"}
        old_heads, new_heads = headword_set(old), headword_set([s for s in new if s["source"] != "no_menu"])
        gained = [k for k in new_keys if k not in old_keys]
        lost = [k for k in old_keys if k not in new_keys]
        route = f"{v19_route(old)} -> {v20_route(plan['cards'][cid], menu)}"
        if not gained and not lost:
            counts["unchanged"] += 1
            kind = "unchanged"
        else:
            kind = "headwords_changed" if old_heads != new_heads else "senses_changed"
            counts[kind] += 1
        flags = []
        if any(FORM_OF.search(k[1]) for k in lost):
            flags.append("form_of_gloss_dropped")
        if any(FORM_OF.search(k[1]) for k in gained):
            flags.append("form_of_gloss_added")
        lemma_added = sorted(h.headword for h in menu.resolution.headwords
                             if h.relation in ("form", "enclitic") and h.headword.casefold() not in old_heads)
        if lemma_added:
            flags.append("lemma_added")
        sense_totals["gained"] += len(gained)
        sense_totals["lost"] += len(lost)
        sense_totals["headwords_added"] += len(new_heads - old_heads)
        sense_totals["headwords_removed"] += len(old_heads - new_heads)
        row = {
            "card_id": cid, "rank": rank.get(cid), "word": plan["cards"][cid].get("word"),
            "kind": kind, "route": route, "flags": flags,
            "headwords_added": sorted(new_heads - old_heads), "headwords_removed": sorted(old_heads - new_heads),
            "senses_gained": [f"{h}: {g}" for h, g in gained], "senses_lost": [f"{h}: {g}" for h, g in lost],
            "v19": [f"{s.get('headword')} {s.get('pos')}: {s.get('translation')} [{s.get('source')}]" for s in old],
            "v20": [f"{s.get('headword')} {s.get('pos')}: {s.get('translation')} [{s.get('source')}]" for s in new],
            "resolution": v20.resolution_record(menu),
        }
        if kind != "unchanged":
            rows.append(row)
        if plan["cards"][cid].get("menu_status") == "no_menu":
            providers = menu.resolution.notes.get("providers") or {}
            unresolved.append({
                "card_id": cid, "rank": rank.get(cid), "word": row["word"],
                "reason": plan["cards"][cid]["resolution"]["reason"],
                "providers": {p: {k: v.get(k) for k in ("coverage", "headwords", "headwords_without_entry", "page_state")}
                              for p, v in providers.items()},
                "card_flags": {k: plan["source"]["master"][cid].get(k) for k in
                               ("extra_category", "is_english", "is_propernoun", "is_noise", "is_interjection")},
                "v19_route": v19_route(old),
                "v19_meaning": row["v19"][:3],
            })
    rows.sort(key=lambda r: r["rank"] or 10**9)
    unresolved.sort(key=lambda r: r["rank"] or 10**9)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / f"{artist}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (OUT / f"unresolved-{artist}.json").write_text(json.dumps(unresolved, ensure_ascii=False, indent=1), encoding="utf-8")
    by_route = Counter(r["route"] for r in rows)
    by_flag = Counter(f for r in rows for f in r["flags"])
    samples: dict[str, list] = defaultdict(list)
    for r in rows:
        if len(samples[r["route"]]) < 4:
            samples[r["route"]].append({k: r[k] for k in ("rank", "word", "headwords_added", "headwords_removed", "v19", "v20")})
    return {"artist": artist, "cards": len(plan["senses"]), "kinds": dict(counts),
            "totals": dict(sense_totals), "by_route": dict(by_route.most_common()),
            "by_flag": dict(by_flag.most_common()), "unresolved": len(unresolved),
            "unresolved_by_reason": dict(Counter(u["reason"] for u in unresolved).most_common()),
            "strategies": dict(Counter(v20_route(plan["cards"][c], plan["resolved"]["cards"][c]["menu"]).split("[")[0]
                                       for c in plan["senses"]).most_common()),
            "samples": samples}


def main() -> None:
    parser = argparse.ArgumentParser(description="Shadow diff of lyrics v19 vs v20 menus")
    parser.add_argument("--artist", default="all")
    args = parser.parse_args()
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import spacy
    real_load = spacy.load
    loaded: dict[str, Any] = {}
    spacy.load = lambda name, *a, **k: loaded.setdefault(name, real_load(name, *a, **k))
    v19 = _load("plant_artist_v19", REPO_ROOT / "scripts/plant_artist_v19.py")
    import plant_artist_v20 as v20
    artists = v20.ARTISTS if args.artist == "all" else (args.artist,)
    summary_path = OUT / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    for artist in artists:
        summary[artist] = diff_artist(v19, v20, artist)
        OUT.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        s = summary[artist]
        print(f"\n[{artist}] {s['cards']:,} cards: {s['kinds']}  totals {s['totals']}  unresolved {s['unresolved']}")


if __name__ == "__main__":
    main()
