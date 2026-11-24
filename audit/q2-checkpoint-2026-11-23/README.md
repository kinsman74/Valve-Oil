# Verified Q2 checkpoint — November 23, 2026

## Installed and observed

Q2 QIDI SOC 01.01.03.02 with the selective Valve Oil port. Existing Q2 motion,
homing, cutting/loading flow and print macros retained; no mainstream installer
was run on the Q2. This is not a general declaration of upstream Q2 support.

Toolhead successfully flashed with the vetted FIFO fix. Full application
readback SHA256 b6e39b1def0bad6c2379cad600c1284cece0c26caab77dbb659adf64d4f4172a;
version 02.02.01.08-valve-oil.1. Bootloader unchanged, SHA256
31f8344db7b091df5429960bc9cd06065e2188c3b8092e43fb65eb3f2833723c.
Fresh pre-flash application matched QIDI stock SHA256
1d34b4b0142f2a2047f08c2fae59d827bcee0adbd1563b4bd1de311dff8b2d62.
No fallback occurred. Transaction finished successfully and cleared the pending
marker after service restoration and ready/idle checks. Physical independent
recovery was explicitly waived by the owner, not verified. The journal records
that distinction. See ../../q2_port/THR_DEPLOYMENT.md.

The new version triggered the stock QDC_100_005_005_001 touchscreen warning.
Applied the Q2-specific two-byte version-prefix fix, following upstream's
Max4/Plus5 approach. Only qidi-client restarted; no manifest/firmware rewrite.
Stock and patched executable hashes, exact offsets, rollback and validation
are in ../../q2_port/TOUCHSCREEN_POPUP.md. Thirty-six actual ARM64 cases passed;
redacted results accompany this checkpoint. No new warning occurrence in the
post-restart bounded log review. Owner confirmation of the actual LCD popup
being gone remains outstanding.

## Calibration and final health

Owner confirmed plate clear, screw tools removed and nothing loose inside.
Ran Q2 stock M901 first: saved and loaded X 2hump_ei 73.4 Hz, Y mzv 45.6 Hz.
Then bed 65 C plus five-minute soak; used the installed Q2 M4032 leveling prefix
without its redundant final shaper pass. No calibration macro source edited.
Stock Z synchronization, nozzle preparation, homing, Z alignment and full-bed
mesh completed; sensors re-enabled and heaters switched off.

Z alignment passed stock tolerance (0.044766 mm versus 0.05 mm). Saved default
mesh covers X/Y 10..260 mm, 6x6 points; range 0.295469 mm. Some probe samples
were rejected/retried, including +3/+6 mm stair-step returns at (60,60); final
accepted points excluded these. Follow-up ten-sample PROBE_ACCURACY at bed 65 C
and nozzle 140 C: range 0.021406, standard deviation 0.008008 mm, no repeated
large returns. Do not describe this as flawless probing or a perfectly flat
bed. No probe tolerances or sampling settings were changed.

Verified saved mesh equals all 36 measured points, including after normal
Klipper reload. One SAVE_CONFIG block; no unsaved changes. Final printer ready
and standby, USB Box online, all registered heater targets zero, patched THR
unchanged, Moonraker warnings and failed components empty. No heater PID,
material flow/pressure-advance or physical screw adjustment was performed.

## Recovery and private evidence

On-printer paths, also copied to private work/ on the Mac:

- /home/qidi/printer_data/.tltg_thr_firmware_backups/q2-thr-lellhiga — fresh
  stock/patched application and unchanged bootloader readbacks, transaction
  journal, transfer logs and verification.
- /home/qidi/q2-thr-preflight-20261123 — before/after pending-mesh preservation
  backups, operator acceptance, flash evidence export and health checks.
- /home/qidi/q2-touchscreen-popup-20261123 — original executable and install
  report; guarded script supports rollback.
- /home/qidi/q2-calibration-20261123 — before/after configuration, actual executed
  sequence, resonance CSVs, probe check, console and final health captures.

