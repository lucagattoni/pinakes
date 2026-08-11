- **A `docs` run that never reported success had already deployed the site**, recorded in
  [STATUS](docs/STATUS.md) as the mirror of every earlier entry in that section. Both jobs
  succeeded and the Pages deployment reached `success` at 14:21:20, while the run object froze at
  `in_progress` twenty seconds earlier and stayed there; `gh run cancel` and the documented
  `force-cancel` escalation both return **HTTP 500**, so it cannot be cleared from outside GitHub.
  **The rule that made it legible cuts both ways** — verify the artifact, never the run's own
  status — and the note names the operational cost: `docs.yml` serialises on
  `concurrency: {group: pages, cancel-in-progress: false}`, so a wedged run holds that group and the
  next `docs/` push queues behind it instead of superseding it. Also fixed: the *First upload* row
  still said `12:32 UTC (0.22.1)` after 0.22.2 shipped at 13:53.
