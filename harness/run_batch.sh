#!/usr/bin/env bash
set -euo pipefail

ALPASIM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ALPASIM_ROOT"

echo "[*] Launching Autolab Checkpoint 2 batch execution..."
uv run python research/harness/autolab_loop.py
