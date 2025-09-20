"""Test configuration for ensuring project modules are importable."""

from __future__ import annotations

import sys
from pathlib import Path


def _add_src_to_syspath() -> None:
    """Ensure the repository root (and therefore ``src`` package) is importable."""

    root = Path(__file__).resolve().parent.parent
    src_path = root / "src"
    root_path = root

    for path in (root_path, src_path):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_add_src_to_syspath()

