"""
Postflight validation (K⁺).

Reads a finished run directory and validates the outcome. Turns crashes, core dumps,
and garbage metrics into structured status.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class PostflightStatus:
    """Result of postflight validation.

    Attributes:
        success: True if run completed successfully with valid metrics.
        at_fault_collision: True if ego caused a collision (collision_any or collision_front).
        rear_contact: True if ego collided with rear (collision_rear).
        solver_status: The MPC solver status if controller CSV exists, else None.
        error: Human-readable error message if validation failed, else None.
    """

    success: bool
    at_fault_collision: Optional[bool] = None
    rear_contact: Optional[bool] = None
    solver_status: Optional[str] = None
    error: Optional[str] = None


def validate_postflight(run_dir: str) -> PostflightStatus:
    """
    Validate a finished run directory.

    Reads metrics and controller CSV to assess the run. Fails if metrics are missing.

    Args:
        run_dir: Path to the finished run directory.

    Returns:
        PostflightStatus with outcome and any relevant error details.
    """
    run_path = Path(run_dir)

    if not run_path.is_dir():
        return PostflightStatus(
            success=False, error=f"run_dir does not exist: {run_dir}"
        )

    # Find metrics file
    metrics_file = None
    for pattern in ["metrics.parquet", "metrics.pkl"]:
        candidate = run_path / pattern
        if candidate.exists():
            metrics_file = candidate
            break

    if metrics_file is None:
        return PostflightStatus(
            success=False, error="metrics file not found (no metrics.parquet)"
        )

    # Load metrics
    try:
        if metrics_file.suffix == ".parquet":
            df = pd.read_parquet(metrics_file)
        else:
            df = pd.read_pickle(metrics_file)
    except Exception as e:
        return PostflightStatus(
            success=False, error=f"failed to load metrics: {e}"
        )

    # Check for at-fault collision
    at_fault = False
    rear = False

    # collision_any or collision_front indicates at-fault
    for metric_name in ["collision_any", "collision_front"]:
        if metric_name in df["name"].values:
            metric_data = df[df["name"] == metric_name]
            if len(metric_data) > 0:
                # Check if any value is True/1
                values = metric_data["values"].iloc[0]
                if isinstance(values, (list, tuple)):
                    if any(v for v in values):
                        at_fault = True
                        break
                else:
                    # Handle numpy arrays and scalars
                    try:
                        if hasattr(values, '__iter__') and not isinstance(values, str):
                            if any(values):
                                at_fault = True
                                break
                        elif values:
                            at_fault = True
                            break
                    except (TypeError, ValueError):
                        # If we can't iterate, treat as scalar
                        if values:
                            at_fault = True
                            break

    # Check for rear-contact
    if "collision_rear" in df["name"].values:
        metric_data = df[df["name"] == "collision_rear"]
        if len(metric_data) > 0:
            values = metric_data["values"].iloc[0]
            if isinstance(values, (list, tuple)):
                if any(v for v in values):
                    rear = True
            else:
                # Handle numpy arrays and scalars
                try:
                    if hasattr(values, '__iter__') and not isinstance(values, str):
                        if any(values):
                            rear = True
                    elif values:
                        rear = True
                except (TypeError, ValueError):
                    # If we can't iterate, treat as scalar
                    if values:
                        rear = True

    # Check for controller CSV and extract solver status
    solver_status = None
    controller_dir = run_path.parent.parent / "controller"
    if controller_dir.exists():
        # Find the controller CSV for this run
        csv_files = list(controller_dir.glob("*.csv"))
        if csv_files:
            controller_csv = csv_files[0]
            try:
                controller_df = pd.read_csv(controller_csv)
                if "status" in controller_df.columns:
                    statuses = controller_df["status"].unique()
                    # Combine all unique statuses
                    solver_status = ",".join(str(s) for s in statuses)
            except Exception:
                pass  # Ignore controller CSV errors

    return PostflightStatus(
        success=True,
        at_fault_collision=at_fault,
        rear_contact=rear,
        solver_status=solver_status,
    )
