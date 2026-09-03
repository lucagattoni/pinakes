## A commit taken inside a mutation window shipped the mutant (20260903 08:30)

`7193983` on the S4 branch has the subject *"Retro: the review harness reported a clean pass while
nobody had looked"*. It changed a retro fragment — and `src/pinakes/template.py`, by one line:

    -        elif character != "\t" and (character < " " or character == "\x7f"):
    +        elif False:

That is battery row *a control character is left raw*, live on disk, committed and **pushed**. Every
control character in a KB name would have gone raw into a TOML basic string, which is the S4 defect
this branch exists to delete, on the branch that deletes it.

### The window is seven seconds wide and it is nobody's fault in particular

    7193983 committed        20260903 02:46:58
    template.py mtime        20260903 02:47:05     <- tools/mutate.py restoring, 7s later

The commit ran *inside* a mutation run. `tools/mutate.py` writes a mutant, runs the named test,
restores the file; `git add` called anywhere in that interval stages the mutant, and the restore
afterwards leaves the tree clean, so there is nothing left over to notice.

CLAUDE.md already says **commit before mutating** — because `git checkout <file>` restores to the
last commit and silently reverts uncommitted fixes. That rule was followed here: the target was
committed before the battery ran. The failure is its unwritten half, in the other direction:

**While a battery is running, that worktree has no committable state.** Not for the files the
battery names, and in practice not at all, because `git add -A` does not know which those are.

### What did not catch it, and what would have

| | |
|---|---|
| `./check.sh` | started, **killed at ten minutes by machine load** (four review agents), deferred to landing time with a note saying so. The note was honest and the gate still did not run |
| the battery itself | ran and reported **9/9 killed** — correctly. A battery mutates a *committed* target and restores it. It has no opinion about what else was committed while it worked |
| `--check-anchors` | green. The anchor was present; it was the arm that was gone |
| reading the commit | `src/pinakes/template.py \| 2 +-` sat in the stat output under a subject that promised a fragment. **Nothing but a human reads that line** |

The cheap durable guard is the last row: **a commit's stat is read before the commit is made**, and
a `src/` path under a `Retro:` or `Docs:` subject is a stop. The expensive one is the first: a gate
deferred because the machine is loaded is a gate that did not run, and the branch was pushed in
between.

### The generalisation, because this is the second instance of it this increment

The [earlier fragment](#a-mutant-killed-for-the-wrong-reason-is-a-survivor-wearing-a-green-light-20260902-1159)
in this branch is about a mutant that died for a reason nobody read. This one is about a mutant that
was never in the report at all. Both are the same shape: **the mutation harness's output was
believed about a state nobody looked at.** 9/9 killed was true of the file `mutate.py` held. It said
nothing about the file `git` held, and the two were different for seven seconds.
