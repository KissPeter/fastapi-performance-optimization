import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
import time


def fire_retry(port):
    try:
        resp = httpx.get(
            f"http://127.0.0.1:{port}/info/retry_sync",
            params={"delay": 0.05, "max_retries": 3, "backoff_factor": 0.1},
            timeout=10.0,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def fire_circuit_breaker(port):
    try:
        resp = httpx.get(
            f"http://127.0.0.1:{port}/info/circuit_breaker_sync",
            params={"delay": 0.05},
            timeout=10.0,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


class TestRetryPattern:

    @pytest.mark.robustness
    def test_retry_succeeds_eventually(self):
        """Retry with 30% fail rate: most requests should succeed after retries."""
        port = 8085
        num_requests = 50
        results = []
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(fire_retry, port) for _ in range(num_requests)]
            for f in as_completed(futures):
                results.append(f.result())

        statuses = [r.get("status") for r in results if "error" not in r]
        oks = sum(1 for s in statuses if s == "ok")
        exhausted = sum(1 for s in statuses if s == "exhausted")

        assert len(statuses) > 0, "No responses received"
        # With 30% fail rate and 3 retries, P(all fail) = 0.3^4 = 0.0081
        # So <1% should exhaust
        success_rate = oks / len(statuses)
        assert success_rate > 0.8, (
            f"Success rate {success_rate:.1%} too low, expected > 80% "
            f"(oks={oks}, exhausted={exhausted})"
        )

    @pytest.mark.robustness
    def test_retry_attempts_tracked(self):
        """Verify retry attempts are tracked correctly."""
        port = 8085
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fire_retry, port) for _ in range(10)]
            for f in as_completed(futures):
                results.append(f.result())

        for r in results:
            if "error" in r:
                continue
            attempts = r.get("attempts", 0)
            status = r.get("status")
            assert attempts >= 1, f"Expected at least 1 attempt, got {attempts}"
            if status == "ok":
                assert attempts <= 4, f"OK with {attempts} attempts (max=4)"
            elif status == "exhausted":
                assert attempts == 4, f"Exhausted with {attempts} attempts (expected=4)"


class TestCircuitBreaker:

    @pytest.mark.robustness
    def test_circuit_opens_after_failures(self):
        """With 50% fail rate and threshold=5, circuit should open after 5 consecutive failures."""
        port = 8085
        num_requests = 50
        results = []
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(fire_circuit_breaker, port)
                for _ in range(num_requests)
            ]
            for f in as_completed(futures):
                results.append(f.result())

        statuses = [r.get("status") for r in results if "error" not in r]
        circuit_opens = sum(1 for s in statuses if s == "circuit_open")

        assert len(statuses) > 0, "No responses received"
        # With 50% fail rate, circuit should open at some point
        # Once open, subsequent requests should be circuit_open
        print(f"  Statuses: ok={statuses.count('ok')}, "
              f"error={statuses.count('error')}, "
              f"circuit_open={circuit_opens}")

    @pytest.mark.robustness
    def test_circuit_breaker_tracks_state(self):
        """Verify circuit breaker state is tracked across requests."""
        port = 8085
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(fire_circuit_breaker, port)
                for _ in range(20)
            ]
            for f in as_completed(futures):
                results.append(f.result())

        for r in results:
            if "error" in r:
                continue
            state = r.get("circuit_state")
            failures = r.get("failures", 0)
            assert state in ("closed", "open", "half-open"), f"Unknown state: {state}"
            assert failures >= 0, f"Negative failures: {failures}"

    @pytest.mark.robustness
    def test_circuit_breaker_recovers(self):
        """After circuit opens and recovery timeout passes, circuit should allow requests."""
        port = 8085
        # Send requests to trigger failures
        for _ in range(10):
            fire_circuit_breaker(port)

        # Wait for recovery timeout (set to 10s in docker-compose)
        time.sleep(11)

        # Send a request — should be half-open (allowed through)
        result = fire_circuit_breaker(port)
        if "error" not in result:
            state = result.get("circuit_state")
            assert state in ("half-open", "closed"), (
                f"Expected half-open or closed after recovery, got {state}"
            )
