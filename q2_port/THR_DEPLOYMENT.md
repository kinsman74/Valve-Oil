# Q2 toolhead recovery workflow

Version **2026.11.22-thr-preview1** is a separate coordinator, not a general
Valve Oil installer. It uses the exact stable 26.11.18.2 transfer/readback tools
from upstream commit aa42eaa3c48f155282f3bda43720199f7e657d99. No protocol,
packet retry, erase bounds, reset command, bootloader profile or image bytes
are modified. Source hashes are pinned in thr-source-lock.json.

The private tool package adapts only the manifest's target SOC and vendor-image
provenance to Q2 01.01.03.02. The complete expected adapted manifest is committed;
all other changes are rejected. It is deliberately **not** an upstream declaration
of Q2 support and is not included in the older preview2 archive.

## What was verified on this Q2

On November 22, 2026, while idle and with all heater targets zero:

- The calibration repair persisted: one readable SAVE_CONFIG block, existing
  saved X zv 46.0 Hz and Y mzv 43.4 Hz loaded, latest saved mesh retained.
- Actual application readback matched QIDI's stock 02.02.01.08 image:
  1d34b4b0142f2a2047f08c2fae59d827bcee0adbd1563b4bd1de311dff8b2d62.
- Actual bootloader matched Valve Oil's recoverable SECOND profile:
  31f8344db7b091df5429960bc9cd06065e2188c3b8092e43fb65eb3f2833723c.
- Non-erasing application reset/bootloader probe returned 0102. After application
  return, a second readback verified unchanged application and bootloader bytes.
- Physical stock and bootloader backups were copied to the Mac. The captured
  bootloader passed upstream transfer emulation. Binary backups remain private.

This verifies entry **through a working application**, not independent recovery
entry when the application is unreadable. No firmware was erased or programmed.

## Prepare and inspect offline

Use the pinned upstream checkout and previously vetted candidate:

```sh
python3 q2_port/thr_deploy.py prepare \
  --upstream /path/to/stable-26.11.18.2 \
  --candidate /path/to/q2-thr-valve-oil-fifo.bin \
  --package /path/to/new-private-thr-package
python3 q2_port/thr_deploy.py dry-run --package /path/to/new-private-thr-package
```

Prepare rejects modified upstream sources and unrecognized candidate bytes.
Dry-run only verifies files; it performs no network, serial, service or printer
operations. The package includes vendor-derived firmware; keep it private.

## Recovery admission before application erase

Valve Oil's [THR operations](https://github.com/thelegendtubaguy/Valve-Oil/blob/v26.11.18.2/firmware/FLASHING.md)
require independently verified board recovery entry before erasing. Its
recovery-to-stock mode handles bounded communication faults for this exact
bootloader. It does not establish recovery after power loss, a killed process,
or cold boot into a partial application. A stock backup and a successful
application reset probe do not replace that missing physical check.

The coordinator requires a private recovery-evidence JSON document with:

- model: Q2; soc: 01.01.03.02; bootloader_sha256: the captured hash above;
- independent_recovery_verified: true **only after actual verification**;
- method: the independent recovery method, not the application reset command;
- verification: the observed procedure/results proving it works on this board.

This is an operator evidence record, not automatic proof of physical access.
Do not fabricate it to bypass the remaining requirement. The staged example
has independent_recovery_verified=false, so apply refuses before service or UART
access. No new permission is needed merely to run dry-run; firmware execution
remains a separate explicitly confirmed operation.

## Application transaction after admission

Keep the printer attended and power stable. Save projects and leave it idle.
Use the established authorized system-service execution on this Q2; qidi is not
a sudoer. Stage the coordinator alongside its policy.py, host_deploy.py, plan.py,
thr-source-lock.json and thr-source-manifest.json dependencies. Once recovery
entry has actually been verified, invoke a fresh service unit with:

```sh
systemd-run --no-ask-password --wait --collect --unit=q2-thr-apply \
  /usr/bin/python3 -B /private/coordinator/thr_deploy.py apply \
  --package /private/thr-package \
  --recovery-evidence /private/verified-recovery.json --confirm-write
```

