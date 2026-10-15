"""Read-only editorial scan. Findings are review prompts, not linguistic verdicts."""
import argparse
from collections import Counter
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
JARGON = re.compile(r'\b(valency|nominal binding|subordination|relativization|clitic|deictic|nexus|nominalizes|pronominal argument|complement|determiner|governs|clausal|infinitive|abstract|degree|standard)\b', re.I)
WORDS = re.compile(r"[^\W\d_]+(?:['’−-][^\W\d_]+)*", re.UNICODE)
CLASSES = {'fw-token-v', 'fw-token-c', 'fw-token-connector'}


def plain(value):
    return unescape(re.sub(r'<[^>]*>', '', value or ''))


def count_words(value):
    return len(WORDS.findall(plain(value)))


class HighlightParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.connectors = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag != 'span' or set(attrs) != {'class'} or attrs.get('class') not in CLASSES:
            self.errors.append('Only spans with a recognised highlight class are allowed.')
        if self.stack:
            self.errors.append('Nested highlights obscure chunk boundaries.')
        if attrs.get('class') == 'fw-token-connector':
            self.connectors += 1
        self.stack.append([tag, False])

    def handle_startendtag(self, tag, attrs):
        self.errors.append('Self-closing highlights are not allowed.')

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            self.errors.append('Unmatched closing tag.')
        else:
            _, has_text = self.stack.pop()
            if not has_text:
                self.errors.append('Empty highlight.')

    def handle_data(self, data):
        if self.stack and data.strip():
            self.stack[-1][1] = True
        if '<' in data or '>' in data:
            self.errors.append('Stray angle bracket or incomplete markup.')

    def handle_comment(self, data):
        self.errors.append('Unexpected HTML comment.')


def markup_errors(value):
    p = HighlightParser()
    p.feed(value or '')
    p.close()
    if p.stack:
        p.errors.append('Unclosed highlight.')
    if not p.connectors:
        p.errors.append('Missing connector highlight.')
    return sorted(set(p.errors))


def scan(suites, rule_limit=20, sentence_limit=15):
    findings = []
    for lang, suite in suites.items():
        for word, entry in suite.items():
            seen = {}
            for i, rel in enumerate(entry.get('relations', [])):
                def add(code, field, detail, example=None):
                    findings.append(dict(language=lang, word=word, pattern=i, example=example,
                                         field=field, code=code, detail=detail, severity='review'))
                for field in ('tag', 'formulaHTML', 'rule'):
                    terms = sorted({m.group().lower() for m in JARGON.finditer(plain(rel.get(field, '')))})
                    if terms:
                        add('jargon', field, ', '.join(terms))
                if count_words(rel.get('rule')) > rule_limit:
                    add('long_rule', 'rule', f"{count_words(rel['rule'])} words (>{rule_limit})")
                for error in markup_errors(rel.get('formulaHTML')):
                    add('markup', 'formulaHTML', error)
                examples = rel.get('examples') or [rel]
                for j, ex in enumerate(examples):
                    target = ex.get('targetHTML', ex.get('target', ''))
                    if not plain(target).strip():
                        add('missing_sentence', 'targetHTML', 'No sentence.', j)
                    if not (ex.get('translation') or '').strip():
                        add('missing_translation', 'translation', 'No English translation.', j)
                    if count_words(target) > sentence_limit:
                        add('long_sentence', 'targetHTML', f'{count_words(target)} words (>{sentence_limit})', j)
                    for error in markup_errors(target):
                        add('markup', 'targetHTML', error, j)
                    key = ' '.join(plain(target).casefold().split())
                    if key and key in seen:
                        add('duplicate_example', 'targetHTML', f'Same sentence as pattern/example {seen[key]}.', j)
                    elif key:
                        seen[key] = f'{i}/{j}'
    return findings


def markdown(findings):
    lines = ['# Whole-suite editorial scan', '',
             'Pattern and example indexes are zero-based. Flags require review; they do not prove a sentence is wrong.', '',
             'Naturalness, translation accuracy, register and semantic highlight boundaries need editorial review.', '',
             '## Counts', '']
    lines += [f'- {k}: {v}' for k, v in sorted(Counter(f['code'] for f in findings).items())]
    lines += ['', '| Language / word | Pattern / example | Field | Flag | Detail |', '|---|---|---|---|---|']
    for f in findings:
        cells = [f"{f['language']} / {f['word']}", f"{f['pattern']} / {f['example'] if f['example'] is not None else '—'}", f['field'], f['code'], f['detail']]
        lines.append('| ' + ' | '.join(c.replace('|', '\\|').replace('\n', ' ') for c in cells) + ' |')
    return '\n'.join(lines) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=ROOT / 'app/data/grammar-words')
    p.add_argument('--format', choices=['json', 'markdown'], default='markdown')
    p.add_argument('--rule-limit', type=int, default=20)
    p.add_argument('--sentence-limit', type=int, default=15)
    args = p.parse_args()
    suites = {lang: json.loads((args.data_dir / f'{lang}.json').read_text()) for lang in ('es', 'pt')}
    findings = scan(suites, args.rule_limit, args.sentence_limit)
    print(json.dumps(findings, ensure_ascii=False, indent=2) if args.format == 'json' else markdown(findings), end='\n')


if __name__ == '__main__':
    main()
