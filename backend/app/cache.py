import json
from typing import Any

from .config import get_settings


class FeatureCache:
    def __init__(self) -> None:
        self._client = None
        settings = get_settings()
        if not settings.redis_url:
            return

        try:
            import redis

            self._client = redis.from_url(settings.redis_url, decode_responses=True)
            self._client.ping()
        except Exception:
            self._client = None

    def get_json(self, key: str) -> dict[str, Any] | None:
        if self._client is None:
            return None
        raw = self._client.get(key)
        return json.loads(raw) if raw else None

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int = 3600) -> None:
        if self._client is None:
            return
        self._client.setex(key, ttl_seconds, json.dumps(value))
