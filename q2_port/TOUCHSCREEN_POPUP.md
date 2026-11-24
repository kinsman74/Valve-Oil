# Q2 toolhead firmware-version popup

The Q2 01.01.03.02 touchscreen compares board version strings for exact equality
with the installed QIDI firmware manifest. A correctly flashed THR reporting
02.02.01.08-valve-oil.1 therefore raises QDC_100_005_005_001 against the
manifest value 02.02.01.08. This is a board-version popup, not proof of a new
online SOC release. Stock update actions can replace patched board firmware.

This Q2-only adaptation follows the reviewed upstream
installer/runtime/qidiclient_firmware_popup.py prefix-comparison fix. It does
not change upstream supported-printer declarations, any firmware manifest,
board firmware, printer configuration or motion.

## Reviewed executable

- Size: 91,597,520 bytes.
- Stock SHA256: c222bb9c77df6fe714e974f915834841be96c291bb75d44cd6f4d371e174f423.
- Patched SHA256: efc4f97012ce2ce1f90d54cf7bfec616907a7f48e33fe892b51aa90712bcee76.
- File offsets: 0x227078 (show check), 0x227220 (clear check).
- Instructions: 40020054 (b.eq) becomes 49020054 (b.ls). Exactly two bytes differ.

The complete length-check/compare/result sequences match the reviewed Plus5
executable instruction for instruction except external call relocation targets.
Q2 checks are relocated from Plus5 offsets 0x226518 and 0x2266c0. ELF dynamic
relocation identifies the comparison call as memcmp. The reported version is
the first copied string; the manifest is the second, and its length is the
memcmp bound. The new unsigned length condition permits a reported version
starting with the entire manifest string, as upstream does. It is a prefix
comparison, not semantic version ordering or an arbitrary warning suppression.

Executed 36 actual ARM64 check cases (stock/patched, show/clear, nine version
pairs) in Unicorn: exact matches, patched suffix, mainboard unchanged, other
mainboard version, truncated version, wrong prefix, older toolhead version,
other suffix, empty report. Verified exactly two changed bytes and expected
results. Validated the deployment script streaming builder against the emulated
candidate hash. Binary inputs, full validation report and stock copy remain
private under work/q2-touchscreen-popup-2026-11-23; do not publish binaries.

## Install and rollback

q2_port/touchscreen_popup.py accepts check, apply or rollback through authorized
system-service execution. It refuses unknown executable hashes, the wrong Q2
SOC, active printing/paused work, heaters, Box tool changes, RFID jobs and
unsaved configuration. It checks idle state again after staging the candidate.
It preserves ownership and modes, verifies output hashes, uses atomic rename
and restarts only qidi-client.service. A failure after replacement restores
exact stock bytes and attempts to restore the service.

Private on-printer backup: /home/qidi/q2-touchscreen-popup-20261123/qidiclient.stock.
For rollback while ready/idle with heaters off, run the staged script with
rollback rather than apply through the same authorized system-service method.
Rollback restores the touchscreen executable only; the patched toolhead remains.
A later unknown touchscreen executable is never overwritten by this tool.

This patch has no board-flashing capability and performs no motion, homing or
Klipper restart. Physical confirmation that the popup clears remains part of
acceptance; backend ready state alone does not prove what the screen displays.

## November 23 deployment

Applied successfully through q2-popup-apply-20261123 (exit 0, 16.774 s). Installed
hash matched the reviewed output. Touchscreen, Klipper and Moonraker services
were active afterward; printer ready/standby, Box online, THR still
02.02.01.08-valve-oil.1. Bounded Moonraker review found only the original
17:46:19 alert and no new occurrence after this touchscreen restart.
Physical touchscreen dismissal/absence remains owner confirmation.
