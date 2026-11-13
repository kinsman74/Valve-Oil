// Offline candidate. Consume consecutive samples from capture-slot.py.
function updateVerification(previous, sample) {
  const scan = sample.last_scan
  const fingerprint = scan && JSON.stringify([
    scan.outcome, scan.empty, scan.malformed, scan.failed, scan.valid, scan.conflict
  ])
  const identity = sample.saved_id
  const inserted = sample.box_inserted === 1

  if (!previous || sample.printer !== 'ready' || sample.box_online !== 1) {
    return { identity, inserted, fingerprint, awaitingScan: false, unverified: false }
  }

  const changed = identity !== previous.identity
  const awaitingScan = inserted && !changed && (!previous.inserted || previous.awaitingScan)
  const fresh = fingerprint && fingerprint !== previous.fingerprint
  const failed = /^(timeout(?:-|$)|conflicting-tags$)/.test(scan?.outcome ?? '')
  const unverified = inserted && !changed &&
    (previous.unverified || Boolean(awaitingScan && fresh && failed))

  return { identity, inserted, fingerprint, awaitingScan, unverified }
}
module.exports = { updateVerification }
