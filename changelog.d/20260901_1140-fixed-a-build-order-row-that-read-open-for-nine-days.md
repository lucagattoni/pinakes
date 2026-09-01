- **A build-order row read open for nine days after its work landed.** Sweep-plan row 3 (S3, the
  per-thread connection in `pnk serve`) was fixed by `e526e29` on 20260831 22:22 UTC —
  `src/pinakes/serve.py:107-153`, five tests, including one asserting S3's own symptom — and the row
  never changed. A peer reading `src/` found it; no gate did. It is now marked BUILT with its commit.
- **Every other open row in that build order was measured against the tree and is correctly open** —
  one agent per row plus an independent spot-check of two verdicts. Rows 4, 5, 6, 8, 9 and 10 each
  now carry a **dated measurement** with the citation that settles it, rather than a bare status:
  `sync.py:693` for S1, `template.py:209-223` for S4, `cli.py:333` for S8/S9, `pairing.py:481-483`
  for D-37, and so on.
- **The two registers in that plan rot at very different rates, and the difference is readership.**
  The build order — the table an implementer opens to pick up work — measured 1 stale row in 7 (14%).
  The parked table below it, which exists so that nobody has to read it, measured 4 in 8 (50%). Both
  numbers are now recorded in the plan with the audit that produced them.
