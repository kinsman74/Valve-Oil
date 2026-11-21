"""Verify that the selective stable refresh preserves Q2's motion exclusions."""

import argparse
import hashlib
import json
from pathlib import Path
import policy


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--staged", type=Path, required=True)
    a = p.parse_args()
    baseline = json.loads(
        Path(__file__).with_name("baseline-source-lock.json").read_text()
    )
    for name in policy.NONMOTION + policy.CORE:
        if name in ("box485_monitor", "box_link_monitor"):
            continue
        local = "work/q2-nonmotion-2026-11-20/package/modules/tltg_" + name + ".py"
        upstream = "installer/klipper/tltg/" + name + ".py"
        expected = baseline["workspace"].get(local) or baseline["upstream"][upstream]
        data = (a.staged / ("modules/tltg_" + name + ".py")).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Unexpected behavior change in retained module: " + name)
    relative = "work/q2-nonmotion-2026-11-20/ui/src/components/Motion.tsx"
    data = (a.staged / "ui/src/components/Motion.tsx").read_bytes()
    if hashlib.sha256(data).hexdigest() != baseline["workspace"][relative]:
        raise ValueError("Manual jogging behavior changed")
    control = (a.staged / "ui/src/screens/Control.tsx").read_text()
    if "<Motion />" not in control or "ToolsMenu" in control or "MoveTab" in control:
        raise ValueError("New movement tools must remain disabled")
    tune = (a.staged / "ui/src/screens/Tune.tsx").read_text()
    if "runGcode" in tune or "Tab" in tune or "G28" in tune:
        raise ValueError("New tuning actions must remain disabled")
    status = (
        a.workspace / "work/q2-nonmotion-2026-11-20/package/tltg_status.py"
    ).read_text()
    if "Handler.do_POST = _q2_read_only_post" not in status:
        raise ValueError("Updater POST guard missing")
    guard = "work/q2-box-firmware-port/src/inventory_rfid_read_guard.py"
    if (
        hashlib.sha256((a.workspace / guard).read_bytes()).hexdigest()
        != baseline["workspace"][guard]
    ):
        raise ValueError("RFID read guard changed")
    relative = "work/q2-valve-align-26.11.18.1/fluidd/src/components/widgets/toolhead/ToolheadCard.vue"
    candidate = (
        a.workspace
        / "work/q2-stable-26.11.18.2/fluidd/src/components/widgets/toolhead/ToolheadCard.vue"
    )
    if (
        hashlib.sha256(candidate.read_bytes()).hexdigest()
        != baseline["workspace"][relative]
    ):
        raise ValueError("Fluidd toolhead behavior changed")
    print(
        "Scope passed: only two host monitor modules changed; manual motion, tag-jog, RFID guard baseline and updater boundary retained"
    )


if __name__ == "__main__":
    main()
