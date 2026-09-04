- **`tools/land.py` now refuses to land a tree no `./check.sh` run has certified.** `check.sh`
  records each tree it passes on, and a landing looks up the tree the merge will actually
  produce — not the branch's, which differs whenever `main` has moved. There is no override flag:
  a gate nobody read is the thing the refusal exists for, and a way to skip it would be the same
  hole with a name. `--cleanup-only` is exempt, since it lands nothing. The refusal names the tree
  it wanted, and says what it cannot catch: a tree that was gated, edited, and edited back to the
  same hash is indistinguishable from one never touched.
