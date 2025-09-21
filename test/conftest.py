"""Pytest configuration for import setup and Tk fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def _add_src_to_syspath() -> None:
    """Ensure the repository root (and therefore ``src`` package) is importable."""

    root = Path(__file__).resolve().parent.parent
    src_path = root / "src"

    for path in (root, src_path):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_add_src_to_syspath()

from src.tk_compat import tk


@pytest.fixture
def tk_root():
    """Provide a Tk root window or skip tests when unavailable."""

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tkinter requires a display to run these tests")

    root.withdraw()

    try:
        yield root
    finally:
        root.destroy()
