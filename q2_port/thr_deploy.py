"""Q2-only coordinator around pinned Valve Oil THR tools; no motion or calibration commands."""

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request

import policy
from host_deploy import atomic

VERSION = "2026.11.22-thr-preview1"
BOOT = "31f8344db7b091df5429960bc9cd06065e2188c3b8092e43fb65eb3f2833723c"
STOCK = policy.STOCK_THR_SHA
PATCHED = policy.FIRMWARE["q2-thr-valve-oil-fifo.bin"][1]
SIZE = policy.FIRMWARE["q2-thr-valve-oil-fifo.bin"][0]
SERVICES = (
    "klipper.service",
    "qidi-client.service",
    "tltg-optimized-auto-update.timer",
)
MANIFEST = "firmware/max4-thr-valve-oil-v1.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    atomic(
        path,
        (json.dumps(value, indent=2) + "\n").encode(),
        0o600,
        os.getuid(),
        os.getgid(),
    )


def no_links(path):
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink in maintenance path: " + str(path))
    return path


def q2_manifest(upstream):
    value = json.loads((upstream / MANIFEST).read_text())
    value["targets"] = {policy.SOC_VERSION: "patched"}
    # Only target selection/provenance changes; the admitted bytes and protocol remain upstream's.
    value["stock_archive"] = {"sha256": policy.QIDI_Q2_ARCHIVE_SHA256}
    value["thr"]["member"] = policy.THR_STOCK_MEMBER
    return value


