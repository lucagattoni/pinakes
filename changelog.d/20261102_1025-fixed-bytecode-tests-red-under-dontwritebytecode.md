- **Two bytecode tests no longer go red in a shell that exports `PYTHONDONTWRITEBYTECODE`.**
  `test_the_bytecode_cache_is_cleared_after_the_write_and_after_the_restore` and
  `test_a_stale_pyc_really_does_report_a_same_length_mutant_as_survived` run a scratch pytest to
  leave a `.pyc` behind and then look for it. Under `PYTHONDONTWRITEBYTECODE=1`, which Claude
  Code's shell exports, none is written: the first failed on *nothing warmed the cache*, the second
  on *expected one cached bytecode file, found []*, and `./check.sh` stopped on a tool that was not
  at fault. It was recorded as a workaround (`env -u PYTHONDONTWRITEBYTECODE ./check.sh`) on
  20261014–15 and is met by any session whose shell exports the variable. `tests/test_mutate.py`
  now builds the environment of the three runs that need a `.pyc` without it. A new test pins that
  where CI can see it: CI exports no such variable, so the two tests passed there whether or not the
  helper worked. Checked by removing each of the tool's two `clear_pycache` calls in turn: the first
  test fails for the reason it states — *the cache survived the write*, *the cache survived the
  restore* — with the variable set or not, where under it the test used to fail on the fixture
  whatever the tool did. The second test is a control on the interpreter and never calls the tool,
  so it does not move. **Not changed, so not claimed:** `test_a_same_length_mutant_is_killed_end_to_end`
  is not a pin on the clearing — with the clearing removed it failed 5 runs of 8 with the variable
  unset (a race on the clock) and 0 of 8 with it set, because the tool's own child runs then write no
  `.pyc` at all — and a shell that exports `PYTHONPYCACHEPREFIX` fails 40 of the file's 74
  tests, as it did before this change, because the tool refuses it by design. A change to the tests only;
  `tools/mutate.py` is untouched. Developer tooling — it ships in no wheel.
