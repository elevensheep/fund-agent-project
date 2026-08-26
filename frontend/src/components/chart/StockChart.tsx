"use client";

import React, { useEffect, useRef, useState } from "react";
import { createChart, IChartApi, ISeriesApi, ColorType, CandlestickData } from "lightweight-charts";
import { CandleData, SmaLineData } from "@/types/agent";
import { formatKRW, formatPercent } from "@/lib/formatters";
import { BarChart3, Clock, Eye, Layers } from "lucide-react";

interface StockChartProps {
  data: CandleData[];
  sma20?: SmaLineData[];
  sma60?: SmaLineData[];
  ticker: string;
  stockName: string;
}

export const StockChart: React.FC<StockChartProps> = ({
  data,
  sma20,
  sma60,
  ticker,
  stockName,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const sma20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const sma60SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  const [hoverData, setHoverData] = useState<{
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
  } | null>(null);

  const [timeframe, setTimeframe] = useState<"1D" | "1M" | "1W">("1D");
  const [showSma20, setShowSma20] = useState(true);
  const [showSma60, setShowSma60] = useState(true);

  // Latest bar summary
  const latestBar = data.length > 0 ? data[data.length - 1] : null;
  const currentHover = hoverData || latestBar;

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Clean up previous instance
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#090d16" }, // Dark Slate/Navy
        textColor: "#94a3b8",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(30, 41, 59, 0.4)" },
        horzLines: { color: "rgba(30, 41, 59, 0.4)" },
      },
      crosshair: {
        vertLine: {
          color: "#64748b",
          width: 1,
          style: 3,
          labelBackgroundColor: "#1e293b",
        },
        horzLine: {
          color: "#64748b",
          width: 1,
          style: 3,
          labelBackgroundColor: "#1e293b",
        },
      },
      timeScale: {
        borderColor: "#1e293b",
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: "#1e293b",
        scaleMargins: {
          top: 0.1,
          bottom: 0.15,
        },
      },
      width: chartContainerRef.current.clientWidth,
      height: 380,
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#ef4444", // 한국 증시: 상승 빨간색
      downColor: "#3b82f6", // 한국 증시: 하락 파란색
      borderVisible: false,
      wickUpColor: "#ef4444",
      wickDownColor: "#3b82f6",
    });

    // Cast data
    const formattedCandles: CandlestickData[] = data.map((d) => ({
      time: d.time as any,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));
    candleSeries.setData(formattedCandles);
    candleSeriesRef.current = candleSeries;

    // SMA 20
    if (sma20 && sma20.length > 0 && showSma20) {
      const sma20Series = chart.addLineSeries({
        color: "#eab308", // Yellow
        lineWidth: 2,
        title: "SMA 20",
        priceLineVisible: false,
      });
      sma20Series.setData(sma20.map((s) => ({ time: s.time as any, value: s.value })));
      sma20SeriesRef.current = sma20Series;
    }

    // SMA 60
    if (sma60 && sma60.length > 0 && showSma60) {
      const sma60Series = chart.addLineSeries({
        color: "#06b6d4", // Cyan
        lineWidth: 1,
        title: "SMA 60",
        priceLineVisible: false,
      });
      sma60Series.setData(sma60.map((s) => ({ time: s.time as any, value: s.value })));
      sma60SeriesRef.current = sma60Series;
    }

    chart.timeScale().fitContent();

    // Crosshair subscribe
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData) {
        setHoverData(null);
        return;
      }
      const candleData = param.seriesData.get(candleSeries) as any;
      if (candleData) {
        setHoverData({
          time: String(param.time),
          open: candleData.open,
          high: candleData.high,
          low: candleData.low,
          close: candleData.close,
        });
      }
    });

    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [data, sma20, sma60, showSma20, showSma60, timeframe]);

  return (
    <div className="flex flex-col w-full rounded-2xl border border-slate-800/80 bg-slate-950/90 overflow-hidden shadow-lg backdrop-blur-md">
      {/* Top Header / OHLC bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-slate-800/80 bg-slate-900/60">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-bold text-slate-100">{stockName}</span>
            <span className="text-xs font-mono text-slate-400">({ticker})</span>
          </div>

          {/* OHLC hover stats */}
          {currentHover && (
            <div className="hidden lg:flex items-center gap-3 text-xs font-mono">
              <span className="text-slate-400">
                시: <strong className="text-slate-200">{formatKRW(currentHover.open)}</strong>
              </span>
              <span className="text-slate-400">
                고: <strong className="text-red-400">{formatKRW(currentHover.high)}</strong>
              </span>
              <span className="text-slate-400">
                저: <strong className="text-blue-400">{formatKRW(currentHover.low)}</strong>
              </span>
              <span className="text-slate-400">
                종:{" "}
                <strong
                  className={
                    currentHover.close >= currentHover.open ? "text-red-400" : "text-blue-400"
                  }
                >
                  {formatKRW(currentHover.close)}
                </strong>
              </span>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {/* Moving average toggles */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-950 border border-slate-800 text-[11px]">
            <button
              onClick={() => setShowSma20(!showSma20)}
              className={`flex items-center gap-1 px-1.5 py-0.5 rounded transition ${
                showSma20 ? "text-yellow-400 font-semibold" : "text-slate-500 opacity-60"
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-yellow-400" />
              SMA 20
            </button>
            <button
              onClick={() => setShowSma60(!showSma60)}
              className={`flex items-center gap-1 px-1.5 py-0.5 rounded transition ${
                showSma60 ? "text-cyan-400 font-semibold" : "text-slate-500 opacity-60"
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              SMA 60
            </button>
          </div>

          {/* Timeframe Buttons */}
          <div className="flex items-center rounded-md bg-slate-950 p-0.5 border border-slate-800 text-xs">
            {(["1M", "1D", "1W"] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 py-1 rounded text-[11px] font-medium transition ${
                  timeframe === tf
                    ? "bg-blue-600 text-white font-bold shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tf === "1M" ? "1분봉" : tf === "1D" ? "일봉" : "주봉"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart Canvas */}
      <div ref={chartContainerRef} className="w-full relative" />
    </div>
  );
};
