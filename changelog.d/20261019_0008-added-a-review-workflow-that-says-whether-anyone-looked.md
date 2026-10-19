- **A committed review workflow, `.claude/workflows/adversarial-review.js`, that returns whether
  anyone looked.** It reviews one pinned commit — `args.sha` and `args.base`, both commit shas, a
  moving ref is refused because `origin/main...<sha>` goes empty once the increment lands — with
  four lenses launched slowest first (runtime, missing-set, population, docs-vs-tree), one refuter
  per finding started the moment its lens returns, and one Opus judge, every call naming its model.
  The result carries `coverage`: `VACUOUS` when no lens returned (a sha that does not exist makes
  every lens report an empty diff), `PARTIAL` when a lens died, a probe was not run, a malformed
  finding was dropped, a finding has no refuter, a high-severity finding was dismissed on a guess,
  or a survivor has no usable ruling, and only otherwise `CLEAN` or `FINDINGS`. A dead agent is
  **counted before anything is filtered**, and one that threw keeps its cause; a finding whose
  refuter died is listed as `unrefuted`, never dropped; a refuted finding keeps its severity,
  evidence and whether the refuter *checked* or only defaulted, and every guess is listed in
  `dismissed_on_a_guess`; a judge that throws is a dead judge rather than the end of the run. Every
  reply is read again before it is believed, because the schemas are enforced by the runtime and
  not by the script.
  This is step 1 and step 3 of *Framing, Not Roles* § 9: a fan-out once lost 17 of its 19 agents to
  a session limit, `.filter(Boolean)` erased them, and it returned `{"raised":0}` as if it had
  looked. `tests/test_review_workflow.py` runs the script file itself against stub hooks under
  Node, and the stub is itself tested to refuse what the runtime refuses; a machine without Node
  skips those tests and `CI` fails instead. `tools/batteries/claude-workflows-adversarial-review.toml`
  holds the mutants. **The real fan-out has not been run yet**; that is the smoke run planned on the
  next increment's diff. `.gitignore` now excludes `.claude/worktrees/` and
  `.claude/settings.local.json`, which a clone without Claude Code's own exclude lines would
  otherwise have committed. Developer tooling — it ships in no wheel.
