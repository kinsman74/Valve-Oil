# Q2 RFID alignment with Valve Oil 26.11.18.1

Installed November 19, 2026. Upstream main:
fea34e996f1ab64c646dd02846d1bb47ad93c272. The reader and catalog here are
unchanged upstream files. Our previous inventory_rfid_read_guard remains
unchanged. This checkpoint follows q2-box-rfid-dev1; its verified Q2 Box
application remains installed without another firmware flash.

## Included

- New reader with Creality, TigerTag and OpenTag3D support alongside QIDI,
  Anycubic, Elegoo and Bambu.
- Improved tag reselection, full-memory reports, diagnostic scanning and
  command aliases. VO_BOX_RFID_REPORT, VO_BOX_RFID_TEST and VO_BOX_RFID_WRITE
  are registered on the live Q2.
- Latest catalog, preserving every existing native entry. Additions by
  nozzle: 0.2 mm 18; 0.4 mm 34; 0.6 mm 34; 0.8 mm 32.
- Fluidd v1.37.7-tltg-32e13db-q2, including the new Box tag-writing dialog.
  Built from upstream tag v1.37.7-tltg-32e13db with the prior Q2 flat-slot
  status fallback and service worker disabled. The version injector uses
  explicit source identity 32e13db-q2 because the source archive has no Git
  metadata. The existing fallback patch and Q2 regression fixture are here.

## Boundaries

Automatic spool rotation for writing an empty slot is not enabled: it needs
Valve Oil's additional box_slot_jog motor-control module, which has not been
qualified on this Q2. Upstream refuses that operation when the module is
absent. A slot with filament inserted supports the upstream manual-turning
write workflow. No physical tag write has been attempted or verified.
Do not use an OEM tag for write validation; upstream only permits blank or
recognized QIDI-format writable tags and verifies readback.

No mainboard/toolhead flash, hardware configuration, calibration, cutter
coordinates, motion configuration, OS optimization or update takeover was
applied. Firmware application remains the verified Q2-specific dev1 image.
Stock printer.cfg and our read guard were hash-verified unchanged. Before
the reload the runtime acceleration limit was 5000; after reload the existing
configured limit of 20000 returned (velocity 600). The previous runtime
acceleration 5000 is being restored after startup scans; verify the final
status before declaring runtime-limit preservation complete. No configured
motion setting was edited.

The newer Valve Oil installer, update scheduling, external-spool fixes,
cold-cut changes, ZeroTier and OS changes are outside this RFID/web update.
The 485-device log issue and cloud MQTT authorization issue remain separate.
Studio settings were not changed in this update. New OEM formats and native
Box tag writing still need physical acceptance on the Q2. Anycubic had
passed on all four slots before this update; fresh post-update reads must
be recorded separately.

## Validation and recovery

Eight upstream reader/catalog/writer-protection tests passed. Eight isolated
compiled-Q2-reader plus new-host/old-guard scenarios passed. The Q2 display
regression passed alongside 178 selected upstream web tests. Production
web build succeeded. Live API returned standby, both readers registered,
all new commands present, job not running, and the expected web version.
These results do not substitute for a physical write/readback test.

Private before/after snapshots, exact before/after manifests, full web bundle
and on-device backup directory are retained locally under the corresponding
work/q2-valve-align-26.11.18.1 folder. No credentials, private snapshots or
hardware identifiers are committed. The install and rollback scripts require
the associated private package, manifest and originals; they are not a
standalone public installer. Install checks idle/task/heater state and exact
input hashes, backs up each changed file, preserves owner/mode, verifies web
assets and file replacements, and restarts services. Rollback refuses when
installed files changed after this update and checks backup hashes before
restoring. Require zero heater targets and no RFID scans before rollback.

For a new build: obtain the pinned upstream Fluidd source and locked
dependencies, apply q2-fluidd.patch, set version provenance explicitly,
run the tests and Vite production build. Never run the upstream all-model
installer on Q2; Q2 is not an upstream supported model.
