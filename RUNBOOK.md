# Runbook

Commands Griffin can launch, and the checks that decide whether a run counts.
All commands run from `/home/willvarner/alpasim`. Python is `uv run`, never an
activated venv.

A run counts only if all three are true:

1. The process exited 0.
2. `aggregate/metrics_results.txt` exists.
3. The requested override is the value in the resolved config, not the value you
   typed. See the check at the bottom.

If any of the three fails, write `FAIL` and the last 30 lines of the log in the
batch CSV. Do not rerun with a guessed flag.

## Nominal rollout

Reactive traffic, no delay, no route offset. This is the reference condition.

```bash
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam trafficsim=catk \
  runtime.simulation_config.route_start_offset_m=0.0 \
  runtime.simulation_config.planner_delay_us=0 \
  wizard.log_dir=./diag/NOMINAL_NAME
```

## Linear MPC, the plant the paper uses

```bash
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam trafficsim=catk \
  controller=linear controller.terminal_cost=stage \
  runtime.simulation_config.route_start_offset_m=0.0 \
  runtime.simulation_config.planner_delay_us=0 \
  wizard.log_dir=./diag/LINEAR_NAME
```

Riccati terminal cost is the same command with `controller.terminal_cost=riccati`.

## Frozen perception

Human plan instead of VaVAM, for the whole rollout. Used in Phase B.

```bash
uv run alpasim_wizard deploy=local topology=1gpu driver=vavam trafficsim=catk \
  +exp=sim/force_gt \
  wizard.log_dir=./diag/FORCE_GT_NAME
```

## Scene qualification

Goal: 20 scenes that finish and write metrics. One rollout per scene, nominal
command above, `wizard.log_dir=./diag/scenes/<scene-id>`. Record:

```text
scene_id, log_dir, exit_code, has_metrics, collision_at_fault, dist_traveled_m, notes
```

Stop at 20 passes. A scene that crashes the wizard is a fail, not a driving collision.
Leave the `.usdz` files where `uv run python research/harness/download_scenes.py` put them.

## Harness scripts

From `/home/willvarner/alpasim`:

```bash
uv run python research/harness/download_scenes.py
uv run python research/harness/analyze_cp2.py
uv run python research/harness/run_delay_sweep.py --dry-run
uv run pytest research/harness/test_analyze_cp2.py
```

## Batch CSV

One file per campaign, `research/batches/<campaign>.csv`, created when the campaign
starts. Columns:

```text
date, operator, log_dir, command_id, scene, seed, exit_code, has_metrics,
collision_at_fault, tracking_error, plan_deviation, dist_traveled_m, notes
```

`command_id` is a short name defined in the campaign sheet Will writes (`nominal`,
`linear-stage`, `switch-k5-x3`, …). Griffin does not invent command ids.

## After a run

Controller CSV, when the run used the controller service:

```text
<log_dir>/controller/alpasim_controller_*.csv
```

The header must end with `solve_time_ms,status` on nonlinear runs. For a gain-schedule
run, Will checks that the logged gains change at the scheduled step. Griffin only
checks that the CSV exists and is longer than the header.

Metrics to copy into the batch CSV are the numbers in
`<log_dir>/aggregate/metrics_results.txt` under Metric Value for `collision_at_fault`,
`tracking_error`, `plan_deviation`, and `dist_traveled_m`.

## Config check

From the run directory, the value the runtime saw:

```bash
uv run python -c "
import yaml, sys
p = sys.argv[1]
c = yaml.safe_load(open(p))
print(c['runtime']['simulation_config']['planner_delay_us'])
" ./diag/NAME/generated-user-config-0.yaml
```

Some runs write `wizard-config.yaml` or `resolved_config.yaml` instead. Open whichever
file is there. If the printed delay is not the delay in the command, the run is
`FAIL` even if metrics exist.

## Do not

- Do not pass a new Hydra key that is not in this file or in a campaign sheet.
- Do not delete `diag/` or `autolab_experiments/` to save space. Ask Will.
- Do not run two wizards at once on the one GPU.
