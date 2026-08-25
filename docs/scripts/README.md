# 📜 Operations & Management Scripts (`scripts`) 문서

본 문서는 **Agent Ecosystem 전체 및 모듈별 서비스 제어를 담당하는 쉘 스크립트** 사용 가이드입니다.

---

## 1. 개요

프로젝트에는 개발 편의성 및 운영 단순화를 위해 **루트 원클릭 제어 스크립트 (`start.sh`, `stop.sh`)**와 **모듈별 세부 제어 스크립트 (`scripts/`)**가 마련되어 있습니다.

---

## 2. 디렉토리 구조

```text
scripts/
├── app/                    # Orchestrator App 제어 스크립트
│   ├── start.sh            # Orchestrator 도커 빌드 & 백그라운드 시작
│   ├── update.sh           # Orchestrator 이미지 재빌드 & 컨테이너 재보내기
│   └── stop.sh             # Orchestrator 컨테이너 중지
├── agent_server/           # Remote Agents Server 제어 스크립트
│   ├── start.sh            # Echo & LangChain 서브 에이전트 시작
│   ├── update.sh           # 서브 에이전트 이미지 업데이트
│   └── stop.sh             # 서브 에이전트 중지
├── mcp_server/             # MCP Discovery Server 제어 스크립트
│   ├── start.sh            # FastMCP SSE 서버 시작
│   ├── update.sh           # MCP 서버 이미지 업데이트
│   └── stop.sh             # MCP 서버 중지
└── monitoring/             # Monitoring Stack 제어 스크립트
    ├── start.sh            # Prometheus/Loki/Grafana 스택 시작
    ├── update.sh           # 모니터링 스택 업데이트
    └── stop.sh             # 모니터링 스택 중지
```

---

## 3. 원클릭 통합 관리 스크립트 (Root Shell Scripts)

### 3.1. 전체 서비스 한 번에 시작 (`./start.sh`)
- **실행 위치**: 프로젝트 루트 디렉토리
- **동작 단계**:
  1. 공유 도커 네트워크 (`agent_shared_net`) 검사 및 자동 생성
  2. `monitoring` 스택 디그레이드 없는 인프라 시작
  3. `mcp_server` FastMCP Discovery 서비스 빌드 및 실행
  4. `agent_server` 원격 에이전트 2종 (Echo, LangChain) 실행
  5. `app` Orchestrator Supervisor API 서버 실행
  6. 서비스들의 헬스 상태 및 활성 엔드포인트 URL 출력

```bash
./start.sh
```

### 3.2. 전체 서비스 한 번에 종료 (`./stop.sh`)
- **실행 위치**: 프로젝트 루트 디렉토리
- **동작 단계**:
  - `app`, `agent_server`, `mcp_server`, `monitoring` 모든 컨테이너 인프라를 안전하게 stop & down 처리합니다.

```bash
./stop.sh
```
