"""Transaction boundaries for the separate Q2 toolhead workflow; no printer access."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import thr_deploy as deploy


class Machine:
    def __init__(self, boot, stock, patched):
        self.boot, self.stock, self.patched = boot, stock, patched
        self.current = stock
        self.active = {"klipper.service", "qidi-client.service"}
        self.transfer_code = 0
        self.writes = 0
        self.snapshot_count = 0
        self.fail_snapshot = 0
        self.corrupt_after = False
        self.fail_stop = None
        self.fail_start = None
        self.ready = True

    def idle(self):
        if not self.ready:
            raise ValueError("not idle")
        return {"shaper_freq_x": 46.0, "shaper_freq_y": 43.4}

    def states(self):
        return {
            n: "active" if n in self.active else "inactive" for n in deploy.SERVICES
        }

    def service(self, action, name):
        if action == "stop":
            self.active.discard(name)
            if name == self.fail_stop:
                raise RuntimeError("partial stop failed")
        else:
            if name == self.fail_start:
                raise RuntimeError("start failed")
            self.active.add(name)

    def tool(self, package, directory, operation, *args):
        if operation == "snapshot":
            self.snapshot_count += 1
            if self.snapshot_count == self.fail_snapshot:
                return 1
            path = Path(args[args.index("--output-dir") + 1])
            path.mkdir()
            (path / "bootloader.bin").write_bytes(self.boot)
            data = (
                b"x" * len(self.current)
                if self.corrupt_after and self.writes
                else self.current
            )
            (path / "application.bin").write_bytes(data)
            return 0
        assert operation == "transfer"
        assert "--recover-to-stock" in args and "--confirm-write" in args
        self.writes += 1
        self.current = self.stock if self.transfer_code == 4 else self.patched
        return self.transfer_code

    def wait_application(self):
        pass

    def healthy(self):
        if self.active != {"klipper.service", "qidi-client.service"}:
            raise RuntimeError("original services not restored")


class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.boot, self.stock, self.patched = b"b" * 32768, b"s" * 64, b"p" * 64

        def sha(data):
            return hashlib.sha256(data).hexdigest()

        for name, value in [
            ("BOOT", sha(self.boot)),
            ("STOCK", sha(self.stock)),
            ("PATCHED", sha(self.patched)),
            ("SIZE", 64),
        ]:
            p = patch.object(deploy, name, value)
            p.start()
            self.addCleanup(p.stop)
        # File integrity has separate admission tests; transaction tests inject validated inputs.
        p = patch.object(deploy, "verify_package")
        p.start()
        self.addCleanup(p.stop)
        self.evidence = self.root / "recovery.json"
        self.evidence.write_text(
            json.dumps(
                {
                    "model": "Q2",
                    "soc": deploy.policy.SOC_VERSION,
                    "bootloader_sha256": sha(self.boot),
                    "independent_recovery_verified": True,
                    "method": "fixture",
                    "verification": "fixture",
                }
            )
        )
        self.package = self.root / "package"
        self.package.mkdir()
        self.data = self.root / "printer_data"
        self.data.mkdir()
        self.machine = Machine(self.boot, self.stock, self.patched)
        self.marker = self.data / ".tltg_thr_firmware_pending.json"

    def run_flow(self):
        return deploy.deploy(self.package, self.data, self.evidence, self.machine)

    def test_missing_recovery_refuses_without_serial_or_marker(self):
        self.evidence.write_text("{}")
        with self.assertRaises(ValueError):
            self.run_flow()
        self.assertEqual(self.machine.snapshot_count, 0)
        self.assertFalse(self.marker.exists())

    def test_live_admission_checks_every_registered_heater(self):
        import copy

        firmware = self.root / "home/qidi/update/firmware_manifest.json"
        firmware.parent.mkdir(parents=True)
        firmware.write_text(
            json.dumps(
                {
                    "SOC": {
                        "version": deploy.policy.SOC_VERSION,
                        "file": "QD_Q2_SOC_" + deploy.policy.SOC_VERSION + "_test",
                    }
                }
            )
        )
        heaters = ["extruder", "heater_bed", "heater_generic extra"]
        status = {
            "heaters": {"available_heaters": heaters},
            "webhooks": {"state": "ready"},
            "print_stats": {"state": "standby"},
            "idle_timeout": {"state": "Idle"},
            "box_extras": {"is_tool_change": 0},
            "tltg_box_rfid": {"job": {"running": False}},
            "configfile": {"save_config_pending": False, "settings": {}},
        }
        for heater in heaters:
            status[heater] = {"target": 0}
        machine = deploy.Machine(self.root)
        for bad in [1, True, float("nan"), "0"]:
            changed = copy.deepcopy(status)
            changed["heater_generic extra"]["target"] = bad
            with (
                self.subTest(target=bad),
                patch.object(machine, "query", return_value=changed),
            ):
                with self.assertRaises(ValueError):
                    machine.idle()

    def test_absent_update_timer_does_not_block_service_admission(self):
        from types import SimpleNamespace

        def result(args, **kwargs):
            missing = args[2].endswith(".timer")
            return SimpleNamespace(
                returncode=1 if missing else 0,
                stdout="LoadState=not-found\nActiveState=inactive\n"
                if missing
                else "LoadState=loaded\nActiveState=active\n",
            )

        with patch.object(deploy.subprocess, "run", result):
            self.assertEqual(
                deploy.Machine(self.root).states(),
                {"klipper.service": "active", "qidi-client.service": "active"},
            )

    def test_symlink_evidence_is_rejected(self):
        link = self.root / "evidence-link.json"
        link.symlink_to(self.evidence)
        self.evidence = link
        with self.assertRaises(ValueError):
            self.run_flow()
        self.assertEqual(self.machine.snapshot_count, 0)

    def test_nonidle_refuses(self):
        self.machine.ready = False
        with self.assertRaises(ValueError):
            self.run_flow()
        self.assertEqual(self.machine.writes, 0)

    def test_existing_pending_operation_refuses(self):
        self.marker.write_text("{}")
        with self.assertRaises(ValueError):
            self.run_flow()
        self.assertEqual(self.machine.snapshot_count, 0)

    def test_partial_stop_restores_original_services(self):
        self.machine.fail_stop = "qidi-client.service"
        with self.assertRaises(RuntimeError):
            self.run_flow()
        self.machine.healthy()
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.machine.writes, 0)

    def test_snapshot_failure_recovers_without_writes(self):
        self.machine.fail_snapshot = 1
        with self.assertRaises(RuntimeError):
            self.run_flow()
        self.machine.healthy()
        self.assertFalse(self.marker.exists())

    def test_unknown_bootloader_refuses_programming(self):
        self.machine.boot = b"z" * 32768
        with self.assertRaises(ValueError):
            self.run_flow()
        self.assertEqual(self.machine.writes, 0)
        self.machine.healthy()
        self.assertFalse(self.marker.exists())

    def test_verified_flash_records_recalibration_and_restores(self):
        result = self.run_flow()
        self.assertEqual(result["outcome"], "flashed")
        self.assertTrue(result["recalibration_required"])
        self.assertTrue((self.data / "logs/tltg_input_shaper_thr_flash.json").exists())
        self.machine.healthy()
        self.assertFalse(self.marker.exists())

    def test_verified_fallback_is_not_reported_as_flash(self):
        self.machine.transfer_code = 4
        result = self.run_flow()
        self.assertEqual(result["outcome"], "fell-back-to-stock")
        self.assertFalse(result["recalibration_required"])
        self.assertFalse((self.data / "logs/tltg_input_shaper_thr_flash.json").exists())
        self.machine.healthy()
        self.assertFalse(self.marker.exists())

    def test_end_unconfirmed_requires_successful_full_readback(self):
        self.machine.transfer_code = 5
        self.assertEqual(self.run_flow()["outcome"], "flashed")

    def test_already_current_does_not_program(self):
        self.machine.current = self.patched
        self.assertEqual(self.run_flow()["outcome"], "already-current")
        self.assertEqual(self.machine.writes, 0)

    def test_transfer_failure_keeps_marker_and_services_stopped(self):
        self.machine.transfer_code = 1
        with self.assertRaises(RuntimeError):
            self.run_flow()
        self.assertTrue(self.marker.exists())
        self.assertFalse(self.machine.active)

    def test_readback_mismatch_keeps_marker_and_services_stopped(self):
        self.machine.corrupt_after = True
        with self.assertRaises(ValueError):
            self.run_flow()
        self.assertTrue(self.marker.exists())
        self.assertFalse(self.machine.active)

    def test_post_snapshot_failure_keeps_marker(self):
        self.machine.fail_snapshot = 2
        with self.assertRaises(RuntimeError):
            self.run_flow()
        self.assertTrue(self.marker.exists())
        self.assertFalse(self.machine.active)

    def test_verification_record_failure_keeps_pending_and_stopped(self):
        original_write = deploy.write_json

        def fail_report(path, value):
            if path.name == "verification.json":
                raise OSError("report disk full")
            return original_write(path, value)

        with patch.object(deploy, "write_json", fail_report):
            with self.assertRaises(OSError):
                self.run_flow()
        self.assertTrue(self.marker.exists())
        self.assertFalse(self.machine.active)

    def test_second_operation_refuses_held_maintenance_lock(self):
        import fcntl

        with open(self.data / ".q2_thr_maintenance.lock", "a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                self.run_flow()
        self.assertEqual(self.machine.snapshot_count, 0)

    def test_restore_failure_keeps_marker_but_attempts_other_services(self):
        self.machine.fail_start = "klipper.service"
        with self.assertRaises(RuntimeError):
            self.run_flow()
        self.assertTrue(self.marker.exists())
        self.assertIn("qidi-client.service", self.machine.active)


if __name__ == "__main__":
    unittest.main(verbosity=2)
