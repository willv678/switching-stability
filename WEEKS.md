# Week by week

22 Sep 2026 through the IV 2027 deadline, Sunday 15 Nov 2026. High level only.
Details of commands and task status stay in `RUNBOOK.md` and `STATUS.md`.

Read this once, then do the current week. The rest of `research/` is there when a
week tells you to open it.

Shao locked the claim on 22 Sep 2026. The paper is Loop 1, the unattended
batch runner with a finite skill menu. The week tasks below that chase gain
switching are paused. Current scope is `STATUS.md`.

## Is this a strong paper?

The question is strong enough for a first IV paper. The manuscript is not strong
yet, because the measurement has not been made.

What a reviewer can respect in six pages: a tracking controller follows a plan that
a neural driver computes from a camera on the car. Switching the controller's gains
is a standard controls move, and the textbooks assume the plan does not depend on
that switch. Here it does. If a fixed switching schedule is safe when the plan is
the human's recording, and unsafe when the plan comes from the camera, that gap is
the paper. One plot. No language model required.

What would make it weak: selling VaVAM's existing crashes as instability, a single
scene, or a section about an agent that chooses experiments. Shao's slides describe
the lab. They are not the six pages.

If the gain switch does not show up above VaVAM's ordinary plan jitter, the paper
gets smaller and remains submittable: how often a switch makes the optimizer
infeasible. That is a controls result. It is less novel. Decide that in the week
of 28 Sep, from data, and tell Shao.

## How the two schedules fit

Will's list is the paper. It does not wait on Griffin.

Griffin's list is real work with a one-week buffer. Each item is due on a Sunday.
Will might use it the following week. If it is not there, Will skips that use and
continues. Griffin does not edit `src/`, does not pick the next experiment, and
does not need the control theory. Commands come from `RUNBOOK.md` or from a sheet
Will writes.

The week of 22 Sep is Griffin's trial. Finishing it is how he shows he can run the
simulator and record a number. Later weeks stay on this list either way; they just
stay off the critical path.

Hours: Will has the semester. Griffin is about ten hours. A Griffin week that needs
more than that should be cut down, not pushed onto Will's week.

---

## Week of 22 Sep — learn the car, test the switch

**Will.** Learn the stack by running one nominal rollout and reading its metrics
file. You need a working picture, not the theory: VaVAM proposes a path from the
camera, the MPC tries to drive that path, AlpaSim is the world. `plan_deviation`
is VaVAM changing its mind. `tracking_error` is the MPC missing the path. A
collision is neither of those by itself. Then check the gain-schedule CSV yourself,
and run the jitter test: one known gain jump against the no-switch plan changes.
That test decides the paper. Read `FACTS.md` and Shao's slides. Skip AURORA until
next week.

**Griffin, due Sun 27 Sep.** Three nominal reruns on the scene Will names, each in
its own log directory. A CSV row per run with exit code, whether metrics exist,
collision, and distance traveled. A list of the `.usdz` files on disk: filename
and size, no rollouts yet. This week is the chance to show the runbook works in
his hands.

**Will uses Griffin's output.** He does not. Look at it Monday 28 Sep only to see
whether Griffin can operate the machine.

## Week of 28 Sep — one concept, then the grid on one scene

**Will.** Learn one idea well enough to say it out loud: dwell time is a minimum
wait between controller switches. The usual guarantee assumes the reference path
is independent of the switch. Ours is not, because the camera is on the car. Read
AURORA's theorem assumptions, not the whole paper. If last week's jitter test
separated, run the core of the switching grid yourself on the one known scene:
a few values of the switching interval, one jump size, a handful of seeds. If it
did not separate, switch the week's runs to "does the optimizer fail at the
switch instant?" Write down what the plot should show before you look.

**Griffin, due Sun 4 Oct.** Start qualifying scenes: one nominal rollout per
scene, pass/fail, using the runbook. Target whatever fits in ten hours, not all
102. Record failures as failures. Do not debug them.

**Will uses this.** The week of 5 Oct, only as a candidate list. The core plot
does not need it.

## Week of 5 Oct — see if the effect is real

**Will.** Finish the one-scene grid and make the first plot: something going wrong
versus how long you wait between switches, with the no-switch runs on the same
axes. Decide, in writing, which claim survived. Tell Shao in a short note: the
slides' outer agent is not the November paper; this plot is. If the plot is
noise, commit to the smaller feasibility paper the same week.

