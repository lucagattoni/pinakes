## A gate against unnoticed drift, and the two shapes it nearly could not see (20260902 10:07)

Row 15 was recorded as one comment on one line: a battery section header reading `# 20260823 · …`
where the reserved forms are a version or `unreleased, YYYYMMDD`. The header itself had already
been fixed. What was left was the gate — refused once, while the question of whether adding a check
counted as new process was open, and unblocked when that question was answered.

Writing it produced two findings, and neither was the one the row described.

**The audit could not see the second instance, because of the shape of its own selector.** Row 15
concluded this was *"the only one matching neither"*. It was not. `src-pinakes-pairing.toml` carried
`# unreleased, 20260831 - S16's residue: …` — a hyphen standing exactly where the `·` separator
belongs. The audit had searched for headers containing `·`, so the one other non-conforming header
in the tree was the single shape its query could not return. The gate found it on its first run.
**A selector defined by the correct form cannot find a violation that consists of that form being
absent.** The row's other numbers fail the same way, and its own arithmetic said so without any
re-measurement: it reported *30 sections, 19 `unreleased, YYYYMMDD ·`, 8 `X.Y.Z ·`, one matching
neither* — and 19 + 8 + 1 is 28, two short of its own stated total. Measured at `a4077b5`, the
commit that wrote it, the tree held 30 sections: **20** unreleased, 8 version, **two** matching
neither. One invisible header is missing from exactly two tallies, which is exactly the two the row
was short.

**And I made the neighbouring error while correcting it.** My first correction tabulated *36
sections, 26, 9, 2* against the row's *30, 19, 8, 1* and called the total wrong. It was not: the
tree grew from 30 to 36 between `a4077b5` and today, and the row's 30 and its 8 were both right for
the tree it was measuring. What was wrong was 19 and *only one*. Comparing today's tree against a
claim about a past tree turns growth into error and hides the real defect — so a count correction
has to name the commit it was measured at, not just the selector.

**Then the gate itself nearly shipped with the identical defect.** Battery sections are fenced by
horizontal rules, and the first `RULE` regex matched only the box-drawing `U+2500`. Nine batteries
use it. Two use ASCII hyphens — and one of those two was `src-pinakes-pairing.toml`. So the gate
read **34 of the tree's 36 headers, reported a clean sweep, and the file it skipped was one of the
two that had drifted.** A gate written to catch unnoticed drift, silently skipping the drift, on its
first run, in the increment whose whole subject is a selector that could not match its target.

It was caught by refusing to accept a clean result. `non-conforming: []` is a null result, and a
null result carries no information until the instrument has been shown able to fire; counting the
headers found against the headers on disk is what turned `[]` from a pass into a discrepancy. The
same discipline had already been spent twice this increment — on a search assertion that passed for
a word in no document, and on a `git cat-file` lookup where zsh ate `:t` out of `"$tag:tools/x.py"`
as a history modifier and reported a file absent from a tag that contains it.

**What generalises: a checker's own matcher is part of what it checks, and it is the part nobody
tests.** The assertions were right in all three cases. What was wrong was the set they ran over.
So the gate now counts both fence shapes, says in a comment why rather than leaving a magic
alternation, and the docstring names what it deliberately does not check — calendar validity, and
section ordering — because a gate that quietly grows a second subject is how the next selector ends
up not matching the thing it is looking for.
