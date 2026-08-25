## The diagnostic that printed nothing, and a review of a moving target (20260825 00:53)

**HIGH — the fix for "a remedy that changes nothing" was an instruction that shows nothing.** The
message printed `git check-ignore -v .pinakes/index.db`. That command reports only *positively
matched* paths, and the branch printing it exists precisely because the path is **not** matched, so
it emitted nothing at all. One defect replaced by the same defect one step along, inside the commit
whose subject line forbade the first.

**The test is why it shipped, and the shape is general.** It asserted the message *contained the
string* `git check-ignore -v`. **Asserting that a message mentions a command is not a test that the
command helps.** The replacement extracts the suggested line out of the printed warning, runs it,
and asserts both that it produces output and that the output contains the negation the user has to
remove. **A test that reads a string can only ever verify the string.**

**MEDIUM — and the sentence describing the *replacement* overclaimed in turn, which is the fourth
instance today.** The proposed docs line said the command shows *"the `!` that defeats the rule"*.
It shows the lines that **name** `.pinakes` — so when the defeating pattern is spelled some other
way (`!.pin*`, `!.pi?akes/`, a broader `!*`, all of which reach the same branch and were verified
to) the line that actually causes the problem is not printed. Caught by a reviewer running a case
the author had not chosen, which is what caught the three before it. **The typical case described
as though it were the only case** — the same shape as the probe set, the version framing and the
status-word grep, in four unrelated places in one night.

**Left deliberately, and named here so it is not rediscovered as a defect.** A diagnostic that
*always* shows the conflicting rule is a larger design question — `cat -n .gitignore`? a
`check-ignore -v` against a path git does match? — and it belongs with the rest of the reserved
gitignore work rather than in a release being held. The shipped command prints something real in
every case the branch fires, which is the improvement; it is not guaranteed to print the *cause*.

**MEDIUM — a review is a measurement with a timestamp.** The adversarial pass took long enough that
the branch moved five times under it, and reviewers measured different commits: several findings
labelled critical were already fixed when they were written, and the adjudicator had to re-run two
survivor claims to find both already killed. Its own caution is the lesson — **a long review of a
moving branch measures a tree nobody will ever ship** — and the response is not to review faster but
to re-verify every finding against the tree as it stands before acting on its severity.

**MEDIUM — the same test-hygiene defect, one layer further out.** An earlier fix in this line
pointed `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` at `os.devnull` so a developer's global
excludes could not decide the answer. It closed the *config* leak and left the *ancestor
repository* open: with `pytest --basetemp` inside a checkout that ignores `.pinakes/`, three tests
failed and two of them are named *outside a repository* while running inside one. **The fixture
covered the half that had been thought of** — the same sentence as the mutation battery two hours
earlier, about a different artefact.

**MEDIUM — two things were in one list because they share a prefix.** `GIT_DIR` and
`GIT_WORK_TREE` *redirect* git at a different repository and must never be honoured here.
`GIT_CEILING_DIRECTORIES` only *limits upward discovery*, so honouring it makes this check agree
with the user's own `git add` and scrubbing it made the two disagree. Naming a constant for what
its members look like rather than for what they do is how the wrong one gets in.

**And a note on the review arrangement itself, because it worked in both directions.** The planner
amended a `docs/CLI.md` sentence specifically to stop it overclaiming what the code does — and
approved the correction by comparing the prose to the *implementer's description* of the code
rather than running the command. A description-versus-code check performed entirely on
descriptions. Caught within the hour by an independent pass, which is the argument for having one.
