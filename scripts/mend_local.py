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

  menus     one new run per language (es, pt, cs; --language for one).
            Stages 01 and 03 carried from the source run (no corpus scan);
            stage 02 rebuilt with the resolver on for the cards v15 shipped
            empty. Reports every card outside that set whose menu moved.
  wsd       without --go: offline only. Prints how many texts are uncached
            (the projected embedding spend) and stops. With --go: targeted
            WSD for re-resolved cards, then one spliced bundle -- carried
            rows, fresh rows, declared rows -- through the importer.
  release   candidate releases <lang>-speech-v15-mend-10000x10, validated
            and sharded, diffed against v15 per card. Nothing is activated.
  clitics   read-only. Numbers for the Spanish clitic-split decision record:
            what would merge into what, rank shifts, what would enter.
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

DECLARED_ROOT = REPO / "config/declared"
# One refetch file and one surface list per scope. "affected" is the 105;
# "deck" is every kept ledger surface whose page SpanishDict has not answered in
# a form that kept its relation. Each merge writes the next free snapshot id.
REFETCH = {
    "affected": ("refetch-no-menu-v15.surfaces.txt", "refetch-no-menu-v15.jsonl"),
    "deck": ("refetch-lemma-relations.surfaces.txt", "refetch-lemma-relations.jsonl"),
    # Headwords a hand-written entry names that no kept page holds (--words).
    "words": ("refetch-headwords.surfaces.txt", "refetch-headwords.jsonl"),
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


class _Rule:
    """The declared-lemma rule with the speech-scoped hand-written headwords applied."""

    def __init__(self, rule, overrides):
        self.rule, self.overrides = rule, overrides
        self.table_has_moods = rule.table_has_moods

    def resolve(self, surface, page, flags):
        return self.rule.resolve(surface, page, flags, override=self.overrides.get(surface))


def _lemma_rule(ws: Path, snapshot_id: str):
    from fluency.sense_menu.spanishdict_lemmas import SpanishDictLemmaRule
    from fluency.surfaces.declared import Context, DeclaredRegistry

    snap = ws / SD_ROOT / snapshot_id
    cache = _json(snap / "surface_cache.json")
    headwords = _json(snap / "headword_cache.json")
    reverse = _json(snap / "conjugation_reverse.json")
    registry = DeclaredRegistry.load(DECLARED_ROOT, "es")
    speech = Context(language="es", mode="speech")
    overrides = {}
    for surface in registry.surfaces("headwords"):
        found = registry.select(surface, "headwords", speech, "derived")
        if found:
            overrides[found.surface] = found.headwords
    rule = SpanishDictLemmaRule(reverse, known_headwords=frozenset(headwords))
    return _Rule(rule, overrides), cache, reverse


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
    if args.scope == "words":
        if not args.words:
            print("--scope words needs --words w1 w2 ..."); return 1
        out_dir.mkdir(parents=True, exist_ok=True)
        surfaces.write_text("\n".join(args.words) + "\n", encoding="utf-8")
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


# ------------------------------------------------------------- run steps (menus, wsd, release)
#
# One new run per language. Stages 01 and 03 are carried from the source run
# byte-for-byte (the harvest's own reuse path, so nothing is rescanned); stage 02
# is rebuilt with the resolver on for the cards v15 shipped empty; Stage 04 is a
# complete spliced bundle -- carried rows, fresh WSD for the re-resolved cards,
# deterministic rows for declared glosses and entities -- through the importer.

SOURCE_RUNS = {
    "es": "20260914T223348Z-c35194bc",
    "pt": "20260914T222723Z-e43a0469",
    "cs": "20260914T223828Z-ad405a28",
}
CANDIDATE_RELEASE = "{lang}-speech-v15-mend-10000x10"
RUNS_FILE = "mend-runs.json"
NEEDS_WSD = ("headwords", "expansion")
DECLARED_STRATEGIES = ("declared_gloss", "entity")


def _languages(args) -> list[str]:
    return [args.language] if args.language else list(SOURCE_RUNS)


def _release_dir(args, lang: str) -> Path:
    base = args.release.resolve()
    # --release points at es by default; derive the sibling for other languages.
    root = base.parents[2] if base.name.endswith("10000x10") else base
    return root / lang / "speech" / f"{lang}-speech-v15-10000x10"


def _complete_contract(run: Path, stage_dir: str, *, note: str) -> None:
    from fluency.core.hashing import file_content_id as _fid
    contract_path = run / "stages" / stage_dir / "contract.json"
    contract = _json(contract_path)
    manifest = _json(run / "stages" / stage_dir / "output/manifest.json")
    contract.update(status="complete", completed_at=manifest.get("completed_at"),
                    output_directory="output",
                    manifest_content_id=_fid(run / "stages" / stage_dir / "output/manifest.json"),
                    carried_note=note)
    contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _carry_inventory(source: Path, run: Path) -> None:
    import shutil
    src, dst = source / "stages/01_inventory/output", run / "stages/01_inventory/output"
    shutil.copytree(src, dst)
    manifest = _json(dst / "manifest.json")
    manifest["reused_from"] = str(src)
    (dst / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n",
                                       encoding="utf-8")
    _complete_contract(run, "01_inventory", note=f"carried byte-for-byte from {source.name}")


def _carry_harvest(source: Path, run: Path) -> None:
    from fluency.harvest.runner import _reuse_harvest_output
    src = source / "stages/03_sentence_harvest/output"
    manifest = _json(src / "manifest.json")
    _reuse_harvest_output(
        src, run_id=run.name, output_directory=run / "stages/03_sentence_harvest/output",
        started_at=datetime.now(UTC), cache_key=manifest["cache_key"],
        implementation_content_id=manifest["implementation_hash"],
        config_content_id=manifest["config_hash"], inputs=manifest["inputs"])
    _complete_contract(run, "03_sentence_harvest", note=f"reused from {source.name}; no corpus scan")


def _kaikki_snapshot(ws: Path, lang: str, content_id: str, override: Path | None) -> Path:
    """The dump the source run read, found by content hash (never by name)."""
    from fluency.core.hashing import file_content_id as _fid
    if override:
        return override
    roots = [ws / "raw/dictionaries" / lang, ws / "raw/dictionaries", ws / "raw"]
    seen: set[Path] = set()
    tried: list[str] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path in seen or not path.is_file() or path.stat().st_size < 1_000_000:
                continue
            posix = path.as_posix().lower()
            if root != roots[0] and not any(k in posix for k in ("kaikki", "wiktionary", "wiktextract")):
                continue
            seen.add(path)
            tried.append(str(path.relative_to(ws)))
            if _fid(path) == content_id:
                return path
    raise SystemExit(f"{lang}: no file matches {content_id}; tried:\n  " + "\n  ".join(tried[:40])
                     + "\npass --kaikki-snapshot <path>")


def _preflight_spanishdict(snapshot: Path, surfaces: list[str]) -> tuple[dict, list[str]]:
    from fluency.sense_menu.spanishdict_lemmas import SpanishDictHeadwordSource, SpanishDictLemmaRule
    from fluency.surfaces.declared import Context
    from fluency.surfaces.resolver import ModePolicy, Resolver, ResolverError
    from fluency.surfaces.stores import stack
    cache, heads = _json(snapshot / "surface_cache.json"), _json(snapshot / "headword_cache.json")
    rule = SpanishDictLemmaRule(_json(snapshot / "conjugation_reverse.json"), known_headwords=frozenset(heads))
    resolver = Resolver(SpanishDictHeadwordSource(rule, cache, heads), stack(REPO, "es"),
                        Context(language="es", mode="speech"),
                        ModePolicy.load(REPO / "config/surfaces/strategy.json", "speech"))
    found, errors = {}, []
    for surface in surfaces:
        try:
            found[surface] = resolver.resolve(surface)
        except ResolverError as error:
            errors.append(str(error))
    return found, errors


def step_menus(args: argparse.Namespace) -> int:
    from fluency.core.workspace import Workspace
    from fluency.pipeline.planning import create_pipeline_plan
    from fluency.sense_menu.runner import build_sense_menu_stage

    ws = args.workspace.resolve()
    workspace = Workspace.load(ws)
    out_dir = (args.out or ws / "raw/surfaces/es/mend").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    runs_path = out_dir / RUNS_FILE
    runs = _json(runs_path) if runs_path.exists() else {}
    lines = ["# MEND menus — new sense-menu runs, resolver on for the cards v15 shipped empty", ""]
    report: dict[str, Any] = {}
    for lang in _languages(args):
        if lang in runs and not args.force_new_run:
            print(f"{lang}: run {runs[lang]} already built; pass --force-new-run to build another")
            continue
        source = ws / "runs" / lang / "speech" / SOURCE_RUNS[lang]
        # The release lists display forms; the run keys cards by surface key.
        # Match through the source run's own cards, and only those whose menu
        # really was empty there.
        released_empty = {c["surface"].casefold() for c in empty_cards(_release_dir(args, lang))}
        source_menu = _json(source / "stages/02_sense_menu/output/sense-menu.json")["cards"]
        display = {c["card_id"]: c["display_form"] for c in
                   _json(source / "stages/03_sentence_harvest/output/candidates.json")["cards"]}
        affected_cards = [c for c in source_menu if not c["analyses"]
                          and display.get(c["card_id"], c["surface_form"]).casefold() in released_empty]
        surfaces = sorted({c["surface_form"] for c in affected_cards})
        if len(affected_cards) != len(released_empty):
            print(f"{lang}: {len(released_empty)} empty in the release, {len(affected_cards)} matched "
                  "to empty menus in the source run; the difference is reported below")
        source_menu_report = _json(source / "stages/02_sense_menu/output/report.json")
        adapter = source_menu_report["source_adapter"]
        profile = _json(source / "profile.json")
        profile["profile_id"] = f"{profile['profile_id']}-mend"
        # Every card the resolver does not touch is carried from the source
        # run's stage 02, so the ledger's drift since then cannot move it.
        profile["sense_menu"]["resolver"] = {"surfaces": surfaces, "carry_from_run": source.name}
        if adapter.startswith("spanishdict"):
            snapshot_id = args.snapshot or (_mend_snapshots(ws) or [source_menu_report["snapshot_id"]])[-1]
            snapshot = ws / SD_ROOT / snapshot_id
            resolved, errors = _preflight_spanishdict(snapshot, surfaces)
            unfetched = sorted({h for r in resolved.values()
                                for h in (r.notes or {}).get("headwords_without_entry", [])})
            if errors or unfetched:
                print(f"{lang}: resolver preflight failed; no run created:\n  " + "\n  ".join(errors))
                if unfetched:
                    print(f"  headwords the snapshot has no entry for: {' '.join(unfetched)}\n"
                          f"  fetch them with: --step refetch --scope words --words {' '.join(unfetched)}")
                return 1
        else:
            snapshot_id = source_menu_report["snapshot_id"]
            snapshot = _kaikki_snapshot(ws, lang, source_menu_report["snapshot_content_id"],
                                        args.kaikki_snapshot)
        if "snapshot_id" in profile["sense_menu"]:
            profile["sense_menu"]["snapshot_id"] = snapshot_id
        run = create_pipeline_plan(workspace, profile)
        _carry_inventory(source, run)
        _carry_harvest(source, run)
        build_sense_menu_stage(REPO, workspace, run_id=run.name, language=lang, mode="speech",
                               dictionary_snapshot=snapshot, snapshot_id=snapshot_id)
        runs[lang] = run.name
        runs_path.write_text(json.dumps(runs, indent=1) + "\n", encoding="utf-8")

        before = {c["card_id"]: c for c in _json(source / "stages/02_sense_menu/output/sense-menu.json")["cards"]}
        after = {c["card_id"]: c for c in _json(run / "stages/02_sense_menu/output/sense-menu.json")["cards"]}
        affected_ids = {c["card_id"] for c in affected_cards}
        moved = sorted(c["surface_form"] for cid, c in after.items() if cid not in affected_ids
                       and json.dumps(c, sort_keys=True) != json.dumps(before.get(cid), sort_keys=True))
        rows, strategies, classes, still_empty = [], Counter(), Counter(), []
        for cid in sorted(affected_ids, key=lambda i: after[i]["surface_form"]):
            card = after[cid]
            res = card.get("resolution") or {}
            strategies[res.get("strategy")] += 1
            classes[res.get("word_class")] += 1
            if not card["analyses"]:
                still_empty.append(f"{card['surface_form']} ({res.get('reason')})")
            heads = ", ".join(h["headword"] for h in res.get("headwords") or []) or \
                (res.get("entry") or {}).get("entry_id") or "—"
            rows.append(f"| {card['surface_form']} | {len(before.get(cid, {}).get('analyses') or [])} | "
                        f"{len(card['analyses'])} | {res.get('strategy')} | {res.get('word_class')} | {heads} |")
        report[lang] = {"run_id": run.name, "snapshot_id": snapshot_id, "affected": len(affected_ids),
                        "released_empty": len(released_empty),
                        "strategies": dict(strategies), "classes": dict(classes),
                        "still_empty": still_empty, "moved_outside_affected": moved}
        lines += [f"## {lang}: run `{run.name}` (snapshot `{snapshot_id}`)", "",
                  f"- affected cards: {len(affected_ids)}; still empty: {len(still_empty)} {still_empty or ''}",
                  f"- strategies: {dict(strategies)}", f"- classes: {dict(classes)}",
                  f"- cards OUTSIDE the affected set whose menu moved: {len(moved)} {moved[:40] or ''}", "",
                  "| surface | analyses before | after | strategy | class | headwords / entry |",
                  "|---|---:|---:|---|---|---|", *rows, ""]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    md = "\n".join(lines) + "\n"
    (out_dir / f"menus-{stamp}.md").write_text(md, encoding="utf-8")
    (out_dir / f"menus-{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(md)
    print(f"wrote {out_dir / f'menus-{stamp}.md'}")
    return 0


def _multiword_path(ws: Path, content_id: str | None) -> Path | None:
    from fluency.core.hashing import file_content_id as _fid
    if not content_id:
        return None
    for path in sorted((ws / "raw/mwe").rglob("mwe_merged.json")):
        if _fid(path) == content_id:
            return path
    raise SystemExit(f"no raw/mwe/**/mwe_merged.json matches {content_id}")


def _prewsd_dir(ws: Path, lang: str, source_run: str) -> Path:
    for name in (source_run + "-v2", source_run):
        path = ws / "raw/surfaces" / lang / "prewsd" / name
        if (path / "pairs.json").exists():
            return path
    raise SystemExit(f"{lang}: no prewsd for {source_run}")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def step_wsd(args: argparse.Namespace) -> int:
    import subprocess
    from fluency.core.hashing import file_content_id as _fid
    from fluency.core.workspace import Workspace
    from fluency.wsd.importer import import_wsd_assignments
    from fluency.wsd.splice import carried_row, declared_row, write_spliced_bundle

    def say(message: str) -> None:
        print(message, flush=True)

    ws = args.workspace.resolve()
    workspace = Workspace.load(ws)
    out_dir = (args.out or ws / "raw/surfaces/es/mend").resolve()
    runs = _json(out_dir / RUNS_FILE)
    lines = [f"# MEND wsd — {'DRY RUN (offline only, no spend)' if not args.go else 'targeted WSD + splice + import'}", ""]
    for lang in _languages(args):
        run = ws / "runs" / lang / "speech" / runs[lang]
        source = ws / "runs" / lang / "speech" / SOURCE_RUNS[lang]
        menu_path = run / "stages/02_sense_menu/output/sense-menu.json"
        menu = {c["card_id"]: c for c in _json(menu_path)["cards"]}
        resolved = {cid: c for cid, c in menu.items() if c.get("resolution")}
        candidates = _json(run / "stages/03_sentence_harvest/output/candidates.json")
        display = {card["card_id"]: card["display_form"] for card in candidates["cards"]}
        # wsd_execute and the importer both name a card by its display form.
        targets = sorted({display[cid] for cid, c in resolved.items()
                          if c["resolution"]["strategy"] in NEEDS_WSD and c["analyses"]})
        declared = {cid for cid, c in resolved.items() if c["resolution"]["strategy"] in DECLARED_STRATEGIES}
        src4 = source / "stages/04_wsd_assignments/output"
        src_method = _json(src4 / "method.json")["method"]
        src_report = _json(src4 / "report.json")
        mwe = _multiword_path(ws, (src_report.get("input_content_ids") or {}).get("multiword_inventory"))
        bundle_dir = ws / "raw/wsd" / lang
        bundle_dir.mkdir(parents=True, exist_ok=True)
        target_bundle = bundle_dir / f"mend-{run.name}-targets.json"
        lines += [f"## {lang}: run `{run.name}`", "",
                  f"- re-resolved cards needing WSD: {len(targets)}; declared (no model): {len(declared)}; "
                  f"carried from `{source.name}`: all other cards"]
        fresh: list[dict[str, Any]] = []
        method = src_method
        if targets and args.go and target_bundle.exists():
            # wsd_execute already finished for this run (a later step may have
            # crashed); its bundle is reused rather than recomputed.
            say(f"{lang}: reusing finished targets bundle {target_bundle.name}")
            lines += ["", f"- reused finished targets bundle `{target_bundle.name}`"]
        elif targets:
            command = [sys.executable, "-X", "faulthandler", "-m", "fluency.speech.wsd_execute",
                       "--run-dir", str(run), "--out", str(target_bundle),
                       "--profile-id", src_method["profile_id"],
                       "--prewsd", str(_prewsd_dir(ws, lang, source.name)),
                       "--target-surfaces", *targets]
            if mwe:
                command += ["--multiword-inventory", str(mwe)]
            if args.env_file:
                command += ["--env-file", str(args.env_file)]
            if not args.go:
                command.append("--offline-only")
            log_path = bundle_dir / f"mend-{run.name}-targets.log"
            say("$ " + " ".join(command[:14]) + f" ... ({len(targets)} surfaces)  [log: {log_path}]")
            # Streamed, not captured: a crash then shows where it happened, on
            # screen and in the log, instead of taking the output with it.
            output: list[str] = []
            with log_path.open("w", encoding="utf-8") as log, subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                    env={**__import__("os").environ, "PYTHONPATH": str(REPO / "src")}) as process:
                for line in process.stdout:
                    print("  | " + line.rstrip(), flush=True)
                    log.write(line)
                    output.append(line.rstrip())
                returncode = process.wait()
            output = [l for l in output if l]
            keep = [l for l in output if any(k in l for k in (
                "sampling:", "exact texts", "exact-text", "absent from the local embedding cache",
                "newly embedded", "assigned", "not_evaluated", "abstained", "no_menu", "Error", "error"))]
            tail = "\n".join((keep or output)[-14:])
            lines += ["", "```", tail, "```"]
            if returncode != 0:
                lines += ["", f"**{lang}: wsd_execute stopped (exit {returncode}).** "
                          + ("With --offline-only this is the uncached count above: that is the projected "
                             "embedding spend. Say go to run it paid." if not args.go
                             else f"Stop and report; full output in {log_path}.")]
                continue
        if targets:
            bundle = _json(target_bundle)
            fresh = [r for r in bundle["assignments"] if r["surface_form"] in set(targets)]
            method = bundle["method"]
            inputs = bundle["inputs"]
        else:
            stages = run / "stages"
            inputs = {"inventory": _fid(stages / "01_inventory/output/inventory.json"),
                      "sense_menu": _fid(menu_path),
                      "candidates": _fid(stages / "03_sentence_harvest/output/candidates.json"),
                      "sentence_bank": _fid(stages / "03_sentence_harvest/output/sentence-bank.jsonl")}
            if mwe:
                inputs["multiword_inventory"] = _fid(mwe)
        if not args.go and targets:
            lines += ["", f"{lang}: offline run succeeded, so no spend is needed. Rerun with --go to splice and import."]
            continue
        new_menu_id = _fid(menu_path)
        redone = set(resolved)
        # re-resolved cards that still have no menu keep their source rows (no_menu)
        still_empty = {cid for cid in redone if not menu[cid]["analyses"]}
        declared_rows = [declared_row(card_id=card["card_id"], surface_form=card["display_form"],
                                      sentence_id=item["sentence_id"], menu_card=menu[card["card_id"]],
                                      sense_menu_content_id=new_menu_id)
                         for card in candidates["cards"] if card["card_id"] in declared
                         for item in card.get("candidates") or []]
        if not args.go and not targets:
            lines += ["", f"{lang}: nothing needs a model; --go splices the carried rows and "
                      f"{len(declared_rows)} declared rows and imports them."]
            continue

        def carried_rows():
            # One pass, one row at a time: the Spanish source is 2.2 GB and was
            # held several times over when read whole.
            with (src4 / "assignments.jsonl").open(encoding="utf-8", newline="\n") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row["card_id"] not in redone or row["card_id"] in still_empty:
                        yield carried_row(row, source_run_id=source.name, source_method=src_method,
                                          sense_menu_content_id=new_menu_id)

        spliced = bundle_dir / f"mend-{run.name}-spliced.json"
        say(f"{lang}: writing spliced bundle {spliced.name} (streaming carried rows)")
        splice_report = write_spliced_bundle(
            spliced, run_id=run.name, language=lang, mode="speech", inputs=inputs, method=method,
            sampling_policy=(src_report.get("occurrence_sampling") or {}).get("policy") or {},
            carried=carried_rows(), fresh=fresh, declared=declared_rows, progress=say)
        say(f"{lang}: bundle written: {splice_report['rows_by_origin']}; importing")
        (bundle_dir / f"mend-{run.name}-splice-report.json").write_text(json.dumps(
            {**splice_report, "source_run": source.name, "source_method": src_method,
             "fresh_method": method}, ensure_ascii=False, indent=1), encoding="utf-8")
        import_wsd_assignments(workspace, run_id=run.name, language=lang, mode="speech", bundle_path=spliced)
        say(f"{lang}: Stage 04 imported")
        lines += ["", f"- imported Stage 04: {splice_report['rows_by_origin']}; statuses {splice_report['statuses']}"]
    md = "\n".join(lines) + "\n"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    (out_dir / f"wsd-{stamp}.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def _card_rows(app: Path) -> tuple[dict[str, dict], dict[str, dict], dict[str, str]]:
    columns = _json(app / "vocabulary.index.columns.json")
    word = dict(zip(columns["id"], columns["word"]))
    rows: dict[str, dict] = {}
    for path in sorted((app / "vocabulary.index.rows").glob("*.json")):
        rows.update(_json(path))
    examples: dict[str, dict] = {}
    for path in sorted((app / "vocabulary.examples.shards").glob("*.json")):
        examples.update(_json(path))
    return rows, examples, word


def step_release(args: argparse.Namespace) -> int:
    from fluency.core.workspace import Workspace
    from fluency.release.example_shards import shard_app_examples
    from fluency.release.index_shards import shard_app_index
    from fluency.release.run_candidate import build_inactive_run_candidate
    from fluency.release.validation import validate_release_bundle

    ws = args.workspace.resolve()
    workspace = Workspace.load(ws)
    out_dir = (args.out or ws / "raw/surfaces/es/mend").resolve()
    runs = _json(out_dir / RUNS_FILE)
    lines = ["# MEND release — candidate releases (inactive; nothing activated or published)", ""]
    for lang in _languages(args):
        v15 = _release_dir(args, lang)
        composition = _json(v15 / "composition.json")
        params = ((composition.get("layers") or {}).get("wsd_assignments") or {}).get("parameters") or {}
        conj = ((composition.get("layers") or {}).get("conjugations") or {}).get("artifact_id")
        _, old_examples, _ = _card_rows(v15 / "app")
        titled = any("source_title" in (ex.get("metadata") or {})
                     for card in list(old_examples.values())[:200] for group in card.get("m") or []
                     for ex in group)
        release_id = CANDIDATE_RELEASE.format(lang=lang)
        output = build_inactive_run_candidate(
            workspace, run_id=runs[lang], release_id=release_id, language=lang, mode="speech",
            conjugations_artifact_id=conj,
            source_titles_path=(REPO / "app/data/source_titles.json") if titled else None,
            wsd_selection_projection=params.get("selection_projection", "provider_only"),
            wsd_publication_projection=params.get("publication_projection", "forced_leaf"))
        validate_release_bundle(output)
        shard_app_index(output / "app")
        shard_app_examples(output / "app")
        deck = _json(output / "deck.json")
        empty = [c["surface_key"] for c in deck["cards"] if not c.get("meanings")]
        undeclared = [c["surface_key"] for c in deck["cards"] if not c.get("meanings") and not c.get("menu_absence")]
        tagged = Counter(c.get("word_class") for c in deck["cards"] if c.get("word_class"))
        new_rows, new_examples, word = _card_rows(output / "app")
        old_rows, _, _ = _card_rows(v15 / "app")
        affected = {c["card_id"] for c in empty_cards(v15)}
        changed_meanings = sorted(word.get(cid, cid) for cid in new_rows if cid not in affected
                                  and json.dumps(new_rows[cid], sort_keys=True) != json.dumps(old_rows.get(cid), sort_keys=True))
        changed_examples = sorted(word.get(cid, cid) for cid in new_examples if cid not in affected
                                  and json.dumps(new_examples[cid], sort_keys=True) != json.dumps(old_examples.get(cid), sort_keys=True))
        lines += [f"## {lang}: `{release_id}` from run `{runs[lang]}`", "",
                  f"- validated: yes; cards {len(deck['cards'])}; empty meanings {len(empty)} "
                  f"(without a declared absence: {len(undeclared)}) {empty[:20] or ''}",
                  f"- class tags on re-resolved cards: {dict(tagged)}",
                  f"- cards outside the {len(affected)} affected whose meanings changed: {len(changed_meanings)} {changed_meanings[:30] or ''}",
                  f"- cards outside the affected whose examples changed: {len(changed_examples)} {changed_examples[:30] or ''}",
                  "  (examples can move where an affected card now takes a sentence another card had: "
                  "the builder lets at most two cards share one)", ""]
    lines += ["Activation would change: config/config.json and app/config/config.json (index, examples, "
              "study structure, manifest and composition paths), app/data/speech-frequency/<lang>.json "
              "indexSha256, tests/app/test_product_shell.py. SETLIST pins no release id. Not done."]
    md = "\n".join(lines) + "\n"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    (out_dir / f"release-{stamp}.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def step_clitics(args: argparse.Namespace) -> int:
    """Read-only numbers for the Spanish clitic-split proposal (decision record draft).

    Splits every verified enclitic surface in the 10k Spanish inventory into
    its host (as the conjugation table spells it) and its pronouns, merges the
    counts, and reports which cards would merge into which, how the hosts'
    ranks move, and which surfaces from beyond rank 10,000 would enter.
    """
    from fluency.sense_menu.spanishdict_lemmas import SpanishDictLemmaRule

    ws = args.workspace.resolve()
    run = ws / "runs/es/speech" / SOURCE_RUNS["es"]
    report = _json(run / "stages/01_inventory/output/report.json")
    ranks = _json(run / "stages/01_inventory/output/frequency-ranks.json")
    top = report["top_surfaces"]
    count = {row["surface"]: float(row["source_frequency"]) for row in top}
    snapshot_id = _json(run / "stages/02_sense_menu/output/report.json")["snapshot_id"]
    rule = SpanishDictLemmaRule(_json(ws / SD_ROOT / snapshot_id / "conjugation_reverse.json"))
    cache = _json(ws / SD_ROOT / snapshot_id / "surface_cache.json")
    NON_VERB = ("noun", "adjective", "adverb", "preposition", "pronoun", "conjunction",
                "article", "determiner", "numeral", "interjection")

    def is_its_own_word(surface: str) -> str | None:
        """A surface that is a word in its own right is not a clitic bundle.

        seguidos is a participle, pase a subjunctive, palo and finales nouns
        and adjectives: stripping a pronoun-shaped ending from them invents a
        split. Two tests, both SpanishDict's: the surface is itself a form in
        the conjugation table, or its page files it under a non-verb part of
        speech.
        """
        if surface.lower() in rule._exact:
            return "conjugation-table form"
        from fluency.sense_menu.spanishdict_lemmas import headword_key
        page = cache.get(surface) or {}
        for analysis in page.get("dictionary_analyses") or []:
            # Only the surface's own entry says what the surface is: verte's
            # page also shows ver (el ver, a noun), which says nothing about verte.
            if headword_key((analysis or {}).get("headword") or "") != headword_key(surface):
                continue
            for sense in (analysis or {}).get("senses") or []:
                pos = str((sense or {}).get("pos") or "").lower()
                if any(word in pos for word in NON_VERB):
                    return f"SpanishDict files it as {pos}"
        return None

    candidates = [x for x in (rule.enclitic_split(row["surface"]) for row in top) if x]
    guarded = {x["surface"]: why for x in candidates if (why := is_its_own_word(x["surface"]))}
    splits = [x for x in candidates if x["surface"] not in guarded]
    merged = dict(count)
    into: dict[str, list[str]] = defaultdict(list)
    for split in splits:
        merged.pop(split["surface"], None)
        merged[split["host"]] = merged.get(split["host"], 0.0) + count[split["surface"]]
        for pronoun in split["pronouns"]:
            merged[pronoun] = merged.get(pronoun, 0.0) + count[split["surface"]]
        into[split["host"]].append(split["surface"])
    new_order = sorted(merged, key=lambda s: (-merged[s], ranks.get(s, 10**9), s))
    new_rank = {s: i for i, s in enumerate(new_order, start=1)}
    old_rank = {row["surface"]: row["rank"] for row in top}
    hosts_in = [h for h in into if h in old_rank]
    hosts_new = [h for h in into if h not in old_rank]
    freed = len(splits) - len(hosts_new)
    beyond = sorted((s for s, r in ranks.items() if r > len(top)), key=lambda s: ranks[s])[:max(freed, 0)]
    moves = sorted(((old_rank[h], new_rank[h], h, len(into[h])) for h in hosts_in),
                   key=lambda m: m[0] - m[1], reverse=True)
    lines = ["# Spanish clitic split — measured (read-only)", "",
             f"- inventory: {len(top):,} surfaces (run `{run.name}`, snapshot `{snapshot_id}`)",
             f"- verified enclitic surfaces that would split: {len(splits):,} "
             f"(abstained or not enclitic: the rest)",
             f"- not split because the surface is a word in its own right: {len(guarded):,} "
             f"(e.g. {', '.join(f'{k} [{v}]' for k, v in list(guarded.items())[:8])})",
             f"- hosts they merge into: {len(into):,} ({len(hosts_in):,} already cards, "
             f"{len(hosts_new):,} not yet in the 10k)",
             f"- cards removed: {len(splits):,}; cards whose learner progress must migrate: {len(splits):,}",
             f"- slots freed for surfaces beyond rank {len(top):,}: {freed:,} "
             f"(first: {', '.join(beyond[:25])})", "",
             "## Biggest rank gains among existing host cards", "",
             "| host | rank before | rank after | forms merged in |", "|---|---:|---:|---|"]
    for old, new, host, n in moves[:40]:
        lines.append(f"| {host} | {old} | {new} | {', '.join(into[host][:6])}{' …' if n > 6 else ''} |")
    lines += ["", "## Hosts not yet in the 10k (would become cards)", "",
              ", ".join(f"{h} ({len(into[h])})" for h in sorted(hosts_new, key=lambda h: -merged[h])[:80])]
    md = "\n".join(lines) + "\n"
    out_dir = (args.out or ws / "raw/surfaces/es/mend").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    (out_dir / f"clitics-{stamp}.md").write_text(md, encoding="utf-8")
    (out_dir / f"clitics-{stamp}.json").write_text(json.dumps(
        {"splits": splits, "guarded": guarded, "into": into, "freed": freed, "entering": beyond},
        ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(md)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", required=True,
                    choices=["measure", "lemmas", "refetch", "menus", "wsd", "release", "clitics"])
    ap.add_argument("--no-merge", action="store_true", help="refetch: fetch only, do not merge")
    ap.add_argument("--scope", choices=sorted(REFETCH), default="affected",
                    help="refetch: the 105 (merged into a new snapshot) or the deck (evidence only)")
    ap.add_argument("--snapshot", help="SpanishDict snapshot id (default: newest MEND snapshot, else the run's)")
    ap.add_argument("--language", choices=["es", "pt", "cs"], help="menus/wsd/release: one language (default all)")
    ap.add_argument("--words", nargs="+", help="refetch --scope words: headword pages to fetch")
    ap.add_argument("--kaikki-snapshot", type=Path, help="menus: Kaikki dump path, if the search does not find it")
    ap.add_argument("--force-new-run", action="store_true", help="menus: build another run even if one is recorded")
    ap.add_argument("--go", action="store_true", help="wsd: run paid embeddings if needed, then splice and import")
    ap.add_argument("--env-file", type=Path, help="wsd: env file holding GEMINI_API_KEY")
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
    if args.step == "menus":
        return step_menus(args)
    if args.step == "wsd":
        return step_wsd(args)
    if args.step == "release":
        return step_release(args)
    if args.step == "clitics":
        return step_clitics(args)
    print(f"step {args.step!r} is not written yet: it waits on the reviewed measure table. "
          "Pull the branch again when the MEND chat says it is ready.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
