# Q2 screw-tilt enablement, November 22, 2026

User explicitly requested injection of the published Q2 configuration.
Source: https://github.com/qidi-community/q2-wiki/blob/main/content/bed-tramming/README.md

Installed q2_port/config/q2-screws-tilt.cfg as
/home/qidi/printer_data/config/q2-port/q2-screws-tilt.cfg and prepended the single
include [include q2-port/q2-screws-tilt.cfg] to printer.cfg. No existing motion
macro, homing routine, firmware or fluidd.cfg was changed. This separate optional
configuration is not automatically injected by the existing preview2 assembler.

Before activation: printer ready/standby; all registered heater targets zero;
no Box tool-change or RFID task; active include graph had no conflicting section.
A new unsaved bed_mesh default was discovered. Saved it via QIDI SAVE_CONFIG_QD,
then validated its stored values against the pending snapshot with the installed
vendor autosave parser. Backed up the file before saving and before adding the
include. No movement/probing command was used.

After restarting Klipper and the QIDI client: ready; the new section loaded all
four published coordinates, CW-M4, speed 50 and clearance 10; command help exposed
SCREWS_TILT_CALCULATE. The saved default mesh loaded, existing input shaper
settings were unchanged, and printer.cfg retained exactly one SAVE_CONFIG block.
Readiness failure would restore the post-save pre-include file and remove only
the newly installed include. No probing, screw adjustment or accuracy result is
claimed. Refresh the interface to see the calculation control.

Private backups and rollback instructions are retained on the Q2 under
/home/qidi/q2-preview2-20261122/screws-tilt/. No private calibration/configuration
contents are committed. To roll back later, remove only this include and file
while idle, then reload Klipper; preserve all later owner/calibration edits.

An optional full-log read helper was killed during final inspection. Repeated
service checks showed all six port services active and 269 MiB available memory;
subsequent inspection used only the last 64 KiB. This was not a Klipper failure.

## Follow-up: missing home precondition

The initial enablement provided only the native command, which requires a
previous home. The owner reported that it failed until homing manually. Added a
SCREWS_TILT_CALCULATE wrapper that renames the native implementation to
_Q2_SCREWS_TILT_CALCULATE_BASE, calls QIDI's unchanged G28 only when homed_axes
is not xyz, then forwards rawparams to the native calculation. This is a local
wrapper around the published configuration, not a claim that the wiki block
includes automatic homing. No M4031 or chamber-heater command was added.

Jinja rendering verified the empty/xy/xyz homed cases and parameter forwarding.
The earlier include is privately backed up. Printer.cfg, calibration and screw
settings are not edit targets for this correction. Activation uses an idle-only
Klipper/client restart; no home or calculation is executed during verification.
The wrapper will initiate homing when the owner explicitly runs the command
with unhomed axes, so the bed must be clear before use.

## Follow-up: command dispatch after homing

The initial wrapper's internal alias _Q2_SCREWS_TILT_CALCULATE_BASE was invalid
for the installed G-code lexer: it dispatches as _Q2, rather than reaching the
registered calculation callback. This reproduced the owner's report that the
wrapper homes and then produces no screw measurements. Merely rendering Jinja
and seeing a name in HELP did not test actual dispatch; those checks missed it.

Changed the internal alias to _QIDI_SCREWS_TILT_CALCULATE_BASE. Used the installed
GCodeDispatch implementation in a separate process, with inert home/calculation
callbacks: old alias failed as _Q2 in every homed-state case; corrected alias
reached calculation for unhomed, partly homed and fully homed states. No printer
object, serial link, actual G28 or probing was instantiated by that test.
The reusable check is q2_port/check_screw_dispatch.py, invoked with the existing
klippy-env Python, --klippy-root /home/qidi/klipper/klippy and --config pointing
at the installed include. Backed up the broken include, changed only that file,
reloaded while idle with heaters zero, and preserved printer.cfg and calibration.
Physical execution of home-plus-probe remains for the owner to confirm.
