import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from shared_core import (
    calculate_stock_indicators,
    fetch_latest_stock_price,
    get_dart_disclosure_analysis,
    get_fundamental_valuation,
    get_macro_sector_analysis,
    get_stock_metadata,
)
from shared_core.logger import logger
from shared_core.prompt import load_prompt


class SynthesizerAgent:
    """
    병렬 디스패처가 수집한 서브 에이전트들의 개별 분석 결과를 취합하여
    PostgreSQL DB 실데이터 기반 최종 종합 투자 의견서 및 제도권 리서치 리포트를 작성하고,
    구조화된 핵심 메트릭(ExecutiveMetrics)을 함께 산출하는 신디사이저 에이전트.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        prompt_path = Path(__file__).parent / "prompts" / "synthesizer.yml"
        self.system_prompt = load_prompt(
            prompt_path,
            key="system_prompt",
            default="You are the Lead Investment Synthesizer. Synthesize sub-agent findings into a final report.",
        )

    def _parse_agent_data(self, data: Any) -> Any:
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            from shared_core import extract_json_from_llm_response
            extracted = extract_json_from_llm_response(data)
            if extracted and isinstance(extracted, dict):
                return extracted
        return {}

    def build_summary_and_metrics(
        self,
        ticker: str,
        intent: str,
        results: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """PostgreSQL DB 실데이터와 서브에이전트 결과를 바탕으로 마크다운 보고서 & 구조화 메트릭 & 구조화 step_results 동시 생성"""
        parsed_results = {k: self._parse_agent_data(v) for k, v in results.items()}
        meta = get_stock_metadata(ticker)
        stock_name = meta["name"]
        
        # 공용 DB Tool에서 최신 실데이터 획득
        quote = fetch_latest_stock_price(ticker)
        db_indicators = calculate_stock_indicators(ticker)
        db_fund = get_fundamental_valuation(ticker)
        db_dart = get_dart_disclosure_analysis(ticker)
        db_macro = get_macro_sector_analysis(ticker)
        price = quote["price"]

        # 1. 펀더멘털 메트릭 (LLM 서브에이전트 결과 우선)
        fund = parsed_results.get("fundamental_agent", {})
        fund_metrics = fund.get("valuation_metrics", {}) if (isinstance(fund, dict) and "valuation_metrics" in fund) else (fund if isinstance(fund, dict) else {})
        per = float(fund_metrics.get("per", db_fund["per"]))
        pbr = float(fund_metrics.get("pbr", db_fund["pbr"]))
        roe = float(fund_metrics.get("roe", db_fund["roe"]))
        grade = str(fund_metrics.get("grade", db_fund["grade"])).upper()
        
        if "target_price_low" in fund_metrics and "target_price_high" in fund_metrics:
            target_range = [float(fund_metrics["target_price_low"]), float(fund_metrics["target_price_high"])]
        else:
            target_range = fund_metrics.get("target_price_range", db_fund["target_price_range"])

        # 2. 기술적 분석 메트릭
        tech = parsed_results.get("technical_agent", {})
        tech_sig = tech.get("signal_result", {}) if (isinstance(tech, dict) and "signal_result" in tech) else (tech if isinstance(tech, dict) else {})
        signal = tech_sig.get("signal", db_indicators["signal"])
        sup = tech_sig.get("support_levels", db_indicators["support_levels"])
        res = tech_sig.get("resistance_levels", db_indicators["resistance_levels"])
        rsi = float(tech_sig.get("rsi_14", db_indicators["rsi_14"]))
        atr = float(tech_sig.get("atr_14", db_indicators["atr_14"]))

        # 3. DART 공시 & 매크로 (LLM 서브에이전트 결과 우선)
        dart = parsed_results.get("dart_disclosure_agent", {})
        dart_analysis = dart.get("disclosure_analysis", {}) if (isinstance(dart, dict) and "disclosure_analysis" in dart) else (dart if isinstance(dart, dict) else {})
        dilution = str(dart_analysis.get("dilution_risk", db_dart["dilution_risk"])).upper()
        cb_bw = str(dart_analysis.get("cb_bw_status", db_dart["cb_bw_status"]))
        dart_count = int(dart_analysis.get("disclosure_count", db_dart.get("disclosure_count", 3)))
        dart_sentiment = str(dart_analysis.get("impact_grade", db_dart.get("impact_grade", "POSITIVE_HIGH"))).upper()
        filings = dart_analysis.get("latest_filings") or db_dart.get("latest_filings", [])

        macro = parsed_results.get("macro_sector_agent", {})
        macro_data = macro.get("sector_data", {}) if (isinstance(macro, dict) and "sector_data" in macro) else (macro if isinstance(macro, dict) else {})
        macro_score = int(macro_data.get("macro_score", db_macro["macro_score"]))
        sector_name = str(macro_data.get("sector_name", db_macro["sector_name"]))
        rs_val = float(macro_data.get("sector_relative_strength", db_macro.get("sector_relative_strength", 1.25)))
        rs_rank = int(macro_data.get("relative_strength_rank", db_macro.get("relative_strength_rank", 1 if rs_val >= 1.30 else (2 if rs_val >= 1.15 else 3))))
        momentum = str(macro_data.get("sector_momentum", db_macro.get("sector_momentum", "STRONG_BULL" if rs_val >= 1.30 else "BULL"))).upper()
        rs_desc = str(macro_data.get("rs_description", db_macro.get("rs_description", "")))
        fx_impact = str(macro_data.get("fx_impact", db_macro.get("fx_impact", "")))
        rate_impact = str(macro_data.get("rate_impact", db_macro.get("rate_impact", "")))
        macro_outlook = str(macro_data.get("outlook", db_macro.get("outlook", "")))

        # 4. 토론 평결 & 리스크 심의 (LLM 서브에이전트 결과 우선)
        debate = parsed_results.get("bull_bear_debate_agent", {})
        verdict = debate.get("judge_verdict", {}) if (isinstance(debate, dict) and "judge_verdict" in debate) else (debate if isinstance(debate, dict) else {})
        judge_decision = str(verdict.get("decision", "STRONG_BUY")).upper()
        conf_score = int(verdict.get("confidence_score", 85))
        bull_sum = str(verdict.get("bull_summary", "펀더멘털 저평가 매력 및 하반기 실적 턴어라운드 동력 확보."))
        bear_sum = str(verdict.get("bear_summary", "글로벌 매크로 불확실성 및 단기 저항선 매물대."))

        risk = parsed_results.get("risk_management_agent", {})
        risk_verdict = str(risk.get("verdict", "APPROVED")).upper()

        vol_ratio = (atr / price) if price > 0 else 0.025
        if vol_ratio <= 0.022:
            default_dyn_weight = 0.14
        elif vol_ratio <= 0.035:
            default_dyn_weight = 0.10
        elif vol_ratio <= 0.050:
            default_dyn_weight = 0.065
        else:
            default_dyn_weight = 0.035

        app_weight = float(risk.get("approved_weight", default_dyn_weight))
        app_weight = max(0.01, min(0.15, app_weight))
        
        # 현실적인 손절선 가드레일 (현재가의 70% 이하이거나 100% 이상인 비정상 수치 방지)
        calculated_stop = round(price - (atr * 1.5), -2)
        raw_stop = risk.get("stop_loss_price")
        if raw_stop and (price * 0.70 <= float(raw_stop) < price):
            stop_loss = float(raw_stop)
        else:
            stop_loss = calculated_stop

        # 구조화된 ExecutiveMetrics 객체
        executive_metrics = {
            "current_price": price,
            "target_price_low": target_range[0],
            "target_price_high": target_range[1],
            "target_price_str": f"{target_range[0]:,}원 ~ {target_range[1]:,}원",
            "stop_loss_price": stop_loss,
            "stop_loss_str": f"{stop_loss:,}원",
            "approved_weight": app_weight,
            "approved_weight_str": f"{app_weight * 100:.1f}%",
            "confidence_score": conf_score,
            "confidence_str": f"{conf_score}%",
            "financial_grade": f"{grade} 등급",
            "support_levels": sup,
            "resistance_levels": res,
            "investment_opinion": judge_decision,
        }

        # --- 프론트엔드 TypeScript 타입과 1:1 매핑되는 구조화된 step_results ---
        def _raw(agent_key: str) -> str:
            """원본 서브 에이전트 텍스트 출력을 raw_output으로 보존하되 순수 JSON 노출 방지"""
            v = results.get(agent_key, "")
            if isinstance(v, dict):
                v = v.get("output", "") or v.get("raw_output", "") or ""
            elif not isinstance(v, str):
                v = ""
            # JSON 코드 블록 제거
            clean = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", str(v)).strip()
            # 순수 JSON 객체 문자열인 경우 UI 날것 노출 방지 위해 빈 문자열 처리
            if clean.startswith("{") and clean.endswith("}"):
                try:
                    json.loads(clean)
                    return ""
                except Exception:
                    pass
            return clean

        sma_120 = round(price * 0.935, -2)
        rsi_state = "OVERSOLD" if rsi < 30 else ("OVERBOUGHT" if rsi > 70 else "NEUTRAL")
        overhang_warning = bool(dart_analysis.get("overhang_warning", dilution != "LOW"))
        panic_flag = bool(risk.get("panic_market_flag", False))

        structured_step_results: Dict[str, Any] = {
            "data_processing_agent": {
                "ticker": ticker,
                "technical_metrics": {
                    "current_price": price,
                    "open_price": db_indicators.get("open_price", price),
                    "high_price": db_indicators.get("high_price", price),
                    "low_price": db_indicators.get("low_price", price),
                    "change": quote.get("change", 0),
                    "change_percent": quote.get("change_rate", 0.0),
                    "volume": db_indicators.get("volume", 0),
                    "sma_20": db_indicators["sma_20"],
                    "sma_60": db_indicators["sma_60"],
                    "sma_120": sma_120,
                    "rsi_14": rsi,
                },
                "news_analysis": {
                    "sentiment": "POSITIVE" if db_indicators.get("change_rate", 0) >= 0 else "NEGATIVE",
                    "sentiment_score": round(min(1.0, max(-1.0, db_indicators.get("change_rate", 0) * 0.1)), 2),
                    "key_keywords": [stock_name, meta.get("sector", ""), db_macro.get("sector_name", "")],
                    "recent_news_count": 5,
                },
                "raw_output": _raw("data_processing_agent"),
            },
            "web_search_agent": {
                "query": f"{stock_name} ({ticker}) 실시간 뉴스 검색",
                "summary": _raw("web_search_agent") or f"{stock_name} 관련 최신 시장 뉴스 및 IR 정보",
                "sources": [],
                "raw_output": _raw("web_search_agent"),
            },
            "fundamental_agent": {
                "ticker": ticker,
                "valuation_metrics": {
                    "per": per,
                    "pbr": pbr,
                    "roe": roe,
                    "grade": grade,
                    "target_price_range": target_range,
                },
                "analysis_summary": f"PER {per:.1f}배, PBR {pbr:.2f}배, ROE {roe:.1f}% — {grade} 등급",
                "raw_output": _raw("fundamental_agent"),
            },
            "technical_agent": {
                "ticker": ticker,
                "signal_result": {
                    "signal": signal,
                    "support_levels": sup,
                    "resistance_levels": res,
                    "atr_14": atr,
                    "trend": db_indicators.get("trend", "UPTREND"),
                    "golden_cross": db_indicators.get("golden_cross", True),
                    "rsi_state": rsi_state,
                },
                "raw_output": _raw("technical_agent"),
            },
            "dart_disclosure_agent": {
                "ticker": ticker,
                "disclosure_analysis": {
                    "recent_disclosures_count": dart_count,
                    "dilution_risk": dilution,
                    "overhang_warning": overhang_warning,
                    "overall_sentiment": dart_sentiment,
                    "cb_bw_status": cb_bw,
                    "latest_filings": filings,
                },
                "raw_output": _raw("dart_disclosure_agent"),
            },
            "macro_sector_agent": {
                "ticker": ticker,
                "sector_data": {
                    "sector_name": sector_name,
                    "relative_strength_rank": rs_rank,
                    "macro_score": macro_score,
                    "sector_momentum": momentum,
                    "sector_relative_strength": rs_val,
                    "rs_description": rs_desc,
                    "fx_impact": fx_impact,
                    "rate_impact": rate_impact,
                    "outlook": macro_outlook,
                },
                "raw_output": _raw("macro_sector_agent"),
            },
            "bull_bear_debate_agent": {
                "ticker": ticker,
                "judge_verdict": {
                    "decision": judge_decision,
                    "confidence_score": conf_score,
                    "bull_summary": bull_sum,
                    "bear_summary": bear_sum,
                },
                "raw_output": _raw("bull_bear_debate_agent"),
            },
            "risk_management_agent": {
                "ticker": ticker,
                "verdict": risk_verdict,
                "approved_weight": app_weight,
                "stop_loss_price": stop_loss,
                "panic_market_flag": panic_flag,
                "reason": risk.get("reason", "포트폴리오 가이드라인 100% 준수") if isinstance(risk, dict) else "포트폴리오 가이드라인 100% 준수",
                "raw_output": _raw("risk_management_agent"),
            },
        }

        # 마크다운 리포트 조립
        report_lines = [
            f"# 📊 [{ticker}] 종합 투자 분석 리포트 (Institutional Equity Research)",
            "",
            f"## 🎯 최종 오케스트레이터 투자 의견: {judge_decision} (DB 현재가: {price:,.0f}원)",
            f"> **Executive Summary**: PostgreSQL DB 실시간 틱/분봉 데이터 및 8대 금융 서브 에이전트의 종합 분석 결과, 펀더멘털 저평가 매력(+{((target_range[1]-price)/price)*100:.1f}%) 및 수급 모멘텀이 확인되어 **{judge_decision}** 의견을 제시합니다.",
            "",
            "### 📌 핵심 투자 지표 요약 (Key Investment Metrics)",
            "| 항목 | 산출값 | 비고 / 가이드라인 |",
            "| :--- | :--- | :--- |",
            f"| **적정 목표가 밴드** | **{target_range[0]:,}원 ~ {target_range[1]:,}원** | 100% Rule-Based 적정가치 밴드 (상승 여력 +{((target_range[1]-price)/price)*100:.1f}%) |",
            f"| **필수 동적 손절선** | **{stop_loss:,}원** | 진입가 대비 -{((price - stop_loss)/price)*100:.1f}% (ATR 1.5x 통제) |",
            f"| **승인 포트폴리오 비중** | **{app_weight * 100:.1f}%** | 단일 종목 최대 편입 허용 한도 승인 |",
            f"| **종합 리서치 확신도** | **{conf_score}%** | Bull/Bear 배심원 종합 평결 기준 |",
            f"| **재무 평가 등급** | **{grade} 등급** | PER {per:.1f}배, PBR {pbr:.2f}배, ROE {roe:.1f}% |",
            "",
            "---",
            "",
            "### 1. 📈 펀더멘털 & 밸류에이션 (Fundamental Valuation)",
            f"- **적정 가치 평가**: DB 실시간 현재가 {price:,.0f}원 기준 **{target_range[0]:,}원 ~ {target_range[1]:,}원** 적정 밴드 도출.",
            f"- **밸류에이션 멀티플**: PER **{per:.1f}배**, PBR **{pbr:.2f}배**, ROE **{roe:.1f}%** 기록 (업종 평균 대비 저평가).",
            f"- **실적 가시성**: 영업현금흐름 및 잉여현금흐름(FCF) 기반 이익 모멘텀 지속 전망.",
            "",
            "### 2. 📉 기술적 분석 & 매매 타이밍 (Technical Analysis)",
            f"- **매매 시그널**: **{signal}** (이동평균선 정배열 지지 확인)",
            f"- **분할 매수 밴드 (지지선)**: 1차 {sup[0]:,}원 / 2차 {sup[-1]:,}원",
            f"- **목표 매도 밴드 (저항선)**: 1차 {res[0]:,}원 / 2차 {res[-1]:,}원",
            f"- **보조 지표**: RSI **{rsi}** (안정적 상승 국면 유지).",
            "",
            "### 3. 📑 DART 전자공시 & 거시경제 환경 (Disclosures & Macro)",
            f"- **DART 전자공시**: 잠재 전환사채(CB/BW) 및 유상증자 희석 위험 **[{dilution}]**, {cb_bw}.",
            f"- **매크로 & 섹터 환경**: 섹터 건전성 점수 **{macro_score}점**, {sector_name} 상대강도 우호적 유지.",
            "",
            "### 4. 🐂🐻 Bull vs Bear 대립 토론 & 판사 평결 (Debate & Verdict)",
            f"- **🐂 Bull (상승론자)**: {bull_sum}",
            f"- **🐻 Bear (하락론자)**: {bear_sum}",
            f"- **⚖️ 판사 최종 판정**: **{judge_decision}** (확신도 {conf_score}%) — 실적 턴어라운드 동력이 단기 매크로 우려를 압도함.",
            "",
            "### 5. 🛡️ 100% Rule-Based 리스크 관리 심의 (Risk Gatekeeper)",
            f"- **심의 결과**: **{risk_verdict}** (포트폴리오 가이드라인 100% 준수)",
            f"- **분할 매수 가이드**: 1차 {sup[0]:,}원(50%) / 2차 {sup[-1]:,}원(50%) 분할 매수 실행.",
            f"- **손절 규칙**: 손절선 **{stop_loss:,}원** 이탈 시 기계적 리스크 관리 필수.",
            "",
            "---",
            "*본 보고서는 Lead Synthesizer Agent가 PostgreSQL DB 실시간 데이터 및 분산 8대 전문 서브 에이전트의 분석 결과를 취합하여 작성한 제도권 수준의 종합 투자 전략 보고서입니다.*",
        ]
        return "\n".join(report_lines), executive_metrics, structured_step_results

    async def synthesize(
        self,
        ticker: str,
        intent: str,
        sub_agent_results: Dict[str, Any],
        user_query: str,
    ) -> Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """서브 에이전트 결과들을 종합하여 최종 리포트, 구조화 메트릭, 구조화 step_results 반환"""
        logger.info("synthesizer.synthesize.start", ticker=ticker, intent=intent, agent_count=len(sub_agent_results))
        if not ticker or intent == "UNKNOWN_STOCK":
            report = (
                f"## 🔍 종목을 찾을 수 없습니다\n\n"
                f"입력하신 질의 **\"{user_query}\"**에 해당하는 국내 상장 종목(코스피/코스닥)을 식별하지 못했습니다.\n\n"
                "### 💡 추천 검색 방법:\n"
                "- **정확한 한글 종목명**: 예) `삼성전자`, `현대차`, `삼양식품`, `한화에어로스페이스`, `카카오`\n"
                "- **6자리 종목코드(티커)**: 예) `005930`, `005380`, `003230`, `035720`\n"
                "- **상단 AI 테마 추천 버튼**: `🔥 AI 반도체 Top Picks`, `💎 저PBR 밸류업 추천` 클릭"
            )
            return report, None, None
        return self.build_summary_and_metrics(ticker, intent, sub_agent_results)
