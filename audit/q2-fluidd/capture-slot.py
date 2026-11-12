"""Poll one Box slot and emit only changes. Uses GET requests exclusively."""
import argparse
import json
import time
from urllib.parse import quote, urlsplit
from urllib.request import urlopen


def sample(base, slot):
    stepper = f"box_stepper slot{slot}"
    objects = ("webhooks", "print_stats", "multi_color_controller",
               stepper, "inventory_rfid_read_guard", "save_variables")
    route = "/printer/objects/query?" + "&".join(map(quote, objects))
    with urlopen(base + route, timeout=4) as response:
        state = json.load(response)["result"]["status"]
    controller = state["multi_color_controller"]
    box = controller["box"]
    unit, position = divmod(slot, 4)
    prefix = f"box{unit}_filament_info_{position}_"
    variables = state.get("save_variables", {}).get("variables", {})
    return {
        "printer": state["webhooks"]["state"],
        "print": state["print_stats"]["state"],
        "task": {key: controller["task"].get(key)
                 for key in ("flow_id", "current_step", "is_paused")},
        "box_online": box.get(f"box{unit}_is_online"),
        "box_inserted": box.get(f"box{unit}_box_inserted_{position}"),
        "filament_inserted": box.get(f"box{unit}_filament_inserted_{position}"),
        "stepper": {key: state.get(stepper, {}).get(key)
                    for key in ("runout_button", "rfid_state")},
        "slot": {key: box.get(prefix + key) for key in (
            "filament_id", "filament_type", "read_rfid_state", "info_from_rfid")},
        "saved_id": variables.get(f"filament_slot{slot}"),
        "last_scan": state.get("inventory_rfid_read_guard", {})
                          .get("last_scans", {}).get(f"slot{slot}"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Moonraker HTTP origin")
    parser.add_argument("--slot", type=int, choices=range(16), default=1,
                        help="Zero-based Box slot, default 1 for 1B")
    parser.add_argument("--seconds", type=float, default=90)
    args = parser.parse_args()
    url = urlsplit(args.base_url)
    if (url.scheme not in ("http", "https") or not url.hostname or url.username or url.password
            or url.path not in ("", "/") or url.query or url.fragment):
        parser.error("Provide an HTTP origin without credentials, path or query")
    if not 1 <= args.seconds <= 600:
        parser.error("Duration must be 1–600 seconds")
    base = args.base_url.rstrip("/")
    start = time.monotonic()
    previous = None
    while time.monotonic() - start < args.seconds:
        current = sample(base, args.slot)
        if current != previous:
            print(json.dumps({"elapsed_seconds": round(time.monotonic() - start, 3),
                              "slot_index": args.slot, **current}), flush=True)
            previous = current
        time.sleep(0.5)


if __name__ == "__main__":
    main()
