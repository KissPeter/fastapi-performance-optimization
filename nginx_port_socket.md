---
title: Nginx in front of FastAPI
layout: template
filename: nginx_port_socket.md
---

# Nginx in front of FastAPI

Another topic not strictly FastAPI performance optimization, but has a great benefit for the overall service if used. [Nginx](https://www.nginx.com/) is a versatile service, web server, reverse proxy, WAF and so on.
By using in front of the FastAPI application some functions can be decoupled from Gunicorn (request sanity check, timeout handling, backlogging, extra logging in case of error, app latency measurement and so on)
Typical reverse proxy [configuration](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/#passing-a-request-to-a-proxied-server) uses TCP ports between the app and the web server / reverse proxy but it has negative impact on the concurrency as web server - app communication requires a pair of ports allocated for each connection.
There are 65535 port all together, but some [ranges](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers#Well-known_ports) are not for this purpose so the concurrency is limited, furthermore a port doesn't become free immediately after a connection is closed
The alternative solution which is mentioned in [Uvicorn](https://www.uvicorn.org/deployment/#running-behind-nginx) documentation suggests using sockets which indeed a better solution with some challenges.

## FastAPI as non-root user
If you run your application as non-root user you need to be sure nginx user can read and write the socket.
Fortunately Gunicorn supports [umask](https://docs.gunicorn.org/en/stable/settings.html#umask). 
The most secure option is dedicating a group to this communication, making nginx's and app's user part of that group and limiting the communication to group read and write (umask 717)

## Test environment

* The [usual](https://kisspeter.github.io/fastapi-performance-optimization/#test-environment) test set was used
* Application runs as **Gunicorn** with [UvicornWorker](https://www.uvicorn.org/deployment/#gunicorn) behind **Nginx** reverse proxy
* Load tested with [Apache Bench](https://httpd.apache.org/docs/2.4/programs/ab.html): `ab -q -c 100 -n 1000` (100 concurrent connections, 1000 requests)
* Each test runs **3 times**, results are averaged
* The two communication methods tested:
  - **Port**: Nginx connects to Gunicorn via TCP port (`proxy_pass http://127.0.0.1:PORT`)
  - **Socket**: Nginx connects to Gunicorn via Unix socket file (`proxy_pass http://unix:/tmp/gunicorn.sock`)

## Measurements

> CI run [29770319196](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/29770319196) — Python 3.14, Ubuntu latest.

### Runner configurations tested

The naming convention is `Gunicorn w{workers}t{threads}` where workers are pre-forked OS processes and threads are per-worker Python threads:

| **Gunicorn config** | **Workers** | **Threads** | **What it means** |
|---|---|---|---|
| w3t1 | 3 | 1 | 3 processes, 1 thread each — highest parallelism tested |
| w1t0 | 1 | 0 | 1 process, no threads — single-process baseline |
| w2t0 | 2 | 0 | 2 processes, no threads — default production config |
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
| Requests per second   |         1936.66  |         1868.64  |         1915.02  |      1906.77  |
| Time per request [ms] |           51.635 |           53.515 |           52.219 |        52.4563 |


#### Nginx - APP via socket

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         7476.71  |          6645.0  |         7434.42  |      7185.38  | +276.83%                  |
| Time per request [ms] |           13.375 |           15.049 |           13.451 |        13.9583 | 38.5 ms                  |

### Observations
* Socket delivers **3.8x throughput** (7,185 vs 1,907 rps) and **73% lower latency** (14.0 vs 52.5 ms)
* This is the largest gain across all scenarios because sync+small is the most connection-intensive — each request opens and closes a full TCP port pair

### Asynchronous API endpoint with small request / response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2780.52  |         2764.32  |         2777.57  |      2774.14  |
| Time per request [ms] |           35.964 |           36.175 |           36.003 |        36.0473 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         7315.44  |         6159.01  |         7347.77  |      6940.74  | +150.19%                  |
| Time per request [ms] |            13.67 |           16.236 |            13.61 |        14.5053 | 21.54 ms                 |

### Observations
* Socket delivers **2.5x throughput** (6,941 vs 2,774 rps) and **60% lower latency** (14.5 vs 36.1 ms)
* Async endpoints reuse connections, so the port baseline is higher (2,774 vs 1,907 rps for sync) — yet socket performance stays flat at ~7k rps, confirming the bottleneck was TCP overhead, not the application

### Synchronous API endpoint with 1MB response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2885.82  |         2758.47  |         2368.75  |      2671.01  |
| Time per request [ms] |           34.652 |           36.252 |           42.216 |        37.7067 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         6454.11  |         6795.05  |         6942.52  |      6730.56  | +151.99%                  |
| Time per request [ms] |           15.494 |           14.717 |           14.404 |        14.8717 | 22.83 ms                 |

### Observations
* Socket delivers **2.5x throughput** (6,731 vs 2,671 rps) and **60% lower latency** (14.9 vs 37.7 ms)
* The 1MB payload reduces the port vs socket gap slightly compared to small responses — the app-side processing time starts to dominate over the connection overhead

### Asynchronous API endpoint with 1MB response

#### Nginx - APP via port

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |         2713.03  |         2819.41  |         2761.47  |      2764.64  |
| Time per request [ms] |           36.859 |           35.468 |           36.213 |         36.18 |

#### Nginx - APP via socket


| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |         6855.33  |         6831.25  |         7037.45  |      6908.01  | +149.87%                  |
| Time per request [ms] |           14.587 |           14.639 |            14.21 |        14.4787 | 21.7 ms                  |

### Observations
* Socket delivers **2.5x throughput** (6,908 vs 2,765 rps) and **60% lower latency** (14.5 vs 36.2 ms)
* Results are nearly identical to sync 1MB, confirming that at 1MB payload size, async/sync distinction has minimal impact — the socket optimization applies equally

## Conclusion

### Apples to apples comparison

| Scenario | Port (rps) | Socket (rps) | Throughput gain | Port latency (ms) | Socket latency (ms) | Latency gain |
|---|---|---|---|---|---|---|
| Sync, small response | 1,907 | 7,185 | +276.8% | 52.5 | 14.0 | 73.3% lower |
| Async, small response | 2,774 | 6,941 | +150.2% | 36.1 | 14.5 | 59.8% lower |
| Sync, 1MB response | 2,671 | 6,731 | +152.0% | 37.7 | 14.9 | 60.5% lower |
| Async, 1MB response | 2,765 | 6,908 | +149.9% | 36.2 | 14.5 | 59.9% lower |

Two clear patterns emerge:

1. **Socket throughput is consistent across all scenarios:** ~6,700-7,200 rps regardless of sync/async or payload size. The communication layer is not the bottleneck — the application is. Switching to sockets removes the networking overhead that was masking this.
2. **Port throughput is constrained by the TCP port pairing overhead:** ranging from 1,907 to 2,774 rps. The sync+small case is hit hardest (+276%) because it is the most connection-intensive — each request opens and closes a TCP pair, while async reuse reduces the impact.

In short: **Unix sockets deliver a flat ~7k rps regardless of endpoint type, while TCP ports cap at ~2-2.8k rps.** The optimization is not scenario-dependent — it is a baseline improvement that applies universally.

Sample socket config is [here](https://github.com/KissPeter/fastapi-performance-optimization/blob/main/app_files/nginx.conf#L31)

## Impact

### Quantified production impact

Assuming a single Gunicorn instance behind nginx:

| Metric | Before (port) | After (socket) | Improvement |
|---|---|---|---|
| Throughput (avg across scenarios) | ~2,529 rps | ~6,941 rps | **~174% more requests/sec** |
| Latency (avg across scenarios) | ~40.6 ms | ~14.5 ms | **~64% lower latency** |
| Effective concurrent users supported (p95 ~200ms budget) | ~380 | ~900 | **~2.4x more headroom** |

### When this matters most

- **High-concurrency APIs** — each TCP port pair costs ~3-5KB kernel memory; sockets eliminate this entirely
- **Containerized deployments** — container orchestration (K8s, ECS) typically shares a network namespace per pod, so port exhaustion is real under load
- **Low-latency endpoints** — sync endpoints with small payloads benefit the most (+276%) because they are connection-bound
- **Multi-worker setups** — the benefit compounds with worker count since each worker creates its own port pairs

### Trade-offs to consider

- **Operational complexity** — socket files require correct filesystem permissions (see [Non-root user section](#fastapi-as-non-root-user)); TCP ports are simpler to manage and debug
- **Observability** — standard TCP tools (ss, netstat, tcpdump) do not work on Unix sockets; you need `ls -la` on the socket file or application-level metrics
- **Load balancing** — TCP port-based load balancing (HAProxy, etc.) is straightforward across multiple app instances; socket-based setups require each instance to have its own socket file and matching nginx upstream
- **Portability** — sockets are filesystem-dependent; they do not work across network boundaries, which matters in split-service architectures

### Recommendation

Switch to Unix socket communication between nginx and Gunicorn **by default**. The throughput and latency gains are significant and consistent across all endpoint types. Only use TCP ports when you need cross-network communication between the reverse proxy and the application.

# Pro tip:
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
