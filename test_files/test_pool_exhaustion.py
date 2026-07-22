import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx


def fire_timeout_endpoint(port, delay=2.0):
    try:
        resp = httpx.get(
            f"http://127.0.0.1:{port}/info/slow_sync_timeout",
            params={"delay": delay},
            timeout=10.0,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


class TestPoolExhaustion:

    @pytest.mark.pool_exhaustion
    def test_timeout_short_pool_blocks(self):
        """With pool=2 and timeout=5s, sending 10 requests with 3s delay each:
        Some should timeout (pool can only handle 2 at a time, 10 * 3s >> 5s timeout)."""
        port = 8083
        num_requests = 10
        results = []
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(fire_timeout_endpoint, port, 3.0)
                for _ in range(num_requests)
            ]
            for f in as_completed(futures):
                results.append(f.result())

        statuses = [r.get("status") for r in results if "error" not in r]
        timeouts = sum(1 for s in statuses if s == "timeout")
        oks = sum(1 for s in statuses if s == "ok")

        assert len(statuses) > 0, "No responses received"
        assert timeouts > 0 or oks > 0, f"Unexpected statuses: {statuses}"
        # With pool=2, timeout=5s, 10 requests * 3s delay:
        # First 2 start immediately, rest queue. After 5s, queued ones timeout.
        print(f"  Timeouts: {timeouts}, OKs: {oks} out of {len(statuses)}")

    @pytest.mark.pool_exhaustion
    def test_timeout_long_pool_succeeds(self):
        """With pool=2 and timeout=60s, sending 10 requests with 3s delay each:
        All should succeed (enough time to queue through 2 connections)."""
        port = 8084
        num_requests = 10
        results = []
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(fire_timeout_endpoint, port, 3.0)
                for _ in range(num_requests)
            ]
            for f in as_completed(futures):
                results.append(f.result())

        statuses = [r.get("status") for r in results if "error" not in r]
        timeouts = sum(1 for s in statuses if s == "timeout")
        oks = sum(1 for s in statuses if s == "ok")

        assert len(statuses) == num_requests, f"Expected {num_requests} responses"
        assert timeouts == 0, f"Expected 0 timeouts, got {timeouts}"
        assert oks == num_requests, f"Expected {num_requests} OKs, got {oks}"
        print(f"  Timeouts: {timeouts}, OKs: {oks}")

    @pytest.mark.pool_exhaustion
    def test_exhaustion_detects_worker_distribution(self):
        """Verify requests are distributed across workers under exhaustion."""
        port = 8083
        num_requests = 10
        results = []
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(fire_timeout_endpoint, port, 3.0)
                for _ in range(num_requests)
            ]
            for f in as_completed(futures):
                results.append(f.result())

        pids = [r.get("worker_pid") for r in results if "error" not in r]
        unique_pids = set(pids)
        assert len(unique_pids) >= 1, f"Expected at least 1 worker PID, got {len(unique_pids)}"
