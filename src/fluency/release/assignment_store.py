"""Read an immutable assignment file one card at a time."""
import json
from functools import lru_cache
from collections import defaultdict, Counter
from fluency.projections import materialize_selection


class SentenceFile:
    """Keep sentence offsets and a small cache rather than the whole corpus."""
    def __init__(self, path):
        self.path = path
        self.offsets = {}
        with path.open('rb') as f:
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                if not line.strip():
                    continue
                row = json.loads(line)
                identity = row.get('sentence_id')
                if not isinstance(identity, str) or identity in self.offsets:
                    raise ValueError('invalid sentence identity')
                self.offsets[identity] = (offset, len(line))
        self._read = lru_cache(maxsize=256)(self._read)

    def __len__(self):
        return len(self.offsets)

    def _read(self, identity):
        offset, length = self.offsets[identity]
        with self.path.open('rb') as f:
            f.seek(offset)
            return json.loads(f.read(length))

    def get(self, identity, default=None):
        return self._read(identity) if identity in self.offsets else default


class AssignmentFile:
    def __init__(self, path, projection):
        self.path, self.projection = path, projection
        self.offsets = defaultdict(dict)
        self.counts = Counter()
        self.cached_card = None
        self.cached_rows = {}
        with path.open('rb') as f:
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                if not line.strip():
                    continue
                row = json.loads(line)
                card, sentence = row.get('card_id'), row.get('sentence_id')
                if not card or not sentence:
                    raise ValueError('assignment lacks card/sentence identity')
                if sentence in self.offsets[card]:
                    raise ValueError('duplicate assignment identity')
                self.offsets[card][sentence] = (offset, len(line))
                self.counts[row.get('status')] += 1

    def __bool__(self):
        return bool(self.offsets)

    def get(self, key, default=None):
        card = key[0] if isinstance(key, tuple) else key
        if card not in self.offsets:
            return default
        if card != self.cached_card:
            rows = {}
            with self.path.open('rb') as f:
                for sentence, (offset, length) in self.offsets[card].items():
                    f.seek(offset)
                    rows[sentence] = materialize_selection(json.loads(f.read(length)), self.projection)
            self.cached_card, self.cached_rows = card, rows
        if isinstance(key, tuple):
            return self.cached_rows.get(key[1], default)
        return self.cached_rows
