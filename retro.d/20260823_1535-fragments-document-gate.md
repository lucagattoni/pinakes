## The gate that read everything except its own output (20260823 15:11)

`tools/fragments.py --check` had run in `check.sh` since 0.24.0. It parsed every pending fragment —
category, slug, emptiness, a leading `---` fence — and asserted **nothing** about the document
`--apply` produces. Three malformed regions sat in `CHANGELOG.md` through every green run, and the
one that names the class was found by reading a release precedent, not by any gate.

**The shape is worth naming, because it is not a missing check — it is a checker pointed one step
short of the thing it exists to protect.** Every other gate here reads *rows*: `mkdocs --strict`
resolves links, `release_order_gate` reads sequences, `markdown_link_gate` reads link targets. A
duplicated heading is a property of *adjacency*, so all of them walk straight past two identical
headings in a row. Nothing in this repository had ever read the assembled file at all.

### The bug this increment shipped, and what caught it

The first draft anchored its fence detector at column zero. `CHANGELOG.md` contains **no
column-zero fence**; its only fenced block is indented two spaces inside a bullet. So the scanner
skipped nothing in the one document it most needs to read, and a changelog entry demonstrating a
Markdown heading would have been refused as document structure.

**It was caught by the test written for it, before landing** — the false-positive test, not the
true-positive one. Both were written in the same pass; only one of them found anything. **A passing
true-positive says nothing about what the checker is failing to look at.** That is the argument for
writing the over-firing case even when the under-firing case is the one the item describes: a gate
refusing a correct document is the failure that gets *acted on*, and `markdown_link_gate`'s own
docstring records a peer rewriting an example into the wrong form to satisfy a false positive
before disbelieving it.

### What the false-positive probe found instead

Probing the `- ` rule against Markdown a changelog author might plausibly write turned up a defect
that has nothing to do with this gate. The 0.24.0 front-matter residue — `---` / `category: added`
/ `---`, spliced verbatim before `check` refused that shape — is **not inert text**. A `---` after
a *text* line underlines it into a **setext H2**, so each residue renders as a heading titled with
its own metadata. There are **five**, not the three this module recorded: three in `CHANGELOG.md`
under `## [0.24.0]` and two in `docs/RETROSPECTIVES.md`, which the original count missed because it
looked only at the stream the refusal was written for. The published site carried
`<h2 id="category-lesson">category: lesson</h2>` twice — page, permalinks and search index. All
five were removed at `9718aaa`, in the same afternoon and by the agent that owns those documents.

Every instrument is green on it. `mkdocs build --strict` resolves links and a spurious heading is
not a broken link; `markdown_link_gate` reads link targets; and **this increment's own gate misses
it**, because it reads ATX headings and this is setext. Which is the same sentence as the item it
closes, one level up: *a defect that exists only in the assembled document is invisible to every
instrument pointed somewhere else in it.* The documents are the planner's to repair and a setext
rule is a plan decision, so this increment recorded the measurement and changed no behaviour.

### The mutation pass, and the survivor that was not mine

Twelve mutants, and the first run reported ten killed and two survived. Both survivors were real.

| Mutant | First run | Why |
|---|---|---|
| the front-matter refusal no longer reaches `--apply` | **SURVIVED** | **0.27.1's row, de-fanged by this increment.** The document gate gave `--apply` a *second* reason to refuse that same fragment: a spliced `---` is not a `- ` list item either. Every assertion in the test stayed true through the mutant |
| the bullet rule reaches the free-form stream | **SURVIVED** | my own discriminating row. The fixture was built from `##` headings and the bullet rule only ever reads a `###`, so the scoping guard could be deleted with the test still green |

**The first is the one to remember. Adding a guard can silently un-pin a different guard**, when
both refuse the same input and the test between them asserts only *that* it was refused. Nothing
about the front-matter check changed; a test that had killed its mutant for three releases stopped,
because a second correct behaviour started covering for it. A test that cannot say **which** guard
fired pins neither, the moment a second one exists. It now names the refusal.

The second says the ordinary thing about fixtures: a fixture that omits the construct the rule
reads exercises nothing. The real `docs/RETROSPECTIVES.md` carries thirty-four `###` headings,
every one opening with prose — the fixture now carries one. Re-run: **12 killed, 0 survived.**

### What the adversarial pass found, and the shape all three share

Five lenses over the diff. Three real defects, none of them in the two rules the item decided —
**all three in the machinery around them**, and every one reproduced end to end (written, fragments
deleted, exit 0, follow-up `--check` green on the wreckage) before it was touched.

| Defect | Why it was invisible |
|---|---|
| `_merge_into_section` spliced an entry **inside a fenced code block** | The checker skips fences; the splicer did not. A column-zero ```` ``` ```` holding `### Added` was a heading to one and not the other |
| `splice` would take a **quoted `## [Unreleased]`** as the insertion point | Same disagreement, one function up — it would bury every future release inside a code block |
| `--apply` **was not atomic across streams** | Refusing on the second stream wrote the first and deleted its fragments, then exited 1 saying *"Nothing written, no fragment deleted"* |

**The first two are one sentence: a checker and the code it checks must agree about what a heading
is.** Before this increment nothing read the document, so the splicer's fence-blindness had no
second party and was merely latent — genuinely harmless, for eleven releases. Adding a gate that
*claims* `--apply` cannot leave the document malformed is what converted a latent asymmetry into a
false claim, and that is why closing it belonged in this change rather than in a new item.

The third is the plainer lesson and the one with teeth: **a refusal message is an assertion about
the world, and it was false.** "Nothing written" was true of the stream that failed and false of
the run. A release step is one step or none.

### The check stopped being read-only, and that is a cost worth naming

The item's stated defect is that `--check` *"asserts nothing about the result of `--apply`"*. The
first draft read the file **on disk** — which asserts something about the result of the *previous*
`--apply`, and nothing about the next one, the one the sentence names. So the narrow draft
satisfied a weaker item. `--check` now validates the assembly the pending fragments would produce.

**The evidence is the replay.** Both instances the item cites came from a fragment whose body opens
with its own `### Fixed`. Run against the tree as it stood at each of those commits, the widened
check exits 1 **at the commit that added the fragment** — at 0.6.0, whose duplicate was
hand-repaired seven minutes after release, and at 0.28.3, twenty-two days before anyone noticed.
Both exited 0 before, and the failure surfaced at release time — **which is exactly when
`docs/RELEASING.md` has somebody weighing whether to hand-edit a document to get a release out.**

**And the cost, which a peer named and this increment had not.** `--check` is no longer a
read-only validator: it simulates the write. So `--check` and `--apply` must agree about assembly
**forever**, and a disagreement between them would be *silent* — `--check` green on an assembly
`--apply` would never produce. That is this increment's own failure mode, reintroduced one layer
up. It is not an argument against the widening; it is the argument for making the two **the same
code** rather than two paths that agree: `main` calls `prospective`, the function `--check`
validates through, and a test imports the module by path and compares the predicted bytes against
what the real subprocess writes. A refactor that gives either path its own assembly turns it red.

**Every new guard buys a new invariant.** Three of this increment's four defects were the previous
instance of that: a checker and a splicer that disagreed about what a heading is, harmless for
eleven releases because nothing read the document, and false the moment something did.

### The hole that was pinned rather than closed

The decided rule is *adjacency*, because that is the shape the evidence had. A heading that repeats
after intervening entries is **not** caught, and there is now a test asserting so, naming the plan
item. Widening the rule fails that test, which reopens the decision instead of quietly changing the
gate. A named hole is a decision; an unnamed one is a discovery waiting to happen.
