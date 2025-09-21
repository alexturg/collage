"""Lightweight browser preview application for the collage project."""

from __future__ import annotations

import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from string import Template
from typing import Dict, Tuple
from urllib.parse import parse_qs, urlparse

from PIL import Image, ImageDraw, ImageFont


DEFAULT_PARAMS: Dict[str, int] = {
    "width": 500,
    "height": 500,
    "margin": 10,
    "border": 4,
    "corner": 70,
}

_HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Collage Browser Preview</title>
  <style>
    body { font-family: sans-serif; margin: 2rem; background: #f5f5f5; }
    main { max-width: 960px; margin: 0 auto; background: #fff; padding: 1.5rem; border-radius: 8px; box-shadow: 0 0 1rem rgba(0,0,0,0.1); }
    form { display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
    label { display: flex; flex-direction: column; font-weight: 600; }
    input { margin-top: 0.25rem; padding: 0.45rem; font-size: 1rem; border-radius: 4px; border: 1px solid #ccc; }
    button { grid-column: 1 / -1; padding: 0.6rem 1.2rem; font-size: 1rem; border: none; border-radius: 4px; background: #0069d9; color: #fff; cursor: pointer; }
    button:hover { background: #0053aa; }
    #preview-wrapper { margin-top: 2rem; text-align: center; }
    #preview { max-width: 100%; border: 1px solid #ccc; background: repeating-conic-gradient(#fafafa 0deg 90deg, #f0f0f0 90deg 180deg); }
    footer { margin-top: 2rem; font-size: 0.9rem; color: #555; text-align: center; }
  </style>
</head>
<body>
  <main>
    <h1>Browser preview for quick layout tests</h1>
    <p>
      This lightweight preview helps to validate collage dimensions without launching the full Tkinter interface.
      Change the parameters below to redraw the placeholder collage.
    </p>
    <form id=\"controls\">
      <label>Width in pixels<input name=\"width\" type=\"number\" min=\"50\" max=\"4000\" value=\"${width}\" required></label>
      <label>Height in pixels<input name=\"height\" type=\"number\" min=\"50\" max=\"4000\" value=\"${height}\" required></label>
      <label>Padding<input name=\"margin\" type=\"number\" min=\"0\" max=\"400\" value=\"${margin}\"></label>
      <label>Border<input name=\"border\" type=\"number\" min=\"0\" max=\"200\" value=\"${border}\"></label>
      <label>Corner radius<input name=\"corner\" type=\"number\" min=\"0\" max=\"500\" value=\"${corner}\"></label>
      <button type=\"submit\">Update preview</button>
    </form>
    <div id=\"preview-wrapper\">
      <img id=\"preview\" alt=\"Collage preview\" src=\"preview.png\" />
    </div>
    <footer>
      Tip: the preview uses placeholder colours. Exported collages in the desktop app will keep the source photos.
    </footer>
  </main>
  <script>
    const form = document.getElementById('controls');
    const preview = document.getElementById('preview');
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const data = new FormData(form);
      const params = new URLSearchParams(data);
      params.append('t', Date.now());
      preview.src = `preview.png?${params.toString()}`;
    });
  </script>
</body>
</html>
""")


class _PreviewRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves the preview page and generated PNG images."""

    server: "BrowserPreviewServer"

    def log_message(self, format: str, *args) -> None:  # pragma: no cover - avoid noisy logs in tests
        return

    def do_GET(self) -> None:  # noqa: N802 - signature defined by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path in {"", "/"}:
            self._handle_index()
        elif parsed.path == "/preview.png":
            self._handle_preview(parse_qs(parsed.query))
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _handle_index(self) -> None:
        html = _HTML_TEMPLATE.safe_substitute(**DEFAULT_PARAMS).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def _handle_preview(self, query: Dict[str, list]) -> None:
        params = DEFAULT_PARAMS.copy()
        for key in params:
            if key in query and query[key]:
                try:
                    params[key] = int(query[key][0])
                except ValueError:
                    continue

        image = self.server.app.generate_preview(**params)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        data = buffer.getvalue()
        buffer.close()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/png")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class BrowserPreviewServer(ThreadingHTTPServer):
    """Threaded HTTP server that is aware of the preview application instance."""

    def __init__(self, server_address: Tuple[str, int], app: "BrowserPreviewApp") -> None:
        super().__init__(server_address, _PreviewRequestHandler)
        self.app = app


class BrowserPreviewApp:
    """Small helper that exposes a lightweight collage preview in a browser."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.server = BrowserPreviewServer((host, port), app=self)

    @property
    def url(self) -> str:
        host, port = self.server.server_address
        display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
        return f"http://{display_host}:{port}/"

    def generate_preview(self, width: int, height: int, margin: int, border: int, corner: int) -> Image.Image:
        width = max(50, min(width, 4000))
        height = max(50, min(height, 4000))
        margin = max(0, min(margin, min(width, height) // 2))
        border = max(0, min(border, min(width, height) // 2))
        corner = max(0, min(corner, min(width, height) // 2))

        image = Image.new("RGBA", (width, height), (240, 240, 240, 255))
        draw = ImageDraw.Draw(image)

        inner_left = margin
        inner_top = margin
        inner_right = width - margin
        inner_bottom = height - margin
        border_color = (80, 120, 200, 255)

        try:
            draw.rounded_rectangle(
                (inner_left, inner_top, inner_right, inner_bottom),
                radius=corner,
                fill=(255, 255, 255, 255),
                outline=border_color,
                width=border,
            )
        except AttributeError:  # pragma: no cover - Pillow < 5 does not provide rounded_rectangle
            draw.rectangle(
                (inner_left, inner_top, inner_right, inner_bottom),
                fill=(255, 255, 255, 255),
                outline=border_color,
                width=border,
            )

        colors = [
            (244, 67, 54, 200),
            (33, 150, 243, 200),
            (76, 175, 80, 200),
            (255, 193, 7, 200),
        ]
        mid_x = (inner_left + inner_right) // 2
        mid_y = (inner_top + inner_bottom) // 2

        draw.rectangle((inner_left, inner_top, mid_x, mid_y), fill=colors[0])
        draw.rectangle((mid_x, inner_top, inner_right, mid_y), fill=colors[1])
        draw.rectangle((inner_left, mid_y, mid_x, inner_bottom), fill=colors[2])
        draw.rectangle((mid_x, mid_y, inner_right, inner_bottom), fill=colors[3])

        draw.line((mid_x, inner_top, mid_x, inner_bottom), fill=border_color, width=max(1, border // 2))
        draw.line((inner_left, mid_y, inner_right, mid_y), fill=border_color, width=max(1, border // 2))

        caption = f"{width}×{height} px | margin {margin}px | border {border}px"
        try:
            font = ImageFont.load_default()
            if hasattr(draw, "textbbox"):
                left, top, right, bottom = draw.textbbox((0, 0), caption, font=font)
                text_w = right - left
                text_h = bottom - top
            else:  # pragma: no cover - Pillow < 8 legacy path
                text_w, text_h = draw.textsize(caption, font=font)
            padding = 6
            box = (
                margin + border + padding,
                height - margin - border - text_h - padding,
                margin + border + text_w + padding,
                height - margin - border - padding,
            )
            draw.rectangle(box, fill=(255, 255, 255, 200))
            draw.text((box[0] + 2, box[1] + 2), caption, fill=(40, 40, 40, 255), font=font)
        except OSError:  # pragma: no cover - fonts may be missing in some environments
            pass

        return image

    def serve_forever(self) -> None:
        self.server.serve_forever()

    def run(self, open_browser: bool = True) -> None:
        if open_browser:
            webbrowser.open(self.url)
        self.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def run_in_thread(self, open_browser: bool = False) -> threading.Thread:
        thread = threading.Thread(target=self.run, kwargs={"open_browser": open_browser}, daemon=True)
        thread.start()
        time.sleep(0.1)
        return thread
