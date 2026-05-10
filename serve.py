"""
本地一键启动：
- 静态托管 index.html 等
- POST /v1/chat/completions  → 反代到 https://api.opus5.xyz （注入 API key）
- GET  /proxy/img?url=...    → 下载远端图片（避开浏览器 CORS / 图床 UA 拒绝）

用法：python serve.py     然后浏览器打开 http://127.0.0.1:8765/
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import os
import sys
import webbrowser
import threading

API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.opus5.xyz").rstrip("/")
PORT = int(os.environ.get("PORT", "8765"))
ROOT = os.path.dirname(os.path.abspath(__file__))

ALLOWED_API_PATHS = {"/v1/chat/completions", "/v1/images/generations"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.address_string(), fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path in ALLOWED_API_PATHS:
            return self._proxy_api()
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/proxy/img":
            return self._proxy_img(parsed)
        return super().do_GET()

    def _proxy_api(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            req = urllib.request.Request(
                f"{BASE_URL}{self.path}",
                data=body,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as r:
                resp_body = r.read()
                self.send_response(r.status)
                self._cors()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            msg = f'{{"error":"local proxy: {str(e)}"}}'.encode("utf-8")
            self.send_response(502)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def _proxy_img(self, parsed):
        qs = urllib.parse.parse_qs(parsed.query)
        target = (qs.get("url") or [""])[0]
        if not target:
            self.send_response(400)
            self.end_headers()
            return
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(target, headers={"User-Agent": "Mozilla/5.0"}),
                timeout=120,
            )
            data = r.read()
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", r.headers.get("Content-Type", "image/png"))
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())


class TServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    if not API_KEY:
        print("[serve] 错误：未设置 OPENAI_API_KEY 环境变量。")
        print("        Windows  PowerShell:  $env:OPENAI_API_KEY = 'sk-...'")
        print("        Windows  cmd:         set OPENAI_API_KEY=sk-...")
        print("        macOS / Linux:        export OPENAI_API_KEY=sk-...")
        print("        然后重新运行：python serve.py")
        sys.exit(1)
    server = TServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"[serve] {url}")
    print(f"[serve] root      = {ROOT}")
    print(f"[serve] base_url  = {BASE_URL}")
    print("[serve] Ctrl+C 退出")
    if "--no-open" not in sys.argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve] bye")


if __name__ == "__main__":
    main()
