"""Explicit scope and firmware identity for the Q2 offline preview."""

UPSTREAM_COMMIT = "fea34e996f1ab64c646dd02846d1bb47ad93c272"
SOC_VERSION = "01.01.03.02"
SCHEMA = 2
NONMOTION = (
    "background_save_config",
    "save_variables_fast",
    "klipper_health",
    "macro_status",
    "printer_warnings",
    "spoolman",
    "probe_test",
    "probe_report",
    "box_heater_refresh",
    "update_lights",
    "box_mcu_temperature",
)
CORE = ("box_rfid", "box485_monitor", "box_link_monitor", "box_slot_jog")
MODULES = {"tltg_" + name for name in NONMOTION + CORE} | {
    "tltg_filament_catalog",
    "inventory_rfid_read_guard",
}
CONFIG = "home/qidi/printer_data/config/printer.cfg"
NGINX = "etc/nginx/sites-available/fluidd"
METADATA = "home/qidi/printer_data/.q2_valve_oil_status.json"
EXACT_FILES = {
    "home/qidi/moonraker/moonraker/components/klippy_apis.py",
    "home/qidi/printer_data/moonraker.asvc",
    "home/qidi/moonraker/moonraker/components/spoolman.py",
    "home/qidi/moonraker/moonraker/components/file_manager/metadata.py",
    "home/qidi/moonraker-env/lib/python3.9/site-packages/tltg_moonraker_fixes.py",
    "home/qidi/moonraker-env/lib/python3.9/site-packages/tltg-moonraker-fixes.pth",
    "home/qidi/fluidd/index.html",
    "usr/local/lib/tltg_remote_screen.py",
    "usr/local/lib/tltg_status.py",
    "etc/systemd/system/tltg-remote-screen.service",
    "etc/systemd/system/tltg-status.service",
}
WEB_PREFIXES = (
    "home/qidi/fluidd/q2-bundle-preview/",
    "home/qidi/valve-oil-ui-q2/",
)
FIRMWARE = {
    "q2-box-valve-rfid-dev1.bin": (
        33776,
        "50e1b2d76a64d3ef7a0c8f79eb4a84be9eafd93cb0912e55d994c8245d93f903",
    ),
    "q2-thr-valve-oil-fifo.bin": (
        35056,
        "b6e39b1def0bad6c2379cad600c1284cece0c26caab77dbb659adf64d4f4172a",
    ),
}
STOCK_BOX_SHA = "c09aa5e0a07161f197c597571d96a48ac1cfb3f19a3758576b3428547a424ba9"
STOCK_THR_SHA = "1d34b4b0142f2a2047f08c2fae59d827bcee0adbd1563b4bd1de311dff8b2d62"


def validate_operation(operation):
    if (
        not isinstance(operation, dict)
        or not isinstance(operation.get("target"), str)
        or not isinstance(operation.get("kind"), str)
    ):
        raise ValueError("Invalid operation")
    target, kind = operation["target"], operation["kind"]
    special = {CONFIG: "config_sections", NGINX: "nginx_routes", METADATA: "metadata"}
    if target in special:
        if kind != special[target]:
            raise ValueError("Wrong operation kind for " + target)
        if kind == "config_sections":
            sections = operation.get("sections", [])
            allowed = MODULES - {"tltg_filament_catalog"}
            if len(sections) != len(set(sections)) or not set(sections) <= allowed:
                raise ValueError("Out-of-scope configuration section")
        return
    catalog_prefix = "home/qidi/QIDI_Client/resource/filament_config/filament-"
    if target.startswith(catalog_prefix):
        nozzle = operation.get("nozzle")
        if kind != "catalog_merge" or nozzle not in ("0.2", "0.4", "0.6", "0.8"):
            raise ValueError("Out-of-scope catalog operation")
        if target != catalog_prefix + nozzle + ".json":
            raise ValueError("Catalog target/nozzle mismatch")
        return
    prefix = "home/qidi/klipper/klippy/extras/"
    if target.startswith(prefix):
        name = target[len(prefix) :]
        if kind != "file" or name not in {n + ".py" for n in MODULES}:
            raise ValueError("Out-of-scope Klipper module: " + target)
        if name == "tltg_box_slot_jog.py" and not operation.get(
            "carried_forward_motion_exception"
        ):
            raise ValueError("Slot-jog must be an unchanged carry-forward")
        return
    if kind == "file" and (target in EXACT_FILES or target.startswith(WEB_PREFIXES)):
        return
    raise ValueError("Out-of-scope target: " + target)
