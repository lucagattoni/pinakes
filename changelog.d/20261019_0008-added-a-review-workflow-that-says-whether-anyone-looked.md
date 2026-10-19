- **A committed review workflow, `.claude/workflows/adversarial-review.js`, that returns whether
  anyone looked.** It reviews one pinned commit (`args.sha` against `args.base`, both required) with
  four lenses launched slowest first — runtime, missing-set, population, docs-vs-tree — one refuter
  per finding started the moment its lens returns, and one Opus judge, every call naming its model.
  The result carries `coverage`: `VACUOUS` when no lens returned, `PARTIAL` when a lens died, a probe
  was not run, a finding has no refuter or a survivor has no ruling, and only otherwise `CLEAN` or
  `FINDINGS`. A dead agent is **counted before anything is filtered** and a finding whose refuter
  died is listed as `unrefuted`, never dropped. This is step 1 and step 3 of *Framing, Not Roles*
  § 9: a fan-out once lost 17 of its 19 agents to a session limit, `.filter(Boolean)` erased them,
  and it returned `{"raised":0}` as if it had looked. `tests/test_review_workflow.py` runs the
  script file itself against stub hooks under Node; a machine without Node skips it and `CI`
  fails instead. `.gitignore` now excludes `.claude/worktrees/` and
  `.claude/settings.local.json`, which a clone without Claude Code's own `.git/info/exclude` line
  would otherwise have committed. Developer tooling — it ships in no wheel.
