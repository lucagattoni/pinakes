## A mutant killed for the wrong reason is a survivor wearing a green light (20260902 11:59)

The S4 battery came back **6 mutants, 6 killed, 0 survived** on its first run. One of the six was
not measuring what its row claimed, and the count could not say so.

The row is named *"a backslash is left raw, so a Windows-style path parses as a name nobody
typed"*. It removes the `\\` entry from `_TOML_ESCAPES`, and its whole point is the **quiet**
failure — a manifest that parses, that `pnk doctor` calls healthy, holding a name the user never
typed. It killed through the eleven-value corpus, whose backslash value is `C:\notes\kb`.

**That value cannot demonstrate the property.** It contains `\k`, which TOML defines as nothing at
all, so `tomllib` **rejects** the file:

    tomllib.TOMLDecodeError: Unescaped '\' in a string (at line 2, column 23)

A parse failure — loud, and caught by every test in the file. The round-trip half the row is named
for was asserted by nothing. Measured across three shapes:

| value | without the backslash escape |
|---|---|
| `C:\notes\kb` | **rejected** — `\k` is not an escape |
| `C:\notes` | **parses**, reads back `C:` + newline + `otes` |
| `C:\build` | **parses**, reads back `C:` + backspace + `uild` |

The fix was one test over `C:\notes` and repointing the row's `kills` at it. The mutant now dies
on `AssertionError: assert 'C:\notes' == 'C:\\notes'` — an equality, which is what the row claims.

**Three things worth keeping, none of them about escaping.**

**A clean aggregate is a fact about the harness before it is a fact about the subject.** *6 of 6
killed* has the same shape as a 30-agent verification panel that overturns nothing, and as a
mutation run with no kills: consistent with the instrument working, equally consistent with it not
discriminating, and **the run cannot tell you which**. Both happened in this repository on the same
day, hours apart. The count is the last thing to read, not the first.

**Read the kill *reason*, never the kill count.** This was found only by reading the failure text of
a mutant that was already dying. Nobody does that when the number comes back clean, which is
precisely why nothing else could have found it: `tools/mutate.py` reports KILLED correctly, the
anchor resolved exactly once, `tests/test_batteries.py` was green, and the row's prose was
self-consistent. **Every gate this repository owns was satisfied.**

**When prose names a value to demonstrate a property, run the value.** The wrong example was written
into a battery header whose own subject is *parsing is the weaker claim* — and it then survived
being relayed to a second agent and dictated back as finished prose for a third file, still
unmeasured. It was checked when it was **executed**, not when it was read, reviewed, or agreed. The
general form is now scoped onto the queued row for the post-render validator: a remedy, a docstring,
a `--help` string or a dictated paragraph that names a value to make a point is **run, not reasoned
about**.
