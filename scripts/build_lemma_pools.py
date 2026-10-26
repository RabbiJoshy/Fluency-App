#!/usr/bin/env python3
"""Pooled sibling sentences for merged Speech cards (lemma-pool/v1).

A merged card (ser) pools the sentences of all its forms (é, foi, era…), but
the app loads sentences only for the 25-card set being studied, and most forms
rank in other sets. Measured on pt-speech-v25-decide-1-expr: 26% of merged
cards' sentences were reachable; ser showed 30 of 808, all "é".

For each merged group this writes, into the set file of its top-ranked form, a
sample of the other forms' sentences: per sense row of that top form, up to
PER_SENSE sentences taken in turn from each form (rank order). Sentences stay
in the release's slim example format, keyed by the form's card id, and each
form's meanings travel with them, so the app expands, corrects and matches
them exactly as it does a loaded set (vocab.js poolLemmaSiblingExamples).

    python scripts/build_lemma_pools.py portuguese spanish
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT.parent / "Fluency-Workspace"
RULE = "lemma-pool/v1"
PER_SENSE = 30
MEANING_FIELDS = ("headword", "pos", "source_reference", "translation", "context")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sense_key(meaning: dict) -> str:
    """vocab.js lemmaSenseDedupeKey."""
    ref = str(meaning.get("source_reference") or "").strip()
    if ref and ref != "mwe-merged/v1":
        return f"ref:{ref}"
    parts = (meaning.get("pos"), meaning.get("translation") or meaning.get("meaning"), meaning.get("context"))
    return "sig:" + "|".join(str(p or "").strip().lower() for p in parts)


def build(language: str) -> None:
    cfg_path = ROOT / "app/config/config.json"
    cfg_text = cfg_path.read_text(encoding="utf-8")
    cfg = json.loads(cfg_text)["languages"][language]
    keys = read_json(ROOT / "app" / cfg["mergeExceptionsPath"]).get("form_privilege_keys")
    if not keys:
        raise SystemExit(f"{language}: no form-privilege overlay")
    index_path = WS / cfg["indexPath"]
    app_dir = index_path.parent
    rows = read_json(index_path)
    shard_manifest = read_json(app_dir / "vocabulary.examples.manifest.json")
    shards = shard_manifest["shards"]
    slim = {}
    for shard in shards:
        slim.update(read_json(app_dir / shard["path"]))

    groups = defaultdict(list)
    for row in rows:
        lemma = keys.get(row["word"].lower())
        if lemma:
            groups[lemma].append(row)

    def buckets(row):
        return (slim.get(row["id"]) or {}).get("m") or []

    by_shard = defaultdict(lambda: {"groups": {}, "rows": {}, "examples": {}})
    stats = {"groups": 0, "sentences": 0}
    for lemma, members in groups.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda r: r["rank"])
        host, siblings = members[0], members[1:]
        seen = {str(e.get("t") or "").strip().lower() for b in buckets(host) for e in (b or [])}
        lanes = {sense_key(m): [] for m in host.get("meanings") or []}
        for sib in siblings:
            per_key = defaultdict(list)
            sib_buckets = buckets(sib)
            for i, meaning in enumerate(sib.get("meanings") or []):
                k = sense_key(meaning)
                if k in lanes and i < len(sib_buckets):
                    per_key[k].extend((i, e) for e in sib_buckets[i] or [])
            for k, items in per_key.items():
                lanes[k].append((sib, items))
        picked = defaultdict(lambda: defaultdict(list))  # card id -> meaning index -> slim records
        for sense_lanes in lanes.values():
            taken, depth = 0, 0
            while taken < PER_SENSE and any(depth < len(items) for _, items in sense_lanes):
                for sib, items in sense_lanes:
                    if depth >= len(items) or taken >= PER_SENSE:
                        continue
                    i, record = items[depth]
                    text = str(record.get("t") or "").strip().lower()
                    if text and text not in seen:
                        seen.add(text)
                        picked[sib["id"]][i].append(record)
                        taken += 1
                depth += 1
        out = by_shard[next(s["set_id"] for s in shards if s["start_rank"] <= host["rank"] <= s["end_rank"])]
        ids = []
        for sib in siblings:
            chosen = picked.get(sib["id"])
            if not chosen:
                continue
            meanings = sib.get("meanings") or []
            out["rows"][sib["id"]] = {"word": sib["word"], "rank": sib["rank"],
                                      "meanings": [{f: m[f] for f in MEANING_FIELDS if m.get(f) is not None}
                                                   for m in meanings]}
            out["examples"][sib["id"]] = {"m": [chosen.get(i, []) for i in range(len(meanings))]}
            ids.append(sib["id"])
            stats["sentences"] += sum(len(v) for v in chosen.values())
        if ids:
            out["groups"][lemma] = {"host": host["id"], "siblings": ids}
            stats["groups"] += 1

    release_id = index_path.parts[-3]
    out_dir = ROOT / "app/data/lemma-pools" / release_id
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_shards, size = [], 0
    for shard in shards:
        payload = by_shard.get(shard["set_id"])
        if not payload or not payload["groups"]:
            continue
        path = out_dir / f"{shard['set_id']}.json"
        path.write_text(json.dumps({"rule": RULE, **payload}, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8")
        size += path.stat().st_size
        manifest_shards.append({"set_id": shard["set_id"], "start_rank": shard["start_rank"],
                                "end_rank": shard["end_rank"], "path": path.name})
    manifest = {
        "rule": RULE, "release_id": release_id, "per_sense": PER_SENSE,
        "index_sha256": hashlib.sha256(index_path.read_bytes()).hexdigest(),
        "merge_keys_from": cfg["mergeExceptionsPath"],
        "example_format": shard_manifest["example_format"], "sources": shard_manifest["sources"],
        "shards": manifest_shards,
    }
    manifest_rel = f"data/lemma-pools/{release_id}/manifest.json"
    (ROOT / "app" / manifest_rel).write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n",
                                            encoding="utf-8")
    old = cfg.get("lemmaPoolPath")
    if old:
        cfg_text = cfg_text.replace(f'"lemmaPoolPath": {json.dumps(old)}',
                                    f'"lemmaPoolPath": {json.dumps(manifest_rel)}', 1)
    else:
        anchor = f'"mergeExceptionsPath": {json.dumps(cfg["mergeExceptionsPath"])}'
        at = cfg_text.index(anchor, cfg_text.index(f'"{language}": {{')) + len(anchor)
        cfg_text = cfg_text[:at] + f',\n      "lemmaPoolPath": {json.dumps(manifest_rel)}' + cfg_text[at:]
    cfg_path.write_text(cfg_text, encoding="utf-8")
    assert json.loads(cfg_text)["languages"][language]["lemmaPoolPath"] == manifest_rel
    print(f"{language}: {stats['groups']} merged cards, {stats['sentences']:,} pooled sentences, "
          f"{len(manifest_shards)} files, {size / 1e6:.1f} MB -> {manifest_rel}")


if __name__ == "__main__":
    for name in sys.argv[1:] or ["portuguese", "spanish"]:
        build(name)
