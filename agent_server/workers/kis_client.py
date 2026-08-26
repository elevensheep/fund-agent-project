import json
from typing import Any, Dict, Optional
import httpx
from core.config import get_settings
from shared_core.logger import logger


class KISClient:
    """
    한국투자증권(KIS) Open API REST & WebSocket 클라이언트 래퍼.
    - WebSocket 실시간 접속을 위한 Approval Key 발급 (/oauth2/Approval)
    - REST 조회를 위한 OAuth2 Access Token 발급 (/oauth2/tokenP)
    - 실시간 주식 체결가(H0STCNT0) 구독 및 해제 페이로드 생성
    """

    def __init__(self):
        self.settings = get_settings()
        self.app_key = self.settings.kis_app_key
        self.app_secret = self.settings.kis_app_secret
        self.account_no = self.settings.kis_account_no
        self.is_paper = self.settings.kis_is_paper_trading

        # 실전투자 vs 모의투자 도메인 설정
        if self.is_paper:
            self.rest_url = "https://openapivts.koreainvestment.com:29443"
            self.ws_url = "ws://ops.koreainvestment.com:31000/tryitout/H0STCNT0"
        else:
            self.rest_url = self.settings.kis_rest_url or "https://openapi.koreainvestment.com:9443"
            self.ws_url = self.settings.kis_ws_url or "ws://ops.koreainvestment.com:21000/tryitout/H0STCNT0"

        self.approval_key: Optional[str] = None
        self.access_token: Optional[str] = None

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
        """
        if not self.is_configured():
            return None

        if self.access_token:
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
                    self.access_token = data.get("access_token")
                    logger.info("kis_client.access_token_issued_successfully")
                    return self.access_token
        except Exception as e:
            logger.error("kis_client.access_token_exception", error=str(e))

        return None

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
