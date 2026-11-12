# Q2 Box replay for Valve Oil Fluidd

The Q2 port branch starts at Valve Oil `384a2934ec452f2e22dba9b987310dada428bb12` (26.11.12.1). Its pinned Fluidd release is `v1.37.7-tltg-0e6d94d`, commit `0e6d94db9a60d17454b0508b9e8eac976ba75171`. The installer, bundle builder and flash entry points retain the local audit guards. The compatibility candidate lives in this audit directory and can be applied to the pinned Fluidd source in an offline test.

## Reproduce

With Node.js 24 and a local Fluidd checkout at the pinned commit, run:

```sh
node audit/q2-fluidd/replay.cjs /path/to/valve-oil-fluidd
```

The replay runs the upstream TypeScript slot reader, status merge and slot-edit handler. It applies the candidate only to a temporary copy of the utility and captures would-send G-code in memory. It checks the input revision and uses no printer endpoints. This is a focused source replay with Vue state stubs. A full Fluidd build, complete Q2 Moonraker subscription and actual slot edit remain hardware acceptance work.

## Findings

- The saved Q2 status includes flat keys like `multi_color_controller.box.box0_filament_info_1_filament_type`. In the fixture, the upstream slot getter falls through to the numeric lookup for this shape. It retains QFZ07 from saved variables, but omits the resolved name and type. The candidate keeps native array precedence and adds the flat controller record as a fallback before numeric lookup.
- The candidate renders Soleyin / PETG Basic Black / PETG / #060606 from the replay fixture. It also picks up the controller's read-state flag when the stepper read state is missing. Existing stepper presence handling remains in use. The fixture contains no stepper presence events, so presence and tool mapping need later evidence.
- The actual upstream Vuex status merge preserves other slots on a partial controller update. The actual edit handler emits string filament IDs and hex lists through SAVE_VARIABLE, matching the syntax in our deployed Q2 Fluidd patch. The replay captures the command only and checks the busy guard.
- The replacement scenario retains eSUN after a scan ends without a new accepted identity. The later accepted Anycubic event changes the rendered identity. A UI compatibility fallback cannot distinguish a replacement timeout from other cases when the controller gives it the same state. The Q2 lifecycle fix still needs a reliable replacement event.

## Fixture provenance

The flat fields are selected from the October 30 Q2 follow-up status capture. The final Pearl Black record uses its captured QFY10 identity. The earlier eSUN identity and scan start/end deltas reconstruct the logged transition, since the intermediate socket packets were not captured. The Soleyin slot overlays the known QFZ07 ID, type-first label and black color onto the saved shape. Its QFZ08 edit target comes from the revised native Q2 catalog. The native-array precedence and numeric fallback cases are synthetic. No private logs, account identifiers or network addresses are included.
