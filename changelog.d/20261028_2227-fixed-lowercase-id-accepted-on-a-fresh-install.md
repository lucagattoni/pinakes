- **A lowercase or mixed-case ID is refused on every `python-ulid`, not only the one the lockfile pins.**
  `ids.parse_kb_id`, `parse_doc_id` and `is_id` relied on the library refusing lowercase.
  `python-ulid` 4.1.0 reads lowercase and mixed case and returns the uppercase form. The dependency
  is `python-ulid>=3.0` and uncapped, so a fresh install of 0.32.7 resolved 4.1.0 and *normalised*
  `01kycj8zvmbjdb4fkrjrnys5dt` where `ids.py` says it must reject it. Measured 20261028 22:24:
  `is_id(minted.lower())` was `True` on `uvx --from "pinakes[light]==0.32.7"`, and four tests failed
  against the newest dependency set (`tests/test_ids.py` twice, `tests/test_uri.py`,
  `tests/test_deep_transcript.py`) while the full suite was green on the lockfile. One place it
  reaches: `transcript_path` checks `is_id` and then files the transcript under the raw string, so a
  lowercase operation id would have been filed under a second spelling. The module now requires the
  library's canonical spelling to equal its input, so the answer no longer depends on the version.
  The four tests that failed were right and are kept; they pass on 4.0.1 and 4.1.0 alike. Two new
  tests (three cases) and one new row in the malformed-ID table are the point of the change: they
  stand in a library that normalises case and fail on the old code even under 4.0.1, which the old
  tests could not — those tested the installed version, not this module. Every ID `pnk` mints is
  uppercase; a hand-edited lowercase one that a 4.1.0 install had been accepting is refused, as it
  always was on 4.0.1.