**Griffin, due Sun 11 Oct.** Finish a pass/fail list aimed at 20 scenes that
actually wrote metrics. Also copy Will's finished one-scene runs into the batch
CSV so the numbers live in one sheet.

**Will uses this.** Scene list: week of 12 Oct, and only if he chooses to add
scenes. The CSV: week of 19 Oct, when the outline needs a table.

## Week of 12 Oct — cut the camera loop

**Will.** Repeat a smaller version of the same grid with the human recording
substituted for VaVAM (`force_gt` in the runbook). Learn why that run matters:
it keeps the tracker and removes the camera's effect on the plan. If the bad
behavior disappears only in that condition, the camera loop is doing the work.
If it does not, say so. Add a second scene only if Griffin's list is in and a
cell is cheap. Start a six-page outline: one paragraph, one figure, one table,
related work as a short column. Nothing else.

**Griffin, due Sun 18 Oct.** Watch the videos for the runs already in the CSV.
One sentence each: finished the route, hit something ahead, left the lane, or
the video is missing. No interpretation beyond that.

**Will uses this.** Week of 19 Oct, as color for figure captions. The plot does
not depend on the sentences.

## Week of 19 Oct — outline while the result is still fresh

**Will.** Freeze the claim in one sentence at the top of the outline. Draft the
figure caption and the table. Read `paper-switching-stability.md` now, as the
long version of the argument, and delete anything your plot does not support.
You are learning to say the result in IV language: what was switched, what was
measured, what the frozen-plan runs did. Do not add an agent section.

**Griffin, due Sun 25 Oct.** Check every number in Will's draft table against
`metrics_results.txt`. Mark mismatches. Download the four papers named in
`FACTS.md` into `research/source/papers/` and write five lines on each: what it
claims, in his own words. Wrong summaries are fine. They show what a cold reader
thinks the paper said.

**Will uses this.** Week of 26 Oct, while writing the draft. He still checks the
important numbers himself.

## Week of 26 Oct — write the draft

**Will.** Full six-page draft. Figures locked. Related work is the four papers
plus whatever you actually read, stated accurately. A claim you cannot point at
a file for gets cut. Send the draft to Shao by Sunday 1 Nov even if a paragraph
is rough. Writing late is how this deadline gets missed.

**Griffin, due Sun 1 Nov.** Nothing new. If the table check or the paper notes
from last week are unfinished, finish those and stop. No new rollouts unless
Will hands him a named missing cell.

**Will uses this.** He is not blocked. Shao's read is the input for next week.

## Week of 2 Nov — revise from Shao, not from new ideas

**Will.** Revise from Shao's comments and from your own cold read. Learn the
page limit as a constraint: six pages including figures and references. A new
experiment this week replaces a paragraph you were willing to delete, or it
does not happen. Re-read the jitter result and the frozen-plan result so the
abstract matches the files.

**Griffin, due Sun 8 Nov.** Read the draft and highlight every sentence he
cannot restate. That list is the clarity pass. He is not copy-editing for
grammar unless he wants to.

**Will uses this.** Week of 9 Nov, as a readability pass before submission.

## Week of 9 Nov — submit

**Will.** Deadline is Sunday 15 Nov. Final PDF, author checklist on the IV
site, submitted with time left on Friday 13 Nov so Sunday is a buffer. After
submission, write a half-page note to Shao on what the slides' Agent 2 would
be as a follow-up. That is the agents pitch, parked until this paper is in.

**Griffin.** No deliverable. Optional: sit with Will for an hour and walk
through the submitted figure so he can explain it.

---

## If a week goes badly

| What happened | What changes |
|---|---|
| Jitter test is noise | Week of 28 Sep becomes the feasibility version. Tell Shao that week. |
| No plot by Sun 11 Oct | Drop the frozen-plan repeats before you drop writing. One figure of the grid you have. |
| Griffin's trial week fails | Later Griffin weeks stay assigned and stay optional. Will does not re-plan around them. |
| Shao wants the agent in the paper | The agent is a constraint on the switch schedule, at most a paragraph, and only after the plot exists. The lab slides stay the meeting story. |
| The draft is late on 1 Nov | Cut scope to the plot you have. Workshop papers are due 1 Feb 2027 if the conference version is not something you believe. That fallback is not the plan. |
