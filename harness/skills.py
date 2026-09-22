"""
Skill menu and step record for the agent loop.

Defines the finite menu of skills the agent can emit and the step record
that captures each decision point.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class Skill(Enum):
    """The finite skill menu the agent can emit."""

    CONFIGURE = "CONFIGURE"
    LAUNCH = "LAUNCH"
    RE_RUN = "RE-RUN"
    RESTART_CLEANUP = "RESTART_CLEANUP"
    ACCEPT = "ACCEPT"


@dataclass(frozen=True)
class StepRecord:
    """A single step in the agent loop.

    Attributes:
        skill: The skill (action) chosen.
        params: Arbitrary parameters passed to the skill.
        k_status: The K status that produced this step.
                  K⁻ (preflight) rejects illegal skills or unsafe configs.
                  K⁺ (postflight) turns crashes/failures into structured status.
    """

    skill: Skill
    params: dict[str, Any]
    k_status: str
