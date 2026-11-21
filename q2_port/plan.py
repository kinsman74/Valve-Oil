"""Read-only file planner, not an installer or a board-admission check."""

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import policy  # noqa: E402 - disable cache writes before importing bundled code


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Unsafe relative path: " + name)
    root = root.resolve()
    destination = root / path
    for part in (destination, *destination.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError("Symlink target refused: " + name)
    if not destination.resolve().is_relative_to(root):
        raise ValueError("Escaping path: " + name)
    return destination


def overlay_config(data, sections):
    text = data.decode()
    marker = "#*# <---------------------- SAVE_CONFIG"
    if marker not in text:
        raise ValueError("Missing calibration marker")
    found = re.findall(r"^\[([^\]\r\n]+)\]", text, re.M)
    if len(found) != len(set(found)):
        raise ValueError("Duplicate configuration section")
    missing = [name for name in sections if name not in found]
    if not missing:
        return data
    newline = "\r\n" if b"\r\n" in data else "\n"
    block = newline + "# Q2 non-motion bundle sections" + newline
    block += "".join("[" + name + "]" + newline * 2 for name in missing)
    result = text.replace(marker, block + marker, 1).encode()
    if result.decode().split(marker, 1)[1] != text.split(marker, 1)[1]:
        raise ValueError("Calibration tail changed")
    return result


def read_catalog(bundle):
    """Extract literal JSON without importing or executing a Python payload."""
    tree = ast.parse(safe(bundle, "filament_catalog.py").read_text())
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "CATALOG" for t in node.targets)
    ]
    if len(assignments) != 1:
        raise ValueError("Catalog must have one CATALOG assignment")
    value = assignments[0].value
    if not (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id == "json"
        and value.func.attr == "loads"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Constant)
        and isinstance(value.args[0].value, str)
    ):
        raise ValueError("Catalog must contain literal JSON")
    catalog = json.loads(value.args[0].value)
    if not isinstance(catalog.get("filaments"), dict):
        raise ValueError("Invalid filament catalog")
    return catalog


def desired(bundle, operation, before):
    kind = operation["kind"]
    if kind == "file":
        data = safe(bundle, operation["payload"]).read_bytes()
        if sha(data) != operation["after_sha256"]:
            raise ValueError("Corrupt payload: " + operation["payload"])
        return data
    if kind == "config_sections":
        return overlay_config(before, operation["sections"])
    if kind == "metadata":
        data = json.loads(before) if before else {}
        if not isinstance(data, dict):
            raise ValueError("Invalid existing Q2 status metadata")
        # Preserve unrelated fields. A different printer/profile needs explicit review.
        printer = data.get("printer", {})
        if not isinstance(printer, dict) or not isinstance(
            data.get("release", {}), dict
        ):
            raise ValueError("Invalid existing Q2 status metadata fields")
        if printer.get("id") not in (None, "q2"):
            raise ValueError("Existing status metadata belongs to another printer")
        data.update(schema=1)
        data["release"] = {
            **data.get("release", {}),
            "installed": "26.11.18.2-q2-selective",
        }
        data["printer"] = {**printer, "id": "q2", "name": "QIDI Q2 selective port"}
        data.setdefault("pending", [])
        data.setdefault("boards", [])
        data.setdefault("run", None)
        return (json.dumps(data, indent=2) + "\n").encode()
    if kind == "nginx_routes":
        text = before.decode()
        newline = "\r\n" if b"\r\n" in before else "\n"
        for name in ("screen-routes.conf", "status-routes.conf", "ui-routes.conf"):
            block = safe(bundle, name).read_text()
            lines = block.splitlines()
            if len(lines) < 2:
                raise ValueError("Invalid nginx route fragment")
            start, end = lines[0].strip(), lines[-1].strip()
            pattern = (
                r"^[ \t]*"
                + re.escape(start)
                + r"\r?\n.*?^[ \t]*"
                + re.escape(end)
                + r"\r?\n"
            )
            matches = list(re.finditer(pattern, text, re.M | re.S))
            if len(matches) > 1:
                raise ValueError("Ambiguous managed nginx block")
            replacement = block.replace("\n", newline)
            if matches:
                text = (
                    text[: matches[0].start()] + replacement + text[matches[0].end() :]
                )
            else:
                anchor = "    location /webcam/ {"
                if text.count(anchor) != 1:
                    raise ValueError("Unknown nginx route structure")
                text = text.replace(anchor, replacement + newline + anchor, 1)
        return text.encode()
    if kind == "catalog_merge":
        catalog = read_catalog(bundle)
        entries = json.loads(before)
        if not isinstance(entries, dict):
            raise ValueError("Existing catalog must be an object")
        used = {
            entry.get("filament_id")
            for entry in entries.values()
            if isinstance(entry, dict)
        }
        additions = {}
        for name, item in catalog["filaments"].items():
            if operation["nozzle"] not in item["nozzles"] or name in entries:
                continue
            entry = item["entry"]
            if entry["filament_id"] in used:
                continue
            additions[name] = dict(entry)
            used.add(entry["filament_id"])
        if not additions:
            return before
        return (
            json.dumps({**entries, **additions}, ensure_ascii=False, indent=2) + "\n"
        ).encode()
    raise ValueError("Unknown operation type: " + kind)


