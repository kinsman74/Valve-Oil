"""Run against the local preview/snapshot; never connects to a printer."""

import argparse
import hashlib
import json
import shutil
import tempfile
import subprocess
import sys
from provenance import verify_group
import unittest
from pathlib import Path
import plan as planner

BUNDLE = SNAPSHOT = None


def digest_tree(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


class BundleTests(unittest.TestCase):
    def test_plan_is_read_only_and_excludes_motion(self):
        before = digest_tree(SNAPSHOT)
        r = planner.plan(BUNDLE, SNAPSHOT)
        self.assertEqual(before, digest_tree(SNAPSHOT))
        m = json.loads((BUNDLE / "manifest.json").read_text())
        targets = [o["target"] for o in m["operations"]]
        self.assertFalse(
            any("/klipper-macros-qd/" in t or "/homing.py" in t for t in targets)
        )
        self.assertTrue(m["no_live_flash"])
        self.assertEqual(r["blocked_source_transforms"], [])

    def test_file_copy_simulation_repeat_and_restore(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            shutil.copytree(SNAPSHOT, root)
            baseline = digest_tree(root)
            m = json.loads((BUNDLE / "manifest.json").read_text())
            planner.plan(BUNDLE, root)
            backups = {}
            installed = {}
            for o in m["operations"]:
                p = planner.safe(root, o["target"])
                old = p.read_bytes() if p.exists() else b""
                new = planner.desired(BUNDLE, o, old)
                if p.exists() and old == new:
                    continue
                backups[o["target"]] = p.read_bytes() if p.exists() else None
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(new)
                installed[o["target"]] = planner.sha(new)
            after = planner.plan(BUNDLE, root)
            self.assertEqual(after["counts"]["replace"] + after["counts"]["create"], 0)
            for n, digest in installed.items():
                self.assertEqual(
                    planner.sha(planner.safe(root, n).read_bytes()), digest
                )
            for n, data in backups.items():
                p = planner.safe(root, n)
                if data is None:
                    p.unlink()
                else:
                    p.write_bytes(data)
            self.assertEqual(digest_tree(root), baseline)

    def test_config_calibration_and_stock_motion_preserved(self):
        data = (SNAPSHOT / "home/qidi/printer_data/config/printer.cfg").read_bytes()
        m = json.loads((BUNDLE / "manifest.json").read_text())
        o = next(o for o in m["operations"] if o["kind"] == "config_sections")
        new = planner.desired(BUNDLE, o, data)
        marker = b"#*# <---------------------- SAVE_CONFIG"
        self.assertEqual(data.split(marker, 1)[1], new.split(marker, 1)[1])
        self.assertEqual(planner.overlay_config(new, o["sections"]), new)
        projected = data.decode()
        for s in o["sections"]:
            projected = projected.replace("[" + s + "]", "#[disabled " + s + "]")
        added = planner.overlay_config(projected.encode(), o["sections"])
        self.assertEqual(added.split(marker, 1)[1], data.split(marker, 1)[1])

    def test_drift_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(SNAPSHOT, root, dirs_exist_ok=True)
            p = root / "home/qidi/moonraker/moonraker/components/klippy_apis.py"
            p.write_bytes(p.read_bytes() + b"\n# owner edit\n")
            before = digest_tree(root)
            with self.assertRaisesRegex(ValueError, "Target drift"):
                planner.plan(BUNDLE, root)
            self.assertEqual(before, digest_tree(root))

    def test_config_drift_is_not_accepted_as_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(SNAPSHOT, root, dirs_exist_ok=True)
            p = root / "home/qidi/printer_data/config/printer.cfg"
            manifest = json.loads((BUNDLE / "manifest.json").read_text())
            operation = next(
                o for o in manifest["operations"] if o["kind"] == "config_sections"
            )
            p.write_bytes(
                planner.desired(BUNDLE, operation, p.read_bytes())
                + b"\n# operator edit after snapshot\n"
            )
            with self.assertRaisesRegex(ValueError, "Target drift"):
                planner.plan(BUNDLE, root)

    def test_nginx_drift_is_not_accepted_as_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(SNAPSHOT, root, dirs_exist_ok=True)
            p = root / "etc/nginx/sites-available/fluidd"
            p.write_bytes(p.read_bytes() + b"\n# local route change\n")
            with self.assertRaisesRegex(ValueError, "Target drift"):
                planner.plan(BUNDLE, root)

    def test_unsupported_firmware_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(SNAPSHOT, root, dirs_exist_ok=True)
            p = root / "home/qidi/update/firmware_manifest.json"
            m = json.loads(p.read_text())
            m["SOC"]["version"] = "99.0.0"
            p.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, "Unsupported SOC"):
                planner.plan(BUNDLE, root)

    def test_target_traversal_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "escape").symlink_to("/tmp")
            for n in ("../bad", "/etc/passwd", "escape/bad"):
                with self.assertRaises(ValueError):
                    planner.safe(root, n)

    def test_payload_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(BUNDLE, root, dirs_exist_ok=True)
            p = root / "payload/home/qidi/klipper/klippy/extras/tltg_box_rfid.py"
            p.write_bytes(p.read_bytes() + b"\n# unexpected\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                planner.plan(root, SNAPSHOT)

    def rewrite_inventory(self, root):
        inventory = {
            p.relative_to(root).as_posix(): planner.sha(p.read_bytes())
            for p in root.rglob("*")
            if p.is_file() and p.relative_to(root).as_posix() != "SHA256SUMS.json"
        }
        (root / "SHA256SUMS.json").write_text(json.dumps(inventory))

    def test_rehashed_motion_operation_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "bundle"
            shutil.copytree(BUNDLE, root)
            path = root / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["operations"][0]["target"] = (
                "home/qidi/klipper/klippy/extras/homing.py"
            )
            path.write_text(json.dumps(manifest))
            self.rewrite_inventory(root)
            with self.assertRaisesRegex(ValueError, "Out-of-scope"):
                planner.plan(root, SNAPSHOT)

    def test_rehashed_firmware_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "bundle"
            shutil.copytree(BUNDLE, root)
            path = root / "firmware/q2-thr-valve-oil-fifo.bin"
            data = bytearray(path.read_bytes())
            data[100] ^= 1
            path.write_bytes(data)
            self.rewrite_inventory(root)
            with self.assertRaisesRegex(ValueError, "Firmware identity mismatch"):
                planner.plan(root, SNAPSHOT)

    def test_missing_source_pin_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "Pinned source mismatch"):
                verify_group(Path(td), "q2_adapter")

    def test_optimized_firmware_builder_refuses_before_inputs(self):
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                str(Path(__file__).with_name("build_firmware.py")),
                "--help",
            ],
            capture_output=True,
            text=True,
        )
        # Help may run before admission; actual build must refuse optimized execution.
        self.assertEqual(result.returncode, 0)
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                str(Path(__file__).with_name("build_firmware.py")),
                "--upstream",
                "/missing",
                "--q2-port",
                "/missing",
                "--thr",
                "/missing",
                "--output",
                "/tmp/not-created-q2-audit",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("optim", (result.stdout + result.stderr).lower())

    def test_metadata_preserves_unknown_fields_and_rejects_wrong_printer(self):
        operation = {"kind": "metadata"}
        before = {
            "custom": "keep",
            "printer": {"id": "q2"},
            "release": {"timestamp": 123},
        }
        after = json.loads(
            planner.desired(BUNDLE, operation, json.dumps(before).encode())
        )
        self.assertEqual(after["custom"], "keep")
        self.assertEqual(after["release"]["timestamp"], 123)
        self.assertEqual(
            json.loads(planner.desired(BUNDLE, operation, b""))["printer"]["id"], "q2"
        )
        with self.assertRaisesRegex(ValueError, "another printer"):
            planner.desired(BUNDLE, operation, b'{"printer":{"id":"plus5"}}')

    def test_standalone_planner_repeats_without_creating_cache(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "bundle"
            shutil.copytree(BUNDLE, root)
            before = digest_tree(root)
            for _ in range(2):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(root / "plan.py"),
                        "--dry-run",
                        "--snapshot",
                        str(SNAPSHOT.resolve()),
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, digest_tree(root))

    def test_catalog_preserves_existing_entries(self):
        m = json.loads((BUNDLE / "manifest.json").read_text())
        o = next(o for o in m["operations"] if o["kind"] == "catalog_merge")
        before = json.loads(planner.safe(SNAPSHOT, o["target"]).read_text())
        before["Operator owned test"] = {
            "filament_id": "QZZ42",
            "type": "PLA",
            "filament_vendor": "Example",
        }
        encoded = json.dumps(before).encode()
        after = json.loads(planner.desired(BUNDLE, o, encoded))
        self.assertTrue(all(after[k] == v for k, v in before.items()))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--snapshot", type=Path, required=True)
    a, rest = p.parse_known_args()
    BUNDLE = a.bundle
    SNAPSHOT = a.snapshot
    unittest.main(argv=["test_bundle", *rest])
