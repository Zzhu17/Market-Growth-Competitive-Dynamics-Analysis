#!/usr/bin/env python
"""Download MRTS files listed in config/data_sources.yaml (no scraping)."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "data_sources.yaml"
RAW_DIR = REPO_ROOT / "data" / "raw" / "mtrs"


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or "download.bin"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        h = hashlib.sha256()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                h.update(chunk)
    print(f"saved {dest} sha256={h.hexdigest()}")


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"missing config: {CONFIG_PATH}", file=sys.stderr)
        return 1

    cfg = yaml.safe_load(CONFIG_PATH.read_text())
    src = cfg.get("mtrs_national_sales", {})
    files = src.get("files") or []
    if not files:
        print("No MRTS file URLs configured. Add URLs under mtrs_national_sales.files in config/data_sources.yaml.")
        return 1

    for url in files:
        filename = _filename_from_url(url)
        dest = RAW_DIR / filename
        _download(url, dest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
