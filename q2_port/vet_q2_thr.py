"""Offline application-level vetting against QIDI's independently downloaded Q2 ZIP."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile
import zlib

from provenance import verify_group
import policy

VENDOR_ARCHIVE_SHA256 = (
    "b42f83d0e1bbc002e62db6276c2a5739fb3343522ee071829ff8c5f56f7f2fcb"
)
VENDOR_URL = "https://public-cdn.qidimaker.com/upgrade/3DPrinter/QD_Q2/01.01.03.02/yjwvejt6ui/QD_Q2_01.01.03.02_20261023_Release.zip"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def vet(args):
    require(__debug__, "Optimized Python is unsupported for imported verification")
    verify_group(args.upstream, "upstream")
    hasher = hashlib.sha256()
    with args.qidi_archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    require(hasher.hexdigest() == VENDOR_ARCHIVE_SHA256, "Unknown QIDI Q2 archive")
    with zipfile.ZipFile(args.qidi_archive) as archive:
        require(
            archive.namelist().count("firmware_manifest.json") == 1,
            "Ambiguous vendor manifest",
        )
        vendor = json.loads(archive.read("firmware_manifest.json"))
        require(
            vendor["SOC"]["version"] == policy.SOC_VERSION
            and vendor["SOC"]["file"].startswith("QD_Q2_SOC_"),
            "Wrong vendor model/version",
        )
        member = vendor["THR"]["file"]
        require(
            member == "QD_Q2_THR_02.02.01.08_20260303.bin", "Unexpected Q2 THR member"
        )
        require(archive.namelist().count(member) == 1, "Ambiguous toolhead member")
        original = archive.read(member)  # zipfile also verifies the member CRC.
        crc = archive.getinfo(member).CRC
    require(
        digest(original) == policy.STOCK_THR_SHA, "Q2 THR differs from admitted image"
    )
    sys.path.insert(0, str(args.upstream.resolve() / "scripts"))
    from build_thr_firmware import patch_thr
    from check_thr_firmware import check_fifo_execution, emulate_identify, CHECKS
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_MCLASS, CS_MODE_THUMB

    manifest = json.loads(
        (args.upstream / "firmware/max4-thr-valve-oil-v1.json").read_text()
    )
    require(
        digest(original) == manifest["thr"]["stock_sha256"],
        "Q2/Valve Oil inputs differ",
    )
    candidate = patch_thr(original, manifest)
    require(
        candidate == args.candidate.read_bytes(),
        "Fresh Q2 build differs from port candidate",
    )
    require(
        (len(candidate), digest(candidate))
        == policy.FIRMWARE["q2-thr-valve-oil-fifo.bin"],
        "Unexpected candidate identity",
    )
    require(candidate == patch_thr(original, manifest), "Build is not reproducible")
    require(original[:8] == candidate[:8], "Application vector table entry changed")
    allowed, fifo_offsets, disassembly = set(), set(), []
    base = int(manifest["thr"]["load_address"], 0)
    for patch in manifest["thr"]["patches"]:
        offset = int(patch["offset"], 0)
        replacement = bytes.fromhex(patch["after"])
        allowed.update(range(offset, offset + len(replacement)))
        require(
            candidate[offset : offset + len(replacement)] == replacement,
            "Wrong replacement bytes",
        )
        if "before" not in patch:
            require(
                digest(original[offset : offset + len(replacement)])
                == patch["before_sha256"],
                "Dictionary preimage differs",
            )
            continue
        before = bytes.fromhex(patch["before"])
        require(
            original[offset : offset + len(before)] == before,
            "Q2 instruction preimage differs",
        )
        require(len(before) == len(replacement), "Instruction block length changed")
        if offset in CHECKS[manifest["patch_id"]]["fifo_offsets"]:
            fifo_offsets.update(range(offset, offset + len(before)))
        engine = Cs(CS_ARCH_ARM, CS_MODE_MCLASS | CS_MODE_THUMB)
        disassembly.append(
            {
                "offset": hex(offset),
                "before": [
                    f"{i.address:#010x}: {i.mnemonic} {i.op_str}"
                    for i in engine.disasm(before, base + offset)
                ],
                "after": [
                    f"{i.address:#010x}: {i.mnemonic} {i.op_str}"
                    for i in engine.disasm(replacement, base + offset)
                ],
            }
        )
    changed = {i for i, (a, b) in enumerate(zip(original, candidate)) if a != b}
    require(changed <= allowed, "Unexpected changes outside patch sites")
    require(len(changed & fifo_offsets) == 5, "Unexpected FIFO code delta")
    check_fifo_execution(original, candidate, manifest)
    old = json.loads(zlib.decompress(emulate_identify(original, manifest)))
    new = json.loads(zlib.decompress(emulate_identify(candidate, manifest)))
    versions = {"vendor": old["version"], "patched": new["version"]}
    new["version"] = old["version"]
    require(
        old == new, "Commands, constants or dictionary fields changed beyond version"
    )
    rejections = {}
    damaged = bytearray(original)
    damaged[100] ^= 1
    for name, data in [
        ("modified_input", bytes(damaged)),
        ("already_patched_input", candidate),
    ]:
        try:
            patch_thr(data, manifest)
        except ValueError:
            rejections[name] = True
        else:
            raise ValueError("Unsafe input accepted: " + name)
    require(not args.output.exists(), "Choose a new output directory")
    args.output.mkdir(parents=True)
    (args.output / "q2-thr-fifo-verified.bin").write_bytes(candidate)
    result = {
        "scope": "offline application-level analysis; no device or UART access",
        "vendor_source_page": "https://www.qidimaker.com/en/downloads/firmware/Q2",
        "vendor_url": VENDOR_URL,
        "archive_sha256": hasher.hexdigest(),
        "archive_fingerprint_note": "Measured direct official download, not a vendor digital signature",
        "vendor_soc": vendor["SOC"]["version"],
        "vendor_thr_member": member,
        "vendor_thr_crc32": f"{crc:08x}",
        "vendor_thr_bytes": len(original),
        "vendor_thr_sha256": digest(original),
        "same_as_valve_oil_expected_stock_image": True,
        "candidate_sha256": digest(candidate),
        "same_as_existing_q2_port_candidate": True,
        "application_vectors": [hex(n) for n in struct.unpack_from("<II", original)],
        "mcu": old["config"].get("MCU"),
        "clock_hz": old["config"].get("CLOCK_FREQ"),
        "versions": versions,
        "fifo_instruction_bytes_changed": len(changed & fifo_offsets),
        "all_other_changes": "Three identify-length instruction sites and version-only compressed dictionary",
        "disassembly": disassembly,
        "emulation_cases": 1024,
        "emulation_scope": "All 256 FIFO status values, two report-buffer states, stock and patched; SPI/timer/report calls stubbed",
        "dictionary_equivalence": "All fields identical after normalizing version",
        "input_rejections": rejections,
        "q2_soc_in_upstream_thr_targets": policy.SOC_VERSION in manifest["targets"],
        "physical_device_admission": "not performed",
        "q2_uart_reset_bootloader_recovery": "not qualified by this analysis",
        "physical_sampling_and_calibration_quality": "not measured",
        "flashing_authorized_or_performed": False,
    }
    (args.output / "vetting-report.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("qidi-archive", "upstream", "candidate", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    vet(parser.parse_args())


if __name__ == "__main__":
    main()
