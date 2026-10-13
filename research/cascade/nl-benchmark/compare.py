"""One line per scorer: accuracy (POS gate on) on random and hard strata, and margin AUROC."""
import glob, os, sys
from evaluate import report, auroc
HERE = os.path.dirname(os.path.abspath(__file__))
names = sys.argv[1:] or sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(HERE, "results", "*.jsonl"))
                             if not os.path.basename(p).startswith(("agree_", "llm_")))
print(f"{'scorer':34s} {'random':>7s} {'hard':>6s} {'AUROC':>6s}   (no POS gate: random/hard)")
for n in names:
    g = report(n, True); u = report(n, False)
    print(f"{n:34s} {g['random'][1]:7.0%} {g['hard'][1]:6.0%} {auroc(g['random'][2]):6.2f}   {u['random'][1]:.0%}/{u['hard'][1]:.0%}")
