- **A lowercase or mixed-case ID is refused on every `python-ulid`, not only the one the lockfile pins.**
  `ids.parse_kb_id`, `parse_doc_id` and `is_id` relied on the library refusing lowercase, and
  `python-ulid` 4.1.0 reads it — lowercase and mixed case — and returns the uppercase form. The
  dependency is `python-ulid>=3.0` and uncapped, so a fresh install of 0.32.7 resolved 4.1.0 and
  treated `01kycj8zvmbjdb4fkrjrnys5dt` as a valid ID: the one thing the module says it must not do,
  because two spellings of one identity slip past the duplicate-ID check. Measured 20261028 22:24:
  `is_id(minted.lower())` was `True` on `uvx --from "pinakes[light]==0.32.7"`, and four tests failed
  against the newest dependency set (`tests/test_ids.py` twice, `tests/test_uri.py`,
  `tests/test_deep_transcript.py`) while the full suite was green on the lockfile. The module now
  requires the library's canonical spelling to equal its input, so the answer no longer depends on
  the version. The tests that failed were right and are kept; they pass on 4.0.1 and 4.1.0 alike.
  Two are new and the point of the change: they stand in a library that normalises case and fail on
  the old code even under 4.0.1, which the old tests could not — they tested the installed version,
  not this module. Nothing on disk changes: every ID `pnk` ever minted is uppercase.
