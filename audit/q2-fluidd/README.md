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
