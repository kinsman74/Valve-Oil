"""Build an experimental Q2 Box RFID image from the pinned stock application."""
import hashlib
import importlib.util
import json
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

import zopfli.zlib

ROOT = Path(__file__).resolve().parent
BASE = 0x08008000
STOCK_SHA = "c09aa5e0a07161f197c597571d96a48ac1cfb3f19a3758576b3428547a424ba9"
STOCK_SIZE = 33776
DICT_OFFSET = 0x6EFC
DICT_BYTES = 2892
VERSION = "KLP_MCU_MKS_V2_1.1.3-q2-valve-rfid-dev1"
FLAGS = ["--target=thumbv7em-none-eabi", "-mcpu=cortex-m4", "-mthumb",
         "-mfloat-abi=soft", "-Os", "-ffreestanding", "-fno-builtin",
         "-fno-common", "-fno-stack-protector", "-fno-jump-tables",
         "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-mno-movt"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def elf_text(path, symbol):
    data = path.read_bytes()
    shoff, = struct.unpack_from("<I", data, 0x20)
    entsize, count, strings = struct.unpack_from("<HHH", data, 0x2E)
    sections = [struct.unpack_from("<10I", data, shoff + n * entsize) for n in range(count)]
    names = sections[strings][4]
    by_name = {data[names + s[0]:].split(b"\0", 1)[0].decode(): s for s in sections}
    if ".rel.text" in by_name or ".rela.text" in by_name:
        raise ValueError("Handler needs unresolved relocations")
    text, symbols = by_name[".text"], by_name[".symtab"]
    strings = sections[symbols[6]][4]
    for offset in range(0, symbols[5], 16):
        name, value, _, _, _, _ = struct.unpack_from("<IIIBBH", data, symbols[4] + offset)
        if data[strings + name:].split(b"\0", 1)[0].decode() == symbol:
            assert value & ~1 == 0
            return data[text[4]:text[4] + text[5]]
    raise ValueError("Missing entry symbol")


def main():
    stock = (ROOT / "QD_Q2_BOX_02.03.01.13_20251127.bin").read_bytes()
    assert len(stock) == STOCK_SIZE and sha(stock) == STOCK_SHA
    patched = bytearray(stock)
    patches = []

    def write(address, data, description):
        offset = address - BASE
        assert 0 <= offset < len(stock) and offset + len(data) <= len(stock)
        assert all(offset + len(data) <= p["offset"] or offset >= p["offset"] + p["size"]
                   for p in patches)
        patches.append({"offset": offset, "size": len(data),
                        "before_sha256": sha(stock[offset:offset + len(data)]),
                        "after_sha256": sha(data), "description": description})
        patched[offset:offset + len(data)] = data

    with tempfile.TemporaryDirectory() as temp:
        for source, symbol, start, end in [
            ("select.c", "fm17550_select_cb", 0x0800B4C8, 0x0800B69C),
            ("transceive.c", "fm17550_transceive_cb", 0x0800A920, 0x0800AAB0),
        ]:
            obj = Path(temp) / (source + ".o")
            subprocess.run(["clang", *FLAGS, "-c", str(ROOT / "src" / source),
                            "-o", str(obj)], check=True)
            code = elf_text(obj, symbol)
            assert len(code) <= end - start
            write(start, code + bytes(end - start - len(code)), symbol)

    table = 0x0800FA48
    old = stock[table - BASE + 17 * 16:table - BASE + 18 * 16]
    msgid, nargs, flags, nparams = struct.unpack_from("<HBBB", old)
    assert (msgid, nargs, nparams) == (17, 1, 1)
    write(table + 17 * 16,
          struct.pack("<HBBB3xII", msgid, 3, flags, 2, 0x0800FF70, 0x0800A921),
          "Command 17 becomes fm17550_transceive")
    for number in (18, 19):
        write(table + 16 * number + 12, struct.pack("<I", 0x08008215),
              f"Retire debug handler {number}")
    for address, msgid in [(0x0800EEB4, 91), (0x0800EEC4, 93)]:
        assert struct.unpack_from("<H", stock, address - BASE)[0] == msgid
        write(address, struct.pack("<HBBI", msgid, 0x40, 3, 0x08010034),
              "RFID response oid, status and buffer")

    original = json.loads(zlib.decompress(stock[DICT_OFFSET:DICT_OFFSET + DICT_BYTES]))
    dictionary = json.loads(json.dumps(original))
    for key in ("fm17550_write_card_cb oid=%c", "fm17550_read_fifo_cb oid=%c",
                "fm17550_read_regs_cb oid=%c", "fm17550_init_cb oid=%c"):
        del dictionary["commands"][key]
    for key in ("fm17550_write_card_return oid=%c status=%c",
                "fm17550_read_fifo_return oid=%c data=%*s",
                "fm17550_read_regs_return oid=%c data=%*s", "fm17550_init_return oid=%c"):
        del dictionary["responses"][key]
    dictionary["commands"].update({"fm17550_select oid=%c": 15,
                                   "fm17550_transceive oid=%c data=%*s": 17})
    dictionary["responses"].update({
        "fm17550_select_return oid=%c status=%c data=%*s": 91,
        "fm17550_transceive_return oid=%c status=%c data=%*s": 93})
    dictionary["version"] = VERSION
    encoded = json.dumps(dictionary, separators=(",", ":"), sort_keys=True).encode()
    compressed = zopfli.zlib.compress(encoded, numiterations=100)
    assert len(compressed) <= DICT_BYTES
    # Preserve identify's existing bounds. zlib accepts the zero-padded compressed stream.
    write(BASE + DICT_OFFSET, compressed + bytes(DICT_BYTES - len(compressed)),
          "Q2 RFID command dictionary, stock identify bounds preserved")
    assert json.loads(zlib.decompress(patched[DICT_OFFSET:DICT_OFFSET + DICT_BYTES])) == dictionary
    for key in ("config", "enumerations"):
        assert dictionary[key] == original[key]
    assert patched[:0x100] == stock[:0x100]
    assert len(patched) == STOCK_SIZE
    for index, (oldbyte, newbyte) in enumerate(zip(stock, patched)):
        assert oldbyte == newbyte or any(p["offset"] <= index < p["offset"] + p["size"]
                                         for p in patches)
    output = ROOT / "q2-box-valve-rfid-dev1.bin"
    output.write_bytes(patched)
    report = {"status": "experimental, static validation only, not qualified for flashing",
              "stock_sha256": STOCK_SHA, "output_sha256": sha(patched),
              "size": len(patched), "version": VERSION, "patches": patches,
              "compressed_dictionary_size": len(compressed), "clang_flags": FLAGS}
    (ROOT / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(output.name, len(patched), sha(patched))
    print("Dictionary", len(compressed), "/", DICT_BYTES)


if __name__ == "__main__":
    main()
