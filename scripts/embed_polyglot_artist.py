"""Embed a reviewed rehearsal's exact misses under an explicit spend ceiling."""
import argparse
import json
from pathlib import Path
from fluency.nlp.embeddings import load_cache, ensure_embeddings
from fluency.lyrics.wsd_execute import dotenv_value
from fluency.core.hashing import file_content_id

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--approved-usd',type=float,required=True)
    p.add_argument('--env-file',type=Path,default=Path('.env'))
    args=p.parse_args()
    manifest=json.loads((args.run/'manifest.json').read_text())
    missfile=args.run/'missing-embeddings.json'
    if file_content_id(missfile) != manifest['outputs']['missing-embeddings.json']:
        raise ValueError('embedding request changed since rehearsal')
    language=manifest['language']
    cache=args.workspace/'embeddings'/language/'exact-text-gemini-embedding-001.npz'
    existing=load_cache(cache)
    missing=[t for t in json.loads(missfile.read_text()) if t not in existing]
    # One token per UTF-8 byte is a conservative planning allowance, not a
    # provider token count. Actual estimated tokens use three characters/token.
    chars=sum(len(t) for t in missing); byte_allowance=sum(len(t.encode('utf-8')) for t in missing)
    estimate=chars/3*0.15/1_000_000
    allowance=byte_allowance*0.15/1_000_000
    print(json.dumps({'language':language,'uncached_texts':len(missing),'projected_usd':estimate,
                      'conservative_planning_usd':allowance,'approved_ceiling_usd':args.approved_usd,
                      'rate_usd_per_million_input_tokens':0.15},indent=2),flush=True)
    if allowance > args.approved_usd or args.approved_usd <= 0:
        raise SystemExit('projected spend exceeds approval')
    if missing:
        ensure_embeddings(cache,missing,api_key=dotenv_value(args.env_file,'GEMINI_API_KEY'))
    print('Embedding cache complete for this request',flush=True)
