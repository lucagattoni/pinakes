- **`tools/review_ledger.py` — a later review pass no longer starts from zero.** Adversarial review
  is the largest single category of subagent spend in this project, and later passes spend it
  re-deriving what earlier passes established. Measured over the 910 subagent transcripts on this
  machine (5.14B raw tokens, newest 20260826 11:32 UTC): **35.6% of a later pass's raw tokens go to turns whose only file
  access was a file an earlier pass over the same increment had already opened**, against 3.0% for
  turns that opened something new — and **40.1%** for the 69 passes costing over 5M raw tokens,
  because a re-read early in a long pass is re-transmitted by every turn after it. 96% of what the median later
  pass opens was already opened by an earlier one. The tool reconstructs, from the transcripts
  already on disk and with no cooperation from any pass, what earlier ones **ran** (deduplicated
  across each reviewer's own scratch directory, so seventeen passes writing the same `pytest`
  invocation read as one probe run seventeen times), what they **opened**, what they **reported**,
  and — the only section that is a gap rather than a summary — what the increment changed that
  **nobody opened**. It leads with the passes that did not finish: a rate-limited agent's last
  message is ordinary assistant text, so a partial pass reads as coverage exactly as an empty
  fan-out reads as a clean bill ([`tools/review_pass_gate.py`](https://github.com/lucagattoni/pinakes/blob/main/tools/review_pass_gate.py),
  one layer down). Three disclaimers print on every brief, because a carried map is the cheapest
  way yet found to make a later pass inherit an earlier one's mistake: opened is not reviewed, a
  printed command is not an exit status, a quoted finding is not a fact. `--measure` re-derives
  every number in the module docstring, since a number in a docstring is otherwise a claim with no
  way to check it.
