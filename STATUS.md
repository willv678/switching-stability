# Status

Living tracker. As of 2026-09-22. If you finish something, replace the row. Do not
append a second status for the same task.

Deadline: conference paper **15 Nov 2026**, 6 pages including figures and references.
Notification 15 Jan 2027. Workshop papers, if needed as a fallback, are due 1 Feb 2027.
Source: https://ieee-iv.org/2027/contributions/call-for-papers/

## Now

PI decision, 22 Sep 2026, after the diagram meeting. November paper is **Loop 1
only**: an agent that runs simulation batches unattended, chooses a skill from a
finite menu, and recovers from execution failures. Loop 2 (searching for vulnerable
scenarios) is motivation, not a result. Do not build it.

The agent emits a skill \(s_k\) such as CONFIGURE, LAUNCH, RE-RUN, RESTART_CLEANUP,
plus parameters. It does not emit free text. \(K^-\) rejects an illegal skill or a
config that must not launch. \(K^+\) turns a crash, a core dump, or a garbage metrics
file into a structured status the agent can use on the next step. Research question
Shao stated: how long can this run without a person, and how does it detect and
recover.

The comparison that makes the model earn its place: the same skill menu with a
hand-written policy, versus the model. Failures \(w_k\) must include bad science,
not only process death: `context_length` underflow, missing metrics, config that
did not land, solver status that is not the solver's. A 24 GB GPU arrives the week
of 29 Sep. The 12 GB out-of-memory failure will get rarer. Do not hang the paper
on it.

Switching-stability and the jitter test are paused. They are not the claim.

## Board

This is the sheet. An agent takes the first `todo`, sets it to `doing`, and does
nothing else. On success it sets `done`, writes the artifact path, and appends
`LOG.md`. It does not start the next row.

| ID | State | Task | Done when |
|---|---|---|---|
| L1 | done | Skill menu and step record. Typed skills: CONFIGURE, LAUNCH, RE-RUN, RESTART_CLEANUP, ACCEPT. A step record with skill, params, and the K status that produced it. | Unit tests pass. No simulator is launched. Code lives under `research/harness/`. `research/harness/skills.py` and `research/harness/test_skills.py`. |
| L2 | done | Preflight \(K^-\). Reject `context_length` other than 8, a Hydra delay that does not match the request, and a missing scene file. | Tests cover those three rejects and one accept. No simulator is launched. `research/harness/preflight.py` and `research/harness/test_preflight.py`. |
| L3 | done | Postflight \(K^+\). Read a finished run directory. Fail it if metrics are missing. Record at-fault and rear-contact separately. Note solver status when a controller CSV exists. | Tests use `diag/test_vavam_ctx8` and a fixture with no metrics file. `research/harness/postflight.py` and `research/harness/test_postflight.py`. |
| L4 | done | Hand-written recovery policy on the same menu. Missing metrics or a dead process becomes RE-RUN or RESTART_CLEANUP. A config \(K^-\) rejected is never launched. A clean run becomes ACCEPT. | A table test lists each status and the skill returned. `research/harness/policy.py` and `research/harness/test_policy.py`. |
| L5 | done | Three wizard launches, started by the runner, driven by L4, written as step records. | Run directories created by the batch (L5_nominal_1, L5_nominal_2, L5_nominal_3). Each launch ACCEPTs or recovers without human intervention. `research/harness/l5_trace.jsonl`. |
| L6 | todo | Model policy versus L4. Inject three failures: `context_length` 1, a run directory with no metrics, a command that exits nonzero. The model is an OpenRouter chat completion, `anthropic/claude-haiku-4.5`, key from `OPENROUTER_API_KEY`. The prompt asks for one skill and nothing else. If the env var is missing, stop. Do not replace the call with another if-statement. | A table of the model's skill against L4 on those three injections, plus the raw response. If the model does not win, say so. |

Do L5 first. L6 does not depend on L5 happening to fail.

Paused, and not on this board: gain-switching sweeps, jitter test, Riccati-as-paper,
scene qualification for its own sake, Loop 2 search. Evidence for the old rows
stays in `FACTS.md` and `diag/`.

## Out of scope

- Free-text sim control.
- An agent that retunes MPC gains or hunts for crash scenarios.
- LoRA training.
- Treating 12 GB out-of-memory as the main failure mode after the 24 GB GPU arrives.