def verify_firmware_artifacts(bundle):
    for name, (size, digest) in policy.FIRMWARE.items():
        data = safe(bundle, "firmware/" + name).read_bytes()
        if len(data) != size or sha(data) != digest:
            raise ValueError("Firmware identity mismatch: " + name)
    stock = safe(
        bundle, policy.FIRMWARE_DELIVERY["vendor_stock_reference"]
    ).read_bytes()
    size, candidate_hash = policy.FIRMWARE["q2-thr-valve-oil-fifo.bin"]
    if len(stock) != size or sha(stock) != policy.STOCK_THR_SHA:
        raise ValueError("Firmware identity mismatch: toolhead stock reference")
    report = json.loads(
        safe(bundle, policy.FIRMWARE_DELIVERY["vetting_report"]).read_text()
    )
    if not isinstance(report, dict):
        raise ValueError("Toolhead vetting report must be an object")
    bindings = {
        "archive_sha256": policy.QIDI_Q2_ARCHIVE_SHA256,
        "vendor_soc": policy.SOC_VERSION,
        "vendor_thr_member": policy.THR_STOCK_MEMBER,
        "vendor_thr_sha256": policy.STOCK_THR_SHA,
        "candidate_sha256": candidate_hash,
        "vendor_thr_bytes": size,
        "emulation_cases": 1024,
    }
    if any(report.get(key) != value for key, value in bindings.items()):
        raise ValueError("Toolhead vetting report does not match bundled images")
    if report.get("flashing_authorized_or_performed") is not False:
        raise ValueError("Toolhead report must not authorize flashing")
    readiness = json.loads(
        safe(bundle, policy.FIRMWARE_DELIVERY["readiness"]).read_text()
    )
    if readiness != policy.THR_READINESS or readiness.get("auto_flash") is not False:
        raise ValueError("Toolhead readiness must preserve pending physical admission")


def verify_bundle(bundle):
    sums = json.loads(safe(bundle, "SHA256SUMS.json").read_text())
    if not isinstance(sums, dict):
        raise ValueError("Invalid bundle checksum inventory")
    actual = set()
    for path in bundle.rglob("*"):
        if path.is_symlink():
            raise ValueError("Bundle symlink refused: " + str(path))
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Non-regular bundle entry")
        name = path.relative_to(bundle).as_posix()
        if name != "SHA256SUMS.json":
            actual.add(name)
    if actual != set(sums):
        raise ValueError("Bundle file inventory mismatch")
    for name, digest in sums.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid checksum: " + name)
        if sha(safe(bundle, name).read_bytes()) != digest:
            raise ValueError("Bundle checksum mismatch: " + name)
    verify_firmware_artifacts(bundle)


