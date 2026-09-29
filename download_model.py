"""Pre-download the local Whisper model used by ghosttype.

Upstream CatBoneheaD/Whisper-Writer hardcoded large-v3 (3.1 GB, Russian prompts).
ghosttype defaults to faster-whisper-base.en (142 MB, English-optimized, ~10x faster
on CPU) for first-install verification. Switch to a larger model via Settings once
you've confirmed hold-to-talk works.

Usage:
    python download_model.py                # base.en
    python download_model.py small.en       # small.en
    python download_model.py large-v3       # large-v3 (3.1 GB)
"""

import os
import sys
import requests

# Default to base.en — fastest path to a working hold-to-talk on CPU.
# Override with argv[1] if you want something bigger.
MODEL = sys.argv[1] if len(sys.argv) > 1 else "base.en"

# HuggingFace repo for Systran's faster-whisper builds.
HF_REPO = f"Systran/faster-whisper-{MODEL}"

CACHE_DIR = os.path.join(
    os.environ["USERPROFILE"], ".cache", "huggingface", "hub",
    f"models--Systran--faster-whisper-{MODEL}", "snapshots", "main",
)
os.makedirs(CACHE_DIR, exist_ok=True)

# The minimal file set faster-whisper needs at runtime.
FILES = ["config.json", "model.bin", "tokenizer.json", "vocabulary.json",
         "preprocessor_config.json"]


def download(filename):
    url = f"https://huggingface.co/{HF_REPO}/resolve/main/{filename}"
    path = os.path.join(CACHE_DIR, filename)
    existing = os.path.getsize(path) if os.path.exists(path) else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}

    print(f"\nDownloading: {filename} (already have: {existing // 1024 // 1024} MB)")
    r = requests.get(url, headers=headers, stream=True, timeout=30)

    if r.status_code == 416:
        print("  Already complete, skipping.")
        return
    if r.status_code not in (200, 206):
        print(f"  Error: HTTP {r.status_code}")
        return

    total = int(r.headers.get("content-length", 0)) + existing
    downloaded = existing

    with open(path, "ab" if existing else "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                pct = downloaded / total * 100 if total else 0
                mb = downloaded // 1024 // 1024
                print(f"\r  {mb} MB / {total // 1024 // 1024} MB ({pct:.1f}%)", end="", flush=True)
    print(f"\n  Done: {filename}")


for name in FILES:
    download(name)

print(f"\nAll files downloaded. Model '{MODEL}' ready.")
print(f"Path: {CACHE_DIR}")
print(f"\nTo use a different model later, open ghosttype Settings → Model and pick one.")
print(f"Or re-run: python download_model.py {{tiny|base|small|medium|large-v3}}")
