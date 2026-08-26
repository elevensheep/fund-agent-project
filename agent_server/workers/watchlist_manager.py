from typing import List
from shared_core.logger import logger


class WatchlistManager:
    """
    WebSocket 구독 한도(20~40개)를 준수하기 위해
    거래대금 상위 및 핵심 관심 종목을 동적으로 관리하는 관리자.
    """

    DEFAULT_WATCHLIST = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
        "005380",  # 현대차
        "005490",  # POSCO홀딩스
        "035720",  # 카카오
        "051910",  # LG화학
        "006400",  # 삼성SDI
        "068270",  # 셀트리온
        "105560",  # KB금융
    ]

    def __init__(self, initial_tickers: List[str] | None = None):
        self._watchlist: List[str] = initial_tickers or list(self.DEFAULT_WATCHLIST)

    def get_watchlist(self) -> List[str]:
        return list(self._watchlist)

    def add_ticker(self, ticker: str) -> None:
        if ticker not in self._watchlist and len(self._watchlist) < 40:
            self._watchlist.append(ticker)
            logger.info("watchlist.added", ticker=ticker, total_count=len(self._watchlist))

    def remove_ticker(self, ticker: str) -> None:
        if ticker in self._watchlist:
            self._watchlist.remove(ticker)
            logger.info("watchlist.removed", ticker=ticker, total_count=len(self._watchlist))
