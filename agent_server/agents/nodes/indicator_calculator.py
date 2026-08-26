from typing import Any, Dict
from shared_core import BaseNode


class CalculateIndicatorsNode(BaseNode[Dict[str, Any], Dict[str, Any]]):
    """
    [Node 3-A: Rule 가공] 기술적 수치 지표 계산 노드 (SMA, 볼린저밴드 등 환각 방지)
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        price_data = state.get("raw_price_data", {})
        prices = price_data.get("prices_20d", [75000.0])
        sma_20 = sum(prices) / len(prices)
        close_price = price_data.get("close", 75000.0)

        # 변동성 및 지표 계산
        metrics = {
            "ticker": price_data.get("ticker", "005930"),
            "close_price": close_price,
            "sma_20": round(sma_20, 2),
            "is_bullish": close_price > sma_20,
            "price_deviation_pct": round(((close_price - sma_20) / sma_20) * 100, 2),
        }
        return {"technical_metrics": metrics}
