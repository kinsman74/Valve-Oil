const assert = require('node:assert/strict')
const fs = require('node:fs')
const { updateVerification } = require('./rfid-verification.cjs')
const files = process.argv.slice(2)
assert.equal(files.length, 2, 'Pass the supported-swap and Soleyin insertion traces')
function replay(file) {
  const samples = fs.readFileSync(file, 'utf8').trim().split('\n').map(JSON.parse)
  let state
  return samples.map(sample => (state = updateVerification(state, sample)))
}
const timeout = replay(files[0])
assert.equal(timeout[0].unverified, false)
const failed = timeout.find(state => state.unverified)
assert.ok(failed, 'Flag the retained assignment while the inlet is occupied')
assert.equal(failed.identity, 'QFY14')
assert.equal(timeout.at(-1).unverified, false, 'Clear warning when the inlet becomes empty')
const success = replay(files[1])
assert.ok(success.every(state => !state.unverified))
assert.equal(success.at(-1).identity, 'QFZ07')
const last = failed
const recovered = updateVerification(last, {
  printer: 'ready', box_online: 1, box_inserted: 1, saved_id: 'QFZ07',
  last_scan: { outcome: 'stock-reader-completed', valid: 2 }
})
assert.equal(recovered.unverified, false)
assert.equal(updateVerification(undefined, {
  printer: 'ready', box_online: 1, box_inserted: 1, saved_id: 'QFY14',
  last_scan: { outcome: 'timeout' }
}).unverified, false, 'Opening the dashboard must not treat historical results as fresh')
console.log('Passed: captured timeout, captured success, recovery and historical result')
