- **The test suite no longer reads the wall clock against the committed price table.** `prices.toml`
  aged past `[budget] max_price_age_days` on 20260827 and 25 tests began failing with no commit
  anywhere near them — the suite had quietly become the CI staleness gate that
  [`docs/DESIGN.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/DESIGN.md) §5 and
  `check.sh`'s own prices-toml gate both deliberately refuse to be. The seam is the **table**, not
  the clock: an autouse fixture calls the real `load_prices()` and replaces exactly one field,
  `as_of`, so every model price, the FX rate and the parse of the committed file stay real and the
  tests that assert a real UTC stamp still do. It reaches only `cli.py` and `sync.py`, which import
  `load_prices` inside a function; a module that binds the name at import time still reads the
  committed `as_of` for real, which is where `pnk doctor`'s price-table checks and the paid-path
  gates keep checking it. `pnk doctor`'s own OK case now pins a fresh table exactly as its sibling
  one function below pins an aged one. **Nothing about the shipped table changed**: an installed
  copy older than `max_price_age_days` still WARNs in `pnk doctor` and still refuses to price a
  paid run, which is the design working as specified.
