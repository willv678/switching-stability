#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 NVIDIA Corporation

"""§4.5 empirical planner-delay sweep for tracking error."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml

ALPASIM_ROOT = Path(__file__).resolve().parents[2]
DELAYS_US = (0, 50_000, 100_000, 150_000, 200_000)
OUTPUT_PLOT = ALPASIM_ROOT / "diag" / "delay_sweep_tracking_error.png"


def _load_planner_delay_us(run_dir: Path) -> int:
    for name in ("resolved_config.yaml", "wizard-config.yaml", "generated-user-config-0.yaml"):
        config_path = run_dir / name
        if not config_path.exists():
            continue
        with config_path.open(encoding="utf-8") as handle:
            resolved = yaml.safe_load(handle)
        if name == "generated-user-config-0.yaml":
            sim_cfg = resolved["simulation_config"]
        else:
            sim_cfg = resolved["runtime"]["simulation_config"]
        return int(sim_cfg["planner_delay_us"])
    raise FileNotFoundError(f"{run_dir}: no config with planner_delay_us")


def _load_tracking_error(run_dir: Path) -> float:
    parquet_path = run_dir / "aggregate" / "metrics_results.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"{run_dir}: missing {parquet_path}")
    df = pd.read_parquet(parquet_path)
    if "tracking_error" not in df.columns:
        raise KeyError(f"{run_dir}: tracking_error column missing from aggregate parquet")
    return float(df["tracking_error"].iloc[0])


def _steady_state_tracking_error(run_dir: Path, tail: int = 10) -> float:
    metrics_paths = list((run_dir / "rollouts").rglob("metrics.parquet"))
    if not metrics_paths:
        raise FileNotFoundError(f"{run_dir}: no rollout metrics.parquet files")
    df = pd.read_parquet(metrics_paths[0])
    te = df[(df["name"] == "tracking_error") & df["valid"]]
    if te.empty:
        return _load_tracking_error(run_dir)
    return float(te["values"].tail(tail).mean())


def run_wizard(delay_us: int, log_dir: Path, dry_run: bool) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "uv",
        "run",
        "alpasim_wizard",
        "deploy=local",
        "topology=1gpu",
        "driver=vavam",
        "trafficsim=catk",
        "controller=linear",
        f"wizard.log_dir={log_dir}",
        "runtime.simulation_config.n_sim_steps=80",
        "runtime.simulation_config.force_gt_duration_us=0",
        "runtime.simulation_config.control_timestep_us=100000",
        f"runtime.simulation_config.planner_delay_us={delay_us}",
        "runtime.simulation_config.route_start_offset_m=0.0",
    ]
    print(f"Running delay={delay_us} us -> {log_dir}")
    if dry_run:
        print(" ".join(cmd))
        return
    subprocess.run(cmd, cwd=ALPASIM_ROOT, check=True)


def collect_results(base_dir: Path, steady_state: bool) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for delay_us in DELAYS_US:
        run_dir = base_dir / f"delay_{delay_us}"
        if not run_dir.exists():
            raise FileNotFoundError(f"Missing sweep run directory: {run_dir}")
        resolved_delay = _load_planner_delay_us(run_dir)
        if resolved_delay != delay_us:
            raise AssertionError(
                f"{run_dir.name}: planner_delay_us={resolved_delay}, expected {delay_us}"
            )
        tracking_error = (
            _steady_state_tracking_error(run_dir)
            if steady_state
            else _load_tracking_error(run_dir)
        )
        rows.append(
            {
                "run_dir": str(run_dir),
                "planner_delay_us": delay_us,
                "planner_delay_ms": delay_us / 1000.0,
                "tracking_error_m": tracking_error,
            }
        )
    return pd.DataFrame(rows)


def plot_results(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(
        df["planner_delay_ms"],
        df["tracking_error_m"],
        marker="o",
        linewidth=2,
    )
    ax.set_xlabel("Planner delay (ms)")
    ax.set_ylabel("Tracking error (m)")
    ax.set_title("Mean tracking error vs planner delay")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    print(f"Wrote plot to {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=ALPASIM_ROOT / "diag" / "delay_sweep",
        help="Directory containing delay_<us> rollout folders",
    )
    parser.add_argument(
        "--output-plot",
        type=Path,
        default=OUTPUT_PLOT,
        help="Output PNG path",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute wizard rollouts for each delay before collecting metrics",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print wizard commands without executing them",
    )
    parser.add_argument(
        "--aggregate-mean",
        action="store_true",
        help="Use aggregate parquet mean instead of steady-state rollout tail mean",
    )
    args = parser.parse_args()

    if args.run:
        for delay_us in DELAYS_US:
            run_wizard(delay_us, args.base_dir / f"delay_{delay_us}", args.dry_run)
        if args.dry_run:
            return 0

    if args.dry_run:
        return 0

    df = collect_results(args.base_dir, steady_state=not args.aggregate_mean)
    csv_path = args.base_dir / "delay_sweep_results.csv"
    df.to_csv(csv_path, index=False)
    print(df.to_string(index=False))
    print(f"Wrote {csv_path}")
    plot_results(df, args.output_plot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
