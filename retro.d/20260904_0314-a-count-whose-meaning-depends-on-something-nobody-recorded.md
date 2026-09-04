## Row 40 — a count whose meaning depended on something nobody recorded (20260904 03:14)

**HIGH — an equivalent mutant and an unpinned assertion are byte-identical in the report, and I
read one as the other.** A committed row came back SURVIVED and I reported it as an unkilled mutant
*and* as a coverage gap. Both halves were wrong. On the newer interpreter the mutated and unmutated
programs behave identically — both spellings of the predicate answer `False` — so nothing could
kill it, and the silence I called a gap is produced by the **fixed** code too, which makes it a
different open question rather than a hole in this battery. What I actually had was narrower and
still worth the row: **the same battery gives two different counts on two interpreters, and the
report never said which one you were reading.**

**HIGH — the fix asked for was the wrong fix, and building it literally would have been worse than
building nothing.** The row said to print `sys.version`. `mutate.py`'s own `sys.version` is the
*launcher's*, and the documented invocation is `python3 tools/mutate.py` — the system interpreter —
while the tests run under `uv run --frozen pytest`, the project venv. Measured by making them
differ on purpose: launcher 3.14.7, venv 3.13.15. The literal implementation would have printed
**3.14.7** beside counts produced entirely by **3.13.15** — an answer that reads as measured and
names a Python no test touched. **A wrong number in a sentence that looks like evidence is worse
than an absent one**, which is why the unprobeable case says *could not identify* instead of
falling back.

**MEDIUM — placement is delivery.** The `pytest = …` command has been printed in this tool's
header the whole time and never answered this question, because the header is what gets left in the
terminal and the counts are what gets pasted into a commit message. The new line goes beside the
counts, and a mutant pins that ordering — a correct sentence in the wrong place is indistinguishable
from an absent one at the moment somebody needs it.

**MEDIUM — the honest way to report an instrument you cannot read.** Two command shapes are probed
because two are documented; anything else returns nothing rather than a guess. That is the stance
this tool already takes towards a JUnit report it cannot parse — *the outcome is unknown rather
than SURVIVED* — and applying it to the interpreter as well cost one `if` and removed a whole class
of confidently wrong report.
