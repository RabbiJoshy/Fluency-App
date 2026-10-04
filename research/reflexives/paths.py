"""Where the evaluation harness finds its inputs.

The tagger itself is ``fluency.reflexive`` (src/). Hand-labelled gold sets live in data/gold/. Parses, UD extracts
and impact runs go to results/ (gitignored)."""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / 'data'
GOLD = DATA / 'gold'
RESULTS = HERE / 'results'
