import json, sys, spacy, warnings
warnings.filterwarnings('ignore')
from spacy.tokens import DocBin
model, inp, outp = sys.argv[1:4]
texts = sorted({i['text'] for i in json.load(open(inp))}) if inp.endswith('.json') else [l.rstrip('\n') for l in open(inp)]
nlp = spacy.load(model)
db = DocBin(store_user_data=False)
for d in nlp.pipe(texts, batch_size=32):
    db.add(d)
db.to_disk(outp)
print('parsed', len(texts))
