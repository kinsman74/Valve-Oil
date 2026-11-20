"""Check the experimental Q2 image and its host response guard."""
import hashlib
import importlib.util
import json
import struct
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("q2_guard", ROOT / "src/inventory_rfid_read_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PortTests(unittest.TestCase):
    def test_image_contract(self):
        stock = (ROOT / "QD_Q2_BOX_02.03.01.13_20251127.bin").read_bytes()
        image = (ROOT / "q2-box-valve-rfid-dev1.bin").read_bytes()
        report = json.loads((ROOT / "build-report.json").read_text())
        self.assertEqual(hashlib.sha256(image).hexdigest(), report["output_sha256"])
        self.assertEqual(len(stock), len(image))
        self.assertEqual(stock[:0x100], image[:0x100])
        a = json.loads(zlib.decompress(stock[0x6efc:]))
        b = json.loads(zlib.decompress(image[0x6efc:]))
        for key in ("config", "enumerations", "output", "app", "license", "build_versions"):
            self.assertEqual(a[key], b[key])
        self.assertEqual(b["commands"]["fm17550_read_card_cb oid=%c"], 16)
        self.assertEqual(b["commands"]["fm17550_select oid=%c"], 15)
        self.assertEqual(b["commands"]["fm17550_transceive oid=%c data=%*s"], 17)
        self.assertEqual(b["responses"]["fm17550_select_return oid=%c status=%c data=%*s"], 91)
        self.assertEqual(b["responses"]["fm17550_transceive_return oid=%c status=%c data=%*s"], 93)
        self.assertEqual(struct.unpack_from("<I", image, 0x7a48 + 15 * 16 + 12)[0], 0x0800b4c9)
        self.assertEqual(struct.unpack_from("<I", image, 0x7a48 + 17 * 16 + 12)[0], 0x0800a921)

    def test_vendor_result_then_empty_then_same_result(self):
        scan = guard.Scan()
        payload = bytes([65, 2, 17, 6, 6, 6]) + bytes(10)
        good = {"oid": 1, "status": 1, "data": payload}
        self.assertEqual(scan.filter(good), good)
        self.assertEqual(scan.filter({"oid": 1, "status": 1, "data": bytes(16)})["status"], 0)
        self.assertEqual(scan.filter(good), good)
        self.assertEqual(scan.summary()["empty"], 1)

    def test_conflicting_vendor_results_quarantine_scan(self):
        scan = guard.Scan()
        a = {"status": 1, "data": bytes([65, 2, 17, 6, 6, 6]) + bytes(10)}
        b = {"status": 1, "data": bytes([65, 2, 18, 6, 6, 6]) + bytes(10)}
        self.assertEqual(scan.filter(a)["status"], 1)
        self.assertEqual(scan.filter(b)["status"], 0)
        self.assertEqual(scan.filter(a)["status"], 0)
        self.assertFalse(guard.Scan().conflict)


if __name__ == "__main__":
    unittest.main()
