# Pre-existing Q2 camera USB failure

## Provenance

This fault predates the Valve Oil/Q2 changes. Gmail evidence reviewed with
owner authorization on November 20, 2026:

- September 13, "New Issue with camera": owner reported camera works locally
  and remotely after full power cycling, then changes to no signal during a
  print; supplied Crowsnest logs reporting no usable devices.
- September 14, "Q2": support recommended a camera-service restart, then
  powering off and reseating the camera cable at the PCB side, then at the
  camera side if needed. The email describes a camera cable on the PCB, not
  a diagnosed Wi-Fi fault.
- October 1, "Re: Q2": owner reported PCB-side reseating followed by four
  consecutive days printing without no-signal errors. Camera-side connection
  was glued and was not disturbed. Ticket closure was requested.

Private email bodies and attachment data are not committed. The historical
ZIP attachment was not retrieved or analyzed through the Gmail connector.

## November 19/20 captures

First capture: camera first disconnected about 26 minutes after boot during
a successful print. USB descriptor errors (-71), repeated disconnects,
unsuccessful re-enumeration and camera-only port power-cycle attempts followed.
Camera disappeared from lsusb and /dev/video*. Streaming server remained
reachable but source online=false and captured_fps=0.

After adding Valve Oil RS-485 and link monitors and rebooting, camera returned
at 15 FPS. A new print ran November 20 07:58:03 to 11:24:24 CST and completed.
The camera disconnected at approximately 08:18:54 and failed enumeration by
08:20:21. Crowsnest reported its lost device at 08:21:45. Thus this failure
occurred during printing, not at print completion.

The RS-485 fix was active: hourly messages count 119 repeated missing-adapter
attempts, consistent with ~30-second retry spacing rather than 2 seconds.
Mainboard, toolhead and Box link heartbeats remained healthy around the camera
failure, without rising retransmission counts. Polling reduction did not
prevent recurrence. This is evidence against that specific polling hypothesis,
not proof excluding all software/USB interactions.

## Additional read-only checks

Camera's USB parent hub 2-1 and controller usb2 both report runtime suspended
time 0 for this boot. Autosuspend is permitted on them, but permission alone
is not evidence of a suspend. Camera's own counter is unavailable because it
has disappeared. Downstream Box hub has only 373 ms recorded suspended time;
it is not the camera's parent. Camera port over_current_count is 0. There is
no captured overcurrent or temperature fault explaining the disconnect.

Do not diagnose a loose connector from the generic kernel cable warning.
Reconnecting can change contact/signal integrity and cable stress as well as
remove device power; the historical repair does not distinguish these effects.
Four days of success after reseating is more informative than a single reboot,
but does not identify the failed component.

## Remaining controlled tests

Preserve failed state first. Any recovery should target only the camera's
branch; do not reset/unbind the shared hub containing printer MCUs. No homing,
reboot, service restart, USB reset or power-setting change was performed in
these read-only investigations. Cleared plate alone does not revoke the owner's
no-reboot instruction.

Compare camera behavior during a long idle stream versus a print; record
camera USB power settings while it is present, printer/chamber temperatures
and failure timing. If needed, compare a known-good camera/cable or test the
original assembly on a separate host. These tests distinguish stream/runtime,
print heat/vibration/power and camera/cable faults. A camera-only power-management
trial remains possible, but parent autosuspend is currently a weak hypothesis.

## Controlled recovery, November 20 afternoon

Owner authorized ordered recovery tests after clearing the plate, retaining
no homing or OS reboot. Restarting Crowsnest failed with no usable devices;
the camera was still missing from USB. Privileged hub inspection showed
camera port 2 physically connected but disabled (status 0x0101); the hub
reports ganged power switching, so independent VBUS cycling is not assumed.
A single camera-port-only USB PORT_RESET changed status to 0x0503 (enabled,
high-speed, connected), but did not recreate a Linux camera device. No shared
power switch or controller-port reset was used in that test.

Next test safely stopped idle QIDI client/Klipper/camera services and rebound
only the parent hub's Linux driver to force enumeration, then restarted the
services. This necessarily detaches the printer MCU USB devices while their
host services are stopped. It is not an operating-system reboot or a
commanded motion test. Record the result separately before drawing conclusions.

Hub-driver rebind result: camera re-enumerated as 32e6:9221 on 2-1.2.
Crowsnest initially hit a failed-start condition after its prior no-device
retries; reset-failed and restart recovered streaming at 640x480/15 FPS.
Klipper returned ready/standby, with no OS reboot or commanded movement.
This establishes recoverability by hub reinitialization plus streamer restart;
it does not establish whether software, device firmware or electrical behavior
caused the initial failure. Hub driver actions may affect hardware state, so
this is not proof that a power-related mechanism was excluded.

Recovered camera power/control was auto with a 2000 ms delay; its own runtime
suspended counter was nonzero while no streamer was active. After streaming
started it was active. That idle suspend is not itself a fault. The owner
authorized iterative diagnosis; a single temporary camera-only trial changed
power/control from auto to on, retaining its previous value in a private
recovery record. No udev rule or boot setting changed. Reboot or device
re-enumeration can discard the trial. Rollback is writing auto back to that
camera's power/control after verifying its vendor/product and path.

Camera remained online at 15 FPS at the final short observation. Previous
runtime acceleration 5000 was restored following the host-service restart.
The print-correlated recurrence test is still required; no long-term fix is
claimed. Repeat a comparable print with camera control=on and watch beyond
the previous 20-30 minute failure window before changing another variable.

## Third capture: November 20 evening, during a newly started print

Read-only capture at 19:21 showed camera absent from USB and streamer offline,
with printer actively starting Collar + Mouth (start 19:20:29). Kernel first
camera disconnect in this boot was ~1215.53 s, approximately 15:45:45 using
the boot epoch/current clock; Crowsnest lost-device line is 15:46:47. Thus
this captured failure occurred during the preceding Ears print (15:26:31 to
16:39:40), not during the evening print's startup. The current boot differs
from the afternoon recovery/test boot; boot epoch is about 15:25:30. Some
startup wall-clock log lines precede that epoch because startup clock changes
make early timestamps unsuitable as exact boot-time evidence.

The camera-only power/control=on trial was explicitly runtime-only and no
persistent rule was installed. An intervening reboot/device enumeration can
reset it. Camera is absent, so its own current control value cannot be checked.
The saved trial record proves the earlier write, not survival across this boot.
This capture therefore does NOT establish failure with autosuspend disabled.
The parent hub again reports runtime_suspended_time=0. Camera re-enumeration
failed with port-enable and -71 descriptor/address errors. Printer health
remained normal at capture (45 timers, ~0.116 main-thread load, ~1 ms delay);
RS-485 monitor detected no hardware or port conflict.

No service restart, port reset, homing, movement or reboot was performed while
the new print was running. Next controlled trial should verify the camera's
own control state after recovery and retain that setting through enumeration,
using a vendor/product-specific rule if authorized, before a comparable print.
