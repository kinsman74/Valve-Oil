"""Emulate Q2's original shutdown dispatcher with synthetic configured objects."""
import json
import struct
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC,
    UC_ARM_REG_SP, UC_ARM_REG_LR,
)

ROOT = Path(__file__).resolve().parent


def shutdown(image, reason, kinds):
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    for address, size in [(0x08000000, 0x40000), (0x20000000, 0x10000),
                          (0x40000000, 0x80000), (0x50000000, 0x40000),
                          (0xE0000000, 0x100000)]:
        uc.mem_map(address, size)
    uc.mem_write(0x08008000, image)
    table = 0x20001000
    def word(address, value):
        uc.mem_write(address, struct.pack("<I", value))
    word(0x200001BC, table)
    uc.mem_write(0x200001B8, bytes([len(kinds)]))
    for index, kind in enumerate(kinds):
        obj = 0x20002000 + 0x100 * index
        identity = {"digital": 0x0800A03D, "stepper": 0x08009F9D,
                    "pwm": 0x0800C4A9}[kind]
        word(table + index * 8, identity)
        word(table + index * 8 + 4, obj)
        if kind == "digital":
            word(obj + 0x18, 0x40020000)
            word(obj + 0x1C, 8)
            uc.mem_write(obj + 0x30, b"\x00")  # default low
        elif kind == "pwm":
            word(obj + 0x0C, 0x40001000)
            word(obj + 0x14, 0)  # default zero duty at the Q2 PWM object offset
            uc.mem_write(obj + 0x1C, b"\x00")
    uc.reg_write(UC_ARM_REG_SP, 0x2000FC00)
    uc.reg_write(UC_ARM_REG_R0, reason)
    outcome = {"writes": [], "stepper_cleanups": 0}

    def code(uc, address, size, user):
        if address == 0x0800831C:
            outcome["reentered"] = uc.reg_read(UC_ARM_REG_R0)
            uc.emu_stop()
        elif address == 0x080083A4:
            if uc.reg_read(UC_ARM_REG_R0) == 0x0800EE7C:
                outcome["reported"] = uc.reg_read(UC_ARM_REG_R2)
                uc.emu_stop()
            else:
                raise AssertionError("Unexpected report encoder")
        elif address in (0x08008188, 0x080082B8, 0x080098F8):
            if address == 0x080098F8:
                outcome["stepper_cleanups"] += 1
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def write(uc, access, address, size, value, user):
        if 0x40000000 <= address < 0x50000000:
            outcome["writes"].append([hex(address), size, value])

    uc.hook_add(UC_HOOK_CODE, code)
    uc.hook_add(UC_HOOK_MEM_WRITE, write)
    uc.emu_start(0x08009081, 0xFFFFFFFF, count=100000)
    return outcome


class ShutdownTests(unittest.TestCase):
    def test_original_reason_reaches_report(self):
        results = {}
        for filename in ("QD_Q2_BOX_02.03.01.13_20251127.bin", "q2-box-valve-rfid-dev1.bin"):
            image = (ROOT / filename).read_bytes()
            for kinds in ((), ("digital",), ("stepper",), ("pwm",),
                          ("digital", "stepper", "pwm")):
                for reason in (10, 28, 32):
                    result = shutdown(image, reason, kinds)
                    self.assertNotIn("reentered", result, (filename, kinds, result))
                    self.assertEqual(result.get("reported"), reason, (filename, kinds, result))
                    if "digital" in kinds:
                        self.assertIn(["0x40020018", 4, 8 << 16], result["writes"])
                    if "pwm" in kinds:
                        self.assertIn(["0x40001000", 4, 0], result["writes"])
                    if "stepper" in kinds:
                        self.assertEqual(result["stepper_cleanups"], 1)
                    results[f"{filename}:{','.join(kinds) or 'empty'}:{reason}"] = result
        (ROOT / "shutdown-results.json").write_text(json.dumps(results, indent=2) + "\n")
        print("30 shutdown scenarios passed for stock and RFID candidate")


if __name__ == "__main__":
    unittest.main()
