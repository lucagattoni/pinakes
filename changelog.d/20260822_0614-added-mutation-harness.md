- **`tools/mutate.py` runs the per-increment mutation battery, and refuses rather than reporting a
  clean bill it has not earned.** The mutation step of
  [BUILDING § 4](https://github.com/lucagattoni/pinakes/blob/main/docs/BUILDING.md) is the
  procedure's one *silently-failing* step: a broken harness prints SURVIVED and KILLED in exactly
  the shape a working one does. The plan counts more than a dozen invalid or destructive runs
  across ten increments, and the `git checkout` trap alone is recorded **six times**. Each written
  rule is now a refusal: the target must be tracked and match `HEAD`; the anchor must occur
  **exactly once**, checked across the whole battery before the first write; `__pycache__` is
  cleared after the write *and* after the restore; pytest never sees `-x`; an invalid mutant is its
  own outcome rather than a kill; the restore happens in a `finally` and its bytes are verified;
  and a batch where **nothing died exits non-zero**, because a run with no kills is a broken
  harness and not a clean bill (`--allow-zero-kills` for a backstop already documented as
  unpinned). The battery is a TOML file of `[[mutant]]` rows — `file`, `old`, `new`, `kills` —
  where `'''…'''` carries an anchor's quotes, backslashes and indentation without escaping, and the
  summary is a Markdown table written to be pasted into the commit message that claims the pass.
- **Five ways a mutation run can lie that the written rules did not cover, all measured, all now
  refusals.** A **skipped** test exits 0 — byte for byte the SURVIVED signal — and Pinakes skips on
  a missing extra as a matter of course, so a battery aimed at a `pdf`, `paid` or `model` selector
  in a `[light]` checkout would have reported every mutant unpinned. An **already-red** selector
  reports KILLED for every mutant aimed at it, including the ones nothing catches. Both are caught
  by one pre-flight run per selector — collect a test, actually *run* a test, be green — before any
  file is touched. **`SIGTERM`, `SIGHUP` and `SIGQUIT`** end a process without unwinding, so a
  plain `finally` never runs and the mutant stays on disk. **`PYTEST_ADDOPTS`** is inherited, so
  `-x` in the operator's shell narrows a two-test kill to one. **`PYTHONPYCACHEPREFIX`** moves every
  `.pyc` into a mirrored tree the clearing cannot reach.
