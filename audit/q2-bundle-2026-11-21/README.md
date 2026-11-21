# Audit revision 2026.11.21-audit2

Supersedes the November 20 preview for further testing. No live printer changes,
restarts, movement or flashes were performed. This revision changes only the
selective offline Q2 tools; the upstream general installer/package version is
unchanged and must not be treated as a Q2 installer.

## Bugs corrected

- Dynamic config/nginx/catalog operations could treat unrelated target edits as
  idempotent. All operations now record expected result hashes and check current
  bytes against the captured before/after states before rendering. A regression
  test demonstrated the nginx bypass before this fix.
- Builders previously recorded a pinned upstream commit without validating their
  actual supplied sources. Content locks now verify upstream Python, workspace
  adaptations/web assets and the Q2 adapter before imports/builds. Unexpected
  Python/static asset inventories and symlinks are rejected. Locks are not signatures.
- Scope was described/tested but insufficiently enforced at runtime. A shared
  explicit target/section policy rejects out-of-scope module operations, even
  with regenerated checksums. Existing slot-jog must match exactly; absent
  slot-jog is not newly installed.
- Firmware admission used assertions that optimized Python could remove. Explicit
  identities are now enforced; builders and emulator refuse optimized execution
  where imported legacy code still relies on assertions.
- Added status metadata operation, preserving unrelated fields and rejecting a
  different printer. The private snapshot includes the existing metadata.
- Standalone planner imported a bundled module and created a cache file, then
  rejected its own inventory on subsequent use. Bytecode writes are disabled
  before bundled imports. Extracted planner checked twice without modifying files.
- Temporary outputs are published only after assembly/build success. Nested output
  overlap is refused. Firmware identity is checked independently of package sums.
- Removed dense one-line code/unused imports and corrected missing source-reference
  handling. Ruff formatting/lint and Git whitespace checks pass.

## Claims corrected

The old rollback check was a file-copy simulation, not proof of installer or
physical recovery. Add-on/OS recipes are reference source, not working complete
Q2 integrations. Source-only packaging is not a standalone reproducible checkout;
it needs the locked development workspace and external vendor/private inputs.
Cached model/firmware metadata is not physical board admission. Configuration
preservation is byte-level, not calibration validation. deployment_ready=false.

## Validation

The final read-only plan covers 298 targets: 258 creates, 6 replacements and
34 unchanged files. No guarded Moonraker source transforms rejected the snapshot.
One additional unchanged target is the captured status metadata.

See bundle-tests.log for 16 passing audit tests, firmware-emulation.log for the rerun
of 1024 THR FIFO cases, identify consistency and two Box calibration reads.
Box and THR images reproduce the previously recorded candidate SHA256 values.
The extracted full archive independently produced the same plan twice.
Historical November 20 logs remain available and are not represented as new
physical testing. Private snapshots and vendor firmware are not committed here.

## Still open

No real installer, ownership/service activation validation, nginx-on-target check,
power-loss recovery, physical temperature test or new THR flash qualification.
Repeated historical SAVE_CONFIG markers remain preserved and unresolved.
Physical blank-tag writing remains unvalidated by this build. The pre-existing
camera fault is separate. Movement/macro optimizations remain excluded.

Full build instructions and limitations: ../../q2_port/README.md.
Local archive names and hashes: archives.json. Full firmware archive is private
local test material, not a public redistribution release.
