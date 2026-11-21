"""Local transaction tests with fake service activation; never contacts a printer."""

import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

import host_deploy as deploy
import policy
from plan import sha


class FakeServices:
    def __init__(self, fail_activation=False):
        self.fail_activation = fail_activation
        self.stops = 0

    def idle(self, root):
        pass

    def active(self):
        return list(deploy.SERVICES)

    def stop(self):
        self.stops += 1

    def nginx(self):
        pass

    def start(self, names):
        pass

    def healthy(self):
        if self.fail_activation:
            self.fail_activation = False
            raise RuntimeError("Simulated activation failure")


class HostDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.root, self.package = base / "root", base / "package"
        self.root.mkdir()
        self.package.mkdir()
        self.existing = "home/qidi/fluidd/index.html"
        self.new = "home/qidi/valve-oil-ui-q2/assets/test.js"
        path = self.root / self.existing
        path.parent.mkdir(parents=True)
        path.write_bytes(b"old web")
        path.chmod(0o640)
        operations = []
        for target, content in ((self.existing, b"new web"), (self.new, b"new asset")):
            path = self.package / "rendered" / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            original = self.root / target
            operations.append(
                {
                    "target": target,
                    "kind": "file",
                    "before_sha256": deploy.current(original),
                    "after_sha256": sha(content),
                }
            )
        self.manifest = {
            "upstream_commit": policy.UPSTREAM_COMMIT,
            "no_flash": True,
            "operations": operations,
        }
        self.save_manifest()

    def save_manifest(self):
        (self.package / "deployment.json").write_text(json.dumps(self.manifest))

    def assert_restored(self):
        path = self.root / self.existing
        self.assertEqual(path.read_bytes(), b"old web")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
        self.assertEqual(path.stat().st_uid, os.getuid())
        self.assertFalse((self.root / self.new).exists())

    def test_apply_and_explicit_rollback_preserve_metadata_and_remove_new_files(self):
        services = FakeServices()
        deploy.apply(self.package, self.root, services)
        self.assertEqual((self.root / self.existing).read_bytes(), b"new web")
        self.assertEqual(
            stat.S_IMODE((self.root / self.existing).stat().st_mode), 0o640
        )
        self.assertEqual(stat.S_IMODE((self.root / self.new).stat().st_mode), 0o644)
        state = json.loads((self.package / "journal.json").read_text())
        self.assertEqual(state["firmware_flashes"], 0)
        deploy.restore(self.package, self.root, services, state)
        self.assert_restored()

    def test_activation_failure_automatically_restores_original_files(self):
        with self.assertRaisesRegex(RuntimeError, "activation failure"):
            deploy.apply(self.package, self.root, FakeServices(fail_activation=True))
        self.assert_restored()
        self.assertEqual(
            json.loads((self.package / "journal.json").read_text())["status"],
            "rolled_back",
        )

    def test_target_drift_is_rejected_before_service_stop_or_write(self):
        (self.root / self.existing).write_bytes(b"owner edit")
        services = FakeServices()
        with self.assertRaisesRegex(ValueError, "target drift"):
            deploy.apply(self.package, self.root, services)
        self.assertEqual(services.stops, 0)
        self.assertEqual((self.root / self.existing).read_bytes(), b"owner edit")
        self.assertFalse((self.root / self.new).exists())

    def test_rollback_refuses_later_edits_without_stopping_services(self):
        services = FakeServices()
        deploy.apply(self.package, self.root, services)
        (self.root / self.existing).write_bytes(b"later edit")
        state = json.loads((self.package / "journal.json").read_text())
        stops = services.stops
        with self.assertRaisesRegex(ValueError, "Rollback target drift"):
            deploy.restore(self.package, self.root, services, state)
        self.assertEqual(services.stops, stops)
        self.assertEqual((self.root / self.existing).read_bytes(), b"later edit")

    def test_corrupt_payload_and_motion_target_are_rejected(self):
        rendered = self.package / "rendered" / self.existing
        rendered.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "payload mismatch"):
            deploy.apply(self.package, self.root, FakeServices())
        rendered.write_bytes(b"new web")
        self.manifest["operations"][0]["target"] = (
            "home/qidi/klipper/klippy/extras/homing.py"
        )
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "Out-of-scope"):
            deploy.apply(self.package, self.root, FakeServices())
        self.assert_restored()

    def test_incomplete_or_finished_transaction_is_not_silently_reapplied(self):
        deploy.apply(self.package, self.root, FakeServices())
        with self.assertRaisesRegex(ValueError, "Existing transaction"):
            deploy.apply(self.package, self.root, FakeServices())

    def test_interrupted_transaction_can_roll_back_with_klipper_offline(self):
        deploy.apply(self.package, self.root, FakeServices())
        path = self.package / "journal.json"
        state = json.loads(path.read_text())
        state["status"] = "activating"
        path.write_text(json.dumps(state))
        offline = FakeServices()
        offline.active = lambda: []
        offline.idle = mock.Mock(side_effect=RuntimeError("API offline"))
        deploy.rollback(self.package, self.root, offline)
        offline.idle.assert_not_called()
        self.assert_restored()

    def test_live_admission_rejects_print_heat_box_flow_and_rfid_activity(self):
        path = self.root / "home/qidi/update/firmware_manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "SOC": {
                        "version": policy.SOC_VERSION,
                        "file": "QD_Q2_SOC_" + policy.SOC_VERSION + "_test.bin",
                    }
                }
            )
        )
        for change in ("print", "heater", "task", "rfid"):
            with self.subTest(change=change):
                status = {
                    "print_stats": {"state": "standby"},
                    "idle_timeout": {"state": "Ready"},
                    "extruder": {"target": 0},
                    "multi_color_controller": {"task": {}},
                    "tltg_box_rfid": {"job": {"running": False}},
                }
                if change == "print":
                    status["print_stats"]["state"] = "printing"
                elif change == "heater":
                    status["extruder"]["target"] = 200
                elif change == "task":
                    status["multi_color_controller"]["task"]["current_step"] = (
                        "BOX_LOAD"
                    )
                else:
                    status["tltg_box_rfid"]["job"]["running"] = True
                with mock.patch.object(
                    deploy,
                    "read_api",
                    side_effect=[{"objects": list(status)}, {"status": status}],
                ):
                    with self.assertRaises(ValueError):
                        deploy.admit_idle(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
