"""Stage stable-pinned Fluidd with Q2 display and existing jog-command compatibility."""

import argparse
from pathlib import Path
import shutil
import subprocess
from provenance import verify_group
from stage_stable import replace_once


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    verify_group(a.source, "fluidd")
    if a.output.exists():
        p.error("Choose a new output directory")
    shutil.copytree(
        a.source,
        a.output,
        ignore=lambda directory, names: [
            name for name in names if (Path(directory) / name).is_symlink()
        ],
    )
    subprocess.run(
        [
            "git",
            "apply",
            str(Path(__file__).with_name("fluidd-preserve-toolhead.patch").resolve()),
        ],
        cwd=a.output,
        check=True,
    )
    target = a.output / "src/util/qidi-box.ts"
    # Same Q2 fallback as companion UI: resolved native controller fields take priority over saved assignments.
    text = target.read_text()
    old = "    return infos.find(info => info?.index === index % 4) ?? infos[index % 4]\n  }"
    new = """    const info = infos.find(info => info?.index === index % 4) ?? infos[index % 4]
    if (info) return info
  }
  // Q2 publishes the same slot fields in a flat controller Box object.
  const box = printer.multi_color_controller?.box
  const prefix = `box${Math.floor(index / 4)}_filament_info_${index % 4}_`
  if (typeof box?.[prefix + 'filament_id'] === 'string' && box[prefix + 'filament_id'] !== '') {
    return Object.fromEntries(Object.entries(box)
      .filter(([key]) => key.startsWith(prefix))
      .map(([key, value]) => [key.slice(prefix.length), value]))
  }"""
    text = replace_once(text, old, new)
    text = replace_once(
        text,
        "reading: stepper?.rfid_state === 1",
        "reading: (stepper?.rfid_state ?? info?.read_rfid_state) === 1",
    )
    target.write_text(text)
    test = Path(__file__).with_name("test_q2_slots.test.ts").read_text()
    (a.output / "src/util/__tests__/qidi-box-q2.spec.ts").write_text(test)
    for target in (a.output / "src").rglob("*"):
        if target.is_file() and target.suffix in (".ts", ".vue"):
            text = target.read_text()
            if "VO_BOX_SLOT_JOG" in text:
                target.write_text(text.replace("VO_BOX_SLOT_JOG", "TLTG_BOX_SLOT_JOG"))
    target = a.output / "vite.config.inject-version.ts"
    target.write_text(
        replace_once(
            target.read_text(),
            "const gitHash = () => child_process",
            "const gitHash = () => process.env.Q2_FLUIDD_REV || child_process",
        )
    )
    print("Use Q2_FLUIDD_REV=e85f13b-q2 when building this tarball-based source")


if __name__ == "__main__":
    main()
