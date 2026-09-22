#!/usr/bin/env bash
set -euo pipefail

ALPASIM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ALPASIM_ROOT"

echo "[*] Cleaning dataset..."
grep '"status": "COMPLETED"' autolab_finetune_dataset.jsonl > autolab_dataset_clean.jsonl

echo "[*] Generating updated failure boundary plot..."
uv run python research/harness/plot_boundaries.py

echo "[*] Formatting SFT training and validation sets..."
uv run python research/harness/format_sft.py

echo "[*] Post-processing complete."
