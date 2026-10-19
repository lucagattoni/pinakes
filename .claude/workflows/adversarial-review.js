export const meta = {
  name: 'adversarial-review',
  description: 'Adversarially review one pinned commit: slow lenses first, one refuter per finding, one judge, and a coverage verdict that says whether anyone looked',
  whenToUse: 'Step 5 of docs/BUILDING.md - a fresh review pass over an increment. Pass {sha, base} as args; read `coverage` before the findings.',
  phases: [
    { title: 'Lenses', detail: 'runtime lens first, then missing-set, then the text lenses' },
    { title: 'Refute', detail: 'one refuter per finding, started the moment its lens returns' },
    { title: 'Judge', detail: 'one Opus judge over the findings no refuter could kill' },
  ],
}

// A review pass that returns zero findings is a claim about the pass. The runtime hands back `null`
// for an agent that died, and the documented idiom for collecting a fan-out is `.filter(Boolean)` -
// which turns a dead agent into an absent finding. 17 of 19 agents died on a session limit once and
// the run returned {"raised":0,"confirmed":[],"refuted":[]}. So this script counts before it
// filters, returns `coverage` beside the findings, and lists what it could not check.
//
// Models are named on every call: Sonnet for lenses and refuters, Opus for the one judge.
//
// What cannot be tested by running it - the real fan-out - is exercised once by hand; everything
// else is tested by tests/test_review_workflow.py, which runs this very file with stub hooks.

const DISK_RULE = 'If a claim is about state on disk, look at the disk: ls, wc -c, cat or a command that reads it. A traceback, a commit message or a docstring is not the disk.'

const SCRATCH_RULE = 'Do not edit any file in the repository. Scratch work goes in a directory you create under the system temp directory, and anything you create (a detached worktree, a scratch KB) you remove before you finish.'

// Slow lenses first. The runtime lens builds a KB and runs a command, so it reports last and is the
// first thing a session limit cuts; started first, it is also the first to finish. The order here
// is the order of launch, and a test pins it.
const LENSES = [
  {
    key: 'runtime',
    frame: 'You test behaviour, not text. Check the pinned commit out into a detached scratch worktree, build a scratch KB, run the real command the diff changed, and read what it printed and what it left on disk. A finding is a command and its output.',
  },
  {
    key: 'missing-set',
    frame: 'For each promise the diff makes, name the set it is over, and ask whether every member of that set has an image. Find the domain the author never modelled: the inputs the fix, its tests and its mutants all fail to use. A set the author did not think of is invisible to every check the author wrote.',
  },
  {
    key: 'population',
    frame: 'Every ratio, count and percentage in the changed documents, comments, messages and fragments: name its population and its instrument, and recompute it. Every null result ("none found", "0 matches"): was the instrument shown able to fire, or could the selector never have matched?',
  },
  {
    key: 'docs-vs-tree',
    frame: 'Every claim a changed document, comment or fragment makes about the code or the tree - a path, a name, a count, a default, a command: check it against the tree at the pinned commit. Also look for what the change makes stale in files it did not touch.',
  },
]

const LENS_SCHEMA = {
  type: 'object',
  properties: {
    checks_run: { type: 'array', minItems: 1, items: { type: 'string' } },
    not_run: { type: 'array', items: { type: 'string' } },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string', minLength: 1 },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          file: { type: 'string' },
          line: { type: 'integer' },
          evidence: { type: 'string', minLength: 1 },
        },
        required: ['claim', 'severity', 'file', 'evidence'],
      },
    },
  },
  required: ['checks_run', 'not_run', 'findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    commands_run: { type: 'array', minItems: 1, items: { type: 'string' } },
    observed: { type: 'string', minLength: 1 },
  },
  required: ['refuted', 'commands_run', 'observed'],
}

const RULING_SCHEMA = {
  type: 'object',
  properties: {
    rulings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          real: { type: 'boolean' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          rationale: { type: 'string', minLength: 1 },
          commands_run: { type: 'array', items: { type: 'string' } },
        },
        required: ['id', 'real', 'severity', 'rationale'],
      },
    },
  },
  required: ['rulings'],
}

