## The restore command is the one that eats the work (20260902 08:53)

I proved a change by running the thing it changes: splice both fragment streams, build the site,
read the anchors out of the built HTML. Then I ran `git checkout -- .` to put the consumed fragments
back, and **destroyed my own uncommitted increment** — the gate, its nine tests, and four link
restorations. `git status` came back empty and that was the whole report.

The rule is already written, in the mutation section: *"`git checkout <file>` restores to the last
commit, not to the pre-mutation state, and silently reverts uncommitted fixes."* I had read it. What
it did not stop is the reason it did not stop me: **the operation felt like a read.** Splicing and
building are a measurement, and the command that undoes a measurement does not present itself as a
write. A peer did the identical thing four hours earlier on the same night, lost a fragment, and
rewrote it. Two agents, one command, both having read the rule — that is a defect in the remedy
rather than in either of us. The remedy that would have worked is one word longer: **commit before
the measurement, not before the mutation**, because a splice is a mutation whatever it feels like.

Recovery cost about ten minutes, and only because I had copied `retro.d/` and the gate to scratch
first — for reasons unrelated to this, and not the test file, which I rewrote. Everything was then
re-verified from the restored tree rather than from the earlier run's output, since the earlier run
had measured a tree that no longer existed.

**A second instrument failure the same hour, and it is the sharper one.** A peer and I each counted
the live `](#…)` links in `docs/RETROSPECTIVES.md`. We both got **2**. The population is **3**.
Their pattern, `\]\(#[a-z0-9][a-z0-9-]*\)`, misses `#measure_sync_cpupy-…` because of the
underscore. The pattern I attributed to them — a grep quoted inside another fragment — misses
`#design-review-passes-17-pre-implementation` because it requires a `-YYYYMMDD-HHMM` suffix. **Two
selectors, two unrelated blind spots, one agreeing wrong answer.** Agreement between instruments is
worth nothing until the instruments are shown to be independent, and these looked independent
precisely because neither of us had written the other's regex down. Earlier the same night the same
pair of us computed the same wrong anchor by the same wrong method and read that as corroboration
too; this is the harder version, because here the methods really were different.

**And a third, which is the one that generalises.** A peer measured a line at 254 characters and
dismissed two neighbouring lines as *"2 characters over, not worth a commit"*. The line was 252
characters and 254 **bytes** — `awk length` counts bytes in this locale — and the two neighbours
were 99 and 100, never over at all. The headline survived the error: at 252 or 254 that line was
two and a half times the file's width and had to be fixed either way. **That is exactly why the
error was safe to keep.** A measurement can be wrong in a direction that does not touch the
conclusion and still poison every judgement made beside it, and those judgements are the ones nobody
re-checks, because the headline held. The number the conclusion rests on gets scrutinised; the
numbers riding along beside it do not.

**The find worth keeping came from reviewing the change after it was green.** A stream `README.md`
is excluded from the fragment set — its own links resolve where it sits — and it must *also* be
excluded from the anchor universe, because its headings never reach the spliced document. Two
exclusions, two functions, and only the first had a test. Without the second a fragment could link
`#how-to-write-a-fragment`, pass on the branch, and die at the release cut: the exact failure the
new gate exists to remove, produced by the gate. Nothing about it was visible in the diff, and the
suite was green when I went looking.
