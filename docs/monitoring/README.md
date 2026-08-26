# 📊 Monitoring Stack (`monitoring`) 문서

본 문서는 **Agent Ecosystem의 관찰 가능성(Observability) 및 메트릭/로그 모니터링 스택인 `monitoring`**에 대한 가이드입니다.

---

## 1. 개요

`monitoring` 모듈은 Docker 기반 인프라스트럭처 내에서 실행 중인 서비스들의 **성능 메트릭(Metrics)** 및 **컨테이너 로그(Logs)**를 실시간으로 수집하고, 사전 구성된 Grafana 대시보드를 통해 원클릭 시각화를 제공합니다.

---

## 2. 디렉토리 및 구성 요소

```text
monitoring/
├── docker-compose.yml      # Prometheus, Loki, Promtail, Grafana, cAdvisor 인프라 스펙
├── prometheus.yml          # 8대 서브 에이전트 & Orchestrator 메트릭 스크랩 설정
├── promtail-config.yaml    # Promtail 로그 수집기 및 Loki 데이터 전송 설정
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasource.yml # Prometheus & Loki 데이터소스 자동 등록 프로비저닝
│   │   └── dashboards/
│   │       └── dashboard.yml  # 대시보드 자동 프로비저닝 설정
│   └── dashboards/
│       └── agent_ecosystem_dashboard.json # ⚡ 금융 멀티에이전트 통합 대시보드
└── README.md               # 메인 참조 링커
```

---

## 3. 모니터링 컴포넌트 구성

### 3.1. Prometheus (`Port: 29090`)
- **역할**: 마이크로서비스들의 `/metrics` HTTP 엔드포인트를 주기적(30초 단위)으로 스크랩하여 시계열 데이터 저장.
- **수집 대상 서비스 (9개 서비스)**:
  - `agent_orchestrator_app:28000/metrics`
  - `agent_data_processing_server:28001/metrics`
  - `agent_web_search_server:28003/metrics`
  - `agent_fundamental_server:28004/metrics`
  - `agent_technical_server:28005/metrics`
  - `agent_dart_disclosure_server:28006/metrics`
  - `agent_macro_sector_server:28007/metrics`
  - `agent_bull_bear_debate_server:28008/metrics`
  - `agent_risk_management_server:28009/metrics`

### 3.2. Promtail & Loki (`Port: 23100`)
- **Promtail**: Docker 컨테이너 로그를 실시간 수집 및 라벨링(`container_name`)하여 Loki로 Push.
- **Loki**: `shared_core.logger`가 생성한 `task.*` 및 `artifact.*` UTF-8 구조화 로그 저장 및 LogQL 검색 엔진 제공.

### 3.3. Grafana (`Port: 23000`)
- **역할**: 수집된 메트릭 및 로그 데이터를 단일 통합 웹 UI에서 시각화.
- **기본 접속 정보**:
  - **URL**: `http://localhost:23000`
  - **ID / PW**: `admin` / `admin`
- **사전 프로비저닝된 대시보드 (`Financial Multi-Agent Ecosystem Dashboard`)**:
  1. **시스템 실시간 KPI**: 가동 에이전트 수(Active Agents), 총 처리량(QPS), 평균 지연시간(Avg Latency), 5xx 에러율
  2. **에이전트별 처리량 & P95 지연시간**: 서비스별 시계열 요청률 및 95 백분위 응답 속도
  3. **HTTP 트래픽 & API 엔드포인트 분포**: 2xx/4xx/5xx 비율 및 호출 상위 API 랭킹
  4. **컨테이너 리소스 모니터링**: 컨테이너별 CPU(%) 및 메모리(MB) 실시간 점유율
  5. **Loki 실시간 구조화 로그 스트림**: `task.*` 및 `artifact.*` 실시간 로그 탐색기

---

## 4. 모니터링 스택 독립 실행방법

```bash
cd monitoring
docker compose up -d
```
