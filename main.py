"""AAH Code Mode 데모 — LangChain + LangGraph + Amazon Bedrock.

LangGraph 그래프:  START → llm → END
모델:              Claude Haiku 4.5 via Bedrock (us-east-1)
컨테이너 계약:     AgentCore Runtime — port 8080 + POST /invocations + GET /ping

핵심:
  - AgentCore Runtime이 컨테이너의 IAM Role을 통해 자동으로 Bedrock 호출 권한 부여
  - 별도 AWS 자격증명 환경변수 불필요 (boto3 default chain → role)
  - 페이로드: {"prompt": "..."} → 응답: {"result": "..."}

Bedrock IAM 정책 필요:
  bedrock:InvokeModel · bedrock:InvokeModelWithResponseStream
  on  us.anthropic.claude-haiku-4-5-20251001-v1:0  (cross-region inference profile)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Annotated, TypedDict

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# ─── LangGraph state + node ──────────────────────────────────────────

class State(TypedDict):
    """Single-message-list state — LangGraph reducer가 새 메시지를 append."""
    messages: Annotated[list, add_messages]


_MODEL_ID = os.environ.get(
    "MODEL_ID",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
)
_REGION = os.environ.get("AWS_REGION", "us-east-1")
_SYSTEM = (
    "당신은 AI Agent Hub (AAH)의 Code Mode 데모용 agent다. "
    "LangChain + LangGraph + Amazon Bedrock 위에서 동작한다는 사실을 답변 시 자연스럽게 한 번 언급한다. "
    "응답은 한국어로 간결하게."
)

_llm = ChatBedrock(model_id=_MODEL_ID, region_name=_REGION,
                     model_kwargs={"max_tokens": 1024, "temperature": 0.3})


def llm_node(state: State) -> dict:
    """그래프의 유일한 노드 — system prompt + 누적된 user 메시지를 LLM에 전달."""
    msgs = [SystemMessage(content=_SYSTEM)] + list(state["messages"])
    out = _llm.invoke(msgs)
    return {"messages": [out]}


_g = StateGraph(State)
_g.add_node("llm", llm_node)
_g.add_edge(START, "llm")
_g.add_edge("llm", END)
_GRAPH = _g.compile()


# ─── AgentCore Runtime container contract (HTTP) ─────────────────────

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
        if self.path in ("/ping", "/", "/healthz"):
            self._respond({"status": "ok",
                            "service": "aah-code-mode-demo",
                            "framework": "langchain+langgraph",
                            "model": _MODEL_ID,
                            "ts": datetime.utcnow().isoformat() + "Z"})
            return
        self._respond({"error": "not found"}, status=404)

    def do_POST(self):
        if self.path != "/invocations":
            self._respond({"error": "expected POST /invocations"}, status=404)
            return
        payload = self._payload()
        prompt = (payload.get("prompt") or payload.get("input") or
                    payload.get("message") or "").strip()
        if not prompt:
            self._respond({"error": "empty prompt"}, status=400)
            return
        try:
            result = _GRAPH.invoke({"messages": [HumanMessage(content=prompt)]})
            answer = result["messages"][-1].content
            self._respond({
                "result": answer,
                "agent": "aah-code-mode-demo",
                "framework": "langgraph",
                "model": _MODEL_ID,
                "graph_nodes": ["llm"],
                "ts": datetime.utcnow().isoformat() + "Z",
            })
        except Exception as e:
            sys.stderr.write(f"[err] {type(e).__name__}: {e}\n")
            self._respond({"error": str(e)[:500]}, status=500)

    def log_message(self, fmt, *args):
        sys.stderr.write("[req] " + (fmt % args) + "\n")


def main():
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"
    print(f"[boot] aah-code-mode-demo on {host}:{port}  model={_MODEL_ID}", flush=True)
    HTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
