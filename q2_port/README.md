# Q2 selective non-motion preview: 2026.11.21-audit2

Offline build and file planner only. This is not an installer, firmware updater,
or a claim of full Valve Oil support. No printer is contacted by these tools.
This revision supersedes the November 20 preview for further testing.

## Scope

Pinned released Valve Oil 26.11.18.1 source at
`fea34e996f1ab64c646dd02846d1bb47ad93c272`, reviewed Q2 host/web adaptations,
our Q2 Box dev1 image and the upstream THR FIFO candidate. Q2 SOC admission is
limited to 01.01.03.02, based on a private cached manifest. Physical board
identity is not established by that file.

New movement, homing, cutting/loading-flow changes, optimized print macros,
and mainboard firmware are excluded. An already installed identical tag-writing
slot-jog module may be carried forward; it is never newly installed by this plan.
Catalog overlays preserve existing entries and conflicting IDs. Personal spool
inventory is not included. Camera troubleshooting is separate.

Add-on management and OS tuning files in review-recipes are source references.
They are not complete runnable subsystems and their dependencies are not bundled.
Automatic update actions remain blocked. Spoolman requires an operator's server
and spool assignments. Physical temperature reporting and blank-tag writing
have not been validated by this build.

## Read-only plan

Extract the full private preview, then run with Python 3.9 or later:

```sh
python3 plan.py --dry-run --snapshot /path/to/private-q2-snapshot
```

The snapshot must mirror absolute target paths beneath its root, including the
cached firmware manifest. It is not included. The planner rejects unknown input
hashes, altered firmware identities, unsafe targets and symlinks. It permits only
recorded before/after states. Configuration rendering preserves the bytes after
the first SAVE_CONFIG marker; this does not validate calibration or fix the
historical repeated markers. Checksums detect accidental changes, not malicious
replacement of the package and its verifier together. Use trusted source.

## Rebuild in the reviewed development workspace

The source-only archive is not a standalone reproducible checkout. Builders
require the original workspace layout recorded in source-lock.json, including
reviewed web builds and host adaptations, the pinned upstream tree, the Q2
adapter source, exact vendor firmware inputs, and a private target-file snapshot.
Missing or changed locked inputs are rejected before upstream Python is imported.
The lock is a content inventory, not a digital signature.

```sh
python3 source-tools/build_firmware.py --upstream /path/to/pinned-upstream \
  --q2-port /path/to/q2-adapter-with-stock-bin --thr /path/to/stock-thr.bin \
  --output /path/to/new-firmware-output
python3 source-tools/assemble.py --upstream /path/to/pinned-upstream \
  --workspace /path/to/reviewed-workspace --snapshot /path/to/private-q2-snapshot \
  --firmware /path/to/new-firmware-output --output /path/to/new-preview
python3 source-tools/test_bundle.py --bundle /path/to/new-preview \
  --snapshot /path/to/private-q2-snapshot -v
python3 source-tools/check_firmware.py --upstream /path/to/pinned-upstream \
  --q2-port /path/to/q2-adapter-with-stock-bin --thr-stock /path/to/stock-thr.bin \
  --firmware /path/to/new-firmware-output
```

From the Git checkout use q2_port instead of source-tools. Build dependencies
include Thumb-capable clang and zopfli; emulation additionally needs capstone and
unicorn. Optimized Python is refused by the firmware builder because imported
legacy verification uses assertions. Emulation may require executable-memory
permission on macOS. No flashing command is provided.

## What testing proves

The audit exercises read-only planning, drift and tamper rejection, scope limits,
metadata handling and file-copy repeat/restore behavior. File-copy simulation
is not an installer rollback test: it does not test ownership, service activation,
nginx admission, kernel behavior, power loss or physical recovery. Firmware
emulation covers 1024 THR FIFO cases, identify consistency and two Box calibration
reads. It is not physical sensor or bootloader qualification.

Before any future deployment, implement and test ownership/mode policy, service
activation ordering, nginx validation, backups and actual rollback. New THR
flashing additionally requires idle physical application/bootloader readback,
exact admission, recovery qualification, verified post-flash readback and review
of recalibration requirements. The planner reports deployment_ready=false.

Firmware binaries retain QIDI's rights. The full preview is private local test
material. Source-only packaging excludes vendor binaries, web builds, machine
snapshots, identifiers, credentials and private recovery data. Upstream license
and notices accompany both packages.
