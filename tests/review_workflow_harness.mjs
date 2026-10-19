// Runs .claude/workflows/adversarial-review.js with stub hooks, for tests/test_review_workflow.py.
//
//   node review_workflow_harness.mjs run      < scenario.json   the whole script, stubbed agents
//   node review_workflow_harness.mjs fuzz     < {seed, n}       n random scenarios, invariants checked
//   node review_workflow_harness.mjs classify < input.json      the marked classify() alone
//   node review_workflow_harness.mjs meta                       the `export const meta` literal
//   node review_workflow_harness.mjs purity   < text            is that text a plain literal?
//
// The script is read from disk on every call, so a mutation battery that edits the file is seen.
// (Tests that read the script's text directly see it too, because the battery edits the real file;
// REVIEW_WORKFLOW_PATH, which points this harness at a copy, does not reach them.)
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

async function execute({ args, replies, delays = {} }) {
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
    return { ok: true, result, calls, missing, logs, phases }
  } catch (error) {
    return { ok: false, error: String(error && error.message || error), calls, missing, logs, phases }
  }
}

async function run() {
  process.stdout.write(JSON.stringify(await execute(stdin())))
}

// --- fuzz --------------------------------------------------------------------------------------
// Random replies, valid and malformed, thrown at the whole script; the invariants below must hold
// whatever came back. They are structural, not a second implementation of the verdict: the oracle
// is "a pass that says CLEAN or FINDINGS has no gap anywhere, and nothing raised goes missing".

function prng(seed) {
  let a = seed | 0
  return () => {
    a = a + 0x6D2B79F5 | 0
    let t = Math.imul(a ^ a >>> 15, 1 | a)
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t
    return ((t ^ t >>> 14) >>> 0) / 4294967296
  }
}

const KEYS = ['runtime', 'missing-set', 'population', 'docs-vs-tree']

function scenario(rand, bad) {
  const pick = list => list[Math.floor(rand() * list.length)]
  const broken = () => rand() < bad
  const finding = (ok = true) => ok
    ? { claim: 'a claim ' + Math.floor(rand() * 99), severity: pick(['high', 'medium', 'low']), file: 'src/x.py', evidence: 'ran it', ...(rand() < 0.4 ? { line: 1 + Math.floor(rand() * 90) } : {}) }
    : pick([{ severity: 'high', file: 'a', evidence: 'e' }, { claim: ' ', severity: 'low', file: 'a', evidence: 'e' }, { claim: 'c', severity: 'critical', file: 'a', evidence: 'e' }, { claim: 'c', severity: 'low', file: 'a', evidence: '' }, { claim: 'c', severity: 'low', file: 'a', evidence: 'e', line: 1.5 }])
  const lens = () => {
    const valid = { diff_files: pick([1, 2, 3, 40]), checks_run: ['rg -n x src'], not_run: rand() < 0.04 ? [pick(['no uv', ' '])] : [], findings: Array.from({ length: pick([0, 0, 0, 0, 1, 1, 2, 3, 3, 21]) }, () => finding()) }
    if (!broken()) return valid
    return pick(['__dead__', '__throw__', {}, 'text', [], { ...valid, checks_run: pick([[], [' '], ['none'], ['n/a'], ['ls '], [null]]) }, { ...valid, findings: pick([null, 'none', {}]) }, { ...valid, not_run: pick([{}, [4], null]) }, { ...valid, diff_files: pick([0, -1, '3', null]) }, { ...valid, findings: [finding(), finding(false)] }])
  }
  const verdict = () => {
    const valid = { refuted: rand() < 0.5, basis: pick(['checked', 'uncertain']), commands_run: ['ls -la docs'], observed: 'saw it' }
    if (!broken()) return valid
    return pick(['__dead__', '__throw__', {}, 'refuted', { ...valid, refuted: pick(['false', null, 1]) }, { ...valid, basis: pick([undefined, 'hunch']) }, { ...valid, commands_run: pick([[], [''], ['n/a'], 'ls docs']) }, { ...valid, observed: pick([null, '  ', 4]) }])
  }
  const ruling = id => {
    const valid = { id, real: rand() < 0.5, severity: pick(['high', 'medium', 'low']), rationale: 'because' }
    if (!broken()) return rand() < 0.1 ? { ...valid, id: '[' + valid.id + ']' } : valid
    return pick([{ ...valid, real: pick([undefined, null, 'false', 0]) }, { ...valid, severity: 'critical' }, { ...valid, rationale: pick([null, '  ', undefined]) }, { ...valid, id: pick([undefined, 7, '', 'invented-9']) }, null, 5, 'x', [], { id: valid.id }, { ...valid, real: !valid.real }])
  }
  // The replies are generated first so that the judge's rulings can name the findings that will
  // really survive: a judge that only ever names strangers would make every scenario PARTIAL and
  // leave the CLEAN and FINDINGS side of the invariants unexercised.
  const replies = {}
  const survivors = []
  for (const key of KEYS) {
    const reply = lens()
    replies['lens:' + key] = reply
    for (let i = 1; i <= 25; i++) {
      const v = verdict()
      replies['refute:' + key + '-' + i] = v
      const usable = reply && typeof reply === 'object' && Array.isArray(reply.findings) && i <= reply.findings.length
      if (usable && v && v.refuted === false) survivors.push(key + '-' + i)
    }
  }
  const noise = () => ruling(pick(['invented-9', 'runtime-1', 'population-2']))
  replies.judge = broken()
    ? pick(['__dead__', '__throw__', {}, { rulings: null }, { rulings: 5 }, { rulings: 'no' }, { rulings: [null, 5, 'x', { id: 'runtime-1' }] }])
    : { rulings: survivors.map(ruling).concat(rand() < 0.2 ? [noise()] : []).concat(rand() < 0.1 && survivors.length ? [ruling(survivors[0])] : []) }
  return { args: { sha: 'abc1234', base: 'def5678' }, replies }
}

