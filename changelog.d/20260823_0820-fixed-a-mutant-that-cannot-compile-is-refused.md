- **`tools/mutate.py` refuses a Python mutant whose result does not compile**, with the anchor
  pre-flight and before the first write. Found by the tool on its own corpus: a repaired anchor
  whose `new` had been left behind produced `keyword argument repeated` — a `SyntaxError` at import,
  which arrives as an ordinary assertion failure when a module is imported *inside* a test rather
  than at collection. The row read `KILLED` in a batch reporting `0 errored`, about a property never
  exercised. `ast.parse` would not catch it: it accepts `f(a=1, a=2)` and `compile()` does not. The
  ERRORED outcome still covers every invalidity only a run can discover — the syntax half moves
  earlier, per this tool's own rule that a refusal available before the first write is made there.
