"""Kind-level check of the Dutch labeller on the earlier hand-picked hard set (nl-benchmark/labels-hard.jsonl)."""
import json, collections, stanza, labeller_nl as L
EXPECT = {"separable_particle": {"unit"}, "er_split": {"role:pronominal_adverb"}, "fixed_er_verb": {"unit"},
          "existential_er": {"role:existential_er"}, "locative_er": {"role:locative_er"}, "partitive_er": {"role:partitive_er"},
          "degree_te": {"role:degree_too"}, "infinitive_te": {"role:infinitive_to"}, "progressive_aan_het": {"unit:aan het"},
          "preposition": {"role:prep"}, "governed_preposition": {"role:prep", "unit"}, "fixed_phrase": {"unit"},
          "conjunction": {"role:conj_that"}, "relative": {"role:relative"}, "demonstrative_pronoun": {"role:demonstrative"},
          "demonstrative_determiner": {"role:demonstrative"}, "possessive": {"role:possessive"}, "copula": {"role:copula", "role:be"},
          "perfect_auxiliary": {"role:aux_perfect"}, "passive_auxiliary": {"role:aux_passive"},
          "existential_zijn": {"role:be"}, "locative_zijn": {"role:be", "role:copula"}}
rows = [json.loads(l) for l in open("../nl-benchmark/labels-hard.jsonl")]
nlp = stanza.Pipeline("nl", processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
docs = nlp.bulk_process([stanza.Document([], text=r["text"]) for r in rows])
per = collections.Counter(); tot = collections.Counter()
for r, d in zip(rows, docs):
    a = r["span"][0]; lab = {"kind": "none", "value": None}
    for s in d.sentences:
        hit = [k for k, w in enumerate(s.words) if w.parent.start_char <= a < w.parent.end_char and w.text.lower() == r["word"]]
        if hit: lab = L.label(s.words, hit[0]); break
    got = f"{lab['kind']}:{lab['value']}"
    ok = got in EXPECT[r["case"]] or lab["kind"] in EXPECT[r["case"]]
    tot[r["case"]] += 1; per[r["case"]] += ok
    if not ok: print(f"  {r['case']:22s} got {got:28s} {r['text'][:60]}")
print("by case:", {c: f"{per[c]}/{tot[c]}" for c in tot}); print(f"ALL {sum(per.values())}/{sum(tot.values())}")
