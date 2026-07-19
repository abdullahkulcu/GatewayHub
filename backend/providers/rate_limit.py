import time
from collections.abc import Callable


class TokenBucket:
    """Token-bucket rate limiter shared by any provider adapter (FR-SYNC-4).

    `acquire()` blocks until enough tokens are available rather than raising
    — sync slows down when a provider's rate limit is hit, it never stops
    with an error.
    """

    def __init__(
        self,
        rate_per_minute: int,
        capacity: int | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if rate_per_minute <= 0:
            raise ValueError("rate_per_minute must be positive")
        self._rate_per_second = rate_per_minute / 60.0
        self._capacity = float(capacity if capacity is not None else rate_per_minute)
        self._tokens = self._capacity
        self._clock = clock
        self._sleep = sleep
        self._last_refill = clock()

    def _refill(self) -> None:
        now = self._clock()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate_per_second)
        self._last_refill = now

    def acquire(self, tokens: float = 1.0) -> None:
        self._refill()
        if self._tokens < tokens:
            deficit = tokens - self._tokens
            self._sleep(deficit / self._rate_per_second)
            self._refill()
        self._tokens = max(0.0, self._tokens - tokens)
