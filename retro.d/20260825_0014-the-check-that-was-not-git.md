## The check that was not git — and the mutant that was not a test (20260825 00:14)

**HIGH — a substring test stood in for git's ignore semantics, and it was wrong in both
directions.** `pnk init` decided whether a KB's `.pinakes/` could reach a remote with
`".pinakes/" not in gitignore.read_text()`. Four failure modes, all reproduced by running rather
than by reading:

| `.gitignore` contains | git ignores `.pinakes/`? | `init` said | |
|---|---|---|---|
| `.pinakes` (no slash) | yes | ⚠️ warns | false positive |
| `.pin*` | yes | ⚠️ warns | false positive |
| `.pinakes/` then `!.pinakes/` | no | silent | false negative |
| `#.pinakes/` | no | silent | **false negative, with a consequence** |

The two false positives train a user to disregard the warning. The false negatives are worse
because they are silent, and the commented-out line is the cheapest way to reach one: comment it
out to debug, re-run `init`, and the ledger and every transcript are tracked with nothing said.

**The general shape: a cheap proxy for an authority, where the authority was one subprocess away.**
git already knows what git ignores — it reads nested ignore files, `.git/info/exclude`, the user's
global excludes and a parent repository's rules, none of which any amount of reading one
`.gitignore` can see. The proxy was not a simplification of the rule; it was a different rule that
agreed with it on the common case.

**MEDIUM — the measurement trap that makes this easy to get wrong twice.**
`git check-ignore .pinakes` returns *not ignored* for the pattern `.pinakes/` whenever the
directory does not exist on disk: a trailing slash only matches a path git can already see is a
directory. At `init` time `.pinakes/` has never been created, so the obvious probe answers
"unprotected" for the very pattern `init` itself writes. A path *inside* the directory carries the
directory in its own name and answers correctly either way. Anyone re-testing this by hand must
`mkdir .pinakes` first, or a correct pattern will look broken.

**MEDIUM — `check-ignore` exits 0 when _any_ argument is ignored, not when all are.** Probing three
paths and reading the exit status would have called a `.gitignore` naming only the ledger full
protection, while the index stayed tracked. The matched paths have to be counted.

**HIGH — the survivor was the useful half of the mutation run, and it found redundant code rather
than a missing test.** Seven mutants; six killed. The survivor deleted an explicit
`startswith("#")` comment-skip from the offline fallback, and every test stayed green. Not a
coverage gap: `"#.pinakes/".rstrip("/")` is `"#.pinakes"`, which already fails a whole-line
equality test, so the skip never decided anything. The code claimed a care it did not exercise,
and the docstring said so in as many words. The loop became one `any(...)`, and the row now
mutates the property that is really load-bearing — whole-line equality against
`".pinakes" in text`, which *is* the shipped defect. **A SURVIVED row is a claim about a pair, and
this time the wrong half was the code.**

**MEDIUM — the tests answered from the developer's machine.** `check-ignore` honours a global
`core.excludesFile` and a system config. A developer with `.pinakes/` in their personal global
ignore file — a sensible thing to have — turned three of these tests red and made two others pass
for a reason the code had nothing to do with (measured: 3 failed, 9 passed). An autouse fixture
points `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` at `os.devnull`. The production code still
honours those files, because a global ignore really does protect the ledger; only the tests must
not depend on which machine runs them. **A test that shells out inherits the whole environment,
and the environment is not part of the fixture unless it is made to be.**

**This is the first mutation battery under `src/`.** Every other one covers `tools/`, which
`tools/batteries/README.md` records as a limitation rather than a design — *"no module under
`src/` has one, and no invariant in INVARIANTS is covered."* The decision that keeps an index, a
spend ledger and a set of verbatim questions off a remote is a reasonable place to stop being able
to say that.

**Scope, deliberately held.** Only the existing one-shot check's *correctness* changed. Whether
`pnk doctor` should carry a recurring check, and whether it reports a warning or a note, is a
decision reserved to the planner and the user — and this measurement changes it rather than
settling it: a detector that misfires on `.pinakes` and `.pin*` is a poor candidate for firing on
every `doctor` run, and a correct one is a much better one.
