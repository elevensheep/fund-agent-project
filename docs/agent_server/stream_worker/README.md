# ⚡ Real-Time Stream Worker (`stream_worker`)

본 문서는 한국투자증권(KIS) WebSocket을 통해 실시간 주식 틱(Tick) 및 체결 데이터를 수집하고, 1분봉 롤링 버퍼링을 거쳐 PostgreSQL에 비동기 벌크 적재하는 **Real-Time Stream Worker**의 아키텍처 및 구현 가이드입니다.

---

## 1. 개요

`stream_worker`는 초당 수십~수백 건씩 발생하는 실시간 시세 스트림을 **LLM 호출 없이 순수 비동기(asyncio / websockets) 기반으로 초고속 수집·적재하는 백그라운드 인제스천 데몬(Daemon)**입니다.

- **Ingestion과 Intelligence의 완전한 분리**:
  - 실시간 스트림 수집 시점에는 LLM을 일절 호출하지 않고 순수 파이썬 워커가 전담하여 **토큰 비용을 0원으로 유지**합니다.
  - LLM 에이전트(`data_processing_agent`, `technical_agent` 등)는 DB/Redis에 이미 적재된 데이터를 **사용자 질의 시(On-Demand) 또는 급등락 이상치 감지 시(Event-Triggered)**에만 1회 조회하여 분석합니다.
- **2-Tier 동적 주시 시스템 (Targeted Watchlist)**:
  - 증권사 WebSocket 세션당 구독 한도(20~40개)를 준수하기 위해, 전종목 전수가 아닌 **핵심 주시 종목(10~40개)**을 동적으로 선별하여 타겟팅 구독합니다.
- **코드 재사용성**:
  - `agent_server/core/`의 PostgreSQL 커넥션 풀(`database.py`)과 ORM 모델(`models.py`)을 100% 재사용합니다.

---

## 2. 시스템 아키텍처 및 데이터 흐름

```mermaid
graph TD
    subgraph Tier 1. 전종목 스크리닝 (REST / pykrx)
        Screening["🔍 Rule/Agent 스크리너<br/>- 당일 거래대금 상위 Top 30<br/>- 포트폴리오 보유 및 관심 종목"]
    end

    Screening -->|동적 주시 리스트 선정 (10~30개)| Watchlist["📋 Dynamic Watchlist<br/>['005930', '000660', '035420', ...]"]

    subgraph Tier 2. 실시간 WebSocket 수집 & 적재 (Stream Worker)
        Watchlist -->|WebSocket Subscribe| KIS_WS["📡 한국투자증권 WebSocket<br/>(H0STCNT0 실시간 체결가)"]
        KIS_WS --> Worker["⚡ stream_worker.py (No LLM)<br/>1. 틱 데이터 파싱<br/>2. In-Memory 1분봉 롤링 버퍼링"]
        
        Worker -->|최신가 초고속 갱신| Redis["🚀 Redis Cache (선택)<br/>key: ticker:005930:latest"]
        Worker -->|100건/1초 주기 비동기 벌크 적재| Postgres["🐘 PostgreSQL<br/>table: stock_minute_prices"]
    end

    subgraph Tier 3. 지능형 에이전트 레이어 (On-Demand / Event-Triggered)
        UserReq["👤 사용자 요청 / 분석 트리거"] --> Supervisor["🤖 Supervisor Agent (28000)"]
        Supervisor --> SubAgents["🗣️ A2A Sub-Agents (28001~28009)<br/>- technical_agent, bull_bear_debate_agent"]
        
        SubAgents -.->|PostgreSQL에서 1분봉/일봉 조회| Postgres
        SubAgents -.->|Redis에서 최신 호가 조회| Redis
        Worker -.->|급등락(3% 이상) 이상치 발생 시 1회 알림| Supervisor
    end
```

---

## 3. 디렉토리 구조

```text
agent_server/
├── agents/                           # A2A 웹 서비스 서브 에이전트들 (HTTP / JSON-RPC)
│   ├── data_processing_agent.py      # Port: 28001
│   ├── technical_agent.py            # Port: 28005
│   └── ...
├── workers/                          # ⚡ [신규] 백그라운드 실시간 수집 워커
│   ├── __init__.py
│   ├── stream_worker.py              # WebSocket 리스너 & 1분봉 롤링 집계기
│   ├── kis_client.py                 # 한국투자증권 WebSocket/REST 통신 래퍼
│   └── watchlist_manager.py          # 동적 주시 종목(Watchlist) 관리자
├── core/                             # 공통 모듈 (재사용)
│   ├── config.py                     # KIS_APP_KEY, KIS_APP_SECRET, POSTGRES_HOST
│   ├── database.py                   # async_session_factory
│   └── models.py                     # StockMinutePrice, StockDailyMetric
├── Dockerfile
└── docker-compose.yml
```

