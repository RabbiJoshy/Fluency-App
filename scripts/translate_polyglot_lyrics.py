"""Create resumable local machine translations with pinned open Marian weights."""
import argparse
import json
from pathlib import Path
import torch
from huggingface_hub import model_info
from transformers import MarianMTModel, MarianTokenizer
from fluency.core.hashing import file_content_id

MODEL = 'Helsinki-NLP/opus-mt-ROMANCE-en'


def translate(sources, output):
    output.mkdir(parents=True, exist_ok=True)
    revision_file = output / 'model.json'
    if revision_file.exists():
        revision = json.loads(revision_file.read_text())['revision']
    else:
        revision = model_info(MODEL).sha
        revision_file.write_text(json.dumps({'model': MODEL, 'revision': revision, 'paid_calls': 0}, indent=2)+'\n')
    tokenizer = MarianTokenizer.from_pretrained(MODEL, revision=revision)
    model = MarianMTModel.from_pretrained(MODEL, revision=revision)
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    model.to(device).eval()
    torch.set_num_threads(4)
    for source in sources:
        raw = json.loads(source.read_text()); language = raw['language']
        target = output / f'{language}-translations.json'
        saved = json.loads(target.read_text()) if target.exists() else {'language':language, 'source_content_id':file_content_id(source), 'model':MODEL, 'revision':revision, 'translations':{}}
        if saved['source_content_id'] != file_content_id(source):
            raise ValueError('source changed since translation checkpoint')
        lines = sorted({line.strip() for song in raw['songs'] for line in song['text'].splitlines() if line.strip() and not line.strip().startswith('[')})
        missing = [line for line in lines if line not in saved['translations']]
        for start in range(0, len(missing), 16):
            batch = missing[start:start+16]
            encoded = tokenizer(batch, return_tensors='pt', padding=True, truncation=True, max_length=256).to(device)
            with torch.inference_mode():
                predicted = model.generate(**encoded, max_new_tokens=128, num_beams=4)
            values = tokenizer.batch_decode(predicted, skip_special_tokens=True)
            saved['translations'].update(zip(batch, values))
            target.write_text(json.dumps(saved, ensure_ascii=False, indent=2)+'\n')
            print(f'{language}: translated {min(start+16,len(missing))}/{len(missing)} missing lines locally', flush=True)
        print(f'{language}: translations complete', flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();translate(args.source,args.output)
