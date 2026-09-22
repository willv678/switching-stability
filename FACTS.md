# Facts

Measurements and code invariants. Do not re-derive these. Replace a row when a new
artifact contradicts it, and name the artifact.

## Hardware and venue

- One 12 GB GPU now. A 24 GB RTX 4090 was expected; do not assume it has arrived.
- Qwen2.5-Coder-3B on CPU exists for the old harness. It is not on the critical path.
- IV 2027: Perth, 15–18 June 2027. Regular papers due 15 Nov 2026, at most 6 pages
  including figures and references. https://ieee-iv.org/2027/contributions/call-for-papers/

## Nominal driving, one scene, CATK, zero injected delay

Source: `diag/nominal_run_1` through `diag/nominal_run_10`.

| Quantity | Value |
|---|---|
| At-fault collisions | 8 / 10 |
| `tracking_error` | about 1.4–1.7 m on every run, including the two that did not collide |
| `plan_deviation` | about 1.6–2.4 m per planner step, with no gain switching at all |
| Route length in the metrics | `gt_dist_traveled_m` = 73.77 m |
| Distance before a typical crash | about 33–47 m |

`plan_deviation` is how much VaVAM changes its mind between plans. It is not tracking
error. `tracking_error` is executed pose versus the plan. `dist_to_gt_trajectory` is
distance from the human's recorded line. Those are three different numbers.

Force-GT (`diag/test_force_gt_1`, `diag/test_force_gt_2`) drives the full route with
0 collisions and `dist_to_gt_trajectory` = 0, while `tracking_error` reports ~10.4 m.
`diag/kinematic_ideal_verify` reports ~10 m as well. Until that is explained, tracking
error on force-GT and kinematic-ideal runs is not evidence.

Historical 212-run corpus, before CATK and before the config parser fix
(`researchideas.md` §0): 74% at-fault, 70% at-fault even at zero claimed latency,
`min_distance_to_obstacle_m` never above 1.13 m, one scene, `progress_rel` saturated
at 1. Do not cite those runs for a latency effect. `analyze_cp2.py` used to regex the
first `planner_delay_us` in the YAML and often recorded 0.

## Code invariants

1. Nonlinear MPC builds its CasADi cost once. Changing Python gain fields afterward
   does nothing. Linear MPC rebuilds Q and R in `update_gains` and sets the QP up on
   every solve. The paper uses linear MPC.
2. Both MPCs default `idx_start_penalty` so the first 1.0 s of a 2.0 s horizon has no
   tracking cost. Setting it to 0 did not fix the nominal crashes (`diag/test_penalty0_run_*`).
3. Nonlinear `set_rterm` penalizes input rate. Linear R penalizes the control itself.
   There is no input-rate penalty on the linear MPC, so nothing in its cost discourages
   chatter. A switching paper on the linear plant has to remember that.
4. Default terminal cost equals stage cost. `terminal_cost: riccati` on the linear
   controller solves the discrete Riccati equation and uses P. Failure falls back to
   stage cost and logs. The fallback means a "riccati" run can silently be a stage run
   if the solve fails.
5. Nonlinear MPC reports solver status from `solver_stats` (`solved`, `max_iter:N`,
   `infeasible`, `unconverged:…`). The controller CSV columns are `solve_time_ms,status`.
6. `controller_gain_schedule` is resolved in `src/runtime/alpasim_runtime/events/controller.py`
   and passed into the controller. A schedule entry applies when the control step index
   is at least `entry.step`. Base gains apply before the first entry.
7. `force_gt` replaces the driver plan with the recorded human trajectory. That is the
   frozen-perception condition for Phase B.
8. Plan fault injection (lateral bias, noise, freeze, horizon truncation) is
   `src/runtime/alpasim_runtime/plan_fault_injection.py`, off unless configured.
9. CATK weights are at `data/trafficsim-models/catk_v120` and run on CPU.
10. Deployed VaVAM `inference.context_length` is 1. The model default in code is 8.
    Do not describe the deployed policy as having eight frames of memory.
11. `open_loop_collision` compares a plan with agents' recorded futures. It is a plan
    quality metric under replay traffic. Under CATK it is not a collision forecast.
12. `kinematic_ideal` does not emit steering and accel. `System._kinematic_ideal_step`
    moves the ego along the plan. It is not a controller plugin in the usual sense.

## Prior work the paper has to sit next to

Read before writing a related-work paragraph. Confirm venue and theorem statements;
several IDs were found by search (`researchideas.md` appendix).

| Work | Why it is in the paper |
|---|---|
| AURORA, arXiv 2511.07768 | Agentic supervisory redesign with a dwell-time theorem. Exogenous reference. We do not claim their theorem is false. We claim the exogeneity assumption does not hold for a camera on the car. |
| DiffTune-MPC, arXiv 2312.11384 | Analytical MPC cost tuning. Better than any LLM at choosing floats. We do not tune floats. |
| Poirot, ISSTA 2026; DVCA; CF-RCA | Module-substitution blame. They need interior modules. Cited only to say we are not doing that. |
| Bench2Drive-Robust, arXiv 2605.18059 | Latency benchmark for end-to-end policies. No supervisor, no switching. |

## Repos

- This checkout, `/home/willvarner/alpasim`, is the working tree. Research notes live
  in `research/`.
- `/home/willvarner/autolab-harness` is a public snapshot of the old red-team harness.
  Its README describes a project we are not submitting.
