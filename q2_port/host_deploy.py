"""Guarded host/web activation for an explicitly rendered Q2 package. Never flashes firmware."""

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

import policy
from plan import safe, sha

SERVICES = ("nginx", "qidi-client", "moonraker", "klipper")


def atomic(path, data, mode, uid, gid):
    handle, temporary = tempfile.mkstemp(prefix=".q2-stable-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fchown(stream.fileno(), uid, gid)
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def current(path):
    return sha(path.read_bytes()) if path.exists() else None


def journal(package, state):
    atomic(
        package / "journal.json",
        (json.dumps(state, indent=2) + "\n").encode(),
        0o600,
        os.getuid(),
        os.getgid(),
    )


def report_recovery_error(message):
    try:
        print(message, file=sys.stderr)
    except OSError:
        pass  # Losing both log destinations must not prevent recovery.


def recovery_journal(package, state):
    """A reporting failure must never prevent file or service recovery."""
    try:
        journal(package, state)
    except OSError as error:
        report_recovery_error("Recovery journal write failed: " + str(error))


def read_api(route):
    with urllib.request.urlopen(
        "http://127.0.0.1:7125/" + route, timeout=10
    ) as response:
        return json.load(response)["result"]


class Services:
    def idle(self, root):
        # /sbin/init is legitimately a merged-/usr symlink. It is never a deployment target.
        if not (root / "sbin/init").is_file():
            raise ValueError("Boot path is broken")
        # Admission reads data only. Nothing here sends G-code or moves a motor.
        admit_idle(root)

    def active(self):
        return [
            name
            for name in SERVICES
            if subprocess.run(["systemctl", "is-active", "--quiet", name]).returncode
            == 0
        ]

    def stop(self):
        for name in SERVICES:
            subprocess.run(["systemctl", "stop", name], check=True, timeout=45)

    def nginx(self):
        subprocess.run(["nginx", "-t"], check=True, timeout=15)

    def start(self, names):
        for name in ("klipper", "moonraker", "qidi-client", "nginx"):
            if name in names:
                subprocess.run(["systemctl", "start", name], check=True, timeout=45)

    def healthy(self):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            try:
                if read_api("printer/info")["state"] == "ready":
                    if set(self.active()) == set(SERVICES):
                        return
            except (OSError, ValueError, KeyError):
                pass
            time.sleep(2)
        raise RuntimeError("Services did not return to ready")


def admit_idle(root):
    # Keep legitimate boot symlinks separate from deployment-target path checks.
    firmware = json.loads(
        safe(root, "home/qidi/update/firmware_manifest.json").read_text()
    )["SOC"]
    if firmware["version"] != policy.SOC_VERSION or not firmware["file"].startswith(
        "QD_Q2_SOC_" + policy.SOC_VERSION + "_"
    ):
        raise ValueError("Wrong Q2 firmware")
    objects = read_api("printer/objects/list")["objects"]
    names = [
        "print_stats",
        "idle_timeout",
        "box_extras",
        "multi_color_controller",
        "tltg_box_rfid",
    ]
    names += [
        n
        for n in objects
        if n in ("extruder", "heater_bed") or n.startswith("heater_generic ")
    ]
    status = read_api(
        "printer/objects/query?"
        + "&".join(urllib.parse.quote(n) for n in names if n in objects)
    )["status"]
    if (
        status["print_stats"]["state"] in ("printing", "paused")
        or status["idle_timeout"]["state"] == "Printing"
    ):
        raise ValueError("Printer is printing or paused")
    if any(status[n].get("target", 0) != 0 for n in names if n in status):
        raise ValueError("A heater target is active")
    task = status.get("multi_color_controller", {}).get("task", {})
    if task.get("current_queue") or task.get("current_step") or task.get("is_paused"):
        raise ValueError("Box flow is active or paused")
    if status.get("box_extras", {}).get("is_tool_change") or status.get(
        "tltg_box_rfid", {}
    ).get("job", {}).get("running"):
        raise ValueError("Box operation or RFID scan is active")


def load(package, root):
    manifest = json.loads((package / "deployment.json").read_text())
    if (
        manifest.get("upstream_commit") != policy.UPSTREAM_COMMIT
        or manifest.get("no_flash") is not True
    ):
        raise ValueError("Wrong deployment scope")
    seen = set()
    for operation in manifest["operations"]:
        policy.validate_operation(operation)
        name = operation["target"]
        # The renderer omits unchanged files. This motion helper must never be
        # a write target, even when a caller labels it an unchanged carry-forward.
        if name == "home/qidi/klipper/klippy/extras/tltg_box_slot_jog.py":
            raise ValueError("Slot-jog writes are outside host deployment scope")
        if name in seen:
            raise ValueError("Duplicate target")
        seen.add(name)
        safe(root, name)
        if (
            sha(safe(package, "rendered/" + name).read_bytes())
            != operation["after_sha256"]
        ):
            raise ValueError("Rendered payload mismatch: " + name)
    return manifest


def restore(package, root, services, state):
    package, root = package.resolve(), root.resolve()
    # Refuse unreviewed owner edits or corrupt backups before touching any target.
    for entry in state["files"]:
        path = safe(root, entry["target"])
        if current(path) not in (entry["before_sha256"], entry["after_sha256"]):
            raise ValueError("Rollback target drift: " + entry["target"])
        if (
            entry["before_sha256"] is not None
            and current(safe(package, "before/" + entry["target"]))
            != entry["before_sha256"]
        ):
            raise ValueError("Rollback backup corrupt")
    services.stop()
    for entry in reversed(state["files"]):
        path = safe(root, entry["target"])
        if entry["before_sha256"] is None:
            if path.exists():
                path.unlink()
        else:
            atomic(
                path,
                safe(package, "before/" + entry["target"]).read_bytes(),
                entry["mode"],
                entry["uid"],
                entry["gid"],
            )
    for name in reversed(state["created_directories"]):
        path = safe(root, name)
        if path.exists():
            try:
                path.rmdir()
            except OSError:
                pass  # Never delete an unexpected file.
    services.nginx()
    services.start(state["services"])
    services.healthy()
    state["status"] = "rolled_back"
    recovery_journal(package, state)


def recover(package, root, services, state):
    if state.get("writes_started") is False:
        # No installed file was touched: retain concurrent owner edits and only
        # return the original services to operation, including a partial stop.
        services.start(state["services"])
        services.healthy()
        state["status"] = "aborted_before_write"
        recovery_journal(package, state)
    else:
        # Legacy journals lack writes_started; conservatively restore their files.
        restore(package, root, services, state)


def apply(package, root, services):
    package, root = package.resolve(), root.resolve()
    manifest = load(package, root)
    if (package / "journal.json").exists():
        raise ValueError(
            "Existing transaction: inspect or roll back before applying again"
        )
    services.idle(root)
    active = services.active()
    if set(active) != set(SERVICES):
        raise ValueError("Expected services are not all active")
    services.nginx()
    state = {
        "status": "preparing",
        "files": [],
        "created_directories": [],
        "services": active,
        "firmware_flashes": 0,
        "writes_started": False,
    }
    before_dir = package / "before"
    before_dir.mkdir(mode=0o700)
    for operation in manifest["operations"]:
        path = safe(root, operation["target"])
        if current(path) != operation["before_sha256"]:
            raise ValueError("Deployment target drift: " + operation["target"])
        owner = path if path.exists() else path.parent
        while not owner.exists():
            owner = owner.parent
        info = owner.stat()
        entry = {
            "target": operation["target"],
            "before_sha256": operation["before_sha256"],
            "after_sha256": operation["after_sha256"],
            "uid": info.st_uid,
            "gid": info.st_gid,
            "mode": stat.S_IMODE(info.st_mode) if path.exists() else 0o644,
        }
        if path.exists():
            backup = safe(package, "before/" + operation["target"])
            backup.parent.mkdir(parents=True, exist_ok=True)
            atomic(backup, path.read_bytes(), 0o600, os.getuid(), os.getgid())
        state["files"].append(entry)
    state["status"] = "prepared"
    journal(package, state)
    services.idle(root)
    try:
        services.stop()
        # Reject a last-moment write after planning and service shutdown.
        for entry in state["files"]:
            if current(safe(root, entry["target"])) != entry["before_sha256"]:
                raise ValueError("Stopped-service target drift: " + entry["target"])
        state["status"] = "applying"
        # Persist the conservative recovery decision BEFORE any directory/file
        # mutation. An interrupted transaction must not skip restoration.
        state["writes_started"] = True
        journal(package, state)
        for entry in state["files"]:
            path = safe(root, entry["target"])
            missing, parent = [], path.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir(mode=0o755)
                os.chown(directory, entry["uid"], entry["gid"])
                state["created_directories"].append(
                    directory.relative_to(root).as_posix()
                )
                journal(package, state)
            atomic(
                path,
                safe(package, "rendered/" + entry["target"]).read_bytes(),
                entry["mode"],
                entry["uid"],
                entry["gid"],
            )
        services.nginx()
        state["status"] = "activating"
        journal(package, state)
        services.start(active)
        services.healthy()
        for entry in state["files"]:
            if current(safe(root, entry["target"])) != entry["after_sha256"]:
                raise ValueError("Installed hash mismatch: " + entry["target"])
        state["status"] = "active"
        journal(package, state)
    except BaseException as error:
        state["error"] = str(error)
        recovery_journal(package, state)
        try:
            recover(package, root, services, state)
        except BaseException as rollback_error:
            state["status"] = "rollback_failed"
            state["rollback_error"] = str(rollback_error)
            report_recovery_error("Recovery failed: " + str(rollback_error))
            recovery_journal(package, state)
        raise
    print(
        json.dumps(
            {
                "status": state["status"],
                "changed_files": len(state["files"]),
                "firmware_flashes": 0,
            }
        )
    )


def rollback(package, root, services):
    state = json.loads((package / "journal.json").read_text())
    if "klipper" in services.active():
        services.idle(root)
    elif state["status"] not in (
        "prepared",
        "applying",
        "activating",
        "rollback_failed",
    ):
        raise ValueError(
            "Offline rollback requires an interrupted maintenance transaction"
        )
    recover(package, root, services, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "rollback"))
    parser.add_argument("--package", required=True, type=Path)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run through the verified administrator service authorization")
    package = args.package.resolve()
    if args.action == "apply":
        apply(package, Path("/"), Services())
    else:
        rollback(package, Path("/"), Services())


if __name__ == "__main__":
    main()
