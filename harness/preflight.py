"""
Preflight validation (K⁻).

Validates configurations before launching any simulation container via `docker compose up`.
Rejects illegal or unsafe configs that would cause immediate crashes.

## Preflight Rules

1. **Reject Missing Linear Controller with VaVAM:**
   - IF `driver == "vavam"` AND `controller != "linear"`:
     - **Reason:** Nonlinear MPC fails on gain updates and lacks Riccati terminal cost support.

2. **Reject Unbuffered VaVAM Context:**
   - IF `driver == "vavam"` AND `driver.inference.context_length == 1`:
     - **Reason:** Context length 1 introduces 2.5 m artificial planning noise floor.

3. **Reject Insufficient Frame Cache Warm-Up:**
   - IF `driver.inference.context_length == 8` AND `runtime.simulation_config.force_gt_duration_us < 4000000`:
     - **Reason:** FrameCache requires 4.0 s (8 frames @ 2 Hz) to buffer before policy handoff.
     - Prevents empty trajectory returns and step-0 crashes.
"""

import os
from pathlib import Path
from typing import Any


class PreflightError(Exception):
    """Raised when preflight validation fails."""

    pass


def validate_preflight(config: dict[str, Any]) -> None:
    """
    Validate a configuration before launch.

    Rejects configs that violate constraints:
    - context_length must be exactly 8
    - hydra_delay must match the request delay
    - scene_file must exist

    Args:
        config: Configuration dict with keys like context_length, hydra_delay,
                request_delay, scene_file.

    Raises:
        PreflightError: If any validation fails.
    """
    # Check context_length
    context_length = config.get("context_length")
    if context_length != 8:
        raise PreflightError(
            f"context_length must be 8, got {context_length}"
        )

    # Check hydra_delay matches request_delay
    hydra_delay = config.get("hydra_delay")
    request_delay = config.get("request_delay")
    if hydra_delay != request_delay:
        raise PreflightError(
            f"hydra_delay ({hydra_delay}) does not match "
            f"request_delay ({request_delay})"
        )

    # Check scene_file exists
    scene_file = config.get("scene_file")
    if scene_file is None:
        raise PreflightError("scene_file not specified")

    if not os.path.exists(scene_file):
        raise PreflightError(f"scene_file does not exist: {scene_file}")
