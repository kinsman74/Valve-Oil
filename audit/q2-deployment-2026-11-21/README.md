# Q2 host/interface deployment, November 21, 2026

**Deployed and independently verified.** The selective Valve Oil 26.11.18.2
host/interface payload from checkpoint 0c84d0c is active on the owner's Q2.
The Plus5 was not changed. No firmware binaries were transferred, no firmware
was flashed, and no OS reboot or homing command was issued.

## Deployment findings

The ordinary qidi login worked. It is not a sudo administrator; the earlier
successful installs used its existing systemd service-management authorization.
That permission was confirmed read-only before reusing the same method. No
account permissions or passwords were changed, and no alternate-account login
was used. An automatically rejected guessed-account approach was abandoned.

The first transaction refused an additional appended bed-mesh block before any
installed-file write or service stop. The configuration change was reviewed as
append-only comments, then the latest bytes were retained in a fresh package.
All 328 target preimages were verified again immediately before the second
transaction. The calibration tail was preserved byte-for-byte.

The successful transaction backed up all 12 replaced files with original
ownership/modes, journaled all operations, installed 316 new files, validated
nginx, restarted the required services and waited for printer readiness. It took
about 73 seconds. Temporary disconnected/503 messages during service startup
were followed by ready state; they are not evidence of a continuing failure.

## Verified result

- All 328 installed file hashes match the rendered package.
- Original ownership/modes match for 12 replacements; 316 new files have mode 0644.
- All 12 recovery-file hashes match their original preimages.
- Klipper, Moonraker, QIDI client, nginx, status and screen-mirroring services active.
- Printer ready/standby, all heater targets zero, no active RFID job or Box flow.
- Fluidd identifies as v1.37.7-tltg-e85f13b-q2.
- Companion UI identifies as 26.11.18.2-q2-preview.
- Status reports 26.11.18.2-q2-selective; updater POST remains blocked with HTTP 409.
- Authenticated touchscreen stream returns a 480 x 272 JPEG; no touch messages sent.
- Box1 MCU temperature reporting now physically returns about 37 degrees C.
  This confirms reporting, not absolute sensor calibration accuracy.

See acceptance.json, interfaces.json, screen-verification.json,
backup-verification.json and permissions-verification.json. Private configs,
identifiers, access tokens, credentials and recovery contents are excluded.
The exact on-printer recovery path is recorded privately in the deployment work
folder, not exposed in a public recovery archive.

## Recovery and repeatability

The separate host_deploy.py helper performs live idle/heater/Box admission,
target hash and scope checks, durable preimage backups/journaling, atomic file
replacement, preserved ownership/modes and service health checks. Failure during
activation invokes restoration. Unknown later target edits block rollback.
An interrupted transaction with Klipper stopped can be recovered without requiring
an unavailable live API. A successful active installation still requires live
idle admission for normal rollback.

Eight local tests cover apply/restore, activation-failure restoration, drift,
corrupt payloads, scope exclusion, incomplete transactions, offline interrupted
recovery and unsafe live print/heater/Box states. These use fake services.
A symlink spelling difference between macOS /var and /private/var was found by
those tests and fixed by resolving roots before transaction bookkeeping.
The renderer reproduces the admitted operation list and every rendered payload
byte. The live success also exercised file permissions, backups, nginx and
service activation on this specific Q2.

A real rollback was not deliberately run on the printer after success; power-loss
recovery, a new physical print and tag writing remain untested here. Toolhead FIFO
firmware remains unflashed and is outside this deployment. The pre-existing
camera fault remains separate; no USB/camera reset was attempted.

The archived preview and read-only planner remain historical offline artifacts,
not a universal installer. This was a separately admitted, per-device host
activation. General updater/OS/add-on takeover and motion optimizations remain
excluded. See [host deployment procedure](../../q2_port/HOST_DEPLOYMENT.md).
