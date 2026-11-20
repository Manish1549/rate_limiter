# Thread-Safe Rate Limiter

A Python rate limiter for shared use by multiple threads. It allows at most **N successful calls in any rolling one-second window**.

<img width="805" height="613" alt="image" src="https://github.com/user-attachments/assets/f18fa92a-5e38-420c-a99a-8156c36ec980" />

Deque
<img width="747" height="331" alt="image" src="https://github.com/user-attachments/assets/44818c2e-6612-4144-8b14-9de1885d7ef0" />



https://www.loom.com/share/0168fb4b8e05411aac8ea4f1792aa8aa

## Usage

Create one limiter for the channel and share that instance among the threads making requests:

```python
from rate_limiter import RateLimiter

limiter = RateLimiter(max_per_second=10)

if limiter.allow_request():
    call_channel_api()
```

`allow_request()` returns `True` when the call is admitted and `False` when the limit has already been reached. `max_per_second` must be a positive integer.

## Algorithm and thread safety

The implementation uses a **sliding-window log**. It stores the monotonic timestamps of successful calls. On each attempt, it removes timestamps at least one second old, checks how many remain, and records the new call if the count is below the limit.

A single `threading.Lock` protects this decision and update so concurrent callers cannot claim the same remaining slot. This is an in-process limiter: separate processes or machines would need shared coordination to enforce one combined limit.

A fixed per-second counter can admit nearly `2N` calls near a second boundary. The sliding window prevents that boundary burst. It can still admit up to `N` calls close together when the window has no recent calls; the guarantee is no more than `N` in any rolling one-second interval.

## Project files

| File | Purpose |
|---|---|
| `rate_limiter.py` | Limiter implementation |
| `test_rate_limiter.py` | Unit tests for limits, window expiry, boundary behavior, invalid limits, and concurrent callers |

The tests use an injectable fake clock to check timing behavior without sleeping. The concurrency test starts 32 threads against a limit of 50 and verifies that exactly 50 calls are admitted.

## Setup and run tests (Windows PowerShell)

From this project folder, create and activate a virtual environment, then run the tests:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m unittest -v test_rate_limiter
```

Alternatively, run the virtual environment's Python directly without activating it:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_rate_limiter
```



## Complexity

Each allowed timestamp is inserted once and removed once, so cleanup is **O(1) amortized per call**. The log uses **O(N) memory** for a limit of N.



## Results

### Test results

All 5 unit tests pass (`python -m unittest -v test_rate_limiter`):

```
test_allows_again_after_window_passes ... ok
test_allows_up_to_limit_then_blocks ... ok
test_concurrent_callers_never_exceed_limit ... ok
test_invalid_limit ... ok
test_no_boundary_burst ... ok

Ran 5 tests in 0.011s

OK
```

| Scenario | Expected | Result |
|---|---|---|
| 5 calls with N = 3 | `True, True, True, False, False` | Pass |
| Call after the 1-second window has passed | Allowed again | Pass |
| N calls at 0.9s, then another call at 1.1s | Rejected (no boundary burst) | Pass |
| `max_per_second = 0` | `ValueError` | Pass |
| 32 threads, 6,400 attempts, N = 50, frozen clock | Exactly 50 admitted | Pass |

### Sliding window vs fixed window

With N = 5 and 10 calls arriving between 0.80s and 1.18s (5 just before the 1-second mark, 5 just after):

| Approach | Calls admitted | Within the limit? |
|---|---|---|
| Fixed per-second counter | 10 | No: 2N calls in about 0.4 seconds |
| Sliding window (this solution) | 5 | Yes |

With bursty traffic (18 calls over 3 seconds, N = 5), the limiter admitted 12 and rejected 6, and never admitted more than 5 in any rolling second. See `rate_limiter_visual.png` for the timeline.

### Conclusion

The limiter never admits more than N calls in any one-second window, including under concurrent access from many threads and at second boundaries where a fixed counter would fail.
