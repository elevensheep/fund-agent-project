from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class StockDailyMetric(Base):
    """주식 일간 지표 및 정제된 뉴스 분석 데이터 ORM 모델"""
    __tablename__ = "stock_daily_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    close_price = Column(Float, nullable=False)
    sma_20 = Column(Float, nullable=True)
    sentiment = Column(String(20), nullable=True)
    summary = Column(Text, nullable=True)
    impact_score = Column(Integer, nullable=True, default=5)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_stock_ticker_date", "ticker", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "close_price": self.close_price,
            "sma_20": self.sma_20,
            "sentiment": self.sentiment,
            "summary": self.summary,
            "impact_score": self.impact_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StockMinutePrice(Base):
    """실시간 체결 및 1분봉 시세 데이터 ORM 모델"""
    __tablename__ = "stock_minute_prices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    open_price = Column(Float, nullable=False, default=0.0)
    high_price = Column(Float, nullable=False, default=0.0)
    low_price = Column(Float, nullable=False, default=0.0)
    close_price = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False, default=0)
    change_rate = Column(Float, nullable=False, default=0.0)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_stock_minute_ticker_time", "ticker", "recorded_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "open_price": self.open_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "close_price": self.close_price,
            "volume": self.volume,
            "change_rate": self.change_rate,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
