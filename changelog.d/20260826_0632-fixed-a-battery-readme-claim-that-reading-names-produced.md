- **`tools/batteries/README.md` no longer says a covered module is uncovered.** Its denominator
  paragraph named `src/pinakes/cli.py` as one of *"the two highest-churn modules … [that] still have
  none"*, while `src-pinakes-init.toml` mutates it twice. The claim came from reading battery
  **names** rather than their targets, and the same error hides more of the map than one line:
  `tools-mcp_handshake_gate.toml` reaches **seven** files, including `Makefile`, `check.sh`,
  `pyproject.toml` and both CI workflows. The paragraph now separates the two cases — `doctor.py`
  genuinely has none; `cli.py` is covered without being named — and gives the command that answers
  the question directly, `grep -h 'file = ' tools/batteries/*.toml | sort -u`. **Its own gate could
  not have caught this**: `tests/test_batteries.py` forces a battery whose name does not begin
  `tools-` to be listed, and nothing checks a claim about what the batteries reach.
