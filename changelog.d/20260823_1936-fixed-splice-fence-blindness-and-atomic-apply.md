- **`--apply` spliced entries inside fenced code blocks, and was not atomic across streams.** Three
  defects, each reproduced end to end before repair — written, fragments deleted, exit 0, and a
  follow-up `--check` green on the wreckage. `_merge_into_section` and `splice` scanned for
  headings without skipping fenced blocks, so a column-zero fence containing `### Added` was a
  heading to the splicer and not to the new gate: an entry landed *inside* the code block,
  rendering as sample code, invisible to the check that exists to catch it. The same disagreement
  one function up let a changelog entry quoting `## [Unreleased]` become the insertion point for
  every future release. And `--apply` walks two streams: refusing on the second wrote the first and
  deleted its fragments, then exited 1 printing *"Nothing written, no fragment deleted"* — false
  about a half-applied release, in the direction that destroys the evidence. Every stream is now
  spliced and validated before any stream is written. Separately, an unclosed fence made the
  scanner swallow every line below it and still report the document well-formed; it now refuses,
  naming the fence's own line.
