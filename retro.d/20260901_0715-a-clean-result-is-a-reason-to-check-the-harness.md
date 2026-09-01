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
faithful mutant is `wanted = f"({day}"`, which accepts a valid heading *and* the date-only form and
so can only be caught by the looseness test that names it.

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
