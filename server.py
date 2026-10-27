"""本地服务器：提供游戏页面 + 接收遥测数据写入 telemetry/ 目录。
运行: python server.py   然后浏览器打开 http://localhost:8765
  telemetry/snapshot.json  每秒覆盖写的实时快照
  telemetry/events.jsonl   逐条追加的事件日志
  telemetry/errors.log     前端 JS 错误
"""
import http.server, json, os, sys, time

PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
TEL = os.path.join(ROOT, "telemetry")
os.makedirs(TEL, exist_ok=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".webmanifest": "application/manifest+json"}

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):  # 静音普通访问日志
        pass

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            if self.path == "/t":
                if data.get("snapshot") is not None:
                    tmp = os.path.join(TEL, "snapshot.json.tmp")
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(data["snapshot"], f, ensure_ascii=False, indent=1)
                    os.replace(tmp, os.path.join(TEL, "snapshot.json"))
                evs = data.get("events") or []
                if evs:
                    with open(os.path.join(TEL, "events.jsonl"), "a", encoding="utf-8") as f:
                        for e in evs:
                            f.write(json.dumps(e, ensure_ascii=False) + "\n")
                errs = data.get("errors") or []
                if errs:
                    with open(os.path.join(TEL, "errors.log"), "a", encoding="utf-8") as f:
                        for e in errs:
                            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + json.dumps(e, ensure_ascii=False) + "\n")
            self.send_response(204)
            self.end_headers()
        except Exception as ex:
            with open(os.path.join(TEL, "errors.log"), "a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + "[server] " + repr(ex) + "\n")
            self.send_response(500)
            self.end_headers()


if __name__ == "__main__":
    print(f"Match3 server running: http://localhost:{PORT}  (close this window to stop)")
    sys.stdout.flush()
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
