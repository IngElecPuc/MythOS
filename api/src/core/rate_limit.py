from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock

from src.core.exceptions import RateLimitExceededError


@dataclass
class WindowCounter:
    window_started_at: float
    count: int


class InMemoryRateLimiter:
    """Limitador básico para desarrollo o una única instancia.

    En despliegues con varias réplicas debe reemplazarse por Redis u otro
    almacenamiento compartido.
    """

    def __init__(self) -> None:
        self._counters: dict[str, WindowCounter] = {}
        self._lock = Lock()

    def check(self, *, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        with self._lock:
            counter = self._counters.get(key)
            if counter is None or now - counter.window_started_at >= window_seconds:
                self._counters[key] = WindowCounter(now, 1)
                return

            if counter.count >= limit:
                retry_after = max(
                    1,
                    int(window_seconds - (now - counter.window_started_at)),
                )
                raise RateLimitExceededError(retry_after=retry_after)

            counter.count += 1
