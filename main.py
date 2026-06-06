"""AAH Code Mode 배포 검증용 hello-world agent — AgentCore Runtime 호환.

AgentCore Runtime 컨테이너 계약 (공식):
  - HTTP server는 port 8080 에 listen
  - POST /invocations 에서 페이로드 수신 (Content-Type: application/json)
  - 200 응답 본문은 JSON
  - GET /ping 또는 / 에서 liveness probe (200 OK)

stdlib(http.server)만 사용하므로 BedrockAgentCoreApp SDK 없이도 동작.
나중에 진짜 Strands/BedrockAgentCoreApp 패턴으로 갈아끼울 때 base로 재활용.
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

    def _payload(self):
        ln = int(self.headers.get("Content-Length", 0) or 0)
        if not ln:
            return {}
        try:
            return json.loads(self.rfile.read(ln).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        # AgentCore Runtime의 liveness probe — / 또는 /ping
        if self.path in ("/ping", "/", "/healthz"):
            self._respond({"status": "ok",
                            "service": "aah-code-mode-demo",
                            "ts": datetime.utcnow().isoformat() + "Z"})
            return
        self._respond({"error": "not found"}, status=404)

    def do_POST(self):
        # AgentCore Runtime의 invoke endpoint — /invocations
        if self.path != "/invocations":
            self._respond({"error": "expected POST /invocations"}, status=404)
            return
        payload = self._payload()
        prompt = (payload.get("prompt") or
                    payload.get("input") or
                    payload.get("message") or "world")
        self._respond({
            "result": f"Hello, {prompt}!",
            "agent": "aah-code-mode-demo",
            "echo": payload,
            "env_demo": os.environ.get("AAH_DEMO", ""),
            "ts": datetime.utcnow().isoformat() + "Z",
        })

    def log_message(self, fmt, *args):
        sys.stderr.write("[req] " + (fmt % args) + "\n")


def main():
    port = int(os.environ.get("PORT", 8080))   # AgentCore Runtime 표준
    host = "0.0.0.0"
    print(f"[boot] aah-code-mode-demo listening on {host}:{port}", flush=True)
    HTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
