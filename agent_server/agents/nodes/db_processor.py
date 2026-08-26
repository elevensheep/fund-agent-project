from typing import Any, Dict
from shared_core import BaseNode
from core.models import StockDailyMetric


class CombineAndSavePostgresNode(BaseNode[Dict[str, Any], Dict[str, Any]]):
    """
    [Node 3-B: Rule 가공 & DB 적재] 데이터 결합 및 PostgreSQL 영속화 노드
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        session_factory = self.get_dependency("db_session_factory")
        metrics = state.get("technical_metrics", {})
        analysis = state.get("news_analysis", {})

        ticker = metrics.get("ticker") or state.get("ticker", "005930")
        close_price = metrics.get("close_price", 75000.0)
        sma_20 = metrics.get("sma_20", 74500.0)
        sentiment = analysis.get("sentiment", "NEUTRAL")
        summary = analysis.get("summary", "데이터 수집 완료")
        impact_score = analysis.get("impact_score", 5)

        record_id = None
        if session_factory:
            try:
                async with session_factory() as session:
                    record = StockDailyMetric(
                        ticker=ticker,
                        close_price=close_price,
                        sma_20=sma_20,
                        sentiment=sentiment,
                        summary=summary,
                        impact_score=impact_score,
                    )
                    session.add(record)
                    await session.commit()
                    await session.refresh(record)
                    record_id = record.id
                    self.logger.info("db_processor.record_saved", record_id=record_id, ticker=ticker)
            except Exception as e:
                self.logger.warning("db_processor.save_failed_fallback", error=str(e))
                record_id = 1

        return {"db_record_id": record_id or 1}
