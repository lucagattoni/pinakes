## X1 — building the tracked-KB check, and an instrument that could not fail (20260825 08:16)

**HIGH — the specification asked for a test that cannot fail, and only writing it revealed that.**
The plan bound the implementation to three constraints, the first being *"the function takes the
resolved KB root and builds the absolute pathspec itself… its test must run it **from a
subdirectory** — the case that fails is invisible from the root."* That constraint was written from
a real, reproduced measurement: `git ls-files -- .pinakes` run from a subdirectory exits 0 with no
rows against a repository tracking three files. Two sessions reproduced it independently.

**It is still not reachable through this code, and the test it prescribes proves nothing.**
`_ask_git` passes `cwd=root` to `subprocess.run`, so the *process* cwd never reaches git: a bare
`.pinakes` resolves against `root` and returns the identical verdict from a subdirectory, and with
a relative root. Measured rather than argued — **with the pathspec mutated to `".pinakes"`, 68 of
the 69 tests in `tests/test_init.py` pass.** A behavioural subdirectory test would have been green
against the exact form it existed to forbid.

**So the constraint moved to where it can fail.** The pathspec is built by its own function and the
test asserts the *pathspec* — `:(literal)` prefix, absolute, ending in `.pinakes` — which is the
one test the relative form kills. The absolute-and-literal form stays, because correctness of the
relative form depends entirely on `_ask_git` keeping `cwd=root`, a coupling no caller can see, and
because a KB root may legally contain `*` or `[`. It is **defensive rather than a bug fix**, and
the docstring says so instead of implying coverage it does not have.

**The general form is worth more than the instance.** *"Pinned by test X" is a claim about a
failing test* was already the rule here. This adds the case the rule does not obviously cover: a
constraint can name a **real property**, be **derived from a real measurement**, and still
prescribe an instrument that cannot observe it. The argument was sound; the domain it quantified
over — *this* call path, rather than the shell where the measurement was taken — was never
examined. Neither session checked it. It surfaced only because the implementer refused to write
`test_…_from_a_subdirectory` without first watching it go red.

**A second gap the same discipline found.** `pinakes_tracked` is a `bool`, so `None` and `False`
collapse into one field and **no test through `init` can tell them apart** — an implementation
returning `False` outside a repository (exit 128, `fatal:` on stderr) passed every test written.
The constraint that unknown must never read as clean is now asserted against `_tracked_by_git`
directly. A field's type can erase a distinction the specification depends on.

**And the pipe hazard fired again, on the person who had just written it up.** The full gate was
run as `./check.sh > log 2>&1; echo "EXIT=$?" | tee -a log; tail -20 log`. The harness reported
**exit code 0**; the gate had exited **1**, on two `reportPrivateUsage` errors. The `$?` was
captured correctly and then discarded by the commands after it — *a gate is only a gate when its
exit status is what the next command reads*, missed by someone who had recorded that sentence
twice the same evening. **Recognition is not the mechanism. Writing the status to its own file,
and reading that file, is.** Three instances of one class in one evening, each caught by running
something rather than by reading it — and this one caught only because the log was read after the
notification said the opposite.
