#!/usr/bin/env python3
"""
KRX(한국거래소) 전종목(코스피/코스닥 2,600+ 기업) 마스터 DB 시더 & 레거시 초기화 스크립트.

사용법:
  # 레거시 데이터 전체 초기화 후 최신 2,600+ 종목 재적재:
  python scripts/seed_krx_stock_master.py --reset

  # 기존 테이블 유지하면서 신규/누락 종목만 Upsert:
  python scripts/seed_krx_stock_master.py
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root & shared_core to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "shared_core" / "src"))
sys.path.insert(0, str(ROOT_DIR / "app"))

from shared_core.stock_seeder import reset_and_seed_stock_database


async def main():
    parser = argparse.ArgumentParser(description="KRX Stock Master DB Seeder & Legacy Data Wiper")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe all legacy stock tables and Redis cache before seeding",
    )
    args = parser.parse_args()

    print("==================================================================")
    print("🚀 [KRX Stock Master DB Seeder]")
    print(f"👉 Reset Legacy Data Mode: {'ON (전체 초기화)' if args.reset else 'OFF (Upsert 모드)'}")
    print("==================================================================")

    res = await reset_and_seed_stock_database(reset_legacy=args.reset)

    print("\n✅ [Seeding Complete!]")
    print(f"📊 Total Stocks in DB: {res.get('total_stocks')} 종목")
    print(f"📈 KOSPI Stocks:       {res.get('kospi')} 종목")
    print(f"📉 KOSDAQ Stocks:      {res.get('kosdaq')} 종목")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(main())