Both configuration archives passed SHA256 and full ZIP CRC on the Mac.
Calibration-before archive: 7ce0fa58a1eeda8ab691d9b47c933fd81ff0d5e94d228dfa224a89ad493e15c9.
Calibration-after archive: 95172fef176092d668b0f9385e54e3853da9538d6ba08483cee4a229a0bcb02c.
Fresh firmware evidence ZIP: c401ae77d2a89fafdd85e503a0048ce5f84b0fc404f40c3b3712c8dbaa35bf95.
Never publish these binaries, raw configuration or device/account identifiers.

Root flasher warning-file ownership was corrected to the Klipper account and
verified readable. Source coordinator now preserves the log-directory owner's
UID/GID for this warning on future flashes. The already-used staged coordinator
is a historical deployment artifact; use the committed source for future runs.

## Known limits and next acceptance

- Independent cold/hardware recovery remains unverified, explicitly accepted.
- Confirm the LCD version popup stays gone.
- Validate a multicolor print with actual Box tool changes on this checkpoint.
- First post-calibration print completed successfully; see acceptance result below.
- Tools-menu screw-tilt button issue remains unresolved; console and Retry had
  worked. No claim that this checkpoint fixes the menu action.
- Camera loss was pre-existing. A real frame was verified after the acceptance
  print; sustained intermittent-camera reliability remains unproven.
- Stock/mainstream Plus5 installation was reported by the owner after its
  verified stock rollback; no new Plus5 audit or changes in this Q2 session.

## Validation reproduction

Run python3 q2_port/test_thr_deploy.py (20 transaction tests).
For binary checks, install capstone, pyelftools and unicorn in an isolated
environment. Run validate_touchscreen.py with --q2-stock and --plus5-stock
pointing to private, hash-matched originals, plus --output-dir outside Git.
The harness emits validation.json and a vendor-derived patched executable;
keep that output private. It never accesses a printer. The tested streaming
deployment builder produced the same patched SHA256.

Checkpoint 20a871e was created locally. The owner subsequently requested
committing the acceptance notes and pushing the checkpoint history to their
origin fork on q2-port-readonly. No printer deployment is part of that push.
Unrelated untracked audit directories and private backups remain excluded.

## First post-calibration print acceptance

Owner reported successful completion with blotches they attributed to plate
cleanliness; no independent print-surface inspection was performed. History
confirms a completed normal job (2746.65 s active print, 2860.18 s total).
This was approximately 46 minutes of printing, not a one-layer test.

Read-only review matched log events to that print window. No toolhead/MCU
shutdown, Box/485 disconnect, probe failure or Moonraker error was found during
the job. Broad text matches were healthy 'no link errors' messages, numerical
coordinate-descent error values and a normal idle-timeout setting. Live THR
still reports 02.02.01.08-valve-oil.1 with zero retransmitted and invalid bytes;
printer ready and USB Box online.

Camera snapshot HTTP 200 produced a valid JPEG with a trailing transport NUL.
Decoded frame visually shows the actual printer interior after the completed
print. This verifies camera availability at this check, not continuous operation
or resolution of the historical intermittent problem.

Loaded input-shaper values remain X 2hump_ei 73.4 Hz / Y mzv 45.6 Hz. The print
created a pending bed_mesh kamp update, as expected from its startup sequence;
no save/reload was done during this read-only review. No printer state was
changed. Private evidence is under work/q2-postprint-2026-11-23 on the Mac and
/home/qidi/q2-postprint-20261123 on the printer; raw metadata/identifiers and
camera images are excluded from Git. This acceptance note is subsequent to
checkpoint commit 20a871e.

## Remaining closeout

The successful first print clears basic post-flash print acceptance. Remaining
checks are LCD confirmation, multicolor/tool-change acceptance, camera endurance
over several jobs and the Tools-menu screw-tilt action. No additional flash or
calibration is required by the current findings. Physical independent recovery
remains unverified and the recorded probe variation remains a known limitation.
