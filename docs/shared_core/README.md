# 📦 Shared Core Library (`shared_core`) 문서

본 문서는 **전체 Agent Ecosystem 프로젝트에서 공통으로 참조 및 재사용하는 라이브러리 모듈 `shared_core`**에 대한 기술 명세서입니다.

---

## 1. 개요

`shared_core`는 독립된 Python 패키지로 구동되며 `app`, `agent_server`, `mcp_server` 등 모든 마이크로서비스에서 로깅 포맷 가이드를 일관되게 유지하고 YAML 프롬프트 설정을 안전하게 로드할 수 있도록 유틸리티를 제공합니다.

---

## 2. 디렉토리 및 패키지 구조

```text
shared_core/
├── src/shared_core/
│   ├── __init__.py         # 패키지 익스포트 인터페이스
│   ├── logger.py           # Structlog 기반 UTF-8 구조화 로그 로거
│   ├── prompt.py           # YAML 프롬프트 로더 유틸리티
│   └── py.typed            # PEP 561 Type Hinting 마커 파일
├── pyproject.toml          # uv 및 패키지 빌드 스펙 (build-system: hatchling)
├── uv.lock                 # 의존성 잠금 파일
└── README.md               # 메인 참조 링커
```

---

## 3. 핵심 모듈 상세

### 3.1. `logger.py` (구조화 로깅 유틸리티)
- **주요 기능**: `structlog` 라이브러리를 바인딩하여 한국어/UTF-8 문자가 깨지지 않도록 처리하고 JSON 또는 Console 색상 출력을 지원합니다.
- **주요 함수**:
  - `setup_logger(log_level="INFO", json_format=False)`: 전역 로거 포맷터 및 핸들러 초기화.
  - `logger`: 인스턴스화된 `structlog` 로거 객체.
- **로그 네이밍 컨벤션**:
  - `task.<module>.<event>`: 태스크 처리 단계 로그 (예: `task.echo_agent.received_message`)
  - `artifact.<module>.<event>`: 아티팩트 및 메시지 생성 로그 (예: `artifact.langchain_agent.event_created`)

### 3.2. `prompt.py` (YAML 프롬프트 로더)
- **주요 기능**: 지정된 YAML 프롬프트 파일 경로에서 특정 키의 텍스트 값을 안전하게 파싱하여 로드합니다.
- **주요 함수**:
  - `load_prompt(yaml_path: str | Path, key: str = "system_prompt", default: str = "") -> str`
- **예시 사용법**:
  ```python
  from shared_core.prompt import load_prompt

  prompt_text = load_prompt("prompts/supervisor.yml", key="supervisor_instruction")
  ```
