"""
Hand-written recovery policy.

A deterministic policy for the skill menu: CONFIGURE, LAUNCH, RE-RUN, RESTART_CLEANUP, ACCEPT.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from postflight import PostflightStatus
from skills import Skill


class RunStatus(Enum):
    """Status of a run attempt."""

    PREFLIGHT_REJECTED = "preflight_rejected"  # K⁻ rejected the config
    LAUNCH_FAILED = "launch_failed"  # Process died before completion
    METRICS_MISSING = "metrics_missing"  # Postflight found no metrics
    PROCESS_DEAD = "process_dead"  # Run directory exists but invalid
    AT_FAULT_COLLISION = "at_fault_collision"  # Metrics show collision
    CLEAN_RUN = "clean_run"  # Metrics valid, no collision


@dataclass(frozen=True)
class PolicyDecision:
    """Decision from the hand-written policy.

    Attributes:
        skill: The next skill to execute.
        reason: Human-readable explanation.
    """

    skill: Skill
    reason: str


def decide_recovery(
    preflight_error: Optional[str],
    postflight_status: Optional[PostflightStatus],
    attempt_count: int = 1,
) -> PolicyDecision:
    """
    Decide the next skill based on run state.

    Rules:
    - If preflight rejected config: never launch. Return CONFIGURE (to fix).
    - If postflight failed (metrics missing): RE-RUN once, then RESTART_CLEANUP.
    - If postflight shows valid metrics (with or without collision): ACCEPT.
      A collision is a valid run with data the paper keeps.
    - If launch failed (postflight_status is None): RE-RUN once, then RESTART_CLEANUP.

    Args:
        preflight_error: Error message from K⁻, or None if preflight passed.
        postflight_status: Result from K⁺, or None if run failed/incomplete.
        attempt_count: How many times we've tried to RE-RUN (1-indexed).

    Returns:
        PolicyDecision with the next skill and reason.
    """
    # Rule 1: Preflight rejected config
    if preflight_error is not None:
        return PolicyDecision(
            skill=Skill.CONFIGURE,
            reason=f"Preflight rejected: {preflight_error}. Reconfigure.",
        )

    # Rule 2: Launch failed (postflight is None or couldn't be run)
    if postflight_status is None:
        if attempt_count == 1:
            return PolicyDecision(
                skill=Skill.RE_RUN,
                reason="Launch failed. Attempting retry.",
            )
        else:
            return PolicyDecision(
                skill=Skill.RESTART_CLEANUP,
                reason=f"Launch failed after {attempt_count} attempts. Restart and cleanup.",
            )

    # Rule 3: Metrics missing (no valid data was written)
    if not postflight_status.success:
        if attempt_count == 1:
            return PolicyDecision(
                skill=Skill.RE_RUN,
                reason=f"Metrics missing: {postflight_status.error}. Retrying.",
            )
        else:
            return PolicyDecision(
                skill=Skill.RESTART_CLEANUP,
                reason=f"Metrics still missing after {attempt_count} attempts. Restart.",
            )

    # Rule 4: Valid postflight (success=True), regardless of collision
    # A collision is real data the paper keeps. Do not re-run.
    return PolicyDecision(
        skill=Skill.ACCEPT,
        reason=f"Metrics valid ({postflight_status.at_fault_collision=}). Accepting run.",
    )
