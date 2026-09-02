## A suspiciously clean result is a reason to check the harness, not to write it down (20260901 07:15)

**Sixteen runs agreed to the character, and not one of them had started.** Measuring how four
programs handle a mistyped `--questions`, I built the commands in a shell variable and expanded it
unquoted: `uv run --frozen $cmd --questions …`. The result was a table of sixteen rows, every one
`exit=2  Caused by: No such file or directory (os error 2)`. It reads as a finding — four tools
agreeing on a failure mode — and it is uv never having spawned an interpreter once.

**This shell is zsh, and zsh does not word-split unquoted parameter expansions.** `c2="python -c";
for w in $c2; do …` iterates **once**, over the single word `python -c`. So uv was handed one argv
element named after the whole command line and reported, accurately, that no such program exists.
Every run of mine that failed built its command in a string; every run that worked used `"$@"`,
already split. **Build commands as arrays or `"$@"` — never as a string expanded unquoted.**

**What caught it was the uniformity, not the content.** Four programs with four argument parsers do
not agree to the character; that is not agreement, it is a shared failure upstream of all four.
This repository already has the negative form of the rule — *a mutation run with no kills is a
broken harness, not a clean bill* — and this is the same shape in a different instrument. **A
result too clean to be interesting is evidence about the instrument.**

**The cost was not the wasted runs; it was the two wrong causes I published in between.** First
that `python3` is absent from the project environment and only `python` works — false, both import
`pinakes` fine in a synced worktree and in the primary checkout. Then, implicitly, that background
execution was to blame — also false, and both were plausible enough that a peer nearly deleted a
**correct** line from `RESUME.md` on the strength of the first. **An invalid measurement produces a
confident wrong cause, and the wrong cause travels further than the measurement does**, because it
is short, it is quotable, and nothing about it looks provisional. Both were caught by someone
re-running the thing rather than re-reading my sentence, which is now the fourth time this week.

**And the corpus could not have caught the defect this increment fixes.** `retro.d/` holds only
*unreleased* fragments; the rest are spliced into `docs/RETROSPECTIVES.md` and deleted at each
release. When the gate was built the live directory held **4 files and all 4 passed**, so a green
run over the corpus proved nothing — the only live counter-example anywhere was a *fixture* in
`tests/test_fragments.py`, which the new rule promptly turned red. A gate whose population is
"whatever is unreleased at this moment" cannot be validated by that population, and the census of
the *historical* fragments is a different denominator that must not be used to predict it.

**The same shape again, one instrument along: a kill is not evidence until you check which
assertion did the killing.** The battery for this gate reported **27 of 27 killed**, and one of
those kills was false. The mutant was named *"the stamp is compared by date alone, so the time may
be anything"* and was written as `clock = ""`, which makes `wanted` the string `(20260901 :)` — a
value that matches **nothing**, so the mutated gate refused *every* fragment, including correct
ones. It is the opposite of the laxity its name claims. It still died, and the report still printed
the name beside the test, so the battery carried a coverage claim for an axis nothing tested. The
faithful mutant *was* `wanted = f"({day}"` — and it stopped being faithful inside this same
increment, when the fourth pass anchored the comparison to the end of the line. `wanted` is
`re.escape`d, so `(20260901` then had to be the heading's trailing token, matched nothing, and
refused every fragment exactly as its predecessor had, the control among them. Nobody re-measured
it, because it was still *killed*. The row now mutates the anchored comparison itself. **A mutant
is faithful only against the code it currently runs against; a kill does not carry forward across
an edit to a line the mutant does not name.**

**A wrongly-credited kill is worse than a survivor.** A survivor is loud — the report says
SURVIVED and somebody looks. A kill is silent, it is what you wanted to see, and nobody rechecks a
green row. This repository already holds the negative form of the rule, *a mutation run with no
kills is a broken harness rather than a clean bill*; this is its inverse, and the two together say
the same thing about every instrument: **the output agreeing with you is not the check.**

Two independent things caught it, and neither was a test. Reading the mutation *report* rather than
the code showed the substituted string, and an adversarial reviewer later reproduced it and found
the part I had missed — under that mutant the pre-existing control
`test_the_real_documents_are_clean_which_is_this_checkers_only_control` **also** fails, because the
repository's own correctly-stamped fragments are refused. So the `kills` attribution was not merely
mis-named, it was not even exclusive.

