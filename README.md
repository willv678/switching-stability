# Research workspace

Start here. This folder is the only current description of Will's IEEE IV 2027 project.
The long notes at the repo root are background. If they disagree with this folder, this
folder wins.

People: Will (senior, writing the paper), Griffin (sophomore, ~10 h/week, runs batches
from the runbook), and whatever agent is in the repo. The advisor is Shao (controls,
University of Georgia). His slides from 2026-09-22 are in `source/diagrams.pdf`.

## Read order

| Who | Read | Update |
|---|---|---|
| Anyone about to change code or launch a run | `STATUS.md`, then `FACTS.md` | `STATUS.md` when an acceptance line is actually met |
| Anyone asking "what is this project" | `MAP.md` | only when the claim changes |
| Will or Griffin, for the semester plan | `WEEKS.md` | when a week is replanned |
| Griffin, or an agent launching rollouts | `RUNBOOK.md` | when a command in it is wrong |
| Anyone tempted to re-diagnose the baseline | `FACTS.md` | when a new measurement replaces an old one |

Do not add another research markdown unless `STATUS.md` names the question it answers.

## What is current

The paper is switching stability of a tracking controller whose reference comes from a
neural policy mounted on the car. Full statement and scope: `MAP.md`. Who does what
each week: `WEEKS.md`.

This folder is its own git repo (ignored by NVlabs AlpaSim), pushed to
https://github.com/willv678/switching-stability. New notes and harness scripts go
here so they publish without copying into `~/autolab-harness`. That older mirror is
frozen. Do not develop there. Griffin: clone or pull that repo for the week plan;
run wizard from the AlpaSim checkout.

Harness Python lives in `harness/`. Run it from the AlpaSim checkout:

```bash
cd /home/willvarner/alpasim
uv run python research/harness/analyze_cp2.py
uv run pytest research/harness/test_analyze_cp2.py
```

Edits inside AlpaSim packages stay in `../src/`. Refresh the published delta with
`./export_src_diff.sh` (writes `patches/alpasim-src.diff`).

## Background, not instructions

| File | What it still contains | What is stale |
|---|---|---|
| `paper-switching-stability.md` | The paper argument, risks, and phases | "Immediate next steps" at the bottom. Use `STATUS.md`. |
| `HANDOFF.md` | Code-level tasks and acceptance tests | The progress blurb at the bottom, and any task `STATUS.md` marks done. |
| `researchideas.md` | Why the red-team / search papers were rejected, and the rigor checklist | The eight-week plan and "next three days." |
| `paper-attribution-repair.md` | Interface interventions, kept as tools inside the stability paper | It is not the lead paper. |
| `SESSION_CHANGES.md` | What one September session changed in the controller | A session log, not a plan. |

## Rules for agents

- Python goes through `uv`. Never activate a venv. See `.cursor/rules/uv-python.mdc`.
- `src/` is upstream AlpaSim. Change it only when `STATUS.md` names the file.
- Harness scripts live in `harness/` (`analyze_cp2.py`, `download_scenes.py`, …). They can change. Do not add new experiment scripts at the AlpaSim repo root.
- Do not build an LLM supervisor. `STATUS.md` will say when that is allowed. It is not allowed now.
- Do not trust `cp2_failure_boundary.png` or `failure_boundary.png`. The latency axis on the historical 212 runs was parsed wrong. See `FACTS.md`.
- When you finish a task, edit `STATUS.md` in the same change: date, what was measured, where the artifact lives. A task with no artifact is not done.
