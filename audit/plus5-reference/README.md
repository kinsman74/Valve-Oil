# Valve Oil Plus5 reference for the Q2 port

Reviewed November 12, 2026. Valve Oil main `384a2934ec452f2e22dba9b987310dada428bb12` ships package `26.11.12.1`. The fetched dev tip is `2821fe60910f682131379cf62a98d89017738a1e`. Plus5 support first shipped in `26.11.11.1` for QIDI firmware `01.01.02.01`. Subsequent releases raised probe travel speed, delayed startup RFID until the Box was ready, addressed a cloud handshake blocking Moonraker, capped resonance-test acceleration on Plus5 and corrected update-time Klipper activation. The Q2 audit branch retains its read-only guards and separate baseline. [Upstream release history](https://github.com/thelegendtubaguy/Valve-Oil/blob/384a2934ec452f2e22dba9b987310dada428bb12/CHANGELOG.md)

## Evidence and comparison files

- Plus5 stock uses Valve Oil's bundled QIDI payload-derived snapshot for `01.01.02.01`, with defaults provenance `25001402d9025dc9f494e51f2cba907f8e1b45d6`. Q2 uses the October 26 factory-restore capture for `01.01.03.02`. Saved-variable presence and binary hashes use our private captures. These are dated baselines. [Plus5 snapshot provenance](https://github.com/thelegendtubaguy/Valve-Oil/blob/384a2934ec452f2e22dba9b987310dada428bb12/installer/stock/qidi-plus5-defaults/README.md)
- [Stock options](stock-options.csv) compares 820 file/section/option keys from printer, captured Box, timelapse and vendor macro configs. Blank or absent values at a path can reflect different file layouts or an uncaptured file. Indented macro bodies need semantic review. Sensitive identifiers and saved values are excluded.
- [Plus5 manifest patches](plus5-manifest-patches.csv) records 17 applicable changes, expected and desired values or normalized section hashes, and each stock baseline at the target path.
- [Valve Oil macro variables](valve-oil-macro-variables.csv) lists 36 declared common and Plus5 macro variables. [Saved-variable keys](saved-variable-keys.csv) lists 114 keys present across the two printer captures. Presence does not establish units, ownership or state semantics. Runtime Box defaults and branch-specific settings live in [box_feed_motion.py](https://github.com/thelegendtubaguy/Valve-Oil/blob/384a2934ec452f2e22dba9b987310dada428bb12/installer/klipper/tltg/box_feed_motion.py) and [box_enablement.py](https://github.com/thelegendtubaguy/Valve-Oil/blob/384a2934ec452f2e22dba9b987310dada428bb12/installer/runtime/box_enablement.py).
- Regenerate with `python3 -B audit/plus5-reference/compare.py UPSTREAM_SNAPSHOT Q2_CONFIG_CAPTURE PLUS5_CONFIG_CAPTURE`. Run this against a trusted local archive of the pinned upstream commit. The script imports the upstream pure section normalizer and reads snapshots. Its four CSV outputs sit beside the script.

## Hardware and runtime

| Area | Plus5 reference | Q2 evidence and consequence |
|---|---|---|
| Linux host | Upstream documents RK3308BS, 486 MB, Debian Bullseye, kernel 5.10.160 build #3. Max 4 uses build #4. | Q2 capture reports aarch64, four CPUs, 498752 kB, Debian 11, Python 3.9.2 and 5.10.160. Exact kernel build, memory pressure, USB IRQ layout, camera/input devices and service paths need separate checks. |
| Mainboard | 02.01.01.12, 134 commands in our capture. Upstream matched the Plus5 and Max 4 application payloads. | 02.01.01.09, 151 commands in our capture. Mainboard replacement is a separate hardware qualification. |
| Toolhead | 02.02.01.08, 127 commands. Upstream reports the test Plus5 matched an accepted THR bootloader. | 02.02.01.08, 127 commands. Shared version and command count support interface investigation. Exact image, bootloader and accelerometer behavior remain unverified. Both stock configs use the !THR:PA1 filament sensor. |
| USB Box | 02.03.01.21, 140 commands. Valve Oil's Plus5 port adds the stock restore path for this firmware family. | Captured Box reports KLP_MCU_MKS_V2_1.1.3, 118 commands. The Q2 Box needs separate firmware and restore qualification before factory RFID. |
| Host RFID/controller | Captured stock `box_rfid.so` and `multi_color_controller.so`. | Both files are byte-identical across captures. SHA-256 prefixes are `6a196c69` and `b7e3bc21` respectively. Shared host interfaces support offline replay. Capture of Q2 `box_stepper.so` and `box_extras.so` is still missing. |
| X/Y and Z | Sensorless TMC2240 X/Y, TMC2209 Z, X −7…326, Y −5…340, Z max 310, XY rotation distance 39. | Same active driver families. Q2 X −1…275, Y −1…295, Z max 265, XY rotation distance 38.82. Direction pins differ. Both report 600 mm/s, 20,000 mm/s², Z rotation distance 4 and zero X/Y homing retract. Geometry and pin mappings stay model-specific. |
| Mesh and chamber | Mesh bounds 15…305, 7×7, 150 mm/s. Chamber heater max 68 °C. | Bounds 10…260, 6×6, 100 mm/s. Chamber heater max 70 °C. Bed and chamber thermistor pins swap between configs. Q2 stock homing already has a lazy G28 wrapper. |
| Box motion | Upstream traced a single fast push and one retract-to-hub stage. A known Plus5 box_stepper hash gates the lookup wrapper. | Similar controller symbols do not establish the same path or argument defaults. Capture hashes and trace Q2 load/unload lookups before selecting a layout or borrowing the 850 mm fast push. |

[Upstream Plus5 engineering record](https://github.com/thelegendtubaguy/Valve-Oil/blob/384a2934ec452f2e22dba9b987310dada428bb12/openspec/changes/archive/2026-11-12-support-qidi-plus5/design.md)

The 17 Plus5 manifest guards all match its bundled stock baseline. Nine also match Q2 at the same path, including the filament sensor section and several numeric starting values. Q2 mesh speed differs and the seven other section-removal targets lack a same-path match. Identical guards establish a matching input only. They do not establish safe Q2 behavior.

The 820 stock options include 266 same-path textual matches, 59 differences and 495 keys present at only one path. Q2 combines vendor macros in `gcode_macro.cfg`, so many path-only differences reflect file layout. The audit ran 46 upstream offline tests covering RFID, Box feed motion, resonance sweep and source-patch lifecycle. All passed on the upstream snapshot.

## Port decisions

| Component | Q2 disposition |
|---|---|
| Model admission and packaging | Reuse the Plus5 design: model-specific SOC identity, firmware allowlist, stock snapshot, guarded variants, separate macro and slicer packs, and offline lifecycle matrix. Q2 admission belongs after fixture and hardware acceptance. |
| Box status, Fluidd and catalog editor | First port candidate. Replay Q2 status/partial updates and collect would-send commands in a harness. Test slot edit, firmware errors, replacement timeout and file filament mapping. The fork's editor must preserve our IDs and type-first labels. |
| RFID startup timing and read guard | Compare upstream deferred INIT_RFID_READ with Q2 startup and our empty-success guard. They solve different failures. Preserve the two-match policy and existing registry. Eject/replacement invalidation and extra retry remain open. |
| Factory RFID and writing | Keep Box flashing behind exact board/build/bootloader and recovery evidence. Existing Q2 IDs collide with 62 upstream 0.4 mm catalog IDs and Plus5 with 93. Resolve identities by product before allocating any new IDs. In-Box writing is a separate feature. |
| RS485 and cloud handling | The newer RS485 detector distinguishes the controller's fallback identity from actual hardware. Our USB-only Q2 and Plus5 currently disable the unused section. Replay USB, absent adapter and real adapter cases before choosing behavior. The cloud handshake change is relevant to API stalls. The observed Plus5 MQTT decryption/authorization failure needs separate diagnosis. |
| Box feed, eject, cut, park and heat | Reuse command/UI scaffolding after confirming Q2 lookup and flow contracts. Keep Q2 distances, motion bounds, heater supervision and sensor timings. Validate each cold/hot path separately. |
| Print start, end and slicer | Reuse guarded probe retry, offset persistence, adaptive mesh selection and update activation concepts. Start from Q2 stock macro bodies and slicer syntax. Plus5 coordinates, currents and motion presets need Q2-specific derivation. |
| Driver cooling and input shaper | Adding X/Y to the board-fan trigger is a plausible candidate because both captures show Z-only triggers and TMC2240 X/Y. Confirm Q2 fan behavior and temperatures first. The Plus5 slope-control measurements and resonance cap are useful test references. Preserve Q2's calibration and test bounds. |
| Klipper/Moonraker and host performance | Classify each source patch by exact baseline and build guard. Prefer observable diagnostics, 3MF metadata replay and reversible UI work first. Measure scheduling and memory before applying service priorities, CPU affinity, zram, wheel or storage changes. |
| Native UI, remote screen and add-ons | UI contract, framebuffer rotation, touch axes, webcam and service permissions need independent Q2 evidence. Treat third-party add-ons as separate installation decisions. |

First deliverable for implementation is a Q2-only offline Box/Fluidd fixture suite that exercises the existing naming change, slot mapping and RFID timeout. Follow it with a Q2-specific installer manifest and macro overlay against pinned stock inputs. This review used local source and captures only.
