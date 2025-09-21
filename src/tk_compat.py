"""Runtime selection between the real tkinter package and a headless shim."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Tuple


def _load_tkinter() -> Tuple[ModuleType, ModuleType, ModuleType, ModuleType]:
    try:
        tk = importlib.import_module("tkinter")
        try:
            root = tk.Tk()
            root.withdraw()
            root.destroy()
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise RuntimeError("tkinter requires a display") from exc
        filedialog = importlib.import_module("tkinter.filedialog")
        messagebox = importlib.import_module("tkinter.messagebox")
        colorchooser = importlib.import_module("tkinter.colorchooser")
        return tk, filedialog, messagebox, colorchooser
    except Exception:
        from src import _headless_tk as tk

        filedialog = tk.filedialog
        messagebox = tk.messagebox
        colorchooser = tk.colorchooser
        sys.modules["tkinter"] = tk
        sys.modules["tkinter.filedialog"] = filedialog
        sys.modules["tkinter.messagebox"] = messagebox
        sys.modules["tkinter.colorchooser"] = colorchooser
        return tk, filedialog, messagebox, colorchooser


tk, filedialog, messagebox, colorchooser = _load_tkinter()

__all__ = ["tk", "filedialog", "messagebox", "colorchooser"]

