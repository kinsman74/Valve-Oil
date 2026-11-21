"""Prepare selective 26.11.18.2 Q2 sources without contacting any printer."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from provenance import verify_group
import policy


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Unexpected source structure: " + old[:60])
    return text.replace(old, new, 1)


def stage(upstream, workspace, output):
    verify_group(upstream, "upstream")
    baseline = json.loads(
        Path(__file__).with_name("baseline-source-lock.json").read_text()
    )
    old_upstream = workspace / "work/q2-valve-align-26.11.18.1/upstream"

    def previous(relative, group="workspace"):
        root = workspace if group == "workspace" else old_upstream
        data = (root / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != baseline[group][relative]:
            raise ValueError("Baseline source mismatch: " + relative)
        return data

    if output.exists():
        raise ValueError("Choose a new staging directory")
    output.mkdir(parents=True)
    modules = output / "modules"
    modules.mkdir()
    for name in policy.NONMOTION + policy.CORE:
        relative = "work/q2-nonmotion-2026-11-20/package/modules/tltg_" + name + ".py"
        if relative in baseline["workspace"]:
            data = previous(relative)
        else:
            data = previous("installer/klipper/tltg/" + name + ".py", "upstream")
        if name in ("box485_monitor", "box_link_monitor"):
            # Retain Q2's deployed module, command, setting and log identities.
            data = (upstream / ("installer/klipper/extras/" + name + ".py")).read_text()
            data = (
                data.replace("vo_", "tltg_")
                .replace("_vo", "_tltg")
                .replace("VO_RS_BOX_REPORT", "TLTG_RS_BOX_REPORT")
                .encode()
            )
        (modules / ("tltg_" + name + ".py")).write_bytes(data)
    ui = output / "ui"
    shutil.copytree(upstream / "ui", ui)
    # Preserve the reviewed Q2 flat-slot fallback and its regression test.
    old_source = workspace / "work/q2-nonmotion-2026-11-20/ui/src/qidi/qidi-box.ts"
    original = (old_upstream / "ui/src/qidi/qidi-box.ts").read_text()
    q2 = old_source.read_text()
    import difflib

    # The committed patch records precisely this historical Q2 compatibility change.
    expected = Path(__file__).with_name("q2-slot-display.patch").read_text()
    actual = "".join(
        difflib.unified_diff(
            original.splitlines(True),
            q2.splitlines(True),
            fromfile="a/qidi-box.ts",
            tofile="b/qidi-box.ts",
        )
    )
    if actual != expected:
        raise ValueError("Historical Q2 display patch changed")
    target = ui / "src/qidi/qidi-box.ts"
    text = target.read_text()
    old = "    return infos.find(info => info?.index === index % 4) ?? infos[index % 4]\n  }"
    new = q2[
        q2.index("    const info = infos.find") : q2.index("\n}\n\n// Earlier firmware")
    ]
    text = replace_once(text, old, new)
    text = replace_once(
        text,
        "reading: stepper?.rfid_state === 1",
        "reading: (stepper?.rfid_state ?? info?.read_rfid_state) === 1",
    )
    target.write_text(text)
    shutil.copy2(
        Path(__file__).with_name("test_q2_slots.test.ts"),
        ui / "src/qidi/__tests__/qidi-box-q2.test.ts",
    )
    # Existing jog commands/speeds remain unchanged; new movement tools are not enabled.
    (ui / "src/components/Motion.tsx").write_bytes(
        previous("work/q2-nonmotion-2026-11-20/ui/src/components/Motion.tsx")
    )
    target = ui / "src/screens/Control.tsx"
    text = replace_once(
        target.read_text(),
        "import { MoveTab, ToolsMenu } from '../components/control/Move'",
        "import { Motion } from '../components/Motion'",
    )
    text = replace_once(
        text,
        "{ value: 'move', label: 'Move', body: () => <MoveTab />, actions: () => <ToolsMenu /> },",
        "{ value: 'move', label: 'Move', body: () => <Motion /> },",
    )
    target.write_text(text)
    # Keep already-deployed tag-jog command identity; RFID write already uses VO_.
    for relative in ("src/state/box-model.ts", "src/state/box-model.test.ts"):
        target = ui / relative
        target.write_text(
            target.read_text().replace("VO_BOX_SLOT_JOG", "TLTG_BOX_SLOT_JOG")
        )
    # New tuning/calibration actions are outside this selective update. Existing printer controls remain available.
    target = ui / "src/screens/Tune.tsx"
    target.write_text(
        'export function TuneScreen() { return <section className="card"><h2>Tune</h2><p>Use the printer touchscreen for calibration.</p></section> }\n'
    )
    print("Selective source staging complete; no printer accessed")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("upstream", "workspace", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    stage(a.upstream, a.workspace, a.output)


if __name__ == "__main__":
    main()
