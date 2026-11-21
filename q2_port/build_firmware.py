"""Build locked Q2 candidate bytes locally. No flashing or device access."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import policy
from provenance import verify_group


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build(args):
    # The imported upstream builder and legacy adapter contain assertions.
    require(
        __debug__, "Optimized Python is unsupported; verification must not be disabled"
    )
    verify_group(args.upstream, "upstream")
    verify_group(args.q2_port, "q2_adapter")
    sys.path.insert(0, str(args.upstream.resolve() / "scripts"))
    from build_thr_firmware import patch_thr

    manifest = json.loads(
        (args.upstream / "firmware/max4-thr-valve-oil-v1.json").read_text()
    )
    stock_thr = args.thr.read_bytes()
    require(sha(stock_thr) == policy.STOCK_THR_SHA, "Unknown Q2 toolhead input")
    thr = patch_thr(stock_thr, manifest)
    require(
        (len(thr), sha(thr)) == policy.FIRMWARE["q2-thr-valve-oil-fifo.bin"],
        "Unexpected toolhead output",
    )
    stock_box = args.q2_port / "QD_Q2_BOX_02.03.01.13_20251127.bin"
    require(sha(stock_box.read_bytes()) == policy.STOCK_BOX_SHA, "Unknown Q2 Box input")
    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary)
        shutil.copy2(args.q2_port / "build.py", stage / "build.py")
        shutil.copytree(
            args.q2_port / "src",
            stage / "src",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        shutil.copy2(stock_box, stage / stock_box.name)
        environment = os.environ.copy()
        environment.pop("PYTHONOPTIMIZE", None)
        subprocess.run(
            [sys.executable, "-B", str(stage / "build.py")], env=environment, check=True
        )
        box = (stage / "q2-box-valve-rfid-dev1.bin").read_bytes()
        require(
            (len(box), sha(box)) == policy.FIRMWARE["q2-box-valve-rfid-dev1.bin"],
            "Unexpected Box output",
        )
        report = json.loads((stage / "build-report.json").read_text())
        report["status"] = (
            "reproduced deployed Q2 dev1; prior hardware evidence is separate"
        )
        for patch in report["patches"]:
            patch["description"] = patch["description"].replace(
                "Retire debug handler", "Retire legacy RFID diagnostic handler"
            )
    (args.output / "q2-box-valve-rfid-dev1.bin").write_bytes(box)
    (args.output / "q2-thr-valve-oil-fifo.bin").write_bytes(thr)
    (args.output / "box-build-report.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    result = {
        "mode": "offline-build-only",
        "upstream_commit": policy.UPSTREAM_COMMIT,
        "source_content_locks_verified": True,
        "box": {
            "stock_sha256": policy.STOCK_BOX_SHA,
            "output_sha256": sha(box),
            "size": len(box),
            "scope": "Q2 RFID transport; empty/malformed/conflict protection is host-side",
        },
        "thr": {
            "stock_sha256": sha(stock_thr),
            "output_sha256": sha(thr),
            "size": len(thr),
            "scope": "Exact upstream image identity; sensor FIFO fix only",
        },
        "mainboard": "no image or motion/closed-loop patch included",
        "shutdown": "Q2 path unchanged; MCB-specific patch not applicable",
        "deployment": "not performed; idle installed-image/bootloader admission and recovery qualification required",
    }
    (args.output / "firmware.json").write_text(json.dumps(result, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("upstream", "q2-port", "thr", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    if args.output.exists() or args.output.is_symlink():
        parser.error("Output already exists")
    for source in (args.upstream, args.q2_port):
        if destination.is_relative_to(source.resolve()):
            parser.error("Output must be outside source inputs")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(
            prefix=".q2-firmware-", dir=destination.parent
        ) as temporary:
            args.output = Path(temporary) / "payload"
            args.output.mkdir()
            build(args)
            args.output.rename(destination)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(2, "Firmware build rejected: " + str(error) + "\n")
    print("Offline Box and THR build passed; no hardware accessed.")


if __name__ == "__main__":
    main()
