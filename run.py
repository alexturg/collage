"""Entrypoint for launching the collage application."""

import argparse
import contextlib

from src.browser_app import BrowserPreviewApp
from src.mainwindow import Application
from src.tk_compat import tk


def _run_tkinter():
    """Run the classic Tkinter desktop version of the application."""
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()


def _run_browser(args):
    """Run the lightweight browser preview application."""
    browser_app = BrowserPreviewApp(host=args.host, port=args.port)
    print(f"Starting browser preview at {browser_app.url}")
    with contextlib.suppress(KeyboardInterrupt):
        browser_app.run(open_browser=not args.no_browser_open)


def main():
    parser = argparse.ArgumentParser(
        description="Run the collage application either as a Tkinter app or as a browser preview.",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Start a lightweight browser preview instead of the Tkinter GUI.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Hostname to bind the browser preview server to (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind the browser preview server to (default: 8765).",
    )
    parser.add_argument(
        "--no-browser-open",
        action="store_true",
        help="Do not automatically open the browser when running the preview.",
    )

    args = parser.parse_args()

    if args.browser:
        _run_browser(args)
    else:
        _run_tkinter()


if __name__ == "__main__":
    main()