The coordinator:

1. Admits exact Q2 SOC, source hashes, candidate bytes and recovery evidence;
   rejects any pending transaction and obtains a maintenance lock.
2. Checks ready/idle state, every heater in Klipper's registry, Box tool-change,
   RFID job and unsaved calibration. Captures original service states.
3. Writes a durable .tltg_thr_firmware_pending.json record, stops only the serial
   owners/update timer, saves and admits fresh application/bootloader readback.
4. Skips programming if already patched. Otherwise records possible programming
   **before** invoking the unchanged upstream tool with --recover-to-stock,
   --reset, --confirm-write and the Q2-specific target manifest.
5. Accepts transfer codes 0, 4 (stock fallback) or 5 (end unconfirmed) only as
   provisional outcomes. Waits for application return and verifies full readback
   against the requested or fallback bytes and the unchanged bootloader.
6. Restores only previously active services; clears the pending record only
   after verified firmware, successful service restoration and ready/idle state.
   A verified stock fallback is reported as fallback, never as a successful fix.
7. For a verified patch, preserves existing calibration and records the old
   shaper frequencies in the upstream warning marker. It commands no movement,
   heater, homing, resonance sweep, leveling or print. Run new input-shaper
   calibration before bed leveling or printing after an actual flash.

The warning is informational and is not a print-interlock claim. The coordinator
does not alter the touchscreen executable or suppress its version warnings.
Q2 touchscreen handling of the patched version remains a physical acceptance
check; do not acknowledge an unexpected firmware update dialog blindly.

## Interrupted operation

If programming might have started and readback is not verified, the marker is
retained and serial-owning services remain stopped. Do not remove the marker or
start printing. Use the recovery folder named by the marker and the independently
verified recovery-entry procedure. Restore stock through the same upstream tool,
with --recover-to-stock for this bootloader, and verify the full application and
unchanged bootloader before restoring the recorded services and removing the
marker. The coordinator does not invent an automatic recovery path after process
termination or power loss.

Before programming starts, a failed snapshot or service stop restores the
previous services without changing firmware. A failed service restore retains
the marker even when firmware readback passed. Original motion/configuration
files are never transaction targets.

## Validation

Run python3 q2_port/test_thr_deploy.py for transaction scenarios. For the actual
private captured bootloader, run pinned upstream scripts/check_thr_flashing.py
and scripts/check_thr_recovery.py with --stock-image, --patched-image and
--bootloader-backup. Those execute captured ARM code with emulated hardware;
they do not prove electrical behavior, independent recovery entry or a real
successful flash. Archive the logs without committing flash binaries or private
printer configuration.

## Explicit operator acceptance, November 23

The owner explicitly instructed proceeding without the physical recovery check.
The coordinator now accepts `--accept-unverified-recovery` only with a matching
Q2/SOC/bootloader record retaining `independent_recovery_verified=false`,
`operator_accepts_unverified_recovery=true`, and the operator instruction.
Default admission still requires verified recovery. The original false evidence
is never relabeled true; the transaction journal preserves this accepted risk.
All image admission, idle checks, backups, recover-to-stock, readback, pending
markers and service-restoration rules remain unchanged. This does not establish
that recovery works after an interrupted write or cold boot.

The November 23 Q2 operation completed successfully: fresh stock readback was
admitted, patched application readback matched the pinned candidate exactly,
and the bootloader stayed unchanged. THR reports `02.02.01.08-valve-oil.1`.
Services returned ready/idle with all heater targets zero, Box online, no
pending configuration, and unchanged saved printer configuration. Stock rollback
and after-readback captures were retained. No physical recovery check or new
input-shaper calibration was performed; calibration is still required before
printing. This is evidence from this printer, not general Q2 support.

The resulting Q2 touchscreen board-version popup was subsequently addressed
with the separately reviewed [two-byte touchscreen fix](TOUCHSCREEN_POPUP.md).
That operation restarted only qidi-client and did not reflash the THR.
