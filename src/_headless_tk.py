"""A minimal Tkinter stand-in for headless environments.

This module provides small, self-contained replacements for the widgets and
helpers that the project needs during its automated test run.  The real
``tkinter`` package requires an available display which is not present on the
CI workers, therefore importing or instantiating real widgets would raise a
``TclError``.  The shim below mimics just enough behaviour for the unit tests
to exercise the non-GUI logic of the application.

Only the attributes that are touched by the code base have been implemented;
every method is intentionally lightweight and keeps book-keeping data in
simple Python structures.  The goal is functional compatibility, not pixel
perfect emulation.
"""

from __future__ import annotations

from itertools import count
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from PIL.ImageColor import getrgb

__all__ = [
    "Button",
    "Canvas",
    "Checkbutton",
    "DoubleVar",
    "END",
    "Entry",
    "Frame",
    "HORIZONTAL",
    "IntVar",
    "Label",
    "LabelFrame",
    "Listbox",
    "Menu",
    "PanedWindow",
    "Scrollbar",
    "SINGLE",
    "StringVar",
    "Text",
    "Tk",
    "TclError",
    "VERTICAL",
    "WORD",
]


# ---------------------------------------------------------------------------
# Shared helpers


VERTICAL = "vertical"
HORIZONTAL = "horizontal"
END = "end"
WORD = "word"
SINGLE = "single"


class TclError(RuntimeError):
    """Replacement for ``tkinter.TclError``."""


class _Variable:
    def __init__(self, master: Optional["Widget"] = None, value: Any = None) -> None:
        self._value = value

    def get(self) -> Any:
        return self._value

    def set(self, value: Any) -> None:
        self._value = value


class IntVar(_Variable):
    pass


class DoubleVar(_Variable):
    pass


class StringVar(_Variable):
    pass


class Widget:
    """A tiny base implementation with Tk-like semantics."""

    def __init__(self, master: Optional["Widget"] = None, **kwargs: Any) -> None:
        self.master = master
        self.children: List[Widget] = []
        self._grid_info: Dict[str, Any] = {}
        self._bindings: Dict[str, Callable[..., Any]] = {}
        self._config: Dict[str, Any] = {
            "width": kwargs.get("width", 0),
            "height": kwargs.get("height", 0),
            "bg": kwargs.get("bg", "white"),
        }
        if master is not None:
            master._register_child(self)
        self.configure(**kwargs)

    # ------------------------------------------------------------------
    # Internal helpers

    def _register_child(self, child: "Widget") -> None:
        self.children.append(child)

    def _remove_child(self, child: "Widget") -> None:
        if child in self.children:
            self.children.remove(child)

    # ------------------------------------------------------------------
    # API surface used by the project

    def configure(self, **kwargs: Any) -> None:
        self._config.update(kwargs)

    config = configure

    def grid(self, row: int = 0, column: int = 0, sticky: Optional[str] = None, **kwargs: Any) -> "Widget":
        self._grid_info = {"row": row, "column": column, "sticky": sticky, **kwargs}
        return self

    def grid_remove(self) -> None:
        self._grid_info = {}

    def bind(self, sequence: str, func: Callable[..., Any]) -> None:
        self._bindings[sequence] = func

    def rowconfigure(self, index: int, weight: int = 0) -> None:
        self._config.setdefault("row_weights", {})[index] = weight

    def columnconfigure(self, index: int, weight: int = 0) -> None:
        self._config.setdefault("column_weights", {})[index] = weight

    def winfo_rgb(self, color: str) -> Tuple[int, int, int]:
        r, g, b = getrgb(color)
        return r << 8, g << 8, b << 8

    def winfo_width(self) -> int:
        return int(self._config.get("width", 0) or 0)

    def winfo_height(self) -> int:
        return int(self._config.get("height", 0) or 0)

    def winfo_reqwidth(self) -> int:
        return self.winfo_width()

    def winfo_reqheight(self) -> int:
        return self.winfo_height()

    def winfo_children(self) -> List["Widget"]:
        return list(self.children)

    def update(self) -> None:  # pragma: no cover - behaviourless stub
        pass

    def update_idletasks(self) -> None:  # pragma: no cover - behaviourless stub
        pass

    def destroy(self) -> None:
        for child in list(self.children):
            child.destroy()
        self.children.clear()
        if self.master is not None:
            self.master._remove_child(self)

    def focus_set(self) -> None:  # pragma: no cover - behaviourless stub
        self._config["has_focus"] = True