**And a stamp read correctly off the clock can still be wrong by the time it lands.** A peer's
closure banner said 07:32 UTC — a true reading when written — and a session-limit stop landed the
merge at 11:14, leaving a document naming a time no commit exists at. The clock rule stops you
composing a number; it does not stop the world moving between the reading and the write. When a
stamp is about *when something landed*, it can only be written after it lands, or it must name both
times and the gap.

**I read a runner's summary instead of the gate's own exit status — in the increment whose whole
subject is reading the thing itself.** `./check.sh > log 2>&1; echo "CHECK_EXIT=$?" >> log`, run in
the background. The harness reported *completed (exit code 0)*: the **wrapper's** status, and the
wrapper ends in an `echo`, which always succeeds. I reported the branch green to a peer while
`CHECK_EXIT=1` sat in my own `tail` output in the same message. The `; echo "$?"` appended
*specifically* to preserve the status is what destroyed it — preserved in the file, discarded in the
wrapper. This repository already rules that **a gate is only a gate when its exit status is what the
next command reads**; the new edge is that wrapping a gate in order to *record* its status mints a
second, always-zero status for whoever is watching the wrapper. **Read the log's last line, never a
runner's summary.**

**`set -e` makes a failing gate produce no result for every gate after it, and an absence reads as a
pass.** `check.sh` stopped at the link gate, so overlap, nul-scan and template-drift never ran.
Anyone reading *check.sh failed on the link gate* concludes the rest was fine. It was **unmeasured**
— the same class as the wrapper above: a status nobody read, and an absence that looks like a pass.

**Two agents mutating one checkout measure each other, and the run reports kills either way.** The
first draft of this increment's review ran two source-mutating lenses concurrently in one worktree;
both apply a mutant to `tools/fragments.py` and restore it, and a restore by one is a false SURVIVED
for the other with nothing in the report able to tell. Rewritten before either finished: the
mutators serialized, the other lenses probing a *copy* through `tools/fragments.py --repo <tmpdir>`.
That is possible only because the tool takes its own root as an argument — **a tool parameterised by
its repository root is testable by agents that must not touch the tree**, which is worth knowing
while writing the next one.

**Two selectors, no dispute to have — and both numbers wrong anyway.** A peer measured five drifted
heading stamps shipping; I measured three; we agreed each was right under a different selector, and
neither of us had stated one. Re-measured over a population I can name — every `retro.d/` path that ever
carried a `YYYYMMDD_HHMM-` prefix, each read at its own adding commit — the triple is **six** drifted
*when written*, **three** still wrong in the published document, and **three** fixed by hand between
fragment and splice (`fbf17da` wrote `(20260826 07:31)` and the shipped line reads `(20260826 07:33)`;
`a54b304`, whose subject is *"applying the new rule to my own fragments found three"*, makes exactly
those three stamp corrections — it changes a fourth file and appends thirty-eight lines of new
prose to one of the three above that file's own one-line stamp fix, neither of them a stamp, so it
*touches* four).

**And the population needs a measurement point and a selector, because it has both and I wrote
neither.** `git rev-list <sha> --objects`, deduplicated, paths matching
`^retro\.d/\d{8}_\d{4}-.*\.md$`: **111** at `56a970c` and still 111 at this branch's tip
`6cb80b4` — 107 at the branch point `8540e27`, so the number moved inside this branch alone. Three
other defensible spellings of the same question, all at `6cb80b4`: adding a `-- retro.d` pathspec
gives **102**, because a pathspec turns on history simplification and prunes merge sides (adding
`--full-history` back restores 111, which is how that was confirmed rather than assumed);
`git log --full-history --diff-filter=A` gives **109**, because a path introduced by a merge was
never *added* by any commit it walks; and plain `git log --diff-filter=A` gives **100**, losing
both. Four selectors, spread eleven apart, and the sentence above named none of them until now. The arithmetic was the tell we both walked past: five minus two
is not three, and six minus three is.
**State the selector even when the other party agrees with you**: agreement between two unstated
populations is a coincidence, not a confirmation.

**The general shape of the defect this gate sits beside.** This gate reads a relation whose **both**
operands are inside its input — the heading against the filename, one file, nothing else consulted.
`tools/markdown_link_gate.py` reads one operand of a relation whose other operand lives in the
*destination* document. A gate holding half a relation can always be wrong about a form that is
correct where it lands, and it is wrong in **both** directions: green on the branch and broken after
splicing, or red on the branch and correct after. One missing operand, two signs. The fix is not a
new rule for that gate; it is handing it the operand it never had.
