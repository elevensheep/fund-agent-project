# Git 컨벤션 가이드 (Git Convention)

Agent Ecosystem 프로젝트의 일관된 소스코드 이력 관리 및 원활한 협업을 위한 Git 브랜치 전략, 커밋 메시지 작성 규칙, PR 가이드라인입니다.

---

## 📌 목차 (Table of Contents)

1. [🌿 브랜치 전략 (Branching Strategy)](#-브랜치-전략-branching-strategy)
2. [📝 커밋 메시지 컨벤션 (Commit Message Convention)](#-커밋-메시지-컨벤션-commit-message-convention)
3. [🔀 Pull Request (PR) & 코드 리뷰 가이드](#-pull-request-pr--코드-리뷰-가이드)
4. [🏷️ 이슈 및 라벨 관리 (Issue & Labeling)](#-이슈-및-라벨-관리-issue--labeling)
5. [✅ 커밋/푸시 전 체크리스트 (Pre-Commit / Pre-Push Checklist)](#-커밋푸시-전-체크리스트-pre-commit--pre-push-checklist)

---

## 🌿 브랜치 전략 (Branching Strategy)

본 프로젝트는 **GitHub Flow**와 **Git Flow**의 이점을 결합한 브랜치 전략을 따릅니다.

### 주요 브랜치 (Main Branches)

- **`main`**: 실제 서비스 배포 및 안정화된 최신 상태를 유지하는 메인 브랜치입니다. 직접 커밋은 금지되며 PR을 통해서만 병합(Merge)합니다.
- **`develop`**: 다음 버전을 위한 통합 개발 브랜치입니다. 기능 개발이 완료된 브랜치들이 1차적으로 병합되는 공간입니다.

### 작업 브랜치 (Topic/Feature Branches)

기능 구현, 버그 수정 등의 작업은 명명 규칙에 따라 새로 작성된 독립적인 브랜치에서 진행합니다.

| 브랜치 접두사 | 설명 | 예시 |
| :--- | :--- | :--- |
| **`feature/`** | 새로운 기능 및 모듈 개발 | `feature/app-supervisor-routing`, `feature/#12-mcp-discovery` |
| **`fix/`** 또는 **`bugfix/`** | 버그 및 결함 수정 | `fix/a2a-timeout-handling`, `fix/#45-logger-utf8` |
| **`refactor/`** | 기능 변경 없는 코드 구조 개선 | `refactor/shared-core-prompt-loader` |
| **`docs/`** | 문서 작성 및 수정 | `docs/git-convention`, `docs/architecture-update` |
| **`test/`** | 테스트 코드 작성 및 하네스 환경 구축 | `test/harness-contract-probing` |
| **`hotfix/`** | `main` 브랜치 긴급 버그 수정 | `hotfix/v1.0.1-security-patch` |
| **`release/`** | 배포 준비 브랜치 | `release/v1.1.0` |

### 브랜치 명명 규칙 (Naming Rules)
- 영문 소문자, 숫자, 하이픈(`-`) 사용
- issue 번호가 있을 경우 포함 권장: `<type>/#<issue-number>-<short-description>`
- 예시: `feature/#24-add-langchain-agent`

---

## 📝 커밋 메시지 컨벤션 (Commit Message Convention)

커밋 메시지는 **Conventional Commits 1.0.0** 표준을 준수합니다.

### 1. 기본 구조

```text
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

- **Subject (제목)**: 변경 사항의 명확하고 간결한 요약 (50자 이내)
- **Body (본문)**: 무엇을 왜 변경했는지에 대한 상세한 설명 (선택 사항)
- **Footer (꼬리말)**: 이슈 추적 번호 연결 등 (`Closes #12`, `Fixes #34`)

---

### 2. Type (커밋 유형)

| Type | 설명 |
| :--- | :--- |
| **`feat`** | 새로운 기능 추가 (`app`, `agent_server`, `mcp_server` 등) |
| **`fix`** | 버그 수정 |
| **`docs`** | 문서 수정 및 추가 (`docs/*`, `README.md` 등) |
| **`style`** | 코드 의미 변경 없는 포맷팅, 세미콜론 누락, 들여쓰기 수정 |
| **`refactor`** | 리팩토링 (기능 변경이나 버그 수정이 아닌 코드 개선) |
| **`test`** | 테스트 코드 추가, 수정, 테스트 하네스 변경 |
| **`chore`** | 빌드 업무 수정, 패키지 매니저 설정, 도커 설정, `.gitignore` 등 환경 작업 |
| **`perf`** | 성능 개선 관련 코드 변경 |
| **`ci`** | CI/CD 파이프라인 관련 변경 |

---

### 3. Scope (작업 범위 - 선택사항)

프로젝트 모듈명 또는 영향 범위를 명시합니다.

- `app`: Orchestrator (Supervisor Client Server)
- `agent`: Remote Sub-Agents (`echo_agent`, `langchain_agent` 등)
- `mcp`: FastMCP Discovery Server
- `shared`: Shared Core Library (`logger`, `prompt` 등)
- `monitoring`: Prometheus, Grafana, Loki 스택
- `harness`: 테스트 & 평가 하네스 프레임워크
- `scripts`: 제어 쉘 스크립트

---

### 4. Subject 작성 규칙

1. 제목은 50자 이내로 간결하게 작성합니다.
2. 제목 끝에 마침표(`.`)를 붙이지 않습니다.
3. 개작문/명령조로 작성합니다. (예: `Fix bug` 또는 `A2A 통신 타임아웃 예외 처리 추가`)
4. 한글 또는 영문 작성 시 팀 내 가독성을 고려하여 명확하게 표기합니다.

---

### 5. 커밋 예시 (Examples)

#### 좋은 예시 ⭕

```bash
# 기능 추가
feat(app): MCP 동적 탐색 연동 및 서브 에이전트 자동 등록 기능 추가

# 버그 수정
fix(agent): A2A JSON-RPC 2.0 응답 타임아웃 예외 처리 추가

# 문서 수정
docs(convention): Git convention 가이드 문서 작성 (Closes #15)

# 본문과 꼬리말 포함 예시
feat(mcp): agent_card 프로빙 서킷 브레이커 패턴 적용

- 원격 서브 에이전트 응답 불능 시 백오프 재시도 로직 추가
- MCP SSE 연결 스트림 안정성 확보

Closes #42
```

#### 잘못된 예시 ❌

```bash
# 모호하고 성의 없는 메시지
fix: 버그 수정
update logic
wip
asdf

# 마침표 및 너무 긴 제목
feat(app): supervisor agent에서 발생하던 여러 문제점들을 한꺼번에 수정하였으며 추가로 테스트 코드까지 작성하였습니다.
```

---

## 🔀 Pull Request (PR) & 코드 리뷰 가이드

### PR 작성 양식

- **PR 제목**: `[<type>] <간결한 설명>`
  - 예: `[feat] MCP 기반 동적 에이전트 카드 수집 구현`
  - 예: `[docs] Git 협업 컨벤션 가이드 수록`

- **PR 본문 템플릿**:
```markdown
## 📌 개요
- 작업 목적 및 주요 변경 사항 요약

## 🔍 변경 사항 (Key Changes)
- [x] 변경 사항 1
- [x] 변경 사항 2

## 🧪 테스트 방법 (How to Test)
- `cd app && uv run pytest`
- `./start.sh` 실행 후 API curl 호출 검증

## 🔗 관련 이슈 (Related Issues)
- Closes #12
```

### 병합(Merge) 전략

1. **Squash and Merge (기본 권장)**
   - 단일 feature 브랜치의 수많은 잔여 커밋을 하나로 합쳐 `develop` 또는 `main` 이력을 깔끔하게 유지합니다.
2. **Rebase and Merge**
   - 커밋 이력을 직렬화하여 선형(Linear) 히스토리를 유지하고자 할 때 사용합니다.

---

## 🏷️ 이슈 및 라벨 관리 (Issue & Labeling)

### 라벨 체계 (Labels)

| Label | 색상 코드 | 설명 |
| :--- | :--- | :--- |
| `feat` | `#a2eeef` | 새로운 기능 추가 요청 |
| `bug` | `#d73a4a` | 버그 신고 및 수정 |
| `documentation` | `#0075ca` | 문서화 작업 |
| `harness` | `#fbca04` | 하네스 테스트 & 검증 연관 |
| `agent-a2a` | `#d4c5f9` | A2A 프로토콜 관련 |
| `mcp` | `#1d76db` | Model Context Protocol 관련 |

---

## ✅ 커밋/푸시 전 체크리스트 (Pre-Commit / Pre-Push Checklist)

코드 제출 및 PR 등록 전 아래 항목을 반드시 수행합니다.

1. **테스트 통과 확인**
   ```bash
   cd app && uv run pytest
   ```
2. **환경변수/보밀키 유출 방지**
   - `.env` 파일 및 API Key (`OPENAI_API_KEY`, `GOOGLE_API_KEY` 등)가 git에 포함되지 않았는지 확인합니다.
3. **코드 스타일 및 Lint 검사**
   - Python 코드 포맷팅 및 사용하지 않는 import 정리를 완료했는지 확인합니다.
4. **문서 동기화**
   - API 변경이나 구조 변경 시 관련 `README.md` 및 `docs/` 문서를 동기화했는지 확인합니다.
