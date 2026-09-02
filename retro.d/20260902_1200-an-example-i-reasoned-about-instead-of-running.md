## An example I reasoned about instead of running (20260902 12:00)

I dictated a sentence into `tools/batteries/README.md` claiming that without the backslash escape,
`C:\notes\kb` renders **valid TOML** that reads back as a name nobody typed. The coder's mutation
run falsified it before it landed. `tomllib` **rejects** that value — `\k` is not a TOML escape at
all — so the mutant it described dies on a parse error, which is the opposite of the point the
sentence was making.

The phenomenon is real; the example did not have the property. `C:\notes` parses and reads back as
`C:` + newline + `otes`; `C:\build` parses and reads back as `C:` + backspace + `uild`. Three
seconds of `tomllib.loads` separates them, and I ran it only after being contradicted.

**Where it was going to land is the part worth keeping.** That README's own subject is that
*parsing is the weaker claim*, and the paragraph exists to teach the difference between a manifest
that parses and one that round-trips. A worked example that fails on the parse side would have
taught the opposite of the file's thesis, in the file's own voice, under a heading that made it
authoritative.

**The rule this repository already had did not cover it.** *A claim resting on a set you selected
must state the selector* is about populations. *The command ran, the number was typed* is about a
figure copied out of prose instead of out of output. Neither reaches a **value chosen to
demonstrate a property**, which is not a measurement at all — it is an argument, and it feels like
reasoning rather than reporting, so nothing prompts you to execute it. The generalisation:

> **When a message, a header, a docstring, a remedy or a `--help` line names a value in order to
> demonstrate a property, the value is run, not reasoned about.** An example is a claim with an
> executable form, and the executable form takes seconds.

**The catch came from a mutation run, and only because someone read the failure text.** The battery
reported six mutants killed and none survived. One of the six was dying on a `TOMLDecodeError`
while its row claimed a round-trip property that nothing in the suite asserted — so the row was
green on a weaker property than its own name disclaims. A clean kill count concealed it; the kill
*reason* did not. **A mutant killed for the wrong reason is a survivor wearing a green light**, and
the aggregate that hid it has the same shape as a refuter panel that overturns nothing and a
`Blocked on` cell nobody re-reads: a number that describes the instrument rather than the subject.

**What the exchange did right.** The coder held the dictated text rather than pasting it, said
which claim it was refusing and why, and brought the run output and a three-row table of measured
values. Refusing planner-dictated prose is the harder direction of the ownership split — the whole
mechanism is *content mine, keystrokes yours* — and it is exactly the direction that has to work,
because a dictated sentence arrives with more authority than it has earned.
