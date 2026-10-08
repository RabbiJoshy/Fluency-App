"""Read release cards the way a learner sees them, for the UNISON audit.

Joins one speech release (index rows + example shards) with the WSD run that
built it (stage 02 full menu, stage 04 per-sentence evidence) for a chosen set
of cards, and applies the app's own display rules through ``display.mjs``.

Cards: the top ``--top`` by rank (chunks t01..), ``--random`` more drawn from
the ranks below with ``--seed`` (chunks r01..), and any ``--extra`` surfaces
(chunk s01). Chunks hold 25 cards.

Writes under ``<workspace>/reviews/unison/<release_id>/``:

  cards.jsonl         one structured record per card (display + menu + evidence)
  view-<chunk>.txt    the card as displayed, with v23's choice per example
  blind-<chunk>.txt   the panel sample: sentence + full menu, v23's choice hidden
  blind-key.jsonl     sample id -> sentence and menu labels -> senses (no v23 choice)
  v23-choice.jsonl    sample id -> the sense v23 shows; open only after labelling

The blind files exist so the random panel is labelled without seeing what v23
chose (PROGRESS.md, 2026-10-08). Nothing here writes to the release or the run.

  python research/unison/cards.py --language es --extra darte,irte,estuve
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE = ROOT.parent / "Fluency-Workspace"
RELEASES = {"es": "es-speech-v23-10000x30-slim", "pt": "pt-speech-v23-10000x30-slim"}
CHUNK = 25
SAMPLE_PER_CARD = 3
# Metadata families the card shows as pills (card-metadata-pills.js senseMetadataItems).
PILL_FAMILIES = {"companion", "construction", "register", "domain", "grammar", "functional", "source_qualifier"}
LEVEL_TIER = {"leaf": 1, "glosskey": 2, "tuple": 3}


def load_json(path: Path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def provider_sense_id(ref: str | None) -> str | None:
    """'spanishdict-menu:sí:e54' -> 'e54'; 'kaikki:en-tu-pt-pron-X' -> 'en-tu-pt-pron-X'."""
    if not ref:
        return None
    if ref.startswith("kaikki:"):
        return ref[len("kaikki:"):]
    return ref.rsplit(":", 1)[-1]


def meaning_key(meaning: dict) -> str | None:
    """A menu identity for a release meaning. Merged phrase senses all carry the
    generic reference 'mwe-merged/v1', so they are keyed by expression and gloss."""
    ref = meaning.get("source_reference")
    if not ref or ref.startswith("mwe-merged"):
        return f"mwe:{meaning.get('headword', '')}|{meaning.get('translation') or ''}"
    return ref


def sample_key(seed: str, sentence_id: str) -> str:
    return hashlib.sha256(f"{seed}:{sentence_id}".encode()).hexdigest()


def select_cards(columns: dict, top: int, extra_random: int, seed: str, extra_words: list[str]):
    rank_of = {cid: int(rank) for cid, rank in zip(columns["id"], columns["rank"])}
    by_rank = sorted(rank_of, key=rank_of.get)
    chosen: list[tuple[str, str]] = []  # (chunk, app card id)
    for i, cid in enumerate(by_rank[:top]):
        chosen.append((f"t{i // CHUNK + 1:02d}", cid))
    pool = by_rank[top:]
    drawn = sorted(random.Random(seed).sample(pool, extra_random), key=rank_of.get) if extra_random else []
    for i, cid in enumerate(drawn):
        chosen.append((f"r{i // CHUNK + 1:02d}", cid))
    taken = {cid for _, cid in chosen}
    word_index = {w: cid for cid, w in zip(columns["id"], columns["word"])}
    for word in extra_words:
        cid = word_index.get(word)
        if cid is None:
            raise SystemExit(f"--extra {word!r} is not a card in this release")
        if cid not in taken:
            chosen.append(("s01", cid))
            taken.add(cid)
    return chosen, rank_of


def load_release_cards(app: Path, wanted: set[str], rank_of: dict) -> dict:
    manifest = load_json(app / "vocabulary.examples.manifest.json")
    shard_of_rank = []
    for shard in manifest["shards"]:
        shard_of_rank.append((shard["start_rank"], shard["end_rank"], shard["set_id"], shard["path"]))
    needed = defaultdict(set)
    for cid in wanted:
        rank = rank_of[cid]
        for start, end, set_id, path in shard_of_rank:
            if start <= rank <= end:
                needed[(set_id, path)].add(cid)
                break
    cards = {}
    for (set_id, path), cids in needed.items():
        rows = load_json(app / "vocabulary.index.rows" / f"{set_id}.json")
        examples = load_json(app / path)
        for cid in cids:
            cards[cid] = {"row": rows[cid], "ex_m": examples.get(cid, {}).get("m", [])}
    return cards


def load_menu(run: Path, full_ids: set[str]) -> dict:
    menu = load_json(run / "stages/02_sense_menu/output/sense-menu.json")
    return {card["card_id"]: card for card in menu["cards"] if card["card_id"] in full_ids}


def load_evidence(run: Path, full_ids: set[str]) -> dict:
    """card_id -> sentence_id (no prefix) -> compact stage 04 evidence."""
    out: dict[str, dict] = defaultdict(dict)
    marker = '"card_id":"'
    with open(run / "stages/04_wsd_assignments/output/assignments.jsonl", encoding="utf-8") as handle:
        for line in handle:
            at = line.find(marker)
            if at < 0:
                continue
            end = line.find('"', at + len(marker))
            if line[at + len(marker):end] not in full_ids:
                continue
            row = json.loads(line)
            ev = row.get("evidence") or {}
            prep = ev.get("candidate_preparation") or {}
            proj = (row.get("selection_projections") or {}).get("provider_only") or {}
            scores = sorted(ev.get("gloss_scores") or [], key=lambda s: -float(s.get("score") or 0))
            runner = next((s for s in scores if s.get("sense_id") != row.get("selected_sense_id")), None)
            sid = str(row.get("sentence_id", "")).removeprefix("sentence_")
            out[row["card_id"]][sid] = {
                "status": row.get("status"),
                "decision_kind": row.get("decision_kind"),
                "level": row.get("emitted_level"),
                "selected": row.get("selected_sense_id"),
                "analysis": row.get("menu_analysis_id"),
                "margin": proj.get("raw_margin"),
                "runner_up": runner.get("sense_id") if runner else None,
                "reflexive": prep.get("reflexive_tag"),
                "carried": bool((ev.get("carried") or {}).get("from_run")),
            }
    return out


def run_display(language: str, items: list[dict]) -> dict:
    result = subprocess.run(
        ["node", str(Path(__file__).with_name("display.mjs"))],
        input=json.dumps({"language": language, "items": items}),
        capture_output=True, text=True, check=True,
    )
    return {card["card_id"]: card for card in json.loads(result.stdout)}


def pills(meaning: dict) -> list[str]:
    features = (((meaning.get("metadata") or {}).get("sense_metadata") or {}).get("features")) or []
    out = []
    for feature in features:
        if feature.get("family") in PILL_FAMILIES and feature.get("value"):
            label = f"{feature['family']}:{feature['value']}"
            if label not in out:
                out.append(label)
    return out[:5]


def single_sentence(text: str) -> bool:
    return not re.search(r"[.!?…]\s+\S", text.strip())


def display_order(examples: list[dict]) -> list[dict]:
    """displayExamplesForSense without personalisation: English, one sentence, confidence, order."""
    def tier(ex):
        w = ex.get("w") or []
        if len(w) > 1 and w[1] == 1:
            return 0
        return LEVEL_TIER.get(w[0] if w else None, 9)
    gated = [ex for ex in examples if (ex.get("w") or [None])[0] in LEVEL_TIER and ex.get("t") and ex.get("e")]
    rest = [ex for ex in examples if ex not in gated]
    ranked = sorted(enumerate(gated), key=lambda p: (not p[1].get("e"), not single_sentence(p[1]["t"]), tier(p[1]), p[0]))
    return [ex for _, ex in ranked] + rest


def menu_entries(menu_card: dict | None, release_row: dict) -> list[dict]:
    """The card's full menu in provider order, plus the phrase senses the release carries."""
    entries = []
    for analysis in (menu_card or {}).get("analyses", []):
        for sense in analysis.get("senses", []):
            ctx = (sense.get("provider_metadata") or {}).get("context") or ""
            entries.append({
                "menu_analysis_id": analysis["menu_analysis_id"],
                "sense_id": sense["sense_id"],
                "headword": analysis.get("headword", ""),
                "pos": analysis.get("part_of_speech", ""),
                "translation": sense.get("translation") or "",
                "context": ctx if isinstance(ctx, str) else "; ".join(map(str, ctx)),
                "ref": sense.get("source_reference"),
            })
    seen = {e["ref"] for e in entries}
    for m in release_row.get("meanings", []) + release_row.get("unused_menu_senses", []):
        key = meaning_key(m)
        if key in seen:
            continue
        seen.add(key)
        evidence = ((m.get("metadata") or {}).get("multiword_evidence") or [{}])[0]
        if key.startswith("mwe:"):
            entries.append({
                "menu_analysis_id": evidence.get("menu_analysis_id") or m.get("menu_analysis_id"),
                "sense_id": m.get("sense_id"),
                "headword": m.get("headword", ""),
                "pos": "PHRASE",
                "translation": m.get("translation") or "",
                "context": m.get("context") or "",
                "ref": key,
            })
        else:
            # A release sense the stage 02 menu does not hold (e.g. a resolved lemma).
            entries.append({
                "menu_analysis_id": m.get("menu_analysis_id"),
                "sense_id": provider_sense_id(m.get("source_reference")),
                "headword": m.get("headword", ""),
                "pos": m.get("pos", ""),
                "translation": m.get("translation") or "",
                "context": m.get("context") or "",
                "ref": key,
            })
    for i, entry in enumerate(entries, 1):
        entry["label"] = f"m{i}"
    return entries


