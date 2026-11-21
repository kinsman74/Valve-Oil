# Q2 selective non-motion preview: 2026.11.21-stable2-preview1

The build and file planner are offline tools. A separate, explicitly invoked
[host deployment helper](HOST_DEPLOYMENT.md) now supports admitted per-device
host activation; it is not a general installer or firmware updater. This does
not claim full Valve Oil support.
This revision supersedes the audit2 preview for further offline testing. The archived preview itself remains an offline artifact; see the deployment audit
for the separately admitted host activation.

## Scope

Pinned released Valve Oil 26.11.18.2 source at
`aa42eaa3c48f155282f3bda43720199f7e657d99`, reviewed Q2 host/web adaptations,
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

## Stable 26.11.18.2 selection

The two Box monitors take upstream's identifier masking, report-trigger and
continuous log-size enforcement fixes. Existing TLTG module, command, setting
and log names remain intact; the broad VO migration is deferred. Other host
helpers and the RFID reader/read guard remain at their reviewed Q2 baseline.

The companion UI uses stable 26.11.18.2, with Q2 flat slot decoding restored.
Fluidd uses stable's pinned source e85f13b2b7bddb3b5f98dd16de808c8461339a1e.
Both retain the existing tag-jog command name. Companion UI retains the original
manual jog component and speeds in Home and Control. The new calibration screen
is disabled, and Fluidd retains its previous toolhead card: new Tools-menu
automatic homing is deliberately excluded from both interfaces. No motion,
load/unload, slicer or optimized print macros are installed by this package.

The Q2 status service, authenticated routes and blocked updater POST actions
are retained. New upstream installation recovery/boot checks are bundled only
as reference code and documentation; they are not a tested Q2 installer. The
activation checklist adds backup/journal, interrupted-operation and bootability
checks, but those checks have not run on the printer. No root filesystem repair
or dosfstools installation is attempted. Stable's queued-write timeout fix is
an installer change, not a new runtime RFID retry fix. UI camera layout fixes
do not fix the separately tracked USB camera fault.

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

Source staging recipes are stage_stable.py (the supplied upstream/workspace into
a new --output directory) and stage_fluidd.py (the pinned --source tree into a
new --output directory). Their output paths used by this workspace are recorded
in assemble.py and source-lock.json. The recipes preserve the baseline inputs;
they do not regenerate trust locks automatically. After staging, use pnpm import
and pnpm install --frozen-lockfile for companion UI, and the supplied frozen pnpm
lock for Fluidd. Run each project's tests and build. Set
VO_UI_VERSION=26.11.18.2-q2-preview for companion UI and
Q2_FLUIDD_REV=e85f13b-q2 for the tarball-based Fluidd build.

check_stable_monitors.py runs upstream regressions against the adapted monitor
sources; check_stable_scope.py verifies retained modules and movement boundaries.
See the accompanying audit for exact results and known limitations.

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

Before another deployment, recheck the current snapshot, idle state, ownership/
mode policy, service ordering, nginx, backups and recovery admission. The separate
host helper has passed one-device activation and local recovery simulations;
a deliberate live rollback and power-loss qualification remain unperformed. New THR
flashing additionally requires idle physical application/bootloader readback,
exact admission, recovery qualification, verified post-flash readback and review
of recalibration requirements. The planner reports deployment_ready=false.

Firmware binaries retain QIDI's rights. The full preview is private local test
material. Source-only packaging excludes vendor binaries, web builds, machine
snapshots, identifiers, credentials and private recovery data. Upstream license
and notices accompany both packages.
