#!/usr/bin/env python3
"""MEND's local steps: run on the machine that holds the workspace.

MEND's code and judgement live in the cloud chat; this script is the part that
needs `../Fluency-Workspace`, the Fluency-Releases clone, or SpanishDict. Each
step prints a short report and writes the same report to disk, then stops. The
local chat pastes the report back; it does not interpret it.

    python scripts/mend_local.py --step measure [--workspace ../Fluency-Workspace]

Steps:
  measure   read-only. The empty-meanings cards of the v15 release, each joined
            to its ledger row, events, snapshot entry, stage-02 quarantine,
            refetch history, Stage 04 statuses and a sample of its lines.
            Proposes a class per card (proposal 0003 §1) and says why the
            menu is empty. Writes nothing but the report.

  lemmas    read-only. Applies the SpanishDict declared-lemma rule
            (fluency.sense_menu.spanishdict_lemmas) to every ledger surface
            and compares it with the ledger's lemma; resolves the 105; writes
            the refetch list and the override queue.
  refetch   network. Asks SpanishDict about the refetch list only, into
            raw/dictionaries/es/spanishdict/refetch-no-menu-v15.jsonl, then
            merges that one file into a NEW snapshot id. Nothing is
            overwritten.

Later steps (menus, wsd, release) are added after review; until then they
refuse to run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.events import by_surface, read, store_path  # noqa: E402
from fluency.surfaces.ledger import ledger_path  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RELEASE_ID = "es-speech-v15-10000x10"
RUN_ID = "20260914T223348Z-c35194bc"  # QUARRY freeze; KILN 2 Stage 04; GLASS release
SD_ROOT = Path("raw/dictionaries/es/spanishdict")

# Same inventory as scripts/resolve_clitic_lemmas.py, longest bundles first.
CLITICS = (
    "melo", "mela", "melos", "melas", "telo", "tela", "telos", "telas",
    "selo", "sela", "selos", "selas", "noslo", "nosla", "noslos", "noslas",
    "oslo", "osla", "oslos", "oslas",
    "nos", "os", "les", "los", "las", "me", "te", "se", "le", "lo", "la",
)
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


# --------------------------------------------------------------------------- io

def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _maybe(path: Path, notes: list[str], label: str) -> Any:
    if not path.exists():
        notes.append(f"missing {label}: {path}")
        return None
    try:
        return _json(path)
    except (OSError, json.JSONDecodeError) as exc:
        notes.append(f"unreadable {label}: {path} ({exc})")
        return None


def deaccent(word: str) -> str:
    out = []
    for ch in unicodedata.normalize("NFD", word):
        if unicodedata.combining(ch) and ch != "̃":
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def clitic_bases(surface: str) -> list[str]:
    """Candidate verb forms once enclitics are removed (as resolve_clitic_lemmas)."""
    stems = {surface}
    for _ in range(3):
        for stem in list(stems):
            for clitic in CLITICS:
                if stem.endswith(clitic) and len(stem) > len(clitic) + 1:
                    stems.add(stem[: -len(clitic)])
    stems.discard(surface)
    seen: list[str] = []
    for stem in sorted(stems, key=len, reverse=True):
        for form in (stem, deaccent(stem), stem + "s", deaccent(stem) + "s"):
            if form and form not in seen:
                seen.append(form)
    return seen


# ------------------------------------------------------------------ release side

def empty_cards(release: Path) -> list[dict[str, Any]]:
    app = release / "app"
    columns = _json(app / "vocabulary.index.columns.json")
    position = {card_id: i for i, card_id in enumerate(columns["id"])}
    manifest = _json(app / "vocabulary.index.manifest.json")
    out = []
    for shard in manifest["shards"]:
        rows = _json(app / shard["path"])
        for card_id, row in rows.items():
            if row.get("meanings"):
                continue
            i = position[card_id]
            out.append({
                "card_id": card_id,
                "surface": columns["word"][i],
                "rank": columns["rank"][i],
                "release_lemma": columns["lemma"][i],
                "set_id": shard["set_id"],
                "unused_menu_senses": len(row.get("unused_menu_senses") or []),
                "wsd_denominator": (row.get("wsd_distribution") or {}).get("denominator"),
            })
    return sorted(out, key=lambda c: c["rank"])


# ---------------------------------------------------------------- workspace side

def refetch_history(sd_root: Path) -> tuple[dict[str, list[dict]], list[dict]]:
    """Every refetch row per word, with where in its file it sits."""
    per_word: dict[str, list[dict]] = defaultdict(list)
    files = []
    for path in sorted(sd_root.glob("refetch-*.jsonl")):
        rows = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        rows.append({"word": None, "_bad": True})
        n = len(rows)
        empties = []
        for i, row in enumerate(rows):
            answered = bool(row.get("analyses") or row.get("possible_results") or row.get("flags"))
            if not answered:
                empties.append(i)
            if row.get("word"):
                per_word[row["word"]].append({
                    "file": path.name, "line": i + 1, "of": n,
                    "analyses": len(row.get("analyses") or []),
                    "possible_results": list(row.get("possible_results") or [])[:5],
                    "flags": row.get("flags") or [],
                    "entry_lang": row.get("entry_lang"),
                })
        empty_set, trailing = set(empties), 0
        while trailing < n and (n - 1 - trailing) in empty_set:
            trailing += 1
        deciles = Counter(min(9, (i * 10) // max(n, 1)) for i in empties)
        files.append({
            "file": path.name, "rows": n,
            "distinct_words": len({r.get("word") for r in rows}),
            "empty_rows": len(empties),
            "empty_by_decile": [deciles.get(d, 0) for d in range(10)],
            "trailing_empty_run": trailing,
        })
    return per_word, files


def stage04_status(run: Path, wanted: set[str], notes: list[str]) -> dict[str, Counter]:
    path = run / "stages/04_wsd_assignments/output/assignments.jsonl"
    out: dict[str, Counter] = defaultdict(Counter)
    if not path.exists():
        notes.append(f"missing Stage 04 assignments: {path}")
        return out
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            card = row.get("card_id")
            if card not in wanted:
                continue
            status = (row.get("assignment_status") or row.get("status")
                      or row.get("decision") or "?")
            out[card][str(status)] += 1
    return out


def prewsd_lines(workspace: Path, notes: list[str]):
    base = workspace / "raw/surfaces/es/prewsd"
    for name in (RUN_ID + "-v2", RUN_ID):
        directory = base / name
        if (directory / "pairs.json").exists():
            examples = _json(directory / "examples.json")
            pairs = _json(directory / "pairs.json")
            return directory.name, examples["columns"], pairs.get("surfaces") or {}
    notes.append(f"missing prewsd for {RUN_ID} under {base}")
    return None, None, {}


def spanish_share(text: str, forms: set[str]) -> float | None:
    tokens = [deaccent(t.lower()) for t in WORD.findall(text)]
    if not tokens or not forms:
        return None
    return sum(t in forms for t in tokens) / len(tokens)


# ------------------------------------------------------------------ classification

def propose_class(card: dict[str, Any]) -> tuple[str, str]:
    """A starting class with the rule that chose it. Josh reviews every one."""
    codes = set(card["event_codes"])
    raw = card["snapshot"]
    shares = [s for s in card["line_spanish_share"] if s is not None]
    if "abbreviation_form" in codes or raw.get("abbreviation_headwords"):
        return "abbreviation", "abbreviation_form event or dotted SpanishDict headword"
    if shares and sum(s < 0.5 for s in shares) * 2 > len(shares):
        return "contamination?", f"{sum(s < 0.5 for s in shares)}/{len(shares)} sampled lines mostly non-Spanish"
    if card["clitic"]["lemmas"]:
        kind = "ambiguous" if len(card["clitic"]["lemmas"]) > 1 else "unique"
        return "attached_clitic", f"base {card['clitic']['base']} -> {'|'.join(card['clitic']['lemmas'])} ({kind})"
    if card["direct_lemmas"]:
        return "ordinary", f"conjugation_reverse -> {'|'.join(card['direct_lemmas'])}"
    if "interjection" in " ".join(raw.get("pos", [])).lower():
        return "interjection", "SpanishDict POS interjection"
    if "capitalised_in_corpus" in codes:
        return "entity?", "capitalised_in_corpus"
    if raw.get("in_spanish_forms"):
        return "ordinary", "in snapshot spanish_forms"
    return "unclassified", "no rule fired"


def why_empty(card: dict[str, Any]) -> str:
    """The mechanism that left the stage-02 menu empty, most specific first."""
    raw = card["snapshot"]
    history = card["refetch"]
    if raw.get("in_surface_cache"):
        if raw.get("entry_lang") not in (None, "", "es"):
            return f"in cache, entry_lang={raw['entry_lang']} (quarantined wrong language)"
        if raw.get("abbreviation_headwords") and raw["abbreviation_headwords"] == raw.get("headwords"):
            return "in cache; every headword dropped by _abbreviation_mismatch"
        if card["quarantine"]:
            return "in cache; filtered: " + ",".join(sorted({q["reason"] for q in card["quarantine"]}))
        if not raw.get("analyses") and raw.get("possible_results_without_headword"):
            return "in cache via merge; possible_results lack 'headword' key (merge format bug)"
        if not raw.get("analyses") and raw.get("possible_results"):
            return "in cache; possible_results only, none found in headword_cache"
        return "in cache; zero analyses"
    if not history:
        return "never asked (not in cache, no refetch row)"
    last = history[-1]
    if any(h["flags"] for h in history):
        return "absent: refetch flagged " + ",".join(sorted({f for h in history for f in h["flags"]}))
    if any(h["analyses"] for h in history):
        return "refetch answered with analyses, but not in the run's snapshot (merged later, or not merged)"
    if any(h["possible_results"] for h in history):
        return "refetch answered possible_results only; merge_spanishdict_refetch skips rows without analyses"
    return f"refetch empty x{len(history)} (last {last['file']} line {last['line']}/{last['of']}); never re-asked"


# -------------------------------------------------------------------------- step

def step_measure(args: argparse.Namespace) -> int:
    notes: list[str] = []
    ws: Path = args.workspace.resolve()
    release: Path = args.release.resolve()
    run = ws / "runs/es/speech" / args.run_id

    cards = empty_cards(release)
    wanted = {c["card_id"] for c in cards}

    menu = _maybe(run / "stages/02_sense_menu/output/sense-menu.json", notes, "stage 02 menu") or {}
    report = _maybe(run / "stages/02_sense_menu/output/report.json", notes, "stage 02 report") or {}
    snapshot_id = menu.get("snapshot_id") or report.get("snapshot_id")
    snap = ws / SD_ROOT / snapshot_id if snapshot_id else None
    surface_cache = _maybe(snap / "surface_cache.json", notes, "surface_cache") if snap else {}
    headword_cache = _maybe(snap / "headword_cache.json", notes, "headword_cache") if snap else {}
    reverse = _maybe(snap / "conjugation_reverse.json", notes, "conjugation_reverse") if snap else {}
    forms_raw = _maybe(snap / "spanish_forms.json", notes, "spanish_forms") if snap else []
    artifact = _maybe(snap / "artifact.json", notes, "snapshot artifact") if snap else {}
    surface_cache, headword_cache, reverse = surface_cache or {}, headword_cache or {}, reverse or {}
    forms = {deaccent(str(f).lower()) for f in (forms_raw or [])}

    heads: dict[str, set[str]] = defaultdict(set)
    for form, entries in reverse.items():
        for entry in entries or []:
            lemma = (entry.get("lemma") or "").strip() if isinstance(entry, dict) else ""
            if lemma:
                heads[form.lower()].add(lemma)

    quarantine_by_surface: dict[str, list[dict]] = defaultdict(list)
    for q in report.get("quarantine") or []:
        quarantine_by_surface[q.get("surface")].append(q)
    menu_status = {c.get("card_id"): len(c.get("analyses") or []) for c in menu.get("cards") or []}

    ledger_doc = _maybe(ledger_path(ws, "es"), notes, "ledger") or {}
    ledger_rows = ledger_doc.get("surfaces") or {}
    events = by_surface(read(store_path(ws, "es")))
    if not events:
        notes.append(f"no events at {store_path(ws, 'es')}")
    per_word, refetch_files = refetch_history(ws / SD_ROOT)
    statuses = stage04_status(run, wanted, notes)
    prewsd_name, ex_cols, pair_surfaces = prewsd_lines(ws, notes)

    for card in cards:
        s = card["surface"]
        entry = surface_cache.get(s) if isinstance(surface_cache.get(s), dict) else None
        analyses = (entry or {}).get("dictionary_analyses") or []
        headwords = sorted({str(a.get("headword") or "") for a in analyses if isinstance(a, dict)})
        pos = sorted({str(sense.get("pos") or "") for a in analyses if isinstance(a, dict)
                      for sense in a.get("senses") or [] if isinstance(sense, dict)})
        possible = [p for p in (entry or {}).get("possible_results") or [] if isinstance(p, dict)]
        card["snapshot"] = {
            "snapshot_id": snapshot_id,
            "in_surface_cache": entry is not None,
            "entry_lang": (entry or {}).get("entry_lang"),
            "merged_from": (entry or {}).get("merged_from"),
            "analyses": len(analyses),
            "headwords": headwords,
            "abbreviation_headwords": [h for h in headwords if "." in h and "." not in s],
            "pos": pos,
            "possible_results": [p.get("headword") or p.get("result") for p in possible][:6],
            "possible_results_without_headword": sum(1 for p in possible if not p.get("headword")),
            "possible_in_headword_cache": [p.get("headword") for p in possible
                                           if p.get("headword") in headword_cache][:6],
            "in_spanish_forms": deaccent(s.lower()) in forms,
            "headword_cache_has_surface": s in headword_cache,
        }
        card["stage02_analyses"] = menu_status.get(card["card_id"])
        card["quarantine"] = quarantine_by_surface.get(s, [])
        row = ledger_rows.get(s) or {}
        card["ledger"] = {k: row.get(k) for k in ("verdict", "reason_codes", "lemma", "lemmas",
                                                   "lemma_provenance", "tags") if k in row}
        card["ledger_present"] = bool(row)
        evs = events.get(s, [])
        card["event_codes"] = sorted({e.get("reason_code") for e in evs})
        card["event_observers"] = sorted({f"{e.get('reason_code')}<-{e.get('observer')}" for e in evs})
        card["refetch"] = per_word.get(s, [])
        card["stage04"] = dict(statuses.get(card["card_id"], {}))
        card["direct_lemmas"] = sorted(heads.get(s.lower(), set()))
        base, lemmas = None, []
        for candidate in clitic_bases(s):
            if candidate.lower() in heads:
                base, lemmas = candidate, sorted(heads[candidate.lower()])
                break
        card["clitic"] = {"base": base, "lemmas": lemmas,
                          "lemma_in_headword_cache": [l for l in lemmas if l in headword_cache]}
        lines, shares = [], []
        pair = pair_surfaces.get(s) or {}
        for index in (pair.get("eligible") or [])[: args.sample]:
            text = ex_cols["target"][index]
            share = spanish_share(text, forms)
            shares.append(share)
            lines.append({"es": text, "en": ex_cols["translation"][index],
                          "spanish_share": None if share is None else round(share, 2)})
        card["eligible_lines"] = len(pair.get("eligible") or [])
        card["lines"] = lines
        card["line_spanish_share"] = shares
        card["proposed_class"], card["class_rule"] = propose_class(card)
        card["why_empty"] = why_empty(card)

    out_dir = (args.out or ws / "raw/surfaces/es/mend").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    document = {
        "report_version": "mend-measure/v1",
        "created_at": stamp,
        "release": str(release), "run_id": args.run_id, "snapshot_id": snapshot_id,
        "snapshot_notes": (artifact or {}).get("notes"),
        "prewsd": prewsd_name,
        "notes": notes,
        "refetch_files": refetch_files,
        "cards": cards,
    }
    json_path = out_dir / f"measure-{stamp}.json"
    json_path.write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")
    md = render_measure(document)
    (out_dir / f"measure-{stamp}.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"\nwrote {json_path}\nwrote {json_path.with_suffix('.md')}")
    return 0


def render_measure(doc: dict[str, Any]) -> str:
    cards = doc["cards"]
    out = [f"# MEND measure — {len(cards)} empty-meanings cards in {RELEASE_ID}", ""]
    out.append(f"run `{doc['run_id']}` · snapshot `{doc['snapshot_id']}` · prewsd `{doc['prewsd']}`")
    for note in doc["notes"]:
        out.append(f"- NOTE: {note}")
    out += ["", "## By proposed class", ""]
    for name, n in Counter(c["proposed_class"] for c in cards).most_common():
        out.append(f"- {name}: {n}")
    out += ["", "## By mechanism (why the menu is empty)", ""]
    for name, n in Counter(re.sub(r"\(last .*?\)|x\d+", "", c["why_empty"]).strip()
                           for c in cards).most_common():
        out.append(f"- {n:3d}  {name}")
    out += ["", "## Refetch files", "",
            "| file | rows | words | empty | empty by decile (first→last) | trailing empty run |",
            "|---|---:|---:|---:|---|---:|"]
    for f in doc["refetch_files"]:
        out.append(f"| {f['file']} | {f['rows']} | {f['distinct_words']} | {f['empty_rows']} | "
                   f"{' '.join(map(str, f['empty_by_decile']))} | {f['trailing_empty_run']} |")
    out += ["", "## Cards", "",
            "| rank | surface | class | rule | why empty | ledger verdict / lemma | events | cache | refetch | lines (es share) |",
            "|---:|---|---|---|---|---|---|---|---|---|"]
    for c in cards:
        led = c["ledger"]
        cache = c["snapshot"]
        refetch = "; ".join(f"{h['file'].removeprefix('refetch-')}:{h['line']}/{h['of']} "
                            f"a{h['analyses']} p{len(h['possible_results'])}"
                            + (f" {','.join(h['flags'])}" if h["flags"] else "")
                            for h in c["refetch"]) or "—"
        lines = " / ".join(f"{l['es'][:50]} ({l['spanish_share']})" for l in c["lines"][:2]) or "—"
        cache_text = ("—" if not cache["in_surface_cache"] else
                      f"a{cache['analyses']} hw={','.join(cache['headwords'][:3])} "
                      f"pos={','.join(cache['pos'][:3])} pr={','.join(map(str, cache['possible_results'][:3]))}")
        out.append("| " + " | ".join(str(x).replace("|", "¦") for x in (
            c["rank"], c["surface"], c["proposed_class"], c["class_rule"], c["why_empty"],
            f"{led.get('verdict')} / {led.get('lemma') or led.get('lemmas') or '—'}",
            ",".join(c["event_codes"]) or "—", cache_text, refetch, lines)) + " |")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ step: lemmas

LEMMA_OVERRIDES = REPO / "config/lemmas/es.json"
# One refetch file and one surface list per scope. "affected" is the 105;
# "deck" is every kept ledger surface whose page SpanishDict has not answered in
# a form that kept its relation. Each merge writes the next free snapshot id.
REFETCH = {
    "affected": ("refetch-no-menu-v15.surfaces.txt", "refetch-no-menu-v15.jsonl"),
    "deck": ("refetch-lemma-relations.surfaces.txt", "refetch-lemma-relations.jsonl"),
}
MEND_SNAPSHOT_PREFIX = "spanishdict-complete-menu-2026-09-23-v"


def _mend_snapshots(ws: Path) -> list[str]:
    root = ws / SD_ROOT
    found = []
    for path in root.glob(MEND_SNAPSHOT_PREFIX + "*"):
        suffix = path.name.removeprefix(MEND_SNAPSHOT_PREFIX)
        if suffix.isdigit() and (path / "artifact.json").exists():
            found.append((int(suffix), path.name))
    return [name for _, name in sorted(found)]


def _snapshot(args: argparse.Namespace, ws: Path, run: Path) -> str:
    """The explicit snapshot, else the newest MEND snapshot, else the run's."""
    if args.snapshot:
        return args.snapshot
    mend = _mend_snapshots(ws)
    return mend[-1] if mend else _json(run / "stages/02_sense_menu/output/report.json")["snapshot_id"]