class Tk(Widget):
    def geometry(self, value: str) -> None:
        self._config["geometry"] = value

    def withdraw(self) -> None:  # pragma: no cover - behaviourless stub
        self._config["withdrawn"] = True

    def deiconify(self) -> None:  # pragma: no cover - behaviourless stub
        self._config.pop("withdrawn", None)

    def mainloop(self) -> None:  # pragma: no cover - behaviourless stub
        pass


class Frame(Widget):
    pass


class Label(Frame):
    pass


class LabelFrame(Frame):
    pass


class Entry(Widget):
    def __init__(self, master: Optional[Widget] = None, textvariable: Optional[_Variable] = None, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self.textvariable = textvariable


class Button(Widget):
    def __init__(self, master: Optional[Widget] = None, command: Optional[Callable[[], Any]] = None, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self.command = command

    def invoke(self) -> Any:
        if callable(self.command):
            return self.command()


class Checkbutton(Widget):
    def __init__(
        self,
        master: Optional[Widget] = None,
        variable: Optional[_Variable] = None,
        onvalue: Any = 1,
        offvalue: Any = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self.variable = variable or IntVar()
        self.onvalue = onvalue
        self.offvalue = offvalue
        self.variable.set(self.offvalue)


class _ScrollableItem:
    def __init__(self, widget: Widget) -> None:
        self.widget = widget
        self.config: Dict[str, Any] = {}


class PanedWindow(Widget):
    def __init__(self, master: Optional[Widget] = None, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._panes: List[_ScrollableItem] = []

    def add(self, widget: Widget) -> None:
        if all(item.widget is not widget for item in self._panes):
            self._panes.append(_ScrollableItem(widget))

    def forget(self, widget: Widget) -> None:
        self._panes = [item for item in self._panes if item.widget is not widget]

    def panes(self) -> List[Widget]:
        return [item.widget for item in self._panes]

    def paneconfigure(self, pane: Widget, before: Optional[Widget] = None, **kwargs: Any) -> None:
        self.paneconfig(pane, before=before, **kwargs)

    def paneconfig(self, pane: Widget, before: Optional[Widget] = None, **kwargs: Any) -> None:
        for item in self._panes:
            if item.widget is pane:
                item.config.update(kwargs)
                break
        if before is not None:
            panes = [item.widget for item in self._panes]
            if pane in panes and before in panes:
                panes.remove(pane)
                index = panes.index(before)
                panes.insert(index, pane)
                lookup = {item.widget: item for item in self._panes}
                self._panes = [lookup[w] for w in panes]


class Canvas(Widget):
    def __init__(self, master: Optional[Widget] = None, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._items: Dict[int, Dict[str, Any]] = {}
        self._id_counter = count(1)
        self._scrollregion = (0, 0, 0, 0)
        self._view = {"x": 0.0, "y": 0.0}

    # Tk's create_window accepts either an (x, y) tuple or two coordinates.
    def create_window(self, *args: Any, **kwargs: Any) -> int:
        if len(args) == 1 and isinstance(args[0], Iterable):
            x, y = args[0]
        else:
            x, y = args[:2]
        window = kwargs.get("window")
        item_id = next(self._id_counter)
        self._items[item_id] = {"type": "window", "x": x, "y": y, "window": window}
        return item_id

    def create_image(self, x: int, y: int, **kwargs: Any) -> int:
        item_id = next(self._id_counter)
        self._items[item_id] = {"type": "image", "x": x, "y": y, **kwargs}
        return item_id

    def itemconfig(self, item_id: int, **kwargs: Any) -> None:
        if item_id in self._items:
            self._items[item_id].update(kwargs)

    def coords(self, item_id: int, x: int, y: int) -> None:
        if item_id in self._items:
            self._items[item_id]["x"] = x
            self._items[item_id]["y"] = y

    def move(self, item_id: int, dx: int, dy: int) -> None:
        if item_id in self._items:
            self._items[item_id]["x"] += dx
            self._items[item_id]["y"] += dy

    def delete(self, item_id: Any) -> None:
        if item_id == "all":
            self._items.clear()
        else:
            self._items.pop(item_id, None)

    def configure(self, **kwargs: Any) -> None:
        if "scrollregion" in kwargs:
            self._scrollregion = tuple(kwargs["scrollregion"])  # type: ignore[assignment]
        super().configure(**kwargs)

    config = configure

    def yview_moveto(self, value: float) -> None:
        self._view["y"] = float(value)

    def xview_moveto(self, value: float) -> None:
        self._view["x"] = float(value)

    def yview(self) -> Tuple[float, float]:  # pragma: no cover - unused helper
        return self._view["y"], self._view["y"] + 1

    def xview(self) -> Tuple[float, float]:  # pragma: no cover - unused helper
        return self._view["x"], self._view["x"] + 1


class Scrollbar(Widget):
    def __init__(
        self,
        master: Optional[Widget] = None,
        orient: str = VERTICAL,
        command: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, orient=orient, **kwargs)
        self.orient = orient
        self.command = command
        self._position = (0.0, 1.0)

    def set(self, first: float, last: float) -> None:
        self._position = (float(first), float(last))

    def get(self) -> Tuple[float, float]:
        return self._position

    def activate(self) -> None:  # pragma: no cover - behaviourless stub
        pass


class Text(Widget):
    def __init__(self, master: Optional[Widget] = None, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._content: str = ""

    def insert(self, index: str, value: str) -> None:
        if index == END:
            self._content += value
        else:
            self._content = value + self._content

    def get(self, start: str, end: str) -> str:
        if end == "end-1c":
            return self._content
        return self._content


class Listbox(Widget):
    def __init__(self, master: Optional[Widget] = None, selectmode: str = SINGLE, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._items: List[str] = []
        self._selection: Optional[int] = None

    def insert(self, index: Any, value: str) -> None:
        self._items.append(value)

    def selection_set(self, index: int) -> None:
        if 0 <= index < len(self._items):
            self._selection = index

    def curselection(self) -> Tuple[int, ...]:
        if self._selection is None:
            return ()
        return (self._selection,)


class Menu(Widget):
    def __init__(self, master: Optional[Widget] = None, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._entries: List[Tuple[str, Callable[[], Any]]] = []

    def add_command(self, label: str, command: Callable[[], Any]) -> None:
        self._entries.append((label, command))

    def tk_popup(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - behaviourless stub
        pass

    def grab_release(self) -> None:  # pragma: no cover - behaviourless stub
        pass


# ---------------------------------------------------------------------------
# Helper submodules exposed via ``tkinter`` compat imports


def _create_module(name: str, **functions: Callable[..., Any]) -> ModuleType:
    module = ModuleType(name)
    for attr, func in functions.items():
        setattr(module, attr, func)
    return module


def _askopenfilename(*_: Any, **__: Any) -> str:
    return ""


def _asksaveasfile(*_: Any, **__: Any) -> Optional[Any]:
    return None


def _showerror(*_: Any, **__: Any) -> None:  # pragma: no cover - behaviourless stub
    pass


def _showinfo(*_: Any, **__: Any) -> None:  # pragma: no cover - behaviourless stub
    pass


def _askyesno(*_: Any, **__: Any) -> bool:  # pragma: no cover - behaviourless stub
    return False


def _askcolor(*_: Any, **__: Any) -> Tuple[Tuple[int, int, int], str]:
    return (0, 0, 0), "#000000"


filedialog = _create_module(
    "filedialog", askopenfilename=_askopenfilename, asksaveasfile=_asksaveasfile
)
messagebox = _create_module(
    "messagebox", showerror=_showerror, showinfo=_showinfo, askyesno=_askyesno
)
colorchooser = _create_module("colorchooser", askcolor=_askcolor)