---

## 4. 핵심 구현 로직 예시

### 4.1. `workers/stream_worker.py` (비동기 틱 수집 및 벌크 적재)

```python
import asyncio
import json
import websockets
from typing import List, Dict, Any
from core.database import async_session_factory
from core.models import StockMinutePrice

class RealtimeStreamWorker:
    def __init__(self, tickers: List[str]):
        self.tickers = tickers
        self.buffer: List[Dict[str, Any]] = []
        self.flush_interval = 1.0  # 1초 주기 벌크 적재

    async def connect_and_stream(self):
        """한국투자증권 WebSocket 연결 및 실시간 틱 수신 (No LLM)"""
        uri = "ws://ops.koreainvestment.com:21000/tryitout/H0STCNT0"
        
        async with websockets.connect(uri) as ws:
            # 1. 선정된 주시 종목들 구독 등록
            for ticker in self.tickers:
                reg_payload = {
                    "header": {"tr_type": "1"},  # 1: 등록, 2: 해제
                    "body": {"input": {"tr_id": "H0STCNT0", "tr_key": ticker}}
                }
                await ws.send(json.dumps(reg_payload))

            # 2. 주기적 DB 플러시 백그라운드 태스크 시작
            flush_task = asyncio.create_task(self._periodic_flush())

            # 3. 실시간 틱 수신 루프
            try:
                while True:
                    raw_msg = await ws.recv()
                    tick_data = self._parse_kis_tick(raw_msg)
                    if tick_data:
                        self.buffer.append(tick_data)
            finally:
                flush_task.cancel()

    def _parse_kis_tick(self, raw_msg: str) -> Dict[str, Any]:
        """KIS 체결가 틱 메시지 파싱"""
        # 구분자(| 또는 ^) 기반 초고속 파싱
        parts = raw_msg.split("^")
        if len(parts) > 10:
            return {
                "ticker": parts[0],
                "price": float(parts[2]),
                "volume": int(parts[12]),
                "change_rate": float(parts[5]),
            }
        return None

    async def _periodic_flush(self):
        """버퍼에 쌓인 틱 데이터를 주기적으로 PostgreSQL에 벌크 인서트"""
        while True:
            await asyncio.sleep(self.flush_interval)
            if self.buffer:
                records = self.buffer.copy()
                self.buffer.clear()
                
                async with async_session_factory() as session:
                    session.add_all([StockMinutePrice(**rec) for rec in records])
                    await session.commit()

if __name__ == "__main__":
    # 주시 종목 Top 20 대상 실시간 수집 실행
    watchlist = ["005930", "000660", "035420", "005380"]
    worker = RealtimeStreamWorker(tickers=watchlist)
    asyncio.run(worker.connect_and_stream())
```

---

## 5. PostgreSQL 테이블 스키마 (`StockMinutePrice`)

```sql
CREATE TABLE IF NOT EXISTS stock_minute_prices (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    open_price NUMERIC(12, 2) NOT NULL,
    high_price NUMERIC(12, 2) NOT NULL,
    low_price NUMERIC(12, 2) NOT NULL,
    close_price NUMERIC(12, 2) NOT NULL,
    volume BIGINT NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 시계열 초고속 조회를 위한 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_stock_minute_ticker_time 
ON stock_minute_prices (ticker, recorded_at DESC);
```

---

## 6. Docker 서비스 구성 (`docker-compose.yml`)

`agent_server`의 단일 Dockerfile 이미지를 공유하며, `command`를 분리하여 **독립 컨테이너 서비스로 격리 실행**합니다.

```yaml
services:
  # 1. A2A 서브 에이전트 서비스 (HTTP / JSON-RPC 서버)
  agent_data_processing_server:
    build: ./agent_server
    command: uvicorn agents.data_processing_agent:app --host 0.0.0.0 --port 28001
    ports:
      - "28001:28001"
    environment:
      - POSTGRES_HOST=postgres

  # 2. [신규] 실시간 WebSocket 백그라운드 수집기 (No HTTP Port)
  agent_stream_worker:
    build: ./agent_server
    command: python -m workers.stream_worker
    restart: always # WebSocket 연결 유실 시 자동 재접속
    environment:
      - POSTGRES_HOST=postgres
      - KIS_APP_KEY=${KIS_APP_KEY}
      - KIS_APP_SECRET=${KIS_APP_SECRET}
```

---

## 7. 실행 및 테스트

### 7.1. 독립 실행
```bash
python -m agent_server.workers.stream_worker
```

### 7.2. 도커 컴포넌트 실행
```bash
docker-compose up -d agent_stream_worker
docker-compose logs -f agent_stream_worker
```
