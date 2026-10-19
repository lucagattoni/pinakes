// Runs .claude/workflows/adversarial-review.js with stub hooks, for tests/test_review_workflow.py.
//
//   node review_workflow_harness.mjs run      < scenario.json   the whole script, stubbed agents
//   node review_workflow_harness.mjs classify < input.json      the marked classify() alone
//   node review_workflow_harness.mjs meta                       the `export const meta` literal
//   node review_workflow_harness.mjs purity   < text            is that text a plain literal?
//
// The script is read from disk on every call, so a mutation battery that edits the file is seen.
// The stubs follow the documented runtime: agent() resolves to null for a dead agent; pipeline()
// starts every item at once and drops an item to null when one of its stages throws; parallel()
// resolves a thunk that throws to null. A scripted reply of "__dead__" is a null, "__throw__" is a
// throw, and "delays" holds milliseconds per label. Date.now(), Math.random(), a bare new Date(),
// process, fetch, setTimeout and require are unavailable to the script, as in the runtime.
//
// A label with no scripted reply throws, and because pipeline() and parallel() absorb throws that
// would read as a dead agent, every such label is also returned in `missing` so the caller can
// refuse a scenario that forgot one.
//
// Nothing here can run the real fan-out; that has not been done yet.

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import vm from 'node:vm'

const SCRIPT = process.env.REVIEW_WORKFLOW_PATH
  || fileURLToPath(new URL('../.claude/workflows/adversarial-review.js', import.meta.url))

const mode = process.argv[2]
const stdinText = () => readFileSync(0, 'utf8')
const stdin = () => JSON.parse(stdinText())
const source = readFileSync(SCRIPT, 'utf8')
const HEAD = /^export const meta = /m

function lookup(replies, label) {
  if (Object.hasOwn(replies, label)) return replies[label]
  const wildcard = String(label).split(':')[0] + ':*'
  if (Object.hasOwn(replies, wildcard)) return replies[wildcard]
  return undefined
}

const sleep = ms => new Promise(resolve => globalThis.setTimeout(resolve, ms))

async function run() {
  const { args, replies, delays = {} } = stdin()
  const calls = []
  const missing = []
  const logs = []
  const phases = []
  let clock = 0
  async function agent(prompt, opts = {}) {
    const call = { label: opts.label ?? null, model: opts.model ?? null, phase: opts.phase ?? null, schema: opts.schema ?? null, prompt, started: ++clock, finished: null }
    calls.push(call)
    const delay = lookup(delays, opts.label)
    if (delay) await sleep(delay)
    call.finished = ++clock
    const reply = lookup(replies, opts.label)
    if (reply === '__dead__') return null
    if (reply === '__throw__') throw new Error('stub agent threw')
    if (reply === undefined) { missing.push(opts.label ?? null); throw new Error('harness: no scripted reply for ' + opts.label) }
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
  // The runtime makes these throw so that a relaunch repeats the same agent() calls.
  const RealDate = Date
  function GuardedDate(...a) {
    if (a.length === 0) throw new Error('new Date() with no argument is not available in a workflow')
    return new RealDate(...a)
  }
  GuardedDate.now = () => { throw new Error('Date.now() is not available in a workflow') }
  GuardedDate.parse = RealDate.parse
  GuardedDate.UTC = RealDate.UTC
  const GuardedMath = Object.create(Math, { random: { value: () => { throw new Error('Math.random() is not available in a workflow') } } })
  if (!HEAD.test(source)) throw new Error('harness: the script no longer starts with `export const meta =`')
  const body = '"use strict";\n' + source.replace(HEAD, 'const meta = ')
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
  const fn = new AsyncFunction('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget', 'Date', 'Math', 'process', 'fetch', 'setTimeout', 'setInterval', 'require', body)
  try {
    const result = await fn(agent, parallel, pipeline, t => phases.push(t), m => logs.push(m), args, { total: null, spent: () => 0, remaining: () => Infinity }, GuardedDate, GuardedMath, undefined, undefined, undefined, undefined, undefined)
    process.stdout.write(JSON.stringify({ ok: true, result, calls, missing, logs, phases }))
  } catch (error) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(error && error.message || error), calls, missing, logs, phases }))
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

// What the loader accepts for `meta`: "a plain object literal ... if it contains anything other than
// literal values, such as a variable, a function call, or a spread, Claude Code drops /<name>".
// Evaluating the text in an empty context catches a free variable and nothing else - 'x'.toLowerCase(),
// a spread of a literal and a template interpolation all evaluate - so the text is scanned instead:
// strings, comments and numbers are removed, and what is left may contain only braces, brackets,
// commas, colons, the words true / false / null and object keys.
function purityProblems(text) {
  const problems = []
  let rest = ''
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (ch === '/' && text[i + 1] === '/') { while (i < text.length && text[i] !== '\n') i++; continue }
    if (ch === '/' && text[i + 1] === '*') { i = text.indexOf('*/', i + 2); if (i < 0) { problems.push('unterminated comment'); break } i++; continue }
    if (ch === "'" || ch === '"' || ch === '`') {
      let j = i + 1
      let interpolated = false
      for (; j < text.length && text[j] !== ch; j++) {
        if (text[j] === '\\') j++
        else if (ch === '`' && text[j] === '$' && text[j + 1] === '{') interpolated = true
      }
      if (interpolated) problems.push('a template literal interpolates')
      rest += '""'
      i = j
      continue
    }
    rest += ch
  }
  if (/\.\.\./.test(rest)) problems.push('a spread')
  if (/\(|\)/.test(rest)) problems.push('a call or a parenthesised expression')
  for (const match of rest.matchAll(/[A-Za-z_$][\w$]*/g)) {
    const after = rest.slice(match.index + match[0].length).trimStart()
    const before = rest.slice(0, match.index).trimEnd()
    const isKey = after.startsWith(':') && /[{,]$/.test(before)
    if (!isKey && !['true', 'false', 'null'].includes(match[0])) problems.push('the identifier ' + match[0] + ' is not a key or a literal')
  }
  return problems
}

function metaText() {
  if (source.search(HEAD) !== 0) throw new Error('harness: `export const meta` is not the first statement of the file')
  const start = source.indexOf('{', 'export const meta = '.length - 1)
  let depth = 0, inString = null, end = -1
  for (let i = start; i < source.length; i++) {
    const ch = source[i]
    if (inString) { if (ch === '\\') i++; else if (ch === inString) inString = null; continue }
    if (ch === "'" || ch === '"' || ch === '`') inString = ch
    else if (ch === '{') depth++
    else if (ch === '}' && --depth === 0) { end = i; break }
  }
  if (end < 0) throw new Error('harness: could not find the end of the meta literal')
  return source.slice(start, end + 1)
}

function meta() {
  const text = metaText()
  const problems = purityProblems(text)
  const value = problems.length ? null : vm.runInNewContext('(' + text + ')', Object.create(null))
  process.stdout.write(JSON.stringify({ meta: value && JSON.parse(JSON.stringify(value)), problems }))
}

if (mode === 'run') await run()
else if (mode === 'classify') classify()
else if (mode === 'meta') meta()
else if (mode === 'purity') process.stdout.write(JSON.stringify({ problems: purityProblems(stdinText()) }))
else { process.stderr.write('usage: harness.mjs run|classify|meta|purity\n'); process.exit(2) }
