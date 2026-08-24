## A closing note credited a fix that predated the defect, and the defect recurred twice (20260824 00:23)

`tools/fragments.py` spliced two consecutive `### Fixed` headings into `CHANGELOG.md` at **0.6.0**,
and again at **0.28.3**, twenty-two days later. Between the two, the item describing it was closed.
**The closing note named a mechanism that could not have fixed it, and the evidence for that was
already in `git log` when the note was written.**

| When | What | Verified by |
|---|---|---|
| 20260729 04:20 | `_merge_into_section` introduced (0.3.0) | `9f7ed5c`, the only commit `git log -S'_merge_into_section'` returns |
| 20260801 10:53 | **0.6.0 ships with two `### Fixed`** — three days *later* | `68ca96b`; two headings under `## [0.6.0]` at that commit |
| 20260801 11:00 | hand-repaired, seven minutes after release | `5920f41` |
| 20260803 22:21 | **item closed**, crediting `_merge_into_section` | `5bef91f`, into `plans/open-corrections.md` |
| 20260823 04:13 | **0.28.3 ships the identical defect** | `2f633a8` |

The closing row reads: *"Fixed with a test (`tests/test_fragments.py`). `_merge_into_section` reuses
an existing `### Category` heading, bounded to the anchor's own section…"* — true of that function,
and irrelevant to the defect, because **the row conflates two mechanisms**:

    what _merge_into_section fixes   the section's *prose* already carries the heading
    what actually kept happening     a *fragment body* opens with its own `### Fixed`,
                                     which `render` then wraps in a second one

Both recurrences are the second mechanism, and it is checkable in one command:

    $ git show 68ca96b^:changelog.d/fixed-two-frozen-yaml-behaviours.md | head -1
    ### Fixed
    $ git show 2f633a8^:changelog.d/20260823_0233-fixed-published-versions-row-…md | head -1
    ### Fixed

### Three instruments that reported the previous truth, in one exchange

The same afternoon produced three more, all of the same shape — **an instrument reporting the
previous truth is indistinguishable from one reporting the current truth, unless you know which it
is.** None of the three is exotic; all three are the everyday tool used the everyday way.

| Instrument | What it actually answers | How it misled |
|---|---|---|
| `git fetch` then reading `origin/main` | *what did I last hear from the remote* | Reported a peer's landing as absent. `origin/main` is a **local cache**; only `git ls-remote origin refs/heads/main` asks the remote |
| `git log -S <string> -- <path>` | *history of this path, stopping at renames* | Returned only the rename commit for a plan file, dating a closure `20260804` instead of `20260803`. **In a repo that renamed every plan to `YYYYMMDD_HHMM-` retrospectively, every `-S` in `plans/` inherits this**; `--follow` or the pre-rename path is the answer |
| `awk '…{print NR}' fileA fileB` | *cumulative record number across all files* | Reported residues in `docs/RETROSPECTIVES.md` at lines `9718`/`9748` — the real lines plus `CHANGELOG.md`'s 3957. `FNR` is the per-file number, and a line number carrying another file's length in it looks exactly like a line number |

The third was **mine**, in a message asserting a peer's work had not landed. Both halves of that
message were wrong, from two different instruments, in the same sentence — and the report read as
confident because each number was real. **A wrong number that was measured is more persuasive than
a guess, which is what makes this class expensive.**

The cheap defence is the same in all three: **name what the instrument reads before trusting what
it says.** A cache is not a remote, a path is not a file's history, and `NR` is not a line number.

### The lesson, which is about closing notes rather than about splicing

**A wrong closing note is worse than an open item.** An open item is a standing invitation to look;
a closed one with a plausible mechanism beside it is a *reason not to*. It spends the evidence — the
instance, the diagnosis, the commit that would have shown the dates — and buys nothing, and the next
occurrence has to be rediscovered from scratch. This one was: 0.28.3's duplicate was found by
reading a release precedent, not by any gate and not by the note.

**The check that would have caught it costs one command.** Every closing note names a mechanism; a
mechanism has a commit; a commit has a date. *Is the fix older than the defect it claims to fix?*
`git log -S` answers it in seconds, and here it would have returned a date three days on the wrong
side. **A fix that predates its defect is not a fix — it is a coincidence with a plausible name.**

The generalisation, and it is the third instance of one shape in a single afternoon: **a green
signal is only evidence about the thing it actually measures.** A closing note measures whether
somebody was satisfied, not whether the defect is gone. A passing true-positive test measures the
case it constructs, not what the checker fails to look at. And a test asserting *that* something was
refused stops pinning *why* the moment a second guard can refuse it too — all three were found here,
and all three had been green for weeks.
