import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from core.config import get_settings
from shared_core.logger import logger

TOKEN_CACHE_FILE = "/tmp/kis_token_cache.json"


class KISClient:
    """
    한국투자증권(KIS) Open API REST & WebSocket 클라이언트 래퍼.
    - 24시간 토큰 로컬/인메모리 캐싱 (1분 1회 제한 대응)
    - 주식현재가 시세 조회 (inquire-price: FHKST01010100)
    - 국내주식 기간별 시세/일봉 조회 (inquire-daily-price: FHKST01010400)
    - WebSocket 실시간 체결가 구독/해제
    """

    def __init__(self):
        self.settings = get_settings()
        self.app_key = self.settings.kis_app_key
        self.app_secret = self.settings.kis_app_secret
        self.account_no = self.settings.kis_account_no
        self.is_paper = self.settings.kis_is_paper_trading

        # 실전투자 vs 모의투자 도메인 설정 (설정된 kis_rest_url 우선)
        if self.settings.kis_rest_url:
            self.rest_url = self.settings.kis_rest_url
            self.ws_url = self.settings.kis_ws_url or "ws://ops.koreainvestment.com:21000/tryitout/H0STCNT0"
        elif self.is_paper:
            self.rest_url = "https://openapivts.koreainvestment.com:29443"
            self.ws_url = "ws://ops.koreainvestment.com:31000/tryitout/H0STCNT0"
        else:
            self.rest_url = "https://openapi.koreainvestment.com:9443"
            self.ws_url = "ws://ops.koreainvestment.com:21000/tryitout/H0STCNT0"

        self.approval_key: Optional[str] = None
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0.0

        # KIS TPS(초당 호출 제한) 방어용 레이트 리미터 설정 (모의투자는 초당 2건 이하 엄격 제한)
        self._last_request_time: float = 0.0
        self._min_interval: float = 1.0 if self.is_paper else 0.3

        # 초기 캐시 파일 로드
        self._load_cached_token()

    def _get_redis_client(self):
        try:
            import redis
            host = self.settings.redis_host or "agent_redis"
            port = self.settings.redis_port or 6379
            return redis.Redis(host=host, port=port, decode_responses=True, socket_connect_timeout=2)
        except Exception:
            return None

    def _load_cached_token(self):
        """파일 캐시 및 Redis로부터 토큰 및 만료시각 로드"""
        # 1. Redis 캐시 확인
        try:
            r = self._get_redis_client()
            if r:
                token = r.get("kis:access_token")
                ttl = r.ttl("kis:access_token")
                if token and ttl > 300:
                    self.access_token = token
                    self.token_expires_at = time.time() + ttl
                    logger.info("kis_client.redis_cached_token_loaded", expires_in=ttl)
                    return
        except Exception as e:
            logger.debug("kis_client.redis_token_load_skip", error=str(e))

        # 2. 파일 캐시 확인
        try:
            if os.path.exists(TOKEN_CACHE_FILE):
                with open(TOKEN_CACHE_FILE, "r") as f:
                    cache_data = json.load(f)
                    now = time.time()
                    if cache_data.get("expires_at", 0) > now + 300:
                        self.access_token = cache_data.get("access_token")
                        self.token_expires_at = cache_data.get("expires_at", 0)
                        logger.info("kis_client.file_cached_token_loaded", expires_in=int(self.token_expires_at - now))
        except Exception as e:
            logger.warning("kis_client.load_cache_failed", error=str(e))

    def _save_cached_token(self, token: str, expires_in: int = 86400):
        """토큰을 Redis 및 로컬 파일에 캐싱 (24시간)"""
        self.access_token = token
        self.token_expires_at = time.time() + expires_in

        # 1. Redis에 24시간 TTL로 저장
        try:
            r = self._get_redis_client()
            if r:
                r.set("kis:access_token", token, ex=expires_in)
                logger.info("kis_client.token_saved_to_redis", ttl=expires_in)
        except Exception as e:
            logger.warning("kis_client.save_redis_token_failed", error=str(e))

        # 2. 파일에 저장
        try:
            with open(TOKEN_CACHE_FILE, "w") as f:
                json.dump({"access_token": token, "expires_at": self.token_expires_at}, f)
        except Exception as e:
            logger.warning("kis_client.save_cache_failed", error=str(e))

    def is_configured(self) -> bool:
        """API 키 설정 여부 검증"""
        return bool(self.app_key and self.app_secret and not self.app_key.startswith("your_"))

    async def get_websocket_approval_key(self) -> Optional[str]:
        """
        WebSocket 접속을 위한 Approval Key 발급 (POST /oauth2/Approval)
        """
        if not self.is_configured():
            logger.info("kis_client.no_api_keys_provided_for_approval_key")
            return None

        if self.approval_key:
            return self.approval_key

        url = f"{self.rest_url}/oauth2/Approval"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.app_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    self.approval_key = data.get("approval_key")
                    logger.info("kis_client.approval_key_issued_successfully")
                    return self.approval_key
                else:
                    logger.error("kis_client.approval_key_failed", status=resp.status_code, body=resp.text)
        except Exception as e:
            logger.error("kis_client.approval_key_exception", error=str(e))

        return None

    async def get_access_token(self) -> Optional[str]:
        """
        REST 조회를 위한 OAuth2 접근토큰 발급 (POST /oauth2/tokenP)
        * 1분 1회 발급 제한에 대응하여 24시간 동안 유효 토큰을 캐시 재사용합니다.
        """
        if not self.is_configured():
            return None

        # 1. 이미 유효한 토큰이 메모리/Redis/파일에 있으면 즉시 반환
        if self.access_token and time.time() < self.token_expires_at - 300:
            return self.access_token

        # Redis 다시 한번 확인
        self._load_cached_token()
        if self.access_token and time.time() < self.token_expires_at - 300:
            return self.access_token

        url = f"{self.rest_url}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    token = data.get("access_token")
                    expires_in = data.get("expires_in", 86400)
                    if token:
                        self._save_cached_token(token, expires_in)
                        logger.info("kis_client.access_token_issued_successfully", expires_in=expires_in)
                        return token
                else:
                    logger.error("kis_client.access_token_failed", status=resp.status_code, body=resp.text)
        except Exception as e:
            logger.error("kis_client.access_token_exception", error=str(e))

        return self.access_token

    async def fetch_current_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        국내주식 현재가 시세 조회 (REST: FHKST01010100)
        실제 KIS 실시간 시세를 직접 가져옵니다.
        """
        token = await self.get_access_token()
        if not token:
            logger.warning("kis_client.fetch_price_no_token", ticker=ticker)
            return None

        def _sync_fetch(attempt: int = 0) -> Optional[Dict[str, Any]]:
            # TPS Rate Throttling
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()

            import urllib.request
            import urllib.parse
            url = f"{self.rest_url}/uapi/domestic-stock/v1/quotations/inquire-price?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD={ticker}"
            req = urllib.request.Request(
                url,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "authorization": f"Bearer {token}",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                    "tr_id": "FHKST01010100",
                    "custtype": "P",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    out = data.get("output", {})
                    if out and out.get("stck_prpr"):
                        close_p = float(out.get("stck_prpr", 0))
                        change_p = float(out.get("prdy_vrss", 0))
                        change_r = float(out.get("prdy_ctrt", 0.0))
                        open_p = float(out.get("stck_oprc", close_p))
                        high_p = float(out.get("stck_hgpr", close_p))
                        low_p = float(out.get("stck_lwpr", close_p))
                        volume = int(out.get("acml_vol", 0))
                        prev_close = float(out.get("stck_sdpr", close_p - change_p))
                        name = out.get("hts_kor_isnm") or ticker

                        return {
                            "ticker": ticker,
                            "name": name,
                            "market": "KOSPI" if not ticker.startswith("2") else "KOSDAQ",
                            "price": close_p,
                            "change": change_p,
                            "changePercent": change_r,
                            "volume": volume,
                            "high": high_p,
                            "low": low_p,
                            "open": open_p,
                            "prevClose": prev_close,
                            "updatedAt": datetime.now().strftime("%H:%M:%S"),
                            "is_live": True,
                        }
                    else:
                        logger.warning("kis_client.fetch_price_empty_output", ticker=ticker, msg=data.get("msg1"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                if "EGW00201" in err_body or "초당 거래건수" in err_body:
                    if attempt < 2:
                        wait_sec = 1.5 * (attempt + 1)
                        logger.warning(
                            "kis_client.fetch_price_rate_limited",
                            ticker=ticker,
                            retry_in_sec=wait_sec,
                            attempt=attempt + 1,
                        )
                        time.sleep(wait_sec)
                        return _sync_fetch(attempt=attempt + 1)
                    else:
                        logger.warning("kis_client.fetch_price_rate_limit_exceeded_skip", ticker=ticker)
                        return None
                logger.error("kis_client.fetch_price_http_error", ticker=ticker, code=e.code, body=err_body[:200])
            except Exception as e:
                logger.error("kis_client.fetch_price_exception", ticker=ticker, error=str(e))
            return None

        import asyncio
        return await asyncio.to_thread(_sync_fetch)

    async def fetch_daily_candles(self, ticker: str, count: int = 30) -> List[Dict[str, Any]]:
        """
        국내주식 일봉 차트 시세 조회 (REST: FHKST01010400)
        """
        token = await self.get_access_token()
        if not token:
            return []

        def _sync_fetch_candles(attempt: int = 0) -> List[Dict[str, Any]]:
            # TPS Rate Throttling
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()

            import urllib.request
            url = (
                f"{self.rest_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
                f"?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD={ticker}"
                f"&FID_PERIOD_DIV_CODE=D&FID_ORG_ADJ_PRC=0"
            )
            req = urllib.request.Request(
                url,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "authorization": f"Bearer {token}",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                    "tr_id": "FHKST01010400",
                    "custtype": "P",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    output2 = data.get("output2", [])
                    candles = []
                    for item in output2[:count]:
                        trade_date = item.get("stck_bsop_date", "")
                        if trade_date and len(trade_date) == 8:
                            formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
                        else:
                            formatted_date = trade_date

                        candles.append({
                            "time": formatted_date,
                            "open": float(item.get("stck_oprc", 0)),
                            "high": float(item.get("stck_hgpr", 0)),
                            "low": float(item.get("stck_lwpr", 0)),
                            "close": float(item.get("stck_clpr", 0)),
                            "volume": int(item.get("acml_vol", 0)),
                        })
                    candles.reverse()  # 시간순 정렬
                    return candles
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                if "EGW00201" in err_body or "초당 거래건수" in err_body:
                    if attempt < 2:
                        wait_sec = 1.5 * (attempt + 1)
                        logger.warning(
                            "kis_client.fetch_daily_candles_rate_limited",
                            ticker=ticker,
                            retry_in_sec=wait_sec,
                            attempt=attempt + 1,
                        )
                        time.sleep(wait_sec)
                        return _sync_fetch_candles(attempt=attempt + 1)
                    else:
                        logger.warning("kis_client.fetch_daily_candles_rate_limit_exceeded_skip", ticker=ticker)
                        return []
                logger.error("kis_client.fetch_daily_candles_http_error", ticker=ticker, code=e.code, body=err_body[:200])
            except Exception as e:
                logger.error("kis_client.fetch_daily_candles_exception", ticker=ticker, error=str(e))
                return []

        import asyncio
        return await asyncio.to_thread(_sync_fetch_candles)

    def get_subscription_payload(self, ticker: str, is_register: bool = True) -> str:
        """
        한국투자증권 WebSocket 실시간 체결가 (H0STCNT0) 등록/해제 요청 페이로드
        - tr_type: 1 (등록), 2 (해제)
        - tr_id: H0STCNT0 (실시간 체결가)
        - tr_key: 종목코드 (e.g. 005930)
        """
        app_key_to_use = self.approval_key or "mock_approval_key"
        payload = {
            "header": {
                "approval_key": app_key_to_use,
                "custtype": "P",
                "tr_type": "1" if is_register else "2",
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0",
                    "tr_key": ticker,
                }
            }
        }
        return json.dumps(payload)
