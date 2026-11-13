// Consume consecutive samples from capture-slot.py with read guard v2.
function updateVerification(previous, sample) {
  const scan = sample.last_scan
  const scanId = scan?.scan_id ?? null
  const identity = sample.saved_id
  const inserted = sample.box_inserted === 1
  const fresh = Boolean(previous && scanId && scanId !== previous.scanId)

  if (!previous || sample.printer !== 'ready' || sample.box_online !== 1 || !inserted) {
    return { identity, inserted, scanId, awaitingScan: false, unverified: false }
  }

  const changed = identity !== previous.identity
  const awaitingScan = !changed && (!previous.inserted || previous.awaitingScan)
  const failed = /^(timeout(?:-|$)|conflicting-tags$)/.test(scan?.outcome ?? '')
  const accepted = fresh && scan.accepted_id != null && scan.accepted_id === identity
  const unverified = !changed && !accepted &&
    (previous.unverified || (awaitingScan && fresh && failed))

  return { identity, inserted, scanId, awaitingScan: awaitingScan && !accepted, unverified }
}
module.exports = { updateVerification }
