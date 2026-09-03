## Three mutants killed for the wrong reason in one increment, and the pattern has three shapes (20260903 09:03)

A mutation battery reports `KILLED` when the named test fails. It does not report **which
assertion** failed, in its summary table — and the table is what gets read, quoted into a commit
message and carried into a fragment. Three rows in the S4 battery died on an assertion other than
the one their name claimed. Each is a different mechanism, and each is generalisable.

### 1. The mutant was a *safe* version of the edit it names

Row: *the refusal echoes the value it is refusing, straight to the terminal.* It substituted
`{text!r}` — and `repr` escapes a surrogate and an ESC **by construction**, so the mutant produced
a terminal-safe echo. Measured:

| assertion | `{text!r}` | `U+…{ord} in {text}` |
|---|---|---|
| `"U+DCFF" in message` | **False** ← the only kill | True |
| `"\udcff" not in message` | True | **False** |
| `"\x1b" not in message` | True | **False** |

The kill came from the words `U+DCFF` going missing. The two assertions the test's docstring calls
load-bearing — *never echoes the value* — were never measured at all, and would have survived a
mutant that actually echoed.

**The check:** a mutant is written against a *property*, so name the assertion it must fail before
writing it. "Does the test go red" is the weaker question, and it is the one the tool answers.

### 2. The mutant raised a different exception, so every assertion after `raises` was unreachable

Row: *the surrogate arm is removed.* Under it, the refusal never fires, `Path.write_text` raises
`UnicodeEncodeError`, and `pytest.raises(TemplateError)` does not catch it. The test dies **at the
`raises`**, so the line below it — `assert not root.exists()`, which the docstring calls the
load-bearing half — never runs. Measured against the real `init()`: `root.exists()` True,
`pinakes.toml` 0 bytes.

This is structural, not a slip: **assertions written after a `pytest.raises` block are pinned only
by mutants that keep the raise.** A mutant that removes the raising code cannot reach them, however
green the report looks.

No edit to `template.py` could fix it, because `render_manifest` runs before `root.mkdir` — so the
row moved to `src-pinakes-init.toml` and mutates the **ordering** instead. It now kills on
`assert not True`.

### 3. A more general arm below shadowed the specific one

`_TOML_ESCAPES` maps `\b`, `\f`, `\n`, `\r` to their single-letter escapes. Every one of them also
satisfies the `\uXXXX` fallback two branches down. Drop any entry and the manifest still parses and
still round-trips the exact value — **every round-trip test in the file stays green**, and no
mutant could distinguish four lines of live code.

What separates them is only the bytes a human opens: `name = "a\nb"` against `name = "a
b"`.
That is now asserted, in the same shape as the tab control.

**The strongest demonstration was accidental.** The planner, having just read the description
above, tried to build the unescaped case by dropping `\n` from the map — and the output still came
out escaped, because the fallback caught it silently. It had to disable *both* arms to see the
defect. A shadowed line resists being shown to be shadowed, by someone who already knows it is.

**The check:** for any specific case, ask whether a more general arm below it produces an
acceptable answer. If it does, the specific arm is unobservable and the test suite is silent about
whether it exists.

### What the tool does and does not print

`tools/mutate.py` **does** print the failing assertion, on the per-mutant line. All three of these
were found by reading that line. What it does not do is put it in the summary table, which reads

    | <row name> | KILLED | <test id> |

— the row's own claim about itself, and no evidence for it. That table is what gets read and
quoted. Moving the reason into it is rowed, not built here.

*(This section is itself the fourth claim in this increment asserted before being run: an earlier
draft said the tool prints no kill reason at all. It was written inside the paragraph about
evidence going unread.)*

### Why the corpus could not have found any of the three

Same shape as [this increment's surrogate
finding](#s4s-fix-reproduced-s4-on-the-one-value-class-the-framing-excluded-20260902-2118): every
artefact asked *does the test go red*, and all three defects live in *why* it went red. A count
cannot carry that, and neither can a green suite. What found them was a review pass that re-derived
each kill's reason — one question per row, asked of evidence the tool had already printed.
