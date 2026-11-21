# Stable 26.11.18.2 selective Q2 refresh

Historical offline checkpoint, November 21, 2026. Deployment was subsequently
authorized and completed; see [the deployment audit](../q2-deployment-2026-11-21/README.md).

At the time of this build: **offline only; deployment held for the current print.**
No printer was contacted, restarted, moved, reconfigured or flashed by this work.
The next candidate now uses the selected stable 26.11.18.2 changes rather than
claiming full Valve Oil parity.

## Pinned originals

- Valve Oil stable v26.11.18.2: aa42eaa3c48f155282f3bda43720199f7e657d99.
- Release-pinned Fluidd source: e85f13b2b7bddb3b5f98dd16de808c8461339a1e.
- Previous audited Q2 baseline: e42b635 plus debugging notes dc3d556, based on
  Valve Oil 26.11.18.1 fea34e996f1ab64c646dd02846d1bb47ad93c272.
- Current/previous content locks, staging recipes and compatibility patches are
  under ../../q2_port. Original downloaded trees and private snapshots stay in
  the local work directory. Source locks are content inventories, not signatures.

## Included and deliberately retained

| Component | Selection |
| --- | --- |
| Box RS-485 monitor | Stable identifier masking for damaged/junk frames, lease IDs and adapter names; corrected report-trigger activation |
| Box link monitor | Stable log cap checked after writes, allowing rotation during long sessions |
| Companion interface | Stable UI, numeric-command formatting and camera layout/fullscreen fixes; Q2 native flat-slot display restored |
| Fluidd | Stable-pinned source plus Q2 native slot display; existing toolhead card retained |
| Names/settings | Existing TLTG module, setting, monitor log and command identities retained; VO RFID commands already supported remain unchanged |
| Movement | Existing companion manual jog component and speeds retained in Home and Control; new movement Tools menu and tuning/calibration screen disabled |
| RFID/Box firmware | Existing reviewed reader, read guard, tag-writing jog and Box dev1 bytes retained |
| Toolhead firmware | Same exact FIFO candidate as before; built/emulated only, not flashed or physically admitted |
| Moonraker/status | Existing behavior retained; upstream private-name renames normalized to keep the runtime payload identical; updater POST guard retained |
| Recovery | Stable boot/recovery/queued-write reference sources and boot-recovery documentation included; future activation checklist strengthened |

Only the two monitor Python payloads differ from the previous audited package.
The expanded web asset count is not a count of newly installed features.
No custom inventory/catalog work is added. Existing QIDI entries remain protected.

## Excluded or deferred

All motion, homing, cutting/loading-flow changes, slicer behavior, optimized
print macros and mainboard firmware remain excluded. The development-only
26.11.20.1 unload change is not included. Broad VO variable migration is deferred;
copying newer modules without their matching names/settings is not supported.

Stable's general installer recovery, root filesystem repair, dosfstools install,
automatic updates, OS tuning and add-on manager are not enabled. Recovery modules
in review-recipes are reference source with external dependencies, not a runnable
Q2 installer. Upstream recovery tests passing does not qualify our Q2 deployment
or rollback. New THR flashing still requires idle physical application/bootloader
readback, admission, recovery qualification and post-flash readback.

The camera layout changes do not repair the pre-existing USB camera dropout.
Historical repeated SAVE_CONFIG markers are preserved, not cleaned or validated.

## Debugging and checks

- 21 adapted upstream monitor tests pass against the actual staged Q2 modules,
  including identifier redaction, MCU serial-port protection, report activation,
  ongoing log rotation and temperature-sensor fakes. Two filename-order test
  expectations were adapted because retained old log names sort differently.
- 653 companion UI tests pass, including the Q2 native-slot regression;
  TypeScript checking and production build pass.
- 68 targeted Fluidd Box tests and all 577 utility tests pass; type checking
  and production build pass. The initial tarball-source
  build required an explicit revision string because no .git directory exists.
  It now identifies itself as e85f13b-q2 rather than claiming an untouched build.
- 20 upstream Moonraker and interrupted-install/recovery simulation tests pass.
  These use local stand-in files/services, not the printer.
- Firmware rebuild reproduces both previous candidate SHA256 values. Offline ARM
  emulation passes 1024 THR FIFO cases, identify consistency and two Box factory
  calibration reads. No physical sensor or new toolhead firmware test occurred.
- Scope checker verifies unchanged retained host helpers, read guard, tag-jog,
  manual jogging and Fluidd toolhead card, with new movement controls excluded.
- All 16 final bundle regression tests pass. They cover read-only planning, target drift, firmware/payload
  tampering, out-of-scope motion injection, metadata, safe paths and repeat runs.
  Copy/restore simulation is not a real activation/rollback test.
- Stable source staging was repeated and compared with the prepared compatibility
  sources. The final archive is extracted and its read-only planner run twice.

See selection.json and dry-run.json for exact target counts, bundle-tests.log
for final regression results, and archives.json for local artifact hashes.
The planner continues to report deployment_ready=false.

## Next test deployment

First prepare and qualify the actual activation/rollback procedure while idle,
including service order, permissions, bootability, config include integrity,
backup/journal state and nginx validation. Refresh the private target snapshot
and reject drift before any write. Deploy host/web changes separately from a THR
flash. The print-in-progress hold remains in effect; this checkpoint does not
lift it. No push or deployment is part of this offline refresh.

Upstream references: [stable release](https://github.com/thelegendtubaguy/Valve-Oil/releases/tag/v26.11.18.2),
[monitor/UI fixes](https://github.com/thelegendtubaguy/Valve-Oil/pull/341),
[queued installer writes](https://github.com/thelegendtubaguy/Valve-Oil/pull/333).
