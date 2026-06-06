# aah-code-mode-demo

AI Agent Hub의 **Code Mode** 배포 파이프라인 검증용 hello-world agent.
**AWS Bedrock AgentCore Runtime 컨테이너 계약**을 그대로 따름.

## AgentCore Runtime 계약

| 항목 | 값 |
|---|---|
| listen port | `8080` |
| invoke | `POST /invocations` (JSON in/out) |
| liveness | `GET /` 또는 `GET /ping` (200 OK) |

stdlib(`http.server`)만 사용 — 의존성 0. BedrockAgentCoreApp SDK 박지 않아도
표준 계약만 지키면 AgentCore Runtime이 호출함.

## AAH 배포

1. AAH `/develop/code-deploy` → "Agent 배포"
2. repo URL: `https://github.com/myzzix4/aah-code-mode-demo`
3. branch: `main`
4. ~6분 → status `ready` → AgentCore Runtime ARN 발급

## 호출

```bash
# AAH 호스트 proxy를 통해
curl -X POST $AAH_HOST/api/internal/agents/$AGENT_ID/invoke \
  -H "Content-Type: application/json" \
  -d '{"input":"장호"}'

# 또는 boto3로 직접
import boto3
acc = boto3.client("bedrock-agentcore", region_name="us-east-1")
acc.invoke_agent_runtime(
    agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:...",
    payload=json.dumps({"prompt":"장호"}).encode(),
)
```

## 로컬 테스트

```bash
PORT=8080 python main.py
curl http://localhost:8080/ping
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" -d '{"prompt":"장호"}'
```
