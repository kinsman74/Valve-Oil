"""Run upstream monitor regressions against Q2's compatibility-named candidates."""

import argparse
from pathlib import Path
import sys
import types
import unittest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upstream", required=True, type=Path)
    p.add_argument("--modules", required=True, type=Path)
    a = p.parse_args()
    sys.path.insert(0, str(a.upstream.resolve()))
    from installer.tests import klipper_fakes, helpers

    def load_extra(name, module_name=None, *, stand_ins=None):
        path = a.modules / ("tltg_" + name + ".py")
        return helpers.load_source(
            module_name or "tltg_" + name, path, stand_ins=stand_ins
        )

    klipper_fakes.load_extra = load_extra
    source = (a.upstream / "installer/tests/klipper/test_box_monitors.py").read_text()
    source = (
        source.replace("vo_", "tltg_")
        .replace("_vo", "_tltg")
        .replace("VO_RS_BOX_REPORT", "TLTG_RS_BOX_REPORT")
    )
    # Retained log names sort differently from upstream's renamed logs.
    source = source.replace(
        '["tltg_box485_report.json", "tltg_box485.log"]',
        '["tltg_box485.log", "tltg_box485_report.json"]',
    )
    source = source.replace(
        '["tltg_box485_report.json", "tltg_box485.log", "tltg_box485.log.1"]',
        '["tltg_box485.log", "tltg_box485.log.1", "tltg_box485_report.json"]',
    )
    module = types.ModuleType("q2_stable_monitor_tests")
    module.__file__ = str(a.upstream / "installer/tests/klipper/test_box_monitors.py")
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(module)
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
