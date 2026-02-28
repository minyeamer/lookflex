"""Redis 클라이언트 싱글턴 및 헬퍼"""
import redis.asyncio as aioredis

from app.core.config import settings

# 모듈 레벨 싱글턴 — lifespan 이벤트에서 초기화
redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client


async def init_redis() -> None:
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


# ── 키 네임스페이스 헬퍼 ───────────────────────────────────────────────────────

def otp_key(email: str) -> str:
    return f"otp:{email}"


def pw_reset_key(token: str) -> str:
    return f"pw_reset:{token}"


def jwt_blacklist_key(jti: str) -> str:
    return f"jwt_blacklist:{jti}"
