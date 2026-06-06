# aah-code-mode-demo

AI Agent Hub의 **Code Mode** 배포 파이프라인 검증용 데모 agent.

**기술 스택**: LangChain + LangGraph + Amazon Bedrock (Claude Haiku 4.5)
**컨테이너 계약**: AWS Bedrock AgentCore Runtime (port 8080 · POST /invocations · GET /ping)

## LangGraph 그래프

```
START → llm → END
```
단일 LLM 노드 · system prompt + user 메시지를 Claude Haiku 4.5에 전달 후 응답.

## AgentCore Runtime 컨테이너 계약

| | path | 설명 |
|---|---|---|
| GET  | `/` 또는 `/ping` | liveness probe → `{"status":"ok"}` |
| POST | `/invocations`   | `{"prompt": "..."}` → `{"result": "...", ...}` |

## 환경변수 (선택)

| key | default | 설명 |
|---|---|---|
| `MODEL_ID` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Bedrock 모델 (cross-region inference profile) |
| `AWS_REGION` | `us-east-1` | Bedrock 호출 region |
| `PORT` | `8080` | HTTP listen port (AgentCore Runtime 표준) |

## IAM 정책 (컨테이너 role)

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": "*"
}
```
AAH가 자동으로 `aah-agentcore-runtime-role` 적용 (이미 Bedrock 권한 포함).

## AAH 배포

1. `/develop/code-deploy` → "Agent 배포"
2. repo URL: `https://github.com/myzzix4/aah-code-mode-demo`
3. ~6-10분 (LangChain 의존성 설치 추가)
4. 상태 `ready` → AgentCore Runtime ARN 발급

## 호출

```bash
# boto3로 직접
import boto3, json
ac = boto3.client("bedrock-agentcore", region_name="us-east-1")
r = ac.invoke_agent_runtime(
    agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:...",
    payload=json.dumps({"prompt":"LangGraph가 뭔지 한 줄로?"}).encode(),
)
print(json.loads(r["response"].read()))
```

## 로컬 테스트

AWS 자격증명 + Bedrock 권한 필요:

```bash
pip install -r requirements.txt
PORT=8080 AWS_REGION=us-east-1 python main.py

curl http://localhost:8080/ping
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"AAH가 뭐 하는 서비스야?"}'
```

## 향후 확장

LangGraph 그래프에 다중 노드 추가:
- ReAct 패턴 (LLM + tool node + condition router)
- RAG (retrieval node 추가)
- Multi-agent (subgraph 또는 supervisor 노드)

같은 컨테이너 계약(8080 + /invocations) 유지하면 AAH 인프라 변경 없이 그대로 동작.