// <classify>
// Coverage is decided here and nowhere else, from counts alone. VACUOUS means nobody looked, which
// is a different outcome from CLEAN and not a smaller one; PARTIAL means someone looked at less
// than was asked for - a dead lens, an unrun probe, a finding no refuter checked, a survivor no
// judge ruled on; FINDINGS and CLEAN are only possible when every one of those is zero.
function classify(c) {
  for (const key of ['lensesExpected', 'lensesReturned', 'notRun', 'refutersExpected', 'refutersReturned', 'confirmed']) {
    if (!Number.isInteger(c[key]) || c[key] < 0) {
      throw new Error('classify: ' + key + ' must be a non-negative integer, got ' + JSON.stringify(c[key]))
    }
  }
  if (c.lensesExpected < 1) throw new Error('classify: lensesExpected must be at least 1')
  if (c.lensesReturned > c.lensesExpected) throw new Error('classify: more lenses returned than expected')
  if (c.refutersReturned > c.refutersExpected) throw new Error('classify: more refuters returned than expected')
  if (typeof c.judgeNeeded !== 'boolean' || typeof c.judgeReturned !== 'boolean') {
    throw new Error('classify: judgeNeeded and judgeReturned must be booleans')
  }
  if (c.lensesReturned === 0) return 'VACUOUS'
  if (c.lensesReturned < c.lensesExpected) return 'PARTIAL'
  if (c.notRun > 0) return 'PARTIAL'
  if (c.refutersReturned < c.refutersExpected) return 'PARTIAL'
  if (c.judgeNeeded && !c.judgeReturned) return 'PARTIAL'
  return c.confirmed > 0 ? 'FINDINGS' : 'CLEAN'
}
// </classify>

if (!args || typeof args !== 'object' || typeof args.sha !== 'string' || !/^[0-9a-f]{7,40}$/.test(args.sha)) {
  throw new Error('adversarial-review: args.sha is required, a commit sha of 7 to 40 hex digits. A review of a moving branch reviews a different tree than the one you named; the sha is what pins it.')
}
if (typeof args.base !== 'string' || args.base.length === 0) {
  throw new Error('adversarial-review: args.base is required, the ref the diff is taken against (usually origin/main).')
}
const claims = Array.isArray(args.claims) ? args.claims.map(String) : []
const target = 'The increment is the diff `git diff ' + args.base + '...' + args.sha + '`, pinned at commit ' + args.sha + '. Review that commit and nothing else: if the branch has moved, the pinned commit is still the subject.'
  + (typeof args.title === 'string' && args.title ? ' Title: ' + args.title + '.' : '')
  + (claims.length ? ' What the increment says it does:\n- ' + claims.join('\n- ') : '')

function lensPrompt(lens) {
  return [
    target,
    'Your lens: ' + lens.key + '. ' + lens.frame,
    DISK_RULE,
    SCRATCH_RULE,
    'Report every check you ran in checks_run. Report what you could NOT run, and why, in not_run - an unrun probe is not a clean probe, and an empty findings list from a lens that ran nothing is not a result. Each finding needs the file, a severity, and evidence: the command and what it printed.',
  ].join('\n\n')
}

function refutePrompt(finding) {
  return [
    target,
    'Another reviewer raised this finding (' + finding.id + ', ' + finding.severity + ', ' + finding.file + (finding.line ? ':' + finding.line : '') + '):\n' + finding.claim + '\nTheir evidence:\n' + finding.evidence,
    'Try to REFUTE it. Default to refuted=true if you are uncertain. You must perform a check - run a command that would show the finding wrong - and "I reasoned about it" is not a check. List the commands in commands_run and what they showed in observed.',
    DISK_RULE,
    SCRATCH_RULE,
  ].join('\n\n')
}

function judgePrompt(survivors) {
  const body = survivors.map(f => '[' + f.id + '] (' + f.severity + ') ' + f.file + (f.line ? ':' + f.line : '') + '\n' + f.claim + '\nEvidence: ' + f.evidence + '\nA refuter tried to kill it and could not: ' + f.refuter_observed).join('\n\n')
  return [
    target,
    'Each finding below survived a refuter. Rule on each by id: real or not real, and its severity as you rule it, not as it was raised. You may run commands, and where a finding is cheap to check you should.',
    DISK_RULE,
    SCRATCH_RULE,
    body,
  ].join('\n\n')
}

phase('Lenses')

