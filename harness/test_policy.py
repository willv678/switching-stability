"""
Unit tests for hand-written recovery policy.

Table test covers each status and the skill returned.
"""

import pytest

from policy import PolicyDecision, decide_recovery
from postflight import PostflightStatus
from skills import Skill


class TestPolicyTable:
    """Table test: each status and the skill it returns."""

    @pytest.mark.parametrize(
        "preflight_error,postflight_status,attempt_count,expected_skill",
        [
            # Preflight rejected: always CONFIGURE
            ("context_length must be 8", None, 1, Skill.CONFIGURE),
            ("hydra_delay mismatch", None, 2, Skill.CONFIGURE),
            ("scene_file does not exist", None, 3, Skill.CONFIGURE),
            # Launch failed: RE-RUN once, then RESTART_CLEANUP
            (None, None, 1, Skill.RE_RUN),
            (None, None, 2, Skill.RESTART_CLEANUP),
            (None, None, 3, Skill.RESTART_CLEANUP),
            # Metrics missing: RE-RUN once, then RESTART_CLEANUP
            (
                None,
                PostflightStatus(success=False, error="metrics not found"),
                1,
                Skill.RE_RUN,
            ),
            (
                None,
                PostflightStatus(success=False, error="metrics corrupted"),
                2,
                Skill.RESTART_CLEANUP,
            ),
            # At-fault collision: ACCEPT (valid data, keep it)
            (
                None,
                PostflightStatus(
                    success=True, at_fault_collision=True, rear_contact=False
                ),
                1,
                Skill.ACCEPT,
            ),
            (
                None,
                PostflightStatus(
                    success=True, at_fault_collision=True, rear_contact=False
                ),
                2,
                Skill.ACCEPT,
            ),
            # Rear contact but no front: ACCEPT (valid data)
            (
                None,
                PostflightStatus(
                    success=True, at_fault_collision=False, rear_contact=True
                ),
                1,
                Skill.ACCEPT,
            ),
            # Clean run: ACCEPT
            (
                None,
                PostflightStatus(success=True, at_fault_collision=False),
                1,
                Skill.ACCEPT,
            ),
            (
                None,
                PostflightStatus(
                    success=True,
                    at_fault_collision=False,
                    rear_contact=False,
                    solver_status="solved",
                ),
                1,
                Skill.ACCEPT,
            ),
        ],
        ids=[
            "preflight_reject_ctx8",
            "preflight_reject_hydra",
            "preflight_reject_scene",
            "launch_fail_1st",
            "launch_fail_2nd",
            "launch_fail_3rd",
            "metrics_missing_1st",
            "metrics_missing_2nd",
            "collision_accept_1st",
            "collision_accept_2nd",
            "rear_contact_accept",
            "clean_run",
            "clean_with_solver",
        ],
    )
    def test_policy_decision(
        self,
        preflight_error,
        postflight_status,
        attempt_count,
        expected_skill,
    ):
        """Test policy decision for each status."""
        decision = decide_recovery(preflight_error, postflight_status, attempt_count)
        assert decision.skill == expected_skill
        assert isinstance(decision.reason, str)
        assert len(decision.reason) > 0


def test_policy_decision_type():
    """Test that decide_recovery returns PolicyDecision."""
    decision = decide_recovery(None, None, 1)
    assert isinstance(decision, PolicyDecision)


def test_policy_decision_reason_nonempty():
    """Test that all decisions have a reason."""
    cases = [
        ("error", None, 1),
        (None, None, 1),
        (
            None,
            PostflightStatus(success=False, error="test"),
            1,
        ),
        (
            None,
            PostflightStatus(success=True, at_fault_collision=True),
            1,
        ),
        (
            None,
            PostflightStatus(success=True, at_fault_collision=False),
            1,
        ),
    ]
    for preflight_error, postflight_status, attempt_count in cases:
        decision = decide_recovery(preflight_error, postflight_status, attempt_count)
        assert decision.reason
        assert isinstance(decision.reason, str)


def test_preflight_error_takes_precedence():
    """Test that preflight error overrides postflight status."""
    # Even if postflight would suggest ACCEPT, preflight error -> CONFIGURE
    decision = decide_recovery(
        preflight_error="bad config",
        postflight_status=PostflightStatus(success=True, at_fault_collision=False),
        attempt_count=1,
    )
    assert decision.skill == Skill.CONFIGURE


def test_attempt_count_matters_for_launch_failure():
    """Test that attempt_count affects decision for launch failures."""
    decision_1 = decide_recovery(None, None, 1)
    decision_2 = decide_recovery(None, None, 2)
    decision_3 = decide_recovery(None, None, 3)

    assert decision_1.skill == Skill.RE_RUN
    assert decision_2.skill == Skill.RESTART_CLEANUP
    assert decision_3.skill == Skill.RESTART_CLEANUP


def test_attempt_count_matters_for_missing_metrics():
    """Test that attempt_count affects decision for missing metrics."""
    status_fail = PostflightStatus(success=False, error="no metrics")

    decision_1 = decide_recovery(None, status_fail, 1)
    decision_2 = decide_recovery(None, status_fail, 2)

    assert decision_1.skill == Skill.RE_RUN
    assert decision_2.skill == Skill.RESTART_CLEANUP


def test_collision_always_accept():
    """Test that collision always returns ACCEPT (valid data to keep)."""
    status = PostflightStatus(success=True, at_fault_collision=True)

    for attempt in [1, 2, 3]:
        decision = decide_recovery(None, status, attempt)
        assert decision.skill == Skill.ACCEPT


def test_clean_run_always_accept():
    """Test that clean run always returns ACCEPT."""
    status = PostflightStatus(
        success=True, at_fault_collision=False, rear_contact=False
    )

    for attempt in [1, 2, 3]:
        decision = decide_recovery(None, status, attempt)
        assert decision.skill == Skill.ACCEPT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
