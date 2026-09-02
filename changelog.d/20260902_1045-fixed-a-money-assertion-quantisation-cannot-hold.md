- **A red `main` fixed: the money trace asserted an equality that quantisation cannot hold.**
  `estimate.per_request_eur` is a euro value taken *before* the ledger's deliberate quantisation; a
  reservation's `cost_eur` is the stored dollar divided back *after* it. The two agreed only while
  the exchange rate happened to make the multiply back land exactly on six decimals. Refreshing
  `prices.toml` to the 20260901 ECB fixing of `1.159` ended that, and **both `[pdf]` CI legs** —
  `check (light pdf)` and `check (light pdf claude)`, since the file's `pytestmark` skips on `[pdf]`
  alone — went red on a test that had passed for a month. The hop now asserts the reservation
  against the stored dollar at the ledger's own quantum, which is the only form that can hold.
- **A second, latent divergence closed one hop down.** The reconciliation hop compared against a
  bare `Decimal.quantize()`, which takes the context default `ROUND_HALF_EVEN`, while the ledger
  writes `ROUND_HALF_UP`. It has never fired, because today's prices make per-token USD exactly six
  decimals and so leave no tie to resolve. It is closed before it could.
- **Added:** two guards in `tests/test_ledger.py` that carry the bracketing exchange rates
  themselves rather than reading `prices.toml`, so no future price refresh can move their inputs.
  They run in every CI leg; the trace they protect runs in two of three.
