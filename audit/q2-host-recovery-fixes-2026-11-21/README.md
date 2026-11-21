# Host deployment/recovery review fixes

Fixes the three reproducible findings in the helper committed with e72a5d0.
The deployed Q2 host/interface payload is unchanged. Only the private saved
recovery helper and its checksum inventory are updated on the printer; the
previous helper is retained. No services, configuration, web assets, firmware or
backup originals are changed by that update.

## Findings and corrections

1. A target edit detected after services stopped made file rollback refuse the
   edit, leaving services stopped even though no installed file had been written.
   Recovery now distinguishes an unwritten transaction and restores only the
   original services, preserving late edits. This also covers partial stop failures.
2. An error-journal write failure escaped before restoration. Recovery reporting
   is now best-effort for I/O errors, including failure of stderr itself. File and
   service restoration are still attempted; recovery failure remains separately
   reported whenever a log destination is available. A log I/O failure can leave
   stale journal status, so direct file/service inspection remains necessary.
3. A motion helper labelled carry-forward passed the live loader despite changed
   bytes. Every slot-jog write target is now rejected independently by that loader.
   The normal renderer already omits the unchanged helper; it is never installed
   or replaced by a host activation package.

The unwritten/written distinction is persisted before any directory/file mutation.
Tests cover an error after an actual atomic replacement, recovery without an API
for an interrupted unwritten transaction, and existing legacy journals without
that marker. A missing marker is treated conservatively as possibly written.

## Evidence

New regressions failed before the fix: 12 tests, four failures and one error
(the slot-jog test exercises two cases). All 16 transaction tests pass afterward.
See regressions-before.log and regressions-after.log. These are local files and
stand-in services, not deliberate live failures or a physical rollback.

Ruff and Python 3.9 syntax checks pass. The saved helper's prior hash must match
before it is replaced. The entire saved package inventory is then verified, and
all 328 installed target hashes are compared before/after the helper update.
See helper-update.json for the receipt. No controller or service restart is
needed to update this saved code.

The running Q2 was healthy during review. These changes strengthen future
activation/recovery handling; they do not imply the prior deployment failed.
Power-loss qualification and deliberate live rollback remain outside this work.
Archived preview artifacts are historical and are not silently rewritten.
