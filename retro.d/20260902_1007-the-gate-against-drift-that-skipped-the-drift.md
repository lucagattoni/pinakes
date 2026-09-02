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
absent.** Row 15's counts were wrong for the same reason and by the same amount: 30 sections
counted, 36 on disk; one non-conformance, two.

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
