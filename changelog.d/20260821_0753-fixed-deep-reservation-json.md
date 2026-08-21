- **`tools/deep_reservation.py --json` raised `TypeError` on both subcommands.** `vars()` on a
  `slots=True` dataclass has no `__dict__` to return, so `count --json` and `report --json` both
  died on their first row. Nothing had ever called it — E6's measurement runs read the printed
  table — so four releases of green tests never touched the branch. It now dumps through
  `dataclasses.asdict` and carries `factor`, which is a property on both row types and would
  otherwise have been missing from the machine-readable output while the table beside it printed
  the number the whole run exists to produce.
