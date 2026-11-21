> Historical checkpoint before the non-motion expansion. See [current additions](q2-nonmotion-2026-11-20/README.md).

# Q2 checkpoint versus Valve Oil, November 20, 2026

Released baseline: Valve Oil 26.11.18.1, main/tag
fea34e996f1ab64c646dd02846d1bb47ad93c272 (verified remotely).
Unreleased dev checked at 6670ec74a7253a483f30c08f4ada4d465925aa96,
26.11.18.2. Nothing from that dev branch was installed by this audit.
This is a selective Q2 adaptation, not the upstream full installer.

## Installed

- Q2-specific Box firmware dev1 with select/transceive RFID extensions;
  application readback verified, original bootloader preserved.
- Released host RFID reader and catalog: OEM Anycubic/Elegoo/Bambu and
  Creality/TigerTag/OpenTag3D format support, reports/diagnostics, tag-writing
  commands and web dialog. Format support is not physical acceptance of every
  brand. Genuine QIDI factory tags are unavailable for testing.
- Additional local inventory_rfid_read_guard: rejects empty/malformed results,
  preserves stock confirmation/timing and quarantines conflicts.
- box485_monitor, box_link_monitor enabled, box_slot_jog for tag-writing
  rotation. Slot rotation/write commands exist; physical blank-tag write is
  not yet acceptance tested. Automatic drying-time spool roll is separate
  and NOT installed.
- Q2 Fluidd v1.37.7-tltg-32e13db-q2, flat-status adaptation and no service worker.
- Remote touchscreen backend, authenticated nginx routes, service enabled;
  websocket/frame capture and visual orientation verified without touch input.
- Earlier selected source patches: Box heater configuration/65 C UI limit,
  shutdown-reason reporting, Moonraker metadata cache and multi-plate/used-tool
  3MF metadata handling.
- Released catalog merges preserve existing native entries. Earlier local
  Studio mapping work exists; this is not the full Valve Oil slicer pack.

## Upstream extra-module inventory

Active released extra modules: box_link_monitor, box485_monitor, box_slot_jog,
box_rfid; filament_catalog installed as reader helper (not its own section).

Not installed as upstream modules: box_mcu_temperature,
background_save_config, box_heater_refresh, klipper_health, macro_status,
printer_warnings, klipper_fixes, save_variables_fast, box_feed_motion,
box_eject, box_filament_guard, box_loaded_slot, box_spool_roll,
box_flow_recovery, cold_cut, spoolman, probe_test, chamber_exhaust_guard,
step_loss_monitor, velocity_limit, resonance_sweep, pause_timeout,
update_lights. A selected host source patch is not equivalent to installing
all of these modules. Some are printer/hardware dependent or overlap stock
Q2 behavior; absence is not automatically a defect requiring transplantation.

## Other upstream components not ported

- Full optimized common/printer-specific macros and slicer starts/ends:
  faster homing/probing/tool changes, prime line, keep-loaded behavior,
  staggered heating, saved-mesh reuse and extended pause behavior.
- Mainboard/toolhead firmware patches, upstream model-specific shutdown fix,
  Max4 closed-loop motor/step-loss behavior and hardware tuning.
- OS/CPU/memory/storage/kernel/network optimizations, Wi-Fi service changes,
  package-managed cloud fixes and animation changes.
- Full Valve Oil companion UI, status/add-on backends, add-on management,
  automatic updates/windows, update takeover and USB installer.

Q2 stock mainboard/toolhead firmware, gantry configuration and calibration
remain. Runtime acceleration 5000 was restored following service restarts;
configured maximum acceleration remains stock 20000, velocity 600.

## Pending priorities and limitations

Configuration-save durability and external-spool load recovery were reviewed
but not applied; clarification requested. Full box_flow_recovery also alters
flows, cold cuts and stranded-filament motion, so it is not a narrowly scoped
external-wipe patch and must not be silently enabled on Q2.

Camera fault is pre-existing (support emails September 13/14, October 1),
recurred with released RS-485 monitoring active, and remains unresolved.
Service restart failed; camera-port reset did not recreate the device; hub
driver reattach plus camera restart recovered 15 FPS without OS reboot or
commanded motion. Camera-only power/control=on is a temporary trial; not a
permanent Valve Oil fix. Camera online at 15 FPS at checkpoint.

Newest dev contains RS-485 log redaction and Box link-log cap fixes, extensive
VO naming/path migrations, fuller companion UI, Wi-Fi lifecycle, prime-line
volumetric limits and installer recovery changes. These need separate review;
do not replace the released modules piecemeal across that migration.

## Repository state

Latest committed checkpoint before today's additions: b002580,
q2-port-readonly. RFID alignment, monitors, screen integration and camera
investigation notes are currently local untracked audit directories and are
not pushed. Private backups, identifiers and recovery records remain outside
committed audit material. No printer change was made for this checkpoint.
