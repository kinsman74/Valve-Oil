# Q2 touchscreen mirroring, 2026-11-20

Completed the missing backend for the newer Fluidd Printer screen card.
Source: Valve Oil fea34e996f1ab64c646dd02846d1bb47ad93c272,
installer/system/tltg_remote_screen.py. Server source and systemd unit are
unchanged upstream; only the screen routes from upstream remote_screen.py
were included, avoiding routes for uninstalled add-on/status services.

Read-only Q2 framebuffer capture passed: 480x272 BGRX, JPEG 19969 bytes.
A real external websocket through nginx returned HTTP 101, hello width480
height272 touch=true, then a valid JPEG frame. The frame was visually
reviewed and shows the normal ready touchscreen in the correct orientation.
No touch events were sent. Fluidd starts in view-only mode; deliberately
enabling control permits real touchscreen presses.

Installed server /usr/local/lib/tltg_remote_screen.py and
/etc/systemd/system/tltg-remote-screen.service. Listens only on 127.0.0.1:7130.
Proxy routes retain Moonraker authorization, with one-shot-token or trusted
client access. Unit uses qidi plus video/input supplementary groups and the
upstream CPU/resource restrictions. nginx configuration test passed; only
nginx was reloaded. Printer and camera services were not restarted.

Original nginx configuration and installed hashes are saved privately on
the printer with a guarded rollback script. Rollback refuses changed
installed files, disables the mirror service, restores original routing,
tests nginx and reloads it. Scripts here require their associated private
installation manifest/backups and are not a standalone public installer.

Camera remains online and its temporary camera-only power/control=on trial
was preserved. No reboot, homing, printer configuration change, calibration
or motion commands were used for this installation.

Other previously withheld items include configuration-save reliability and
external-spool loading recovery. They are separate from screen mirroring and
were not silently bundled into this change; scope clarification requested.
