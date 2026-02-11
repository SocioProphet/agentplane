#!/usr/bin/env python3
"""Extract a spine archive into `spine/` with safe defaults.

- Normalizes folder names (strip suffixes like -main)
- Removes __MACOSX, .DS_Store
- Strips nested .git directories from zip snapshots
- Optionally scrubs venv/__pycache__/*.pyc

Usage:
  python3 scripts/ingest_archives.py --archive _archives/Archive.zip
"""

import argparse
import os
import shutil
import zipfile
from pathlib import Path

NORMALIZE = {
    "SourceOS-main": "sourceos",
    "TriTRPC-main": "tritrpc",
    "socios-main": "socios",
    "sociosphere-main": "sociosphere",
    "agentplane": "agentplane",
    "tritfabric_repo_fresh": "tritfabric",
    "socioprophet-standards-storage": "standards-storage",
    "socioprophet-standards-knowledge": "standards-knowledge",
    "global-devsecops-intelligence": "global-devsecops-intelligence",
}

SCRUB_DIRS = {".venv", "venv", "env", "__pycache__", ".git"}

def rm_tree(path: Path):
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)

def scrub(root: Path):
    # Remove OS junk files
    for p in root.rglob(".DS_Store"):
        p.unlink(missing_ok=True)

    # Remove scrub dirs and pyc files
    for p in list(root.rglob("*")):
        if p.is_dir() and p.name in SCRUB_DIRS:
            rm_tree(p)
        elif p.is_file() and p.suffix == ".pyc":
            p.unlink(missing_ok=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True, help="Path to Archive.zip")
    ap.add_argument("--out", default="spine", help="Output dir (default: spine)")
    ap.add_argument("--no-scrub", action="store_true", help="Do not scrub .git/.venv/__pycache__/pyc/.DS_Store")
    args = ap.parse_args()

    archive = Path(args.archive)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    tmp = out / "_tmp_extract"
    rm_tree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive) as z:
        z.extractall(tmp)

    # Remove __MACOSX
    rm_tree(tmp / "__MACOSX")

    # Move normalized dirs
    for src_name, dest_name in NORMALIZE.items():
        src = tmp / src_name
        dest = out / dest_name
        if not src.exists():
            continue
        rm_tree(dest)
        shutil.move(str(src), str(dest))

    rm_tree(tmp)

    if not args.no_scrub:
        scrub(out)

    print(f"Extracted spine into: {out.resolve()}")
    print("Contents:")
    for p in sorted(out.iterdir()):
        if p.is_dir() and not p.name.startswith('_'):
            print(f"  - {p.name}")

if __name__ == "__main__":
    main()
