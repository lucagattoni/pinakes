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

**HIGH — the replacement's first draft was a *regression*, and only an adversarial pass found it.**
It probed three named files: `index.db`, `ledger.jsonl`, `deep/transcript.json`. A `.gitignore`
carrying `*.db` and `*.json` — an ordinary thing to write — ignores all three, so the new check
reported **protected** while `index.db-wal` stayed tracked, and in WAL mode that file holds
megabytes of verbatim document text. **The substring test being replaced warned there.** The
general shape is worth more than the instance: *a check that answers about three filenames cannot
answer a question about a directory*, and the docstring's careful reasoning that every probe must
match made the answer sound complete when the probe set was the incomplete part. **A sound argument over
an unstated domain** — every clause true, the population unexamined, which is the same skeleton as
the version framing that opened this session and as the status-word grep that swept `plans/`. Three
instances in one night, in three unrelated places. The probes are now opaque random paths only a
directory-covering rule can match.

**MEDIUM — a reviewer's fix is a hypothesis exactly like the code it corrects.** The
suggestion was two opaque probes, flat and nested. Measured against ground truth — `git add -A`
then `git ls-files --cached`, so the oracle never goes through `check-ignore` — that set still
reports protected for `.pinakes/*` with `!.pinakes/cache`, which tracks the entire extraction
cache. Four probes, two of them under `cache/extract/` and `deep/`, is what passes all eleven
configurations. The review was **right about the defect and wrong about the fix**, and only
measurement separated those two — a distinction that disappears if a reviewer's remedy is applied
because the reviewer was right about the problem.

**MEDIUM — a hand-rolled fallback disagreed with the thing it was standing in for.** Outside a
repository the text scan read `.pinakes/` followed by `!.pinakes/` as protection — silently, on the
very input the in-repo tests assert must warn — and warned about `/.pinakes/`, which git honours.
Two definitions of one answer will diverge; the fallback now copies the `.gitignore` into a
throwaway repository and runs the identical probes, and reading the file is reached only when there
is no `git` at all.

**MEDIUM — the increment had quietly widened its own trigger, and justified it with something
false.** The check was made to run whether the `.gitignore` was adopted or written, on the reasoning
that an ancestor repository could negate what `init` wrote. It cannot: git resolves ignore rules by
directory depth, so the file written in the KB wins over any ancestor. What the widening *did*
reach was a path already in the index, where `check-ignore` reports not-ignored and the warning
would tell the user to add a line their file already contains. Narrowed back, and the message that
case produces was fixed rather than left: **the printed remedy must never instruct an action that
would not change the verdict**, which the old text could not violate — under a substring test the
string's presence *was* the verdict, so a redundant remedy was impossible. Asking git split
"unprotected" from "the line is missing" into two facts and the message went on assuming they were
one. **A capability arrives with the failure modes it makes reachable, and they are invisible from
inside the change that adds it.** **Scope creep that survives is usually scope creep with a
plausible comment attached.**

**HIGH — two mutation survivors, and both were about the test rather than the code.** The first
deleted a `startswith("#")` comment-skip and nothing went red: `"#.pinakes/".rstrip("/")` already
fails whole-line equality, so the skip decided nothing and the docstring claimed a care it did not
exercise. The second was `len(matched) > 0` surviving against
`test_ignoring_only_part_of_pinakes_is_not_protection` — a test whose *name* is that assertion. Its
input had been a `.gitignore` naming only the ledger, which discriminated while the probes were
named files and stopped discriminating the moment they became opaque: no probe matches, so "any"
and "all" agree. **A test can stop pinning the property it is named for without changing a
character**, when what changed is the code it points at.

**MEDIUM — the tests answered from the developer's machine.** `check-ignore` honours a global
`core.excludesFile` and a system config. A developer with `.pinakes/` in their personal global
ignore file — a sensible thing to have — turned three of these tests red and made two others pass
for a reason the code had nothing to do with (measured: 3 failed, 9 passed). An autouse fixture
points `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` at `os.devnull`. The production code still
honours those files, because a global ignore really does protect the ledger; only the tests must
not depend on which machine runs them. **A test that shells out inherits the whole environment, and
the environment is not part of the fixture unless it is made to be.**

**MEDIUM — shelling out brought six failure modes that had nothing to do with ignore rules.** No
timeout, so a wedged `core.fsmonitor` hook blocks `init` forever — *after* `pinakes.toml` is
written, leaving a KB the next `pnk init` refuses as already a KB. An inherited `GIT_DIR` answering
for an unrelated repository, which git exports to every hook it runs. Exit 1 read as an
authoritative *not ignored* when git had in fact printed a warning. `text=True` decoding strictly
*inside* `subprocess.run`, past `except OSError`. An inherited stdin. And a non-UTF-8 `.gitignore`
aborting with a traceback. Each has a test. **The cost of asking an authority is that you inherit
its whole process model, not just its answer.**

**This is the first mutation battery under `src/`.** Every other one covers `tools/`, which
`tools/batteries/README.md` records as a limitation rather than a design — *"no module under
`src/` has one, and no invariant in INVARIANTS is covered."* The decision that keeps an index, a
spend ledger and a set of verbatim questions off a remote is a reasonable place to stop being able
to say that. Updating that sentence surfaced that it was already stale: it said *"Four batteries,
four primary targets"* with five on disk. The paragraph that exists to prevent a hidden denominator
had one.

**Scope, deliberately held.** Only the existing check's *correctness* changed — and its trigger, once
widened, was put back. Whether `pnk doctor` should carry a recurring check, and whether it reports a
warning or a note, is a decision reserved to the planner and the user, and this measurement changes
it rather than settling it: a detector that misfires on `.pinakes` and `.pin*` is a poor candidate
for firing on every `doctor` run, and a correct one is a much better one.
