#!/usr/bin/env python3
"""Ask SpanishDict about surfaces its cached snapshot does not cover.

The recovered snapshot holds a 7,297-entry surface cache against a 10,000-card
deck and shipped without an HTTP client. SpanishDict supplies the sense menus,
so it is also the authority on Spanish lemmas: where the cache is silent the
answer should come from SpanishDict rather than from a different dictionary
that may name a headword SpanishDict has never heard of.

Request discipline follows the original builder: one page at a time, 0.35s
apart, Retry-After honoured on 429 and 503, and ?langFrom=es to force
Spanish-source mode -- without it SpanishDict guesses direction from the
surface and returns a backwards entry for words like "has" or "dice".

Two answers are recorded but withheld from use. A spelling substitution means
SpanishDict has no entry and answered about a different word: the page says so
in data-spelling_suggestion_was_requested, and because these surfaces come from
a corpus-derived frequency list they are real words, so a suggestion always
means "no entry" and never "you misspelt it". An English entry means it
answered in the wrong language. Both are evidence about the surface; neither is
a lemma.

    python scripts/fetch_spanishdict.py --run-dir <run> [--surfaces list.txt]
"""

from __future__ import annotations

import argparse, json, os, re, signal, sys, time
from pathlib import Path
from urllib.parse import quote

import requests

COMPONENT = re.compile(r"SD_COMPONENT_DATA\s*=\s*(\{.*?\});", re.S)
SPELLING_REQUESTED = re.compile(r'data-spelling_suggestion_was_requested="(\w+)"')
SPELLING_SUGGESTION = re.compile(r'data-spelling_suggestion="([^"]*)"')
STOP = False


def _stop(signum, frame):
    global STOP
    STOP = True
    print("\n  stopping after the current word; rerun to resume", flush=True)


signal.signal(signal.SIGINT, _stop)


def human(seconds: float) -> str:
    seconds = int(max(seconds, 0))
    h, m = divmod(seconds // 60, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{seconds % 60:02d}s"


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "Fluency SpanishDict cache builder/1.0",
                      "Accept-Language": "en-US,en;q=0.9"})
    return s


def spelling_substitution(html: str) -> str | None:
    requested = SPELLING_REQUESTED.search(html)
    if not requested or requested.group(1).lower() != "true":
        return None
    suggested = SPELLING_SUGGESTION.search(html)
    return suggested.group(1) if suggested else "?"


def fetch(s: requests.Session, word: str) -> dict | None:
    url = f"https://www.spanishdict.com/translate/{quote(word)}?langFrom=es"
    for attempt in range(5):
        try:
            response = s.get(url, timeout=20)
            response.raise_for_status()
            match = COMPONENT.search(response.text)
            if not match:
                return None
            return {"component": json.loads(match.group(1)),
                    "substituted": spelling_substitution(response.text)}
        except requests.HTTPError as exc:
            code = getattr(exc.response, "status_code", None)
            if code in (429, 503):
                after = (getattr(exc.response, "headers", {}) or {}).get("Retry-After")
                try:
                    wait = min(int(after), 60) if after else min(5 * 2**attempt, 60)
                except ValueError:
                    wait = min(5 * 2**attempt, 60)
                print(f"  {code}; waiting {wait}s", flush=True)
                time.sleep(wait)
                continue
            return None
        except requests.RequestException:
            time.sleep(min(3 * 2**attempt, 30))
    return None


