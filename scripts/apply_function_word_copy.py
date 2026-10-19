#!/usr/bin/env python3
"""Apply a function-word row-copy file to app/data/grammar-words/{es,pt}.json.

Each line of the TSV is: lang, word, index, pattern, meaning. The pattern uses
[W:…] for the function word and [V:…]/[C:…] for the two slot sides; this script
refuses a row that changes which slot sides a pattern has, because examples are
highlighted by side and would stop lining up. The replaced copy is kept on the
row under "previous_copy". Run scripts/sync_function_word_card_js.py afterwards.

    python3 scripts/apply_function_word_copy.py docs/audits/function-word-copy/rewrite_2026-10-19.tsv
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASS = {'W': 'fw-token-connector', 'V': 'fw-token-v', 'C': 'fw-token-c'}
TOKEN = re.compile(r"\[([WVC]):([^\]]*)\]")


def to_html(pattern: str) -> str:
    out, pos = [], 0
    for m in TOKEN.finditer(pattern):
        out.append(html.escape(pattern[pos:m.start()], quote=False))
        out.append(f'<span class="{CLASS[m.group(1)]}">{html.escape(m.group(2), quote=False)}</span>')
        pos = m.end()
    out.append(html.escape(pattern[pos:], quote=False))
    return ''.join(out)


def sides(formula_html: str) -> set[str]:
    return set(re.findall(r"fw-token-(v|c)['\"]", formula_html))


def main(path: str) -> None:
    rows = [line.split('\t') for line in Path(path).read_text().splitlines()
            if line.strip() and not line.startswith('#')]
    stamp = Path(path).stem
    suites = {lang: json.loads((ROOT / f'app/data/grammar-words/{lang}.json').read_text()) for lang in ('es', 'pt')}
    changed = 0
    for lang, word, idx, pattern, meaning in rows:
        rel = suites[lang][word]['relations'][int(idx)]
        new_html = to_html(pattern)
        if sides(new_html) != sides(rel['formulaHTML']):
            sys.exit(f'{lang}:{word}:{idx} changes slot sides {sides(rel["formulaHTML"])} -> {sides(new_html)}')
        if (rel['formulaHTML'], rel['tag']) == (new_html, meaning):
            continue
        rel.setdefault('previous_copy', []).append(dict(formulaHTML=rel['formulaHTML'], tag=rel['tag'], replaced_by=stamp))
        rel['formulaHTML'], rel['tag'] = new_html, meaning
        changed += 1
    for lang, suite in suites.items():
        (ROOT / f'app/data/grammar-words/{lang}.json').write_text(json.dumps(suite, ensure_ascii=False, indent=4) + '\n')
    print(f'Updated {changed} of {len(rows)} rows.')


if __name__ == '__main__':
    main(sys.argv[1])
