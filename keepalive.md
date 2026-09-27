---
title: Keepalive support
description: "HTTP connection keepalive for FastAPI behind Nginx: +9-12% on small payloads, negligible on 1MB responses. Cheap, safe default — matters more when connections are expensive (HTTPS)."
layout: template
filename: keepalive.md
---

# FastAPI connection keepalive

Nobody initializes new connection for each and every query right? :-)
Here is an example how to do it right from the client side:
```python
http_client = urllib3.PoolManager(
            retries=Retry(
                connect=5,
                read=2,
                redirect=5,
                status_forcelist=[429, 500, 501, 502, 503, 504],
                backoff_factor=0.2,
            ),
            timeout=Timeout(connect=5.0, read=10.0),
            num_pools=10,
        )
```

> **TL;DR** Enable HTTP keepalive between Nginx and your Python app — it is a cheap, safe default. Measured **+8.98% on sync** and **+12.30% on async** small endpoints. On 1MB responses it makes no difference (within noise). The win grows when connection setup is expensive, e.g. **HTTPS**.

## Verdict

* Keepalive is a **small but near-free** win on small payloads: **+8.98%** sync, **+12.30%** async, simply by reusing upstream connections
* On **1MB responses** keepalive is a wash (+0.13% sync, -1.98% async — noise)
* If you use **HTTPS**, connection creation has even higher overhead due to the additional SSL layer, so keepalive matters more

## What is HTTP keepalive?

When your client and server frequently interacts you should always create [persistent HTTP connection](
https://en.wikipedia.org/wiki/HTTP_persistent_connection)

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/HTTP_persistent_connection.svg/600px-HTTP_persistent_connection.svg.png" alt="HTTP Keepalive">

Let's see how to support HTTP connection keep-alive from FastAPI as well.

## Measurements

> CI run [36235373898](https://github.com/KissPeter/fastapi-performance-optimization/actions/runs/36235373898) — Python 3.14, Ubuntu latest. All jobs green, no non-2xx responses. Tested on the default app config (w3t1) over a Unix socket: **8009** = no upstream keepalive, **8017** = `keepalive 8` in the nginx upstream.

### Synchronous API endpoint with small request / response

#### Nginx - APP connection, but no keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |        2716.62   |         2910.12  |         2950.52  |      2859.09  |
| Time per request [ms] |           36.81  |          34.363  |          33.892  |      35.0217  |

#### Nginx - APP connection with keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |        3147.31   |         3141.11  |         3059.43  |      3115.95  | +8.98%                   |
| Time per request [ms] |          31.773  |          31.836  |          32.686  |     32.0983   | 2.92 ms                  |

### Observations
* **+8.98%** throughput, **2.92 ms** lower latency — we simply reuse our existing connections instead of establishing a fresh upstream connection per request

### Asynchronous API endpoint with small request / response

#### Nginx - APP connection, but no keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |        3445.89   |         3437.83  |         3489.34  |      3457.69  |
| Time per request [ms] |            29.02 |          29.088  |          28.659  |     28.9223   |

#### Nginx - APP connection with keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |        3865.38   |         3837.63  |         3945.8   |      3882.94  | +12.30%                  |
| Time per request [ms] |          25.871  |          26.058  |          25.343  |     25.7573   | 3.16 ms                  |

### Observations
* **+12.30%** throughput, **3.16 ms** lower latency. Keepalive helps async endpoints at least as much as sync ones by avoiding connection churn on the busy nginx↔app channel

### Synchronous API endpoint with 1MB response

#### Nginx - APP connection, but no keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |           18.08  |           17.79  |           17.96  |      17.9433  |
| Time per request [ms] |         5529.88   |         5619.71  |         5568.45  |      5572.68  |

#### Nginx - APP connection with keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |           17.89  |           17.99  |           18.02  |      17.9667  | +0.13%                   |
| Time per request [ms] |         5588.77   |         5557.51  |         5550.14  |      5565.47  | 7.2 ms                   |

### Observations
* **+0.13%** — connection setup is nothing compared to moving a megabyte per request, keepalive is irrelevant here

### Asynchronous API endpoint with 1MB response

#### Nginx - APP connection, but no keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** |
|-----------------------|------------------|------------------|------------------|---------------|
| Requests per second   |           18.14  |           18.11  |           18.24  |      18.1633  |
| Time per request [ms] |        5512.51    |         5521.74  |         5481.62  |      5505.29  |

#### Nginx - APP connection with keepalive

| **Test attribute**    |   **Test run 1** |   **Test run 2** |   **Test run 3** |   **Average** | Difference to baseline   |
|-----------------------|------------------|------------------|------------------|---------------|--------------------------|
| Requests per second   |           17.94  |           17.78  |           17.69  |      17.8033  | -1.98%                   |
| Time per request [ms] |         5574.23   |         5623.66  |         5653.73  |      5617.21  | -111.92 ms               |

### Observations
* **-1.98%** — same magnitude as the run-to-run noise on this scenario, not a real regression. Keepalive neither helps nor hurts large bodies

## Pro tip

* This is a full **Nginx config for FastAPI** with keepalive support:

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
![](./test.svg)
```html
<hr>

```