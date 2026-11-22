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
