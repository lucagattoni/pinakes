- **`pnk link` no longer blames your path for a permission problem.** A document this process
  cannot reach — one inside a directory it may not traverse, or a symlink pointing into one — was
  reported as `'docs/x.md' is not a document in this KB`, whose remedy sends you to re-check a path
  that is spelled correctly; a sidecar in the same state was reported as `has no sidecar`, whose
  remedy sends you to run `pnk sync`, which cannot help either. Both now say `cannot be read:
  Permission denied` and point at the directory's permissions. Only the message moves — both paths
  already exited non-zero. The refusal was reported correctly on Python 3.13 and wrongly on 3.14,
  so which answer you got depended on your interpreter.
