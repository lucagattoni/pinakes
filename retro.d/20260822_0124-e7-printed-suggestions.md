## E7 — Printed suggestions, and the mutant that proved the battery blind (20260822 01:24)

**The increment that closes the deep release.** A `--deep` run ends by printing the `links[]`
entries its own citations propose. Small — one module, one CLI seam — and it turned up four defects
the tests could not see, three of them found by mutating rather than by reading.

**HIGH — the control mutant survived, and it was the *first* one run.** `docs/BUILDING.md` § 4 says
to kill a known-catchable mutant first, because a run with no kills is a broken harness rather than
a clean bill. This run had seven kills and *lost the control*: `REL = "co-cited"` → `"related"` left
all 71 tests green. Every assertion about the relation imported `REL` and compared it with itself,
so the constant and the expectation moved together. The shipped value of the thing a user pastes was
pinned by nothing.

The generalisation is worth more than the fix: **a constant imported into both sides of an assertion
is not tested, it is restated.** `test_cli_ask.py`'s `FINGERPRINT` comment says exactly this one
file away — *"a test that derives the expected value from the same object it checks would still pass
if `fingerprint()` started returning the empty string"* — and this suite was written without
noticing it applied. One literal test now names `("co-cited", "deep")`. Half of it was already
caught by accident: `rel = ""` went red, because `sidecar._links` refuses an entry without one. Only
the *plausible* wrong value survived, which is the direction that matters.

**HIGH — a test that certified containment was satisfied by absence.** The escaping-path test cited
`../outside.md`, a path with nothing at the end of it, so the read failed because the file was
missing and the assertion passed with no containment check at all. The mutation pass is what
separated them: the bypass mutant killed the neighbouring *deleted-document* test and left this one
green, on the same code. It now cites a real document in a second KB next door, with a sidecar
carrying the id the citation claims — so only containment can refuse it, and what it prevents is
nameable: a fragment carrying `pnk://<this KB>/<that KB's document>`.

**MEDIUM — three direction tests could not observe direction.** ULIDs are monotonic, and the fixture
built its documents `alpha, beta, gamma`, so the ids ascended in the same order as the paths. Every
assertion about *which* sidecar an entry lands in was green whether the code ordered by path or by
id. Minting the fixture backwards made the two orders disagree — and immediately paid: the entry
order *inside* a sidecar was by URI, which is mint order, which is arbitrary to a reader. **A
fixture whose two orderings agree cannot tell them apart, and the agreement is usually accidental.**

**MEDIUM — a newline in a filename would have broken the fragment, silently.** The module builds
YAML as text, which is defensible: every *value* in it is a ULID URI or one of two constants, and a
test pins that against `sidecar.needs_quoting`. But the document paths go into YAML **comments**,
and a POSIX filename may contain a newline — one ends the comment and turns the rest of the path
into a node. `needs_quoting` cannot see it, because it answers about a scalar and a comment is not
one. The lesson is the sibling of 0.25.3's reflowed shell command: **a value that is safe as a
scalar is not thereby safe as a comment, and the check that certifies the first says nothing about
the second.**

**Two more, from reading the diff as a stranger.** `propose` is public and re-checks every endpoint
it is handed, but would have proposed a document linked to itself — which `pnk link` refuses
outright. And resolution was quadratic in *disk* reads: a block citing n documents makes n(n-1)/2
pairs, each resolving both endpoints, so every sidecar was read and YAML-parsed n-1 times, with
`[retrieval] final_k` having no ceiling and the money already spent.

**The design decision worth keeping: observing and proposing are two functions, and the split exists
so a test can exist.** § 5's rule is that a suggestion's endpoints must be documents this run
retrieved. Enforced inside one function, the rule is unfalsifiable — every candidate comes from the
same expression that validates it, so a working guard and a missing one produce identical output on
every input a test could construct. `co_citations` observes; `propose` re-checks what it is handed;
the refusal test calls `propose` with a pair no run would produce. **A guard whose input is built by
its own validator is not a guard, and its test is a tautology in test clothing.**

**What the battery still cannot reach.** The prompt-injection test — a retrieved passage instructing
the model to add a link, obeyed in prose, producing nothing — asserts the *absence of a behaviour*.
No mutation makes it fail, because the code that would fail it was never written: nothing in the
module reads `AnswerBlock.text`. It is a real test of a real property and it is not mutation-backed,
which is the same class `docs/BUILDING.md` § 4 names as *a defect with no assertion anywhere*, seen
from the other side.

**And an old row that had been false for four releases.** `docs/DESIGN.md` §9 still bounded `--deep`
with *"no orchestration the free path doesn't have"* — written before the loop existed, and
contradicted by the loop the moment it shipped. `docs/graph/PINAKES_APPROACH.md` § 6 had asked for
that exact row to be amended in the increment that shipped the design, and named the replacement
bound. E4 shipped and the row did not move. Found here by auditing the neighbourhood rather than the
diff — **the increment that closes a release is the last cheap chance to fix what the release made
false**, because after it nobody is reading those rows for a while.

**Ten of ten mutants killed after the fixes**, control included, with the containment mutant now
caught by the containment test rather than by its neighbour.
