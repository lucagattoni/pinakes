- **A `pnk doctor` test that asserted only that the diagnosis finished now asserts what it found.**
  `test_an_unreadable_paid_document_does_not_crash_the_whole_diagnosis` injected a read failure and
  then checked only that two check names appeared in the report — true whether or not anything was
  denied. It passed with its own injection disabled, so it would have gone on passing the day the
  production code stopped calling `Path.read_bytes`. No behaviour change; the test now fails if the
  denial never reaches the code under test.
