"""Render an admitted snapshot into a host-only activation package; no printer access."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

import plan
import policy


def render(bundle, snapshot, output):
    report = plan.plan(bundle, snapshot)
    manifest = json.loads((bundle / "manifest.json").read_text())
    if output.exists() or any(
        output.resolve().is_relative_to(p.resolve()) for p in (bundle, snapshot)
    ):
        raise ValueError("Choose a new output outside the inputs")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".q2-host-", dir=output.parent
    ) as temporary:
        package = Path(temporary) / "package"
        package.mkdir(mode=0o700)
        operations = []
        for operation in manifest["operations"]:
            target = plan.safe(snapshot, operation["target"])
            before = target.read_bytes() if target.exists() else b""
            after = plan.desired(bundle, operation, before)
            if target.exists() and before == after:
                continue
            if operation["target"] == policy.CONFIG:
                marker = b"#*# <---------------------- SAVE_CONFIG"
                if before.split(marker, 1)[1] != after.split(marker, 1)[1]:
                    raise ValueError("Calibration tail changed")
            destination = plan.safe(package, "rendered/" + operation["target"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(after)
            operations.append(
                {
                    **operation,
                    "before_sha256": plan.sha(before) if target.exists() else None,
                }
            )
        for name in ("host_deploy.py", "plan.py", "policy.py"):
            shutil.copy2(Path(__file__).with_name(name), package / name)
        deployment = {
            "schema": 1,
            "version": manifest["version"],
            "upstream_commit": policy.UPSTREAM_COMMIT,
            "no_flash": True,
            "operations": operations,
        }
        (package / "deployment.json").write_text(
            json.dumps(deployment, indent=2) + "\n"
        )
        inventory = {
            p.relative_to(package).as_posix(): plan.sha(p.read_bytes())
            for p in sorted(package.rglob("*"))
            if p.is_file()
        }
        (package / "SHA256SUMS.json").write_text(json.dumps(inventory, indent=2))
        package.rename(output)
    return {
        "changed_files": len(operations),
        "firmware_binaries": 0,
        "plan_counts": report["counts"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "snapshot", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.bundle, args.snapshot, args.output), indent=2))


if __name__ == "__main__":
    main()
