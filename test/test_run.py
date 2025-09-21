import pytest


pytest.importorskip("numpy")

import threading
import urllib.request

from src.browser_app import BrowserPreviewApp
from src.mainwindow import Application
from src.textconfig import TextConfigureApp


def test_run_Application(tk_root):
    app = Application(master=tk_root)
    app.update()
    app.destroy()


def test_run_TextConfigureApp(tk_root):
    app = TextConfigureApp(master=tk_root)
    app.update()
    app.destroy()


def test_browser_preview_server():
    app = BrowserPreviewApp(host="127.0.0.1", port=0)
    thread = threading.Thread(target=app.serve_forever, daemon=True)
    thread.start()

    try:
        with urllib.request.urlopen(app.url) as response:
            assert response.status == 200
            body = response.read().decode("utf-8")
            assert "Browser preview" in body

        preview_url = f"{app.url}preview.png?width=200&height=150&margin=10&border=5&corner=20"
        with urllib.request.urlopen(preview_url) as response:
            assert response.status == 200
            data = response.read()
            assert data.startswith(b"\x89PNG")
            assert len(data) > 0
    finally:
        app.shutdown()
        thread.join(timeout=1)
