#!/usr/bin/env python3
"""
Scans app/images/loading/ and generates or updates app/images/loading/manifest.json.

Supported image extensions: .png, .jpg, .jpeg, .webp, .svg, .avif

Usage:
    python3 scripts/update_loading_images.py
    python3 scripts/update_loading_images.py --check
"""

import os
import sys
import json
from pathlib import Path

VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.svg', '.avif'}
BASE_DIR = Path(__file__).resolve().parent.parent / 'app' / 'images' / 'loading'
MANIFEST_FILE = BASE_DIR / 'manifest.json'

KNOWN_LANGUAGES = [
    'default',
    'spanish',
    'french',
    'italian',
    'portuguese',
    'portuguese_brazilian',
    'swedish',
    'dutch',
    'russian',
    'polish',
    'czech'
]


def scan_loading_images():
    result = {}
    for lang in KNOWN_LANGUAGES:
        result[lang] = []

    # 1. Scan default folder
    default_dir = BASE_DIR / 'default'
    if default_dir.is_dir():
        for f in sorted(default_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS:
                result['default'].append(f"images/loading/default/{f.name}")

    # 2. Scan languages folder
    lang_base = BASE_DIR / 'languages'
    if lang_base.is_dir():
        for lang_dir in sorted(lang_base.iterdir()):
            if lang_dir.is_dir():
                lang_key = lang_dir.name.lower()
                if lang_key not in result:
                    result[lang_key] = []
                for f in sorted(lang_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS:
                        result[lang_key].append(f"images/loading/languages/{lang_key}/{f.name}")

    return result


def main():
    check_mode = '--check' in sys.argv
    scanned = scan_loading_images()

    if check_mode:
        if not MANIFEST_FILE.is_file():
            print(f"Error: {MANIFEST_FILE} does not exist.")
            sys.exit(1)
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        if existing == scanned:
            print("Manifest is up to date.")
            sys.exit(0)
        else:
            print("Manifest is out of date. Run python3 scripts/update_loading_images.py to update.")
            sys.exit(1)

    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(scanned, f, indent=2)
        f.write('\n')

    total_images = sum(len(imgs) for imgs in scanned.values())
    print(f"Updated {MANIFEST_FILE} with {total_images} images across {len(scanned)} categories.")


if __name__ == '__main__':
    main()
