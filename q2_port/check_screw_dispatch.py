"""Render screw-tilt macros through the actual Klipper dispatcher with inert handlers.

Run with the printer's klippy-env Python and --klippy-root pointing at its source.
This process never constructs a printer, opens serial, or sends G-code to hardware.
"""

import argparse
import configparser
from pathlib import Path
import sys

import jinja2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--klippy-root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.klippy_root))
    import gcode

    config = configparser.RawConfigParser()
    config.read(args.config)
    macro = config["gcode_macro SCREWS_TILT_CALCULATE"]
    base = macro["rename_existing"].upper()
    environment = jinja2.Environment(
        block_start_string="{%",
        block_end_string="%}",
        variable_start_string="{",
        variable_end_string="}",
    )
    template = environment.from_string(macro["gcode"])
    for homed in ("", "xy", "xyz"):
        events = []
        dispatcher = object.__new__(gcode.GCodeDispatch)
        dispatcher.abort_epoch = 0
        dispatcher.gcode_handlers = {
            "G28": lambda cmd: events.append("home"),
            base: lambda cmd: events.append(("calculate", cmd.get_commandline())),
        }
        dispatcher.cmd_default = (
            lambda cmd: events.append(("unmatched", cmd.get_command()))
            if cmd.get_command()
            else None
        )
        rendered = template.render(
            printer={"toolhead": {"homed_axes": homed}}, rawparams="MAX_DEVIATION=0.1"
        )
        dispatcher._process_commands(rendered.splitlines(), need_ack=False)
        expected = (["home"] if homed != "xyz" else []) + [
            ("calculate", base + " MAX_DEVIATION=0.1")
        ]
        if events != expected:
            raise AssertionError(
                "Dispatch failed for homed axes %r: %r" % (homed, events)
            )
        print("PASS homed=%r: %r" % (homed, events))
    print(
        "Actual dispatcher reached inert calculation handlers; no hardware commands executed."
    )


if __name__ == "__main__":
    main()
