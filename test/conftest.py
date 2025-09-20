import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def tk_root():
    """Provide a Tk root window or skip tests when no display is available."""
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tkinter requires a display to run these tests")

    root.withdraw()

    try:
        yield root
    finally:
        root.destroy()
