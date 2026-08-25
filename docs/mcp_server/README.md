# 🔌 MCP Server (`mcp_server`) 문서

본 문서는 **Agent Ecosystem의 동적 탐색을 담당하는 `mcp_server` (FastMCP Server)**의 역량, 프로토콜 및 도구 구현에 대해 설명합니다.

---

## 1. 개요

`mcp_server`는 Anthropic의 **Model Context Protocol (MCP)** 표준에 따라 구축된 FastMCP SSE(Server-Sent Events) 서버입니다.
네트워크상에 등록된 분산 서브 에이전트들의 정보(Agent Card)를 프로빙(Probing)하여, 중앙 Supervisor가 동적으로 사용 가능한 에이전트를 탐색하고 호출할 수 있는 메커니즘을 제공합니다.

---

## 2. 디렉토리 및 파일 구조

```text
mcp_server/
├── tools/                  # MCP 전용 실행 도구 정의
│   └── agent_card.py       # list_agent_cards (Sub-Agent 카드 동적 수집 도구)
├── server.py               # FastMCP SSE 서버 진입점 (Port: 28002)
├── Dockerfile              # 도커 이미지 빌드 파일
├── docker-compose.yml      # agent_mcp_server 도커 서비스 정의
├── pyproject.toml          # uv 패키지 명세
└── README.md               # 메인 참조 링커
```

---

## 3. 핵심 제공 MCP 도구 (`list_agent_cards`)

### 3.1. `list_agent_cards`
- **도구 명**: `list_agent_cards`
- **설명**: 네트워크에 존재하는 서브 에이전트들의 HTTP URL 엔드포인트를 순회하며 `/.well-known/agent-card.json`을 요청, 수집한 에이전트 카드의 JSON 메타데이터 리스트를 반환합니다.
- **기본 검색 대상 목록**:
  - `http://agent_echo_server:28001`
  - `http://agent_langchain_server:28003`
- **Agent Card 수집 구조 예시**:
  ```json
  [
    {
      "name": "echo_agent",
      "description": "Echo agent powered by LangGraph",
      "url": "http://agent_echo_server:28001"
    },
    {
      "name": "langchain_agent",
      "description": "LangChain ReAct 에이전트 예제 (도구: 숫자 더하기, 날씨 조회)",
      "url": "http://agent_langchain_server:28003"
    }
  ]
  ```

---

## 4. MCP 서버 실행 및 SSE 엔드포인트

- **실행 명령**: `python server.py`
- **전송 프로토콜**: Server-Sent Events (`SSE`)
- **포트**: `28002`
- **SSE 접속 URL**: `http://agent_mcp_server:28002/sse`
