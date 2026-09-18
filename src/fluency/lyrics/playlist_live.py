"""Persist a live playlist dump into the workspace.

The Cloudflare worker is the cross-device store. The local ``fluency dev``
server writes the same payload here so Joshua can open the JSON on disk.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_segment(value: object) -> str:
    text = _SAFE.sub("-", str(value or "").strip())[:80].strip("-.")
    return text or "unknown"


def playlist_live_root(workspace_root: Path, payload: dict[str, Any]) -> Path:
    return (
        Path(workspace_root)
        / "raw"
        / "playlists"
        / _safe_segment(payload.get("user"))
        / _safe_segment(payload.get("language"))
        / _safe_segment(payload.get("playlistId"))
    )


def store_playlist_live(workspace_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "")
    root = playlist_live_root(workspace_root, payload)
    root.mkdir(parents=True, exist_ok=True)
    if action == "savePlaylistLiveTracks":
        path = root / "tracks.jsonl"
        records = payload.get("records") or []
        if payload.get("record"):
            records = [*records, payload["record"]]
        with path.open("a", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"path": path.as_posix(), "count": len(records)}
    if action == "savePlaylistLiveDeck":
        path = root / "deck.json"
        path.write_text(
            json.dumps(payload.get("deck"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"path": path.as_posix()}
    raise ValueError(f"unsupported playlist-live action: {action}")
