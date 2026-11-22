# Q2 toolhead methods checkpoint, November 22, 2026

Implemented a separate Q2-only coordinator around unchanged, hash-pinned Valve
Oil 26.11.18.2 THR tools. See ../../q2_port/THR_DEPLOYMENT.md for operation,
recovery, limits and source adaptation. Existing preview2 archives are unchanged.

The coordinator adds service/transaction handling on this Q2, whose qidi account
uses the established system-service authorization rather than sudo. It admits
only SOC 01.01.03.02 and the exact captured recoverable SECOND bootloader. The
manifest changes only Q2 target selection and official-image provenance. No
upstream protocol, retry behavior, erased range, reset sequence or firmware byte
is changed. No mainboard or Box flashing, motion, homing, heater or calibration
command is included.

Local transaction coverage: 19 tests passed. Source, manifest target and image
tampering were rejected; coordinator syntax was checked for Python 3.9. The final
private package was uploaded and its inventory and file-only dry-run verified on
the Q2. No apply operation was run. The example recovery record remains false.

The Q2's actual stock application and recoverable bootloader were read back,
admitted, copied privately to the Mac, non-erasing-probed, then read back again.
Application and bootloader were unchanged. Captured-code transfer emulation
passed. The physical report here contains MCU-class registers, not the MCU UID;
no board firmware or private printer configuration is committed.

Q2 health after the calibration repair: one readable SAVE_CONFIG block; existing
saved X zv 46 Hz and Y mzv 43.4 Hz loaded; latest saved mesh retained; six port
services active; ready/idle; heater targets zero; camera snapshot was a valid
JPEG. Previous stale USB-ID and QIDILink launchers were condition-guarded with
backups. Rockchip/LightDM base-OS failures remain separate; they were not repaired
by this workflow. The intermittent camera fault is not claimed fixed.

The implemented recovery-to-stock mode covers supported communication/session
failures. It does not demonstrate recovery after power loss, process termination,
or cold boot into a partially written application. Independent recovery entry
remains unverified, so the new apply path refuses before touching services/UART
unless a truthful recovery-evidence record is supplied. Do not fabricate it.

Firmware programmed: no. Toolhead remains QIDI 02.02.01.08. No additional reboot
or movement is part of staging this coordinator. Private archives and physical
bootloader/application dumps stay outside Git; artifact.json records the archive
fingerprint. No push is part of this checkpoint.

## Full recovery fault injection

The unchanged upstream check_thr_recovery.py completed successfully against the
captured Q2 bootloader: 233 recovering-transfer simulations across five clock
rates, plus 133 plain-transfer comparisons. Recovering mode produced no cases
classified by the harness as avoidably unusable. At nominal clock speed, 20
outages exceeded the modeled rescue window and left the simulated application
unusable. Passing this suite therefore does not eliminate the independent
recovery-entry requirement. These are emulated results, not physical flash or
power-loss tests. See captured-bootloader-recovery-check.json and
validation-summary.json for the complete outcome counts.