function violations(out) {
  if (!out.ok) return ['the script threw: ' + out.error]
  const r = out.result
  const found = []
  // Every reply was scripted, so a missing label is a harness bug and would read as a dead agent.
  if (out.missing.length) found.push('no scripted reply for ' + out.missing.join(', '))
  const ids = [r.confirmed, r.refuted, r.not_real, r.unrefuted, r.unjudged].flat().map(f => f.id)
  if (new Set(ids).size !== ids.length) found.push('an id is on more than one list: ' + ids.join(','))
  if (ids.length !== r.raised) found.push('the lists hold ' + ids.length + ' findings but raised is ' + r.raised)
  const gaps = r.lenses.died.length + Object.keys(r.not_run).length + r.unrefuted.length + r.unjudged.length + r.unchecked_high.length + r.contested_rulings.length
  const said = r.coverage
  if ((said === 'CLEAN' || said === 'FINDINGS') && gaps) found.push(said + ' with ' + gaps + ' gap(s): died=' + r.lenses.died + ' not_run=' + Object.keys(r.not_run) + ' unrefuted=' + r.unrefuted.length + ' unjudged=' + r.unjudged.length + ' unchecked_high=' + r.unchecked_high)
  if (said === 'VACUOUS' && r.lenses.returned.length) found.push('VACUOUS while ' + r.lenses.returned + ' returned')
  if (!r.lenses.returned.length && said !== 'VACUOUS') found.push(said + ' while no lens returned')
  if (said === 'CLEAN' && r.confirmed.length) found.push('CLEAN with confirmed findings')
  if (said === 'FINDINGS' && !r.confirmed.length) found.push('FINDINGS with none confirmed')
  if (r.lenses.died.length + r.lenses.returned.length !== KEYS.length) found.push('lenses died + returned is not 4')
  for (const key of r.lenses.died) if (!r.lenses.died_why[key]) found.push('lens ' + key + ' died with no reason')
  return found
}

async function fuzz() {
  const { seed, n } = stdin()
  const rand = prng(seed)
  const coverages = {}
  const bad = []
  for (let i = 0; i < n; i++) {
    const out = await execute(scenario(rand, [0, 0.03, 0.15, 0.7][i % 4]))
    const found = violations(out)
    const said = out.ok ? out.result.coverage : 'THREW'
    coverages[said] = (coverages[said] ?? 0) + 1
    if (found.length && bad.length < 5) bad.push({ i, found })
  }
  process.stdout.write(JSON.stringify({ scenarios: n, coverages, violations: bad }))
}

// --- the rest ----------------------------------------------------------------------------------

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
else if (mode === 'fuzz') await fuzz()
else if (mode === 'classify') classify()
else if (mode === 'meta') meta()
else if (mode === 'purity') process.stdout.write(JSON.stringify({ problems: purityProblems(stdinText()) }))
else { process.stderr.write('usage: harness.mjs run|fuzz|classify|meta|purity\n'); process.exit(2) }
