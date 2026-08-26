import hashlib
import json
import os
from typing import Any, Dict, Optional
import redis.asyncio as aioredis

from shared_core.logger import logger


class RedisCacheManager:
    """
    공통 Redis 비동기 캐시 관리자 (Async Redis Cache Manager).
    연결 실패 시 에러를 유발하지 않고 Graceful Fallback 처리(Fail-open)합니다.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: int = 0,
        default_ttl: int = 300,
    ):
        self.host = host or os.getenv("REDIS_HOST", "agent_redis")
        self.port = int(port or os.getenv("REDIS_PORT", 6379))
        self.password = password or os.getenv("REDIS_PASSWORD") or None
        self.db = db
        self.default_ttl = default_ttl
        self._client: Optional[aioredis.Redis] = None
        self._is_connected: bool = False

    async def get_client(self) -> Optional[aioredis.Redis]:
        if self._client is None:
            try:
                self._client = aioredis.Redis(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    db=self.db,
                    decode_responses=True,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                )
                await self._client.ping()
                self._is_connected = True
                logger.info("cache.redis.connected", host=self.host, port=self.port)
            except Exception as e:
                logger.warning("cache.redis.connection_failed", host=self.host, port=self.port, error=str(e))
                self._client = None
                self._is_connected = False
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """문자열 캐시 조회"""
        try:
            client = await self.get_client()
            if client:
                val = await client.get(key)
                if val is not None:
                    logger.info("cache.hit", key=key)
                    return val
                logger.debug("cache.miss", key=key)
        except Exception as e:
            logger.warning("cache.get_failed", key=key, error=str(e))
        return None

    async def get_json(self, key: str) -> Optional[Any]:
        """JSON 역직렬화 캐시 조회"""
        raw = await self.get(key)
        if raw is not None:
            try:
                return json.loads(raw)
            except Exception as e:
                logger.warning("cache.json_decode_failed", key=key, error=str(e))
        return None

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """문자열 캐시 저장 (TTL 설정)"""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        try:
            client = await self.get_client()
            if client:
                await client.set(key, value, ex=ttl)
                logger.info("cache.set", key=key, ttl=ttl)
                return True
        except Exception as e:
            logger.warning("cache.set_failed", key=key, error=str(e))
        return False

    async def set_json(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> bool:
        """JSON 직렬화 캐시 저장"""
        try:
            serialized = json.dumps(data, ensure_ascii=False)
            return await self.set(key, serialized, ttl_seconds=ttl_seconds)
        except Exception as e:
            logger.warning("cache.json_encode_failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """캐시 삭제"""
        try:
            client = await self.get_client()
            if client:
                await client.delete(key)
                logger.info("cache.delete", key=key)
                return True
        except Exception as e:
            logger.warning("cache.delete_failed", key=key, error=str(e))
        return False

    async def ttl(self, key: str) -> int:
        """잔여 TTL(초) 조회"""
        try:
            client = await self.get_client()
            if client:
                return await client.ttl(key)
        except Exception as e:
            logger.warning("cache.ttl_failed", key=key, error=str(e))
        return -2

    async def ping(self) -> bool:
        """Redis 헬스체크"""
        try:
            client = await self.get_client()
            if client:
                return bool(await client.ping())
        except Exception:
            return False
        return False

    async def close(self):
        """연결 종료"""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._is_connected = False

    @staticmethod
    def generate_key(prefix: str, *parts: str) -> str:
        """캐시 키 생성 헬퍼"""
        clean_parts = [str(p).strip().replace(" ", "_") for p in parts if p]
        return f"{prefix}:{':'.join(clean_parts)}"

    @staticmethod
    def hash_text(text: str) -> str:
        """텍스트 해시 생성"""
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


_default_cache: Optional[RedisCacheManager] = None


def get_cache_manager(
    host: Optional[str] = None,
    port: Optional[int] = None,
    password: Optional[str] = None,
    default_ttl: int = 300,
) -> RedisCacheManager:
    global _default_cache
    if _default_cache is None:
        _default_cache = RedisCacheManager(
            host=host,
            port=port,
            password=password,
            default_ttl=default_ttl,
        )
    return _default_cache
