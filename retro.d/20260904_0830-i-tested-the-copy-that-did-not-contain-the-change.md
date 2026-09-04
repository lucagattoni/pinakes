## Row 39 — I tested the copy that did not contain the change, and broke `main` doing it (20260904 08:30)

**HIGH — a smoke test run against the wrong binary reads exactly like a passing one.** I had just
written the guard that refuses to land an ungated tree, and I wanted to watch it refuse. So I
committed it as WIP and ran `python3 tools/land.py <my branch>` from the primary checkout,
expecting a refusal. **It landed, and pushed** — because `land.py` executes from the *primary
checkout*, which still held `main`'s ungated copy. I had written the sentence *"the gate runs in
the branch's worktree and this refusal runs here"* into that same file minutes earlier. **The
instrument did not contain the thing under test**, which is the identical shape as the vacuous test
found hours before: an injection that no longer intercepted anything, and a result that read as
informative because nothing about the output says which code produced it.

**HIGH — the change broke `main`, and the way it broke is the argument for the change.** Six
`tests/test_land.py` tests went red immediately: their scratch repositories never run `./check.sh`,
so the new guard correctly refused every landing they assert. The tests were right, the guard was
right, and they had never been introduced to each other. **What actually put a red tree on
`origin/main` was not the guard — it was landing without running `./check.sh` at all**, which is
precisely what the guard makes impossible. It could not stop me because it was not yet on `main`:
**this guard's own landing is the one landing it cannot police.** That bootstrapping hole is worth
stating rather than smiling at, because it is the general case — a gate can never cover the commit
that introduces it, so that commit needs the discipline the gate is replacing.

**HIGH — the planner caught a hole that would have made the guard blind exactly where it matters,
and the measurement was worse than the report.** The first design keyed the marker to the branch's
tree. But `git merge --no-ff` combines the branch with a `main` that may have moved, and the result
is then neither side's tree. Reported as one merge in three; **measured across all four merges
available, it was two of four** — and both were mine. So the guard would have passed while a tree
nobody had gated reached `origin/main`: the *a clean auto-merge is not a correct merge* case, with
the guard asleep in the one situation it exists for. `git merge-tree --write-tree` computes the
merge result without performing it, touching neither the working tree nor `HEAD`, and predicted the
real tree in all four — so the check happens *before* the merge rather than after it with a reset
to undo.

**MEDIUM — the absence of an escape hatch is a feature, so it is asserted rather than assumed.** A
flaky or environmental red now blocks a landing; a suite killed by machine contention did exactly
that the same night, correctly. The first person to meet that at 3am will want `--no-gate`, and a
test now fails if one appears. The reason it does not exist is that the rule being skippable is
what put the guard here in the first place.
