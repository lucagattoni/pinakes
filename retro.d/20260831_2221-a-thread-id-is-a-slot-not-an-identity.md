- **A defect in how threads share a handle is invisible to a suite that never starts a thread.**
  `tests/test_serve.py` had no thread anywhere in it. The bug was not missed by a weak assertion; it
  was outside the shape of every test in the file. **The trigger was a property of the transport,
  and the transport was the part nobody was testing** — `serve.py` starts no threads, so reading it
  end to end tells you it is single-threaded, and that reading is what the tests encoded.
- **The inherited explanation of *when* it fires was wrong, and only running it said so.** The
  finding came with a mechanism — a worker retired after ten idle seconds, so the first call after
  a pause gets a new thread — and it is a correct account of `anyio`. It is not what fails. Driven
  through the real `mcp.call_tool`, an eleven-second pause reproduced **nothing**: the retired
  worker's thread id had already been reused by its replacement, and `sqlite3` compares ids, so it
  saw one thread. What did reproduce, on every attempt, was `close()` — shutdown runs on a thread
  that opened nothing — and, under six concurrent calls, four of six raising `ProgrammingError`.
  **The trigger is contention, not idleness.** The mechanism was sound, the population was never
  checked, and the first commit message asserted the pause as though it had been measured; it is
  corrected in the follow-up rather than left to read as evidence.
- **A thread id is a slot the OS reuses, not an identity — and it faked a passing test.** The first
  version of the rebuild test ran two worker threads in succession and **passed against the unfixed
  code**. macOS had handed the second thread the id of the first the moment the first was reclaimed;
  `sqlite3` compares ids, saw one thread, and allowed the reuse it exists to refuse. Measured
  directly: three successive `anyio` workers reported one identical `get_ident()` and three
  different `Thread` objects. Two consequences, one for the test and one for the fix — the opener
  must be a thread that is still *running* when the reader starts, and the per-thread cache is keyed
  by the thread object, because keying by id both hands a new thread a dead one's handle and makes a
  dead entry indistinguishable from a live one, which is the entry reaping exists to find.
- **The control is what turned this from a plausible fix into a pinned one.** Reverting the fix
  failed three of the four tests *in their bodies*; the fourth — the handle-count bound — is red
  under the old design only because the attribute does not exist, so it was checked separately by
  deleting `_reap_dead_threads()` alone (`assert 12 <= 2`). Without running both controls the weak
  test above would have shipped as a certificate, and its docstring now says which control it
  answers to.
- **The seam is named in the test that has one.** Driving real `threading.Thread`s proves the
  handler is per-thread; it does not prove the transport ever uses a second thread. That half is the
  whole premise of the fix, so it is asserted against `mcp` directly rather than assumed — a probe
  tool that records the thread it ran on. If the library stops offloading sync tools, that test goes
  red and says so, and nothing else in the suite would have noticed.
- **The measurement that corrected it also found a second defect nobody had named.** Counting the
  connections actually opened showed the old `connection()` testing and assigning one shared slot
  with no lock: threads arriving together each opened one, the last assignment won, and the losers
  stayed open, unreferenced and unclosable. That race is why *some* concurrent calls answered — a
  thread that won it was using a connection it had opened itself — so the leak was also the thing
  hiding the failure. Neither would have been found by reasoning about the fix; both came from
  instrumenting the run and asking how many, rather than whether.
