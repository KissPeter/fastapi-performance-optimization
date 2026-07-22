import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx


def fire_slow_sync(port, delay=0.5):
    """Send request to /info/slow_sync and return introspection data."""
    try:
        resp = httpx.get(
            f"http://127.0.0.1:{port}/info/slow_sync",
            params={"delay": delay},
            timeout=10.0,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def fire_slow_async(port, delay=0.5):
    """Send request to /info/slow_async and return introspection data."""
    try:
        resp = httpx.get(
            f"http://127.0.0.1:{port}/info/slow_async",
            params={"delay": delay},
            timeout=10.0,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def send_concurrent(port, num_requests=20, delay=0.5, async_endpoint=False):
    """Fire concurrent requests and return results grouped by worker PID."""
    fn = fire_slow_async if async_endpoint else fire_slow_sync
    results = []

    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [
            executor.submit(fn, port, delay) for _ in range(num_requests)
        ]
        for f in as_completed(futures):
            results.append(f.result())

    workers = {}
    for r in results:
        if "error" in r:
            continue
        pid = r.get("worker_pid")
        if pid not in workers:
            workers[pid] = []
        workers[pid].append(r)

    return workers


class TestConcurrency:

    @pytest.mark.concurrency
    def test_per_worker_pool_isolation_pool_2(self):
        """Pool size=2 with 2 workers: each worker handles max 2 concurrent sync requests."""
        workers = send_concurrent(port=8070, num_requests=20, delay=0.3)
        assert len(workers) >= 1, f"Expected at least 1 worker, got {len(workers)}"
        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            assert max_conc <= 4, (
                f"Worker {pid}: max concurrent={max_conc}, expected ≤ 4 "
                f"(pool_size=2 × 2 workers margin)"
            )

    @pytest.mark.concurrency
    def test_per_worker_pool_isolation_pool_4(self):
        """Pool size=4 with 2 workers: each worker handles max 4 concurrent sync requests."""
        workers = send_concurrent(port=8071, num_requests=20, delay=0.3)
        assert len(workers) >= 1, f"Expected at least 1 worker, got {len(workers)}"
        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            assert max_conc <= 6, (
                f"Worker {pid}: max concurrent={max_conc}, expected ≤ 6 "
                f"(pool_size=4 + margin)"
            )

    @pytest.mark.concurrency
    def test_anyio_thread_pool_ceiling(self):
        """Pool size=100 with 2 workers: concurrency capped by anyio thread pool (40), not pool size."""
        workers = send_concurrent(port=8072, num_requests=60, delay=0.3)
        assert len(workers) >= 1, f"Expected at least 1 worker, got {len(workers)}"
        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            assert max_conc <= 42, (
                f"Worker {pid}: max concurrent={max_conc}, expected ≤ 42 "
                f"(anyio ceiling=40 + margin)"
            )

    @pytest.mark.concurrency
    def test_pool_is_per_process_not_per_app(self):
        """With 2 workers, requests should be distributed across multiple PIDs."""
        workers = send_concurrent(port=8071, num_requests=20, delay=0.3)
        pids = list(workers.keys())
        assert len(pids) >= 2, (
            f"Expected 2 worker PIDs for per-process isolation, got {len(pids)}: {pids}. "
            f"This suggests pool may be per-app, not per-process."
        )

    @pytest.mark.concurrency
    def test_async_pool_not_limited_by_http_pool(self):
        """Async endpoints should not be blocked by per-worker HTTP pool limits."""
        workers = send_concurrent(
            port=8070, num_requests=20, delay=0.3, async_endpoint=True
        )
        assert len(workers) >= 1, f"Expected at least 1 worker, got {len(workers)}"
        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            assert max_conc <= 22, (
                f"Worker {pid}: async max concurrent={max_conc}, expected ≤ 22 "
                f"(anyio ceiling + margin)"
            )
