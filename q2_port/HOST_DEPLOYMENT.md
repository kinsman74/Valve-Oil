# Per-device Q2 host deployment

This helper activates only a rendered, hash-admitted Q2 host/interface package.
It never flashes firmware, issues G-code, homes or reboots the printer. It is
not the general Valve Oil installer and is qualified only against this project's
captured Q2 SOC 01.01.03.02 setup. Physical print/tag-writing and power-loss tests
are separate from host activation acceptance.

1. Wait for an idle printer, no paused print, all heater targets zero and no Box
   flow/RFID task. Capture current target files privately in the snapshot layout
   required by plan.py. Keep config contents, machine identifiers and backups out
   of Git. Check the active include graph and boot path read-only.
2. Plan against the snapshot. Review drift instead of overwriting it. Reassembly
   from current data is appropriate only after each difference is understood;
   preserve newer calibration and do not normalize unknown owner edits away.
3. Build a host-only package locally:

   ```sh
   python3 q2_port/render_host.py --bundle /path/to/admitted-preview \
     --snapshot /path/to/private-current-snapshot --output /path/to/new-host-package
   ```

   The renderer runs the strict planner first, includes only changed host/web
   files, and transfers no firmware images. A rendered package contains private
   printer configuration. Store/upload it in a private directory.
4. Verify the uploaded inventory and current target preimages. Use only known,
   verified administrator authorization. On the tested Q2, the existing qidi
   account's system-service policy permits the following; qidi does not have sudo.
   Do not assume that policy or try guessed account passwords on another printer.

   ```sh
   systemd-run --no-ask-password --wait --collect --unit=q2-host-apply \
     /usr/bin/python3 -B /private/package/host_deploy.py apply \
     --package /private/package
   ```

   This rechecks admission, records backups and a journal, stops nginx/QIDI client/
   Moonraker/Klipper, rechecks hashes, replaces files atomically, validates nginx,
   starts the original services and waits for ready state. All preimages are
   stored before installed-file writes. Existing ownership/modes are preserved;
   new files inherit the nearest existing directory's owner and use mode 0644.
   Do not begin a print or operate the Box during this maintenance window.
5. Independently verify installed hashes/permissions, printer ready state, heater
   targets, service activity, interface versions and disabled updater actions.
   Confirm backups and record acceptance without committing private contents.

## Rollback

Keep the private package directory, journal.json and before/ backups. Do not
edit the journal or delete backups. While the printer is idle, invoke the same
verified service authorization with a fresh unit name:

```sh
systemd-run --no-ask-password --wait --collect --unit=q2-host-rollback \
  /usr/bin/python3 -B /private/package/host_deploy.py rollback \
  --package /private/package
```

Rollback verifies every original backup and refuses targets that match neither
recorded before nor installed states. It restores original metadata, removes
only known new files and empty created directories, validates nginx and returns
services to ready. It does not overwrite later calibration/owner edits blindly.
If those edits are present, review them first. Offline recovery is admitted only
for an interrupted maintenance transaction with Klipper stopped; the helper does
not assume an unavailable API means a running printer is idle.

Run test_host_deploy.py locally for the transaction regressions. Those tests use
stand-in files/services, not a physical rollback or a power-cut qualification.
