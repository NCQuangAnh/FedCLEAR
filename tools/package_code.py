"""Zip the working code (flip/ and tools/) for upload as a *private* Kaggle dataset.

Excludes git metadata, caches, figures and any local run outputs. FLIP has no license
file upstream, so keep the Kaggle dataset private.

Usage:
    python tools/package_code.py            # -> dist/fpl-triage-code.zip
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ["flip", "tools", "splits", "server"]   # splits/: CoOp split files, so no Google Drive download
DST = os.path.join(ROOT, "dist", "fpl-triage-code.zip")
SKIP_DIRS = {".git", "__pycache__", "assets", "results", "summaries", "outputs", "data"}


def main():
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    n = 0
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zf:
        for src_name in SOURCES:
            src = os.path.join(ROOT, src_name)
            for dirpath, dirnames, filenames in os.walk(src):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for name in filenames:
                    if name.endswith((".pyc", ".pyo")):
                        continue
                    full = os.path.join(dirpath, name)
                    zf.write(full, os.path.join(src_name, os.path.relpath(full, src)))
                    n += 1
    print(f"wrote {n} files to {DST} ({os.path.getsize(DST) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
