# Status

Living tracker. As of 2026-09-22. If you finish something, replace the row. Do not
append a second status for the same task.

Deadline: conference paper **15 Nov 2026**, 6 pages including figures and references.
Notification 15 Jan 2027. Workshop papers, if needed as a fallback, are due 1 Feb 2027.
Source: https://ieee-iv.org/2027/contributions/call-for-papers/

## Now

The substrate for the paper mostly exists. The paper result does not. The next
measurement is the jitter-floor test in `paper-switching-stability.md` §4.1: one scene,
fixed seed, a known gain jump, compared with the no-switch plan-change distribution.
If that perturbation does not separate from ordinary VaVAM jitter, the perception-coupling
claim is unmeasurable and the paper narrows to recursive feasibility. Do that before
any sweep and before any writing.

Griffin's current job is scene qualification, not new code. See `RUNBOOK.md`.

## Tracker

| ID | Task | State | Evidence |
|---|---|---|---|
| S1 | Seed variance on one nominal config | done | 10 CATK runs in `diag/nominal_run_{1..10}`. Tracking error about 1.4–1.7 m. Collision is **not** stable: 8/10 at-fault. Wall clock was reported ~49 s/rollout in `HANDOFF.md`; re-measure before budgeting a sweep. |
| S2 | Nominal collision rate under 10% | **open, and it blocks multi-scene claims** | Same 10 runs: 80% at-fault with VaVAM + CATK + zero delay. `idx_start_penalty=0` and `short_horizon` still collide. `exp=sim/force_gt` does not (`diag/test_force_gt_*`, 0 collisions, ~71 m). Verdict so far: on this one scene the crashes are the planner, not the tracker. A stability paper can still study tracking and solver feasibility on the crashing policy, but a safety-rate claim cannot. |
| S3 | Scenes on disk | downloaded, not qualified | 102 `.usdz` files, ~190 GB, under `data/`. Acceptance is 20 scenes that finish a rollout and write metrics. None of that qualification is recorded. |
| S4 | Silent-failure rate (historical 22%) | open | Not re-measured after the harness fixes. |
| I1 | Real IPOPT status in the controller CSV | done on the nominal path | `nonlinear_mpc.py` reads `solver_stats`. `system.py` logs `solve_time_ms,status`. `diag/solver_status_verify`: 195/195 steps `solved`. Tests: `src/controller/tests/mpc_impl/test_nonlinear_mpc.py`. |
| I2 | Tracking-error scorer | done, interpret with care | `tracking_error` is in the parquets. On nominal runs it is ~1.5 m. On force-GT it is ~10 m while `dist_to_gt_trajectory` is 0. That disagreement is a frame bug or a scorer bug until someone explains it. Do not quote force-GT tracking error. |
| I3 | Config parsed by YAML path, not regex | done in `research/harness/analyze_cp2.py` | `research/harness/test_analyze_cp2.py`. Historical latency plots stay untrustworthy. |
| C1 | Mid-rollout gain change on linear MPC | implemented, acceptance not closed | `update_gains` in `linear_mpc.py`. Schedule resolved in `events/controller.py` via `controller_gain_schedule`. Verify rollouts `diag/gain_schedule_verify` and `diag/gains_reconfig_verify` both collided. Nobody has written down a CSV row showing the gain value changed at the scheduled step. Close this before Phase A. |
| C2 | Riccati terminal cost | implemented, certificate not shown | `controller=linear controller.terminal_cost=riccati`. `diag/riccati_verify` completed and collided. CLF plot exists; stepwise monotonicity was ~43% because the model re-linearizes. Not yet a dwell-time number. |
| C3 | `kinematic_ideal` tracker | implemented, not ideal | `system.py` bypasses the vehicle model. `diag/kinematic_ideal_verify` tracking error ~10 m, same family as the force-GT scorer bug. Do not use it as a perfect-tracker baseline until tracking error is ~0. |
| C4 | Plan-corruption hook | implemented | `plan_fault_injection.py`, wired in `events/controller.py`. `diag/fault_injection_bias` collided harder and traveled less than `diag/fault_injection_baseline`. Good enough as a tool. Not a paper result. |
| C5 | What `planner_delay_us` actually does | open | Directories `diag/delay_sweep/delay_{0,50000,100000,150000,200000}` exist and contain no metrics. |
| P1 | Jitter-floor test | **next** | Not run. This decides whether the endogenous-reference effect is measurable. |
| P2 | Phase A switching sweep | blocked on C1 and P1 | Deterministic switcher, no LLM. Design in `paper-switching-stability.md` §5. |
| P3 | Phase B frozen-perception ablation | blocked on P2 | `force_gt` already exists. |
| P4 | LLM supervisor (Phase C) | not started, and out of scope until P2 lands | Building it now spends the six pages on a demo. |

## Explicitly not in scope before 15 Nov

- An LLM that retunes gains or picks the next experiment.
- LoRA training (`research/harness/train_lora.py`, `autolab_lora_adapter/`).
- Numeric MPC tuning as a contribution. DiffTune-MPC and stability-informed BO already do it.
- The red-team search paper described in `~/autolab-harness/README.md`.
- Phase D, the supervisor also editing the scenario. Cut first if anything slips.
