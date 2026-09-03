## A replace-all edits fixtures you never read (20260903 12:58)

**MEDIUM — caught by a printed count, which is the only reason it was caught at all.** Adding
tests to `tests/test_eval.py`, I needed a `kind:` line in three new YAML fixtures and reached for a
whole-file string replace. I printed the occurrence count out of habit rather than suspicion:

    occurrences: 6

Three new fixtures, six matches. The other three were pre-existing fixtures belonging to other
tests, and one of them was `test_an_unknown_kind_is_refused`, whose YAML came out carrying
`kind: lexical` **and** `kind: multihop` — a duplicate key, where YAML silently takes the last.

**Every other edit in the increment went through a helper that asserts the anchor matched exactly
once and refuses otherwise. This one did not, because it was "just adding a line to my own new
tests".** The count was printed as information; had it been an assertion, the replace would not
have run.

Two things I did **not** establish, and will not claim: whether the damaged fixtures' tests still
passed — I restored the file before running them, so the honest answer is that I do not know — and
whether `git diff --stat` would have shown it. What did show it was reading the hunks: `git diff`
per-hunk, not the summary. A same-line-count replacement moves no totals, so a diffstat is weak
evidence here either way.

The recovery is the part worth reusing: **restore the file from `HEAD` and re-append only your own
block**, rather than inspecting and repairing what a replace-all touched. The block was still in
memory as a string, the restore was one command, and the resulting diff — 53 insertions, zero
deletions — is a *checkable* claim that nothing existing changed, which "I looked and it seemed
fine" is not.
