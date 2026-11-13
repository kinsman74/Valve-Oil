# Q2 Box replay for Valve Oil Fluidd

The Q2 port branch starts at Valve Oil `384a2934ec452f2e22dba9b987310dada428bb12` (26.11.12.1). Its pinned Fluidd release is `v1.37.7-tltg-0e6d94d`, commit `0e6d94db9a60d17454b0508b9e8eac976ba75171`. The installer, bundle builder and flash entry points retain the local audit guards. The compatibility candidate lives in this audit directory and can be applied to the pinned Fluidd source in an offline test.

## Reproduce

With Node.js 24 and a local Fluidd checkout at the pinned commit, run:

```sh
node audit/q2-fluidd/replay.cjs /path/to/valve-oil-fluidd
```

The replay runs the upstream TypeScript slot reader, status merge and slot-edit handler. It applies the candidate only to a temporary copy of the utility and captures would-send G-code in memory. It checks the input revision and uses no printer endpoints. This is a focused source replay with Vue state stubs. See the live acceptance below for the full build and owner test.

## Findings

- The saved Q2 status includes flat keys like `multi_color_controller.box.box0_filament_info_1_filament_type`. In the fixture, the upstream slot getter falls through to the numeric lookup for this shape. It retains QFZ07 from saved variables, but omits the resolved name and type. The candidate keeps native array precedence and adds the flat controller record as a fallback before numeric lookup.
- The candidate renders Soleyin / PETG Basic Black / PETG / #060606 from the replay fixture. It also picks up the controller's read-state flag when the stepper read state is missing. Existing stepper presence handling remains in use. The fixture contains no stepper presence events, so presence and tool mapping need later evidence.
- The actual upstream Vuex status merge preserves other slots on a partial controller update. The actual edit handler emits string filament IDs and hex lists through SAVE_VARIABLE, matching the syntax in our deployed Q2 Fluidd patch. The replay captures the command only and checks the busy guard.
- The replacement scenario retains eSUN after a scan ends without a new accepted identity. The later accepted Anycubic event changes the rendered identity. A UI compatibility fallback cannot distinguish a replacement timeout from other cases when the controller gives it the same state. The Q2 lifecycle fix still needs a reliable replacement event.

## Fixture provenance

The flat fields are selected from the October 30 Q2 follow-up status capture. The final Pearl Black record uses its captured QFY10 identity. The earlier eSUN identity and scan start/end deltas reconstruct the logged transition, since the intermediate socket packets were not captured. The Soleyin slot overlays the known QFZ07 ID, type-first label and black color onto the saved shape. Its QFZ08 edit target comes from the revised native Q2 catalog. The native-array precedence and numeric fallback cases are synthetic. No private logs, account identifiers or network addresses are included.

## Live Q2 acceptance

The owner changed slot 1B from black to red in the Valve Oil Fluidd preview, restored black, and selected Reprint on the Q2 touchscreen. The touchscreen mapped the saved job to the correct filament. This records the owner-confirmed edit and reprint mapping for Soleyin PETG Basic Black. Print completion was outside this check.

## Next acceptance check for spool replacement

Capture two separate operator actions with the printer idle. First retract/eject filament and reinsert it with the same spool still in place. Then physically remove a spool and insert a different known tagged spool in the same slot. Run a fresh capture for each action and note when the spool is lifted and seated. Wait for the first scan to finish before pressing any reset or reread controls.

Run `python3 -B audit/q2-fluidd/capture-slot.py http://PRINTER --slot 1 --seconds 90` for 1B. The recorder uses GET requests and emits changes in controller presence fields, inlet sensor, scan flags, saved identity and reader outcome. At the live idle baseline, 1B had saved and live QFZ07, with controller box_inserted=1, filament_inserted=0 and stepper runout_button=0. One idle sample cannot establish what each field does during physical removal. A replacement guard needs the two contrasting traces before it can safely clear a slot or schedule another scan.

### Slot 1B comparison result

Both trials produced the same inlet transitions: controller `box_inserted` went 1 → 0 → 1, stepper `runout_button` went 0 → 1 → 0, and `filament_inserted` stayed 0. The saved and live Soleyin ID stayed QFZ07 throughout. These fields cannot distinguish the same-spool test from the swap in this capture.

The same-spool scan timed out with 100 failed polls and zero valid reads. The replacement Anycubic PETG Blue spool had only its factory Anycubic tag, as the owner clarified afterward. The Q2 under test uses stock Box firmware and our TinkerBarn response adapter. The first scan after the swap timed out with 89 failed polls, 11 empty responses and zero valid reads. This trial shows stale identity after a swap to a spool whose tag this setup does not decode. It cannot measure recognition or retry behavior for a supported replacement tag. Both generated a reader outcome even though the sampled public read flags stayed zero. The old identity after the swap is therefore a failed acceptance, not evidence of a missing scan. A further offline candidate can show an unverified assignment on a fresh failed scan while retaining the last saved ID. A reliable physical replacement trigger remains unverified.

### Supported-format replacement trial

The owner wrote and applied TinkerBarn tags to both spools. A manual reread of Anycubic PETG Blue in 1B accepted two valid responses after four empty responses and 22 failed polls. It saved QFY14, PETG, #1353AB. This verified the starting assignment and the Anycubic tag.

