---
title: Retry and Circuit Breaker
layout: template
filename: retry_circuit_breaker.md
---

# Retry and Circuit Breaker Patterns

When your FastAPI application calls external services, failures are inevitable. Retry logic and circuit breakers protect your application from cascading failures and resource exhaustion.

## The problem

```
External API is slow/down
  │
  ├── Request fails → retry → fails again → retry → fails again
  │     └── Worker blocked for retries × timeout
  │           └── Other requests queue up
  │                 └── Thread pool exhausted
  │                       └── All workers blocked → total outage
  │
  └── Without protection: 1 failing service takes down your entire app
```

## Retry patterns

### Exponential backoff

Wait exponentially longer between retries. Prevents thundering herd on recovering services.

```
Attempt 1: fail → wait 0.5s
Attempt 2: fail → wait 1.0s
Attempt 3: fail → wait 2.0s
Attempt 4: fail → give up
```

### Retry with jitter

Add random delay to prevent synchronized retries from all clients.

```
Attempt 1: fail → wait 0.5s + random(0, 0.3s)
Attempt 2: fail → wait 1.0s + random(0, 0.5s)
Attempt 3: fail → wait 2.0s + random(0, 1.0s)
```

### What to retry

| Error type | Retry? | Reason |
|-----------|--------|--------|
| Connection timeout | Yes | Transient network issue |
| 500 Internal Server Error | Yes | Server might recover |
| 502/503/504 | Yes | Upstream service temporarily unavailable |
| 429 Too Many Requests | Yes (with delay) | Rate limited, respect Retry-After header |
| 400 Bad Request | No | Client error, won't fix itself |
| 401/403 | No | Auth issue, won't fix with retry |
| 404 | No | Resource doesn't exist |

### Retry budget

Limit total retry attempts to prevent amplification:

```
retry_budget = original_requests × max_retries × error_rate
```

If 10% of requests fail and you retry 3 times:
```
1000 requests × 10% failure × 3 retries = 300 extra requests
Total: 1300 requests (30% amplification)
```

Keep retry amplification under 20% of your original traffic.

## Circuit breaker pattern

A circuit breaker monitors failures and **stops sending requests** when failures exceed a threshold. This gives the failing service time to recover.

### States

```
CLOSED (normal) ──[failures exceed threshold]──► OPEN (rejecting)
     ▲                                              │
     │                                    [timeout expires]
     │                                              │
     └──────────[probe succeeds]────────── HALF-OPEN (testing)
```

### Configuration

| Parameter | Typical value | Purpose |
|-----------|--------------|---------|
| Failure threshold | 5 failures in 60s | When to trip the circuit |
| Recovery timeout | 30s | How long to stay open |
| Half-open max calls | 1-3 | Probe requests to test recovery |
| Success threshold | 2-3 successes | When to close the circuit |

### Behavior

**CLOSED state:**
- Requests pass through normally
- Failures are counted
- If failures exceed threshold → trip to OPEN

**OPEN state:**
- All requests are rejected immediately (no wait, no retry)
- After timeout → move to HALF-OPEN

**HALF-OPEN state:**
- Allow a few probe requests through
- If they succeed → close circuit (back to normal)
- If they fail → trip back to OPEN

## Interaction with connection pools

Retry and circuit breaker behavior directly impacts connection pool utilization:

### Without circuit breaker

```
External API slow (5s response time)
  │
  ├── Request 1: takes connection, waits 5s, fails, retries...
  │     └── Connection held for 5s × 3 retries = 15s
  ├── Request 2: same pattern
  ├── Request 3: same pattern
  └── Pool exhausted, new requests wait
```

### With circuit breaker

```
External API slow (5s response time)
  │
  ├── Request 1: fails 5 times → circuit opens
  ├── Request 2: rejected immediately (no connection needed)
  ├── Request 3: rejected immediately
  └── Pool stays available for other services
```

## Implementation considerations

### Per-worker isolation

Like connection pools, circuit breakers are **per-process**. Each worker maintains its own failure counts and circuit state.

```
Worker 1: circuit OPEN (saw failures)
Worker 2: circuit CLOSED (didn't see failures)
Worker 3: circuit OPEN (saw failures)
```

This is generally fine — each worker independently detects problems.

### Shared state (advanced)

For true circuit breaker coordination across workers, you need shared state:

| Approach | Complexity | Consistency |
|----------|-----------|-------------|
| Per-worker (no sharing) | Low | Eventual |
| Redis-backed | Medium | Strong |
| External service (e.g., Prometheus + Alertmanager) | High | Strong |

Per-worker is usually sufficient. The circuit will trip independently in each worker, which is acceptable.

### Connection pool drain

When the circuit opens:
1. Stop sending new requests to the failing service
2. Existing connections time out and close
3. Pool becomes available for other services

This prevents connection pool exhaustion during outages.

## Recommendations

| Traffic level | Retry strategy | Circuit breaker |
|--------------|---------------|-----------------|
| Low (< 100 RPS) | 3 retries, exponential backoff | Optional |
| Medium (100-1000 RPS) | 3 retries, exponential + jitter | Recommended |
| High (> 1000 RPS) | 2 retries, tight timeout | Required |

### Key settings

```
# Retry
max_retries: 3
backoff_base: 0.5s
backoff_max: 5s
timeout: 5s

# Circuit breaker
failure_threshold: 5
failure_window: 60s
recovery_timeout: 30s
half_open_max_calls: 2
```

## Impact on performance

| Scenario | Without protection | With circuit breaker |
|----------|-------------------|---------------------|
| External API down | All workers blocked, app hangs | Quick rejection, app stays responsive |
| External API slow | Connection pool exhausted, latency spikes | Circuit trips, latency stays low |
| External API recovers | Gradual recovery as connections drain | Circuit closes, traffic resumes |

The circuit breaker trades **availability of one endpoint** for **availability of the entire application**.
