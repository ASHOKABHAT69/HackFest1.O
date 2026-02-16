from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import cgi
import tempfile
from dataclasses import asdict

from .analyzer import analyze_hybrid


MAX_UPLOAD_SIZE_MB = 20
ALLOWED_EXTENSIONS = {"wav"}
PACKAGE_DIR = Path(__file__).resolve().parent


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _build_index_html() -> bytes:
    html = (PACKAGE_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    html = html.replace("{{ max_upload_size_mb }}", str(MAX_UPLOAD_SIZE_MB))
    html = html.replace("{{ url_for('static', filename='styles.css') }}", "/static/styles.css")
    html = html.replace("{{ url_for('static', filename='app.js') }}", "/static/app.js")
    return html.encode("utf-8")


def _json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    raw = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _serve_static(handler: BaseHTTPRequestHandler, filename: str, content_type: str) -> None:
    file_path = PACKAGE_DIR / "static" / filename
    if not file_path.exists():
        handler.send_error(HTTPStatus.NOT_FOUND)
        return

    raw = file_path.read_bytes()
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _parse_upload(handler: BaseHTTPRequestHandler) -> tuple[bytes, str] | tuple[None, None]:
    form = cgi.FieldStorage(
        fp=handler.rfile,
        headers=handler.headers,
        environ={
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": handler.headers.get("Content-Type", ""),
        },
    )

    if "audio_file" not in form:
        return None, None

    file_item = form["audio_file"]
    filename = file_item.filename or ""
    data = file_item.file.read() if file_item.file else b""
    return data, filename


def _analyze_upload_bytes(audio_data: bytes, filename: str) -> dict:
    if not filename:
        raise ValueError("Empty filename. Choose a WAV file.")
    if not _allowed_file(filename):
        raise ValueError("Unsupported format. Please upload a .wav file.")
    if not audio_data:
        raise ValueError("Uploaded file is empty.")

    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as temp_file:
        temp_file.write(audio_data)
        temp_file.flush()
        report = analyze_hybrid(temp_file.name)
    return asdict(report)


class AudioForensicsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            payload = _build_index_html()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/static/styles.css":
            _serve_static(self, "styles.css", "text/css; charset=utf-8")
            return
        if self.path == "/static/app.js":
            _serve_static(self, "app.js", "application/javascript; charset=utf-8")
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0") or 0)
        if content_length > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            _json_response(self, {"error": "File too large."}, 413)
            return

        audio_data, filename = _parse_upload(self)
        if audio_data is None:
            _json_response(self, {"error": "No file provided. Use the audio dropzone."}, 400)
            return

        try:
            report = _analyze_upload_bytes(audio_data, filename or "")
        except ValueError as err:
            _json_response(self, {"error": str(err)}, 400)
            return
        except Exception as err:  # pragma: no cover - defensive
            _json_response(self, {"error": f"Analysis failed: {err}"}, 500)
            return

        _json_response(self, report, 200)


def create_server(host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), AudioForensicsHandler)


def main() -> None:
    server = create_server()
    print("Audio Forensic Toolkit UI running at http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