def rows_from(component: dict) -> tuple[list[dict], list[str], str]:
    props = component.get("sdDictionaryResultsProps") or {}
    entry = props.get("entry") or {}
    lang = props.get("entryLang") or entry.get("entryLang") or "es"
    rows = []
    for nd in entry.get("neodict") or []:
        for group in nd.get("posGroups") or []:
            for sense in group.get("senses") or []:
                part = ((sense.get("partOfSpeech") or {}).get("nameEn")) or ""
                for tr in sense.get("translations") or []:
                    rows.append({
                        "headword": (sense.get("subheadword") or "").strip(),
                        "translation": (tr.get("translation") or "").strip(),
                        "part": part,
                        "context": (sense.get("context") or "").strip(),
                        "regions": [r.get("nameEn", "") for r in
                                    (sense.get("regions") or []) + (tr.get("regions") or [])
                                    if r.get("nameEn")]})
    possible = []
    for item in component.get("dictionaryPossibleResults") or []:
        heuristic = (item.get("resultHeuristic") or "").strip()
        source = (item.get("wordSource") or "").strip()
        result = (item.get("result") or "").strip()
        head = source if heuristic in {"conjugation", "inflection"} and source else (result or source)
        if head:
            possible.append(head)
    return rows, possible, lang


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--surfaces", type=Path,
                    help="newline-separated surfaces; defaults to the run's menu-less cards")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--delay", type=float, default=0.35)
    ap.add_argument("--every", type=int, default=100)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    if args.surfaces:
        wanted = [w.strip() for w in args.surfaces.read_text(encoding="utf-8").splitlines() if w.strip()]
    else:
        stages = args.run_dir / "stages"
        menu = json.loads((stages / "02_sense_menu/output/sense-menu.json").read_text())
        inv = json.loads((stages / "01_inventory/output/inventory.json").read_text())
        form = {c["card_id"]: c["display_form"] for c in inv["cards"]}
        wanted = [form[c["card_id"]] for c in menu.get("cards", [])
                  if not (c.get("analyses") or c.get("headword_analyses") or [])
                  and c["card_id"] in form]
    if args.limit:
        wanted = wanted[: args.limit]

    out = args.out or (args.run_dir.resolve().parents[3]
                       / "raw/dictionaries/es/spanishdict/refetch-menuless.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.open(encoding="utf-8"):
            try:
                row = json.loads(line)
                if row.get("analyses") or row.get("possible_results") or row.get("flags"):
                    done.add(row["word"])     # an empty is a blip and is retried
            except Exception:
                pass
    todo = [w for w in wanted if w not in done]
    print(f"surfaces {len(wanted):,}  already answered {len(done):,}  to fetch {len(todo):,}")
    print(f"pacing {args.delay}s -> about {human(len(todo) * (args.delay + 0.02))}\n")
    if not todo:
        return 0

    s = session()
    started = time.time()
    empty = 0
    with out.open("a", encoding="utf-8") as fh:
        for i, word in enumerate(todo, 1):
            if STOP:
                break
            t0 = time.time()
            payload = fetch(s, word) or {}
            if STOP and not payload:
                print(f"  {word} interrupted mid-request; left for the resume", flush=True)
                break
            rows, possible, lang = (rows_from(payload["component"])
                                    if payload.get("component") else ([], [], ""))
            flags = []
            if lang and lang != "es":
                flags.append("entry_lang_not_spanish")
            if payload.get("substituted"):
                flags.append(f"spelling_substitution:{payload['substituted']}")
            usable = [] if flags else rows
            if not usable and not possible:
                empty += 1
            fh.write(json.dumps({"word": word, "entry_lang": lang, "flags": flags,
                                 "analyses": usable,
                                 "rejected_analyses": rows if flags else [],
                                 "possible_results": possible}, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            time.sleep(max(0.0, args.delay - (time.time() - t0)))
            if i % args.every == 0 or i == len(todo):
                elapsed = time.time() - started
                rate = i / elapsed
                left = (len(todo) - i) / rate if rate else 0
                print(f"  {i:>5,}/{len(todo):,} ({100*i/len(todo):5.1f}%)  {rate:4.1f}/s  "
                      f"elapsed {human(elapsed)}  left {human(left)}  "
                      f"eta {time.strftime('%H:%M', time.localtime(time.time()+left))}  "
                      f"nothing {empty}", flush=True)
    print(f"\nwrote {out}\nran {human(time.time()-started)}; {empty} returned nothing")
    if STOP:
        print("stopped early -- rerun to resume")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
