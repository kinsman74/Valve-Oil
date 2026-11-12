"""Read manifest and saved stock configuration files. Output Markdown to stdout."""
import argparse
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "installer/runtime/vendor"))
import yaml
sys.path.insert(0, str(ROOT))
from installer.runtime.klipper_cfg import normalized_section_sha256

def section(root, relative, name):
    path = root / relative
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        return None
    lines = path.read_text(errors="replace").splitlines(keepends=True)
    body = []
    active = False
    for line in lines:
        match = re.match(r"^\[([^]]+)\]", line)
        if match:
            if active:
                break
            active = match[1].casefold() == name.casefold()
        if active:
            body.append(line)
    return "".join(body) or None

def option(root, patch):
    body = section(root, patch["file"], patch["section"])
    if body:
        match = re.search(r"^" + re.escape(patch["option"]) + r"\s*[:=]\s*([^#;\n]+)", body, re.M)
        if match:
            return match[1].strip()
    return None

def cell(value):
    return "—" if value is None else str(value).replace("|", "\\|")

def state(actual, expected):
    if actual is None:
        return "absent"
    return "matches" if actual == expected else "differs"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("q2_snapshot", type=Path, help="Saved Q2 service home containing printer_data/config")
    args = parser.parse_args()
    manifest = yaml.safe_load((ROOT / "installer/package.yaml").read_text())
    q2 = args.q2_snapshot / "printer_data"
    max4 = ROOT / "installer/stock/qidi-max4-defaults/firmwares"
    versions = manifest["printers"][0]["firmware"]
    if not (q2 / "config/printer.cfg").is_file():
        parser.error("Q2 snapshot is missing printer_data/config/printer.cfg")
    print("# Manifest comparison\n")
    print("Max 4 stock observations use the bundled snapshots. Q2 uses a saved factory-restore capture.\n")
    print("Q2 printer.cfg SHA-256: " + hashlib.sha256((q2 / "config/printer.cfg").read_bytes()).hexdigest() + "\n")
    for kind, patches in manifest["patches"].items():
        print(f"## {kind}\n")
        print("| Patch | Max 4 firmware | Expected → desired | Max 4 stock | Q2 stock |")
        print("|---|---|---|---|---|")
        for patch in patches:
            for variant in patch["variants"]:
                for version in variant["firmwares"]:
                    if kind == "set_options":
                        expected, desired = variant["expected"], variant["desired"]
                        observed = option(max4 / version, patch)
                        actual = option(q2, patch)
                        if actual is not None:
                            actual = f"{actual} ({state(actual, expected)} Max 4 guard)"
                        intent = f"{expected} → {desired}"
                    else:
                        expected = variant["expected_normalized_sha256"]
                        intent = f"{expected[:12]} → remove"
                        def check(root):
                            body = section(root, patch["file"], patch["section"])
                            return state(normalized_section_sha256(body) if body else None, expected)
                        observed, actual = check(max4 / version), check(q2)
                    print("| " + " | ".join(map(cell, (patch["id"], version, intent, observed, actual))) + " |")
        print()
    print("## Guarded Klipper source replacements\n")
    print("| Patch | Max 4 firmware | Expected stock hash | Q2 capture |")
    print("|---|---|---|---|")
    for patch in manifest["install"]["source_patches"]:
        path = args.q2_snapshot / "klipper" / patch["destination"]
        actual = None
        if path.is_file() and path.resolve().is_relative_to(args.q2_snapshot.resolve()):
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        for variant in patch["variants"]:
            expected = variant["expected_sha256"]
            print("| " + " | ".join((patch["id"], variant["firmware"], expected,
                                    state(actual, expected) if actual else "not captured")) + " |")
    print()
    print("Max 4 source hashes above are installer guard expectations. The bundled stock config trees do not supply these source files.\n")
    inventories = [
        ("Common Klipper modules", (ROOT / "installer/klipper/tltg").glob("*.py")),
        ("Common and Max 4 macro files", (ROOT / "installer/klipper").rglob("*.cfg")),
        ("Installer runtime", (ROOT / "installer/runtime").glob("*.*")),
        ("Firmware manifests", (ROOT / "firmware").glob("*.json")),
        ("Slicer packs", (p for folder in ("orcaslicer_gcode", "qidistudio_gcode") for p in (ROOT / folder).rglob("*.gcode"))),
    ]
    for title, paths in inventories:
        print(f"## {title}\n")
        for path in sorted(paths):
            print(f"- `{path.relative_to(ROOT)}`")
        if title != inventories[-1][0]:
            print()

if __name__ == "__main__":
    main()
