---
title: Nginx in front of FastAPI
description: "Nginx in front of FastAPI: Unix socket beats TCP port by ~9-19% on small payloads (~3-5ms lower latency) and is a wash on 1MB responses. Cheap to enable, switch by default."
layout: template
filename: nginx_port_socket.md
---

# Nginx in front of FastAPI

Another topic not strictly FastAPI performance optimization, but has a great benefit for the overall service if used. [Nginx](https://www.nginx.com/) is a versatile service, web server, reverse proxy, WAF and so on.
By using in front of the FastAPI application some functions can be decoupled from Gunicorn (request sanity check, timeout handling, backlogging, extra logging in case of error, app latency measurement and so on)
Typical reverse proxy [configuration](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/#passing-a-request-to-a-proxied-server) uses TCP ports between the app and the web server / reverse proxy but it has negative impact on the concurrency as web server - app communication requires a pair of ports allocated for each connection.
There are 65535 port all together, but some [ranges](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers#Well-known_ports) are not for this purpose so the concurrency is limited, furthermore a port doesn't become free immediately after a connection is closed
The alternative solution which is mentioned in [Uvicorn](https://www.uvicorn.org/deployment/#running-behind-nginx) documentation suggests using sockets which indeed a better solution with some challenges.

> **TL;DR** Talk to your app over a **Unix socket**, not a TCP port. For **small payloads** sockets are consistently ~5-19% faster than a TCP port for both sync and async endpoints. For **1MB responses** the difference collapses to noise (~1-3%). Cheap to enable, so use sockets by default — but don't expect order-of-magnitude gains.

## Verdict

> **Individual impact: ~+12-15% throughput and ~3-5ms lower latency** on small payloads by switching nginx ↔ Gunicorn from TCP port to Unix socket. On 1MB responses the two are equivalent.

**Switch to Unix socket communication between nginx and Gunicorn by default.** The gain is small but consistent on small payloads (default app config, w3t1):

| Scenario | Port (rps) | Socket (rps) | Throughput gain | Latency gain |
|---|---|---|---|---|
| Sync, small response | 2,465.63 | 2,820.24 | +14.38% | 5.09 ms lower |
| Async, small response | 2,910.96 | 3,439.80 | +18.17% | 5.30 ms lower |
| Sync, 1MB response | 17.24 | 17.56 | +1.84% | 107 ms lower |
| Async, 1MB response | 17.19 | 17.71 | +3.01% | 170 ms lower |

Small requests spend proportionally little time in the application, so the per-connection overhead of TCP (socket pair allocation and teardown for every connection) is a measurable share of the total. A Unix socket has no such per-connection cost. When the response body is 1MB, moving bytes dominates the request (≈5.7s each), so the transport choice is a rounding error.

> **Why did the numbers change?** An earlier revision of this page reported a flat ~7k rps on sockets and concluded TCP ports cap at ~2-2.8k rps. That data came from unreliable CI runs (nginx `502` responses and `ab` timeouts under the load test, with no guard flagging them). The harness was fixed — nginx backlog raised, Gunicorn/nginx timeouts aligned, and a non-2xx response guard added per test — and everything was re-measured in a single fully-green CI run. Once the errors were filtered out, the real socket advantage is what you see above.

**Only use TCP ports when you need cross-network communication** between the reverse proxy and the application. Trade-offs to accept with sockets: socket file permissions, no `ss`/`tcpdump` observability, and per-instance socket files for load balancing.

## FastAPI as non-root user
If you run your application as non-root user you need to be sure nginx user can read and write the socket.
Fortunately Gunicorn supports [umask](https://docs.gunicorn.org/en/stable/settings.html#umask). 
The most secure option is dedicating a group to this communication, making nginx's and app's user part of that group and limiting the communication to group read and write (umask 717)

## Test environment

* The [usual](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) test set was used
* Application runs as **Gunicorn** with [UvicornWorker](https://www.uvicorn.org/deployment/#gunicorn) behind **Nginx** reverse proxy
* Load tested with [Apache Bench](https://httpd.apache.org/docs/2.4/programs/ab.html): `ab -q -c 100 -n 1000` (100 concurrent connections, 1000 requests; 500 for the 1MB tests)
* Each test runs **3 times**, results are averaged
* The two communication methods tested:
  - **Port**: Nginx connects to Gunicorn via TCP port (`proxy_pass http://127.0.0.1:PORT`)
  - **Socket**: Nginx connects to Gunicorn via Unix socket file (`proxy_pass http://unix:/tmp/gunicorn.sock`)

## Measurements

> CI run [36235373898](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/36235373898) — Python 3.14, Ubuntu latest. All jobs green, no non-2xx responses.

### Runner configurations tested

The default app runs **w3t1** (3 workers, 1 thread). The other runner configurations were measured to verify the transport effect is consistent:

| **Gunicorn config** | **Workers** | **Threads** | **What it means** |
|---|---|---|---|
| w3t1 | 3 | 1 | 3 processes, 1 thread each — default app config |
| w1t0 | 1 | 0 | 1 process, no threads — single-process baseline |
| w2t0 | 2 | 0 | 2 processes, no threads — gunicorn default production config |
| w1t1 | 1 | 1 | 1 process, 1 thread — minimal threading |
| w2t1 | 2 | 1 | 2 processes, 1 thread each — balanced config |
| w1t2 | 1 | 2 | 1 process, 2 threads — thread-heavy single process |
| w2t2 | 2 | 2 | 2 processes, 2 threads each — max threading tested |

Each configuration was tested with both TCP port and Unix socket communication, on different ports:

| **Config** | **Port test port** | **Socket test port** |
|---|---|---|
| w3t1 | 8008 | 8009 |
| w1t0 | 8140 | 8141 |
| w2t0 | 8142 | 8143 |
| w1t1 | 8144 | 8145 |
| w2t1 | 8146 | 8147 |
| w1t2 | 8148 | 8149 |
| w2t2 | 8150 | 8151 |

### Synchronous API endpoint with small request / response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2495.28  |         2478.33  |         2423.27  |      2465.63  |
| Time per request [ms] |           40.076 |            40.35 |           41.267 |        40.5643 |


#### Nginx - APP via socket

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         2822.6   |         2756.06  |         2882.07  |      2820.24  | +14.38%                  |
| Time per request [ms] |           35.428 |           36.284 |           34.697 |        35.4697 | 5.09 ms                  |

### Observations
* Socket delivers **+14.38% throughput** (2,820 vs 2,465 rps) and **5.09 ms lower latency** (35.5 vs 40.6 ms)
* Sync + small is the most connection-intensive scenario — each request opens and closes a full TCP socket pair, so transport overhead is the largest share of the total time

### Asynchronous API endpoint with small request / response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2970.45  |         2814.26  |         2948.16  |      2910.96  |
| Time per request [ms] |           33.665 |           35.533 |           33.919 |        34.3723 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         3445.51  |         3483.48  |         3390.42  |       3439.8  | +18.17%                  |
| Time per request [ms] |           29.023 |           28.707 |           29.495 |         29.075 | 5.3 ms                   |

### Observations
* Socket delivers **+18.17% throughput** (3,440 vs 2,911 rps) and **5.3 ms lower latency** (29.1 vs 34.4 ms)
* Async endpoints already reuse connections, yet the socket edge is if anything larger than for sync

### Synchronous API endpoint with 1MB response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |           17.35  |            17.6  |           16.77  |        17.24  |
| Time per request [ms] |         5762.78  |         5682.46  |         5962.79  |      5802.68  |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |           17.57  |           17.45  |           17.65  |      17.5567  | +1.84%                   |
| Time per request [ms] |        5692.3    |         5731.41  |         5664.51  |      5696.07  | 106.6 ms                 |

### Observations
* Socket delivers **+1.84% throughput** (17.56 vs 17.24 rps) — within run-to-run noise
* With a 1MB body, ~5.7s of every request is spent copying the payload, dwarfing the transport choice

### Asynchronous API endpoint with 1MB response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |           17.48  |           16.96  |           17.14  |      17.1933  |
| Time per request [ms] |          5719.7   |         5897.27  |         5834.24  |      5817.07  |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |           17.81  |            17.8  |           17.52  |         17.71  | +3.01%                   |
| Time per request [ms] |        5614.69    |         5617.02  |         5709.14  |      5646.95  | 170.12 ms                |

### Observations
* Socket delivers **+3.01% throughput** (17.71 vs 17.19 rps) — within run-to-run noise
* Same as sync: at 1MB the payload transfer dominates, transport does not matter

## All runner configurations

The socket effect is consistent across every runner configuration on small payloads, and consistent in being negligible on 1MB responses:

### Small request / response

| **Config** | **Sync @ port (rps)** | **Sync @ socket (rps)** | **Sync Δ** | **Async @ port (rps)** | **Async @ socket (rps)** | **Async Δ** |
|---|---|---|---|---|---|---|
| w3t1 | 2,465.63 | 2,820.24 | +14.38% | 2,910.96 | 3,439.80 | +18.17% |
| w1t0 | 2,138.20 | 2,319.94 | +8.50% | 2,463.98 | 2,730.93 | +10.83% |
| w2t0 | 2,661.41 | 3,030.04 | +13.85% | 3,150.07 | 3,746.71 | +18.94% |
| w1t1 | 2,005.78 | 2,219.59 | +10.66% | 2,436.33 | 2,697.49 | +10.72% |
| w2t1 | 2,703.77 | 3,060.75 | +13.20% | 3,150.18 | 3,721.35 | +18.13% |
| w1t2 | 2,111.44 | 2,210.28 | +4.68% | 2,409.85 | 2,681.91 | +11.29% |
| w2t2 | 2,519.80 | 2,911.70 | +15.55% | 3,050.35 | 3,484.52 | +14.23% |

### 1MB request / response

| **Config** | **Sync @ port (rps)** | **Sync @ socket (rps)** | **Sync Δ** | **Async @ port (rps)** | **Async @ socket (rps)** | **Async Δ** |
|---|---|---|---|---|---|---|
| w3t1 | 17.24 | 17.56 | +1.84% | 17.19 | 17.71 | +3.01% |
| w1t0 | 12.77 | 13.22 | +3.50% | 12.76 | 12.88 | +0.91% |
| w2t0 | 22.66 | 23.52 | +3.81% | 23.28 | 22.58 | -2.98% |
| w1t1 | 12.75 | 13.07 | +2.51% | 12.88 | 12.75 | -1.03% |
| w2t1 | 23.40 | 23.69 | +1.24% | 23.46 | 22.75 | -3.01% |
| w1t2 | 12.98 | 13.19 | +1.64% | 12.76 | 12.95 | +1.49% |
| w2t2 | 23.48 | 24.17 | +2.95% | 22.63 | 23.94 | +5.76% |

The negative async 1MB deltas (w2t0, w1t1, w2t1) are noise — magnitude below the run-to-run variance of the port baseline itself.

## Conclusion

Two clear patterns emerge:

1. **Small payloads: sockets are consistently faster.** Every one of the 14 small-payload measurements (7 configs × sync/async) improved with a socket, by **+4.7% to +18.9%** (median ~+13.5%). Latency drops by roughly 2-5 ms.
2. **1MB responses: sockets and ports are equivalent.** Differences stay in the ±3% band, i.e. within noise. The bottleneck is copying megabytes, not the transport.

In short: **Unix sockets are a small but real, free win for typical small-payload APIs; they bring nothing measurable once responses get large.** Use them by default — they are strictly simpler operationally than managing port inventories too.

Sample socket config is [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/nginx.conf#L31)

## Impact

### Quantified production impact

Assuming a single Gunicorn instance behind nginx:

| Metric | Before (port) | After (socket) | Improvement |
|---|---|---|---|
| Throughput, small payload (default w3t1, sync+async avg) | ~2,688 rps | ~3,130 rps | **~+16% more requests/sec** |
| Latency, small payload (default w3t1, sync+async avg) | ~37.5 ms | ~32.3 ms | **~5 ms lower latency** |
| 1MB responses | ~17.2-17.2 rps | ~17.6-17.7 rps | ±3% (noise) |

### When this matters most

- **Small, chatty APIs** — many cheap requests per second, where per-connection TCP overhead is a visible share of the budget (+5-19% on small payloads)
- **Very high concurrency** — each TCP connection costs a socket pair in kernel memory and port inventory; sockets eliminate this entirely (relevant at tens of thousands of concurrent connections)
- The benefit matters **less** the larger the responses get; plan your nginx config around your actual payload size

### Trade-offs to consider

- **Operational complexity** — socket files require correct filesystem permissions (see [Non-root user section](#fastapi-as-non-root-user)); TCP ports are simpler to manage and debug
- **Observability** — standard TCP tools (ss, netstat, tcpdump) do not work on Unix sockets; you need `ls -la` on the socket file or application-level metrics
- **Load balancing** — TCP port-based load balancing (HAProxy, etc.) is straightforward across multiple app instances; socket-based setups require each instance to have its own socket file and matching nginx upstream
- **Portability** — sockets are filesystem-dependent; they do not work across network boundaries, which matters in split-service architectures

## Pro tip

* If you use [nginx-light](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/Dockerfile#L3) instead of nginx in your Docker build you can save ~100MB container image size.
* This is a full **Nginx config for FastAPI**:

```shell
user nobody nogroup;
pid /var/run/nginx.pid;
worker_processes 1;  # 1/CPU, to be configured, but Nginx is so powerful, 1 worker can easly handle 1-2k QPS 
events {
  worker_connections 4096; # increase in case of lot of clients
  accept_mutex off; # set to 'on' if nginx worker_processes > 1
  use epoll; # for Linux 2.6+
}

http {
  include mime.types;
  # fallback in case we can't determine a type
  default_type application/octet-stream;
  tcp_nodelay on; # avoid buffer
  access_log off;
  error_log stderr;
  upstream gunicorn {
    # fail_timeout=0 means we always retry an upstream even if it failed
    # to return a good HTTP response
    server unix:/tmp/gunicorn.sock fail_timeout=0;
    keepalive 8;
  }

  server {
    listen                                80;
    server_tokens                         off;
    client_max_body_size                  20M;

    gzip                                  on;
    gzip_proxied                          any;
    gzip_disable                          "msie6";
    gzip_comp_level                       6;
    gzip_min_length                       200; # check your average response size and configure accordingly

    location / {
      proxy_pass                          http://gunicorn;
      proxy_set_header Host               $host;
      proxy_set_header X-Real-IP          $remote_addr;
      proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto  $http_x_forwarded_proto;
      proxy_pass_header                   Server;
      proxy_ignore_client_abort           on;
      proxy_connect_timeout               65s; #  65 here and 60 sec in gconf in order to time out at app side first
      proxy_read_timeout                  65s;
      proxy_send_timeout                  65s;
      proxy_redirect                      off;
      proxy_http_version                  1.1;
      proxy_set_header Connection         "";
      proxy_buffering                     off;
    }
    keepalive_requests                    5000;  
    keepalive_timeout                     120;
    set_real_ip_from                      10.0.0.0/8;
    set_real_ip_from                      172.16.0.0/12;
    set_real_ip_from                      192.168.0.0/16;
    real_ip_header                        X-Forwarded-For;
    real_ip_recursive                     on;
  }
}

```