// pipeline, not a barrier: a lens's refuters start the moment that lens returns. The stage returns a
// record even when the agent died, so the death is counted before anything is filtered.
const runs = await pipeline(
  LENSES,
  lens => agent(lensPrompt(lens), { label: 'lens:' + lens.key, phase: 'Lenses', schema: LENS_SCHEMA, model: 'sonnet' })
    .then(out => ({ lens: lens.key, out })),
  async (prev, lens) => {
    const out = prev && prev.out
    const ran = out && Array.isArray(out.checks_run) && out.checks_run.length > 0
    if (!ran) return { lens: lens.key, dead: true, notRun: [], raised: [], verdicts: [] }
    const raised = (out.findings || []).map((f, i) => ({ ...f, id: lens.key + '-' + (i + 1), lens: lens.key }))
    const verdicts = await parallel(raised.map(f => () =>
      agent(refutePrompt(f), { label: 'refute:' + f.id, phase: 'Refute', schema: VERDICT_SCHEMA, model: 'sonnet' })))
    return { lens: lens.key, dead: false, notRun: out.not_run || [], raised, verdicts }
  },
)

// Count before filtering. `runs[i]` is null when a stage threw, which is a dead lens like any other.
const lensRecords = LENSES.map((lens, i) => runs[i] || { lens: lens.key, dead: true, notRun: [], raised: [], verdicts: [] })
const lensesDied = lensRecords.filter(r => r.dead).map(r => r.lens)
const lensesReturned = lensRecords.filter(r => !r.dead).map(r => r.lens)

const raised = lensRecords.flatMap(r => r.raised)
const refuted = []
const unrefuted = []
const survivors = []
lensRecords.forEach(r => r.raised.forEach((f, i) => {
  const v = r.verdicts[i]
  const checked = v && Array.isArray(v.commands_run) && v.commands_run.length > 0
  if (!checked) unrefuted.push(f)
  else if (v.refuted) refuted.push({ id: f.id, claim: f.claim, observed: v.observed })
  else survivors.push({ ...f, refuter_observed: v.observed })
}))
const notRun = Object.fromEntries(lensRecords.filter(r => r.notRun.length).map(r => [r.lens, r.notRun]))
const notRunCount = lensRecords.reduce((n, r) => n + r.notRun.length, 0)

phase('Judge')
let rulings = null
if (survivors.length) {
  const judged = await agent(judgePrompt(survivors), { label: 'judge', phase: 'Judge', schema: RULING_SCHEMA, model: 'opus' })
  rulings = judged && Array.isArray(judged.rulings) ? judged.rulings : null
}
// One ruling per id: the first the judge gave. A repeated id with a different answer must not put a
// finding on both the confirmed and the not-real list.
const ruling = new Map()
for (const r of rulings || []) if (!ruling.has(r.id)) ruling.set(r.id, r)
const confirmed = survivors.filter(f => ruling.has(f.id) && ruling.get(f.id).real)
  .map(f => ({ ...f, severity_as_ruled: ruling.get(f.id).severity }))
const notReal = survivors.filter(f => ruling.has(f.id) && !ruling.get(f.id).real)
  .map(f => ({ id: f.id, claim: f.claim, rationale: ruling.get(f.id).rationale }))
const unjudged = survivors.filter(f => !ruling.has(f.id))

const coverage = classify({
  lensesExpected: LENSES.length,
  lensesReturned: lensesReturned.length,
  notRun: notRunCount,
  refutersExpected: raised.length,
  refutersReturned: raised.length - unrefuted.length,
  judgeNeeded: survivors.length > 0,
  judgeReturned: survivors.length === 0 || unjudged.length === 0,
  confirmed: confirmed.length,
})

const note = (coverage === 'CLEAN' || coverage === 'FINDINGS')
  ? 'Every lens, refuter and judge that was asked for returned.'
  : 'NOT a clean pass. Do not report this review as clean. ' + lensesDied.length + ' of ' + LENSES.length + ' lenses died, ' + notRunCount + ' probe(s) were not run, ' + unrefuted.length + ' finding(s) have no refuter and ' + unjudged.length + ' survivor(s) have no ruling. Relaunch with resumeFromRunId to retry the dead agents, or tell the user the gap.'
log('coverage ' + coverage + ': ' + lensesReturned.length + '/' + LENSES.length + ' lenses, ' + raised.length + ' raised, ' + refuted.length + ' refuted, ' + unrefuted.length + ' unrefuted, ' + confirmed.length + ' confirmed, ' + unjudged.length + ' unjudged')

return {
  coverage,
  pinned: { sha: args.sha, base: args.base },
  lenses: { expected: LENSES.map(l => l.key), returned: lensesReturned, died: lensesDied },
  not_run: notRun,
  raised: raised.length,
  confirmed,
  refuted,
  not_real: notReal,
  unrefuted,
  unjudged,
  note,
}
