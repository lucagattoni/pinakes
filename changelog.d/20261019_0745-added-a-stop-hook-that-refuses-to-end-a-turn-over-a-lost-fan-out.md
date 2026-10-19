- **A Stop hook that will not let a turn end over a review fan-out that lost agents, until the user
  has been told.** `tools/hooks/review_stop_hook.py`, wired by the new `.claude/settings.json`,
  runs at the end of every turn: it reads `transcript_path` from the hook payload, finds the
  workflow runs of that session, runs `tools/review_pass_gate.py` over each journal, and blocks
  while a run has an agent that never returned or returned nothing and no acknowledgement covers it.
  The reason names the run, each agent by the label the journal gave it, and the verdict
  (`VACUOUS` when nobody returned anything, `PARTIAL` otherwise), and prints the one command that
  acknowledges it (`--acknowledge <run> --told "<what the user was told>"`, a sentence and not the
  placeholder the message prints). That records what was said and the counts plus a digest of the
  journal, because a resume appends to the same journal in the same run directory, so a run that
  is resumed and changes is judged again. A run on which the gate errors is reported on stderr and
  does not hide a dead run beside it; a journal with no parseable agent line passes silently. The message says in the same breath that this is the
  journal's count and not the workflow's own `coverage`.
  Three things decide a run's fate that the gate alone cannot: nothing is judged while the payload's
  `background_tasks` lists a workflow in flight (a slow agent looks exactly like a dead one); with
  the list present and no workflow in it every run is judged as finished, because a fan-out killed
  seconds before the turn ended would otherwise read "probably still running" and pass; and with the
  list absent the gate's own quiet window decides. An internal error, a malformed payload, or a gate
  that exits `1` without the verdict it promises exits `1` with the cause on stderr — visible, and
  never a block — because `1` is also what a traceback exits with. It is a nudge and not a lock:
  Claude Code overrides a Stop hook after eight consecutive continuations. The command in
  `settings.json` follows the working directory's git top-level, since `${CLAUDE_PROJECT_DIR}` stays
  at the original checkout inside a worktree, and exits `0` quietly where the script is absent, so
  a checkout that predates the hook prints no error at every turn end. The script is standard-library only and
  runs on the Xcode `python3` 3.9. This is step 2 of *Framing, Not Roles* § 9. Tested over a
  synthetic session of the true layout, including a run under `/usr/bin/python3` and the settings
  command itself; `tools/batteries/tools-hooks-review_stop_hook.toml` holds the mutants, and a fully killed first draft was not enough: two reviewers wrote their own and each left some alive. **The hook
  fired live once** (20261019 09:24 UTC, a fresh session): a planted dead run blocked its turn end,
  the acknowledge command the message prints worked, and the next turn end was silent. The session
  that created `.claude/settings.json` had not picked it up (08:26 UTC). Two things stay unobserved:
  the real Stop payload (the hook is built from the hooks reference) and which checkout runs it in
  a worktree session. In that fresh worktree session the script that ran was the primary
  checkout's copy, so following the git top-level did not follow the worktree there; the cause is
  untested. Developer tooling — it ships in no wheel.
