# Next Q2 bundle: 2026.11.21-stable2-preview2

Prepared offline for the next push. **No printer access, upload, restart, reset,
calibration or firmware flash.** The user's running print was not touched.

## Contents and changes

- The exact independently vetted toolhead candidate, SHA256
  b6e39b1def0bad6c2379cad600c1284cece0c26caab77dbb659adf64d4f4172a.
- Matching QIDI stock application reference, SHA256
  1d34b4b0142f2a2047f08c2fae59d827bcee0adbd1563b4bd1de311dff8b2d62.
  This is not a physical readback backup of the installed board.
- Fresh official-Q2 provenance/vetting report and an explicit pending-admission
  record, with automatic flashing disabled. Canonical image, stock reference,
  evidence and admission fields are independently bound by the bundled planner.
- The corrected recovery helper, renderer and regression tests from 91e5636.
- Existing stable 26.11.18.2 host/UI payloads, stock-motion exclusions and unchanged
  Q2 Box dev1 candidate. No new motion, loading/cutting macros or OS tuning.
- Reviewed THR patch/generator/checker source references and existing licenses.

Bundle format advances to schema 3. Older archives retain their own planners;
use the planner shipped in the archive being checked. The new assembler requires
--thr-stock and --thr-vetting inputs and rejects mismatched images or evidence
before publishing its output.

## Baseline and expected effect

The private snapshot was reconstructed offline from the saved pre-deployment
capture plus all 328 verified installed payloads. It represents the last verified
host deployment, not a live capture of the currently printing machine. New mesh
or other owner changes made during this print are not included and must be
checked while idle before any later deployment. Private snapshots are excluded
from both archives and Git.

Against that reconstructed state the host plan is 0 creates, 0 replacements,
352 unchanged targets. The toolhead files are artifacts outside the host target
operation list. This bundle does not enable a Q2 toolhead flasher. Do not invoke
host activation merely to deliver the candidate when the host plan is unchanged.

## Validation

- 17 bundle regression tests, including altered stock/candidate images, rehashed
  image tampering, mismatched evidence and changes to the no-auto-flash/pending
  admission record. These checks still reject after inventory regeneration.
- 16 host transaction/recovery tests, including the three reviewed fixes.
- Final bundled candidate re-vetted against the official QIDI Q2 ZIP; 1,024 ARM
  FIFO execution cases, identify consistency and unsafe-input rejection passed.
- Repeated assemblies compared by full file/hash inventory.
- Full archive extracted and its independent planner run twice without modifying
  the extracted files. Payload syntax checked for Python 3.9.

The file-copy repeat/restore test has no host changes on this post-deployment
baseline; nonempty transactions and recovery paths are covered separately by the
host helper tests and prior deployment evidence. No physical rollback, new print,
new tag-write or new THR flash is claimed by these offline tests.

See validation logs, dry-run.json, build-verification.json and archives.json.
The complete firmware archive is local/private; source, reports and artifact
hashes are committed. No vendor firmware binaries or compiled web builds are
added to Git. The source-only archive is not a standalone installable bundle.

## Before a future firmware deployment

Wait for idle. Establish the installed application and physical bootloader
identity, Q2 reset/UART/boot entry and recovery procedure, and Q2 touchscreen
handling of the patched version suffix. Obtain separate firmware deployment
authorization, verify application readback afterward, then recalibrate input
shaping before bed leveling or printing. The vendor stock file in this bundle
supports review/recovery planning but does not replace those checks.

No push or deployment is performed as part of preparing this revision.
