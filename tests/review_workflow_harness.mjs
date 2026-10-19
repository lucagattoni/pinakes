// Runs .claude/workflows/adversarial-review.js with stub hooks, for tests/test_review_workflow.py.
//
//   node review_workflow_harness.mjs run      < scenario.json   the whole script, stubbed agents
//   node review_workflow_harness.mjs classify < input.json      the marked classify() alone
//   node review_workflow_harness.mjs meta                       the `export const meta` literal
//
// The script is read from disk on every call, so a mutation battery that edits the file is seen.
// The stubs follow the documented runtime: agent() resolves to null for a dead agent; pipeline()
// starts every item at once and drops an item to null when one of its stages throws; parallel()
// resolves a thunk that throws to null. A scripted reply of "__dead__" is a null, "__throw__" is a
// throw, and any label without a reply is an error - a test that forgot one fails loudly.
//
// Nothing here can run the real fan-out; that is exercised once by hand (plans/20261018_2354-...).

import { readFileSync } from 'node:fs'
import vm from 'node:vm'

const SCRIPT = process.env.REVIEW_WORKFLOW_PATH
  || new URL('../.claude/workflows/adversarial-review.js', import.meta.url).pathname

const mode = process.argv[2]
const stdin = () => JSON.parse(readFileSync(0, 'utf8'))
const source = readFileSync(SCRIPT, 'utf8')
const HEAD = /^export const meta = /m

function lookup(replies, label) {
  if (Object.hasOwn(replies, label)) return replies[label]
  const wildcard = String(label).split(':')[0] + ':*'
  if (Object.hasOwn(replies, wildcard)) return replies[wildcard]
  return undefined
}

async function run() {
  const { args, replies } = stdin()
  const calls = []
  const logs = []
  const phases = []
  async function agent(prompt, opts = {}) {
    calls.push({ label: opts.label ?? null, model: opts.model ?? null, phase: opts.phase ?? null, schema: Boolean(opts.schema), prompt })
    const reply = lookup(replies, opts.label)
    if (reply === '__dead__') return null
    if (reply === '__throw__') throw new Error('stub agent threw')
    if (reply === undefined) throw new Error('harness: no scripted reply for ' + opts.label)
    return structuredClone(reply)
  }
  async function parallel(thunks) {
    return Promise.all(thunks.map(async thunk => { try { return await thunk() } catch { return null } }))
  }
  async function pipeline(items, ...stages) {
    return Promise.all(items.map(async (item, i) => {
      try {
        let prev = item
        for (const stage of stages) prev = await stage(prev, item, i)
        return prev
      } catch { return null }
    }))
  }
  if (!HEAD.test(source)) throw new Error('harness: the script no longer starts with `export const meta =`')
  const body = source.replace(HEAD, 'const meta = ')
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
  const fn = new AsyncFunction('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget', body)
  try {
    const result = await fn(agent, parallel, pipeline, t => phases.push(t), m => logs.push(m), args, { total: null, spent: () => 0, remaining: () => Infinity })
    process.stdout.write(JSON.stringify({ ok: true, result, calls, logs, phases }))
  } catch (error) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(error && error.message || error), calls, logs, phases }))
  }
}

function classify() {
  const open = source.indexOf('// <classify>')
  const close = source.indexOf('// </classify>')
  if (open < 0 || close < open) throw new Error('harness: the <classify> markers are missing or out of order')
  const fn = new Function(source.slice(open, close) + '\nreturn classify')()
  try {
    process.stdout.write(JSON.stringify({ ok: true, value: fn(stdin()) }))
  } catch (error) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(error && error.message || error) }))
  }
}

function meta() {
  const at = source.search(HEAD)
  if (at !== 0) throw new Error('harness: `export const meta` is not the first statement of the file')
  const start = source.indexOf('{', HEAD.exec(source).index + 'export const meta = '.length - 1)
  let depth = 0, inString = null, end = -1
  for (let i = start; i < source.length; i++) {
    const ch = source[i]
    if (inString) { if (ch === '\\') i++; else if (ch === inString) inString = null; continue }
    if (ch === "'" || ch === '"' || ch === '`') inString = ch
    else if (ch === '{') depth++
    else if (ch === '}' && --depth === 0) { end = i; break }
  }
  if (end < 0) throw new Error('harness: could not find the end of the meta literal')
  // An empty context: a variable, a call or a spread inside the literal has nothing to resolve
  // against and throws, which is what "a pure literal" means to the loader.
  const value = vm.runInNewContext('(' + source.slice(start, end + 1) + ')', Object.create(null))
  process.stdout.write(JSON.stringify({ meta: JSON.parse(JSON.stringify(value)) }))
}

if (mode === 'run') await run()
else if (mode === 'classify') classify()
else if (mode === 'meta') meta()
else { process.stderr.write('usage: harness.mjs run|classify|meta\n'); process.exit(2) }
