# Q2 selective port changelog

## 2026.11.22 Q2 screw-tilt homing correction

- Add the missing conditional G28 wrapper around SCREWS_TILT_CALCULATE.
  Home through the existing QIDI routine only when XYZ are not already homed.
- Preserve native command parameters, published screw settings and all saved
  calibration. No chamber-heater changes or M4031 routine are added.
- Validate unhomed, partly homed and homed template branches without movement.

## 2026.11.22 Q2 screw-tilt enablement

- Add the published community Q2 screw-tilt configuration as an optional separate
  include, enabling SCREWS_TILT_CALCULATE and its interface control.
- Save and preserve a pending default mesh before the idle-only activation.
  Retain input shaper and one valid saved-calibration block.
- Verify loaded settings, command availability and ready state without probing
  or movement. Record private backups and rollback instructions.

## 2026.11.22-thr-preview1

- Add a separate Q2-only coordinator around pinned Valve Oil toolhead methods:
  fresh backups, exact bootloader/application admission, recovery-to-stock,
  durable pending state, full readback and original service restoration.
- Bind the Q2 manifest and upstream source identities; keep protocol and image
  bytes unchanged. Require documented independent recovery entry before erase.
- Add transaction regression coverage and operator/recovery instructions.
- Preserve motion/configuration files and saved calibration. Stage only; no
  physical firmware flash is claimed. Existing preview2 archives are unchanged.

## 2026.11.21-stable2-preview2

- Bundle the freshly QIDI-vetted toolhead candidate and matching original stock
  reference, with verification evidence and explicit pending physical admission.
- Advance the bundle to schema 3 and bind images/report/readiness independently
  of the package checksum inventory. Automatic flashing remains disabled.
- Include the reviewed host renderer and corrected recovery helper with its
  regression coverage. Preserve existing host/UI payloads and motion exclusions.
- Use an offline reconstruction of the last verified deployed state for planning;
  no running-printer capture, upload, reset, calibration or flash is performed.
- Keep firmware-containing archives local; commit source, evidence and artifact
  hashes for the next push. Existing archived builds remain unchanged.

## 2026.11.21 recovery guard fixes

- Recover original service operation without overwriting late owner edits when
  shutdown/drift detection fails before any installed-file mutation. Persist a
  write marker before mutations so interrupted recovery takes the correct path.
- Journal/error-log I/O failure no longer blocks file or service restoration.
- Reject every slot-jog write in the live host loader, even when labelled as an
  unchanged carry-forward. Existing journals without the new marker still work.
- Add regressions for all three findings, partial stops, interrupted recovery and
  legacy journal compatibility. All 16 transaction tests pass. Update only the
  saved Q2 recovery helper and inventory; no service restart or runtime changes.

## 2026.11.21 host activation

Add a separate host-only renderer and guarded activation/recovery helper, with
eight local transaction tests. Deployed the existing stable2-preview1 payload
on the Q2, preserving newer calibration, verifying all targets/permissions and
backups, and confirming ready services and authenticated screen streaming. No
firmware, reboot, homing or optimized motion changes. This does not revise the
archived preview binaries or qualify a universal installer.

## 2026.11.21-stable2-preview1

Offline refresh against stable Valve Oil 26.11.18.2 (aa42eaa3), with the
release-pinned Fluidd e85f13b. No printer deployment or firmware flash.

- Backport Box monitor identifier-masking and report-start fixes while retaining
  deployed command/settings/log identities. Enforce the Box link log size limit
  after writes rather than only at startup.
- Build the newer companion UI, including camera layout/fullscreen and numeric
  command formatting fixes, while preserving Q2 slot decoding.
- Retain existing manual jog behavior, disable new companion calibration actions,
  and retain Fluidd's previous toolhead card to exclude new automatic homing.
- Preserve the Q2 blocked-updater boundary and existing RFID protections.
- Refresh upstream recovery reference sources and boot-recovery documentation.
  Add recovery prerequisites to the future activation checklist; no general
  recovery installer, filesystem repair or OS package change is enabled.
- Pin updated sources and supply repeatable Q2 compatibility staging recipes.
- Keep Box/THR candidate bytes unchanged; THR remains unflashed and unqualified
  for physical deployment. All motion and optimized print macros remain excluded.

## 2026.11.21-audit2

Harden offline source/firmware identity checks, scope enforcement, target drift
rejection and standalone package verification. Correct rollback and deployment
claims; retain historical evidence. Based on stable Valve Oil 26.11.18.1.