def _next_snapshot_id(ws: Path) -> str:
    mend = _mend_snapshots(ws)
    last = int(mend[-1].removeprefix(MEND_SNAPSHOT_PREFIX)) if mend else 3
    return f"{MEND_SNAPSHOT_PREFIX}{last + 1}"


def _latest_flags(sd_root: Path) -> dict[str, list[str]]:
    """The flags on each word's most recent refetch row (later files win)."""
    flags: dict[str, list[str]] = {}
    for path in sorted(sd_root.glob("refetch-*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    if row.get("word"):
                        flags[row["word"]] = list(row.get("flags") or [])
    return flags


def _lemma_rule(ws: Path, snapshot_id: str):
    from fluency.sense_menu.spanishdict_lemmas import SpanishDictLemmaRule, load_overrides

    snap = ws / SD_ROOT / snapshot_id
    cache = _json(snap / "surface_cache.json")
    headwords = _json(snap / "headword_cache.json")
    reverse = _json(snap / "conjugation_reverse.json")
    overrides = load_overrides(_json(LEMMA_OVERRIDES) if LEMMA_OVERRIDES.exists() else None)
    rule = SpanishDictLemmaRule(reverse, overrides=overrides, known_headwords=frozenset(headwords))
    return rule, cache, reverse


def _row_as_page(row: dict[str, Any]) -> dict[str, Any]:
    return {"entry_lang": row.get("entry_lang") or "es",
            "dictionary_analyses": [{"headword": a.get("headword") or row["word"]}
                                    for a in row.get("analyses") or []],
            "possible_results": [p if isinstance(p, dict) else {"result": p}
                                 for p in row.get("possible_results") or []]}


def step_lemmas(args: argparse.Namespace) -> int:
    """Read-only: apply the declared-lemma rule and compare it with the ledger."""
    ws = args.workspace.resolve()
    run = ws / "runs/es/speech" / args.run_id
    snapshot_id = _snapshot(args, ws, run)
    rule, cache, reverse = _lemma_rule(ws, snapshot_id)
    flags = _latest_flags(ws / SD_ROOT)
    # Deck-scope refetch rows are never merged into a menu snapshot; they are
    # read here as the page, because they kept the relation the cache lost.
    deck_rows = ws / SD_ROOT / REFETCH["deck"][1]
    fresh = 0
    if deck_rows.exists():
        for line in deck_rows.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("word") and not row.get("flags"):
                    cache[row["word"]] = _row_as_page(row)
                    fresh += 1
    ledger = _json(ledger_path(ws, "es")).get("surfaces") or {}
    empty = {c["surface"]: c for c in empty_cards(args.release.resolve())}

    sample_rows = next((rows for rows in reverse.values() if isinstance(rows, list) and rows), [])
    resolutions, comparison, disagreements = {}, Counter(), []
    for surface, row in ledger.items():
        found = rule.resolve(surface, cache.get(surface), flags.get(surface, ()))
        resolutions[surface] = found
        current = row.get("lemma")
        declared = found.lemma_names
        if declared and current in declared:
            kind = "agrees"
        elif declared and current:
            kind = "differs"
        elif declared:
            kind = "gained"
        elif current:
            kind = "ledger_only"
        else:
            kind = "neither"
        comparison[kind] += 1
        if kind in ("differs", "ledger_only") and row.get("verdict") == "keep":
            disagreements.append({"surface": surface, "rank": row.get("rank"), "kind": kind,
                                  "ledger": current, "ledger_provenance": row.get("lemma_provenance"),
                                  "declared": declared, "status": found.status,
                                  "rejected": list(found.rejected_headwords)})
    disagreements.sort(key=lambda d: (d["rank"] is None, d["rank"] or 0))

    affected = []
    for surface, card in sorted(empty.items(), key=lambda kv: kv[1]["rank"]):
        found = resolutions.get(surface) or rule.resolve(surface, cache.get(surface), flags.get(surface, ()))
        affected.append({"rank": card["rank"], "card_id": card["card_id"], **found.to_dict()})
    refetch = [a["surface"] for a in affected if a["needs_refetch"]]
    queue = [a["surface"] for a in affected if a["status"] in ("no_lemma", "enclitic_ambiguous")
             and not a["needs_refetch"]]
    deck_refetch = sorted((s for s, r in resolutions.items()
                           if r.needs_refetch and (ledger.get(s) or {}).get("verdict") == "keep"),
                          key=lambda s: (ledger[s].get("rank") is None, ledger[s].get("rank") or 0))

    out_dir = (args.out or ws / "raw/surfaces/es/mend").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    document = {
        "report_version": "mend-lemmas/v1", "created_at": stamp, "snapshot_id": snapshot_id,
        "rule_version": affected[0]["rule_version"] if affected else None,
        "conjugation_table": {"forms": len(reverse), "has_moods": rule.table_has_moods,
                              "sample_row": sample_rows[0] if sample_rows else None},
        "overrides": len(rule.overrides),
        "deck_refetch_pages_read": fresh,
        "ledger_surfaces": len(ledger),
        "status_counts": dict(Counter(r.status for r in resolutions.values())),
        "ledger_comparison": dict(comparison),
        "relation_unknown_deckwide": sum(1 for r in resolutions.values() if r.relation_unknown),
        "disagreements": disagreements,
        "affected": affected,
        "refetch_surfaces": refetch,
        "deck_refetch_count": len(deck_refetch),
        "deck_refetch_by_reason": dict(Counter(
            "unfetched" if resolutions[s].page_state == "unfetched"
            else "relation_unknown" if resolutions[s].relation_unknown else "rejected_headword"
            for s in deck_refetch)),
        "override_queue": queue,
    }
    path = out_dir / f"lemmas-{stamp}.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / REFETCH["affected"][0]).write_text("\n".join(refetch) + "\n", encoding="utf-8")
    (out_dir / REFETCH["deck"][0]).write_text("\n".join(deck_refetch) + "\n", encoding="utf-8")

    lines = [f"# MEND lemmas — declared-lemma rule vs ledger ({snapshot_id})", "",
             f"conjugation table: {len(reverse):,} forms, moods present: {rule.table_has_moods}, "
             f"sample row: {document['conjugation_table']['sample_row']}",
             f"overrides: {len(rule.overrides)} · deck refetch pages read: {fresh}", "",
             "## All ledger surfaces", ""]
    lines += [f"- {k}: {v}" for k, v in sorted(document["status_counts"].items())]
    lines += ["", "ledger lemma vs declared lemmas:"]
    lines += [f"- {k}: {v}" for k, v in comparison.most_common()]
    lines += [f"- page relations lost at fetch (deck-wide): {document['relation_unknown_deckwide']}", "",
              f"## Kept surfaces whose ledger lemma is not declared ({len(disagreements)}; first 150)", "",
              "| rank | surface | ledger (provenance) | declared | status | rejected |", "|---:|---|---|---|---|---|"]
    for d in disagreements[:150]:
        lines.append(f"| {d['rank']} | {d['surface']} | {d['ledger']} ({d['ledger_provenance']}) | "
                     f"{', '.join(d['declared']) or '—'} | {d['status']} | {', '.join(d['rejected']) or '—'} |")
    lines += ["", "## The 105", "", "| rank | surface | status | lemmas (provenance) | page | rejected | unknown relation |",
              "|---:|---|---|---|---|---|---|"]
    for a in affected:
        lemmas = ", ".join(f"{l['lemma']} ({l['provenance'].removeprefix('spanishdict-')})" for l in a["lemmas"]) or "—"
        lines.append(f"| {a['rank']} | {a['surface']} | {a['status']} | {lemmas} | {a['page_state']} | "
                     f"{', '.join(a['rejected_headwords']) or '—'} | {', '.join(a['relation_unknown']) or '—'} |")
    lines += ["", f"refetch, the 105 ({len(refetch)}): {' '.join(refetch) or '—'}",
              f"refetch, deck-wide kept surfaces ({len(deck_refetch)}): "
              f"{document['deck_refetch_by_reason']} (list in {REFETCH['deck'][0]})",
              f"override queue ({len(queue)}): {' '.join(queue) or '—'}"]
    md = "\n".join(lines) + "\n"
    path.with_suffix(".md").write_text(md, encoding="utf-8")
    print(md)
    print(f"\nwrote {path}\nwrote {path.with_suffix('.md')}")
    for name, _ in REFETCH.values():
        print(f"wrote {out_dir / name}")
    return 0


# ----------------------------------------------------------------- step: refetch

def step_refetch(args: argparse.Namespace) -> int:
    """Ask SpanishDict about a scope's surface list (written by --step lemmas).

    affected: the 105's surfaces. The file is merged into the next free MEND
      snapshot id, copied from the newest one, so only these surfaces' cache
      entries change -- that snapshot is what the menus step builds from.
    deck: kept surfaces across the ledger. Fetched only, never merged: those
      pages would replace cache entries for cards whose menus must not move.
      The lemmas step reads the file directly as lemma evidence.
    """
    import subprocess

    ws = args.workspace.resolve()
    run = ws / "runs/es/speech" / args.run_id
    out_dir = (args.out or ws / "raw/surfaces/es/mend").resolve()
    list_name, out_name = REFETCH[args.scope]
    surfaces = out_dir / list_name
    if not surfaces.exists() or not surfaces.read_text(encoding="utf-8").strip():
        print(f"no surface list at {surfaces}; run --step lemmas first"); return 1
    wanted = [w for w in surfaces.read_text(encoding="utf-8").split("\n") if w.strip()]
    target = ws / SD_ROOT / out_name
    python = sys.executable
    fetch = [python, str(REPO / "scripts/fetch_spanishdict.py"), "--run-dir", str(run),
             "--surfaces", str(surfaces), "--out", str(target)]
    print("$ " + " ".join(fetch), flush=True)
    if subprocess.call(fetch) != 0:
        return 1
    wanted_set = set(wanted)
    rows = [json.loads(l) for l in target.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("word") in wanted_set]
    flagged = Counter(f.split(":")[0] for r in rows for f in r.get("flags") or [])
    declared = sum(1 for r in rows if any(isinstance(p, dict) and p.get("heuristic") in ("conjugation", "inflection")
                                          for p in r.get("possible_results") or []))
    print(f"\n## {out_name}: {len(rows)} rows for {len(wanted)} surfaces; "
          f"with a declared relation {declared}; flags {dict(flagged)}\n")
    if len(rows) <= 60:
        print("| word | entry_lang | flags | analyses | headwords | possible (relation) |\n|---|---|---|---:|---|---|")
        for row in rows:
            heads = sorted({a.get("headword") or row["word"] for a in row.get("analyses") or []})
            possible = [f"{p.get('headword')} ({p.get('heuristic') or '?'})" if isinstance(p, dict) else f"{p} (?)"
                        for p in row.get("possible_results") or []]
            print(f"| {row['word']} | {row.get('entry_lang')} | {','.join(row.get('flags') or []) or '—'} | "
                  f"{len(row.get('analyses') or [])} | {', '.join(heads[:4]) or '—'} | {', '.join(possible[:4]) or '—'} |")
    if args.scope == "deck" or args.no_merge:
        print("\nnot merged (deck scope is lemma evidence only)" if args.scope == "deck" else "\nnot merged")
        return 0
    base = _snapshot(args, ws, run)
    out_id = _next_snapshot_id(ws)
    merge = [python, str(REPO / "scripts/merge_spanishdict_refetch.py"), "--workspace", str(ws),
             "--snapshot", base, "--out-id", out_id, "--refetch", out_name]
    print("\n$ " + " ".join(merge), flush=True)
    return subprocess.call(merge)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", required=True,
                    choices=["measure", "lemmas", "refetch", "menus", "wsd", "release"])
    ap.add_argument("--no-merge", action="store_true", help="refetch: fetch only, do not merge")
    ap.add_argument("--scope", choices=sorted(REFETCH), default="affected",
                    help="refetch: the 105 (merged into a new snapshot) or the deck (evidence only)")
    ap.add_argument("--snapshot", help="SpanishDict snapshot id (default: newest MEND snapshot, else the run's)")
    ap.add_argument("--workspace", type=Path, default=REPO.parent / "Fluency-Workspace")
    ap.add_argument("--release", type=Path,
                    default=Path("/private/tmp/fluency-releases/es/speech") / RELEASE_ID)
    ap.add_argument("--run-id", default=RUN_ID)
    ap.add_argument("--sample", type=int, default=6, help="lines sampled per card")
    ap.add_argument("--out", type=Path, help="report directory (default <ws>/raw/surfaces/es/mend)")
    args = ap.parse_args()
    if args.step == "measure":
        return step_measure(args)
    if args.step == "lemmas":
        return step_lemmas(args)
    if args.step == "refetch":
        return step_refetch(args)
    print(f"step {args.step!r} is not written yet: it waits on the reviewed measure table. "
          "Pull the branch again when the MEND chat says it is ready.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
