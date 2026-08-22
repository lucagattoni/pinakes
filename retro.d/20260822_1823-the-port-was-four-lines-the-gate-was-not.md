## The mcp 2.x port — the port was four lines, the gate was not (20260822 18:23)

**HIGH — A gate whose passing depends on a dependency's teardown timing is not a gate.** The
handshake in both workflows wrote three JSON-RPC lines into `pnk serve` and closed stdin. Measured
on the same three lines, same KB, ten runs each:

| | `initialize` answered | `tools/list` answered |
|---|---|---|
| `mcp` 1.28.1 | 10/10 | **10/10** |
| `mcp` 2.0.0 | 10/10 | **2/10** |
| a real `ClientSession`, 2.0.0 | 8/8 | **8/8** |

1.x drained the queue before shutting down on EOF; 2.x does not. Nothing in the step named that
dependency, and nothing could have: it is a property of a library's shutdown path, not of its API.
The generalisation is worth more than the instance — **if a check's passing depends on a race
nobody in this repository wrote, it is not a check** — and the remedy is not a longer sleep but
removing the race's cause, which here meant driving the session with a client that holds the
connection open until it has its answers.

**The timing is the uncomfortable part.** That handshake was written **the same morning**, in
0.27.2, *to catch the `mcp` outage* — and it was written against the behaviour of the version it
was about to lose. A gate built for a dependency major was itself a hostage to that major. `git
log -S '"method":"initialize"'` returns exactly two commits: the one that added it and the one that
removed it, four hours apart.

**HIGH — The third copy is the one nobody looks at.** Two workflows were fixed; `make smoke` — the
pre-tag check a maintainer actually runs — kept the dead shape and was **red on every run** against
a healthy wheel. Review found it, and found the second half too: `test_make_smoke_exercises_the_wheel_rather_than_only_its_version`
asserted `'"method":"initialize"' in body` and passed, certifying "drives a handshake" against a
recipe that no longer produced one. **When a shape is replaced because it is wrong, grep the whole
tree for that shape before believing it is gone** — and check what the tests pinning the old copies
now assert, because a test written against an implementation outlives the implementation.

**HIGH — There is no independent source of a project's own version inside its own checkout.** The
version test compared what the server advertised against `importlib.metadata.version("pinakes")`,
reaching for independence from `pinakes.__version__`. `[tool.hatch.version]` reads that same file,
so the metadata is the same constant copied into `.dist-info` **at install time** — and `uv run`
does not refresh it when the constant changes. Bumping `__version__` to cut the release diverged
them at once and reddened two tests, with a message blaming the `serverInfo` defect the increment
had just fixed. **A landmine the release commit would have stepped on twenty minutes later.**

The lesson is not "use the other source". It is that **a longer route to the same origin is not a
second opinion**, and saying so in the docstring is worth more than the appearance of rigour. The
genuine cross-check exists, but only in CI: the expected value comes from the built **wheel's
filename** and the advertised one from a separately installed copy of it.

**MEDIUM — An error message is part of the assertion surface.** `assert EXPECTED in result.stderr`
looked like it checked that a failure names what was expected. It was satisfied by the gate's own
sentence, *"Until 0.27.2 this field carried the mcp library's version"* — because `EXPECTED` was
`0.27.2`. The assertion held with the fix deleted. **A version literal in a diagnostic is a value a
test may accidentally be reading**; the message now names no version.

**MEDIUM — The negative form of a rule is not the rule.** Two exit-status pins asserted the absence
of one literal string, `out=$(timeout` — the shape the step used to have. `| tee`, `|| true`, `if
…; then` and a backticked capture all stayed green, and `| tee` is the *likely* edit, since the
shape it replaced existed precisely to print the gate's output. The positive form —
*this invocation is a simple command under `timeout`* — is one assertion instead of an
ever-growing list of forbidden ones. Generally: **when a rule says "the status must reach `set
-e`", assert the shape that makes it true, never the shapes that made it false last time.**

**MEDIUM — `step["run"]` is a YAML literal block, comments included.** `release.yml`'s pins were
bare substring searches over it, so commenting out the commands left every assertion satisfied by
the prose above them. Its `ci.yml` twin had required *command* lines since 0.27.2 for exactly this
reason and the release side never got it — **a fix applied to one of two twins is half a fix, and
the release path is the half where being wrong is irreversible.**

**MEDIUM — The only untested branch was the one the gate exists for.** A server dead on import —
the 0.27.2 outage itself — reached the gate's generic session-failure path, and no test drove it.
Also untested: the timeout ceiling and `serverInfo.name`. All three now have one, and `--timeout`
became a real flag so the timeout test costs a second rather than thirty. **Ask which branch the
tool was built for, and check that one has a test before counting the others.**

**MEDIUM — A test can pin a message and leave the behaviour free.** The timeout test asserted
`"no complete session in 1s"` and nothing about the clock. The mutation battery wired `timeout=` to
a constant while the message still read the flag, and reported `ERRORED` rather than a kill — the
harness refusing to call a run that never finished either a kill or a survivor, which is exactly
what `tools/mutate.py` was built to do. The test now asserts elapsed time as well, with a loose
bound: what must be true is *seconds rather than the job*.

**LOW, and a pattern rather than an item — four false statements, all in prose written to explain
why the code was careful.** `SESSION_TIMEOUT_SECONDS` was commented "Ten" beside a value of 30; a
docstring said comparing `__version__` with itself "would hold with the `version=` argument
deleted", which is simply untrue; `tools/wheel_import_gate.py` still said `uv.lock` *pins* 1.28.1;
and a changelog fragment called the flaky handshake "a coin flip that landed the same way for a
year" when `git log -S` puts it at four hours old in a repository 28 days old. **Explanatory prose
is where false claims accumulate, because it is written once, at the moment of most confidence, and
never re-read against the code it explains.**

**LOW — Two run-the-real-thing checks that no unit test could replace.** The three CI legs were run
verbatim against a built wheel resolved fresh onto `mcp` 2.0.0, which is the only way to learn that
`uv run --isolated --no-project --with <wheel>` puts `pnk` on `PATH` for a *child* process the gate
spawns. And the gate's timeout was driven with a shim that spawns and stays silent: it exits 1 after
32s and leaves no orphan behind it.

**Process — the primary checkout's tree can change under a running gate.** A peer session ran
`tools/land.py` while `./check.sh` was running in that same directory, and three tests failed with
*"matched 0 `# Part` heading(s)"* — loud, plausible, and pointed at the file the peer had just
touched. Nothing was wrong; a re-run at the new sha was green. **Run gates in your own worktree.
The primary checkout is where landings happen and its tree can change under a running pytest at any
moment; a red run there may be about a tree that no longer exists.**

**Review economics, recorded because the numbers are the argument.** Round one: four lenses over the
diff, each finding verified by an adversarial refuter. 31 findings raised, **19 confirmed and 12
refuted** — and the refutations were substantive, one of them disproving a claimed process-group
escape by reading `multiprocessing.util.spawnv_passfds` on the machine. Two of the confirmed
findings were defects I had already found myself; the other seventeen I had not. The mutation
battery grew from 15 to 24 mutants over the same increment, all killed. **The refutation stage
earned its cost twice over: it is what makes 19 findings worth reading rather than 31 worth
arguing with.**
