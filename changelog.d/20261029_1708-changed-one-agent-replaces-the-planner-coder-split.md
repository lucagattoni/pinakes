- **One agent replaces the planner/coder split.** `CLAUDE.md` no longer makes a session name a role
  and block until the user answers, and the ownership table that made every document the planner's
  and every change to one a proposed `git diff` is gone. One agent plans, builds, documents,
  reviews, lands, releases and hands over, through subtasks and subagents, and a subagent's work
  reaches `main` only through it. **What the split carried that is not about roles stays:** ask
  live peers for their task and file set before writing, one writer per file in every brief,
  `changelog.d/` and `retro.d/` fragments instead of edits to the two files every increment would
  touch, and a `docs/VERIFICATION.md` row or counted paragraph changing in the commit that makes it
  true. `docs/BUILDING.md` lost its role, propose-a-diff and dictated-text sections and gained
  *Subtasks and subagents* and *Open questions* (an open question in a plan stays a stop; how to
  build what it specifies is the agent's, permanent surface and anything irreversible is the
  user's). The non-obvious rule in the first is that a builder's brief must open with its job: `tools/review_ledger.py` reads the first 400 characters of a brief and otherwise counts a
  builder's own brief as a review pass of the work it wrote. `docs/RELEASING.md` is addressed to the
  agent that built the work, which now cuts the release. The `CLAUDE.md` size gate's failure message
  no longer says whose file it is; its test and one of its mutants changed with it. Plans,
  retrospectives and release records keep the words they were written with, and `CLAUDE.md` says to
  read "planner" and "coder" in them as the one agent. Developer process only: no `pnk` behaviour
  changes. `CLAUDE.md` now also says a release tag is pushed only on the user's yes, which the old role
  split had left as an unwritten consequence of who cut releases. It was reviewed against the
  hygiene rules on 20261030 07:59.
