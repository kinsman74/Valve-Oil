# Q2 THR FIFO patch: independent vendor-image vet

**Application-level compatibility passes against a freshly downloaded official
QIDI Q2 image. No Q2-specific instruction relocation or different application
patch is needed for this exact image. Physical flashing is not admitted by this
result. The running printer was not accessed, reset, calibrated or interrupted.**

## Independent QIDI provenance

QIDI's official Q2 firmware page published SOC 01.01.03.02, dated October 25,
2026. Its download URL supplied QD_Q2_01.01.03.02_20261023_Release.zip. The full
245,739,996-byte archive was downloaded directly with TLS verification enabled.
The archive SHA256 is:

`b42f83d0e1bbc002e62db6276c2a5739fb3343522ee071829ff8c5f56f7f2fcb`

This is a measured official-download fingerprint, not a QIDI digital signature.
The included manifest identifies the Q2 SOC and its THR member:

`QD_Q2_THR_02.02.01.08_20260303.bin`

The THR is 35,056 bytes, ZIP CRC32 9deb3c69, SHA256:

`1d34b4b0142f2a2047f08c2fae59d827bcee0adbd1563b4bd1de311dff8b2d62`

That equals both the previously cached Q2 input and the complete stock image
identity pinned by Valve Oil's Max4/Plus5 THR patch. This is full byte identity,
not an inference based on matching version numbers or similar hardware.
The original vendor ZIP and binaries remain outside Git.

## Q2-specific applicability

The QIDI dictionary identifies stm32f103xe at 72 MHz. The application's initial
stack/reset vector entries are unchanged by the patch. The captured Q2 host
configuration selects lis2dw for resonance testing, using THR PA10 chip select
and software SPI on PA5/PA7/PA6, with axes y,z,-x. No host pin or axis changes are
required or made. This configuration evidence is from our private snapshot;
it is not a new physical sensor-identification or sampling test.

The official Q2 image has the exact inverted LIS2DW FIFO decision Valve Oil
patches. At image offset 0x0bfe, bne.w becomes beq.w; at 0x0c04 the scheduler
store is replaced to keep the requested flag clear on the nonempty path. Those
two sites account for five changed instruction bytes. The corrected code wakes
the task to drain pending samples when the six-bit FIFO count is nonzero and
rearms polling when it is zero. The stock decision is reversed.

The additional changes are three identify-length instruction constants and the
recompressed dictionary containing the new version label. Every other byte is
unchanged outside the declared patch regions. Dictionary contents are identical
after normalizing the version: commands, responses, enumerations and hardware
constants remain unchanged. No heater, motor, motion or pin-mapping code is
transplanted from another printer.

Building from this fresh vendor Q2 member produces exactly our existing candidate:

`b6e39b1def0bad6c2379cad600c1284cece0c26caab77dbb659adf64d4f4172a`

## Checks performed

- Full official ZIP fingerprint and toolhead member CRC/SHA verified.
- All patch instruction/dictionary preimages and replacement bytes verified.
- Full output size/hash and identity with the previously staged candidate checked.
- Initial application vectors unchanged; no out-of-region byte changes.
- ARM execution of all 256 FIFO status bytes with two report-buffer states, on
  stock and patched images: 1,024 cases passed.
- SPI reads, sample copying, report contents/sequence, overflow accounting,
  scheduling and pending flags checked by the pinned upstream emulator.
- Actual identify handlers emulated; dictionary equivalence except version verified.
- Modified and already-patched inputs rejected; repeated raw builds identical.

The emulator stubs SPI, timer registration and host reporting. It does not measure
real sampling rate, interrupts under printer load, vibration accuracy, calibration
quality or every unrelated firmware path. The fix is a logic correction; this
analysis does not promise a measurable improvement on this particular printer.

## Remaining deployment boundaries

Valve Oil's upstream THR target map does not include Q2 SOC 01.01.03.02. Its
whole Max4 updater ZIP or installer must not be treated as a Q2 update merely
because the embedded application bytes match. Only a standalone Q2 candidate
was generated; the vendor update archive was not repacked.

Before any future flash, validate the installed application and physical
bootloader identity, Q2 UART/reset/boot entry and recovery procedure while idle.
Readback of the application was not performed during this vet. Check Q2's
handling of the patched version suffix: upstream has touchscreen version-popup
adaptations for its supported models; those must not be assumed ported to Q2.
If flashed later, input-shaper recalibration must precede bed leveling/printing,
as upstream requires. None of these physical operations was attempted here.

## Reproduce offline

Use the exact vendor archive, pinned Valve Oil 26.11.18.2 source and existing
candidate with capstone/unicorn available:

```sh
python3 q2_port/vet_q2_thr.py --qidi-archive /path/to/QD_Q2_01.01.03.02_20261023_Release.zip \
  --upstream /path/to/pinned-26.11.18.2 --candidate /path/to/q2-thr-valve-oil-fifo.bin \
  --output /path/to/new-vetting-output
```

The tool makes no network, serial, service or printer calls. It uses the existing
source locks and rejects an archive differing from this reviewed fingerprint.
On macOS, the ARM emulator needs executable-memory permission. The output binary
is local review material and is not included in Git.

Primary references: [QIDI's Q2 release page](https://www.qidimaker.com/en/downloads/firmware/Q2),
[original Klipper fix](https://github.com/Klipper3d/klipper/commit/6269dda56bb7c08263153b18715d08e2d964bcab),
[Valve Oil THR documentation](https://github.com/thelegendtubaguy/Valve-Oil/blob/v26.11.18.2/firmware/README.md).
