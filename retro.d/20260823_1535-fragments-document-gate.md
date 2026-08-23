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
true-positive one. Both were written in the same pass; only one of them found anything. That is the
argument for writing the over-firing case even when the under-firing case is the one the item
describes: a gate refusing a correct document is the failure that gets *acted on*, and
`markdown_link_gate`'s own docstring records a peer rewriting an example into the wrong form to
satisfy a false positive before disbelieving it.

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

### The hole that was pinned rather than closed

The decided rule is *adjacency*, because that is the shape the evidence had. A heading that repeats
after intervening entries is **not** caught, and there is now a test asserting so, naming the plan
item. Widening the rule fails that test, which reopens the decision instead of quietly changing the
gate. A named hole is a decision; an unnamed one is a discovery waiting to happen.
