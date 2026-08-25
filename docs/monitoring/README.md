# 📊 Monitoring Stack (`monitoring`) 문서

본 문서는 **Agent Ecosystem의 관찰 가능성(Observability) 및 메트릭/로그 모니터링 스택인 `monitoring`**에 대한 가이드입니다.

---

## 1. 개요

`monitoring` 모듈은 Docker 기반 인프라스트럭처 내에서 실행 중인 서비스들의 **성능 메트릭(Metrics)** 및 **컨테이너 로그(Logs)**를 실시간으로 수집하고 대시보드 시각화를 제공합니다.

---

## 2. 디렉토리 및 구성 요소

```text
monitoring/
├── docker-compose.yml      # Prometheus, Loki, Promtail, Grafana, cAdvisor 인프라 스펙
├── prometheus.yml          # Prometheus 타겟 수집 주파수 및 엔드포인트 설정
├── promtail-config.yaml    # Promtail 로그 수집기 및 Loki 데이터 전송 설정
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── datasource.yml # Prometheus & Loki 데이터소스 자동 등록 프로비저닝
└── README.md               # 메인 참조 링커
```

---

## 3. 모니터링 컴포넌트 구성

### 3.1. Prometheus (`Port: 29090`)
- **역할**: 마이크로서비스들의 `/metrics` HTTP 엔드포인트를 주기적(15초 단위)으로 스크랩하여 시계열 데이터 저장.
- **수집 대상 서비스**:
  - `agent_orchestrator_app:28000/metrics`
  - `agent_echo_server:28001/metrics`
  - `agent_langchain_server:28003/metrics`

### 3.2. Promtail & Loki (`Port: 23100`)
- **Promtail**: `/var/lib/docker/containers/*/*.log` 경로의 도커 컨테이너 로그를 실시간 수집 및 라벨링하여 Loki로 Push.
- **Loki**: 수집된 UTF-8 구조화 로그 저장 및 LogQL 검색 엔진 제공.

### 3.3. Grafana (`Port: 23000`)
- **역할**: 수집된 메트릭 및 로그 데이터를 단일 웹 UI에서 시각화.
- **기본 접속 정보**:
  - **URL**: `http://localhost:23000`
  - **ID / PW**: `admin` / `admin`
- **프로비저닝 데이터소스**:
  - `Prometheus` (`http://agent_prometheus:9090`)
  - `Loki` (`http://agent_loki:3100`)

---

## 4. 모니터링 스택 독립 실행방법

```bash
cd monitoring
docker compose up -d
```
