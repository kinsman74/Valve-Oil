# Q2 Box monitoring and tag-writing rotation, 2026-11-20

Requested additions: Valve Oil USB/RS-485 discovery protection, Box link
monitoring, and automatic spool rotation used by Box tag writing.

Sources are unchanged Valve Oil main fea34e996f1ab64c646dd02846d1bb47ad93c272:
box485_monitor.py, box_link_monitor.py, box_slot_jog.py, installed under
tltg_ names. Only their three module sections were added to printer.cfg,
before SAVE_CONFIG, preserving its calibration block. The saved variable
tltg_box_link_monitor was set to 1. No board firmware or gantry tuning changed.

The RS-485 monitor guards Klipper MCU serial ports from the RS-485 reader,
backs off missing-adapter retries from 2 to 30 seconds, and rate-limits the
repeated missing-485 log to hourly summaries. Link monitoring records health
and supplies upstream keepalive behavior. The generic slot-jog module supplies
the movement dependency of VO_BOX_RFID_WRITE for an empty slot: it retains
upstream idle/task/sensor checks and restores the borrowed motor state.
Enabling it is not a physical tag-write acceptance test.

Validation before install: 14 selected upstream RFID/spool-roll integration
tests passed; actual Q2 Box485Manager connect/reconnect, toolhead queue API,
stepper state APIs and five C motion helper symbols were checked in an isolated
process and all were present. Python syntax checks passed. These checks do not
prove camera recovery or physical tag writing.

Private configuration/saved-variable/compiled-interface backups and exact
installation manifests are in the local work folder and on-device recovery
folder (path recorded privately). Install requires idle, no active Box flow
or RFID scans, zero heater targets and unchanged input configuration. Original
configuration/modules and a hash-guarded rollback script were staged before
reboot. Rollback restores module/config files; the link-monitor saved flag
is inert if the module is removed. Require an idle printer, completed scans,
and zero heater targets before invoking recovery. The supplied scripts need
the private expected/installed manifests and originals; they are not a general
public installer.

A full reboot was requested to activate changes and reset the failed camera.
See the subsequent acceptance record for live outcomes. Do not interpret a
camera returning after reboot as proof that polling caused its USB failure.

Post-reboot: Klipper ready/standby, camera enumerated and stream source online,
link logging enabled and emitting MCU baselines, no RS-485 hardware detected
and no serial-port conflict. Slot-jog and tag-write commands registered.
Startup RFID checks must finish before printing. Camera recurrence and physical
blank-tag writing remain unvalidated. A reboot recovery alone does not establish
the cause of the previous camera USB disconnect.

Final handoff: startup scans finished, standby, camera online at 15 captured
FPS, prior runtime acceleration 5000 restored. No tag write or test motion
was issued. Configuration retains its stock acceleration value.
