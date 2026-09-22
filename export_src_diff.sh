#!/usr/bin/env bash
# Write AlpaSim src/ changes vs origin/main into patches/alpasim-src.diff.
# Includes untracked files under src/ as new-file diffs.
set -euo pipefail

OVERLAY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALPASIM_ROOT="$(cd "$OVERLAY_ROOT/.." && pwd)"
OUT="$OVERLAY_ROOT/patches/alpasim-src.diff"
mkdir -p "$OVERLAY_ROOT/patches"
git -C "$ALPASIM_ROOT" diff origin/main -- src/ > "$OUT"
while IFS= read -r -d '' f; do
  git -C "$ALPASIM_ROOT" diff --no-index -- /dev/null "$f" >> "$OUT" || true
done < <(git -C "$ALPASIM_ROOT" ls-files -z --others --exclude-standard -- src/)
echo "Wrote $OUT"