During the subsequent monitored swap from Anycubic Blue to the newly tagged Soleyin PETG Basic Black, 1B went from inserted to empty to inserted. The automatic read finished about 31 seconds after insertion with 100 failed polls and zero valid reads. The saved and live ID both stayed QFY14. This reproduces the stale assignment after a replacement with a supported tag format. The new Soleyin tag still needs a successful read to establish that it is readable from that slot. The capture alone cannot distinguish tag placement, write quality or the reader path.

### Owner clarification on prior assignments

The owner clarified that the original identities on these spools were selected manually. The spools did not have TinkerBarn tags during the original same-spool and factory-only swap trials. A saved or displayed filament ID in those trials is evidence of a slot assignment, not a previously successful tag read. The original timeouts cannot be used to assess reliability with a known-good tag.

The later Anycubic reread after tag writing remains a verified RFID result: the recorder saw two valid responses and the live and saved identity change from QFZ07 to QFY14. For the later Soleyin swap, the recorder establishes a timeout and retention of QFY14. No successful read of the replacement Soleyin tag was captured, so the old manual QFZ07 assignment cannot establish that the tag worked or that the automatic read missed a known-good tag.

### Automatic Soleyin Black read after tagging

A later insertion started with 1B empty and the previous Anycubic Blue ID QFY14 still saved. The owner inserted the newly tagged Soleyin PETG Basic Black. About two seconds after the inlet detected insertion, the recorder observed two valid reads, six failed polls, zero empty responses, and a completed scan. The live and saved IDs both changed to QFZ07 with type PETG. This confirms the supported tag can be read automatically in 1B and replace the prior assignment. The earlier timeout with the same reported product remains a separate unsuccessful attempt.

### Offline RFID warning prototype

The warning prototype flags an occupied slot after an observed inlet cycle and a newly observed timeout or conflict while retaining the saved identity. Replay passed on the recorded timeout and successful Soleyin insertion, with additional checks for an empty inlet, a changed identity and a historical result on dashboard open. Run `node test-rfid-verification.cjs TIMEOUT_TRACE SUCCESS_TRACE` from this directory.

The current guard exposes summary counts without a scan sequence or an explicit acceptance result. Two scans with identical summaries look the same, and stock-reader-completed alone cannot establish that a slot assignment was accepted. Before UI integration, expose a per-scan sequence and acceptance evidence so repeated failures can be detected and a confirmed reread of the same ID can clear a warning. This prototype makes no printer changes.

### Scan reporting candidate

The toolkit's staged read guard v2 assigns each scan a unique ID across guard instances. It records an accepted filament ID when the stock reader emits the captured success message for that same slot. The replay now uses the scan ID for freshness and clears the warning after a confirmed same-ID reread. Reconstructed historical samples carry synthetic IDs. Separate replay assertions cover identical timeout summaries with different IDs and same-ID acceptance.

The acceptance observer is covered by mock-reader tests. Live Q2 still runs v1. Verify v2 against the isolated compiled reader before activation and use its live status when integrating the warning into Fluidd.

### Guard v2 and warning preview deployment

The isolated stock reader passed all eight cases, including matching accepted IDs to the stock save calls and distinct scan IDs. The Q2 then loaded guard v2 after a Klipper service restart. A live 1B scan reported accepted ID QFZ07. The separate warning preview passed 46 upstream Box tests and its served HTML matched the built artifact. The warning display and clearance were exercised in offline replay. A live timeout demonstration in the new preview is pending.

To reproduce the preview, apply flat-controller.patch and warning-preview.patch with git apply --unidiff-zero to the pinned Fluidd checkout, then copy qidi-rfid-verification.ts into src/util and build. The preview adds the warning to the Box card, using guard v2 scan events. Its PWA plugin is disabled.

### Warning after opening or refreshing the preview

The live untagged Soleyin White test in 1B recorded 100 failed polls, zero valid responses and no accepted ID. The slot remained occupied with QFZ07 saved. A direct Moonraker WebSocket subscription returned the failure and retained assignment in its initial snapshot. Preview v2 intentionally ignored that initial result, so refreshing did not display the warning.

The follow-up build warns on the initial snapshot when the Box is online, the inlet is occupied, a saved ID is present and the latest identified scan timed out or found conflicting tags. The banner describes the last read so it does not imply that the page observed a swap. The capture replay and refresh tests pass against the same TypeScript module used by the build. The follow-up build was deployed to the separate preview. The served index and dashboard bundle matched the local build by SHA-256. The previous preview directory was moved outside the web root for rollback. The owner confirmed that the banner appeared after refreshing with untagged Soleyin PETG White in 1B. After the tagged Soleyin PETG Black was reinserted, the guard recorded a new scan with two valid responses and accepted the same saved ID, QFZ07. The owner confirmed that the banner cleared on its own. This completes the live timeout and same-ID recovery test on the Q2 preview.

### Live Anycubic swap and Studio sync

With the preview open, the owner replaced tagged Soleyin PETG Black in 1B with tagged Anycubic PETG Blue. The touchscreen and preview updated on insertion. The Q2 reported two valid responses and accepted QFY14, replacing QFZ07 in both live slot state and saved variables. The installed Q2 0.4 mm preset carries QFY14, and the owner confirmed that live Box sync in QIDI Studio resolved to the custom Anycubic PETG Blue preset.
