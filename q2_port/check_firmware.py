"""Offline emulation of the exact candidate bytes; no hardware access."""

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    require(__debug__, "Optimized Python is unsupported for upstream emulation checks")
    p = argparse.ArgumentParser()
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--q2-port", type=Path, required=True)
    p.add_argument("--thr-stock", type=Path, required=True)
    p.add_argument("--firmware", type=Path, required=True)
    a = p.parse_args()
    from provenance import verify_group

    verify_group(a.upstream, "upstream")
    verify_group(a.q2_port, "q2_adapter")
    sys.path.insert(0, str(a.upstream.resolve() / "scripts"))
    from check_thr_firmware import check_fifo_execution, emulate_identify

    m = json.loads((a.upstream / "firmware/max4-thr-valve-oil-v1.json").read_text())
    import policy

    stock = a.thr_stock.read_bytes()
    require(
        hashlib.sha256(stock).hexdigest() == policy.STOCK_THR_SHA, "Wrong stock THR"
    )
    thr = (a.firmware / "q2-thr-valve-oil-fifo.bin").read_bytes()
    require(
        (len(thr), hashlib.sha256(thr).hexdigest())
        == policy.FIRMWARE["q2-thr-valve-oil-fifo.bin"],
        "Wrong THR candidate",
    )
    check_fifo_execution(stock, thr, m)
    old = json.loads(zlib.decompress(emulate_identify(stock, m)))
    new = json.loads(zlib.decompress(emulate_identify(thr, m)))
    old["version"] = new["version"]
    require(old == new, "Firmware verification failed")
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE
    from unicorn.arm_const import (
        UC_ARM_REG_R0,
        UC_ARM_REG_R1,
        UC_ARM_REG_SP,
        UC_ARM_REG_LR,
    )

    box = (a.firmware / "q2-box-valve-rfid-dev1.bin").read_bytes()
    require(
        (len(box), hashlib.sha256(box).hexdigest())
        == policy.FIRMWARE["q2-box-valve-rfid-dev1.bin"],
        "Wrong Box candidate",
    )
    original = (a.q2_port / "QD_Q2_BOX_02.03.01.13_20251127.bin").read_bytes()
    d = json.loads(zlib.decompress(box[28412:]))
    require(
        d["commands"]["debug_read order=%c addr=%u"] == 12
        and d["responses"]["debug_result val=%u"] == 90,
        "Firmware verification failed",
    )
    require(original[5292:5360] == box[5292:5360], "Firmware verification failed")
    cases = 0
    for addr, value in [(536836652, 837), (536836654, 1383)]:
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        u.mem_map(134217728, 196608)
        u.mem_map(536870912, 65536)
        u.mem_map(536834048, 4096)
        u.mem_write(134250496, box)
        u.mem_write(addr, struct.pack("<H", value))
        u.mem_write(536875008, struct.pack("<II", 1, addr))
        u.reg_write(UC_ARM_REG_R0, 536875008)
        u.reg_write(UC_ARM_REG_SP, 536936192)
        u.reg_write(UC_ARM_REG_LR, 134348801)
        captured = []

        def hook(machine, pc, size, data):
            if pc == 134251428:
                captured.append(
                    (machine.reg_read(UC_ARM_REG_R0), machine.reg_read(UC_ARM_REG_R1))
                )
                machine.emu_stop()

        u.hook_add(UC_HOOK_CODE, hook)
        u.emu_start(134255789, 134348800, count=100)
        require(
            len(captured) == 1 and captured[0][1] == value,
            "Firmware verification failed",
        )
        require(
            struct.unpack_from("<H", box, captured[0][0] - 134250496)[0] == 90,
            "Firmware verification failed",
        )
        cases += 1
    result = {
        "thr_fifo": "all upstream status/buffer cases passed",
        "thr_identify": "version-only dictionary difference",
        "box_standard_debug_read": "unchanged handler and command; both STM32F4 calibration halfwords emulated",
        "box_calibration_cases": cases,
        "physical_temperature_sensor": "not exercised",
        "physical_new_thr": "not flashed or qualified",
        "mode": "offline-only",
    }
    (a.firmware / "emulation-report.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
