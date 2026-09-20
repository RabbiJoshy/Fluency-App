"""A shared exact-text embedding store with a resumable writer.

Both modes cached embeddings, and each got half of it right.

Speech kept its cache in the right place -- ``workspace/embeddings/<language>/``,
shared across runs and modes -- but wrote it in one shot at the end, so an
interruption partway through a long embed lost every vector bought so far.

Lyrics wrote carefully -- checkpointing every thousand vectors, parsing the
provider's own ``retry in Ns`` hint, checkpointing again before each retry -- but
into a private run-scoped delta that nothing else could reuse.

This takes the location from speech and the write path from lyrics. Embeddings
are expensive and perfectly reusable; losing them to a dropped connection is a
cost with nothing to show for it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import time
from typing import Any, Callable, Iterable, Sequence

from fluency.nlp.models import setting


_ROLE = "exact-text-embedding"
EMBED_MODEL = setting(_ROLE, "name")
TASK_TYPE = setting(_ROLE, "task_type")
BATCH_SIZE = setting(_ROLE, "batch_size", 100)
CHECKPOINT_EVERY = setting(_ROLE, "checkpoint_every", 1000)
MAX_QUOTA_RETRIES = setting(_ROLE, "max_quota_retries", 12)
MIN_SECONDS_PER_BATCH = setting(_ROLE, "min_seconds_per_batch", 2.2)
_RETRY_HINT = re.compile(r"retry in ([0-9.]+)s", re.IGNORECASE)


class EmbeddingStoreError(RuntimeError):
    """Raised when a cache is corrupt or embeddings cannot be completed."""


def delta_directory(cache_path: Path) -> Path:
    """Return the sidecar directory holding vectors not yet merged into cache."""

    return cache_path.parent / f"{cache_path.name}.delta"


def _load_delta(delta: Path, width: int) -> tuple[dict[str, int], Any]:
    import numpy as np

    index_path, vector_path = delta / "index.json", delta / "vec.npy"
    if not (index_path.exists() and vector_path.exists()):
        return {}, np.zeros((0, width), dtype=np.float32)

    index = json.loads(index_path.read_text(encoding="utf-8"))
    matrix = np.load(vector_path)
    if sorted(index.values()) != list(range(len(index))) or len(matrix) < len(index):
        raise EmbeddingStoreError(f"delta index and vectors disagree: {delta}")
    # The vectors are replaced before the index at each checkpoint. A process
    # killed between those two atomic renames leaves an uncommitted tail;
    # discard only that and resume from the last complete index.
    return index, matrix[: len(index)]


def load_cache(cache_path: Path) -> dict[str, Any]:
    """Return every vector already stored, including an unmerged delta."""

    import numpy as np

    vectors: dict[str, Any] = {}
    width = 0
    if cache_path.exists():
        blob = np.load(cache_path, allow_pickle=True)
        matrix = blob["vectors"]
        width = matrix.shape[1] if len(matrix) else 0
        vectors = {str(key): matrix[i] for i, key in enumerate(blob["keys"])}

    delta_index, delta_matrix = _load_delta(delta_directory(cache_path), width)
    for text, position in delta_index.items():
        vectors[text] = delta_matrix[position]
    return vectors


def _embed_batch(client: Any, batch: Sequence[str], types_module: Any) -> Any:
    return client.models.embed_content(
        model=EMBED_MODEL,
        contents=list(batch),
        config=types_module.EmbedContentConfig(task_type=TASK_TYPE),
    )


def _embed_batch_worker(
    batch: Sequence[str],
    *,
    api_key: str,
    types_module: Any,
    max_retries: int = MAX_QUOTA_RETRIES,
    min_seconds: float = 1.0,
    log: Callable[[str], None] = print,
) -> tuple[Sequence[str], Any]:
    import numpy as np
    from google import genai

    client = genai.Client(api_key=api_key)
    attempts = 0
    while True:
        started = time.monotonic()
        try:
            response = _embed_batch(client, batch, types_module)
            values = np.asarray([item.values for item in response.embeddings], dtype=np.float32)
            if len(values) != len(batch):
                raise EmbeddingStoreError("provider returned an incomplete embedding batch")
            values /= np.linalg.norm(values, axis=1, keepdims=True) + 1e-9
            elapsed = time.monotonic() - started
            if min_seconds > 0 and elapsed < min_seconds:
                time.sleep(min_seconds - elapsed)
            return batch, values
        except Exception as error:
            status = getattr(error, "status_code", None) or getattr(error, "code", None)
            err_str = str(error)
            is_quota = status == 429 or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
            is_transient = (
                is_quota
                or (isinstance(status, int) and 500 <= status < 600)
                or any(code in err_str for code in ("500", "502", "503", "504", "UNAVAILABLE"))
                or isinstance(error, (ConnectionError, OSError, TimeoutError))
                or "remoteprotocolerror" in error.__class__.__name__.lower()
                or any(phrase in err_str.lower() for phrase in ("connection reset", "readerror", "connecterror", "remotedisconnected", "disconnected", "broken pipe", "timeout"))
            )
            if not is_transient:
                raise
            attempts += 1
            if attempts > max_retries:
                raise EmbeddingStoreError(
                    f"embedding request failed after {max_retries} resumable retries: {error}"
                ) from error
            if is_quota:
                hint = _RETRY_HINT.search(err_str)
                delay = min(60.0, (float(hint.group(1)) + 2.0) if hint else 20.0)
                log(f"  quota pause; retrying batch of {len(batch)} in {delay:.1f}s...")
            else:
                delay = min(60.0, 3.0 * attempts)
                log(f"  transient error ({error.__class__.__name__}); retrying batch of {len(batch)} in {delay:.1f}s...")
                try:
                    client = genai.Client(api_key=api_key)
                except Exception:
                    pass
            time.sleep(delay)


def ensure_embeddings(
    cache_path: Path,
    needed: Iterable[str],
    *,
    api_key: str | None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Return vectors for ``needed``, embedding and checkpointing any misses.

    Work already paid for is never re-bought: misses land in a delta that is
    flushed every ``CHECKPOINT_EVERY`` vectors and before every quota retry, and
    is merged into the cache only once the run completes.
    """

    from concurrent.futures import ThreadPoolExecutor, as_completed
    import numpy as np

    vectors = load_cache(cache_path)
    missing = [text for text in dict.fromkeys(needed) if text not in vectors]
    if not missing:
        return vectors
    if not api_key:
        raise EmbeddingStoreError(
            f"{len(missing):,} exact-text embeddings are missing; provide an API key to create them"
        )

    from google.genai import types

    delta = delta_directory(cache_path)
    width = next(iter(vectors.values())).shape[0] if vectors else 0
    delta_index, delta_matrix = _load_delta(delta, width)

    def checkpoint() -> None:
        delta.mkdir(parents=True, exist_ok=True)
        vector_temporary = delta / "vec.npy.partial"
        index_temporary = delta / "index.json.partial"
        with vector_temporary.open("wb") as handle:
            np.save(handle, delta_matrix)
        index_temporary.write_text(json.dumps(delta_index, ensure_ascii=False), encoding="utf-8")
        # Vectors first: a tear leaves an uncommitted tail, never a claim
        # in the index that no vector backs.
        os.replace(vector_temporary, delta / "vec.npy")
        os.replace(index_temporary, delta / "index.json")

    workers = setting(_ROLE, "workers", 2)
    min_seconds = setting(_ROLE, "min_seconds_per_batch", 1.2)
    batches = [missing[offset : offset + BATCH_SIZE] for offset in range(0, len(missing), BATCH_SIZE)]
    log(f"embedding {len(missing):,} cache misses across {len(batches):,} batches ({workers} workers)...")

    since_checkpoint = 0
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_batch = {
            executor.submit(
                _embed_batch_worker,
                batch,
                api_key=api_key,
                types_module=types,
                max_retries=MAX_QUOTA_RETRIES,
                min_seconds=min_seconds,
                log=log,
            ): batch
            for batch in batches
        }
        delta_chunks = [delta_matrix] if len(delta_matrix) else []
        for future in as_completed(future_to_batch):
            batch, values = future.result()
            start = len(delta_index)
            delta_chunks.append(values)
            for position, text in enumerate(batch, start=start):
                delta_index[text] = position

            since_checkpoint += len(batch)
            done += len(batch)
            if since_checkpoint >= CHECKPOINT_EVERY or done == len(missing):
                delta_matrix = np.vstack(delta_chunks)
                delta_chunks = [delta_matrix]
                checkpoint()
                since_checkpoint = 0
            log(f"  embedded {done:,}/{len(missing):,}")

        if len(delta_chunks) > 1:
            delta_matrix = np.vstack(delta_chunks)

    for text, position in delta_index.items():
        vectors[text] = delta_matrix[position]
    merge_delta(cache_path, vectors)
    return vectors


def merge_delta(cache_path: Path, vectors: dict[str, Any]) -> None:
    """Write every vector into the shared cache and drop the delta."""

    import numpy as np

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(vectors)
    # savez_compressed appends .npz unless the name already ends in it, so the
    # temporary file is named to survive that rather than be renamed twice.
    temporary = cache_path.parent / f"{cache_path.stem}.partial.npz"
    np.savez_compressed(
        temporary,
        keys=np.array(ordered, dtype=object),
        vectors=np.stack([vectors[key] for key in ordered]),
    )
    os.replace(temporary, cache_path)

    delta = delta_directory(cache_path)
    for name in ("vec.npy", "index.json"):
        (delta / name).unlink(missing_ok=True)
    if delta.exists() and not any(delta.iterdir()):
        delta.rmdir()
