"""Create an immutable, offline French/Portuguese Artist candidate."""
import argparse
from pathlib import Path
from fluency.lyrics.polyglot import build, recovered_french, write_json

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--recover-french',type=Path)
    args=parser.parse_args()
    if args.recover_french:
        if args.source.exists(): raise FileExistsError(args.source)
        write_json(args.source,recovered_french(args.recover_french))
    build(Path(__file__).resolve().parents[1],args.workspace.resolve(),args.source.resolve(),args.output.resolve(),args.config.resolve())
