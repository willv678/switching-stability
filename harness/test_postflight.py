"""
Unit tests for postflight validation (K⁺).
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from postflight import PostflightStatus, validate_postflight


@pytest.fixture
def temp_run_dir_no_metrics():
    """Create a temporary run directory without metrics file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_run_dir_with_metrics_no_collision():
    """Create a temporary run directory with valid metrics but no collision."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir)

        # Create minimal valid metrics DataFrame
        data = {
            "name": [
                "collision_any",
                "collision_front",
                "collision_rear",
                "tracking_error",
            ],
            "timestamps_us": [[1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3]],
            "values": [[False, False, False], [False, False, False], [False, False, False], [1.5, 1.6, 1.7]],
            "valid": [[True, True, True], [True, True, True], [True, True, True], [True, True, True]],
            "time_aggregation": ["last", "last", "last", "mean"],
            "clipgt_id": ["clip1", "clip1", "clip1", "clip1"],
            "rollout_id": ["roll1", "roll1", "roll1", "roll1"],
            "run_uuid": ["uuid1", "uuid1", "uuid1", "uuid1"],
            "run_name": ["test_run", "test_run", "test_run", "test_run"],
        }
        df = pd.DataFrame(data)
        df.to_parquet(run_path / "metrics.parquet")
        yield str(run_path)


@pytest.fixture
def temp_run_dir_with_at_fault_collision():
    """Create a temporary run directory with at-fault collision."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir)

        # Create metrics with collision
        data = {
            "name": ["collision_any", "collision_front", "collision_rear", "tracking_error"],
            "timestamps_us": [[1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3]],
            "values": [
                [False, True, False],  # collision_any
                [False, True, False],  # collision_front
                [False, False, False],  # collision_rear
                [1.5, 1.6, 1.7],  # tracking_error
            ],
            "valid": [[True, True, True], [True, True, True], [True, True, True], [True, True, True]],
            "time_aggregation": ["last", "last", "last", "mean"],
            "clipgt_id": ["clip1", "clip1", "clip1", "clip1"],
            "rollout_id": ["roll1", "roll1", "roll1", "roll1"],
            "run_uuid": ["uuid1", "uuid1", "uuid1", "uuid1"],
            "run_name": ["test_run", "test_run", "test_run", "test_run"],
        }
        df = pd.DataFrame(data)
        df.to_parquet(run_path / "metrics.parquet")
        yield str(run_path)


@pytest.fixture
def temp_run_dir_with_rear_collision():
    """Create a temporary run directory with rear collision."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_path = Path(tmpdir)

        # Create metrics with rear collision
        data = {
            "name": ["collision_any", "collision_front", "collision_rear", "tracking_error"],
            "timestamps_us": [[1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3]],
            "values": [
                [False, False, False],  # collision_any
                [False, False, False],  # collision_front
                [False, True, False],  # collision_rear
                [1.5, 1.6, 1.7],  # tracking_error
            ],
            "valid": [[True, True, True], [True, True, True], [True, True, True], [True, True, True]],
            "time_aggregation": ["last", "last", "last", "mean"],
            "clipgt_id": ["clip1", "clip1", "clip1", "clip1"],
            "rollout_id": ["roll1", "roll1", "roll1", "roll1"],
            "run_uuid": ["uuid1", "uuid1", "uuid1", "uuid1"],
            "run_name": ["test_run", "test_run", "test_run", "test_run"],
        }
        df = pd.DataFrame(data)
        df.to_parquet(run_path / "metrics.parquet")
        yield str(run_path)


def test_fail_missing_metrics(temp_run_dir_no_metrics):
    """Test failure when metrics file is missing."""
    status = validate_postflight(temp_run_dir_no_metrics)
    assert status.success is False
    assert "metrics file not found" in status.error


def test_fail_nonexistent_run_dir():
    """Test failure when run directory does not exist."""
    status = validate_postflight("/nonexistent/path/to/run")
    assert status.success is False
    assert "does not exist" in status.error


def test_success_no_collision(temp_run_dir_with_metrics_no_collision):
    """Test success with valid metrics and no collision."""
    status = validate_postflight(temp_run_dir_with_metrics_no_collision)
    assert status.success is True
    assert status.at_fault_collision is False
    assert status.rear_contact is False
    assert status.error is None


def test_detect_at_fault_collision(temp_run_dir_with_at_fault_collision):
    """Test detection of at-fault collision."""
    status = validate_postflight(temp_run_dir_with_at_fault_collision)
    assert status.success is True
    assert status.at_fault_collision is True
    assert status.rear_contact is False


def test_detect_rear_contact(temp_run_dir_with_rear_collision):
    """Test detection of rear contact."""
    status = validate_postflight(temp_run_dir_with_rear_collision)
    assert status.success is True
    assert status.at_fault_collision is False
    assert status.rear_contact is True


def test_real_test_vavam_ctx8():
    """Test with the actual diag/test_vavam_ctx8 run."""
    run_dir = "/home/willvarner/alpasim/diag/test_vavam_ctx8/rollouts/clipgt-01d503d4-449b-46fc-8d78-9085e70d3554/c45514d0-b698-11f1-b414-6348a5c2a655"
    status = validate_postflight(run_dir)
    assert status.success is True
    # This run should have metrics
    assert status.error is None
    # Check for collision and solver status
    assert isinstance(status.at_fault_collision, bool)
    assert isinstance(status.rear_contact, bool)


def test_postflight_status_frozen():
    """Test that PostflightStatus is immutable."""
    status = PostflightStatus(success=True)
    with pytest.raises(AttributeError):
        status.success = False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
