'use strict'
const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const vm = require('node:vm')
const { execFileSync } = require('node:child_process')
const { stripTypeScriptTypes } = require('node:module')

const source = process.argv[2]
assert.ok(source, 'Pass the pinned Valve Oil Fluidd checkout')
const expected = '0e6d94db9a60d17454b0508b9e8eac976ba75171'
assert.equal(execFileSync('git', ['-C', source, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(), expected)
const read = file => fs.readFileSync(path.join(source, file), 'utf8')
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, 'q2-box-fixture.json'), 'utf8'))
const utilityPath = 'src/util/qidi-box.ts'
execFileSync('git', ['-C', source, 'diff', '--quiet', 'HEAD', '--', utilityPath,
  'src/store/printer/mutations.ts', 'src/components/widgets/qidiBox/QidiBoxFilamentDialog.vue'])

function evaluate (code, exports, stubs = {}) {
  const sandbox = { ...stubs, result: null }
  const stripped = stripTypeScriptTypes(code
    .replace(/^import .*$/gm, '')
    .replace(/^export /gm, ''), { mode: 'transform' })
  vm.runInNewContext(stripped + '\nresult = {' + exports.join(',') + '}', sandbox, { timeout: 1000 })
  return sandbox.result
}

const utilities = ['qidiBoxSlots', 'parseQidiFilamentDatabase']
const upstream = evaluate(read(utilityPath), utilities)
const originalSlot = upstream.qidiBoxSlots(fixture.baseline, null)[1]
assert.equal(originalSlot.filamentId, 'QFZ07')
assert.equal(originalSlot.name, null, 'Unmodified Fluidd should reproduce the flat-status gap')
assert.equal(originalSlot.type, null)

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'q2-fluidd-replay-'))
let candidate
try {
  const file = path.join(tmp, utilityPath)
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, read(utilityPath))
  execFileSync('git', ['apply', '--unidiff-zero', path.join(__dirname, 'flat-controller.patch')], { cwd: tmp })
  candidate = evaluate(fs.readFileSync(file, 'utf8'), utilities)
} finally {
  fs.rmSync(tmp, { recursive: true, force: true })
}

const state = { printer: structuredClone(fixture.baseline) }
const { mutations } = evaluate(read('src/store/printer/mutations.ts'), ['mutations'], {
  Vue: { set: (obj, key, value) => { obj[key] = value } },
  isPlainObject: value => Object.prototype.toString.call(value) === '[object Object]'
})
const slots = () => candidate.qidiBoxSlots(state.printer, null)
const update = payload => mutations.setSocketNotify(state, { key: 'multi_color_controller', payload })
const slot = slots()[1]
assert.equal(slot.name, 'PETG Basic Black')
assert.equal(slot.type, 'PETG')
assert.equal(slot.vendor, 'Soleyin')
assert.equal(slot.color, '#060606')

update(fixture.before_replacement)
update(fixture.scan_start)
assert.equal(slots()[0].reading, true)
assert.equal(slots()[1].filamentId, 'QFZ07', 'Partial update must preserve the other slot')
update(fixture.scan_timeout)
assert.equal(slots()[0].reading, false)
assert.equal(slots()[0].filamentId, 'QFY82', 'Timeout reproduces stale identity from upstream status')
update(fixture.rescan_accepted)
assert.equal(slots()[0].filamentId, 'QFY10')
assert.equal(slots()[0].vendor, 'Anycubic')
assert.equal(slots()[1].name, 'PETG Basic Black')

const withResolved = structuredClone(fixture.baseline)
withResolved.box_extras = { boxes: [{ filament_info: [{
  index: 1, filament_id: 'QFZ08', filament_str: 'PETG Basic White', filament_type: 'PETG'
}] }] }
assert.equal(candidate.qidiBoxSlots(withResolved, null)[1].filamentId, 'QFZ08', 'Keep native resolved-array precedence')
const legacy = { save_variables: { variables: { box_count: 1, filament_slot0: 7 } } }
assert.equal(candidate.qidiBoxSlots(legacy, { fila7: { filament: 'PLA Basic', type: 'PLA' } })[0].type, 'PLA')

const vue = read('src/components/widgets/qidiBox/QidiBoxFilamentDialog.vue')
const match = vue.match(/^  handleSave \(\) \{\n[\s\S]*?^  \}/m)
assert.ok(match, 'Could not locate the pinned Fluidd save handler')
const { dialog } = evaluate('const dialog = {\n' + match[0] + '\n}', ['dialog'])
const sent = []
const database = candidate.parseQidiFilamentDatabase(fixture.catalog)
assert.equal(database.find(f => f.id === 'QFZ08').name, 'Soleyin PETG Basic White')
const receiver = {
  boxSlot: slot,
  draft: { filament: 'QFZ08', color: '#FAFAFA', vendor: 'Soleyin' },
  database,
  busy: false,
  open: true,
  sendGcode: text => sent.push(text)
}
dialog.handleSave.call(receiver)
assert.deepEqual(sent, [
  'SAVE_VARIABLE VARIABLE=filament_slot1 VALUE=\'"QFZ08"\'\n' +
  'SAVE_VARIABLE VARIABLE=color_slot1 VALUE="[\'FAFAFA\']"'
])
assert.equal(receiver.open, false)
receiver.busy = true
dialog.handleSave.call(receiver)
assert.equal(sent.length, 1)
console.log('Passed: reproduced upstream display gap, Q2 slot identity, partial merge, timeout and recovery, native/legacy precedence, dry-run edit, busy guard')
