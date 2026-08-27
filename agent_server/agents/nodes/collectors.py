from typing import Any, Dict
from shared_core import BaseNode
from shared_core.db_stock_tool import fetch_latest_stock_price, calculate_stock_indicators


class CollectPriceDataNode(BaseNode[Dict[str, Any], Dict[str, Any]]):
    """
    [Node 1: Rule 수집] 주식 시세 API 및 실시간 DB 수집 노드 (OHLCV)
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        indicators = calculate_stock_indicators(ticker)
        price = indicators["current_price"]
        
        raw_price = {
            "ticker": ticker,
            "close": price,
            "open": indicators["open_price"],
            "high": indicators["high_price"],
            "low": indicators["low_price"],
            "volume": indicators["volume"],
            "prices_20d": [
                round(price * (0.95 + (i * 0.05 / 20)), -2) for i in range(20)
            ],
        }
        return {"raw_price_data": raw_price}
