# Q2 Box RFID port checkpoint, 2026-11-19

Experimental Q2 adaptation of Valve Oil 26.11.15.1, upstream commit
4703fc20f372b7d31e5a47d5a2d06b7a495c43c1. This is a source and evidence
checkpoint, not a supported Q2 installer. Q2 hardware, motion, calibration,
mainboard and toolhead firmware remain stock.

## Deployed and verified

The Box application was flashed and read back byte for byte. Output SHA-256:
50e1b2d76a64d3ef7a0c8f79eb4a84be9eafd93cb0912e55d994c8245d93f903.
The captured bootloader remained unchanged. The host modules in src match
those installed on the Q2, verified by SHA-256 on November 19.

The upstream reader/catalog modules are unchanged from the pinned commit.
The Q2-specific C handlers provide select/transceive using verified Q2
addresses. Our additional host guard rejects empty and malformed successes,
requires stock matching confirmation, and quarantines conflicting payloads
until the existing scan deadline. No automatic second scan is added.

After removing a spool carrying conflicting OEM and TinkerBarn tags, all
four slots accepted Anycubic OEM tags within single operator scan requests:

| Slot | Catalog ID | Material | RGB |
| --- | --- | --- | --- |
| 1 | QFX22 | Anycubic PLA | E9E9E7 |
| 2 | QFX11 | Anycubic PETG | 003594 |
| 3 | QFX22 | Anycubic PLA | 0067B9 |
| 4 | QFX22 | Anycubic PLA | F2A900 |

Each accepted scan had two matching valid replies, no conflict, and no final
timeout. Internal unsuccessful polls preceded acceptance; first-shot means
one operator request, not one RF transaction. Slot 2 also passed a repeat
scan. Genuine QIDI factory tags, Elegoo and Bambu acceptance remain unverified
in this deployment. Studio mapping of this four-spool lineup remains pending.
The recurring `Can not find 485 device` message is still present.

## Latest upstream comparison

Compared against Valve Oil 26.11.18.1, main commit
fea34e996f1ab64c646dd02846d1bb47ad93c272 (November 18).
Upstream adds Box tag writing with readback verification, Creality/TigerTag/
OpenTag3D reading, 34 Creality catalog entries, broader fallback, improved
full-memory reports and reselection, and VO_BOX_RFID_TEST diagnostics.
Its Fluidd build is v1.37.7-tltg-32e13db. Our Q2 dashboard is the earlier
v1.37.7-tltg-f4f1ba3 adaptation. New host features have NOT been installed.

No files under upstream firmware/, nor build_box_firmware.py or
flash_box_firmware.py, changed between these commits. New RFID features use
the existing select/transceive protocol. Host-only migration is plausible,
but requires Q2 integration tests, especially writes and reader timing.
Keep our guard while evaluating the newer reader. Do not infer write safety
from successful reads.

Other newer upstream changes include SAVE_CONFIG storage durability,
external-spool loading/start fixes, cold-cut recovery, USB installation,
ZeroTier, update windows and chamber-light handling. These are not included
by this checkpoint. The storage durability fix addresses interaction with
Valve Oil OS storage optimization; the Q2 has not received that optimization.
Do not copy another printer's cutter coordinates or shutdown patch. Q2's
shutdown path differs; synthetic qualification found no reason to apply the
upstream MCB-specific shutdown patch.

## Reproduction and evidence

Provide your own exact Q2 stock application named
QD_Q2_BOX_02.03.01.13_20251127.bin in this directory. Required SHA-256:
c09aa5e0a07161f197c597571d96a48ac1cfb3f19a3758576b3428547a424ba9.
Vendor binaries, full device backups, credentials and hardware identifiers
are intentionally excluded. Source retains the repository license/notices;
QIDI firmware remains QIDI's property.

With Python zopfli and clang supporting Thumb, run `python3 build.py`, then
`python3 test_port.py`. ARM emulation additionally requires unicorn;
`emulate_handlers.py` and `test_shutdown_q2.py` use simulated helpers.
Recorded qualification: 8 handler cases, 3 image/guard tests, 8 prior guard
regressions, 6 upstream RFID cases, 8 isolated compiled-reader combinations,
30 synthetic shutdown scenarios and 7 bootloader transfer/recovery cases.
Not all harnesses are standalone in this checkpoint. Synthetic tests do not
establish physical write behavior or electrical fault recovery.

Before any future flash: capture the installed application/bootloader,
qualify recovery, require an idle printer with zero heater targets and no
Box tasks, and verify full readback before restarting services. The original
application and host-module backups are retained privately on the device
and in the local work archive. This checkpoint is not an unattended deployment
or rollback command; recovery must use those exact verified artifacts.
