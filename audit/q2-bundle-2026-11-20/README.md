# Combined Q2 non-motion preview and dry run

Built November 20 from released Valve Oil 26.11.18.1 main
fea34e996f1ab64c646dd02846d1bb47ad93c272, our deployed Q2 Box dev1 and local
Q2 host/web compatibility changes. Scope excludes new movement, homing,
cutting/loading-flow behavior and optimized print macros. Existing, separately
authorized tag-writing slot-jog is carried forward unchanged. Nothing was
installed, flashed, restarted, homed or moved by this build/dry run.

## Result

297 file targets checked against read-only copies of actual Q2 files:
258 creates (mostly static web assets), 6 replacements, 33 unchanged.
No guarded Moonraker source transform rejected the captured Q2 files.
Replacements are config module wiring, klippy_apis.py, moonraker.asvc,
Moonraker spoolman.py, metadata.py and web entry. Calibration and original
stock settings are preserved. Catalog merge retains QIDI/operator entries.

Eight dry-run/install-simulation/repeat/rollback/rejection tests passed.
Eleven upstream Moonraker tests passed after enabling their local test
loopback sockets. Eight Box Thumb handler cases and 30 synthetic Q2 shutdown
scenarios passed. THR passed 1024 stock/patched FIFO executions and identify
version-only consistency. Two Box factory-calibration read cases passed.
Repeat firmware builds produced identical bytes/reports; modified and
already-patched THR inputs were rejected. Payload Python parses as Python3.9.
The final archive was extracted and its standalone planner passed again.
These are offline checks, not new physical firmware/sensor qualification.

## Combined firmware

- Box: exact reproduction of deployed dev1, SHA256
  50e1b2d76a64d3ef7a0c8f79eb4a84be9eafd93cb0912e55d994c8245d93f903.
  Q2 transport adaptation of Tuba RFID commands plus our host read guard;
  stock Q2 shutdown retained, bootloader outside application unchanged.
- THR: cached Q2 02.02.01.08 exactly matches the upstream Max4/Plus5 stock
  hash 1d34b4b0142f2a2047f08c2fae59d827bcee0adbd1563b4bd1de311dff8b2d62.
  Its hash-locked FIFO fix produces the exact upstream patched image
  b6e39b1def0bad6c2379cad600c1284cece0c26caab77dbb659adf64d4f4172a.
  Standalone candidate only. No full QIDI update ZIP or mainboard patch.

New THR flashing still requires idle readback/bootloader/recovery admission;
none was attempted during the owner's print. Physical sensor reporting and
blank-tag writing remain unvalidated.

## Correction and boundaries

Our earlier Box-temperature blocker was incorrect: retired commands18/19
are RFID register/init diagnostics, not standard debug_read/write (12/11).
Standard debug_read and both calibration halfword reads are preserved and
were emulated. Temperature reporting is therefore staged, not live-installed.
Existing firmware need not be changed to restore those standard commands.

Captured printer.cfg has 43 SAVE_CONFIG headers, also present in earlier
backups (40 before the latest host module installation). Planner preserves
the entire tail from the first marker rather than rejecting or cleaning it.
This historical accumulation deserves separate investigation before release.

This remains a selective preview, not full upstream parity. Source recipes
for add-on management, OS/kernel/IRQ/storage changes and automatic updates
are included for review but have not passed/enabled Q2 installer/privilege/
architecture admission. Their guards are not bypassed. The camera fault is
separate and no speculative camera policy is baked into firmware.

## Artifacts and reproduction

Local full preview and source-only archives are in the work folder outside
Git. The full archive includes QIDI-derived firmware and is not a public
release. Machine snapshots and private recovery/config files are excluded.
The source archive excludes vendor binaries and built web assets and is
clearly labeled non-installable. Source builders/planner/tests are in q2_port.
Builder source records the development workspace layout; reproducing the
complete package needs the pinned upstream checkout, locked web builds,
exact stock firmware inputs and a private target-file snapshot. It is not a
general Q2 installer. See the full preview README for commands and limits.
