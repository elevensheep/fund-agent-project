import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncpg
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from shared_core.db_stock_tool import STOCK_MASTER, extract_ticker_from_text
from shared_core.logger import logger
from shared_core.prompt import load_prompt


class PlanStep(BaseModel):
    step_id: int = Field(..., description="실행 단계 번호 (동일 번호는 병렬 실행)")
    agent_name: str = Field(..., description="호출할 서브 에이전트 명 (e.g. data_processing_agent)")
    task_prompt: str = Field(..., description="서브 에이전트에 전달할 세부 지시문")


class ExecutionPlan(BaseModel):
    ticker: str = Field(default="", description="대상 주식 종목 코드 (6자리)")
    stock_name: Optional[str] = Field(default=None, description="대상 주식 종목명")
    query_intent: str = Field(
        default="FULL_ANALYSIS",
        description="사용자 질의 의도: NEWS_ONLY, CHART_ONLY, FULL_ANALYSIS, UNKNOWN_STOCK 등",
    )
    steps: List[PlanStep] = Field(
        default_factory=list,
        description="실행할 단계별 서브 에이전트 목록 (DAG)",
    )


class PlannerAgent:
    """
    사용자 질의 의도 분석 및 Plan-and-Execute 실행 계획(DAG)을 수립하는 플래너 에이전트.
    - 다계층 동적 티커 식별 (1. 사전/정규식 -> 2. PostgreSQL DB -> 3. LLM KRX 상장사 동적 추론 & Auto-onboarding)
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        prompt_path = Path(__file__).parent / "prompts" / "planner.yml"
        self.system_prompt = load_prompt(
            prompt_path,
            key="system_prompt",
            default="You are the Lead Investment Planner Agent. Create a structured ExecutionPlan.",
        )

    async def _onboard_resolved_stock(self, ticker: str, name: str, market: str, sector: str):
        """새롭게 식별된 상장 종목을 PostgreSQL DB 및 Redis에 자동 등록"""
        try:
            conn = await asyncpg.connect(
                host=os.getenv("POSTGRES_HOST", "agent_postgres"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres_secure_pw"),
                database=os.getenv("POSTGRES_DB", "agent_stock_db"),
                timeout=2.0,
            )
            # stock_master_info 테이블 보장 및 적재
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_master_info (
                    ticker VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    market VARCHAR(20) DEFAULT 'KOSPI',
                    sector VARCHAR(100) DEFAULT '주요 상장기업',
                    default_price DOUBLE PRECISION DEFAULT 0.0,
                    aliases TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            await conn.execute(
                """
                INSERT INTO stock_master_info (ticker, name, market, sector, aliases)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (ticker) DO UPDATE
                SET name = $2, market = $3, sector = $4;
                """,
                ticker, name, market, sector, [name, ticker]
            )

            # stock_watchlist 테이블 보장 및 적재
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_watchlist (
                    ticker VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    market VARCHAR(20) DEFAULT 'KOSPI',
                    sector VARCHAR(100) DEFAULT '',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            await conn.execute(
                """
                INSERT INTO stock_watchlist (ticker, name, market, sector, is_active, updated_at)
                VALUES ($1, $2, $3, $4, TRUE, NOW())
                ON CONFLICT (ticker) DO UPDATE
                SET is_active = TRUE, updated_at = NOW();
                """,
                ticker, name, market, sector
            )
            await conn.close()
            logger.info("planner.onboarded_to_db", ticker=ticker, name=name)
        except Exception as e:
            logger.warning("planner.onboard_stock_db_error", ticker=ticker, error=str(e))

        # Redis에도 등록 (stream_worker 즉시 폴링 연동)
        try:
            import redis.asyncio as aioredis
            host = os.getenv("REDIS_HOST", "agent_redis")
            port = int(os.getenv("REDIS_PORT", 6379))
            r = aioredis.from_url(f"redis://{host}:{port}", encoding="utf-8", decode_responses=True)
            raw = await r.get("watchlist:active")
            tickers = json.loads(raw) if raw else []
            if ticker not in tickers:
                tickers.append(ticker)
                await r.set("watchlist:active", json.dumps(tickers), ex=3600 * 24)
            await r.aclose()
        except Exception as e:
            logger.debug("planner.onboard_stock_redis_error", error=str(e))

    async def resolve_ticker(self, query: str) -> Dict[str, Any]:
        """
        다계층(Multi-tier) 동적 티커 식별 파이프라인:
        1. 6자리 숫자 정규식 매칭
        2. In-Memory STOCK_MASTER 사전 매칭
        3. PostgreSQL stock_master_info DB 비동기 검색 (ILIKE / aliases)
        4. LLM 기반 KRX(코스피/코스닥) 상장사 동적 추론 및 DB Auto-Onboarding
        """
        # Tier 1: 정규식 & 인메모리 사전 매칭
        extracted = extract_ticker_from_text(query, default="")
        if extracted:
            meta = STOCK_MASTER.get(extracted, {"name": extracted, "market": "KOSPI" if not extracted.startswith("2") else "KOSDAQ"})
            return {"ticker": extracted, "name": meta.get("name", extracted), "market": meta.get("market", "KOSPI")}

        # Tier 2: PostgreSQL stock_master_info DB 검색
        clean_q = query.strip()
        try:
            conn = await asyncpg.connect(
                host=os.getenv("POSTGRES_HOST", "agent_postgres"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres_secure_pw"),
                database=os.getenv("POSTGRES_DB", "agent_stock_db"),
                timeout=2.0,
            )
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_master_info (
                    ticker VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    market VARCHAR(20) DEFAULT 'KOSPI',
                    sector VARCHAR(100) DEFAULT '주요 상장기업',
                    default_price DOUBLE PRECISION DEFAULT 0.0,
                    aliases TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            row = await conn.fetchrow(
                """
                SELECT ticker, name, market, sector
                FROM stock_master_info
                WHERE $1 ILIKE ('%' || name || '%')
                   OR $1 ILIKE ('%' || ticker || '%')
                   OR ticker ILIKE $2
                   OR name ILIKE $2
                ORDER BY LENGTH(name) DESC
                LIMIT 1
                """,
                clean_q, f"%{clean_q}%"
            )
            await conn.close()
            if row:
                logger.info("planner.ticker_resolved_db", ticker=row["ticker"], name=row["name"])
                return {"ticker": row["ticker"], "name": row["name"], "market": row["market"]}
        except Exception as e:
            logger.debug("planner.db_search_skip", error=str(e))

        # Tier 3: LLM 기반 KRX 상장사 동적 추론 및 DB Auto-Onboarding
        if self.llm:
            try:
                system_msg = SystemMessage(
                    content=(
                        "You are an expert Korean Stock Market (KRX - KOSPI/KOSDAQ) stock resolution engine. "
                        "Given the user's query, identify if there is any publicly listed Korean company mentioned. "
                        "Respond ONLY with a valid JSON object in this exact format (no markdown code fences):\n"
                        '{"found": true, "ticker": "003230", "name": "삼양식품", "market": "KOSPI", "sector": "음식료품"}\n'
                        'If no specific Korean listed company is mentioned or it is not listed in KRX, return:\n'
                        '{"found": false, "ticker": "", "name": "", "market": "", "sector": ""}'
                    )
                )
                human_msg = HumanMessage(content=f"사용자 질의: '{query}'")
                llm_resp = await self.llm.ainvoke([system_msg, human_msg])
                content = llm_resp.content if isinstance(llm_resp.content, str) else str(llm_resp.content)

                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if data.get("found") and data.get("ticker") and len(str(data["ticker"]).strip()) == 6 and str(data["ticker"]).strip().isdigit():
                        ticker = str(data["ticker"]).strip()
                        name = data.get("name") or ticker
                        market = data.get("market") or ("KOSPI" if not ticker.startswith("2") else "KOSDAQ")
                        sector = data.get("sector") or "상장기업"

                        logger.info("planner.ticker_resolved_llm", ticker=ticker, name=name, market=market)
                        await self._onboard_resolved_stock(ticker, name, market, sector)
                        return {"ticker": ticker, "name": name, "market": market}
            except Exception as e:
                logger.warning("planner.llm_ticker_resolve_error", error=str(e))

        return {"ticker": "", "name": "", "market": ""}

    def extract_ticker(self, query: str) -> str:
        """단순 정규식 및 사전 기반 동기 티커 추출 (하위 호환용)"""
        return extract_ticker_from_text(query, default="")

    def classify_intent_rule_based(self, query: str) -> str:
        """룰 기반 질의 의도 1차 분류"""
        q = query.lower()
        if any(w in q for w in ["뉴스만", "뉴스 검색", "기사만", "소식만", "news_only"]):
            return "NEWS_ONLY"
        if any(w in q for w in ["차트만", "이평선만", "기술적만", "보조지표만", "chart_only"]):
            return "CHART_ONLY"
        return "FULL_ANALYSIS"

    def build_default_plan(self, ticker: str, intent: str, stock_name: Optional[str] = None) -> ExecutionPlan:
        """의도에 따른 결정론적 실행 계획(DAG) 생성"""
        if not ticker or intent == "UNKNOWN_STOCK":
            return ExecutionPlan(
                ticker="",
                stock_name=None,
                query_intent="UNKNOWN_STOCK",
                steps=[],
            )

        steps: List[PlanStep] = []
        name_str = f"({stock_name})" if stock_name else ""

        if intent == "NEWS_ONLY":
            steps.append(
                PlanStep(
                    step_id=1,
                    agent_name="web_search_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목의 최신 뉴스 및 웹 정보를 검색해줘",
                )
            )
        elif intent == "CHART_ONLY":
            steps.append(
                PlanStep(
                    step_id=1,
                    agent_name="data_processing_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목의 시세 수집 및 지표 연산을 수행해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="technical_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목의 캔들 차트, 이평선, 보조지표 및 매매신호를 분석해줘",
                )
            )
        else:  # FULL_ANALYSIS
            # Step 1: 수집 레이어 병렬 실행
            steps.append(
                PlanStep(
                    step_id=1,
                    agent_name="data_processing_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목 시세 수집, 뉴스 정제, 지표 가공 및 DB 적재를 수행해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=1,
                    agent_name="web_search_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목의 최신 금융 뉴스 및 IR 공시를 웹에서 검색해줘",
                )
            )
            # Step 2: 심층 분석 레이어 병렬 실행
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="fundamental_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목의 재무제표 3표 및 밸류에이션(PER/PBR/ROE)을 분석해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="technical_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목의 기술적 지표, 지지/저항선 및 매매 시그널을 분석해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="dart_disclosure_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목의 DART 전자공시 및 오버행/희석률을 분석해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="macro_sector_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목의 거시경제 지표 및 섹터 로테이션 상대강도를 분석해줘",
                )
            )
            # Step 3: 토론 및 최종 판단
            steps.append(
                PlanStep(
                    step_id=3,
                    agent_name="bull_bear_debate_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목에 대한 Bull vs Bear 대립 토론 및 판사 최종 투자 판단을 내려줘",
                )
            )
            # Step 4: 리스크 심의 (100% Rule-Based)
            steps.append(
                PlanStep(
                    step_id=4,
                    agent_name="risk_management_agent",
                    task_prompt=f"[{ticker}{name_str}] 종목에 대해 포트폴리오 비중 한도(15%), 패닉장 필터, 동적 손절선을 심의해줘",
                )
            )

        return ExecutionPlan(
            ticker=ticker,
            stock_name=stock_name,
            query_intent=intent,
            steps=steps,
        )

    async def create_plan(self, user_query: str) -> ExecutionPlan:
        """사용자 질의로부터 ExecutionPlan 수립 (다계층 동적 티커 식별 적용)"""
        resolved = await self.resolve_ticker(user_query)
        ticker = resolved.get("ticker", "")
        stock_name = resolved.get("name") or None
        intent = self.classify_intent_rule_based(user_query)

        logger.info("planner.create_plan.start", query=user_query, ticker=ticker, stock_name=stock_name, intent=intent)

        if not ticker:
            logger.info("planner.stock_not_identified", query=user_query)
            return self.build_default_plan("", "UNKNOWN_STOCK", None)

        try:
            if hasattr(self.llm, "with_structured_output"):
                structured_llm = self.llm.with_structured_output(ExecutionPlan)
                prompt = (
                    f"사용자 요청: '{user_query}'\n"
                    f"대상 종목 코드: {ticker} ({stock_name or ticker}), 감지된 의도: {intent}\n"
                    f"적절한 PlanStep 목록을 구성하여 반환하세요."
                )
                res = await structured_llm.ainvoke([
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=prompt),
                ])
                if isinstance(res, ExecutionPlan) and res.steps:
                    res.ticker = ticker
                    res.stock_name = stock_name
                    logger.info("planner.structured_plan_generated", step_count=len(res.steps))
                    return res
        except Exception as e:
            logger.warning("planner.llm_plan_fallback", error=str(e))

        plan = self.build_default_plan(ticker, intent, stock_name=stock_name)
        logger.info("planner.default_plan_built", ticker=ticker, intent=intent, steps=len(plan.steps))
        return plan
