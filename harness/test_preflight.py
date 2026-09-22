"""
Unit tests for preflight validation (K⁻).
"""

import os
import tempfile
from pathlib import Path

import pytest

from preflight import PreflightError, validate_preflight


@pytest.fixture
def temp_scene_file():
    """Create a temporary scene file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{}")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_reject_wrong_context_length():
    """Test rejection when context_length is not 8."""
    config = {
        "context_length": 1,
        "hydra_delay": 10,
        "request_delay": 10,
        "scene_file": "/tmp/test.json",
    }
    with pytest.raises(PreflightError, match="context_length must be 8"):
        validate_preflight(config)


def test_reject_context_length_16():
    """Test rejection when context_length is 16."""
    config = {
        "context_length": 16,
        "hydra_delay": 10,
        "request_delay": 10,
        "scene_file": "/tmp/test.json",
    }
    with pytest.raises(PreflightError, match="context_length must be 8"):
        validate_preflight(config)


def test_reject_hydra_delay_mismatch():
    """Test rejection when hydra_delay does not match request_delay."""
    config = {
        "context_length": 8,
        "hydra_delay": 15,
        "request_delay": 10,
        "scene_file": "/tmp/test.json",
    }
    with pytest.raises(
        PreflightError, match="hydra_delay.*does not match.*request_delay"
    ):
        validate_preflight(config)


def test_reject_missing_scene_file():
    """Test rejection when scene_file does not exist."""
    config = {
        "context_length": 8,
        "hydra_delay": 10,
        "request_delay": 10,
        "scene_file": "/nonexistent/path/to/scene.json",
    }
    with pytest.raises(PreflightError, match="scene_file does not exist"):
        validate_preflight(config)


def test_accept_valid_config(temp_scene_file):
    """Test acceptance of a valid configuration."""
    config = {
        "context_length": 8,
        "hydra_delay": 10,
        "request_delay": 10,
        "scene_file": temp_scene_file,
    }
    # Should not raise
    validate_preflight(config)


def test_reject_missing_scene_file_key():
    """Test rejection when scene_file key is missing."""
    config = {
        "context_length": 8,
        "hydra_delay": 10,
        "request_delay": 10,
    }
    with pytest.raises(PreflightError, match="scene_file not specified"):
        validate_preflight(config)


def test_accept_valid_config_with_different_delays(temp_scene_file):
    """Test acceptance with matching delays of different values."""
    config = {
        "context_length": 8,
        "hydra_delay": 25,
        "request_delay": 25,
        "scene_file": temp_scene_file,
    }
    validate_preflight(config)


def test_reject_context_length_zero():
    """Test rejection when context_length is 0."""
    config = {
        "context_length": 0,
        "hydra_delay": 10,
        "request_delay": 10,
        "scene_file": "/tmp/test.json",
    }
    with pytest.raises(PreflightError, match="context_length must be 8"):
        validate_preflight(config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
