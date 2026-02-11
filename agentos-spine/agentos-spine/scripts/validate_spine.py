#!/usr/bin/env python3
"""Validate hygiene + license posture for extracted spine repos in `spine/`.

Fail-fast conditions (default):
- missing LICENSE/COPYING in any spine repo
- presence of .DS_Store, nested .git, venv dirs, __pycache__, *.pyc

Usage:
  python3 scripts/validate_spine.py
"""

import argparse
from pathlib import Path
import sys

BAD_FILES = {".DS_Store"}
BAD_DIRS = {".git", ".venv", "venv", "env", "__pycache__"}
BAD_SUFFIXES = {".pyc"}

LICENSE_NAMES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "COPYING.txt")

def has_license(repo: Path) -> bool:
    for name in LICENSE_NAMES:
        if (repo / name).exists():
            return True
    # also allow LICENSE.* patterns at root
    for p in repo.glob("LICENSE*"):
        if p.is_file():
            return True
    return False

def scan(repo: Path):
    issues = []
    for p in repo.rglob("*"):
        if p.is_file():
            if p.name in BAD_FILES:
                issues.append(f"bad file: {p}")
            if p.suffix in BAD_SUFFIXES:
                issues.append(f"bad file: {p}")
        if p.is_dir() and p.name in BAD_DIRS:
            issues.append(f"bad dir: {p}")
    return issues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", default="spine", help="Spine directory (default: spine)")
    ap.add_argument("--allow-missing-license", action="store_true", help="Do not fail on missing license")
    args = ap.parse_args()

    spine = Path(args.spine)
    if not spine.exists():
        print(f"ERROR: spine directory not found: {spine}")
        sys.exit(2)

    repos = [p for p in spine.iterdir() if p.is_dir() and not p.name.startswith('_')]
    repos.sort(key=lambda p: p.name.lower())

    failed = False
    print("=== Spine validation ===")
    for repo in repos:
        repo_failed = False
        lic_ok = has_license(repo)
        issues = scan(repo)

        if not lic_ok and not args.allow_missing_license:
            repo_failed = True
            print(f"[FAIL] {repo.name}: missing LICENSE/COPYING")
        else:
            print(f"[ OK ] {repo.name}: license={'yes' if lic_ok else 'missing (allowed)'}")

        if issues:
            repo_failed = True
            print(f"       hygiene issues ({len(issues)}):")
            for line in issues[:25]:
                print(f"         - {line}")
            if len(issues) > 25:
                print(f"         ... {len(issues)-25} more")

        if repo_failed:
            failed = True

    if failed:
        print("\nValidation failed. Fix hygiene/license issues before integrating into the OS base.")
        sys.exit(1)

    print("\nValidation passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
