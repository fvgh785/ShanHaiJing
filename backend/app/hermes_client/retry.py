import time
import functools


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is open and requests are blocked."""
    pass


class CircuitBreaker:
    def __init__(self, threshold=5, cooldown=60):
        self.threshold = threshold
        self.cooldown = cooldown
        self._failure_count = 0
        self._last_failure_time = None
        self._open_time = None

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.threshold:
            self._open_time = time.time()

    def record_success(self):
        self._failure_count = 0
        self._last_failure_time = None
        self._open_time = None

    def is_open(self):
        if self._open_time is None:
            return False
        if time.time() - self._open_time >= self.cooldown:
            self._failure_count = 0
            self._open_time = None
            return False
        return True

    def remaining_cooldown(self):
        if self._open_time is None:
            return 0
        elapsed = time.time() - self._open_time
        return max(0, self.cooldown - elapsed)


def with_retry(func, max_retries=3, backoff_base=1):
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func()
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                sleep_time = backoff_base * (2 ** attempt)
                time.sleep(sleep_time)
    raise last_exception
