- **`tools/mutate.py` now names the interpreter its counts came from.** A battery's verdict can
  depend on the Python it runs under — a mutant can be *equivalent* on one interpreter and killable
  on another — so `67 killed` and `66 killed` could both be true of the same tree with nothing in
  the report to tell them apart. The summary line beside the counts now reads
  `tests ran under Python 3.13.15 at …`. It asks the battery's own `pytest` command rather than
  reporting the interpreter `mutate.py` itself is running on, because the documented invocation is
  `python3 tools/mutate.py` and the tests run under the project venv — those differ, and the
  launcher's version would name a Python no test had touched. A `pytest` command it cannot probe is
  reported as *could not identify*, never guessed at.
