# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_cp2 import (
    OUTPUT_COLUMNS,
    _assert_planner_delay_matches_metadata,
    _parse_run,
    extract_resolved_config,
)


def _write_resolved_config(run_dir: Path, planner_delay_us: int, **overrides: object) -> None:
    config = {
        "planner_delay_us": 0,
        "runtime": {
            "simulation_config": {
                "planner_delay_us": planner_delay_us,
                "route_start_offset_m": overrides.get("route_start_offset_m", 0.0),
                "force_gt_duration_us": overrides.get("force_gt_duration_us", 1_700_000),
            }
        },
    }
    with (run_dir / "resolved_config.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle)


def _write_run_args(run_dir: Path, planner_delay_us: int) -> None:
    run_args = {
        "runtime": {
            "simulation_config": {
                "planner_delay_us": planner_delay_us,
                "route_start_offset_m": 4.0,
                "force_gt_duration_us": 1_700_000,
            }
        }
    }
    with (run_dir / "run_args.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(run_args, handle)


def _write_results_summary(run_dir: Path) -> None:
    summary = {
        "rollouts": [
            {
                "rollout_id": "rollout-0",
                "run_name": "test-run",
                "failure_reason": None,
                "random_seed": 7,
                "metrics": {
                    "collision_at_fault": False,
                    "plan_deviation": 1.5,
                },
            }
        ]
    }
    aggregate_dir = run_dir / "aggregate"
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    (aggregate_dir / "results-summary.json").write_text(json.dumps(summary))


def test_extract_resolved_config_ignores_top_level_duplicate(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    run_dir.mkdir()
    _write_resolved_config(run_dir, planner_delay_us=150_000)

    knobs = extract_resolved_config(run_dir)

    assert knobs["planner_delay_us"] == 150_000
    assert knobs["route_start_offset_m"] == 0.0


def test_extract_resolved_config_falls_back_to_wizard_config(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    run_dir.mkdir()
    config = {
        "runtime": {
            "simulation_config": {
                "planner_delay_us": 200_000,
                "route_start_offset_m": 4.5,
            }
        }
    }
    with (run_dir / "wizard-config.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle)

    knobs = extract_resolved_config(run_dir)

    assert knobs["planner_delay_us"] == 200_000
    assert knobs["route_start_offset_m"] == 4.5


def test_assert_planner_delay_matches_metadata_passes(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_003"
    run_dir.mkdir()
    resolved = {"planner_delay_us": 100_000}
    requested = {"planner_delay_us": 100_000}

    _assert_planner_delay_matches_metadata(run_dir, resolved, requested)


def test_assert_planner_delay_matches_metadata_raises_on_mismatch(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_004"
    run_dir.mkdir()
    resolved = {"planner_delay_us": 0}
    requested = {"planner_delay_us": 150_000}

    with pytest.raises(AssertionError, match="planner_delay_us mismatch"):
        _assert_planner_delay_matches_metadata(run_dir, resolved, requested)


def test_parse_run_writes_expected_csv_columns(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_005"
    run_dir.mkdir()
    _write_resolved_config(run_dir, planner_delay_us=125_000, route_start_offset_m=4.0)
    _write_run_args(run_dir, planner_delay_us=125_000)
    _write_results_summary(run_dir)

    records = _parse_run(run_dir)
    assert len(records) == 1

    df = pd.DataFrame(records)
    for column in OUTPUT_COLUMNS:
        assert column in df.columns

    assert df.loc[0, "planner_delay_us"] == 125_000
    assert df.loc[0, "route_start_offset_m"] == 4.0
    assert df.loc[0, "fault_label"] == "none"

    csv_path = tmp_path / "results.csv"
    df.to_csv(csv_path, index=False)
    header_columns = csv_path.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header_columns[: len(OUTPUT_COLUMNS)] == list(OUTPUT_COLUMNS)
    assert "planner_delay_us" in header_columns
    assert "plan_deviation" in header_columns
