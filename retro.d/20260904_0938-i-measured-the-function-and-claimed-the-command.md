## Row 43 — I measured the function and made a claim about the command (20260904 09:38)

**HIGH — an isolated measurement is evidence about what you called, never about what the user
runs, and the gap between those two is where I put a false finding.** Row 36 sent me to probe the
`pathlib` predicate sites nobody had looked at. I called two of them directly, watched
`PermissionError` on 3.13 and silence on 3.14, and reported **two live defects on the declared
floor** — including *"ends `pnk sync` in a raw traceback"*. The divergence was real and
reproducible. **The consequence was invented.** Measured afterwards, against the real command:
`pnk sync` on that state produces **byte-identical reports on both interpreters**, both call sites
of the first function sit inside `except (PinakesError, OSError)`, and the second is unreachable
because `manifest.load` refuses an untraversable root before `apply` ever runs. **Reachable count:
zero.** The planner filed a row and ranked it above a gate design on that report.

**HIGH — the thing that caught it was the test failing to fail.** I wrote the end-to-end test
first. It passed. Then I reverted the one-word fix and ran it again — **it passed again**. A test
green with and without the change under test pins nothing, and that is what sent me looking for the
call path instead of banking the finding. **That is row 41's own method, turned on row 41's author
about an hour after it was written up**, and it is the second time in one day the same check has
caught something: once in the audit, once in the auditor.

**MEDIUM — the strongest argument for closing a class rather than fixing instances came from
being wrong.** The reason my `sync.py` finding is unreachable is **row 31's own guard**:
`unreadable_directories` refuses the directory at the walk, so the per-file path is never entered.
A fix that landed the same morning, one level above the site, had already closed the class the site
belongs to. Nobody planned that overlap and it is the clearest evidence for the ordering the queue
keeps arguing about.

**MEDIUM — what a hygiene change has to say about itself to survive.** Both lines still changed —
one word each — because the codebase has decided `paths.py` owns this question and these were the
last holdouts on user paths. But each docstring now states plainly that **no production path
reaches it today**, how that was measured, and **what would change it**: the walk guard narrowing,
or a caller dropping its `except`. Without that last clause the next reader deletes the change as
pointless, and without the first two they inherit my false claim in a comment.

**MEDIUM — a test that discriminates on one interpreter should say so in its own docstring.** Both
new tests are red on 3.13 without their fix and green on 3.14 either way, because the unfixed
spelling already returned `False` there. Stated in the tests rather than left for someone to
discover when a 3.14-only run reports them as covering something.