def prepare(upstream, candidate, output):
    lock = json.loads(Path(__file__).with_name("thr-source-lock.json").read_text())
    for name, expected in lock["files"].items():
        if digest((upstream / name).read_bytes()) != expected:
            raise ValueError("Pinned upstream source mismatch: " + name)
    data = candidate.read_bytes()
    if len(data) != SIZE or digest(data) != PATCHED:
        raise ValueError("Candidate does not match vetted Q2 image")
    no_links(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in lock["files"]:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if name == MANIFEST:
            write_json(target, q2_manifest(upstream))
        else:
            shutil.copyfile(upstream / name, target)
    (output / "candidate.bin").write_bytes(data)
    write_json(output / "source-lock.json", lock)


def verify_package(package):
    lock = json.loads(Path(__file__).with_name("thr-source-lock.json").read_text())
    for name, expected in lock["files"].items():
        if (
            name != MANIFEST
            and digest(no_links(package / name).read_bytes()) != expected
        ):
            raise ValueError("Changed transfer source: " + name)
    manifest = json.loads(no_links(package / MANIFEST).read_text())
    if manifest.get("targets") != {policy.SOC_VERSION: "patched"}:
        raise ValueError("Wrong Q2 target selection")
    spec = manifest["thr"]
    if (spec["size"], spec["stock_sha256"], spec["patched_sha256"]) != (
        SIZE,
        STOCK,
        PATCHED,
    ):
        raise ValueError("Wrong image admission")
    # Every manifest field is bound to the original except the three documented Q2 adaptations.
    original = json.loads(
        Path(__file__).with_name("thr-source-manifest.json").read_text()
    )
    if manifest != original:
        raise ValueError("Changed Q2 manifest")
    image = no_links(package / "candidate.bin").read_bytes()
    if len(image) != SIZE or digest(image) != PATCHED:
        raise ValueError("Changed toolhead candidate")


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def verify_snapshot(directory, expected):
    boot = no_links(directory / "bootloader.bin").read_bytes()
    app = no_links(directory / "application.bin").read_bytes()
    if len(boot) != 32768 or digest(boot) != BOOT:
        raise ValueError("Q2 bootloader differs from qualified physical capture")
    if len(app) != SIZE or digest(app) not in expected:
        raise ValueError("Toolhead application readback differs")
    # Snapshot files and directory entries must survive an interrupted transfer.
    for path in (directory / "bootloader.bin", directory / "application.bin"):
        with open(path, "rb") as stream:
            os.fsync(stream.fileno())
    sync_directory(directory)
    sync_directory(directory.parent)
    return digest(app)


def admit_recovery(evidence):
    value = json.loads(no_links(evidence).read_text())
    if (
        value.get("model") != "Q2"
        or value.get("soc") != policy.SOC_VERSION
        or value.get("bootloader_sha256") != BOOT
        or value.get("independent_recovery_verified") is not True
        or not isinstance(value.get("method"), str)
        or not value["method"].strip()
        or not isinstance(value.get("verification"), str)
        or not value["verification"].strip()
    ):
        raise ValueError("Independent Q2 recovery entry is not documented as verified")
    return value


class Machine:
    def __init__(self, root):
        self.root = root

    def query(self, names):
        url = "http://127.0.0.1:7125/printer/objects/query?" + "&".join(
            urllib.parse.quote(n) for n in names
        )
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.load(response)["result"]["status"]

    def idle(self):
        firmware = json.loads(
            (self.root / "home/qidi/update/firmware_manifest.json").read_text()
        )["SOC"]
        if firmware["version"] != policy.SOC_VERSION or not firmware["file"].startswith(
            "QD_Q2_SOC_" + policy.SOC_VERSION + "_"
        ):
            raise ValueError("Not the admitted Q2 SOC")
        names = [
            "print_stats",
            "webhooks",
            "idle_timeout",
            "heaters",
            "box_extras",
            "tltg_box_rfid",
            "configfile",
        ]
        first = self.query(names)
        heaters = first["heaters"]["available_heaters"]
        if (
            not isinstance(heaters, list)
            or not 1 <= len(heaters) <= 32
            or not all(isinstance(n, str) and n for n in heaters)
            or len(set(heaters)) != len(heaters)
            or not {"extruder", "heater_bed"}.issubset(heaters)
        ):
            raise ValueError("Incomplete heater registry")
        status = self.query(names + heaters)
        if (
            status["heaters"]["available_heaters"] != heaters
            or status["webhooks"]["state"] != "ready"
            or status["print_stats"]["state"]
            not in {"standby", "complete", "cancelled", "error"}
            or status["idle_timeout"]["state"] not in {"Ready", "Idle"}
            or status["box_extras"]["is_tool_change"]
            or status["tltg_box_rfid"]["job"]["running"]
            or status["configfile"]["save_config_pending"]
        ):
            raise ValueError("Printer is not safely idle")
        for name in heaters:
            target = status[name]["target"]
            if (
                isinstance(target, bool)
                or not isinstance(target, (int, float))
                or not math.isfinite(target)
                or target != 0
            ):
                raise ValueError("Heater target must be zero: " + name)
        return status["configfile"]["settings"].get("input_shaper", {})

    def states(self):
        states = {}
        for service in SERVICES:
            result = subprocess.run(
                ["systemctl", "show", service, "-p", "LoadState", "-p", "ActiveState"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            values = dict(
                line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
            )
            if service.endswith(".timer") and values.get("LoadState") == "not-found":
                continue
            if (
                result.returncode
                or values.get("LoadState") != "loaded"
                or values.get("ActiveState")
                not in {
                    "active",
                    "inactive",
                }
            ):
                raise ValueError("Cannot establish service ownership: " + service)
            states[service] = values["ActiveState"]
        return states

    def service(self, action, name):
        subprocess.run(["systemctl", action, name], check=True, timeout=60)

    def tool(self, package, directory, operation, *arguments):
        args = [
            "/home/qidi/klippy-env/bin/python",
            str(package / "scripts/flash_thr_firmware.py"),
            operation,
            *map(str, arguments),
            "--printer-idle-confirmed",
        ]
        with open(directory / (operation + ".log"), "ab", buffering=0) as log:
            return subprocess.run(
                args, stdout=log, stderr=subprocess.STDOUT, timeout=960
            ).returncode

    def wait_application(self):
        time.sleep(12)

    def healthy(self):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            try:
                self.idle()
                return
            except (OSError, ValueError, KeyError):
                time.sleep(2)
        raise RuntimeError("Printer readiness not restored")


def deploy(package, data_root, evidence, machine):
    package, data_root = no_links(package), no_links(data_root)
    verify_package(package)
    recovery = admit_recovery(evidence)
    marker = no_links(data_root / ".tltg_thr_firmware_pending.json")
    if marker.exists():
        raise ValueError("Unresolved THR operation; inspect existing recovery marker")
    # A file lock covers preflight through ready verification; a second invocation cannot race the marker.
    lock_path = no_links(data_root / ".q2_thr_maintenance.lock")
    with open(lock_path, "a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = {
            number: signal.signal(number, signal.SIG_IGN)
            for number in (signal.SIGHUP, signal.SIGINT)
        }
        try:
            return transaction(package, data_root, marker, recovery, machine)
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)


def transaction(package, data_root, marker, recovery, machine):
    if marker.exists():
        raise ValueError("Unresolved THR operation")
    shaper = machine.idle()
    states = machine.states()
    parent = no_links(data_root / ".tltg_thr_firmware_backups")
    parent.mkdir(mode=0o700, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="q2-thr-", dir=parent))
    sync_directory(parent)
    sync_directory(data_root)
    record = {
        "version": VERSION,
        "phase": "stopping_services",
        "backup_directory": str(directory),
        "services": states,
        "recovery_evidence": recovery,
        "programming_may_have_started": False,
    }
    write_json(directory / "journal.json", record)
    write_json(marker, record)
    verified = False
    outcome = None
    try:
        for service in reversed(SERVICES):
            if service in states:
                machine.service("stop", service)
        before = directory / "before"
        if machine.tool(package, directory, "snapshot", "--output-dir", before) != 0:
            raise RuntimeError("Pre-flash snapshot failed; no programming requested")
        current = verify_snapshot(before, {STOCK, PATCHED})
        if current == PATCHED:
            outcome = "already-current"
            verified = True
        else:
            # Durable uncertainty marker precedes invocation, including reset and any potential erase.
            record.update(phase="programming", programming_may_have_started=True)
            write_json(directory / "journal.json", record)
            write_json(marker, record)
            code = machine.tool(
                package,
                directory,
                "transfer",
                "--image",
                package / "candidate.bin",
                "--backup-dir",
                before,
                "--reset",
                "--confirm-write",
                "--recover-to-stock",
                "--firmware",
                policy.SOC_VERSION,
            )
            if code not in (0, 4, 5):
                raise RuntimeError(
                    "Transfer/recovery unresolved; leave services stopped"
                )
            machine.wait_application()
            after = directory / "after"
            if machine.tool(package, directory, "snapshot", "--output-dir", after) != 0:
                raise RuntimeError("Post-flash snapshot failed; leave services stopped")
            expected = STOCK if code == 4 else PATCHED
            verify_snapshot(after, {expected})
            outcome = "fell-back-to-stock" if code == 4 else "flashed"
            if outcome == "flashed":
                logs = no_links(data_root / "logs")
                logs.mkdir(exist_ok=True)
                write_json(logs / "tltg_input_shaper_thr_flash.json", shaper)
        record.update(phase="verified", outcome=outcome)
        write_json(directory / "verification.json", record)
        verified = True
    finally:
        # Upstream behavior: never restart serial-owning services after an unverified possible write.
        if verified or not record["programming_may_have_started"]:
            failures = []
            for service in SERVICES:
                if states.get(service) == "active":
                    try:
                        machine.service("start", service)
                    except Exception as exc:
                        failures.append(str(exc))
            if failures:
                raise RuntimeError(
                    "Service restore incomplete; marker retained: "
                    + "; ".join(failures)
                )
            machine.healthy()
            marker.unlink()
            fd = os.open(data_root, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    return {
        "outcome": outcome,
        "verified": verified,
        "backup_directory": str(directory),
        "recalibration_required": outcome == "flashed",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["prepare", "dry-run", "apply"])
    parser.add_argument("--upstream", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--recovery-evidence", type=Path)
    parser.add_argument("--confirm-write", action="store_true")
    args = parser.parse_args()
    if args.operation == "prepare":
        if args.upstream is None or args.candidate is None:
            parser.error("prepare requires --upstream and --candidate")
        prepare(args.upstream, args.candidate, args.package)
        print("Prepared pinned Q2 THR tools; no printer access")
    elif args.operation == "dry-run":
        verify_package(args.package)
        print(
            json.dumps(
                {
                    "version": VERSION,
                    "model": "Q2",
                    "soc": policy.SOC_VERSION,
                    "application": PATCHED,
                    "bootloader": BOOT,
                    "uart_accessed": False,
                    "recover_to_stock": True,
                    "recovery_entry_still_required": True,
                },
                indent=2,
            )
        )
    else:
        if not args.confirm_write or args.recovery_evidence is None:
            parser.error("apply requires --confirm-write and --recovery-evidence")
        if os.geteuid() != 0:
            parser.error("apply requires authorized system-service execution")
        print(
            json.dumps(
                deploy(
                    args.package,
                    Path("/home/qidi/printer_data"),
                    args.recovery_evidence,
                    Machine(Path("/")),
                ),
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
