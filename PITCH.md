# Pitch

Paste the block below into a new LLM session, then paste this file. If a detail
here disagrees with `STATUS.md`, `STATUS.md` wins.

```
Read research/PITCH.md and research/STATUS.md.
Take the first board row whose state is todo. Change that row to doing.
Do only that task. Stop when its "Done when" cell is true.
Then set the row to done, write the artifact path in the row, and append one
dated line to research/LOG.md.
Do not start the next row. Do not add tasks.
```

Will Varner, senior at Georgia, is writing one IEEE IV 2027 paper with his PI,
Dr. Shao. Deadline 15 Nov 2026. Six pages including figures and references.
Griffin helps about ten hours a week on batches. The stack is AlpaSim: VaVAM
turns a camera image into a plan, a linear MPC tracks it, the sim is the world.
Repo: `/home/willvarner/alpasim`. Research notes: `research/`. Do not develop in
`~/autolab-harness`.

Shao's diagram has two loops. Loop 1 runs one simulation and recovers when it
fails. Loop 2 picks the next experiment. We sell the whole picture in the
introduction. The contribution is Loop 1. Loop 2 is a short demonstration that
a simple rule can consume runs Loop 1 already cleaned. It is not a search paper.

The agent does not write prose and does not drive the car. Each step it emits
one skill from a finite menu, plus parameters: CONFIGURE, LAUNCH, RE-RUN,
RESTART_CLEANUP, and only the other skills the menu actually needs. Preflight
\(K^-\) rejects an illegal skill or a config that must not launch. Postflight
\(K^+\) turns a crash, a core dump, or garbage metrics into a structured status.
The agent then picks the next skill. The baseline is the same menu driven by a
hand-written policy. If the model does not beat that script, the script is the
result.

The claim: a batch can run without a person, and every run kept in the dataset
is real driving data. Unattended uptime is the setting. The result is the
absence of invisible failures. Known ones: `context_length: 1` made VaVAM look
like it always crashed; a latency plot was drawn from a config value the sim
never used; about 22% of older runs wrote no metrics; the nonlinear MPC used to
report `solved` whenever it did not throw. A 24 GB GPU arrives the week of
29 Sep 2026. Do not build the paper on 12 GB out-of-memory crashes.

Do not build Loop 2 as a method, an LLM supervisor that retunes MPC gains, a
switching-stability theorem, or numeric MPC tuning. Those notes at the repo
root are paused background. Python runs through `uv`. Change `src/` only when
`STATUS.md` names the task. When a task meets its criterion, update `STATUS.md`
with the artifact path.
