import asyncio
import httpx
from core.config import get_settings

async def main():
    settings = get_settings()
    app_key = settings.kis_app_key
    app_secret = settings.kis_app_secret

    print(f"Testing KIS Token...")
    print(f"AppKey (len={len(app_key)}): {app_key[:8]}...")
    print(f"AppSecret (len={len(app_secret)}): {app_secret[:8]}...")

    # 1. Test Real Trading Endpoint (9443)
    real_url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    # 2. Test Paper Trading Endpoint (29443)
    paper_url = "https://openapivts.koreainvestment.com:29443/oauth2/tokenP"

    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        print("\n--- Testing Real Trading Server (openapi.koreainvestment.com:9443) ---")
        try:
            resp_real = await client.post(real_url, json=payload)
            print(f"Status: {resp_real.status_code}")
            print(f"Response: {resp_real.text}")
        except Exception as e:
            print(f"Error: {e}")

        print("\n--- Testing Paper Trading Server (openapivts.koreainvestment.com:29443) ---")
        try:
            resp_paper = await client.post(paper_url, json=payload)
            print(f"Status: {resp_paper.status_code}")
            print(f"Response: {resp_paper.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
