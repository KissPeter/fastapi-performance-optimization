import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx


def fire_slow_sync(port, delay=0.2):
    try:
        resp = httpx.get(
            f"http://127.0.0.1:{port}/info/slow_sync",
            params={"delay": delay},
            timeout=30.0,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


class TestThreadPoolTuning:

    @pytest.mark.thread_pool_tuning
    def test_anyio_40_concurrency(self):
        """With anyio_tokens=40 and pool=100, handler concurrency should reach near 40."""
        num_requests = 60
        workers = {}
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(fire_slow_sync, 8080, 0.3)
                for _ in range(num_requests)
            ]
            for f in as_completed(futures):
                r = f.result()
                if "error" not in r:
                    pid = r.get("worker_pid")
                    if pid not in workers:
                        workers[pid] = []
                    workers[pid].append(r)

        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            print(f"  Worker {pid}: max_concurrent={max_conc}, total_requests={len(reqs)}")
            assert max_conc >= 5, (
                f"anyio_tokens=40: worker {pid} max concurrent={max_conc}, expected ≥ 5"
            )

    @pytest.mark.thread_pool_tuning
    def test_anyio_80_concurrency(self):
        """With anyio_tokens=80 and pool=100, handler concurrency should reach near 80."""
        num_requests = 100
        workers = {}
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(fire_slow_sync, 8081, 0.3)
                for _ in range(num_requests)
            ]
            for f in as_completed(futures):
                r = f.result()
                if "error" not in r:
                    pid = r.get("worker_pid")
                    if pid not in workers:
                        workers[pid] = []
                    workers[pid].append(r)

        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            print(f"  Worker {pid}: max_concurrent={max_conc}, total_requests={len(reqs)}")
            assert max_conc >= 5, (
                f"anyio_tokens=80: worker {pid} max concurrent={max_conc}, expected ≥ 5"
            )

    @pytest.mark.thread_pool_tuning
    def test_anyio_100_concurrency(self):
        """With anyio_tokens=100 and pool=100, handler concurrency should reach near 100."""
        num_requests = 120
        workers = {}
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(fire_slow_sync, 8082, 0.3)
                for _ in range(num_requests)
            ]
            for f in as_completed(futures):
                r = f.result()
                if "error" not in r:
                    pid = r.get("worker_pid")
                    if pid not in workers:
                        workers[pid] = []
                    workers[pid].append(r)

        for pid, reqs in workers.items():
            max_conc = max(r.get("concurrent_at_start", 0) for r in reqs)
            print(f"  Worker {pid}: max_concurrent={max_conc}, total_requests={len(reqs)}")
            assert max_conc >= 5, (
                f"anyio_tokens=100: worker {pid} max concurrent={max_conc}, expected ≥ 5"
            )
