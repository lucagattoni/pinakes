- **Two bytecode tests no longer go red in a shell that exports `PYTHONDONTWRITEBYTECODE`.**
  `test_the_bytecode_cache_is_cleared_after_the_write_and_after_the_restore` and
  `test_a_stale_pyc_really_does_report_a_same_length_mutant_as_survived` ran a scratch pytest to
  leave a `.pyc` behind. Under `PYTHONDONTWRITEBYTECODE=1`, which Claude Code's shell exports, it
  left none, so both failed on *nothing warmed the cache* and `./check.sh` stopped on a tool that
  was not at fault. It was recorded as a workaround (`env -u PYTHONDONTWRITEBYTECODE ./check.sh`)
  on 20261014–15 and measured again on 20261028 and, in two other sessions, on 20261102.
  `tests/test_mutate.py` now builds those runs' environment without that variable and without
  `PYTHONPYCACHEPREFIX`, which moves the `.pyc` somewhere the tests do not look. Checked with each
  variable set alone and together, and by removing each of the tool's two `clear_pycache` calls in
  turn: both tests fail for the reason they state — *the cache survived the write*, *the cache
  survived the restore* — whether the variable is set or not, where under it they used to fail on
  the fixture whatever the tool did. A helper that strips only one of the two names is caught by the
  other. A change to the tests only; `tools/mutate.py` is untouched. Developer tooling — it ships in
  no wheel.
