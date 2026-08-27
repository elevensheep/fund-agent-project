import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv(".env")
app_key = os.getenv("KIS_APP_KEY", "")
app_secret = os.getenv("KIS_APP_SECRET", "")
is_paper = os.getenv("KIS_IS_PAPER_TRADING", "false").lower() == "true"

print(f"Loaded from .env: len(app_key)={len(app_key)}, len(app_secret)={len(app_secret)}, is_paper={is_paper}")

payload = {
    "grant_type": "client_credentials",
    "appkey": app_key,
    "appsecret": app_secret,
}

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Real
        try:
            r = await client.post("https://openapi.koreainvestment.com:9443/oauth2/tokenP", json=payload)
            print(f"Real Trading (9443): {r.status_code} => {r.text[:150]}")
        except Exception as e:
            print(f"Real Error: {e}")

        # 2. Paper
        try:
            r = await client.post("https://openapivts.koreainvestment.com:29443/oauth2/tokenP", json=payload)
            print(f"Paper Trading (29443): {r.status_code} => {r.text[:150]}")
        except Exception as e:
            print(f"Paper Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
