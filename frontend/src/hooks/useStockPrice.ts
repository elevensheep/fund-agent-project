import { useEffect, useState, useCallback, useRef } from "react";
import { StockQuote } from "@/types/agent";

export function useStockPrice(ticker: string) {
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const isMounted = useRef(true);

  const fetchLiveQuote = useCallback(async (targetTicker: string) => {
    if (!targetTicker) return;
    try {
      const res = await fetch(`/api/stock/quote?ticker=${targetTicker}`, {
        cache: "no-store",
      });
      if (res.ok && isMounted.current) {
        const data = await res.json();
        if (data && data.price) {
          setQuote({
            ticker: data.ticker || targetTicker,
            name: data.name || targetTicker,
            market: data.market || "KOSPI",
            price: Number(data.price),
            change: Number(data.change) || 0,
            changePercent: Number(data.changePercent) || 0,
            volume: Number(data.volume) || 0,
            high: Number(data.high) || Number(data.price),
            low: Number(data.low) || Number(data.price),
            open: Number(data.open) || Number(data.price),
            prevClose: Number(data.prevClose) || Number(data.price),
            updatedAt: data.updatedAt || new Date().toLocaleTimeString("ko-KR", { hour12: false }),
          });
        }
      }
    } catch (err) {
      // Keep existing quote on temporary fetch failure
    }
  }, []);

  useEffect(() => {
    isMounted.current = true;
    if (ticker) {
      fetchLiveQuote(ticker);
      const interval = setInterval(() => {
        if (isMounted.current) {
          fetchLiveQuote(ticker);
        }
      }, 3000);
      return () => {
        isMounted.current = false;
        clearInterval(interval);
      };
    }
    return () => {
      isMounted.current = false;
    };
  }, [ticker, fetchLiveQuote]);

  return { quote, refetch: () => fetchLiveQuote(ticker) };
}
