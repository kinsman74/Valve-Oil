"""Execute the new Thumb handlers with emulated RAM and stubbed stock helpers."""
import json
import struct
import unittest
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent
BASE, RAM, STOP = 0x08008000, 0x20000000, 0x08040000
REGISTERS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)


def run(address, payload=None, selected=True, cascade=False, bits=16, error=0, oid=0):
    emulator = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    emulator.mem_map(0x08000000, 0x50000)
    emulator.mem_map(RAM, 0x10000)
    emulator.mem_write(BASE, (ROOT / "q2-box-valve-rfid-dev1.bin").read_bytes())
    stack = RAM + 0xFF00
    emulator.reg_write(UC_ARM_REG_SP, stack)
    emulator.reg_write(UC_ARM_REG_LR, STOP | 1)
    table, obj, spi, args, data = (RAM + value for value in (0x1000, 0x2000, 0x3000, 0x4000, 0x5000))
    emulator.mem_write(RAM + 0x1B8, b"\x01")
    emulator.mem_write(RAM + 0x1BC, struct.pack("<I", table))
    emulator.mem_write(table, struct.pack("<II", 0x0800A841, obj))
    emulator.mem_write(obj + 0x10, struct.pack("<I", spi))
    packet = payload if payload is not None else b""
    emulator.mem_write(args, struct.pack("<III", oid, len(packet), data))
    if packet:
        emulator.mem_write(data, packet)
    emulator.reg_write(UC_ARM_REG_R0, args)
    result = {"calls": [], "response": None}
    register = 0
    values = {0x14: 0x83, 0x15: 0x40, 0x08: 0x08}

    def read_word(pointer):
        return struct.unpack("<I", emulator.mem_read(pointer, 4))[0]

    def hook(uc, pc, size, user):
        nonlocal register
        if pc == STOP:
            uc.emu_stop()
            return
        registers = [uc.reg_read(reg) for reg in REGISTERS]
        r0, r1, r2, r3 = registers
        if pc == 0x08009630:
            result["invalid_oid"] = True
            uc.emu_stop()
            return
        if pc == 0x080083A4:
            pointer = read_word(uc.reg_read(UC_ARM_REG_SP))
            result["response"] = {"encoder": r0, "oid": r1, "status": r2,
                                  "data": bytes(uc.mem_read(pointer, r3)).hex()}
        elif pc == 0x0800A674:
            assert r0 == spi
            packet = bytes(uc.mem_read(r3, r2))
            if r2 == 1 and packet[0] & 0x80:
                register = (packet[0] & 0x7F) >> 1
            elif r2 == 1 and r1:
                uc.mem_write(r3, bytes([values.get(register, 0)]))
            elif r2 == 2:
                values[packet[0] >> 1] = packet[1]
            else:
                raise AssertionError(("Unexpected SPI transfer", packet))
        elif pc in (0x0800EBE4, 0x0800EC34, 0x0800E9BC):
            result["calls"].append([hex(pc), r1, r2])
        elif pc == 0x0800AC44:
            rx = read_word(uc.reg_read(UC_ARM_REG_SP))
            bit_pointer = read_word(uc.reg_read(UC_ARM_REG_SP) + 4)
            receive_bits = bits if payload is not None else 16
            uc.mem_write(bit_pointer, struct.pack("<i", receive_bits))
            uc.mem_write(rx, b"\x44\x00" if payload is None else bytes(range(96)))
            uc.reg_write(UC_ARM_REG_R0, error if selected else 1)
        elif pc == 0x0800AF44:
            uc.mem_write(r2, b"\x01\x02\x03\x04\x04")
            uc.reg_write(UC_ARM_REG_R0, 0)
        elif pc == 0x0800B09C:
            uc.mem_write(r3, bytes([4 if cascade and r1 == 0x93 else 8]))
            uc.reg_write(UC_ARM_REG_R0, 0)
        else:
            return
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    emulator.hook_add(UC_HOOK_CODE, hook)
    emulator.emu_start(address | 1, STOP + 2, count=100000)
    if not result.get("invalid_oid"):
        assert emulator.reg_read(UC_ARM_REG_PC) == STOP
        assert emulator.reg_read(UC_ARM_REG_SP) == stack
        assert result["response"] is not None
    return result


class HandlerTests(unittest.TestCase):
    def test_select(self):
        response = run(0x0800B4C8)["response"]
        self.assertEqual((response["encoder"], response["oid"], response["status"]),
                         (0x0800EEB4, 0, 1))
        self.assertEqual(len(bytes.fromhex(response["data"])), 20)

    def test_select_failure(self):
        self.assertEqual(run(0x0800B4C8, selected=False)["response"]["status"], 0)

    def test_select_cascade(self):
        self.assertEqual(run(0x0800B4C8, cascade=True)["response"]["status"], 1)

    def test_invalid_oid(self):
        self.assertTrue(run(0x0800B4C8, oid=1)["invalid_oid"])

    def test_transceive(self):
        response = run(0x0800A920, b"\x0c\x03\x30\x04", bits=128)["response"]
        self.assertEqual((response["encoder"], response["status"]), (0x0800EEC4, 1))
        self.assertEqual(bytes.fromhex(response["data"])[4:], bytes(range(16)))

    def test_transceive_error(self):
        self.assertEqual(run(0x0800A920, b"\x0c\x03\x30", error=1)["response"]["status"], 0)

    def test_transceive_bounds(self):
        for bits in (-1, 0, 768):
            data = bytes.fromhex(run(0x0800A920, b"\x0c\x03\x30", bits=bits)["response"]["data"])
            self.assertLessEqual(len(data), 48)
            self.assertEqual(len(data), 4 if bits <= 0 else 48)

    def test_transceive_invalid_packet(self):
        for packet in (b"", b"\x0c", b"\xff\x03\x30", b"\x0c" * 35):
            response = run(0x0800A920, packet)["response"]
            self.assertEqual(response["status"], 0)
            self.assertEqual(len(bytes.fromhex(response["data"])), 4)


if __name__ == "__main__":
    unittest.main()
