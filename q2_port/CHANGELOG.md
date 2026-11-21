# Q2 selective port changelog

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
