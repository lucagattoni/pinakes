## A gate spoke correctly about an input nobody had edited (20260901 18:40)

**MEDIUM — `./check.sh` went red on a branch that had touched nothing near the failing gate, and
the cause was not in the source tree at all.** The repository's standing rule is *assume other
agents run concurrently*, and the failure mode it names is a clean-but-wrong **merge**. This is one
layer below that. Nothing was merged. Nothing was edited. `git status` was clean throughout. What
changed was which tree the worktree's virtualenv resolved `pinakes` to.

**The facts, which are two runs on one tree an hour apart.**

| | |
|---|---|
| Earlier run, nothing else touching the worktree | `2420 passed, 4 skipped`, no failures |
| Later run, six review agents working against the same worktree | `1 failed, 2419 passed`, `CHECK_EXIT=1` |
| The failure | `test_the_real_package_is_refused_from_the_source_tree` expected `"resolved to the source tree"` |
| What it got | `wheel-import: pinakes resolved to an unpacked tree at /private/tmp/claude-501/…` — a **scratchpad** path |
| Re-run alone, minutes later | `23 passed`; the gate invoked directly names this worktree's own `src` |
| The venv | two `.pth` files, the editable one pointing at this worktree's `src`, by then correct |

**The inference, which is an inference.** Between the two runs the venv's editable `pinakes` install
pointed at a copy of the tree in a scratchpad, and `uv run --frozen` put it back. Six agents were
running against that worktree under an instruction to copy it into their own scratch directory
before experimenting. **Which one, and by what command, is not established, and no agent is named
here** — the honest limit of the evidence is that six were running under that instruction.

**The repair was visible, and that is the sharper half.** `uv run --frozen` printed `Uninstalled 1
package … Installed 1 package` above the test output before the tests ran. So the log held both
the damage and its cure, in order, and a reader scrolling to the failure would have found a red gate
a branch that never went near it. A *silent* repair leaves a mystery; a visible one leaves something
worse — a plausible wrong answer, in the log, above the evidence against it. **The line that
explains a failure is often printed before the failure, where nobody is looking yet.**

**The rule.** *A red `./check.sh` is not evidence until you have re-run it with nothing else
touching the tree.* The same holds for a green one: a run made while agents work in the same
worktree is measuring a tree that was not the tree at any single moment. Landing on such a run is
landing on a measurement of something that no longer exists.

**Why `git status` cannot catch this class.** Every guard this repository has for concurrency reads
*tracked files* — `tools/shared_file_overlap.py` compares file sets, a monitor watches the primary
checkout going dirty, `land.py` refuses a worktree holding an untracked file. `.venv/` is
gitignored, so the one piece of state deciding what `import pinakes` means is invisible to all of
them. The seam is not the source; it is everything the source is resolved *through*.

**What it cost and what it nearly cost.** Twenty minutes, and one report to a peer that would have
read as *this branch broke the wheel-import gate*. It did not go out that way, because the first
move was to re-run the single file rather than to explain the failure — the same discipline as
reading a gate's own exit status instead of a runner's summary, applied to a gate whose *input*
rather than whose *status* had been substituted.
