## Landing beside a peer — the overlap tool answers a different question (20260823 14:57)

**MEDIUM — a check named for a problem is not a check for that problem.**
`tools/shared_file_overlap.py --fetch --strict` reads as the collision check between concurrent
sessions, and two sessions ran it that way for a full afternoon. It compares a branch to
`origin/main`. **It never looks at another branch**, so it cannot see a peer at all: it reported
*none* while a coder held `20260823_1424-markdown-link-gate`. It was not wrong — the file
intersection genuinely was empty — but it could not have been right, because it was answering
"will this merge cleanly" and being read as "is anyone else in these files". The remedy is a
`comm -12` over the two branches' file lists, which is three lines and answers the actual
question.

**MEDIUM — the landing order can be forced, and asking your peer will not reveal it.** The
convention is that complete, gated work lands first and the other rebases, which frames order as
something two sessions *agree*. Here it was determined by a gate. The coder's new
`tools/markdown_link_gate.py` reported **11 broken links and exit non-zero against `main`**, so
its own `./check.sh` could not go green until the planner's link fixes landed — its branch was
unable to land, not merely second in a queue. **Neither session knew.** The coder was running the
gate on its own tree, where it passed; the planner found it by copying the gate out of the peer's
branch and running it against `main` and against its own worktree. **Run the peer's gate, in both
places.** A peer's report of its own state is honest and still blind, because the failing
configuration is the one it never runs.

**LOW — the same window bites twice, so it is a property of the procedure and not of one tool.**
Both sessions' link checkers crashed with `FileNotFoundError` on a file `git ls-files` lists and
the disk does not have. That state is not exotic: `docs/RELEASING.md` step 1 splices fragments and
deletes them, and `./check.sh` runs before the commit that removes them from the index. Any gate
enumerating tracked files and opening each one meets it on every release. A tracked-but-absent file
is a normal mid-release state, and the handling is a skip.
