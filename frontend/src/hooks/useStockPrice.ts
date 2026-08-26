import { useEffect, useState } from "react";
import { StockQuote } from "@/types/agent";
import { POPULAR_STOCKS } from "@/lib/mockData";

export function useStockPrice(ticker: string) {
  const [quote, setQuote] = useState<StockQuote>(() => {
    return (
      POPULAR_STOCKS.find((s) => s.ticker === ticker) || {
        ticker,
        name: ticker,
        market: "KOSPI",
        price: 75000,
        change: 500,
        changePercent: 0.67,
        volume: 1200000,
        high: 76000,
        low: 74200,
        open: 74500,
        prevClose: 74500,
        updatedAt: "15:30:00",
      }
    );
  });

  useEffect(() => {
    const found = POPULAR_STOCKS.find((s) => s.ticker === ticker);
    if (found) {
      setQuote(found);
    }

    // Tick simulation for realism
    const interval = setInterval(() => {
      setQuote((prev) => {
        const delta = (Math.random() - 0.49) * (prev.price * 0.002);
        const newPrice = Math.round(prev.price + delta);
        const change = newPrice - prev.prevClose;
        const changePercent = (change / prev.prevClose) * 100;
        return {
          ...prev,
          price: newPrice,
          change,
          changePercent,
          volume: prev.volume + Math.round(Math.random() * 500),
          high: Math.max(prev.high, newPrice),
          low: Math.min(prev.low, newPrice),
          updatedAt: new Date().toLocaleTimeString("ko-KR", { hour12: false }),
        };
      });
    }, 4000);

    return () => clearInterval(interval);
  }, [ticker]);

  return quote;
}
