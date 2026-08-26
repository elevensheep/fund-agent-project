from typing import Any, Dict
from shared_core import BaseNode


class CollectPriceDataNode(BaseNode[Dict[str, Any], Dict[str, Any]]):
    """
    [Node 1: Rule 수집] 주식 시세 API 수집 노드 (OHLCV)
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        
        # 기본 시세 데이터 셋업 (실제 환경에서는 증권사 API/DB 조회)
        raw_price = {
            "ticker": ticker,
            "close": 75000.0,
            "open": 74200.0,
            "high": 75500.0,
            "low": 73800.0,
            "volume": 14250000,
            "prices_20d": [
                73000.0, 73500.0, 74000.0, 73800.0, 74200.0,
                74500.0, 74000.0, 74800.0, 75000.0, 75200.0,
                74900.0, 74600.0, 75100.0, 75300.0, 74700.0,
                74500.0, 74800.0, 75000.0, 75200.0, 75000.0,
            ],
        }
        return {"raw_price_data": raw_price}
