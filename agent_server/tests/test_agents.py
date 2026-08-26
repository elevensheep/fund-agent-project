import pytest
from agents.data_processing_agent import create_data_processing_graph
from agents.fundamental_agent import create_fundamental_graph
from agents.technical_agent import create_technical_graph
from agents.dart_disclosure_agent import create_dart_graph
from agents.macro_sector_agent import create_macro_graph
from agents.bull_bear_debate_agent import create_debate_graph
from agents.risk_management_agent import create_risk_graph
from workers.watchlist_manager import WatchlistManager
from workers.stream_worker import RealtimeStreamWorker


@pytest.mark.asyncio
async def test_data_processing_graph():
    graph = create_data_processing_graph()
    res = await graph.ainvoke({"ticker": "005930", "raw_news_text": "삼성전자 반도체 실적 호조"})
    assert "005930" in res["output"]
    assert "technical_metrics" in res
    assert "news_analysis" in res


@pytest.mark.asyncio
async def test_fundamental_graph():
    graph = create_fundamental_graph()
    res = await graph.ainvoke({"ticker": "005930"})
    assert "005930" in res["output"]
    assert "valuation_metrics" in res
    assert res["valuation_metrics"]["grade"] in ["S", "A", "B", "C", "D"]


@pytest.mark.asyncio
async def test_technical_graph():
    graph = create_technical_graph()
    res = await graph.ainvoke({"ticker": "005930"})
    assert "005930" in res["output"]
    assert "signal_result" in res
    assert res["signal_result"]["signal"] in ["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]


@pytest.mark.asyncio
async def test_dart_disclosure_graph():
    graph = create_dart_graph()
    res = await graph.ainvoke({"ticker": "005930"})
    assert "005930" in res["output"]
    assert "disclosure_analysis" in res


@pytest.mark.asyncio
async def test_macro_sector_graph():
    graph = create_macro_graph()
    res = await graph.ainvoke({"ticker": "005930"})
    assert "005930" in res["output"]
    assert "sector_data" in res
    assert 0 <= res["sector_data"]["macro_score"] <= 100


@pytest.mark.asyncio
async def test_bull_bear_debate_graph():
    graph = create_debate_graph()
    res = await graph.ainvoke({"ticker": "005930"})
    assert "005930" in res["output"]
    assert "judge_verdict" in res
    assert res["judge_verdict"]["decision"] in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]


@pytest.mark.asyncio
async def test_risk_management_graph_approval():
    graph = create_risk_graph()
    res = await graph.ainvoke({
        "ticker": "005930",
        "proposed_weight": 0.10,
        "market_status": {"kospi_change_rate": +1.0, "current_price": 75000.0, "atr_14": 1500.0},
    })
    assert res["verdict"] == "APPROVED"
    assert res["approved_weight"] == 0.10
    assert res["stop_loss_price"] == 72750.0  # 75000 - 1500*1.5


@pytest.mark.asyncio
async def test_risk_management_graph_panic_rejection():
    graph = create_risk_graph()
    res = await graph.ainvoke({
        "ticker": "005930",
        "proposed_weight": 0.10,
        "market_status": {"kospi_change_rate": -3.5, "current_price": 75000.0, "atr_14": 1500.0},
    })
    assert res["verdict"] == "REJECTED"
    assert res["approved_weight"] == 0.0


def test_watchlist_manager():
    mgr = WatchlistManager(["005930", "000660"])
    assert len(mgr.get_watchlist()) == 2
    mgr.add_ticker("035420")
    assert len(mgr.get_watchlist()) == 3
    mgr.remove_ticker("000660")
    assert len(mgr.get_watchlist()) == 2
    assert "000660" not in mgr.get_watchlist()


def test_stream_worker_tick_parsing():
    worker = RealtimeStreamWorker(tickers=["005930"])
    raw_kis = "005930^1^75000^75500^74500^0.8^0^0^0^0^0^0^500"
    parsed = worker.parse_kis_tick(raw_kis)
    assert parsed is not None
    assert parsed["ticker"] == "005930"
    assert parsed["close_price"] == 75000.0
    assert parsed["volume"] == 500
