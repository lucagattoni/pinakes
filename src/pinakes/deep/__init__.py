"""`pnk ask --deep` — the bounded reasoning loop (the deep release).

**This package's `__init__` imports nothing, and that is load-bearing.** `pnk ask` *without*
`--deep` is a free command that will import `pinakes.deep.estimate` to print what answering would
cost, and a package `__init__` that reached for `client` would drag the paid client into the free
path through the import system alone — with every gate still green, because
`tools/paid_path_gate.py` greps for the import statement it would not find here.
`tests/test_paid_path.py`'s subprocess run is what would catch it, and it should never have to.
"""