def fmt_pct(value) -> str:
    return "—" if value is None else f"{round(float(value) * 100)}%"


def evidence_tag(ex: dict, ev: dict | None) -> str:
    w = ex.get("w") or []
    level = {"leaf": "L", "glosskey": "G", "tuple": "T"}.get(w[0] if w else None, "?")
    bits = [level + ("✓" if len(w) > 1 and w[1] == 1 else "")]
    if ev:
        if ev.get("margin") is not None:
            bits.append(f"{float(ev['margin']):.2f}")
        if ev.get("reflexive"):
            bits.append(ev["reflexive"])
    return "[" + " ".join(bits) + "]"


def build(language: str, workspace: Path, top: int, extra_random: int, seed: str, extra_words: list[str]) -> Path:
    release_id = RELEASES[language]
    release_dir = workspace / "releases" / language / "speech" / release_id
    app = release_dir / "app"
    run_id = load_json(release_dir / "manifest.json")["wsd"]["source_id"]
    run = workspace / "runs" / language / "speech" / run_id
    columns = load_json(app / "vocabulary.index.columns.json")
    chosen, rank_of = select_cards(columns, top, extra_random, seed, extra_words)
    info = {cid: (w, lemma, full) for cid, w, lemma, full in
            zip(columns["id"], columns["word"], columns["lemma"], columns["surface_card_id"])}
    wanted = {cid for _, cid in chosen}
    full_ids = {info[cid][2] for cid in wanted}

    release = load_release_cards(app, wanted, rank_of)
    menus = load_menu(run, full_ids)
    evidence = load_evidence(run, full_ids)
    display = run_display(language, [
        {"card_id": cid, "word": info[cid][0], "meanings": release[cid]["row"]["meanings"],
         "ex_m": release[cid]["ex_m"], "unused_menu_senses": release[cid]["row"].get("unused_menu_senses", [])}
        for cid in wanted
    ])

    out_dir = workspace / "reviews" / "unison" / release_id
    out_dir.mkdir(parents=True, exist_ok=True)
    views: dict[str, list[str]] = defaultdict(list)
    blinds: dict[str, list[str]] = defaultdict(list)
    keys, choices, records = [], [], []
    sample_counter: dict[str, int] = defaultdict(int)

    for chunk, cid in chosen:
        word, lemma, full_id = info[cid]
        rank = rank_of[cid]
        row = release[cid]["row"]
        shown = display[cid]
        ev_by_sentence = evidence.get(full_id, {})
        by_release_sense = {m["sense_id"]: m for m in row["meanings"] + row.get("unused_menu_senses", [])}
        example_by_id = {}
        for bucket_index, bucket in enumerate(release[cid]["ex_m"]):
            for ex in bucket:
                example_by_id[ex.get("i")] = (bucket_index, ex)
        menu = menu_entries(menus.get(full_id), row)
        label_of_ref = {e["ref"]: e["label"] for e in menu}

        # --- the card as displayed ---------------------------------------
        main = [m for m in shown["main"] if not m["expression_child"]]
        expressions = [m for m in shown["main"] if m["expression_child"]]
        rare = [m for m in shown["rare"] if not m["expression_child"] and (m["translation"] or m["example_ids"])]
        n_examples = sum(len(b) for b in release[cid]["ex_m"])
        flags = []
        if shown["dropped"]:
            flags.append(f"dropped-empty-translation={shown['dropped']}")
        if shown["drift"]:
            flags.append("EXAMPLE-BUCKET-DRIFT")
        if shown["grammar_card"]:
            flags.append("grammar-card")
        split_card_of = {}
        if shown.get("split"):
            split = shown["split"]
            flags.append(f"SPLIT-{split['kind']}: " + " | ".join(
                f"C{n} {c['label']}" for n, c in enumerate(split["cards"], 1)))
            for n, c in enumerate(split["cards"], 1):
                for ref in c["refs"]:
                    split_card_of[ref] = f"C{n} "
            # buildSplitCardPair: a reading with no main-card sense shows the whole card again.
            main_refs = {m["ref"] for m in shown["main"] if not m["expression_child"]}
            for n, c in enumerate(split["cards"], 1):
                if not main_refs & set(c["refs"]):
                    flags.append(f"SPLIT-EMPTY-C{n}(repeats whole card)")
        lines = [f"#{rank} {word}  [card {cid} · lemma {lemma}]  examples {n_examples} · rows {len(main)} · "
                 f"rarer {len(rare)} · expressions {len(expressions)}" + (f"  !! {' '.join(flags)}" if flags else "")]
        sections: dict[tuple, list[dict]] = defaultdict(list)
        for m in main:
            sections[(m["pos"], m["headword"])].append(m)
        ordered = sorted(sections.items(), key=lambda kv: -sum(x["shown_share"] or 0 for x in kv[1]))
        for (pos, headword), members in ordered:
            total = sum(x["shown_share"] or 0 for x in members)
            lines.append(f"  {pos} {headword} — {fmt_pct(total)}")
            for m in sorted(members, key=lambda x: -(x["shown_share"] or 0)):
                source_meaning = by_release_sense.get(m["sense_id"], {})
                chips = pills(source_meaning)
                label = label_of_ref.get(meaning_key(source_meaning), "?")
                merged = f" (merged {len(m['merged_sense_ids'])})" if m["merged_sense_ids"] else ""
                lines.append(f"    · {split_card_of.get(m['ref'], '')}{m['translation']}" + (f"  ⟨{m['context']}⟩" if m["context"] else "")
                             + f"  {fmt_pct(m['shown_share'])} {label}{merged}"
                             + (f"  {{{', '.join(chips)}}}" if chips else "") + f"  ex {len(m['example_ids'])}")
                exs = [example_by_id[i][1] for i in m["example_ids"] if i in example_by_id]
                for n, ex in enumerate(display_order(exs), 1):
                    lines.append(f"        {n}. {ex.get('t', '')} | {ex.get('e', '')}  "
                                 f"{evidence_tag(ex, ev_by_sentence.get(ex.get('i')))} {str(ex.get('i'))[:8]}")
        if rare:
            lines.append("  Rarer uses:")
            # Unused menu senses with no sentence are summarised per headword;
            # the blind file and cards.jsonl keep every one of them.
            idle = [m for m in rare if not m["low_share"] and not m["example_ids"]]
            for m in rare:
                if m in idle:
                    continue
                why = "low share" if m["low_share"] else "unused"
                source_meaning = by_release_sense.get(m["sense_id"], {})
                label = label_of_ref.get(meaning_key(source_meaning), "?")
                lines.append(f"    · {m['pos']} {m['headword']} · {m['translation'] or '(no translation)'}"
                             + (f"  ⟨{m['context']}⟩" if m["context"] else "") + f"  [{why}] {label}  ex {len(m['example_ids'])}")
                exs = [example_by_id[i][1] for i in m["example_ids"] if i in example_by_id]
                for n, ex in enumerate(display_order(exs), 1):
                    lines.append(f"        {n}. {ex.get('t', '')} | {ex.get('e', '')}  "
                                 f"{evidence_tag(ex, ev_by_sentence.get(ex.get('i')))} {str(ex.get('i'))[:8]}")
            groups: dict[tuple, list[str]] = defaultdict(list)
            for m in idle:
                source_meaning = by_release_sense.get(m["sense_id"], {})
                label = label_of_ref.get(meaning_key(source_meaning), "?")
                groups[(m["pos"], m["headword"])].append(f"{label} {m['translation'] or '(no translation)'}")
            for (pos, headword), glosses in groups.items():
                text = "; ".join(glosses)
                lines.append(f"    · unused {pos} {headword} ×{len(glosses)}: "
                             + (text if len(text) <= 160 else text[:157] + "…"))
        if expressions:
            lines.append("  Expressions (follow-up cards):")
            for m in expressions:
                lines.append(f"    · {m['headword']} — {m['translation']}  {fmt_pct(m['percentage'])}  ex {len(m['example_ids'])}")
                exs = [example_by_id[i][1] for i in m["example_ids"] if i in example_by_id]
                for n, ex in enumerate(display_order(exs), 1):
                    lines.append(f"        {n}. {ex.get('t', '')} | {ex.get('e', '')}  "
                                 f"{evidence_tag(ex, ev_by_sentence.get(ex.get('i')))} {str(ex.get('i'))[:8]}")
        views[chunk].append("\n".join(lines))

        # --- the blind sample ----------------------------------------------
        candidates = sorted((sid for sid in example_by_id if sid), key=lambda sid: sample_key(seed, sid))
        picked = candidates[:SAMPLE_PER_CARD]
        if picked:
            block = [f"#{rank} {word}  (card {cid})", "  menu:"]
            for e in menu:
                block.append(f"    {e['label']} {e['pos']} {e['headword']} · {e['translation'] or '(no translation)'}"
                             + (f"  ⟨{e['context']}⟩" if e["context"] else ""))
            for sid in picked:
                sample_counter[chunk] += 1
                sample_id = f"{language}-{chunk}-{sample_counter[chunk]:04d}"
                bucket_index, ex = example_by_id[sid]
                block.append(f"  [{sample_id}] {ex.get('t', '')}\n      EN: {ex.get('e', '')}")
                keys.append({"id": sample_id, "language": language, "chunk": chunk, "rank": rank, "word": word,
                             "card_id": cid, "surface_card_id": full_id, "sentence_id": sid,
                             "text": ex.get("t", ""), "translation": ex.get("e", ""),
                             "menu": {e["label"]: {k: e[k] for k in ("menu_analysis_id", "sense_id", "headword", "pos", "translation", "context")} for e in menu}})
                source_meaning = row["meanings"][bucket_index] if bucket_index < len(row["meanings"]) else {}
                shown_row = next((m for m in shown["main"] + shown["rare"] if sid in m["example_ids"]), None)
                choices.append({"id": sample_id, "label": label_of_ref.get(meaning_key(source_meaning)),
                                "ref": meaning_key(source_meaning),
                                "headword": source_meaning.get("headword"), "pos": source_meaning.get("pos"),
                                "translation": source_meaning.get("translation"),
                                "displayed_under": None if shown_row is None else
                                f"{shown_row['headword']}: {shown_row['translation']}",
                                "displayed_as": None if shown_row is None else
                                ("rare" if shown_row in shown["rare"] else "expression" if shown_row["expression_child"] else "main"),
                                "evidence": ev_by_sentence.get(sid)})
            blinds[chunk].append("\n".join(block))

        records.append({"language": language, "chunk": chunk, "rank": rank, "word": word, "lemma": lemma,
                        "card_id": cid, "surface_card_id": full_id, "display": shown,
                        "menu": menu, "examples": {sid: {"bucket": b, **ex} for sid, (b, ex) in example_by_id.items()},
                        "evidence": ev_by_sentence})

    for chunk, blocks in views.items():
        (out_dir / f"view-{chunk}.txt").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    for chunk, blocks in blinds.items():
        (out_dir / f"blind-{chunk}.txt").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    for name, rows in (("blind-key.jsonl", keys), ("v23-choice.jsonl", choices), ("cards.jsonl", records)):
        with open(out_dir / name, "w", encoding="utf-8") as handle:
            for r in rows:
                handle.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out_dir / "selection.json").write_text(json.dumps({
        "release_id": release_id, "run_id": run_id, "top": top, "random": extra_random, "seed": seed,
        "extra": extra_words, "sample_per_card": SAMPLE_PER_CARD,
        "cards": [{"chunk": chunk, "rank": rank_of[cid], "word": info[cid][0], "card_id": cid} for chunk, cid in chosen],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", required=True, choices=sorted(RELEASES))
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--top", type=int, default=300)
    parser.add_argument("--random", type=int, default=100)
    parser.add_argument("--seed", default="unison-1")
    parser.add_argument("--extra", default="", help="comma-separated surfaces added as chunk s01")
    args = parser.parse_args()
    extra = [w for w in args.extra.split(",") if w]
    print(build(args.language, args.workspace, args.top, args.random, args.seed, extra))


if __name__ == "__main__":
    main()
