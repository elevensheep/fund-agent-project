import { useEffect, useState, useCallback, useRef } from "react";
import { CandleData, SmaLineData } from "@/types/agent";

interface UseStockCandlesResult {
  candles: CandleData[];
  sma20: SmaLineData[];
  sma60: SmaLineData[];
  timeframe: "1D" | "1M" | "1W";
  setTimeframe: (tf: "1D" | "1M" | "1W") => void;
  isLoading: boolean;
  isEmpty: boolean;
  source: string;
  refetch: () => Promise<void>;
}

export function useStockCandles(ticker: string, initialTimeframe: "1D" | "1M" | "1W" = "1D"): UseStockCandlesResult {
  const [candles, setCandles] = useState<CandleData[]>([]);
  const [sma20, setSma20] = useState<SmaLineData[]>([]);
  const [sma60, setSma60] = useState<SmaLineData[]>([]);
  const [timeframe, setTimeframe] = useState<"1D" | "1M" | "1W">(initialTimeframe);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isEmpty, setIsEmpty] = useState<boolean>(false);
  const [source, setSource] = useState<string>("empty");

  const isMounted = useRef(true);

  const fetchCandles = useCallback(async (targetTicker: string, targetTf: string) => {
    if (!targetTicker) return;
    setIsLoading(true);

    try {
      const res = await fetch(`/api/stock/candles?ticker=${targetTicker}&timeframe=${targetTf}&count=60`, {
        cache: "no-store",
      });

      if (res.ok && isMounted.current) {
        const data = await res.json();
        if (data) {
          const rawCandles: CandleData[] = data.candles || [];
          setCandles(rawCandles);
          setSma20(data.sma20 || []);
          setSma60(data.sma60 || []);
          setIsEmpty(Boolean(data.is_empty) || rawCandles.length === 0);
          setSource(data.source || "empty");
        }
      }
    } catch (err) {
      console.warn("Failed to fetch stock candles:", err);
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    isMounted.current = true;
    if (ticker) {
      fetchCandles(ticker, timeframe);
    }
    return () => {
      isMounted.current = false;
    };
  }, [ticker, timeframe, fetchCandles]);

  return {
    candles,
    sma20,
    sma60,
    timeframe,
    setTimeframe,
    isLoading,
    isEmpty,
    source,
    refetch: () => fetchCandles(ticker, timeframe),
  };
}
