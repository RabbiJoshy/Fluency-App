#!/usr/bin/env python3
"""Retired: deploys now go through main. Kept so the old command still works.

gh-pages is written only by .github/workflows/deploy-pages.yml. This runs
scripts/deploy.py, which pushes HEAD to main and lets that workflow publish.
"""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("deploy.py")), run_name="__main__")
