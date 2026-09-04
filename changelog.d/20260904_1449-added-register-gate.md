- **`tools/register_gate.py` — a register's documented row counts, checked against the files it
  names.** The process-review harvest's `README.md` stated three different row counts for one
  dataset, and the one under its own *"the two questions this harvest was steered to answer"*
  heading was a figure withdrawn twice, 4.4x too high, fourteen lines below the block withdrawing
  it. Nothing was wrong with the file; the register describing it had never been compared to it.
  Wired into `./check.sh`, which prints how many rows it compared so a vacuous pass is visible as
  one. Developer tooling — it ships in no wheel.
