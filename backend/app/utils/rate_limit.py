import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from app.core.config import get_settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, request: Request) -> None:
        settings = get_settings()
        key = request.client.host if request.client else "anonymous"
        now = time.time()
        bucket = self._buckets[key]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again shortly.")
        bucket.append(now)


rate_limiter = InMemoryRateLimiter()
