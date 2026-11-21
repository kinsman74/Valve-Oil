"""Content locks for build inputs; not a signature or a trust-on-first-use loader."""

import hashlib
import json
from pathlib import Path

LOCK_FILE = Path(__file__).with_name("source-lock.json")


def verify_group(root, group):
    lock = json.loads(LOCK_FILE.read_text())
    expected = lock[group]
    root = root.resolve()
    for name, digest in expected.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid source lock path")
        path = root / relative
        for part in (path, *path.parents):
            if part == root:
                break
            if part.is_symlink():
                raise ValueError("Source symlink refused: " + name)
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest
        ):
            raise ValueError("Pinned source mismatch: " + group + "/" + name)
    if group == "upstream":
        for name in lock.get("upstream_absent", []):
            if (root / name).exists():
                raise ValueError("Unexpected upstream initializer: " + name)
        # New Python modules in imported directories can shadow locked imports.
        actual = set()
        for prefix in lock["upstream_python_roots"]:
            base = root / prefix
            for path in [base] if base.is_file() else base.rglob("*.py"):
                if "__pycache__" not in path.parts:
                    actual.add(path.relative_to(root).as_posix())
        if actual != {name for name in expected if name.endswith(".py")}:
            raise ValueError("Unexpected upstream Python source inventory")
    inventory_roots = []
    if group == "upstream":
        inventory_roots = ["ui"]
    elif group == "fluidd":
        inventory_roots = ["src"]
    elif group == "workspace":
        inventory_roots = [
            "work/q2-stable-26.11.18.2/fluidd/dist",
            "work/q2-stable-26.11.18.2/staged/ui/dist",
        ]
    elif group == "q2_adapter":
        inventory_roots = ["src"]
    for prefix in inventory_roots:
        actual = set()
        for path in (root / prefix).rglob("*"):
            if "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                raise ValueError("Unexpected source symlink: " + str(path))
            if path.is_file():
                actual.add(path.relative_to(root).as_posix())
        pinned = {name for name in expected if name.startswith(prefix + "/")}
        if actual != pinned:
            raise ValueError(
                "Unexpected source file inventory: " + group + "/" + prefix
            )
    return lock["upstream_commit"]
