"""Bounded-memory reader for the ordinary JSON emitted by write_spliced_bundle.

No new bundle schema: the strict line layout lets us decode the same JSON array
one record at a time. Validated records spool to disk until coverage is complete.
"""
import json
import tempfile
from fluency.core.canonical_json import canonical_json

HEADER = ', "assignments": ['
FOOTER = '], "sampling": '


def load_streamed_bundle(path):
    with path.open(encoding='utf-8') as f:
        first = f.readline().rstrip('\n')
        if not first.endswith(HEADER):
            raise ValueError('streaming import requires write_spliced_bundle line layout')
        header = json.loads(first[:-len(HEADER)] + '}')
        last = None
        for line in f:
            if line.strip():
                last = line.strip()
        if not last or not last.startswith(FOOTER) or not last.endswith('}'):
            raise ValueError('streamed bundle lacks final sampling object')
        header['sampling'] = json.loads(last[len(FOOTER):-1])
    header['assignments'] = StreamedRows(path, last)
    return header


class StreamedRows:
    def __init__(self, path, footer):
        self.path, self.footer = path, footer

    def __iter__(self):
        with self.path.open(encoding='utf-8') as f:
            f.readline()
            pending = None
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line == self.footer:
                    if pending is not None:
                        if pending.endswith(','):
                            raise ValueError('trailing comma in streamed assignment array')
                        yield json.loads(pending)
                    if f.read().strip():
                        raise ValueError('content after streamed bundle')
                    return
                if pending is not None:
                    if not pending.endswith(','):
                        raise ValueError('missing assignment separator')
                    yield json.loads(pending[:-1])
                pending = line
            raise ValueError('streamed bundle was truncated')


class SpooledAssignments:
    def __init__(self, directory):
        self.file = tempfile.TemporaryFile(mode='w+b', dir=directory)
        self.offsets = {}

    def __contains__(self, pair):
        return pair in self.offsets

    def __iter__(self):
        return iter(self.offsets)

    def __setitem__(self, pair, assignment):
        raw = (canonical_json(assignment.to_dict()) + '\n').encode('utf-8')
        self.offsets[pair] = (self.file.tell(), len(raw))
        self.file.write(raw)

    def serialized(self, pair):
        offset, length = self.offsets[pair]
        self.file.seek(offset)
        return self.file.read(length).decode('utf-8')

    def close(self):
        self.file.close()
