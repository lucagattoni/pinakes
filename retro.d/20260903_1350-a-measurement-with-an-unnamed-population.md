## A measurement with an unnamed population, copied forward three times (20260903 13:50)

**HIGH — the sentence said *measured*, and it was. It was measured on one interpreter and written
as though it were about the language.** Row 8 left this comment in `sync.py`:

> Measured, not assumed: `exists()` swallows the `PermissionError` and returns False.

That was true. It was run, the value came out of the run, and the phrase *measured, not assumed*
was earned — on Python 3.14. On 3.13 `Path.exists()` raises, and `pyproject.toml` promises 3.13.
The claim's population was one interpreter out of the two this project supports, and nothing in
the sentence said so.

**Then it was copied into two more places** — a test docstring and a mutation-battery row comment
— each time as settled fact, each time propagating a scope nobody had ever stated. Three
locations, one measurement, zero mentions of what it was measured on.

**The failure mode is not laziness, it is that the guard against it was already engaged.** *Measured,
not assumed* is the phrase this repository uses to mark a claim as checked, so the sentence
arrived pre-defended: a reader looking for unverified assertions skips it, and a reader looking for
scope sees a word that promises rigour. A false claim with no evidence gets challenged. A true
claim over an unnamed domain does not, because the challenge it invites — *did you check?* — has
already been answered.

**The question that catches it is not "did you measure?" but "measured on what?"** For anything
whose answer can differ across an axis the project spans — interpreter, OS, filesystem, extra,
locale — the population belongs *in the sentence*. The corrected comment now carries a table with
both interpreters named and both versions given, because a table cannot omit its own columns the
way a sentence can omit its own scope.

Related: [[a-null-result-carries-no-information]] and the 20260831 record of six wrong claims in
one day, each a valid inference over a population nobody named. This is that shape again, with the
extra twist that the inference here was not merely valid but genuinely executed.
