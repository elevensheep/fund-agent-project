import asyncio
import httpx
from core.config import get_settings
from workers.kis_client import KISClient

async def main():
    settings = get_settings()
    print(f"Configured: app_key={settings.kis_app_key[:6]}..., is_paper={settings.kis_is_paper_trading}, rest_url={settings.kis_rest_url}")

    client = KISClient()
    token = await client.get_access_token()
    print(f"Token generated: {bool(token)}")
    if token:
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": client.app_key,
            "appsecret": client.app_secret,
            "tr_id": "FHKST01010100",
            "custtype": "P",
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930",
        }
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            res = await http_client.get(f"{client.rest_url}/uapi/domestic-stock/v1/quotations/inquire-price", headers=headers, params=params)
            print(f"Status: {res.status_code}")
            if res.status_code == 200:
                body = res.json()
                out = body.get("output", {})
                print("Output:", {
                    "name": out.get("hts_kor_isnm"),
                    "price": out.get("stck_prpr"),
                    "change": out.get("prdy_vrss"),
                    "rate": out.get("prdy_ctrt"),
                    "high": out.get("stck_hgpr"),
                    "low": out.get("stck_lwpr"),
                    "vol": out.get("acml_vol"),
                })
            else:
                print("Error:", res.text)

if __name__ == "__main__":
    asyncio.run(main())
