# aah-code-mode-demo

AI Agent Hub의 **Code Mode** 배포 파이프라인 검증용 hello-world agent.

stdlib(`http.server`)만 사용해서 의존성 0. AAH의 CodeBuild → ECR →
App Runner 사이클이 한 사이클(~6분) 안에 끝나는지 확인하는 데 쓰입니다.

## Endpoints

| | path | 설명 |
|---|---|---|
| GET  | `/`           | health + 서비스 메타 JSON |
| GET  | `/healthz`    | liveness probe (`{"status":"ok"}`) |
| POST | `/`           | `{prompt: ...}` → greeting echo |
| POST | `/invocations`| BedrockAgentCoreApp 호환 (`payload→result`) |

## AAH 배포 방법

1. AAH `/develop/code-deploy` → "Agent 배포" 클릭
2. repo URL: `https://github.com/<owner>/aah-code-mode-demo`
3. branch: `main` / 기본값 그대로 (entry: `python main.py`)
4. ~6분 대기 → status `ready` → URL 받음

## 직접 호출

```bash
URL=https://<xxx>.us-east-1.awsapprunner.com
curl $URL/
curl -X POST $URL/ -H 'Content-Type: application/json' -d '{"prompt":"장호"}'
```

## 로컬 실행

```bash
python main.py        # :8000
curl http://localhost:8000/
```

## 향후 확장

이 파일을 base로 `bedrock_agentcore`/`strands` SDK 도입 시 `requirements.txt`에
추가 + `main.py`의 `do_POST` 안에서 SDK 호출만 변경하면 된다. AAH의 entry.sh가
같은 패턴(root `main.py` + `requirements.txt`)을 자동 인식.
