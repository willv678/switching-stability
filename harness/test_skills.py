"""
Unit tests for skills and step records.
"""

import pytest
from skills import Skill, StepRecord


def test_skill_enum_values():
    """Test that all required skills are present."""
    assert Skill.CONFIGURE.value == "CONFIGURE"
    assert Skill.LAUNCH.value == "LAUNCH"
    assert Skill.RE_RUN.value == "RE-RUN"
    assert Skill.RESTART_CLEANUP.value == "RESTART_CLEANUP"
    assert Skill.ACCEPT.value == "ACCEPT"


def test_all_skills_in_enum():
    """Test that all expected skills are defined."""
    skills = {skill.value for skill in Skill}
    expected = {"CONFIGURE", "LAUNCH", "RE-RUN", "RESTART_CLEANUP", "ACCEPT"}
    assert skills == expected


def test_step_record_creation():
    """Test basic StepRecord creation."""
    record = StepRecord(
        skill=Skill.CONFIGURE,
        params={"context_length": 8, "scene": "test.json"},
        k_status="accepted",
    )
    assert record.skill == Skill.CONFIGURE
    assert record.params == {"context_length": 8, "scene": "test.json"}
    assert record.k_status == "accepted"


def test_step_record_all_skills():
    """Test StepRecord with each skill type."""
    for skill in Skill:
        record = StepRecord(
            skill=skill, params={"test": "value"}, k_status="ok"
        )
        assert record.skill == skill


def test_step_record_empty_params():
    """Test StepRecord with empty params."""
    record = StepRecord(skill=Skill.ACCEPT, params={}, k_status="success")
    assert record.params == {}


def test_step_record_complex_params():
    """Test StepRecord with nested and complex params."""
    params = {
        "config": {"a": 1, "b": [1, 2, 3]},
        "list": [1, "string", {"nested": True}],
        "value": None,
    }
    record = StepRecord(skill=Skill.LAUNCH, params=params, k_status="ok")
    assert record.params == params


def test_step_record_immutable():
    """Test that StepRecord is frozen (immutable)."""
    record = StepRecord(
        skill=Skill.LAUNCH, params={"test": 1}, k_status="ok"
    )
    with pytest.raises(AttributeError):
        record.skill = Skill.ACCEPT


def test_step_record_k_status_variants():
    """Test StepRecord with different K status values."""
    statuses = ["accepted", "rejected", "error", "success", "failure"]
    for status in statuses:
        record = StepRecord(
            skill=Skill.RE_RUN, params={}, k_status=status
        )
        assert record.k_status == status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
