## `make release-check` — a gate that could not fail, and what that says about the others (20260826 06:38)

**HIGH — the target had a help string, a `docs/RELEASING.md` step, a `CLAUDE.md` rule and a
`docs/STATUS.md` sentence, and no comparison anywhere in its recipe.** Four documents described a
check; the recipe printed three lines and exited 0. Nothing was wrong with any single document —
each was written by someone who had read the others. **The failure is that a target's documentation
and a target's exit status are separate artifacts, and only one of them is executable.** The
generalisable form: *a check named in four places and implemented in none is indistinguishable, from
every document, from a check that works.* It survived from the target's creation to 20260826, and
what found it was neither a gate nor a reader of the Makefile — it was a planner building an
argument that rested on the phrase *"the tree `make release-check` was run against"* and going to
read what that meant.

**The remedy is not "test the gate" — it is `make help` and the recipe pinned in one test.** The
`##` string is what a release operator reads and it is *not* an argument to the recipe, so the two
can disagree silently forever. `test_the_release_check_help_string_and_its_recipe_are_pinned_together`
holds them together. Two of this increment's mutants are the same idea one layer down: commenting
the recipe out (`make` hands `\t#…` to `/bin/sh`, which exits 0) and a single leading `-` (`make`
discards that line's exit status). Both restore *"the target cannot fail"* in one character, and
both now die.

**MEDIUM — a `KILLED` row is not self-validating, and this is the mirror of the survivor rule the
batteries README already states.** The mutant for *"an annotated tag with an empty message passes"*
was written as `if not …: → if False:`. It reported `KILLED`. It was killed by an `IndexError`
traceback out of `splitlines()[0]`, not by the exit code — because removing that branch does not
make the empty-message case pass, it makes the tool crash. So the row was a true statement about
the wrong property: *the tests notice a broken tool*, not *the tests notice an unannotated tag being
waved through*. Rewritten as an early `return 0`, it dies on `assert 0 == 1`. **Read what killed a
mutant, not that something did** — `mutate.py` prints the assertion, and it is the only place the
distinction is visible.

**MEDIUM — the increment's own test of its own gate had the escape hatch the gate exists to
remove.** Nine of the eleven tests supply `--repo` and `--expect-version`, so the defaults are a
region no fixture reaches; the one test covering them read
`assert str(ROOT) in output or result.returncode == 0`, and on the green branch the `or` carried it
and it could not fail. An unfailable assertion inside the increment whose entire subject is an
unfailable check. **A test seam does not only hide the real path — it concentrates the temptation
to write a weak assertion there**, because that is where a strong one is awkward. The repair was
two assertions that can fail plus two mutants (`REPO` repointed, the default version hard-coded to
`0.0.0`) that are invisible to every other test in the file.

**LOW, and named rather than closed: the gate never asks whether `HEAD` is on the remote's default
branch.** A tag on an unpushed commit passes all four legs, and pushing it hands the publishing
workflow bytes that are on no branch. Every offline form of the check is wrong — a remote-tracking
ref is as stale as the last fetch, and the remote's tip may be an object this clone does not have —
and the correct form has to fetch, which makes a release gate mutate local state and go red for
being *behind*, a state that is not a publish hazard. Left to the procedure, which lands and pushes
before it tags. **The reasoning is in the tool's docstring, not only here**, because the next person
to notice the gap will be reading the tool.

**A citation is a measurement, again, and this time it was caught inside the same increment.** The
docstring's gap paragraph first read *"steps 4 and 5 land and push before step 6 creates the tag"* —
citing a numbering that only exists in a diff still sitting with the planner. Rewritten number-free.
The same pass kept `docs/RELEASING.md`'s steps 6 and 7 **unrenumbered** for the same reason: five
live citations name *"`docs/RELEASING.md` step 8"* — in `CHANGELOG.md`, `docs/STATUS.md`,
`docs/ROADMAP.md`, `.github/workflows/release.yml` and `tests/test_check_script.py` — and pushing
that step to 9 would leave every one off by one, silently, in the exact class this repository has
now recorded five passes of.
