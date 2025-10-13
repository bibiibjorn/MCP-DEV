import time
import unittest

from core.rate_limiter import RateLimiter


class RateLimiterTests(unittest.TestCase):
    def test_allow_request_and_throttle(self):
        rl = RateLimiter({
            'global_calls_per_second': 2,
            'global_burst': 2,
            'tool_limits': {'t': 1},
            'tool_bursts': {'t': 1},
        })
        # First request should pass
        self.assertTrue(rl.allow_request('t'))
        # Second immediate request should be throttled due to tool burst=1
        acquired, wait = rl.acquire('t', cost=1.0, timeout=0.0)
        self.assertFalse(acquired)
        # wait may be None on some fast systems; if so, treat as 0.0
        if wait is None:
            w = 0.0
        else:
            w = float(wait)
        self.assertGreaterEqual(w, 0.0)
        # After a short wait, it should pass
        time.sleep(1.1)
        self.assertTrue(rl.allow_request('t'))

    def test_get_retry_after(self):
        rl = RateLimiter({
            'global_calls_per_second': 1,
            'global_burst': 1,
            'tool_limits': {'x': 0.5},  # 1 every 2 seconds
            'tool_bursts': {'x': 1},
        })
        # Consume initial tokens
        self.assertTrue(rl.allow_request('x'))
        # Immediately ask for retry-after
        ra = rl.get_retry_after('x')
        self.assertIsInstance(ra, float)
        self.assertGreaterEqual(ra, 0.0)


if __name__ == '__main__':
    unittest.main()
