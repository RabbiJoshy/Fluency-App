"""Deterministic labels for Dutch separable particles: parser + dictionary, no WSD.

For every eligible sentence of a particle card, Stanza (pinned nl 1.14.0) marks the
particle compound:prt and attaches it to its verb; the joined verb (op + bellen ->
opbellen) is looked up in English Wiktionary (Kaikki 2026-09-09). Reports how often
a particle use is found, how often the joined verb has a dictionary gloss, examples.
"""
import json, os, pickle, collections, random, stanza
SCRATCH = os.environ["NL_SCRATCH"]
menus, pools, bank = pickle.load(open(os.path.join(SCRATCH, "cache.pkl"), "rb"))
KAIKKI = "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-09/kaikki.org-dictionary-Dutch.jsonl"
verbs = {}
for line in open(KAIKKI):
    e = json.loads(line)
    if e.get("pos") != "verb": continue
    gl = [g for s in e.get("senses", []) for g in s.get("glosses", []) if "form of" not in g and "inflection of" not in g]
    if gl: verbs.setdefault(e["word"], gl[0])
PARTICLES = ["op", "aan", "uit", "mee", "af", "toe", "in", "door", "over", "om", "terug", "weg"]
nlp = stanza.Pipeline("nl", processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
stats = collections.Counter(); found = collections.Counter(); samples = collections.defaultdict(list); missing = collections.Counter()
for p in PARTICLES:
    sids = [s for s in pools.get(p, [])]
    docs = nlp.bulk_process([stanza.Document([], text=bank[s][0]) for s in sids])
    for sid, d in zip(sids, docs):
        for sent in d.sentences:
            for w in sent.words:
                if w.text.lower() != p: continue
                stats[(p, "occurrence")] += 1
                if w.deprel != "compound:prt": continue
                stats[(p, "particle")] += 1
                head = sent.words[w.head - 1]
                lemma = head.lemma.replace("_", "")
                comp = lemma if lemma.startswith(p) else p + lemma
                if comp in verbs:
                    stats[(p, "glossed")] += 1
                    if len(samples[p]) < 3: samples[p].append(f"{bank[sid][0][:70]}  -> {comp}: {verbs[comp][:50]}")
                else:
                    missing[comp] += 1
for p in PARTICLES:
    o, pa, g = stats[(p, "occurrence")], stats[(p, "particle")], stats[(p, "glossed")]
    print(f"{p:6s} uses {o:4d}  particle {pa:4d} ({pa/max(o,1):4.0%})  joined verb in Wiktionary {g:4d} ({g/max(pa,1):4.0%})")
O = sum(v for k, v in stats.items() if k[1] == "occurrence"); P = sum(v for k, v in stats.items() if k[1] == "particle"); G = sum(v for k, v in stats.items() if k[1] == "glossed")
print(f"ALL    uses {O}  particle {P} ({P/O:.0%})  glossed {G} ({G/P:.0%})")
print("most common joined verbs not in Wiktionary:", missing.most_common(12))
for p in ("op", "aan", "uit"):
    for s in samples[p]: print("  ", s)
