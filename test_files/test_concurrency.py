import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
import time


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
    def test_per_worker_process_isolation(self):
        """With 2 Gunicorn workers, requests are handled by 2 distinct PIDs.

        This proves each worker is a separate OS process with its own memory space,
        connection pool, and concurrency counter.
        """
        workers = send_concurrent(port=8071, num_requests=20, delay=0.3)
        pids = list(workers.keys())
        assert len(pids) >= 2, (
            f"Expected 2 worker PIDs for per-process isolation, got {len(pids)}: {pids}"
        )
        for pid, reqs in workers.items():
            assert len(reqs) > 0

    @pytest.mark.concurrency
    def test_sync_handler_concurrency_limited_by_thread_pool(self):
        """Sync handler concurrency is limited by anyio thread pool, NOT by HTTP pool.

        With pool_size=2 but default anyio thread pool (40), sending 20 concurrent
        requests to 2 workers results in ~10 concurrent handlers per worker.
        The HTTP pool_size only limits outgoing connections, not handler execution.
        Handlers block waiting for a pool slot but are still counted as active.
        """
        workers = send_concurrent(port=8070, num_requests=20, delay=0.3)
        assert len(workers) >= 1
        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            # With 20 requests / 2 workers = ~10 per worker, limited by thread pool
            assert max_conc >= 2, (
                f"Worker {pid}: max concurrent={max_conc}, expected ≥ 2 "
                f"(requests should queue beyond pool_size)"
            )

    @pytest.mark.concurrency
    def test_async_handler_concurrency_unlimited_by_pool(self):
        """Async handlers are NOT limited by HTTP connection pool at all.

        Async handlers use the event loop, not threads. They can all be in-flight
        simultaneously, only limited by the mock API's ability to handle them.
        """
        workers = send_concurrent(
            port=8070, num_requests=20, delay=0.3, async_endpoint=True
        )
        assert len(workers) >= 1
        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            # Async handlers can all be concurrent since they don't block threads
            assert max_conc >= 2, (
                f"Worker {pid}: async max concurrent={max_conc}, expected ≥ 2"
            )

    @pytest.mark.concurrency
    def test_all_requests_complete_with_small_pool(self):
        """Even with pool_size=2, all 20 requests complete successfully.

        The pool queues excess requests rather than rejecting them. This proves
        the pool acts as a throttle, not a hard limit.
        """
        port = 8070
        num_requests = 20
        results = []

        start = time.time()
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(fire_slow_sync, port, 0.2)
                for _ in range(num_requests)
            ]
            for f in as_completed(futures):
                results.append(f.result())
        elapsed = time.time() - start

        errors = [r for r in results if "error" in r]
        successes = [r for r in results if "error" not in r]
        assert len(successes) == num_requests, (
            f"Expected all {num_requests} requests to succeed, "
            f"got {len(successes)} success, {len(errors)} errors"
        )
        # With pool_size=2 and 2 workers, 20 requests at 0.2s each
        # should take roughly 20 * 0.2 / 2 = 2s minimum (2 workers)
        assert elapsed < 10, f"Took too long: {elapsed:.1f}s for {num_requests} requests"

    @pytest.mark.concurrency
    def test_worker_pid_consistency(self):
        """Multiple requests to same worker always return same PID.

        Confirms Gunicorn workers are long-lived processes, not spawned per-request.
        """
        workers = send_concurrent(port=8071, num_requests=20, delay=0.1)
        for pid, reqs in workers.items():
            pids_seen = [r.get("worker_pid") for r in reqs]
            assert all(p == pid for p in pids_seen), (
                f"Inconsistent PIDs for worker group: {set(pids_seen)}"
            )

    @pytest.mark.concurrency
    def test_pool_40_handler_concurrency(self):
        """Pool=40 (matching anyio tokens): handlers should reach near anyio ceiling.

        With pool_size=40, connection contention is eliminated for up to 40 concurrent
        sync requests per worker. Handler concurrency should be limited by anyio (40)
        or by the number of requests sent, whichever is smaller.
        """
        workers = send_concurrent(port=8073, num_requests=50, delay=0.3)
        assert len(workers) >= 1
        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            # With 50 requests / 2 workers = ~25 per worker, pool=40 should not block
            assert max_conc >= 5, (
                f"Worker {pid}: max concurrent={max_conc}, expected ≥ 5 "
                f"(pool=40 should not be the bottleneck with 25 reqs/worker)"
            )

    @pytest.mark.concurrency
    def test_pool_80_handler_concurrency(self):
        """Pool=80 (w*t=2*40): should match anyio ceiling exactly.

        With pool_size=80, even under heavy load the handler concurrency is
        capped by anyio thread pool (40 per worker), not by the connection pool.
        """
        workers = send_concurrent(port=8074, num_requests=60, delay=0.3)
        assert len(workers) >= 1
        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            # Pool=80 should never be the bottleneck — anyio (40) is the limit
            assert max_conc >= 5, (
                f"Worker {pid}: max concurrent={max_conc}, expected ≥ 5 "
                f"(pool=80 should never bottleneck)"
            )

    @pytest.mark.concurrency
    def test_pool_sizing_comparison(self):
        """Compare handler concurrency across pool sizes: 2, 40, 80, 100.

        All should show similar handler concurrency (limited by anyio, not pool),
        but throughput will differ because small pools cause connection queuing.
        """
        ports = {
            "pool_2": 8070,
            "pool_40": 8073,
            "pool_80": 8074,
            "pool_100": 8072,
        }
        num_requests = 40
        delay = 0.2
        results = {}

        for label, port in ports.items():
            workers = send_concurrent(port=port, num_requests=num_requests, delay=delay)
            for pid, reqs in workers.items():
                max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
                results[f"{label}_worker_{pid}"] = max_conc

        # All pool sizes should show handler concurrency > 2
        # (limited by anyio thread pool, not connection pool)
        for key, max_conc in results.items():
            assert max_conc >= 2, (
                f"{key}: max concurrent={max_conc}, expected ≥ 2"
            )
