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
  command itself; `tools/batteries/tools-hooks-review_stop_hook.toml` holds 48 mutants. **The hook
  has not fired in a live session yet**: the session that created `.claude/settings.json` did not
  pick it up (a planted dead run did not block its turn end, though the hook blocks on the same
  input fed by hand), so the Stop payload is built from the hooks reference and a later session's
  first turn end is the first live firing. Developer tooling — it ships in no wheel.
