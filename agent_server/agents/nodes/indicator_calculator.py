from typing import Any, Dict
from shared_core import BaseNode
from shared_core.db_stock_tool import calculate_stock_indicators


class CalculateIndicatorsNode(BaseNode[Dict[str, Any], Dict[str, Any]]):
    """
    [Node 3-A: Rule 가공] 기술적 수치 지표 계산 노드 (SMA, 볼린저밴드 등 환각 방지)
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        price_data = state.get("raw_price_data", {})
        
        # 실제 시세 데이터 기반 실계산
        close_price = price_data.get("close")
        if not close_price:
            ind = calculate_stock_indicators(ticker)
            close_price = ind["current_price"]
            sma_20 = ind["sma_20"]
        else:
            prices = price_data.get("prices_20d", [close_price])
            sma_20 = sum(prices) / len(prices)

        # 변동성 및 지표 계산
        metrics = {
            "ticker": ticker,
            "close_price": close_price,
            "sma_20": round(sma_20, 2),
            "is_bullish": close_price >= sma_20,
            "price_deviation_pct": round(((close_price - sma_20) / sma_20) * 100, 2) if sma_20 else 0.0,
        }
        return {"technical_metrics": metrics}
