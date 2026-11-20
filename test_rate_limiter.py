"""Run with:  python -m unittest -v test_rate_limiter"""
import threading
import unittest

from rate_limiter import RateLimiter


class FakeClock:
    """Manually controlled clock so tests are fast and deterministic."""

    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class RateLimiterTests(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        rl = RateLimiter(3, clock=FakeClock())
        self.assertEqual([rl.allow_request() for _ in range(5)],
                         [True, True, True, False, False])

    def test_allows_again_after_window_passes(self):
        clk = FakeClock()
        rl = RateLimiter(2, clock=clk)
        self.assertTrue(rl.allow_request())
        self.assertTrue(rl.allow_request())
        self.assertFalse(rl.allow_request())
        clk.t += 1.0
        self.assertTrue(rl.allow_request())

    def test_no_boundary_burst(self):
        clk = FakeClock()
        rl = RateLimiter(2, clock=clk)
        clk.t += 0.9
        self.assertTrue(rl.allow_request())
        self.assertTrue(rl.allow_request())
        clk.t += 0.2  # a fixed window would reset here; this must not
        self.assertFalse(rl.allow_request())

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            RateLimiter(0)

    def test_concurrent_callers_never_exceed_limit(self):
        limit, threads, per_thread = 50, 32, 200
        rl = RateLimiter(limit, clock=FakeClock())  # frozen time = one window
        allowed = []
        barrier = threading.Barrier(threads)

        def worker():
            barrier.wait()
            allowed.append(sum(rl.allow_request() for _ in range(per_thread)))

        ts = [threading.Thread(target=worker) for _ in range(threads)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        self.assertEqual(sum(allowed), limit)


if __name__ == "__main__":
    unittest.main(verbosity=2)
