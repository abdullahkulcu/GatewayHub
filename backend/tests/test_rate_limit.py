import pytest

from providers.rate_limit import TokenBucket


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_rejects_non_positive_rate() -> None:
    with pytest.raises(ValueError, match="positive"):
        TokenBucket(rate_per_minute=0)


def test_acquire_does_not_sleep_when_tokens_available() -> None:
    clock = _FakeClock()
    sleeps: list[float] = []
    bucket = TokenBucket(rate_per_minute=60, clock=clock, sleep=sleeps.append)

    bucket.acquire()

    assert sleeps == []


def test_acquire_sleeps_when_bucket_is_empty_and_never_raises() -> None:
    clock = _FakeClock()

    def fake_sleep(seconds: float) -> None:
        clock.advance(seconds)

    bucket = TokenBucket(rate_per_minute=60, capacity=1, clock=clock, sleep=fake_sleep)

    bucket.acquire()  # consumes the single token, tokens now 0
    bucket.acquire()  # bucket empty: must wait ~1s (60/min == 1/s), not raise

    # two tokens consumed over ~1 second at 1 token/sec: no exception, clock advanced
    assert clock.now >= 1.0


def test_refills_over_time_without_exceeding_capacity() -> None:
    clock = _FakeClock()
    sleeps: list[float] = []
    bucket = TokenBucket(rate_per_minute=60, capacity=5, clock=clock, sleep=sleeps.append)

    for _ in range(5):
        bucket.acquire()
    assert sleeps == []  # burst capacity absorbs 5 immediate acquisitions

    clock.advance(120)  # plenty of time to refill past capacity
    bucket.acquire()

    assert sleeps == []  # refilled (capped at capacity), so still no sleep needed


def test_repeated_acquire_beyond_capacity_never_raises() -> None:
    clock = _FakeClock()
    bucket = TokenBucket(
        rate_per_minute=600, capacity=1, clock=clock, sleep=clock.advance
    )

    for _ in range(20):
        bucket.acquire()  # would raise/deadlock if implementation were broken
