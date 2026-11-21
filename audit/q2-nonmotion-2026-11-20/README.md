# Q2 non-motion feature installation, November 20, 2026

Authorized scope: remaining released Valve Oil features that do not change
movement, print macros or hardware-specific behavior. Pinned source is
26.11.18.1, fea34e996f1ab64c646dd02846d1bb47ad93c272. No dev-branch
26.11.18.2 features were deployed.

## New host modules

Installed and loaded: background_save_config, save_variables_fast,
klipper_health, macro_status, printer_warnings, spoolman, probe_test,
probe_report, box_heater_refresh and update_lights, with tltg_ filenames and
sections. Macro_status is a lightweight read-only facts provider; it does not
install optimized macros. Health supplies diagnostics and stopped/orphaned
load-cell timer cleanup, with original behavior retained by its wrappers.
Box heater refresh changes resend cadence and shutdown-poll handling, not
heater limits or targets. Probe report is passive; probe_test is a motion-free
manual diagnostic command and was not run physically. Spoolman slot integration
is installed but no Spoolman server or invented inventory connection was added.
Update_lights is installed but inactive without an automatic-update hold file.

Printer_warnings has one Q2 gate: skip the input-shaper warning when optimized
motion globals are absent. Upstream's warning claimed acceleration was limited
by macros not installed on this Q2. Existing warning wording is unchanged;
that incompatible check is omitted. No calibration decision or change was made.
The helper's shape information alone must not be treated as a Q2 calibration
audit.

## Companion UI and status

Released Valve Oil UI built as 26.11.18.1-q2 is served at /valve-oil/ beside
Fluidd. Q2 flat slot-status parsing and RFID-state fallback were ported from
our Fluidd adaptation. Source patch and regression fixture are included.

Added authenticated nginx routes and tltg-status.service on loopback 7133.
Status source has an explicit Q2 selective-port boundary: all POST mutations
are rejected with HTTP409 and update_now always carries a Q2 unsupported-port
blocker. The separate Q2 metadata file does not fake a normal upstream
installer ledger. No upstream installer bundle, automatic update/enrollment,
firmware takeover or board-flash action was enabled. Read-only status and
upstream support-bundle GET capability are provided. The service was verified
through nginx; graphical browser inspection was attempted but its webview
failed to attach, so no full interactive visual acceptance is claimed.

## Held back with concrete reasons

- Box MCU temperature: QIDI temperature_mcu calibration calls debug_read/
  debug_result; our Q2 RFID firmware repurposed those handler slots. Enabling
  it unchanged could block initialization. Needs a separately qualified
  firmware/sensor adaptation, outside this no-board-firmware scope.
- klipper_fixes contains trsync/stepper changes, not just status fixes; omitted.
- box_loaded_slot, filament guards, flow recovery, feed/eject/cut modules,
  dry-time spool rotation, resonance/velocity/pause macros and calibration
  helpers alter movement, print flows or hardware handling; omitted.
- chamber_exhaust_guard changes fan behavior and depends on the optimized fan
  macros; omitted. Bed-soak and calibration tools perform heating/motion.
- OS/kernel/storage/network tuning remains unqualified for this Q2 kernel and
  retained stock environment. No unsupported upstream admission guard bypass.
- Add-on management and automatic updates are not complete standalone Q2
  features: their upstream installer/privilege/kernel admission has not been
  ported. No broken manager or blanket sudo grant was installed. No third-party
  remote-access program or account was added.

These are compatibility/scope boundaries, not a claim of full upstream parity.
The existing RFID, monitors, tag-writing rotation, screen mirror and selected
host source fixes remain installed.

## Validation and recovery

29 upstream host tests passed (save variables, health, heater refresh,
probe signal). 219 companion UI tests passed, including the new Q2 flat-slot
case; production TypeScript/Vite build succeeded. The Q2 warning gate and
status mutation rejection were tested separately. All ten modules compile
under the Q2's actual Python environment. Live same-value SAVE_VARIABLE
preserved both saved-variable file hash and modification time, confirming the
fast no-op path. SAVE_CONFIG and real probing/heating were not exercised.

Final live state: ready/standby, no startup scans or active warnings, camera
online at 640x480/15 FPS, camera-only power/control=on preserved. Stock
configuration excluding the added module sections compared exactly to its
before copy; saved calibration block unchanged. Original runtime acceleration
5000 restored; no homing, movement, board flash or OS reboot was performed.
Only host services were reloaded; camera services were untouched.

Private backups, exact install manifests, complete web bundle and on-device
recovery paths remain in work/q2-nonmotion-2026-11-20 and on the printer.
Hash-guarded module and web rollback scripts were staged. Scripts here require
the associated private package and manifests; they are not standalone public
installers. Do not commit private configuration or hardware identifiers.

Correction from the bundle audit: the earlier Box-temperature rationale was
incorrect. Standard debug_read/write remain intact; only legacy RFID
diagnostic handlers were retired. Factory-calibration reads passed offline
emulation. The sensor module is now staged in the preview, not installed live.
See ../q2-bundle-2026-11-20/README.md.
