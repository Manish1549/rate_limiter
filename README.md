# Thread-Safe Rate Limiter

A Python rate limiter for shared use by multiple threads. It allows at most **N successful calls in any rolling one-second window**.

<img width="805" height="613" alt="image" src="https://github.com/user-attachments/assets/f18fa92a-5e38-420c-a99a-8156c36ec980" />

Deque
<img width="747" height="331" alt="image" src="https://github.com/user-attachments/assets/44818c2e-6612-4144-8b14-9de1885d7ef0" />



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
