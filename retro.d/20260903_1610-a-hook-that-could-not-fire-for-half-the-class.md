## A hook that could not fire for half the class (20260903 16:10)

**What happened.** The decided fix for row 31 was *ask the filesystem instead of inferring*: replace
a silent `root.glob(pattern)` with a walk carrying an `os.walk` error hook, collect the directories
it could not read, and hold the documents under them. The decision named two fixtures — an
unreadable root and an unreadable subdirectory — and both were measured on both interpreters before
it was taken. It was still insufficient, and the gap was not in the reasoning.

**The measurement that found it.** Before writing anything I enumerated the *modes*, not the cases:
`0o000`, `0o100`, `0o400`, `0o500` on a subdirectory, asking each of `root.glob("**/*.md")`,
`os.walk(onerror=…)` and `os.path.isfile` what it said. Four rows, one script. The `0o400` row is
the one nobody had:

| mode | glob yields | `onerror` fires | `os.path.isfile` |
|---|---|---|---|
| `0o000` | nothing | yes | `False` |
| `0o100` | nothing | yes | `True` |
| `0o400` | **the entry** | **no** | `False` |
| `0o500` | the entry | no | `True` |

At `0o400` the directory **lists and cannot be entered**. `scandir` succeeds, so no error is raised
for any hook to receive; the glob hands back the name; and every `stat` on that name then fails one
at a time. So the decided mechanism — an error hook — is structurally blind to it, and the walk was
still deleting the documents underneath at exit 0. On Python 3.13 it did not even do that quietly:
`Path.is_symlink()` `lstat`s, `lstat` needs `+x` on the **parent**, and the next line raised.

**Why the decision could not have found it.** Both named fixtures make the directory *unlistable*,
and unlistable is the only state that fires a hook. A decision reasoned from two instances of one
state will specify an instrument that covers exactly that state, and the specification then reads as
complete because every fixture in it passes. The gap is invisible from inside the case list; it is
only visible from the axis the cases are points on.

**The generalisable move.** When a fix is specified in terms of *an instrument* — a hook, a probe, a
callback — enumerate the states of the thing being instrumented and ask the instrument about each
one, before writing the fix. Not more fixtures of the same shape: the **axis**. Here the axis was
four permission bits and cost one script; the two cases in the decision were both the same point on
it. The question that finds this is *"what can this instrument not see?"*, and it has to be asked
while the instrument is still a choice.

**What it changed in the build.** The fix is two halves rather than one, and they are not
alternatives: `paths.unreadable_directories` collects what the hook can see, and `paths.unreachable`
catches the rest one candidate at a time, with the walk recording that candidate's **parent** —
always the culprit, because a glob cannot descend past an untraversable directory, so every entry it
still yields from one is a direct child. A test pins the limit itself
(`test_unreadable_directories_cannot_see_a_directory_that_lists_but_cannot_be_entered`), because the
per-candidate half looks redundant beside the collector and the next reader will delete it
otherwise. **A stated limit needs a test as much as a behaviour does** — it is the only thing that
turns red when someone acts on the belief that one half is enough.

**A postscript, because it is the same lesson pointed at the test harness.** The mutation battery
for this work reads **57 of 57 killed on 3.13, and 56 of 57 on 3.14** — one survivor, the row that
reverts `doctor`'s directory guard to the `pathlib` spelling. That row is not a gap. `Path.is_dir()`
raises on 3.13 and returns `False` on 3.14, so on the newer interpreter the mutant merely skips the
root and the test's assertions still hold. **The row's own comment said so before the run**, which
is the only reason the survivor is readable as a prediction rather than as a hole; written
afterwards it would be indistinguishable from an excuse. An instrument that cannot see a case has
to say so in advance — which is exactly what the `0o400` row above is about, one layer down.
