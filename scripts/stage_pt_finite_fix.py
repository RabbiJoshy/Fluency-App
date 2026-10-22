#!/usr/bin/env python3
"""Finish the prepared Portuguese correction from an internet-enabled terminal.

Publishes the immutable data release, records the app change, commits only this
fix's paths, and deploys staging. Does not promote production.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OLD = "pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-slim"
NEW = "pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-finite-v1-slim"
RELEASE = ROOT / "dist/pt-finite-staging/pt/speech" / NEW
PATHS = [
    "src/fluency/sense_menu/kaikki.py",
    "src/fluency/release/linked_finite_forms.py",
    "scripts/repair_linked_finite_release.py",
    "scripts/stage_pt_finite_fix.py",
    "config/learner-cues/pt-linked-finite-forms-v1.json",
    "tests/sense_menu/test_kaikki_linked_finite_forms.py",
    "tests/release/test_linked_finite_forms.py",
    "app/config/config.json",
    "app/config/dev_changelog.json",
]


def run(*command):
    subprocess.run(command, cwd=ROOT, check=True,
                   env={**os.environ, "PYTHONPATH": str(ROOT / "src")})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-local", action="store_true")
    args = parser.parse_args()
    report = json.loads((RELEASE / "linked-finite-form-corrections.json").read_text())
    assert len(report["readings"]) == 100
    assert len({r["surface"] for r in report["readings"]}) == 99
    for path in PATHS:
        if not (ROOT / path).is_file():
            raise FileNotFoundError(path)
    config_path = ROOT / "app/config/config.json"
    config_text = config_path.read_text()
    if OLD not in config_text and NEW not in config_text:
        raise ValueError("Portuguese config changed; review its release before proceeding")
    print(f"Prepared: 100 corrected readings on 99 cards. Release: {RELEASE}", flush=True)
    if args.check_local:
        return
    run("git", "merge-base", "--is-ancestor", "staging", "HEAD")
    print("Checking GitHub connectivity...", flush=True)
    run("git", "ls-remote", "--heads", "https://github.com/RabbiJoshy/Fluency-Releases-pt", "gh-pages")
    print("Running tests...", flush=True)
    run(sys.executable, "-m", "unittest", "discover", "-s", "tests/sense_menu", "-p", "test_kaikki*.py")
    run(sys.executable, "-m", "unittest", "tests.release.test_linked_finite_forms")
    run(sys.executable, "-m", "unittest", "discover", "-s", "tests/app", "-t", ".")
    print("Publishing corrected Portuguese release...", flush=True)
    run(sys.executable, "scripts/publish_release.py", "--segment", "pt", "--release", str(RELEASE))
    # Point at new assets only after their publication succeeds.
    config_path.write_text(config_text.replace(OLD, NEW))
    log_path = ROOT / "app/config/dev_changelog.json"
    log = json.loads(log_path.read_text())
    summary = "Portuguese verb forms show real inflected meanings and conjugation tables."
    if not log["entries"] or log["entries"][0].get("summary") != summary:
        now = datetime.now(ZoneInfo("Europe/London"))
        log["entries"].insert(0, {
            "timestamp": now.isoformat(), "date": now.strftime("%Y-%m-%d %H:%M %Z"),
            "agent": "Codex", "summary": summary,
            "detail": [
                "Correct 100 grammatical-reading rows on 99 Portuguese cards; foram shows they went / they were.",
                "Resolve the correct verb tables while preserving card and meaning IDs, example assignments and progress namespace.",
                "Keep original dictionary grammar and correction provenance; no new lexical WSD assignments are claimed.",
            ], "commit": "pending",
        })
        log["entries"] = log["entries"][:30]
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    run("git", "diff", "--check", "--", *PATHS)
    run("git", "add", "--", *PATHS)
    changed = subprocess.run(["git", "diff", "--cached", "--quiet", "--", *PATHS], cwd=ROOT)
    if changed.returncode == 1:
        run("git", "commit", "--only", "-m", "Correct Portuguese finite-form meanings and conjugation lookups", "--", *PATHS)
    elif changed.returncode:
        raise RuntimeError("could not inspect staged correction")
    print("Deploying to staging...", flush=True)
    run(sys.executable, "scripts/deploy_staging.py", "--skip-tests")
    print("STAGING DEPLOYED: https://fluency-staging.pages.dev/", flush=True)


if __name__ == "__main__":
    main()