def plan(bundle, snapshot):
    verify_bundle(bundle)
    manifest = json.loads(safe(bundle, "manifest.json").read_text())
    if (
        manifest.get("schema") != policy.SCHEMA
        or manifest.get("upstream_commit") != policy.UPSTREAM_COMMIT
        or manifest.get("supported_soc") != policy.SOC_VERSION
        or manifest.get("mode") != "dry-run-only"
        or manifest.get("no_live_flash") is not True
        or manifest.get("firmware_delivery") != policy.FIRMWARE_DELIVERY
    ):
        raise ValueError("Unsupported bundle policy or provenance")
    firmware = json.loads(
        safe(snapshot, "home/qidi/update/firmware_manifest.json").read_text()
    )
    soc = firmware.get("SOC", {})
    if soc.get("version") != policy.SOC_VERSION:
        raise ValueError("Unsupported SOC version")
    if not re.match(r"^QD_Q2_SOC_01\.01\.03\.02(?:_|$)", soc.get("file", "")):
        raise ValueError("Wrong printer model")
    actions, seen = [], set()
    for operation in manifest["operations"]:
        policy.validate_operation(operation)
        target = operation["target"]
        if target in seen:
            raise ValueError("Duplicate operation target")
        seen.add(target)
        path = safe(snapshot, target)
        before = path.read_bytes() if path.exists() else b""
        current_hash = sha(before) if path.exists() else None
        expected_after = operation.get("after_sha256")
        if not isinstance(expected_after, str) or not re.fullmatch(
            r"[0-9a-f]{64}", expected_after
        ):
            raise ValueError("Missing expected result hash: " + target)
        # Check identity BEFORE rendering; arbitrary config edits are never an idempotence shortcut.
        if current_hash not in (operation.get("before_sha256"), expected_after):
            raise ValueError("Target drift: " + target)
        result = desired(bundle, operation, before)
        if sha(result) != expected_after:
            raise ValueError("Transformation result mismatch: " + target)
        if target.endswith("/tltg_box_slot_jog.py") and current_hash != expected_after:
            raise ValueError(
                "New or modified slot-jog is outside this non-motion upgrade"
            )
        state = (
            "unchanged"
            if current_hash == expected_after
            else "create"
            if not path.exists()
            else "replace"
        )
        actions.append(
            {
                "target": target,
                "action": state,
                "before_sha256": current_hash,
                "after_sha256": expected_after,
                "feature": operation["feature"],
                "mode": oct(path.stat().st_mode & 0o777) if path.exists() else "0o644",
                "ownership": "preserve existing"
                if path.exists()
                else "requires installer policy",
            }
        )
    return {
        "mode": "dry-run",
        "read_only": True,
        "model": "Q2",
        "soc": policy.SOC_VERSION,
        "model_evidence": "cached manifest only; not physical board admission",
        "upstream_commit": policy.UPSTREAM_COMMIT,
        "actions": actions,
        "counts": {
            key: sum(action["action"] == key for action in actions)
            for key in ("create", "replace", "unchanged")
        },
        "blocked_source_transforms": manifest["blocked_transforms"],
        "feature_status": manifest["feature_status"],
        "complete_upstream_parity": False,
        "validation_scope": "file identities and rendering only; file-copy simulation is not an installer test",
        "activation_not_executed": manifest["activation_requirements"],
        "deployment_ready": False,
        "firmware_delivery": manifest["firmware_delivery"],
        "live_flash": "requires idle physical board admission, recovery qualification and readback",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--bundle", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(plan(args.bundle, args.snapshot), indent=2))
    except (ValueError, OSError, SyntaxError) as error:
        parser.exit(2, "Dry-run rejected: " + str(error) + "\n")


if __name__ == "__main__":
    main()
