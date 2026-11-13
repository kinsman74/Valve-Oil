export interface RfidScan {
  scan_id?: string;
  accepted_id?: string | null;
  outcome?: string;
}

export interface RfidSample {
  printer: string;
  box_online: unknown;
  box_inserted: unknown;
  saved_id: unknown;
  last_scan?: RfidScan;
}

export interface RfidVerification {
  identity: unknown;
  inserted: boolean;
  scanId: string | null;
  awaitingScan: boolean;
  unverified: boolean;
}
export function updateVerification (previous: RfidVerification | undefined, sample: RfidSample): RfidVerification {
  const scan = sample.last_scan
  const scanId = scan?.scan_id ?? null
  const identity = sample.saved_id
  const inserted = sample.box_inserted === 1
  const fresh = Boolean(previous && scanId && scanId !== previous.scanId)

  const failed = /^(timeout(?:-|$)|conflicting-tags$)/.test(scan?.outcome ?? '')

  if (sample.printer !== 'ready' || sample.box_online !== 1 || !inserted) {
    return { identity, inserted, scanId, awaitingScan: false, unverified: false }
  }

  if (!previous) {
    const unverified = Boolean(scanId && failed && typeof identity === 'string' && identity)
    return { identity, inserted, scanId, awaitingScan: false, unverified }
  }

  const changed = identity !== previous.identity
  const awaitingScan = !changed && (!previous.inserted || previous.awaitingScan)
  const accepted = fresh && scan.accepted_id != null && scan.accepted_id === identity
  const unverified = !changed && !accepted &&
    (previous.unverified || (awaitingScan && fresh && failed))

  return { identity, inserted, scanId, awaitingScan: awaitingScan && !accepted, unverified }
}
