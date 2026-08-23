- **The Guide said every command in it was run against `0.2.0`.** That stamp had been on the
  published site for twenty-six releases — the whole of this project's life bar four days — and
  nine output blocks and four prose claims had drifted behind it. Every command on the page has now
  been re-run against `0.28.1` and the outputs replaced with what it printed: `pnk templates` and
  both `pnk init` blocks said `notes@1.1` where the shipped template is `1.2`; the `You get:` tree
  omitted the `README.md` and `eval/questions.yaml` that `init` really writes; the two `pnk ask`
  estimates read `€0.26` and `€1.69` against a live `€0.20` and `€1.33`, having gone stale when
  `deep/estimate.py` was re-measured in `0.25.3`; the budget refusal quoted `€1.69` and named the
  `decomposition` branch where a KB with no calibrated signal is told `unknown`; and `pnk upgrade`'s
  cap example showed `0.05 → 0.30` against a real `0.30 → 2.00`.
- **Three places said only one thing in Pinakes can spend money.** `pnk ask --deep` has been the
  second since `0.24.0`. `docs/GUIDE.md` claimed it in *Watching what it costs* and again in
  *Troubleshooting*, and described `per_operation_eur` as bounding one `pnk sync` when it bounds one
  whole command, a deep run's every round included. `docs/CLI.md` had it right already, which is
  what made the Guide's version findable.
- **`cannot compare` no longer happens to every KB in existence, and two documents still said it
  did.** The archive has shipped `notes@1.1` since `0.17.0` and `notes@1.2` since `0.24.0`, so only
  a KB predating the archive lands there. The message itself enumerates what the build ships and now
  reads `notes@1.1, notes@1.2`; `docs/GUIDE.md` and `docs/CLI.md` were quoting the one-version form.
