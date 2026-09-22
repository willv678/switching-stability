"""Analyze Checkpoint 2 batch runs into a tidy, resumable results parquet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml

PROJECT_ROOT = Path.home() / "alpasim"
EXP_DIR = PROJECT_ROOT / "autolab_experiments"
OUTPUT_PARQUET = PROJECT_ROOT / "cp2_results.parquet"
OUTPUT_CSV = PROJECT_ROOT / "cp2_results.csv"
OUTPUT_PLOT = PROJECT_ROOT / "cp2_failure_boundary.png"

KNOB_NAMES = (
    "planner_delay_us",
    "route_start_offset_m",
    "force_gt_duration_us",
)

METADATA_COLUMNS = {
    "run_dir",
    "run_name",
    "rollout_id",
    "config_hash",
    "fault_label",
    "intervention_label",
    "seed",
    *KNOB_NAMES,
}

OUTPUT_COLUMNS = (
    "run_dir",
    "run_name",
    "rollout_id",
    "config_hash",
    "fault_label",
    "intervention_label",
    "seed",
    "planner_delay_us",
    "route_start_offset_m",
    "force_gt_duration_us",
)


def extract_resolved_config(run_dir: Path) -> dict[str, Any]:
    config_path = run_dir / "resolved_config.yaml"
    if not config_path.exists():
        config_path = run_dir / "wizard-config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"{run_dir.name}: missing resolved_config.yaml")

    with config_path.open(encoding="utf-8") as handle:
        resolved = yaml.safe_load(handle)

    try:
        sim_cfg = resolved["runtime"]["simulation_config"]
        planner_delay_us = int(sim_cfg["planner_delay_us"])
    except KeyError as err:
        raise RuntimeError(f"Missing expected key in {config_path}: {err}") from err

    return {
        "planner_delay_us": planner_delay_us,
        "route_start_offset_m": float(sim_cfg.get("route_start_offset_m", 0.0)),
        "force_gt_duration_us": int(sim_cfg.get("force_gt_duration_us", 1_700_000)),
    }


def _parse_hydra_override_value(raw: str) -> int | float:
    if "." in raw:
        return float(raw)
    return int(raw)


def _parse_hydra_overrides(args_text: str) -> dict[str, Any]:
    knob_paths = {
        "planner_delay_us": ("runtime", "simulation_config", "planner_delay_us"),
        "route_start_offset_m": ("runtime", "simulation_config", "route_start_offset_m"),
        "force_gt_duration_us": ("runtime", "simulation_config", "force_gt_duration_us"),
    }
    requested: dict[str, Any] = {}
    for token in args_text.split():
        if "=" not in token:
            continue
        key, raw_value = token.split("=", 1)
        for name, path in knob_paths.items():
            if key == ".".join(path):
                requested[name] = _parse_hydra_override_value(raw_value)
    return requested


def _load_requested_knobs(run_dir: Path) -> dict[str, Any] | None:
    run_args_yaml = run_dir / "run_args.yaml"
    if run_args_yaml.exists():
        with run_args_yaml.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        return extract_resolved_config_from_dict(config)

    run_args_json = run_dir / "run_args.json"
    if run_args_json.exists():
        config = json.loads(run_args_json.read_text())
        return extract_resolved_config_from_dict(config)

    metadata_path = run_dir / "run_metadata.yaml"
    if metadata_path.exists():
        metadata = yaml.safe_load(metadata_path.read_text()) or {}
        run_args = metadata.get("run_args")
        if isinstance(run_args, str) and run_args not in {"", "unknownArgs"}:
            requested = _parse_hydra_overrides(run_args)
            if requested:
                return requested

    return None


def extract_resolved_config_from_dict(config: dict[str, Any]) -> dict[str, Any]:
    sim_cfg = config["runtime"]["simulation_config"]
    return {
        "planner_delay_us": int(sim_cfg["planner_delay_us"]),
        "route_start_offset_m": float(sim_cfg.get("route_start_offset_m", 0.0)),
        "force_gt_duration_us": int(sim_cfg.get("force_gt_duration_us", 1_700_000)),
    }


def _assert_planner_delay_matches_metadata(
    run_dir: Path,
    resolved_knobs: dict[str, Any],
    requested_knobs: dict[str, Any] | None,
) -> None:
    if requested_knobs is None or "planner_delay_us" not in requested_knobs:
        return

    expected = int(requested_knobs["planner_delay_us"])
    actual = int(resolved_knobs["planner_delay_us"])
    if actual != expected:
        raise AssertionError(
            f"{run_dir.name}: planner_delay_us mismatch: "
            f"resolved={actual}, metadata={expected}"
        )


def _config_hash(resolved_knobs: dict[str, Any]) -> str:
    payload = json.dumps(resolved_knobs, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _derive_fault_label(metrics: dict[str, Any], failure_reason: str | None) -> str:
    if failure_reason:
        return failure_reason
    if metrics.get("collision_at_fault"):
        return "collision_at_fault"
    if metrics.get("offroad"):
        return "offroad"
    if metrics.get("collision_any"):
        return "collision_any"
    return "none"


def _derive_intervention_label(resolved_knobs: dict[str, Any]) -> str:
    labels: list[str] = []
    if resolved_knobs["planner_delay_us"] > 0:
        labels.append("system:latency")
    if resolved_knobs["route_start_offset_m"] != 0:
        labels.append("env:spawn")
    if resolved_knobs["force_gt_duration_us"] != 1_700_000:
        labels.append("warmup:force_gt")
    return ",".join(labels) if labels else "none"


def _metric_columns(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metrics.items()
        if key not in METADATA_COLUMNS and not str(key).endswith("_std")
    }


def _load_results_summary(run_dir: Path) -> dict[str, Any] | None:
    summary_path = run_dir / "aggregate" / "results-summary.json"
    if not summary_path.exists():
        return None
    return json.loads(summary_path.read_text())


def _load_rollout_rows(run_dir: Path) -> list[dict[str, Any]]:
    summary = _load_results_summary(run_dir)
    if summary and summary.get("rollouts"):
        rows: list[dict[str, Any]] = []
        for rollout in summary["rollouts"]:
            metrics = dict(rollout.get("metrics", {}))
            rows.append(
                {
                    "rollout_id": rollout.get("rollout_id"),
                    "run_name": rollout.get("run_name"),
                    "failure_reason": rollout.get("failure_reason"),
                    "seed": rollout.get("random_seed", rollout.get("session_seed", 0)),
                    "metrics": metrics,
                }
            )
        return rows

    parquet_candidates = [
        run_dir / "aggregate" / "metrics_results.parquet",
        run_dir / "aggregate" / "metrics_unprocessed.parquet",
    ]
    parquet_candidates.extend(run_dir.glob("rollouts/**/metrics.parquet"))
    parquet_path = next((path for path in parquet_candidates if path.exists()), None)
    if parquet_path is None:
        return []

    metrics_df = pd.read_parquet(parquet_path)
    if metrics_df.empty:
        return []

    row = metrics_df.iloc[0].to_dict()
    return [
        {
            "rollout_id": None,
            "run_name": row.get("run_name"),
            "failure_reason": None,
            "seed": 0,
            "metrics": {
                key: value
                for key, value in row.items()
                if not str(key).endswith("_std")
            },
        }
    ]


def _parse_run(run_dir: Path) -> list[dict[str, Any]]:
    resolved_knobs = extract_resolved_config(run_dir)
    requested_knobs = _load_requested_knobs(run_dir)
    _assert_planner_delay_matches_metadata(run_dir, resolved_knobs, requested_knobs)

    rollout_rows = _load_rollout_rows(run_dir)
    if not rollout_rows:
        return []

    config_hash = _config_hash(resolved_knobs)
    intervention_label = _derive_intervention_label(resolved_knobs)
    records: list[dict[str, Any]] = []

    for rollout in rollout_rows:
        metrics = rollout["metrics"]
        record = {
            "run_dir": run_dir.name,
            "run_name": rollout.get("run_name"),
            "rollout_id": rollout.get("rollout_id"),
            "config_hash": config_hash,
            "fault_label": _derive_fault_label(metrics, rollout.get("failure_reason")),
            "intervention_label": intervention_label,
            "seed": rollout.get("seed", 0),
            **resolved_knobs,
            **_metric_columns(metrics),
        }
        records.append(record)

    return records


def _collect_runs(
    exp_dir: Path,
    output_parquet: Path,
    max_runs: int | None = None,
) -> pd.DataFrame:
    existing_run_dirs: set[str] = set()
    existing_frames: list[pd.DataFrame] = []
    if output_parquet.exists():
        existing_df = pd.read_parquet(output_parquet)
        existing_run_dirs = set(existing_df["run_dir"].astype(str))
        existing_frames.append(existing_df)

    all_runs = sorted(
        [path for path in exp_dir.glob("run_*") if path.is_dir()],
        key=lambda path: path.stat().st_mtime,
    )
    if max_runs is not None:
        all_runs = all_runs[-max_runs:]

    new_records: list[dict[str, Any]] = []
    for run_dir in all_runs:
        if run_dir.name in existing_run_dirs:
            continue
        new_records.extend(_parse_run(run_dir))

    frames = existing_frames
    if new_records:
        frames.append(pd.DataFrame(new_records))

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def _plot_failure_boundary(results: pd.DataFrame, output_plot: Path) -> None:
    if results.empty:
        return

    crashes = results[results["fault_label"].isin(
        {"collision_at_fault", "collision_any", "offroad_or_collision_at_fault"}
    )]
    safes = results[~results.index.isin(crashes.index)]

    plt.figure(figsize=(8, 5))
    if not safes.empty:
        plt.scatter(
            safes["route_start_offset_m"],
            safes["planner_delay_us"] / 1000.0,
            c="mediumseagreen",
            label=f"Safe (n={len(safes)})",
            s=70,
            alpha=0.85,
        )
    if not crashes.empty:
        plt.scatter(
            crashes["route_start_offset_m"],
            crashes["planner_delay_us"] / 1000.0,
            c="crimson",
            marker="x",
            label=f"Collision (n={len(crashes)})",
            s=90,
            linewidths=2,
        )

    plt.title("VaVAM Planner Robustness Boundary (Warmup = 2.5s)", fontsize=12)
    plt.xlabel("Route Start Offset (m)", fontsize=10)
    plt.ylabel("Injected Planner Latency (ms)", fontsize=10)
    plt.xlim(3.3, 5.7)
    plt.ylim(30, 220)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(output_plot, dpi=300)


def main() -> None:
    results = _collect_runs(EXP_DIR, OUTPUT_PARQUET)
    print(f"Total Parsed Checkpoint 2 Runs: {len(results)}")
    if results.empty:
        raise SystemExit(1)

    results.to_parquet(OUTPUT_PARQUET, index=False)
    results.to_csv(OUTPUT_CSV, index=False)
    print(f"[*] Tidy results saved to {OUTPUT_PARQUET}")
    print(f"[*] CSV export saved to {OUTPUT_CSV}")

    crashes = results[
        results["fault_label"].isin(
            {"collision_at_fault", "collision_any", "offroad_or_collision_at_fault"}
        )
    ]
    safes = results[~results.index.isin(crashes.index)]

    print(
        f"Collision Count: {len(crashes)} / {len(results)} "
        f"({len(crashes) / len(results):.1%})"
    )
    if not safes.empty and "plan_deviation" in safes:
        print(f"Mean Plan Deviation (Safe): {safes['plan_deviation'].mean():.2f}m")
    if not crashes.empty and "plan_deviation" in crashes:
        print(f"Mean Plan Deviation (Crash): {crashes['plan_deviation'].mean():.2f}m")
        if "open_loop_collision" in crashes:
            print(f"Mean Open-Loop Collision Rate: {crashes['open_loop_collision'].mean():.2f}")

    preview_cols = [
        col
        for col in [
            "run_dir",
            "route_start_offset_m",
            "planner_delay_us",
            "fault_label",
            "collision_at_fault",
        ]
        if col in results.columns
    ]
    print("\nSample of Extracted Configurations:")
    print(results[preview_cols].head(10).to_string(index=False))

    _plot_failure_boundary(results, OUTPUT_PLOT)
    print(f"\n[*] Boundary plot saved to {OUTPUT_PLOT}")


if __name__ == "__main__":
    main()
