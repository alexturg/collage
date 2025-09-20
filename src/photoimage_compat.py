"""Provide a Tk-free stand-in for :class:`PIL.ImageTk.PhotoImage` in tests."""

from __future__ import annotations

from typing import Any

from src.tk_compat import tk

try:  # pragma: no cover - exercised only when a display is available
    from PIL.ImageTk import PhotoImage as _PhotoImage
except Exception:  # pragma: no cover - missing Pillow or Tk support
    _PhotoImage = None  # type: ignore[assignment]


def _is_headless() -> bool:
    return getattr(tk, "__name__", "") == "src._headless_tk"


if not _is_headless() and _PhotoImage is not None:
    PhotoImage = _PhotoImage  # pragma: no cover - real Tk path
else:

    class PhotoImage:  # pragma: no cover - tiny shim
        """Minimal object that mimics the bits of ``PhotoImage`` we rely on."""

        def __init__(self, image: Any) -> None:
            self._image = image
            self.width = _dimension(image, "width", index=0)
            self.height = _dimension(image, "height", index=1)

        def __repr__(self) -> str:
            return f"<HeadlessPhotoImage size={self.width}x{self.height}>"


def _dimension(image: Any, attr: str, index: int) -> int:
    value = getattr(image, attr, None)
    if callable(value):
        return int(value())
    if value is not None:
        return int(value)
    if hasattr(image, "size"):
        return int(image.size[index])
    raise AttributeError(f"Cannot determine dimension '{attr}' for {image!r}")

