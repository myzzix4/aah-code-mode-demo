"""AAH Code Mode 배포 검증용 hello-world agent.

stdlib만 사용 — 의존성 0, 빌드 빠름. AgentCore Runtime의 표준 패턴
(POST /invocations + 페이로드)도 지원하므로 향후 진짜 BedrockAgentCoreApp/
Strands SDK 패턴으로 갈아끼울 때 base로 재활용 가능.

Endpoints:
  GET  /                  → health + 서비스 메타
  GET  /healthz           → liveness probe ("ok")
  POST /                  → echo + greeting
  POST /invocations       → BedrockAgentCoreApp 호환 형식 (payload→result)
"""
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def _respond(self, body, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode("utf-8"))

    def _read_payload(self):
        ln = int(self.headers.get("Content-Length", 0) or 0)
        if not ln:
            return {}
        try:
            return json.loads(self.rfile.read(ln).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        if self.path.startswith("/healthz"):
            self._respond({"status": "ok"})
            return
        self._respond({
            "service": "aah-code-mode-demo",
            "status": "ok",
            "hint": "POST {\"prompt\":\"...\"} to / or /invocations",
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def do_POST(self):
        payload = self._read_payload()
        prompt = payload.get("prompt") or payload.get("input") or "world"
        self._respond({
            "result": f"Hello, {prompt}!",
            "agent": "aah-code-mode-demo",
            "echo": payload,
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def log_message(self, fmt, *args):
        sys.stderr.write("[req] " + (fmt % args) + "\n")


def main():
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    print(f"[boot] aah-code-mode-demo listening on {host}:{port}", flush=True)
    HTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
